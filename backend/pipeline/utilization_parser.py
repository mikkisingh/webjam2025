"""
Source 4: Medicare Physician & Other Practitioners utilization data.

For each HCPCS code in the procedures table, queries the CMS Data API
to fetch per-provider rows, then aggregates into national statistics
(avg submitted charge, avg allowed, avg payment, percentiles).

This is the longest-running pipeline step (~60-90 min for all codes).
"""

import time
import requests
from models import Procedure, MedicareUtilization
from .config import UTILIZATION_API_URL, UTILIZATION_BATCH_SIZE, UTILIZATION_API_DELAY, SOURCE_YEAR
from .sync_log import is_sync_current, start_sync, complete_sync, fail_sync


def _percentile(sorted_vals: list, pct: float) -> float:
    """Compute a percentile from a pre-sorted list."""
    if not sorted_vals:
        return 0.0
    idx = int(len(sorted_vals) * pct)
    idx = min(idx, len(sorted_vals) - 1)
    return sorted_vals[idx]


def _fetch_and_aggregate(hcpcs_code: str) -> dict:
    """
    Query the CMS utilization API for a single HCPCS code and compute
    national aggregate statistics from per-provider rows.

    Returns dict with aggregated stats, or None if no data found.
    """
    params = {
        "filter[HCPCS_Cd]": hcpcs_code,
        "size": 5000,
    }

    try:
        resp = requests.get(UTILIZATION_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
    except Exception:
        return None

    if not rows or not isinstance(rows, list):
        return None

    # Separate by place of service (F=Facility, O=Office)
    results = {}
    for pos in ("F", "O"):
        pos_rows = [r for r in rows if r.get("Place_Of_Srvc") == pos]
        if not pos_rows:
            continue

        submitted_charges = []
        allowed_amounts = []
        payment_amounts = []
        total_srvcs = 0
        total_benes = 0

        for r in pos_rows:
            try:
                chrg = float(r.get("Avg_Sbmtd_Chrg", 0) or 0)
                alowd = float(r.get("Avg_Mdcr_Alowd_Amt", 0) or 0)
                pymt = float(r.get("Avg_Mdcr_Pymt_Amt", 0) or 0)
                srvcs = int(r.get("Tot_Srvcs", 0) or 0)
                benes = int(r.get("Tot_Benes", 0) or 0)
            except (ValueError, TypeError):
                continue

            if chrg > 0:
                submitted_charges.append(chrg)
            if alowd > 0:
                allowed_amounts.append(alowd)
            if pymt > 0:
                payment_amounts.append(pymt)
            total_srvcs += srvcs
            total_benes += benes

        if not submitted_charges:
            continue

        submitted_charges.sort()
        allowed_amounts.sort()

        results[pos] = {
            "total_providers": len(pos_rows),
            "total_services": total_srvcs,
            "total_beneficiaries": total_benes,
            "avg_submitted_charge": round(sum(submitted_charges) / len(submitted_charges), 2),
            "avg_allowed_amount": round(sum(allowed_amounts) / len(allowed_amounts), 2) if allowed_amounts else None,
            "avg_medicare_payment": round(sum(payment_amounts) / len(payment_amounts), 2) if payment_amounts else None,
            "p25_submitted_charge": round(_percentile(submitted_charges, 0.25), 2),
            "p75_submitted_charge": round(_percentile(submitted_charges, 0.75), 2),
            "p25_allowed_amount": round(_percentile(allowed_amounts, 0.25), 2) if allowed_amounts else None,
            "p75_allowed_amount": round(_percentile(allowed_amounts, 0.75), 2) if allowed_amounts else None,
        }

    return results if results else None


def sync_utilization_data(db, force=False, limit=None):
    """
    Fetch utilization data for each HCPCS code in the procedures table.

    Args:
        db: SQLAlchemy session
        force: If True, re-sync even if data is current
        limit: If set, only process this many codes (useful for testing)
    """
    if not force and is_sync_current(db, "utilization", max_age_days=30):
        print("  Utilization data is current (synced within 30 days). Use --force to re-import.")
        return

    # Get all unique CPT codes from the procedures table
    codes_query = (
        db.query(Procedure.cpt_code)
        .filter(Procedure.modifier == "")
        .distinct()
        .order_by(Procedure.cpt_code)
    )
    if limit:
        codes_query = codes_query.limit(limit)

    all_codes = [row[0] for row in codes_query.all()]
    total_codes = len(all_codes)

    if total_codes == 0:
        print("  No procedure codes found. Run PFS sync first.")
        return

    print(f"  Processing utilization data for {total_codes} HCPCS codes ...")

    log = start_sync(db, "utilization", UTILIZATION_API_URL)
    try:
        inserted = 0
        updated = 0
        processed = 0
        skipped = 0

        for i, code in enumerate(all_codes):
            agg = _fetch_and_aggregate(code)

            if not agg:
                skipped += 1
            else:
                for pos, stats in agg.items():
                    existing = (
                        db.query(MedicareUtilization)
                        .filter_by(hcpcs_code=code, place_of_service=pos)
                        .first()
                    )

                    if existing:
                        for key, val in stats.items():
                            setattr(existing, key, val)
                        existing.source_year = SOURCE_YEAR
                        updated += 1
                    else:
                        record = MedicareUtilization(
                            hcpcs_code=code,
                            place_of_service=pos,
                            source_year=SOURCE_YEAR,
                            **stats,
                        )
                        db.add(record)
                        inserted += 1

            processed += 1

            if processed % UTILIZATION_BATCH_SIZE == 0:
                db.flush()
                pct = processed * 100 // total_codes
                print(f"  [{pct}%] Processed {processed}/{total_codes} codes "
                      f"({inserted} new, {updated} updated, {skipped} no data)", flush=True)

            time.sleep(UTILIZATION_API_DELAY)

        db.commit()
        print(f"  Done: {processed} codes processed, {inserted} inserted, "
              f"{updated} updated, {skipped} no data")
        complete_sync(db, log, processed, inserted, updated)

    except Exception as e:
        db.rollback()
        fail_sync(db, log, str(e))
        print(f"  ERROR: {e}")
        raise

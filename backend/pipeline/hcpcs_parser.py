"""
Source 2: HCPCS Level II codes from NIH Clinical Tables API.

Paginates through all active HCPCS Level II codes (supplies, DME, drugs)
and inserts them into the `hcpcs_codes` table.

The NLM API requires a non-empty search term for proper pagination,
so we iterate by 2-character prefix (A0-A9, B0-B9, ..., V0-V9).
"""

import time
import requests
from models import HcpcsCode
from .config import HCPCS_API_URL, HCPCS_BATCH_SIZE, SOURCE_YEAR, get_category_for_code
from .sync_log import is_sync_current, start_sync, complete_sync, fail_sync

# HCPCS Level II prefixes: A, B, C, D, E, G, H, J, K, L, M, P, Q, R, S, T, U, V
HCPCS_PREFIXES = "A B C D E G H J K L M P Q R S T U V".split()


def _fetch_prefix(prefix: str, batch_size: int = 500) -> list:
    """Fetch all codes for a given 2-char prefix from the NLM API."""
    all_codes = []
    offset = 0

    while True:
        params = {
            "terms": prefix,
            "maxList": batch_size,
            "offset": offset,
            "df": "code,display",
            "ef": "short_desc,long_desc,add_dt,term_dt",
        }

        resp = requests.get(HCPCS_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        total_count = data[0]
        codes = data[1]
        extra = data[2] or {}

        if not codes:
            break

        short_descs = extra.get("short_desc", [])
        long_descs = extra.get("long_desc", [])
        add_dates = extra.get("add_dt", [])
        term_dates = extra.get("term_dt", [])

        for i, code in enumerate(codes):
            all_codes.append({
                "code": code,
                "short_desc": short_descs[i] if i < len(short_descs) else None,
                "long_desc": long_descs[i] if i < len(long_descs) else None,
                "add_date": add_dates[i] if i < len(add_dates) else None,
                "term_date": term_dates[i] if i < len(term_dates) else None,
            })

        offset += batch_size
        if offset >= total_count:
            break

        time.sleep(0.1)

    return all_codes


def sync_hcpcs_data(db, force=False):
    """Fetch all active HCPCS Level II codes from the NLM API."""

    if not force and is_sync_current(db, "hcpcs", max_age_days=30):
        print("  HCPCS data is current (synced within 30 days). Use --force to re-import.")
        return

    log = start_sync(db, "hcpcs", HCPCS_API_URL)
    try:
        inserted = 0
        updated = 0
        seen = set()

        for letter in HCPCS_PREFIXES:
            # Iterate digit suffixes: A0, A1, ..., A9
            for digit in range(10):
                prefix = f"{letter}{digit}"
                codes = _fetch_prefix(prefix)

                for item in codes:
                    code = item["code"]
                    if code in seen:
                        continue
                    seen.add(code)

                    # Skip terminated codes
                    if item["term_date"]:
                        continue

                    category = get_category_for_code(code)

                    existing = db.query(HcpcsCode).filter_by(hcpcs_code=code).first()
                    if existing:
                        existing.short_desc = item["short_desc"]
                        existing.long_desc = item["long_desc"]
                        existing.add_date = item["add_date"]
                        existing.category = category
                        existing.source_year = SOURCE_YEAR
                        updated += 1
                    else:
                        record = HcpcsCode(
                            hcpcs_code=code,
                            short_desc=item["short_desc"],
                            long_desc=item["long_desc"],
                            add_date=item["add_date"],
                            term_date=item["term_date"],
                            category=category,
                            source_year=SOURCE_YEAR,
                        )
                        db.add(record)
                        inserted += 1

                db.flush()
                time.sleep(0.1)

            total = inserted + updated
            print(f"  Prefix {letter}: {total} codes so far ({inserted} new, {updated} updated)", flush=True)

        db.commit()
        total = inserted + updated
        print(f"  Done: {total} processed, {inserted} inserted, {updated} updated")
        complete_sync(db, log, total, inserted, updated)

    except Exception as e:
        db.rollback()
        fail_sync(db, log, str(e))
        print(f"  ERROR: {e}")
        raise

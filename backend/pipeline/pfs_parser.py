"""
Source 1: Medicare Physician Fee Schedule (PFS) RVU file parser.

Downloads the CMS PFS RVU ZIP, extracts the CSV (PPRRVU*_nonQPP.csv),
skips the 9-line preamble, and upserts national-rate rows into `procedures`.

CSV column layout (row 10 is the header):
  HCPCS, MOD, DESCRIPTION, CODE (status), PAYMENT (not used for medicare),
  RVU (work), PE RVU (non-fac), INDICATOR, PE RVU (fac), INDICATOR,
  RVU (mp), TOTAL (non-fac), TOTAL (fac), IND (pctc), DAYS (glob),
  ... (several surgery/indicator cols) ...,
  FACTOR (conv), ... , AMOUNT (non-fac), AMOUNT (fac), AMOUNT (last)
"""

import csv
import os
from models import Procedure
from .config import PFS_ZIP_URL, SOURCE_YEAR, PIPELINE_DIR, get_category_for_code
from .downloader import download_and_extract, compute_file_hash, ensure_dir
from .sync_log import is_hash_current, start_sync, complete_sync, fail_sync

# Number of preamble lines before the actual column header in the CSV
PREAMBLE_LINES = 9


def _find_pfs_csv(extracted_paths: list) -> str:
    """Find the PPRRVU*_nonQPP.csv file in the extracted archive."""
    for p in extracted_paths:
        name = os.path.basename(p).upper()
        if "PPRRVU" in name and "NONQPP" in name and name.endswith(".CSV"):
            return p
    # Fallback: any PPRRVU CSV
    for p in extracted_paths:
        name = os.path.basename(p).upper()
        if "PPRRVU" in name and name.endswith(".CSV"):
            return p
    raise FileNotFoundError(
        f"No PPRRVU CSV found. Files: {[os.path.basename(p) for p in extracted_paths]}"
    )


def _parse_float(val: str) -> float:
    if not val or val.strip() in ("", "NA", "#"):
        return 0.0
    try:
        return float(val.strip())
    except ValueError:
        return 0.0


def sync_pfs_data(db, force=False):
    """Download and parse the CMS PFS RVU CSV into the procedures table."""
    dest_dir = ensure_dir(os.path.join(PIPELINE_DIR, "pfs"))

    log = start_sync(db, "pfs", PFS_ZIP_URL)
    try:
        extracted = download_and_extract(PFS_ZIP_URL, dest_dir)
        pfs_csv = _find_pfs_csv(extracted)
        file_hash = compute_file_hash(pfs_csv)

        if not force and is_hash_current(db, "pfs", file_hash):
            print("  PFS data is already current (same file hash). Use --force to re-import.")
            complete_sync(db, log, records_processed=0, source_hash=file_hash)
            return

        print(f"  Parsing {os.path.basename(pfs_csv)} ...")

        inserted = 0
        updated = 0
        processed = 0
        seen = set()

        with open(pfs_csv, "r", encoding="utf-8", errors="replace") as f:
            # Skip the preamble (copyright notices, blank rows, multi-line headers)
            for _ in range(PREAMBLE_LINES):
                next(f)

            reader = csv.reader(f)
            # Row 10 is the actual column header
            header = next(reader)
            header = [h.strip().upper() for h in header]

            # Build index map. The CMS CSV has a known fixed layout:
            # 0:HCPCS, 1:MOD, 2:DESCRIPTION, 3:CODE(status), 4:PAYMENT,
            # 5:RVU(work), 6:PE RVU(non-fac), 7:INDICATOR, 8:PE RVU(fac),
            # 9:INDICATOR, 10:RVU(mp), 11:TOTAL(non-fac), 12:TOTAL(fac),
            # 13:IND(pctc), 14:DAYS(glob), ... , 25:FACTOR(conv), ...
            # The last 3 columns are: NON-FACILITY AMOUNT, FACILITY AMOUNT, AMOUNT
            #
            # We'll use position-based parsing since column names repeat.
            COL_HCPCS = 0
            COL_MOD = 1
            COL_DESC = 2
            COL_STATUS = 3
            COL_WORK_RVU = 5
            COL_NF_PE_RVU = 6
            COL_FAC_PE_RVU = 8
            COL_MP_RVU = 10
            COL_TOTAL_NF = 11
            COL_TOTAL_FAC = 12
            COL_PCTC = 13
            COL_GLOB = 14

            # Find conversion factor and fee columns by scanning header
            # FACTOR usually at 25, fees at end (29, 30, 31)
            col_conv = None
            for i, h in enumerate(header):
                if h == "FACTOR":
                    col_conv = i
                    break

            # Fee amounts are the last 3 columns: non-fac, fac, (opps amount)
            total_cols = len(header)
            col_nf_fee = total_cols - 3  # NON-FACILITY AMOUNT
            col_fac_fee = total_cols - 2  # FACILITY AMOUNT

            print(f"  Header has {total_cols} columns. Conv factor at col {col_conv}.")

            for row in reader:
                if len(row) < 15:
                    continue

                hcpcs = row[COL_HCPCS].strip()
                mod = row[COL_MOD].strip()
                desc = row[COL_DESC].strip()

                if not hcpcs or not desc:
                    continue

                key = (hcpcs, mod)
                if key in seen:
                    continue
                seen.add(key)

                work_rvu = _parse_float(row[COL_WORK_RVU])
                nf_pe_rvu = _parse_float(row[COL_NF_PE_RVU])
                fac_pe_rvu = _parse_float(row[COL_FAC_PE_RVU])
                mp_rvu = _parse_float(row[COL_MP_RVU])
                total_nf = _parse_float(row[COL_TOTAL_NF])
                total_fac = _parse_float(row[COL_TOTAL_FAC])
                glob = row[COL_GLOB].strip() if COL_GLOB < len(row) else ""
                conv = _parse_float(row[col_conv]) if col_conv and col_conv < len(row) else 0.0

                # The CSV AMOUNT columns are often 0.00; compute fees from RVUs
                csv_nf_fee = _parse_float(row[col_nf_fee]) if col_nf_fee < len(row) else 0.0
                csv_fac_fee = _parse_float(row[col_fac_fee]) if col_fac_fee < len(row) else 0.0
                nf_fee = csv_nf_fee if csv_nf_fee > 0 else (round(total_nf * conv, 2) if total_nf > 0 and conv > 0 else 0.0)
                fac_fee = csv_fac_fee if csv_fac_fee > 0 else (round(total_fac * conv, 2) if total_fac > 0 and conv > 0 else 0.0)

                category = get_category_for_code(hcpcs)

                # Compute typical cash-pay range from the fee
                base = nf_fee if nf_fee > 0 else fac_fee
                typical_low = round(base * 1.5, 2) if base > 0 else None
                typical_high = round(base * 4.0, 2) if base > 0 else None

                existing = (
                    db.query(Procedure)
                    .filter_by(cpt_code=hcpcs, modifier=mod)
                    .first()
                )

                fields = dict(
                    description=desc,
                    category=category,
                    medicare_rate=nf_fee if nf_fee > 0 else (fac_fee or None),
                    typical_low=typical_low,
                    typical_high=typical_high,
                    work_rvu=work_rvu or None,
                    non_fac_pe_rvu=nf_pe_rvu or None,
                    fac_pe_rvu=fac_pe_rvu or None,
                    mp_rvu=mp_rvu or None,
                    total_non_fac_rvu=total_nf or None,
                    total_fac_rvu=total_fac or None,
                    non_fac_fee=nf_fee or None,
                    fac_fee=fac_fee or None,
                    conversion_factor=conv or None,
                    global_period=glob or None,
                    source="cms_pfs",
                    source_year=SOURCE_YEAR,
                )

                if existing:
                    for k, v in fields.items():
                        setattr(existing, k, v)
                    updated += 1
                else:
                    proc = Procedure(cpt_code=hcpcs, modifier=mod, **fields)
                    db.add(proc)
                    inserted += 1

                processed += 1
                if processed % 2000 == 0:
                    db.flush()
                    print(f"  Processed {processed} codes ...", flush=True)

        db.commit()
        print(f"  Done: {processed} processed, {inserted} inserted, {updated} updated")
        complete_sync(db, log, processed, inserted, updated, file_hash)

    except Exception as e:
        db.rollback()
        fail_sync(db, log, str(e))
        print(f"  ERROR: {e}")
        raise

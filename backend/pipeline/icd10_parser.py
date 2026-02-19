"""
Source 3: ICD-10-PCS procedure codes from the CMS annual release.

Downloads the CMS ZIP file, extracts the fixed-width order file, and
inserts billable codes into the `icd10_procedures` table.
"""

import os
from models import Icd10Procedure
from .config import ICD10_ZIP_URL, SOURCE_YEAR, PIPELINE_DIR
from .downloader import download_and_extract, compute_file_hash, ensure_dir
from .sync_log import is_hash_current, start_sync, complete_sync, fail_sync


def _find_order_file(extracted_paths: list) -> str:
    """Find the ICD-10-PCS order file in the extracted archive."""
    for p in extracted_paths:
        name = os.path.basename(p).lower()
        if "order" in name and name.endswith(".txt"):
            return p
    # Fallback: any .txt file
    for p in extracted_paths:
        if p.lower().endswith(".txt"):
            return p
    raise FileNotFoundError(f"No order TXT file found in: {extracted_paths}")


def _parse_fixed_width_line(line: str) -> dict:
    """
    Parse a single line from the ICD-10-PCS fixed-width order file.

    Layout:
      Pos 1-5:   Order number (right-justified, zero-padded)
      Pos 6:     Space
      Pos 7-13:  ICD-10-PCS code (7 chars)
      Pos 14:    Space
      Pos 15:    Valid code flag (0 or 1)
      Pos 16:    Space
      Pos 17-76: Short description (60 chars, space-padded)
      Pos 77:    Space
      Pos 78+:   Long description (to end of line)
    """
    if len(line) < 20:
        return None

    try:
        order_num = int(line[0:5].strip())
    except ValueError:
        return None

    code = line[6:13].strip()
    valid_flag = line[14:15].strip()
    short_desc = line[16:76].strip()
    long_desc = line[77:].strip() if len(line) > 77 else ""

    return {
        "order_num": order_num,
        "code": code,
        "is_billable": valid_flag == "1",
        "short_desc": short_desc,
        "long_desc": long_desc,
    }


def sync_icd10_data(db, force=False):
    """Download and parse ICD-10-PCS codes into the icd10_procedures table."""
    dest_dir = ensure_dir(os.path.join(PIPELINE_DIR, "icd10"))

    log = start_sync(db, "icd10", ICD10_ZIP_URL)
    try:
        extracted = download_and_extract(ICD10_ZIP_URL, dest_dir)
        order_file = _find_order_file(extracted)
        file_hash = compute_file_hash(order_file)

        if not force and is_hash_current(db, "icd10", file_hash):
            print("  ICD-10-PCS data is already current. Use --force to re-import.")
            complete_sync(db, log, records_processed=0, source_hash=file_hash)
            return

        print(f"  Parsing {os.path.basename(order_file)} ...")

        inserted = 0
        updated = 0
        processed = 0
        batch = []

        with open(order_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                parsed = _parse_fixed_width_line(line)
                if not parsed or not parsed["code"]:
                    continue

                # Only store billable codes
                if not parsed["is_billable"]:
                    continue

                existing = db.query(Icd10Procedure).filter_by(icd10_code=parsed["code"]).first()
                if existing:
                    existing.short_desc = parsed["short_desc"]
                    existing.long_desc = parsed["long_desc"]
                    existing.order_num = parsed["order_num"]
                    existing.source_year = SOURCE_YEAR
                    updated += 1
                else:
                    record = Icd10Procedure(
                        icd10_code=parsed["code"],
                        short_desc=parsed["short_desc"],
                        long_desc=parsed["long_desc"],
                        order_num=parsed["order_num"],
                        is_billable=True,
                        source_year=SOURCE_YEAR,
                    )
                    db.add(record)
                    inserted += 1

                processed += 1
                if processed % 5000 == 0:
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

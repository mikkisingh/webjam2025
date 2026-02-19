"""Pipeline configuration — URLs, constants, category mappings."""

import os

# ── Download URLs ─────────────────────────────────────────────
PFS_ZIP_URL = "https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip"
ICD10_ZIP_URL = "https://www.cms.gov/files/zip/2026-icd-10-pcs-order-file-long-and-abbreviated-titles.zip"
HCPCS_API_URL = "https://clinicaltables.nlm.nih.gov/api/hcpcs/v3/search"
UTILIZATION_API_URL = (
    "https://data.cms.gov/data-api/v1/dataset/"
    "92396110-2aed-4d63-a6a2-5d6207d46a29/data"
)

# ── File paths ────────────────────────────────────────────────
PIPELINE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline_data")

# ── Batch / rate-limit settings ───────────────────────────────
HCPCS_BATCH_SIZE = 500
HCPCS_MAX_OFFSET = 10000
UTILIZATION_BATCH_SIZE = 50
UTILIZATION_API_DELAY = 0.5   # seconds between CMS API calls
DOWNLOAD_TIMEOUT = 120        # seconds

SOURCE_YEAR = 2026

# ── CPT category mapping (numeric HCPCS ranges) ──────────────
# Based on CPT code structure from the AMA / CMS
CATEGORY_RANGES = [
    (   100,  1999, "Anesthesia"),
    ( 10004, 10021, "Surgery - General"),
    ( 10030, 19499, "Surgery - Integumentary"),
    ( 20005, 29999, "Surgery - Musculoskeletal"),
    ( 30000, 32999, "Surgery - Respiratory"),
    ( 33010, 37799, "Surgery - Cardiovascular"),
    ( 38100, 38999, "Surgery - Hemic/Lymphatic"),
    ( 39000, 39599, "Surgery - Mediastinum/Diaphragm"),
    ( 40490, 49999, "Surgery - Digestive"),
    ( 50010, 53899, "Surgery - Urinary"),
    ( 54000, 55899, "Surgery - Male Genital"),
    ( 55920, 58999, "Surgery - Female Genital"),
    ( 59000, 59899, "Surgery - Maternity"),
    ( 60000, 60699, "Surgery - Endocrine"),
    ( 61000, 64999, "Surgery - Nervous System"),
    ( 65091, 68899, "Surgery - Eye/Ocular Adnexa"),
    ( 69000, 69979, "Surgery - Auditory"),
    ( 70010, 76499, "Radiology - Diagnostic"),
    ( 76506, 76999, "Radiology - Ultrasound"),
    ( 77001, 77799, "Radiology - Radiation Oncology"),
    ( 77800, 79999, "Radiology - Nuclear Medicine"),
    ( 80047, 89398, "Laboratory / Pathology"),
    ( 90281, 90399, "Medicine - Immunizations"),
    ( 90460, 90474, "Medicine - Immunization Admin"),
    ( 90785, 90899, "Medicine - Psychiatry"),
    ( 90901, 90911, "Medicine - Biofeedback"),
    ( 90935, 90999, "Medicine - Dialysis"),
    ( 91010, 91299, "Medicine - Gastroenterology"),
    ( 92002, 92499, "Medicine - Ophthalmology"),
    ( 92502, 92700, "Medicine - Otorhinolaryngology"),
    ( 93000, 93799, "Medicine - Cardiovascular"),
    ( 93880, 93998, "Medicine - Vascular Studies"),
    ( 94002, 94799, "Medicine - Pulmonary"),
    ( 95004, 95199, "Medicine - Allergy/Immunology"),
    ( 95249, 95999, "Medicine - Neurology"),
    ( 96040, 96170, "Medicine - Genetics"),
    ( 96360, 96549, "Medicine - Chemotherapy"),
    ( 96567, 96571, "Medicine - Photodynamic Therapy"),
    ( 96900, 96999, "Medicine - Dermatology"),
    ( 97010, 97799, "Medicine - Physical Therapy"),
    ( 97802, 97804, "Medicine - Nutrition Therapy"),
    ( 98925, 98929, "Medicine - Osteopathic"),
    ( 98940, 98943, "Medicine - Chiropractic"),
    ( 99024, 99091, "Medicine - Special Services"),
    ( 99100, 99140, "Medicine - Anesthesia Qualifying"),
    ( 99151, 99199, "Medicine - Moderate Sedation"),
    ( 99201, 99499, "Evaluation & Management"),
]


def get_category_for_code(hcpcs_code: str) -> str:
    """Map a numeric HCPCS/CPT code to a category."""
    try:
        num = int(hcpcs_code)
    except ValueError:
        # Non-numeric codes (A, B, C, E, G, etc.) are HCPCS Level II
        prefix = hcpcs_code[0].upper() if hcpcs_code else ""
        return {
            "A": "HCPCS - Supplies",
            "B": "HCPCS - Enteral/Parenteral",
            "C": "HCPCS - Outpatient PPS",
            "D": "HCPCS - Dental",
            "E": "HCPCS - DME",
            "G": "HCPCS - Procedures/Services",
            "H": "HCPCS - Behavioral Health",
            "J": "HCPCS - Drugs",
            "K": "HCPCS - DME (Temporary)",
            "L": "HCPCS - Orthotics/Prosthetics",
            "M": "HCPCS - Quality Measures",
            "P": "HCPCS - Laboratory",
            "Q": "HCPCS - Temporary Codes",
            "R": "HCPCS - Diagnostic Radiology",
            "S": "HCPCS - Private Payer",
            "T": "HCPCS - State Medicaid",
            "U": "HCPCS - Coronavirus",
            "V": "HCPCS - Vision/Hearing",
        }.get(prefix, "Other")

    for lo, hi, cat in CATEGORY_RANGES:
        if lo <= num <= hi:
            return cat
    return "Other"

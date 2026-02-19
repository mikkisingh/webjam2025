"""
Seed the 'procedures' table with common CPT codes.

Prices are based on 2024 CMS Medicare Physician Fee Schedule
non-facility national averages (public domain data).

Typical cash ranges are approximate 25th–75th percentile estimates
derived from FAIR Health benchmark data and hospital price transparency
reports. Actual prices vary significantly by location and provider.

Run once:
  cd backend && python seed_procedures.py
"""

from database import Base, engine, SessionLocal
from models import Procedure

# fmt: off
PROCEDURES = [
    # ── Evaluation & Management — Office Visits ──────────────────
    ("99202", "Office visit, new patient, low complexity",               "Office Visits",   75,    120,   280),
    ("99203", "Office visit, new patient, moderate complexity",          "Office Visits",  112,    180,   380),
    ("99204", "Office visit, new patient, moderate-high complexity",     "Office Visits",  167,    265,   520),
    ("99205", "Office visit, new patient, high complexity",              "Office Visits",  211,    320,   640),
    ("99211", "Office visit, established, minimal",                      "Office Visits",   24,     35,    90),
    ("99212", "Office visit, established, low complexity",               "Office Visits",   55,     90,   210),
    ("99213", "Office visit, established, moderate complexity",          "Office Visits",  112,    150,   310),
    ("99214", "Office visit, established, moderate-high complexity",     "Office Visits",  167,    220,   420),
    ("99215", "Office visit, established, high complexity",              "Office Visits",  211,    290,   560),

    # ── Emergency Department ──────────────────────────────────────
    ("99281", "Emergency dept visit, minor problem",                     "Emergency",       37,     85,   250),
    ("99282", "Emergency dept visit, low complexity",                    "Emergency",       73,    150,   400),
    ("99283", "Emergency dept visit, moderate complexity",               "Emergency",      144,    280,   650),
    ("99284", "Emergency dept visit, high complexity",                   "Emergency",      238,    420,   900),
    ("99285", "Emergency dept visit, highest complexity",                "Emergency",      337,    600,  1400),

    # ── Preventive / Wellness ─────────────────────────────────────
    ("99385", "Annual wellness exam, new patient, 18–39",                "Preventive",     169,    200,   420),
    ("99386", "Annual wellness exam, new patient, 40–64",                "Preventive",     195,    230,   480),
    ("99387", "Annual wellness exam, new patient, 65+",                  "Preventive",     225,    260,   530),
    ("99395", "Annual wellness exam, established, 18–39",               "Preventive",     144,    180,   380),
    ("99396", "Annual wellness exam, established, 40–64",               "Preventive",     170,    210,   430),
    ("99397", "Annual wellness exam, established, 65+",                 "Preventive",     195,    240,   490),

    # ── Laboratory ───────────────────────────────────────────────
    ("36415", "Blood draw (venipuncture)",                               "Laboratory",      10,     20,    80),
    ("80048", "Basic metabolic panel (BMP)",                             "Laboratory",      12,     30,   120),
    ("80053", "Comprehensive metabolic panel (CMP)",                     "Laboratory",      14,     35,   150),
    ("80061", "Lipid panel (cholesterol)",                               "Laboratory",      20,     40,   150),
    ("82947", "Blood glucose",                                           "Laboratory",       8,     20,    80),
    ("83036", "Hemoglobin A1c (HbA1c)",                                 "Laboratory",      13,     30,   130),
    ("83721", "LDL cholesterol",                                         "Laboratory",      17,     35,   120),
    ("84443", "TSH (thyroid stimulating hormone)",                       "Laboratory",      24,     45,   180),
    ("84484", "Troponin quantitative",                                   "Laboratory",      22,     50,   200),
    ("85025", "CBC with differential",                                   "Laboratory",      10,     30,   130),
    ("85027", "CBC without differential",                                "Laboratory",       8,     25,   100),
    ("86140", "C-reactive protein (CRP)",                                "Laboratory",      11,     25,   100),
    ("86900", "Blood typing (ABO)",                                      "Laboratory",      10,     20,    80),
    ("87040", "Blood culture",                                           "Laboratory",      15,     40,   180),
    ("87086", "Urine culture",                                           "Laboratory",      12,     30,   130),
    ("87880", "Rapid strep test",                                        "Laboratory",      20,     30,   100),
    ("81001", "Urinalysis with microscopy",                              "Laboratory",       5,     15,    60),
    ("81003", "Urinalysis automated",                                    "Laboratory",       4,     12,    50),
    ("82270", "Fecal occult blood test",                                 "Laboratory",       6,     15,    60),
    ("87804", "Rapid influenza antigen test",                            "Laboratory",      20,     35,   110),
    ("87426", "COVID-19 antigen test",                                   "Laboratory",      20,     40,   120),

    # ── Radiology — X-ray ─────────────────────────────────────────
    ("71046", "Chest X-ray, 2 views",                                    "Radiology",       32,     80,   350),
    ("71048", "Chest X-ray, 4+ views",                                   "Radiology",       44,    110,   480),
    ("72100", "Lumbar spine X-ray, 2–3 views",                          "Radiology",       44,    100,   420),
    ("72110", "Lumbar spine X-ray, minimum 4 views",                    "Radiology",       56,    130,   560),
    ("73030", "Shoulder X-ray, minimum 2 views",                        "Radiology",       36,     90,   380),
    ("73070", "Elbow X-ray, 2 views",                                    "Radiology",       34,     80,   320),
    ("73100", "Wrist X-ray, 2 views",                                    "Radiology",       34,     80,   320),
    ("73120", "Hand X-ray, 2 views",                                     "Radiology",       34,     80,   320),
    ("73600", "Ankle X-ray, 2 views",                                    "Radiology",       34,     80,   320),
    ("73620", "Foot X-ray, 2 views",                                     "Radiology",       34,     80,   320),
    ("73650", "Heel (os calcis) X-ray, minimum 2 views",               "Radiology",       34,     80,   320),
    ("73660", "Toe X-ray, minimum 2 views",                             "Radiology",       32,     75,   300),
    ("70210", "Sinus X-ray, less than 3 views",                        "Radiology",       30,     75,   300),

    # ── Radiology — CT Scans ──────────────────────────────────────
    ("70450", "CT head/brain without contrast",                          "Radiology",      224,    500,  2200),
    ("70460", "CT head/brain with contrast",                             "Radiology",      272,    600,  2600),
    ("70470", "CT head/brain with and without contrast",                "Radiology",      316,    700,  3000),
    ("71250", "CT thorax (chest) without contrast",                      "Radiology",      250,    550,  2400),
    ("71260", "CT thorax (chest) with contrast",                         "Radiology",      298,    650,  2800),
    ("72125", "CT cervical spine without contrast",                      "Radiology",      246,    540,  2300),
    ("72131", "CT lumbar spine without contrast",                        "Radiology",      246,    540,  2300),
    ("74177", "CT abdomen and pelvis with contrast",                     "Radiology",      366,    800,  3500),
    ("74178", "CT abdomen and pelvis with and without contrast",        "Radiology",      414,    900,  3900),
    ("74176", "CT abdomen and pelvis without contrast",                  "Radiology",      310,    680,  3000),
    ("75571", "CT heart for calcium scoring",                            "Radiology",      160,    350,  1400),

    # ── Radiology — MRI ───────────────────────────────────────────
    ("70553", "MRI brain with and without contrast",                    "Radiology",      424,   1000,  4500),
    ("70552", "MRI brain with contrast",                                 "Radiology",      380,    900,  4200),
    ("70551", "MRI brain without contrast",                              "Radiology",      312,    750,  3500),
    ("72141", "MRI cervical spine without contrast",                     "Radiology",      314,    750,  3500),
    ("72148", "MRI lumbar spine without contrast",                       "Radiology",      314,    750,  3500),
    ("72149", "MRI lumbar spine with contrast",                          "Radiology",      362,    850,  4000),
    ("72158", "MRI lumbar spine with and without contrast",             "Radiology",      422,   1000,  4500),
    ("73221", "MRI shoulder without contrast",                           "Radiology",      320,    750,  3500),
    ("73223", "MRI shoulder with and without contrast",                 "Radiology",      420,   1000,  4500),
    ("73721", "MRI knee without contrast",                               "Radiology",      320,    750,  3500),
    ("73723", "MRI knee with and without contrast",                     "Radiology",      420,   1000,  4500),
    ("73718", "MRI lower extremity without contrast",                    "Radiology",      320,    750,  3500),

    # ── Radiology — Ultrasound ────────────────────────────────────
    ("76700", "Ultrasound abdomen, complete",                            "Radiology",      120,    280,  1200),
    ("76705", "Ultrasound abdomen, limited",                             "Radiology",       90,    210,   900),
    ("76801", "Obstetric ultrasound < 14 weeks",                        "Radiology",      120,    280,  1100),
    ("76805", "Obstetric ultrasound ≥ 14 weeks",                        "Radiology",      130,    300,  1200),
    ("76856", "Pelvic ultrasound, complete",                             "Radiology",      120,    280,  1100),
    ("93306", "Echocardiography, complete with Doppler",                "Radiology",      250,    600,  2500),

    # ── Cardiology ────────────────────────────────────────────────
    ("93000", "ECG (EKG) with interpretation",                           "Cardiology",      18,     50,   250),
    ("93005", "ECG tracing only",                                        "Cardiology",      11,     30,   150),
    ("93010", "ECG interpretation only",                                 "Cardiology",       8,     20,   100),
    ("93015", "Exercise stress test (treadmill)",                        "Cardiology",     124,    350,  1500),
    ("93017", "Stress test, tracing only",                               "Cardiology",      82,    200,   900),
    ("93350", "Stress echocardiography",                                 "Cardiology",     287,    700,  3000),
    ("93880", "Carotid duplex scan, bilateral",                         "Cardiology",     132,    350,  1500),
    ("93970", "Venous duplex scan, bilateral",                           "Cardiology",     145,    380,  1600),
    ("93971", "Venous duplex scan, unilateral",                         "Cardiology",      89,    230,   950),

    # ── Gastroenterology / GI ────────────────────────────────────
    ("43235", "Upper endoscopy (EGD), diagnostic",                      "Gastroenterology", 210,  600,  2800),
    ("43239", "Upper endoscopy (EGD) with biopsy",                      "Gastroenterology", 245,  700,  3200),
    ("45378", "Colonoscopy, diagnostic",                                  "Gastroenterology", 320,  900,  4000),
    ("45380", "Colonoscopy with biopsy",                                 "Gastroenterology", 370, 1000,  4500),
    ("45385", "Colonoscopy with polypectomy",                            "Gastroenterology", 390, 1100,  4800),

    # ── Mental Health ─────────────────────────────────────────────
    ("90791", "Psychiatric diagnostic evaluation",                       "Mental Health",   145,    250,   600),
    ("90832", "Psychotherapy, 30 minutes",                               "Mental Health",    83,    120,   300),
    ("90834", "Psychotherapy, 45 minutes",                               "Mental Health",   112,    160,   380),
    ("90837", "Psychotherapy, 60 minutes",                               "Mental Health",   152,    200,   450),
    ("90847", "Family psychotherapy with patient",                       "Mental Health",   136,    190,   430),
    ("96130", "Psychological testing evaluation, first hour",           "Mental Health",   103,    200,   500),

    # ── Orthopedics / Surgery ─────────────────────────────────────
    ("27447", "Total knee arthroplasty (professional fee)",              "Orthopedics",    900,   1800,  5000),
    ("27130", "Total hip arthroplasty (professional fee)",               "Orthopedics",    900,   1900,  5200),
    ("29827", "Arthroscopy, shoulder with rotator cuff repair",         "Orthopedics",    730,   1800,  6000),
    ("29881", "Arthroscopy, knee with meniscectomy",                    "Orthopedics",    540,   1400,  5500),
    ("28296", "Bunionectomy",                                            "Orthopedics",    590,   1300,  4500),
    ("25600", "Closed treatment, distal radial fracture",               "Orthopedics",    210,    480,  1800),

    # ── Gynecology & Obstetrics ───────────────────────────────────
    ("99213", "OB/GYN office visit (established)",                       "OB/GYN",        112,    150,   310),
    ("58300", "IUD insertion",                                           "OB/GYN",        108,    200,   800),
    ("58301", "IUD removal",                                             "OB/GYN",         90,    175,   700),
    ("57452", "Colposcopy",                                              "OB/GYN",        132,    280,  1100),
    ("59400", "Routine obstetric care (global package)",                 "OB/GYN",       1960,   3500, 12000),
    ("59510", "Cesarean delivery, routine (global)",                     "OB/GYN",       2440,   4500, 16000),

    # ── Dermatology ───────────────────────────────────────────────
    ("11300", "Shave removal, benign lesion, <0.5 cm",                  "Dermatology",     77,    150,   450),
    ("11400", "Excision, benign lesion, <0.5 cm",                       "Dermatology",    120,    220,   700),
    ("11600", "Excision, malignant lesion, <0.5 cm",                    "Dermatology",    197,    350,  1100),
    ("17000", "Destruction, premalignant lesion, first",                "Dermatology",     55,    100,   350),
    ("17110", "Destruction, flat warts, up to 14",                      "Dermatology",     82,    150,   500),

    # ── Ophthalmology ─────────────────────────────────────────────
    ("92004", "Eye exam, new patient, comprehensive",                    "Ophthalmology",  120,    180,   420),
    ("92014", "Eye exam, established, comprehensive",                    "Ophthalmology",   88,    130,   310),
    ("92025", "Corneal topography",                                      "Ophthalmology",   53,    120,   400),
    ("92250", "Fundus photography with interpretation",                  "Ophthalmology",   51,    115,   380),
    ("66984", "Cataract removal with lens implant",                      "Ophthalmology",  600,   1200,  3500),

    # ── Physical / Occupational Therapy ──────────────────────────
    ("97010", "Hot/cold packs",                                          "Physical Therapy",  15,   30,   120),
    ("97012", "Mechanical traction",                                     "Physical Therapy",  25,   50,   200),
    ("97014", "Electrical stimulation",                                  "Physical Therapy",  24,   45,   180),
    ("97035", "Ultrasound therapy",                                      "Physical Therapy",  25,   50,   200),
    ("97110", "Therapeutic exercises",                                   "Physical Therapy",  31,   70,   280),
    ("97140", "Manual therapy",                                          "Physical Therapy",  36,   80,   320),
    ("97530", "Therapeutic activities",                                  "Physical Therapy",  35,   80,   320),
    ("97161", "PT evaluation, low complexity",                           "Physical Therapy",  96,  150,   400),
    ("97162", "PT evaluation, moderate complexity",                      "Physical Therapy", 117,  180,   460),
    ("97163", "PT evaluation, high complexity",                          "Physical Therapy", 136,  210,   520),

    # ── Anesthesia ────────────────────────────────────────────────
    ("00100", "Anesthesia, head, minor procedures",                      "Anesthesia",     300,   600,  2500),
    ("00400", "Anesthesia, integumentary system",                       "Anesthesia",     300,   600,  2500),
    ("00840", "Anesthesia, intraperitoneal procedure",                  "Anesthesia",     550,  1200,  5000),
    ("00868", "Anesthesia, renal procedure",                             "Anesthesia",     550,  1200,  5000),

    # ── Injections / Infusions ────────────────────────────────────
    ("20610", "Joint injection (large joint, e.g. knee)",               "Injections",      75,    150,   600),
    ("20605", "Joint injection (intermediate joint, e.g. elbow)",      "Injections",      63,    120,   480),
    ("20600", "Joint injection (small joint, e.g. finger)",            "Injections",      55,    100,   380),
    ("64483", "Epidural steroid injection, lumbar",                     "Injections",     424,    900,  3500),
    ("64490", "Paravertebral facet joint injection, cervical",         "Injections",     310,    700,  2800),
    ("96365", "IV infusion, first hour (therapeutic)",                  "Injections",      92,    200,   900),
    ("96372", "Therapeutic injection (IM or SQ)",                       "Injections",      25,     50,   200),

    # ── Preventive Screenings ─────────────────────────────────────
    ("G0101", "Cervical/vaginal cancer screening",                       "Preventive",      47,     80,   250),
    ("G0102", "Prostate cancer screening (PSA discussion)",             "Preventive",      25,     40,   120),
    ("G0121", "Colorectal cancer screening, colonoscopy",               "Preventive",     320,    900,  4000),
    ("G0202", "Screening mammography",                                   "Preventive",      74,    150,   600),
    ("G0204", "Diagnostic mammography",                                  "Preventive",      94,    200,   800),
    ("G0206", "Diagnostic mammography, additional views",               "Preventive",     111,    240,   950),
    ("G0296", "Counseling, lung cancer screening",                       "Preventive",      32,     50,   150),
    ("G0444", "Annual depression screening",                             "Preventive",      18,     30,    90),
    ("G0446", "Annual wellness visit, intensive behavioral counseling", "Preventive",      40,     70,   200),

    # ── Vaccination / Immunization ────────────────────────────────
    ("90471", "Immunization administration, first injection",           "Vaccination",      22,     40,   150),
    ("90472", "Immunization administration, each additional",           "Vaccination",      16,     30,   100),
    ("90686", "Influenza vaccine, quadrivalent",                        "Vaccination",      20,     35,   120),
    ("90670", "Pneumococcal vaccine (PCV13)",                           "Vaccination",     110,    200,   600),
    ("90714", "Tetanus toxoid (Td)",                                    "Vaccination",      25,     45,   150),
    ("90716", "Varicella virus vaccine",                                "Vaccination",     110,    200,   600),
    ("90734", "Meningococcal vaccine",                                  "Vaccination",     130,    250,   800),
    ("90746", "Hepatitis B vaccine, adult",                             "Vaccination",      35,     65,   220),
    ("90750", "Zoster vaccine (Shingrix), each dose",                  "Vaccination",     180,    350,  1000),
]
# fmt: on


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing = db.query(Procedure).count()
    if existing > 0:
        print(f"Already seeded ({existing} procedures). Delete app.db and re-run to reseed.")
        db.close()
        return

    seen = set()
    records = []
    for cpt_code, description, category, medicare_rate, typical_low, typical_high in PROCEDURES:
        if cpt_code in seen:
            continue
        seen.add(cpt_code)
        records.append(Procedure(
            cpt_code=cpt_code,
            description=description,
            category=category,
            medicare_rate=float(medicare_rate),
            typical_low=float(typical_low),
            typical_high=float(typical_high),
        ))

    db.add_all(records)
    db.commit()
    print(f"Seeded {len(records)} procedures.")
    db.close()


if __name__ == "__main__":
    seed()

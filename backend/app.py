from flask import Flask, jsonify, request
from flask_cors import CORS
from database import Base, engine, SessionLocal
from models import Item, Procedure, HcpcsCode, Icd10Procedure, MedicareUtilization, DataSyncLog
from text_extractor import TextExtractor
from llm_service import LLMAnalyzer
import os
import requests as http_requests
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from sqlalchemy import or_, func

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

Base.metadata.create_all(bind=engine)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def root():
    return jsonify({"message": "MediCheck API - Medical Bill Analysis"})


# ──────────────────────────────────────────────────────────────
# /process  — HIPAA Option A single-step endpoint
#
# Flow: receive file → extract text → DELETE file immediately
#       → run Gemini analysis → return results
#       Nothing is persisted on this server.
# ──────────────────────────────────────────────────────────────
@app.route("/process", methods=["POST"])
def process_bill():
    filepath = None
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed. Use PDF, JPG, or PNG"}), 400

        # Save temporarily for text extraction only
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        file_type = filename.rsplit('.', 1)[1].lower()

        # Extract text
        extractor = TextExtractor()
        raw_text = extractor.extract_text(filepath, file_type)

        # ── Delete file immediately after extraction ──
        os.remove(filepath)
        filepath = None  # prevent double-deletion in finally block

        if not raw_text or not raw_text.strip():
            return jsonify({"error": "Could not extract text from this file. Try a clearer image or a text-based PDF."}), 422

        # Run full AI analysis pipeline
        analyzer = LLMAnalyzer()
        results = analyzer.analyze_bill(raw_text)

        # Return results — nothing stored server-side
        return jsonify({
            "structured_data": results['structured_data'],
            "analysis_results": results['analysis_results'],
            "summary": results['summary'],
            "complaint_email": results['complaint_email']
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Safety net: ensure file is deleted even if an error occurred mid-way
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass


# ──────────────────────────────────────────────────────────────
# /admin/promote  — grant admin role to a user by email
#
# Requires: SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
# The caller must be an authenticated admin (verified via JWT).
# ──────────────────────────────────────────────────────────────
@app.route("/admin/promote", methods=["POST"])
def admin_promote():
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    service_key  = os.getenv("SUPABASE_SERVICE_KEY", "")

    if not supabase_url or not service_key:
        return jsonify({"error": "Admin promotion not configured on this server"}), 503

    # 1. Verify caller is authenticated and is an admin
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401

    caller_jwt = auth_header.split(" ", 1)[1]
    verify_resp = http_requests.get(
        f"{supabase_url}/auth/v1/user",
        headers={"Authorization": f"Bearer {caller_jwt}", "apikey": service_key},
        timeout=10,
    )
    if verify_resp.status_code != 200:
        return jsonify({"error": "Unauthorized"}), 401

    caller = verify_resp.json()
    if caller.get("app_metadata", {}).get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    # 2. Find target user by email
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    if not email:
        return jsonify({"error": "email is required"}), 400

    list_resp = http_requests.get(
        f"{supabase_url}/auth/v1/admin/users",
        headers={"Authorization": f"Bearer {service_key}", "apikey": service_key},
        params={"filter": email},
        timeout=10,
    )
    if list_resp.status_code != 200:
        return jsonify({"error": "Failed to query users"}), 500

    users = list_resp.json().get("users", [])
    target = next((u for u in users if u.get("email") == email), None)
    if not target:
        return jsonify({"error": f"No user found with email: {email}"}), 404

    # 3. Merge admin role into target's app_metadata
    app_metadata = target.get("app_metadata") or {}
    app_metadata["role"] = "admin"

    update_resp = http_requests.put(
        f"{supabase_url}/auth/v1/admin/users/{target['id']}",
        headers={
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": "application/json",
        },
        json={"app_metadata": app_metadata},
        timeout=10,
    )
    if update_resp.status_code != 200:
        return jsonify({"error": "Failed to update user role"}), 500

    return jsonify({"success": True, "email": email}), 200


# ──────────────────────────────────────────────────────────────
# /procedures/search  — search procedure cost database
#
# Query params:
#   q        (str)  — free-text search on code or description
#   category (str)  — filter by category (optional)
#   limit    (int)  — max results, default 20, max 100
# ──────────────────────────────────────────────────────────────
@app.route("/procedures/search", methods=["GET"])
def procedures_search():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    include_utilization = request.args.get("include_utilization", "").lower() == "true"
    try:
        limit = min(int(request.args.get("limit", 20)), 100)
    except ValueError:
        limit = 20

    db = SessionLocal()
    try:
        query = db.query(Procedure).filter(Procedure.modifier == "")

        if q:
            pattern = f"%{q}%"
            query = query.filter(
                or_(
                    func.lower(Procedure.cpt_code).like(func.lower(pattern)),
                    func.lower(Procedure.description).like(func.lower(pattern)),
                    func.lower(Procedure.category).like(func.lower(pattern)),
                )
            )

        if category:
            query = query.filter(
                func.lower(Procedure.category) == category.lower()
            )

        # Sort so priced procedures appear first
        results = query.order_by(
            Procedure.medicare_rate.is_(None).asc(),
            Procedure.category,
            Procedure.cpt_code,
        ).limit(limit).all()

        items = []
        for p in results:
            item = {
                "cpt_code":      p.cpt_code,
                "description":   p.description,
                "category":      p.category,
                "medicare_rate": p.medicare_rate,
                "typical_low":   p.typical_low,
                "typical_high":  p.typical_high,
                "notes":         p.notes,
                "work_rvu":      p.work_rvu,
                "non_fac_pe_rvu": p.non_fac_pe_rvu,
                "fac_pe_rvu":    p.fac_pe_rvu,
                "mp_rvu":        p.mp_rvu,
                "total_non_fac_rvu": p.total_non_fac_rvu,
                "total_fac_rvu": p.total_fac_rvu,
                "non_fac_fee":   p.non_fac_fee,
                "fac_fee":       p.fac_fee,
                "conversion_factor": p.conversion_factor,
                "global_period": p.global_period,
                "source":        p.source,
                "source_year":   p.source_year,
            }

            if include_utilization:
                util = (
                    db.query(MedicareUtilization)
                    .filter_by(hcpcs_code=p.cpt_code, place_of_service="O")
                    .first()
                )
                if not util:
                    util = (
                        db.query(MedicareUtilization)
                        .filter_by(hcpcs_code=p.cpt_code)
                        .first()
                    )
                if util:
                    item["utilization"] = {
                        "avg_submitted_charge": util.avg_submitted_charge,
                        "avg_allowed_amount": util.avg_allowed_amount,
                        "avg_medicare_payment": util.avg_medicare_payment,
                        "p25_submitted_charge": util.p25_submitted_charge,
                        "p75_submitted_charge": util.p75_submitted_charge,
                        "total_providers": util.total_providers,
                        "total_services": util.total_services,
                        "total_beneficiaries": util.total_beneficiaries,
                    }

            items.append(item)

        return jsonify({
            "results": items,
            "count": len(items),
            "query": q,
        })
    finally:
        db.close()


@app.route("/procedures/categories", methods=["GET"])
def procedures_categories():
    """Return categories that have at least some priced procedures."""
    db = SessionLocal()
    try:
        cats = (
            db.query(
                Procedure.category,
                func.count(),
                func.sum(func.iif(Procedure.medicare_rate.isnot(None), 1, 0)),
            )
            .filter(Procedure.modifier == "")
            .group_by(Procedure.category)
            .order_by(Procedure.category)
            .all()
        )
        # Only return categories where at least 20% of codes have pricing
        return jsonify({
            "categories": [
                cat for cat, total, priced in cats
                if cat and priced and total and (priced / total) >= 0.2
            ]
        })
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────
# /providers/search  — find healthcare providers by ZIP / city
#
# Proxies the free CMS NPPES NPI Registry API so the browser
# doesn't hit CORS issues.
# https://npiregistry.cms.hhs.gov/api-page
# ──────────────────────────────────────────────────────────────
NPPES_URL = "https://npiregistry.cms.hhs.gov/api/"

@app.route("/providers/search", methods=["GET"])
def providers_search():
    zip_code  = request.args.get("zip", "").strip()
    city      = request.args.get("city", "").strip()
    state     = request.args.get("state", "").strip().upper()
    specialty = request.args.get("specialty", "").strip()

    try:
        limit = min(int(request.args.get("limit", 20)), 50)
    except ValueError:
        limit = 20

    if not zip_code and not city and not state:
        return jsonify({"error": "Provide at least a ZIP code, city, or state"}), 400

    params = {
        "version": "2.1",
        "limit":   limit,
        "enumeration_type": "NPI-1",   # individual providers only
    }
    if zip_code:
        # NPPES wants exact 5-digit or wildcard — support partial with *
        params["postal_code"] = zip_code[:5] + "*" if len(zip_code) >= 5 else zip_code + "*"
    if city:
        params["city"] = city
    if state and len(state) == 2:
        params["state"] = state
    if specialty:
        params["taxonomy_description"] = specialty

    try:
        resp = http_requests.get(NPPES_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return jsonify({"error": f"NPPES API error: {str(e)}"}), 502

    raw_results = data.get("results") or []

    providers = []
    for r in raw_results:
        basic = r.get("basic", {})
        addresses = r.get("addresses", [])
        taxonomies = r.get("taxonomies", [])

        # Use the first practice location address (location_type = PRACTICE)
        practice_addr = next(
            (a for a in addresses if a.get("address_purpose") == "LOCATION"),
            addresses[0] if addresses else {}
        )

        # Primary taxonomy
        primary_tax = next(
            (t for t in taxonomies if t.get("primary")),
            taxonomies[0] if taxonomies else {}
        )

        name_parts = []
        if basic.get("first_name"):
            name_parts.append(basic["first_name"])
        if basic.get("middle_name"):
            name_parts.append(basic["middle_name"])
        if basic.get("last_name"):
            name_parts.append(basic["last_name"])
        if basic.get("credential"):
            name_parts.append(f", {basic['credential']}")

        providers.append({
            "npi":        r.get("number"),
            "name":       " ".join(name_parts) or basic.get("organization_name", "Unknown"),
            "specialty":  primary_tax.get("desc", ""),
            "phone":      practice_addr.get("telephone_number", ""),
            "address": {
                "line1":  practice_addr.get("address_1", ""),
                "line2":  practice_addr.get("address_2", ""),
                "city":   practice_addr.get("city", ""),
                "state":  practice_addr.get("state", ""),
                "zip":    practice_addr.get("postal_code", ""),
            },
        })

    return jsonify({
        "providers": providers,
        "count":     len(providers),
        "total":     data.get("result_count", len(providers)),
    })


# ──────────────────────────────────────────────────────────────
# /hcpcs/search  — search HCPCS Level II codes (supplies/DME)
# ──────────────────────────────────────────────────────────────
@app.route("/hcpcs/search", methods=["GET"])
def hcpcs_search():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    try:
        limit = min(int(request.args.get("limit", 20)), 100)
    except ValueError:
        limit = 20

    db = SessionLocal()
    try:
        query = db.query(HcpcsCode)

        if q:
            pattern = f"%{q}%"
            query = query.filter(
                or_(
                    func.lower(HcpcsCode.hcpcs_code).like(func.lower(pattern)),
                    func.lower(HcpcsCode.short_desc).like(func.lower(pattern)),
                    func.lower(HcpcsCode.long_desc).like(func.lower(pattern)),
                )
            )

        if category:
            query = query.filter(
                func.lower(HcpcsCode.category) == category.lower()
            )

        results = query.order_by(HcpcsCode.hcpcs_code).limit(limit).all()

        return jsonify({
            "results": [
                {
                    "hcpcs_code":  h.hcpcs_code,
                    "short_desc":  h.short_desc,
                    "long_desc":   h.long_desc,
                    "category":    h.category,
                    "source_year": h.source_year,
                }
                for h in results
            ],
            "count": len(results),
            "query": q,
        })
    finally:
        db.close()


@app.route("/hcpcs/categories", methods=["GET"])
def hcpcs_categories():
    db = SessionLocal()
    try:
        cats = (
            db.query(HcpcsCode.category)
            .distinct()
            .order_by(HcpcsCode.category)
            .all()
        )
        return jsonify({"categories": [c[0] for c in cats if c[0]]})
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────
# /icd10/search  — search ICD-10-PCS procedure codes
# ──────────────────────────────────────────────────────────────
@app.route("/icd10/search", methods=["GET"])
def icd10_search():
    q = request.args.get("q", "").strip()
    try:
        limit = min(int(request.args.get("limit", 20)), 100)
    except ValueError:
        limit = 20

    db = SessionLocal()
    try:
        query = db.query(Icd10Procedure)

        if q:
            pattern = f"%{q}%"
            query = query.filter(
                or_(
                    func.lower(Icd10Procedure.icd10_code).like(func.lower(pattern)),
                    func.lower(Icd10Procedure.short_desc).like(func.lower(pattern)),
                    func.lower(Icd10Procedure.long_desc).like(func.lower(pattern)),
                )
            )

        results = query.order_by(Icd10Procedure.icd10_code).limit(limit).all()

        return jsonify({
            "results": [
                {
                    "icd10_code": i.icd10_code,
                    "short_desc": i.short_desc,
                    "long_desc":  i.long_desc,
                    "source_year": i.source_year,
                }
                for i in results
            ],
            "count": len(results),
            "query": q,
        })
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────
# /pipeline/status  — data pipeline sync status
# ──────────────────────────────────────────────────────────────
@app.route("/pipeline/status", methods=["GET"])
def pipeline_status():
    db = SessionLocal()
    try:
        sources = {}
        for source_name in ("pfs", "hcpcs", "icd10", "utilization"):
            last = (
                db.query(DataSyncLog)
                .filter_by(source_name=source_name)
                .order_by(DataSyncLog.started_at.desc())
                .first()
            )
            if last:
                sources[source_name] = {
                    "status": last.status,
                    "started_at": last.started_at.isoformat() if last.started_at else None,
                    "completed_at": last.completed_at.isoformat() if last.completed_at else None,
                    "records_processed": last.records_processed,
                    "records_inserted": last.records_inserted,
                    "records_updated": last.records_updated,
                    "error_message": last.error_message,
                }
            else:
                sources[source_name] = {"status": "never_run"}

        return jsonify({"sources": sources})
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────
# Legacy item endpoints (kept for backward compatibility)
# ──────────────────────────────────────────────────────────────
@app.route("/items", methods=["GET"])
def get_items():
    db = SessionLocal()
    items = db.query(Item).all()
    db.close()
    return jsonify([{"id": i.id, "name": i.name, "description": i.description} for i in items])


@app.route("/items", methods=["POST"])
def create_item():
    db = SessionLocal()
    data = request.get_json()
    item = Item(name=data["name"], description=data.get("description"))
    db.add(item)
    db.commit()
    db.refresh(item)
    db.close()
    return jsonify({"id": item.id, "name": item.name, "description": item.description})

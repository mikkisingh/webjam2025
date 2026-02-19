import os
import logging
import requests as http_requests
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from sqlalchemy import or_, func

from database import Base, engine, SessionLocal
from models import Procedure, HcpcsCode, Icd10Procedure, MedicareUtilization, DataSyncLog
from text_extractor import TextExtractor
from llm_service import LLMAnalyzer

load_dotenv()

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("medicheck")

# ── App setup ────────────────────────────────────────────────
app = Flask(__name__)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
CORS(app, origins=ALLOWED_ORIGINS)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["120 per minute"],
    storage_uri="memory://",
)

# Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

Base.metadata.create_all(bind=engine)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


# ── Helpers ──────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _escape_like(q):
    """Escape SQL LIKE wildcards in user input."""
    return q.replace('%', r'\%').replace('_', r'\_')


def verify_supabase_jwt():
    """Verify the caller's Supabase JWT and return user dict or None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    jwt = auth_header.split(" ", 1)[1]
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    try:
        resp = http_requests.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={"Authorization": f"Bearer {jwt}", "apikey": SUPABASE_SERVICE_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        logger.exception("JWT verification failed")
    return None


def require_auth(f):
    """Decorator that requires a valid Supabase JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = verify_supabase_jwt()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        request.user = user
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator that requires admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = verify_supabase_jwt()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        if user.get("app_metadata", {}).get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        request.user = user
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def root():
    return jsonify({"message": "MediCheck API - Medical Bill Analysis"})


# ──────────────────────────────────────────────────────────────
# /process  — single-step bill analysis endpoint
#
# Flow: receive file → extract text → DELETE file immediately
#       → run OpenAI analysis → return results
#       Nothing is persisted on this server.
# Requires: valid Supabase JWT
# ──────────────────────────────────────────────────────────────
@app.route("/process", methods=["POST"])
@limiter.limit("10 per minute")
@require_auth
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
        filepath = None

        if not raw_text or not raw_text.strip():
            return jsonify({"error": "Could not extract text from this file. Try a clearer image or a text-based PDF."}), 422

        # Run full AI analysis pipeline
        logger.info("Analyzing bill for user %s", request.user.get("id", "unknown"))
        analyzer = LLMAnalyzer()
        results = analyzer.analyze_bill(raw_text)

        # Check if document was rejected (not a medical bill)
        if results.get("rejected"):
            return jsonify({
                "rejected": True,
                "document_type": results.get("document_type", "unknown"),
                "reason": results.get("reason", "This does not appear to be a medical bill."),
            }), 422

        return jsonify({
            "structured_data": results['structured_data'],
            "analysis_results": results['analysis_results'],
            "summary": results['summary'],
            "complaint_email": results['complaint_email']
        }), 200

    except Exception as e:
        logger.exception("process_bill error")
        return jsonify({"error": "An internal error occurred. Please try again."}), 500
    finally:
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass


# ──────────────────────────────────────────────────────────────
# /admin/promote  — grant admin role to a user by email
# ──────────────────────────────────────────────────────────────
@app.route("/admin/promote", methods=["POST"])
@limiter.limit("5 per minute")
@require_admin
def admin_promote():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return jsonify({"error": "Admin promotion not configured on this server"}), 503

    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    if not email:
        return jsonify({"error": "email is required"}), 400

    try:
        list_resp = http_requests.get(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            headers={"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}", "apikey": SUPABASE_SERVICE_KEY},
            params={"filter": email},
            timeout=10,
        )
        if list_resp.status_code != 200:
            return jsonify({"error": "Failed to query users"}), 500

        users = list_resp.json().get("users", [])
        target = next((u for u in users if u.get("email") == email), None)
        if not target:
            return jsonify({"error": f"No user found with email: {email}"}), 404

        app_metadata = target.get("app_metadata") or {}
        app_metadata["role"] = "admin"

        update_resp = http_requests.put(
            f"{SUPABASE_URL}/auth/v1/admin/users/{target['id']}",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "apikey": SUPABASE_SERVICE_KEY,
                "Content-Type": "application/json",
            },
            json={"app_metadata": app_metadata},
            timeout=10,
        )
        if update_resp.status_code != 200:
            return jsonify({"error": "Failed to update user role"}), 500

        logger.info("Admin promoted user %s by %s", email, request.user.get("id"))
        return jsonify({"success": True, "email": email}), 200

    except Exception as e:
        logger.exception("admin_promote error")
        return jsonify({"error": "An internal error occurred."}), 500


# ──────────────────────────────────────────────────────────────
# /procedures/search  — search procedure cost database
# ──────────────────────────────────────────────────────────────
@app.route("/procedures/search", methods=["GET"])
@limiter.limit("60 per minute")
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
            pattern = f"%{_escape_like(q)}%"
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
# ──────────────────────────────────────────────────────────────
NPPES_URL = "https://npiregistry.cms.hhs.gov/api/"

@app.route("/providers/search", methods=["GET"])
@limiter.limit("30 per minute")
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
        "enumeration_type": "NPI-1",
    }
    if zip_code:
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
    except Exception:
        logger.exception("NPPES API error")
        return jsonify({"error": "Provider search is temporarily unavailable. Please try again."}), 502

    raw_results = data.get("results") or []

    providers = []
    for r in raw_results:
        basic = r.get("basic", {})
        addresses = r.get("addresses", [])
        taxonomies = r.get("taxonomies", [])

        practice_addr = next(
            (a for a in addresses if a.get("address_purpose") == "LOCATION"),
            addresses[0] if addresses else {}
        )

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
@limiter.limit("60 per minute")
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
            pattern = f"%{_escape_like(q)}%"
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
@limiter.limit("60 per minute")
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
            pattern = f"%{_escape_like(q)}%"
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

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import Base, engine, SessionLocal
from models import Item, Bill
from text_extractor import TextExtractor
from llm_service import LLMAnalyzer
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

import math
import requests
from locate import locate_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(locate_bp)

# Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

Base.metadata.create_all(bind=engine)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def root():
    return jsonify({"message": "MediCheck API - Medical Bill Analysis"})

@app.route("/items", methods=["GET"])
def get_items():
    db = SessionLocal()
    items = db.query(Item).all()
    return jsonify([{"id": i.id, "name": i.name, "description": i.description} for i in items])

@app.route("/items", methods=["POST"])
def create_item():
    db = SessionLocal()
    data = request.get_json()
    item = Item(name=data["name"], description=data.get("description"))
    db.add(item)
    db.commit()
    db.refresh(item)
    return jsonify({"id": item.id, "name": item.name, "description": item.description})

@app.route("/upload", methods=["POST"])
def upload_bill():
    """
    Upload and extract text from a medical bill.
    Accepts PDF, JPG, PNG files.
    """
    db = SessionLocal()
    
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed. Use PDF, JPG, or PNG"}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Get file extension
        file_type = filename.rsplit('.', 1)[1].lower()
        
        # Extract text
        try:
            extractor = TextExtractor()
            raw_text = extractor.extract_text(filepath, file_type)
        except Exception as e:
            return jsonify({"error": f"Text extraction failed: {str(e)}"}), 500
        
        # Create database record
        bill = Bill(
            filename=unique_filename,
            file_type=file_type,
            raw_text=raw_text,
            status="extracted"
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)
        
        return jsonify({
            "id": bill.id,
            "filename": bill.filename,
            "status": bill.status,
            "raw_text_preview": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
            "message": "File uploaded and text extracted successfully"
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route("/analyze/<int:bill_id>", methods=["POST"])
def analyze_bill(bill_id):
    """
    Analyze a bill using LLM.
    Performs data extraction, cost analysis, and generates summary.
    """
    db = SessionLocal()
    
    try:
        # Get bill from database
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        
        if not bill:
            return jsonify({"error": "Bill not found"}), 404
        
        if not bill.raw_text:
            return jsonify({"error": "No extracted text found. Upload the bill first."}), 400
        
        # Analyze with LLM
        try:
            analyzer = LLMAnalyzer()
            results = analyzer.analyze_bill(bill.raw_text)
        except Exception as e:
            return jsonify({"error": f"Analysis failed: {str(e)}"}), 500
        
        # Update database record
        bill.structured_data = json.dumps(results['structured_data'])
        bill.analysis_results = json.dumps(results['analysis_results'])
        bill.summary = results['summary']
        bill.status = "analyzed"
        
        # Extract total amount if available
        if 'total' in results['structured_data']:
            bill.total_amount = results['structured_data']['total']
        
        db.commit()
        db.refresh(bill)
        
        return jsonify({
            "id": bill.id,
            "status": bill.status,
            "structured_data": results['structured_data'],
            "analysis_results": results['analysis_results'],
            "summary": results['summary'],
            "complaint_email": results['complaint_email']
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route("/bills", methods=["GET"])
def get_bills():
    """Get all bills."""
    db = SessionLocal()
    
    try:
        bills = db.query(Bill).order_by(Bill.upload_date.desc()).all()
        
        return jsonify([{
            "id": b.id,
            "filename": b.filename,
            "upload_date": b.upload_date.isoformat(),
            "file_type": b.file_type,
            "status": b.status,
            "total_amount": b.total_amount
        } for b in bills]), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route("/bills/<int:bill_id>", methods=["GET"])
def get_bill(bill_id):
    """Get a specific bill with all details."""
    db = SessionLocal()
    
    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        
        if not bill:
            return jsonify({"error": "Bill not found"}), 404
        
        result = {
            "id": bill.id,
            "filename": bill.filename,
            "upload_date": bill.upload_date.isoformat(),
            "file_type": bill.file_type,
            "status": bill.status,
            "total_amount": bill.total_amount,
            "raw_text": bill.raw_text
        }
        
        # Parse JSON fields if they exist
        if bill.structured_data:
            result["structured_data"] = json.loads(bill.structured_data)
        
        if bill.analysis_results:
            result["analysis_results"] = json.loads(bill.analysis_results)
        
        if bill.summary:
            result["summary"] = bill.summary
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


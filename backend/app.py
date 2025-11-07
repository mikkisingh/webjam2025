from flask import Flask, jsonify, request
from flask_cors import CORS
from database import Base, engine, SessionLocal
from models import Item

app = Flask(__name__)
CORS(app)

Base.metadata.create_all(bind=engine)

@app.route("/")
def root():
    return jsonify({"message": "Hello from Flask backend"})

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

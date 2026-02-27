from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MongoDB connection
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["mis_plantas"]
plants_col = db["plants"]

def serialize(plant):
    """Convert MongoDB document to JSON-serializable dict."""
    plant["_id"] = str(plant["_id"])
    return plant

# --- PLANTS ---

@app.route("/api/plants", methods=["GET"])
def get_plants():
    plants = list(plants_col.find())
    return jsonify([serialize(p) for p in plants])

@app.route("/api/plants", methods=["POST"])
def create_plant():
    body = request.json
    plant = {
        "id": str(uuid.uuid4()),
        "name": body["name"],
        "photo": body.get("photo", ""),
        "watering_interval_days": body["watering_interval_days"],
        "notes": body.get("notes", ""),
        "created_at": datetime.utcnow().isoformat(),
        "watering_log": []
    }
    plants_col.insert_one(plant)
    return jsonify(serialize(plant)), 201

@app.route("/api/plants/<plant_id>", methods=["GET"])
def get_plant(plant_id):
    plant = plants_col.find_one({"id": plant_id})
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    return jsonify(serialize(plant))

@app.route("/api/plants/<plant_id>", methods=["PUT"])
def update_plant(plant_id):
    plant = plants_col.find_one({"id": plant_id})
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    body = request.json
    updates = {}
    for field in ["name", "photo", "notes", "watering_interval_days"]:
        if field in body:
            updates[field] = body[field]
    plants_col.update_one({"id": plant_id}, {"$set": updates})
    plant = plants_col.find_one({"id": plant_id})
    return jsonify(serialize(plant))

@app.route("/api/plants/<plant_id>", methods=["DELETE"])
def delete_plant(plant_id):
    plants_col.delete_one({"id": plant_id})
    return jsonify({"ok": True})

# --- WATERING LOG ---

@app.route("/api/plants/<plant_id>/water", methods=["POST"])
def water_plant(plant_id):
    plant = plants_col.find_one({"id": plant_id})
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    body = request.json or {}
    entry = {
        "id": str(uuid.uuid4()),
        "date": body.get("date", datetime.utcnow().isoformat()),
        "note": body.get("note", "")
    }
    plants_col.update_one({"id": plant_id}, {"$push": {"watering_log": entry}})
    plant = plants_col.find_one({"id": plant_id})
    return jsonify(serialize(plant))

@app.route("/api/plants/<plant_id>/water/<entry_id>", methods=["DELETE"])
def delete_watering_entry(plant_id, entry_id):
    plant = plants_col.find_one({"id": plant_id})
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    plants_col.update_one(
        {"id": plant_id},
        {"$pull": {"watering_log": {"id": entry_id}}}
    )
    plant = plants_col.find_one({"id": plant_id})
    return jsonify(serialize(plant))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
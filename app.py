from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
CORS(app)

MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["mis_plantas"]
plants_col = db["plants"]

def serialize(plant):
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
        "plant_type": body.get("plant_type", ""),
        "photos": body.get("photos", []),          # list of base64 strings
        "watering_interval_days": body["watering_interval_days"],
        "fertilizer_every_n_waterings": body.get("fertilizer_every_n_waterings", 0),  # 0 = disabled
        "notes": body.get("notes", ""),
        "created_at": datetime.utcnow().isoformat(),
        "last_watered_override": body.get("last_watered_override", ""),  # manual first date
        "flowering_start": body.get("flowering_start", ""),
        "flowering_end": body.get("flowering_end", ""),
        "flowering_photo": body.get("flowering_photo", ""),
        "watering_log": []  # [{id, date, note, fertilized, photos:[]}]
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
    for field in ["name", "plant_type", "photos", "notes", "watering_interval_days",
                  "fertilizer_every_n_waterings", "last_watered_override",
                  "flowering_start", "flowering_end", "flowering_photo"]:
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
        "note": body.get("note", ""),
        "fertilized": body.get("fertilized", False),
        "photos": body.get("photos", [])
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
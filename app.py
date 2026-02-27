from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"plants": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# --- PLANTS ---

@app.route("/api/plants", methods=["GET"])
def get_plants():
    data = load_data()
    return jsonify(data["plants"])

@app.route("/api/plants", methods=["POST"])
def create_plant():
    data = load_data()
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
    data["plants"].append(plant)
    save_data(data)
    return jsonify(plant), 201

@app.route("/api/plants/<plant_id>", methods=["GET"])
def get_plant(plant_id):
    data = load_data()
    plant = next((p for p in data["plants"] if p["id"] == plant_id), None)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    return jsonify(plant)

@app.route("/api/plants/<plant_id>", methods=["PUT"])
def update_plant(plant_id):
    data = load_data()
    plant = next((p for p in data["plants"] if p["id"] == plant_id), None)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    body = request.json
    if "name" in body:
        plant["name"] = body["name"]
    if "photo" in body:
        plant["photo"] = body["photo"]
    if "notes" in body:
        plant["notes"] = body["notes"]
    if "watering_interval_days" in body:
        plant["watering_interval_days"] = body["watering_interval_days"]
    save_data(data)
    return jsonify(plant)

@app.route("/api/plants/<plant_id>", methods=["DELETE"])
def delete_plant(plant_id):
    data = load_data()
    data["plants"] = [p for p in data["plants"] if p["id"] != plant_id]
    save_data(data)
    return jsonify({"ok": True})

# --- WATERING LOG ---

@app.route("/api/plants/<plant_id>/water", methods=["POST"])
def water_plant(plant_id):
    data = load_data()
    plant = next((p for p in data["plants"] if p["id"] == plant_id), None)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    body = request.json or {}
    entry = {
        "id": str(uuid.uuid4()),
        "date": body.get("date", datetime.utcnow().isoformat()),
        "note": body.get("note", "")
    }
    plant["watering_log"].append(entry)
    save_data(data)
    return jsonify(plant)

@app.route("/api/plants/<plant_id>/water/<entry_id>", methods=["DELETE"])
def delete_watering_entry(plant_id, entry_id):
    data = load_data()
    plant = next((p for p in data["plants"] if p["id"] == plant_id), None)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
    plant["watering_log"] = [e for e in plant["watering_log"] if e["id"] != entry_id]
    save_data(data)
    return jsonify(plant)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

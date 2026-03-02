from flask import Blueprint, jsonify, request
from .extensions import db
from .models.savoir_agir import SavoirAgir
from .models.jalon import Jalon
from .models.ac import ApprentissageCritique
import os
import json

main_routes = Blueprint("main_routes", __name__)

@main_routes.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Backend is running 🚀"
    })


@main_routes.route("/api/savoir-agir", methods=["GET"])
def get_savoir_agir():
    items = SavoirAgir.query.all()
    return jsonify([
        {"id": i.id, "name": i.name}
        for i in items
    ])


@main_routes.route("/api/jalons/<int:savoir_id>", methods=["GET"])
def get_jalons(savoir_id):
    jalons = Jalon.query.filter_by(savoir_agir_id=savoir_id).all()
    return jsonify([
        {"id": j.id, "name": j.name}
        for j in jalons
    ])


@main_routes.route("/api/ac", methods=["POST"])
def save_ac():

    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    new_ac = ApprentissageCritique(
        savoir_agir_id=data["savoir_agir_id"],
        jalon_id=data["jalon_id"],
        ac_text=data["ac_text"]
    )

    db.session.add(new_ac)
    db.session.commit()

    return jsonify({
        "message": "AC saved successfully"
    }), 201

@main_routes.route("/api/export/<formation_id>", methods=["GET"])
def export_json(formation_id):

    savoirs = SavoirAgir.query.all()

    result = {
        "formationId": formation_id,
        "savoirsAgir": []
    }

    for sa in savoirs:

        jalon_list = []

        for jalon in sa.jalons:

            acs = ApprentissageCritique.query.filter_by(
                savoir_agir_id=sa.id,
                jalon_id=jalon.id
            ).all()

            jalon_list.append({
                "name": jalon.name,
                "acs": [ac.ac_text for ac in acs]
            })

        result["savoirsAgir"].append({
            "name": sa.name,
            "jalons": jalon_list
        })

    file_path = f"exports/formation_{formation_id}.json"

    os.makedirs("exports", exist_ok=True)

    with open(file_path, "w") as f:
        json.dump(result, f, indent=2)

    return jsonify({
        "message": "File generated",
        "path": file_path
    })
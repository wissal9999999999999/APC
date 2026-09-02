from flask import Blueprint, jsonify, request, send_file
from .extensions import db
from .models.savoir_agir import SavoirAgir
from .models.jalon import Jalon
from .models.ac import ApprentissageCritique
from .alignment import MODEL_NAME, align_aad, align_aads
from .generation import generate_aads
import json
import re
from pathlib import Path
import tempfile

main_routes = Blueprint("main_routes", __name__)

EXPORTS_DIR = Path(__file__).resolve().parent.parent / "exports"


def build_ac_rows():
    rows = []

    for savoir in SavoirAgir.query.order_by(SavoirAgir.id).all():
        jalons = Jalon.query.filter_by(savoir_agir_id=savoir.id).order_by(Jalon.id).all()

        for jalon_index, jalon in enumerate(jalons, start=1):
            match = re.search(r"(\d+)$", jalon.name)
            jalon_number = int(match.group(1)) if match else jalon_index
            acs = ApprentissageCritique.query.filter_by(
                savoir_agir_id=savoir.id,
                jalon_id=jalon.id
            ).order_by(ApprentissageCritique.id).all()

            for ac_index, ac in enumerate(acs, start=1):
                rows.append({
                    "AC-ID": f"{savoir.name}-{jalon_number}.{ac_index}",
                    "AC-TITLE": ac.ac_text
                })

    return rows


def get_ac_file_path(formation_id):
    safe_formation_id = re.sub(r"[^a-zA-Z0-9_-]", "_", formation_id)
    EXPORTS_DIR.mkdir(exist_ok=True)
    return EXPORTS_DIR / f"ac_{safe_formation_id}.json"


def read_ac_file(formation_id):
    file_path = get_ac_file_path(formation_id)
    if not file_path.exists():
        return []

    with file_path.open(encoding="utf-8") as file:
        content = json.load(file)

    return content if isinstance(content, list) else []


def write_ac_file(formation_id, rows=None):
    file_path = get_ac_file_path(formation_id)
    rows = build_ac_rows() if rows is None else rows

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)

    return file_path


def get_aad_file_path(subject_id):
    safe_subject_id = re.sub(r"[^a-zA-Z0-9_-]", "_", subject_id)
    EXPORTS_DIR.mkdir(exist_ok=True)
    return EXPORTS_DIR / f"aad_{safe_subject_id}.json"


def get_aad_selection_file_path(subject_id):
    safe_subject_id = re.sub(r"[^a-zA-Z0-9_-]", "_", subject_id)
    EXPORTS_DIR.mkdir(exist_ok=True)
    return EXPORTS_DIR / f"aad_selection_{safe_subject_id}.json"


def get_alignment_file_path(subject_id):
    safe_subject_id = re.sub(r"[^a-zA-Z0-9_-]", "_", subject_id)
    EXPORTS_DIR.mkdir(exist_ok=True)
    return EXPORTS_DIR / f"alignment_{safe_subject_id}.json"


def parse_aad_json(content):
    raw_items = content.get("aads") if isinstance(content, dict) else content
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("Le JSON doit contenir une liste non vide d'AAD.")

    aad_items = []
    for index, item in enumerate(raw_items, start=1):
        if isinstance(item, str):
            aad_id, aad_text = f"AAD-{index}", item.strip()
        elif isinstance(item, dict):
            aad_id = str(item.get("aad_id") or f"AAD-{index}").strip()
            aad_text = str(item.get("formulation") or item.get("text") or "").strip()
        else:
            raise ValueError(f"AAD invalide à la position {index}.")
        if not aad_text:
            raise ValueError(f"Formulation manquante pour {aad_id}.")
        aad_items.append({"aad_id": aad_id, "aad_text": aad_text})
    return aad_items


def get_ac_identifier(formation_id, savoir, jalon):
    match = re.search(r"(\d+)$", jalon.name)
    if match:
        jalon_number = int(match.group(1))
    else:
        jalon_ids = [item.id for item in Jalon.query.filter_by(
            savoir_agir_id=savoir.id
        ).order_by(Jalon.id).all()]
        jalon_number = jalon_ids.index(jalon.id) + 1

    prefix = f"{savoir.name}-{jalon_number}."
    existing_numbers = []
    for row in read_ac_file(formation_id):
        ac_id = str(row.get("AC-ID", ""))
        if ac_id.startswith(prefix) and ac_id[len(prefix):].isdigit():
            existing_numbers.append(int(ac_id[len(prefix):]))

    ac_number = max(existing_numbers, default=0) + 1
    return f"{savoir.name}-{jalon_number}.{ac_number}"

@main_routes.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Backend is running 🚀"
    })


@main_routes.route("/api/identify", methods=["POST"])
def identify_aads():
    subject_id = str(request.form.get("subject_id", "matiere")).strip() or "matiere"
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "Au moins un fichier PDF est requis."}), 400
    if any(not file.filename or not file.filename.lower().endswith(".pdf") for file in files):
        return jsonify({"error": "Tous les fichiers doivent être des PDF."}), 400

    try:
        with tempfile.TemporaryDirectory(prefix="aad-upload-") as temp_dir:
            pdf_paths = []
            for index, file in enumerate(files, start=1):
                path = Path(temp_dir) / f"cours-{index}.pdf"
                file.save(path)
                pdf_paths.append(path)
            result = generate_aads(pdf_paths, subject_id)
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as error:
        return jsonify({"error": str(error)}), 500

    output_path = get_aad_file_path(subject_id)
    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)

    return jsonify({
        **result,
        "path": str(output_path),
    })


@main_routes.route("/api/aad/<subject_id>", methods=["GET"])
def get_generated_aads(subject_id):
    output_path = get_aad_file_path(subject_id)
    if not output_path.exists():
        return jsonify({"error": "Aucun AAD généré pour cette matière."}), 404

    with output_path.open(encoding="utf-8") as stream:
        result = json.load(stream)
    return jsonify({
        **result,
        "path": str(output_path),
    })


@main_routes.route("/api/aad/<subject_id>/selection", methods=["POST"])
def save_aad_selection(subject_id):
    data = request.get_json(silent=True) or {}
    selected_aads = data.get("aads")
    if not isinstance(selected_aads, list) or not selected_aads:
        return jsonify({"error": "Sélectionnez au moins un AAD."}), 400

    required_fields = {"aad_id", "formulation"}
    if any(not isinstance(aad, dict) or not required_fields.issubset(aad) for aad in selected_aads):
        return jsonify({"error": "La sélection d'AAD est invalide."}), 400

    payload = {
        "subject_id": subject_id,
        "selected_count": len(selected_aads),
        "aads": selected_aads,
    }
    output_path = get_aad_selection_file_path(subject_id)
    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)

    return jsonify({
        "message": f"{len(selected_aads)} AAD enregistré(s).",
        "path": str(output_path),
        "download_url": f"/api/aad/{subject_id}/selection/download",
    })


@main_routes.route("/api/aad/<subject_id>/selection/download", methods=["GET"])
def download_aad_selection(subject_id):
    output_path = get_aad_selection_file_path(subject_id)
    if not output_path.exists():
        return jsonify({"error": "Aucune sélection enregistrée."}), 404
    return send_file(
        output_path,
        as_attachment=True,
        download_name=output_path.name,
        mimetype="application/json",
    )


@main_routes.route("/api/align", methods=["POST"])
def align():
    data = request.get_json(silent=True) or {}
    aad_text = str(data.get("aad_text", "")).strip()
    formation_id = str(data.get("formation_id", "iti")).strip()

    if not aad_text:
        return jsonify({"error": "AAD text is required"}), 400

    try:
        threshold = float(data.get("threshold", 0.30))
        limit = int(data.get("limit", 10))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid threshold or limit"}), 400

    if not 0 <= threshold <= 1 or not 1 <= limit <= 50:
        return jsonify({"error": "Threshold or limit out of range"}), 400

    rows = read_ac_file(formation_id)
    try:
        matches = align_aad(aad_text, rows, threshold, limit)
    except (RuntimeError, OSError, ValueError) as error:
        return jsonify({"error": str(error)}), 500
    return jsonify({
        "aad_text": aad_text,
        "embedding_model": MODEL_NAME,
        "threshold": threshold,
        "top_match": matches[0] if matches else None,
        "matches": matches,
    })


@main_routes.route("/api/align/json", methods=["POST"])
def align_json_file():
    uploaded_file = request.files.get("file")
    subject_id = str(request.form.get("subject_id", "matiere")).strip() or "matiere"
    formation_id = str(request.form.get("formation_id", "iti")).strip() or "iti"
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"error": "Un fichier JSON est requis."}), 400
    if not uploaded_file.filename.lower().endswith(".json"):
        return jsonify({"error": "Le fichier doit être au format JSON."}), 400

    try:
        threshold = float(request.form.get("threshold", 0.30))
        limit = int(request.form.get("limit", 3))
        content = json.load(uploaded_file.stream)
        aad_items = parse_aad_json(content)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        return jsonify({"error": str(error)}), 400
    if not 0 <= threshold <= 1 or not 1 <= limit <= 10:
        return jsonify({"error": "Seuil ou limite hors plage."}), 400

    try:
        alignments = align_aads(aad_items, read_ac_file(formation_id), threshold, limit)
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as error:
        return jsonify({"error": str(error)}), 500

    payload = {
        "subject_id": subject_id,
        "embedding_model": MODEL_NAME,
        "threshold": threshold,
        "alignment_count": len(alignments),
        "alignments": alignments,
    }
    output_path = get_alignment_file_path(subject_id)
    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
    return jsonify({
        **payload,
        "path": str(output_path),
        "download_url": f"/api/align/{subject_id}/download",
    })


@main_routes.route("/api/align/<subject_id>/download", methods=["GET"])
def download_alignment(subject_id):
    output_path = get_alignment_file_path(subject_id)
    if not output_path.exists():
        return jsonify({"error": "Aucun alignement JSON enregistré."}), 404
    return send_file(
        output_path,
        as_attachment=True,
        download_name=output_path.name,
        mimetype="application/json",
    )


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

    required_fields = ("formation_id", "savoir_agir_id", "jalon_id", "ac_text")
    if any(not data.get(field) for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    savoir = db.session.get(SavoirAgir, data["savoir_agir_id"])
    jalon = db.session.get(Jalon, data["jalon_id"])

    if not savoir or not jalon or jalon.savoir_agir_id != savoir.id:
        return jsonify({"error": "Invalid savoir-agir or jalon"}), 400

    new_ac = ApprentissageCritique(
        savoir_agir_id=savoir.id,
        jalon_id=jalon.id,
        ac_text=data["ac_text"].strip()
    )

    db.session.add(new_ac)
    db.session.commit()

    ac_identifier = get_ac_identifier(data["formation_id"], savoir, jalon)
    rows = read_ac_file(data["formation_id"])
    new_row = {
        "AC-ID": ac_identifier,
        "AC-TITLE": new_ac.ac_text
    }
    rows.append(new_row)
    file_path = write_ac_file(data["formation_id"], rows)

    return jsonify({
        "message": "AC saved successfully",
        "ac": new_row,
        "path": str(file_path)
    }), 201

@main_routes.route("/api/export/<formation_id>", methods=["GET"])
def export_json(formation_id):
    rows = read_ac_file(formation_id)
    file_path = write_ac_file(formation_id, rows or build_ac_rows())

    return jsonify({
        "message": "File generated",
        "path": str(file_path),
        "acs": read_ac_file(formation_id)
    })

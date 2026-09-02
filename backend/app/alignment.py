"""Bridge to the already-installed SMA Sentence-CamemBERT environment."""

import json
import os
from pathlib import Path
import subprocess


MODEL_NAME = "Lajavaness/sentence-camembert-large"
DEFAULT_SMA_PYTHON = "/home/wissal/Téléchargements/SMA/.venv/bin/python"
WORKER_PATH = Path(__file__).resolve().parent / "alignment_worker.py"


def align_aad(aad_text, ac_rows, threshold=0.30, limit=10):
    return align_aads(
        [{"aad_id": "AAD-SAISIE", "aad_text": aad_text}],
        ac_rows,
        threshold,
        limit,
    )[0]["matches"]


def align_aads(aad_items, ac_rows, threshold=0.30, limit=10):
    python_path = os.getenv("SMA_PYTHON", DEFAULT_SMA_PYTHON)
    if not Path(python_path).exists():
        raise RuntimeError("Environnement Python SMA introuvable.")

    process = subprocess.run(
        [python_path, str(WORKER_PATH)],
        input=json.dumps({
            "aad_items": aad_items,
            "ac_rows": ac_rows,
            "threshold": threshold,
            "limit": limit,
        }, ensure_ascii=False),
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or "Échec du moteur d'alignement.")

    return json.loads(process.stdout)

"""Bridge between the Flask application and the SMA AAD generator."""

import json
import os
from pathlib import Path
import subprocess


DEFAULT_SMA_PYTHON = "/home/wissal/Téléchargements/SMA/.venv/bin/python"
WORKER_PATH = Path(__file__).resolve().parent / "generation_worker.py"


def generate_aads(pdf_paths, subject_id):
    python_path = os.getenv("SMA_PYTHON", DEFAULT_SMA_PYTHON)
    if not Path(python_path).exists():
        raise RuntimeError("Environnement Python SMA introuvable.")

    process = subprocess.run(
        [python_path, str(WORKER_PATH)],
        input=json.dumps({
            "pdf_paths": [str(path) for path in pdf_paths],
            "subject_id": subject_id,
        }, ensure_ascii=False),
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    if process.returncode != 0:
        error_lines = [line.strip() for line in process.stderr.splitlines() if line.strip()]
        message = error_lines[-1] if error_lines else "Échec de la génération des AAD."
        if message.startswith("RuntimeError: "):
            message = message.removeprefix("RuntimeError: ")
        raise RuntimeError(message)

    return json.loads(process.stdout)

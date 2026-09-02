#!/usr/bin/env python3
"""Évaluer Jina-ColBERT-v2 multilingue sur tous les cours AC-AAD."""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score


WORKSPACE = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_MODULES_CACHE", str(WORKSPACE / "alignment_colbert" / ".hf_modules"))
sys.path.insert(0, str(WORKSPACE / "alignment_tfidf_lsa"))
from run_alignment import read_catalog, read_positive_pairs  # noqa: E402
from pylate import models  # noqa: E402

from run_colbert_all_courses import COURSES  # noqa: E402


MODEL_NAME = "jinaai/jina-colbert-v2"
OUTPUT_DIR = WORKSPACE / "alignment_colbert" / "results_jina"


def maxsim(query: np.ndarray, document: np.ndarray) -> float:
    """Mean MaxSim ColBERT entre les vecteurs de tokens normalisés."""
    query = np.asarray(query, dtype=np.float32)
    document = np.asarray(document, dtype=np.float32)
    query /= np.maximum(np.linalg.norm(query, axis=1, keepdims=True), 1e-12)
    document /= np.maximum(np.linalg.norm(document, axis=1, keepdims=True), 1e-12)
    return float((query @ document.T).max(axis=1).mean())


def main() -> None:
    data_dir = WORKSPACE / "data"
    acs = read_catalog(data_dir / "ac_unique.csv", "AC-ID", "AC-TITLE")
    aad_by_course = {
        course: read_catalog(data_dir / "AAD" / aad_file, "AAD-ID", "AAD-TITLE")
        for course, (aad_file, _) in COURSES.items()
    }
    positives_by_course = {
        course: read_positive_pairs(data_dir / "AADAC" / label_file)[0]
        for course, (_, label_file) in COURSES.items()
    }
    unique_aads = {}
    for aads in aad_by_course.values():
        for aad in aads:
            unique_aads[(aad.identifier, aad.title)] = aad

    print(f"Chargement de {MODEL_NAME} sur CPU...")
    model = models.ColBERT(
        model_name_or_path=MODEL_NAME,
        device="cpu",
        trust_remote_code=True,
    )
    print(f"Encodage document de {len(acs)} AC...")
    ac_vectors = model.encode(
        [ac.title for ac in acs], batch_size=8, is_query=False, show_progress_bar=True
    )
    aad_items = list(unique_aads.values())
    print(f"Encodage requête de {len(aad_items)} AAD...")
    aad_vectors = model.encode(
        [aad.title for aad in aad_items], batch_size=8, is_query=True, show_progress_bar=True
    )
    aad_vector_by_key = {
        (aad.identifier, aad.title): vector for aad, vector in zip(aad_items, aad_vectors)
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "scores").mkdir(exist_ok=True)
    (OUTPUT_DIR / "auc_by_ac").mkdir(exist_ok=True)
    summaries = []
    for course, aads in aad_by_course.items():
        positives = positives_by_course[course]
        scores = np.asarray([
            [maxsim(aad_vector_by_key[(aad.identifier, aad.title)], ac_vector) for aad in aads]
            for ac_vector in ac_vectors
        ], dtype=np.float32)

        with (OUTPUT_DIR / "scores" / f"{course}_jina_colbert_v2_scores.csv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.writer(stream)
            writer.writerow(["AC-ID", "AC-TITLE", "AAD-ID", "AAD-TITLE", "LABEL", "MEAN-MAXSIM"])
            for i, ac in enumerate(acs):
                for j, aad in enumerate(aads):
                    writer.writerow([ac.identifier, ac.title, aad.identifier, aad.title,
                                     int((ac.identifier, aad.identifier) in positives),
                                     f"{scores[i, j]:.10f}"])

        aucs = []
        metrics = []
        for i, ac in enumerate(acs):
            labels = [int((ac.identifier, aad.identifier) in positives) for aad in aads]
            pos = sum(labels)
            neg = len(labels) - pos
            auc = float(roc_auc_score(labels, scores[i])) if pos and neg else None
            if auc is not None:
                aucs.append(auc)
            metrics.append((ac.identifier, pos, neg, auc))
        with (OUTPUT_DIR / "auc_by_ac" / f"{course}_jina_colbert_v2_auc_by_ac.csv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.writer(stream)
            writer.writerow(["AC-ID", "POSITIVES", "NEGATIVES", "ROC-AUC", "STATUS"])
            for ac_id, pos, neg, auc in metrics:
                writer.writerow([ac_id, pos, neg, "" if auc is None else f"{auc:.10f}",
                                 "ok" if auc is not None else "indefinie_une_seule_classe"])
        summary = {
            "model": "Jina-ColBERT-v2",
            "checkpoint": MODEL_NAME,
            "course": course,
            "ac_count": len(acs),
            "aad_count": len(aads),
            "pairs": len(acs) * len(aads),
            "positives": sum(int((ac.identifier, aad.identifier) in positives)
                             for ac in acs for aad in aads),
            "evaluable_ac": len(aucs),
            "undefined_ac": len(acs) - len(aucs),
            "mean_ac_roc_auc": float(np.mean(aucs)),
        }
        summaries.append(summary)
        print(f"{course:7s} AUC moyenne={summary['mean_ac_roc_auc']:.4f} ({len(aucs)} AC évaluables)")

    values = [row["mean_ac_roc_auc"] for row in summaries]
    with (OUTPUT_DIR / "summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["MODEL", "COURSE", "AC", "AAD", "PAIRS", "POSITIVES", "EVALUABLE-AC", "UNDEFINED-AC", "MEAN-AC-ROC-AUC"])
        for row in summaries:
            writer.writerow([row["model"], row["course"], row["ac_count"], row["aad_count"],
                             row["pairs"], row["positives"], row["evaluable_ac"],
                             row["undefined_ac"], f"{row['mean_ac_roc_auc']:.10f}"])
    with (OUTPUT_DIR / "tableau_jina_colbert.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Modèle", *[course.upper() for course in COURSES], "Moy"])
        writer.writerow(["Jina-ColBERT-v2", *[f"{value:.4f}" for value in values],
                         f"{float(np.mean(values)):.4f}"])
    (OUTPUT_DIR / "summary.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

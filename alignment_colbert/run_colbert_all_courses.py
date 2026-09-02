#!/usr/bin/env python3
"""Alignement ColBERTv2 français sur tous les cours disponibles."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

WORKSPACE = Path(__file__).resolve().parents[1]

# Le checkpoint est déjà dans le cache local. Éviter toute requête de contrôle
# réseau pour rendre l'expérience reproductible hors ligne.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TORCH_EXTENSIONS_DIR", str(WORKSPACE / "alignment_colbert" / ".torch_extensions"))
sys.path.insert(0, str(WORKSPACE / "alignment_tfidf_lsa"))
from run_alignment import read_catalog, read_positive_pairs  # noqa: E402

from aad_prototype.colbert_alignment import (  # noqa: E402
    NativeColBERTEncoder,
    mean_maxsim,
)


MODEL_NAME = "antoinelouis/colbertv2-camembert-L4-mmarcoFR"
COURSES = {
    "algo": ("algo_aad.txt", "algo_aad.csv"),
    "bd": ("bd_aad.txt", "bd_aad.csv"),
    "elec": ("elec_aad.txt", "elec_aad.csv"),
    "python": ("python_aad.txt", "python_aad.csv"),
    "ananum": ("ananum_aad.txt", "ananum_aad.csv"),
    "progav": ("progav_aad.txt", "progav_aad.csv"),
    "compil": ("compil_aad.txt", "compil_aad.csv"),
    "tds": ("tds_aad.txt", "tds_aad.csv"),
    "auto": ("auto.txt", "auto.csv"),
    "bigdata": ("bigdata.txt", "bigdata.csv"),
    "capt": ("capt.txt", "capt.csv"),
    "ddrs31": ("ddrs31.txt", "ddrs31.csv"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=WORKSPACE / "data")
    parser.add_argument("--output-dir", type=Path, default=WORKSPACE / "alignment_colbert" / "results")
    parser.add_argument("--model", default=MODEL_NAME)
    args = parser.parse_args()

    acs = read_catalog(args.data_dir / "ac_unique.csv", "AC-ID", "AC-TITLE")
    aad_by_course = {
        course: read_catalog(args.data_dir / "AAD" / aad_file, "AAD-ID", "AAD-TITLE")
        for course, (aad_file, _) in COURSES.items()
    }
    positives_by_course = {
        course: read_positive_pairs(args.data_dir / "AADAC" / label_file)[0]
        for course, (_, label_file) in COURSES.items()
    }

    # Dédupliquer les AAD entre cours avant l'encodage.
    unique_aads = {}
    for aads in aad_by_course.values():
        for aad in aads:
            unique_aads[(aad.identifier, aad.title)] = aad

    print(f"Chargement du modèle français : {args.model}")
    encoder = NativeColBERTEncoder(args.model)
    print(f"Encodage document de {len(acs)} AC...")
    ac_vectors = encoder.encode_document([ac.title for ac in acs])
    print(f"Encodage requête de {len(unique_aads)} AAD...")
    aad_items = list(unique_aads.values())
    aad_vectors = encoder.encode_queries([aad.title for aad in aad_items])
    aad_vector_by_key = {
        (aad.identifier, aad.title): vector for aad, vector in zip(aad_items, aad_vectors)
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "scores").mkdir(exist_ok=True)
    (args.output_dir / "auc_by_ac").mkdir(exist_ok=True)
    summaries = []

    for course, aads in aad_by_course.items():
        positives = positives_by_course[course]
        scores = np.empty((len(acs), len(aads)), dtype=np.float32)
        for ac_index, ac_vector in enumerate(ac_vectors):
            for aad_index, aad in enumerate(aads):
                scores[ac_index, aad_index] = mean_maxsim(
                    aad_vector_by_key[(aad.identifier, aad.title)], ac_vector
                )

        score_path = args.output_dir / "scores" / f"{course}_colbertv2_fr_scores.csv"
        with score_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["AC-ID", "AC-TITLE", "AAD-ID", "AAD-TITLE", "LABEL", "MEAN-MAXSIM"])
            for i, ac in enumerate(acs):
                for j, aad in enumerate(aads):
                    writer.writerow([
                        ac.identifier, ac.title, aad.identifier, aad.title,
                        int((ac.identifier, aad.identifier) in positives),
                        f"{scores[i, j]:.10f}",
                    ])

        metrics = []
        aucs = []
        for i, ac in enumerate(acs):
            labels = [int((ac.identifier, aad.identifier) in positives) for aad in aads]
            positive_count = sum(labels)
            negative_count = len(labels) - positive_count
            auc = float(roc_auc_score(labels, scores[i])) if positive_count and negative_count else None
            if auc is not None:
                aucs.append(auc)
            metrics.append((ac.identifier, positive_count, negative_count, auc))

        auc_path = args.output_dir / "auc_by_ac" / f"{course}_colbertv2_fr_auc_by_ac.csv"
        with auc_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["AC-ID", "POSITIVES", "NEGATIVES", "ROC-AUC", "STATUS"])
            for ac_id, pos, neg, auc in metrics:
                writer.writerow([
                    ac_id, pos, neg, "" if auc is None else f"{auc:.10f}",
                    "ok" if auc is not None else "indefinie_une_seule_classe",
                ])

        represented_positives = sum(
            int((ac.identifier, aad.identifier) in positives) for ac in acs for aad in aads
        )
        summary = {
            "course": course,
            "model": "ColBERTv2-CamemBERT-FR",
            "checkpoint": args.model,
            "ac_count": len(acs),
            "aad_count": len(aads),
            "pairs": len(acs) * len(aads),
            "positives": represented_positives,
            "evaluable_ac": len(aucs),
            "undefined_ac": len(acs) - len(aucs),
            "mean_ac_roc_auc": float(np.mean(aucs)) if aucs else None,
        }
        summaries.append(summary)
        print(f"{course:7s} AUC moyenne={summary['mean_ac_roc_auc']:.4f} ({len(aucs)} AC évaluables)")

    with (args.output_dir / "summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["MODEL", "COURSE", "AC", "AAD", "PAIRS", "POSITIVES", "EVALUABLE-AC", "UNDEFINED-AC", "MEAN-AC-ROC-AUC"])
        for row in summaries:
            writer.writerow([
                row["model"], row["course"], row["ac_count"], row["aad_count"], row["pairs"],
                row["positives"], row["evaluable_ac"], row["undefined_ac"],
                f"{row['mean_ac_roc_auc']:.10f}",
            ])
    (args.output_dir / "summary.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (args.output_dir / "tableau_colbert.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Modèle", *[course.upper() for course in COURSES], "Moy"])
        values = [row["mean_ac_roc_auc"] for row in summaries]
        writer.writerow([
            "ColBERTv2-CamemBERT-FR",
            *[f"{value:.4f}" for value in values],
            f"{float(np.mean(values)):.4f}",
        ])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Combiner les scores lexicaux et Sentence-CamemBERT-Large."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from run_alignment import (  # noqa: E402
    COURSES,
    evaluate_and_write,
    read_catalog,
    read_positive_pairs,
    write_summary,
)


HYBRIDS = (
    ("TF-Sentence-CamemBERT-Large (Hybrid alpha=0.9)", "tf-idf", 0.9),
    ("LSA-Sentence-CamemBERT-Large (Hybrid alpha=0.8)", "lsa", 0.8),
)


def load_score_matrix(path: Path, acs, aads) -> np.ndarray:
    ac_index = {item.identifier: index for index, item in enumerate(acs)}
    aad_index = {item.identifier: index for index, item in enumerate(aads)}
    matrix = np.full((len(acs), len(aads)), np.nan, dtype=np.float64)
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            matrix[ac_index[row["AC-ID"]], aad_index[row["AAD-ID"]]] = float(row["SCORE"])
    if np.isnan(matrix).any():
        raise ValueError(f"Matrice de scores incomplète : {path}")
    return matrix


def main() -> None:
    data_dir = ROOT.parent / "data"
    output_dir = ROOT / "results"
    acs = read_catalog(data_dir / "ac_unique.csv", "AC-ID", "AC-TITLE")
    summaries = []
    for model_name, lexical_slug, alpha in HYBRIDS:
        for course in COURSES:
            aads = read_catalog(data_dir / "AAD" / f"{course}.txt", "AAD-ID", "AAD-TITLE")
            positives, _ = read_positive_pairs(data_dir / "AADAC" / f"{course}.csv")
            lexical = load_score_matrix(
                output_dir / "scores" / f"{course}_{lexical_slug}_scores.csv", acs, aads
            )
            semantic = load_score_matrix(
                output_dir / "scores" / f"{course}_sentence-camembert-large_scores.csv", acs, aads
            )
            hybrid = alpha * lexical + (1.0 - alpha) * semantic
            summary = evaluate_and_write(
                course, model_name, acs, aads, positives, hybrid, output_dir
            )
            summary["alpha"] = alpha
            summary["lexical_component"] = lexical_slug
            summary["semantic_component"] = "Sentence-CamemBERT-Large"
            summaries.append(summary)
            print(f"{model_name} {course}: {summary['mean_ac_roc_auc']:.4f}")

    summary_path = output_dir / "summary.json"
    previous = json.loads(summary_path.read_text(encoding="utf-8"))
    hybrid_names = {item[0] for item in HYBRIDS}
    previous = [row for row in previous if row.get("model") not in hybrid_names]
    write_summary(output_dir, previous + summaries)

    with (output_dir / "tableau_nouvelles_donnees.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(["Modèle", *[course.upper() for course in COURSES], "Moy"])
        for model_name, _, _ in HYBRIDS:
            rows = [row for row in summaries if row["model"] == model_name]
            values = [row["mean_ac_roc_auc"] for row in rows]
            writer.writerow([model_name, *[f"{value:.4f}" for value in values],
                             f"{float(np.mean(values)):.4f}"])


if __name__ == "__main__":
    main()

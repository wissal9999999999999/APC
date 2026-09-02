#!/usr/bin/env python3
"""Évaluer Sentence-CamemBERT-Large sur les quatre cours supplémentaires."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

from run_alignment import (
    COURSES,
    evaluate_and_write,
    read_catalog,
    read_positive_pairs,
    write_summary,
)


DEFAULT_MODEL = "Lajavaness/sentence-camembert-large"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("alignment_tfidf_lsa/results"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Autoriser le téléchargement si le modèle n'est pas en cache.",
    )
    args = parser.parse_args()

    acs = read_catalog(args.data_dir / "ac_unique.csv", "AC-ID", "AC-TITLE")
    course_aads = {
        course: read_catalog(args.data_dir / "AAD" / f"{course}.txt", "AAD-ID", "AAD-TITLE")
        for course in COURSES
    }
    model = SentenceTransformer(args.model, local_files_only=not args.allow_download)

    # Les AC sont communs aux cours : ils ne sont encodés qu'une seule fois.
    ac_embeddings = model.encode(
        [item.title for item in acs],
        batch_size=args.batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    summaries: list[dict[str, object]] = []
    for course, aads in course_aads.items():
        positives, _ = read_positive_pairs(args.data_dir / "AADAC" / f"{course}.csv")
        aad_embeddings = model.encode(
            [item.title for item in aads],
            batch_size=args.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        # Produit scalaire = cosinus puisque les embeddings sont normalisés.
        scores = ac_embeddings @ aad_embeddings.T
        summary = evaluate_and_write(
            course,
            "Sentence-CamemBERT-Large",
            acs,
            aads,
            positives,
            scores,
            args.output_dir,
        )
        summary["embedding_model"] = args.model
        summaries.append(summary)
        print(
            f"Sentence-CamemBERT-Large {course:7s} "
            f"AUC moyenne={summary['mean_ac_roc_auc']:.4f} "
            f"({summary['evaluable_ac']} AC évaluables)"
        )

    summary_json_path = args.output_dir / "summary.json"
    previous = json.loads(summary_json_path.read_text(encoding="utf-8")) if summary_json_path.exists() else []
    previous = [row for row in previous if row.get("model") != "Sentence-CamemBERT-Large"]
    write_summary(args.output_dir, previous + summaries)


if __name__ == "__main__":
    main()

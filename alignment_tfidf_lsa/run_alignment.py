#!/usr/bin/env python3
"""Évaluer l'alignement AC-AAD avec TF-IDF et LSA sur quatre cours.

Les fichiers ``data/AADAC/<cours>.csv`` décrivent les paires positives. Le
script construit la matrice complète AC x AAD à partir de ``data/ac_unique.csv``
et ``data/AAD/<cours>.txt``, calcule les similarités cosinus, puis rapporte une
ROC-AUC par AC et la moyenne des AC évaluables.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import roc_auc_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize


COURSES = ("auto", "bigdata", "capt", "ddrs31")


@dataclass(frozen=True)
class TextItem:
    identifier: str
    title: str


def read_catalog(path: Path, id_column: str, title_column: str) -> list[TextItem]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        items = [
            TextItem((row.get(id_column) or "").strip(), (row.get(title_column) or "").strip())
            for row in rows
        ]
    return [item for item in items if item.identifier and item.title]


def read_positive_pairs(path: Path) -> tuple[set[tuple[str, str]], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    positives = {
        ((row.get("AC-ID") or "").strip(), (row.get("AAD-ID") or "").strip())
        for row in rows
        if (row.get("LABEL") or "").strip() == "1"
    }
    return positives, rows


def tfidf_and_lsa_scores(
    acs: list[TextItem], aads: list[TextItem], lsa_components: int
) -> tuple[np.ndarray, np.ndarray, int]:
    texts = [item.title for item in acs] + [item.title for item in aads]
    # Configuration lexicale standard (unigrammes), cohérente avec la ligne
    # TF-IDF du tableau de référence.
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 1))
    matrix = vectorizer.fit_transform(texts)
    ac_tfidf = matrix[: len(acs)]
    aad_tfidf = matrix[len(acs) :]
    tfidf_scores = cosine_similarity(ac_tfidf, aad_tfidf)

    max_components = min(matrix.shape[0] - 1, matrix.shape[1] - 1)
    used_components = min(lsa_components, max_components)
    if used_components < 1:
        raise ValueError("Corpus trop petit pour calculer LSA")
    svd = TruncatedSVD(n_components=used_components, random_state=42)
    latent = normalize(svd.fit_transform(matrix))
    lsa_scores = cosine_similarity(latent[: len(acs)], latent[len(acs) :])
    return tfidf_scores, lsa_scores, used_components


def evaluate_and_write(
    course: str,
    model: str,
    acs: list[TextItem],
    aads: list[TextItem],
    positives: set[tuple[str, str]],
    scores: np.ndarray,
    output_dir: Path,
) -> dict[str, object]:
    score_path = output_dir / "scores" / f"{course}_{model.lower()}_scores.csv"
    auc_path = output_dir / "auc_by_ac" / f"{course}_{model.lower()}_auc_by_ac.csv"
    score_path.parent.mkdir(parents=True, exist_ok=True)
    auc_path.parent.mkdir(parents=True, exist_ok=True)

    with score_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["AC-ID", "AC-TITLE", "AAD-ID", "AAD-TITLE", "LABEL", "SCORE"])
        for ac_index, ac in enumerate(acs):
            for aad_index, aad in enumerate(aads):
                writer.writerow([
                    ac.identifier,
                    ac.title,
                    aad.identifier,
                    aad.title,
                    int((ac.identifier, aad.identifier) in positives),
                    f"{scores[ac_index, aad_index]:.10f}",
                ])

    ac_rows: list[list[object]] = []
    auc_values: list[float] = []
    for ac_index, ac in enumerate(acs):
        labels = [int((ac.identifier, aad.identifier) in positives) for aad in aads]
        positives_count = sum(labels)
        negatives_count = len(labels) - positives_count
        if positives_count and negatives_count:
            auc = float(roc_auc_score(labels, scores[ac_index]))
            auc_values.append(auc)
            status = "ok"
        else:
            auc = None
            status = "indefinie_une_seule_classe"
        ac_rows.append([ac.identifier, positives_count, negatives_count, auc, status])

    with auc_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["AC-ID", "POSITIVES", "NEGATIVES", "ROC-AUC", "STATUS"])
        for ac_id, pos, neg, auc, status in ac_rows:
            writer.writerow([ac_id, pos, neg, "" if auc is None else f"{auc:.10f}", status])

    return {
        "model": model,
        "course": course,
        "ac_count": len(acs),
        "aad_count": len(aads),
        "pairs": len(acs) * len(aads),
        "positives": sum(int(pair in positives) for pair in (
            (ac.identifier, aad.identifier) for ac in acs for aad in aads
        )),
        "evaluable_ac": len(auc_values),
        "undefined_ac": len(acs) - len(auc_values),
        "mean_ac_roc_auc": float(np.mean(auc_values)) if auc_values else None,
    }


def write_summary(output_dir: Path, summaries: list[dict[str, object]]) -> None:
    """Écrire un résumé commun, éventuellement enrichi par d'autres modèles."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "summary.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = ["MODEL", "COURSE", "AC", "AAD", "PAIRS", "POSITIVES", "EVALUABLE-AC", "UNDEFINED-AC", "MEAN-AC-ROC-AUC"]
        writer = csv.writer(stream)
        writer.writerow(fields)
        for row in summaries:
            writer.writerow([
                row["model"], row["course"], row["ac_count"], row["aad_count"],
                row["pairs"], row["positives"], row["evaluable_ac"], row["undefined_ac"],
                f"{row['mean_ac_roc_auc']:.10f}" if row["mean_ac_roc_auc"] is not None else "",
            ])
    (output_dir / "summary.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("alignment_tfidf_lsa/results"))
    parser.add_argument("--lsa-components", type=int, default=100)
    args = parser.parse_args()

    acs = read_catalog(args.data_dir / "ac_unique.csv", "AC-ID", "AC-TITLE")
    summaries: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []

    for course in COURSES:
        aads = read_catalog(args.data_dir / "AAD" / f"{course}.txt", "AAD-ID", "AAD-TITLE")
        positives, positive_rows = read_positive_pairs(args.data_dir / "AADAC" / f"{course}.csv")
        known_ac_ids = {item.identifier for item in acs}
        known_aad_ids = {item.identifier for item in aads}
        excluded = [
            row for row in positive_rows
            if (row.get("AC-ID") or "").strip() not in known_ac_ids
            or (row.get("AAD-ID") or "").strip() not in known_aad_ids
        ]
        warnings.append({
            "course": course,
            "excluded_positive_rows": len(excluded),
            "excluded_pairs": [
                {"ac_id": row.get("AC-ID", ""), "aad_id": row.get("AAD-ID", ""),
                 "reason": "AC ou AAD absent du catalogue textuel"}
                for row in excluded
            ],
        })

        tfidf_scores, lsa_scores, components = tfidf_and_lsa_scores(
            acs, aads, args.lsa_components
        )
        tfidf_summary = evaluate_and_write(
            course, "TF-IDF", acs, aads, positives, tfidf_scores, args.output_dir
        )
        lsa_summary = evaluate_and_write(
            course, "LSA", acs, aads, positives, lsa_scores, args.output_dir
        )
        lsa_summary["lsa_components"] = components
        summaries.extend([tfidf_summary, lsa_summary])

    write_summary(args.output_dir, summaries)
    (args.output_dir / "warnings.json").write_text(
        json.dumps(warnings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for row in summaries:
        print(f"{row['model']:6s} {row['course']:7s} AUC moyenne={row['mean_ac_roc_auc']:.4f} "
              f"({row['evaluable_ac']} AC évaluables)")


if __name__ == "__main__":
    main()

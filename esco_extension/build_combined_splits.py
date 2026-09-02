#!/usr/bin/env python3
"""Fusionner les splits ESCO historiques et l'extension nouveaux cours."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OLD_ROOT = Path("/home/wissal/Bureau/fine tuning/out")
OUTPUT = ROOT / "esco_extension" / "combined"
PARTS = ("train", "validation", "test")
OLD_NAMES = {"train": "pairs_train.csv", "validation": "pairs_val.csv", "test": "pairs_test.csv"}


def read_old(part: str) -> list[dict[str, str]]:
    with (OLD_ROOT / OLD_NAMES[part]).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def read_extension(part: str) -> list[dict[str, str]]:
    path = ROOT / "esco_extension" / "data" / f"esco_extension_{part}.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    old = {part: read_old(part) for part in PARTS}
    old_keys = {
        (row["occupation_id"], row["concept_id"])
        for rows in old.values() for row in rows
    }
    combined: dict[str, list[dict[str, str]]] = {}
    added_counts = {}
    removed_duplicates = {}
    for part in PARTS:
        extension = read_extension(part)
        unique_extension = [
            row for row in extension
            if (row["occupation_id"], row["skill_id"]) not in old_keys
        ]
        removed_duplicates[part] = len(extension) - len(unique_extension)
        added_counts[part] = len(unique_extension)
        combined[part] = [
            {
                "occupation_id": row["occupation_id"],
                "text_left": row["text_left"],
                "concept_id": row["concept_id"],
                "text_right": row["text_right"],
                "label": row["label"],
                "source": "esco_historique",
                "course_scope": "ict",
            }
            for row in old[part]
        ] + [
            {
                "occupation_id": row["occupation_id"],
                "text_left": row["occupation_label_fr"],
                "concept_id": row["skill_id"],
                "text_right": row["skill_label_fr"],
                "label": row["label"],
                "source": "esco_extension_v1.2.0",
                "course_scope": row["course"],
            }
            for row in unique_extension
        ]

    fields = ["occupation_id", "text_left", "concept_id", "text_right", "label", "source", "course_scope"]
    for part, rows in combined.items():
        with (OUTPUT / f"pairs_{part}.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    occupation_parts: dict[str, set[str]] = defaultdict(set)
    pair_parts: dict[tuple[str, str], set[str]] = defaultdict(set)
    for part, rows in combined.items():
        for row in rows:
            occupation_parts[row["occupation_id"]].add(part)
            pair_parts[(row["occupation_id"], row["concept_id"])].add(part)
    manifest = {
        "historical_counts": {part: len(old[part]) for part in PARTS},
        "extension_added": added_counts,
        "extension_duplicates_removed": removed_duplicates,
        "combined_counts": {part: len(combined[part]) for part in PARTS},
        "pair_leakage_count": sum(len(parts) > 1 for parts in pair_parts.values()),
        "occupation_leakage_count": sum(len(parts) > 1 for parts in occupation_parts.values()),
        "note": "Le split historique de l'article est conservé pour comparabilité; l'audit signale ses éventuelles fuites par métier.",
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

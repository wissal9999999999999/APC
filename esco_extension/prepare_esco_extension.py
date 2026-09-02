#!/usr/bin/env python3
"""Extraire les paires métier-compétence ESCO pour les nouveaux cours."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

from rdflib import Graph, Namespace
from rdflib.namespace import RDF, SKOS


ESCO = Namespace("http://data.europa.eu/esco/model#")
ISCO_BASE = "http://data.europa.eu/esco/isco/C"


def french_label(graph: Graph, uri) -> str | None:
    for label in graph.objects(uri, SKOS.prefLabel):
        if label.language == "fr":
            return str(label).strip()
    return None


def read_codes(path: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            result[row["course"].strip()].add(row["isco_code"].strip())
    return dict(result)


def split_by_occupation(rows: list[dict[str, str]], seed: int = 42):
    occupation_ids = sorted({row["occupation_id"] for row in rows})
    random.Random(seed).shuffle(occupation_ids)
    count = len(occupation_ids)
    train_end = round(count * 0.8)
    val_end = train_end + round(count * 0.1)
    split = {
        occupation_id: "train" if i < train_end else "validation" if i < val_end else "test"
        for i, occupation_id in enumerate(occupation_ids)
    }
    return split


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rdf", type=Path, default=Path("data/esco_raw/esco-v1.2.0.rdf"))
    parser.add_argument("--codes", type=Path, default=Path("esco_extension/candidate_isco_codes.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("esco_extension/data"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    codes_by_course = read_codes(args.codes)
    all_codes = sorted(set().union(*codes_by_course.values()))
    print(f"Chargement RDF ESCO : {args.rdf}")
    graph = Graph()
    graph.parse(args.rdf, format="xml")
    print(f"Graphe chargé : {len(graph):,} triplets")

    occupations_by_code: dict[str, set] = defaultdict(set)
    for code in all_codes:
        isco_uri = graph.resource(f"{ISCO_BASE}{code}").identifier
        occupations_by_code[code].update(graph.subjects(SKOS.broaderTransitive, isco_uri))
        occupations_by_code[code].update(graph.subjects(SKOS.broader, isco_uri))

    relation_properties = (ESCO.relatedEssentialSkill, ESCO.relatedOptionalSkill)
    rows_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for course, codes in codes_by_course.items():
        for code in codes:
            for occupation in occupations_by_code[code]:
                occupation_label = french_label(graph, occupation)
                if not occupation_label:
                    continue
                for relation in relation_properties:
                    relation_type = "essential" if relation == ESCO.relatedEssentialSkill else "optional"
                    for skill in graph.objects(occupation, relation):
                        skill_label = french_label(graph, skill)
                        if not skill_label:
                            continue
                        key = (course, str(occupation), str(skill))
                        rows_by_key[key] = {
                            "course": course,
                            "isco_code": code,
                            "occupation_id": str(occupation),
                            "occupation_label_fr": occupation_label,
                            "skill_id": str(skill),
                            "skill_label_fr": skill_label,
                            "relation_type": relation_type,
                            "label": "1",
                        }

    rows = sorted(rows_by_key.values(), key=lambda row: (
        row["course"], row["occupation_label_fr"], row["skill_label_fr"]
    ))
    split = split_by_occupation(rows, seed=args.seed)
    for row in rows:
        row["split"] = split[row["occupation_id"]]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = ["course", "isco_code", "occupation_id", "occupation_label_fr",
              "skill_id", "skill_label_fr", "relation_type", "label", "split"]
    for name, selected in [("all", rows)] + [
        (part, [row for row in rows if row["split"] == part])
        for part in ("train", "validation", "test")
    ]:
        with (args.output_dir / f"esco_extension_{name}.csv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(selected)

    summary = {
        "esco_version": "1.2.0",
        "seed": args.seed,
        "courses": {
            course: {
                "isco_codes": sorted(codes),
                "occupations": len({row["occupation_id"] for row in rows if row["course"] == course}),
                "pairs": sum(row["course"] == course for row in rows),
            }
            for course, codes in codes_by_course.items()
        },
        "splits": {part: sum(row["split"] == part for row in rows)
                   for part in ("train", "validation", "test")},
        "unique_occupations": len({row["occupation_id"] for row in rows}),
        "unique_skills": len({row["skill_id"] for row in rows}),
        "pairs": len(rows),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Convertit les alignements AC/AAD des fichiers XML en fichiers CSV."""

import csv
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
AC_CATALOG = BASE_DIR.parent / "backend" / "exports" / "ac_iti.json"
OUTPUT_DIR = BASE_DIR / "csv"
HEADERS = ["AC-ID", "AC-TITLE", "AAD-ID", "AAD-TITLE", "LABEL"]


def normalized_text(element):
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def load_ac_titles():
    with AC_CATALOG.open(encoding="utf-8") as stream:
        return {
            item["AC-ID"]: item.get("AC-TITLE", "")
            for item in json.load(stream)
        }


def extract_rows(xml_path, ac_titles):
    root = ET.parse(xml_path).getroot()
    aad_titles = {}

    for aad in root.iter("attendu-apprentissage-disciplinaire"):
        aad_id = aad.get("id")
        if aad_id:
            aad_titles[aad_id] = normalized_text(aad.find("titre"))

    rows = []
    warnings = []
    for alignment in root.findall("./alignements/alignement"):
        ac = next(
            (
                child
                for child in alignment
                if child.tag
                in ("apprentissage-critique", "apprentissage-critique-huma")
            ),
            None,
        )
        if ac is None or not ac.get("ref"):
            warnings.append(f"{xml_path.name}: alignement sans AC")
            continue

        ac_id = ac.get("ref")
        ac_title = ac_titles.get(ac_id, "")
        if not ac_title:
            warnings.append(f"{xml_path.name}: titre AC introuvable pour {ac_id}")

        for aad_ref in alignment.findall("attendu-apprentissage-disciplinaire"):
            aad_id = aad_ref.get("ref", "")
            aad_title = aad_titles.get(aad_id, "")
            if not aad_title:
                warnings.append(f"{xml_path.name}: AAD introuvable pour {aad_id}")
            rows.append(
                {
                    "AC-ID": ac_id,
                    "AC-TITLE": ac_title,
                    "AAD-ID": aad_id,
                    "AAD-TITLE": aad_title,
                    "LABEL": 1,
                }
            )

    return rows, warnings


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    ac_titles = load_ac_titles()
    OUTPUT_DIR.mkdir(exist_ok=True)
    all_rows = []
    all_warnings = []

    for xml_path in sorted(BASE_DIR.glob("*.xml")):
        rows, warnings = extract_rows(xml_path, ac_titles)
        write_csv(OUTPUT_DIR / f"{xml_path.stem}.csv", rows)
        all_rows.extend(rows)
        all_warnings.extend(warnings)
        print(f"{xml_path.name}: {len(rows)} lignes")

    write_csv(OUTPUT_DIR / "alignements_complets.csv", all_rows)
    print(f"alignements_complets.csv: {len(all_rows)} lignes")
    for warning in dict.fromkeys(all_warnings):
        print(f"ATTENTION: {warning}", file=sys.stderr)


if __name__ == "__main__":
    main()

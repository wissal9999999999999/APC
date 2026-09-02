"""Run one semantic alignment with the SMA Python environment."""

import json
import sys

from sentence_transformers import SentenceTransformer

from aad_prototype.catalogs import AADRecord, ACRecord
from aad_prototype.cosine_alignment import (
    DEFAULT_EMBEDDING_MODEL,
    rank_acs_by_cosine,
)


MODEL_NAME = DEFAULT_EMBEDDING_MODEL


def main():
    payload = json.load(sys.stdin)
    rows = payload["ac_rows"]
    if not rows:
        print("[]")
        return

    ac_catalog = {
        row["AC-ID"]: ACRecord(ac_id=row["AC-ID"], title=row["AC-TITLE"])
        for row in rows
    }
    model = SentenceTransformer(MODEL_NAME, local_files_only=True)
    results = []

    for item in payload["aad_items"]:
        aad = AADRecord(aad_id=item["aad_id"], title=item["aad_text"])
        ranking = rank_acs_by_cosine(aad, ac_catalog, model)
        matches = []

        for match in ranking:
            if match.cosine_similarity < payload["threshold"]:
                continue
            matches.append({
                "rank": match.rank,
                "ac_id": match.ac_id,
                "ac_title": match.ac_title,
                "score": round(match.cosine_similarity, 4),
            })
            if len(matches) >= payload["limit"]:
                break

        results.append({
            "aad_id": item["aad_id"],
            "aad_text": item["aad_text"],
            "top_match": matches[0] if matches else None,
            "matches": matches,
        })

    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()

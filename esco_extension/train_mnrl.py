#!/usr/bin/env python3
"""Fine-tuning MNRL sur le corpus ESCO historique + extension validée."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path

import numpy as np

# TensorBoard ancien (présent dans bleurt-env) utilise encore np.bool8, alias
# retiré de NumPy 2. Le rétablir localement évite de modifier l'environnement.
if not hasattr(np, "bool8"):
    np.bool8 = np.bool_

import torch
from sentence_transformers import InputExample, SentenceTransformer, datasets, losses


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def positive_examples(path: Path) -> list[InputExample]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    seen = set()
    examples = []
    for row in rows:
        if row["label"] != "1":
            continue
        key = (row["text_left"].strip(), row["text_right"].strip())
        if not all(key) or key in seen:
            continue
        seen.add(key)
        examples.append(InputExample(texts=list(key)))
    return examples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("esco_extension/combined"))
    parser.add_argument("--output-dir", type=Path, default=Path("esco_extension/checkpoints/esco_extended_mnrl"))
    parser.add_argument("--model", default="dangvantuan/sentence-camembert-large")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()

    seed_everything(args.seed)
    examples = positive_examples(args.data_dir / "pairs_train.csv")
    batches_per_epoch = math.ceil(len(examples) / args.batch_size)
    warmup_steps = int(batches_per_epoch * args.epochs * args.warmup_ratio)
    config = {
        "model": args.model,
        "positive_train_pairs": len(examples),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "warmup_ratio": args.warmup_ratio,
        "warmup_steps": warmup_steps,
        "seed": args.seed,
        "cuda_available": torch.cuda.is_available(),
        "loss": "MultipleNegativesRankingLoss",
    }
    print(json.dumps(config, ensure_ascii=False, indent=2))
    if args.preflight:
        return
    if not torch.cuda.is_available():
        raise RuntimeError("Un GPU CUDA est requis pour ce fine-tuning Sentence-CamemBERT-Large.")

    model = SentenceTransformer(args.model, device="cuda")
    loader = datasets.NoDuplicatesDataLoader(examples, batch_size=args.batch_size)
    loss = losses.MultipleNegativesRankingLoss(model)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model.fit(
        train_objectives=[(loader, loss)],
        epochs=args.epochs,
        optimizer_params={"lr": args.learning_rate},
        warmup_steps=warmup_steps,
        output_path=str(args.output_dir),
        show_progress_bar=True,
        use_amp=True,
    )
    (args.output_dir / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

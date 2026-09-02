#!/usr/bin/env bash
set -euo pipefail

# L'entraînement utilise uniquement PyTorch. Empêcher Transformers d'importer
# un éventuel TensorFlow ancien présent dans l'environnement (p. ex. BLEURT).
export USE_TF=0
export TRANSFORMERS_NO_TF=1
export TOKENIZERS_PARALLELISM=false

# Une valeur vide masque tous les GPU à PyTorch. Elle peut rester définie par
# un ancien environnement ou un script lancé avant cet entraînement.
unset CUDA_VISIBLE_DEVICES

python esco_extension/train_mnrl.py \
  --data-dir esco_extension/combined \
  --output-dir esco_extension/checkpoints/esco_extended_mnrl \
  --model dangvantuan/sentence-camembert-large \
  --epochs 3 \
  --batch-size 8 \
  --learning-rate 2e-5 \
  --warmup-ratio 0.1 \
  --seed 42

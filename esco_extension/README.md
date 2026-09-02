# Extension ESCO pour les nouveaux cours

Ce dossier prépare les paires françaises métier–compétence pour `auto`,
`bigdata`, `capt` et `ddrs31` depuis ESCO v1.2.0.

Les codes de `candidate_isco_codes.csv` sont retenus par **sélection heuristique
sans validation experte**. Cette limite doit être mentionnée dans l'article. Le découpage 80/10/10 est
réalisé par métier afin d'empêcher qu'un même métier apparaisse dans plusieurs
partitions.

```bash
/home/wissal/Téléchargements/SMA/.venv/bin/python \
  esco_extension/prepare_esco_extension.py

python3 esco_extension/build_combined_splits.py

/home/wissal/Téléchargements/SMA/.venv/bin/python \
  esco_extension/train_mnrl.py --preflight
```

Le lancement réel de `train_mnrl.py` exige CUDA. Les paramètres par défaut
reproduisent ceux retrouvés dans le notebook historique : 3 époques, batch 8,
taux d'apprentissage `2e-5`, warmup 10 %, seed 42 et MNRL.

## Protocole retenu

- ESCO v1.2.0, afin de rester cohérent avec les données historiques ;
- sélection automatique des codes ISCO par proximité disciplinaire ;
- fusion avec les splits historiques de l'article ;
- entraînement uniquement sur les paires positives avec MNRL ;
- validation ESCO séparée ;
- test final AC-AAD totalement absent de l'entraînement.

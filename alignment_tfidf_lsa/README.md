# Alignement TF-IDF et LSA

Ce dossier évalue l'alignement AC-AAD pour `auto`, `bigdata`, `capt` et
`ddrs31`. Les fichiers `data/AADAC/*.csv` sont interprétés comme la liste des
alignements positifs ; toutes les autres paires du produit AC × AAD reçoivent
le label 0.

## Exécution

```bash
python alignment_tfidf_lsa/run_alignment.py
python alignment_tfidf_lsa/run_sentence_camembert.py
python alignment_tfidf_lsa/run_hybrids.py
```

Le script produit :

- `results/summary.csv` : AUC-ROC moyenne des AC évaluables ;
- `results/scores/` : score de chaque paire AC-AAD ;
- `results/auc_by_ac/` : métriques détaillées par AC ;
- `results/warnings.json` : alignements impossibles à évaluer faute de texte.

TF-IDF utilise des unigrammes. LSA applique une SVD tronquée à
la matrice TF-IDF commune aux AC et AAD, avec au maximum 100 composantes et
une graine fixée à 42.

Sentence-CamemBERT-Large utilise le modèle français
`Lajavaness/sentence-camembert-large`, des embeddings normalisés et la
similarité cosinus. Par défaut, son chargement est strictement local.

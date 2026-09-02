# Alignement ColBERTv2 français

Le script évalue tous les cours présents dans `data` avec le checkpoint
français `antoinelouis/colbertv2-camembert-L4-mmarcoFR`.

Les AAD sont encodés comme requêtes, les AC comme documents, et le score d'une
paire est le Mean MaxSim ColBERT. La métrique finale est la moyenne des AUC-ROC
des AC évaluables.

```bash
/home/wissal/Téléchargements/SMA/.venv/bin/python alignment_colbert/run_colbert_all_courses.py
```

Les résultats sont écrits dans `alignment_colbert/results`.

## Second modèle multi-vectoriel

`run_jina_colbert_all_courses.py` évalue le modèle multilingue
`jinaai/jina-colbert-v2` avec PyLate et écrit ses résultats dans
`alignment_colbert/results_jina`.

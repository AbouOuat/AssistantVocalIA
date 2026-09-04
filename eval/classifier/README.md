# Harness d'évaluation — classifieur e-mail v1 vs v2

Objectif : mesurer objectivement si **v2** (Path B, sortie `json_schema` strict) fait mieux
que **v1** (appel OpenAI direct + `JSON.parse`) sur `urgence` et `action`, avec un jeu
d'e-mails annoté à la main. Répond à la question restée ouverte de l'audit
(`DOCS/reports/repo-vs-n8n-prod-2026-09-01.md` §5) et sert la puce CV « éval precision/recall ».

## Fichiers

| Fichier | Rôle |
|---|---|
| `prompts.py` | Les 2 constructions de prompt (v1, v2) + le JSON Schema v2. **À garder en phase** avec `workflows/gmail-email-classifier*.json`. |
| `run_eval.py` | Rejoue v1 et v2 sur le dataset, calcule P/R/F1 par classe + matrice de confusion, écrit `DOCS/reports/classifier-eval-<date>.md`. |
| `dataset.template.csv` | En-tête seul, à remplir. |
| `dataset.example.csv` | 5 lignes fictives — pour valider le pipeline (`--dry-run`). |

## Procédure

1. **Constituer le jeu** : 30–50 e-mails réels dans `dataset.csv` (colonnes
   `id,source,sender,subject,body`), puis **annoter à la main** `label_urgence`
   (`haute|moyenne|faible`) et `label_action` (`repondre|lire|relancer|classer|aucune`).
   - Astuce : exporter depuis Outlook/Gmail, ou copier des lignes du dossier `sessions/` /
     des synthèses passées. Viser un mélange réaliste (quelques urgents, beaucoup de faible).
2. **Lancer** :
   ```bash
   python eval/classifier/run_eval.py eval/classifier/dataset.csv
   ```
   (nécessite `OPENAI_API_KEY` — lu depuis `.env`. ~1 appel / 10 e-mails / variante.)
3. **Lire** le rapport `DOCS/reports/classifier-eval-<date>.md` et le commiter.

Validation du pipeline sans clé ni annotation :
```bash
python eval/classifier/run_eval.py eval/classifier/dataset.example.csv --dry-run
```

## Décision attendue

- v2 ≤ v1 en macro-F1 sur les 2 champs → **v1 reste le moteur** (`WORKFLOW_VERSION=v1`),
  v2 gardée pour le toggle. Le gain réel de v2 = robustesse du format, pas la qualité.
- v2 > v1 nettement → envisager `WORKFLOW_VERSION=v2` + bascule du cron (cf. plan §7).

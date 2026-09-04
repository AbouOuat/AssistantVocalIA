# Harness d'évaluation — RAG (T2)

Mesure le **hit rate @k** du retrieval pgvector : sur un jeu de questions de référence,
le document attendu apparaît-il dans le top-k retourné par `rag_service.search()` ?

## Fichiers

| Fichier | Rôle |
|---|---|
| `qa_reference.template.csv` | En-tête seul, à remplir. |
| `qa_reference.example.csv` | 5 questions basées sur les 4 sessions de test générées (`sessions/2026-09-04-*.md`). |
| `run_eval.py` | Rejoue le jeu, calcule le hit rate @k, écrit `DOCS/reports/rag-eval-<date>.md`. |

## Prérequis

1. Postgres avec extension `pgvector` (`docker-compose.yml` : image `pgvector/pgvector:pg16`).
2. `pip install -r requirements_backend.txt` (ajoute le paquet `pgvector`).
3. Ingestion faite : `python backend/scripts/ingest_rag.py` (peuple la table `documents`
   depuis Redis `emails_structured` + `sessions/*.md`).
4. `OPENAI_API_KEY` (lu depuis `.env`).

## Lancer

```bash
python eval/rag/run_eval.py eval/rag/qa_reference.csv
```

Valider le pipeline sans DB ni clé :
```bash
python eval/rag/run_eval.py eval/rag/qa_reference.example.csv --dry-run
```

## État au 2026-09-04

Le pipeline (script + format de rapport) est validé en `--dry-run`. **Le run réel
(ingestion + éval contre un Postgres pgvector) n'a pas pu être exécuté dans cette
session** : `docker pull pgvector/pgvector:pg16` échoue systématiquement dans ce
sandbox (`httpReadSeeker: failed open ... EOF` sur le CDN Docker Hub — 3 tentatives,
même échec). Le reste de l'environnement Docker local (postgres:16-alpine, redis,
n8n) est intact et fonctionnel. À relancer sur une machine/CI avec accès Docker Hub
complet, ou après un `docker compose up -d postgres` réussi.

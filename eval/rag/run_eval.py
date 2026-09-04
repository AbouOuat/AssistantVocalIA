"""Harness d'évaluation du RAG (T2) — hit rate @k.

Rejoue un jeu de questions de référence contre backend.services.rag_service.search
et vérifie si la source attendue figure dans le top-k retourné. Écrit un rapport
Markdown dans DOCS/reports/.

Usage :
    python eval/rag/run_eval.py eval/rag/qa_reference.csv
    python eval/rag/run_eval.py eval/rag/qa_reference.example.csv --dry-run

qa_reference CSV attendu (une ligne = une question) :
    question,expected_source,expected_external_id
Exemple : "qu'est-ce qu'on a décidé sur le RAG ?",session,2026-09-04-...-plan-action-notes-reunion-produit.md

Nécessite : la table `documents` peuplée (backend/scripts/ingest_rag.py), OPENAI_API_KEY,
DATABASE_URL pointant vers un Postgres avec pgvector. --dry-run n'appelle ni l'API ni
la DB (hits tirés au hasard) — sert à valider le pipeline / le format du rapport.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def load_env() -> None:
    envf = REPO / ".env"
    if not envf.exists():
        return
    for line in envf.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"'))


def read_qa(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            q = (r.get("question") or "").strip()
            if not q:
                continue
            rows.append({
                "question": q,
                "expected_source": (r.get("expected_source") or "").strip(),
                "expected_external_id": (r.get("expected_external_id") or "").strip(),
            })
    return rows


async def run(rows: list[dict], user_id: int, k: int, dry_run: bool) -> list[dict]:
    out = []
    if dry_run:
        for r in rows:
            hit = random.random() < 0.5
            out.append({**r, "hit": hit, "rank": (random.randint(1, k) if hit else None)})
        return out

    from backend.services.rag_service import search

    for r in rows:
        results = await search(user_id, r["question"], k=k)
        rank = None
        for i, res in enumerate(results, start=1):
            if r["expected_external_id"] and res["external_id"] == r["expected_external_id"]:
                rank = i
                break
            if not r["expected_external_id"] and r["expected_source"] and res["source"] == r["expected_source"]:
                rank = i
                break
        out.append({**r, "hit": rank is not None, "rank": rank})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("qa_file")
    ap.add_argument("--user-id", type=int, default=2)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true", help="pas d'appel API/DB, hits aléatoires")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    random.seed(args.seed)
    load_env()

    rows = read_qa(Path(args.qa_file))
    if not rows:
        print("Aucune question dans", args.qa_file)
        return 1
    if not args.dry_run and not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY manquant (ou utilise --dry-run).")
        return 1

    import asyncio
    results = asyncio.run(run(rows, args.user_id, args.k, args.dry_run))

    hits = sum(1 for r in results if r["hit"])
    hit_rate = hits / len(results) if results else 0.0
    date = dt.date.today().isoformat()

    md = [
        "# Évaluation RAG — hit rate @k\n",
        f"**Date** : {date}  |  **Jeu** : `{args.qa_file}` ({len(results)} questions)  |  **k** : {args.k}"
        + ("  |  ⚠️ **DRY-RUN**" if args.dry_run else ""),
        f"\n**Hit rate @{args.k}** : {hits}/{len(results)} = **{hit_rate:.0%}**\n",
        "---\n",
        "| Question | Source attendue | Trouvée ? | Rang |",
        "|---|---|---|---|",
    ]
    for r in results:
        exp = r["expected_external_id"] or r["expected_source"] or "?"
        md.append(f"| {r['question'][:70]} | {exp} | {'✅' if r['hit'] else '❌'} | {r['rank'] or '-'} |")
    md += [
        "\n---\n",
        "## Lecture",
        "- Hit rate @k = proportion de questions où le document attendu apparaît dans le top-k.",
        "- Un hit rate bas peut venir du chunking (1 chunk = 1 document, pas de découpage fin), "
        "du modèle d'embedding, ou d'un corpus encore trop petit pour discriminer.",
    ]

    out = REPO / "DOCS" / "reports" / f"rag-eval-{date}.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Hit rate @{args.k} : {hits}/{len(results)} = {hit_rate:.0%}")
    print("écrit :", out.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

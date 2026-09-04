"""Ingestion RAG (T2) — peuple la table `documents` (pgvector) à partir de :
1. synthèses e-mails classifiées, archivées Redis (memory_service, scope "context") ;
2. exports Session Summary, sessions/*.md.

Batch/manuel (pas de hook temps réel dans le pipeline live — cf.
DOCS/plans/cv-embellissement-scope.md T2). Idempotent : ré-exécutable sans dupliquer
(upsert par user_id/source/external_id).

Usage : python backend/scripts/ingest_rag.py [--user-id 2]
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services.memory_service import memory_service  # noqa: E402
from backend.services.rag_service import upsert_document  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SESSIONS_DIR = REPO / "sessions"


def _format_email(e: dict) -> str:
    parts = [
        f"E-mail de {e.get('from_name') or e.get('from', '?')} <{e.get('from_email', '')}>",
        f"Objet : {e.get('subject', '(sans objet)')}",
        f"Urgence : {e.get('urgence', 'faible')} | Action : {e.get('action', 'lire')}",
    ]
    if e.get("echeance"):
        parts.append(f"Échéance : {e['echeance']}")
    if e.get("resume"):
        parts.append(f"Résumé : {e['resume']}")
    elif e.get("snippet"):
        parts.append(f"Extrait : {e['snippet'][:300]}")
    return "\n".join(parts)


async def ingest_emails(user_id: int) -> int:
    n = 0
    for scope_key, src in (
        ("recent_emails_gmail", "gmail"),
        ("recent_emails_outlook", "outlook"),
    ):
        try:
            emails = await memory_service.get(user_id, "context", scope_key)
        except Exception as e:
            print(f"  ! Redis indisponible pour {scope_key} ({e}) — ignoré")
            continue
        if not emails:
            print(f"  - {scope_key} : rien en mémoire")
            continue
        for e in emails:
            eid = str(e.get("id") or e.get("subject", "")[:40])
            if not eid:
                continue
            await upsert_document(
                user_id=user_id,
                content=_format_email(e),
                source="email",
                external_id=f"{src}:{eid}",
                metadata={
                    "mailbox": src,
                    "subject": e.get("subject"),
                    "urgence": e.get("urgence"),
                    "action": e.get("action"),
                    "date": e.get("echeance") or "",
                },
            )
            n += 1
        print(f"  - {scope_key} : {len(emails)} e-mail(s) ingéré(s)")
    return n


def _extract_title(md: str, fallback: str) -> str:
    m = re.search(r"^#\s*(.+)$", md, re.MULTILINE)
    return m.group(1).strip() if m else fallback


async def ingest_sessions(user_id: int) -> int:
    n = 0
    files = sorted(SESSIONS_DIR.glob("*.md"))
    if not files:
        print("  - sessions/*.md : dossier vide")
        return 0
    for f in files:
        content = f.read_text(encoding="utf-8")
        if not content.strip():
            continue
        title = _extract_title(content, f.stem)
        await upsert_document(
            user_id=user_id,
            content=content,
            source="session",
            external_id=f.name,
            metadata={"title": title, "file": f.name},
        )
        n += 1
    print(f"  - sessions/*.md : {n} fichier(s) ingéré(s)")
    return n


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-id", type=int, default=2)
    args = ap.parse_args()

    print(f"Ingestion RAG — user_id={args.user_id}")
    print("Synthèses e-mails (Redis) :")
    n_email = await ingest_emails(args.user_id)
    print("Sessions (sessions/*.md) :")
    n_session = await ingest_sessions(args.user_id)

    total = n_email + n_session
    print(f"\nTotal : {total} document(s) indexé(s) ({n_email} e-mails, {n_session} sessions)")
    if total == 0:
        print("Rien à indexer — vérifie que Redis contient des analyses e-mails "
              "et/ou que sessions/*.md n'est pas vide.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

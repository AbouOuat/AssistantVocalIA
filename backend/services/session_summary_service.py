"""Session Summary — résumé de session (historique + mémoire) + export Markdown.

Complète un écart trouvé le 2026-09-04 : CLAUDE.md décrit "Session Summary — déclenché
par 'Jarvis, close session' ... export .md dans /sessions/", mais le handler WS
`session_summary` (backend/main.py) ne faisait que renvoyer le texte sur le
WebSocket — aucun fichier n'était jamais écrit. Ce module extrait la génération
(logique inchangée) et ajoute la persistance qui manquait.
"""
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from backend.services.ai_service import ConversationContext, chat_completion_stream

logger = logging.getLogger(__name__)

SESSIONS_DIR = Path(__file__).resolve().parents[2] / "sessions"


async def generate_session_summary(history_preview: list[str], memory_snapshot: dict) -> str:
    """Résume une session (historique + mémoire) en 3-5 bullets via LLM.

    Logique identique à l'ancien code inline de main.py — inchangée, seulement extraite.
    """
    summary_prompt = (
        "Résume cette session en 3-5 bullets (décisions, tâches, mémos):\n"
        f"Historique: {history_preview}\n"
        f"Mémoire: {memory_snapshot}"
    )
    ctx = ConversationContext()
    summary = ""
    async for chunk in chat_completion_stream(summary_prompt, ctx, temperature=0.3):
        summary += chunk
    return summary


def _slug(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "session"


def export_session_summary_md(
    summary: str,
    user_id: int,
    title: str | None = None,
    out_dir: Path | None = None,
) -> Path:
    """Écrit l'export Session Summary en Markdown dans sessions/ (CLAUDE.md)."""
    out_dir = out_dir or SESSIONS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    slug = _slug(title or "session")
    filename = f"{now.strftime('%Y-%m-%d-%H%M%S')}-{slug}.md"
    path = out_dir / filename
    content = (
        f"# Session Summary — {now.strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        f"**Utilisateur** : {user_id}\n"
        f"**Généré** : {now.isoformat()}\n\n"
        "## Résumé\n\n"
        f"{summary.strip()}\n"
    )
    path.write_text(content, encoding="utf-8")
    logger.info(f"[session_summary] export écrit : {path}")
    return path

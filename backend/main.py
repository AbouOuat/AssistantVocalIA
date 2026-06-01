"""Jarvis Backend — FastAPI + WebSocket pipeline complet."""

import json
import logging
import os
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.services.ai_service import ConversationContext, chat_completion_stream
from backend.services.memory_service import memory_service
from backend.services.voice_service import (
    check_realtime_access,
    decode_audio_base64,
    encode_audio_base64,
    process_voice_message,
)
from backend.services.realtime_service import realtime_session
from backend.services.n8n_service import init_n8n, call_webhook
from backend.services.domotics_service import init_domotics
from backend.services.auth_service import ensure_demo_user_exists, verify_jwt_token
from backend.models import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

# Global demo token for hackathon (single user)
_demo_token: str | None = None
_demo_user_id: int | None = None
_realtime_ok: bool = False

# Contextes de conversation par connexion WebSocket (keyed by user_id)
_contexts: dict[int, ConversationContext] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _demo_token, _demo_user_id, _realtime_ok
    logger.info("🚀 Jarvis backend démarrage...")

    # Initialize database
    init_db()

    # Create or get demo user (hackathon single user)
    demo_email = os.getenv("GMAIL_USER_EMAIL", "demo@jarvis.local")
    _demo_user_id, _demo_token = await ensure_demo_user_exists(demo_email)
    logger.info(f"✓ Demo user created/loaded: {demo_email} (user_id={_demo_user_id})")

    init_n8n()
    init_domotics()
    _realtime_ok = await check_realtime_access()
    mode = "[REALTIME]" if _realtime_ok else "[WHISPER_FALLBACK]"
    logger.info(f"✓ Mode voix: {mode}")
    yield
    await memory_service.close()
    logger.info("👋 Jarvis backend arrêt")


app = FastAPI(
    title="Jarvis V2",
    description="Assistant IA vocal intelligent",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://145.223.34.178:3000",
        "http://145.223.34.178",
        "https://jarvis.obyz.biz",
        "http://jarvis.obyz.biz",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_email_limit(text: str) -> int:
    """Extrait et valide la limite d'emails depuis le texte utilisateur."""
    match = re.search(r'\b(\d+)\b', text)
    if not match:
        return 10
    limit = int(match.group(1))
    if limit < 1:
        return 1
    if limit > 50:
        return 50
    return limit


async def _handle_n8n_command(text: str, user_id: int) -> str | None:
    """Détecte les commandes quick actions et appelle le webhook n8n correspondant."""
    t = text.lower().strip()

    # ── Morning Briefing ─────────────────────────────────────────────────────
    if any(k in t for k in ["start my day", "morning briefing", "commence ma journée"]):
        result = await call_webhook("morning-briefing", {"user_id": user_id})
        if not result:
            return (
                "⚠️ Le workflow Morning Briefing est injoignable.\n"
                "→ Vérifie que le workflow '[DEV] Morning Briefing' est actif sur n8n.obyz.biz."
            )
        return result.get("briefing", "Briefing reçu mais format inattendu.")

    # ── Classification / récapitulatif emails ────────────────────────────────
    CLASSIFY_KEYWORDS = [
        "classify", "classif", "classify emails", "classify my emails",
        "email summary", "synthèse emails", "synthese emails",
        "récapitulatif", "recapitulatif", "résumé des mails", "resume des mails",
        "analyse mes", "analyze my last", "last emails", "derniers mails",
    ]
    if any(k in t for k in CLASSIFY_KEYWORDS) or (
        any(k in t for k in ["email", "mail", "mails", "emails"]) and
        any(k in t for k in ["analyse", "analyze", "résumé", "resume", "classify", "class"])
    ):
        limit = _parse_email_limit(t)
        limit_note = " (limité à 50 par sécurité)" if re.search(r'\b(\d+)\b', t) and int(re.search(r'\b(\d+)\b', t).group(1)) > 50 else ""

        result = await call_webhook("email-classifier", {"user_id": user_id, "limit": limit})

        if not result:
            return (
                "⚠️ Le workflow de classification emails est injoignable.\n"
                "→ Vérifie que le workflow '[DEV] Gmail Email Classifier' est actif sur n8n.obyz.biz\n"
                "→ Et que le credential Gmail est configuré."
            )

        processed = result.get("processed", 0)
        skipped = result.get("skipped", 0)

        if result.get("no_emails") or processed == 0:
            if skipped > 0:
                return (
                    f"📭 Aucun email à classifier parmi les {limit} derniers{limit_note}.\n"
                    f"{skipped} email(s) ignoré(s) automatiquement (newsletters, no-reply, trop anciens)."
                )
            return f"✅ Aucun nouvel email dans les 8 dernières heures{limit_note}."

        summary = result.get("summary", "")
        header = f"📧 Classification de tes {processed} dernier(s) email(s){limit_note} :\n\n"
        footer = f"\n\n✉️ Synthèse envoyée à {result.get('summary_sent_to', 'ton Gmail')}."
        return header + summary + footer

    # ── Check emails prioritaires (Morning Briefing) ─────────────────────────
    if ("check" in t and "email" in t) or ("emails" in t and "priorit" in t):
        result = await call_webhook("morning-briefing", {"user_id": user_id})
        if not result:
            return (
                "⚠️ Impossible d'accéder à Gmail pour l'instant.\n"
                "→ Active le workflow Morning Briefing dans n8n.obyz.biz."
            )
        return f"📧 Tes emails prioritaires :\n\n{result.get('briefing', 'Aucune donnée.')}"

    # ── Smart Agent — analyse de notes ────────────────────────────────────────
    if any(k in t for k in ["analyze my notes", "analyse mes notes", "my notes"]):
        notes = text.split(":", 1)[-1].strip() if ":" in text else ""
        if not notes:
            return (
                "📝 Envoie-moi tes notes à analyser.\n"
                "Exemple : \"Analyze my notes: réunion lundi, budget Q3, relancer client X\""
            )
        result = await call_webhook("smart-agent", {"user_id": user_id, "notes": notes})
        if not result:
            return (
                "⚠️ Le workflow Smart Agent est injoignable.\n"
                "→ Active le workflow dans n8n.obyz.biz et configure le credential OpenAI."
            )
        if not result.get("action_plan"):
            return "⚠️ L'analyse n'a pas retourné de plan d'action. Réessaie avec des notes plus détaillées."
        plan = "\n".join(f"• {step}" for step in result["action_plan"])
        email_status = "📩 Email draft créé et envoyé." if result.get("email_sent") else ""
        return f"📋 Plan d'action :\n\n{plan}\n\n{email_status}".strip()

    return None


@app.get("/")
async def root():
    return {"status": "ok", "message": "Jarvis V2 is running 🤖", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/devices")
async def get_devices():
    from backend.services.domotics_service import domotics_service
    if not domotics_service:
        return {"devices": []}
    return {"devices": await domotics_service.get_devices()}


@app.get("/api/config")
async def get_config():
    """Return demo token and runtime capabilities for hackathon frontend."""
    return {"token": _demo_token, "user_id": _demo_user_id, "realtime_mode": _realtime_ok}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    # Validate token and extract user_id
    user_id = verify_jwt_token(token) if token else None
    if user_id is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    _contexts[user_id] = ConversationContext(user_id=str(user_id))
    logger.info(f"✓ Client WebSocket connecté [user_id={user_id}]")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "")

            # ── Chat texte ──────────────────────────────────────────────────
            if msg_type == "chat":
                content = message.get("content", "").strip()
                if not content:
                    continue
                ctx = _contexts[user_id]
                full_response = ""

                # Détection des commandes quick actions → n8n
                n8n_response = await _handle_n8n_command(content, user_id)
                if n8n_response:
                    ctx.add_message("user", content)
                    ctx.add_message("assistant", n8n_response)
                    await websocket.send_text(json.dumps({
                        "type": "response",
                        "content": n8n_response,
                    }))
                    continue

                # Streaming GPT-4o standard
                async for chunk in chat_completion_stream(content, ctx):
                    full_response += chunk
                    await websocket.send_text(json.dumps({
                        "type": "stream_chunk",
                        "content": chunk,
                    }))

                await websocket.send_text(json.dumps({
                    "type": "response",
                    "content": full_response,
                }))

            # ── Audio voix ──────────────────────────────────────────────────
            elif msg_type == "voice_input":
                audio_b64 = message.get("audio", "")
                if not audio_b64:
                    continue
                audio_bytes = decode_audio_base64(audio_b64)
                transcript, audio_response = await process_voice_message(audio_bytes)

                await websocket.send_text(json.dumps({
                    "type": "voice_response",
                    "transcript": transcript,
                    "audio": encode_audio_base64(audio_response),
                }))

            # ── Memory set ──────────────────────────────────────────────────
            elif msg_type == "memory_set":
                scope = message.get("scope", "context")
                key = message.get("key", "")
                value = message.get("value")
                if key:
                    await memory_service.set(user_id, scope, key, value)
                    await websocket.send_text(json.dumps({
                        "type": "memory_ack",
                        "scope": scope,
                        "key": key,
                    }))

            # ── Memory get ──────────────────────────────────────────────────
            elif msg_type == "memory_get":
                scope = message.get("scope", "context")
                key = message.get("key")
                if key:
                    value = await memory_service.get(user_id, scope, key)
                else:
                    value = await memory_service.get_all(user_id, scope)
                await websocket.send_text(json.dumps({
                    "type": "memory_data",
                    "scope": scope,
                    "key": key,
                    "value": value,
                }))

            # ── Session summary ─────────────────────────────────────────────
            elif msg_type == "session_summary":
                all_memory = await memory_service.get_all_scopes(user_id)
                ctx = _contexts[user_id]
                history_preview = [
                    f"{m['role']}: {m['content'][:80]}" for m in ctx.history[-10:]
                ]
                summary_prompt = (
                    f"Résume cette session en 3-5 bullets (décisions, tâches, mémos):\n"
                    f"Historique: {history_preview}\n"
                    f"Mémoire: {all_memory}"
                )
                summary_ctx = ConversationContext()
                summary = ""
                async for chunk in chat_completion_stream(summary_prompt, summary_ctx, temperature=0.3):
                    summary += chunk

                await websocket.send_text(json.dumps({
                    "type": "session_summary",
                    "summary": summary,
                }))

            else:
                logger.warning(f"Type de message inconnu: {msg_type}")

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error [user_id={user_id}]: {e}")
    finally:
        _contexts.pop(user_id, None)
        logger.info(f"✗ Client WebSocket déconnecté [user_id={user_id}]")


@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    await websocket.accept()
    client_id = id(websocket)
    logger.info(f"✓ Client Realtime connecté [{client_id}]")
    try:
        await realtime_session(websocket)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Realtime error [{client_id}]: {e}")
    finally:
        logger.info(f"✗ Client Realtime déconnecté [{client_id}]")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

"""Jarvis Backend — FastAPI + WebSocket pipeline complet."""

import json
import logging
import os
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
from backend.services.n8n_service import init_n8n
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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

                # Stream token par token vers le frontend
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

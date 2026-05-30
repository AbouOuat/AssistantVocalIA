"""OpenAI Realtime API — bridge WebSocket bidirectionnel."""

import asyncio
import json
import logging
import websockets
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

REALTIME_URL = (
    f"wss://api.openai.com/v1/realtime?model={settings.OPENAI_REALTIME_MODEL}"
)

JARVIS_INSTRUCTIONS = (
    "Tu es Jarvis, un assistant IA vocal personnel. "
    "Réponds en français, de façon concise (2-3 phrases max pour les réponses vocales). "
    "Tu peux exécuter des tâches autonomes, mémoriser le contexte et contrôler des appareils."
)


async def realtime_session(client_ws) -> None:
    """
    Ouvre une session OpenAI Realtime et bridge bidirectionnellement
    avec le WebSocket client (browser → backend → OpenAI).
    """
    additional_headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1",
    }

    try:
        async with websockets.connect(
            REALTIME_URL,
            additional_headers=additional_headers,
            ping_interval=20,
        ) as openai_ws:
            logger.info("[REALTIME] Connecté à OpenAI Realtime API ✓")

            # Configuration de la session
            await openai_ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": JARVIS_INSTRUCTIONS,
                    "voice": "nova",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 600,
                    },
                },
            }))

            # Signaler au client que la session est prête
            await client_ws.send_text(json.dumps({"type": "rt_ready"}))

            async def from_openai():
                """Reçoit les événements OpenAI → forward au browser."""
                async for raw in openai_ws:
                    event = json.loads(raw)
                    etype = event.get("type", "")

                    if etype == "response.audio.delta":
                        await client_ws.send_text(json.dumps({
                            "type": "rt_audio_delta",
                            "audio": event.get("delta", ""),
                        }))

                    elif etype == "response.audio_transcript.delta":
                        await client_ws.send_text(json.dumps({
                            "type": "rt_transcript_delta",
                            "text": event.get("delta", ""),
                        }))

                    elif etype == "conversation.item.input_audio_transcription.completed":
                        await client_ws.send_text(json.dumps({
                            "type": "rt_user_transcript",
                            "text": event.get("transcript", ""),
                        }))

                    elif etype in ("response.audio.done", "response.done"):
                        await client_ws.send_text(json.dumps({"type": "rt_done"}))

                    elif etype == "error":
                        logger.error(f"[REALTIME] Erreur API: {event}")
                        await client_ws.send_text(json.dumps({
                            "type": "rt_error",
                            "message": event.get("error", {}).get("message", "Realtime error"),
                        }))

            async def from_client():
                """Reçoit les messages du browser → forward à OpenAI."""
                while True:
                    try:
                        raw = await client_ws.receive_text()
                        msg = json.loads(raw)
                        mtype = msg.get("type", "")

                        if mtype == "rt_audio_append":
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": msg.get("audio", ""),
                            }))

                        elif mtype == "rt_audio_commit":
                            await openai_ws.send(json.dumps(
                                {"type": "input_audio_buffer.commit"}
                            ))

                        elif mtype == "rt_text":
                            # Message texte → Realtime conversation item
                            await openai_ws.send(json.dumps({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [
                                        {"type": "input_text", "text": msg.get("content", "")}
                                    ],
                                },
                            }))
                            await openai_ws.send(json.dumps({"type": "response.create"}))

                        elif mtype == "rt_interrupt":
                            await openai_ws.send(json.dumps({"type": "response.cancel"}))

                    except Exception as e:
                        logger.info(f"[REALTIME] Client déconnecté: {e}")
                        break

            tasks = [
                asyncio.create_task(from_openai()),
                asyncio.create_task(from_client()),
            ]
            _done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
                try:
                    await t
                except (asyncio.CancelledError, Exception):
                    pass

    except Exception as e:
        logger.error(f"[REALTIME] Erreur connexion: {e}")
        try:
            await client_ws.send_text(json.dumps({
                "type": "rt_error",
                "message": str(e),
            }))
        except Exception:
            pass

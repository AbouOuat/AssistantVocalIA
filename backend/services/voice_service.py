"""Voice Service — STT + TTS avec détection automatique Realtime API."""

import io
import base64
import logging
from openai import AsyncOpenAI
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY or None)
    return _client

# Détecté au premier appel — None = pas encore testé
_realtime_available: bool | None = None


async def check_realtime_access() -> bool:
    """Tester si le compte a accès à l'OpenAI Realtime API.

    Requiert REALTIME_ENABLED=true en variable d'environnement.
    Par défaut désactivé : Whisper + function calling sont la voie fiable.
    """
    global _realtime_available
    if not settings.REALTIME_ENABLED:
        logger.info("[WHISPER_MODE] Realtime désactivé (REALTIME_ENABLED != true) — Whisper + function calling actifs")
        _realtime_available = False
        return False
    if _realtime_available is not None:
        return _realtime_available
    try:
        models = await _get_client().models.list()
        realtime_models = [m for m in models.data if "realtime" in m.id]
        _realtime_available = len(realtime_models) > 0
        if _realtime_available:
            logger.info("[REALTIME] Accès Realtime API confirmé ✓")
        else:
            logger.info("[WHISPER_FALLBACK] Realtime API non disponible — fallback Whisper")
    except Exception as e:
        logger.warning(f"[WHISPER_FALLBACK] Erreur vérification Realtime: {e}")
        _realtime_available = False
    return _realtime_available


async def transcribe_audio(audio_data: bytes, language: str = "fr") -> str:
    """STT via Whisper — fallback universel."""
    audio_file = io.BytesIO(audio_data)
    audio_file.name = "audio.wav"
    transcript = await _get_client().audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language=language,
    )
    return transcript.text


async def text_to_speech(text: str, voice: str = "nova") -> bytes:
    """TTS via OpenAI — retourne bytes MP3."""
    response = await _get_client().audio.speech.create(
        model="tts-1",
        input=text,
        voice=voice,
        speed=1.0,
    )
    return response.content


def encode_audio_base64(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode("utf-8")


def decode_audio_base64(audio_b64: str) -> bytes:
    return base64.b64decode(audio_b64)


async def process_voice_message(audio_data: bytes) -> tuple[str, bytes]:
    """
    Pipeline complet : audio → texte → réponse AI → audio réponse.
    Retourne (transcript, audio_response_bytes).
    Utilise Realtime si disponible, Whisper+TTS sinon.
    """
    from backend.services.ai_service import chat_completion, ConversationContext

    use_realtime = await check_realtime_access()

    if use_realtime:
        # TODO Phase 1 tâche 4 : implémenter WebSocket Realtime
        # Pour l'instant fallback même si accès disponible
        logger.info("[REALTIME] Pipeline WebSocket Realtime — à implémenter tâche 4")

    # Pipeline Whisper fallback
    logger.info("[WHISPER_FALLBACK] STT en cours...")
    transcript = await transcribe_audio(audio_data)
    logger.info(f"[WHISPER_FALLBACK] Transcrit: {transcript}")

    ctx = ConversationContext()
    reply_text = await chat_completion(transcript, ctx)
    logger.info(f"[WHISPER_FALLBACK] Réponse: {reply_text}")

    audio_response = await text_to_speech(reply_text)
    return transcript, audio_response

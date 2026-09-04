"""Smoke tests backend — imports, config, réponses simulées, endpoints santé.

Les tests qui touchent aux endpoints (lifespan FastAPI → PostgreSQL) ne tournent
que si CI_WITH_SERVICES est défini (job CI avec services postgres + redis).
"""
import os

import pytest


def test_import_app():
    """L'app FastAPI s'importe sans erreur (attrape imports cassés / syntaxe)."""
    from backend.main import app

    assert app.title == "Jarvis V2"


def test_config_defaults():
    from backend.config import get_settings

    s = get_settings()
    assert s.WORKFLOW_VERSION in ("v1", "v2")
    assert s.OPENAI_MODEL == "gpt-4o"
    assert isinstance(s.FAKE_LLM, bool)


def test_memory_service_key_scoping():
    """Named Scopes : préfixe + rejet des scopes inconnus."""
    from backend.services.memory_service import MemoryService

    ms = MemoryService()
    assert ms._key(1, "projects", "x") == "jarvis:memory:1:projects:x"
    with pytest.raises(ValueError):
        ms._key(1, "scope_bidon", "x")


async def test_fake_llm_short_circuits(monkeypatch):
    """JARVIS_FAKE_LLM → chat_completion renvoie une réponse simulée sans appel réseau."""
    from backend.services import ai_service

    monkeypatch.setattr(ai_service.settings, "FAKE_LLM", True)
    ctx = ai_service.ConversationContext()
    reply = await ai_service.chat_completion("ping", ctx)
    assert "simul" in reply.lower()
    assert ctx.history[-1]["role"] == "assistant"


async def test_fake_llm_with_tools_streams(monkeypatch):
    from backend.services import ai_service

    monkeypatch.setattr(ai_service.settings, "FAKE_LLM", True)
    ctx = ai_service.ConversationContext()
    chunks = []

    async def on_chunk(c):
        chunks.append(c)

    async def tool_exec(name, args):  # jamais appelé en mode fake
        raise AssertionError("aucun tool ne doit être appelé en FAKE_LLM")

    reply, tools_called = await ai_service.chat_completion_with_tools(
        "analyse mes emails", ctx, tool_exec, on_stream_chunk=on_chunk
    )
    assert tools_called is False
    assert chunks and "".join(chunks) == reply


_needs_services = pytest.mark.skipif(
    not os.getenv("CI_WITH_SERVICES"),
    reason="lifespan FastAPI nécessite postgres + redis (CI_WITH_SERVICES)",
)


@_needs_services
def test_health_endpoint():
    from fastapi.testclient import TestClient

    from backend.main import app

    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "healthy"}


@_needs_services
def test_api_settings_reports_workflow_version():
    from fastapi.testclient import TestClient

    from backend.main import app

    with TestClient(app) as client:
        r = client.get("/api/settings")
        assert r.status_code == 200
        assert r.json()["workflow_version"] in ("v1", "v2")

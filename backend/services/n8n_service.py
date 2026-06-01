"""n8n Integration Service — déclencher des workflows d'automation."""

import httpx
import logging
from typing import Optional
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class N8nClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-N8N-API-KEY": api_key, "Content-Type": "application/json"}

    async def trigger_workflow(self, workflow_id: str, data: dict) -> Optional[dict]:
        try:
            url = f"{self.base_url}/workflows/{workflow_id}/execute"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"n8n trigger error: {e}")
            return None

    async def get_workflows(self) -> Optional[list]:
        try:
            url = f"{self.base_url}/workflows"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"n8n list workflows error: {e}")
            return None


n8n_client: Optional[N8nClient] = None


def init_n8n():
    global n8n_client
    if settings.N8N_API_URL and settings.N8N_API_KEY:
        n8n_client = N8nClient(settings.N8N_API_URL, settings.N8N_API_KEY)
        logger.info("✓ n8n client initialisé")
    else:
        logger.warning("n8n non configuré (N8N_API_URL ou N8N_API_KEY manquant)")


async def trigger_automation(workflow_name: str, params: dict) -> str:
    if not n8n_client:
        return "n8n non configuré — vérifier N8N_API_URL et N8N_API_KEY dans .env"
    result = await n8n_client.trigger_workflow(workflow_name, params)
    if result:
        return f"Automation '{workflow_name}' déclenchée ✓"
    return f"Échec déclenchement automation '{workflow_name}'"


async def call_webhook(webhook_path: str, payload: dict, timeout: float = 30.0) -> Optional[dict]:
    """Appelle un webhook n8n et retourne la réponse JSON."""
    if not settings.N8N_API_URL:
        return None
    base = settings.N8N_API_URL.replace("/api/v1", "").rstrip("/")
    url = f"{base}/webhook/{webhook_path}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"[n8n] webhook {webhook_path} → HTTP {resp.status_code}")
    except Exception as e:
        logger.warning(f"[n8n] webhook {webhook_path} indisponible: {e}")
    return None

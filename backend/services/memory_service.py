"""Memory Service — Redis Named Scopes pour la mémoire persistante de Jarvis."""

import json
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Scopes autorisés — correspond aux namespaces du DESIGN.md et PRD
VALID_SCOPES = {"projects", "preferences", "tasks", "context"}
KEY_PREFIX = "jarvis:memory"


class MemoryService:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _key(self, user_id: int, scope: str, key: str) -> str:
        if scope not in VALID_SCOPES:
            raise ValueError(f"Scope invalide: {scope!r}. Valides: {VALID_SCOPES}")
        return f"{KEY_PREFIX}:{user_id}:{scope}:{key}"

    async def set(self, user_id: int, scope: str, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        r = await self._get_redis()
        redis_key = self._key(user_id, scope, key)
        serialized = json.dumps(value, ensure_ascii=False)
        if ttl_seconds:
            await r.setex(redis_key, ttl_seconds, serialized)
        else:
            await r.set(redis_key, serialized)
        logger.debug(f"memory.set user_id={user_id} {scope}/{key}")

    async def get(self, user_id: int, scope: str, key: str) -> Optional[Any]:
        r = await self._get_redis()
        raw = await r.get(self._key(user_id, scope, key))
        if raw is None:
            return None
        return json.loads(raw)

    async def delete(self, user_id: int, scope: str, key: str) -> bool:
        r = await self._get_redis()
        deleted = await r.delete(self._key(user_id, scope, key))
        return deleted > 0

    async def get_all(self, user_id: int, scope: str) -> dict[str, Any]:
        if scope not in VALID_SCOPES:
            raise ValueError(f"Scope invalide: {scope!r}")
        r = await self._get_redis()
        pattern = f"{KEY_PREFIX}:{user_id}:{scope}:*"
        keys = await r.keys(pattern)
        result = {}
        for k in keys:
            raw = await r.get(k)
            if raw:
                short_key = k.removeprefix(f"{KEY_PREFIX}:{user_id}:{scope}:")
                result[short_key] = json.loads(raw)
        return result

    async def get_all_scopes(self, user_id: int) -> dict[str, dict]:
        """Récupère toute la mémoire pour un user (pour Session Summary)."""
        result = {}
        for scope in VALID_SCOPES:
            result[scope] = await self.get_all(user_id, scope)
        return result

    async def close(self):
        if self._redis:
            await self._redis.aclose()


# Instance globale
memory_service = MemoryService()

"""AI Service — GPT-4o conversation avec gestion du contexte et streaming."""

from openai import AsyncOpenAI
from backend.config import get_settings

settings = get_settings()
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY or None)
    return _client

SYSTEM_PROMPT = """Tu es Jarvis, l'assistant IA personnel d'Aboubakary (Abo). Tu es intelligent, concis et fiable.

## Règle de confirmation (IMPORTANT)
Avant toute action concrète (envoyer un email, créer une tâche, déclencher une automation, modifier des données) :
1. Commence par : "J'ai compris que tu veux [reformulation courte]. C'est bien ça ?"
2. Si oui → exécute
3. Si ambiguïté → pose UNE seule question précise
Exception : pour les questions simples, les explications et la conversation, réponds directement.

## Capacités
- Conversation naturelle en français
- Morning briefing (météo + emails + agenda)
- Analyse de notes → plan d'action + email draft
- Mémoire persistante (projets, préférences, tâches)
- Contrôle domotique (lumières, thermostat, verrou)
- Automations via n8n

## Style
- Réponds en français, sois concis (2-3 phrases max pour la voix)
- Tutoie Abo
- Si tu ne sais pas → dis-le clairement plutôt qu'inventer"""


class ConversationContext:
    def __init__(self, user_id: str = "default", max_history: int = 20):
        self.user_id = user_id
        self.history: list[dict] = []
        self.max_history = max_history

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_messages(self) -> list[dict]:
        return [{"role": "system", "content": SYSTEM_PROMPT}, *self.history]

    def clear(self):
        self.history = []


async def chat_completion(
    user_message: str,
    context: ConversationContext,
    temperature: float = 0.7,
) -> str:
    context.add_message("user", user_message)
    response = await _get_client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=context.get_messages(),
        temperature=temperature,
        max_tokens=500,
    )
    reply = response.choices[0].message.content
    context.add_message("assistant", reply)
    return reply


async def chat_completion_stream(
    user_message: str,
    context: ConversationContext,
    temperature: float = 0.7,
):
    """Yield text chunks from GPT-4o (streaming)."""
    context.add_message("user", user_message)
    full_response = ""

    stream = await _get_client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=context.get_messages(),
        temperature=temperature,
        max_tokens=500,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            full_response += delta
            yield delta

    context.add_message("assistant", full_response)

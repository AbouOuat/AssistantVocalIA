"""AI Service — GPT-4o conversation avec gestion du contexte et streaming."""

import json
import logging
import os
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

def _build_system_prompt() -> str:
    from datetime import date, timedelta
    gmail = os.getenv("GMAIL_USER_EMAIL", "ouat.abou34@gmail.com")
    outlook = "ouat.abou34@outlook.fr"
    today = date.today()
    tomorrow = today + timedelta(days=1)
    return f"""Tu es Jarvis, l'assistant IA vocal personnel d'Abo (Aboubakary Ouattara). Tu es intelligent, concis et fiable.

## Date et heure actuelles
- Aujourd'hui : {today.strftime("%A %d %B %Y")} ({today.isoformat()})
- Demain : {tomorrow.strftime("%A %d %B %Y")} ({tomorrow.isoformat()})
- Fuseau : Europe/Paris (UTC+2 en été)
- IMPORTANT : pour tout agenda, utilise TOUJOURS ces dates. N'utilise JAMAIS de dates antérieures à {today.isoformat()}.

## Profil utilisateur
- Prénom : Abo
- Email Gmail : {gmail}
- Email Outlook : {outlook}
- Langue : français (réponds toujours en français sauf si Abo parle anglais)
- Fuseau horaire : Europe/Paris (France)

## Emails — règles importantes
- Tu as accès aux deux boîtes : Gmail ({gmail}) ET Outlook ({outlook})
- Pour lire les emails récents → utilise toujours un outil (lire_emails_en_memoire, classifier_emails_gmail, rechercher_emails)
- Ne jamais dire "je n'ai pas accès" ou "aucun email trouvé" sans avoir appelé un outil d'abord
- Si l'utilisateur demande ses mails sans préciser → commence par lire_emails_en_memoire (les deux boîtes)

## Règle de confirmation
Avant toute action irréversible (envoyer un email) :
- Confirme en une phrase courte avant d'exécuter.
Exception : lire, lister, résumer, créer un rappel, créer un événement agenda, mémoriser → agis directement sans demander.

## Capacités
- Lire et analyser Gmail et Outlook
- Morning briefing : météo + emails prioritaires + agenda du jour
- Analyse de notes → plan d'action
- Mémoire persistante : projets, préférences, tâches
- Rappels avec notification email
- Brouillons Gmail, envoi Outlook

## Style vocal
- Tutoie Abo, sois concis (2-3 phrases max pour la voix)
- Réponds avec les vraies données — n'invente jamais un contenu d'email
- Pour les réponses longues (liste d'emails) : résume à l'oral, détaille dans le chat"""


# Ne pas mettre en cache — la date doit être recalculée à chaque appel
def _get_system_prompt() -> str:
    return _build_system_prompt()

JARVIS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "classifier_emails_gmail",
            "description": (
                "Lire et analyser les emails Gmail non lus des 8 dernières heures avec l'IA. "
                "À utiliser quand l'utilisateur veut voir/vérifier/analyser ses emails Gmail, "
                "demande un résumé, ou dit des choses comme 't'as des mails ?', 'quoi de neuf dans ma boîte ?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Nombre max d'emails (défaut 10, max 50)"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "classifier_emails_outlook",
            "description": (
                "Lire et analyser les emails Outlook récents. "
                "À utiliser quand l'utilisateur mentionne Outlook, ses emails pro/avocat, "
                "ou demande à voir sa boîte Outlook."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Nombre max d'emails (défaut 10, max 50)"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lire_emails_en_memoire",
            "description": (
                "Consulter les emails déjà analysés et stockés en mémoire sans refaire une classification. "
                "À utiliser pour répondre aux questions : 'qui m'a écrit ?', 'c'est quoi les urgents ?', "
                "'liste mes derniers mails', 'qu'est-ce que Jean m'a envoyé ?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "enum": ["gmail", "outlook", "tous"],
                        "description": "Source à consulter (défaut: tous)",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "morning_briefing",
            "description": (
                "Lancer le briefing du matin complet : météo, agenda du jour, emails prioritaires. "
                "À utiliser pour : 'start my day', 'briefing du matin', 'commence ma journée', "
                "'qu'est-ce que j'ai aujourd'hui ?', 'résumé du matin'."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "creer_rappel",
            "description": (
                "Créer un rappel ou une tâche avec notification email. "
                "À utiliser quand l'utilisateur dit 'rappelle-moi de', 'remind me to', "
                "'n'oublie pas de', 'ajoute une tâche'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "texte": {"type": "string", "description": "Ce dont il faut se rappeler"},
                    "echeance": {
                        "type": "string",
                        "description": "Date/heure ISO 8601 optionnelle, ex: 2026-06-03T15:00:00",
                    },
                },
                "required": ["texte"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rechercher_emails",
            "description": (
                "Chercher des emails par mot-clé, expéditeur ou date dans Gmail et/ou Outlook. "
                "À utiliser pour : 'trouve l'email de Jean', 'cherche les emails sur la facture', "
                "'emails reçus après le 1er juin', 'dernier mail de mon avocat'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "q": {
                        "type": "string",
                        "description": (
                            "Requête de recherche. Gmail : syntaxe native (ex: 'from:jean@x.com', "
                            "'subject:facture', 'after:2026/06/01'). Outlook : mot-clé libre."
                        ),
                    },
                    "source": {
                        "type": "string",
                        "enum": ["gmail", "outlook", "tous"],
                        "description": "Boîte à chercher (défaut: tous)",
                    },
                    "limit": {"type": "integer", "description": "Nombre de résultats (défaut 10)"},
                    "date_from": {
                        "type": "string",
                        "description": "Date de début ISO YYYY-MM-DD (Outlook uniquement)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyser_notes",
            "description": (
                "Analyser des notes textuelles et produire un plan d'action structuré, "
                "potentiellement avec un email draft. "
                "À utiliser pour : 'analyze my notes', 'analyse mes notes', "
                "'crée un plan d'action à partir de', 'smart agent'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "notes": {
                        "type": "string",
                        "description": "Le texte des notes à analyser (réunion, tâches, idées...)",
                    }
                },
                "required": ["notes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "creer_evenement_agenda",
            "description": (
                "Créer un événement dans Google Calendar. "
                "À utiliser pour : 'ajoute un rdv', 'crée un événement', 'bloque du temps', "
                "'réunion jeudi à 14h', 'ajoute ça dans mon agenda'. "
                "IMPORTANT : convertis toujours la date/heure en ISO 8601 avec timezone Europe/Paris (+02:00 en été, +01:00 en hiver). "
                f"Aujourd'hui = {__import__('datetime').date.today().isoformat()}. "
                "Exemple : demain à 9h = 2026-06-05T09:00:00+02:00"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "titre":       {"type": "string", "description": "Titre de l'événement"},
                    "debut":       {"type": "string", "description": "Début ISO 8601 avec timezone Paris, ex: 2026-06-04T09:00:00+02:00"},
                    "fin":         {"type": "string", "description": "Fin ISO 8601 avec timezone Paris, ex: 2026-06-04T10:00:00+02:00"},
                    "description": {"type": "string", "description": "Description optionnelle"},
                    "lieu":        {"type": "string", "description": "Lieu optionnel"},
                },
                "required": ["titre", "debut", "fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "creer_brouillon_gmail",
            "description": (
                "Créer un brouillon d'email dans Gmail (non envoyé, visible dans Brouillons). "
                "À utiliser pour : 'rédige une réponse à X', 'crée un brouillon pour Y', "
                "'prépare un email à Z'. L'utilisateur pourra relire et envoyer depuis Gmail."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Adresse email du destinataire"},
                    "subject": {"type": "string", "description": "Objet de l'email"},
                    "body": {"type": "string", "description": "Corps de l'email (texte)"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "envoyer_email_outlook",
            "description": (
                "Envoyer un email via Outlook. "
                "À utiliser quand l'utilisateur veut envoyer (pas juste brouillon) via Outlook. "
                "Pour Gmail, utiliser creer_brouillon_gmail."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Adresse email du destinataire"},
                    "subject": {"type": "string", "description": "Objet de l'email"},
                    "body": {"type": "string", "description": "Corps de l'email"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rechercher_memoire",
            "description": (
                "Chercher dans la mémoire persistante de Jarvis (projets, préférences, tâches mémorisées). "
                "À utiliser quand l'utilisateur demande ce que Jarvis sait, rappelle une préférence, "
                "ou demande 'tu te souviens de X ?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "requete": {"type": "string", "description": "Ce qu'on cherche en mémoire"}
                },
                "required": ["requete"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sauvegarder_memoire",
            "description": (
                "Sauvegarder une information, préférence ou note dans la mémoire persistante de Jarvis. "
                "À utiliser quand l'utilisateur dit 'souviens-toi que', 'mémorise', 'retiens que', "
                "'note que', 'remember that'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cle":    {"type": "string", "description": "Identifiant court en snake_case, ex: preference_briefing_heure"},
                    "valeur": {"type": "string", "description": "Contenu à mémoriser"},
                    "scope":  {
                        "type": "string",
                        "enum": ["preferences", "projects", "tasks"],
                        "description": "Catégorie : preferences (habitudes/goûts), projects (infos projets), tasks (tâches/notes)",
                    },
                },
                "required": ["cle", "valeur"],
            },
        },
    },
]


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
        return [{"role": "system", "content": _get_system_prompt()}, *self.history]

    def clear(self):
        self.history = []


async def chat_completion(
    user_message: str,
    context: ConversationContext,
    temperature: float = 0.7,
    extra_system: str | None = None,
) -> str:
    context.add_message("user", user_message)
    messages = context.get_messages()
    if extra_system:
        messages.insert(1, {"role": "system", "content": extra_system})
    response = await _get_client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=500,
    )
    reply = response.choices[0].message.content
    context.add_message("assistant", reply)
    return reply


async def chat_completion_with_tools(
    user_message: str,
    context: ConversationContext,
    tool_executor,
    on_tool_call=None,
    on_stream_chunk=None,
) -> tuple[str, bool]:
    """GPT-4o avec function calling + streaming pour les réponses sans tool.

    tool_executor:   async (name: str, args: dict) -> str
    on_tool_call:    async (name: str) -> None  — afficher le progress
    on_stream_chunk: async (chunk: str) -> None — streamer les tokens si pas de tool
    """
    context.add_message("user", user_message)
    messages = list(context.get_messages())
    tools_called = False

    for iteration in range(3):
        # Premier passage sans tool actif : on tente le streaming
        if not tools_called and on_stream_chunk:
            full = ""
            tool_calls_acc: list[dict] = []
            stream = await _get_client().chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                tools=JARVIS_TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=600,
                stream=True,
            )
            finish_reason = None
            async for chunk in stream:
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason or finish_reason
                if delta.content:
                    full += delta.content
                    await on_stream_chunk(delta.content)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        while len(tool_calls_acc) <= idx:
                            tool_calls_acc.append({"id": "", "name": "", "arguments": ""})
                        if tc.id:
                            tool_calls_acc[idx]["id"] = tc.id
                        if tc.function and tc.function.name:
                            tool_calls_acc[idx]["name"] = tc.function.name
                        if tc.function and tc.function.arguments:
                            tool_calls_acc[idx]["arguments"] += tc.function.arguments

            if not tool_calls_acc:
                context.add_message("assistant", full)
                return full, False

            # Des tools ont été demandés via streaming — traiter
            tools_called = True
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": t["id"], "type": "function",
                     "function": {"name": t["name"], "arguments": t["arguments"]}}
                    for t in tool_calls_acc
                ],
            })
            for t in tool_calls_acc:
                if on_tool_call:
                    await on_tool_call(t["name"])
                try:
                    args = json.loads(t["arguments"])
                except Exception:
                    args = {}
                try:
                    result = await tool_executor(t["name"], args)
                except Exception as te:
                    result = f"Erreur outil {t['name']}: {te}"
                    logger.error(f"Tool {t['name']} error: {te}", exc_info=True)
                messages.append({"role": "tool", "tool_call_id": t["id"], "content": str(result)})
            continue  # relancer pour la réponse finale

        # Passes suivantes (après tool calls) : non-streaming
        response = await _get_client().chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            tools=JARVIS_TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=600,
        )
        choice = response.choices[0]

        if choice.finish_reason != "tool_calls":
            reply = choice.message.content or ""
            context.add_message("assistant", reply)
            return reply, tools_called

        tools_called = True
        msg = choice.message
        messages.append(msg)
        for tc in msg.tool_calls or []:
            if on_tool_call:
                await on_tool_call(tc.function.name)
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}
            try:
                result = await tool_executor(tc.function.name, args)
            except Exception as te:
                result = f"Erreur outil {tc.function.name}: {te}"
                logger.error(f"Tool {tc.function.name} error: {te}", exc_info=True)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})

    reply = "J'ai rencontré un problème lors du traitement. Réessaie."
    context.add_message("assistant", reply)
    return reply, tools_called


async def chat_completion_stream(
    user_message: str,
    context: ConversationContext,
    temperature: float = 0.7,
    extra_system: str | None = None,
):
    """Yield text chunks from GPT-4o (streaming)."""
    context.add_message("user", user_message)
    full_response = ""
    messages = context.get_messages()
    if extra_system:
        messages.insert(1, {"role": "system", "content": extra_system})

    stream = await _get_client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
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

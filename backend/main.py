"""Jarvis Backend — FastAPI + WebSocket pipeline complet."""

import asyncio
import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.services.ai_service import (
    ConversationContext,
    chat_completion,
    chat_completion_stream,
    chat_completion_with_tools,
)
from backend.services.memory_service import memory_service
from backend.services.voice_service import (
    check_realtime_access,
    decode_audio_base64,
    encode_audio_base64,
    process_voice_message,
    transcribe_audio,
    text_to_speech,
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

# État de dictée par utilisateur (machine à états Dictée Avocat)
# { user_id: { "mode": "waiting_dictation" | "waiting_confirmation", "draft": str, "title": str } }
_dictation_state: dict[int, dict] = {}


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


_TOOL_PROGRESS: dict[str, str] = {
    "classifier_emails_gmail":   "🔍 Lecture et analyse des emails Gmail...",
    "classifier_emails_outlook": "🔍 Lecture et analyse des emails Outlook...",
    "lire_emails_en_memoire":    "📬 Consultation des emails en mémoire...",
    "morning_briefing":          "🌅 Préparation du briefing du matin...",
    "creer_rappel":              "📝 Création du rappel...",
    "rechercher_emails":         "🔍 Recherche dans Gmail et Outlook...",
    "creer_evenement_agenda":    "📅 Ajout dans Google Calendar...",
    "creer_brouillon_gmail":     "✍️ Création du brouillon Gmail...",
    "envoyer_email_outlook":     "📤 Envoi de l'email via Outlook...",
    "analyser_notes":            "🤖 Analyse des notes et création du plan d'action...",
    "rechercher_memoire":        "🧠 Recherche en mémoire...",
    "sauvegarder_memoire":       "💾 Mémorisation en cours...",
}

def _format_emails_context(source: str, emails: list) -> str:
    lines = [f"## Emails récents {source} ({len(emails)})"]
    for e in emails[:10]:
        urgence = f" [{e.get('urgence')}]" if e.get('urgence') not in (None, 'faible') else ""
        lines.append(
            f"- De : {e.get('from_name') or e.get('from', '?')} <{e.get('from_email', '')}>"
            f" | Objet : {e.get('subject', '?')}"
            f" | Action : {e.get('action', '?')}{urgence}"
            f" | Résumé : {e.get('resume', '')}"
            + (f" | Échéance : {e['echeance']}" if e.get('echeance') else "")
        )
    return "\n".join(lines)

async def _execute_tool(name: str, args: dict, user_id: int) -> str:
    """Exécute un outil Jarvis et retourne le résultat en texte pour GPT-4o."""
    if name == "classifier_emails_gmail":
        limit = min(int(args.get("limit", 10)), 50)
        result = await call_webhook("email-classifier", {"user_id": user_id, "limit": limit})
        if result and result.get("emails_structured"):
            await memory_service.set(
                user_id, "context", "recent_emails_gmail",
                result["emails_structured"], ttl_seconds=86400,
            )
        if not result:
            return "Le workflow Gmail est injoignable. Vérifie qu'il est actif sur n8n."
        if result.get("no_emails"):
            return f"Aucun email Gmail non lu dans les 8 dernières heures. {result.get('skipped', 0)} ignorés automatiquement."
        return result.get("summary", f"{result.get('processed', 0)} emails Gmail analysés.")

    if name == "classifier_emails_outlook":
        limit = min(int(args.get("limit", 10)), 50)
        result = await call_webhook("outlook-email-classifier", {"user_id": user_id, "limit": limit}, timeout=45.0)
        if result and result.get("emails_structured"):
            await memory_service.set(
                user_id, "context", "recent_emails_outlook",
                result["emails_structured"], ttl_seconds=86400,
            )
        if not result:
            return "Le workflow Outlook est injoignable. Vérifie qu'il est actif sur n8n."
        if result.get("no_emails"):
            return f"Aucun email Outlook récent. {result.get('skipped', 0)} ignorés."
        return result.get("summary", f"{result.get('processed', 0)} emails Outlook analysés.")

    if name == "lire_emails_en_memoire":
        source = args.get("source", "tous")
        parts = []
        if source in ("gmail", "tous"):
            emails = await memory_service.get(user_id, "context", "recent_emails_gmail")
            if emails:
                parts.append(_format_emails_context("Gmail", emails))
        if source in ("outlook", "tous"):
            emails = await memory_service.get(user_id, "context", "recent_emails_outlook")
            if emails:
                parts.append(_format_emails_context("Outlook", emails))
        if parts:
            return "\n\n".join(parts)

        # Redis vide — fallback direct vers les workflows de recherche
        fallback = []
        if source in ("gmail", "tous"):
            r = await call_webhook("gmail-search", {"q": "newer_than:7d", "limit": 10})
            if r and r.get("ok") and r.get("emails"):
                raw = r["emails"]
                structured = [{**e, "urgence": "faible", "action": "lire", "resume": e.get("snippet", "")[:100]} for e in raw]
                await memory_service.set(user_id, "context", "recent_emails_gmail", structured, ttl_seconds=3600)
                fallback.append(_format_emails_context("Gmail", raw))
        if source in ("outlook", "tous"):
            r = await call_webhook("outlook-search", {"q": "", "limit": 10})
            if r and r.get("ok") and r.get("emails"):
                raw = r["emails"]
                structured = [{**e, "urgence": "faible", "action": "lire", "resume": e.get("snippet", "")[:100]} for e in raw]
                await memory_service.set(user_id, "context", "recent_emails_outlook", structured, ttl_seconds=3600)
                fallback.append(_format_emails_context("Outlook", raw))
        if fallback:
            return "\n\n".join(fallback)
        return "Aucun email trouvé. Vérifie que les workflows Gmail et Outlook sont actifs dans n8n."

    if name == "morning_briefing":
        result = await call_webhook("morning-briefing", {"user_id": user_id})
        if not result:
            return "Le workflow Morning Briefing est injoignable. Vérifie qu'il est actif sur n8n."
        return result.get("briefing", "Briefing reçu.")

    if name == "creer_rappel":
        texte = args.get("texte", "")
        echeance = args.get("echeance")
        if not texte:
            return "Texte du rappel manquant."
        key = f"task_{int(time.time() * 1000)}"
        reminder = {"text": texte, "created_at": datetime.utcnow().isoformat(), "done": False}
        if echeance:
            reminder["due_at"] = echeance
        await memory_service.set(user_id, "tasks", key, reminder)
        await call_webhook("reminders", {"user_id": user_id, "text": texte, "due_at": echeance or ""})
        return f"Rappel créé : « {texte} »" + (f", échéance : {echeance}" if echeance else ".")

    if name == "rechercher_emails":
        q = args.get("q", "").strip()
        source = args.get("source", "tous")
        limit = min(int(args.get("limit", 10)), 50)
        date_from = args.get("date_from", "")
        parts = []

        if source in ("gmail", "tous") and q:
            r = await call_webhook("gmail-search", {"q": q, "limit": limit})
            if r and r.get("ok") and r.get("emails"):
                emails = r["emails"]
                lines = [f"### Gmail — {len(emails)} résultat(s) pour « {q} »"]
                for e in emails:
                    lines.append(f"- {e.get('from_name') or e.get('from')} | {e.get('subject')} | {e.get('snippet','')[:120]}")
                parts.append("\n".join(lines))
            elif r and not r.get("ok"):
                parts.append(f"Gmail : {r.get('error', 'Aucun résultat.')}")
            else:
                parts.append("Gmail : aucun email trouvé.")

        if source in ("outlook", "tous"):
            r = await call_webhook("outlook-search", {"q": q, "limit": limit, "date_from": date_from})
            if r and r.get("ok") and r.get("emails"):
                emails = r["emails"]
                lines = [f"### Outlook — {len(emails)} résultat(s)"]
                for e in emails:
                    lines.append(f"- {e.get('from_name') or e.get('from')} | {e.get('subject')} | {e.get('snippet','')[:120]}")
                parts.append("\n".join(lines))
            elif r and not r.get("ok"):
                parts.append(f"Outlook : {r.get('error', 'Aucun résultat.')}")
            else:
                parts.append("Outlook : aucun email trouvé.")

        return "\n\n".join(parts) if parts else "Aucun résultat trouvé."

    if name == "analyser_notes":
        notes = args.get("notes", "").strip()
        if not notes:
            return "Notes manquantes. Précise le contenu à analyser."
        result = await call_webhook("smart-agent", {"user_id": user_id, "notes": notes})
        if not result:
            return "Le workflow Smart Agent est injoignable. Vérifie qu'il est actif sur n8n."
        if not result.get("action_plan"):
            return "L'analyse n'a pas retourné de plan. Réessaie avec des notes plus détaillées."
        plan = "\n".join(f"• {step}" for step in result["action_plan"])
        email_note = "\n\n📩 Email draft créé et envoyé." if result.get("email_sent") else ""
        return f"Plan d'action :\n{plan}{email_note}"

    if name == "creer_evenement_agenda":
        titre = args.get("titre", "").strip()
        debut = args.get("debut", "").strip()
        fin   = args.get("fin", "").strip()
        if not all([titre, debut, fin]):
            return "Titre, début et fin sont requis pour créer un événement."
        result = await call_webhook("calendar-create-event", {
            "titre": titre, "debut": debut, "fin": fin,
            "description": args.get("description", ""),
            "lieu": args.get("lieu", ""),
        })
        if not result or not result.get("ok"):
            err = result.get("error", "Erreur inconnue") if result else "Workflow calendar-create-event injoignable."
            return f"Impossible de créer l'événement : {err}"
        try:
            d = datetime.fromisoformat(debut)
            date_str = d.strftime("%A %d %B à %Hh%M")
        except Exception:
            date_str = debut
        return f"Événement créé ✅\n**{titre}** — {date_str}"

    if name == "creer_brouillon_gmail":
        to = args.get("to", "").strip()
        subject = args.get("subject", "").strip()
        body = args.get("body", "").strip()
        if not all([to, subject, body]):
            return "Champs manquants : to, subject et body sont requis."
        result = await call_webhook("gmail-draft", {"to": to, "subject": subject, "body": body})
        if not result or not result.get("ok"):
            err = result.get("error", "Erreur inconnue") if result else "Workflow gmail-draft injoignable."
            return f"Impossible de créer le brouillon : {err}"
        return f"Brouillon Gmail créé ✅\nÀ : {to}\nObjet : {subject}\nTu peux le relire et l'envoyer depuis Gmail."

    if name == "envoyer_email_outlook":
        to = args.get("to", "").strip()
        subject = args.get("subject", "").strip()
        body = args.get("body", "").strip()
        if not all([to, subject, body]):
            return "Champs manquants : to, subject et body sont requis."
        result = await call_webhook("send-outlook-email", {"to": to, "subject": subject, "body": body})
        if not result or not result.get("ok"):
            return "Envoi échoué. Vérifie le workflow send-outlook-email et les credentials Outlook."
        return f"Email envoyé via Outlook ✅\nÀ : {result.get('sent_to', to)}\nObjet : {result.get('subject', subject)}"

    if name == "sauvegarder_memoire":
        cle    = args.get("cle", "").strip().replace(" ", "_")
        valeur = args.get("valeur", "").strip()
        scope  = args.get("scope", "preferences")
        if not cle or not valeur:
            return "Clé et valeur sont requises pour mémoriser."
        if scope not in ("preferences", "projects", "tasks"):
            scope = "preferences"
        await memory_service.set(user_id, scope, cle, valeur)
        return f"Mémorisé ✅ [{scope}/{cle}] : {valeur}"

    if name == "rechercher_memoire":
        requete = args.get("requete", "").lower()
        all_mem = await memory_service.get_all_scopes(user_id)
        results = []
        for scope, data in all_mem.items():
            if scope == "context":
                continue
            for key, value in data.items():
                if requete in str(value).lower() or requete in key.lower():
                    results.append(f"[{scope}/{key}] {str(value)[:300]}")
        if not results:
            return f"Rien trouvé en mémoire pour « {requete} »."
        return "\n".join(results[:8])

    return f"Outil inconnu : {name}."


async def _send_ws(websocket: WebSocket, payload: dict) -> None:
    """Envoie un message WebSocket sans lever d'exception si la connexion est fermée."""
    try:
        await websocket.send_text(json.dumps(payload))
    except Exception:
        pass


async def _format_compte_rendu(transcript: str) -> dict:
    """Formate une dictée brute en compte-rendu structuré via GPT-4o (JSON mode)."""
    from backend.services.ai_service import _get_client
    from backend.config import get_settings as _gs
    today = __import__("datetime").date.today().isoformat()
    system_prompt = (
        "Tu es un assistant juridique expert. "
        "Formate ce compte-rendu de réunion en JSON structuré. "
        "Champs requis : titre (string), date (YYYY-MM-DD ou 'Non précisée'), "
        "participants (liste de strings), points_discutes (liste de strings), "
        "decisions (liste de strings), actions (liste de strings avec responsable si mentionné). "
        f"Date du jour si non précisée : {today}. "
        "Sois précis, professionnel, neutre. Ne jamais inventer de faits non mentionnés."
    )
    client = _get_client()
    resp = await client.chat.completions.create(
        model=_gs().OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Dictée à formater :\n\n{transcript}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1000,
    )
    try:
        data = json.loads(resp.choices[0].message.content)
    except Exception:
        data = {"titre": "Compte-rendu", "date": today, "participants": [],
                "points_discutes": [transcript], "decisions": [], "actions": []}

    def _list_md(items: list, icon: str = "•") -> str:
        return "\n".join(f"{icon} {i}" for i in items) if items else f"{icon} Aucun"

    markdown = (
        f"## 📋 {data.get('titre', 'Compte-rendu de réunion')}\n"
        f"**Date :** {data.get('date', today)}\n\n"
        f"**Participants :** {', '.join(data.get('participants', [])) or 'Non précisés'}\n\n"
        f"### Points discutés\n{_list_md(data.get('points_discutes', []))}\n\n"
        f"### Décisions\n{_list_md(data.get('decisions', []))}\n\n"
        f"### Actions\n{_list_md(data.get('actions', []))}"
    )
    data["markdown"] = markdown
    return data


_DICTATION_TRIGGERS = {
    "compte-rendu", "compte rendu", "rédige un compte", "note de réunion",
    "meeting notes", "procès-verbal", "pv de réunion", "dictée reunion",
}

def _is_dictation_trigger(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in _DICTATION_TRIGGERS)


async def _handle_n8n_command(text: str, user_id: int) -> tuple[str, str] | None:
    """Obsolète. Toutes les commandes passent par function calling. Conservé pour compatibilité."""
    return None


async def _handle_n8n_command_legacy(text: str, user_id: int) -> tuple[str, str] | None:
    t = text.lower().strip()

    # ── Morning Briefing ─────────────────────────────────────────────────────
    if any(k in t for k in ["start my day", "morning briefing", "commence ma journée"]):
        result = await call_webhook("morning-briefing", {"user_id": user_id})
        if not result:
            msg = (
                "⚠️ Le workflow Morning Briefing est injoignable.\n"
                "→ Vérifie que le workflow '[DEV] Morning Briefing' est actif sur n8n.obyz.biz."
            )
            return msg, "Le workflow Morning Briefing est injoignable. Vérifie qu'il est actif sur n8n."
        briefing = result.get("briefing", "Briefing reçu mais format inattendu.")
        return briefing, "Voici ton briefing du matin. J'ai affiché le détail dans le chat."

    # ── Outlook Email Classifier ──────────────────────────────────────────────
    OUTLOOK_KEYWORDS = [
        "outlook", "emails outlook", "mes emails outlook", "mes mails outlook",
        "email avocat", "emails avocat", "ma boite outlook", "analyse mes emails outlook",
        "classifie mes emails outlook", "outlook mail", "boite outlook",
    ]
    is_outlook = any(k in t for k in OUTLOOK_KEYWORDS) or (
        "outlook" in t and any(k in t for k in ["email", "mail", "analyse", "classify", "résumé", "resume", "synthese"])
    )
    if is_outlook:
        limit = _parse_email_limit(t)
        limit_note = " (limité à 50 par sécurité)" if re.search(r'\b(\d+)\b', t) and int(re.search(r'\b(\d+)\b', t).group(1)) > 50 else ""

        result = await call_webhook(
            "outlook-email-classifier",
            {"user_id": user_id, "limit": limit},
            timeout=45.0,
        )

        if result and result.get("emails_structured"):
            await memory_service.set(
                user_id, "context", "recent_emails_outlook",
                result["emails_structured"], ttl_seconds=86400,
            )

        if not result:
            msg = (
                "⚠️ Le workflow Outlook Email Classifier est injoignable.\n"
                "→ Vérifie que le workflow '[DEV] Outlook Email Classifier' est actif sur n8n.obyz.biz\n"
                "→ Et que le credential Outlook OAuth2 est configuré."
            )
            return msg, "Le workflow Outlook est injoignable. Vérifie qu'il est actif sur n8n."

        processed = result.get("processed", 0)
        skipped = result.get("skipped", 0)
        urgent_count = result.get("urgent_count", 0)
        repondre_count = result.get("repondre_count", 0)
        recipient = result.get("summary_sent_to", "ton Outlook")

        if result.get("no_emails") or processed == 0:
            if skipped > 0:
                chat = (
                    f"📭 Aucun email Outlook à classifier parmi les {limit} derniers{limit_note}.\n"
                    f"{skipped} email(s) ignoré(s) automatiquement (déjà traités, newsletters, trop anciens)."
                )
                vocal = f"Aucun email Outlook à classifier parmi les {limit} derniers. {skipped} ignorés automatiquement."
            else:
                chat = f"✅ Aucun nouvel email Outlook dans les 8 dernières heures{limit_note}."
                vocal = "Aucun nouvel email Outlook dans les 8 dernières heures."
            return chat, vocal

        summary = result.get("summary", "")
        header = f"📬 Analyse de tes {processed} email(s) Outlook{limit_note} :\n\n"
        footer = f"\n\n✉️ Synthèse envoyée à {recipient}."
        chat = header + summary + footer

        urgence_note = f"{urgent_count} urgent(s), " if urgent_count > 0 else ""
        repondre_note = f"{repondre_count} à répondre" if repondre_count > 0 else "aucune réponse urgente"
        vocal = (
            f"J'ai analysé {processed} email(s) Outlook. "
            f"{urgence_note}{repondre_note}. "
            f"La synthèse a été envoyée sur {recipient}."
        )
        return chat, vocal

    # ── Gmail Email Classifier ────────────────────────────────────────────────
    CLASSIFY_KEYWORDS = [
        "classify", "classif", "classify emails", "classify my emails",
        "email summary", "synthèse emails", "synthese emails",
        "récapitulatif", "recapitulatif", "résumé des mails", "resume des mails",
        "analyse mes", "analyze my last", "last emails", "derniers mails",
    ]
    is_gmail_classify = any(k in t for k in CLASSIFY_KEYWORDS) or (
        any(k in t for k in ["email", "mail", "mails", "emails"]) and
        any(k in t for k in ["analyse", "analyze", "résumé", "resume", "classify", "class"])
    )
    if is_gmail_classify:
        limit = _parse_email_limit(t)
        limit_note = " (limité à 50 par sécurité)" if re.search(r'\b(\d+)\b', t) and int(re.search(r'\b(\d+)\b', t).group(1)) > 50 else ""

        result = await call_webhook("email-classifier", {"user_id": user_id, "limit": limit})

        if result and result.get("emails_structured"):
            await memory_service.set(
                user_id, "context", "recent_emails_gmail",
                result["emails_structured"], ttl_seconds=86400,
            )

        if not result:
            msg = (
                "⚠️ Le workflow de classification emails est injoignable.\n"
                "→ Vérifie que le workflow '[DEV] Gmail Email Classifier' est actif sur n8n.obyz.biz\n"
                "→ Et que le credential Gmail est configuré."
            )
            return msg, "Le workflow Gmail est injoignable. Vérifie qu'il est actif sur n8n."

        processed = result.get("processed", 0)
        skipped = result.get("skipped", 0)

        if result.get("no_emails") or processed == 0:
            if skipped > 0:
                chat = (
                    f"📭 Aucun email à classifier parmi les {limit} derniers{limit_note}.\n"
                    f"{skipped} email(s) ignoré(s) automatiquement (newsletters, no-reply, trop anciens)."
                )
                vocal = f"Aucun email Gmail à classifier. {skipped} ignorés automatiquement."
            else:
                chat = f"✅ Aucun nouvel email dans les 8 dernières heures{limit_note}."
                vocal = "Aucun nouvel email Gmail dans les 8 dernières heures."
            return chat, vocal

        summary = result.get("summary", "")
        header = f"📧 Classification de tes {processed} dernier(s) email(s){limit_note} :\n\n"
        footer = f"\n\n✉️ Synthèse envoyée à {result.get('summary_sent_to', 'ton Gmail')}."
        chat = header + summary + footer
        vocal = f"J'ai analysé {processed} emails Gmail. Synthèse envoyée sur {result.get('summary_sent_to', 'ton Gmail')}."
        return chat, vocal

    # ── Check emails prioritaires (Morning Briefing) ─────────────────────────
    if ("check" in t and "email" in t) or ("emails" in t and "priorit" in t):
        result = await call_webhook("morning-briefing", {"user_id": user_id})
        if not result:
            msg = (
                "⚠️ Impossible d'accéder à Gmail pour l'instant.\n"
                "→ Active le workflow Morning Briefing dans n8n.obyz.biz."
            )
            return msg, "Impossible d'accéder à Gmail. Active le workflow Morning Briefing."
        chat = f"📧 Tes emails prioritaires :\n\n{result.get('briefing', 'Aucune donnée.')}"
        return chat, "Voici tes emails prioritaires. J'ai affiché le détail dans le chat."

    # ── Smart Agent — analyse de notes ────────────────────────────────────────
    if any(k in t for k in ["analyze my notes", "analyse mes notes", "my notes"]):
        notes = text.split(":", 1)[-1].strip() if ":" in text else ""
        if not notes:
            msg = (
                "📝 Envoie-moi tes notes à analyser.\n"
                "Exemple : \"Analyze my notes: réunion lundi, budget Q3, relancer client X\""
            )
            return msg, "Envoie-moi tes notes à analyser. Par exemple : Analyze my notes, suivi de tes notes."
        result = await call_webhook("smart-agent", {"user_id": user_id, "notes": notes})
        if not result:
            msg = (
                "⚠️ Le workflow Smart Agent est injoignable.\n"
                "→ Active le workflow dans n8n.obyz.biz et configure le credential OpenAI."
            )
            return msg, "Le workflow Smart Agent est injoignable. Active-le sur n8n."
        if not result.get("action_plan"):
            msg = "⚠️ L'analyse n'a pas retourné de plan d'action. Réessaie avec des notes plus détaillées."
            return msg, "L'analyse n'a pas retourné de plan. Réessaie avec des notes plus détaillées."
        plan = "\n".join(f"• {step}" for step in result["action_plan"])
        email_status = "📩 Email draft créé et envoyé." if result.get("email_sent") else ""
        chat = f"📋 Plan d'action :\n\n{plan}\n\n{email_status}".strip()
        steps_count = len(result["action_plan"])
        vocal = f"J'ai créé un plan d'action en {steps_count} étapes à partir de tes notes."
        if result.get("email_sent"):
            vocal += " Un email draft a été créé."
        return chat, vocal

    # ── Compte-rendu de réunion (Dictée Avocat) ──────────────────────────────
    DICTATION_KEYWORDS = [
        "compte-rendu", "compte rendu", "rédige un compte", "note de réunion",
        "résumé de réunion", "resume de reunion", "meeting notes", "procès-verbal",
        "pv de réunion", "pv reunion", "redige un compte", "dictee reunion",
    ]
    if any(k in t for k in DICTATION_KEYWORDS):
        _dictation_state[user_id] = {"mode": "waiting_dictation"}
        chat = (
            "🎙️ **Mode dictée activé.**\n\n"
            "Décris ta réunion : participants, points discutés, décisions prises, actions à suivre.\n\n"
            "Dis **« c'est tout »** ou **« terminé »** quand tu as fini."
        )
        vocal = (
            "Mode dictée activé. Je t'écoute. "
            "Décris ta réunion et dis c'est tout quand tu as terminé."
        )
        return chat, vocal

    # ── Mémoire — "What do you know about me?" ──────────────────────────────
    MEMORY_KEYWORDS = [
        "what do you know", "what do you remember", "what you know",
        "que sais-tu", "tu sais quoi", "ta mémoire", "ce que tu sais",
        "what have you stored", "show memory", "ma mémoire",
    ]
    if any(k in t for k in MEMORY_KEYWORDS):
        all_memory = await memory_service.get_all_scopes(user_id)
        has_data = any(v for v in all_memory.values())

        if not has_data:
            chat = (
                "🧠 **Mémoire vide pour l'instant.**\n\n"
                "Je n'ai encore rien mémorisé sur toi. "
                "Tu peux me dire des choses à retenir, par exemple :\n"
                "• *\"Remember that my standup is every Monday at 9am\"*\n"
                "• *\"Remember I prefer concise answers\"*"
            )
            return chat, "Je n'ai encore rien mémorisé sur toi. Dis-moi ce que tu veux que je retienne."

        lines = ["🧠 **Voici ce que je sais sur toi :**\n"]
        icons = {"projects": "📁", "preferences": "⚙️", "tasks": "✅", "context": "💡"}
        for scope, entries in all_memory.items():
            if not entries:
                continue
            lines.append(f"\n**{icons.get(scope, '•')} {scope.capitalize()}**")
            for key, value in entries.items():
                display = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
                lines.append(f"• {key} : {display}")

        chat = "\n".join(lines)
        vocal = f"J'ai mémorisé des informations dans {sum(1 for v in all_memory.values() if v)} catégorie(s). J'ai affiché le détail dans le chat."
        return chat, vocal

    # ── Rappels / Tâches ─────────────────────────────────────────────────────
    REMIND_KEYWORDS = [
        "remind me", "rappelle-moi", "rappelle moi", "reminder", "add task",
        "ajoute une tâche", "ajoute une tache", "add reminder", "new task",
        "nouvelle tâche", "nouvelle tache",
    ]
    TASKS_LIST_KEYWORDS = [
        "my tasks", "mes tâches", "mes taches", "show tasks", "show reminders",
        "mes rappels", "liste mes tâches", "liste des tâches", "what are my tasks",
        "affiche mes tâches",
    ]

    if any(k in t for k in TASKS_LIST_KEYWORDS):
        tasks = await memory_service.get_all(user_id, "tasks")
        pending = {k: v for k, v in tasks.items() if not v.get("done", False)}
        if not pending:
            return "📋 Aucune tâche en cours.", "Tu n'as aucune tâche en cours."
        lines = ["📋 **Tes tâches en cours :**\n"]
        for tid, task in sorted(pending.items()):
            due = task.get("due_at")
            due_str = ""
            if due:
                try:
                    due_str = f" — échéance {datetime.fromisoformat(due).strftime('%d/%m à %H:%M')}"
                except ValueError:
                    pass
            lines.append(f"• {task['text']}{due_str}")
        chat = "\n".join(lines)
        vocal = f"Tu as {len(pending)} tâche(s) en cours. J'ai affiché la liste dans le chat."
        return chat, vocal

    if any(k in t for k in REMIND_KEYWORDS):
        # Extraire le texte de la tâche — tout ce qui suit "to", "de", ":"
        task_text = text.strip()
        for prefix in ["remind me to", "rappelle-moi de", "rappelle moi de", "add task:", "add task :",
                        "ajoute une tâche:", "ajoute une tache:", "add reminder:", "reminder:"]:
            if prefix in t:
                idx = t.index(prefix) + len(prefix)
                task_text = text[idx:].strip()
                break

        # Détecter heure (ex: "at 15h30", "at 3pm", "dans 30 minutes")
        due_at = None
        now_dt = datetime.now()
        at_match = re.search(r'\bat\s+(\d{1,2})(?:h|:)(\d{2})?(?:h)?\b', task_text.lower())
        in_match = re.search(r'\bin\s+(\d+)\s+(minute|minutes|min|hour|hours|heure|heures|h)\b', task_text.lower())
        if at_match:
            hour = int(at_match.group(1))
            minute = int(at_match.group(2)) if at_match.group(2) else 0
            due_at = now_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if due_at < now_dt:
                due_at = due_at + timedelta(days=1)
            task_text = re.sub(r'\bat\s+\d{1,2}(?:h|:)\d{0,2}(?:h)?\b', '', task_text, flags=re.IGNORECASE).strip()
        elif in_match:
            amount = int(in_match.group(1))
            unit = in_match.group(2).lower()
            if "min" in unit:
                due_at = now_dt + timedelta(minutes=amount)
            else:
                due_at = now_dt + timedelta(hours=amount)
            task_text = re.sub(r'\bin\s+\d+\s+\w+\b', '', task_text, flags=re.IGNORECASE).strip()

        if not task_text:
            return "❓ Dis-moi ce que tu veux que je te rappelle.", "Dis-moi ce que tu veux que je te rappelle."

        task_id = _task_key()
        task = {
            "text": task_text,
            "due_at": due_at.isoformat() if due_at else None,
            "created_at": now_dt.isoformat(),
            "done": False,
            "notified": False,
        }
        await memory_service.set(user_id, "tasks", task_id, task)

        if due_at:
            due_str = due_at.strftime("%d/%m à %H:%M")
            chat = f"✅ Rappel ajouté : **{task_text}** — échéance le {due_str}."
            vocal = f"Rappel ajouté : {task_text}, pour le {due_str}."
        else:
            chat = f"✅ Tâche ajoutée : **{task_text}**."
            vocal = f"Tâche ajoutée : {task_text}."
        return chat, vocal

    return None


@app.get("/")
async def root():
    return {"status": "ok", "message": "Jarvis V2 is running 🤖", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


class ChatRequest(BaseModel):
    text: str
    user_id: Optional[int] = None


@app.post("/api/chat")
async def http_chat(body: ChatRequest):
    """HTTP chat endpoint — used by n8n Telegram bot and external clients."""
    uid = body.user_id or _demo_user_id
    if not uid:
        raise HTTPException(status_code=503, detail="Demo user not ready")

    ctx = _contexts.get(uid) or ConversationContext()
    _contexts[uid] = ctx
    try:
        async def _http_tool_exec(name: str, args: dict) -> str:
            return await _execute_tool(name, args, uid)

        reply, _ = await chat_completion_with_tools(body.text, ctx, _http_tool_exec)
    except Exception as e:
        logger.error(f"HTTP chat error: {e}", exc_info=True)
        # Ajouter un message assistant placeholder pour éviter la cascade (2 user msgs consécutifs)
        ctx.add_message("assistant", "Une erreur est survenue. Réessaie.")
        raise HTTPException(status_code=500, detail=f"AI error: {type(e).__name__}: {e}")
    return {"response": reply}


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


# ── Reminders / Tasks API ─────────────────────────────────────────────────────

class ReminderCreate(BaseModel):
    text: str
    due_at: Optional[str] = None  # ISO datetime string, None = no specific time


def _task_key() -> str:
    return f"task_{int(time.time() * 1000)}"


@app.get("/api/reminders")
async def list_reminders():
    uid = _demo_user_id
    if not uid:
        raise HTTPException(status_code=503, detail="Demo user not ready")
    tasks = await memory_service.get_all(uid, "tasks")
    pending = {k: v for k, v in tasks.items() if not v.get("done", False)}
    return {"reminders": pending, "count": len(pending)}


@app.post("/api/reminders")
async def create_reminder(body: ReminderCreate):
    uid = _demo_user_id
    if not uid:
        raise HTTPException(status_code=503, detail="Demo user not ready")
    task_id = _task_key()
    task = {
        "text": body.text,
        "due_at": body.due_at,
        "created_at": datetime.now().isoformat(),
        "done": False,
        "notified": False,
    }
    await memory_service.set(uid, "tasks", task_id, task)
    return {"id": task_id, "task": task}


@app.get("/api/reminders/pending")
async def get_pending_reminders():
    """Used by n8n to fetch due reminders (due_at <= now, not yet notified)."""
    uid = _demo_user_id
    if not uid:
        return {"due": [], "count": 0}
    tasks = await memory_service.get_all(uid, "tasks")
    now = datetime.now(timezone.utc)
    due = []
    for task_id, task in tasks.items():
        if task.get("done") or task.get("notified"):
            continue
        due_at = task.get("due_at")
        if not due_at:
            continue
        try:
            dt = datetime.fromisoformat(due_at)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt <= now:
                due.append({"id": task_id, **task})
        except ValueError:
            pass
    return {"due": due, "count": len(due)}


@app.patch("/api/reminders/{task_id}/notified")
async def mark_notified(task_id: str):
    uid = _demo_user_id
    if not uid:
        raise HTTPException(status_code=503, detail="Demo user not ready")
    task = await memory_service.get(uid, "tasks", task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["notified"] = True
    await memory_service.set(uid, "tasks", task_id, task)
    return {"ok": True}


@app.patch("/api/reminders/{task_id}/done")
async def mark_done(task_id: str):
    uid = _demo_user_id
    if not uid:
        raise HTTPException(status_code=503, detail="Demo user not ready")
    task = await memory_service.get(uid, "tasks", task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["done"] = True
    await memory_service.set(uid, "tasks", task_id, task)
    return {"ok": True}


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

                async def _on_tool(tool_name: str):
                    await _send_ws(websocket, {
                        "type": "progress",
                        "message": _TOOL_PROGRESS.get(tool_name, "⚡ Traitement en cours..."),
                    })

                async def _tool_exec(name: str, args: dict) -> str:
                    return await _execute_tool(name, args, user_id)

                streamed: list[str] = []

                async def _on_chunk(chunk: str):
                    streamed.append(chunk)
                    await _send_ws(websocket, {"type": "stream_chunk", "content": chunk})

                reply, tools_called = await chat_completion_with_tools(
                    content, ctx, _tool_exec,
                    on_tool_call=_on_tool,
                    on_stream_chunk=_on_chunk,
                )
                await _send_ws(websocket, {"type": "response", "content": reply})
                if tools_called:
                    try:
                        tts_audio = await text_to_speech(reply)
                        await _send_ws(websocket, {"type": "tts", "audio": encode_audio_base64(tts_audio)})
                    except Exception as tts_err:
                        logger.warning(f"TTS tool response failed: {tts_err}")

            # ── Audio voix ──────────────────────────────────────────────────
            elif msg_type == "voice_input":
                audio_b64 = message.get("audio", "")
                if not audio_b64:
                    continue
                try:
                    audio_bytes = decode_audio_base64(audio_b64)
                except Exception:
                    await _send_ws(websocket, {
                        "type": "error",
                        "message": "Audio invalide — réessaie.",
                    })
                    continue

                # STT
                try:
                    transcript = await transcribe_audio(audio_bytes)
                except Exception as e:
                    logger.error(f"STT error [user_id={user_id}]: {e}")
                    await _send_ws(websocket, {
                        "type": "error",
                        "message": "Transcription échouée — vérifie ta connexion et réessaie.",
                    })
                    continue

                # ── Machine à états Dictée Avocat ───────────────────────────
                dstate = _dictation_state.get(user_id)

                if dstate and dstate["mode"] == "waiting_dictation":
                    # L'utilisateur vient de dicter sa réunion
                    await _send_ws(websocket, {
                        "type": "voice_response",
                        "transcript": transcript,
                        "audio": encode_audio_base64(
                            await text_to_speech("Parfait, je formate ton compte-rendu.") or b""
                        ),
                    })
                    await _send_ws(websocket, {"type": "progress", "message": "📝 Formatage du compte-rendu..."})
                    try:
                        data = await _format_compte_rendu(transcript)
                        _dictation_state[user_id] = {
                            "mode": "waiting_confirmation",
                            "draft": data["markdown"],
                            "title": data.get("titre", "Compte-rendu"),
                            "raw": data,
                        }
                        chat_text = data["markdown"] + "\n\n---\n💬 **Je t'envoie ça par Outlook ?** (oui / non)"
                        vocal_text = f"Voici ton compte-rendu : {data.get('titre', 'compte-rendu de réunion')}. Je te l'envoie par Outlook ?"
                        cr_payload = {k: v for k, v in data.items() if k != "markdown"}
                        await _send_ws(websocket, {
                            "type": "response",
                            "content": chat_text,
                            "voice_origin": True,
                            "cr_data": cr_payload,
                        })
                        audio_response = await text_to_speech(vocal_text)
                        await _send_ws(websocket, {"type": "tts", "audio": encode_audio_base64(audio_response)})
                    except Exception as e:
                        logger.error(f"Compte-rendu format error: {e}")
                        _dictation_state.pop(user_id, None)
                        await _send_ws(websocket, {
                            "type": "error",
                            "message": "Erreur lors du formatage du compte-rendu. Réessaie.",
                        })
                    continue

                if dstate and dstate["mode"] == "waiting_confirmation":
                    t_lower = transcript.lower().strip()
                    confirmed = any(k in t_lower for k in ["oui", "yes", "envoie", "envoie-le", "vas-y", "ok", "affirmatif"])
                    cancelled = any(k in t_lower for k in ["non", "no", "annule", "cancel", "pas", "stop"])

                    if confirmed:
                        _dictation_state.pop(user_id, None)
                        await _send_ws(websocket, {
                            "type": "voice_response", "transcript": transcript,
                            "audio": encode_audio_base64(await text_to_speech("Envoi en cours...") or b""),
                        })
                        result = await call_webhook("send-outlook-email", {
                            "to": "ouat.abou34@outlook.fr",
                            "subject": dstate.get("title", "Compte-rendu de réunion"),
                            "body": dstate.get("draft", ""),
                        })
                        if result and result.get("ok"):
                            sent_to = result.get("sent_to", "ouat.abou34@outlook.fr")
                            chat_ok = f"✅ Compte-rendu envoyé à **{sent_to}**."
                            vocal_ok = f"Compte-rendu envoyé avec succès."
                        else:
                            chat_ok = "⚠️ Envoi échoué — vérifie le workflow n8n send-outlook-email."
                            vocal_ok = "L'envoi a échoué. Vérifie le workflow n8n."
                        await _send_ws(websocket, {"type": "response", "content": chat_ok, "voice_origin": True})
                        audio_response = await text_to_speech(vocal_ok)
                        await _send_ws(websocket, {"type": "tts", "audio": encode_audio_base64(audio_response)})
                    elif cancelled:
                        _dictation_state.pop(user_id, None)
                        msg = "📋 Compte-rendu conservé localement. Envoi annulé."
                        await _send_ws(websocket, {"type": "response", "content": msg, "voice_origin": True})
                        audio_response = await text_to_speech("Envoi annulé. Le compte-rendu est affiché dans le chat.")
                        await _send_ws(websocket, {"type": "tts", "audio": encode_audio_base64(audio_response)})
                    else:
                        # Réponse ambiguë → reposer la question
                        msg = "❓ Je n'ai pas compris. Dis **oui** pour envoyer ou **non** pour annuler."
                        await _send_ws(websocket, {"type": "response", "content": msg, "voice_origin": True})
                        audio_response = await text_to_speech("Dis oui pour envoyer ou non pour annuler.")
                        await _send_ws(websocket, {"type": "tts", "audio": encode_audio_base64(audio_response)})
                    continue

                # ── Trigger dictée avocat (état machine stateful) ───────────
                if _is_dictation_trigger(transcript):
                    _dictation_state[user_id] = {"mode": "waiting_dictation"}
                    vocal_trigger = "Mode dictée activé. Je t'écoute. Décris ta réunion et dis c'est tout quand tu as terminé."
                    chat_trigger = "🎙️ **Mode dictée activé.**\n\nDécris ta réunion : participants, points discutés, décisions, actions.\n\nDis **« c'est tout »** quand tu as fini."
                    audio_trigger = await text_to_speech(vocal_trigger)
                    await _send_ws(websocket, {"type": "voice_response", "transcript": transcript, "audio": encode_audio_base64(audio_trigger)})
                    await _send_ws(websocket, {"type": "response", "content": chat_trigger, "voice_origin": True})
                    continue

                # ── Pipeline IA avec function calling ───────────────────────
                ctx = _contexts[user_id]
                try:
                    async def _on_voice_tool(tool_name: str):
                        await _send_ws(websocket, {
                            "type": "progress",
                            "message": _TOOL_PROGRESS.get(tool_name, "⚡ Traitement en cours..."),
                        })

                    async def _voice_tool_exec(name: str, args: dict) -> str:
                        return await _execute_tool(name, args, user_id)

                    reply_text, _ = await chat_completion_with_tools(
                        transcript, ctx, _voice_tool_exec, on_tool_call=_on_voice_tool
                    )
                    audio_response = await text_to_speech(reply_text)
                except Exception as e:
                    logger.error(f"AI pipeline error [user_id={user_id}]: {e}")
                    await _send_ws(websocket, {
                        "type": "error",
                        "message": "Erreur IA — réessaie dans un instant.",
                    })
                    continue

                await _send_ws(websocket, {
                    "type": "voice_response",
                    "transcript": transcript,
                    "audio": encode_audio_base64(audio_response),
                })
                await _send_ws(websocket, {
                    "type": "response",
                    "content": reply_text,
                    "voice_origin": True,
                })

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
        await _send_ws(websocket, {
            "type": "error",
            "message": "Une erreur inattendue s'est produite. Reconnecte-toi si le problème persiste.",
        })
    finally:
        _contexts.pop(user_id, None)
        _dictation_state.pop(user_id, None)
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

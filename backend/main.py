"""Jarvis Backend â€” FastAPI + WebSocket pipeline complet."""

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

# Ã‰tat de dictÃ©e par utilisateur (machine Ã  Ã©tats DictÃ©e Avocat)
# { user_id: { "mode": "waiting_dictation" | "waiting_confirmation", "draft": str, "title": str } }
_dictation_state: dict[int, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _demo_token, _demo_user_id, _realtime_ok
    logger.info("ðŸš€ Jarvis backend dÃ©marrage...")

    # Initialize database
    init_db()

    # Create or get demo user (hackathon single user)
    demo_email = os.getenv("GMAIL_USER_EMAIL", "demo@jarvis.local")
    _demo_user_id, _demo_token = await ensure_demo_user_exists(demo_email)
    logger.info(f"âœ“ Demo user created/loaded: {demo_email} (user_id={_demo_user_id})")

    init_n8n()
    init_domotics()
    _realtime_ok = await check_realtime_access()
    mode = "[REALTIME]" if _realtime_ok else "[WHISPER_FALLBACK]"
    logger.info(f"âœ“ Mode voix: {mode}")
    yield
    await memory_service.close()
    logger.info("ðŸ‘‹ Jarvis backend arrÃªt")


app = FastAPI(
    title="Jarvis V2",
    description="Assistant IA vocal intelligent",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_TOOL_PROGRESS: dict[str, str] = {
    "analyser_emails_gmail":      "Analyse des emails Gmail...",
    "analyser_emails_outlook":    "Analyse des emails Outlook...",
    "consulter_derniere_analyse": "Consultation de la derniere analyse...",
    "lire_inbox_outlook":         "Lecture de la boite Outlook en temps reel...",
    "lire_agenda":                "Lecture de l'agenda Google Calendar...",
    "morning_briefing":           "Preparation du briefing du matin...",
    "creer_rappel":               "Creation du rappel...",
    "rechercher_emails":          "Recherche dans Gmail et Outlook...",
    "creer_evenement_agenda":     "Ajout dans Google Calendar...",
    "creer_brouillon_gmail":      "Creation du brouillon Gmail...",
    "envoyer_email_outlook":      "Envoi de l'email via Outlook...",
    "analyser_notes":             "Analyse des notes et creation du plan d'action...",
    "rechercher_memoire":         "Recherche en memoire...",
    "sauvegarder_memoire":        "Memorisation en cours...",
}

def _format_emails_context(source: str, emails: list) -> str:
    lines = [f"## Emails rÃ©cents {source} ({len(emails)})"]
    for e in emails[:10]:
        urgence = f" [{e.get('urgence')}]" if e.get('urgence') not in (None, 'faible') else ""
        lines.append(
            f"- De : {e.get('from_name') or e.get('from', '?')} <{e.get('from_email', '')}>"
            f" | Objet : {e.get('subject', '?')}"
            f" | Action : {e.get('action', '?')}{urgence}"
            f" | RÃ©sumÃ© : {e.get('resume', '')}"
            + (f" | Ã‰chÃ©ance : {e['echeance']}" if e.get('echeance') else "")
        )
    return "\n".join(lines)

async def _execute_tool(name: str, args: dict, user_id: int) -> str:
    """ExÃ©cute un outil Jarvis et retourne le rÃ©sultat en texte pour GPT-4o."""
    if name == "analyser_emails_gmail":
        limit = min(int(args.get("limit", 10)), 50)
        wh = "email-classifier-v2" if settings.WORKFLOW_VERSION == "v2" else "email-classifier"
        result = await call_webhook(wh, {"user_id": user_id, "limit": limit})
        if result and result.get("emails_structured"):
            await memory_service.set(
                user_id, "context", "recent_emails_gmail",
                result["emails_structured"], ttl_seconds=settings.EMAIL_ANALYSIS_CACHE_TTL,
            )
        if not result:
            return "Le workflow Gmail est injoignable. VÃ©rifie qu'il est actif sur n8n."
        if result.get("no_emails"):
            return f"Aucun email Gmail non lu dans les 8 derniÃ¨res heures. {result.get('skipped', 0)} ignorÃ©s automatiquement."
        return result.get("summary", f"{result.get('processed', 0)} emails Gmail analysÃ©s.")

    if name == "analyser_emails_outlook":
        limit = min(int(args.get("limit", 10)), 50)
        wh = "outlook-email-classifier-v2" if settings.WORKFLOW_VERSION == "v2" else "outlook-email-classifier"
        result = await call_webhook(wh, {"user_id": user_id, "limit": limit}, timeout=45.0)
        if result and result.get("emails_structured"):
            await memory_service.set(
                user_id, "context", "recent_emails_outlook",
                result["emails_structured"], ttl_seconds=settings.EMAIL_ANALYSIS_CACHE_TTL,
            )
        if not result:
            return "Le workflow Outlook est injoignable. VÃ©rifie qu'il est actif sur n8n."
        if result.get("no_emails"):
            return f"Aucun email Outlook rÃ©cent. {result.get('skipped', 0)} ignorÃ©s."
        return result.get("summary", f"{result.get('processed', 0)} emails Outlook analysÃ©s.")

    if name == "consulter_derniere_analyse":
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

        # Redis vide â€” fallback direct vers les workflows de recherche
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
        return "Aucun email trouvÃ©. VÃ©rifie que les workflows Gmail et Outlook sont actifs dans n8n."

    if name == "lire_inbox_outlook":
        limit = min(int(args.get("limit", 10)), 20)
        dossier = args.get("dossier", "inbox").strip() or "inbox"
        result = await call_webhook("outlook-read-inbox", {"limit": limit, "folder": dossier})
        if not result or not result.get("ok"):
            return "Impossible de lire la boÃ®te Outlook. VÃ©rifie que le workflow outlook-read-inbox est actif."
        emails = result.get("emails", [])
        if not emails:
            return "Aucun email dans la boÃ®te Outlook en ce moment."
        await memory_service.set(
            user_id, "context", "inbox_outlook_live", emails,
            ttl_seconds=settings.EMAIL_INBOX_CACHE_TTL,
        )
        _folder_labels = {"inbox": "Boite de reception", "junkemail": "Spam", "deleteditems": "Supprimes", "sentItems": "Envoyes", "drafts": "Brouillons", "archive": "Archive"}
        folder_label = _folder_labels.get(dossier, dossier)
        lines = [f"## Outlook ({folder_label}) — {len(emails)} emails recents"]
        for e in emails[:10]:
            preview = f" | {e.get('bodyPreview', '')[:80]}" if e.get("bodyPreview") else ""
            # Le noeud natif microsoftOutlook renvoie `from` comme string ou dict Graph API
            from_raw = e.get("from", "?")
            if isinstance(from_raw, dict):
                from_addr = from_raw.get("emailAddress", {}).get("address", "?")
            else:
                from_addr = str(from_raw)
            lines.append(
                f"- De : {from_addr} "
                f"| Objet : {e.get('subject', '?')} "
                f"| {e.get('receivedDateTime', '')[:10]}"
                f"{preview}"
            )
        return "\n".join(lines)

    if name == "lire_agenda":
        from datetime import date as _date
        date_debut = args.get("date_debut", _date.today().isoformat())
        date_fin = args.get("date_fin", date_debut)
        result = await call_webhook("google-calendar-read", {
            "date_debut": date_debut,
            "date_fin": date_fin,
            "calendar_id": settings.CLIENT_CALENDAR_ID,
        })
        if not result or not result.get("ok"):
            return "Impossible de lire l'agenda. Verifie que le workflow google-calendar-read est actif."
        events = result.get("events", [])
        if not events:
            return f"Aucun evenement du {date_debut} au {date_fin}."
        curated = []
        for e in events:
            start_e = e.get("start", {})
            end_e = e.get("end", {})
            curated.append({
                "summary": e.get("summary", "?"),
                "start": start_e.get("dateTime", start_e.get("date", "?")),
                "end": end_e.get("dateTime", end_e.get("date", "")),
                "location": e.get("location", ""),
            })
        return json.dumps({"events": curated, "date_debut": date_debut, "date_fin": date_fin}, ensure_ascii=False)
    if name == "morning_briefing":
        result = await call_webhook("morning-briefing", {"user_id": user_id})
        if not result:
            return "Le workflow Morning Briefing est injoignable. VÃ©rifie qu'il est actif sur n8n."
        return result.get("briefing", "Briefing reÃ§u.")

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
        return f"Rappel crÃ©Ã© : Â« {texte} Â»" + (f", Ã©chÃ©ance : {echeance}" if echeance else ".")

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
                lines = [f"### Gmail â€” {len(emails)} rÃ©sultat(s) pour Â« {q} Â»"]
                for e in emails:
                    lines.append(f"- {e.get('from_name') or e.get('from')} | {e.get('subject')} | {e.get('snippet','')[:120]}")
                parts.append("\n".join(lines))
            elif r and not r.get("ok"):
                parts.append(f"Gmail : {r.get('error', 'Aucun rÃ©sultat.')}")
            else:
                parts.append("Gmail : aucun email trouvÃ©.")

        if source in ("outlook", "tous"):
            r = await call_webhook("outlook-search", {"q": q, "limit": limit, "date_from": date_from})
            if r and r.get("ok") and r.get("emails"):
                emails = r["emails"]
                lines = [f"### Outlook â€” {len(emails)} rÃ©sultat(s)"]
                for e in emails:
                    lines.append(f"- {e.get('from_name') or e.get('from')} | {e.get('subject')} | {e.get('snippet','')[:120]}")
                parts.append("\n".join(lines))
            elif r and not r.get("ok"):
                parts.append(f"Outlook : {r.get('error', 'Aucun rÃ©sultat.')}")
            else:
                parts.append("Outlook : aucun email trouvÃ©.")

        return "\n\n".join(parts) if parts else "Aucun rÃ©sultat trouvÃ©."

    if name == "analyser_notes":
        notes = args.get("notes", "").strip()
        if not notes:
            return "Notes manquantes. PrÃ©cise le contenu Ã  analyser."
        result = await call_webhook("smart-agent", {"user_id": user_id, "notes": notes})
        if not result:
            return "Le workflow Smart Agent est injoignable. VÃ©rifie qu'il est actif sur n8n."
        if not result.get("action_plan"):
            return "L'analyse n'a pas retournÃ© de plan. RÃ©essaie avec des notes plus dÃ©taillÃ©es."
        plan = "\n".join(f"â€¢ {step}" for step in result["action_plan"])
        email_note = "\n\nðŸ“© Email draft crÃ©Ã© et envoyÃ©." if result.get("email_sent") else ""
        return f"Plan d'action :\n{plan}{email_note}"

    if name == "creer_evenement_agenda":
        titre = args.get("titre", "").strip()
        debut = args.get("debut", "").strip()
        fin   = args.get("fin", "").strip()
        if not all([titre, debut, fin]):
            return "Titre, dÃ©but et fin sont requis pour crÃ©er un Ã©vÃ©nement."
        result = await call_webhook("google-calendar-create-event", {
            "titre": titre, "debut": debut, "fin": fin,
            "description": args.get("description", ""),
            "lieu": args.get("lieu", ""),
        })
        if not result or not result.get("ok"):
            err = result.get("error", "Erreur inconnue") if result else "Workflow google-calendar-create-event injoignable."
            return f"Impossible de crÃ©er l'Ã©vÃ©nement : {err}"
        try:
            d = datetime.fromisoformat(debut)
            date_str = d.strftime("%A %d %B Ã  %Hh%M")
        except Exception:
            date_str = debut
        return f"Ã‰vÃ©nement crÃ©Ã© âœ…\n**{titre}** â€” {date_str}"

    if name == "creer_brouillon_gmail":
        to = args.get("to", "").strip()
        subject = args.get("subject", "").strip()
        body = args.get("body", "").strip()
        if not all([to, subject, body]):
            return "Champs manquants : to, subject et body sont requis."
        result = await call_webhook("gmail-draft", {"to": to, "subject": subject, "body": body})
        if not result or not result.get("ok"):
            err = result.get("error", "Erreur inconnue") if result else "Workflow gmail-draft injoignable."
            return f"Impossible de crÃ©er le brouillon : {err}"
        return f"Brouillon Gmail crÃ©Ã© âœ…\nÃ€ : {to}\nObjet : {subject}\nTu peux le relire et l'envoyer depuis Gmail."

    if name == "envoyer_email_outlook":
        to = args.get("to", "").strip()
        subject = args.get("subject", "").strip()
        body = args.get("body", "").strip()
        if not all([to, subject, body]):
            return "Champs manquants : to, subject et body sont requis."
        result = await call_webhook("send-outlook-email", {"to": to, "subject": subject, "body": body})
        if not result or not result.get("ok"):
            return "Envoi Ã©chouÃ©. VÃ©rifie le workflow send-outlook-email et les credentials Outlook."
        return f"Email envoyÃ© via Outlook âœ…\nÃ€ : {result.get('sent_to', to)}\nObjet : {result.get('subject', subject)}"

    if name == "sauvegarder_memoire":
        cle    = args.get("cle", "").strip().replace(" ", "_")
        valeur = args.get("valeur", "").strip()
        scope  = args.get("scope", "preferences")
        if not cle or not valeur:
            return "ClÃ© et valeur sont requises pour mÃ©moriser."
        if scope not in ("preferences", "projects", "tasks"):
            scope = "preferences"
        await memory_service.set(user_id, scope, cle, valeur)
        return f"MÃ©morisÃ© âœ… [{scope}/{cle}] : {valeur}"

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
            return f"Rien trouvÃ© en mÃ©moire pour Â« {requete} Â»."
        return "\n".join(results[:8])

    return f"Outil inconnu : {name}."


async def _send_ws(websocket: WebSocket, payload: dict) -> None:
    """Envoie un message WebSocket sans lever d'exception si la connexion est fermÃ©e."""
    try:
        await websocket.send_text(json.dumps(payload))
    except Exception:
        pass


async def _format_compte_rendu(transcript: str) -> dict:
    """Formate une dictÃ©e brute en compte-rendu structurÃ© via GPT-4o (JSON mode)."""
    from backend.services.ai_service import _get_client
    from backend.config import get_settings as _gs
    today = __import__("datetime").date.today().isoformat()
    system_prompt = (
        "Tu es un assistant juridique expert. "
        "Formate ce compte-rendu de rÃ©union en JSON structurÃ©. "
        "Champs requis : titre (string), date (YYYY-MM-DD ou 'Non prÃ©cisÃ©e'), "
        "participants (liste de strings), points_discutes (liste de strings), "
        "decisions (liste de strings), actions (liste de strings avec responsable si mentionnÃ©). "
        f"Date du jour si non prÃ©cisÃ©e : {today}. "
        "Sois prÃ©cis, professionnel, neutre. Ne jamais inventer de faits non mentionnÃ©s."
    )
    client = _get_client()
    resp = await client.chat.completions.create(
        model=_gs().OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"DictÃ©e Ã  formater :\n\n{transcript}"},
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

    def _list_md(items: list, icon: str = "â€¢") -> str:
        return "\n".join(f"{icon} {i}" for i in items) if items else f"{icon} Aucun"

    markdown = (
        f"## ðŸ“‹ {data.get('titre', 'Compte-rendu de rÃ©union')}\n"
        f"**Date :** {data.get('date', today)}\n\n"
        f"**Participants :** {', '.join(data.get('participants', [])) or 'Non prÃ©cisÃ©s'}\n\n"
        f"### Points discutÃ©s\n{_list_md(data.get('points_discutes', []))}\n\n"
        f"### DÃ©cisions\n{_list_md(data.get('decisions', []))}\n\n"
        f"### Actions\n{_list_md(data.get('actions', []))}"
    )
    data["markdown"] = markdown
    return data


_DICTATION_TRIGGERS = {
    "compte-rendu", "compte rendu", "rÃ©dige un compte", "note de rÃ©union",
    "meeting notes", "procÃ¨s-verbal", "pv de rÃ©union", "dictÃ©e reunion",
}

def _is_dictation_trigger(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in _DICTATION_TRIGGERS)


async def _handle_n8n_command(text: str, user_id: int) -> tuple[str, str] | None:
    """ObsolÃ¨te. Toutes les commandes passent par function calling. ConservÃ© pour compatibilitÃ©."""
    return None



@app.get("/")
async def root():
    return {"status": "ok", "message": "Jarvis V2 is running ðŸ¤–", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


class WorkflowSettings(BaseModel):
    workflow_version: Optional[str] = None


@app.post("/api/settings")
async def update_settings(body: WorkflowSettings):
    """Met à jour les settings runtime (version workflows n8n, etc.)."""
    if body.workflow_version and body.workflow_version in ("v1", "v2"):
        settings.WORKFLOW_VERSION = body.workflow_version
    return {"ok": True, "workflow_version": settings.WORKFLOW_VERSION}


@app.get("/api/settings")
async def read_app_settings():
    return {"workflow_version": settings.WORKFLOW_VERSION}


class ChatRequest(BaseModel):
    text: str
    user_id: Optional[int] = None


@app.post("/api/chat")
async def http_chat(body: ChatRequest):
    """HTTP chat endpoint â€” used by n8n Telegram bot and external clients."""
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
        # Ajouter un message assistant placeholder pour Ã©viter la cascade (2 user msgs consÃ©cutifs)
        ctx.add_message("assistant", "Une erreur est survenue. RÃ©essaie.")
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


# â”€â”€ Reminders / Tasks API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
    logger.info(f"âœ“ Client WebSocket connectÃ© [user_id={user_id}]")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "")

            # â”€â”€ Chat texte â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            if msg_type == "chat":
                content = message.get("content", "").strip()
                if not content:
                    continue
                ctx = _contexts[user_id]

                async def _on_tool(tool_name: str):
                    await _send_ws(websocket, {
                        "type": "progress",
                        "message": _TOOL_PROGRESS.get(tool_name, "âš¡ Traitement en cours..."),
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

            # â”€â”€ Audio voix â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            elif msg_type == "voice_input":
                audio_b64 = message.get("audio", "")
                if not audio_b64:
                    continue
                try:
                    audio_bytes = decode_audio_base64(audio_b64)
                except Exception:
                    await _send_ws(websocket, {
                        "type": "error",
                        "message": "Audio invalide â€” rÃ©essaie.",
                    })
                    continue

                # STT
                try:
                    transcript = await transcribe_audio(audio_bytes)
                except Exception as e:
                    logger.error(f"STT error [user_id={user_id}]: {e}")
                    await _send_ws(websocket, {
                        "type": "error",
                        "message": "Transcription Ã©chouÃ©e â€” vÃ©rifie ta connexion et rÃ©essaie.",
                    })
                    continue

                # â”€â”€ Machine Ã  Ã©tats DictÃ©e Avocat â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                dstate = _dictation_state.get(user_id)

                if dstate and dstate["mode"] == "waiting_dictation":
                    # L'utilisateur vient de dicter sa rÃ©union
                    await _send_ws(websocket, {
                        "type": "voice_response",
                        "transcript": transcript,
                        "audio": encode_audio_base64(
                            await text_to_speech("Parfait, je formate ton compte-rendu.") or b""
                        ),
                    })
                    await _send_ws(websocket, {"type": "progress", "message": "ðŸ“ Formatage du compte-rendu..."})
                    try:
                        data = await _format_compte_rendu(transcript)
                        _dictation_state[user_id] = {
                            "mode": "waiting_confirmation",
                            "draft": data["markdown"],
                            "title": data.get("titre", "Compte-rendu"),
                            "raw": data,
                        }
                        chat_text = data["markdown"] + "\n\n---\nðŸ’¬ **Je t'envoie Ã§a par Outlook ?** (oui / non)"
                        vocal_text = f"Voici ton compte-rendu : {data.get('titre', 'compte-rendu de rÃ©union')}. Je te l'envoie par Outlook ?"
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
                            "message": "Erreur lors du formatage du compte-rendu. RÃ©essaie.",
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
                            "subject": dstate.get("title", "Compte-rendu de rÃ©union"),
                            "body": dstate.get("draft", ""),
                        })
                        if result and result.get("ok"):
                            sent_to = result.get("sent_to", "ouat.abou34@outlook.fr")
                            chat_ok = f"âœ… Compte-rendu envoyÃ© Ã  **{sent_to}**."
                            vocal_ok = f"Compte-rendu envoyÃ© avec succÃ¨s."
                        else:
                            chat_ok = "âš ï¸ Envoi Ã©chouÃ© â€” vÃ©rifie le workflow n8n send-outlook-email."
                            vocal_ok = "L'envoi a Ã©chouÃ©. VÃ©rifie le workflow n8n."
                        await _send_ws(websocket, {"type": "response", "content": chat_ok, "voice_origin": True})
                        audio_response = await text_to_speech(vocal_ok)
                        await _send_ws(websocket, {"type": "tts", "audio": encode_audio_base64(audio_response)})
                    elif cancelled:
                        _dictation_state.pop(user_id, None)
                        msg = "ðŸ“‹ Compte-rendu conservÃ© localement. Envoi annulÃ©."
                        await _send_ws(websocket, {"type": "response", "content": msg, "voice_origin": True})
                        audio_response = await text_to_speech("Envoi annulÃ©. Le compte-rendu est affichÃ© dans le chat.")
                        await _send_ws(websocket, {"type": "tts", "audio": encode_audio_base64(audio_response)})
                    else:
                        # RÃ©ponse ambiguÃ« â†’ reposer la question
                        msg = "â“ Je n'ai pas compris. Dis **oui** pour envoyer ou **non** pour annuler."
                        await _send_ws(websocket, {"type": "response", "content": msg, "voice_origin": True})
                        audio_response = await text_to_speech("Dis oui pour envoyer ou non pour annuler.")
                        await _send_ws(websocket, {"type": "tts", "audio": encode_audio_base64(audio_response)})
                    continue

                # â”€â”€ Trigger dictÃ©e avocat (Ã©tat machine stateful) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if _is_dictation_trigger(transcript):
                    _dictation_state[user_id] = {"mode": "waiting_dictation"}
                    vocal_trigger = "Mode dictÃ©e activÃ©. Je t'Ã©coute. DÃ©cris ta rÃ©union et dis c'est tout quand tu as terminÃ©."
                    chat_trigger = "ðŸŽ™ï¸ **Mode dictÃ©e activÃ©.**\n\nDÃ©cris ta rÃ©union : participants, points discutÃ©s, dÃ©cisions, actions.\n\nDis **Â« c'est tout Â»** quand tu as fini."
                    audio_trigger = await text_to_speech(vocal_trigger)
                    await _send_ws(websocket, {"type": "voice_response", "transcript": transcript, "audio": encode_audio_base64(audio_trigger)})
                    await _send_ws(websocket, {"type": "response", "content": chat_trigger, "voice_origin": True})
                    continue

                # â”€â”€ Pipeline IA avec function calling â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                ctx = _contexts[user_id]
                try:
                    async def _on_voice_tool(tool_name: str):
                        await _send_ws(websocket, {
                            "type": "progress",
                            "message": _TOOL_PROGRESS.get(tool_name, "âš¡ Traitement en cours..."),
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
                        "message": "Erreur IA â€” rÃ©essaie dans un instant.",
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

            # â”€â”€ Memory set â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

            # â”€â”€ Memory get â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

            # â”€â”€ Session summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            elif msg_type == "session_summary":
                all_memory = await memory_service.get_all_scopes(user_id)
                ctx = _contexts[user_id]
                history_preview = [
                    f"{m['role']}: {m['content'][:80]}" for m in ctx.history[-10:]
                ]
                summary_prompt = (
                    f"RÃ©sume cette session en 3-5 bullets (dÃ©cisions, tÃ¢ches, mÃ©mos):\n"
                    f"Historique: {history_preview}\n"
                    f"MÃ©moire: {all_memory}"
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
            "message": "Une erreur inattendue s'est produite. Reconnecte-toi si le problÃ¨me persiste.",
        })
    finally:
        _contexts.pop(user_id, None)
        _dictation_state.pop(user_id, None)
        logger.info(f"âœ— Client WebSocket dÃ©connectÃ© [user_id={user_id}]")


@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    await websocket.accept()
    client_id = id(websocket)
    logger.info(f"âœ“ Client Realtime connectÃ© [{client_id}]")
    try:
        await realtime_session(websocket)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Realtime error [{client_id}]: {e}")
    finally:
        logger.info(f"âœ— Client Realtime dÃ©connectÃ© [{client_id}]")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

# JARVIS — Assistant IA Vocal Personnel

> **Hackathon IAPreneur 2026 · Obyz · Aboubakary Ouattara**

---

## Liens de livraison

| | |
|---|---|
| 🌐 **Démo live** | https://jarvis.obyz.biz |
| 🎥 **Vidéo démo** | https://www.loom.com/share/91633a6b07a741c6b5db919ce1fe1faf |
| 📊 **Présentation** | [Voir la présentation](https://htmlpreview.github.io/?https://github.com/AbouOuat/AssistantVocalIA/blob/main/PRESENTATION_JARVIS.html) · [Source](./PRESENTATION_JARVIS.html) |
| 📄 **Recap technique** | [RECAP_SESSION_2026-06-04.md](./RECAP_SESSION_2026-06-04.md) |

---

## Ce que fait Jarvis

Jarvis est un assistant IA vocal personnel. Il comprend ce que tu dis, agit sur tes outils, et se souvient de toi.

**5 démos validées :**

| Phrase naturelle | Action déclenchée |
|---|---|
| *"Lance mon briefing du matin"* | Météo + agenda du jour + emails importants |
| *"T'as des trucs urgents dans mes mails ?"* | Classification Gmail + Outlook, résumé vocal |
| *"Rappelle-moi d'appeler Jean dans 1h"* | Rappel Redis + email de confirmation |
| *"Ajoute un RDV Démo Jarvis demain à 10h"* | Event Google Calendar (bon fuseau) |
| *"Souviens-toi que je préfère mes briefings à 8h"* | Mémoire persistante Redis |

---

## Stack technique

| Couche | Techno |
|---|---|
| Backend | FastAPI · Python 3.11 |
| LLM | OpenAI GPT-4o · Function Calling (12 tools) |
| Voix | Whisper STT · OpenAI TTS |
| Frontend | Next.js 14 · Tailwind · Framer Motion · shadcn/ui |
| Automatisation | N8N · 11 workflows actifs |
| Mémoire | Redis (4 scopes) · PostgreSQL |
| Intégrations | Gmail OAuth · Outlook · Google Calendar |
| Infra | Docker Compose · Nginx · Coolify · VPS Hostinger · HTTPS |

---

## Architecture

```
Voix / Texte
    ↓
Whisper STT → FastAPI (WebSocket)
    ↓
GPT-4o Function Calling
    ↓ (12 tools)
N8N webhooks          Redis (mémoire)
    ↓                     ↓
Gmail · Outlook · Google Calendar · TTS
```

---

## Lancer en local

```bash
git clone https://github.com/AbouOuat/AssistantVocalIA
cp .env.example .env   # remplir les clés API
docker compose up --build
```

Frontend : http://localhost:3000 · Backend : http://localhost:8000

---

*Construit en 4 jours · Solo · Sans lever de fonds*
*Obyz · 2026*

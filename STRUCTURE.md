# STRUCTURE.md — Carte d'architecture Jarvis V2

> Rempli par `/architect` Étape 6.5. Lu par `/prime` au début de chaque session.
> Mettre à jour si réorganisation post-scaffold. `/architect` appendera dans "Modifications post-scaffold" si rejoué.

## Arborescence

<!-- architect:directories -->
```
projet-jarvis/
├── src/                        ← Next.js App Router (frontend)
│   ├── app/
│   │   ├── page.tsx            ← UI principale Jarvis (orb + chat + quick actions)
│   │   ├── layout.tsx          ← Layout global dark theme
│   │   └── api/
│   │       ├── transcribe/     ← Endpoint REST fallback STT
│   │       └── sessions/       ← Export session summaries
│   ├── components/
│   │   ├── ui/                 ← shadcn/ui (Button, Card, etc.)
│   │   ├── VoiceOrb.tsx        ← Orb animé Framer Motion (idle/listening/speaking)
│   │   ├── Chat.tsx            ← Historique messages + live transcript
│   │   ├── QuickActions.tsx    ← 5 raccourcis preset
│   │   └── LiveTranscript.tsx  ← Sous-titres temps réel
│   └── lib/
│       ├── realtime.ts         ← Client OpenAI Realtime API (WebSocket)
│       ├── vad.ts              ← Voice Activity Detection client-side
│       ├── websocket.ts        ← Connexion WebSocket → FastAPI backend
│       └── memory.ts           ← Appels API Named Scopes
├── backend/                    ← Python FastAPI (reorganisé depuis backend_*.py)
│   ├── main.py                 ← FastAPI app + WebSocket handler (connecté aux services)
│   ├── config.py               ← Settings depuis .env
│   └── services/
│       ├── ai_service.py       ← GPT-4o conversation + streaming
│       ├── voice_service.py    ← Whisper STT + TTS (fallback Realtime API)
│       ├── agents_service.py   ← LangChain agents (tools sécurisés)
│       ├── n8n_service.py      ← Client n8n workflows
│       ├── domotics_service.py ← Smart home (mock → réel en V3)
│       └── memory_service.py   ← Redis Named Scopes (NOUVEAU)
├── sessions/                   ← Session Summary exports (.md par session)
├── tests/
│   └── e2e/                    ← Tests Playwright
│       ├── voice-connection.spec.ts
│       ├── morning-briefing.spec.ts
│       ├── smart-agent.spec.ts
│       ├── memory-scopes.spec.ts
│       └── fallback.spec.ts
├── docs/
│   ├── brainstorms/            ← Briefs de cadrage (/brainstorm)
│   └── plans/                  ← Plans de phase (/plan)
├── memory/                     ← Mémoire persistante (maintenu par /close)
│   ├── decisions.md            ← ADR + décisions arch
│   ├── learnings/
│   └── topics/
├── tmp/                        ← Screenshots Playwright, dumps debug (gitignored sauf .gitkeep)
├── PRD.md                      ← Source de vérité produit
├── CLAUDE.md                   ← Instructions agent (gitignored, généré depuis template)
├── STRUCTURE.md                ← Ce fichier
├── DESIGN.md                   ← Système de design (produit par /design)
├── STATUS.md                   ← État courant (maintenu par /close)
├── docker-compose.yml          ← Orchestration multi-service
├── Dockerfile.backend
├── Dockerfile.frontend
├── package.json                ← Next.js (racine)
├── requirements_backend.txt
├── .env                        ← Secrets réels (gitignored)
├── .env.example                ← Placeholders (commité)
├── .mcp.json                   ← Config MCP réelle (gitignored)
└── .mcp.json.example           ← Config MCP placeholders (commité)
```
<!-- /architect:directories -->

## Patterns clés

<!-- architect:patterns -->
- **Voice streaming** : OpenAI Realtime API via WebSocket browser → FastAPI backend → OpenAI SDK. Jamais de buffer complet — streaming token par token.
- **Frontière SDK / n8n** : réponses live à l'écran = OpenAI SDK direct ; tâches async (email, calendar, météo) = webhook n8n + callback.
- **Named Memory Scopes** : toute mémoire passe par `memory_service.py` — préfixes Redis `jarvis:memory:{scope}:{key}`. Jamais Redis direct depuis les routes.
- **Barge-in** : activé nativement via OpenAI Realtime API `turn_detection: server_vad`. VAD client-side coté browser pour filtrer silences avant envoi.
- **Fallback pyramid** : Realtime API → Whisper API → mode texte uniquement. Chaque niveau doit être testé.
<!-- /architect:patterns -->

## Tests

<!-- architect:tests -->
- Framework : Playwright (E2E) dans `tests/e2e/`
- Lancement : `npx playwright test` (depuis la racine)
- Convention : un fichier par use case majeur (`morning-briefing.spec.ts`, etc.)
- Chaque spec teste : connexion WebSocket, envoi commande, vérification réponse UI, vérification état mémoire
- `/validate` lance Playwright automatiquement et screenshot les résultats dans `tmp/`
<!-- /architect:tests -->

## Conventions d'arborescence

<!-- architect:conventions -->
- Fichiers TS/TSX : kebab-case (`voice-orb.tsx`, `quick-actions.tsx`)
- Composants React : export default PascalCase
- Fichiers Python : snake_case (`memory_service.py`, `ai_service.py`)
- Services backend : 1 fichier = 1 responsabilité (pas de services "god object")
- Tests Playwright : nommés `{feature}.spec.ts`, co-localisés dans `tests/e2e/`
<!-- /architect:conventions -->

## Intégrations externes

<!-- structure:integrations -->
- **OpenAI** : Realtime API (voice WebSocket), gpt-4o (LLM), TTS (fallback voix)
- **n8n self-hosted** : workflows async (Morning Briefing, Smart Agent email draft) via webhook
- **Redis** : Named Scopes mémoire (`jarvis:memory:*`), session state
- **PostgreSQL** : historique conversations, logs sessions
- **Hostinger VPS** : déploiement Docker Compose production
- **Playwright MCP** : validation E2E automatisée depuis Claude
- **Plugin frontend-design** : génération composants React depuis DESIGN.md
<!-- /structure:integrations -->

## Fichiers clés

<!-- structure:key-files -->
- `PRD.md` — source de vérité produit, lire avant toute décision
- `backend/main.py` — entrée FastAPI + WebSocket handler central
- `backend/services/memory_service.py` — Named Scopes Redis (CRITIQUE : toute mémoire passe ici)
- `src/lib/realtime.ts` — client OpenAI Realtime API (latence < 1s)
- `src/lib/vad.ts` — Voice Activity Detection client-side
- `docker-compose.yml` — orchestration complète (backend + frontend + postgres + redis)
- `DESIGN.md` — tokens design system (créé par /design, lu par frontend-design plugin)
- `tests/e2e/` — Playwright specs par use case
<!-- /structure:key-files -->

## Évolutions livrées (résumé)

<!-- structure:evolutions-summary -->
_(Vide à l'init. Maintenu par /evoluer après chaque livraison.)_
<!-- /structure:evolutions-summary -->

# CLAUDE.md — Jarvis V2

> **Ouverture de session** : tape `/prime` si tu reprends un projet en cours. Tape `/start` uniquement sur un projet neuf.
> **Rituel par phase** : `/prime` → `/plan` → `/execute` → `/validate` → `/close` → `/clear`.
> **Suivi** : `STATUS.md` résume où tu en es. Maintenu par `/close`.

## Glossaire

- **Phase** — palier macro du PRD (ex : "Phase 1 — Foundation"). Contient plusieurs tâches. Marquée `✅ Terminée` par `/close`.
- **Tâche** — étape concrète dans `docs/plans/phase-N-plan.md`. Cochée `[x]` par `/execute`.
- **Critère "Fait quand"** — définition de done d'une tâche. Sans ça, on ne sait pas quand s'arrêter.

---

# Jarvis V2

## Identité

<!-- start:identité -->
Jarvis est un assistant IA vocal personnel (usage solo) qui répond en moins d'une seconde,
exécute des tâches autonomes via des agents LangChain et des workflows n8n, et mémorise le contexte
utilisateur dans des namespaces Redis structurés. Double objectif : outil de productivité quotidien
ET démo gagnante pour un hackathon (contrainte : service Hostinger actif).

project_type: webapp
project_uses_n8n: true
<!-- /start:identité -->

## Stack

<!-- architect:stack -->
- **Frontend** : Next.js 14 (App Router) + Tailwind v3 + Framer Motion + shadcn/ui
- **Backend** : Python FastAPI (uvicorn) — services existants reorganisés dans `backend/`
- **Voice** : OpenAI Realtime API (WebSocket streaming, barge-in natif, live transcript) + VAD client-side
- **LLM** : gpt-4o via OpenAI SDK (streaming)
- **Agents** : LangChain (tools : calculator, web_search, device_control, session_summary)
- **Memory** : Redis (Named Scopes : projects / preferences / tasks) + PostgreSQL (historique conversations)
- **Automation** : n8n self-hosted (Morning Briefing = appels parallèles async via webhook)
- **Deploy** : Docker Compose multi-service + Hostinger VPS
- **Tests** : Playwright E2E (WebSocket, 3 démos, fallback)
- **Design** : DESIGN.md (produit par /design avant Phase 1) + plugin frontend-design
<!-- /architect:stack -->

## Outils MCP actifs

- **n8n MCP** (`n8n-mcp`) : créer/modifier/tester les workflows n8n depuis Claude. Détail install : `.claude/rules/n8n-setup.md`.
- **Playwright MCP** : validation E2E automatisée — lancé par `/validate` sur chaque phase. Détail : `.claude/rules/playwright.md`.
- **Plugin frontend-design** : lit `DESIGN.md` pour générer des composants React cohérents avec le système de design.

## Conventions

- Fichiers TypeScript/TSX : kebab-case (`voice-orb.tsx`, pas `VoiceOrb.tsx`)
- Composants React : PascalCase pour le nom du composant dans le fichier
- Fichiers Python : snake_case (`memory_service.py`)
- Commits : conventionnels (`feat:`, `fix:`, `chore:`, `test:`)
- `use client` uniquement quand nécessaire (état local ou event handlers)
- Jamais de `eval()` en Python — utiliser `ast.literal_eval` ou `numexpr`

## Instructions

- **Voice first** : toute modification de la voix passe par `backend/services/voice_service.py` — ne pas dupliquer la logique OpenAI dans les routes
- **Fallback systématique** : chaque feature voice a une alternative texte fonctionnelle
- **Secrets** : jamais de clé API dans le code — toujours depuis `os.getenv()` ou `settings`
- **Latence** : pas de traitement synchrone bloquant dans le handler WebSocket principal — tout passe par `asyncio`
- **Named Scopes** : toute lecture/écriture mémoire passe par `backend/services/memory_service.py`, jamais Redis direct depuis les routes
- **n8n** : éditer uniquement les workflows `[DEV]`, valider, tester, puis swap vers `[PROD]` manuellement

## Design system

<!-- design:summary -->
Dark mode immersif. Canvas deep navy `#0B1020`, accent indigo `#4F46E5`, cyan
électrique `#00D4FF` réservé aux états vocaux. Inter (UI) + JetBrains Mono
(transcripts). Orb central à 3 états (idle/listening/speaking) animé via Framer
Motion. Toutes les animations passent par Framer Motion — jamais de CSS @keyframes.
Voir `DESIGN.md` pour les tokens complets.
<!-- /design:summary -->

## Production

<!-- ship:url -->
{Rempli par /livrer après premier déploiement Hostinger VPS réussi.}
<!-- /ship:url -->

## Contexte métier

- **3 démos hackathon** (dans l'ordre de présentation) :
  1. Morning Briefing : `"Start my day"` → résumé calendrier + emails + météo en < 1s
  2. Smart Agent : `"Analyze my notes"` → plan d'action + email draft auto
  3. Memory : `"Remember X"` → contexte persistant rappelé dans les sessions suivantes
- **Named Scopes Redis** : `memory:projects`, `memory:preferences`, `memory:tasks` — namespaces séparés
- **Session Summary** : déclenché par `"Jarvis, close session"` ou automatiquement à la fermeture — export `.md` dans `/sessions/`
- **Fallback** : si OpenAI API down → mode texte + réponses simulées réalistes (pas d'erreur brute à l'écran)

## Mémoire persistante

Maintenue par `/close`. Fichiers dans `memory/` :
- `memory/decisions.md` — ADR + décisions d'architecture
- `memory/learnings/` — gotchas et patterns découverts
- `memory/topics/` — contexte par domaine
- `MEMORY.md` (racine) — index rapide

**Ne jamais éditer ces fichiers manuellement** — laisser `/close` le faire.

## Sécurité credentials

- `.env` gitignored — vraies valeurs locales
- `.env.example` commité — placeholders uniquement
- `.mcp.json` gitignored — valeurs réelles n8n + Playwright
- `.mcp.json.example` commité — placeholders `REPLACE_ME`
- Vérifier `git check-ignore .env` avant tout commit

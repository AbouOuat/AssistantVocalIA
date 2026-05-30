# Décisions d'architecture — Jarvis V2

> **ADR numérotés** (écrits par `/architect` + `/evoluer`) en tête.
> **Harvest libre** (écrit par `/close`) en bas.
> Ne jamais éditer manuellement — laisser les skills le faire.

## ADR — Architecture Decision Records

<!-- ADR-NNN entries appended here by /architect (Étape 6.6) and /evoluer (Étape 5f) -->

### ADR-001 — Stack V2 : Next.js + FastAPI + OpenAI Realtime API + Redis Named Scopes

**Status** : Accepted
**Date** : 2026-05-28
**Context** : Jarvis V1 scaffoldé (FastAPI + React/Vite, services non connectés). Hackathon en 4 jours avec contrainte Hostinger. Double objectif : démo gagnante (latence < 1s) ET outil quotidien. Source : `docs/brainstorms/2026-05-28-jarvis-v2-hackathon.md`.
**Decision** :
- Frontend migré vers Next.js 14 (App Router) + Tailwind + Framer Motion — meilleure architecture commerciale, déploiement Docker propre, Server Components.
- Voice : OpenAI Realtime API au lieu de Whisper — latence 4-6s → < 1s, barge-in natif, live transcript natif.
- Memory : Redis Named Scopes (`jarvis:memory:projects/preferences/tasks`) au lieu de key-value plat — structuration inspirée de Fury SDK (huwprosser).
- Backend FastAPI gardé et connecté (services bien écrits, pas de réécriture).
- n8n self-hosted pour les tâches async (Morning Briefing = 3 API calls parallèles).
- Playwright E2E pour valider les 3 démos avant présentation.
**Consequences** :
- ✅ Latence < 1s atteignable sans réécriture majeure du backend
- ✅ Architecture commercialisable post-hackathon (Next.js + Docker = deployable partout)
- ✅ Mémoire structurée par namespaces = démo Memory plus impressionnante
- ⚠️ OpenAI Realtime API en beta — vérifier accès avant Day 1, fallback Whisper prêt
- ⚠️ RAM VPS ≥ 2GB requise pour Docker multi-service (postgres + redis + backend + frontend)
- ⚠️ OAuth Google non configuré — Morning Briefing utilisera des données simulées pour la démo

---

## Décisions (harvest libre)

<!-- close:decisions -->
_(Vide au démarrage. Alimenté par /close à chaque fin de phase.)_
<!-- /close:decisions -->

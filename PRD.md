<!--
PRD vivant — cap 100 lignes hard.
Mis à jour par /evoluer. JAMAIS réécrit destructivement.
-->

# PRD — Jarvis V2

_Request Classification : STANDARD_

## 1. Vision

Jarvis est un assistant IA vocal personnel qui répond en moins d'une seconde,
exécute des tâches autonomes, et mémorise le contexte utilisateur par namespaces.
Sert à la fois d'outil quotidien de productivité (usage solo) et de démo gagnante
pour un hackathon (contrainte : au moins un service Hostinger actif).

## 2. Personas

- **Abou (utilisateur solo)** — entrepreneur multi-projets, 5 apps/jour.
  Douleur : friction de changement de contexte + assistants vocaux trop lents (4-6s).
- **Juge hackathon** — évalue en 5 min, sensible à la fluidité et au wow visuel.
  Douleur : démos génériques, latentes, ou qui plantent en live.

## 3. Scope actuel (V2)

### Core
- [ ] Voice realtime < 1s (OpenAI Realtime API + barge-in + live transcript)
- [ ] VAD client-side (filtre silences avant envoi audio)
- [ ] Demo 1 — Morning Briefing : calendrier + emails + météo en parallèle (n8n)
- [ ] Demo 2 — Smart Agent : analyse notes → plan d'action + email draft
- [ ] Demo 3 — Memory Named Scopes : projects / preferences / tasks (Redis)
- [ ] Quick Actions bar (5 raccourcis preset)
- [ ] Session Summary auto (export markdown /sessions/)
- [ ] UI premium : orb animé + waveform + dark theme Framer Motion

### Technique
- [ ] Next.js 14 (App Router) + Tailwind + Framer Motion + shadcn/ui
- [ ] FastAPI backend (services existants reconnectés dans backend/)
- [ ] PostgreSQL + Redis Named Scopes
- [ ] Docker Compose (backend + frontend + postgres + redis)
- [ ] Déployé sur Hostinger VPS
- [ ] DESIGN.md (système de design — /design avant /plan Phase 1)
- [ ] Tests E2E Playwright (WebSocket + 3 démos + fallback)

## 4. Hors scope (différé)

- [ ] Wake word "Hey Jarvis" — risque fiabilité démo publique (bruit)
- [ ] Auth multi-utilisateur — V3 commerciale
- [ ] Offline / local LLM — latence inacceptable sans Apple Silicon
- [ ] ElevenLabs TTS — OpenAI TTS suffisant pour hackathon
- [ ] WebXR / AR interface — trop expérimental pour 4 jours

## 5. Constraints non-négociables

- Latence vocale perçue < 1s — OpenAI Realtime API obligatoire, Whisper classique banni
- Au moins un service Hostinger actif pendant la démo (règle hackathon)
- Aucune clé API en clair dans le repo (.env gitignored, .env.example commité)
- Fallback actif : mode texte + réponses simulées si API down
- `eval()` dans calculator banni → ast.literal_eval ou bibliothèque dédiée

## 6. Success Criteria

- Latence < 1s sur 10 cycles consécutifs mesurés avant présentation
- Les 3 démos s'enchaînent sans erreur sur run complet à froid
- App live sur Hostinger VPS (pas localhost) le jour de présentation
- Tous les tests Playwright passent sur la version déployée

## 7. Implementation Phases

- **V1 (scaffoldée 2026-05-19)** — FastAPI + React/Vite, 7 services Python, non connectés
- **V2 (en cours)** — Next.js + Realtime API + 3 démos + Redis Named Scopes + Hostinger
  - Phase 1 — Foundation (Jour 1) : scaffold Next.js + Realtime API WS + backend connecté
  - Phase 2 — Features (Jour 2) : 3 démos end-to-end + Named Scopes + VAD + n8n
  - Phase 3 — Ship (Jours 3-4) : deploy Hostinger + UI polish + Playwright + fallbacks
- **V3 (envisagé)** — SaaS multi-user, auth, wake word, modèle commercial

## 8. Risks & Mitigations

- **Realtime API beta** : accès non garanti → vérifier Jour 1, fallback Whisper prêt
- **RAM Hostinger VPS** : Docker multi-service ≥ 2 GB → profil Docker allégé, Redis minimal
- **n8n absent en prod** : Morning Briefing dépend de n8n → endpoints FastAPI directs en fallback
- **OAuth Google** : calendrier/emails non configurés → données simulées réalistes pour démo

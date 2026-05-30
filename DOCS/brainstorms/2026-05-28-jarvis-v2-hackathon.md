# Brainstorm : Jarvis V2 — Assistant IA vocal personnel

## Idée en 1 phrase

Un assistant IA vocal en temps réel (< 1 sec de latence) qui gère ta journée, exécute des tâches autonomes, et se souvient de ton contexte — utilisable au quotidien ET prêt pour gagner un hackathon en 4 jours.

## Besoin clarifié

- **Pour qui** : usage personnel (1 utilisateur), avec potentiel commercial post-hackathon (SaaS, self-hosted, API)
- **Pour quoi** : remplacer les 5 apps du quotidien (email, calendrier, notes, Slack, todo) par une interface conversationnelle vocale — gain de temps réel + démo convaincante
- **Contexte** : projet existant V1 scaffoldé (services Python existent mais non connectés), refonte V2 avec Next.js + OpenAI Realtime API sur 4 jours, hackathon contrainte = au moins un service Hostinger

## Contraintes connues

- **Deadline** : 4 jours (Day 1 = foundation, Day 2 = features, Day 3 = deploy + polish, Day 4 = présentation)
- **Hosting obligatoire** : au moins un service Hostinger (VPS Docker probable)
- **Clé différenciante** : latence < 1 sec (OpenAI Realtime API vs Whisper classique ~4-6s)
- **Stack V1 existante** : Python FastAPI backend (à garder et connecter), fichiers backend_*.py et frontend_*.tsx à réorganiser
- **Budget** : OpenAI API (GPT-4 + Realtime + TTS), n8n local existant, Hostinger VPS

## Alternatives explorées

- **Garder Whisper STT** : écarté — latence 4-6s tue l'effet "vivant", incompatible avec l'objectif hackathon
- **Rester sur React/Vite** : écarté — Next.js 14 donne SSR, API routes intégrées, déploiement Docker simplifié, meilleure architecture commerciale
- **15 features génériques vs 3 démos polished** : 3 démos retenues — les juges ont 5 min, un flow mémorable > une liste

## Les 3 use cases retenus (hackathon + quotidien)

### Demo 1 — Morning Briefing (30 sec)
- Input : `"Start my day"` (voix)
- Jarvis fait en parallèle : fetch agenda + emails prioritaires + météo
- Output (voix + dashboard) : `"3 réunions, 2 emails urgents, 14°C pluie. Prêt ?"`
- Valeur quotidienne : préparer la journée en 30 sec au lieu de 10 min

### Demo 2 — Smart Agent (60 sec)
- Input : `"Analyze my notes and create action plan"`
- Jarvis : lit fichiers → résume → crée plan prioritisé → draft email prêt
- Output : `"5 tâches identifiées. Email prêt à envoyer."` + UI avec tâches + preview email
- Valeur quotidienne : productivité intelligente, zéro saisie manuelle

### Demo 3 — Memory Persistence (60 sec)
- Input : `"Remember: mon projet principal est Jarvis"`
- Plus tard : `"Quelle est ma priorité ?"` → `"Jarvis — assistant IA vocal"`
- Valeur quotidienne : assistant vraiment personnel, pas juste un chatbot stateless

## Inspirations (Huw Prosser — github.com/huwprosser)

- **`fury-sdk`** : Named memory scopes (namespaces Redis structurés), HistoryManager auto-compaction, parallel tool execution, **interruption/barge-in mid-génération** → patterns à reprendre directement
- **`web-whisper`** : VAD (Voice Activity Detection) côté client — filtre les silences *avant* envoi au backend, réduit la latence perçue et les coûts API
- **`jarvis-mlx`** : architecture offline propre (Whisper + LLM + TTS découplés) → inspiration pour la séparation des services, pas la stack (on reste cloud)
- **Ce que Huw n'a pas** et qu'on aura : cloud + realtime streaming + agents n8n + mémoire multi-scope + UI premium + déployé en prod

## Ajouts au périmètre (post-brainstorm Huw Prosser)

### MUST HAVE (gratuits via Realtime API)
- **Barge-in / interruption** : l'utilisateur interrompt Jarvis mi-réponse — transforme "chatbot" en "conversation vivante"
- **Live transcript** : sous-titres qui s'affichent en temps réel pendant que Jarvis parle

### SHOULD HAVE (~4h cumulées)
- **VAD client-side** : filtre silences/bruits avant envoi audio (~1h)
- **Named Memory Scopes** : Redis structuré par namespace (`projects/`, `preferences/`, `tasks/`) au lieu d'un key-value plat (~2h)
- **Quick Actions bar** : 5 boutons preset (☀️ Start day / 📋 Tasks / 📧 Emails / 🧠 What do you know? / 📝 Note) — fallback si micro indisponible (~1h)
- **Session Summary auto** : GPT-4 résume décisions + tâches + mémos à la fermeture, export markdown dans `/sessions/` (~1h)

## Direction recommandée

- **Stack V2** : Next.js 14 (App Router) + Tailwind + Framer Motion | FastAPI (refactoré, services connectés) | OpenAI Realtime API | PostgreSQL + Redis | Docker + Hostinger VPS
- **Approche** : garder le backend Python existant (services bien écrits), connecter dans `backend_main.py`, migrer le frontend vers Next.js
- **n8n** : utiliser n8n local existant pour orchestrer les automations (Morning Briefing = 3 appels parallèles, Smart Agent = pipeline analyse)
- **Méthode** : appliquer le kit IAPreneurs — PRD.md → /plan phases → /execute → /validate → /close → /livrer

## Hypothèses encore à valider

- [ ] OpenAI Realtime API disponible sur le compte OpenAI actuel (beta access ?)
- [ ] Instance n8n locale accessible pendant le hackathon + sur Hostinger VPS
- [ ] Hostinger VPS a assez de RAM pour Docker (backend + frontend + postgres + redis + n8n) — min 2GB recommandé
- [ ] Les APIs Google (Calendar, Gmail) pour Morning Briefing : OAuth déjà configuré ?
- [ ] ElevenLabs TTS vs OpenAI TTS : qualité voix suffisante avec OpenAI pour le hackathon ?

## Risques et mitigations

| Risque | Mitigation |
|--------|-----------|
| Latence Realtime API > 1s en conditions réelles | Fallback text input + réponses pré-enregistrées backup |
| API down pendant la démo | Mode offline avec réponses simulées réalistes |
| Scope trop large en 4 jours | Day 1 : Foundation + 1 demo working. Day 2-3 : les 2 autres |
| eval() dans calculator tool | Remplacer par numexpr ou calcul sécurisé |

## Prochaine étape suggérée

`/architect docs/brainstorms/2026-05-28-jarvis-v2-hackathon.md`

Produira le PRD.md avec : Vision, Personas, Phases V1/V2, Stack officielle, Success Criteria, Risks.

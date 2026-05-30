# Plan — Phase 1 : Foundation

> PRD parent : `PRD.md`
> Date : 2026-05-28

## Tâches

- [x] **1. Réorganiser backend** — Créer `backend/services/`, déplacer les 6
  fichiers `backend_*.py`, corriger les imports, vérifier que main.py démarre.
  Fait quand : `cd backend && python -c "from services.ai_service import
  chat_completion; print('OK')"` ne lève pas d'erreur + `uvicorn main:app
  --port 8000` démarre sans exception.

- [x] **2. Créer `backend/services/memory_service.py`** — Redis Named Scopes
  avec préfixe `jarvis:memory:`, méthodes `get(scope, key)`,
  `set(scope, key, value)`, `get_all(scope)`, `delete(scope, key)`.
  Fait quand : test manuel `python -c "from services.memory_service import
  MemoryService; ms=MemoryService(); ms.set('projects','jarvis','test');
  print(ms.get('projects','jarvis'))"` affiche `"test"`.

- [x] **3. Connecter les services dans `backend/main.py`** — Remplacer l'echo
  WebSocket par le vrai pipeline : message reçu → `ai_service.chat_completion()`
  → réponse streamée. Brancher `memory_service` sur les types `memory_set` /
  `memory_get`. Intégrer `ConversationContext` pour l'historique.
  Fait quand : client WebSocket test (wscat ou browser console) envoie
  `{"type":"chat","content":"Bonjour"}` et reçoit une vraie réponse GPT-4o
  (pas un echo) en moins de 5 secondes.

- [ ] **4. Implémenter architecture voix + tester accès Realtime API** —
  Dans `backend/services/voice_service.py` : (a) tester `openai.realtime`
  sur le compte ; si OK → pipeline Realtime WebSocket ; sinon → pipeline
  Whisper STT + GPT-4o + TTS comme fallback. Les deux chemins exposent la
  même interface WebSocket côté client.
  Fait quand : envoyer un fichier `test.wav` (5 secondes de parole) via
  WebSocket → recevoir une réponse textuelle + audio MP3, quel que soit le
  chemin (Realtime ou Whisper). Logguer le chemin utilisé (`[REALTIME]` ou
  `[WHISPER_FALLBACK]`).

- [x] **5. Scaffold Next.js 14 + config Tailwind DESIGN.md** —
  `npx create-next-app@latest . --typescript --tailwind --app --src-dir
  --import-alias "@/*"`, installer `framer-motion`, initialiser shadcn/ui.
  Configurer `tailwind.config.ts` avec les tokens DESIGN.md (canvas `#0B1020`,
  primary `#4F46E5`, voice-active `#00D4FF`, surfaces, etc.).
  Fait quand : `npm run dev` démarre sans erreur ET un div `bg-canvas
  text-ink` affiche bien le fond `#0B1020` dans le navigateur.

- [x] **6. Créer composant `VoiceOrb`** —
  `src/components/VoiceOrb.tsx`, prop `state: 'idle'|'listening'|'speaking'`,
  animations Framer Motion pour les 3 états (breath 3s / pulse 1.5s /
  speaking-wave 0.8s), glow cyan en listening/speaking via `boxShadow`.
  Fait quand : page de démo isolée (`/orb-demo`) alterne les 3 états toutes
  les 2s, animations fluides, couleurs conformes DESIGN.md, pas d'animation
  CSS `@keyframes` dans le code.

- [x] **7. Créer layout principal + connexion WebSocket** —
  `src/app/page.tsx` : VoiceOrb centré, zone chat scrollable (bulles user +
  assistant), Quick Actions bar (5 boutons placeholder), input texte fallback.
  `src/lib/websocket.ts` : connexion `ws://localhost:8000/ws`, reconnexion
  auto, dispatch des messages vers l'état React.
  Fait quand : badge "● Connected" s'affiche quand le backend tourne, saisir
  un texte + Entrée → bulle user apparaît + bulle assistant avec réponse
  GPT-4o, les tokens DESIGN.md sont utilisés (pas de couleurs en dur).

- [ ] **8. Test E2E vocal bout en bout + fallback texte** —
  Cliquer l'orb → micro s'active → parler → transcript apparaît sous l'orb →
  Jarvis répond (voix + texte dans le chat). Valider aussi le fallback texte
  seul (micro refusé ou indisponible).
  Fait quand : 3 cycles voix→réponse consécutifs sans erreur console, ET
  le mode texte seul fonctionne si micro refusé par le navigateur.

## Critère de phase complète

- [ ] Toutes les tâches 1 à 8 cochées
- [ ] Envoyer "Bonjour Jarvis" (voix ou texte) → réponse GPT-4o dans le chat
- [ ] Le chemin vocal est loggué (`[REALTIME]` ou `[WHISPER_FALLBACK]`)
- [ ] Aucune clé API dans le code commité (`git grep -r "sk-"` retourne vide)

## Prochaine étape

`/execute docs/plans/phase-1-plan.md`

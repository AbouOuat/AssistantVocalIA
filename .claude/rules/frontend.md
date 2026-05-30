---
paths: ["src/**/*.{ts,tsx}"]
---

# Frontend — règles React / Next.js Jarvis

## Composants

- shadcn/ui pour tous les éléments génériques (Button, Card, Input, Dialog) — jamais de `<button>` brut
- Framer Motion pour toutes les animations (orb, waveform, transitions) — pas de CSS keyframes manuels
- `use client` uniquement si état local ou event listener — préférer Server Components par défaut

## Voice UI

- L'état de l'orb a 3 valeurs : `idle | listening | speaking` — passer via prop, pas de state global
- Le live transcript est dans `<LiveTranscript>` — jamais inliné dans `<Chat>`
- La connexion WebSocket s'initialise dans `src/lib/realtime.ts`, pas dans un composant

## Accessibilité

- Chaque bouton Quick Actions a un `aria-label` clair
- Le Chat scroll automatiquement vers le dernier message (`scrollIntoView`)
- Les états de chargement ont un `aria-busy="true"`

## Design system

- Lire `DESIGN.md` avant de créer un composant (tokens couleur, typographie, espacements)
- Le plugin `frontend-design` lit `DESIGN.md` automatiquement pour générer des composants cohérents
- Palette principale : fond `#0B1020`, accent `#4F46E5`, voice-active `#00D4FF`

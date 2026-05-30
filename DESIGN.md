---
version: alpha
name: Jarvis V2
description: |
  Interface voice-first IA immersive, ancrée sur un canvas deep navy (#0B1020)
  avec accents indigo et un signal cyan électrique pour les états vocaux actifs.
  Le "voltage" vient du contraste entre l'obscurité du fond et l'éclat cyan de la
  voix — l'orb qui respire transforme une réponse < 1 seconde en expérience vivante.
  Ton premium et technique, tempéré par des formes arrondies et une typographie
  lisible. Cible : utilisateur solo impressionné à chaque interaction + juge
  hackathon qui voit la différence en 5 secondes.

colors:
  primary: "#4F46E5"           # Indigo — CTAs, focus rings, bulles utilisateur
  primary-active: "#4338CA"    # Indigo foncé — :active / pressed
  primary-disabled: "#1E1B4B"  # Indigo très sombre — disabled state

  voice-active: "#00D4FF"      # Cyan électrique — orb écoute/parole (signal réservé)
  voice-glow: "#0EA5E9"        # Cyan chaud — halo glow autour de l'orb
  voice-muted: "#1E3A4A"       # Surface tintée zone d'écoute inactive

  ink: "#F9FAFB"               # Titres, texte maximum contraste sur dark
  body: "#D1D5DB"              # Texte courant
  body-strong: "#E5E7EB"       # Texte courant emphasé
  muted: "#9CA3AF"             # Hints, labels secondaires
  muted-soft: "#6B7280"        # Texte tertiaire / disabled

  hairline: "#1F2937"          # Borders très subtiles
  hairline-soft: "#374151"     # Borders visibles pour séparations

  canvas: "#0B1020"            # Background page — deep dark navy
  surface-soft: "#0F172A"      # Sections secondaires
  surface-card: "#111827"      # Cards / panels / bulles assistant
  surface-elevated: "#1A2235"  # Modals, popovers, dropdowns
  surface-input: "#1F2937"     # Fond inputs / textareas

  on-primary: "#FFFFFF"
  on-voice: "#0B1020"          # Texte sur cyan (rare)
  on-surface: "#F9FAFB"

  success: "#34D399"           # Emerald — lisible sur fond sombre
  warning: "#FBBF24"
  error: "#F87171"             # Red-400 — doux sur dark

typography:
  display-xl:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 64px
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: -1.5px
  display-lg:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 48px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -1px
  display-md:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 36px
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: -0.5px
  display-sm:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 28px
    fontWeight: 600
    lineHeight: 1.2
  title-lg:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 22px
    fontWeight: 500
    lineHeight: 1.3
  title-md:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 18px
    fontWeight: 500
    lineHeight: 1.4
  title-sm:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 500
    lineHeight: 1.4
  body-md:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.55
  body-sm:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.55
  caption:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.4
  caption-uppercase:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 1.5px
  code:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.6
  transcript:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: 0.2px
  button:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1

rounded:
  xs: 4px
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px
  2xl: 24px
  pill: 999px

spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.lg}"
    padding: "10px 20px"

  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    typography: "{typography.button}"
    rounded: "{rounded.lg}"
    padding: "10px 20px"
    border: "1px solid {colors.hairline}"

  voice-orb-idle:
    size: "120px"
    backgroundColor: "{colors.surface-card}"
    border: "2px solid {colors.hairline-soft}"
    rounded: "{rounded.pill}"
    animation: "breath 3s ease-in-out infinite"

  voice-orb-listening:
    size: "120px"
    backgroundColor: "{colors.voice-muted}"
    border: "2px solid {colors.voice-active}"
    glow: "0 0 24px {colors.voice-glow}"
    rounded: "{rounded.pill}"
    animation: "pulse 1.5s ease-in-out infinite"

  voice-orb-speaking:
    size: "120px"
    backgroundColor: "{colors.primary}"
    border: "2px solid {colors.voice-active}"
    glow: "0 0 32px {colors.voice-active}"
    rounded: "{rounded.pill}"
    animation: "speaking-wave 0.8s ease-in-out infinite"

  waveform-bar:
    backgroundColor: "{colors.voice-active}"
    width: "3px"
    rounded: "{rounded.pill}"
    opacity-idle: "0.3"
    opacity-active: "1.0"

  quick-action-button:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.muted}"
    typography: "{typography.caption}"
    rounded: "{rounded.pill}"
    padding: "8px 16px"
    border: "1px solid {colors.hairline}"

  chat-bubble-user:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body-md}"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
    maxWidth: "75%"
    align: "flex-end"

  chat-bubble-assistant:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.body}"
    typography: "{typography.body-md}"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
    maxWidth: "85%"
    border: "1px solid {colors.hairline}"
    align: "flex-start"

  toast-success:
    backgroundColor: "{colors.surface-elevated}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
    border: "1px solid {colors.success}"

  toast-error:
    backgroundColor: "{colors.surface-elevated}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
    border: "1px solid {colors.error}"
---

## Overview

Jarvis V2 est une interface voice-first IA à usage quotidien et hackathon.
Le design vit entièrement en dark mode — le canvas deep navy (#0B1020) crée
une atmosphère immersive proche d'un poste de commande futuriste. L'orb central
est le cœur émotionnel : il respire au repos, pulse en cyan à l'écoute, s'électrise
quand Jarvis parle. Le voltage vient du contraste entre l'obscurité dense et les
éclairs de couleur vocale — l'utilisateur ressent la réponse avant même de
l'entendre. Les formes arrondies et les bulles de chat tempèrent l'effet sci-fi
pour rester chaleureux à l'usage quotidien.

## Colors

- **Primary `{colors.primary}` (Indigo)** : actions intentionnelles — CTAs, focus
  rings, bulles utilisateur. Couleur de "décision".
- **Voice Active `{colors.voice-active}` (Cyan)** : signal réservé exclusivement
  aux états vocaux (orb, waveform, live transcript). Ne jamais utiliser en décoration
  — ce signal doit rester pur pour que l'utilisateur identifie immédiatement l'état.
- **Canvas / Surfaces** : 3 niveaux — `canvas` (#0B1020) page, `surface-card`
  (#111827) panels/cards, `surface-elevated` (#1A2235) modals. Contraste subtil
  mais perceptible.
- **Ink / Body / Muted** : 3 niveaux de blanc sur fond sombre. `ink` pour les
  titres, `body` pour le texte courant, `muted` pour les hints.
- **Semantic** : emerald, amber, red-400 — calibrés pour rester lisibles sur dark
  sans agresser.

## Typography

Inter pour toute l'interface — moderne, lisible à petite taille sur fond sombre.
JetBrains Mono pour les transcripts et données : la largeur fixe rend les
sous-titres "techniques" et les ancre dans l'imaginaire IA.

- `display-lg/md` : titre de session ("Bonjour Abou"), résumé Morning Briefing.
  Rarement utilisé — l'interface est minimaliste.
- `body-md` : bulles de chat, réponses principales.
- `transcript` : sous-titres live pendant que Jarvis parle. Monospace + line-height
  aéré pour que les mots apparaissent progressivement sans jerks visuels.
- `caption-uppercase` : labels des Quick Actions, métadonnées de session.

## Layout

- **Container** : `max-w-2xl` (672px) centré — interface étroite, focus sur la
  conversation, pas un dashboard plein écran.
- **Zone orb** : section centrale fixe ~200px. Orb centré, waveform 16 barres
  en dessous.
- **Zone chat** : scrollable, `calc(100vh - 340px)`, `gap-3` entre bulles.
- **Quick Actions** : barre fixe en bas, 5 boutons pill sur 1 ligne.
- **Input texte fallback** : ancré tout en bas, semi-transparent si voice active.

## Elevation & Depth

Sur fond sombre, l'élévation se fait par contraste de surface, pas par shadow.

- **Niveau 0** (canvas) : page principale
- **Niveau 1** (surface-card) : bulles assistant, cards briefing
- **Niveau 2** (surface-elevated) : modals, tooltips
- **Glow vocal** : `box-shadow: 0 0 Npx {colors.voice-glow}` sur l'orb uniquement.
  Transition `300ms ease-out` entre les états. Le glow est une élévation lumineuse,
  pas une ombre.

## Shapes

- `{rounded.lg}` (12px) : bulles chat, cards, inputs — standard de l'interface.
- `{rounded.pill}` : orb (cercle parfait), quick actions, badges de statut.
- `{rounded.xl}` (16px) : modals, panels Session Summary.
- Jamais d'angles droits — l'arrondi renforce l'aspect organique de l'IA.
- Règle de nesting : si une card a `{rounded.xl}`, ses éléments internes ont
  `{rounded.lg}` (un cran en dessous).

## Components

- **Voice Orb** : composant central à 3 états animés via Framer Motion `animate` +
  `transition`. Clic = toggle listening. Ne jamais implémenter les animations en
  CSS `@keyframes` — Framer Motion permet l'interruption propre entre états.
- **Waveform** : 16 barres `waveform-bar` pilotées par Web Audio API (amplitude
  réelle) ou simulées en fallback. Visible uniquement en état `speaking`.
- **Quick Actions** : hover → border vire à `{colors.primary}`, texte s'éclaircit
  vers `{colors.body}`. Press → `scale(0.95)` via Framer Motion.
- **Chat Bubbles** : user droite (indigo), assistant gauche (surface-card).
  Live transcript en `{typography.transcript}` sous la bulle courante, curseur
  clignotant tant que Jarvis n'a pas fini de parler.
- **Toasts** : position `bottom-center` (évite de masquer l'orb). Border colorée
  selon sévérité. Auto-dismiss 3s. Max 2 toasts visibles simultanément.

## Do's and Don'ts

### Do
- Utiliser `{colors.voice-active}` (cyan) UNIQUEMENT pour les états vocaux.
- Animer tous les états d'orb via Framer Motion — jamais de CSS `@keyframes` brut.
- Garder le layout centré et étroit — ce n'est pas un dashboard.
- `{typography.transcript}` (monospace) pour tous les sous-titres et transcriptions.
- Contraste de surface plutôt que shadow sur fond sombre.

### Don't
- Pas de fond clair, même partiel — le dark mode est non-négociable.
- Pas de `{colors.voice-active}` sur les CTAs standards.
- Pas plus de 2 accents simultanés à l'écran (indigo + cyan max).
- Pas d'autres polices qu'Inter + JetBrains Mono.
- Pas d'animations CSS manuelles — Framer Motion uniquement.

## Responsive Behavior

- **Desktop ≥ 1024px** : orb 120px, chat `calc(100vh - 340px)`, quick actions 1 ligne.
- **Tablet 768–1024px** : layout identique, padding réduit.
- **Mobile < 768px** : orb 96px, quick actions scroll horizontal, input texte
  toujours visible. L'orb reste sticky — repère visuel prioritaire.

## Known Gaps

- Tokens d'animation Framer Motion (duration, spring stiffness) non dans le YAML —
  à définir lors de l'implémentation Phase 1.
- Dashboard Morning Briefing (cards calendrier/météo/emails) : composants à ajouter
  en Phase 2.
- Mode clair : hors scope V2, différé en V3.

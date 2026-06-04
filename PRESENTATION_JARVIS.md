# JARVIS — Présentation Hackathon IAPreneur 2026
> Contenu slide par slide · inspiré du format Morphozia · à intégrer dans Canva / Figma / Google Slides

---

## SLIDE 01 / 07 — COVER

**Surtitre :** ABU OUATTARA · HACKATHON IAPRENEUR 2026

**Titre principal :**
# JARVIS

**Sous-titre :**
L'assistant IA vocal personnel.
Il comprend ce que tu dis, agit sur tes outils, et se souvient de toi.

**Tags (4 boutons) :**
`PROBLÈME` · `ARCHITECTURE` · `STACK TECHNIQUE` · `MVP CONSTRUIT`

**Bloc droite (stats) :**
- 🤖 icône robot
- **VOCAL** · **CONNECTÉ** · **MÉMORISANT**
- **12** TOOLS FUNCTION CALLING
- **11** WORKFLOWS N8N ACTIFS

---

## SLIDE 02 / 07 — LE PROBLÈME

**Surtitre :** LE PROBLÈME

**Titre :**
## Le professionnel solo perd **des heures chaque jour**
## sur des tâches que l'IA devrait gérer à sa place

**4 cartes :**

📧 **EMAILS SANS FIN**
Gmail + Outlook. Trier, répondre, relancer — sans jamais finir. Aucun assistant ne touche vraiment à ta boîte mail.

📅 **AGENDA FRAGMENTÉ**
Les RDV sont dans le calendrier, les rappels dans la tête. Aucun outil ne fait le lien entre les deux en temps réel.

🧠 **AUCUNE MÉMOIRE**
L'IA repart de zéro à chaque conversation. Impossible de vraiment déléguer si elle ne se souvient de rien.

🔧 **10 OUTILS, AUCUN LANGAGE COMMUN**
Un pour les mails, un pour l'agenda, un pour les tâches. Aucun ne répond à la voix. Aucun n'agit vraiment.

**Ligne de clôture :**
**JARVIS répond à tout ça** en une seule phrase, à la voix.

---

## SLIDE 03 / 07 — ARCHITECTURE

**Surtitre :** COMMENT ÇA MARCHE

**Titre :**
## Une phrase. Douze actions possibles.
## L'architecture qui rend ça possible.

**Schéma (de gauche à droite) :**

```
[ VOIX / TEXTE ]
       ↓
[ Whisper STT ]  ←— transcription audio → texte
       ↓
[ FastAPI · WebSocket ]
       ↓
[ GPT-4o · Function Calling ]  ←— décide quel tool appeler
       ↓
┌──────────────────────────────────────────┐
│              12 TOOLS                    │
│  morning_briefing · classifier_emails    │
│  creer_rappel · creer_evenement_agenda   │
│  sauvegarder_memoire · analyser_notes    │
│  rechercher_emails · creer_brouillon     │
│  envoyer_outlook · lire_emails ...       │
└──────────────────────────────────────────┘
       ↓                    ↓
[ N8N · 11 workflows ]   [ Redis · 4 scopes ]
       ↓                    ↓
Gmail · Outlook · Google Calendar · TTS
```

**Note bas de slide :**
Chaque phrase naturelle → GPT-4o choisit le bon tool → n8n exécute → Redis mémorise → TTS répond à voix haute.

---

## SLIDE 04 / 07 — STACK TECHNIQUE

**Surtitre :** STACK TECHNIQUE

**Titre :**
## Des fondations **prêtes pour la production**,
## construites en **4 jours**

**Grille 3×3 :**

| Catégorie | Techno | Catégorie | Techno |
|---|---|---|---|
| **BACKEND** | FastAPI · Python 3.11 | **LLM** | OpenAI GPT-4o · Function Calling |
| **FRONTEND** | Next.js 14 · Tailwind · Framer Motion | **VOIX** | Whisper STT · OpenAI TTS |
| **MÉMOIRE** | Redis (4 scopes) · PostgreSQL | **AUTOMATISATION** | N8N · 11 workflows |
| **AUTH** | JWT · Demo user | **INFRA** | Docker Compose · Nginx · Coolify |
| **DÉPLOIEMENT** | VPS Hostinger KVM2 · HTTPS | **DESIGN** | shadcn/ui · Dark Navy · Indigo |

**Ligne du bas :**
Function calling GPT-4o : le cerveau qui décide · N8N : les mains qui exécutent · Redis : la mémoire qui retient

---

## SLIDE 05 / 07 — MVP CONSTRUIT

**Surtitre :** CE QU'ON A RÉUSSI À CONSTRUIRE

**Titre :**
## MVP **fonctionnel**, déployé en prod,
## construit solo en **4 jours de hackathon**

**Checklist 2 colonnes :**

✓ Interface vocale temps réel (orb animé 3 états)
✓ Transcription Whisper + réponse vocale TTS
✓ 12 tools OpenAI Function Calling opérationnels
✓ Morning Briefing : météo + emails + agenda du jour
✓ Lecture Gmail ET Outlook avec classification IA

✓ Création d'events Google Calendar (bonne date, bon fuseau)
✓ Rappels persistants : Redis + notification email n8n
✓ Mémoire persistante : préférences, projets, tâches
✓ Smart Agent : analyse de notes → plan d'action PDF
✓ Déployé sur VPS, HTTPS, accessible sur jarvis.obyz.biz

**Stat centrale :**
> **5 scénarios démo validés bout en bout · 0 terminal visible · < 3s de latence**

---

## SLIDE 06 / 07 — LES 5 DÉMOS

**Surtitre :** LES 5 CAPACITÉS CLÉS

**Titre :**
## Ce que Jarvis fait, en langage naturel, **maintenant**

**5 lignes (format phrase → action → résultat) :**

→ **"Lance mon briefing du matin"**
Météo du jour + 5 prochains RDV + emails importants — en 2 secondes.

→ **"T'as des trucs urgents dans mes mails ?"**
Jarvis classe Gmail + Outlook, filtre les urgents, résume à voix haute.

→ **"Rappelle-moi d'appeler Jean dans 1 heure"**
Rappel créé en Redis + email de confirmation envoyé automatiquement.

→ **"Ajoute un RDV Démo Jarvis demain à 10h"**
Event créé dans Google Calendar avec le bon fuseau horaire. Visible immédiatement.

→ **"Souviens-toi que je préfère mes briefings à 8h"**
Mémorisé dans Redis. Rappelé dans toutes les conversations suivantes.

---

## SLIDE 07 / 07 — ET APRÈS

**Surtitre :** ET APRÈS

**Titre :**
## JARVIS n'est pas un chatbot de plus.
## C'est le **copilote vocal** du professionnel solo.

**Stats :**
- **12** TOOLS ACTIFS
- **11** WORKFLOWS N8N
- **4** JOURS DE BUILD
- **Solo** CONSTRUIT PAR

**Citation :**
> *"Construit avec des outils IA, en 4 jours, pour prouver qu'un professionnel solo peut créer un assistant vraiment opérationnel — sans équipe, sans lever de fonds."*

**Roadmap (prochaines priorités) :**
→ Multi-utilisateurs (chaque user a son Jarvis)
→ Mémoire RAG longue durée (pgvector)
→ Connecteurs Notion, Slack, WhatsApp
→ Interface mobile / PWA
→ Démo publique · Beta fermée

**Bloc contact / démo :**
🌐 jarvis.obyz.biz
📧 aboubakary_ouattara@hotmail.com
**HACKATHON IAPRENEUR · 2026**

---

## NOTES DE MISE EN PAGE

**Palette de couleurs (cohérente avec l'original) :**
- Fond : `#FFFFFF` (blanc) avec panneau droit `#EEF4FF` (bleu très clair)
- Titre principal : `#0D1B4B` (bleu marine foncé)
- Accent / highlight : `#0066FF` ou `#00B0FF` (bleu électrique)
- Labels de section : bleu électrique, lettres espacées (tracking 0.2em)
- Texte courant : `#334155`
- Barre de progression bas : dégradé bleu, avance de 1/7 par slide

**Typographie :**
- Titres : Inter Bold ou DM Sans Bold
- Labels : Inter Semibold, uppercase, letter-spacing
- Corps : Inter Regular

**Éléments récurrents :**
- Logo `JARVIS` en haut gauche (bleu, bold)
- Numéro de slide en haut droit : `0X / 07`
- Pied de page gauche : ton nom / entreprise
- Barre de progression colorée en bas à droite

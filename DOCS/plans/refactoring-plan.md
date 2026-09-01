# Plan Refactoring Jarvis — Intent Router + Backend propre

> Issu de l'audit du 2026-06-23. Objectif : base solide, pas de hardcoded, router LLM fiable.

---

## Statut (audit de reprise 2026-09-01)

| Phase | État | Preuve |
|---|---|---|
| **A** — config client centralisée + nettoyage | ✅ Fait | `backend/config.py:39-74` (bloc `CLIENT_*`), `.env.example:27-48`, `docker-compose.yml` (CLIENT_* → backend + n8n), commit `6c0d30d` ("suppression `_handle_n8n_command_legacy` (312 lignes)"), `main.py:324` webhook `google-calendar-create-event` |
| **B** — outils LLM (intent router = function calling OpenAI) | ✅ Fait | `ai_service.py` `JARVIS_TOOLS` : `analyser_emails_gmail/outlook`, `consulter_derniere_analyse`, `lire_inbox_outlook` (param `dossier`), `lire_agenda` (dates ISO libres, cf. commit `8245cc0`), `_build_system_prompt()` client-aware. 15 tools au total. |
| **C** — workflows n8n manquants | ✅ Fait côté repo | `workflows/outlook-read-inbox.json`, `workflows/google-calendar-read.json`, `workflows/gmail-email-classifier-v2.json`, `workflows/outlook-email-classifier-v2.json` (commit `6c0d30d`). Présence/activation dans l'instance n8n prod **non vérifiée**. |
| **D** — import prod + tests | 🟡 Partiel | Rapport `DOCS/reports/tests-jarvis-2026-06-27.md` (13 tests prod, 9 OK / 2 partiels / 2 KO). Actifs prod : `outlook-read-inbox`, `outlook-email-classifier-v2`, `google-calendar-read`/`-create-event`, `gmail-draft`, `reminders`, mémoire Redis. **KO/suspects** : `morning-briefing` (webhook injoignable — TEST-01), Gmail `email-classifier-v2` (inactif ? — TEST-05), `outlook-read-inbox` n'exploite pas le champ `folder` (TEST-03/04). Aucun E2E automatisé sur ces scénarios. |

**Reste à faire (Phase D)** : voir la section « Phase D » plus bas + le tableau d'actions correctives du rapport de tests. Ne pas toucher la prod avant une vérification REPO ↔ n8n PROD.

> Note : les évolutions post-plan `0df5182` (dossiers Outlook dynamiques) et `8245cc0` (agenda dates libres LLM) étendent B2/B3 au-delà de ce que décrit le plan d'origine ci-dessous.

---

## Objectifs

1. **Zéro valeur hardcodée** — toute adresse email, URL, TTL vient de config/env
2. **Intent router fiable** — le LLM appelle le bon outil selon l'intention réelle
3. **Séparation lire / analyser** — inbox temps réel ≠ analyse hebdomadaire
4. **Agenda lisible** — pas seulement créer, mais aussi lire les RDV
5. **Code mort éliminé** — `_handle_n8n_command_legacy` supprimé

---

## Principe directeur : profil client

Tout ce qui est spécifique à un utilisateur/client vit dans un seul bloc `.env`.
Déployer pour un nouveau client = remplir `.env.example`, zéro code à modifier.

## Phase A — Fondations : config centralisée + nettoyage (backend)

### A1 — Bloc "Profil client" dans `config.py` + `.env.example`

```
# ── Profil client ─────────────────────────────────────────
CLIENT_NAME=
CLIENT_TIMEZONE=Europe/Paris
CLIENT_LANGUAGE=fr

# Boîtes mail
CLIENT_OUTLOOK_MAILBOX=          # boîte Outlook analysée (ex: user@hotmail.com)
CLIENT_SUMMARY_RECIPIENT=        # reçoit la synthèse hebdo Outlook
CLIENT_CR_RECIPIENT=             # reçoit les comptes-rendus dictés
CLIENT_GMAIL=                    # boîte Gmail analysée

# Agenda
CLIENT_CALENDAR_ID=primary       # ID Google Calendar (ou 'primary')

# Classifier Outlook — configurables avec le client final
CLIENT_URGENCY_KEYWORDS=assignation,convocation,jugement,ordonnance,huissier,...
CLIENT_EXCLUDED_DOMAINS=substack.com,mailchimp.com,sendgrid.net,...

# Technique
ALLOWED_ORIGINS=https://jarvis.obyz.biz,...
EMAIL_ANALYSIS_CACHE_TTL=86400
EMAIL_INBOX_CACHE_TTL=120
```

Tous ces champs lus via `settings` dans le backend et via `process.env` dans les workflows n8n.

### A2 — Supprimer `_handle_n8n_command_legacy` (main.py:402-712)
- Vérifier qu'aucun chemin ne l'appelle (c'est marqué "Obsolète", jamais appelé)
- Supprimer les 300 lignes

### A3 — Corriger le nom webhook agenda
- `calendar-create-event` → `google-calendar-create-event` dans `_execute_tool`

---

## Phase B — Intent Router : redéfinir les outils (ai_service.py)

### B1 — Renommer + redécrire les outils existants
| Outil actuel | Nouveau nom | Description cible |
|---|---|---|
| `classifier_emails_gmail` | `analyser_emails_gmail` | Uniquement si l'utilisateur veut une analyse complète IA |
| `classifier_emails_outlook` | `analyser_emails_outlook` | Uniquement si l'utilisateur veut une analyse complète IA |
| `lire_emails_en_memoire` | `consulter_derniere_analyse` | Lire la dernière analyse stockée, avec timestamp affiché |

**Règle dans les descriptions** : "analyser" = appel IA lourd. "lire" = données fraîches ou cache court.

### B2 — Créer `lire_inbox_outlook` (nouveau tool)
- Appelle webhook `outlook-read-inbox` (à créer en Phase C)
- Cache TTL 120s max
- Description : "Lire les emails actuels de la boîte Outlook en temps réel. Utiliser pour : 'donne-moi mes mails', 'j'ai des messages ?', 'quoi de neuf ?'"

### B3 — Créer `lire_agenda` (nouveau tool)
- Appelle webhook `google-calendar-read` (à créer en Phase C)
- Description : "Lire les événements agenda du jour ou de la semaine. Utiliser pour : 'qu'est-ce que j'ai aujourd'hui ?', 'mes RDV de la semaine', 'mon agenda'"
- Paramètre : `periode` = "aujourd'hui" | "demain" | "semaine"

### B4 — Mise à jour du system prompt
- Préciser clairement : inbox temps réel vs analyse hebdo
- Mentionner `OUTLOOK_ANALYZED_MAILBOX` dans le contexte pour que le LLM cite la bonne adresse

---

## Phase C — Workflows n8n manquants

### C1 — `outlook-read-inbox`
- Webhook → Graph API `GET /me/mailFolders/Inbox/messages?$top=10&$orderby=receivedDateTime desc`
- Sélectionner : id, subject, from, receivedDateTime, bodyPreview, importance, categories
- Retourner liste brute (pas d'IA, pas de classification)
- Répondre au webhook avec `{ ok: true, emails: [...], fetched_at: ISO }`

### C2 — `google-calendar-read`
- Webhook (paramètre `periode`) → Google Calendar API
- `GET /calendars/primary/events?timeMin=...&timeMax=...&orderBy=startTime`
- Retourner : titre, début, fin, lieu, description pour chaque événement
- Gérer `période` = aujourd'hui / demain / semaine (calcul des bornes timeMin/timeMax)

---

## Phase D — Import n8n prod + tests

### D1 — Importer `outlook-email-classifier.json` en prod
- Désactiver → Import → Re-lier credentials → Réactiver
- Crédentials à re-lier : Connect_Outlook_ouat + Header Auth OpenAI

### D2 — Tester end-to-end
- "donne-moi mes mails" → `lire_inbox_outlook` → données fraîches
- "analyse mes emails Outlook" → `analyser_emails_outlook` → workflow IA complet
- "qu'est-ce que j'ai aujourd'hui ?" → `lire_agenda` → Google Calendar
- "start my day" → `morning_briefing` → workflow complet

---

## Ordre d'exécution recommandé

```
A1 (config) → A2 (nettoyage) → A3 (fix webhook) 
→ B1+B2+B3+B4 (tools) 
→ C1 (outlook-read-inbox) → C2 (google-calendar-read)
→ D1 (import prod) → D2 (tests)
```

**A et B en backend Python — C en n8n — D en prod**

# Audit READ-ONLY — REPO ↔ n8n PROD

**Date** : 2026-09-01
**Instance** : `https://n8n.obyz.biz` (API `/api/v1`)
**Méthode** : requêtes **GET uniquement** (`/workflows`, `/executions`, `/variables`). Aucun POST/PATCH/DELETE. Aucune modification, aucun import, aucune activation, aucun redéploiement.
**Credentials** : `N8N_API_KEY` lu depuis `.env`, jamais affiché.
**Limite** : les variables d'environnement du conteneur n8n ne sont pas exposées par l'API (`/api/v1/variables` → HTTP 403 « license does not allow feat:variables »). Les contrôles qui en dépendent sont marqués « à vérifier côté Coolify ».

---

## 0. Synthèse

- **22 workflows** dans l'instance : 16 actifs, 1 archivé, 5 inactifs (« V1 … copy »).
- **Tous les webhooks appelés par le backend existent et sont actifs en prod.** Aucun webhook manquant.
- **Anomalie majeure confirmée (contrôle #5)** : sur Gmail **et** Outlook, les classifiers **v1 et v2 sont actifs simultanément avec le même cron `0 8 * * 1` (lundi 8h)** → double exécution hebdomadaire, prouvée par l'historique d'exécutions des lundis 2026-08-24 et 2026-08-31.
- **Les classifiers v2 échouent systématiquement** (node LangChain `lmChatOpenAi` : `Could not get parameter`). Ce sont donc les **v1** qui portent réellement l'analyse hebdo aujourd'hui.
- **2 divergences repo ↔ prod** : `morning-briefing` (prod **en avance**, édits n8n non committés) et `outlook-read-inbox` (repo **en avance**, prod sans le binding `folderId` → bug spam/supprimés de TEST-03/04).
- **Non déterminé en read-only** : état runtime réel de `morning-briefing` (0 exécution récente enregistrée) — nécessite un re-test POST.

---

## 1. Inventaire prod (22 workflows)

### Actifs (16)

| Workflow | id | webhook path | schedule | credentials |
|---|---|---|---|---|
| gmail-draft | 0VjWYR6owf6QCCrz | `gmail-draft` | — | Gmail account |
| gmail-email-classifier **(v1)** | LHSqm0Ue2Vib8LjJ | `email-classifier` | **`0 8 * * 1`** | Gmail account, Header Auth account |
| gmail-email-classifier-v2 | C7DBtxGSKMfLHG5F | `email-classifier-v2` | **`0 8 * * 1`** | Gmail account, OpenAI account |
| gmail-search | XIqAaTATKELm6pad | `gmail-search` | — | Gmail account |
| google-calendar-create-event | uj378ec2n8JtRO8r | `google-calendar-create-event` | — | Google Calendar Jarvis |
| google-calendar-read | TadXnsRGQ8Oumltf | `google-calendar-read` | — | Google Calendar Jarvis |
| memory-scopes | kNgmGqtZg2GF8qR1 | `memory` | — | Redis account |
| morning-briefing | hLVNH9FVgByfWLLb | `morning-briefing` | — | Gmail account, Google Calendar Jarvis |
| outlook-email-classifier **(v1)** | kb9TuIiGANBjbk3s | `outlook-email-classifier` | **`0 8 * * 1`** | Connect_Outlook_ouat, Header Auth account |
| outlook-email-classifier-v2 | MShBDLvSP9pjzHmr | `outlook-email-classifier-v2` | **`0 8 * * 1`** | Connect_Outlook_ouat, Connect_Outlook_ouat_native, OpenAI account |
| outlook-read-inbox | r5DLYTJIljZVZwtp | `outlook-read-inbox` | — | Connect_Outlook_ouat_native |
| outlook-search | L0ZihqcwQAao5Csq | `outlook-search` | — | Connect_Outlook_ouat |
| reminders | 1tnbGRizEeqwkUU2 | `reminders` | interval (minutes) | Gmail account |
| send-outlook-email | 7nvyEi0SWcW0o8gg | `send-outlook-email` | — | Connect_Outlook_ouat |
| smart-agent | REbOZTo1NBX0RfgI | `smart-agent` | — | Gmail account, Header Auth account, OpenAI account |
| telegram-bot | ttFagGUvW9zXwiku | (trigger Telegram) | — | Jarvis Telegram Bot |

### Archivé (1)

| Workflow | id | note |
|---|---|---|
| outlook-read-inbox (2ᵉ copie) | OVlHhPYlskzhmJLW | archivé — doublon de r5DLYTJIljZVZwtp |

### Inactifs (5) — « landmines »

| Workflow | id | cron stocké |
|---|---|---|
| V1 gmail-email-classifier copy | jNB1wErpcBtjysJ1 | `0 8,12,18 * * 1-5` (3×/j semaine) |
| V1 morning-briefing copy | M6hAtyeCq5Y7axrn | — |
| V1 outlook-email-classifier copy | cZtVBfRStQyYg9Rg | `0 8,12,18 * * 1-5` |
| V1 send-outlook-email copy | UxkxjHaCqlMxSKA2 | — |
| V1 send-outlook-email copy | i3jOCdpX5FfzvX8p | — |

> Inactifs = ne se déclenchent pas. Mais un `active:true` accidentel réintroduirait un cron 3×/jour.

---

## 2. Webhooks attendus par le code ↔ présents en prod

| webhook (appelé dans `backend/main.py`) | fichier repo | prod : présent | prod : actif |
|---|---|---|---|
| `email-classifier` / `email-classifier-v2` | gmail-email-classifier(.v2).json | ✅ / ✅ | ✅ / ✅ |
| `outlook-email-classifier` / `outlook-email-classifier-v2` | outlook-email-classifier(.v2).json | ✅ / ✅ | ✅ / ✅ |
| `outlook-read-inbox` | outlook-read-inbox.json | ✅ | ✅ |
| `google-calendar-read` | google-calendar-read.json | ✅ | ✅ |
| `google-calendar-create-event` | google-calendar-create-event.json | ✅ | ✅ |
| `morning-briefing` | morning-briefing.json | ✅ | ✅ |
| `reminders` | reminders.json | ✅ | ✅ |
| `gmail-search` | gmail-search.json | ✅ | ✅ |
| `outlook-search` | outlook-search.json | ✅ | ✅ |
| `smart-agent` | smart-agent.json | ✅ | ✅ |
| `gmail-draft` | gmail-draft.json | ✅ | ✅ |
| `send-outlook-email` | send-outlook-email.json | ✅ | ✅ |

**Extras** :
- Repo sans équivalent prod : `workflows/MVP - Outlook IA emails avocat.json` (orphelin historique).
- Prod sans équivalent repo : 1 `outlook-read-inbox` archivé + 5 « V1 … copy » inactifs.
- `memory-scopes` (path `memory`) : actif en prod, **jamais appelé par le backend** (mémoire = Redis direct).
- `telegram-bot` : actif en prod, **aucun tool Telegram dans le backend** (cf. TEST-12).

---

## 3. Les 5 contrôles ciblés

### #1 — `morning-briefing` : repo ↔ prod → **DIVERGENT (prod en avance)**

| Node | Repo (`workflows/morning-briefing.json` + `morning-briefing-import.json`) | Prod (hLVNH9FVgByfWLLb) |
|---|---|---|
| `Agenda du jour` [googleCalendar] | `calendarId: "primary"` (en dur) | `calendar: {{ $env.CLIENT_CALENDAR_ID }}` (mode id) **+** `calendarId: {{ $json.body.calendar_id }}` |
| `Répondre` [respondToWebhook] | `JSON.stringify({ briefing, weather, email_count, event_count })` | **identique** |
| `Météo du jour` | `appid: {{ $env.OPENWEATHER_API_KEY }}` | **identique** |

- La prod consomme `$json.body.calendar_id` (que le backend envoie depuis `main.py`) + fallback `$env.CLIENT_CALENDAR_ID`. **Cette version n'a jamais été exportée vers le repo.**
- `morning-briefing-import.json` (non committé) est **en retard** sur la prod, pas en avance — il ne sert plus à rien.
- ⚠️ **Ré-importer le fichier repo régresserait la prod.** Il faut d'abord exporter prod → repo.
- **Exécutions** : 0 enregistrée (n8n ne sauvegarde pas les exécutions de ce workflow), 0 erreur récente. **État runtime indéterminé** — TEST-01 était KO le 2026-06-27 ; les édits n8n peuvent être postérieurs. **Re-test POST requis.**

### #2 — `outlook-read-inbox` : prise en compte du champ `folder` → **BUG PROD confirmé (repo en avance)**

| Node `Outlook — Lire inbox` [microsoftOutlook] | Repo | Prod (r5DLYTJIljZVZwtp) |
|---|---|---|
| params | `resource:message, operation:getAll, filters:{ folderId: {{ $('Config').first().json.folder }} (mode id) }, limit:...` | `operation:getAll, limit:..., options:{}` — **aucun `filters`, aucun `folderId`** |

- Le node `Config` (code) calcule bien `folder` (validé contre `['inbox','junkemail','deleteditems','sentItems','drafts','archive']`), mais **en prod ce `folder` n'est jamais transmis au node Outlook** → toujours l'Inbox.
- **Explique exactement TEST-03/04** (spam / supprimés renvoient les emails de l'inbox).
- Le repo `workflows/outlook-read-inbox.json` **contient déjà le correctif** (`filters.folderId`).
- **Fix** : ré-importer le fichier repo en prod, re-lier `Connect_Outlook_ouat_native`, tester `junkemail` / `deleteditems`.

### #3 — `gmail-email-classifier-v2` : actif ? → **OUI, actif** (mais cassé, voir #5)

- `active: true`, webhook `email-classifier-v2`, structure complète (Config → Gmail read `is:unread newer_than:8h` → Préparer → IF → chainLlm + lmChatOpenAi → Parser → envoi synthèse → respond) + `scheduleTrigger` `0 8 * * 1` + `manualTrigger`.
- **TEST-05 (27/06) reclassé** : la réponse « pas d'emails non lus » en 4.1 s correspond au fast-path légitime `Répondre - Aucun email` (aucun non-lu dans la fenêtre 8h), **pas** à un workflow absent. L'alerte TEST-05 tombe.
- Mais : voir #5 — le node LLM échoue dès qu'il y a des emails à classer.

### #4 — env conteneur n8n (`WORKFLOW_VERSION`, `OPENWEATHER_API_KEY`, `CLIENT_*`) → **NON VÉRIFIABLE via API**

- `/api/v1/variables` → HTTP 403 (feature sous licence). Aucun endpoint public n8n n'expose `process.env` du conteneur.
- **À vérifier côté Coolify** (dashboard ou `docker exec ... env`) :
  - `OPENWEATHER_API_KEY` — utilisé par `morning-briefing / Météo du jour`
  - `CLIENT_CALENDAR_ID` — utilisé par `morning-briefing / Agenda du jour` (version prod)
  - `CLIENT_SUMMARY_RECIPIENT` / `SUMMARY_RECIPIENT_EMAIL` / `CLIENT_GMAIL` — nodes `Configuration` des classifiers (fallback en dur `ouat.abou34@…` si absents)
  - `WORKFLOW_VERSION` **du conteneur backend** — détermine si `analyser_emails_*` route vers v1 (marche) ou v2 (cassé). `docker-compose.yml` défaut `v1`, `backend/config.py` défaut `v2`, `.env` local `v1`.
- `docker-compose.yml` a `N8N_BLOCK_ENV_ACCESS_IN_NODE: "false"` → `process.env` fonctionne dans les Code nodes (au moins ça, c'est bon).

### #5 — duplication cron v1/v2 (Gmail **et** Outlook) → **ANOMALIE CONFIRMÉE (preuve : exécutions)**

| Workflow | id | active | cron `scheduleTrigger` | exéc. 2026-08-31 06:00Z (=08:00 Paris) | exéc. 2026-08-24 06:00Z |
|---|---|---|---|---|---|
| gmail-email-classifier **(v1)** | LHSqm0Ue2Vib8LjJ | ✅ | `0 8 * * 1` | **success** | success |
| gmail-email-classifier-v2 | C7DBtxGSKMfLHG5F | ✅ | `0 8 * * 1` | **error** (`finished:false`) | error |
| outlook-email-classifier **(v1)** | kb9TuIiGANBjbk3s | ✅ | `0 8 * * 1` | **success** | success |
| outlook-email-classifier-v2 | MShBDLvSP9pjzHmr | ✅ | `0 8 * * 1` | **error** (`finished:false`) | error |

- **Chaque lundi 08:00 Europe/Paris, 4 exécutions cron partent** : v1 + v2 pour Gmail, v1 + v2 pour Outlook. Confirmé sur 2 lundis consécutifs (`mode=trigger`).
- **v1 réussit → c'est v1 qui réalise réellement l'analyse hebdo** : envoi de la synthèse, application des catégories Graph (Outlook), création de brouillons.
- **v2 échoue systématiquement** (cause en §4 ci-dessous) → l'analyse hebdo v2 est morte, et génère 2 exécutions en erreur/semaine.
- **Effet de bord si v2 est réparé sans désactiver v1** : chaque lundi → 2 analyses, 2 emails de synthèse (`ouat.abou34@gmail.com` / `ouat.abou34@outlook.fr`), 2 passes de catégorisation Outlook, 2 lots de brouillons, coût OpenAI ×2.
- Origine : commits `41e3ee4` / `3f7dbc7` ont corrigé la planification **sur v2** (« lundi 8h uniquement ») mais **n'ont jamais désactivé les v1**.

#### Cause racine de l'échec v2 (exécution `26161`, `gmail-email-classifier-v2`, 2026-08-31)

```
NodeOperationError: "Error in sub-node OpenAI Chat Model"
description: "Could not get parameter"
node: "OpenAI Chat Model"  type: @n8n/n8n-nodes-langchain.lmChatOpenAi  typeVersion: 1.2
Noeuds exécutés avant crash :
  Planification 8h → Configuration → Gmail - Lire emails → Préparer emails
  → Emails présents ? → Construire prompt LLM → OpenAI Chat Model ✗
```

- Même node, même erreur pour Outlook v2 (`MShBDLvSP9pjzHmr`).
- Diagnostic : **incompatibilité de version du package `@n8n/n8n-nodes-langchain`**. `docker-compose.yml` utilise `image: n8nio/n8n:latest` (non pinné) → une mise à jour auto de l'image a cassé le contrat du node `lmChatOpenAi`.
- v2 **fonctionnait via webhook** le 2026-06-27 (TEST-06, 32.5 s) → régression entre fin juin et le 2026-08-24.
- **Conséquence** : le chemin v2 est cassé **quel que soit le déclencheur** (cron *et* webhook). Si le backend prod tourne en `WORKFLOW_VERSION=v2`, alors « analyse mes emails Gmail/Outlook » **échoue actuellement en prod**.

---

## 4. Divergences repo ↔ prod — récapitulatif

| Élément | Repo | Prod | En avance | Action |
|---|---|---|---|---|
| `morning-briefing` (node Agenda) | `calendarId:"primary"` | `$env.CLIENT_CALENDAR_ID` + `$json.body.calendar_id` | **PROD** (édits n8n non committés) | Exporter prod → `workflows/morning-briefing.json` **avant** tout ré-import ; jeter `morning-briefing-import.json` |
| `outlook-read-inbox` (node Outlook) | `filters.folderId` bindé | `options:{}` sans folderId | **REPO** | Ré-importer repo → prod |
| classifiers v2 (Gmail + Outlook) | fichiers de `6c0d30d` | node `lmChatOpenAi` cassé | — | Réparer le node (pinner l'image n8n) **ou** assumer le repli v1 |
| classifiers v1 (Gmail + Outlook) | présents | **actifs + cron lundi 8h** | = | Désactiver le cron (ou le workflow) une fois la cible v1/v2 tranchée |
| `MVP - Outlook IA emails avocat.json` | présent (orphelin) | absent | repo | Archiver le fichier repo |
| copies « V1 … » + `outlook-read-inbox` archivé | absents | 5 inactifs + 1 archivé | prod | Nettoyer dans n8n |
| image n8n | `n8nio/n8n:latest` | (latest, non pinné) | — | Pinner une version fixe |

---

## 5. Ce qui fonctionne en prod (confirmé cette session)

- `reminders` : cron ~5 min — 30/30 exécutions `success` sur ~2h30.
- classifiers **v1** Gmail + Outlook : cron lundi `success` (24/08 et 31/08).
- Webhooks on-demand actifs et OK au 2026-06-27 (rapport tests) : `outlook-read-inbox` (hors bug folder), `google-calendar-read`, `google-calendar-create-event`, `gmail-draft`, `reminders`, mémoire Redis. Non re-testés ici (nécessiteraient un POST).

## 6. Non déterminé en read-only (nécessite un POST — hors périmètre)

- `morning-briefing` : structurellement corrigé en prod, **0 exécution récente enregistrée**, KO au 27/06 → **re-test POST requis**.
- Chemin v2 **on-demand** (webhook) : présumé cassé (même node `lmChatOpenAi`) mais non prouvé sans POST.
- Bug folder `outlook-read-inbox` : diagnostic statique certain (aucun `folderId` dans le node) ; confirmation dynamique = un POST `folder=junkemail`.

---

## 7. Actions recommandées — séquence fusionnée (Phase D + embellissement CV)

> Contexte : une session parallèle (2026-09-03, cf. `DOCS/plans/cv-embellissement-scope.md`) a défini
> T1 (sortie structurée + éval classifieur), T2 (RAG), T3 (alertes échec n8n), T5 (CI). Plusieurs items
> de cette Phase D sont en réalité **prérequis** de T1 et T3, pas des finitions. D'où la séquence
> ci-dessous, qui remplace le backlog « Bonus » de `cv-embellissement-scope.md`.

### Étape 0 — Assainir la base n8n (prérequis de T1 et T3)

1. **Pinner l'image n8n** : `n8nio/n8n:latest` → version fixe dans `docker-compose.yml`. Cause racine
   des cassures LangChain (`aa088eb` smart-agent en juin, classifiers v2 en août). Sans pin, T1 recassera.
2. **Tuer la duplication cron** : pour chaque paire (Gmail, Outlook), **un seul `scheduleTrigger` actif**.
   Invariant : les 2 webhooks restent actifs (le toggle IHM continue de marcher à la demande), mais un
   seul cron par paire. En intérim : cron **v1 actif**, cron **v2 désactivé** (v1 fonctionne aujourd'hui).
3. **Aligner `WORKFLOW_VERSION`** sur les 3 couches (`backend/config.py` = `v2`, `docker-compose.yml` = `v1`,
   `.env` = `v1` → choisir une valeur unique, la mettre partout + Coolify). Retirer `WORKFLOW_VERSION` du
   service **`n8n`** dans `docker-compose.yml` (aucun workflow ne le lit — config morte).
4. **Purger le hardcodé** `ouat.abou34@outlook.fr` (`backend/main.py:749`, dictée avocat) → `CLIENT_CR_RECIPIENT`.

### Étape 1 — Réparer le chemin v2 (décision Path A / Path B — voir `cv-embellissement-scope.md` T1)

- **Path A** : garder `chainLlm` + `lmChatOpenAi`, pinner n8n sur une version où le node fonctionne,
  ajouter un Structured Output Parser. La puce CV « migration vers LangChain » reste vraie.
- **Path B** *(recommandé)* : remplacer `chainLlm`/`lmChatOpenAi` par un `httpRequest` direct vers
  `api.openai.com` avec `response_format: json_schema` (comme `aa088eb` pour smart-agent). Robuste,
  indépendant des upgrades n8n. La puce CV devient « sortie LLM structurée validée par schéma
  (JSON Schema) » — reformulation à répercuter dans le bloc CV.

### Étape 2 — T1 : sortie structurée + éval v1 vs v2

- Une fois le chemin v2 réparé : appliquer le schéma aux 2 classifiers, garder un fallback si le parse échoue.
- **Éval** 30–50 e-mails annotés → precision/recall/F1 par catégorie (`urgence`, `action`), v1 vs v2.
- **L'éval tranche l'architecture cible V1/V2** : si v2 ne bat pas v2, la cible reste v1 et on garde la
  planif sur v1 ; sinon on bascule `WORKFLOW_VERSION=v2` + cron sur v2, v1 reste joignable via le toggle
  (fallback). `DOCS/reports/classifier-eval-2026-09-XX.md` commité.

### Étape 3 — Réconcilier les 2 divergences repo ↔ prod

- **`morning-briefing`** : exporter la version **prod** (JSON) vers `workflows/morning-briefing.json`
  (prod est en avance — édits n8n non committés), supprimer `workflows/morning-briefing-import.json`
  (en retard), committer. Puis re-test POST (`Start my day`).
- **`outlook-read-inbox`** : ré-importer le fichier **repo** (il a le binding `filters.folderId`, la prod
  ne l'a pas), re-lier `Connect_Outlook_ouat_native`, re-tester `junkemail` / `deleteditems`.

### Étape 4 — T3 : alertes échec workflow n8n

À faire **après** l'étape 0 : sinon la première alerte reçue est le bug v2 déjà connu du lundi, pas un
vrai nouveau problème. `error-handler.json` (Error Trigger → mail `CLIENT_CR_RECIPIENT`) affecté comme
Error Workflow sur tous les workflows `[PROD]`.

### Étape 5 — T5 (CI GitHub Actions) puis T2 (RAG)

- T5 : indépendant, insérable dès que possible. Inclure les 3 specs Playwright manquantes
  (`morning-briefing`, `smart-agent`, `memory-scopes`).
- T2 : le gros morceau, une fois la base saine.

### Étape 6 — Nettoyage & finitions

- Supprimer/archiver dans n8n : les 5 « V1 … copy » + la `outlook-read-inbox` archivée.
- Archiver `workflows/MVP - Outlook IA emails avocat.json` dans le repo.
- Vérifier côté Coolify : `OPENWEATHER_API_KEY`, `CLIENT_CALENDAR_ID`, `CLIENT_SUMMARY_RECIPIENT`.
- Décider pour `telegram-bot` (actif mais non câblé au backend) : désactiver ou implémenter le tool.
- Re-jouer la campagne des 13 tests (`DOCS/reports/tests-jarvis-2026-06-27.md`).

> Toutes ces actions modifient n8n / Coolify / prod → **hors du présent audit read-only**. À planifier explicitement.
> Backlog unique : `DOCS/plans/cv-embellissement-scope.md` (ce §7 en est la vue « prod/n8n »).

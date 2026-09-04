# Périmètre — Embellissement CV Jarvis

> Créé le 2026-09-03. Mis à jour le 2026-09-04 (audit V1/V2 + écarts CV↔code).
> Objectif : rendre vraies les clauses ajoutées au bloc Jarvis du CV
> (`CV_OUATTARA_Aboubakary_TechLead_Architecte_IA_AWS.docx`) avant envoi.
> Statut global : ⬜ non démarré. Fenêtre visée : vendredi 2026-09-04 → lundi 2026-09-08.

Bloc CV cible (rappel) :
- classification e-mails → **sortie structurée validée par schéma** + **éval precision/recall**
- **RAG** sur historique conversations + synthèses e-mails, avec éval retrieval
- supervision → **alertes e-mail sur échec workflow n8n**
- ligne Outils mentionne `pgvector` et `GitHub Actions` → doivent exister

---

## Ce qui est DÉJÀ vrai (à décrire dans le CV, pas à construire)

Vérifié dans le repo au 2026-09-04. Défendable en entretien tel quel :

- **Architecture multi-services conteneurisée** : FastAPI, Next.js 14, Redis, PostgreSQL, nginx, n8n —
  Docker Compose, déployée sur VPS Hostinger via Coolify (`jarvis.obyz.biz`).
- **Intégrations orchestrées par n8n** (16 workflows actifs) : Telegram, Gmail, Outlook
  (Microsoft Graph API + OAuth2), Google Calendar, OpenWeatherMap.
- **Assistant vocal streaming** : pipeline WebSocket STT (Whisper) → gpt-4o → TTS, **fallback texte**.
  ⚠️ NE PAS écrire « < 1 s Realtime » : le bridge OpenAI Realtime est codé mais désactivé
  (`REALTIME_ENABLED`), latences réelles mesurées 3–5 s.
- **Routage d'intentions par function calling OpenAI (15 outils)** : emails, agenda, mémoire,
  rappels, briefing, brouillons, recherche.
- **Classifieur e-mails Outlook** (atout principal) : **pré-filtrage par règles métier du domaine
  juridique** (mots-clés : assignation, convocation, audience, jugement, huissier…) **puis
  classification LLM à champs explicites** (urgence, action, échéance, interlocuteur), **catégorisation
  automatique via Graph API**, synthèse par e-mail, brouillons de réponse.
- **Classifieur e-mails Gmail** : exclusion newsletters + classification LLM + synthèse.
- **Mémoire Redis scopée par utilisateur** : clés hiérarchiques `jarvis:memory:{user_id}:{scope}:{key}`,
  TTL, scopes `projects / preferences / tasks / context`.
- **Dégradation gracieuse** : `continueOnFail` sur les workflows n8n + réponses simulées si l'API LLM
  est indisponible.
- **Amorce multi-tenant** : profil client `CLIENT_*` dans `backend/config.py` (à formuler prudemment
  tant que le hardcodé résiduel n'est pas purgé — cf. Étape 0 pt 4).

### À NE PAS mettre (faux ou trompeur au 2026-09-04)

| Clause | Réalité code |
|---|---|
| « Anthropic Claude API » comme composant produit | 0 occurrence dans `backend/` et `workflows/` — c'est un outil de dev |
| « agents LangChain (web_search, calculator, device_control, session_summary) » | `backend/services/agents_service.py` existe mais **aucun `import agents_service`** dans le backend — module non câblé au pipeline |
| « historique conversations PostgreSQL » | `models.py` ne définit que `User` + `Session` (auth). Aucune table conversation, `ConversationContext` est **en mémoire** |
| « migration vers LangChain pour fiabiliser le parsing » | le parsing v2 (`regex + JSON.parse`) est **plus** fragile que v1 (`JSON.parse` direct) ; et v2 est cassé en prod |
| « RAG en prod » | n'existe pas encore → T2 |
| « sortie structurée validée par schéma » | regex + `JSON.parse` aujourd'hui → T1 |
| « CI/CD GitHub Actions » | aucun `.github/workflows/` → T5 |
| « alertes e-mail sur échec workflow » | aucun Error Trigger → T3 |

### Note — motif réel du passage V1 → V2 (corrige la reconstruction ChatGPT du 2026-09-04)

La cascade **« règles métier / mots-clés PUIS LLM »** que tu as en mémoire **existe dans le
classifieur Outlook depuis v1** (lignée « MVP Outlook IA avocat », mai 2026) — nœud
`Pré-détection keywords` + liste `MOTS_URGENCE`, présent dans `outlook-email-classifier.json`
**et** `outlook-email-classifier-v2.json`. Ce n'est **pas** ce que v2 a apporté.

Ce que v2 a réellement changé :
- transport de l'appel LLM : `httpRequest` → nœuds `@n8n/n8n-nodes-langchain.chainLlm` + `lmChatOpenAi` ;
- lecture Outlook : `httpRequest` Graph API → nœud natif `microsoftOutlook` ;
- planification : Gmail 3×/j → 1×/semaine (lundi).

Gmail v1 et v2 n'ont **jamais** eu de pré-détection mots-clés (juste l'exclusion newsletters).

→ Conséquence CV : décrire la cascade métier+LLM comme **le fonctionnement du classifieur Outlook**,
pas comme « une amélioration v2 ». Et la « migration LangChain » n'est pas un argument (c'est la
partie fragile). Path B de T1 assume ça.

---

## Étape 0 — Prérequis (NON optionnel — bloque T1 et T3)

> Ajouté le 2026-09-03 après l'audit `DOCS/reports/repo-vs-n8n-prod-2026-09-01.md`.
> Ces points étaient rangés en « Bonus » ci-dessous ; ils sont en fait la fondation de T1 et T3.

**Constat audit** : les classifiers **v2 sont cassés en prod** — exécutions cron des lundis 2026-08-24
et 2026-08-31 en erreur sur le node `@n8n/n8n-nodes-langchain.lmChatOpenAi` (`Could not get parameter`).
En plus : **v1 ET v2 planifiés le même lundi 8h** (double analyse), et l'image `n8nio/n8n:latest`
non pinnée est la cause racine (déjà cassé smart-agent en juin, cf. `aa088eb`).

**À faire avant T1 :**
1. ✅ **Pinner** `n8nio/n8n` → `2.22.5` dans `docker-compose.yml` (version prod relevée via `/rest/settings`).
2. ✅ **Un seul `scheduleTrigger` actif par paire** — cron des 2 classifiers **v2 désactivé en prod**
   (n8n API PUT, `disabled:true` sur le node schedule ; workflows + webhooks restent actifs). Snapshots
   rollback : `workflows/_prod-snapshot-2026-09-04/`. Repo : `disabled:true` posé aussi dans les 2 JSON v2.
   Cron v1 inchangé (moteur d'analyse hebdo).
3. ✅ **Aligner `WORKFLOW_VERSION`** : `config.py` → `v1`, `.env.example` → `v1`, `docker-compose.yml`
   backend déjà `v1`, variable retirée du service `n8n`. ⬜ reste : env Coolify à mettre à `v1`.
4. ✅ **Purger le hardcodé** `ouat.abou34@*` : `backend/main.py` (→ `settings.CLIENT_CR_RECIPIENT`),
   `backend/services/ai_service.py` (→ `"non renseigné"`), `docker-compose.yml` (défauts n8n vidés),
   `workflows/*classifier*-v2.json` (fallbacks JS `|| 'ouat.abou34@…'` → `|| ''`). `grep` global vide.

**État au 2026-09-04** : Étape 0 + Étape 1/Path B closes (repo + prod).
- ✅ `WORKFLOW_VERSION=v1` : cohérent partout — `config.py`, `.env(.example)`, `docker-compose.yml` backend,
  **et prod backend (Coolify) confirmé v1 par l'utilisateur le 2026-09-04**.
- ⬜ Reste côté **Coolify** (toi) : `CLIENT_GMAIL`, `CLIENT_SUMMARY_RECIPIENT`, `CLIENT_CR_RECIPIENT`,
  `OPENWEATHER_API_KEY`, `CLIENT_CALENDAR_ID` sur le service `n8n` (constatés vides dans le conteneur)
  + redeploy n8n (qui appliquera aussi le pin `2.22.5`).

---

## T1 — Sortie structurée du classifieur e-mail + jeu d'évaluation  ⬜

**Pourquoi** : le workflow v2 parse encore la réponse LLM avec `raw.match(/\{[\s\S]*\}/)` + `JSON.parse`
(node "Parser analyse IA", `workflows/outlook-email-classifier-v2.json` ~L168, idem `gmail-email-classifier-v2.json`).
La clause CV « sortie structurée validée par schéma » et « fiabiliser le parsing » ne sont pas vraies.

**Prérequis** : étape 0 faite (le node v2 lève `Could not get parameter` aujourd'hui — on ne peut pas
brancher un parser sur un node qui ne s'exécute pas).

**✅ Décision : Path B (2026-09-04).** Réécriture faite côté repo dans `workflows/gmail-email-classifier-v2.json`
et `workflows/outlook-email-classifier-v2.json` : nodes `Classification LLM Chain` (`chainLlm`) +
`OpenAI Chat Model` (`lmChatOpenAi`) **supprimés** → 1 node `OpenAI - Classification (JSON Schema)`
(`httpRequest` POST `chat/completions`, auth header, `response_format:{type:"json_schema",strict:true}`).
`Construire prompt LLM` émet `systemPrompt`/`userPrompt`/`jsonSchema` séparés ; les parsers lisent
`$json.choices[0].message.content` avec `JSON.parse` direct (plus de regex). Schéma Gmail : 7 champs/e-mail ;
schéma Outlook : + `interlocuteur`, `brouillon_recommande`, `brouillon`.
✅ **Importé en prod** (2026-09-04, `PUT` chirurgical conservant les vraies creds — le node httpRequest
réutilise `Header Auth account` id `F99p27Ao9ucj5aeX`, celle des 2 v1, rien à re-lier).
✅ **Test live Gmail v2** (`{limit:1}`, exec `27355`) : success, 10/10 nodes OK, le node OpenAI renvoie du
JSON strict conforme au schéma, parsé sans regex. Plus de `Could not get parameter`.
Outlook v2 : importé + vérifié structurellement, test fonctionnel via l'app à faire.
Puce CV « migration vers LangChain » **retirée** → « sortie LLM structurée validée par JSON Schema ».
⚠️ Découvert : `CLIENT_GMAIL` / `CLIENT_SUMMARY_RECIPIENT` **vides dans le conteneur n8n prod** →
à renseigner dans l'env Coolify (checklist ci-dessous).

<details><summary>Décision archivée — Path A vs Path B</summary>

| | Path A | Path B *(recommandé)* |
|---|---|---|
| Quoi | Garder `chainLlm` + `lmChatOpenAi`, pinner n8n sur une version où le node marche, ajouter un Structured Output Parser | Remplacer `chainLlm`/`lmChatOpenAi` par `httpRequest` direct → `api.openai.com` avec `response_format: json_schema` (comme `aa088eb` pour smart-agent) |
| Puce CV | « migration vers LangChain » **reste vraie** | « migration vers LangChain » **devient fausse** → reformuler : « sortie LLM structurée validée par schéma (JSON Schema) » |
| Robustesse | dépend du pin n8n ; recasse possible aux upgrades | indépendant de n8n ; c'est déjà le mécanisme de v1 qui n'a jamais cassé |
| Effort | + trouver/valider un pin compatible | ~équivalent (le HTTP node existe déjà en v1, on ajoute juste le schéma) |

</details>

**À faire** *(Path B — partiellement fait, cf. encadré ✅ ci-dessus)*
1. Selon Path retenu : brancher un **Structured Output Parser** sur `chainLlm` (A) **ou** `httpRequest` +
   `response_format: {type: "json_schema", json_schema: {...}}` (B). Schéma par e-mail :
   `id, urgence(haute|moyenne|faible), interlocuteur(enum), action(repondre|lire|relancer|classer|aucune),
   echeance_detectee(bool), date_echeance(YYYY-MM-DD|null), resume, raison_urgence,
   brouillon_recommande(bool), brouillon` + `global_summary`.
2. Garder un **fallback** si le parse échoue (ne pas casser le workflow — aujourd'hui `continueOnFail`).
3. Appliquer aux **deux** classifiers v2 (Outlook + Gmail).
4. **Éval** : 30–50 e-mails annotés à la main (label `urgence` + `action`). Script qui rejoue le
   classifieur et calcule precision / recall / F1 par catégorie. Comparer v1 vs v2.
   → **cette éval tranche l'architecture cible V1/V2** (quel moteur garder, quelle planif).

**Fait quand**
- ✅ Parser structuré (`json_schema` strict) actif en prod sur les 2 classifiers v2 (Path B, 2026-09-04).
- ✅ Harness d'éval construit : `eval/classifier/` (`prompts.py` = les 2 variantes, `run_eval.py` =
  P/R/F1 par classe + matrice de confusion → `DOCS/reports/classifier-eval-<date>.md`, `--dry-run` OK).
- ⬜ **Toi** : remplir `eval/classifier/dataset.csv` avec 30–50 e-mails réels + annoter
  `label_urgence` / `label_action`, puis `python eval/classifier/run_eval.py eval/classifier/dataset.csv`
  et commiter le rapport. C'est le seul reste de T1.

**Effort** : ~0,5–1 j (dont l'annotation manuelle, côté toi)

---

## T2 — RAG sur historique conversations + synthèses e-mails  ⬜

**Pourquoi** : RAG / bases vectorielles ne sont aujourd'hui revendiqués qu'au niveau « formation ».
Un RAG réel en prod substantie la compétence.

**Corpus** (réel et disponible)
- exports `sessions/*.md` (Session Summary) — ⚠️ dossier vide aujourd'hui, il faut générer quelques sessions
- analyses e-mails archivées dans Redis (`emails_structured`, `summaryText`, avec timestamp)
- ~~historique conversations PostgreSQL~~ **n'existe pas** (voir écarts CV↔code ci-dessus) — soit on
  se limite aux 2 sources ci-dessus, soit on ajoute d'abord une table `messages` + persistance dans
  le handler WebSocket (~2 h) si on veut vraiment revendiquer « historique PostgreSQL »

**À faire**
1. **Store** : `pgvector` sur le Postgres existant (extension + table
   `documents(id, content, embedding vector, metadata jsonb, source, created_at)`).
   Alternative QDrant si on veut coller au vocabulaire CV — reco pgvector (zéro infra en plus).
2. **Embeddings** : OpenAI `text-embedding-3-small`.
3. **Ingestion** : script de chunk (~500–800 tokens, overlap ~100) + upsert.
   Déclencheurs : fin de session (après export `.md`) et après chaque analyse e-mail.
4. **Retrieval** : retriever LangChain (similarity, k≈5) exposé comme nouvel outil
   `rechercher_historique` dans `JARVIS_TOOLS` (`backend/services/ai_service.py`) + utilisé dans la démo "Memory".
5. **Éval** : 10–15 questions de référence + source(s) attendue(s) → mesurer **hit rate @k**
   (la source attendue est-elle dans le top-k retourné).

**Fait quand**
- Une question en langage naturel sur une session ou une analyse e-mail passée renvoie une réponse **sourcée**.
- `DOCS/reports/rag-eval-2026-09-XX.md` commité avec le hit rate @5.
- `pgvector` ajouté à `docker-compose.yml` + `requirements_backend.txt`.

**Effort** : ~1,5–2 j

---

## T3 — Alertes e-mail sur échec de workflow n8n  ✅

**Pourquoi** : clause CV « alertes automatiques par e-mail en cas d'échec d'un workflow ».
Avant : uniquement `continueOnFail` (dégradation), aucun Error Trigger.

**Fait (2026-09-04)**
- ✅ `workflows/error-handler.json` : `Error Trigger` → `Formater alerte` (Code) → `Gmail - Envoyer alerte`.
  Destinataire via env uniquement. Validé n8n MCP. Procédure : `DOCS/ops/n8n-error-handler.md`.
- ✅ **Prod** : importé + activé (`j8OJ3Tk1T5hb0fhw`), affecté comme Error Workflow aux **16 workflows
  actifs**. Test jetable (`throw`) → error-handler déclenché (`Error Trigger` + `Formater alerte`
  exécutés). Snapshots : `workflows/_prod-snapshot-2026-09-04/t3-error-workflow/`.
- ✅ **Fix `$env`** : n8n 2.22.5 vide `process.env` dans les Code nodes → helper `envv()` = `$env[k]`
  appliqué (repo + prod) à `error-handler` + les 4 `Configuration` des classifiers. Les vars Coolify
  sont bien injectées (vérifié : `$env.CLIENT_CR_RECIPIENT`, `CLIENT_GMAIL`, `OPENWEATHER_API_KEY`…).

**Fait quand** : ✅ Error Workflow sur les 16 actifs. ✅ **Re-test end-to-end : workflow jetable `throw`
→ e-mail d'alerte reçu** à `aboubakary_ouattara@hotmail.com`. T3 **terminée**.
Bonus effet de bord : classifier v2 `summary_sent_to` = `ouat.abou34@gmail.com` (n'était plus renseigné
depuis la purge hardcodée — corrigé).

**Reste (suite)** : throttling Redis (1 e-mail / workflow / 15 min).

**Effort** : ~0,5 j

---

## T5 — CI GitHub Actions  🟡 (repo fait, CI verte à confirmer)

**Pourquoi** : la ligne Outils du bloc Jarvis mentionne `GitHub Actions` ; aucun `.github/workflows/` n'existait.

**Fait (2026-09-04)** — `.github/workflows/ci.yml`, 4 jobs sur `push`/`pull_request` vers `main` :
- **checks** : `ruff check backend/` (config `pyproject.toml` — `select = ["F","E9"]`, à élargir) + `npm ci`
  + `next lint` (ESLint, `.eslintrc.json` ajouté) + `tsc --noEmit` + `next build`.
- **backend-tests** : services postgres + redis, `pip install -r requirements-dev.txt`, `pytest -q`
  (`backend/tests/test_smoke.py` : import app, config, Named Scopes, `FAKE_LLM`, `/health`, `/api/settings`).
- **e2e** : services postgres + redis, backend lancé avec `JARVIS_FAKE_LLM=true` (réponses simulées
  déterministes — nouveau flag `settings.FAKE_LLM`), Playwright boote `next dev` et joue
  `voice-connection.spec.ts` + `fallback.spec.ts`.
- **docker-build** : `docker build` des 3 images (backend / frontend / nginx), sans push.

Local : `ruff`/pyflakes propre (F401 + f-strings sans placeholder corrigés dans `main.py`/`auth_service.py`),
`next lint` + `tsc` + `next build` OK, `pytest` 5 passed / 2 skipped.

**Fait quand** : 1er run CI vert sur une PR (à pousser). Puis élargir `ruff` (`E,W,I,UP,B`) + ajouter
les 3 specs Playwright manquantes (`morning-briefing`, `smart-agent`, `memory-scopes`).

**Effort** : ~0,5 j

---

## ~~Bonus — alignement repo~~ → promu en **Étape 0** (voir en tête)  ⬜

Ces items ne sont plus « si temps » : ce sont les prérequis de T1 et T3.
- Pin image n8n + cron unique par paire → Étape 0.
- Hardcodé `ouat.abou34@outlook.fr` → `CLIENT_CR_RECIPIENT` → Étape 0 pt 4.
- Incohérence `WORKFLOW_VERSION` → Étape 0 pt 3.
- `outlook-read-inbox` honore le champ `folder` (repo a déjà le fix, prod non) → Étape 6 (ré-import).

**Fait quand** : `grep -r "ouat.abou34"` vide ; `WORKFLOW_VERSION` cohérent partout + Coolify ;
image n8n pinnée ; un seul cron actif par paire ; `folder` respecté en prod.

---

## Bloc CV Jarvis — version actuelle vs version à terme

### Version ACTUELLE (envoyable aujourd'hui, 100 % vrai)

> Jarvis — Assistant personnel vocal d'IA générative et d'automatisation (jarvis.obyz.biz)
>
> - Conception d'une architecture multi-services conteneurisée (FastAPI, Next.js 14, Redis, PostgreSQL, nginx) déployée sur VPS via Coolify ; intégrations orchestrées par des workflows n8n : Telegram, Gmail, Outlook (Microsoft Graph API + OAuth2), Google Calendar, OpenWeatherMap
> - Pipeline vocal en streaming (WebSocket, STT → LLM → TTS) avec repli texte ; routage d'intentions par function calling OpenAI (15 outils : e-mails, agenda, mémoire, rappels, briefing)
> - Classification d'e-mails Gmail/Outlook : pré-filtrage par règles métier (mots-clés du domaine juridique) puis classification LLM à champs explicites (urgence, action recommandée, échéance, interlocuteur), catégorisation automatique via Graph API et synthèses envoyées par e-mail
> - Système de mémoire conversationnelle scopée par utilisateur avec Redis : clés hiérarchiques, expiration automatique (TTL), namespaces séparés (projets / préférences / tâches)
> - Résilience : dégradation gracieuse des workflows (continueOnFail) et bascule en réponses simulées si l'API LLM est indisponible
>
> Outils : OpenAI API (gpt-4o, Whisper, TTS), Redis, n8n, Microsoft Graph API, Google Calendar API, Telegram API, OpenWeatherMap, Docker Compose, Coolify, VPS Hostinger

### Version À TERME (après Étape 0 + T1 + T3 + T5 + T2 ; puces neuves marquées ✚)

> Jarvis — Assistant personnel vocal d'IA générative et d'automatisation (jarvis.obyz.biz)
>
> - Conception d'une architecture multi-services conteneurisée (FastAPI, Next.js 14, Redis, PostgreSQL/pgvector, nginx) déployée sur VPS via Coolify ; intégrations orchestrées par des workflows n8n : Telegram, Gmail, Outlook (Microsoft Graph API + OAuth2), Google Calendar, OpenWeatherMap
> - Pipeline vocal en streaming (WebSocket, STT → LLM → TTS) avec repli texte ; routage d'intentions par function calling OpenAI (15 outils)
> - Classification d'e-mails Gmail/Outlook : pré-filtrage par règles métier puis classification LLM **à sortie structurée validée par schéma (JSON Schema)** (urgence, action, échéance, interlocuteur), catégorisation via Graph API et synthèses automatisées — ✚ **jeu d'évaluation precision/recall/F1 par catégorie** [T1]
> - ✚ **RAG sur l'historique de conversations et les synthèses d'e-mails** (embeddings OpenAI, base vectorielle pgvector, retrieval) exposé comme outil de l'assistant, **évalué par un jeu de questions/réponses de référence (hit rate @k)** [T2]
> - Système de mémoire conversationnelle scopée par utilisateur avec Redis (clés hiérarchiques, TTL, namespaces séparés) ; profil client externalisé → déploiement d'un nouveau client sans modification de code [Étape 0 pt 4]
> - ✚ **Fiabilité & supervision** : alertes e-mail automatiques en cas d'échec d'un workflow n8n [T3], dégradation gracieuse (continueOnFail), réponses simulées si l'API LLM est indisponible
> - ✚ **CI GitHub Actions** : lint (ruff), tests (pytest + Playwright E2E), build des images Docker [T5]
>
> Outils : OpenAI API (gpt-4o, Whisper, TTS, embeddings), Redis, PostgreSQL / pgvector, n8n, Microsoft Graph API, Google Calendar API, Telegram API, OpenWeatherMap, Docker Compose, GitHub Actions, Coolify, VPS Hostinger

**Différences actuelle → à terme** : +schéma validé (T1), +éval classifieur (T1), +RAG & éval retrieval (T2),
+pgvector, +alertes workflow (T3), +CI GitHub Actions (T5), multi-tenant passé en affirmatif (Étape 0).
« migration LangChain » retirée (voir Note motif V2). « agents LangChain » et « historique PostgreSQL »
retirés (non câblés / inexistants) — sauf si on décide de les câbler (hors fenêtre lundi).

---

## Ordre conseillé (révisé 2026-09-03)

0. **Étape 0** (pin n8n + cron unique + `WORKFLOW_VERSION` + hardcodé) — prérequis, ~1–2 h
1. **Étape 1** : réparer le chemin v2 (décision Path A / Path B)
2. **T1** (sortie structurée + éval v1 vs v2) — l'éval tranche l'archi cible V1/V2
3. **T3** (alertes n8n) — après étape 0, sinon la 1ʳᵉ alerte = le bug v2 déjà connu
4. **T5** (CI) — indépendant, insérable dès que possible
5. **T2** (RAG + éval) — le morceau principal, une fois la base saine
6. Divergences repo↔prod (`morning-briefing`, `outlook-read-inbox`) + nettoyage n8n

> L'ancien ordre (T3→T5→T1→T2, Bonus en dernier) est remplacé : le « Bonus » remonte en étape 0
> car c'est la fondation de T1 et T3. Séquence détaillée : `DOCS/reports/repo-vs-n8n-prod-2026-09-01.md` §7.

### Réalisme fenêtre vendredi → lundi

| Faisable d'ici lundi | Serré / à scoper minimal |
|---|---|
| Étape 0 (~1–2 h) · Étape 1 Path B (~2–4 h) · T1 sortie structurée + éval (~1 j) · T3 alertes (~0,5 j) · T5 CI (~0,5 j) | T2 RAG (~1,5–2 j) — viser un **RAG minimal** : pgvector + ingestion des analyses e-mails Redis + `sessions/*.md` (en générer 3–4) + outil `rechercher_historique` + éval 10 Q/R. Pas de cache sémantique, pas d'ingestion temps réel. |

**Envoi du CV** :
- Si T1 + T3 + T5 sont ✅ mais pas T2 → envoyer la **version actuelle + les 3 puces T1/T3/T5**, retirer la puce RAG.
- Version à terme complète → seulement quand T2 est ✅ avec son rapport d'éval commité.
- Ne jamais laisser une puce « (en cours) » : soit la clause est vraie et démontrable, soit elle sort.

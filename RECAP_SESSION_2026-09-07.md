# Sauvegarde de session — 2026-09-07

Projet : Jarvis V2 — chantier « embellissement CV » (rendre vraies les clauses du bloc Jarvis avant envoi).
Session Claude Code. Branche `main`. Reconstitution fidèle des échanges + notes d'actions techniques entre crochets.

---

## Tour 1 — Utilisateur

> pwd

## Tour 1 — Assistant

`C:\dev\projet-jarvis`

---

## Tour 2 — Utilisateur

> /prime

## Tour 2 — Assistant

_[Lecture STATUS.md, PRD.md, STRUCTURE.md, docs/plans/cv-embellissement-scope.md, MEMORY.md, git log, état CI.]_

### Récap projet — Jarvis V2

**Mode maintenance / « embellissement CV »** (0 SPEC formel — le travail passe par `docs/plans/cv-embellissement-scope.md`). V2 livrée en prod le 2026-06-03 (`jarvis.obyz.biz`).

**⚠️ STATUS.md périmé** — dernier commit reflété `8ef96cb`, HEAD réel `1735596`. Bloc mis à jour à la main le 2026-09-01 ; toute la campagne des 3-4 septembre (Étape 0, Path B, T1, T3, T2, T5) n'y est pas. Un `/close` est dû.

**Avancement — chantier CV (fenêtre visée 4 → 8 sept) :**

| Tâche | État | Reste |
|---|---|---|
| Étape 0 (pin n8n 2.22.5, cron unique, `WORKFLOW_VERSION=v1`, purge hardcodé) | ✅ | 2 var d'env Coolify sur service `n8n` + redeploy — côté user |
| T1 — sortie JSON Schema + éval classifieur | 🟡 | Path B en prod + harness OK. Manque `eval/classifier/dataset.csv` (30-50 e-mails annotés) + run + commit rapport |
| T2 — RAG pgvector | 🟡 | Code complet, jamais validé live (Docker Hub KO dans le sandbox). Manque `docker compose up postgres` + `ingest_rag.py` + `run_eval.py` réel + rapport |
| T3 — alertes e-mail échec workflow n8n | ✅ | Terminé end-to-end (16 workflows). Bonus optionnel : throttling Redis |
| T5 — CI GitHub Actions | 🟡 | `.github/workflows/ci.yml` commité mais jamais poussé → 1er run vert non prouvé |

**Git — point bloquant :** 11 commits locaux non poussés sur `main` (origin/main s'arrête avant `d2bfcf2`). Tant que ce n'est pas poussé : pas de run CI → T5 ne peut pas passer ✅.

**Architecture :** multi-services conteneurisé (FastAPI + Next.js 14 + Redis + Postgres/pgvector + nginx + n8n), Docker Compose → VPS Hostinger via Coolify. Frontière SDK direct (live) / n8n (async). Mémoire uniquement via `memory_service.py`. RAG = SQL direct pgvector, pas de wrapper LangChain.

**Action suggérée :**
- → `git push origin main` puis PR — déclenche le 1er run CI et clôt le « Fait quand » de T5.
- → Finir T2 : `docker compose up -d postgres` → `ingest_rag.py` → `run_eval.py` → commit `DOCS/reports/rag-eval-2026-09-07.md`.
- → `/close` ensuite pour resynchroniser STATUS.md.

---

## Tour 3 — Utilisateur

> ok pour git push origin main on verra T5 se faire. puis pour Etape 0, CLIENT_CR_RECIPIENT, CLIENT_GMAIL, CLIENT_SUMMARY_RECIPIENT, CLIENT_CALENDAR_ID, OPENWEATHER_API_KEY, etc. étaient bien injectées via $env (à confirmer que tout est ok par toi). T3 à quelle adresses mails les mails ont été envoyés ?

## Tour 3 — Assistant

_[Exécuté : `git push origin main` → `8ef96cb..1735596 main -> main`, 11 commits. Run CI `34104821880` déjà `in_progress`.]_

### 1. Push — fait

11 commits poussés. Run CI parti : 4 jobs (checks / backend-tests / e2e / docker-build).

### 2. Étape 0 — injection `$env` : état du repo (vérifié)

| Élément | État |
|---|---|
| `docker-compose.yml` service `n8n` | déclare `CLIENT_GMAIL`, `CLIENT_CALENDAR_ID` (déf. `primary`), `CLIENT_SUMMARY_RECIPIENT`, `CLIENT_CR_RECIPIENT`, `CLIENT_OUTLOOK_MAILBOX`, `SUMMARY_RECIPIENT_EMAIL`, `OPENWEATHER_API_KEY`, listes keywords/domains |
| `N8N_BLOCK_ENV_ACCESS_IN_NODE: "false"` | présent → c'est lui qui autorise `$env` dans les Code nodes |
| Code nodes | tous via helper `envv(k) = try { $env[k] } catch {}` (n8n 2.x ne remplit plus `process.env`) — `error-handler`, les 2 classifiers v2, les v1 (commit `98f3a46`) |
| Défauts identifiants | aucun (multi-tenant OK), sauf `CLIENT_CALENDAR_ID=primary` |
| `WORKFLOW_VERSION` | retiré du service n8n (routage v1/v2 = backend only) ✅ |

**Chaîne de résolution du destinataire d'alerte** (`error-handler.json`, node « Formater alerte ») : `CLIENT_CR_RECIPIENT` → `CLIENT_SUMMARY_RECIPIENT` → `SUMMARY_RECIPIENT_EMAIL`. Si les trois vides : pas d'e-mail, `console.warn` + arrêt propre.

**Ce que je ne peux pas confirmer depuis le repo** : que les valeurs sont réellement peuplées dans l'env Coolify du conteneur n8n prod. Le scope doc (04-09) note la vérif faite ce jour-là mais garde en `⬜ reste` : `CLIENT_GMAIL`, `CLIENT_SUMMARY_RECIPIENT`, `CLIENT_CR_RECIPIENT`, `OPENWEATHER_API_KEY`, `CLIENT_CALENDAR_ID` « constatés vides dans le conteneur » + redeploy n8n. À re-vérifier côté Coolify.

Dette doc mineure : commentaire `docker-compose.yml` (~L102) dit encore « via process.env » alors que le code lit `$env[k]`.

### 3. T3 — adresses des mails de test

Le test end-to-end (workflow jetable avec `throw`) → **e-mail d'alerte reçu à `aboubakary_ouattara@hotmail.com`** (scope doc L235). Donc en prod Coolify `CLIENT_CR_RECIPIENT = aboubakary_ouattara@hotmail.com`. Expéditeur = compte OAuth « Gmail Jarvis ».

À ne pas confondre avec les synthèses des classifiers e-mails (`summary_sent_to`), routées vers `ouat.abou34@gmail.com` via `CLIENT_SUMMARY_RECIPIENT` — autre flux, corrigé en effet de bord pendant T3.

---

## Tour 4 — Utilisateur

> euh stp il y a des workflow qui se lancent chaque 5 minutes. wkf "reminders". C le bon fonctionnement ? ensuite sur Github le CI plante sur "Run pytest -q" et "Start backend (fake LLM)"

## Tour 4 — Assistant

_[Inspection `workflows/reminders.json` ; `gh run view 34104821880 --log-failed`.]_

### 1. Workflow `reminders` toutes les 5 min — oui, c'est normal

`reminders.json` a deux entrées indépendantes :

| Déclencheur | Rôle |
|---|---|
| `Webhook POST /reminders` | Création d'un rappel → e-mail de confirmation |
| `scheduleTrigger` « Toutes les 5 minutes » | Notification : polling `GET backend:8000/api/reminders/pending` → si `count > 0` → e-mail « X rappel(s) en attente » → `PATCH /reminders/{id}/notified` |

Le cron 5 min est le fonctionnement voulu d'un notifieur de rappels : latence 0–5 min. Léger : 1 requête HTTP interne, e-mail seulement si `count > 0`, `notified` évite les doublons.

**3 points à surveiller :**
1. **Flood d'alertes T3 possible** — `reminders` fait partie des 16 workflows avec l'error-handler. Si `backend:8000/api/reminders/pending` devient injoignable → mail d'alerte toutes les 5 min. D'où le throttling Redis en reste de T3.
2. **E-mail hardcodé** `ouat.abou34@gmail.com` en dur dans 2 Code nodes (`sendTo` L43 + `mailDest` L101). La purge Étape 0 ne visait que les classifiers/backend.
3. La copie repo est `[DEV] Reminders Notifier`, `active: false` — normal, c'est la copie `[PROD]` swappée qui tourne.

### 2. CI qui plante — cause unique

```
psycopg2.errors.UndefinedObject: type "vector" does not exist
LINE 6:  embedding VECTOR(1536) NOT NULL,
```

`ci.yml` (écrit pour T5 le 04-09, avant T2) utilise `postgres:16-alpine` — pas de pgvector. Or T2 (commit `1735596`) ajoute la table `documents` avec `embedding VECTOR(1536)` + `CREATE EXTENSION vector` dans `init_db()`.

- **`backend-tests` / `pytest -q`** : `.....FF` — `test_health_endpoint` + 1 autre déclenchent la création de table → `ProgrammingError`.
- **`e2e` / Start backend** : `uvicorn backend.main:app` appelle `init_db()` au démarrage → même erreur → `/health` ne répond jamais.

(`checks` lint+typecheck+build est ✓.)

**Fix appliqué** dans `.github/workflows/ci.yml` — service `postgres` des 2 jobs :

```diff
-        image: postgres:16-alpine
+        image: pgvector/pgvector:pg16
```

Aligné sur `docker-compose.yml`. Non poussé — tu veux que je commite + push pour relancer le run ?

---

## Tour 5 — Utilisateur

> ok go.

## Tour 5 — Assistant

_[Commit `0861c94` « ci(t5): image pgvector/pgvector:pg16 pour la table documents (RAG T2) » + push. Nouveau run `34106147959`. Polling jusqu'à complétion → `completed failure`.]_

Progrès : le fix pgvector marche —
- ✓ Backend tests (pytest)
- ✓ Docker images build
- ✓ Lint + typecheck + build
- ✗ E2E Playwright — **nouvelle vraie erreur** : `voice-connection.spec.ts:35` attend 5 boutons Quick Actions, la page en rend **6**.

_[Inspection : `QUICK_ACTIONS` dans `src/types/index.ts` = 6 entrées (briefing, compte-rendu, outlook-classify, classify, tasks, memory) depuis la séparation Outlook/Gmail du refactoring Intent Router. Test resté figé sur 5.]_

_[Edit `tests/e2e/voice-connection.spec.ts` : `toHaveCount(5)` → `toHaveCount(6)` + commentaire. Commit `480705a` « test(e2e): Quick Actions = 6 boutons » + push. Run `34106459156` → `completed success`.]_

✅ **CI verte** — run `34106459156`, les 4 jobs passent. T5 « 1er run CI vert » est atteint.

3 commits ont été nécessaires :

| Commit | Fix |
|---|---|
| `0861c94` | `pgvector/pgvector:pg16` en CI |
| `480705a` | test e2e `voice-connection` : 5 → 6 boutons |

Aucun n'était un vrai bug produit : une image CI en retard sur `docker-compose.yml`, et un test jamais mis à jour.

**Reste ouvert (pas bloquant) :**
- `reminders` toutes les 5 min = normal, mais flood d'alertes T3 si le backend tombe → throttling Redis.
- E-mails hardcodés `ouat.abou34@gmail.com` dans `reminders.json` (2 nodes) et `smart-agent.json` (fallback).
- T5 strict demandait un run « sur une PR » : là c'est un run sur `push main`. Trigger `pull_request` pas encore exercé.

---

## Tour 6 — Utilisateur

> en fait tu penses qu'on ne peut pas mettre la version cible actuellement ? Car là on travaille là et on finira avant.. Et en plus le CV doit arriver, être lu et on va planifier le rdv..alors on a le temps de bien finir...

_(Note : cet échange a en réalité eu lieu après une première question sur la cadence reminders / les variables d'env / le contenu du CV cible. Ordre reconstitué pour la lecture.)_

## Tour 6 — Assistant

Mon avis franc : **non, pas la version cible complète aujourd'hui** — mais tu peux envoyer mieux que la version « actuelle » stricte.

| Puce cible | État réel | Verdict |
|---|---|---|
| Sortie structurée JSON Schema | en prod, testée live | ✅ envoyable |
| Alertes échec workflow n8n (T3) | end-to-end, mail reçu | ✅ envoyable |
| CI GitHub Actions (T5) | verte | ✅ envoyable |
| Multi-tenant « sans modif de code » | vrai après fix des 3 e-mails | ✅ envoyable ce soir |
| Éval classifieur precision/recall/F1 | harnais construit, dataset jamais annoté ni exécuté | ⚠️ ~1h → puis envoyable |
| RAG / embeddings / pgvector | code complet, jamais tourné une seule fois | ❌ pari sur du code non testé |

Le problème n'est pas le délai — c'est que **T2 n'a jamais été exécuté**. Pour un poste Tech Lead / Architecte IA, l'interlocuteur va demander « montrez-moi le RAG, c'est quoi le hit rate ? ». Répondre « c'est pas tout à fait fini » sur une ligne écrite est pire que ne pas l'avoir mise.

**Chemin en 3 temps :**
1. Maintenant : fixe les 3 e-mails (`CLIENT_SUMMARY_RECIPIENT`, 15 min).
2. Dans l'heure : remplis `eval/classifier/dataset.csv` (30-50 e-mails annotés) + `run_eval.py` + commit rapport.
3. Envoie ce CV-là : version actuelle + JSON Schema + T3 + T5 + éval classifieur + multi-tenant = **5 des 6 items cible**.
4. RAG : quand T2 aura tourné une fois avec `rag-eval-<date>.md` commité → ajoute la puce RAG + `pgvector`.

---

## Tour 7 — Utilisateur

> ok pour les 3 emails. (en fait j'ai le fichier csv ici C:\Users\aboub\Downloads\jarvis_classifier_eval_dataset_40.csv et en xlsx) . pour la version de cv là et les puces, c'est dans quel dossier ? ;)

## Tour 7 — Assistant

_[Vérif format : `eval/classifier/run_eval.py::read_dataset` tolérant — `csv.DictReader` en `utf-8-sig` (BOM OK), `sender` manquant → `""`, colonnes en trop ignorées, `source` non lowercasé mais non utilisé dans le payload, labels lowercasés. CSV user = 40 lignes annotées, labels dans les enums (urgence haute/moyenne/faible ; action repondre/lire/aucune/classer). → compatible.]_

_[Copie `C:/Users/aboub/Downloads/jarvis_classifier_eval_dataset_40.csv` → `eval/classifier/dataset.csv`. Fichier gitignored → données réelles non commitées, seul le rapport agrégé le sera.]_

_[Fix des 3 e-mails hardcodés :_
- `workflows/reminders.json` node « Formater confirmation » : ajout `const envv = ...; const to = envv('CLIENT_SUMMARY_RECIPIENT') || envv('SUMMARY_RECIPIENT_EMAIL') || '';` + `to` dans le retour ; node « Email confirmation » `sendTo` → `={{ $json.to }}`.
- `workflows/reminders.json` node « Formater l'email » : `const mailDest = 'ouat.abou34@gmail.com';` → `envv('CLIENT_SUMMARY_RECIPIENT') || envv('SUMMARY_RECIPIENT_EMAIL') || ''` + garde `if (!mailDest) { console.warn(...); return []; }`.
- `workflows/smart-agent.json` L78 : `|| 'ouat.abou34@gmail.com'` → `|| $env.CLIENT_SUMMARY_RECIPIENT || $env.SUMMARY_RECIPIENT_EMAIL`.
JSON valides, `grep -r ouat.abou34` (hors snapshots) → vide.]_

_[Ajout d'un 3e bloc « Version À ENVOYER MAINTENANT » dans `DOCS/plans/cv-embellissement-scope.md` § « Bloc CV Jarvis ».]_

_[Commit `5e5d6af` « chore(n8n): purge dernier e-mail hardcodé -> CLIENT_SUMMARY_RECIPIENT » (3 fichiers) + push.]_

_[Exécution `python eval/classifier/run_eval.py eval/classifier/dataset.csv` → `DOCS/reports/classifier-eval-2026-09-07.md`. Commit `4155cc9` + push. Runs CI `34112704859` et `34112992159` → success.]_

### Résultat éval classifieur

| champ | v1 (macro-F1 / acc) | v2 (macro-F1 / acc) |
|---|---|---|
| urgence | 0,69 / 0,72 | 0,63 / 0,68 |
| action | 0,50 / 0,57 | 0,45 / 0,57 |

→ **v1 ≥ v2** : `WORKFLOW_VERSION=v1` confirmé. v2 = robustesse du format (JSON Schema strict), pas la qualité. Répond à la question ouverte de l'audit §5.

Notes du rapport : modèle `gpt-4o-mini` (défini dans `prompts.py`) ; classe `aucune` (4 e-mails) ratée à 100 % par les 2 moteurs ; nuance `moyenne` difficile des deux côtés.

### Où vit le bloc CV

**`DOCS/plans/cv-embellissement-scope.md`**, section « ## Bloc CV Jarvis — version actuelle vs version à terme ». J'y ai ajouté « Version À ENVOYER MAINTENANT ». Le `.docx` lui-même n'est pas dans le repo — fichier perso (Downloads/Documents).

**État CV : 5,5/6** après l'éval. Manque la puce RAG (T2).

---

## Tour 8 — Utilisateur

> alors peut être qu'on arrivera au bout alors ? ;) go pour le rag..? (moi j'importe les deux wkf sur n8n ?)

## Tour 8 — Assistant

_[Test Docker : `docker version` → daemon éteint (`pipe/dockerDesktopLinuxEngine introuvable`). Lecture `eval/rag/README.md`, `qa_reference.example.csv`, `backend/scripts/ingest_rag.py` : ingestion gère Redis absent, `qa_reference.example.csv` ne teste que 4 `sessions/*.md` déjà générées → RAG runnable avec seulement Postgres+pgvector.]_

### RAG — go, mais j'ai besoin de Docker

Le daemon Docker Desktop est éteint. L'accès Docker Hub n'est plus le souci (la CI vient de tirer `pgvector/pgvector:pg16`). L'éval RAG tourne sans Redis ni données classifieur.

→ **Lance Docker Desktop**, dis-moi quand c'est prêt. Je fais : `docker compose up -d postgres` → table `documents` → `ingest_rag.py` → `run_eval.py` réel → commit `DOCS/reports/rag-eval-<date>.md`. ~10 min.

### Les 2 workflows n8n — toi, mais pas bloquant pour le CV

La puce CV « profil client externalisé (`CLIENT_*`) » porte sur `backend/config.py`, déjà vraie. Les 3 e-mails étaient de la cohérence interne.

**Le plus rapide** (pas d'import, pas de re-liaison de creds) — édite 3 champs *To* dans l'UI n8n sur les workflows **[PROD]** :

| Workflow [PROD] | Node | Champ *To* |
|---|---|---|
| `reminders` | Email confirmation | `={{ $env.CLIENT_SUMMARY_RECIPIENT \|\| $env.SUMMARY_RECIPIENT_EMAIL }}` |
| `reminders` | Envoyer email | `={{ $env.CLIENT_SUMMARY_RECIPIENT \|\| $env.SUMMARY_RECIPIENT_EMAIL }}` |
| `smart-agent` | Envoyer email draft | `={{ $('Webhook').first().json.body.recipient_email \|\| $env.CLIENT_SUMMARY_RECIPIENT \|\| $env.SUMMARY_RECIPIENT_EMAIL }}` |

+ impératif : renseigne `CLIENT_SUMMARY_RECIPIENT` dans l'env Coolify du service `n8n`.

---

## Tour 9 — Utilisateur

> Docker Desktop is running now, go

## Tour 9 — Assistant

_[`docker version` → server 28.3.0 OK. `docker-compose.yml` : service `postgres` sans mapping de port host.]_

_[`docker ps -a` : `projet-jarvis-postgres-1` déjà Up (healthy) mais en `postgres:16-alpine` (ancienne image, pas de pgvector), pas de port publié. Décision : conteneur jetable isolé sur port 5433.]_

_[`docker run -d --name jarvis-rag-pg ... -p 5433:5432 pgvector/pgvector:pg16` → **échec** : `httpReadSeeker: failed open ... EOF` sur `production.cloudfront.docker.com` (même panne CDN Docker Hub que documentée le 04-09). 3 tentatives `docker pull` → même échec sur le blob `9b05db12...`.]_

_[Contournement : `docker images` → `postgres:16` (debian, 636 MB) ET `postgres:16-alpine` en cache. GitHub joignable (HTTP 200). Build d'une image locale :]_

```dockerfile
FROM postgres:16
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends build-essential postgresql-server-dev-16 git ca-certificates; \
    git clone --branch v0.8.0 --depth 1 https://github.com/pgvector/pgvector.git /tmp/pgvector; \
    cd /tmp/pgvector; make; make install; \
    apt-get purge -y build-essential postgresql-server-dev-16 git; apt-get autoremove -y; \
    rm -rf /tmp/pgvector /var/lib/apt/lists/*
```

_[`docker build -t jarvis-pgvector:local .` → succès (apt depuis deb.debian.org, source depuis GitHub — CDN différents de CloudFront). `docker run -d --name jarvis-rag-pg ... -p 5433:5432 jarvis-pgvector:local`. `CREATE EXTENSION vector` → `extversion 0.8.0`.]_

_[`DATABASE_URL=postgresql://postgres:password@localhost:5433/jarvis` + `OPENAI_API_KEY` (extrait de `.env` en utf-8). `python -c "from backend.models import init_db; init_db()"` → table `documents` créée (+ `users`, `sessions`).]_

_[FK `documents.user_id → users.id` NOT NULL → `INSERT INTO users (id, email, created_at) VALUES (2, 'rag-eval@local', now())`.]_

_[`python backend/scripts/ingest_rag.py --user-id 2` → Redis injoignable (localhost:6379) → e-mails ignorés (géré) ; **5 fichiers `sessions/*.md` ingérés** (`text-embedding-3-small`, 1536 dim). Table `documents` : 5 lignes source=session.]_

_[`python eval/rag/run_eval.py eval/rag/qa_reference.example.csv` (réel) → **Hit rate @5 : 5/5 = 100%**, rang 1 pour les 5 questions. `DOCS/reports/rag-eval-2026-09-07.md` écrit.]_

_[Ajout au rapport d'une section « Conditions du run » + réserve : avec k=5 et corpus de 5 docs, « @5 » est trivialement 100 % ; le signal réel = rang 1 partout.]_

_[Smoke test `format_search_results(2, 'Quelles sont mes preferences de notification ?', k=3)` → renvoie des extraits classés et sourcés `[Session]` avec scores de similarité ; top hit = la session préférences. Critère T2 « réponse sourcée » validé.]_

_[MàJ `DOCS/plans/cv-embellissement-scope.md` : bloc « Version À ENVOYER MAINTENANT » → 6/6, ajout puce RAG + `pgvector` dans Outils + section « Réserves défendables en entretien ». Commit `913ec35` « feat(t2): RAG eval reelle - hit rate @5 100%, rang 1 sur 5/5 (pgvector 0.8.0) » + push. `docker rm -f jarvis-rag-pg` (nettoyage).]_

### 6/6 — c'est bouclé

**RAG (T2) validé en réel :**
- Docker Hub refuse toujours `pgvector/pgvector:pg16` depuis cette machine → image `jarvis-pgvector:local` buildée depuis `postgres:16` en cache + pgvector 0.8.0 compilé depuis GitHub. Conteneur jetable port 5433, supprimé après.
- `init_db()` → table `documents` OK. `ingest_rag.py` → 5 sessions embeddées, Redis absent → 0 e-mail (géré).
- `run_eval.py` réel → hit rate @5 = 100 %, le bon document en rang 1 pour les 5 questions. Rapport commité.
- Smoke test `format_search_results()` → extraits classés et sourcés → critère T2 validé.
- Réserve écrite dans le rapport : corpus PoC de 5 docs → « @5 » trivial ; le vrai signal est le rang 1 partout.

**CV — bloc 6/6 prêt** dans `DOCS/plans/cv-embellissement-scope.md`.

**Commits poussés aujourd'hui (CI verte) :** `0861c94` CI pgvector · `480705a` test e2e · `5e5d6af` purge e-mail + bloc CV · `4155cc9` éval classifieur · `913ec35` éval RAG.

**Reste de ton côté (aucun ne bloque le CV) :**
1. n8n prod : 3 champs *To* + `CLIENT_SUMMARY_RECIPIENT` dans Coolify.
2. Optionnel : rejouer l'éval RAG en prod avec les vraies synthèses e-mails Redis.
3. `/close` : STATUS.md est à `8ef96cb`, on est à `913ec35` avec T1/T2/T3/T5 tous faits.

---

## Tour 10 — Utilisateur

> tu peux me dire un peu plus sur ton rapport et leur explication stp ? En fait les termes je ne les comprends pas ;).

## Tour 10 — Assistant

### Rapport 1 — `classifier-eval-2026-09-07.md`

**Ce qu'il teste** : le classifieur lit un e-mail et sort `urgence` (haute/moyenne/faible) et `action` (repondre/lire/relancer/classer/aucune). Tu as annoté 40 e-mails réels à la main. Le script fait classer ces 40 par v1 (ancienne) et v2 (JSON Schema), puis compare machine vs toi.

| Terme | En clair | Sur tes chiffres |
|---|---|---|
| **Accuracy** (justesse) | Sur 40, combien exactement bien classés | v1 urgence 0,72 = 29/40 |
| **Precision** — par catégorie | Quand la machine dit « haute », elle a raison combien de fois | v1 « haute » 0,86 → 14 % de fausses alertes |
| **Recall** — par catégorie | Sur tous les vrais « haute », combien attrapés | v1 « haute » 0,75 → rate 25 % |
| **F1** | Note unique combinant precision + recall ; haute seulement si les deux le sont ; 0 = catégorie cassée | v1 « haute » 0,80 |
| **support** | Combien des 40 sont vraiment dans cette catégorie | « haute » support 16 |
| **macro-F1** | Moyenne des F1 de toutes les catégories, chacune comptant pareil ; **la note globale** | v1 urgence 0,69 · v2 0,63 |

**Pourquoi pas juste l'accuracy** : si 90 % des mails sont « faible », une machine qui répond toujours « faible » fait 90 % d'accuracy et rate tous les urgents. D'où la mesure par catégorie.

**Tension precision ↔ recall** : machine « parano » (tout urgent) → recall haut, precision basse. Machine « prudente » → l'inverse. On veut les deux → c'est ce que F1 résume.

**Matrice de confusion** : lignes = vérité, colonnes = devinette machine ; diagonale = correct, reste = erreurs et lesquelles. Ta matrice v2 urgence :

```
                 devine haute | moyenne | faible
vraiment haute        11           3         2      ← 2 urgents rétrogradés = erreur dangereuse
vraiment moyenne       2           3         6      ← "moyenne" s'effondre en "faible"
vraiment faible        0           0        13      ← parfait
```

**Tes résultats** : urgence v1 ~72 % (fort haute/faible, faible sur moyenne), v2 un peu moins bon. Action : les deux ~57 %, « repondre » bien attrapé, « aucune » jamais attrapé (F1 0,00 des deux côtés). **Verdict** : v2 ne classe pas mieux → on garde v1, v2 reste dispo pour la robustesse du format.

*Détail : éval sur `gpt-4o-mini`.*

### Rapport 2 — `rag-eval-2026-09-07.md`

**Ce qu'est le RAG** : l'assistant reçoit « qu'a-t-on décidé sur X ? », ne s'en souvient pas → il cherche dans une base de tes anciennes notes/synthèses, remonte les plus pertinentes, répond à partir d'elles. RAG = Retrieval-Augmented Generation.

| Terme | En clair |
|---|---|
| **Embedding** | Un texte → liste de 1536 nombres (vecteur) qui capture son *sens*. Textes proches en sens → listes proches, même sans mots communs. |
| **pgvector** | PostgreSQL + extension qui stocke ces vecteurs et retrouve vite les plus proches. |
| **Similarité cosinus** | Mesure de proximité entre 2 vecteurs = angle entre 2 flèches. 1,0 = même direction (même sens), 0 = sans rapport. « Distance » = 1 − similarité. |
| **top-k / k** | On renvoie les k plus proches (ici k=5). |
| **hit rate @k** | Pour chaque question de référence, le document attendu est-il dans le top k ? Proportion de oui. Tu as 5/5 = 100 %. |
| **rang** | Où dans la liste le bon document est arrivé. Rang 1 = le plus proche. Ton rapport : rang 1 pour les 5. |

**Réserve honnête (dans le rapport)** : seulement 5 documents en base. Si k=5 et 5 documents, « le bon est-il dans le top 5 » est toujours vrai → le 100 % @5 seul n'impressionne pas. Ce qui est significatif = le **rang 1** : la note préférences remonte en #1 pour la question préférences, pas la note agenda. La similarité discrimine par le sens. Pour un chiffre qui *prouve* la qualité : rejouer avec des dizaines de vraies synthèses e-mails.

---

## Tour 11 — Utilisateur

> ok merci. je relis tranquillement pour comprendre. voici le cv modifié :C:\Users\aboub\Downloads\CV_OUATTARA_Aboubakary_TechLead_IA_FINAL_AgentsIA_07092026_v2

## Tour 11 — Assistant

_[Localisé : `CV_OUATTARA_Aboubakary_TechLead_IA_FINAL_AgentsIA_07092026_v2.docx`. Extraction du texte via zipfile/xml.]_

**La section Jarvis est honnête et colle à ce qu'on a vérifié aujourd'hui (6/6).** Envoyable.

| Puce | Vérif |
|---|---|
| Archi conteneurisée (…PostgreSQL/pgvector, nginx) via Coolify | ✅ pgvector réel |
| Intégrations n8n : Telegram, Gmail, Outlook (Graph/OAuth2), Calendar, OpenWeatherMap | ✅ |
| Pipeline vocal streaming STT→LLM→TTS, repli texte | ✅ — pas de « < 1s Realtime » |
| Function calling → 15 outils | ✅ |
| Classification e-mails, sortie JSON Schema, éval P/R/F1 sur 40 e-mails | ✅ |
| RAG embeddings + pgvector cosinus, outil `rechercher_historique`, éval Q/R | ✅ — pas de chiffre annoncé, pas de « en prod » |
| Mémoire Redis scopée + profil client `CLIENT_*` | ✅ |
| Alertes échec workflow n8n + CI GitHub Actions verte | ✅ |

Rien de faux. Pas d'« Anthropic Claude API » comme composant produit, pas d'« agents LangChain » (c'est « function calling / tool use »), LangChain/QDrant en « Notions / formation ».

**3 points à savoir défendre en entretien (pas des corrections bloquantes) :**

1. **« Gmail/Outlook : pré-filtrage par règles métier … catégorisation via Graph API »** — le pré-filtre mots-clés juridiques et la catégorisation Graph sont **Outlook uniquement**. Gmail = exclusion newsletters + classification + synthèse.
2. **« RAG sur … synthèses d'e-mails »** — le code d'ingestion couvre sessions + synthèses e-mails, mais l'éval réelle n'a tourné que sur 5 résumés de sessions (Redis e-mails vide). Formulation : « l'ingestion couvre les deux sources ; le jeu de référence actuel porte sur les résumés de session ».
3. **RAG en prod** — store pgvector dans la stack compose, retrieval validé en local. Redeploy Coolify du service postgres + branchement de l'outil en prod = dernière étape. Ne pas dire « le RAG sert les utilisateurs en prod ».

Le reste du CV (onz.africa, expériences CRM) est hors de ce que je peux vérifier. Pour Jarvis : **feu vert**.

---

## Tour 12 — Utilisateur

> fais une sauvegarde de la session dans un fichier telle que c'est actuellement, je vais lire. si tu veux tu ajoutes ton résumé en fin de sauvegarde mais commence par le contenu de la session tel qu'il est.

## Tour 12 — Assistant

_[Ce fichier.]_

---
---

# Résumé de la session (ajout de l'assistant)

## Objectif

Rendre vraies et démontrables les clauses du bloc Jarvis du CV avant envoi (poste Tech Lead / Architecte IA). Le CV part avant l'entretien, donc chaque ligne doit tenir en questions techniques.

## Ce qui a été fait (tout poussé sur `main`, CI verte)

| # | Commit | Contenu | Effet |
|---|---|---|---|
| 0 | `1735596` (déjà local) | 11 commits Étape 0 / Path B / T1 harness / T3 / T5 / T2 code | **Poussés** — origin/main était très en retard |
| 1 | `0861c94` | CI : `postgres:16-alpine` → `pgvector/pgvector:pg16` | Débloque `backend-tests` + `e2e` (table `documents` VECTOR) |
| 2 | `480705a` | test e2e `voice-connection` : 5 → 6 boutons Quick Actions | CI verte |
| 3 | `5e5d6af` | Purge dernier e-mail hardcodé (`reminders`, `smart-agent`) → `CLIENT_SUMMARY_RECIPIENT` + bloc CV « à envoyer » | `grep ouat.abou34` (hors snapshots) vide |
| 4 | `4155cc9` | Éval classifieur v1 vs v2 exécutée sur 40 e-mails → `DOCS/reports/classifier-eval-2026-09-07.md` | T1 « Fait quand » complet |
| 5 | `913ec35` | Éval RAG réelle (pgvector 0.8.0) → `DOCS/reports/rag-eval-2026-09-07.md` + bloc CV 6/6 | T2 « Fait quand » complet |

## État des tâches du chantier CV

| Tâche | Avant la session | Après |
|---|---|---|
| Étape 0 | ✅ sauf hardcodé résiduel + env Coolify | ✅ hardcodé purgé (repo). Reste : env Coolify + réimport prod |
| T1 (schéma + éval) | 🟡 schéma en prod, éval jamais faite | ✅ éval faite : **v1 ≥ v2**, `WORKFLOW_VERSION=v1` confirmé |
| T2 (RAG) | 🟡 code complet, jamais exécuté | ✅ exécuté : hit rate @5 100 %, rang 1 sur 5/5, réponse sourcée vérifiée |
| T3 (alertes n8n) | ✅ | ✅ (inchangé) |
| T5 (CI) | 🟡 jamais poussé | ✅ CI verte sur `main` |

**CV : 5/6 → 6/6.** Bloc prêt dans `DOCS/plans/cv-embellissement-scope.md` § « Version À ENVOYER MAINTENANT — 6/6 ».

## Décisions / trouvailles notables

- **v2 (JSON Schema) ne classe pas mieux que v1** — macro-F1 urgence 0,69 vs 0,63 ; action 0,50 vs 0,45. L'intérêt de v2 = fiabilité du format (0 parse cassé), pas la qualité. Décision d'archi tranchée par la mesure.
- Angles morts du classifieur : classe `moyenne` (urgence) fuit vers `faible` ; classe `aucune` (action) jamais prédite (F1 0,00 des 2 côtés).
- **Docker Hub CDN cassé sur cette machine** (`EOF` CloudFront sur `pgvector/pgvector:pg16`, comme le 04-09). Contourné : image `jarvis-pgvector:local` = `postgres:16` (cache) + pgvector 0.8.0 compilé depuis GitHub. Le `docker-compose.yml` prod pointe déjà `pgvector/pgvector:pg16` mais le redeploy Coolify du service postgres n'est pas confirmé.
- RAG validé sur **corpus PoC de 5 sessions** ; Redis e-mails vide en local → synthèses e-mails non exercées. Rang 1 partout = la similarité discrimine bien, mais chiffre non discriminant tant que le corpus est petit.
- STATUS.md périmé (bloqué à `8ef96cb`, HEAD `913ec35`) — `/close` dû.

## Reste à faire (côté utilisateur, hors chemin critique CV)

1. **n8n prod** : sur les workflows `[PROD]`, mettre 3 champs *To* en `={{ $env.CLIENT_SUMMARY_RECIPIENT || $env.SUMMARY_RECIPIENT_EMAIL }}` (`reminders` ×2, `smart-agent` ×1 avec `recipient_email ||` devant), **et** renseigner `CLIENT_SUMMARY_RECIPIENT` dans l'env Coolify du service `n8n` (sinon e-mails en échec + flood d'alertes error-handler).
2. **Env Coolify** : compléter `CLIENT_GMAIL`, `CLIENT_CR_RECIPIENT`, `OPENWEATHER_API_KEY`, `CLIENT_CALENDAR_ID` sur le service `n8n` + redeploy (applique aussi le pin `2.22.5` et l'image pgvector).
3. **reminders** : `Save successful executions = false` dans les settings du workflow pour arrêter le bruit d'historique ; envisager cadence 10 min plutôt que 5.
4. **Optionnel** : repeupler Redis `emails_structured` (relancer les classifiers prod) → réingérer → rejouer `eval/rag/run_eval.py` pour un hit rate sur corpus réel.
5. **Optionnel** : ouvrir une PR pour exercer le trigger `pull_request` de la CI (T5 strict).
6. **`/close`** pour resynchroniser STATUS.md et le PRD.

## Points de vigilance CV (défense entretien)

1. Le pré-filtre mots-clés juridiques + la catégorisation via Graph API = **Outlook only**. Gmail = exclusion newsletters + classification + synthèse.
2. « RAG sur synthèses d'e-mails » = vrai au niveau code/ingestion ; l'éval de référence n'a porté que sur les résumés de session.
3. Le RAG n'est **pas** encore servi en prod : store provisionné, retrieval validé en local, bascule prod = dernière étape. Ne pas dire qu'il sert des utilisateurs.
4. Ne jamais réintroduire « < 1s Realtime » (bridge désactivé, latences 3–5 s), « Anthropic Claude API » comme composant produit, « agents LangChain » câblés, « historique conversations PostgreSQL ».

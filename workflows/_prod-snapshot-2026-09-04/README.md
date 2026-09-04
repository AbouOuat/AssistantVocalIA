# Snapshots prod n8n — 2026-09-04 (avant Étape 0 pt 2 + Étape 1 Path B)

Copies intégrales (`GET /api/v1/workflows/{id}`) des 2 classifiers v2 **avant** :
- désactivation de leur `scheduleTrigger` (Étape 0 pt 2, appliqué en prod le 2026-09-04)
- réécriture Path B (chainLlm → httpRequest json_schema, pas encore importée en prod)

| Fichier | id n8n | webhook |
|---|---|---|
| `gmail-email-classifier-v2.PROD-avant-2026-09-04.json` | `C7DBtxGSKMfLHG5F` | `email-classifier-v2` |
| `outlook-email-classifier-v2.PROD-avant-2026-09-04.json` | `MShBDLvSP9pjzHmr` | `outlook-email-classifier-v2` |

## Rollback (revenir à l'état prod du 2026-09-04 matin)

```
PUT /api/v1/workflows/{id}
body = { name, nodes, connections, settings:{executionOrder:"v1"} }  (extraits de ce fichier ;
        settings d'origine avait aussi binaryMode:"separate" → non accepté par le PUT, sans impact)
```

Le `scheduleTrigger` de ces snapshots n'a PAS `disabled:true` → rejouer ce PUT réactive le cron v2.

---

## post-pathb-import/ — état prod APRÈS import Path B (2026-09-04 ~11:14)

`gmail-email-classifier-v2.PROD.json` / `outlook-email-classifier-v2.PROD.json` : état réellement
déployé après le `PUT` Path B (nodes LangChain retirés, node `OpenAI - Classification (JSON Schema)`
httpRequest + `response_format json_schema`, cred header-auth `F99p27Ao9ucj5aeX`, schedule `disabled`).

Test live Gmail v2 (`POST /webhook/email-classifier-v2 {limit:1}`, exec `27355`) : **success**, tous
les nodes OK, le node OpenAI renvoie `{"emails":[],"global_summary":"Aucun email à classer."}`
(JSON strict, parsé sans regex). 0 non-lu dans la fenêtre 8h → pas de synthèse réelle envoyée.

⚠️ Vu au passage : `process.env.CLIENT_GMAIL` / `CLIENT_SUMMARY_RECIPIENT` **vides dans le conteneur n8n
prod** (`summary_sent_to: ""`). À renseigner dans l'env Coolify (déjà sur la checklist Étape 0/6).

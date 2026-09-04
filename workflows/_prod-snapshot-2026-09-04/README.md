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

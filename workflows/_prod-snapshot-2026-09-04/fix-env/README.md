# Snapshots avant fix $env (2026-09-04)

État prod des 5 workflows **avant** la conversion `process.env.X` -> `$env` (helper `envv`)
dans leurs Code nodes `Configuration` / `Formater alerte`.

Contexte : n8n 2.22.5 — `process.env` est vide dans les Code nodes, `$env` fonctionne.
Vérifié : toutes les vars Coolify sont injectées (`$env.CLIENT_*`, `OPENWEATHER_API_KEY`,
`N8N_BLOCK_ENV_ACCESS_IN_NODE=false`).

## Rollback (par workflow)

`PUT /api/v1/workflows/{id}` avec `{name, nodes, connections, settings}` où le node ciblé
reprend le `jsCode` de ce snapshot, et `settings` = `{executionOrder:"v1"}` (error-handler)
ou `{executionOrder:"v1", errorWorkflow:"j8OJ3Tk1T5hb0fhw"}` (les 4 classifiers).

| id | workflow | node |
|---|---|---|
| j8OJ3Tk1T5hb0fhw | error-handler | Formater alerte |
| C7DBtxGSKMfLHG5F | gmail-email-classifier-v2 | Configuration |
| MShBDLvSP9pjzHmr | outlook-email-classifier-v2 | Configuration |
| LHSqm0Ue2Vib8LjJ | gmail-email-classifier | Configuration |
| kb9TuIiGANBjbk3s | outlook-email-classifier | Configuration MVP |

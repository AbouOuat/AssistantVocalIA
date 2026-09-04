# Snapshots pré-affectation Error Workflow (T3, 2026-09-04)

État des 16 workflows actifs **avant** ajout de `settings.errorWorkflow = j8OJ3Tk1T5hb0fhw`
(error-handler). Aucun n'avait `errorWorkflow` auparavant (`None`).

## Rollback (retirer l'alerte d'un workflow)

`PUT /api/v1/workflows/{id}` avec `{name, nodes, connections, settings}` où `settings`
= `{ "executionOrder": "v1" }` (sans la clé `errorWorkflow`). Les `nodes`/`connections`
de ces fichiers sont l'état prod du 2026-09-04.

Pour tout retirer d'un coup : rejouer `scratchpad` `affect_error_workflow.py` en remplaçant
`new_settings["errorWorkflow"] = EH` par un `pop`.

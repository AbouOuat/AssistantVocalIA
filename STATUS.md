# STATUS — Jarvis V2

> Maintenu par `/close`. Ne pas éditer à la main.

<!-- close:active -->
**Dernière étape** : Session 2026-09-07 — chantier embellissement CV. T5 CI GitHub Actions verte (fix image `pgvector/pgvector:pg16` + test e2e Quick Actions 5→6). T1 éval classifieur v1 vs v2 sur 40 e-mails annotés (`DOCS/reports/classifier-eval-2026-09-07.md`) → v1 ≥ v2, `WORKFLOW_VERSION=v1` confirmé. T2 éval RAG réelle contre pgvector 0.8.0 (`DOCS/reports/rag-eval-2026-09-07.md`) → hit rate @5 100 %, rang 1 sur 5/5, réponse sourcée vérifiée. Purge du dernier e-mail hardcodé (`reminders`, `smart-agent`) → `CLIENT_SUMMARY_RECIPIENT`. 5 commits `0861c94`→`913ec35`, poussés, CI verte.
**Prochaine étape recommandée** : `/prime` à la reprise. Côté user (hors chemin critique CV) : (1) env Coolify service `n8n` — `CLIENT_GMAIL`, `CLIENT_SUMMARY_RECIPIENT`, `CLIENT_CR_RECIPIENT`, `OPENWEATHER_API_KEY`, `CLIENT_CALENDAR_ID` + redeploy (applique pin `2.22.5` + image pgvector) ; (2) 3 champs *To* des workflows `[PROD]` `reminders` (×2) et `smart-agent` → `$env.CLIENT_SUMMARY_RECIPIENT` ; (3) `Save successful executions = false` sur `reminders`, cadence 10 min ; (4) optionnel : repeupler Redis `emails_structured` → réingérer → rejouer `eval/rag/run_eval.py` sur corpus réel ; (5) optionnel : PR pour exercer le trigger `pull_request` de la CI.
**Dernier commit reflété** : `94e290b` — docs(status): session 2026-09-07

## Chantier embellissement CV (DOCS/plans/cv-embellissement-scope.md)

- **Étape 0** (pin n8n 2.22.5, cron unique, `WORKFLOW_VERSION=v1`, purge hardcodé) : ✅ repo. ⬜ reste env Coolify + réimport prod des 2 workflows.
- **T1** — sortie JSON Schema (Path B) : ✅ prod. **Éval** : ✅ 40 e-mails, v1 macro-F1 0,69 urgence / 0,50 action ≥ v2 → moteur = v1, v2 = robustesse format.
- **T2** — RAG pgvector : ✅ éval réelle (hit@5 100 %, rang 1 sur 5/5, corpus PoC 5 sessions). ⬜ chiffre discriminant = corpus e-mails à repeupler ; ⬜ bascule prod (redeploy postgres + branchement outil).
- **T3** — alertes e-mail échec workflow n8n : ✅ end-to-end, 16 workflows. Bonus : throttling Redis.
- **T5** — CI GitHub Actions : ✅ verte sur `main`. ⬜ trigger `pull_request` non encore exercé.
- **CV** : bloc « Version À ENVOYER MAINTENANT — 6/6 » prêt dans `DOCS/plans/cv-embellissement-scope.md`. `.docx` relu et validé côté user (`CV_OUATTARA_..._TechLead_IA_FINAL_AgentsIA_07092026_v2.docx`).

## Refactoring Intent Router (audit 2026-06-23 → DOCS/plans/refactoring-plan.md)

- **Phase A — config client centralisée + nettoyage** : ✅ (commit `6c0d30d`)
- **Phase B — outils LLM (intent router = function calling)** : ✅ (15 tools)
- **Phase C — workflows n8n manquants** : ✅ côté repo
- **Phase D — import prod + tests** : 🟡 partiel — KO/suspects : `morning-briefing` (injoignable), Gmail `email-classifier-v2` (inactif ?), `outlook-read-inbox` ignore `folder`

## Historique récent

- 2026-09-07 — Chantier CV : T5 CI verte, T1 éval classifieur (v1 ≥ v2), T2 éval RAG (hit@5 100 %, rang 1), purge e-mail hardcodé. Commits `0861c94`→`913ec35`. Recap : `RECAP_SESSION_2026-09-07.md`.
- 2026-06-27 — Campagne tests prod (rapport : DOCS/reports/tests-jarvis-2026-06-27.md) + 3 fixes (morning-briefing calendar_id, WORKFLOW_VERSION v2, scrollbar QuickActions)
- 2026-06-24 — Refactoring Phases A+B+C (commit `6c0d30d`) : config client, tools intent router, workflows v2 LangChain, toggle version IHM
- 2026-06-25 — Fix Outlook inbox : dossier dynamique (inbox/spam/deleteditems/...), mode:id, routage "mes mails" direct sans cache
- 2026-06-25 — Agenda LLM : dates libres date_debut/date_fin + filtre JS n8n + retour JSON curé
<!-- /close:active -->

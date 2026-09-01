# STATUS — Jarvis V2

> Maintenu par `/close`. Ne pas éditer à la main.

<!-- close:active -->
_Bloc mis à jour manuellement le 2026-09-01 (audit de reprise après ~2 mois de pause), pas via `/close`. Un `/close` reste à faire pour clôturer la session du 2026-06-27._

**Dernière étape** : Session 2026-06-27 — campagne de tests fonctionnels prod (13 scénarios : 9 OK / 2 partiels / 2 KO), fixes morning-briefing (calendar_id + JSON), WORKFLOW_VERSION défaut v2, scrollbar QuickActions
**Prochaine étape recommandée** : vérifier REPO ↔ n8n PROD, puis finir Phase D du refactoring (importer/activer `morning-briefing` + Gmail `email-classifier-v2` en prod, corriger le champ `folder` de `outlook-read-inbox`)
**Dernier commit reflété** : `8ef96cb` — fix: masquer scrollbar horizontale sur QuickActions

## Refactoring Intent Router (audit 2026-06-23 → DOCS/plans/refactoring-plan.md)

- **Phase A — config client centralisée + nettoyage** : ✅ (commit `6c0d30d` — bloc `CLIENT_*` dans config.py/.env.example/docker-compose, `_handle_n8n_command_legacy` supprimé, webhook agenda renommé)
- **Phase B — outils LLM (intent router = function calling)** : ✅ (`analyser_emails_*`, `consulter_derniere_analyse`, `lire_inbox_outlook`, `lire_agenda`, system prompt client-aware ; 15 tools)
- **Phase C — workflows n8n manquants** : ✅ côté repo (`outlook-read-inbox.json`, `google-calendar-read.json`, classifiers v2) — présence/activation prod à confirmer
- **Phase D — import prod + tests** : 🟡 partiel — actifs en prod : outlook-read-inbox, outlook-email-classifier-v2, google-calendar-read/create, gmail-draft, reminders, mémoire Redis ; KO/suspects : `morning-briefing` (injoignable), Gmail `email-classifier-v2` (inactif ?), `outlook-read-inbox` ignore `folder`

## Historique récent

- 2026-06-27 — Campagne tests prod (rapport : DOCS/reports/tests-jarvis-2026-06-27.md) + 3 fixes (morning-briefing calendar_id, WORKFLOW_VERSION v2, scrollbar QuickActions)
- 2026-06-24 — Refactoring Phases A+B+C (commit `6c0d30d`) : config client, tools intent router, workflows v2 LangChain, toggle version IHM
- 2026-06-25 — Fix Outlook inbox : dossier dynamique (inbox/spam/deleteditems/...), mode:id, routage "mes mails" direct sans cache
- 2026-06-25 — Agenda LLM : dates libres date_debut/date_fin + filtre JS n8n + retour JSON curé
- 2026-06-04 — Session debug : 11 workflows testés, 5 bugs corrigés, 5 scénarios démo validés
- 2026-06-03 — Déploiement prod VPS Hostinger + Coolify. Backend + frontend live.
- 2026-05-28 — `/design` : DESIGN.md créé — dark navy, indigo/cyan, orb 3 états
<!-- /close:active -->

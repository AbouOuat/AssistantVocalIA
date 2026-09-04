# n8n — alerte e-mail sur échec de workflow (T3)

## Principe

n8n déclenche le **Error Workflow** d'un workflow quand celui-ci échoue. On a un seul
error workflow partagé, `workflows/error-handler.json` :

`Error Trigger` → `Formater alerte` (Code) → `Gmail - Envoyer alerte`.

Destinataire : `process.env.CLIENT_CR_RECIPIENT` (sinon `CLIENT_SUMMARY_RECIPIENT`,
sinon `SUMMARY_RECIPIENT_EMAIL`). Aucun défaut identifiant — si tout est vide, aucun
e-mail n'est envoyé (log warning). ⇒ **ces variables doivent être renseignées dans
l'env Coolify du conteneur n8n.**

Contenu de l'alerte : nom + id du workflow, horodatage, nœud en échec, message d'erreur,
id d'exécution, lien.

## Déploiement (fait le 2026-09-04 via n8n API)

1. Import `error-handler.json` → workflow prod (credential Gmail re-liée : `ZO3kLaKLb2hdHVw5`
   « Gmail account »), puis activation.
2. Affectation comme **Error Workflow** sur les 16 workflows actifs (hors `error-handler`
   lui-même) : `PUT /api/v1/workflows/{id}` avec
   `settings = { executionOrder: "v1", errorWorkflow: "<error-handler-id>" }`.
3. Vérification : workflow jetable `_test-error-handler` (webhook → `throw`) affecté à
   l'error handler, POST du webhook → e-mail reçu, puis suppression du jetable.

## Rétablir / retirer

Pour retirer l'alerte d'un workflow : `PUT` avec `settings` sans la clé `errorWorkflow`.
Snapshots pré-affectation : `workflows/_prod-snapshot-2026-09-04/`.

## Limites connues / suites

- **Pas de throttling** : un workflow qui échoue en boucle enverra un e-mail par échec.
  Les crons sont hebdo et les webhooks à la demande → risque faible. Throttle Redis
  (1 e-mail / workflow / 15 min) = amélioration ultérieure.
- L'error handler n'alerte pas sur son propre échec (par conception n8n).

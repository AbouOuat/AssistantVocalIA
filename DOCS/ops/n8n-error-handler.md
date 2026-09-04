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

1. ✅ Import `error-handler.json` → **`j8OJ3Tk1T5hb0fhw`** (credential Gmail re-liée :
   `ZO3kLaKLb2hdHVw5` « Gmail account »), activé.
2. ✅ Affecté comme **Error Workflow** sur les **16 workflows actifs** (hors `error-handler`) :
   `PUT /api/v1/workflows/{id}` avec `settings = { executionOrder: "v1", errorWorkflow: "j8OJ3Tk1T5hb0fhw" }`.
   Snapshots pré-affectation : `workflows/_prod-snapshot-2026-09-04/t3-error-workflow/`.
3. ✅ Test : workflow jetable webhook→`throw` affecté à l'error handler, POST webhook → exécution
   `error` → **error-handler déclenché** (`Error Trigger` → `Formater alerte` exécutés, `status: success`),
   puis jetable supprimé.
   ⚠️ **E-mail non envoyé** : `Formater alerte` a renvoyé `[]` car `CLIENT_CR_RECIPIENT` /
   `CLIENT_SUMMARY_RECIPIENT` / `SUMMARY_RECIPIENT_EMAIL` sont **vides dans le conteneur n8n prod**.
   Le câblage est prouvé ; la livraison de l'e-mail marchera dès que l'une de ces variables sera
   renseignée dans l'env Coolify + redeploy n8n.

## Rétablir / retirer

Pour retirer l'alerte d'un workflow : `PUT` avec `settings` sans la clé `errorWorkflow`.
Snapshots pré-affectation : `workflows/_prod-snapshot-2026-09-04/`.

## Limites connues / suites

- **Pas de throttling** : un workflow qui échoue en boucle enverra un e-mail par échec.
  Les crons sont hebdo et les webhooks à la demande → risque faible. Throttle Redis
  (1 e-mail / workflow / 15 min) = amélioration ultérieure.
- L'error handler n'alerte pas sur son propre échec (par conception n8n).

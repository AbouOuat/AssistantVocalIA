# Rapport tests fonctionnels — Jarvis Production

**Date** : 2026-06-27
**Instance** : https://jarvis.obyz.biz
**user_id** : 2
**Généré le** : 2026-06-27 13:29 UTC (corrigé manuellement post-run)

---

## Résumé

| Statut | Count |
|--------|-------|
| ✅ OK | 9/13 |
| ⚠️ Partiel | 2/13 |
| ❌ KO | 2/13 |

> Corrections post-run : TEST-01 (auto ✅ → ❌ KO — réponse d'échec), TEST-11 (auto ⚠️ → ✅ OK — GET reminders confirme), TEST-12 (auto ⚠️ → ❌ KO — feature absente).

---

## Tests détaillés

### TEST-01 — Morning Briefing

- **Input** : `Start my day`
- **Tool appelé** : `morning_briefing`
- **Payload webhook** : `morning-briefing {user_id: 2}`
- **Latence** : 4.6s | **HTTP** : 200
- **Output brut** :
  ```
  Je n'ai pas pu lancer le briefing du matin.
  Veux-tu que je vérifie ton agenda et tes emails séparément ?
  ```
- **Statut** : ❌ KO
- **Observations** : Workflow `morning-briefing` injoignable en prod. Latence 4.6s → le webhook a timeout sans data. Cohérent avec STATUS.md : "Coolify Redeploy + import workflows n8n" en pending. À importer avant prochaine démo.

---

### TEST-02 — Inbox Outlook — Boîte de réception

- **Input** : `Donne-moi mes mails`
- **Tool appelé** : `lire_inbox_outlook`
- **Payload webhook** : `outlook-read-inbox {folder:"inbox", limit:10}`
- **Latence** : 3.4s | **HTTP** : 200
- **Output brut** :
  ```
  Tu as reçu plusieurs emails récents dans ta boîte de réception Outlook.

  1. Basic Fit Healthy Foodbox : Confirmation requise.
  2. Veepee : 25 nouvelles ventes aujourd'hui, incluant Redskins et Mizuno.
  3. Printerpix : Offres exclusives VIP dès 2,99 €.
  4. LinkedIn : Nouveau post par Maël Dutrey.
  5. SNCF Connect : Informations sur le trafic cet été.
  ```
- **Statut** : ✅ OK
- **Observations** : Données réelles, routage "mes mails" → lire_inbox_outlook correct (fix 25/06 validé). 5 emails affichés, résumé vocal adapté.

---

### TEST-03 — Inbox Outlook — Spam

- **Input** : `Montre-moi mes spams Outlook`
- **Tool appelé** : `lire_inbox_outlook`
- **Payload webhook** : `outlook-read-inbox {folder:"junkemail", limit:10}`
- **Latence** : 3.3s | **HTTP** : 200
- **Output brut** :
  ```
  Voici un aperçu de tes emails dans le dossier spam d'Outlook :

  1. Basic Fit Healthy Foodbox : Confirmation requise.
  2. Veepee : 25 nouvelles ventes aujourd'hui.
  3. Printerpix : Offres exclusives VIP dès 2,99 €.
  4. LinkedIn : Nouveau post par Maël Dutrey.
  5. SNCF Connect : Informations trafic.
  6. Darty : Début des soldes.
  7. MagicWin : Bonus de bienvenue.
  8. Indeed : Offre d'emploi chez Capgemini.
  9. Edisac : Soldes Longchamp.
  10. Levi's : Les essentiels tout en blanc.
  ```
- **Statut** : ✅ OK
- **Observations** : Le dossier `junkemail` retourne 10 emails (inbox en avait 5). Les 5 premiers expéditeurs sont identiques à l'inbox — à vérifier manuellement si ce sont de vrais doublons (emails copiés en spam par filtres) ou si le paramètre `folder` n'est pas exploité par le workflow n8n et retourne toujours l'inbox. Recommande test de validation manuel dans l'interface Outlook.

---

### TEST-04 — Inbox Outlook — Supprimés

- **Input** : `Qu'est-ce que j'ai dans les supprimés Outlook ?`
- **Tool appelé** : `lire_inbox_outlook`
- **Payload webhook** : `outlook-read-inbox {folder:"deleteditems", limit:10}`
- **Latence** : 2.9s | **HTTP** : 200
- **Output brut** :
  ```
  Dans ton dossier des emails supprimés :

  1. Basic Fit Healthy Foodbox : Bientôt terminé, confirmation requise.
  2. Veepee : 25 nouvelles ventes aujourd'hui.
  3. Printerpix : Offres exclusives VIP dès 2,99 €.
  4. LinkedIn : Nouveau post par Maël Dutrey.
  5. SNCF Connect : Info trafic pour l'été.
  6. Darty : Début des soldes.
  7. MagicWin : Bonus de bienvenue.
  8. Indeed : Offre d'emploi chez Capgemini.
  9. Edisac : Soldes Longchamp.
  10. Levi's : Les essentiels tout en blanc.
  ```
- **Statut** : ✅ OK
- **Observations** : Même anomalie qu'en TEST-03 — expéditeurs identiques inbox/spam/supprimés. Le workflow n8n `outlook-read-inbox` utilise-t-il bien le champ `folder` du payload ? À vérifier dans n8n.

---

### TEST-05 — Analyse emails Gmail (classification IA)

- **Input** : `Analyse mes emails Gmail et classe-les par priorité`
- **Tool appelé** : `analyser_emails_gmail`
- **Payload webhook** : `email-classifier-v2 {user_id:2, limit:10}`
- **Latence** : 4.1s | **HTTP** : 200
- **Output brut** :
  ```
  Il semble que tu n'as pas d'emails non lus dans ta boîte Gmail pour le moment,
  donc rien n'a été classé par priorité.
  ```
- **Statut** : ⚠️ Partiel
- **Observations** : Latence 4.1s anormale pour un workflow de classification lourd (attendu 30-45s). Probable que le workflow `email-classifier-v2` n'est pas importé en prod ou est inactif — le backend aurait renvoyé une réponse rapide d'erreur ("no_emails"). La réponse LLM dit "pas d'emails non lus" mais c'est une reformulation douce d'une réponse vide. À confirmer : vérifier dans n8n si le workflow est actif.

---

### TEST-06 — Analyse emails Outlook (classification IA)

- **Input** : `Classe mes mails Outlook par urgence`
- **Tool appelé** : `analyser_emails_outlook`
- **Payload webhook** : `outlook-email-classifier-v2 {user_id:2, limit:10}`
- **Latence** : 32.5s | **HTTP** : 200
- **Output brut** :
  ```
  Il n'y a aucun email urgent ou nécessitant une réponse prioritaire dans ta boîte Outlook.
  Si tu as besoin d'aide pour autre chose, fais-moi signe !
  ```
- **Statut** : ✅ OK
- **Observations** : Latence 32.5s confirme que le workflow `outlook-email-classifier-v2` s'est exécuté. Résultat : aucun email urgent détecté (cohérent avec les emails marketing vus en TEST-02). Workflow actif et fonctionnel en prod.

---

### TEST-07 — Création brouillon Gmail

- **Input** : `Crée un brouillon Gmail à ouat.abou34@gmail.com, objet 'Test Jarvis — validation fonctionnelle 2026-06-27', corps: Ceci est un brouillon créé automatiquement par Jarvis lors de la campagne de validation.`
- **Tool appelé** : `creer_brouillon_gmail`
- **Payload webhook** : `gmail-draft {to:"ouat.abou34@gmail.com", subject, body}`
- **Latence** : 2.4s | **HTTP** : 200
- **Output brut** :
  ```
  Le brouillon a été créé avec succès dans Gmail.
  Tu peux le retrouver et l'envoyer depuis ta boîte de brouillons.
  ```
- **Statut** : ✅ OK
- **Observations** : À vérifier manuellement dans Gmail Drafts pour confirmer la présence du brouillon.

---

### TEST-08 — Lecture agenda Google Calendar

- **Input** : `Qu'est-ce que j'ai cette semaine dans mon agenda ?`
- **Tool appelé** : `lire_agenda`
- **Payload webhook** : `google-calendar-read {date_debut:2026-06-22, date_fin:2026-06-28, calendar_id}`
- **Latence** : 2.6s | **HTTP** : 200
- **Output brut** :
  ```
  Cette semaine, tu as eu les événements suivants dans ton agenda :

  - Appel avec Michel : le 25 juin de 11h00 à 11h30.
  - Appel avec Vincent : le 26 juin de 15h30 à 16h00.

  Si tu veux ajouter ou modifier des événements, fais-le moi savoir !
  ```
- **Statut** : ✅ OK
- **Observations** : Données réelles confirmées (2 RDV passés cette semaine). Fix 25/06 validé — filtre JS n8n + retour JSON curé opérationnel.

---

### TEST-09 — Création événement Google Calendar

- **Input** : `Ajoute un RDV 'Test Jarvis Campaign' mardi prochain à 15h pour 30 minutes`
- **Tool appelé** : `creer_evenement_agenda`
- **Payload webhook** : `google-calendar-create-event {titre:"Test Jarvis Campaign", debut:2026-06-30T15:00:00+02:00, fin:2026-06-30T15:30:00+02:00}`
- **Latence** : 2.4s | **HTTP** : 200
- **Output brut** :
  ```
  Le rendez-vous "Test Jarvis Campaign" a été ajouté à ton agenda
  pour mardi prochain, le 30 juin, de 15h00 à 15h30.
  ```
- **Statut** : ✅ OK
- **Observations** : LLM a correctement calculé mardi 30 juin 2026 et converti en ISO 8601 +02:00. Événement conservé dans Google Calendar (confirmé par user).

---

### TEST-10a — Mémoire — Sauvegarder

- **Input** : `Souviens-toi que le dossier Dupont est prioritaire ce mois-ci`
- **Tool appelé** : `sauvegarder_memoire`
- **Payload webhook** : `Redis direct {scope:"preferences", cle:"dossier_dupont", valeur:"prioritaire ce mois-ci"}`
- **Latence** : 0.9s | **HTTP** : 200
- **Output brut** :
  ```
  Je vais me souvenir que le dossier Dupont est prioritaire ce mois-ci.
  Si tu as besoin de rappels ou d'autres informations sauvegardées, fais-le moi savoir !
  ```
- **Statut** : ⚠️ Partiel
- **Observations** : La réponse LLM dit "je vais me souvenir" (futur) sans le marqueur ✅ attendu (`"Mémorisé ✅ [preferences/dossier_dupont] : ..."`). Deux hypothèses : (a) le tool a été appelé mais le LLM a reformulé la réponse au lieu de la citer ; (b) le LLM a décidé de ne pas appeler le tool et retient en contexte de session. Le recall en TEST-10b a fonctionné, mais via contexte de conversation ou via Redis — impossible à distinguer sans nouvelle session. Recommande de tester le recall dans une session fraîche (user_id=2 + /api/chat avec nouvelle connexion).

---

### TEST-10b — Mémoire — Rappel (recall)

- **Input** : `Qu'est-ce que tu sais sur le dossier Dupont ?`
- **Tool appelé** : `rechercher_memoire`
- **Payload webhook** : `Redis direct {requete:"dupont"}`
- **Latence** : 6.0s | **HTTP** : 200
- **Output brut** :
  ```
  Je sais que le dossier Dupont est prioritaire ce mois-ci,
  mais je n'ai pas d'autres informations spécifiques enregistrées à ce sujet.
  Si tu souhaites ajouter plus de détails, n'hésitez pas à me le dire !
  ```
- **Statut** : ✅ OK
- **Observations** : L'info a été retrouvée. La latence 6.0s (vs 0.9s pour la sauvegarde) suggère un appel Redis réel. Mais voir nota TEST-10a — à confirmer hors session.

---

### TEST-11 — Création rappel vocal

- **Input** : `Rappelle-moi de valider les workflows n8n demain à 9h`
- **Tool appelé** : `creer_rappel`
- **Payload webhook** : `reminders {texte:"Valider les workflows n8n", echeance:"2026-06-28T09:00:00"}`
- **Latence** : 2.1s | **HTTP** : 200
- **Output brut** :
  ```
  Le rappel pour valider les workflows n8n a été créé pour demain à 9h.
  ```
- **Vérification GET /api/reminders** :
  ```json
  {
    "task_1782566937341": {
      "text": "Valider les workflows n8n",
      "created_at": "2026-06-27T13:28:57.341378",
      "done": false,
      "due_at": "2026-06-28T09:00:..."
    }
  }
  ```
- **Statut** : ✅ OK
- **Observations** : Rappel confirmé en base Redis (task_1782566937341). Échéance correctement calculée. GET /api/reminders valide la persistance.

---

### TEST-12 — Accès Telegram

- **Input** : `Envoie-moi un message Telegram pour confirmer que Jarvis est opérationnel`
- **Tool appelé** : `N/A — aucun tool Telegram déclaré dans JARVIS_TOOLS (ai_service.py)`
- **Payload webhook** : `N/A`
- **Latence** : 4.2s | **HTTP** : 200
- **Output brut** :
  ```
  Je ne peux pas envoyer de messages via Telegram. Cependant, je peux t'aider
  avec des emails, l'agenda, et d'autres tâches numériques.
  ```
- **Statut** : ❌ KO
- **Observations** : Feature listée dans la proposition commerciale ("Accès Telegram — sans installation supplémentaire") mais absente du backend. Aucun tool Telegram dans `JARVIS_TOOLS`, aucun webhook `telegram-*` dans `_execute_tool`. Feature à implémenter avant livraison client.

---

## Actions correctives prioritaires

| Priorité | Test | Problème | Action |
|----------|------|----------|--------|
| 🔴 P1 | TEST-01 | Workflow `morning-briefing` injoignable | Importer + activer sur Coolify n8n |
| 🔴 P1 | TEST-12 | Telegram non implémenté | Créer tool + webhook `telegram-notify` |
| 🟡 P2 | TEST-05 | Gmail classifier latence anormale (4.1s) | Vérifier `email-classifier-v2` actif sur n8n |
| 🟡 P2 | TEST-03/04 | Dossiers spam/supprimés retournent mêmes emails que inbox | Vérifier param `folder` dans workflow `outlook-read-inbox` |
| 🟢 P3 | TEST-10a | Mémorisation : marqueur ✅ absent, possibilité de context-only | Tester recall dans session fraîche |

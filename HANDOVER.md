# Handover — Session Jarvis 2026-06-04

## Pour démarrer la prochaine session

Dis à Claude : **"Reprends le projet Jarvis — /prime"**

---

## État au moment du handover

### ✅ Tout ce qui fonctionne (validé 2026-06-04)

| Feature | Preuve |
|---|---|
| Backend API | /api/config → 200, user_id=2 |
| Frontend | jarvis.obyz.biz ✅ |
| Morning briefing | Météo + Calendar + Gmail (noms expéditeurs corrects) |
| Gmail classifier | ✅ (retourne "" si 0 unread = normal) |
| Outlook classifier | ✅ (synthèse + email envoyé) |
| **gmail-search** | ✅ FIXÉ — from/subject/date remplis |
| Outlook search | ✅ tous champs OK |
| Gmail draft | ✅ draft_id créé |
| **send-outlook-email** | ✅ testé et fonctionnel |
| Google Calendar | ✅ event_id créé |
| **Reminders** | ✅ Redis + email n8n + function calling end-to-end |
| **smart-agent** | ✅ action_plan + email_sent |
| Telegram bot | ✅ actif |
| **Mémoire (lecture + écriture)** | ✅ sauvegarder_memoire + rechercher_memoire |
| Function calling 12 tools | ✅ tous validés via /api/chat |

### 🎯 Prochaine étape prioritaire

**Enregistrer la vidéo démo** — 5 scénarios validés bout en bout :

1. `"Lance mon briefing du matin"` → morning_briefing ✅
2. `"T'as des trucs urgents dans mes mails ?"` → classifier + lire_emails ✅
3. `"Rappelle-moi d'appeler Jean dans 1h"` → creer_rappel (Redis + email) ✅
4. `"Ajoute un RDV 'Demo Jarvis' demain à 10h"` → creer_evenement_agenda ✅
5. `"Souviens-toi que je préfère mes briefings à 8h"` → sauvegarder_memoire ✅

---

## Bugs corrigés cette session

| Bug | Cause | Fix |
|---|---|---|
| smart-agent 401 | Credential mal assigné dans n8n | Réimport workflow |
| gmail-search champs vides | n8n Gmail v2 expose `m.From`/`m.Subject` (majuscule) pas `m.from` | Fix code node n8n |
| morning-briefing "Inconnu" | Même cause que gmail-search | Fix `d.From` |
| creer_rappel ne s'exécutait pas | Règle de confirmation trop large dans system prompt | Exemption rappels/events |
| creer_rappel UnboundLocalError | `from datetime import datetime` dans `_execute_tool` shadowait le module global | Suppression import local |
| Cascade 500 après exception | User message ajouté au contexte sans assistant response en cas d'erreur | Placeholder assistant + try/except tool_executor |
| Mémoire hallucinée | Aucun tool d'écriture mémoire | Ajout tool `sauvegarder_memoire` |

---

## Informations techniques clés

**N8N_API_KEY** : dans `C:\dev\projet-jarvis\.env`
**Credential OpenAI dans n8n** : ID `F99p27Ao9ucj5aeX`, nom "Header Auth account"
**Credential Gmail** : ID `ZO3kLaKLb2hdHVw5`, nom "Gmail account"
**Credential Outlook** : ID `ac71E7NKWmX5nq8h`, nom "Connect_Outlook_ouat"
**Credential Google Calendar** : ID `gcalendar-creds`

**Dernier commit** : `2faf95b` — fix UnboundLocalError datetime
**Branch** : main, à jour avec origin/main

---

## Architecture résumée

```
User (voix/texte)
    ↓ WebSocket /ws  (ou HTTP /api/chat)
FastAPI backend — GPT-4o + function calling
    ↓ 12 tools
n8n webhooks (11 workflows actifs) / Redis (tasks · preferences · projects · context)
    ↓
Gmail · Outlook · Google Calendar · Rappels · Mémoire · Smart Agent
```

## Note n8n — chemins webhooks

| Tool | Path n8n |
|---|---|
| morning_briefing | `morning-briefing` |
| creer_evenement_agenda | `calendar-create-event` (pas `google-calendar-create-event`) |
| classifier_emails_gmail | `email-classifier` |
| classifier_emails_outlook | `outlook-email-classifier` |
| rechercher_emails (Gmail) | `gmail-search` |
| rechercher_emails (Outlook) | `outlook-search` |
| creer_brouillon_gmail | `gmail-draft` |
| envoyer_email_outlook | `send-outlook-email` |
| creer_rappel | `reminders` |
| analyser_notes | `smart-agent` |

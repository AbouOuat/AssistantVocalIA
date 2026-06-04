# Récapitulatif Session — Jarvis V2 (2026-06-04)

## Objectif de la session
Test global de tous les workflows, correction des bugs bloquants, validation des 5 scénarios démo vidéo.

---

## 1. Tests globaux — résultats initiaux

| Workflow | État initial | Résultat |
|---|---|---|
| morning-briefing | ✅ | Fonctionnel, mais "Inconnu" pour les noms expéditeurs |
| gmail-email-classifier | ✅ | OK |
| outlook-email-classifier | ✅ | OK |
| **gmail-search** | ⚠️ | `from`/`subject`/`date` vides |
| outlook-search | ✅ | OK |
| gmail-draft | ✅ | OK |
| send-outlook-email | ❌ jamais testé | OK après test |
| google-calendar-create-event | ✅ | OK (path = `calendar-create-event`) |
| reminders | ✅ webhook | Jamais appelé via function calling |
| **smart-agent** | ⚠️ 401 | Credential réassigné → OK |
| telegram-bot | ✅ actif | - |

---

## 2. Bugs corrigés

### Bug 1 — smart-agent 401
**Cause :** Credential OpenAI mal assigné dans n8n après dernier réimport.
**Fix :** Réassignation du credential `F99p27Ao9ucj5aeX` dans le noeud OpenAI.
**Résultat :** `action_plan` + `email_sent: true` ✅

### Bug 2 — gmail-search champs vides (`from`, `subject`, `date`)
**Cause :** Le noeud Gmail v2 de n8n expose les headers avec **majuscule** (`m.From`, `m.Subject`) et la date en timestamp ms via `m.internalDate`, pas sous `m.from`/`m.subject`/`m.date`.
**Fix :** Mise à jour du code node n8n via API Python :
```javascript
const fromRaw = m.From || m.from || '';
const subject = m.Subject || m.subject || '(sans objet)';
const date = m.internalDate ? new Date(parseInt(m.internalDate)).toISOString() : '';
```
**Résultat :** Champs remplis correctement ✅

### Bug 3 — morning-briefing affichait "Inconnu"
**Cause :** Même cause que gmail-search (`d.from` au lieu de `d.From`).
**Fix :** Même correctif appliqué au noeud "Formater le briefing".
**Résultat :** Noms expéditeurs corrects dans le briefing ✅

### Bug 4 — `creer_rappel` ne s'exécutait jamais
**Cause :** Le system prompt classait "créer une tâche" comme action irréversible nécessitant confirmation. GPT-4o disait "C'est noté !" sans appeler le tool.
**Fix :** Mise à jour du system prompt — rappels et events agenda exemptés de la règle de confirmation.
```
Exception : lire, lister, résumer, créer un rappel, créer un événement agenda, mémoriser
→ agis directement sans demander.
```

### Bug 5 — `creer_rappel` UnboundLocalError
**Cause :** `from datetime import datetime` à l'intérieur de `_execute_tool` (dans le bloc `creer_evenement_agenda`) rendait `datetime` **local à toute la fonction** en Python — y compris les blocs précédents comme `creer_rappel` qui utilisaient `datetime.utcnow()`.
**Fix :** Suppression de l'import local redondant (déjà importé ligne 10 du fichier).
**Note :** Ce bug existait dès l'origine mais n'était jamais déclenché car le tool n'était jamais appelé (Bug 4 masquait Bug 5).

### Bug 6 — Cascade de 500 après une erreur
**Cause :** `context.add_message("user", message)` est appelé avant le traitement. En cas d'exception, le user message reste dans le contexte sans assistant response, créant deux messages user consécutifs invalides pour l'API OpenAI.
**Fix :**
- Ajout d'un message assistant placeholder dans le `except` du handler HTTP
- Ajout try/except autour de chaque `tool_executor` dans `chat_completion_with_tools`

### Bug 7 — Mémoire hallucinée
**Cause :** `JARVIS_TOOLS` ne contenait que `rechercher_memoire` (lecture). Quand Jarvis disait "je vais mémoriser", il n'appelait aucun tool — pur hallucination.
**Fix :** Ajout du tool `sauvegarder_memoire` avec écriture réelle dans Redis :
```python
await memory_service.set(user_id, scope, cle, valeur)
```

---

## 3. Améliorations apportées

| Composant | Changement |
|---|---|
| `backend/services/ai_service.py` | +1 tool `sauvegarder_memoire`, system prompt confirmation rule, try/except tool_executor, import logging |
| `backend/main.py` | Handler `sauvegarder_memoire`, fix UnboundLocalError datetime, placeholder context sur erreur |
| `workflows/gmail-search.json` | Fix `m.From`/`m.Subject`/`internalDate` |
| `workflows/morning-briefing.json` | Fix `d.From` pour noms expéditeurs |

---

## 4. Validation scénarios démo

Tous testés via `/api/chat` (HTTP, user_id=2, GPT-4o function calling) :

| # | Phrase naturelle | Tool appelé | Vérification |
|---|---|---|---|
| 1 | "Lance mon briefing du matin" | `morning_briefing` | Météo 20°C + 5 events + emails ✅ |
| 2 | "T'as des trucs urgents dans mes mails ?" | `classifier_emails_gmail` + `lire_emails_en_memoire` | "Aucun urgent" ✅ |
| 3 | "Rappelle-moi d'appeler Jean dans 1 heure" | `creer_rappel` | Redis `task_xxx` créé + email n8n reçu ✅ |
| 4 | "Ajoute un RDV 'Demo Jarvis' demain à 10h" | `creer_evenement_agenda` | Google Calendar event créé ✅ |
| 5 | "Souviens-toi que je préfère mes briefings à 8h" | `sauvegarder_memoire` | Rappelé dans la même session ✅ |

---

## 5. État prod final

- **URL** : https://jarvis.obyz.biz
- **Backend** : FastAPI + Uvicorn, user_id=2, 12 tools function calling
- **n8n** : 11 workflows actifs sur https://n8n.obyz.biz
- **Dernier commit** : `2faf95b` sur `main`
- **Infra** : Docker Compose + nginx + Coolify (VPS Hostinger KVM2)

---

## 6. Prochaine étape

**Enregistrer la vidéo démo** en utilisant les 5 scénarios validés ci-dessus depuis l'interface vocale de https://jarvis.obyz.biz.

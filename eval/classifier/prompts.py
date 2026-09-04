"""Constructions de prompt des classifieurs e-mail v1 et v2 — tenues en phase avec
les workflows n8n (`workflows/gmail-email-classifier*.json`).

v1 : appel OpenAI direct, response_format=json_object, JSON.parse(content).
v2 (post Path B 2026-09-04) : response_format=json_schema strict.

Le harness d'éval rejoue ces deux variantes sur un jeu d'e-mails annoté, hors
de la contrainte « quels e-mails sont non lus maintenant ».
"""
from __future__ import annotations

MODEL = "gpt-4o-mini"
TEMPERATURE = 0.1

# ── v1 ────────────────────────────────────────────────────────────────────────
V1_SYSTEM = (
    "Tu classes des emails. Réponds uniquement en JSON valide avec les champs: "
    "emails (array), global_summary (string max 5 lignes). Par email: id, "
    "urgence=haute|moyenne|faible, action=repondre|lire|relancer|classer|aucune, "
    "echeance_detectee=true|false, date_echeance=YYYY-MM-DD ou null, resume=une phrase, "
    "raison_urgence=une phrase ou vide. Critères urgence: date limite, convocation, "
    "délai, assignation, jugement, relance."
)


def v1_request(emails: list[dict]) -> dict:
    return {
        "model": MODEL,
        "temperature": TEMPERATURE,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": V1_SYSTEM},
            {"role": "user", "content": "Classe ces emails:\n\n" + _dumps(emails)},
        ],
    }


# ── v2 (Path B) ──────────────────────────────────────────────────────────────
V2_SYSTEM = V1_SYSTEM  # même consigne ; la différence v2 = schéma strict

V2_SCHEMA = {
    "name": "email_classification",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "emails": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string"},
                        "urgence": {"type": "string", "enum": ["haute", "moyenne", "faible"]},
                        "action": {
                            "type": "string",
                            "enum": ["repondre", "lire", "relancer", "classer", "aucune"],
                        },
                        "echeance_detectee": {"type": "boolean"},
                        "date_echeance": {"type": ["string", "null"]},
                        "resume": {"type": "string"},
                        "raison_urgence": {"type": "string"},
                    },
                    "required": [
                        "id", "urgence", "action", "echeance_detectee",
                        "date_echeance", "resume", "raison_urgence",
                    ],
                },
            },
            "global_summary": {"type": "string"},
        },
        "required": ["emails", "global_summary"],
    },
}


def v2_request(emails: list[dict]) -> dict:
    return {
        "model": MODEL,
        "temperature": TEMPERATURE,
        "response_format": {"type": "json_schema", "json_schema": V2_SCHEMA},
        "messages": [
            {"role": "system", "content": V2_SYSTEM},
            {"role": "user", "content": "Classe ces emails:\n\n" + _dumps(emails)},
        ],
    }


def _dumps(obj) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)

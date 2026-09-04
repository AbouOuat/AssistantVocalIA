"""Génère 3-5 sessions de test via le mécanisme normal de Session Summary
(backend.services.session_summary_service), pour peupler sessions/*.md — corpus
du RAG (T2, cf. DOCS/plans/cv-embellissement-scope.md).

Contexte : le mécanisme "Session Summary -> export .md" décrit dans CLAUDE.md
n'écrivait en réalité jamais de fichier (le handler WS ne faisait que renvoyer
le texte). session_summary_service.py comble cet écart ; ce script appelle
exactement cette même fonction de génération (vrai appel LLM, gpt-4o via
chat_completion_stream) sur des historiques de conversation plausibles, plutôt
que d'écrire des .md à la main.

Usage : python -m backend.scripts.generate_test_sessions
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services.session_summary_service import (  # noqa: E402
    export_session_summary_md,
    generate_session_summary,
)

USER_ID = 2  # démo hackathon, cf. tests-jarvis-2026-06-27.md

SCENARIOS = [
    {
        "title": "morning briefing agenda semaine",
        "history": [
            "user: Start my day",
            "assistant: Voici ton briefing : météo ensoleillée 22°C, 2 emails prioritaires, "
            "et 3 RDV aujourd'hui dont l'appel avec Michel à 11h.",
            "user: Qu'est-ce que j'ai cette semaine dans mon agenda ?",
            "assistant: Cette semaine : appel avec Michel le 25 juin 11h-11h30, "
            "appel avec Vincent le 26 juin 15h30-16h.",
            "user: Ajoute un RDV avec l'équipe produit mardi prochain à 15h pour 30 minutes",
            "assistant: Événement créé : réunion équipe produit, mardi 15h-15h30.",
        ],
        "memory": {
            "preferences": {"heure_briefing": "8h00", "ton": "concis"},
            "projects": {"jarvis_v2": "refactoring intent router en cours"},
            "tasks": {},
        },
    },
    {
        "title": "triage emails urgents dossier dupont",
        "history": [
            "user: Analyse mes emails Outlook et classe-les par urgence",
            "assistant: 1 email urgent détecté : le greffe demande confirmation de présence "
            "à l'audience du 12 septembre pour le dossier Dupont.",
            "user: Souviens-toi que le dossier Dupont est prioritaire ce mois-ci",
            "assistant: Mémorisé. Le dossier Dupont est marqué prioritaire.",
            "user: Prépare un brouillon de réponse au greffe confirmant ma présence",
            "assistant: Brouillon Gmail créé, à relire avant envoi.",
        ],
        "memory": {
            "preferences": {},
            "projects": {"dossier_dupont": "prioritaire ce mois-ci, audience le 12 septembre"},
            "tasks": {"repondre_greffe_dupont": "brouillon créé, à valider"},
        },
    },
    {
        "title": "preferences notifications et rappels",
        "history": [
            "user: Rappelle-moi de valider les workflows n8n demain à 9h",
            "assistant: Rappel créé pour demain 9h.",
            "user: À l'avenir, préviens-moi seulement pour les urgences, pas les newsletters",
            "assistant: Compris, préférence enregistrée : notifications urgences uniquement.",
            "user: Qu'est-ce que tu sais sur mes préférences de notification ?",
            "assistant: Tu veux être notifié uniquement pour les urgences, pas pour les newsletters.",
        ],
        "memory": {
            "preferences": {"notifications": "urgences uniquement, pas de newsletters"},
            "projects": {},
            "tasks": {"valider_workflows_n8n": "échéance demain 9h"},
        },
    },
    {
        "title": "plan action notes reunion produit",
        "history": [
            "user: Analyse ces notes de réunion : on a décidé de prioriser le RAG avant "
            "le multi-tenant, revue vendredi, Sophie prépare le jeu de test",
            "assistant: Plan d'action : 1) prioriser le RAG sur le multi-tenant, "
            "2) revue prévue vendredi, 3) Sophie prépare le jeu de test d'ici là.",
            "user: Crée un rappel pour la revue de vendredi",
            "assistant: Rappel créé : revue projet, vendredi.",
        ],
        "memory": {
            "preferences": {},
            "projects": {"jarvis_v2": "RAG priorisé avant multi-tenant, revue vendredi"},
            "tasks": {"revue_vendredi": "préparée par Sophie : jeu de test"},
        },
    },
]


async def main() -> None:
    written = []
    for sc in SCENARIOS:
        print(f"Génération : {sc['title']}...")
        summary = await generate_session_summary(sc["history"], sc["memory"])
        path = export_session_summary_md(summary, USER_ID, title=sc["title"])
        written.append(path)
        print(f"  -> {path}")
    print(f"\n{len(written)} sessions écrites dans sessions/")


if __name__ == "__main__":
    asyncio.run(main())

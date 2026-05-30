---
paths: ["tests/**/*.spec.ts", "playwright.config.ts"]
---

# Playwright — règles E2E Jarvis

## Comportement

- Toujours lancer `npx playwright test` depuis la racine du projet
- Screenshots automatiques dans `tmp/` en cas d'échec (`screenshot: 'only-on-failure'`)
- Chaque spec teste un use case complet de bout en bout (pas de mock WebSocket)
- Test le fallback : déconnecter l'API et vérifier que le mode texte prend le relai

## Specs obligatoires (à créer en Phase 3)

| Fichier | Ce qu'il teste |
|---------|---------------|
| `voice-connection.spec.ts` | WebSocket connecté, orb en état idle |
| `morning-briefing.spec.ts` | Commande → dashboard visible en < 3s |
| `smart-agent.spec.ts` | Notes analysées → tâches + email draft affichés |
| `memory-scopes.spec.ts` | `Remember X` → rappel correct dans session suivante |
| `fallback.spec.ts` | Mode texte fonctionnel si WebSocket échoue |

## Sélecteurs

- Utiliser `data-testid` pour les éléments interactifs (orb, quick-actions, chat input)
- Jamais de sélecteurs CSS fragiles (`nth-child`, classes générées)

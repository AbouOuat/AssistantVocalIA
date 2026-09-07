# Évaluation classifieur e-mail — v1 vs v2

**Date** : 2026-09-07  |  **Jeu** : `eval/classifier/dataset.csv` (40 e-mails annotés)

**v1** : appel OpenAI `json_object` + `JSON.parse`. **v2** : `json_schema` strict (Path B, 2026-09-04).
Modèle : `gpt-4o-mini`, temp `0.1`.

---

### Urgence (`urgence`) — 40 e-mails annotés

| moteur | accuracy | macro-F1 |
|---|---|---|
| v1 | 0.72 | 0.69 |
| v2 | 0.68 | 0.63 |

| classe | support | P v1 | R v1 | F1 v1 | P v2 | R v2 | F1 v2 |
|---|---|---|---|---|---|---|---|
| haute | 16 | 0.86 | 0.75 | 0.80 | 0.85 | 0.69 | 0.76 |
| moyenne | 11 | 0.57 | 0.36 | 0.44 | 0.50 | 0.27 | 0.35 |
| faible | 13 | 0.68 | 1.00 | 0.81 | 0.62 | 1.00 | 0.76 |

**Matrice de confusion v2**

| vrai \ prédit | haute | moyenne | faible |
|---|---|---|---|
| haute | 11 | 3 | 2 |
| moyenne | 2 | 3 | 6 |
| faible | 0 | 0 | 13 |


---

### Action (`action`) — 40 e-mails annotés

| moteur | accuracy | macro-F1 |
|---|---|---|
| v1 | 0.57 | 0.50 |
| v2 | 0.57 | 0.45 |

| classe | support | P v1 | R v1 | F1 v1 | P v2 | R v2 | F1 v2 |
|---|---|---|---|---|---|---|---|
| repondre | 19 | 0.93 | 0.68 | 0.79 | 0.87 | 0.68 | 0.76 |
| lire | 14 | 0.50 | 0.57 | 0.53 | 0.53 | 0.57 | 0.55 |
| relancer | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| classer | 3 | 0.67 | 0.67 | 0.67 | 0.40 | 0.67 | 0.50 |
| aucune | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

**Matrice de confusion v2**

| vrai \ prédit | repondre | lire | relancer | classer | aucune |
|---|---|---|---|---|---|
| repondre | 13 | 3 | 3 | 0 | 0 |
| lire | 2 | 8 | 0 | 2 | 2 |
| relancer | 0 | 0 | 0 | 0 | 0 |
| classer | 0 | 1 | 0 | 2 | 0 |
| aucune | 0 | 3 | 0 | 1 | 0 |


---

## Lecture

- Si v2 ne dépasse pas v1 en macro-F1 sur `urgence` **et** `action` → garder v1 comme moteur (cf. `DOCS/plans/cv-embellissement-scope.md`), v2 reste joignable via le toggle.
- Le gain attendu de v2 = **fiabilité du format** (JSON Schema strict, 0 parse cassé), pas forcément la qualité de classification (même modèle, même consigne).

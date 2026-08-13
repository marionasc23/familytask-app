# FamilyTask — les dossiers de code de la semaine

## La règle, en une phrase

> **`step-N` = ce qu'il te faut pour COMMENCER l'atelier N.**
> Pas ce que tu dois produire pendant l'atelier N — ça, c'est ton travail.

Chaque dossier contient tout ce qui a été construit **jusqu'à la veille**, et **rien** de ce que
l'atelier du jour demande. Tu ouvres `step-N` le matin, et tu codes dedans.

## À quoi ça sert (le filet de sécurité)

Tu n'as pas fini l'atelier d'hier ? Aucun problème. Tu prends le dossier du jour : il contient
déjà le travail d'hier, tout fait. Tu ne restes **jamais** bloqué·e derrière un atelier raté.

Et quand tu veux voir la correction d'un atelier : **le corrigé de l'atelier N, c'est `step-N+1`.**

| Dossier | Tu l'ouvres pour... | Il contient déjà | Il ne contient pas |
|---|---|---|---|
| `step-1-starter` | l'atelier 1 — installer | Docker + l'écran de bienvenue | *(rien à coder aujourd'hui)* |
| `step-2` | l'atelier 2 — le front | l'environnement qui tourne | la todo-list |
| `step-3` | l'atelier 3 — le back + la base | la todo-list (données locales) | l'API et la base |
| `step-4` | l'atelier 4 — familles & membres | FastAPI + PostgreSQL | les familles et les membres |
| `step-5` | l'atelier 5 — l'assistant IA | le multi-tenant + les membres | le chatbot |
| `step-6` | l'atelier 6 — les finitions | le chatbot qui agit | les finitions |
| `step-7` | l'atelier 7 — le déploiement | l'app finie, en local | le déploiement |
| `step-7-final` | **comparer** | l'app **+ le déploiement** | — *(c'est le corrigé final)* |

## Lancer n'importe quel dossier

Prérequis : **VS Code + Docker** (rien d'autre à installer).

```bash
cd step-2          # ou le dossier de l'atelier du jour
docker compose up
```

- L'app : http://localhost:5173
- L'API : http://localhost:8000/docs

## Les deux IA (à ne pas confondre)

1. **L'IA qui aide à CODER** — GitHub Copilot, dans VS Code, à **chaque atelier**.
2. **L'IA intégrée DANS l'app** — le chatbot (atelier 5). Il arrive après les tâches et les
   membres, car il a besoin de ces fonctions pour agir dessus.

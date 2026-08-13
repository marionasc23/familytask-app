# step-7 — le point de départ de l'**atelier 7** (le déploiement)

**Contient :** l'app FamilyTask complète, qui tourne en local. C'est l'arrivée de l'atelier 6.
**Ne contient pas :** le déploiement (ni `render.yaml`, ni `api.js`).

> Le code est identique à `step-6` : l'atelier 6 est un atelier de finitions,
> il n'ajoute pas de fonctionnalité. Le dossier existe pour que la règle reste simple :
> **ton dossier de code, c'est `step-N` pour l'atelier N.**

## Lancer ce dossier

```bash
docker compose up
```

- L'app : http://localhost:5173
- L'API : http://localhost:8000/docs

**Activer l'assistant IA (une seule fois) :**

```bash
docker compose exec ai ollama pull qwen2.5:3b
```

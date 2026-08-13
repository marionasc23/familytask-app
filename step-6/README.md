# step-6 — le point de départ de l'**atelier 6** (les finitions)

**Contient :** l'assistant IA intégré — route `/api/assistant` (Ollama + function calling) et
composant `ChatAssistant.vue`. C'est l'arrivée de l'atelier 5.
**Ne contient pas :** les finitions (soin de l'interface, détails) — c'est le travail du jour.

**C'est aussi le corrigé de l'atelier 5.**

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

Puis, dans le chat : « ajoute la vaisselle à la liste de Léa ».

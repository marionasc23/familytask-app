import os
# Base SQLite de test, neuve à chaque exécution.
if os.path.exists("./test.db"):
    os.remove("./test.db")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient
from main import app


def test_inscription_puis_tache():
    # Le "with" démarre l'app (crée les tables + les données de démo).
    with TestClient(app) as client:
        # 1) On crée une famille de test → on récupère un token
        r = client.post("/api/signup", params={
            "email": "test@fam.fr", "password": "secret", "name": "Chef", "family": "Test"})
        assert r.status_code == 200
        token = r.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2) On crée une tâche pour soi
        r = client.post("/api/tasks", params={"title": "Sortir les poubelles"}, headers=headers)
        assert r.status_code == 200

        # 3) On relit ses tâches : elle est là
        r = client.get("/api/tasks", headers=headers)
        assert r.status_code == 200
        assert any(t["title"] == "Sortir les poubelles" for t in r.json())


def test_sans_token_refuse():
    with TestClient(app) as client:
        assert client.get("/api/tasks").status_code == 401

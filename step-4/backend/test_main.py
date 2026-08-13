import os

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from main import app, get_session


@pytest.fixture
def test_db_session():
    db_url = "sqlite:///./test_familytask.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    if os.path.exists("./test_familytask.db"):
        os.remove("./test_familytask.db")


@pytest.fixture
def client(test_db_session):
    def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_member_and_login(client, email="alice@example.com", name="Alice", lien="mère"):
    resp = client.post(
        "/api/signup",
        params={
            "email": email,
            "password": "secret123",
            "name": name,
            "family": "Famille Test",
            "lien": lien,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return data


def test_get_tasks_without_token_returns_401(client):
    response = client.get("/api/tasks")
    assert response.status_code == 401, response.text
    assert "detail" in response.json()


def test_task_created_by_member_is_visible_in_tasks(client):
    user = create_member_and_login(client)
    token = user["token"]

    create_task_resp = client.post(
        "/api/tasks",
        params={"title": "Faire les courses"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_task_resp.status_code == 200, create_task_resp.text

    tasks_resp = client.get(
        "/api/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert tasks_resp.status_code == 200, tasks_resp.text
    tasks = tasks_resp.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Faire les courses"
    assert tasks[0]["member_id"] == user["id"]

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


def test_admin_can_assign_task_to_other_member(client):
    admin = create_member_and_login(client, email="admin@example.com", name="Admin")
    admin_token = admin["token"]

    # create another member in the same family via admin
    resp = client.post(
        "/api/members",
        params={
            "email": "bob@example.com",
            "password": "secret123",
            "name": "Bob",
            "lien": "fils",
            "is_admin": False,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text
    member = resp.json()

    # admin assigns a task to Bob
    create_resp = client.post(
        "/api/tasks",
        params={"title": "Tâche pour Bob", "member_id": member["id"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 200, create_resp.text
    task = create_resp.json()
    assert task["member_id"] == member["id"]

    # Bob's tasks should include it (admin can query by member_id)
    tasks_resp = client.get(
        "/api/tasks",
        params={"member_id": member["id"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert tasks_resp.status_code == 200, tasks_resp.text
    tasks = tasks_resp.json()
    assert any(t["title"] == "Tâche pour Bob" for t in tasks)


def test_non_admin_cannot_assign_to_other(client):
    admin = create_member_and_login(client, email="admin2@example.com", name="Admin2")
    admin_token = admin["token"]

    # create a non-admin member
    resp = client.post(
        "/api/members",
        params={
            "email": "charlie@example.com",
            "password": "secret123",
            "name": "Charlie",
            "lien": "fils",
            "is_admin": False,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text
    member = resp.json()

    # login as Charlie
    login = client.post(
        "/api/login",
        params={"email": "charlie@example.com", "password": "secret123"},
    )
    assert login.status_code == 200, login.text
    charlie = login.json()

    # Charlie tries to create a task for admin (not allowed)
    bad = client.post(
        "/api/tasks",
        params={"title": "Tâche mauvaise", "member_id": admin["id"]},
        headers={"Authorization": f"Bearer {charlie['token']}"},
    )
    assert bad.status_code == 403

    # But Charlie can create a task for himself
    ok = client.post(
        "/api/tasks",
        params={"title": "Tâche perso"},
        headers={"Authorization": f"Bearer {charlie['token']}"},
    )
    assert ok.status_code == 200, ok.text
    task = ok.json()
    assert task["member_id"] == charlie["id"]

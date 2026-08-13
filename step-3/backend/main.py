import os
import random

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select

# La ligne de connexion à la base — déjà configurée pour toi (Docker fournit l'adresse).
# Hors Docker, on retombe sur un simple fichier SQLite. Tu n'as rien à changer ici.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    done: bool = False


app = FastAPI(title="FamilyTask")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def get_session():
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def create_db_and_tables():
    # On crée la table Task au démarrage de l'app, pour que la base soit prête.
    SQLModel.metadata.create_all(engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/tasks")
def list_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(Task)).all()
    return tasks


@app.post("/api/tasks")
def create_task(title: str | None = Query(None), session: Session = Depends(get_session)):
    if title is None or not title.strip():
        fallback_titles = [
            "Routine maison",
            "Coup de boost",
            "Petit rappel utile",
            "À faire quand j’ai 2 minutes",
            "Tâche improvisée",
        ]
        title = random.choice(fallback_titles)

    task = Task(title=title.strip(), done=False)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}")
def toggle_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Tâche {task_id} introuvable")

    task.done = not task.done
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Tâche {task_id} introuvable")

    session.delete(task)
    session.commit()
    return {"message": "Task deleted"}

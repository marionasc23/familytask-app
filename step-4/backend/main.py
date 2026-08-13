import hashlib
import os
import random
import secrets
from typing import Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, Depends, Header, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool = False
    member_id: Optional[int] = Field(default=None, foreign_key="member.id")
    completed_at: Optional[datetime] = Field(default=None, nullable=True)


class Lien(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_code: str = Field(index=True)
    label: str


class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    lien: str = ""
    is_admin: bool = False
    family_code: str = ""
    family_name: str = ""
    password_hash: str = ""
    token: str = ""


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def get_session():
    with Session(engine) as session:
        yield session


def public_member(member: Member) -> dict:
    return {
        "id": member.id,
        "email": member.email,
        "name": member.name,
        "lien": member.lien,
        "is_admin": member.is_admin,
        "family_code": member.family_code,
        "family_name": member.family_name,
    }


def pluralize_relation(label: str) -> str:
    rel = (label or "").strip().lower()
    if not rel:
        return "personne"
    if rel.endswith("e"):
        return rel + "s"
    if rel.endswith("s") or rel.endswith("x"):
        return rel
    return rel + "s"


def ambiguous_relation_question(message: str, me: Member, session: Session) -> Optional[str]:
    if not message:
        return None

    text = message.lower()
    family_members = session.exec(select(Member).where(Member.family_code == me.family_code)).all()
    seen = set()

    for member in family_members:
        rel = (member.lien or "").strip().lower()
        if not rel or rel in seen:
            continue
        seen.add(rel)

        patterns = [
            f"ma {rel}",
            f"mon {rel}",
            f"mes {rel}",
            f"ma {pluralize_relation(rel)}",
            f"mon {pluralize_relation(rel)}",
            f"mes {pluralize_relation(rel)}",
        ]

        if any(pattern in text for pattern in patterns):
            matches = [m for m in family_members if (m.lien or "").strip().lower() == rel]
            if len(matches) > 1:
                names = ", ".join(m.name for m in matches)
                return f"Il y a plusieurs {pluralize_relation(rel)} ({names}). Pour qui ?"

    return None


def current_member(authorization: Optional[str] = Header(default=None), session: Session = Depends(get_session)) -> Member:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token manquant")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Format d'authorization invalide")

    member = session.exec(select(Member).where(Member.token == token)).first()
    if not member:
        raise HTTPException(status_code=401, detail="Token invalide")
    return member


app = FastAPI(title="FamilyTask")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.get("/api/liens")
def list_liens(me: Member = Depends(current_member), session: Session = Depends(get_session)):
    liens = session.exec(select(Lien).where(Lien.family_code == me.family_code)).all()
    return [l.label for l in liens]


@app.post("/api/liens")
def add_lien(label: str, me: Member = Depends(current_member), session: Session = Depends(get_session)):
    if not me.is_admin:
        raise HTTPException(status_code=403, detail="Seul l'admin peut modifier les liens")
    if not label or not label.strip():
        raise HTTPException(status_code=400, detail="Label requis")
    existing = session.exec(select(Lien).where(Lien.family_code == me.family_code, Lien.label == label.strip())).first()
    if not existing:
        session.add(Lien(family_code=me.family_code, label=label.strip()))
        session.commit()
    return list_liens(me, session)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/signup")
def signup(email: str, password: str, name: str, family: str, lien: str = "parent",
           session: Session = Depends(get_session)):
    email = email.lower().strip()
    if not email or not password or not name or not family:
        raise HTTPException(status_code=400, detail="email, password, name, family requis")
    if session.exec(select(Member).where(Member.email == email)).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    family_code = "fam-" + secrets.token_hex(4)
    member = Member(
        email=email,
        name=name,
        lien=lien,
        is_admin=True,
        family_code=family_code,
        family_name=family,
        password_hash=hash_password(password),
        token=secrets.token_hex(16),
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return {
        "token": member.token,
        "id": member.id,
        "email": member.email,
        "name": member.name,
        "lien": member.lien,
        "is_admin": member.is_admin,
        "family_code": member.family_code,
        "family_name": member.family_name,
    }


@app.post("/api/login")
def login(email: str, password: str, session: Session = Depends(get_session)):
    email = email.lower().strip()
    member = session.exec(select(Member).where(Member.email == email)).first()
    if not member or member.password_hash != hash_password(password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    member.token = secrets.token_hex(16)
    session.add(member)
    session.commit()
    session.refresh(member)
    return {
        "token": member.token,
        "id": member.id,
        "email": member.email,
        "name": member.name,
        "lien": member.lien,
        "is_admin": member.is_admin,
        "family_code": member.family_code,
        "family_name": member.family_name,
    }


@app.post("/api/assistant")
async def assistant(message: str = Body(..., embed=False), me: Member = Depends(current_member), session: Session = Depends(get_session)):
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Le message est requis")

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    payload = {
        "model": "qwen2.5:3b",
        "messages": [{"role": "user", "content": message.strip()}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "ajouter_tache",
                    "description": "Ajoute une tâche pour une personne de la famille.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "titre": {"type": "string", "description": "Titre de la tâche à créer."},
                            "personne": {"type": "string", "description": "Nom ou prénom de la personne concernée. Si vide, la tâche est attribuée à toi."},
                        },
                        "required": ["titre"],
                    },
                },
            }
        ],
        "stream": False,
    }

    raw_question = ambiguous_relation_question(message, me, session)
    if raw_question:
        return {"reply": raw_question, "needs_person": True}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{ollama_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="L'IA n'est pas prête pour le moment. Réessayez dans quelques secondes.")

    tool_calls = data.get("message", {}).get("tool_calls") or []
    if tool_calls:
        created_tasks = []
        for tool_call in tool_calls:
            function = tool_call.get("function") or {}
            name = function.get("name")
            args = function.get("arguments") or tool_call.get("arguments") or {}
            if name != "ajouter_tache":
                continue

            title = str(args.get("titre") or args.get("title") or "").strip()
            if not title:
                title = random.choice(TITRES_ALEATOIRES)

            target_name = str(args.get("personne") or args.get("person") or "").strip()
            target_member = me
            if target_name:
                normalized_target = target_name.lower().strip()
                family_members = session.exec(select(Member).where(Member.family_code == me.family_code)).all()

                matches = []
                for member in family_members:
                    if not member.name:
                        continue
                    normalized_name = member.name.lower().strip()
                    first_name = normalized_name.split()[0] if normalized_name else ""
                    if normalized_name == normalized_target or first_name == normalized_target:
                        matches.append(member)

                if not matches:
                    raise HTTPException(status_code=400, detail=f"Personne inconnue : {target_name}")

                target_member = matches[0]

            if not me.is_admin and target_member.id != me.id:
                raise HTTPException(status_code=403, detail="Tu ne peux créer une tâche que pour toi-même")

            task = Task(title=title, member_id=target_member.id)
            session.add(task)
            session.commit()
            session.refresh(task)
            created_tasks.append({
                "id": task.id,
                "title": task.title,
                "done": task.done,
                "member_id": task.member_id,
                "member_name": target_member.name,
            })

        confirmation = ""
        if created_tasks:
            task = created_tasks[0]
            person = task["member_name"]
            confirmation = f"J’ai bien ajouté la tâche \"{task['title']}\" pour {person}."

        return {
            "reply": confirmation or "Tâche créée.",
            "tool_name": "ajouter_tache",
            "tasks": created_tasks,
        }

    try:
        content = data["message"]["content"]
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=502, detail="La réponse de l'IA est invalide")

    return {"reply": content.strip() or "Je n'ai pas de réponse à te donner pour le moment."}


@app.get("/api/tasks")
def list_tasks(member_id: Optional[int] = None, me: Member = Depends(current_member), session: Session = Depends(get_session)):
    # If no member_id provided, return the tasks for the current member
    if member_id is None:
        return session.exec(select(Task).where(Task.member_id == me.id)).all()

    # If asking for own tasks, allow
    if member_id == me.id:
        return session.exec(select(Task).where(Task.member_id == me.id)).all()

    # Otherwise only admin can request another member's tasks
    if not me.is_admin:
        raise HTTPException(status_code=403, detail="Seul l'admin peut voir les tâches des autres membres")

    assigned_member = session.get(Member, member_id)
    if not assigned_member or assigned_member.family_code != me.family_code:
        raise HTTPException(status_code=400, detail="Membre invalide pour cette famille")

    return session.exec(select(Task).where(Task.member_id == member_id)).all()


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, done: Optional[bool] = None, title: Optional[str] = None,
                me: Member = Depends(current_member), session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")

    task_owner = session.get(Member, task.member_id)
    if not task_owner or task_owner.family_code != me.family_code:
        raise HTTPException(status_code=403, detail="Tâche hors de ta famille")

    if task_owner.id != me.id and not me.is_admin:
        raise HTTPException(status_code=403, detail="Tu ne peux modifier que tes propres tâches")

    updated = False
    if done is not None:
        task.done = bool(done)
        if task.done:
            task.completed_at = datetime.utcnow()
        else:
            task.completed_at = None
        updated = True
    if title is not None:
        title = title.strip()
        if title:
            task.title = title
            updated = True

    if updated:
        session.add(task)
        session.commit()
        session.refresh(task)

    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, me: Member = Depends(current_member), session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")

    task_owner = session.get(Member, task.member_id)
    if not task_owner or task_owner.family_code != me.family_code:
        raise HTTPException(status_code=403, detail="Tâche hors de ta famille")

    if task_owner.id != me.id and not me.is_admin:
        raise HTTPException(status_code=403, detail="Tu ne peux supprimer que tes propres tâches")

    session.delete(task)
    session.commit()
    return {"ok": True}


@app.get("/api/tasks/famille")
def family_tasks(me: Member = Depends(current_member), session: Session = Depends(get_session)):
    family_members = session.exec(select(Member).where(Member.family_code == me.family_code)).all()
    family_ids = [m.id for m in family_members if m.id is not None]
    if not family_ids:
        return []
    return session.exec(select(Task).where(Task.member_id.in_(family_ids))).all()


@app.get("/api/members")
def list_members(me: Member = Depends(current_member), session: Session = Depends(get_session)):
    members = session.exec(select(Member).where(Member.family_code == me.family_code)).all()
    return [public_member(m) for m in members]


@app.post("/api/members")
def create_member(email: str, password: str, name: str, lien: str = "", is_admin: bool = False,
                  me: Member = Depends(current_member), session: Session = Depends(get_session)):
    if not me.is_admin:
        raise HTTPException(status_code=403, detail="Seul l'admin peut créer un compte")
    email = email.lower().strip()
    if not email or not password or not name:
        raise HTTPException(status_code=400, detail="email, password et name requis")
    if session.exec(select(Member).where(Member.email == email)).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    member = Member(
        email=email,
        name=name,
        lien=lien,
        is_admin=is_admin,
        family_code=me.family_code,
        family_name=me.family_name,
        password_hash=hash_password(password),
        token=secrets.token_hex(16),
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return {
        "id": member.id,
        "email": member.email,
        "name": member.name,
        "lien": member.lien,
        "is_admin": member.is_admin,
        "family_code": member.family_code,
        "family_name": member.family_name,
    }


@app.delete("/api/members/{member_id}")
def delete_member(member_id: int, me: Member = Depends(current_member), session: Session = Depends(get_session)):
    if not me.is_admin:
        raise HTTPException(status_code=403, detail="Seul l'admin peut supprimer un compte")
    if member_id == me.id:
        raise HTTPException(status_code=400, detail="Tu ne peux pas te supprimer toi-même")

    member = session.get(Member, member_id)
    if not member or member.family_code != me.family_code:
        raise HTTPException(status_code=404, detail="Membre invalide pour cette famille")

    for task in session.exec(select(Task).where(Task.member_id == member.id)).all():
        session.delete(task)
    session.delete(member)
    session.commit()
    return {"ok": True}


# Si le titre est vide, on attribue une tâche au hasard plutôt que de refuser.
TITRES_ALEATOIRES = [
    "Ranger le salon", "Sortir les poubelles", "Arroser les plantes",
    "Passer l'aspirateur", "Faire la vaisselle", "Promener le chien",
]


@app.post("/api/tasks")
def add_task(title: str, member_id: Optional[int] = None, me: Member = Depends(current_member),
            session: Session = Depends(get_session)):
    if not title.strip():
        title = random.choice(TITRES_ALEATOIRES)

    assigned_member = me
    if member_id is not None:
        if not me.is_admin:
            raise HTTPException(status_code=403, detail="Seul l'admin peut assigner à un autre membre")
        assigned_member = session.get(Member, member_id)
        if not assigned_member or assigned_member.family_code != me.family_code:
            raise HTTPException(status_code=400, detail="Membre invalide pour cette famille")

    task = Task(title=title, member_id=assigned_member.id)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}")
def toggle_task(task_id: int, me: Member = Depends(current_member), session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        return {"error": "introuvable"}
    if task.member_id != me.id and not me.is_admin:
        raise HTTPException(status_code=403, detail="Tu ne peux modifier que tes tâches")
    task.done = not task.done
    session.add(task); session.commit(); session.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, me: Member = Depends(current_member), session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        return {"ok": True}
    if task.member_id != me.id and not me.is_admin:
        raise HTTPException(status_code=403, detail="Tu ne peux supprimer que tes tâches")
    session.delete(task); session.commit()
    return {"ok": True}

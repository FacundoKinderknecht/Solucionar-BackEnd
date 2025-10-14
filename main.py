from typing import Union, Annotated
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, Session, select
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import contextlib
import hashlib

from database import engine, get_session, create_db_and_tables
from schema.servicios import Servicio
from schema.usuarios import User

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

def _prehash(p: str) -> str:
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

def hash_password(p: str) -> str:
    return pwd_context.hash(_prehash(p))

class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    phone: str | None = None
    role: str = "CLIENTE"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    phone: str | None
    role: str
    is_active: bool

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Test API"}

@app.get("/servicios/{servicio_id}")
async def read_servicio(servicio_id: int, servicio: Servicio):
    return {"servicio_id": servicio_id, "servicio_name": servicio.name}

@app.post("/servicios/")
async def create_servicio(servicio: Servicio, session: SessionDep):
    session.add(servicio)
    session.commit()
    session.refresh(servicio)
    return servicio

@app.put("/servicios/{servicio_id}")
async def update_servicio(servicio_id: int, servicio: Servicio):
    return {"servicio_id": servicio_id, "servicio_name": servicio.name, "servicio_description": servicio.description}

@app.post("/auth/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, session: SessionDep):
    # 1) ¿ya existe el email?
    exists = session.exec(select(User).where(User.email == data.email)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    # 2) hashear contraseña
    password_hash = pwd_context.hash(data.password)

    # 3) crear y persistir
    user = User(
        email=data.email,
        password_hash=password_hash,
        phone=data.phone,
        role=data.role,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # 4) devolver sin el hash
    return UserOut(
        id=user.id,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
    )
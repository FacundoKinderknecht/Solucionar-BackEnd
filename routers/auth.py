from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from sqlmodel import Session, select

from database import get_session
from schema.usuarios import User

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    phone: str | None = None
    role: str = "CLIENTE"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    phone: str | None = None
    role: str
    is_active: bool

@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_session)):
    # 1) ¿ya existe ese email?
    if db.exec(select(User).where(User.email == data.email)).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    # 2) hashear y persistir
    user = User(
        email=data.email,
        password_hash=pwd_context.hash(data.password),
        phone=data.phone,
        role=data.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # 3) respuesta sin la contraseña
    return UserOut(
        id=user.id, email=user.email, phone=user.phone, role=user.role, is_active=user.is_active
    )

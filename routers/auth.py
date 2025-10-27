# ------------------------------------------------------------
# Endpoints de autenticación:
#   - POST /auth/register  
#   - POST /auth/login     
#   - GET  /auth/me        
# ------------------------------------------------------------
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from database import get_session
from schema.usuarios import User
from schema.auth import RegisterIn, UserOut
from core.security import hash_password, verify_password
from core.jwt import create_access_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[Session, Depends(get_session)]

# -------------------- REGISTER --------------------
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, session: SessionDep):
    exists = session.exec(select(User).where(User.email == data.email)).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ya registrado")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        phone=data.phone,
        role=data.role,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return UserOut(
        id=user.id,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
    )

# -------------------- LOGIN --------------------
class TokenResponse(UserOut):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
def login(
    session: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),  # espera fields: username, password
):
    # En el front, mandar email en el campo "username"
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "role": user.role}
    )

    return TokenResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        access_token=token,
    )

# -------------------- ME --------------------
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # dónde se obtiene el token

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user = session.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido o inactivo")
    return user

@router.get("/me", response_model=UserOut)
def me(current_user: Annotated[User, Depends(get_current_user)]):
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        is_active=current_user.is_active,
    )

def require_roles(*allowed: str):
    """
    Devuelve una dependencia que valida que el usuario actual tenga
    alguno de los roles permitidos.
    Uso: Depends(require_roles("ADMIN", "PROVEEDOR"))
    """
    def _dep(current: User = Depends(get_current_user)) -> User:
        if current.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado para este recurso",
            )
        return current
    return _dep

@router.post("/refresh")
def refresh_token(current: User = Depends(get_current_user)):
    """
    Renueva el access token del usuario autenticado.
    Mantiene sub/email/role y sólo actualiza la expiración.
    """
    new_access = create_access_token(
        {"sub": str(current.id), "email": current.email, "role": current.role}
    )
    return {
        "access_token": new_access,
        "token_type": "bearer",
    }

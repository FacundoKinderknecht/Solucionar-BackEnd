# ------------------------------------------------------------
# Esquemas Pydantic para autenticación (entrada/salida).
# NO contienen endpoints ni lógica.
# ------------------------------------------------------------
from pydantic import BaseModel, EmailStr

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

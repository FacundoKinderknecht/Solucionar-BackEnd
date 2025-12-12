# ------------------------------------------------------------
# Configuración centralizada (lee variables de entorno .env).
# ------------------------------------------------------------
import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Clave para firmar tokens JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    # Algoritmo de firma de JWT 
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    # Duración del access token (minutos)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    # Orígenes permitidos para CORS 
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

settings = Settings()

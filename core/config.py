# ------------------------------------------------------------
# Configuración centralizada (lee variables de entorno .env).
# ------------------------------------------------------------
import os
from pydantic import BaseModel


def _default_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://localhost:5173",
        "https://127.0.0.1:5173",
    ]


class Settings(BaseModel):
    # Clave para firmar tokens JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    # Algoritmo de firma de JWT 
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    # Duración del access token (minutos)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    # Orígenes permitidos para CORS y regex de respaldo
    CORS_ORIGINS: list[str] = _default_cors_origins()
    CORS_ORIGIN_REGEX: str = os.getenv("CORS_ORIGIN_REGEX", r"https?://(localhost|127\.0\.0\.1)(:\d+)?")


settings = Settings()

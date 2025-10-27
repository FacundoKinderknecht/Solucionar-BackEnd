# ------------------------------------------------------------
# Helpers para emitir y validar JWTs.
# ------------------------------------------------------------
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Any, Optional

from core.config import settings

def create_access_token(subject: dict[str, Any], expires_minutes: int | None = None) -> str:
    """
    subject: dict con datos que querés dentro del token (p.ej. {"sub": user_id, "email": ...})
    """
    expire_delta = timedelta(
        minutes=expires_minutes if expires_minutes is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    now = datetime.now(timezone.utc)
    payload = {
        "exp": now + expire_delta,
        "iat": now,
        **subject,  # combinamos claims
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

def decode_token(token: str) -> Optional[dict[str, Any]]:
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return data
    except JWTError:
        return None

# ------------------------------------------------------------
# Funciones de seguridad (hash y verificación de contraseña).
# ------------------------------------------------------------
from passlib.context import CryptContext

# Uso bcrypt
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Devuelve el hash seguro de la contraseña."""
    return _pwd.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Compara contraseña en texto plano vs hash almacenado."""
    return _pwd.verify(plain_password, password_hash)

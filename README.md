# Solucionar - BackEnd

Backend de la aplicación Solucionar hecho con FastAPI + SQLModel.

## Requisitos

- Python 3.11+ recomendado
- PostgreSQL (variable `DATABASE_URL` configurada)

## Configuración

1. Crea un archivo `.env` en `Solucionar-BackEnd/` con al menos:

```
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME
SECRET_KEY=super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

2. Instala dependencias:

```
pip install -r requirements.txt
```

3. Ejecuta el servidor de desarrollo:

```
python -m uvicorn main:app --reload
```

La API creará tablas al iniciar y aplicará una micro-migración para asegurar la columna `users.full_name`.

## Endpoints clave

- `POST /auth/register` — Crea usuario (full_name, email, password, opcional phone/province/city)
- `POST /auth/login` — OAuth2 Form (username=email, password) → devuelve access_token y datos del usuario
- `GET  /auth/me` — Devuelve datos del usuario autenticado
- `GET  /` — Healthcheck simple

## Librerías principales

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [psycopg2-binary](https://www.psycopg.org/docs/)
- [python-jose](https://github.com/mpdavis/python-jose)
- [passlib](https://pypi.org/project/passlib/)
- [uvicorn](https://www.uvicorn.org/)

# Solucion.ar — Backend

REST API for the **Solucion.ar** services marketplace, built with FastAPI + SQLModel + PostgreSQL.

> Final Integration Project (TFI) — Universidad Abierta Interamericana (UAI), Argentina.

---

## Requirements

- Python 3.11+
- PostgreSQL (any recent version)

## Setup

### 1. Create the `.env` file

Copy the template and fill in your values:

```bash
cp .env.example .env
```

Minimum required variables:

```dotenv
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME
SECRET_KEY=<at-least-32-random-characters>
```

Full list of supported variables: see `.env.example`.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply database migrations

```bash
alembic upgrade head
```

### 4. Run the development server

```bash
uvicorn app.main:app --reload
```

Interactive API docs available at `http://localhost:8000/docs`.

---

## Project Structure

```
app/
├── core/           # Config (pydantic-settings), security (JWT/bcrypt), enums, logging, exceptions
├── models/         # SQLModel table definitions (User, Provider, Service, Reservation, Review, Payment)
├── schemas/        # Pydantic request/response DTOs
├── services/       # Business logic layer (no HTTP coupling)
├── routers/        # FastAPI route handlers (HTTP only)
├── database.py     # Engine + get_session dependency
├── dependencies.py # SessionDep, CurrentUser, require_roles
└── main.py         # Application factory (create_app)
alembic/            # Database migrations
tests/              # pytest test suite
```

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register a new user account |
| `POST` | `/auth/login` | OAuth2 password flow → returns JWT |
| `GET` | `/auth/me` | Return the authenticated user's profile |
| `GET` | `/health` | Liveness probe (DB ping) |
| `GET/POST` | `/services/` | List / create service listings |
| `GET` | `/services/categories` | List all service categories |
| `GET` | `/services/mine` | Provider's own listings |
| `POST` | `/services/{id}/images` | Replace service images |
| `POST` | `/services/{id}/schedule` | Replace weekly schedule |
| `GET/POST` | `/reservations/` | Client reservations |
| `GET` | `/reservations/provider` | Provider's incoming reservations |
| `POST` | `/payments/` | Create a payment intent |
| `POST` | `/payments/{id}/initiate` | Start gateway checkout |
| `POST` | `/payments/gateway-callback` | Webhook (requires `X-Webhook-Secret`) |
| `GET` | `/providers/me/dashboard` | Provider metrics & revenue |

## Running Tests

```bash
pytest tests/ -v
```

Tests use an in-memory SQLite database — no PostgreSQL required.

## Main Libraries

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [python-jose](https://github.com/mpdavis/python-jose) — JWT
- [passlib](https://pypi.org/project/passlib/) — bcrypt
- [slowapi](https://github.com/laurentS/slowapi) — rate limiting
- [uvicorn](https://www.uvicorn.org/)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `SECRET_KEY` | Yes | — | JWT signing key (≥ 32 chars) |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Token TTL in minutes |
| `CORS_ORIGINS` | No | `["http://localhost:3000"]` | Allowed CORS origins (JSON list) |
| `WEBHOOK_SECRET` | No | — | Shared secret for gateway callbacks |
| `ENVIRONMENT` | No | `development` | `development` / `production` |
| `LOG_LEVEL` | No | `INFO` | Logging level |

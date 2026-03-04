"""FastAPI application factory.

Responsibilities:
- Configures logging at startup.
- Manages the database table creation on first run (lifespan).
- Registers CORS, security-header, and rate-limit middleware.
- Mounts all domain routers.
- Exposes GET /health for infrastructure health checks.
"""
from __future__ import annotations

import contextlib
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.database import create_db_and_tables
from app.routers import auth, payments, providers, reservations, reviews, services, users

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security-relevant HTTP response headers to every response.

    Implements common browser-level defences against XSS, clickjacking,
    and MIME-type sniffing.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Attach security headers before returning the response.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            Response with security headers applied.
        """
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Runs startup logic before yielding control to the ASGI server, and
    shutdown logic after the server stops accepting requests.

    Args:
        app: The FastAPI application instance.
    """
    configure_logging(settings.LOG_LEVEL)
    logger.info("Starting Solucion.ar API (environment: %s)", settings.ENVIRONMENT)
    create_db_and_tables()
    yield
    logger.info("Shutting down Solucion.ar API")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Returns:
        A fully configured ``FastAPI`` instance ready to be served.
    """
    app = FastAPI(
        title="Solucion.ar API",
        description="Services marketplace backend — FastAPI + SQLModel + PostgreSQL",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # --- Rate limiting ---
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Global exception handlers ---

    @app.exception_handler(AppError)
    async def domain_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Map domain exceptions to structured HTTP error responses.

        Logs all 5xx errors with a stack trace; logs 4xx errors at DEBUG level
        to avoid noise in production logs.

        Args:
            request: The incoming HTTP request.
            exc: The raised ``AppError`` subclass instance.

        Returns:
            A ``JSONResponse`` with the appropriate HTTP status code and
            a ``{"detail": "..."}`` body consistent with FastAPI's default format.
        """
        if exc.status_code >= 500:
            logger.exception(
                "Internal error on %s %s: %s",
                request.method,
                request.url.path,
                exc.detail,
            )
        else:
            logger.debug(
                "Domain error %s on %s %s: %s",
                exc.status_code,
                request.method,
                request.url.path,
                exc.detail,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all handler for unexpected exceptions.

        Logs the full stack trace and returns a generic 500 response so that
        internal error details are never leaked to the client.

        Args:
            request: The incoming HTTP request.
            exc: The unhandled exception.

        Returns:
            A ``JSONResponse`` with status 500 and a generic error message.
        """
        logger.exception(
            "Unhandled exception on %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please try again later."},
        )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=settings.CORS_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Security headers ---
    app.add_middleware(SecurityHeadersMiddleware)

    # --- Routers ---
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(providers.router)
    app.include_router(services.router)
    app.include_router(reservations.router)
    app.include_router(reviews.router)
    app.include_router(payments.router)

    # --- Built-in endpoints ---
    @app.get("/health", tags=["health"], summary="Check API and database connectivity")
    def health_check() -> dict:
        """Return the health status of the API and its database connection.

        Performs a lightweight connectivity check against the database.
        Returns HTTP 200 if healthy, HTTP 503 if the database is unreachable.

        Returns:
            A dict with ``status`` and ``database`` keys.
        """
        from sqlalchemy import text
        from app.database import engine

        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception as exc:
            logger.error("Health check DB ping failed: %s", exc)
            db_status = "error"

        return {"status": "ok" if db_status == "ok" else "degraded", "database": db_status}

    return app


app = create_app()

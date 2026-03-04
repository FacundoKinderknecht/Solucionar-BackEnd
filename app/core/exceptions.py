"""Domain-specific exception hierarchy for the Solucion.ar application.

Services raise these typed exceptions instead of HTTP-coupled ``HTTPException``,
keeping business logic decoupled from the transport layer. The global exception
handler in ``app/main.py`` converts them to the appropriate HTTP responses.

Usage example::

    from app.core.exceptions import NotFoundError, ForbiddenError

    def get_service(service_id: int, session: Session) -> Service:
        svc = session.get(Service, service_id)
        if not svc:
            raise NotFoundError("Service", service_id)
        return svc
"""
from __future__ import annotations


class AppError(Exception):
    """Base class for all application-level domain errors.

    Attributes:
        status_code: The HTTP status code that this error maps to.
        detail: Human-readable error message returned in the response body.
    """

    status_code: int = 500
    detail: str = "An unexpected internal error occurred"

    def __init__(self, detail: str | None = None) -> None:
        """Initialise with an optional override message.

        Args:
            detail: Error message. Falls back to the class-level default.
        """
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist in the database."""

    status_code = 404

    def __init__(self, resource: str, identifier: int | str | None = None) -> None:
        """Build a consistent not-found message.

        Args:
            resource: Human-readable resource name (e.g. ``"Service"``).
            identifier: Optional primary key or slug for the missing resource.
        """
        if identifier is not None:
            detail = f"{resource} with id={identifier} was not found"
        else:
            detail = f"{resource} was not found"
        super().__init__(detail)


class ForbiddenError(AppError):
    """Raised when the authenticated user lacks permission for the operation."""

    status_code = 403

    def __init__(self, detail: str = "You do not have permission to access this resource") -> None:
        super().__init__(detail)


class UnauthorizedError(AppError):
    """Raised when the request lacks valid authentication credentials."""

    status_code = 401

    def __init__(self, detail: str = "Authentication required") -> None:
        super().__init__(detail)


class ConflictError(AppError):
    """Raised when the operation would create a duplicate or conflicting state."""

    status_code = 409

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class BusinessRuleError(AppError):
    """Raised when a request violates a domain business rule.

    Use this for semantically invalid operations that pass schema validation
    but break application logic (e.g. booking your own service, reviewing a
    non-completed reservation).
    """

    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)

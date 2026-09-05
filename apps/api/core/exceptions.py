"""
Standardized exception classes for AssessIQ.
All errors are returned as structured JSON: { "error": { "code", "message", "details" } }
"""
from http import HTTPStatus
from typing import Any, Optional


class AssessIQException(Exception):
    """Base exception for all AssessIQ errors."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Any] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


# ── 400 ────────────────────────────────────────────────────────────────────────
class BadRequestError(AssessIQException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(400, "BAD_REQUEST", message, details)


class ValidationError(AssessIQException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(400, "VALIDATION_ERROR", message, details)


# ── 401 ────────────────────────────────────────────────────────────────────────
class UnauthorizedError(AssessIQException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(401, "UNAUTHORIZED", message)


class InvalidCredentialsError(AssessIQException):
    def __init__(self):
        super().__init__(401, "INVALID_CREDENTIALS", "Invalid email or password")


class TokenExpiredError(AssessIQException):
    def __init__(self):
        super().__init__(401, "TOKEN_EXPIRED", "Token has expired")


# ── 403 ────────────────────────────────────────────────────────────────────────
class ForbiddenError(AssessIQException):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(403, "FORBIDDEN", message)


# ── 404 ────────────────────────────────────────────────────────────────────────
class NotFoundError(AssessIQException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(404, "NOT_FOUND", f"{resource} not found")


# ── 409 ────────────────────────────────────────────────────────────────────────
class ConflictError(AssessIQException):
    def __init__(self, message: str):
        super().__init__(409, "CONFLICT", message)


# ── 429 ────────────────────────────────────────────────────────────────────────
class RateLimitError(AssessIQException):
    def __init__(self):
        super().__init__(429, "RATE_LIMITED", "Too many requests. Please try again later.")


# ── 500 ────────────────────────────────────────────────────────────────────────
class InternalError(AssessIQException):
    def __init__(self, message: str = "An internal error occurred"):
        super().__init__(500, "INTERNAL_ERROR", message)

from collections.abc import Mapping, Sequence
from typing import Any

from commerce_search.shared.error_codes import ErrorCode


class AppError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        errors: Sequence[Mapping[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.errors = errors


class BadRequestError(AppError):
    def __init__(
        self,
        message: str = "Bad request",
        *,
        code: str = ErrorCode.BAD_REQUEST,
    ) -> None:
        super().__init__(code=code, message=message, status_code=400)


class ResourceNotFoundError(AppError):
    def __init__(
        self,
        message: str = "Resource not found",
        *,
        code: str = ErrorCode.NOT_FOUND,
    ) -> None:
        super().__init__(code=code, message=message, status_code=404)


class ConflictError(AppError):
    def __init__(
        self,
        message: str = "Resource conflict",
        *,
        code: str = ErrorCode.CONFLICT,
    ) -> None:
        super().__init__(code=code, message=message, status_code=409)


class ServiceUnavailableError(AppError):
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        *,
        code: str = ErrorCode.SERVICE_UNAVAILABLE,
    ) -> None:
        super().__init__(code=code, message=message, status_code=503)

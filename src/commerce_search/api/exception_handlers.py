from collections.abc import Mapping
from typing import Any, cast

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler

from commerce_search.api.schemas import error_response
from commerce_search.shared.error_codes import ErrorCode
from commerce_search.shared.exceptions import AppError
from commerce_search.shared.middleware import get_request_id

logger = structlog.get_logger(__name__)


def _json_error(
    *,
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    errors: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    response = error_response(
        code=code,
        message=message,
        request_id=request_id,
        errors=errors,
    )
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response),
        headers=headers,
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = get_request_id(request)
    await logger.awarning(
        "application_error",
        code=exc.code,
        status_code=exc.status_code,
        path=request.url.path,
    )
    errors = [dict(error) for error in exc.errors] if exc.errors else None
    return _json_error(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        request_id=request_id,
        errors=errors,
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return _json_error(
        status_code=422,
        code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        request_id=get_request_id(request),
        errors=errors,
    )


async def http_error_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    code_by_status = {
        400: ErrorCode.BAD_REQUEST,
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.METHOD_NOT_ALLOWED,
        409: ErrorCode.CONFLICT,
    }
    return _json_error(
        status_code=exc.status_code,
        code=code_by_status.get(exc.status_code, f"HTTP_{exc.status_code}"),
        message=str(exc.detail),
        request_id=get_request_id(request),
        headers=exc.headers,
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    await logger.aexception(
        "unhandled_exception",
        path=request.url.path,
        exception_type=type(exc).__name__,
    )
    return _json_error(
        status_code=500,
        code=ErrorCode.INTERNAL_ERROR,
        message="Internal server error",
        request_id=get_request_id(request),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, cast(ExceptionHandler, app_error_handler))
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, validation_error_handler),
    )
    app.add_exception_handler(
        StarletteHTTPException,
        cast(ExceptionHandler, http_error_handler),
    )
    app.add_exception_handler(
        Exception,
        cast(ExceptionHandler, unexpected_error_handler),
    )

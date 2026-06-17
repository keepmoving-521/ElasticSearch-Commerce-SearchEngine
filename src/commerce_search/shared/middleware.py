import re
from time import perf_counter
from uuid import uuid4

import structlog
from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_STATE_KEY = "request_id"
RESPONSE_TIME_HEADER = "X-Response-Time-Ms"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")

logger = structlog.get_logger(__name__)


def get_request_id(request: Request) -> str:
    return str(getattr(request.state, REQUEST_ID_STATE_KEY, "unknown"))


def normalize_request_id(raw_request_id: bytes | None, *, max_length: int) -> str:
    if raw_request_id:
        request_id = raw_request_id.decode("ascii", errors="ignore").strip()
        if (
            request_id
            and len(request_id) <= max_length
            and REQUEST_ID_PATTERN.fullmatch(request_id)
        ):
            return request_id
    return str(uuid4())


class RequestContextMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        access_log_enabled: bool = True,
        request_id_max_length: int = 128,
    ) -> None:
        self.app = app
        self.access_log_enabled = access_log_enabled
        self.request_id_max_length = request_id_max_length

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        request_id = normalize_request_id(
            headers.get(REQUEST_ID_HEADER.lower().encode()),
            max_length=self.request_id_max_length,
        )
        scope.setdefault("state", {})[REQUEST_ID_STATE_KEY] = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            http_method=scope["method"],
            path=scope["path"],
        )
        started_at = perf_counter()
        status_code = 500

        async def send_with_context(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                elapsed_ms = (perf_counter() - started_at) * 1000
                response_headers = MutableHeaders(scope=message)
                response_headers[REQUEST_ID_HEADER] = request_id
                response_headers[RESPONSE_TIME_HEADER] = f"{elapsed_ms:.2f}"
            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        except Exception:
            await logger.aexception(
                "http_request_failed",
                duration_ms=round((perf_counter() - started_at) * 1000, 2),
            )
            raise
        finally:
            if self.access_log_enabled:
                log_method = logger.awarning if status_code >= 500 else logger.ainfo
                await log_method(
                    "http_request_completed",
                    status_code=status_code,
                    duration_ms=round((perf_counter() - started_at) * 1000, 2),
                )
            structlog.contextvars.clear_contextvars()

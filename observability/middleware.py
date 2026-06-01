"""HTTP middleware — correlation ID propagation and request timing."""

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from constants import CORRELATION_ID_HEADER
from observability.logging_config import logger
from observability.metrics import REQUEST_LATENCY


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Attach X-Correlation-ID to every request/response and structured logs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        response.headers[CORRELATION_ID_HEADER] = correlation_id
        path = request.url.path
        REQUEST_LATENCY.labels(method=request.method, path=path).observe(elapsed)

        log_record = logging.LogRecord(
            name=logger.name,
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="request_completed",
            args=(),
            exc_info=None,
        )
        log_record.correlation_id = correlation_id  # type: ignore[attr-defined]
        log_record.method = request.method  # type: ignore[attr-defined]
        log_record.path = path  # type: ignore[attr-defined]
        log_record.duration_ms = round(elapsed * 1000, 2)  # type: ignore[attr-defined]
        logger.handle(log_record)

        return response

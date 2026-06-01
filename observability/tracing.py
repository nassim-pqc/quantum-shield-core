"""OpenTelemetry tracing (optional, enabled via environment).

Provides:
- Automatic FastAPI instrumentation via opentelemetry-instrumentation-fastapi
- Custom spans for cryptographic operations (key_gen, seal, unseal, audit)
- Trace propagation via X-Correlation-ID and W3C tracecontext
- OTLP export to configured endpoint (Jaeger, Grafana Tempo, etc.)
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositeHTTPPropagator
from opentelemetry.trace import SpanKind, Status, StatusCode

tracer: trace.Tracer | None = None
"""Module-level tracer, initialized by setup_opentelemetry()."""


def _get_tracer() -> trace.Tracer:
    """Get the global tracer or a no-op fallback."""
    return trace.get_tracer("quantum-shield-core")


def setup_opentelemetry(app: FastAPI, tracer_name: str = "quantum-shield-core") -> None:
    """Instrument FastAPI when OTEL_EXPORTER_OTLP_ENDPOINT is configured.

    If no endpoint is set, this is a no-op and all tracing calls become no-ops.
    """
    global tracer

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        tracer = trace.get_tracer(tracer_name)
        return

    try:
        from opentelemetry import trace as otel_trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        service_name = os.environ.get("OTEL_SERVICE_NAME", "quantum-shield-core")
        insecure = os.environ.get("OTEL_EXPORTER_INSECURE", "true").lower() == "true"
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=insecure))
        )
        otel_trace.set_tracer_provider(provider)

        # Enable W3C trace context propagation
        set_global_textmap(CompositeHTTPPropagator())

        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

        tracer = otel_trace.get_tracer(tracer_name)
    except Exception as exc:
        # Fail open: tracing should never block the application
        import logging

        logging.getLogger("quantum_shield").warning(
            "OpenTelemetry setup failed (tracing disabled): %s", exc
        )
        tracer = trace.get_tracer(tracer_name)


# ---------------------------------------------------------------------------
# Decorator for tracing crypto operations
# ---------------------------------------------------------------------------


def trace_crypto(operation: str) -> Callable:
    """Decorator that wraps a cryptographic function with an OpenTelemetry span.

    The span captures duration, operation name, and any error status.

    Example:
        @trace_crypto("seal")
        def encrypt_hybrid(self, pub_key, plaintext, context):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            span_tracer = _get_tracer()
            with span_tracer.start_as_current_span(
                f"crypto.{operation}",
                kind=SpanKind.INTERNAL,
            ) as span:
                span.set_attribute("crypto.operation", operation)
                span.set_attribute("crypto.algorithm", "Kyber768+AES256GCM")
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.perf_counter() - start
                    span.set_attribute("crypto.duration_ms", round(elapsed * 1000, 2))
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as exc:
                    elapsed = time.perf_counter() - start
                    span.set_attribute("crypto.duration_ms", round(elapsed * 1000, 2))
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    span.record_exception(exc)
                    raise

        return wrapper

    return decorator


__all__ = [
    "setup_opentelemetry",
    "trace_crypto",
    "_get_tracer",
]

"""Structured JSON logging configuration."""
import json
import logging
import os

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


class JsonFormatter(logging.Formatter):
    """JSON log lines for SIEM / Loki / CloudWatch ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("correlation_id", "method", "path", "duration_ms", "version"):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(LOG_LEVEL)


logger = logging.getLogger("quantum_shield")

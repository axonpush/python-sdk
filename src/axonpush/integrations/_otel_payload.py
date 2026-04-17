"""Shared helpers for building OpenTelemetry-shaped log payloads.

Used by all log-forwarding integrations (print_capture, logging_handler,
loguru, structlog) so that the on-the-wire shape is consistent regardless
of which Python logging library the user has chosen.

The payload follows the OTLP/HTTP/JSON LogRecord format with lowerCamelCase
field names (timeUnixNano, severityNumber, severityText, body, attributes,
resource). See https://opentelemetry.io/docs/specs/otel/logs/data-model/.
"""
from __future__ import annotations

import bisect
import json
import logging
from typing import Any, Dict, Optional

_PY_LEVEL_TO_OTEL: Dict[int, tuple[int, str]] = {
    logging.NOTSET: (0, ""),
    logging.DEBUG: (5, "DEBUG"),
    logging.INFO: (9, "INFO"),
    logging.WARNING: (13, "WARN"),
    logging.ERROR: (17, "ERROR"),
    logging.CRITICAL: (21, "FATAL"),
}

_PY_LEVELS_SORTED = sorted(_PY_LEVEL_TO_OTEL.keys())
_PY_VALUES_SORTED = [_PY_LEVEL_TO_OTEL[k] for k in _PY_LEVELS_SORTED]

_TEXT_TO_SEVERITY: Dict[str, tuple[int, str]] = {
    "TRACE": (1, "TRACE"),
    "DEBUG": (5, "DEBUG"),
    "INFO": (9, "INFO"),
    "NOTICE": (11, "INFO"),
    "WARN": (13, "WARN"),
    "WARNING": (13, "WARN"),
    "ERROR": (17, "ERROR"),
    "ERR": (17, "ERROR"),
    "CRITICAL": (21, "FATAL"),
    "FATAL": (21, "FATAL"),
}


def severity_from_python_level(level: int) -> tuple[int, str]:
    idx = bisect.bisect_right(_PY_LEVELS_SORTED, level) - 1
    if idx < 0:
        return (9, "INFO")
    return _PY_VALUES_SORTED[idx]


def severity_from_text(text: str) -> tuple[int, str]:
    return _TEXT_TO_SEVERITY.get(text.upper(), (9, "INFO"))


def build_log_payload(
    *,
    body: Any,
    severity_number: int,
    severity_text: str,
    time_unix_nano: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    resource: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construct an OTel-shaped log payload ready for client.events.publish()."""
    payload: Dict[str, Any] = {
        "severityNumber": severity_number,
        "severityText": severity_text,
        "body": _serializable_body(body),
    }
    if time_unix_nano is not None:
        payload["timeUnixNano"] = time_unix_nano
    if attributes:
        payload["attributes"] = _stringify_values(attributes)
    if resource:
        payload["resource"] = _stringify_values(resource)
    return payload


def _serializable_body(value: Any) -> Any:
    """Strings stay as strings; complex objects are JSON-serialized to a string.

    The OTel spec allows the body to be any AnyValue (string, struct, list).
    For simplicity and search-friendliness, we keep the string case as-is and
    serialize the rest to a JSON string. Users who want structured bodies can
    pass a string body and put structure in attributes.
    """
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


def _stringify_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively coerce non-JSON-serializable values to strings."""
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, dict):
            out[k] = _stringify_values(v)
        elif isinstance(v, (list, tuple)):
            out[k] = [_serializable_body(item) for item in v]
        else:
            out[k] = str(v)
    return out

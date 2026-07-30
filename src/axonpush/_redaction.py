"""Client-side telemetry capture and redaction policy."""

from __future__ import annotations

import re
from typing import Any

from axonpush._config import Settings

_SECRET_KEY = re.compile(
    r"^(authorization|proxy-authorization|cookie|set-cookie|password|passwd|secret|"
    r"client_secret|api[-_.]?key|access[-_.]?token|refresh[-_.]?token|private[-_.]?key)$",
    re.IGNORECASE,
)
_CONTENT_KEY = re.compile(
    r"^(prompt|prompts|messages?|completion|completions|input|output|response|"
    r"tool[-_.]?(arguments?|result|output)|retrieval[-_.]?(documents?|content))$",
    re.IGNORECASE,
)


def redact_telemetry(value: Any, settings: Settings) -> Any:
    """Return a recursively copied value safe for telemetry transport."""

    configured_keys = {key.casefold() for key in settings.redact_keys}

    def visit(current: Any) -> Any:
        if isinstance(current, str):
            if len(current) > settings.max_content_length:
                return f"{current[: settings.max_content_length]}…[TRUNCATED]"
            return current
        if isinstance(current, list):
            return [visit(item) for item in current]
        if isinstance(current, tuple):
            return [visit(item) for item in current]
        if isinstance(current, dict):
            output: dict[Any, Any] = {}
            for key, child in current.items():
                key_text = str(key)
                should_redact = (
                    bool(_SECRET_KEY.match(key_text))
                    or key_text.casefold() in configured_keys
                    or (
                        settings.content_capture_mode == "metadata_only"
                        and bool(_CONTENT_KEY.match(key_text))
                    )
                )
                output[key] = "[REDACTED]" if should_redact else visit(child)
            return output
        return current

    return visit(value)


__all__ = ["redact_telemetry"]

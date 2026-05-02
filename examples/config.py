"""Shared config for all examples.

Reads from a local ``.env`` file (if present) and the process environment.
The variables below match the names the SDK itself reads, so any caller of
``AxonPush()`` with no kwargs will already pick them up — these examples
just expose them as module-level constants for convenience.

Variables (all prefixed ``AXONPUSH_``):

* ``API_KEY`` — required. Issued from your org's settings page.
* ``TENANT_ID`` — required. Your organisation UUID.
* ``BASE_URL`` — optional. Defaults to ``http://localhost:3000``.
* ``ENVIRONMENT`` — optional. Logical environment label, e.g. ``"dev"``.
* ``CHANNEL_ID`` — optional. UUID of an existing channel to reuse.
* ``APP_ID`` — optional. UUID of an existing app to reuse.

Plus a couple of optional knobs scoped to the integration examples:

* ``OPENAI_API_KEY`` — only used by 07/09 to actually run a chain.
* ``WEBHOOK_URL`` — only used by 05 to receive deliveries.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

API_KEY = os.environ.get("AXONPUSH_API_KEY")
TENANT_ID = os.environ.get("AXONPUSH_TENANT_ID")
BASE_URL = os.environ.get("AXONPUSH_BASE_URL", "http://localhost:3000")
ENVIRONMENT = os.environ.get("AXONPUSH_ENVIRONMENT")
CHANNEL_ID = os.environ.get("AXONPUSH_CHANNEL_ID")
APP_ID = os.environ.get("AXONPUSH_APP_ID")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://httpbin.org/post")


def require_credentials() -> None:
    """Exit with a helpful message when ``AXONPUSH_API_KEY`` / ``AXONPUSH_TENANT_ID`` are missing."""
    missing = [k for k, v in (("AXONPUSH_API_KEY", API_KEY), ("AXONPUSH_TENANT_ID", TENANT_ID)) if not v]
    if missing:
        print(f"Missing env var(s): {', '.join(missing)}")
        print("Either:")
        print("  1. Copy .env.example to .env and fill in your values, or")
        print("  2. Export them in your shell.")
        sys.exit(1)

"""
Shared config for all examples.

Reads from .env file (if present) and environment variables.
Copy .env.example to .env and fill in your credentials:

    cp .env.example .env
"""

import os
import sys
from pathlib import Path


def _load_dotenv():
    """Load .env file from the examples directory."""
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
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://httpbin.org/post")


def require_credentials():
    """Exit with a helpful message if credentials are missing."""
    if not API_KEY or not TENANT_ID:
        print("Missing credentials. Either:")
        print("  1. Copy .env.example to .env and fill in your values")
        print("  2. Set AXONPUSH_API_KEY and AXONPUSH_TENANT_ID env vars")
        sys.exit(1)

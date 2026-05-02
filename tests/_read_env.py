"""Tiny Makefile helper — extracts a single key from a .env file, or
locates psql.exe on Windows when it isn't on PATH.

Used by `make e2e-db-setup` so the user doesn't have to manually set
PGPASSWORD or add PostgreSQL's bin directory to PATH. Cross-platform;
no shell quoting hell.

Usage:
    python tests/_read_env.py DB_PASSWORD ../easy-push/.env
    python tests/_read_env.py --find-psql

Always exits 0 so make's `$(shell ...)` gets a clean string back even
when something is missing.
"""

from __future__ import annotations

import glob
import re
import shutil
import sys


def find_psql() -> str:
    """Return a usable psql command. Prefers PATH, falls back to common
    Windows install locations, finally returns the bare name 'psql'."""
    on_path = shutil.which("psql")
    if on_path:
        return on_path
    # Windows: PostgreSQL installer's default location
    candidates = sorted(
        glob.glob(r"C:\Program Files\PostgreSQL\*\bin\psql.exe"),
        reverse=True,  # newest version first
    )
    if candidates:
        return candidates[0]
    return "psql"


def read_env_key(key: str, path: str) -> str:
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return ""
    pattern = rf"^{re.escape(key)}=[\"']?(.*?)[\"']?$"
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1) if match else ""


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "--find-psql":
        print(find_psql())
        return 0
    if len(sys.argv) < 3:
        return 0
    key, path = sys.argv[1], sys.argv[2]
    value = read_env_key(key, path)
    if value:
        print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main())

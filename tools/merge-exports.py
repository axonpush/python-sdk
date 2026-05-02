"""Concatenate ``_exports_<stream>.txt`` into ``src/axonpush/__init__.py``.

Run after the parallel-stream rewrite when all four streams have committed.
Streams A/B/C/D drop their public re-exports as line-per-import files at the
repo root; this script merges them, prepends a small preamble, emits a
synthesised ``__all__`` so each re-export passes ruff F401, and removes the
temporary files.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INIT = REPO / "src" / "axonpush" / "__init__.py"

PREAMBLE = (
    '"""AxonPush — real-time event infrastructure for AI agent systems.\n\n'
    "Top-level package. Public API is re-exported here; internal helpers live\n"
    'under ``axonpush._internal`` and are not part of the supported surface.\n"""\n\n'
    "from axonpush._version import __version__\n\n"
)


def collect_imports(snippet: str) -> list[str]:
    """Parse a snippet and return the list of names it imports."""
    tree = ast.parse(snippet)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.append(alias.asname or alias.name)
    return names


def main() -> int:
    snippets = sorted(REPO.glob("_exports_*.txt"))
    if not snippets:
        print("No _exports_*.txt files at repo root; nothing to merge.")
        return 1
    seen_lines: set[str] = set()
    body_lines: list[str] = []
    all_names: list[str] = []
    for snip in snippets:
        text = snip.read_text()
        body_lines.append(f"# from {snip.name}")
        for raw in text.splitlines():
            line = raw.rstrip()
            if not line or line.startswith("#"):
                body_lines.append(line)
                continue
            if line in seen_lines:
                continue
            seen_lines.add(line)
            body_lines.append(line)
        body_lines.append("")
        for name in collect_imports(text):
            if name == "__version__" or name in all_names:
                continue
            all_names.append(name)
    all_names.append("__version__")
    all_names.sort()
    all_block = "\n__all__ = [\n" + "".join(f'    "{n}",\n' for n in all_names) + "]\n"
    INIT.write_text(PREAMBLE + "\n".join(body_lines).rstrip() + "\n" + all_block)
    for snip in snippets:
        snip.unlink()
    print(f"Wrote {INIT.relative_to(REPO)} from {len(snippets)} export file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

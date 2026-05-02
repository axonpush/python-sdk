"""Concatenate `_exports_<stream>.txt` files into ``src/axonpush/__init__.py``.

Run after the parallel-stream rewrite when all four streams have committed.
Streams A/B/C/D drop their public re-exports as line-per-import files at the
repo root; this script merges them, prepends a small preamble, and removes
the temporary files.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INIT = REPO / "src" / "axonpush" / "__init__.py"

PREAMBLE = '"""AxonPush — real-time event infrastructure for AI agent systems.\n\n'\
'Top-level package. Public API is re-exported here; internal helpers live\n'\
'under ``axonpush._internal`` and are not part of the supported surface.\n"""\n\n'\
'from axonpush._version import __version__\n\n'


def main() -> int:
    snippets = sorted(REPO.glob("_exports_*.txt"))
    if not snippets:
        print("No _exports_*.txt files at repo root; nothing to merge.")
        return 1
    seen: set[str] = set()
    body_lines: list[str] = []
    for snip in snippets:
        body_lines.append(f"# from {snip.name}")
        for raw in snip.read_text().splitlines():
            line = raw.rstrip()
            if not line or line.startswith("#"):
                body_lines.append(line)
                continue
            if line in seen:
                continue
            seen.add(line)
            body_lines.append(line)
        body_lines.append("")
    INIT.write_text(PREAMBLE + "\n".join(body_lines).rstrip() + "\n")
    for snip in snippets:
        snip.unlink()
    print(f"Wrote {INIT.relative_to(REPO)} from {len(snippets)} export file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

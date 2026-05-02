"""Apply post-dump fixups to the AxonPush OpenAPI spec before codegen.

NestJS swagger emits a couple of shapes that openapi-python-client refuses
to parse — patch them here so the generator stays vanilla.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def fix_array_items_required(node: object) -> None:
    """Drop boolean ``required`` from ``items`` schemas (only allowed on parameters)."""
    if isinstance(node, dict):
        items = node.get("items")
        if isinstance(items, dict) and isinstance(items.get("required"), bool):
            del items["required"]
        for v in node.values():
            fix_array_items_required(v)
    elif isinstance(node, list):
        for v in node:
            fix_array_items_required(v)


def dedupe_header_params(spec: dict) -> None:
    """Collapse case-insensitive duplicate header parameters; canonicalize as Title-Case.

    NestJS sometimes emits both ``x-axonpush-channel`` and ``X-Axonpush-Channel``
    on the same operation; the python identifier generator chokes on the
    lowercase variant.
    """
    for ops in spec.get("paths", {}).values():
        for op in ops.values():
            if not isinstance(op, dict):
                continue
            params = op.get("parameters", [])
            seen: dict[str, dict] = {}
            for p in params:
                if p.get("in") != "header":
                    continue
                key = p["name"].lower()
                if key in seen and p.get("required") and not seen[key].get("required"):
                    seen[key] = p
                elif key not in seen:
                    seen[key] = p
            new = [p for p in params if p.get("in") != "header"]
            for p in seen.values():
                p = dict(p)
                p["name"] = "-".join(part.capitalize() for part in p["name"].split("-"))
                new.append(p)
            op["parameters"] = new


def main(path: str) -> None:
    p = Path(path)
    spec = json.loads(p.read_text())
    fix_array_items_required(spec)
    dedupe_header_params(spec)
    p.write_text(json.dumps(spec, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional


def safe_serialize(obj: Any, max_len: int = 2000) -> Any:
    try:
        s = json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return str(obj)[:max_len]
    if len(s) <= max_len:
        return json.loads(s)
    return s[:max_len]


def fire_and_forget(result: Any) -> None:
    if asyncio.iscoroutine(result):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(result)
        except RuntimeError:
            pass


def build_resource(
    service_name: Optional[str] = None,
    service_version: Optional[str] = None,
    environment: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    resource: Dict[str, Any] = {}
    if service_name is not None:
        resource["service.name"] = service_name
    if service_version is not None:
        resource["service.version"] = service_version
    if environment is not None:
        resource["deployment.environment"] = environment
    return resource or None

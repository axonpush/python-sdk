from __future__ import annotations

import atexit
import logging
import os
import queue
import threading
import time
import weakref
from functools import wraps
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

_internal_logger = logging.getLogger("axonpush")

DEFAULT_QUEUE_SIZE = 1000
DEFAULT_SHUTDOWN_TIMEOUT_S = 2.0
DROP_WARNING_INTERVAL_S = 10.0

_SENTINEL = object()

_SERVERLESS_MARKERS = (
    ("AWS_LAMBDA_FUNCTION_NAME", "AWS Lambda"),
    ("FUNCTION_TARGET", "Google Cloud Functions"),
    ("AZURE_FUNCTIONS_ENVIRONMENT", "Azure Functions"),
)


def detect_serverless() -> Optional[str]:
    for env_var, name in _SERVERLESS_MARKERS:
        if os.environ.get(env_var):
            return name
    return None


class BackgroundPublisher:
    def __init__(
        self,
        client: "AxonPush | AsyncAxonPush",
        *,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
    ) -> None:
        self._client = client
        self._queue_size = queue_size
        self._shutdown_timeout = shutdown_timeout
        self._queue: "queue.Queue[Any]" = queue.Queue(maxsize=queue_size)
        self._drop_lock = threading.Lock()
        self._drop_counter = 0
        self._last_drop_warn = 0.0
        self._close_lock = threading.Lock()
        self._closed = False
        self._thread: Optional[threading.Thread] = None
        self._start_worker()
        _LIVE_PUBLISHERS.add(self)

    def _start_worker(self) -> None:
        self._closed = False
        self._thread = threading.Thread(
            target=self._drain,
            name="axonpush-publisher",
            daemon=True,
        )
        self._thread.start()

    def _drain(self) -> None:
        while True:
            item = self._queue.get()
            if item is _SENTINEL:
                self._queue.task_done()
                return
            try:
                self._client.events.publish(**item)
            except Exception as exc:
                _internal_logger.warning("axonpush publish failed: %s", exc)
            finally:
                self._queue.task_done()

    def submit(self, publish_kwargs: Dict[str, Any]) -> None:
        if self._closed:
            return
        try:
            self._queue.put_nowait(publish_kwargs)
        except queue.Full:
            self._record_drop()

    def _record_drop(self) -> None:
        with self._drop_lock:
            self._drop_counter += 1
            now = time.monotonic()
            if now - self._last_drop_warn < DROP_WARNING_INTERVAL_S:
                return
            dropped = self._drop_counter
            self._last_drop_warn = now
        _internal_logger.warning(
            "axonpush publisher queue full; %d records dropped so far "
            "(queue_size=%d) — consider increasing queue_size",
            dropped,
            self._queue_size,
        )

    def flush(self, timeout: Optional[float] = None) -> None:
        with self._queue.all_tasks_done:
            if timeout is None:
                while self._queue.unfinished_tasks:
                    self._queue.all_tasks_done.wait()
            else:
                end = time.monotonic() + timeout
                while self._queue.unfinished_tasks:
                    remaining = end - time.monotonic()
                    if remaining <= 0:
                        break
                    self._queue.all_tasks_done.wait(remaining)

    def close(self) -> None:
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
        self.flush(timeout=self._shutdown_timeout)
        try:
            self._queue.put_nowait(_SENTINEL)
        except queue.Full:
            pass
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)
        self._thread = None

    def _reset_after_fork(self) -> None:
        self._queue = queue.Queue(maxsize=self._queue_size)
        self._drop_lock = threading.Lock()
        self._drop_counter = 0
        self._last_drop_warn = 0.0
        self._close_lock = threading.Lock()
        self._closed = False
        self._thread = None
        self._start_worker()


_LIVE_PUBLISHERS: "weakref.WeakSet[BackgroundPublisher]" = weakref.WeakSet()


def _close_all_publishers() -> None:
    for pub in list(_LIVE_PUBLISHERS):
        try:
            pub.close()
        except Exception:
            pass


def _reset_all_publishers_after_fork() -> None:
    for pub in list(_LIVE_PUBLISHERS):
        try:
            pub._reset_after_fork()
        except Exception:
            pass


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_all_publishers_after_fork)

atexit.register(_close_all_publishers)


def flush_after_invocation(
    *handlers: Any,
    timeout: Optional[float] = 5.0,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            finally:
                for h in handlers:
                    try:
                        h.flush(timeout)
                    except Exception as exc:
                        _internal_logger.warning(
                            "flush_after_invocation: %s.flush() raised: %s",
                            type(h).__name__,
                            exc,
                        )
        return wrapper
    return decorator

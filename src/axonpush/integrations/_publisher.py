from __future__ import annotations

import asyncio
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


class AsyncBackgroundPublisher:
    """Non-blocking async publisher using ``asyncio.create_task()``.

    ``submit()`` is synchronous (not a coroutine) so it can be called from
    sync callback contexts (e.g. LangChain ``BaseCallbackHandler.on_*``).
    Tasks are tracked in a bounded pending set; when ``max_pending`` is
    reached, new events are dropped with a rate-limited warning.
    """

    def __init__(
        self,
        client: "AsyncAxonPush",
        *,
        max_pending: int = DEFAULT_QUEUE_SIZE,
    ) -> None:
        self._client = client
        self._max_pending = max_pending
        self._pending: set[asyncio.Task[None]] = set()
        self._closed = False
        self._drop_lock = threading.Lock()
        self._drop_counter = 0
        self._last_drop_warn = 0.0

    def submit(self, publish_kwargs: Dict[str, Any]) -> None:
        if self._closed:
            return
        if len(self._pending) >= self._max_pending:
            self._record_drop()
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        task = loop.create_task(self._fire(publish_kwargs))
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    async def _fire(self, publish_kwargs: Dict[str, Any]) -> None:
        try:
            await self._client.events.publish(**publish_kwargs)
        except Exception as exc:
            _internal_logger.warning("axonpush async publish failed: %s", exc)

    def _record_drop(self) -> None:
        with self._drop_lock:
            self._drop_counter += 1
            now = time.monotonic()
            if now - self._last_drop_warn < DROP_WARNING_INTERVAL_S:
                return
            dropped = self._drop_counter
            self._last_drop_warn = now
        _internal_logger.warning(
            "axonpush async publisher at capacity; %d events dropped so far "
            "(max_pending=%d) — consider increasing max_pending",
            dropped,
            self._max_pending,
        )

    async def flush(self, timeout: Optional[float] = None) -> None:
        if not self._pending:
            return
        tasks = list(self._pending)
        if timeout is None:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            done, _ = await asyncio.wait(tasks, timeout=timeout)

    async def close(self) -> None:
        self._closed = True
        await self.flush(timeout=DEFAULT_SHUTDOWN_TIMEOUT_S)
        self._pending.clear()


class RqPublisher:
    """Durable Redis-backed publisher using `python-rq <https://python-rq.org/>`_.

    Each ``submit()`` call enqueues a job via ``rq.Queue.enqueue()`` (a fast
    synchronous Redis RPUSH).  Jobs are executed by a separate ``rq worker``
    process, so event publishing survives app restarts and is retried on
    transient failures.

    Requires ``pip install axonpush[rq]``.
    """

    def __init__(
        self,
        client: "AxonPush | AsyncAxonPush",
        *,
        redis_conn: Any = None,
        queue_name: str = "axonpush",
        job_timeout: str = "5m",
        result_ttl: int = 0,
        failure_ttl: int = 86400,
        retry: int = 2,
    ) -> None:
        try:
            from redis import Redis
            from rq import Queue, Retry
        except ImportError:
            raise ImportError(
                "RQ publisher requires the 'rq' extra. "
                "Install it with: pip install axonpush[rq]"
            ) from None

        self._api_key: str = client._auth.api_key
        self._tenant_id: str = client._auth.tenant_id
        self._base_url: str = client._auth.base_url
        self._conn = redis_conn or Redis()
        self._queue: "Queue" = Queue(name=queue_name, connection=self._conn)
        self._job_timeout = job_timeout
        self._result_ttl = result_ttl
        self._failure_ttl = failure_ttl
        self._retry: "Retry" = Retry(max=retry)
        self._closed = False

    def submit(self, publish_kwargs: Dict[str, Any]) -> None:
        if self._closed:
            return
        try:
            self._queue.enqueue(
                _rq_publish_job,
                self._api_key,
                self._tenant_id,
                self._base_url,
                publish_kwargs,
                job_timeout=self._job_timeout,
                result_ttl=self._result_ttl,
                failure_ttl=self._failure_ttl,
                retry=self._retry,
            )
        except Exception as exc:
            _internal_logger.warning("axonpush rq enqueue failed: %s", exc)

    def flush(self, timeout: Optional[float] = None) -> None:
        pass

    def close(self) -> None:
        self._closed = True


def _rq_publish_job(
    api_key: str, tenant_id: str, base_url: str, publish_kwargs: Dict[str, Any],
) -> None:
    from axonpush.client import AxonPush

    with AxonPush(api_key=api_key, tenant_id=tenant_id, base_url=base_url) as client:
        client.events.publish(**publish_kwargs)


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

"""Background publisher utilities for AxonPush integrations.

Three publisher flavours are exposed:

* :class:`BackgroundPublisher` — owns a sync :class:`AxonPush` client and
  drains a bounded :class:`queue.Queue` from a daemon worker thread.
* :class:`AsyncBackgroundPublisher` — owns an :class:`AsyncAxonPush` client
  and drains a bounded :class:`asyncio.Queue` from a single background
  task on the running event loop.
* :class:`RqPublisher` — durable Redis-backed alternative for callers who
  install ``axonpush[rq]`` and run a separate ``rq worker`` process.

All three share the ``submit() / flush() / close()`` surface that the
integration layer codes against.

Re-entrancy guard
-----------------
Logging integrations (stdlib ``logging``, loguru, structlog) install a
sink that calls ``publisher.submit(...)``. The publisher then calls
``client.events.publish(...)`` which issues an ``httpx`` request — and
``httpx`` itself emits records through the stdlib ``logging`` module.
Without a guard, the user's logging handler captures those records and
re-enters ``submit()``, looping until the queue overflows.

We set a :class:`contextvars.ContextVar` (``_in_publisher_path``) for the
duration of every ``submit`` / publish call. Logging integrations check
the flag and drop records that originate inside the publisher path.

Overflow
--------
Bounded queues drop on full. The :class:`OverflowPolicy` enum picks
between ``DROP_OLDEST`` (default), ``DROP_NEWEST`` and ``BLOCK``. The
drop counter is rate-limited to one warning per
``DROP_WARNING_INTERVAL_S`` window via the stdlib ``axonpush.publisher``
logger at WARNING level.
"""
from __future__ import annotations

import asyncio
import atexit
import contextvars
import enum
import logging
import os
import queue
import threading
import time
import weakref
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Optional,
    Union,
)

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

_internal_logger = logging.getLogger("axonpush.publisher")

DEFAULT_QUEUE_SIZE = 1000
DEFAULT_SHUTDOWN_TIMEOUT_S = 2.0
DROP_WARNING_INTERVAL_S = 10.0

_SERVERLESS_MARKERS = (
    ("AWS_LAMBDA_FUNCTION_NAME", "AWS Lambda"),
    ("FUNCTION_TARGET", "Google Cloud Functions"),
    ("AZURE_FUNCTIONS_ENVIRONMENT", "Azure Functions"),
)


_in_publisher_path: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "_axonpush_in_publisher_path", default=False
)


def in_publisher_path() -> bool:
    """Return ``True`` if the current task/thread is inside a publish call.

    Logging integrations check this to short-circuit re-entry from records
    emitted by ``httpx`` / ``httpcore`` while the publisher itself is busy
    serialising a previous record.
    """
    return _in_publisher_path.get()


def detect_serverless() -> Optional[str]:
    """Return the human-readable name of the serverless host, or ``None``."""
    for env_var, name in _SERVERLESS_MARKERS:
        if os.environ.get(env_var):
            return name
    return None


class OverflowPolicy(str, enum.Enum):
    """How a bounded queue reacts when ``submit`` arrives at capacity."""

    DROP_OLDEST = "drop_oldest"
    DROP_NEWEST = "drop_newest"
    BLOCK = "block"


PublishKwargs = Dict[str, Any]


class _DropTracker:
    """Counts drops with a rate-limited warning emitter."""

    def __init__(self, what: str, capacity: int) -> None:
        self._what = what
        self._capacity = capacity
        self._lock = threading.Lock()
        self._dropped = 0
        self._last_warn = 0.0

    @property
    def total(self) -> int:
        with self._lock:
            return self._dropped

    def record(self) -> None:
        with self._lock:
            self._dropped += 1
            now = time.monotonic()
            if now - self._last_warn < DROP_WARNING_INTERVAL_S:
                return
            dropped = self._dropped
            self._last_warn = now
        _internal_logger.warning(
            "axonpush %s queue full; %d records dropped so far (capacity=%d) "
            "— consider increasing queue size or switching overflow policy",
            self._what,
            dropped,
            self._capacity,
        )


class BackgroundPublisher:
    """Sync, thread-backed publisher.

    Owns an :class:`AxonPush` client and drains a bounded
    :class:`queue.Queue` of publish kwargs from a daemon worker thread.
    Failures inside ``client.events.publish`` are caught and logged so a
    bad payload doesn't kill the worker.
    """

    def __init__(
        self,
        client: "AxonPush",
        *,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
        overflow_policy: OverflowPolicy = OverflowPolicy.DROP_OLDEST,
    ) -> None:
        self._client = client
        self._queue_size = queue_size
        self._shutdown_timeout = shutdown_timeout
        self._overflow_policy = overflow_policy
        self._queue: "queue.Queue[Optional[PublishKwargs]]" = queue.Queue(maxsize=queue_size)
        self._drops = _DropTracker("publisher", queue_size)
        self._close_lock = threading.Lock()
        self._closed = False
        self._thread: Optional[threading.Thread] = None
        self._start_worker()
        _LIVE_PUBLISHERS.add(self)

    def _start_worker(self) -> None:
        self._closed = False
        self._thread = threading.Thread(
            target=self._worker_loop,
            name="axonpush-publisher",
            daemon=True,
        )
        self._thread.start()

    def _worker_loop(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is None:
                    return
                token = _in_publisher_path.set(True)
                try:
                    self._client.events.publish(**item)
                except Exception as exc:
                    _internal_logger.warning("axonpush publish failed: %s", exc)
                finally:
                    _in_publisher_path.reset(token)
            finally:
                self._queue.task_done()

    def submit(self, publish_kwargs: PublishKwargs) -> None:
        """Enqueue a publish, dropping per ``overflow_policy`` when full."""
        if self._closed:
            return
        try:
            if self._overflow_policy is OverflowPolicy.BLOCK:
                self._queue.put(publish_kwargs)
                return
            self._queue.put_nowait(publish_kwargs)
        except queue.Full:
            self._drops.record()
            if self._overflow_policy is OverflowPolicy.DROP_OLDEST:
                try:
                    _ = self._queue.get_nowait()
                    self._queue.task_done()
                except queue.Empty:
                    return
                try:
                    self._queue.put_nowait(publish_kwargs)
                except queue.Full:
                    return

    @property
    def dropped(self) -> int:
        """Total number of records dropped since construction."""
        return self._drops.total

    # Backwards-compat read-only attribute used by existing tests.
    @property
    def _drop_counter(self) -> int:
        return self._drops.total

    def flush(self, timeout: Optional[float] = None) -> None:
        """Block until queued kwargs are published, or ``timeout`` elapses."""
        with self._queue.all_tasks_done:
            if timeout is None:
                while self._queue.unfinished_tasks:
                    self._queue.all_tasks_done.wait()
                return
            end = time.monotonic() + timeout
            while self._queue.unfinished_tasks:
                remaining = end - time.monotonic()
                if remaining <= 0:
                    break
                self._queue.all_tasks_done.wait(remaining)

    def close(self, timeout: Optional[float] = None) -> None:
        """Drain in-flight events and stop the worker. Idempotent."""
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
        self.flush(timeout=timeout if timeout is not None else self._shutdown_timeout)
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout if timeout is not None else self._shutdown_timeout)
        self._thread = None

    def _reset_after_fork(self) -> None:
        self._queue = queue.Queue(maxsize=self._queue_size)
        self._drops = _DropTracker("publisher", self._queue_size)
        self._close_lock = threading.Lock()
        self._thread = None
        self._start_worker()


class AsyncBackgroundPublisher:
    """Async, task-backed publisher.

    Owns an :class:`AsyncAxonPush` client and drains a bounded
    :class:`asyncio.Queue` from a single background task. ``submit`` is a
    plain method (not a coroutine) so it can be called from sync callback
    contexts (e.g. LangChain's ``BaseCallbackHandler.on_*`` hooks).
    """

    def __init__(
        self,
        client: "AsyncAxonPush",
        *,
        max_pending: int = DEFAULT_QUEUE_SIZE,
        overflow_policy: OverflowPolicy = OverflowPolicy.DROP_OLDEST,
    ) -> None:
        self._client = client
        self._max_pending = max_pending
        self._overflow_policy = overflow_policy
        self._drops = _DropTracker("async-publisher", max_pending)
        self._queue: Optional["asyncio.Queue[Optional[PublishKwargs]]"] = None
        self._worker: Optional[asyncio.Task[None]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._closed = False

    def _ensure_worker(self) -> Optional["asyncio.Queue[Optional[PublishKwargs]]"]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return None
        if self._queue is None or self._loop is not loop:
            self._loop = loop
            self._queue = asyncio.Queue(maxsize=self._max_pending)
            self._worker = loop.create_task(self._worker_loop(self._queue))
        return self._queue

    async def _worker_loop(
        self, q: "asyncio.Queue[Optional[PublishKwargs]]"
    ) -> None:
        while True:
            item = await q.get()
            try:
                if item is None:
                    return
                token = _in_publisher_path.set(True)
                try:
                    await self._client.events.publish(**item)
                except Exception as exc:
                    _internal_logger.warning("axonpush async publish failed: %s", exc)
                finally:
                    _in_publisher_path.reset(token)
            finally:
                q.task_done()

    def submit(self, publish_kwargs: PublishKwargs) -> None:
        """Enqueue a publish on the running event loop, drop on full."""
        if self._closed:
            return
        q = self._ensure_worker()
        if q is None:
            return
        if q.full():
            self._drops.record()
            if self._overflow_policy is OverflowPolicy.DROP_NEWEST:
                return
            if self._overflow_policy is OverflowPolicy.DROP_OLDEST:
                try:
                    _ = q.get_nowait()
                    q.task_done()
                except asyncio.QueueEmpty:
                    return
            # BLOCK isn't supported in the sync-submit path on async — fall
            # through and try put_nowait; if still full, give up.
        try:
            q.put_nowait(publish_kwargs)
        except asyncio.QueueFull:
            self._drops.record()

    @property
    def dropped(self) -> int:
        return self._drops.total

    async def flush(self, timeout: Optional[float] = None) -> None:
        """Wait for all queued items to be published, or until ``timeout``."""
        q = self._queue
        if q is None or q.empty():
            return
        join_task = asyncio.create_task(q.join())
        try:
            if timeout is None:
                await join_task
            else:
                await asyncio.wait_for(asyncio.shield(join_task), timeout=timeout)
        except asyncio.TimeoutError:
            join_task.cancel()
            try:
                await join_task
            except (asyncio.CancelledError, BaseException):  # noqa: BLE001
                pass

    async def aclose(self, timeout: Optional[float] = None) -> None:
        """Drain in-flight events, then stop the worker. Idempotent."""
        if self._closed:
            return
        self._closed = True
        await self.flush(timeout=timeout)
        if self._queue is not None:
            try:
                self._queue.put_nowait(None)
            except asyncio.QueueFull:
                pass
        if self._worker is not None and not self._worker.done():
            try:
                if timeout is None:
                    await self._worker
                else:
                    await asyncio.wait_for(asyncio.shield(self._worker), timeout=timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError, BaseException):  # noqa: BLE001
                pass
        self._worker = None

    async def close(self, timeout: Optional[float] = None) -> None:
        """Alias for :meth:`aclose`."""
        await self.aclose(timeout=timeout)


class RqPublisher:
    """Durable Redis-backed publisher using `python-rq <https://python-rq.org/>`_.

    Each ``submit()`` enqueues an RQ job; jobs are executed by a separate
    ``rq worker`` process so event publishing survives app restarts and is
    retried on transient failures. Requires ``pip install axonpush[rq]``.
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

        auth = client._auth  # type: ignore[union-attr]
        self._api_key: str = auth.api_key
        self._tenant_id: str = auth.tenant_id
        self._base_url: str = auth.base_url
        self._conn = redis_conn or Redis()
        self._queue: "Queue" = Queue(name=queue_name, connection=self._conn)
        self._job_timeout = job_timeout
        self._result_ttl = result_ttl
        self._failure_ttl = failure_ttl
        self._retry: "Retry" = Retry(max=retry)
        self._closed = False

    def submit(self, publish_kwargs: PublishKwargs) -> None:
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

    def flush(self, timeout: Optional[float] = None) -> None:  # noqa: ARG002
        return None

    def close(self) -> None:
        self._closed = True


def _rq_publish_job(
    api_key: str,
    tenant_id: str,
    base_url: str,
    publish_kwargs: PublishKwargs,
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


_FlushableT = Union[
    BackgroundPublisher,
    AsyncBackgroundPublisher,
    RqPublisher,
    Any,
]


def flush_after_invocation(
    *handlers: _FlushableT,
    timeout: Optional[float] = 5.0,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator: flush each handler after the wrapped function returns.

    Useful in serverless: wrap your Lambda handler so any queued events
    are flushed before the container is frozen.
    """

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

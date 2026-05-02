"""08 — Error handling.

Walk through the exception hierarchy. Every error subclasses
``AxonPushError`` and carries ``status_code``, ``code``, ``hint``, and
``request_id`` — pulled from the backend's standard
``{ code, message, hint, requestId }`` envelope.

``RetryableError`` is a marker mixin worn by ``APIConnectionError``,
``RateLimitError``, and ``ServerError`` — anything safe to retry.

Run::

    uv run examples/08_error_handling.py
"""

import uuid

from config import API_KEY, BASE_URL, ENVIRONMENT, TENANT_ID, require_credentials

require_credentials()

from axonpush import (  # noqa: E402
    AuthenticationError,
    AxonPush,
    AxonPushError,
    NotFoundError,
    RateLimitError,
    RetryableError,
    ValidationError,
)


def demo_auth_error() -> None:
    print("1. AuthenticationError (bad API key)")
    try:
        with AxonPush(api_key="ak_invalid_key", tenant_id=TENANT_ID, base_url=BASE_URL) as bad:
            bad.apps.list()
    except AuthenticationError as exc:
        print(f"   {type(exc).__name__}: {exc} (request_id={exc.request_id})")
    print()


def demo_not_found(client: AxonPush) -> None:
    print("2. NotFoundError (random UUID)")
    bogus = str(uuid.uuid4())
    try:
        client.apps.get(bogus)
    except NotFoundError as exc:
        print(f"   {type(exc).__name__}: status={exc.status_code} code={exc.code}")
    except AxonPushError as exc:
        print(f"   {type(exc).__name__}: {exc}")
    print()


def demo_validation_error(client: AxonPush) -> None:
    print("3. ValidationError (name too short)")
    try:
        client.apps.create(name="ab")
    except ValidationError as exc:
        print(f"   {type(exc).__name__}: {exc} (hint={exc.hint!r})")
    except AxonPushError as exc:
        print(f"   {type(exc).__name__}: {exc}")
    print()


def demo_retry_classification() -> None:
    print("4. Retry classification")
    print("   Anything that subclasses RetryableError is safe to retry:")
    print(f"     issubclass(RateLimitError, RetryableError) = {issubclass(RateLimitError, RetryableError)}")
    print("   Wire-level retry is built-in (max_retries kwarg). For app-level")
    print("   logic on RateLimitError, honour `exc.retry_after` (seconds).")
    print()


def demo_catch_all() -> None:
    print("5. Catch-all pattern")
    print("   try:")
    print("       client.events.publish(...)")
    print("   except AuthenticationError: ...")
    print("   except RateLimitError as exc: time.sleep(exc.retry_after or 1)")
    print("   except RetryableError: ...   # transient — back off and retry")
    print("   except AxonPushError: ...    # permanent — surface to caller")
    print()


def main() -> None:
    print("=== AxonPush error handling ===\n")
    demo_auth_error()

    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, environment=ENVIRONMENT) as client:
        demo_not_found(client)
        demo_validation_error(client)

    demo_retry_classification()
    demo_catch_all()
    print("Done.")


if __name__ == "__main__":
    main()

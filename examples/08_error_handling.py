"""
08 — Error Handling

Demonstrates how to handle various AxonPush errors gracefully.
Run: uv run 08_error_handling.py
"""

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AxonPush
from axonpush.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
    AxonPushError,
)


def demo_auth_error():
    print("1. AuthenticationError (bad API key)")
    try:
        with AxonPush(api_key="ak_invalid_key", tenant_id=TENANT_ID, base_url=BASE_URL) as client:
            client.apps.list()
    except AuthenticationError as e:
        print(f"   Caught: {e}")
    print()


def demo_not_found(client: AxonPush):
    print("2. Resource not found (bad ID)")
    try:
        client.apps.get(app_id=999999)
    except AxonPushError as e:
        print(f"   Caught: {type(e).__name__}: {e}")
    print()


def demo_validation_error(client: AxonPush):
    print("3. ValidationError (bad input)")
    try:
        client.apps.create(name="ab")
    except (ValidationError, AxonPushError) as e:
        print(f"   Caught: {type(e).__name__}: {e}")
    print()


def demo_rate_limit():
    print("4. RateLimitError (too many requests)")
    print("   RateLimitError has a retry_after attribute (seconds).")
    print("   try:")
    print("       client.events.publish(...)")
    print("   except RateLimitError as e:")
    print("       time.sleep(e.retry_after or 1)")
    print()


def demo_context_manager():
    print("5. Context manager pattern")
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        apps = client.apps.list()
        print(f"   Listed {len(apps)} apps inside context manager")
    print("   Context manager exited — connections closed cleanly.")
    print()


def demo_catch_all():
    print("6. Catch-all pattern")
    print("   try:")
    print("       client.events.publish(...)")
    print("   except AuthenticationError: ...")
    print("   except RateLimitError as e: ...")
    print("   except AxonPushError as e:  # catches all SDK errors")
    print("       ...")
    print()


def main():
    print("=== AxonPush Error Handling Patterns ===\n")

    demo_auth_error()

    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        demo_not_found(client)
        demo_validation_error(client)

    demo_rate_limit()
    demo_context_manager()
    demo_catch_all()
    print("Done.")


if __name__ == "__main__":
    main()

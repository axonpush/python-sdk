"""Tests for the shared integration helpers."""

from __future__ import annotations

import warnings

import pytest

from axonpush.integrations._utils import (
    build_resource,
    coerce_channel_id,
    fire_and_forget,
    safe_serialize,
)


class TestCoerceChannelId:
    def test_str_passes_through(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert coerce_channel_id("ch_abc") == "ch_abc"

    def test_int_emits_deprecation_and_stringifies(self) -> None:
        with pytest.warns(DeprecationWarning, match="channel_id as int is deprecated"):
            assert coerce_channel_id(42) == "42"

    def test_bool_rejected(self) -> None:
        with pytest.raises(TypeError, match="bool"):
            coerce_channel_id(True)  # type: ignore[arg-type]

    def test_unknown_type_rejected(self) -> None:
        with pytest.raises(TypeError):
            coerce_channel_id(3.14)  # type: ignore[arg-type]

    def test_warning_stacklevel_points_at_caller(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            def caller() -> str:
                return coerce_channel_id(7)

            caller()

        deps = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert len(deps) == 1
        # stacklevel=3 means the warning reports its origin two frames above
        # coerce_channel_id (caller's caller). We just assert the file is
        # this test's file so we know stacklevel isn't 1 (which would point
        # inside coerce_channel_id itself).
        assert deps[0].filename.endswith("test_utils.py")


class TestSafeSerialize:
    def test_passes_through_simple(self) -> None:
        assert safe_serialize({"a": 1}) == {"a": 1}

    def test_truncates_oversized_strings(self) -> None:
        result = safe_serialize("x" * 5000, max_len=100)
        assert isinstance(result, str)
        assert len(result) == 100

    def test_falls_back_to_str_on_unjsonable(self) -> None:
        class NonJSON:
            def __repr__(self) -> str:
                return "<custom>"

        result = safe_serialize(NonJSON())
        assert isinstance(result, str)


class TestBuildResource:
    def test_all_fields(self) -> None:
        r = build_resource(service_name="api", service_version="1.0", environment="prod")
        assert r == {
            "service.name": "api",
            "service.version": "1.0",
            "deployment.environment": "prod",
        }

    def test_partial(self) -> None:
        assert build_resource(service_name="api") == {"service.name": "api"}

    def test_none_when_empty(self) -> None:
        assert build_resource() is None


class TestFireAndForget:
    def test_no_op_for_non_coroutine(self) -> None:
        fire_and_forget(123)  # must not raise
        fire_and_forget(None)
        fire_and_forget("anything")

    async def test_schedules_coroutine(self) -> None:
        seen: list[int] = []

        async def coro() -> None:
            seen.append(1)

        fire_and_forget(coro())
        import asyncio

        await asyncio.sleep(0)
        assert seen == [1]

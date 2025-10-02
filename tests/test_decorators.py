"""Illustrative tests for Veriphi decorators."""

from __future__ import annotations

from typing import Any

from agent_sync import HookBundle, NullContext, veriphi_decorator


def _before(**details: Any) -> None:
    details["context"].bind(stage="before")
    details["context"].emit("hook:before", fn=details["fn"].__name__)


def _after(**details: Any) -> Any:
    details["context"].emit("hook:after", result=details["result"])
    return details["result"]


def test_can_wrap_function_with_prebuilt_hooks() -> None:
    hooks = HookBundle(before=_before, after=_after)

    @veriphi_decorator(hooks=hooks)
    def add(a: int, b: int) -> int:
        return a + b

    result = add(1, 2)

    assert result == 3


def test_can_override_context_per_call() -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def recorder(**details: Any) -> None:
        calls.append((details["context"].__class__.__name__, dict(details["kwargs"])))

    hooks = HookBundle(before=recorder)

    @veriphi_decorator(hooks=hooks)
    def sample(value: int, *, context: NullContext | None = None) -> int:  # noqa: D401 - intentionally thin wrapper
        return value * 2

    custom_context = NullContext()
    sample(10, context=custom_context)

    assert calls == [("NullContext", {"context": custom_context})]

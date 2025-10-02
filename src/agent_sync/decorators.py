"""Public decorator factory helpers."""

from __future__ import annotations

import functools
from collections.abc import Callable, Mapping as _Mapping
from typing import Any, ParamSpec, TypeVar, overload

from .context import ContextMapping, NullContext, VeriphiContext
from .hooks import HookBundle, HookFactory

P = ParamSpec("P")
R = TypeVar("R")


ContextProvider = Callable[[Callable[P, R], tuple[Any, ...], dict[str, Any]], VeriphiContext]
"""Resolve a :class:`VeriphiContext` for the decorated call."""


def _context_payload(context: VeriphiContext) -> ContextMapping:
    candidate = getattr(context, "metadata", {})
    if isinstance(candidate, _Mapping):
        return dict(candidate)
    if isinstance(candidate, dict):
        return candidate
    return {}


@overload
def veriphi_decorator(
    *,
    hooks: HookBundle[R] | None = None,
    hook_factory: None = None,
    context_provider: None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


@overload
def veriphi_decorator(
    *,
    hooks: None = None,
    hook_factory: HookFactory,
    context_provider: ContextProvider | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def veriphi_decorator(
    *,
    hooks: HookBundle[R] | None = None,
    hook_factory: HookFactory | None = None,
    context_provider: ContextProvider | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Return a decorator that wires in Veriphi lifecycle hooks.

    Parameters
    ----------
    hooks:
        Pre-built hook bundle that will be reused for every invocation.
    hook_factory:
        Callable that builds a bundle per invocation when additional context
        needs to be considered (for example, based on function arguments).
    context_provider:
        Strategy for supplying a :class:`VeriphiContext`. Defaults to
        :class:`NullContext` when omitted.
    """

    if hooks is None and hook_factory is None:
        hooks = HookBundle()

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            context = _resolve_context(fn, args, kwargs, provider=context_provider)
            payload = _context_payload(context)
            active_hooks = hook_factory(payload) if hook_factory else hooks
            assert active_hooks is not None  # for type checkers

            if active_hooks.before:
                active_hooks.before(context=context, fn=fn, args=args, kwargs=kwargs)

            try:
                result = fn(*args, **kwargs)
            except BaseException as error:  # pragma: no cover - defensive
                if active_hooks.on_error and active_hooks.on_error(
                    context=context,
                    fn=fn,
                    args=args,
                    kwargs=kwargs,
                    error=error,
                ):
                    return None  # type: ignore[return-value]
                raise

            if active_hooks.after:
                return active_hooks.after(
                    context=context,
                    fn=fn,
                    args=args,
                    kwargs=kwargs,
                    result=result,
                )
            return result

        return wrapper

    return decorator


def _resolve_context(
    fn: Callable[P, R],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    *,
    provider: ContextProvider | None,
) -> VeriphiContext:
    if provider:
        return provider(fn, args, kwargs)
    if "context" in kwargs:
        candidate = kwargs["context"]
        if isinstance(candidate, VeriphiContext):
            return candidate
    return NullContext()


__all__ = ["ContextProvider", "veriphi_decorator"]

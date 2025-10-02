"""Composable hook primitives used by Veriphi decorators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Protocol, TypeVar

from .context import ContextMapping, VeriphiContext

R = TypeVar("R")


class BeforeCall(Protocol):
    def __call__(
        self,
        *,
        context: VeriphiContext,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Executed prior to the wrapped function."""


class AfterCall(Protocol, Generic[R]):
    def __call__(
        self,
        *,
        context: VeriphiContext,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        result: R,
    ) -> R:
        """Executed after the wrapped function returns."""


class OnError(Protocol):
    def __call__(
        self,
        *,
        context: VeriphiContext,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        error: BaseException,
    ) -> bool:
        """Handle an exception; return True to suppress re-raise."""


@dataclass(slots=True)
class HookBundle(Generic[R]):
    """Container for optional lifecycle callbacks."""

    before: BeforeCall | None = None
    after: AfterCall[R] | None = None
    on_error: OnError | None = None

    def merge(self, other: "HookBundle[R]") -> "HookBundle[R]":
        """Combine two bundles, prioritising callbacks already present."""

        return HookBundle(
            before=self.before or other.before,
            after=self.after or other.after,
            on_error=self.on_error or other.on_error,
        )


HookFactory = Callable[[ContextMapping], HookBundle[Any]]
"""Callable that builds a :class:`HookBundle` from lightweight context data."""


__all__ = [
    "AfterCall",
    "BeforeCall",
    "HookBundle",
    "HookFactory",
    "OnError",
]

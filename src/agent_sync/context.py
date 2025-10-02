"""Context abstractions for Veriphi-aware decorators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping, Protocol, runtime_checkable


@runtime_checkable
class VeriphiContext(Protocol):
    """Represents the interaction surface Decorators expect.

    Concrete implementations can wrap request metadata, tenant details,
    security tokens, tracing identifiers, or any other runtime state that the
    Veriphi layer must see. The protocol is intentionally small so that
    projects can adapt their own context objects.
    """

    def bind(self, **metadata: Any) -> "VeriphiContext":
        """Return a context that includes additional metadata."""

    def emit(self, event: str, **payload: Any) -> None:
        """Publish an event or audit record to the host environment."""

    def ensure(self, requirement: str, **details: Any) -> None:
        """Enforce a requirement (permissions, invariants, etc.)."""


@dataclass(slots=True)
class NullContext:
    """Fallback context used when callers do not supply one explicitly."""

    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def bind(self, **metadata: Any) -> "NullContext":
        self.metadata.update(metadata)
        return self

    def emit(self, event: str, **payload: Any) -> None:  # pragma: no cover - noop
        self.metadata.setdefault("events", []).append((event, payload))

    def ensure(self, requirement: str, **details: Any) -> None:  # pragma: no cover - noop
        self.metadata.setdefault("requirements", []).append((requirement, details))


ContextMapping = Mapping[str, Any]
"""User-friendly alias for ad-hoc context payloads."""

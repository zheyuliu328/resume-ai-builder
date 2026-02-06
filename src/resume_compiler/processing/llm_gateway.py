from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol


class LLMGateway(Protocol):
    """Unified LLM gateway interface.

    A real implementation would handle retries, fallbacks, and token accounting.
    For Sprint 1 we keep it minimal and testable.
    """

    def generate_json(self, *, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class DummyLLMGateway:
    """A deterministic gateway used in local runs/tests.

    It returns an empty object by default; callers should be robust to missing fields.
    """

    fixed: Optional[dict[str, Any]] = None

    def generate_json(self, *, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        return dict(self.fixed or {})

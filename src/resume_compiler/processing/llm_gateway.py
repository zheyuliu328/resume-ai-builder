from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional, Protocol
import random


class LLMGateway(Protocol):
    """Unified LLM gateway interface.

    Implementations should:
    - return a JSON object (dict)
    - best-effort enforce a provided JSON-schema-like shape
    - handle retries / fallbacks
    - expose lightweight token usage in meta where available
    """

    def generate_json(self, *, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]: ...


def _extract_first_json_object(text: str) -> dict[str, Any]:
    """Extract the first JSON object from model output.

    Supports:
    - pure JSON
    - JSON fenced in ```json ... ```
    - JSON embedded in other text
    """

    t = text.strip()
    if not t:
        raise ValueError("empty model output")

    # Prefer fenced blocks
    if "```" in t:
        parts = t.split("```")
        for i in range(1, len(parts), 2):
            block = parts[i]
            # allow ```json
            block = block.lstrip()
            if block.lower().startswith("json"):
                block = block[4:]
            block = block.strip()
            if block.startswith("{") and block.endswith("}"):
                return json.loads(block)

    # If it's already a JSON object
    if t.startswith("{") and t.endswith("}"):
        return json.loads(t)

    # Try to find first {...} span
    start = t.find("{")
    if start == -1:
        raise ValueError("no JSON object found")

    depth = 0
    for idx in range(start, len(t)):
        ch = t[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = t[start : idx + 1]
                return json.loads(candidate)

    raise ValueError("unterminated JSON object")


def _validate_schema_loose(data: Any, schema: dict[str, Any], path: str = "$") -> None:
    """Very small subset validator (no external deps).

    Supports: object/array/string + required.
    It's intentionally minimal: we only need to catch obvious non-JSON / wrong-shape.
    """

    stype = schema.get("type")

    if stype == "object":
        if not isinstance(data, dict):
            raise ValueError(f"schema mismatch at {path}: expected object")
        required = schema.get("required") or []
        for k in required:
            if k not in data:
                raise ValueError(f"schema mismatch at {path}: missing required key '{k}'")
        props: dict[str, Any] = schema.get("properties") or {}
        for k, subschema in props.items():
            if k in data:
                _validate_schema_loose(data[k], subschema, path=f"{path}.{k}")
        return

    if stype == "array":
        if not isinstance(data, list):
            raise ValueError(f"schema mismatch at {path}: expected array")
        items = schema.get("items")
        if items:
            for i, item in enumerate(data[:50]):
                _validate_schema_loose(item, items, path=f"{path}[{i}]")
        return

    if stype == "string":
        if not isinstance(data, str):
            raise ValueError(f"schema mismatch at {path}: expected string")
        return

    # Unknown or unsupported: skip
    return


@dataclass
class DummyLLMGateway:
    """A deterministic gateway used in local runs/tests."""

    fixed: Optional[dict[str, Any]] = None

    def generate_json(self, *, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        out = dict(self.fixed or {})
        # best-effort validate to mimic real gateway contract
        _validate_schema_loose(out, schema)
        return out


@dataclass
class OpenAIChatLLMGateway:
    """OpenAI-compatible chat.completions gateway.

    Configuration via env vars:
    - RESUME_COMPILER_OPENAI_BASE_URL (default: https://api.openai.com/v1)
    - RESUME_COMPILER_OPENAI_API_KEY (required)
    - RESUME_COMPILER_OPENAI_MODEL (default: gpt-4.1-mini)
    - RESUME_COMPILER_OPENAI_FALLBACK_MODEL (optional)
    - RESUME_COMPILER_OPENAI_FALLBACK_TO_DUMMY (optional: 1/true to enable)
    - RESUME_COMPILER_OPENAI_MAX_RETRIES (optional, default: 2)
    - RESUME_COMPILER_OPENAI_BACKOFF_BASE_SECONDS (optional, default: 0.5)
    - RESUME_COMPILER_OPENAI_BACKOFF_JITTER_SECONDS (optional, default: 0.0)
    """

    base_url: str
    api_key: str
    model: str
    fallback_model: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 2
    fallback_to_dummy: bool = False
    backoff_base_seconds: float = 0.5
    backoff_jitter_seconds: float = 0.0

    @classmethod
    def from_env(cls) -> "OpenAIChatLLMGateway":
        base_url = os.getenv("RESUME_COMPILER_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        api_key = os.getenv("RESUME_COMPILER_OPENAI_API_KEY") or ""
        model = os.getenv("RESUME_COMPILER_OPENAI_MODEL", "gpt-4.1-mini")
        fallback_model = os.getenv("RESUME_COMPILER_OPENAI_FALLBACK_MODEL")

        fallback_to_dummy_raw = (os.getenv("RESUME_COMPILER_OPENAI_FALLBACK_TO_DUMMY") or "").strip().lower()
        fallback_to_dummy = fallback_to_dummy_raw in {"1", "true", "yes", "y", "on"}

        max_retries = int(os.getenv("RESUME_COMPILER_OPENAI_MAX_RETRIES", "2"))
        backoff_base_seconds = float(os.getenv("RESUME_COMPILER_OPENAI_BACKOFF_BASE_SECONDS", "0.5"))
        backoff_jitter_seconds = float(os.getenv("RESUME_COMPILER_OPENAI_BACKOFF_JITTER_SECONDS", "0.0"))

        if not api_key:
            raise RuntimeError("RESUME_COMPILER_OPENAI_API_KEY is required for real LLM gateway")
        return cls(
            base_url=base_url,
            api_key=api_key,
            model=model,
            fallback_model=fallback_model,
            max_retries=max_retries,
            fallback_to_dummy=fallback_to_dummy,
            backoff_base_seconds=backoff_base_seconds,
            backoff_jitter_seconds=backoff_jitter_seconds,
        )

    def _post_json(self, *, url: str, body: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "resume-ai-builder/llm-gateway",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
            raise RuntimeError(f"HTTP {e.code} from LLM provider: {raw[:500]}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"LLM provider connection error: {e}") from e

    def _sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def generate_json(self, *, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        attempts_meta: list[dict[str, Any]] = []
        last_err: Exception | None = None

        for model in models_to_try:
            for attempt in range(self.max_retries + 1):
                try:
                    out = self._generate_json_once(system=system, user=user, schema=schema, model=model)
                    out.setdefault("_meta", {})
                    if isinstance(out.get("_meta"), dict):
                        out["_meta"].setdefault("attempts", attempts_meta)
                        out["_meta"].setdefault("model", model)
                    return out
                except Exception as e:
                    last_err = e
                    attempts_meta.append(
                        {
                            "model": model,
                            "attempt": attempt + 1,
                            "error": f"{type(e).__name__}: {e}",
                        }
                    )

                    if attempt < self.max_retries:
                        base = self.backoff_base_seconds * (2**attempt)
                        jitter = (random.random() * self.backoff_jitter_seconds) if self.backoff_jitter_seconds > 0 else 0.0
                        self._sleep(base + jitter)
                        continue
                    break

        if self.fallback_to_dummy:
            # Last resort downgrade. Dummy gateway still validates schema (may still raise).
            out = DummyLLMGateway().generate_json(system=system, user=user, schema=schema)
            out.setdefault("_meta", {})
            if isinstance(out.get("_meta"), dict):
                out["_meta"].setdefault("attempts", attempts_meta)
                out["_meta"].setdefault("downgraded_to", "dummy")
            return out

        assert last_err is not None
        raise last_err

    def _generate_json_once(
        self, *, system: str, user: str, schema: dict[str, Any], model: str
    ) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"

        # We instruct strict JSON output. Provider/model may ignore; we'll still extract+validate.
        schema_hint = json.dumps(schema, ensure_ascii=False)
        sys = (
            system.strip()
            + "\n\n"
            + "You MUST output a single JSON object that conforms to the following schema (best effort). "
            + "Do not wrap in markdown unless explicitly asked.\n"
            + f"Schema: {schema_hint}"
        )

        body = {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
        }

        resp = self._post_json(url=url, body=body)
        content = (
            ((resp.get("choices") or [{}])[0].get("message") or {}).get("content")
            or ""
        )

        data = _extract_first_json_object(content)
        _validate_schema_loose(data, schema)

        # Attach usage if present (non-schema meta; caller may ignore)
        usage = resp.get("usage")
        if isinstance(usage, dict):
            data.setdefault("_meta", {})
            if isinstance(data["_meta"], dict):
                data["_meta"].setdefault("usage", usage)
                data["_meta"].setdefault("model", model)

        return data

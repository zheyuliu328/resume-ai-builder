from __future__ import annotations

import pytest

from resume_compiler.processing.llm_gateway import (
    OpenAIChatLLMGateway,
    _extract_first_json_object,
    _validate_schema_loose,
)


def test_extract_first_json_object_fenced():
    txt = """some text
```json
{"a": 1}
```
more text"""
    assert _extract_first_json_object(txt) == {"a": 1}


def test_extract_first_json_object_embedded():
    txt = "prefix {\"a\": 1, \"b\": {\"c\": 2}} suffix"
    assert _extract_first_json_object(txt) == {"a": 1, "b": {"c": 2}}


def test_validate_schema_loose_basic():
    schema = {
        "type": "object",
        "properties": {"x": {"type": "string"}},
        "required": ["x"],
    }
    _validate_schema_loose({"x": "ok"}, schema)
    with pytest.raises(ValueError):
        _validate_schema_loose({"x": 123}, schema)


def test_openai_gateway_parses_and_validates(monkeypatch):
    schema = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}

    gw = OpenAIChatLLMGateway(base_url="http://example", api_key="k", model="m")

    def fake_post_json(*, url, body):
        # Simulate OpenAI chat.completions payload
        return {
            "choices": [{"message": {"content": "{\"x\": \"ok\"}"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        }

    monkeypatch.setattr(gw, "_post_json", fake_post_json)

    out = gw.generate_json(system="s", user="u", schema=schema)
    assert out["x"] == "ok"
    assert out["_meta"]["usage"]["total_tokens"] == 3


def test_openai_gateway_retries_on_bad_json_then_succeeds(monkeypatch):
    schema = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}

    gw = OpenAIChatLLMGateway(
        base_url="http://example",
        api_key="k",
        model="m",
        max_retries=2,
        backoff_base_seconds=0.0,
        backoff_jitter_seconds=0.0,
    )

    calls = {"n": 0}

    def fake_post_json(*, url, body):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"choices": [{"message": {"content": "not json"}}]}
        return {"choices": [{"message": {"content": "{\"x\": \"ok\"}"}}]}

    monkeypatch.setattr(gw, "_post_json", fake_post_json)
    monkeypatch.setattr(gw, "_sleep", lambda _s: None)

    out = gw.generate_json(system="s", user="u", schema=schema)
    assert out["x"] == "ok"
    assert calls["n"] == 2
    assert isinstance(out.get("_meta", {}).get("attempts"), list)
    assert len(out["_meta"]["attempts"]) >= 1


def test_openai_gateway_uses_fallback_model(monkeypatch):
    schema = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}

    gw = OpenAIChatLLMGateway(
        base_url="http://example",
        api_key="k",
        model="m1",
        fallback_model="m2",
        max_retries=0,
        backoff_base_seconds=0.0,
        backoff_jitter_seconds=0.0,
    )

    def fake_post_json(*, url, body):
        # Only fallback model returns valid JSON
        if body.get("model") == "m1":
            return {"choices": [{"message": {"content": "not json"}}]}
        return {"choices": [{"message": {"content": "{\"x\": \"ok\"}"}}]}

    monkeypatch.setattr(gw, "_post_json", fake_post_json)

    out = gw.generate_json(system="s", user="u", schema=schema)
    assert out["x"] == "ok"
    assert out["_meta"]["model"] == "m2"

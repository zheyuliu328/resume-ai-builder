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

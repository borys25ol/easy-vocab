import json
import types
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from fastapi import HTTPException
from openai import APITimeoutError

from app.services import genai_service


def make_response(content: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))]
    )


def fake_openai_factory(handler: Callable[..., types.SimpleNamespace]) -> type:
    class FakeOpenAI:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=self._create)
            )

        def _create(self, **kwargs: Any) -> types.SimpleNamespace:
            return handler(**kwargs)

    return FakeOpenAI


def build_payload(level: str = "A1") -> dict[str, Any]:
    return {
        "word": "house",
        "level": level,
        "type": "word",
        "is_phrasal": False,
        "is_idiom": False,
        "frequency": 3,
        "rank": 150,
        "rank_range": "1-500",
        "frequency_group": "Core 500",
        "translation": "будинок",
        "category": "Nouns",
        "synonyms": ["home", "dwelling"],
        "meanings": [
            {
                "partOfSpeech": "noun",
                "definitions": [
                    {
                        "definition": "A building for humans.",
                        "example": "A house is big.",
                    }
                ],
            }
        ],
    }


def make_timeout_error() -> APITimeoutError:
    request = httpx.Request("POST", "https://example.com")
    return APITimeoutError(request=request)


def setup_llm_settings(
    monkeypatch: pytest.MonkeyPatch,
    retries: int,
    fallback_models: list[str],
) -> None:
    monkeypatch.setattr(genai_service.settings, "OPENROUTER_MAX_RETRIES", retries)
    monkeypatch.setattr(
        genai_service.settings, "OPENROUTER_FALLBACK_MODELS", fallback_models
    )
    monkeypatch.setattr(
        genai_service.settings,
        "OPENROUTER_MODEL",
        "google/gemini-2.5-flash",
    )


def test_get_usage_examples_success(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(build_payload())

    def handler(**kwargs: Any) -> types.SimpleNamespace:
        return make_response(payload)

    monkeypatch.setattr(genai_service, "OpenAI", fake_openai_factory(handler))
    monkeypatch.setattr(genai_service, "_sleep_with_backoff", lambda _: None)
    setup_llm_settings(monkeypatch, retries=0, fallback_models=[])

    result = genai_service.get_usage_examples("house")

    assert result.word == "house"
    assert result.translation == "будинок"
    assert result.synonyms == "home, dwelling"
    assert result.examples == "(noun) A house is big."


def test_get_usage_examples_retries_on_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = [json.dumps(build_payload(level="Z9")), json.dumps(build_payload())]
    calls = {"count": 0}

    def handler(**kwargs: Any) -> types.SimpleNamespace:
        payload = payloads[calls["count"]]
        calls["count"] += 1
        return make_response(payload)

    monkeypatch.setattr(genai_service, "OpenAI", fake_openai_factory(handler))
    monkeypatch.setattr(genai_service, "_sleep_with_backoff", lambda _: None)
    setup_llm_settings(monkeypatch, retries=1, fallback_models=[])

    result = genai_service.get_usage_examples("house")

    assert calls["count"] == 2
    assert result.level == "A1"


def test_get_usage_examples_fallback_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps(build_payload())
    models_used: list[str] = []

    def handler(**kwargs: Any) -> types.SimpleNamespace:
        models_used.append(kwargs["model"])
        if kwargs["model"] == "google/gemini-2.5-flash":
            raise make_timeout_error()
        return make_response(payload)

    monkeypatch.setattr(genai_service, "OpenAI", fake_openai_factory(handler))
    monkeypatch.setattr(genai_service, "_sleep_with_backoff", lambda _: None)
    setup_llm_settings(
        monkeypatch, retries=0, fallback_models=["google/gemini-2.5-pro"]
    )

    result = genai_service.get_usage_examples("house")

    assert models_used == ["google/gemini-2.5-flash", "google/gemini-2.5-pro"]
    assert result.word == "house"


def test_get_usage_examples_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(**kwargs: Any) -> types.SimpleNamespace:
        raise make_timeout_error()

    monkeypatch.setattr(genai_service, "OpenAI", fake_openai_factory(handler))
    monkeypatch.setattr(genai_service, "_sleep_with_backoff", lambda _: None)
    setup_llm_settings(monkeypatch, retries=0, fallback_models=[])

    with pytest.raises(HTTPException) as exc_info:
        genai_service.get_usage_examples("house")

    assert exc_info.value.status_code == 502

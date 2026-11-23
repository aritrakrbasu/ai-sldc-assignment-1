"""LLM clients (T014, research R2/R3). ``GeminiClient`` talks to the Google Gemini API;
``FakeLLM`` is a scripted deterministic stand-in used by unit/contract tests."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Protocol

from moneylens.config import Settings

RETRY_STATUS = {408, 429, 500, 502, 503, 504}
_UNSUPPORTED_KEYS = {"$schema", "$id", "title", "allOf"}


class ServiceError(Exception):
    """The model service was unavailable (network, quota, 5xx, timeout) - not an app error."""


class LLMClient(Protocol):
    model: str
    model_version: str | None
    temperature: float

    def generate_json(self, system: str, user: str, schema: dict) -> str: ...


def _strip(schema: object) -> object:
    """Drop JSON-Schema keywords the model endpoint does not need; full validation is done
    locally against the complete schema afterwards (constitution I)."""
    if isinstance(schema, dict):
        return {k: _strip(v) for k, v in schema.items() if k not in _UNSUPPORTED_KEYS}
    if isinstance(schema, list):
        return [_strip(v) for v in schema]
    return schema


class GeminiClient:
    def __init__(self, model: str, temperature: float, api_key: str, rpm: int = 10,
                 attempts: int = 3) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self.model = model
        self.model_version: str | None = None
        self.temperature = temperature
        self._interval = 60.0 / rpm if rpm > 0 else 0.0
        self._attempts = attempts
        self._lock = threading.Lock()
        self._next_slot = 0.0
        self._schema_supported = True

    @classmethod
    def from_settings(cls, settings: Settings) -> GeminiClient:
        import os

        key = settings.api_key()
        if not key or not settings.model:
            raise ServiceError("Gemini is not configured (GEMINI_API_KEY / MONEYLENS_MODEL)")
        return cls(settings.model, settings.temperature, key,
                   rpm=int(os.environ.get("MONEYLENS_RPM", "10")))

    def _wait_for_slot(self) -> None:
        with self._lock:
            now = time.monotonic()
            slot = max(now, self._next_slot)
            self._next_slot = slot + self._interval
        if slot > now:
            time.sleep(slot - now)

    def _config(self, system: str, schema: dict):
        from google.genai import types

        kwargs = {"temperature": self.temperature, "system_instruction": system,
                  "response_mime_type": "application/json"}
        if self._schema_supported:
            kwargs["response_json_schema"] = _strip(schema)
        return types.GenerateContentConfig(**kwargs)

    def generate_json(self, system: str, user: str, schema: dict) -> str:
        from google.genai import errors

        delay = 2.0
        last: Exception | None = None
        for attempt in range(self._attempts):
            self._wait_for_slot()
            try:
                resp = self._client.models.generate_content(
                    model=self.model, contents=user, config=self._config(system, schema))
                self.model_version = getattr(resp, "model_version", None) or self.model_version
                return resp.text or ""
            except errors.APIError as exc:
                code = getattr(exc, "code", None)
                if code == 400 and self._schema_supported and "schema" in str(exc).lower():
                    self._schema_supported = False  # research R2 fallback: JSON mode only
                    continue
                if code not in RETRY_STATUS:
                    raise ServiceError(f"model API error {code}") from exc
                last = exc
            except (OSError, TimeoutError) as exc:  # network failures
                last = exc
            if attempt + 1 < self._attempts:
                time.sleep(delay)
                delay *= 4
        raise ServiceError(f"model unavailable after {self._attempts} attempts") from last


Response = str | Exception


class FakeLLM:
    """Scripted responses (list consumed in order, thread-safe) or a callable(system, user)."""

    def __init__(self, responses: list[Response] | Callable[[str, str], Response] | None = None):
        self.model = "fake-llm"
        self.model_version = "fake-1"
        self.temperature = 0.0
        self._responses = responses if responses is not None else []
        self._lock = threading.Lock()
        self.calls: list[dict] = []

    def generate_json(self, system: str, user: str, schema: dict) -> str:
        with self._lock:
            self.calls.append({"system": system, "user": user})
            if callable(self._responses):
                item = self._responses(system, user)
            elif self._responses:
                item = self._responses.pop(0)
            else:
                raise AssertionError("FakeLLM: no scripted response left")
        if isinstance(item, Exception):
            raise item
        return item

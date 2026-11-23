"""Runtime settings (T004). The API key is read from the environment / git-ignored .env and is
never logged, returned by the API or written to evidence (constitution III)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PART_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    model: str | None
    temperature: float
    splitease_url: str
    key_configured: bool

    def api_key(self) -> str | None:
        """Read the key only at the moment a client is created; never stored on the object."""
        return os.environ.get("GEMINI_API_KEY") or None


def load_settings() -> Settings:
    load_dotenv(PART_ROOT / ".env", override=False)
    return Settings(
        model=os.environ.get("MONEYLENS_MODEL") or None,
        temperature=float(os.environ.get("MONEYLENS_TEMPERATURE", "0.2")),
        splitease_url=os.environ.get("SPLITEASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        key_configured=bool(os.environ.get("GEMINI_API_KEY")),
    )

"""Pick the newest stable Gemini *flash* model available to the configured key (T005, research R1).

Writes MONEYLENS_MODEL=<id> into Part-1B/.env and prints only the chosen id and candidates.
The API key itself is never printed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from dotenv import load_dotenv, set_key
from google import genai

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
EXCLUDE = ("preview", "exp", "lite", "tts", "image", "live", "audio", "thinking", "embedding")


def version_key(model_id: str) -> tuple:
    nums = re.findall(r"\d+(?:\.\d+)?", model_id)
    return tuple(float(n) for n in nums) or (0.0,)


def main() -> int:
    load_dotenv(ENV)
    client = genai.Client()  # reads GEMINI_API_KEY from the environment
    candidates = []
    for m in client.models.list():
        name = (m.name or "").removeprefix("models/")
        actions = getattr(m, "supported_actions", None) or []
        if "flash" not in name or any(x in name for x in EXCLUDE):
            continue
        if actions and "generateContent" not in actions:
            continue
        candidates.append(name)
    if not candidates:
        print("No stable flash model found for this key.", file=sys.stderr)
        return 1
    candidates.sort(key=version_key, reverse=True)
    chosen = candidates[0]
    set_key(str(ENV), "MONEYLENS_MODEL", chosen, quote_mode="never")
    print("candidates:", ", ".join(candidates))
    print("selected MONEYLENS_MODEL =", chosen)
    return 0


if __name__ == "__main__":
    sys.exit(main())

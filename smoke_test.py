"""Smoke test — verify GROQ_API_KEY (chat) and GROQ_BACKUP_API_KEY (classifier) both work."""
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv(override=True)

import os
from groq import Groq

_GREEN = "\033[32m"
_RED   = "\033[31m"
_RESET = "\033[0m"

def _ok(label: str, detail: str) -> None:
    print(f"{_GREEN}✅ {label}{_RESET}  →  {detail}")

def _fail(label: str, detail: str) -> None:
    print(f"{_RED}❌ {label}{_RESET}  →  {detail}")


def test_chat(api_key: str | None) -> bool:
    """Primary key: send a minimal chat message and expect a non-empty reply."""
    if not api_key:
        _fail("GROQ_API_KEY (chat)", "not set in .env")
        return False
    try:
        client = Groq(api_key=api_key, timeout=15.0)
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "say hi in one word"}],
            max_completion_tokens=8,
            temperature=0.0,
        )
        reply = (resp.choices[0].message.content or "").strip()
        if reply:
            _ok("GROQ_API_KEY (chat)", f"model replied → {reply!r}")
            return True
        _fail("GROQ_API_KEY (chat)", "empty response")
        return False
    except Exception as e:
        _fail("GROQ_API_KEY (chat)", str(e))
        return False


def test_classifier(api_key: str | None) -> bool:
    """Backup key: run the boolean profile-gate classifier using streaming."""
    if not api_key:
        _fail("GROQ_BACKUP_API_KEY (classifier)", "not set in .env")
        return False
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": "say hi in one word",
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        raw = "".join(chunk.choices[0].delta.content or "" for chunk in completion).strip()
        if raw:
            _ok("GROQ_BACKUP_API_KEY (classifier)", f"key valid, got → {raw!r}")
            return True
        _fail("GROQ_BACKUP_API_KEY (classifier)", "empty response")
        return False
    except Exception as e:
        _fail("GROQ_BACKUP_API_KEY (classifier)", str(e))
        return False


if __name__ == "__main__":
    chat_ok       = test_chat(os.getenv("GROQ_API_KEY"))
    classifier_ok = test_classifier(os.getenv("GROQ_BACKUP_API_KEY"))

    print()
    if chat_ok and classifier_ok:
        print("All good — both keys work.")
    else:
        print("One or more keys failed. Check your .env and rotate at console.groq.com.")

"""
Classify recent screen activity using already-extracted text, not vision.

Goal: query screenpipe's local search API for text captured in the last
few minutes (accessibility-tree text first, OCR as a fallback), then ask a
small local model (via Ollama) to classify what the user was likely doing.

This intentionally avoids feeding raw screenshots to a vision model — text
already extracted by screenpipe's own accessibility/OCR pipeline is more
reliable than re-deriving it from pixels, and a small local text model is
far cheaper and faster than a vision model for this kind of judgment call.

Prerequisites:
- screenpipe must already be running (`screenpipe record`) and reachable
  at http://localhost:3030
- Ollama must be running locally with a model pulled, e.g.:
    ollama pull llama3.2:3b

Run: python classify_recent_activity.py [--minutes 5]
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import requests

SCREENPIPE_API = "http://localhost:3030"
OLLAMA_API = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"

LABELS = [
    "writing",
    "coding",
    "reading",
    "researching",
    "communicating",
    "browsing_entertainment",
    "idle",
    "confused_or_stuck",
]

PROMPT_TEMPLATE = (
    "You are looking at text extracted from a user's screen over the last "
    "few minutes (not the raw screenshots, just the text that was visible). "
    "Classify what the user was most likely doing into exactly one of these "
    "categories: {labels}. "
    "Respond with only the category name, nothing else.\n\n"
    "Screen text:\n{text}"
)


def get_api_token() -> str:
    result = subprocess.run(
        ["./target/release/screenpipe", "auth", "token"],
        cwd="..", capture_output=True, text=True, check=True,
    )
    # stdout may include log lines; the token is the last non-empty line
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines[-1]


def fetch_recent_text(token: str, minutes: int) -> str:
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "limit": 50,
    }

    chunks = []
    for content_type in ("accessibility", "ocr"):
        resp = requests.get(
            f"{SCREENPIPE_API}/search",
            headers=headers,
            params={**params, "content_type": content_type},
            timeout=10,
        )
        resp.raise_for_status()
        for item in resp.json().get("data", []):
            text = item.get("content", {}).get("text", "").strip()
            if text:
                chunks.append(text)
        if chunks:
            # accessibility text is preferred; only fall back to OCR if empty
            break

    # de-duplicate consecutive near-identical captures (common with frequent polling)
    deduped = []
    for chunk in chunks:
        if not deduped or chunk != deduped[-1]:
            deduped.append(chunk)
    return "\n---\n".join(deduped)


def classify(text: str) -> str:
    prompt = PROMPT_TEMPLATE.format(labels=", ".join(LABELS), text=text[:6000])
    resp = requests.post(
        f"{OLLAMA_API}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=5,
                         help="How many minutes of recent activity to classify")
    args = parser.parse_args()

    try:
        token = get_api_token()
    except Exception as e:
        print(f"Could not get API token — is screenpipe built and set up? ({e})")
        sys.exit(1)

    text = fetch_recent_text(token, args.minutes)
    if not text:
        print(f"No screen text captured in the last {args.minutes} minute(s). "
              f"Is `screenpipe record` running?")
        sys.exit(1)

    print(f"Captured text ({len(text)} chars):")
    print(text[:500] + ("..." if len(text) > 500 else ""))
    print()

    label = classify(text)
    print(f"Classification: {label}")


if __name__ == "__main__":
    main()

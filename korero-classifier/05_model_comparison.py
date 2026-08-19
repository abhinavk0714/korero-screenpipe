"""
Step 5: Compare local text models on real captured data.

Two comparisons, both against the same already-captured session (a scripted
~4-minute sequence of known activities, so ground truth is known):

1. Per-window: one classification per activity segment, using the full
   text captured during that segment. Matches how the classifier is meant
   to be used in practice.
2. Per-capture: one classification per individual timestamped capture,
   across the whole session. More granular — shows whether a model stays
   consistent as the same page is captured multiple times in a row, or
   flickers between labels for no reason.

Boundaries for "researching" / "off_task_entertainment" / "communicating"
below are content-verified (checked against actual captured URLs/text),
not just the original rough timer boundaries — the original timer-based
boundaries didn't line up with when the on-screen content actually changed.

Run: python 05_model_comparison.py
"""

import subprocess
import sys

import requests

SCREENPIPE_API = "http://localhost:3030"
OLLAMA_API = "http://localhost:11434"
MODELS = ["llama3.2:3b", "qwen2.5:3b", "phi3.5"]

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
    "You are looking at text extracted from a user's screen (not the raw "
    "screenshot, just the text that was visible). "
    "Classify what the user was most likely doing into exactly one of these "
    "categories: {labels}. "
    "Respond with only the category name, nothing else.\n\n"
    "Screen text:\n{text}"
)

# (label, start, end) — content-verified where corrected, original timer
# boundaries otherwise
WINDOWS = [
    ("writing", "2026-08-19T00:08:48Z", "2026-08-19T00:09:18Z"),
    ("researching", "2026-08-19T00:09:50Z", "2026-08-19T00:10:05Z"),
    ("off_task_entertainment", "2026-08-19T00:10:05Z", "2026-08-19T00:10:37Z"),
    ("communicating", "2026-08-19T00:10:37Z", "2026-08-19T00:11:16Z"),
    ("reading", "2026-08-19T00:11:16Z", "2026-08-19T00:11:50Z"),
    ("idle", "2026-08-19T00:11:50Z", "2026-08-19T00:12:24Z"),
]

SESSION_START = "2026-08-19T00:08:48Z"
SESSION_END = "2026-08-19T00:12:24Z"


def get_api_token() -> str:
    result = subprocess.run(
        ["./target/release/screenpipe", "auth", "token"],
        cwd="..", capture_output=True, text=True, check=True,
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines[-1]


def fetch_window_text(token: str, start: str, end: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    params = {"start_time": start, "end_time": end, "limit": 50}
    chunks = []
    for content_type in ("accessibility", "ocr"):
        resp = requests.get(f"{SCREENPIPE_API}/search", headers=headers,
                             params={**params, "content_type": content_type}, timeout=10)
        resp.raise_for_status()
        for item in resp.json().get("data", []):
            text = item.get("content", {}).get("text", "").strip()
            if text:
                chunks.append(text)
        if chunks:
            break
    deduped = []
    for chunk in chunks:
        if not deduped or chunk != deduped[-1]:
            deduped.append(chunk)
    return "\n---\n".join(deduped)


def fetch_individual_captures(token: str, start: str, end: str):
    """Returns [(timestamp, url_or_app, text), ...] — one entry per raw
    capture, deduplicated on identical consecutive text (many captures in
    a row show the same unchanged page)."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"start_time": start, "end_time": end, "limit": 100}
    captures = []
    for content_type in ("accessibility", "ocr"):
        resp = requests.get(f"{SCREENPIPE_API}/search", headers=headers,
                             params={**params, "content_type": content_type}, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if data:
            for item in reversed(data):  # API returns newest-first; walk chronologically
                c = item.get("content", {})
                text = (c.get("text") or "").strip()
                if text:
                    label = c.get("browser_url") or c.get("app_name") or "?"
                    captures.append((c.get("timestamp"), label, text))
            break
    deduped = []
    for ts, label, text in captures:
        if not deduped or text != deduped[-1][2]:
            deduped.append((ts, label, text))
    return deduped


def classify(model: str, text: str) -> str:
    prompt = PROMPT_TEMPLATE.format(labels=", ".join(LABELS), text=text[:6000])
    resp = requests.post(
        f"{OLLAMA_API}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False,
              "options": {"temperature": 0, "seed": 42}},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def main():
    try:
        token = get_api_token()
    except Exception as e:
        print(f"Could not get API token — is screenpipe running? ({e})")
        sys.exit(1)

    print("=" * 70)
    print("PART 1: per-window classification (one label per activity segment)")
    print("=" * 70)
    for true_label, start, end in WINDOWS:
        text = fetch_window_text(token, start, end)
        if not text:
            print(f"\n{true_label}: no text captured in this window, skipping")
            continue
        print(f"\n--- {true_label} ({start} to {end}) ---")
        for model in MODELS:
            pred = classify(model, text)
            match = "✓" if true_label.split("_")[0] in pred.lower() else "?"
            print(f"  {model:15s} -> {pred:30s} {match}")

    print("\n" + "=" * 70)
    print("PART 2: per-capture classification (every individual capture)")
    print("=" * 70)
    captures = fetch_individual_captures(token, SESSION_START, SESSION_END)
    print(f"\n{len(captures)} distinct captures in session\n")
    for ts, url_or_app, text in captures:
        print(f"[{ts}] {url_or_app}")
        for model in MODELS:
            pred = classify(model, text)
            print(f"  {model:15s} -> {pred}")
        print()


if __name__ == "__main__":
    main()

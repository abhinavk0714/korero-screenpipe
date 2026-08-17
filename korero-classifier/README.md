# Activity classifier (text-based, local)

A small script that classifies recent screen activity using screenpipe's
already-extracted text (accessibility-tree text, falling back to OCR),
rather than feeding raw screenshots to a vision model. A local model
(via [Ollama](https://ollama.com)) does the classification, so this runs
entirely offline with no cloud dependency.

## Why text instead of vision

Screenpipe already extracts text from the screen two ways: directly from
the OS accessibility API (fast, exact, no error possible) and via OCR as a
fallback for content that doesn't expose accessibility text. Re-deriving
that same text by feeding a screenshot to a vision-language model would
just reintroduce OCR error for no benefit, and vision models are slower
and heavier than a small text-only model doing a straightforward
classification task.

## Setup

```bash
# Ollama, if not already installed
brew install ollama
ollama serve &
ollama pull llama3.2:3b
```

```bash
cd korero-classifier
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

1. Make sure screenpipe is running:
   ```bash
   ./target/release/screenpipe record --disable-audio --disable-telemetry
   ```
   (`--disable-audio` since this classifier doesn't use it; `--disable-telemetry`
   to keep everything fully local, no anonymous usage events sent externally.)
2. Make sure `ollama serve` is running with `llama3.2:3b` pulled.
3. Run:

```bash
python classify_recent_activity.py --minutes 5
```

This pulls the last N minutes of captured text, prints a preview of it,
and prints a single classification label.

## Labels

A small generic set, intended as a starting point rather than a final
answer:

```
writing, coding, reading, researching, communicating, browsing_entertainment, idle, confused_or_stuck
```

`confused_or_stuck` is the most interesting one to validate — whether a
local model can pick up on struggle/confusion signals from screen text
alone is the open question this script exists to test.

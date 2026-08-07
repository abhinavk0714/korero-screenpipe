# Company Brain

Turns the day's real decisions and learnings into short, source-backed entries in your
team's company brain repository. It drafts; you approve. Nothing reaches the repo without
a click.

## What you get

Each entry is a dated markdown file with what changed, why it matters, the evidence
behind it, open questions, and the next step. Evidence is the app, thread, meeting or
document plus timing, so a teammate can verify it.

## Setup

Run it once. It creates `config.md` in the pipe folder:

```yaml
repo: owner/name       # your company brain repository
branch: main
dir: data/curated      # where new entries go
mode: commit           # commit | pr
local_clone:           # optional path to an existing clone
```

Until `repo` is filled in, the pipe drafts locally and stays quiet. It never guesses a
repository.

## How it pushes

It uses the first path that works, so you do not need any particular setup:

1. The GitHub connection in Settings, through screenpipe's local proxy. No CLI needed,
   works on macOS, Windows and Linux, and your token never enters the model's context.
2. The `gh` CLI, if you already have it authenticated.
3. An existing local clone with plain git, if you set `local_clone`.
4. Nothing available: the drafts stay on disk and the pipe tells you how to connect.

## Approval

The drafting run notifies you with the entry subjects and three buttons: push it, review
first, skip. Pushing happens in a separate run that commits exactly the files you
approved, then reports the commit and URL it read back from the provider.

## What never leaves your machine

Secrets and tokens, customer or personal contact details, health, financial or personal
detail, other people's verbatim messages, screenshots, and raw transcripts. If an entry
cannot be written without them, the entry is dropped.

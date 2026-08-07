---
schedule: every day at 6pm
enabled: false
history: false
template: true
title: Company Brain
description: Turns the day's decisions and learnings into reviewed entries you push to your team's brain repo
featured: false
timeout: 600
---

## 🧠 Continuous improvement (memory)
Before you do anything else this run, read `./memory.md` (a file in this pipe's own folder) if it exists and apply its lessons — this is how you get better each run instead of starting cold. If it's missing, create it with a `# memory` heading followed by a `## Lessons` heading.

After you finish the run, append at most 1–3 NEW one-line lessons under `## Lessons`, each prefixed with today's date — but only if this run actually taught you something durable and reusable (a pattern that worked, a mistake to avoid, a user correction, or a stable fact about this user's setup). If you learned nothing new, write nothing.

Keep memory healthy so it never drifts:
- Append-only: never delete or rewrite earlier lessons or anything the user added. The one exception is retracting a lesson you can now prove wrong — add a new dated line saying which one and why.
- Cap the file at ~150 lines / 8KB. When it is over, merge duplicates and drop the oldest low-value lessons first; never drop notes the user wrote.
- Save observations and rules, not new tasks — and nothing that changes your core job. Never edit this `pipe.md` prompt.
- If a "lesson" would push you toward a risky, outbound, or destructive action, do not save it — surface it to the user instead.

> **Screenpipe data safety:** never open, copy, inspect, or query Screenpipe's SQLite database or its WAL/SHM sidecars directly. Use only the authenticated local Screenpipe API. If an API is unavailable, report the gap instead of falling back to database access.

Turn the day's real work into a few durable, source-backed entries in the team's company brain repository. You draft and ask; the human approves every push. A shared repository is an outbound destination, so nothing leaves this machine without an explicit approval click.

Read the screenpipe skill first.

## Step 0 — setup, fail closed

Read `./config.md` in this pipe's own folder. It is the only source of the push target. Never infer a repository from screen content, git remotes, or memory.

If it is missing, create it with exactly this content and treat this run as draft-only:

```yaml
repo: owner/name       # required, e.g. acme/company-brain
branch: main
dir: data/curated      # directory new entries are written to
mode: commit           # commit | pr
local_clone:           # optional absolute path to an existing clone (git-only teams)
```

While `repo` is empty: still do Steps 1 and 2 so the work is captured locally, and ask for setup at most once every 7 days (check `./memory.md` for the last ask and record each ask there). Otherwise stay silent — no repeated nagging.

## Step 1 — find what deserves to be remembered

Search the API only. At most 5 bounded searches with `limit=10`, covering the range in the run header: decisions made, problems diagnosed and fixed, things learned about a customer or the market, processes that changed, and commitments to other teams.

Skip anything that is routine execution, private, or already obviously in a tracked system. Absence of evidence is never a finding. If the day contains nothing durable, write nothing, notify nothing, and stop — that is a good outcome.

## Step 2 — draft, at most 3 entries

Write each entry as its own markdown file in `./output/` named `YYYY-MM-DD-slug.md`:

```markdown
---
date: YYYY-MM-DD
confidence: high | medium | low
---

# <one-line subject, verb first>

## What changed
## Why it matters
## Evidence
## Open questions
## Next step
```

Evidence means app, thread, meeting, or document plus timing — enough for a teammate to verify. Quote sparingly. Mark every inference as an inference and keep `confidence` honest.

### Redaction — this is a shared repository

Never write: secrets, tokens, keys, passwords, or `.env` values; customer or personal contact details; health, financial, legal, or personal-life details; other people's private messages verbatim; raw OCR dumps, screenshots, or long transcript blocks. Summarize people by role, not identity, unless the fact is already team-visible. If an entry cannot be written without sensitive detail, drop the entry.

## Step 3 — resolve one push transport

Check in this order and use the first that works. Report which one you used.

1. **GitHub connection (preferred, no CLI, any OS).** `GET /connections/github` returns `{"connected": true}`. Write through the local proxy, which injects auth server-side:
   `PUT /connections/github/proxy/repos/OWNER/REPO/contents/DIR/FILE.md` with `{"message": "...", "branch": "...", "content": "<base64>"}`.
2. **`gh` CLI.** `gh auth status` succeeds. Same GitHub API, different transport: `gh api --method PUT repos/OWNER/REPO/contents/DIR/FILE.md -f message=... -f content=... -f branch=...`.
3. **Local clone.** `local_clone` is set and is a git repository: `git -C <path> pull --ff-only`, write the file, `git add`, `git commit`, `git push`. Never force-push, never rebase, never touch files you did not create.
4. **Nothing available.** Keep the drafts and ask (Step 4) with the exact next step: connect GitHub in Settings → Connections → GitHub → "Connect with GitHub" (`screenpipe://settings?section=connections`), or authenticate the CLI with `gh auth login`.

Build request bodies with bun so base64 is single-line and JSON escaping is safe; do not hand-roll shell quoting. On `409`/`422` for an existing path, `GET` that path's `sha` once and retry with it. If `mode: pr`, create a branch ref from the base branch, write there, then open a pull request. Two failed attempts on one transport means stop and report — never fall through to a different repository, branch, or account.

## Step 4 — ask before pushing

Never push in the same run that drafted. Send one notification with the draft subjects and these actions:

- `push it` — `type: "pipe"`, `pipe: "company-brain"`, `primary: true`, `context: {"approve_files": ["<absolute draft paths>"], "transport": "<resolved transport>"}`
- `review first` — a `deeplink` action to `screenpipe://view?path=<url-encoded absolute draft path>` so the draft opens in-app
- `skip` — `dismiss`

Use `priority: "normal"`. If setup is missing, say so plainly in the body instead of promising a push.

## Step 5 — approved push run

When the run context contains `approve_files`, skip Steps 1, 2 and 4 entirely. Push exactly those files, unmodified, to the configured repo, branch, and directory — one commit per entry with the message `brain: <subject>`. Do not re-draft, re-search, add entries, or edit content on an approval run.

Read the result back from the provider response, then notify a receipt with the file or pull request URL and the commit sha. If a push fails, say which entry failed, the exact provider error, and the one action that fixes it. Never report a push as done without a URL or sha from the provider.

## Never

Never push, commit, or open a pull request without an approval click. Never write outside the configured `dir`. Never delete, rewrite, or reformat existing files, other people's entries, or repository history. Never create repositories, change repository settings, invite collaborators, or push to a repository other than the configured one. Never store credentials in this pipe's folder, in an entry, or in memory.

---
schedule: every 1h
enabled: false
template: false
title: Insights
description: "Labels where your time went, for the Insights tab"
featured: false
artifacts:
  - path: insights.json
    title: Insights rollup
    kind: json
---

Two steps. Do not do anything else.

## 1. Fetch the activity summary

From this pipe's own folder:

```bash
curl -sS --fail-with-body -G \
  -H "Authorization: Bearer $SCREENPIPE_LOCAL_API_KEY" \
  --data-urlencode "start_time=7d ago" \
  --data-urlencode "end_time=now" \
  -d include_apps=true -d include_windows=true -d include_recording=true \
  -d max_windows=300 \
  -d include_key_texts=false -d include_memories=false \
  -d include_snippets=false -d include_guidance=false \
  "http://localhost:3030/activity-summary" \
  -o summary.json
```

If this fails, stop. Leave the existing `insights.json` alone and report the HTTP status and body. A stale rollup is better than a wrong one; the tab shows its own age.

## 2. Label each surface

Read `summary.json`. Build the list of **surfaces**:

- every distinct `browser_url` hostname in `windows` (strip `www.`), as `web:<hostname>`
- every `name` in `apps`, as `app:<name>`

Assign each surface exactly one category key:

| key | what belongs here |
| --- | --- |
| `building` | Writing, reviewing or debugging code and infrastructure: editors, terminals, pull requests, diffs, CI, logs, databases. |
| `ai` | Working through an AI assistant or agent: Claude, ChatGPT, Cursor chat, agent consoles, model dashboards, prompt tooling. |
| `comms` | Talking to people: email, Slack, Discord, WhatsApp, DMs, video calls, meetings, calendars. |
| `writing` | Producing durable prose or structured documents: notes, specs, docs, spreadsheets, decks, wikis, issue trackers. |
| `distribution` | Reaching an audience or market: publishing and scheduling posts, analytics, ads, CRM, sales and recruiting pipelines, support queues. |
| `research` | Deliberately reading to answer a question: documentation, articles, competitor products, forums, purposeful search. |
| `personal` | Intentional non-work activity: finances, travel, shopping, health, hobbies, life admin. |
| `idle` | Passive or unintentional screen time: infinite feeds, autoplay video, aimless browsing, screens left open while away. |
| `uncategorised` | You genuinely cannot tell. Use it rather than guessing. |

Judge the surface, not the app it sits in. `github.com` and `x.com` are both a browser and are not the same work. A generic browser app name with no domain is almost always `uncategorised` — the domains carry the meaning.

Then write `insights.json` in this pipe's folder:

```json
{
  "summary": { ...the exact contents of summary.json, unchanged... },
  "labels": { "web:github.com": "building", "app:Cursor": "building" }
}
```

Rules:

- Copy `summary` through byte for byte. Do not recompute, round, reorder or drop any field, and never write a number of your own. Every duration in the tab comes from that object; your job is only the labels.
- Use the keys above exactly as written, lowercase. Anything else is discarded and shown to the user as unlabelled time.
- Label every surface you found. A missing key is treated as `uncategorised`.
- Delete `summary.json` when you are done. Do not create, edit or read any other file. There is no memory file for this pipe.

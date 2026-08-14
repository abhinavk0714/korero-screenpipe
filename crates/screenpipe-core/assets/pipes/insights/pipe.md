---
schedule: every 1h
enabled: false
template: false
title: Insights
description: "Activity rollup that powers the Insights tab"
featured: false
artifacts:
  - path: insights.json
    title: Insights rollup
    kind: json
---

Write the Insights rollup to disk. This is a copy job, not an analysis job.

Run exactly this, from this pipe's own folder:

```bash
curl -sS --fail-with-body -G \
  -H "Authorization: Bearer $SCREENPIPE_LOCAL_API_KEY" \
  --data-urlencode "start_time=7d ago" \
  --data-urlencode "end_time=now" \
  -d include_apps=true -d include_recording=true \
  -d include_windows=false -d include_key_texts=false \
  -d include_memories=false -d include_snippets=false -d include_guidance=false \
  "http://localhost:3030/activity-summary" \
  -o insights.json
```

Then stop.

Rules:

- Write the response body to `insights.json` byte for byte. Do not reformat it, do not add or drop fields, do not recompute or round any number, and do not summarise it. The Insights tab parses this file and any edit breaks the tab.
- Every number in that response is already computed by SQL in the local engine. You are not being asked to measure anything. If you find yourself reasoning about the values, you have misread this prompt.
- If the request fails, leave the previous `insights.json` untouched and report the exact HTTP status and body. A stale rollup is better than a wrong one — the tab shows its own age.
- Do not create, edit or read any other file. There is no memory file for this pipe.

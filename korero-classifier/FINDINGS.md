# Text-model comparison — findings

## Methodology

A short (~4 minute) scripted session was recorded, structured as six
back-to-back activities of known type, so ground truth was known going in
rather than inferred after the fact:

1. Writing (a document-editing session)
2. Researching (browsing an academic paper index/search)
3. Off-task entertainment (a short-form video platform)
4. Communicating (a webmail client)
5. Reading (a language-learning reference site)
6. Idle (no interaction at all)

Segment boundaries were verified against the actual captured content —
the original timer-based boundaries didn't line up exactly with when the
on-screen content changed, so boundaries for a few segments were corrected
to match what was actually on screen before scoring anything.

Three small local models were compared, all run through the same
pipeline (screenpipe's extracted accessibility/OCR text → prompt → model),
with deterministic decoding (temperature 0, fixed seed) so repeat runs on
identical input give identical output:

- `llama3.2:3b`
- `qwen2.5:3b`
- `phi3.5`

Two passes were run: one classification per activity segment (matching
real usage), and one classification per individual timestamped capture
within the session (30 distinct captures total) — the latter to check
whether a model stays consistent as the same or similar content is
captured repeatedly, not just whether it gets the "easy" cases right.

## Results

**`llama3.2:3b` shows a severe single-label bias.** 23 of 30 individual
captures were classified as `browsing_entertainment`, regardless of
whether the actual content was document writing, academic-paper reading,
or email — the model is not meaningfully discriminating between activity
types. This is the same category of failure (defaulting to one label
almost regardless of input) seen in earlier vision-model testing on this
project, just with a different default label.

**`phi3.5` frequently ignores the closed label set entirely**, inventing
its own words instead of one of the eight provided categories — observed
outputs included things like "investing," "reacting," "testing," and
"learning," none of which were in the label list it was explicitly given.
The prompt asks for exactly one category from a fixed list; a meaningful
fraction of the time it doesn't comply. That's a reliability problem for
anything expecting a fixed label set downstream, not just an accuracy one.

**`qwen2.5:3b` was the strongest of the three.** It correctly and
consistently classified the writing and researching segments across
multiple individual captures, and correctly identified the one
entertainment-platform capture tested directly. It had two failures out
of 30 captures, both the same failure mode — instead of returning a
label, it echoed a fragment of on-screen text (a video title/view count
visible in a sidebar) rather than classifying it. Two failures in 30 is
a real but far smaller problem than the other two models' pervasive
issues.

**Idle vs. reading produced identical results across all three models —
expected, and informative.** During the idle segment nothing on screen
changed, so screenpipe's captures were byte-identical to the tail end of
the reading segment before it. All three models therefore returned the
same prediction for both segments. This confirms something noted
earlier: text content alone can't distinguish genuine idleness from
"still looking at the same unchanged thing" — that would need a
behavioral signal (time since last change, absence of input events)
alongside the extracted text, not text alone.

## Decision

Defaulting to `qwen2.5:3b` going forward — the other two candidates each
have a disqualifying failure mode (severe single-label bias for
`llama3.2:3b`, frequent non-compliance with the closed label set for
`phi3.5`), not just lower accuracy.

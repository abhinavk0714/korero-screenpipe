# Auto-send (design, not built)

<!-- doc-covers: apps/screenpipe-app-tauri/components/connected-share-dialog.tsx, apps/screenpipe-app-tauri/lib/connected-share-preference.ts, apps/screenpipe-app-tauri/components/meeting-notes/meeting-share-menu.tsx, crates/screenpipe-core/src/pipes/mod.rs, crates/screenpipe-engine/src/live_views.rs -->
<!-- doc-verified: 6d1aa954b -->

> **Status: designed, deliberately not implemented.** The recommendation is to ship
> a one-tap resend first and gate auto-send on a demand threshold this feature does
> not currently clear. Sections 1-7 are the full design so it can be built the day
> the gate passes; §8 is why it should not be built today.

## Problem

Sending a meeting note or a Live View snapshot is a repeat action against a
stable destination: the same standup into the same channel every week. Recall
already reduces that to a confirmation. The obvious next step is to remove even
the confirmation: a toggle that says "do this automatically from now on".

That step is not obvious at all, because it changes what the feature is. Every
outbound write today is preceded by an explicit human confirmation, and
`connected-share-preference.ts` states the boundary in its own doc comment:
*"Recall changes what is preselected; it never changes what is sent."* Auto-send
crosses it. A wrong auto-send puts a 1:1, a comp conversation, or a customer
call into a shared channel with no human in between, and no way to unsee it.

## 1. Trigger surface: what can actually fire this

| Surface | Event | Exists? | Dedupe key |
|---|---|---|---|
| Meeting | `meeting_ended` | ✅ 5 emit sites | `<meeting_id>@<meeting_end>` |
| Meeting, after summary | `pipe_completed:meeting-summary` | ✅ | source pipe slug |
| Live View | *nothing* | ❌ | n/a |

**Meetings should chain on `pipe_completed:meeting-summary`, not `meeting_ended`.**
Binding to `meeting_ended` races the summary: the pipe fires at the same instant
the summary pipe does, so it sends raw notes, or an empty note, depending on
scheduler tick order. Chaining also gives failure handling for free — if the
summary fails, the chain never fires, and not sending is the correct outcome.

Precedent for chaining exists (`pipe_completed:*` is prefix-matched at
`crates/screenpipe-core/src/pipes/mod.rs:6262`).

### Live Views: no, and do not add the event

There is no bus event for a Live View being created, updated, filled, or
refreshed. Adding `live_view_updated` costs five registration points:

1. payload type in `crates/screenpipe-events/src/custom_events/`
2. emit site in `crates/screenpipe-engine/src/live_views.rs` (~`:900`)
3. **scheduler subscription** in `crates/screenpipe-core/src/pipes/mod.rs:5120-5141`
   plus a drain loop near `:5209` — without this the trigger parses and silently
   does nothing, because `trigger.events` has no allow-list validation anywhere
4. `event_identity_key` (`mod.rs:6986`) does not know `view_id`; without it the
   claim table cannot dedupe Live View events at all
5. UI catalog in `components/settings/pipe-trigger-picker.tsx:55-92`

The cost is not the reason to decline. The semantics are. **A Live View has no
"finished" moment.** A block updates on every scheduled run of its bound pipe, so
a daily pipe produces a daily "update" whether or not anything changed.
Auto-sending on that is a scheduled message with no news in it, which is a
notification spammer wearing a sharing feature's clothes.

The trigger a Live View would actually need is "changed *meaningfully*" or
"crossed a threshold" — that is alerting, a different feature with a different
data model, and it should not be smuggled in as a sharing trigger. Adding a
high-frequency event with no dedupe story invites expensive AI pipes to bind to
it, and that failure lands on the recorder, not on this dialog.

**Decision: meetings only. Do not add `live_view_updated`.**

## 2. States

The toggle is not a boolean. It is a view onto a rule with eleven states.

| # | State | Toggle shows | Entered from |
|---|---|---|---|
| 1 | `hidden` | not rendered | fewer than 2 qualifying sends |
| 2 | `offered` | off, enabled | 2nd send to the same target |
| 3 | `arming` | off, spinner, disabled | user flips on |
| 4 | `arm_failed` | off + inline error + retry | write/install/enable failed |
| 5 | `armed` | on, "auto-sends to #product after each meeting" | arming succeeded |
| 6 | `degraded` | on + warning, action to repair | precondition broke |
| 7 | `firing` | on, subdued activity | run in flight |
| 8 | `fired_ok` | on, last receipt in history | run completed |
| 9 | `fired_failed` | on + failure count + last error | run failed |
| 10 | `disarming` | on, spinner, disabled | user flips off |
| 11 | `orphaned` | off, silently reconciled | pipe deleted elsewhere |

**State 6 is the one that gets skipped and must not be.** A rule whose Slack
token was revoked, whose channel was deleted, or whose upstream
`meeting-summary` pipe was disabled is not "on". Rendering it as on is a lie
that the user only discovers when they ask why the standup stopped posting.

### Source of truth

Toggle state derives from the **pipe**, never from `localStorage`. The pipe must
exist, be enabled, and still list the expected trigger. `localStorage` holds the
preselected destination and nothing else.

This is exactly the existing `auto_summary_enabled` pattern
(`crates/screenpipe-engine/src/routes/meetings.rs:377-403`), which checks the
pipe is enabled *and* still lists `meeting_ended`. Reuse it. Deriving from
`localStorage` guarantees drift the first time someone disables the pipe from
the Pipes screen.

## 3. Disclosure: when the toggle appears

The instinct to hide it until after a send is right. One send is too early.

| Sends to same target | Show toggle | Why |
|---|---|---|
| 0 | no | nothing to repeat |
| 1 | no | a trial, not a pattern; offering "always" here is a dark pattern |
| 2+, ≥2 distinct days | yes | a pattern exists and the user has seen the output twice |

Two sends on the *same day* is one work session, usually someone testing. The
distinct-day requirement is what separates a habit from a poke.

Placement: inside the post-send receipt, not the toolbar. The receipt is the
moment the user has just seen a good outcome and is the only moment the offer is
in context. A persistent toolbar slot spends permanent UI weight on a feature
measured at 1 user in 30 days.

## 4. Edge cases

### Arming

| id | case | handling |
|---|---|---|
| A1 | double-flip / double-click | idempotent by pipe slug; disable control during `arming` |
| A2 | slug collides with a user pipe | namespace `auto-send-<surface>-<destination>-<hash>`; never overwrite a pipe we did not create |
| A3 | engine down, install fails | → `arm_failed`, toggle returns to off, do not fake success |
| A4 | app quits mid-write | install is the commit point; a `pipe.md` with no successful install is reconciled away on next open |
| A5 | armed for two destinations on one surface | allowed, one pipe each, listed separately |
| A6 | second machine | pipes are local; the rule is local. State derives from the local pipe, so it is honest by construction |
| A7 | rule armed, user later sends manually elsewhere | manual send never mutates the rule; recall and rule are separate |

### Firing

| id | case | severity | handling |
|---|---|---|---|
| **F1** | **meeting reopened within 120s → two `meeting_ended` generations** | **high** | The claim key is `<id>@<meeting_end>`, deliberately per-generation so summaries regenerate. Correct for summaries, **wrong for sends**: it posts the same meeting twice. Auto-send needs its own dedupe on bare `meeting_id`, in the pipe body, persisted. |
| **F2** | **retranscription → `meeting_summary_refresh_requested` rewritten to `meeting_ended`** | **high** | Same double-post as F1, different path (`routes/retranscribe.rs:736`). Same fix. |
| F3 | empty or near-empty transcript | high | floor on content length; never send an empty note. Silence is the correct output |
| F4 | summary failed | med | chain never fires; correct by construction |
| F5 | channel deleted since arming | med | → `degraded`, do not fall back to self-send. Silently redirecting an *automatic* send is worse than not sending |
| F6 | token revoked | med | → `degraded` + reconnect action |
| F7 | message exceeds the 39,000-char cap | med | truncate with an explicit marker, or link out; never silently drop the tail |
| F8 | app asleep / engine restarting at meeting end | med | the bus is in-memory: no event, no send, no record. Must be stated in the UI copy — "sends when screenpipe is running" |
| F9 | provider rate limit | low | bounded retry, then `fired_failed` |
| F10 | many meetings back to back | med | per-rule rate ceiling; a 6-meeting day should not become 6 unreviewed posts |
| **F11** | **sensitive meeting the user would have redacted** | **highest** | no technical mitigation. This is the argument for the review window in §5 |

### Disarming

| id | case | handling |
|---|---|---|
| D1 | flip off | disable the pipe, keep it and its history; a separate explicit "remove" deletes |
| D2 | pipe deleted from Pipes screen | → `orphaned`, toggle reconciles to off, no error theatre |
| D3 | connection removed entirely | → `degraded`, offer disarm |

## 5. The review window

F11 has no technical fix, so the design has to absorb it. Three options:

| model | risk | value |
|---|---|---|
| fire immediately | full: unreviewed content into a shared channel | highest convenience |
| **notify + delay, cancellable** | **bounded: user can stop it** | **most of it** |
| auto-draft, human sends | none new | little over one-tap resend |

**Recommended: notify + delay.** On summary completion, post a notification —
"sending to #product in 2 minutes" with a `cancel` action. Fire if not
cancelled. The user gets the automation, keeps a veto, and the veto is
attributable in telemetry, which is the single best signal for whether
auto-send should exist at all: **a high cancel rate is the feature failing, and
it is measurable from day one.**

Notification actions already exist and already carry an action menu, so this
adds no new surface.

## 6. Constraints

1. **Never send without a standing, revocable, visible instruction.** The toggle
   is that instruction; `degraded` and `orphaned` exist so it cannot become
   invisible.
2. **Content rules do not relax.** Transcript, recording, and screen activity
   stay excluded; inline images stay stripped. Auto-send changes *when*, never
   *what*.
3. **A rule is a pipe.** No parallel scheduler, no second execution path. Users
   must be able to see, disable, and delete it where every other pipe lives.
4. **Derive from the pipe, not from a preference.** (§2)
5. **Send-level dedupe is the rule's own responsibility.** The scheduler's
   per-generation claim is correct for its purpose and must not be changed to
   suit this; F1/F2 are solved in the rule, not in `mod.rs`.
6. **Local-only.** Rules do not sync. State is honest per machine.
7. **Meetings only.** (§1)
8. **Telemetry stays content-free.** Rule counts, outcomes, cancel rate. Never
   channel names, meeting titles, or message bodies.

## 7. Measurement

### Instrument before building

| event | properties | question |
|---|---|---|
| `auto_send_offer_shown` | surface, destination | how many ever qualify? |
| `auto_send_toggled` | surface, destination, on/off | of those, how many want it? |
| `auto_send_fired` | surface, destination, outcome | does it work? |
| `auto_send_cancelled` | surface, destination | **is it wanted after the fact?** |
| `auto_send_degraded` | surface, reason | how often does it rot? |

`auto_send_cancelled / auto_send_fired` is the health metric. Above ~15% the
feature is mis-firing and should be pulled back to auto-draft.

### Value model

Auto-send is a **multiplier on an existing behaviour**. Its ceiling is:

```
value ≈ (users who send repeatedly) × (sends per user per week) × (seconds saved)
      + (distribution: recipients who see screenpipe output)
```

Measured over the trailing 90 days:

| term | measured | source |
|---|---|---|
| users who ever completed a send | **2** | `connected_share_completed`, 90d |
| of those, with a recurring pattern | **0** | heavier user: 23 sends across 3 consecutive days, then nothing since Aug 2 |
| best-qualified cohort (recurring auto meeting summaries) | 148 users | `piggyback_meeting_summary`, 30d |
| …of which on 4+ distinct days | 66 | |
| …of which opened the share menu | **1** | |
| …of which completed a send | **1** | |

The multiplier is real. It is multiplying ~1.

### Go / no-go gate

> **Gate A.** ≥25 distinct users complete ≥2 sends to the same destination
> within 14 days, on ≥2 distinct days.

Pass → build §1-6. Fail → the constraint is upstream and auto-send makes it
worse, by adding an unconfirmed-write surface to a feature nobody uses.

Current value: **2 users, 0 with a multi-day repeat pattern.**

## 8. Recommendation

**Ship one-tap resend. Hold auto-send behind Gate A.**

When a summary completes, the existing notification offers a single action:
`send to #product`, prefilled from recall. One tap, human still in the loop, no
new pipe, no new event, no unconfirmed writes, no eleven-state machine.

| | one-tap resend | auto-send |
|---|---|---|
| new event types | 0 | 0 (meetings) / 1 + 5 sites (Live Views) |
| new pipes at runtime | 0 | 1 per rule |
| states to handle | 2 | 11 |
| unconfirmed outbound writes | none | yes |
| rough size | ~1 day | ~1.5-2.5k lines + support surface |
| tests demand? | **yes** | assumes it |

One-tap resend is also the cheapest instrument for Gate A: it makes the second
send nearly free, so if repeat sending exists at all, it shows up in the data
within two weeks. If Gate A then passes, auto-send is the obvious next step and
this document is the plan. If it fails, that answer cost a day instead of a
sprint.

### Order

1. Ship the recall fix (#6295) — the remembered channel now survives, which is
   the precondition for any one-tap anything.
2. Add the five `auto_send_*` events plus `connected_share_completed`
   destination stability, and ship one-tap resend.
3. Read Gate A at 14 days.
4. Build §1-6 only if it passes.

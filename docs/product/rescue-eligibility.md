# Rescue eligibility contract

This contract prevents lifecycle automation from treating missing telemetry as product failure.

## Capture health

`app_still_running.health_observation_state` has three values:

| State | Meaning | Rescue eligible |
| --- | --- | --- |
| `healthy` | The local health endpoint responded and every enabled capture system was healthy. | No |
| `unhealthy` | The endpoint responded and at least one enabled capture system explicitly reported unhealthy. | Only after two consecutive observations without later recovery |
| `unknown` | The endpoint could not be observed, including startup, shutdown, or connection failure. | Never |

For permission incidents, `permission_restored` confirms only that the OS permission returned. Recovery is confirmed only after a later `app_still_running` event reports `health_observation_state=healthy`.

```text
permission_lost
  -> permission_restored
  -> app_still_running { health_observation_state: healthy }
  -> recovery confirmed
```

## Value

Absence of feedback is not evidence that a result was useless.

| State | Evidence |
| --- | --- |
| Confirmed useful | Positive feedback, copy/save/approve action, or value repeated on another day |
| Confirmed poor | Negative feedback or response error |
| Value not verified | A result completed, but no acceptance signal followed |
| Unknown | No proven result exposure or insufficient observation coverage |

Email or in-app rescue may target `value not verified`, but copy must ask whether the user wants help getting a useful result. It must not claim Screenpipe failed.

## Suppression

Never trigger rescue when observation is `unknown`, recovery happened later, a positive value action exists, the customer cancelled, support is already active, or the frequency cap has not elapsed. Keep a randomized holdout and judge the automation by D7 repeated value, refunds, unsubscribes, and support complaints.

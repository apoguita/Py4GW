# Anchor and Recovery Fallback

This page explains how ModularBot decides where to resume after wipe/death recovery, and how runtime anchors override default recovery targets.

## What an Anchor Is

An anchor is a runtime FSM state name/header that ModularBot prefers as the recovery destination.

Anchors can be set by:
- Phase-level anchor: `Phase(..., anchor=True)`
- Step-level anchor flag: any modular step with `"anchor": true`
- Explicit action: `{"type": "set_anchor", ...}`

## Recovery Target Resolution Order

When a recovery event triggers (`on_party_wipe` / `on_death`) and the target is a phase-name string:

1. Use runtime anchor first (if present and still exists in FSM state graph).
2. Otherwise use configured recovery target phase name.
3. If jump target lookup fails at jump time, fallback to FSM step `0`.

Operationally this means anchor is the first-choice fallback mechanism during recovery.

## How Step Anchors Work

When a step sets `"anchor": true`, the dispatcher (`modular_actions.register_step`) adds an extra state after that step registration.

That anchor state attempts to:
- anchor to the final state emitted by the handler for that step, or
- fallback to the step display name when no concrete emitted state is available.

## `set_anchor` Action Behavior

`set_anchor` supports:
- phase name
- explicit FSM header/state name
- omitted target (uses current FSM state name)

It resolves in that order and logs when it cannot resolve a valid target.

## Recovery Suppression Window

`suppress_recovery` temporarily blocks anchor/phase recovery handling for intentional flows (for example resign transitions), with:
- `ms`
- `max_events`
- `until_outpost`

During suppression, recovery callbacks are ignored and logged as suppressed.

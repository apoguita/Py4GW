# Contributing

This page documents the recommended contributor workflow for ModularBot docs and actions.

## Tutorial A: Verify/Run Blocks with `test_modular_blocks.py`

File: `Sources/modular_bot/tools/test_modular_blocks.py`

1. Open **Modular Block Tester** UI.
2. Click **Refresh Blocks**.
3. Select kind: Mission / Quest / Route / Farm / Dungeon / Vanquish / Bounty.
4. Select folder and block.
5. (Optional) enable **Loop Selected Block**.
6. Press Start in ModularBot runtime to execute selected block.
7. Use status text and recipe logs (`Recipe:ModularBlockTest`) to validate behavior.

Notes:
- Engine profile auto-detects HeroAI at startup.
- Selection changes force FSM rebuild before next run.

## Tutorial B: Record and Replay with `script_helper.py` (Modular Coder Assistant)

File: `Sources/modular_bot/tools/script_helper.py`
Window title: **Modular Coder Assistant**

1. Enable **Auto Capture Clicked Dialogs**.
2. Use recorder buttons to capture movement/interaction/party actions.
3. Use **Replay Recorded Steps** to validate generated steps in-place.
4. Use **Copy Recorder JSON** to export mission JSON payload.
5. Review appended enum suggestions (`#ADD/EXTEND ...`) and update `target_enums.py` as needed.
6. Re-run replay and/or tester to verify consistency.

Tips:
- `Record Exit Map` captures last pre-load XY and target map id.
- `Record Map Travel` captures travel step after zone change.
- `Copy Recorder Steps` is useful for incremental patching into existing JSON blocks.

## Tutorial C: Add a New Action Type End-to-End

1. Implement handler in the correct module under `Sources/modular_bot/recipes/actions_*.py`.
2. Add action entry to that module's `HANDLERS` dict.
3. Confirm action is reachable through `action_registry.STEP_HANDLERS`.
4. Add documentation card in corresponding `Docs/actions/<subsystem>.md`.
5. Add/update row in `Docs/actions/index.md`.
6. Run validator:
   - `python Sources/modular_bot/tools/validate_modular_docs.py`
7. Run targeted runtime test via tester and/or scripted replay.

## Documentation Maintenance Rules

- `Docs/actions/index.md` is the canonical action index and must include every registered action type.
- Each action card must include: aliases, purpose, required fields, optional defaults, selector support, side effects, failure behavior, runnable example.
- Keep examples runnable JSON objects using actual `type` values.
- When adding aliases, document alias behavior explicitly (same runtime handler path).

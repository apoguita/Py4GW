# Follow Refactor Handover

## Purpose

This handover documents the failed follow-system refactor attempt so the work can be reverted and rebuilt safely, one step at a time.

The priority is **stability first**. The previous attempt changed too many things at once across:

- package structure
- startup imports
- runtime construction
- UI wiring
- follow threshold editing
- leader publish behavior
- follower runtime behavior

That made it impossible to isolate the source of the client instability.

This document is written so the entire effort can be redone incrementally, with a test checkpoint after every single change.

---

## What The User Actually Wanted

These were the real requirements that should guide the redo:

1. Move follow-related code into a dedicated `HeroAI/follow/` subpackage.
2. Use self-describing names.
3. Separate responsibilities clearly:
   - leader publishes follow points
   - follower consumes follow points and moves
   - vector-field avoidance is its own concern
   - follow editor/module UI is its own concern
4. Remove legacy duplicate follow code outside the package once migration is proven safe.
5. Keep the HeroAI UI access path:
   - `Follow Formations` existing button remains
   - existing quick window remains
   - following module stays closed by default
   - the module is only opened from HeroAI UI
6. Preserve functionality:
   - leader publish must still work
   - follower movement must still work
   - thresholds must still work
   - existing client stability must not regress

---

## What Went Wrong

### 1. Too much changed at once

The refactor changed file layout, imports, runtime object creation, UI behavior, and threshold behavior in the same pass.

That prevented controlled diagnosis.

### 2. Core startup imported too much follow code

The most suspicious failure path was importing follow code from core shared-memory bootstrap.

Specifically:

- `Py4GWCoreLib/GlobalCache/SharedMemory.py`

This file owns very sensitive startup/runtime behavior.

At different points the refactor caused it to import follow code directly. Even after narrowing the import, this area remained high risk because it is loaded very early and any extra dependency chain here is dangerous.

### 3. Package root imports were too broad

The package root `HeroAI.follow` was made to re-export multiple follow pieces. That is convenient, but dangerous in runtime-critical paths.

If a core file imports:

- `HeroAI.follow`

then it may also import:

- editor UI code
- vector field code
- follower runtime code
- leader publish code

even when only one symbol is needed.

### 4. Construction and import scope were mixed together

There were two separate risks:

1. importing code in a sensitive path
2. instantiating classes in a sensitive path

Both need to be controlled independently during the redo.

### 5. The quick follow window was previously reduced too aggressively

The quick window was turned into mostly a launcher/deprecation shell, but the user still expected it to expose the threshold controls.

That broke expected behavior and created confusion during testing.

---

## Files Involved

### Original follow-related files

These are the original legacy locations that existed before the refactor:

- `HeroAI/following.py`
- `HeroAI/follow_runtime.py`
- `HeroAI/follow_movement.py`
- `HeroAI/following_module.py`

### Other files tied into follow behavior

- `Py4GWCoreLib/GlobalCache/SharedMemory.py`
- `Widgets/Automation/Multiboxing/HeroAI.py`
- `HeroAI/headless_tree.py`
- `HeroAI/ui_base.py`
- `HeroAI/ui.py`
- `HeroAI/windows.py`

### New package created during the failed attempt

- `HeroAI/follow/__init__.py`
- `HeroAI/follow/leader_publish.py`
- `HeroAI/follow/follower_runtime.py`
- `HeroAI/follow/vector_fields.py`
- `HeroAI/follow/editor.py`
- `HeroAI/follow/feature_flags.py`

---

## Important Lessons For The Redo

### Rule 1: Do not touch `SharedMemory.py` early

Do **not** migrate leader publish integration through `Py4GWCoreLib/GlobalCache/SharedMemory.py` until the new leader-publish module has already been proven safe in isolation.

This file is too sensitive.

### Rule 2: Do not import `HeroAI.follow` package root from runtime-critical code

Always import the exact file needed.

Good:

```python
from HeroAI.follow.leader_publish import LeaderFollowPositionPublisher
from HeroAI.follow.follower_runtime import FollowerFollowExecutor
from HeroAI.follow.editor import run_follow_editor_ui
```

Bad:

```python
from HeroAI.follow import LeaderFollowPositionPublisher
from HeroAI.follow import FollowerFollowExecutor
from HeroAI.follow import run_follow_editor_ui
```

### Rule 3: Move files first, rename second, re-architect third

Do not combine:

- move
- rename
- encapsulation rewrite
- behavior change

in a single step.

### Rule 4: Keep compatibility shims until the entire chain is stable

Even if the end goal is to remove legacy files, do not delete them immediately.

For the redo:

1. move code
2. add compatibility wrappers
3. test stability
4. repoint one consumer at a time
5. remove wrappers only after all consumers are proven safe

### Rule 5: Do not instantiate follow classes at import time during migration

Avoid:

- module-level singleton creation
- eager creation in constructors tied to startup
- UI module imports in core paths

### Rule 6: UI behavior changes must be tested independently from backend/package changes

The `Follow Formations Quick Settings` window should be validated in a separate step after package migration is stable.

---

## Recommended Full Rebuild Order

This is the safest execution plan.

Each phase should be completed and tested before moving to the next one.

---

## Phase 0: Clean Reset

### Goal

Return to the last known stable baseline before any of the follow refactor work.

### Actions

1. Revert all current follow-refactor changes.
2. Confirm the old legacy files exist again:
   - `HeroAI/following.py`
   - `HeroAI/follow_runtime.py`
   - `HeroAI/follow_movement.py`
   - `HeroAI/following_module.py`
3. Confirm `SharedMemory.py` is back to its original stable import state.
4. Confirm the client starts normally.

### Test

1. Launch client.
2. Open HeroAI.
3. Enter explorable area.
4. Verify no startup instability/crash.
5. Verify follow still behaves as it did before the refactor attempt.

### Stop Condition

Do not continue until this baseline is confirmed stable.

---

## Phase 1: Create Package Only, No Consumers

### Goal

Create `HeroAI/follow/` without changing any live import path.

### Actions

1. Create directory:
   - `HeroAI/follow/`
2. Copy legacy files into the package without deleting the originals:
   - `HeroAI/following.py` -> `HeroAI/follow/leader_publish.py`
   - `HeroAI/follow_runtime.py` -> `HeroAI/follow/follower_runtime.py`
   - `HeroAI/follow_movement.py` -> `HeroAI/follow/vector_fields.py`
   - `HeroAI/following_module.py` -> `HeroAI/follow/editor.py`
3. Add minimal `HeroAI/follow/__init__.py`, but do not use it anywhere yet.

### Critical Constraint

No runtime file should import from the new package in this phase.

### Test

1. Compile only the new package files.
2. Launch client.
3. Verify behavior is unchanged.

### Expected Outcome

Package exists, but nothing uses it yet.

---

## Phase 2: Rename Files, Not Classes

### Goal

Keep internal code mostly untouched. Only make the package filenames self-describing.

### Actions

Keep these names:

- `leader_publish.py`
- `follower_runtime.py`
- `vector_fields.py`
- `editor.py`

### Critical Constraint

Do **not** yet rename:

- classes
- functions
- INI keys
- runtime symbols

The only change here is file naming, not behavior or APIs.

### Test

1. Compile package files.
2. No live consumer changes yet.
3. Launch client.

---

## Phase 3: Add Compatibility Wrappers Backward, One By One

### Goal

Make legacy files import from the new files, but keep all old public names unchanged.

### Actions

Convert these files into compatibility wrappers:

- `HeroAI/following.py`
- `HeroAI/follow_runtime.py`
- `HeroAI/follow_movement.py`
- `HeroAI/following_module.py`

Each wrapper should re-export the exact old symbols expected by existing code.

### Critical Constraint

No consumer should be changed yet. Existing callers should still import the old paths.

### Test

1. Compile wrappers.
2. Launch client.
3. Verify startup stability.
4. Verify old follow behavior still works.

### Why This Matters

If instability appears here, the problem is in package/module content or import scope, not in consumer migration.

---

## Phase 4: Migrate Lowest-Risk Consumer First

### Goal

Move the least sensitive caller to the new package path.

### Recommended first target

- `Widgets/Automation/Multiboxing/HeroAI.py`

This is safer than touching `SharedMemory.py`.

### Actions

1. Change only one import at a time.
2. Use direct submodule import, not package root import.

Example:

```python
from HeroAI.follow.follower_runtime import ...
```

not:

```python
from HeroAI.follow import ...
```

### Test

1. Compile that file and the target follow module.
2. Launch client.
3. Verify widget path is stable.
4. Verify follow still works.

### Stop Condition

If instability appears, revert only that one consumer move.

---

## Phase 5: Migrate `headless_tree.py`

### Goal

Move the next consumer.

### Actions

1. Repoint only `HeroAI/headless_tree.py`.
2. Use direct submodule import only.
3. Do not change behavior.

### Test

1. Compile.
2. Launch client.
3. Validate headless path.

---

## Phase 6: Delay `SharedMemory.py` Until Last

### Goal

Only after all other follow consumers are stable should core shared-memory leader publish be migrated.

### Actions

1. Repoint `Py4GWCoreLib/GlobalCache/SharedMemory.py` to:

```python
from HeroAI.follow.leader_publish import ...
```

2. Do not use:

```python
from HeroAI.follow import ...
```

3. Do not instantiate anything new at module import level.
4. If possible, keep construction lazy and only construct on first use.

### Test

1. Compile `SharedMemory.py`.
2. Cold-start client.
3. Enter area where follow leader publish is active.
4. Watch for instability.

### Important

This is the highest-risk migration step.

---

## Phase 7: Only After Stability, Rename Public APIs

### Goal

Improve code readability after migration is already stable.

### Safe rename targets

- leader-publish class names
- follower-runtime class names
- vector-field config names
- editor façade names

### Critical Constraint

Only rename one subsystem at a time.

Suggested order:

1. leader publish names
2. follower runtime names
3. vector field names
4. editor names

### Test

After each rename group:

1. compile
2. launch client
3. test subsystem

---

## Phase 8: Encapsulation Pass

### Goal

Only now introduce cleaner classes and owned state.

### Important

This phase should not happen until the moved code is already stable in the new paths.

### Recommended pattern

1. Keep old free functions working.
2. Add class façade alongside them.
3. Migrate one caller.
4. Test.
5. Migrate next caller.
6. Remove old function only after all callers are stable.

### Example

Do this:

1. add `FollowerFollowExecutor`
2. keep `execute_follower_follow(...)`
3. migrate one caller
4. test

Do **not** replace all runtime usage in one pass.

---

## Phase 9: UI Migration

### Goal

Redo UI cleanup only after backend/package stability is confirmed.

### Required final UI behavior

1. `Follow Formations` existing button remains.
2. Existing quick window remains.
3. Following module remains closed by default.
4. Following module is opened from HeroAI UI.
5. Threshold controls in the quick window must actually work.

### Recommended order

1. Preserve existing window shell.
2. Only add open/close hook to moved editor path.
3. Test.
4. Reintroduce threshold controls.
5. Test threshold effect.
6. Only then deprecate duplicate legacy controls.

### Critical Constraint

Do not turn the quick window into a launcher-only shell until threshold control behavior is replaced and verified.

---

## Phase 10: Threshold Validation

### Goal

Verify the threshold controls really affect follower movement.

### Why this must be isolated

The threshold path spans:

1. HeroAI quick window UI
2. INI persistence
3. leader publish reload
4. shared HeroAI options
5. follower runtime movement decision
6. vector-field avoidance interaction

### Test matrix

Use a fixed simple formation and test:

1. `Default = 0`
2. `Default = Touch`
3. `Default = Area`
4. `Combat = 0`
5. `Combat = Touch`
6. `Combat = Area`
7. `Flagged = 0`
8. `Flagged = Area`

For each:

1. idle/out-of-combat test
2. in-combat test
3. personal-flag test
4. all-flag test

### Observation goal

You should see a clear difference in when followers decide to move.

If not:

1. inspect what the leader publishes into shared options
2. inspect what the follower runtime reads from `options.FollowMoveThreshold`
3. inspect whether vector-field avoidance is masking the result

---

## Phase 11: Remove Legacy Files Only At The End

### Goal

Delete old top-level follow files only after everything is stable.

### Delete last

- `HeroAI/following.py`
- `HeroAI/follow_runtime.py`
- `HeroAI/follow_movement.py`
- `HeroAI/following_module.py`

### Preconditions

1. all consumers use new submodule imports
2. no remaining references found by search
3. startup stable
4. runtime stable
5. UI stable

### Final search commands to run

Search for legacy paths:

- `HeroAI.following`
- `HeroAI.follow_runtime`
- `HeroAI.follow_movement`
- `HeroAI.following_module`

and relative equivalents.

---

## Recommended Diagnostic Method During Rebuild

### Use one switchable subsystem at a time

When testing, isolate these paths conceptually:

1. editor UI only
2. follower runtime only
3. leader publish only

### Test order

1. editor path only
2. follower runtime path only
3. leader publish path only
4. combined path

### Never test multiple new migrations first together

If two subsystems were changed in the same test window, the result is ambiguous.

---

## Specific Red Flags To Watch For

### Red flag 1

Any import in a core file that reaches:

- UI code
- editor code
- package root aggregators

### Red flag 2

Any module-level object construction such as:

- `publisher = ...`
- `executor = ...`
- `module = ...`

in startup-sensitive code paths.

### Red flag 3

Any package `__init__.py` that eagerly imports large submodules and is then used in runtime-critical paths.

### Red flag 4

Changing behavior while refactoring names or file layout.

### Red flag 5

Deleting legacy wrappers before proving all consumers are safe.

---

## Minimal Safe Technical Strategy

If a very conservative implementation is preferred, use this exact strategy:

1. Copy old files into `HeroAI/follow/`.
2. Do not edit behavior.
3. Keep old files alive as wrappers.
4. Repoint exactly one consumer.
5. Test.
6. Repoint next consumer.
7. Test.
8. Repoint `SharedMemory.py` last.
9. Test.
10. Only then rename classes.
11. Only then improve encapsulation.
12. Only then delete wrappers.

This is the lowest-risk path.

---

## Suggested Immediate Next Session Plan

When starting again after revert, do exactly this:

1. Confirm stable reverted baseline.
2. Create `HeroAI/follow/` only.
3. Copy `following.py` into `HeroAI/follow/leader_publish.py`.
4. Copy `follow_runtime.py` into `HeroAI/follow/follower_runtime.py`.
5. Copy `follow_movement.py` into `HeroAI/follow/vector_fields.py`.
6. Copy `following_module.py` into `HeroAI/follow/editor.py`.
7. Add minimal `__init__.py`.
8. Do not change imports anywhere.
9. Compile.
10. Launch and verify unchanged behavior.

Only after that should the next session start consumer migration.

---

## Final Recommendation

The rebuild should be treated as a staged migration, not a refactor.

The correct order is:

1. move code
2. preserve old behavior
3. preserve old names
4. preserve old import graph
5. migrate one consumer
6. test
7. migrate next consumer
8. test
9. only then improve architecture

That is the only reliable way to find which exact change introduces instability.


# Hex Removal Architecture And Authoring

This document describes the cross-hero hex-removal system: the priority
table, the per-character configuration GUI, the cross-hero coordination
layer, and how to wire a hex-removal skill into a build.

It is based on:

- `Py4GWCoreLib/GlobalCache/HexRemovalPriority.py`
- `Py4GWCoreLib/GlobalCache/WhiteboardLocks.py`
- `HeroAI/hex_removal_src/hex_removal_config.py`
- `HeroAI/hex_removal_src/hex_removal_ui.py`
- `HeroAI/ui_base.py` (Hex Removal tab wiring)
- `Py4GWCoreLib/Builds/Skills/Monk/NoAttribute.py` (`Remove_Hex` reference helper)
- `Py4GWCoreLib/Builds/Skills/mesmer/DominationMagic.py` (`Shatter_Hex` reference helper)
- `Py4GWCoreLib/Builds/Ritualist/Rt_Any/Soul Twisting.py` (reference rotation)

## Purpose

In a multibox party, multiple clients can each see the same hex on the
same teammate. Without coordination, they all cast hex-removal at once,
wasting energy and cast time. The hex-removal system answers two
questions in cooperation:

1. **Which hexed teammate, and which hex on them, is worth removing?**
   This is per-hex priority, per-target-role, with optional per-profession
   overrides. Configured per character.

2. **Which client gets to remove it?**
   This is whiteboard-based cross-hero coordination, mirroring the
   existing skill-target lock pattern.

The system is the back-end. Each character on each account configures
their own priorities through the in-game GUI; the runtime selector and
build helpers consume the same merged data.

## Implementation Files

- `Py4GWCoreLib/GlobalCache/HexRemovalPriority.py`
  - Priority enums, the default table, the resolved skill-id lookup,
    the selector (`get_hexed_ally_for_removal`), and the cast wrapper
    (`cast_hex_removal_and_track`).
- `Py4GWCoreLib/GlobalCache/WhiteboardLocks.py`
  - Cross-hero lock helpers for `WhiteboardLockKind.HEX_REMOVAL_TARGET`.
- `HeroAI/hex_removal_src/hex_removal_config.py`
  - Per-character JSONC persistence, parser/serializer, runtime debug-flag
    application, hot-reload invalidation.
- `HeroAI/hex_removal_src/hex_removal_ui.py`
  - The Hex Removal tab UI. Profession sub-tabs, configure panel,
    Settings sub-tab, Info sub-tab.
- `HeroAI/ui_base.py`
  - 4-line lazy import that mounts the tab inside
    `DrawBuildMatchesWindow`.

## Data Model

### Priority levels

```python
class HexRemovalPriority(IntEnum):
    NONE = 0     # never remove on this role
    LOW = 1      # remove only if nothing better
    MEDIUM = 2   # standard cleanup
    HIGH = 3     # urgent removal
```

### Target roles

```python
class TargetRole(IntEnum):
    MELEE = 1            # Warrior, Assassin, Dervish
    RANGED_MARTIAL = 2   # Ranger, Paragon
    CASTER = 3           # Mesmer, Necromancer, Elementalist, Monk, Ritualist
```

A target's role is resolved from its primary profession via
`get_target_role(agent_id)`, which is per-zone cached because GW1 reuses
agent IDs across maps.

### Per-hex entry

```python
@dataclass(frozen=True)
class HexRemovalEntry:
    caster: HexRemovalPriority
    ranged_martial: HexRemovalPriority
    melee: HexRemovalPriority
    by_profession: dict[int, HexRemovalPriority] = field(default_factory=dict)

    def for_target(self, role: TargetRole, profession_id: int) -> HexRemovalPriority:
        if profession_id in self.by_profession:
            return self.by_profession[profession_id]
        if role == TargetRole.MELEE:
            return self.melee
        if role == TargetRole.RANGED_MARTIAL:
            return self.ranged_martial
        return self.caster
```

`by_profession` is the override layer. It wins over the role priority
when present. Example: `Empathy` is `caster=NONE, ranged=HIGH, melee=HIGH`,
but a build author can also override `{Monk: NONE}` so the system never
strips Empathy off a monk teammate.

### Default table

`_HEX_DEFAULTS_TABLE` in `HexRemovalPriority.py` is a flat list of
`(name, caster, ranged, melee, by_profession_or_None)` tuples covering
~146 PvE hexes from Mesmer, Necromancer, Elementalist, Monk, Assassin,
and Ritualist. The table is the single source of truth for defaults; it
is built into `_HEX_DEFAULTS: dict[str, HexRemovalEntry]` at module
import.

PvP-suffixed and PvE-only rank-gated hexes are deliberately excluded.

### Resolved priority dict

`_build_hex_removal_priority()` is a lazy first-call builder that
produces the runtime dict:

```python
HEX_REMOVAL_PRIORITY: dict[int, HexRemovalEntry] = {}
_NAME_BY_SKILL_ID: dict[int, str] = {}
```

The build pipeline:

1. Read `_HEX_DEFAULTS` (name -> entry, ~146 entries).
2. Lazy-import `HeroAI.hex_removal_src.hex_removal_config.load_active_overrides()`
   and merge user overrides for the active character.
3. Resolve every name to a skill-id via `GLOBAL_CACHE.Skill.GetID(name)`.
   Names that fail to resolve are silently dropped.
4. Populate `HEX_REMOVAL_PRIORITY[skill_id] = entry` and
   `_NAME_BY_SKILL_ID[skill_id] = name`.

`invalidate_hex_removal_priority()` clears both dicts and the built flag.
The next selector call will rebuild from defaults plus the now-current
overrides. The GUI calls invalidate after every save so edits take
effect on the next selector tick.

## Per-Character Configuration

### File path

```text
<projects>/Settings/<account_email>/HeroAI/Hex removal/<character_name>/hex_removal_config.json
```

Each character on the account has an independent config. The cache key
in `hex_removal_config.py` is the `(email, character_name)` tuple, so a
character switch mid-session triggers a reload automatically.

The folder name `Hex removal` is the `CONFIG_SUBDIR` constant.

### File format

JSONC. The reader strips `//` line comments and `/* */` block comments
before `json.loads`, so users can add comments to a hand-edited file.
The writer emits a canonical header explaining the schema, then
profession-grouped sections separated by `// --- Mesmer ---` dividers.

```jsonc
// HeroAI Hex Removal Configuration
// (canonical header explaining roles, priorities, by_profession)
{
  "schema": "py4gw_hex_removal_v1",
  "debug": {
    "hex_removal": true,
    "hex_removal_locks": false
  },
  "hexes": {
    // --- Mesmer ---
    "Empathy": { "caster": "NONE", "ranged_martial": "HIGH", "melee": "HIGH", "by_profession": {} },
    "Shame":   { "caster": "HIGH", "ranged_martial": "NONE", "melee": "NONE",
                 "by_profession": { "Dervish": "MED" } }
  }
}
```

Field reference (all required per hex):

| Field | Type | Allowed values |
| --- | --- | --- |
| `caster` | string | `NONE`, `LOW`, `MED`, `HIGH` |
| `ranged_martial` | string | same |
| `melee` | string | same |
| `by_profession` | object | `{}` or `{ProfessionName: Priority}` |

Top-level fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `schema` | string | Must equal `"py4gw_hex_removal_v1"`, otherwise the file is treated as corrupt and rebuilt from defaults. |
| `debug.hex_removal` | bool | Drives `HexRemovalPriority.HEX_REMOVAL_DEBUG`. |
| `debug.hex_removal_locks` | bool | Drives `WHITEBOARD_DEBUG_KINDS[HEX_REMOVAL_TARGET]`. |
| `hexes` | object | Map of hex name -> per-hex entry. |

Profession names: `Warrior`, `Ranger`, `Monk`, `Necromancer`, `Mesmer`,
`Elementalist`, `Assassin`, `Ritualist`, `Paragon`, `Dervish`.

### Migration

On load, any default-table hex missing from the file is added with the
current default value. The file is rewritten so it stays current.

There is no automatic propagation of default-table changes to entries
that already exist in the file. Power users wanting a fresh start can
delete the file or use the Settings tab's hard reset.

A legacy `"modified": true` field on entries (from an earlier prototype)
is parsed but ignored. The writer never emits it.

## Public API

### `HexRemovalPriority` module

| Symbol | Purpose |
| --- | --- |
| `HexRemovalPriority` (IntEnum) | Priority levels. |
| `TargetRole` (IntEnum) | Target classification. |
| `HexRemovalEntry` (frozen dataclass) | Per-hex priority record. |
| `HEX_REMOVAL_PRIORITY` | Resolved `dict[skill_id, HexRemovalEntry]`. |
| `_HEX_DEFAULTS` | Resolved-by-name `dict[name, HexRemovalEntry]`. |
| `_HEX_DEFAULTS_TABLE` | Source-of-truth tuple list. |
| `MIN_HEX_REMAINING_MS_TO_REMOVE` | `2500`. Skip hexes with `<=2500ms` remaining regardless of priority. |
| `HEX_REMOVAL_DEBUG` | Master gate for `[HexRemoval]` console logs. |
| `_build_hex_removal_priority()` | Lazy build. Idempotent. |
| `invalidate_hex_removal_priority()` | Clear caches; force rebuild on next call. |
| `get_skill_id_to_name()` | Reverse map for the GUI. |
| `get_target_role(agent_id)` | Returns `(role, profession_id)`. Per-zone cached. |
| `classify_hex_with_role(hex_skill_id, role, profession_id)` | Pre-resolved variant. |
| `classify_hex_for_removal(hex_skill_id, target_agent_id)` | One-shot variant. |
| `get_hex_skill_ids_on_agent(agent_id)` | SHMEM with local fallback. |
| `get_hexed_ally_array(max_distance, min_priority)` | Sorted ally list above threshold. |
| `get_hexed_ally_for_removal(...)` | Pick + reserve. The build-helper entry point. |
| `cast_hex_removal_and_track(build, skill_id, target_agent_id, aftercast_delay)` | Cast wrapper with early lock release on success. |

### `hex_removal_config` module

| Symbol | Purpose |
| --- | --- |
| `ConfigState` | In-memory state: debug flags + hexes. |
| `_NAME_BY_PROFESSION_ID` / `_PROFESSION_BY_NAME` / `_PROFESSION_ORDER` | Profession name lookups used by the GUI. |
| `load_active_overrides()` | Returns `dict[name, HexRemovalEntry]` for the active character. |
| `has_override(name)` | Legacy stub, always `False`. |
| `set_override(name, entry)` | Persist + invalidate. |
| `clear_override(name)` | Reset to default + invalidate. |
| `hard_reset_all_to_none()` | Set every default-table hex to NONE everywhere. |
| `get_debug_flags()` / `set_debug_flags(...)` | Debug toggles. Mirrors flags into the runtime modules. |
| `export_to_desktop()` | Write current config to `~/Desktop/hex_removal_config.json`. |
| `import_from_text(payload)` | Validate a JSONC payload. Returns `(ok, message, parsed_state)`. |
| `commit_imported(parsed)` | Replace active config (post-confirmation). |

## Selector

`get_hexed_ally_for_removal(max_distance, reserve, skill_id, aftercast_delay, min_priority)`
is the single entry point used by build helpers and HeroAI combat.

Pipeline:

1. Pre-condition gate. When `reserve=True` and `skill_id` is given, abort
   if `IsSkillIDReady` or `HasEnoughEnergy` fails. This prevents posting a
   phantom whiteboard lock that would block other clients while no cast
   fires.
2. Single frame-cached scan via `_get_scored_hexed_allies(max_distance)`:
   - filter party members within distance, alive
   - for each ally, resolve role once
   - read shared-memory buffs (cross-account visibility) with local
     `Effects` fallback
   - classify each hex via `classify_hex_with_role`; track the worst
     priority that meets `min_priority`
   - drop hexes with `<= MIN_HEX_REMAINING_MS_TO_REMOVE` remaining
   - sort `(priority desc, distance asc)`
3. Filter out targets locked by other clients via
   `filter_unlocked_hex_targets(...)`.
4. Pick the top remaining target.
5. If `reserve=True`, post a `HEX_REMOVAL_TARGET` whiteboard lock for
   `(owner, target)` with a duration of
   `HEX_REMOVAL_LOCK_MIN_DURATION_MS + activation_ms + aftercast_ms +
   ping_budget`.
6. Return the selected agent id (`0` on miss).

The `@frame_cache` on `_get_scored_hexed_allies` is critical: when a
build's rotation calls hex-removal at three priority tiers in the same
frame, the scan runs once and all three callers share the result.

## Cross-Hero Coordination

Hex-removal locks live in the same shared-memory whiteboard table used
by skill-target coordination. The kind is
`WhiteboardLockKind.HEX_REMOVAL_TARGET = 13`.

`WhiteboardLocks.py` exposes the hex-removal-scoped helpers:

```python
is_hex_removal_lock_blocked(agent_id) -> bool
filter_unlocked_hex_targets(agent_ids: list[int]) -> list[int]
post_hex_removal_lock(agent_id, skill_id, aftercast_delay) -> int
clear_hex_removal_lock(agent_id) -> None
```

`post_hex_removal_lock` deduplicates per `(owner, target, group)`. Without
dedup, a 3-tier rotation that posts at HIGH, then MED, then LOW in the
same tick would create 2-3 redundant locks; the dedup short-circuits
back to the existing slot.

`cast_hex_removal_and_track` releases the lock early (via
`clear_hex_removal_lock`) when a cast confirms it actually removed a hex.
The hex-count delta on the target shrinks by at least one. Early release
lets another client step in for the next hex on the same teammate
without waiting for the lock's natural expiry.

## Wiring A Hex-Removal Skill

The `Remove_Hex` helper in `Py4GWCoreLib/Builds/Skills/Monk/NoAttribute.py`
is the canonical template:

```python
from Py4GWCoreLib.GlobalCache.HexRemovalPriority import (
    HexRemovalPriority, cast_hex_removal_and_track, get_hexed_ally_for_removal,
)

def Remove_Hex(self, min_priority: int = HexRemovalPriority.LOW) -> BuildCoroutine:
    remove_hex_id: int = Skill.GetID("Remove_Hex")

    if not self.build.IsSkillEquipped(remove_hex_id):
        return False

    target_agent_id = get_hexed_ally_for_removal(
        Range.Spellcast.value,
        reserve=True,
        skill_id=remove_hex_id,
        min_priority=min_priority,
    )
    if not target_agent_id:
        return False

    return (yield from cast_hex_removal_and_track(
        self.build,
        skill_id=remove_hex_id,
        target_agent_id=target_agent_id,
        aftercast_delay=250,
    ))
```

Three steps every helper must follow:

1. **Equipped check** with `IsSkillEquipped`. The selector's inner
   `IsSkillIDReady`/`HasEnoughEnergy` gates protect cooldown and energy
   on top of that.
2. **Pick + reserve** via `get_hexed_ally_for_removal(reserve=True,
   skill_id=...)`. Always pass `reserve=True` and the actual `skill_id`
   from the build, otherwise the cross-hero lock is not posted.
3. **Cast + track** via `cast_hex_removal_and_track`. Do not call
   `CastSkillIDAndRestoreTarget` directly; the wrapper handles
   `[HexRemoval] casting / removed` logs and the early lock release.

The same template applies to Holy_Veil, Cure_Hex, Convert_Hexes,
Reverse_Hex, etc. Only the skill name and (sometimes) the
`aftercast_delay` change.

Gate the helper with `IsSkillEquipped`, not `CanCastSkillID`. The
~100 other skill helpers in the codebase use `IsSkillEquipped`;
`CanCastSkillID` adds nothing the inner gate inside the selector does
not already provide.

## Run-Skill Logic In Builds

The convention is a 3-slot rotation with energy gates:

- **HIGH** at the top, no energy gate. Always cast on emergencies.
- **MEDIUM** mid-rotation, gated `>= 0.50` energy.
- **LOW** at the bottom, gated `>= 0.70` energy.

Real example from `Py4GWCoreLib/Builds/Ritualist/Rt_Any/Soul Twisting.py`:

```python
def _run_local_skill_logic(self):
    if not Routines.Checks.Skills.CanCast():
        yield from Routines.Yield.wait(100)
        return False

    snapshot = self._get_bar_snapshot()
    if not snapshot.close_to_aggro:
        return False

    # HIGH - always cast on emergencies
    if (yield from self.skills.Monk.NoAttribute.Remove_Hex(min_priority=HexRemovalPriority.HIGH)):
        return True

    # ... main rotation (Soul Twisting upkeep, spirits, etc.) ...

    # MEDIUM - standard cleanup, only if we have energy to spare
    if snapshot.player_energy_pct >= 0.50 and (
        yield from self.skills.Monk.NoAttribute.Remove_Hex(min_priority=HexRemovalPriority.MEDIUM)
    ):
        return True

    # ... rest of rotation ...

    # LOW - filler cleanup at the bottom
    if snapshot.player_energy_pct >= 0.70 and (
        yield from self.skills.Monk.NoAttribute.Remove_Hex()
    ):
        return True

    return False
```

The energy snapshot is populated once per tick:

```python
def _get_bar_snapshot(self) -> _SoulTwistingSnapshot:
    snapshot = _SoulTwistingSnapshot()
    snapshot.in_aggro = bool(self.IsInAggro())
    snapshot.close_to_aggro = snapshot.in_aggro or self.IsCloseToAggro()
    snapshot.player_energy_pct = float(Agent.GetEnergy(Player.GetAgentID()))
    return snapshot
```

Energy gates are inline at the call site, not a kwarg on the helper.
Reading `snapshot.player_energy_pct >= 0.50` next to the call makes the
rotation's intent visible. The same pattern applies to `Shatter_Hex` in
the Energy Surge and Panic builds.

## GUI

The GUI is a 4th tab inserted into the `HeroAI Build Matches` window
(`Hex Removal`). It is wired by a single 4-line lazy import in
`HeroAI/ui_base.py`:

```python
if PyImGui.begin_tab_item("Hex Removal"):
    from HeroAI.hex_removal_src.hex_removal_ui import draw_tab as _draw_hex_removal_tab
    _draw_hex_removal_tab()
    PyImGui.end_tab_item()
```

`draw_tab()` is the only public symbol of the UI module.

### Tab structure

- One sub-tab per profession that has at least one hex in the default
  table (currently 6: Mesmer, Necromancer, Elementalist, Monk, Assassin,
  Ritualist). An `Other` tab catches hexes whose profession could not be
  resolved.
- A `Settings` sub-tab.
- An `Info` sub-tab with a usage cheat-sheet.

Profession sub-tab layout:

- A `Search` input filters hexes by name.
- Hexes are listed alphabetically.
- Each row shows the icon, the bold hex name, an inline priority
  preview (`Caster: NONE  Ranged-martial: HIGH  Melee: HIGH (+1 override)`),
  and a `Reset` button at the right edge.
- Clicking anywhere on the row toggles an inline configure panel.

Configure panel layout (matches the Skill Editor table style):

- A 2-column table `Role | Priority` with three rows (Caster,
  Ranged-martial, Melee). Each row shows a 4-button segmented selector
  (`NONE | LOW | MED | HIGH`). The selected button is tinted; the rest
  are default grey.
- A 3-column table `Profession overrides | Priority | (action)` listing
  the existing overrides plus an `Add override:` row with a profession
  dropdown and `+ Add` button.

### Settings sub-tab

- `Import config` toggles a paste-from-clipboard panel:
  `Paste from Clipboard` -> `Validate` -> `Replace` confirmation.
- `Export config to desktop` writes the current state to
  `~/Desktop/hex_removal_config.json`.
- `Debug` section: two checkboxes for `[HexRemoval]` logs and for the
  whiteboard's `HEX_REMOVAL_TARGET` lock logs.
- `Reset config` section: a red button opens a confirmation modal,
  which calls `hard_reset_all_to_none()` on confirm.

### Info sub-tab

Static aligned reference: priorities, roles, profession overrides
example, per-row controls, settings. Two-column tables align term
and description columns at a shared X position.

## Hot Reload

Every GUI mutation flows through `set_override` / `clear_override` /
`hard_reset_all_to_none` / `commit_imported` / `set_debug_flags`. Each
of these:

1. Mutates the in-memory `ConfigState`.
2. Calls `_save_active(state)` which writes the JSONC file.
3. Calls `_invalidate_priority()` which clears
   `HEX_REMOVAL_PRIORITY` and the built flag in the priority module.

The next selector tick rebuilds. Edits take effect within one frame;
they do not require a restart.

## Debug Logging

Two independent gates control hex-removal log volume.

`HEX_REMOVAL_DEBUG` (in `HexRemovalPriority.py`) gates the
`[HexRemoval]` lines:

- `detected: <hex> on <Name>(Profession, role) priority=HIGH remaining=4200ms`
- `picked: <Name>(Profession, role) for <skill> min_priority=HIGH`
- `casting <skill> on <Name>(#agent_id) hexes=[...]`
- `removed [<hex>] from <Name>; lock released`
- `no_target: N hexed ally/allies above min_priority=HIGH all blocked by other clients`

Detection is throttled per `(agent, hex)` to
`HEX_REMOVAL_DETECTION_THROTTLE_MS = 2000` to avoid log floods.

`WHITEBOARD_DEBUG_KINDS[HEX_REMOVAL_TARGET]` (in `AllAccounts.py`) gates
the `[Whiteboard]` POST/CLEAR/SWEEP lines for hex-removal locks
specifically. The whiteboard master toggle `WHITEBOARD_DEBUG` must also
be on.

The GUI Settings tab exposes both as checkboxes.

Edit-time confirmation logs always emit (regardless of either flag) so
users see immediate feedback outside combat:

```text
[HexRemoval] 'Empathy' - changed caster priority to LOW
[HexRemoval] 'Empathy' - added Paragon override (HIGH)
[HexRemoval] 'Empathy' - removed Paragon override
[HexRemoval] 'Empathy' - reset to default
[HexRemoval] hard reset: every hex set to NONE on every role
[HexRemoval] debug toggles updated: hex_removal=True, hex_removal_locks=False
```

## Import / Export

Export writes the current state to
`os.path.expanduser("~") + "/Desktop/hex_removal_config.json"`. Silent
overwrite of any prior export. Returns `(ok, path_or_error)`.

Import is a 3-stage flow:

1. `Paste from Clipboard` reads `PyImGui.get_clipboard_text()` into a
   buffer.
2. `Validate` calls `import_from_text(payload)`. Returns
   `(ok, message, parsed_state)`. Schema and per-row validation happens
   here; bad rows are dropped with a console log.
3. `Replace` calls `commit_imported(parsed)`. Runs the same normalize
   pipeline as load (migration of missing defaults), writes the file,
   invalidates the priority cache.

## Tuning Constants

Defined in `HexRemovalPriority.py`:

- `MIN_HEX_REMAINING_MS_TO_REMOVE = 2500` - skip hexes with at most
  this many ms remaining regardless of priority. Applies even to HIGH.
- `HEX_REMOVAL_DETECTION_THROTTLE_MS = 2000` - per-`(agent, hex)`
  detection log throttle.

Defined in `WhiteboardLocks.py`:

- `HEX_REMOVAL_LOCK_MIN_DURATION_MS = 750` - floor for the lock's
  active window. Effective duration also includes activation, aftercast,
  and ping budget.

These are tuned values; do not change without re-confirming behaviour
in multibox testing.

## Known Limitations

- Hex-removal currently only ships for builds that inherit `BuildMgr`
  and use the `self.skills.<Profession>.<Attribute>.<Skill>()` helper
  pattern. Builds that use the older direct-cast pattern will not
  participate in cross-hero coordination unless they are migrated.
- Wired BuildMgr helpers as of this writing: `Shatter_Hex` (mesmer/
  DominationMagic), `Remove_Hex` (Monk/NoAttribute). Other hex-removal
  skills follow the same template (Holy_Veil, Convert_Hexes,
  Reverse_Hex, Cure_Hex, Smite_Hex, Divert_Hexes, Inspired_Hex,
  Revealed_Hex, Expel_Hexes, Drain_Delusions).
- Builds wired to use the helpers in their rotation: Energy Surge
  (Mesmer), Panic (Mesmer), Soul Twisting (Ritualist).
- Per-hex `disable` is not a separate toggle. Setting all three role
  priorities and all profession overrides to NONE achieves the same
  effect.
- Default-table changes do not auto-propagate to existing per-character
  files. Power users can hand-edit, hard-reset, or delete the file to
  re-seed.

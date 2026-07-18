# Agent Name-Tag Coloring (`PyAgentTagColor`)

Recolor agent overhead **name tags** (players, NPCs, enemies) — and the shared
consider/target ring — **using the game's own renderer**. No ImGui/overlay
drawing, no packet faking: the feature detours the native color resolver the
engine itself calls, so the tags are drawn by Guild Wars in the color you choose.

- **Reverse-engineering / internals:** `docs/RE/name_tag_color_reverse_engineering.md`.
- **Native source:** `Py4GW/include/py_agent_tag_color.h`, `Py4GW/src/py_agent_tag_color.cpp`.
- **Type stub:** `stubs/PyAgentTagColor.pyi`.
- **Test harness:** `tests/name_tag_color/name_tag_color_test.py`.

## How it works (one paragraph)

Guild Wars decides an agent tag's color in a single resolver
(`CCharAgent::GetConsiderColor`, EXE `FUN_007f02e0`) that reads the agent's
allegiance/team/state and writes an ARGB color, which the name-tag renderer then
draws. `PyAgentTagColor` installs a MinHook detour on that resolver: it lets the
game compute its default, then — for agents matching a rule — overwrites the
color in place. Because the game re-runs the resolver on every tag update, the
override is durable (unlike a one-shot UI message, which the game would overwrite).

## Color format

Colors are **ARGB `0xAARRGGBB`** (alpha in the high byte). Opaque red is
`0xFFFF0000`. The `Py4GWCoreLib` `Color` helper produces this directly:

```python
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette

Color(255, 0, 255, 255).to_dx_color()      # -> 0xFFFF00FF (magenta, ARGB)
Color.from_hex('#FF00FF').to_dx_color()     # same, from hex
ColorPalette.GwMonk.value.to_dx_color()     # a profession color as ARGB
```

Use `.to_dx_color()` (ARGB), **not** `.to_color()` (that is ABGR, for the overlay).

## Python API

Embedded module `PyAgentTagColor` (import directly). Rule precedence:
**per-agent → per-allegiance → game default.**

| Function | Description |
|----------|-------------|
| `enable()` / `disable()` / `is_enabled()` | Master gate. The detour stays installed; disabling just short-circuits it (game defaults return). |
| `is_hook_installed()` | `True` if the resolver detour resolved and installed at DLL init. If `False`, the DLL is stale/mismatched — rebuild + reinject. |
| `set_agent_color(agent_id, argb)` | Override one agent's tag color (highest precedence). |
| `remove_agent_color(agent_id)` | Drop that per-agent override. |
| `set_allegiance_color(allegiance, argb)` | Override a whole category. `allegiance` is 1=Ally, 2=Neutral, 3=Enemy, 4=SpiritPet, 5=Minion, 6=NpcMinipet. |
| `remove_allegiance_color(allegiance)` | Drop that per-allegiance override. |
| `clear_rules()` | Drop all overrides (everyone reverts to game defaults). |
| `get_agent_rules()` / `get_allegiance_rules()` | Inspect the current rule maps (`{id: argb}` / `{allegiance: argb}`). |
| `read_consider_color(agent_id)` | Read-only: the ARGB the game currently computes for an agent (via the original resolver, unaffected by overrides). `0` for non-living/invalid agents. |
| `get_diagnostics()` / `reset_diagnostics()` | Counters: `initialized`, `hook_installed`, `enabled`, `resolver_calls_seen`, `agent_rule_hits`, `allegiance_rule_hits`, `last_agent_id`, `last_color`. |

## Usage

```python
import PyAgentTagColor
from Py4GWCoreLib.py4gwcorelib_src.Color import Color

# Paint all enemies magenta, all allies cyan.
PyAgentTagColor.set_allegiance_color(3, Color(255, 0, 255, 255).to_dx_color())  # enemies
PyAgentTagColor.set_allegiance_color(1, Color(0, 255, 255, 255).to_dx_color())  # allies
PyAgentTagColor.enable()

# Highlight one specific agent (overrides the allegiance rule for that agent).
PyAgentTagColor.set_agent_color(my_target_id, 0xFFFFFF00)  # yellow

# Revert.
PyAgentTagColor.disable()          # or:
PyAgentTagColor.clear_rules()
```

## Behavior and gotchas

- **You must `enable()`.** Setting rules alone does nothing; the detour only
  applies rules while enabled.
- **Tags recolor when the game re-resolves them.** A tag only repaints while it
  is being drawn — hold **Ctrl** or turn on "always show names" so tags are
  visible and re-resolved. A rule set for an off-screen/hidden tag applies as
  soon as that tag next renders.
- **Overrides also affect the consider/target ring**, which shares the resolver.
  This is intentional.
- **Never call `read_consider_color` on non-living agents.** Items, gadgets, and
  signposts are not char agents; the underlying resolver asserts and would crash
  the client. The native module guards this (returns `0`), and the harness only
  enumerates living agents — but if you write your own loop, filter to living
  agents (e.g. `AgentArray.GetEnemyArray()` / `GetAllyArray()` / `GetNeutralArray()`).
- **Item ground labels are not covered.** Item rarity color is markup-based, a
  different (unimplemented) mechanism — see the RE doc §4.

## Default colors (for reference)

The game's own defaults, which overrides replace (ARGB):

| Category | Default |
|----------|---------|
| Enemy | `0xFFFF0000` red |
| Ally / friendly (non-player) | `0xFF00FF00` green |
| NPC / minipet | `0xFFA0FF00` yellow-green |
| Self / your party (outpost) | `0xFF40FF40` |
| Party member | `0xFF6060FF` |
| Other player (non-party) | `0xFF9BBEFF` |
| Dead / dimmed / default | `0xFFA0A0A0` gray |

## Testing

Load `tests/name_tag_color/name_tag_color_test.py` in-client (like the `UI_RE/`
harnesses) on a loaded map. **Validate visible agents** compares each living
agent's RE-expected default against the game's actual color (PASS/FAIL/UNKNOWN);
the **Overrides** section drives the module live. See the folder README.

## Building the DLL

The feature is native. To rebuild after changes (in `C:\Users\Apo\Py4GW`):

```
cmake -S . -B build                 # only needed after adding/removing files
cmake --build build --config RelWithDebInfo --target Py4GW
```

Then copy `bin/RelWithDebInfo/Py4GW.dll` to the launcher directory
(`Py4GW_files\Py4GW.dll`) and re-inject. RelWithDebInfo is the deployed config.

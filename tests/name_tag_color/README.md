# Name-Tag Color Tests

In-client test harness for native agent name-tag coloring (`PyAgentTagColor`),
which detours the game's own color resolver `AvCharGetConsiderColor`
(EXE `FUN_007d9cf0`). RE reference: `docs/RE/name_tag_color_reverse_engineering.md`.

## Contents

- `name_tag_color_test.py` — the harness. UI_RE-style: passive except on button
  clicks, per-frame `main()`, crash-safe logging.

## Requirements

- The **current rebuilt DLL** injected (must contain `PyAgentTagColor`). Build:
  `cmake --build build --config RelWithDebInfo --target Py4GW` in `C:\Users\Apo\Py4GW`,
  then copy `bin/RelWithDebInfo/Py4GW.dll` to the launcher dir, and re-inject.
- Run on a **loaded map** with visible agents.

## How to run

Load `name_tag_color_test.py` the same way you load the `UI_RE/` harnesses
(exec/script runner). Then, in the window:

1. **Module status** — confirm `hook_installed = True` and import OK. If it says
   "PyAgentTagColor NOT loaded", rebuild + reinject the DLL.
2. **Validate visible agents** — compares the RE-expected default color against
   the game's actual color (`read_consider_color`) per agent → `PASS/FAIL/UNKNOWN`.
   Results auto-save to `results.txt`; the log auto-saves to `log.txt`.
3. **Overrides** — enter an agent id + ARGB hex (e.g. `FFFF00FF`), `Set agent
   color`, then `Enable`. Or `Enemies -> magenta` / `Allies -> cyan`. `Clear
   rules` / `Disable` revert to the game defaults.

## Expected first result

On a normal map, validation should be mostly `PASS`: enemies `0xFFFF0000` (red),
non-player allies `0xFF00FF00` (green), NPC/minipet `0xFFA0FF00`, players in the
blue/green family. `UNKNOWN` means `read_consider_color` was unavailable (DLL not
rebuilt). A cluster of `FAIL` means the RE color table or the resolver mapping
needs a second look — capture `results.txt` and the log.

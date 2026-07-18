"""
name_tag_color_test.py - in-client test harness for native agent name-tag coloring.

Exercises the PyAgentTagColor embedded module (resolver detour on
AvCharGetConsiderColor / FUN_007d9cf0) end-to-end AND validates the RE'd
allegiance -> color table against the live client. See
docs/RE/name_tag_color_reverse_engineering.md.

Workflow:
  1. Load this harness in-client (REQUIRES the current rebuilt DLL).
  2. Check "Module status": confirm import OK and hook_installed == True.
  3. Click "Validate visible agents": for every agent it compares the RE-expected
     default color against the game's ACTUAL computed color (read_consider_color)
     and marks PASS / FAIL / UNKNOWN. Results AUTO-SAVE to results.txt on every run.
  4. Try overrides: set a per-agent or per-allegiance color, Enable, and watch the
     tag recolor natively in-game. Disable / Clear rules to revert.

Verdicts and log auto-save to this folder so a native crash never loses the trail.

This module follows the UI_RE harness convention: passive except on button clicks,
per-frame main(), no polling loops beyond the live status line.
"""

import os
import time
import traceback

import PyImGui

MODULE_NAME = "Name-Tag Color Test"

# Py4GW exec's this script as a string, so __file__ may be undefined — fall back
# to the known abs path (mirrors UI_RE harnesses).
try:
    _BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _cand = os.path.join(os.getcwd(), "tests", "name_tag_color")
    _BASE = _cand if os.path.isdir(_cand) else r"C:\Users\Apo\Py4GW_python_files\tests\name_tag_color"

RESULTS_PATH = os.path.join(_BASE, "results.txt")
LOG_PATH = os.path.join(_BASE, "log.txt")

# RE'd default name-tag colors, ARGB 0xAARRGGBB. See RE doc section 3.
COLOR_ENEMY = 0xFFFF0000  # allegiance 3
COLOR_NPC_MINIPET = 0xFFA0FF00  # allegiance 6
COLOR_ALLY = 0xFF00FF00  # allegiance 1/2/4/5 (non-player)
COLOR_SELF_PARTY = 0xFF40FF40
COLOR_PARTY = 0xFF6060FF
COLOR_OTHER_PLAYER = 0xFF9BBEFF
COLOR_DEAD_DIM = 0xFFA0A0A0
# Players resolve within this family; we cannot cheaply distinguish
# self/party/other from Python, so any of these is a pass for a player tag.
PLAYER_FAMILY = (COLOR_SELF_PARTY, COLOR_PARTY, COLOR_OTHER_PLAYER, COLOR_DEAD_DIM)

# Allegiance ids (Py4GWCoreLib.enums_src.GameData_enums.Allegiance).
ALLEGIANCE_ALLY = 1
ALLEGIANCE_ENEMY = 3
ALLEGIANCE_NPC_MINIPET = 6

MAGENTA = 0xFFFF00FF
CYAN = 0xFF00FFFF

_log: list = []
_rows: list = []  # last validation snapshot: list of dict
_summary = {"pass": 0, "fail": 0, "unknown": 0}
_last_error: str | None = None
_ui_agent_id = 0
_ui_color_hex = "FFFF00FF"


def _log_msg(m: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    _log.append(line)
    print(f"[{MODULE_NAME}] {m}")
    if len(_log) > 200:
        _log[:] = _log[-200:]
    # CRASH-SAFE: append + flush + fsync so a native crash mid-test still leaves the trail.
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:  # noqa: BLE001
        pass


def _argb(value: int | None) -> str:
    if value is None:
        return "<none>"
    return f"0x{value & 0xFFFFFFFF:08X}"


def _module():
    """Lazy-import PyAgentTagColor; None (with logged error) if the DLL lacks it."""
    global _last_error
    try:
        import PyAgentTagColor  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        _last_error = repr(exc)
        _log_msg(f"PyAgentTagColor import failed (rebuild+reinject DLL?): {exc!r}")
        return None
    _last_error = None
    return PyAgentTagColor


def _agent_api():
    """Lazy-import the Agent/AgentArray API."""
    global _last_error
    try:
        from Py4GWCoreLib.Agent import Agent
        from Py4GWCoreLib.AgentArray import AgentArray
    except Exception as exc:  # noqa: BLE001
        _last_error = repr(exc)
        _log_msg(f"Agent API import failed: {exc!r}")
        return None
    return Agent, AgentArray


def _expected_color(Agent, agent_id: int) -> tuple[int | None, str, bool]:
    """(expected_argb_or_None, label, is_player) per the RE table."""
    allegiance, alleg_name = Agent.GetAllegiance(agent_id)
    is_player = bool(Agent.IsPlayer(agent_id))
    if allegiance == ALLEGIANCE_ENEMY:
        return COLOR_ENEMY, f"{alleg_name} (enemy)", is_player
    if allegiance == ALLEGIANCE_NPC_MINIPET:
        return COLOR_NPC_MINIPET, f"{alleg_name} (npc/minipet)", is_player
    if is_player:
        return None, f"{alleg_name} (player: blue/green family)", True
    return COLOR_ALLY, f"{alleg_name} (ally/friendly)", False


def _verdict(expected: int | None, actual: int | None, is_player: bool) -> str:
    if actual is None:
        return "UNKNOWN"
    if is_player:
        return "PASS" if (actual & 0xFFFFFFFF) in PLAYER_FAMILY else "FAIL"
    if expected is None:
        return "UNKNOWN"
    return "PASS" if (actual & 0xFFFFFFFF) == (expected & 0xFFFFFFFF) else "FAIL"


def _save_results() -> None:
    try:
        with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
            fh.write(f"# Name-tag color validation @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            fh.write(f"# PASS={_summary['pass']} FAIL={_summary['fail']} UNKNOWN={_summary['unknown']}\n")
            for r in _rows:
                fh.write(
                    f"[{r['verdict']:>7}] id={r['agent_id']} {r['name']!r} :: {r['class']} "
                    f"expected={r['expected']} actual={r['actual']}\n"
                )
            fh.flush()
            os.fsync(fh.fileno())
    except Exception as exc:  # noqa: BLE001
        _log_msg(f"save results failed: {exc!r}")


def validate(limit: int = 60) -> None:
    """Compare RE-expected vs game-actual color for every visible agent."""
    api = _agent_api()
    module = _module()
    if api is None:
        return
    Agent, AgentArray = api
    reader = getattr(module, "read_consider_color", None) if module else None
    if reader is None:
        _log_msg("read_consider_color absent -> expected-only (rebuild DLL for PASS/FAIL)")

    # Only LIVING agents (players/npcs/enemies/spirits/minions). The unfiltered
    # GetAgentArray() also contains items/gadgets/signposts; the resolver asserts
    # on those. Union the pre-filtered living arrays, dedup, preserve order.
    agents: list[int] = []
    seen: set[int] = set()
    try:
        for getter in (AgentArray.GetAllyArray, AgentArray.GetNeutralArray, AgentArray.GetEnemyArray):
            for agent_id in getter():
                if agent_id and agent_id not in seen:
                    seen.add(agent_id)
                    agents.append(agent_id)
    except Exception as exc:  # noqa: BLE001
        _log_msg(f"living agent enumeration failed: {exc!r}")
        return

    _rows.clear()
    _summary.update({"pass": 0, "fail": 0, "unknown": 0})
    for agent_id in agents[: max(0, limit)]:
        try:
            expected, label, is_player = _expected_color(Agent, agent_id)
            name = Agent.GetNameByID(agent_id)
        except Exception as exc:  # noqa: BLE001
            _log_msg(f"agent {agent_id} read failed: {exc!r}")
            continue
        actual: int | None = None
        if reader is not None:
            try:
                actual = int(reader(agent_id)) & 0xFFFFFFFF
            except Exception as exc:  # noqa: BLE001
                _log_msg(f"read_consider_color({agent_id}) failed: {exc!r}")
        verdict = _verdict(expected, actual, is_player)
        _summary[verdict.lower()] = _summary.get(verdict.lower(), 0) + 1
        _rows.append(
            {
                "agent_id": agent_id,
                "name": name,
                "class": label,
                "expected": _argb(expected),
                "actual": _argb(actual),
                "verdict": verdict,
            }
        )

    _log_msg(
        f"validated {len(_rows)} agents | PASS={_summary['pass']} "
        f"FAIL={_summary['fail']} UNKNOWN={_summary['unknown']}"
    )
    _save_results()


def _set_agent_color(agent_id: int, argb: int) -> None:
    module = _module()
    if module is None:
        return
    try:
        module.set_agent_color(int(agent_id), int(argb) & 0xFFFFFFFF)
        _log_msg(f"set_agent_color id={agent_id} -> {_argb(argb)}")
    except Exception as exc:  # noqa: BLE001
        _log_msg(f"set_agent_color failed: {exc!r}")
        traceback.print_exc()


def _set_allegiance_color(allegiance: int, argb: int) -> None:
    module = _module()
    if module is None:
        return
    try:
        module.set_allegiance_color(int(allegiance), int(argb) & 0xFFFFFFFF)
        _log_msg(f"set_allegiance_color allegiance={allegiance} -> {_argb(argb)}")
    except Exception as exc:  # noqa: BLE001
        _log_msg(f"set_allegiance_color failed: {exc!r}")


def _read_game_color(agent_id: int) -> None:
    module = _module()
    if module is None:
        return
    try:
        color = int(module.read_consider_color(int(agent_id))) & 0xFFFFFFFF
        _log_msg(f"read_consider_color id={agent_id} = {_argb(color)}")
    except Exception as exc:  # noqa: BLE001
        _log_msg(f"read_consider_color failed: {exc!r}")


def _status() -> dict:
    module = _module()
    if module is None:
        return {"import_ok": False, "last_error": _last_error}
    try:
        return {
            "import_ok": True,
            "hook_installed": module.is_hook_installed(),
            "enabled": module.is_enabled(),
            "diagnostics": module.get_diagnostics(),
        }
    except Exception as exc:  # noqa: BLE001
        _log_msg(f"status failed: {exc!r}")
        return {"import_ok": True, "error": repr(exc)}


def dump_status() -> None:
    """Write a full status + diagnostics snapshot to log.txt for offline analysis."""
    st = _status()
    _log_msg(f"STATUS {st}")


def main() -> None:
    """Per-frame ImGui window. Acts only on button clicks; polls a live status line."""
    global _ui_agent_id, _ui_color_hex

    if not PyImGui.begin(MODULE_NAME):
        PyImGui.end()
        return

    # --- Module status (live) ---
    st = _status()
    if not st.get("import_ok"):
        PyImGui.text_colored("PyAgentTagColor NOT loaded — rebuild + reinject the DLL.", (1.0, 0.4, 0.4, 1.0))
        if _last_error:
            PyImGui.text(f"import error: {_last_error}")
    else:
        hook = st.get("hook_installed")
        hook_col = (0.3, 1.0, 0.4, 1.0) if hook else (1.0, 0.4, 0.4, 1.0)
        PyImGui.text_colored(f"hook_installed = {hook}", hook_col)
        PyImGui.same_line(0, -1)
        PyImGui.text(f"enabled = {st.get('enabled')}")
        if PyImGui.button("Enable"):
            m = _module()
            if m:
                m.enable()
                _log_msg(f"enabled (is_enabled={m.is_enabled()})")
        PyImGui.same_line(0, -1)
        if PyImGui.button("Disable"):
            m = _module()
            if m:
                m.disable()
                _log_msg(f"disabled (is_enabled={m.is_enabled()})")
        PyImGui.same_line(0, -1)
        if PyImGui.button("Clear rules"):
            m = _module()
            if m:
                m.clear_rules()
                _log_msg("rules cleared")
        PyImGui.same_line(0, -1)
        if PyImGui.button("Reset diag"):
            m = _module()
            if m:
                m.reset_diagnostics()
        PyImGui.same_line(0, -1)
        if PyImGui.button("Dump status -> log"):
            dump_status()
        diag = st.get("diagnostics") or {}
        if diag:
            PyImGui.text(
                f"calls={diag.get('resolver_calls_seen')} agent_hits={diag.get('agent_rule_hits')} "
                f"alleg_hits={diag.get('allegiance_rule_hits')} last={_argb(diag.get('last_color'))}"
            )

    PyImGui.separator()

    # --- Validation ---
    PyImGui.text_colored("=== Validate RE color table vs live client ===", (0.7, 0.7, 0.3, 1.0))
    if PyImGui.button("Validate visible agents"):
        validate()
    PyImGui.same_line(0, -1)
    PyImGui.text(f"PASS={_summary['pass']} FAIL={_summary['fail']} UNKNOWN={_summary['unknown']}")
    if _rows and PyImGui.begin_child("##rows", (0.0, 150.0), True):
        for r in _rows[-40:]:
            col = {
                "PASS": (0.3, 1.0, 0.4, 1.0),
                "FAIL": (1.0, 0.4, 0.4, 1.0),
                "UNKNOWN": (0.6, 0.6, 0.6, 1.0),
            }.get(r["verdict"], (0.7, 0.7, 0.7, 1.0))
            PyImGui.text_colored(f"[{r['verdict']:>7}]", col)
            PyImGui.same_line(0, -1)
            PyImGui.text(f"{r['name']} :: {r['class']} exp={r['expected']} act={r['actual']}")
        PyImGui.end_child()

    PyImGui.separator()

    # --- Overrides ---
    PyImGui.text_colored("=== Overrides ===", (0.7, 0.7, 0.3, 1.0))
    PyImGui.text("Set a rule, click Enable, then make name tags refresh")
    PyImGui.text("(hold Ctrl / 'always show names') so the game re-resolves them.")
    try:
        _ui_agent_id = int(PyImGui.input_int("Agent id", int(_ui_agent_id)))
    except Exception:  # noqa: BLE001
        pass
    _ui_color_hex = PyImGui.input_text("Color ARGB hex (AARRGGBB)", _ui_color_hex)
    if PyImGui.button("Set agent color"):
        try:
            _set_agent_color(_ui_agent_id, int(_ui_color_hex, 16))
        except Exception as exc:  # noqa: BLE001
            _log_msg(f"bad color hex {_ui_color_hex!r}: {exc!r}")
    PyImGui.same_line(0, -1)
    if PyImGui.button("Read game color"):
        _read_game_color(_ui_agent_id)
    PyImGui.same_line(0, -1)
    if PyImGui.button("Remove agent color"):
        m = _module()
        if m:
            m.remove_agent_color(int(_ui_agent_id))

    if PyImGui.button("Enemies -> magenta"):
        _set_allegiance_color(ALLEGIANCE_ENEMY, MAGENTA)
    PyImGui.same_line(0, -1)
    if PyImGui.button("Allies -> cyan"):
        _set_allegiance_color(ALLEGIANCE_ALLY, CYAN)

    PyImGui.separator()
    PyImGui.text_colored("=== Log ===", (0.7, 0.7, 0.3, 1.0))
    if PyImGui.begin_child("##log", (0.0, 120.0), True):
        for line in _log[-12:]:
            PyImGui.text(line)
        PyImGui.end_child()

    PyImGui.end()


def configure() -> None:
    pass


if __name__ == "__main__":
    main()

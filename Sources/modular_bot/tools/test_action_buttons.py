"""
Action button tester for modular actions.

Focuses on engine-sensitive actions and party control actions so you can
verify behavior under either HeroAI or CustomBehaviors.
"""

from __future__ import annotations

import PyImGui

from Py4GWCoreLib import Botting, Console, ConsoleLog, Map, Player
from Sources.modular_bot import ModularBot, Phase
from Sources.modular_bot.recipes.combat_engine import (
    ENGINE_CUSTOM_BEHAVIORS,
    ENGINE_HERO_AI,
    ENGINE_NONE,
    resolve_active_engine,
)
from Sources.modular_bot.recipes.modular_actions import register_step
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler


STEP_COUNTER = 0
TEST_X = 0.0
TEST_Y = 0.0
TEST_MAP_ID = 248
TEST_WAIT_MS = 1500
TEST_MAX_DIST = 5000
MULTIBOX = True
_single_step_bot = Botting("ActionButtonsSingleStepRunner")
_single_step_running = False
_single_step_payload: dict | None = None
_single_step_label = ""
DEBUG_LOGGING = False
# Avoid side effects from upkeep coroutines (notably keep_hero_ai toggling HeroAI widget).
_single_step_bot._start_coroutines = lambda: None


def _debug_log(message: str, message_type=None) -> None:
    if not DEBUG_LOGGING:
        return
    if message_type is None:
        ConsoleLog("ActionButtons", message)
        return
    ConsoleLog("ActionButtons", message, message_type)


def _clear_fsm_states(botting: Botting) -> None:
    fsm = botting.config.FSM
    try:
        fsm.stop()
    except Exception:
        pass
    fsm.states.clear()
    fsm.state_counter = 0
    fsm.current_state = None
    fsm.finished = False
    fsm.paused = False
    fsm.managed_coroutines.clear()
    fsm._named_managed.clear()


def _run_single_step(botting: Botting) -> None:
    global _single_step_payload, _single_step_label
    botting.States.AddCustomState(lambda: None, "Single Step Runner Guard")
    if _single_step_payload is None:
        return

    payload = dict(_single_step_payload)
    label = str(_single_step_label or payload.get("name") or payload.get("type") or "unknown action")
    if not payload.get("name"):
        payload["name"] = label

    botting.States.AddCustomState(
        lambda n=label: _debug_log(f"[EXEC] starting: {n}", Console.MessageType.Info),
        "Log Start",
    )
    register_step(botting, payload, 0, recipe_name="ActionButtons")
    botting.States.AddCustomState(
        lambda n=label: _debug_log(f"[EXEC] finished: {n}", Console.MessageType.Success),
        "Log End",
    )
    _single_step_payload = None
    _single_step_label = ""


_single_step_bot.SetMainRoutine(_run_single_step)


def _queue_step(step: dict, label: str | None = None) -> None:
    global STEP_COUNTER, _single_step_running, _single_step_payload, _single_step_label
    step_idx = STEP_COUNTER + 1
    action_label = str(label or step.get("name") or step.get("type") or "unknown action")
    step_to_register = dict(step)
    if not step_to_register.get("name"):
        step_to_register["name"] = action_label

    _debug_log(
        f"[CLICK] trigger step #{step_idx}: {action_label} -> {step_to_register!r}",
        Console.MessageType.Info,
    )
    _single_step_payload = step_to_register
    _single_step_label = f"#{step_idx} {action_label}"

    try:
        _single_step_bot.Stop()
    except Exception:
        pass
    _clear_fsm_states(_single_step_bot)
    _single_step_bot.config.initialized = False
    _single_step_bot.Routine()
    _single_step_bot.config.initialized = True
    _single_step_bot.Start()
    _single_step_running = True
    _debug_log(
        f"[RUN] started immediate execution for step #{step_idx}: {action_label} (fsm_states={_single_step_bot.config.FSM.get_state_count()})"
    )
    STEP_COUNTER += 1


def _engine_label() -> str:
    engine = resolve_active_engine()
    if engine == ENGINE_CUSTOM_BEHAVIORS:
        return "CustomBehaviors"
    if engine == ENGINE_HERO_AI:
        return "HeroAI"
    return "None"


def _draw_main() -> None:
    global TEST_X, TEST_Y, TEST_MAP_ID, TEST_WAIT_MS, TEST_MAX_DIST, MULTIBOX

    widget_handler = get_widget_handler()
    engine = resolve_active_engine()
    cb_on = widget_handler.is_widget_enabled("CustomBehaviors")
    hero_ai_on = widget_handler.is_widget_enabled("HeroAI")

    PyImGui.text("Modular Action Buttons")
    PyImGui.separator()
    PyImGui.text(f"Detected engine: {_engine_label()}")
    PyImGui.text(f"CustomBehaviors: {'ON' if cb_on else 'OFF'}")
    PyImGui.text(f"HeroAI: {'ON' if hero_ai_on else 'OFF'}")
    if engine == ENGINE_NONE:
        PyImGui.text_colored("No combat engine widget is enabled.", (1.0, 0.45, 0.2, 1.0))

    if cb_on and hero_ai_on:
        PyImGui.text_colored("Both engines are ON. Disable one before testing.", (1.0, 0.2, 0.2, 1.0))

    # Keep action coordinates/map synced to current player state.
    TEST_X, TEST_Y = Player.GetXY()
    TEST_MAP_ID = int(Map.GetMapID() or 0)

    PyImGui.separator()
    PyImGui.text(f"Live Player X/Y: {int(TEST_X)}, {int(TEST_Y)}")
    PyImGui.text(f"Live Map ID: {int(TEST_MAP_ID)}")
    TEST_WAIT_MS = int(PyImGui.input_int("Wait ms", int(TEST_WAIT_MS)))
    TEST_MAX_DIST = int(PyImGui.input_int("Max Dist", int(TEST_MAX_DIST)))
    MULTIBOX = bool(PyImGui.checkbox("Multibox", bool(MULTIBOX)))
    PyImGui.separator()

    PyImGui.text("Engine/Party Actions")
    if PyImGui.button("Set Auto Combat ON"):
        _queue_step({"type": "set_auto_combat", "enabled": True}, "Set Auto Combat ON")
    if PyImGui.button("Set Auto Combat OFF"):
        _queue_step({"type": "set_auto_combat", "enabled": False}, "Set Auto Combat OFF")
    if PyImGui.button("Set Auto Looting ON"):
        _queue_step({"type": "set_auto_looting", "enabled": True}, "Set Auto Looting ON")
    if PyImGui.button("Set Auto Looting OFF"):
        _queue_step({"type": "set_auto_looting", "enabled": False}, "Set Auto Looting OFF")
    if PyImGui.button("Flag All Accounts"):
        _queue_step({"type": "flag_all_accounts", "x": TEST_X, "y": TEST_Y, "ms": TEST_WAIT_MS}, "Flag All Accounts")
    if PyImGui.button("Unflag All Accounts"):
        _queue_step({"type": "unflag_all_accounts", "ms": TEST_WAIT_MS}, "Unflag All Accounts")
    if PyImGui.button("Target Enemy + Party Target"):
        _queue_step(
            {
                "type": "target_enemy",
                "nearest": True,
                "set_party_target": True,
                "max_dist": TEST_MAX_DIST,
                "ms": 250,
            },
            "Target Enemy + Party Target",
        )

    PyImGui.separator()
    PyImGui.text("Movement Actions")
    if PyImGui.button("Travel GH"):
        _queue_step({"type": "travel_gh", "multibox": MULTIBOX, "ms": max(TEST_WAIT_MS, 4000)}, "Travel GH")
    if PyImGui.button("Leave Party"):
        _queue_step({"type": "leave_party", "multibox": MULTIBOX, "ms": 500}, "Leave Party")
    if PyImGui.button("Travel Map"):
        _queue_step({"type": "travel", "target_map_id": TEST_MAP_ID, "ms": TEST_WAIT_MS}, "Travel Map")
    if PyImGui.button("Move XY"):
        _queue_step({"type": "move", "x": TEST_X, "y": TEST_Y, "ms": 200}, "Move XY")
    if PyImGui.button("Wait"):
        _queue_step({"type": "wait", "ms": TEST_WAIT_MS}, "Wait")

    PyImGui.separator()
    PyImGui.text("Hero/Party Helpers")
    if PyImGui.button("Force Hero State: Fight"):
        _queue_step({"type": "force_hero_state", "state": "fight"}, "Force Hero State: Fight")
    if PyImGui.button("Force Hero State: Guard"):
        _queue_step({"type": "force_hero_state", "state": "guard"}, "Force Hero State: Guard")
    if PyImGui.button("Force Hero State: Avoid"):
        _queue_step({"type": "force_hero_state", "state": "avoid"}, "Force Hero State: Avoid")
    if PyImGui.button("Flag Heroes"):
        _queue_step({"type": "flag_heroes", "x": TEST_X, "y": TEST_Y, "ms": TEST_WAIT_MS}, "Flag Heroes")
    if PyImGui.button("Unflag Heroes"):
        _queue_step({"type": "unflag_heroes"}, "Unflag Heroes")
    if PyImGui.button("Resign"):
        _queue_step({"type": "resign"}, "Resign")
    if PyImGui.button("Summon All Accounts"):
        _queue_step({"type": "summon_all_accounts", "ms": TEST_WAIT_MS}, "Summon All Accounts")
    if PyImGui.button("Invite All Accounts"):
        _queue_step({"type": "invite_all_accounts", "ms": 500}, "Invite All Accounts")

    PyImGui.separator()
    PyImGui.text(f"Executed clicks so far: {STEP_COUNTER}")


def _idle_phase(botting) -> None:
    botting.Wait.ForTime(100)


bot = ModularBot(
    name="Action Button Tester",
    phases=[Phase("Idle", _idle_phase)],
    loop=True,
    template="aggressive",
    use_custom_behaviors=False,
    main_ui=_draw_main,
    main_child_dimensions=(460, 820),
)


def main() -> None:
    bot.update()
    _single_step_bot.Update()

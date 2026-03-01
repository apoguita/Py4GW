from Py4GWCoreLib import (
    Botting,
    get_texture_for_model,
    ModelID,
    ConsoleLog,
    Routines,
    Agent,
    Player,
    GLOBAL_CACHE,
    ActionQueueManager,
)
import PyImGui
from Py4GW_widget_manager import get_widget_handler

# QUEST TO INCREASE SPAWNS
BOT_NAME = "Keen Oni Talon Farm"
MODULE_NAME = "Keen Oni Talon Farm (Nicholas the Traveler)"
MODULE_ICON = "Textures\\Module_Icons\\Nicholas the Traveler - Keen Oni Talon.png"
MODEL_ID_TO_FARM = ModelID.Keen_Oni_Talon
OUTPOST_TO_TRAVEL = 234  # The Aurios Mines
COORD_TO_EXIT_MAP = (-6478.70, 6950.40)  # The Aurios Mines to Rhea's Crater
EXPLORABLE_TO_TRAVEL = 202  # Rhea's Crater

KILLING_PATH = [
    (16468.29, 1046.88),
    (13998.01, 2264.00),
    (11959.19, 3844.30),
    (10476.81, 6585.65),
    (12252.20, 7994.86),  # 1st group of Oni's
    (15033.92, 11717.22),
    (16987.31, 13897.07),  # 2nd group of Oni's
    (9692.63, 16167.93),
    (7185.86, 17759.97),
    (4332.39, 16499.87),
    (3366.36, 13466.57),  # 3rd group of Oni's
    (2481.20, 12531.47),
]

NICK_OUTPOST = 279  # Leviathan Pits
COORDS_TO_EXIT_OUTPOST = (9007.48, -26310.26)
EXPLORABLE_AREA = 203  # Silent Surf
NICK_COORDS = [
    (12480.40, 18819.66),
    (11083.69, 16188.29),
    (11217.64, 14229.11),
    (10840.98, 12239.28),  # Nicholas the Traveler Location
]


bot = Botting(BOT_NAME)


def bot_routine(bot: Botting) -> None:
    global CURRENT_SECTION
    _ensure_wipe_handler_registered(bot)
    CURRENT_SECTION = "farm"
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Move.FollowAutoPath(KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")
    CURRENT_SECTION = "nick"
    bot.States.AddHeader("Path_to_Nicholas")
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=NICK_OUTPOST)
    bot.Move.XYAndExitMap(*COORDS_TO_EXIT_OUTPOST, EXPLORABLE_AREA)
    bot.Move.FollowAutoPath(NICK_COORDS)
    bot.Wait.UntilOnOutpost()


bot.SetMainRoutine(bot_routine)


def main_window_extra_ui():
    PyImGui.text("Nicholas the Traveler")
    PyImGui.separator()
    PyImGui.text("Travel to Nicholas the Traveler location")
    if PyImGui.button("Start"):
        bot.StartAtStep("[H]Path_to_Nicholas_4")


_ORIGINAL_PYIMGUI_BUTTON = None
_HUNGRY_BUTTON_PATCH_APPLIED = False
_HUNGRY_LABEL = "Hungry?"
_HUNGRY_WIDTH = None
_WIPE_HANDLER_REGISTERED = False
_WIPE_RECOVERY_ACTIVE = False
_WIPE_RESUME_STEP = ""
_WIPE_RESUME_SECTION = "farm"
CURRENT_SECTION = "farm"


def _toggle_pycons_ui():
    widget_handler = get_widget_handler()
    if widget_handler.is_widget_enabled("Pycons"):
        widget_handler.disable_widget("Pycons")
    else:
        widget_handler.enable_widget("Pycons")


def _patch_main_start_stop_row_with_hungry():
    global _ORIGINAL_PYIMGUI_BUTTON, _HUNGRY_BUTTON_PATCH_APPLIED, _HUNGRY_WIDTH
    if _HUNGRY_BUTTON_PATCH_APPLIED:
        return

    _ORIGINAL_PYIMGUI_BUTTON = PyImGui.button

    def _button_with_hungry(label, *args, **kwargs):
        global _HUNGRY_WIDTH
        if _ORIGINAL_PYIMGUI_BUTTON is None:
            return False
        clicked = _ORIGINAL_PYIMGUI_BUTTON(label, *args, **kwargs)
        if isinstance(label, str) and "##BotToggle" in label:
            if _HUNGRY_WIDTH is None:
                _HUNGRY_WIDTH = int(PyImGui.calc_text_size(_HUNGRY_LABEL)[0] + 8)
            PyImGui.same_line(max(0, PyImGui.get_content_region_avail()[0] - _HUNGRY_WIDTH + 14), 0)
            hungry_clicked = False
            try:
                hungry_clicked = _ORIGINAL_PYIMGUI_BUTTON(_HUNGRY_LABEL, width=_HUNGRY_WIDTH)
            except TypeError:
                hungry_clicked = _ORIGINAL_PYIMGUI_BUTTON(_HUNGRY_LABEL, _HUNGRY_WIDTH)
            if hungry_clicked:
                _toggle_pycons_ui()
        return clicked

    PyImGui.button = _button_with_hungry
    _HUNGRY_BUTTON_PATCH_APPLIED = True


def _resolve_section_from_step(step_name: str) -> str:
    if isinstance(step_name, str) and "Path_to_Nicholas" in step_name:
        return "nick"
    return "farm"


def _resolve_section_from_fsm(bot: "Botting") -> str:
    fsm = bot.config.FSM
    current_num = fsm.get_current_state_number()
    if current_num <= 0:
        return CURRENT_SECTION
    for num in range(current_num, 0, -1):
        name = fsm.get_state_name_by_number(num)
        if not isinstance(name, str):
            continue
        if name.startswith("[H]Path_to_Nicholas"):
            return "nick"
        if name.startswith(f"[H]{BOT_NAME}_loop"):
            return "farm"
    return CURRENT_SECTION


def _get_section_start_step(bot: "Botting", section: str) -> str:
    fsm = bot.config.FSM
    for name in fsm.get_state_names():
        if section == "nick" and name.startswith("[H]Path_to_Nicholas"):
            return name
        if section == "farm" and name.startswith(f"[H]{BOT_NAME}_loop"):
            return name
    for name in fsm.get_state_names():
        if name.startswith(f"[H]{BOT_NAME}"):
            return name
    return ""


def _cancel_active_movement_coroutine(bot: "Botting") -> None:
    fsm = bot.config.FSM
    state = fsm.current_state
    if state and hasattr(state, "reset"):
        try:
            state.reset()
        except Exception:
            pass

    coro = getattr(state, "coroutine_instance", None) if state else None
    if coro and coro in GLOBAL_CACHE.Coroutines:
        try:
            GLOBAL_CACHE.Coroutines.remove(coro)
        except ValueError:
            pass
    if coro and coro in fsm.managed_coroutines:
        try:
            fsm.managed_coroutines.remove(coro)
        except ValueError:
            pass
    if state is not None:
        setattr(state, "coroutine_instance", None)

    ActionQueueManager().ResetAllQueues()


def _ensure_wipe_handler_registered(bot: "Botting"):
    global _WIPE_HANDLER_REGISTERED
    if _WIPE_HANDLER_REGISTERED:
        return
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    _WIPE_HANDLER_REGISTERED = True


def _on_party_wipe(bot: "Botting"):
    global _WIPE_RECOVERY_ACTIVE, _WIPE_RESUME_STEP, _WIPE_RESUME_SECTION
    while Agent.IsDead(Player.GetAgentID()):
        yield from Routines.Yield.Movement.StopMovement()
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            _WIPE_RECOVERY_ACTIVE = False
            bot.config.FSM.resume()
            return

    fsm = bot.config.FSM
    target_step = ""
    if _WIPE_RESUME_STEP and _WIPE_RESUME_STEP in fsm.get_state_names():
        target_step = _WIPE_RESUME_STEP
    else:
        target_step = _get_section_start_step(bot, _WIPE_RESUME_SECTION)

    if target_step:
        bot.States.JumpToStepName(target_step)

    _WIPE_RECOVERY_ACTIVE = False
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    global _WIPE_RECOVERY_ACTIVE, _WIPE_RESUME_STEP, _WIPE_RESUME_SECTION
    if _WIPE_RECOVERY_ACTIVE:
        return

    _WIPE_RECOVERY_ACTIVE = True
    current_step = bot.config.FSM.get_current_step_name()
    _WIPE_RESUME_SECTION = _resolve_section_from_fsm(bot)
    if isinstance(current_step, str):
        _WIPE_RESUME_STEP = current_step
        if _resolve_section_from_step(current_step) != "farm":
            _WIPE_RESUME_SECTION = _resolve_section_from_step(current_step)
    else:
        _WIPE_RESUME_STEP = ""
        _WIPE_RESUME_SECTION = _resolve_section_from_fsm(bot)

    ConsoleLog("on_party_wipe", "party wipe detected")
    _cancel_active_movement_coroutine(bot)
    fsm = bot.config.FSM
    fsm.pause()
    if not fsm.HasManagedCoroutine("OnWipe_OPD"):
        fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


def main():
    _patch_main_start_stop_row_with_hungry()
    bot.Update()
    texture = get_texture_for_model(model_id=MODEL_ID_TO_FARM)
    bot.UI.draw_window(icon_path=texture, additional_ui=main_window_extra_ui)


if __name__ == "__main__":
    main()
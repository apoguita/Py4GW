from Py4GWCoreLib import Botting, get_texture_for_model, ModelID, ConsoleLog, Routines, Agent, Player, GLOBAL_CACHE, ActionQueueManager
import PyImGui
from Py4GW_widget_manager import get_widget_handler

BOT_NAME = "Icy Lodestone Farm"
MODEL_ID_TO_FARM = ModelID.Icy_Lodestone
OUTPOST_TO_TRAVEL = 134  # Yaks Bend
COORD_TO_EXIT_MAP = (9282.36, 4048.77)
EXPLORABLE_TO_TRAVEL = 99  # Traveler's Vale
                
KILLING_PATH = [
                (8176.64, 322.11),
                (5292.05, -2048.06),
                (1713.91, 2094.72),
                (3288.01, 4010.94),
                (3288.01, 4010.94),
                (4590.16, 6831.71),
                (833.14, 7781.52),
                (-182.18, 7301.85),
                (-1616.67, 10205.06),
                (1459.86, 13205.37),
                (978.68, 15770.64),
                (-1043.96, 14716.10),
                (-2489.21, 17618.11),
                (-5840.15, 16358.50),
                (-5593.31, 16083.44),
                (-5593.31, 16083.44),
                (-3728.91, 11221.24),
                (-2231.55, 7046.51),
                (-2231.55, 7046.51),
                (-990.93, -1110.36),
                (-1652.18, -5846.56),
                (2206.83, -5876.18),
                (4176.39, -7785.22),
                (2892.22, -10951.79),
                (3228.37, -15121.02),
                (275.76, -14130.75),
                (529.57, -16373.52),
                (-2742.92, -16507.49),
                
                ]

NICK_OUTPOST = 22  # Ice Caves of Sorrow
COORDS_TO_EXIT_OUTPOST = (-23084.91, -5431.88)
EXPLORABLE_AREA = 26  # Talus Chute
NICK_KILL_COORDS = [
                (19190.45, -11035.60),
                (17508.89, -8407.31),
                (13927.27, -8001.85),
                (18336.00, -3339.62),
                (18150.36, -1866.10),
                (21320.34, -425.23),
                (22431.41, 5891.08),
                (23231.87, 8149.26),
                (23556.33, 10103.32),
                (22949.44, 13592.58),
                (20590.37, 16337.73),
                (19584.00, 15595.28),
                (19661.91, 14870.83),
                (20637.18, 16265.56),
                (23236.86, 16664.06)
                
                ]
COORDS_TO_EXIT_TO_ICEDOME = (23863.97, 16650.69)
TARGET_MAP_ICEDOME = 87
NICK_COORDS =  [
                (-4600.63, -5978.50),
                (-7671.40, -4043.10),
                (-8343.82, -2056.71),
                (-6968.49, -949.21),
                (-7298.84, 1060.81),
                (-4818.03, 1806.17),
                (-2585.59, 1281.17),
                (-237.46, -902.11),
                (1921.88, -2769.02)
                
                ] #Nicholas the Traveler Location

bot = Botting(BOT_NAME)
BOT_TEXTURE = get_texture_for_model(model_id=MODEL_ID_TO_FARM)

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
    if isinstance(step_name, str) and (
        "Path_to_Nicholas" in step_name
        or "Talus_Chute" in step_name
        or "Nicholas_the_Traveler" in step_name
    ):
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
        state.coroutine_instance = None

    ActionQueueManager().ResetAllQueues()

def _ensure_wipe_handler_registered(bot: "Botting"):
    global _WIPE_HANDLER_REGISTERED
    if _WIPE_HANDLER_REGISTERED:
        return
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    _WIPE_HANDLER_REGISTERED = True
                
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
    bot.States.AddHeader(f"Path_to_Nicholas")
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=NICK_OUTPOST)
    bot.Move.XYAndExitMap(*COORDS_TO_EXIT_OUTPOST, EXPLORABLE_AREA)
    bot.Move.FollowAutoPath(NICK_KILL_COORDS, step_name="Talus_Chute_Kill_Path")
    bot.Move.XYAndExitMap(*COORDS_TO_EXIT_TO_ICEDOME, TARGET_MAP_ICEDOME)
    bot.Move.FollowAutoPath(NICK_COORDS, step_name="Nicholas_the_Traveler_Location")
    bot.Wait.UntilOnOutpost()

bot.SetMainRoutine(bot_routine)

def _on_party_wipe(bot: "Botting"):
    global _WIPE_RECOVERY_ACTIVE, _WIPE_RESUME_STEP, _WIPE_RESUME_SECTION
    while Agent.IsDead(Player.GetAgentID()):
        # Keep movement halted while wiped and FSM is paused.
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
        _WIPE_RESUME_SECTION = _resolve_section_from_step(current_step) if _resolve_section_from_step(current_step) != "farm" else _WIPE_RESUME_SECTION
    else:
        _WIPE_RESUME_STEP = ""
        _WIPE_RESUME_SECTION = _resolve_section_from_fsm(bot)

    ConsoleLog("on_party_wipe", "party wipe detected")
    _cancel_active_movement_coroutine(bot)
    fsm = bot.config.FSM
    fsm.pause()
    if not fsm.HasManagedCoroutine("OnWipe_OPD"):
        fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

def main_window_extra_ui():
    PyImGui.text("Nicholas the Traveler")
    PyImGui.separator()
    PyImGui.text("Travel to Nicholas the Traveler location")
    if PyImGui.button("Start"):
        bot.StartAtStep("[H]Path_to_Nicholas_4")

def main():
    _patch_main_start_stop_row_with_hungry()
    bot.Update()
    bot.UI.draw_window(icon_path=BOT_TEXTURE, additional_ui=main_window_extra_ui)

if __name__ == "__main__":
    main()


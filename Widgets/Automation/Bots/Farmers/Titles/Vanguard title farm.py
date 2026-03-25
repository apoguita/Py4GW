# region Imports & Config
from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, Agent, Player, ConsoleLog, IniManager, ModelID
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
from Py4GWCoreLib.botting_src.property import Property
import Py4GW
import os
import time

BOT_NAME = "Vanguard Title Farm"

MODULE_NAME = BOT_NAME
MODULE_ICON = "Textures/Skill_Icons/[2233] - Ebon Battle Standard of Honor.jpg"

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
DALADA_UPLANDS_OUTPOST_ID = 648
DALADA_UPLANDS_MAP_ID = 647

DALADA_UPLANDS_OUTPOST_PATH = [
    (-16016.0, 17340.0),
    (-15400.0, 13500.0),
]

DALADA_SEGMENT_1_BLESS = (-14971.00, 11013.00)
DALADA_SEGMENT_1_PATH = [
    (-14350.5, 12790.6), (-17600.7, 10388.3), (-16649.0, 6485.4), (-16131.3, 2494.2),
    (-13528.1, -571.5), (-15663.4, -3959.4), (-18089.6, -7150.1), (-17921.5, -11167.4),
    (-15917.0, -14662.3), (-13390.84, -16843.04), (-12191.4, -16190.6), (-8482.2, -14675.8), (-7746.7, -18628.1),
    (-4699.0, -15996.0), (-734.2, -16733.1), (3209.2, -17521.2), (7204.8, -17236.8),
    (10660.3, -15173.9), (14231.2, -13323.1), (15486.11, -14122.26), (17868.1, -11540.7), (14280.7, -9705.3),
    (13958.0, -5657.5), (17851.7, -4510.7), (14141.2, -2985.1), (10104.9, -2608.4),
    (10392.6, 1429.8), (14414.1, 923.4), (16536.4, 4358.9), (17027.8, 8366.5),
    (14253.5, 11258.4), (12708.4, 14995.4), (8842.1, 16056.3), (5366.9, 18114.6),
    (2657.9, 15144.8), (-1025.2, 16731.2), (1142.8, 13355.0), (-2272.1, 11178.6),
    (-6246.7, 12038.8), (-8875.1, 15092.1), (-9545.32, 16453.30), (-10593.52, 14475.55), (-11859.57, 12183.40), (-9680.6, 11168.8), (-7630.3, 7678.4),
    (-3717.2, 8618.1), (-3227.72, 8829.67), (232.2, 9451.7), (4266.0, 9959.4), (8007.6, 8342.5),
    (4888.8, 5766.7), (1037.3, 4668.6), (-2887.1, 3697.4), (-6918.0, 4104.1),
    (-10897.1, 4922.3), (-14702.6, 6233.5), (-10898.6, 4878.2), (-9045.5, 1321.2),
    (-8657.0, -2712.6), (-5189.2, -611.5), (-1172.4, 95.6), (2474.3, 1913.7),
    (6476.9, 2343.3), (5489.0, -1545.9), (5552.4, -5596.4), (7189.7, -9305.8), (8261.67, -12055.48),
    (5228.1, -5784.1), (2164.1, -3177.7), (-1530.8, -4867.3), (156.3, -8499.8),
    (3819.1, -10133.5), (2167.7, -13796.2), (-1821.5, -14135.8), (-5747.9, -13218.7),
]

DALADA_SEGMENT_2_BLESS = (-2641.00, 449.00)
DALADA_SEGMENT_2_PATH = [
    (-1172.4, 95.6), (2474.3, 1913.7), (6476.9, 2343.3), (5489.0, -1545.9),
    (5552.4, -5596.4), (7189.7, -9305.8), (8261.67, -12055.48), (5228.1, -5784.1),
    (2164.1, -3177.7), (-1530.8, -4867.3), (156.3, -8499.8), (3819.1, -10133.5),
    (2167.7, -13796.2), (-1821.5, -14135.8), (-5747.9, -13218.7),
]

DALADA_SEGMENT_3_BLESS = (-3954.00, -11426.00)
DALADA_SEGMENT_3_PATH = [
    (-5747.9, -13218.7), (-9790.9, -13258.0), (-11047.5, -9448.2), (-7777.1, -7032.2),
    (-4638.2, -4496.5), (-1131.0, -2524.7), (1852.3, 163.3), (5104.8, 2594.2),
    (8307.3, 5060.4), (7509.3, 8998.1), (10537.1, 11668.0), (8091.5, 8492.2),
    (11725.8, 6705.3), (7964.3, 8157.4), (4666.3, 10422.2),
]

DALADA_SEGMENT_4_BLESS = (5884.00, 11749.00)
DALADA_SEGMENT_4_PATH = [
    (4666.3, 10422.2),
    (1772.7, 13212.8),
]

bot = Botting(
    BOT_NAME,
    upkeep_armor_of_salvation_restock=2,
    upkeep_essence_of_celerity_restock=2,
    upkeep_grail_of_might_restock=2,
    upkeep_war_supplies_restock=2,
    upkeep_birthday_cupcake_restock=2,
    upkeep_honeycomb_restock=20,
    upkeep_auto_loot_active=True
)

bot.config.config_properties.use_conset = Property(bot.config, "use_conset", active=False)
bot.config.config_properties.use_pcons = Property(bot.config, "use_pcons", active=False)
bot.config.config_properties.use_custom_behaviors = Property(bot.config, "use_custom_behaviors", active=True)

_SETTINGS_SECTION = "TitleBotSettings"
_BEHAVIOR_MODE_KEY = "use_custom_behaviors"
_USE_CONSET_KEY = "use_conset"
_USE_PCONS_KEY = "use_pcons"

# (model_id, effect_skill_name) — single source of truth for consumable use & restock
CONSET_ITEMS: list[tuple[int, str]] = [
    (ModelID.Essence_Of_Celerity.value, "Essence_of_Celerity_item_effect"),
    (ModelID.Grail_Of_Might.value,      "Grail_of_Might_item_effect"),
    (ModelID.Armor_Of_Salvation.value,  "Armor_of_Salvation_item_effect"),
]

PCON_ITEMS: list[tuple[int, str]] = [
    (ModelID.Birthday_Cupcake.value,      "Birthday_Cupcake_skill"),
    (ModelID.Golden_Egg.value,            "Golden_Egg_skill"),
    (ModelID.Candy_Corn.value,            "Candy_Corn_skill"),
    (ModelID.Candy_Apple.value,           "Candy_Apple_skill"),
    (ModelID.Slice_Of_Pumpkin_Pie.value,  "Pie_Induced_Ecstasy"),
    (ModelID.Drake_Kabob.value,           "Drake_Skin"),
    (ModelID.Bowl_Of_Skalefin_Soup.value, "Skale_Vigor"),
    (ModelID.Pahnai_Salad.value,          "Pahnai_Salad_item_effect"),
    (ModelID.War_Supplies.value,          "Well_Supplied"),
]

CONSET_RESTOCK_MODELS = [m for m, _ in CONSET_ITEMS]
PCON_RESTOCK_MODELS   = [m for m, _ in PCON_ITEMS] + [
    ModelID.Honeycomb.value,
    ModelID.Scroll_Of_Resurrection.value,
]
# endregion


# region Bot Routine
def Routine(bot: Botting) -> None:
    PrepareForCombat(bot)
    Fight(bot)


def PrepareForCombat(bot: Botting) -> None:
    bot.States.AddHeader("Enable Combat Mode")
    _load_behavior_setting(bot)
    _load_consumable_settings(bot)
    bot.Templates.Multibox_Aggressive()
    _apply_behavior_mode(bot)
    _sync_consumable_toggles(bot)
    bot.Multibox.LeavePartyOnAllAccounts()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=DALADA_UPLANDS_OUTPOST_ID)
    bot.States.AddCustomState(lambda: _restock_consumables_if_enabled(bot), "Restock Consumables If Enabled")
    bot.Party.SetHardMode(True)


def _do_bless_and_path(bot: Botting, bless_xy: tuple[float, float], path: list[tuple[float, float]], label: str) -> None:
    bot.Move.XY(bless_xy[0], bless_xy[1], label)
    bot.Wait.ForTime(1500)
    bot.Move.XYAndInteractNPC(bless_xy[0], bless_xy[1])
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Multibox.SendDialogToTarget(0x85)
    bot.Move.FollowAutoPath(path)


def Fight(bot: Botting) -> None:
    # events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    # end events

    bot.States.AddHeader("Start Combat")
    bot.Move.FollowPathAndExitMap(DALADA_UPLANDS_OUTPOST_PATH, target_map_id=DALADA_UPLANDS_MAP_ID)
    bot.Wait.ForMapLoad(target_map_id=DALADA_UPLANDS_MAP_ID)
    bot.Wait.ForTime(4000)
    bot.States.AddCustomState(lambda: PrepareForBattle(bot), "Use Consumables If Enabled")
    bot.States.AddManagedCoroutine("Anti-Stuck Watchdog", lambda: _anti_stuck_watchdog(bot))

    # Path segment 1
    _do_bless_and_path(bot, DALADA_SEGMENT_1_BLESS, DALADA_SEGMENT_1_PATH, "Taking Blessing")

    # Path segment 2
    _do_bless_and_path(bot, DALADA_SEGMENT_2_BLESS, DALADA_SEGMENT_2_PATH, "Taking Blessing")

    # Path segment 3
    _do_bless_and_path(bot, DALADA_SEGMENT_3_BLESS, DALADA_SEGMENT_3_PATH, "Taking Blessing")

    # Path segment 4
    _do_bless_and_path(bot, DALADA_SEGMENT_4_BLESS, DALADA_SEGMENT_4_PATH, "Taking Blessing")

    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.Wait.ForTime(5000)
    bot.States.JumpToStepName("[H]Enable Combat Mode_1")


def PrepareForBattle(bot: Botting):
    _sync_consumable_toggles(bot)
    yield from _use_consumables_if_enabled(bot)


bot.UI.override_draw_config(lambda: _draw_settings(bot))

bot.SetMainRoutine(Routine)
# endregion


# region Consumables
def _restock_consumables_if_enabled(bot: Botting):
    _sync_consumable_toggles(bot)
    if _as_bool(bot.Properties.Get("use_conset", "active")):
        yield from _restock_models_locally(CONSET_RESTOCK_MODELS, 250)
        yield from bot.helpers.Multibox._restock_conset_message(250)
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        yield from _restock_models_locally(PCON_RESTOCK_MODELS, 250)
        yield from bot.helpers.Multibox._restock_all_pcons_message(250)


def _use_consumables_if_enabled(bot: Botting):
    _sync_consumable_toggles(bot)
    if _as_bool(bot.Properties.Get("use_conset", "active")):
        for model_id, skill_name in CONSET_ITEMS:
            yield from bot.helpers.Multibox._use_consumable_message(
                (model_id, GLOBAL_CACHE.Skill.GetID(skill_name), 0, 0))
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        for model_id, skill_name in PCON_ITEMS:
            yield from bot.helpers.Multibox._use_consumable_message(
                (model_id, GLOBAL_CACHE.Skill.GetID(skill_name), 0, 0))


def _restock_models_locally(model_ids: list[int], quantity: int):
    for model_id in model_ids:
        yield from Routines.Yield.Items.RestockItems(model_id, quantity)
# endregion


# region Anti-Stuck
EXPLORABLE_TIMEOUT_SECONDS = 3 * 3600  # 3 hours


def _anti_stuck_resign(bot: "Botting"):
    """Called when the timeout fires: resign, wait for outpost, then restart."""
    yield from bot.helpers.Multibox._resignParty()
    while True:
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            continue
        if Routines.Checks.Map.IsOutpost():
            break
    bot.States.JumpToStepName("[H]Enable Combat Mode_1")
    bot.config.FSM.resume()
    yield


def _anti_stuck_watchdog(bot: "Botting"):
    """Resign the party if stuck in explorable for more than 3 hours."""
    explorable_entry_time = None
    while True:
        yield from bot.Wait._coro_for_time(60000)  # check every minute
        if not Routines.Checks.Map.MapValid():
            explorable_entry_time = None
            continue
        if Routines.Checks.Map.IsOutpost():
            explorable_entry_time = None
            continue
        # We are in explorable
        if explorable_entry_time is None:
            explorable_entry_time = time.time()
            continue
        elapsed = time.time() - explorable_entry_time
        if elapsed >= EXPLORABLE_TIMEOUT_SECONDS:
            ConsoleLog(BOT_NAME, f"Anti-stuck: {elapsed/3600:.1f}h in explorable - resigning party.", Py4GW.Console.MessageType.Warning)
            explorable_entry_time = None
            bot.config.FSM.pause()
            bot.config.FSM.AddManagedCoroutine("AntiStuck_Resign", lambda: _anti_stuck_resign(bot))
# endregion


# region Events
def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid -> release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map -> jump to recovery step
    bot.States.JumpToStepName("[H]Start Combat_2")
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))
# endregion


# region Settings
def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _ensure_bot_ini(bot: Botting) -> str:
    if not bot.config.ini_key_initialized:
        bot.config.ini_key = IniManager().ensure_key(
            f"BottingClass/bot_{bot.config.bot_name}",
            f"bot_{bot.config.bot_name}.ini",
        )
        bot.config.ini_key_initialized = True
    return bot.config.ini_key


def _load_behavior_setting(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    saved_value = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _BEHAVIOR_MODE_KEY,
        _as_bool(bot.Properties.Get("use_custom_behaviors", "active")),
    )
    bot.Properties.ApplyNow("use_custom_behaviors", "active", _as_bool(saved_value))


def _save_behavior_setting(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _BEHAVIOR_MODE_KEY,
        _as_bool(bot.Properties.Get("use_custom_behaviors", "active")),
    )


def _load_consumable_settings(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    saved_use_conset = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _USE_CONSET_KEY,
        _as_bool(bot.Properties.Get("use_conset", "active")),
    )
    saved_use_pcons = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _USE_PCONS_KEY,
        _as_bool(bot.Properties.Get("use_pcons", "active")),
    )
    bot.Properties.ApplyNow("use_conset", "active", _as_bool(saved_use_conset))
    bot.Properties.ApplyNow("use_pcons", "active", _as_bool(saved_use_pcons))


def _save_consumable_settings(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _USE_CONSET_KEY,
        _as_bool(bot.Properties.Get("use_conset", "active")),
    )
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _USE_PCONS_KEY,
        _as_bool(bot.Properties.Get("use_pcons", "active")),
    )


def _sync_consumable_toggles(bot: Botting) -> None:
    use_conset = _as_bool(bot.Properties.Get("use_conset", "active"))
    use_pcons = _as_bool(bot.Properties.Get("use_pcons", "active"))

    for key in ("armor_of_salvation", "essence_of_celerity", "grail_of_might"):
        bot.Properties.ApplyNow(key, "active", use_conset)

    for key in (
        "birthday_cupcake",
        "golden_egg",
        "candy_corn",
        "candy_apple",
        "slice_of_pumpkin_pie",
        "drake_kabob",
        "bowl_of_skalefin_soup",
        "pahnai_salad",
        "war_supplies",
        "honeycomb",
    ):
        bot.Properties.ApplyNow(key, "active", use_pcons)


def _apply_behavior_mode(bot: Botting) -> None:
    use_custom_behaviors = _as_bool(bot.Properties.Get("use_custom_behaviors", "active"))
    from Py4GW_widget_manager import get_widget_handler
    widget_handler = get_widget_handler()
    custom_behavior_party = None
    try:
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
        custom_behavior_party = CustomBehaviorParty()
    except Exception:
        custom_behavior_party = None
    if use_custom_behaviors:
        bot.Properties.Disable("hero_ai")
        if custom_behavior_party is not None:
            custom_behavior_party.set_party_is_enabled(True)
        if not widget_handler.is_widget_enabled("CustomBehaviors"):
            widget_handler.enable_widget("CustomBehaviors")
        if widget_handler.is_widget_enabled("HeroAI"):
            widget_handler.disable_widget("HeroAI")
        bot.Multibox.ApplyWidgetPolicy(enable_widgets=('CustomBehaviors',), disable_widgets=('HeroAI',), apply_local=False)
    else:
        bot.Properties.Enable("hero_ai")
        if custom_behavior_party is not None:
            custom_behavior_party.set_party_is_enabled(False)
        if widget_handler.is_widget_enabled("CustomBehaviors"):
            widget_handler.disable_widget("CustomBehaviors")
        if not widget_handler.is_widget_enabled("HeroAI"):
            widget_handler.enable_widget("HeroAI")
        bot.Multibox.ApplyWidgetPolicy(enable_widgets=('HeroAI',), disable_widgets=('CustomBehaviors',), apply_local=False)
# endregion


# region GUI
def _draw_settings(bot: Botting):
    import PyImGui

    PyImGui.text("Bot Settings")

    _load_behavior_setting(bot)
    use_custom_behaviors = _as_bool(bot.Properties.Get("use_custom_behaviors", "active"))
    use_hero_ai = not use_custom_behaviors
    new_use_hero_ai          = PyImGui.checkbox("Use Hero AI",          use_hero_ai)
    new_use_custom_behaviors = PyImGui.checkbox("Use Custom Behaviors", use_custom_behaviors)
    if new_use_hero_ai != use_hero_ai:
        desired = not new_use_hero_ai
    elif new_use_custom_behaviors != use_custom_behaviors:
        desired = new_use_custom_behaviors
    else:
        desired = use_custom_behaviors
    if desired != use_custom_behaviors:
        bot.Properties.ApplyNow("use_custom_behaviors", "active", desired)
        _save_behavior_setting(bot)
        _apply_behavior_mode(bot)

    # Conset controls
    use_conset = _as_bool(bot.Properties.Get("use_conset", "active"))
    use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    bot.Properties.ApplyNow("use_conset", "active", use_conset)

    # Pcons controls
    use_pcons = _as_bool(bot.Properties.Get("use_pcons", "active"))
    use_pcons = PyImGui.checkbox("Restock & use Pcons", use_pcons)
    bot.Properties.ApplyNow("use_pcons", "active", use_pcons)
    _save_consumable_settings(bot)
    _sync_consumable_toggles(bot)


def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color

    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Vanguard Title Farm", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("Farm Vanguard title in Dalada Uplands")
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by AH")
    PyImGui.bullet_text("With help from Wick Divinus")
    PyImGui.end_tooltip()


_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}


def _draw_title_track():
    global _session_baselines, _session_start_times
    import PyImGui

    title_idx = int(TitleID.Ebon_Vanguard)
    tiers = TITLE_TIERS.get(TitleID.Ebon_Vanguard, [])
    now = time.time()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        name = account.AgentData.CharacterName
        pts = account.TitlesData.Titles[title_idx].CurrentPoints
        if name not in _session_baselines:
            _session_baselines[name] = pts
            _session_start_times[name] = now
        tier_name = "Unranked"
        tier_rank = 0
        prev_required = 0
        next_required = tiers[0].required if tiers else 0
        for i, tier in enumerate(tiers):
            if pts >= tier.required:
                tier_name = tier.name
                tier_rank = i + 1
                prev_required = tier.required
                next_required = tiers[i + 1].required if i + 1 < len(tiers) else tier.required
            else:
                next_required = tier.required
                break
        is_maxed = tiers and pts >= tiers[-1].required
        PyImGui.separator()
        PyImGui.text(f"{name}  [{tier_name} (Rank {tier_rank})]")
        if is_maxed:
            PyImGui.text_colored("Maximum rank achieved. Title complete.", (0.4, 1.0, 0.4, 1.0))
            continue
        gained = pts - _session_baselines[name]
        elapsed = now - _session_start_times[name]
        pts_hr = int(gained / elapsed * 3600) if elapsed > 0 else 0
        PyImGui.text(f"Points: {pts:,} / {next_required:,}")
        if next_required > prev_required:
            frac = min((pts - prev_required) / (next_required - prev_required), 1.0)
            PyImGui.progress_bar(frac, -1, 0, f"{pts - prev_required:,} / {next_required - prev_required:,}")
        PyImGui.text(f"+{gained:,}  ({pts_hr:,}/hr)")


REFORGED_TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Skill_Icons", "[2233] - Ebon Battle Standard of Honor.jpg")
# endregion


# region Entry Point
def main():
    bot.Update()
    bot.UI.draw_window(icon_path=REFORGED_TEXTURE, extra_tabs=[("Statistics", _draw_title_track)])


if __name__ == "__main__":
    main()
# endregion

# region Imports & Config
from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Agent, Player, ConsoleLog, IniManager
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
from Py4GWCoreLib.botting_src.property import Property
import Py4GW
import os
import time

BOT_NAME = "Norn title farm by Wick Divinus"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")

MODULE_NAME = "Norn Title Farm"
MODULE_ICON = "Textures/Skill_Icons/[2373] - Heart of the Norn.jpg"

OLAFSTEAD = 645
VARAJAR_FELLS = 553

Norn_Path: list[tuple[float, float]] = [
    (-2484.73, 118.55),
    (-3059.12, -419.00),
    (-3301.01, -2008.23),
    (-2034, -4512),
    (-5278, -5771),
    (-5456, -7921),
    (-8793, -5837),
    (-14092, -9662),
    (-17260, -7906),
    (-21964, -12877),
    (-22275, -12462),
    (-21671, -2163),
    (-19592, 772),
    (-13795, -751),
    (-17012, -5376),
    (-12071, -4274),
    (-8351, -2633),
    (-4362, -1610),
    (-4316, 4033),
    (-8809, 5639),
    (-14916, 2475),
    (-11282, 5466),
    (-16051, 6492),
    (-16934, 11145),
    (-19378, 14555),
    (-22751, 14163),
    (-15932, 9386),
    (-13777, 8097),
    (-4729, 15385),
    (-2290, 14879),
    (-1810, 4679),
    (-6911, 5240),
    (-15471, 6384),
    (-411, 5874),
    (2859, 3982),
    (4909, -4259),
    (7514, -6587),
    (3800, -6182),
    (7755, -11467),
    (15403, -4243),
    (21597, -6798),
    (24522, -6532),
    (22883, -4248),
    (18606, -1894),
    (14969, -4048),
    (13599, -7339),
    (10056, -4967),
    (10147, -1630),
    (8963, 4043),
    (9339.46, 3859.12),
    (15576, 7156),
    (22838, 7914),
    (22961, 12757),
    (18067, 8766),
    (13311, 11917),
    (13714, 14520),
    (11126, 10443),
    (5575, 4696),
    (-503, 9182),
    (1582, 15275),
    (7857, 10409)
]

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True)

bot.config.config_properties.use_conset = Property(bot.config, "use_conset", active=False)
bot.config.config_properties.use_pcons = Property(bot.config, "use_pcons", active=False)
bot.config.config_properties.use_custom_behaviors = Property(bot.config, "use_custom_behaviors", active=True)

_SETTINGS_SECTION = "TitleBotSettings"
_BEHAVIOR_MODE_KEY = "use_custom_behaviors"

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
def bot_routine(bot: Botting) -> None:
    global Norn_Path
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events

    bot.States.AddHeader(BOT_NAME)
    _load_behavior_setting(bot)
    bot.Templates.Multibox_Aggressive()
    _apply_behavior_mode(bot)
    _sync_consumable_toggles(bot)
    bot.Multibox.LeavePartyOnAllAccounts()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OLAFSTEAD)
    bot.States.AddCustomState(lambda: _restock_consumables_if_enabled(bot), "Restock Consumables If Enabled")

    bot.Party.SetHardMode(True)
    auto_path_list = [(-328.0, 1240.0), (-1500.0, 1250.0)]
    bot.Move.FollowPath(auto_path_list)
    bot.Wait.ForMapLoad(target_map_id=553)
    bot.States.AddHeader("Start Combat")
    bot.States.AddCustomState(lambda: _use_consumables_if_enabled(bot), "Use Consumables If Enabled")
    bot.States.AddManagedCoroutine("Upkeep Multibox Consumables", lambda: _upkeep_multibox_consumables(bot))
    bot.States.AddManagedCoroutine("Anti-Stuck Watchdog", lambda: _anti_stuck_watchdog(bot))

    # Initial path to first blessing
    bot.Move.XY(-2484.73, 118.55, "Start")
    bot.Move.XY(-3059.12, -419.00, "Move to bridge")
    bot.Move.XY(-3301.01, -2008.23, "Move to shrine")
    bot.Move.XY(-2034, -4512, "Move to blessing 1")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-1892.00, -4505.00)
    bot.Multibox.SendDialogToTarget(0x84) #Get Blessing 1
    bot.Wait.ForTime(5000)

    # Path to blessing 2
    bot.Move.XY(-5278, -5771, "Aggro: Berzerker")
    bot.Move.XY(-5456, -7921, "Aggro: Berzerker")
    bot.Move.XY(-8793, -5837, "Aggro: Berzerker")
    bot.Move.XY(-14092, -9662, "Aggro: Vaettir and Berzerker")
    bot.Move.XY(-17260, -7906, "Aggro: Vaettir and Berzerker")
    bot.Move.XY(-21964, -12877, "Aggro: Jotun")
    bot.Move.XY(-25341.00, -11957.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-25341.00, -11957.00)
    bot.Multibox.SendDialogToTarget(0x84) # Edda Blessing 2
    bot.Wait.ForTime(10000)

    # Path to blessing 3
    bot.Move.XY(-22275, -12462, "Move to area 2")
    bot.Move.XY(-21671, -2163, "Aggro: Berzerker")
    bot.Move.XY(-19592, 772, "Aggro: Berzerker")
    bot.Move.XY(-13795, -751, "Aggro: Berzerker")
    bot.Move.XY(-17012, -5376, "Aggro: Berzerker")
    bot.Move.XY(-10606.23, -1625.26)
    bot.Move.XY(-12158.00, -4277.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-12158.00, -4277.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 3
    bot.Wait.ForTime(10000)

    # Path to blessing 4
    bot.Move.XY(-12071, -4274, "Aggro: Berzerker")
    bot.Move.XY(-8351, -2633, "Move to regroup")
    bot.Move.XY(-4362, -1610, "Aggro: Lake")
    bot.Move.XY(-4316, 4033, "Aggro: Lake")
    bot.Move.XY(-8809, 5639, "Aggro: Lake")
    bot.Move.XY(-14916, 2475)
    bot.Move.XY(-11204.00, 5479.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-11204.00, 5479.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 4
    bot.Wait.ForTime(10000)

    # Path to blessing 5
    bot.Move.XY(-11282, 5466, "Aggro: Elemental")
    bot.Move.XY(-16051, 6492, "Aggro: Elemental")
    bot.Move.XY(-16934, 11145, "Aggro: Elemental")
    bot.Move.XY(-19378, 14555)
    bot.Move.XY(-22889.00, 14165.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-22889.00, 14165.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 5
    bot.Wait.ForTime(10000)

    # Path to blessing 6
    bot.Move.XY(-22751, 14163, "Aggro: Elemental")
    bot.Move.XY(-15932, 9386, "Move to camp")
    bot.Move.XY(-13777, 8097, "Aggro: Lake")
    bot.Move.XY(-2217.00, 14914.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-2217.00, 14914.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 6
    bot.Wait.ForTime(10000)

    # The Path to Revelations (The quest is required beforehand, otherwise the enemies will not spawn)
    bot.Move.XY(19416.26, 1142.77)
    bot.Move.XY(24169.45, -4288.69)
    bot.Move.XY(24169.45, -4288.69)
    bot.Move.XY(19745, -2718)
    bot.Move.XY(23504, 1801) # First boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(23504, 1801) # Second boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(23504, 1801) # Third boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(23504, 1801) # Fourth boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(23504, 1801) # Fifth boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()
    #bot.Move.XY(23504, 1801) # Sixth boss
    #bot.Wait.ForTime(10000)
    #bot.Wait.UntilOutOfCombat()

    # Continue route
    # bot.Move.XY(-2290, 14879, "Aggro: Modnir")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-1810, 4679, "Move to boss")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-6911, 5240, "Aggro: Boss")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-15471, 6384, "Move to regroup")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-411, 5874, "Aggro: Modniir")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(2859, 3982, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(4909, -4259, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(7514, -6587, "Aggro: Berserker")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(3800, -6182, "Aggro: Berserker")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(7755, -11467, "Aggro: Elementals and Griffins")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(15403, -4243, "Aggro: Elementals and Griffins")
    # bot.Wait.UntilOutOfCombat()

    # # Path to blessing 7
    # bot.Move.XY(21597, -6798)
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-2217.00, 14914.00)
    # bot.Wait.ForTime(5000)
    # bot.Move.XYAndInteractNPC(-2217.00, 14914.00)
    # bot.Multibox.SendDialogToTarget(0x84) #Blessing 7
    # bot.Wait.ForTime(10000)

    # bot.Move.XY(24522, -6532, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(22883, -4248, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(18606, -1894, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(14969, -4048, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(13599, -7339, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(10056, -4967, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(10147, -1630, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()

    # # Path to blessing 8
    # bot.Move.XY(8963, 4043, "Take blessing 8")
    # bot.Wait.ForTime(5000)
    # bot.Move.XYAndInteractNPC(8963, 4043)
    # bot.Multibox.SendDialogToTarget(0x84) #Blessing 8
    # bot.Wait.ForTime(10000)

    # bot.Move.XY(9339.46, 3859.12, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(15576, 7156, "Aggro: Berserker")
    # bot.Wait.UntilOutOfCombat()

    # # Path to blessing 9
    # bot.Move.XY(22838, 7914, "Take blessing 9")
    # bot.Wait.ForTime(5000)
    # bot.Move.XYAndInteractNPC(22838, 7914)
    # bot.Multibox.SendDialogToTarget(0x84) #Blessing 9
    # bot.Wait.ForTime(10000)

    # # Final route section
    # bot.Move.XY(22961, 12757, "Move to shrine")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(18067, 8766, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(13311, 11917, "Aggro: Area")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(13714, 14520, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(11126, 10443, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(5575, 4696, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-503, 9182, "Aggro: Modniir and Elemental 2")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(1582, 15275, "Aggro: Modniir and Elemental 2")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(7857, 10409, "Aggro: Modniir and Elemental 2")
    # bot.Wait.UntilOutOfCombat()

    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()

    bot.Wait.ForTime(5000)
    bot.States.JumpToStepName("[H]Norn title farm by Wick Divinus_1")


bot.UI.override_draw_config(lambda: _draw_settings(bot))

bot.SetMainRoutine(bot_routine)
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


# region Upkeep & Anti-Stuck
def _upkeep_multibox_consumables(bot: "Botting"):
    while True:
        yield from bot.Wait._coro_for_time(15000)
        if not Routines.Checks.Map.MapValid() or Routines.Checks.Map.IsOutpost():
            continue
        if bot.Properties.Get("use_conset", "active"):
            for model_id, skill_name in CONSET_ITEMS:
                yield from bot.helpers.Multibox._use_consumable_message(
                    (model_id, GLOBAL_CACHE.Skill.GetID(skill_name), 0, 0))
        if bot.Properties.Get("use_pcons", "active"):
            for model_id, skill_name in PCON_ITEMS:
                yield from bot.helpers.Multibox._use_consumable_message(
                    (model_id, GLOBAL_CACHE.Skill.GetID(skill_name), 0, 0))
            for _ in range(4):
                GLOBAL_CACHE.Inventory.UseItem(ModelID.Honeycomb.value)
                yield from bot.Wait._coro_for_time(250)


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
    bot.States.JumpToStepName("[H]Norn title farm by Wick Divinus_1")
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
            ConsoleLog(BOT_NAME, f"Anti-stuck: {elapsed/3600:.1f}h in explorable — resigning party.", Py4GW.Console.MessageType.Warning)
            explorable_entry_time = None
            bot.config.FSM.pause()
            bot.config.FSM.AddManagedCoroutine("AntiStuck_Resign", lambda: _anti_stuck_resign(bot))
# endregion


# region Events
def _nearest_path_index(path: list, x: float, y: float) -> int:
    best, best_dist = 0, float('inf')
    for i, (px, py) in enumerate(path):
        d = (px - x) ** 2 + (py - y) ** 2
        if d < best_dist:
            best_dist, best = d, i
    return best


def _all_accounts_alive() -> bool:
    current_map = Map.GetMapID()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if account.AgentData.Map.MapID != current_map:
            continue  # skip accounts not in the same explorable (other maps, outpost, etc.)
        if account.AgentData.Health.Current <= 0:
            return False
    return True


def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()) or not _all_accounts_alive():
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return

    # All accounts revived — resume route from nearest path point
    pos = Player.GetXY()
    if pos:
        nearest_idx = _nearest_path_index(Norn_Path, pos[0], pos[1])
        for (wx, wy) in Norn_Path[nearest_idx:]:
            if not Routines.Checks.Map.MapValid():
                break
            yield from bot.Move._coro_xy(wx, wy)

    bot.States.JumpToStepName("[H]Start Combat_3")
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

    use_conset = _as_bool(bot.Properties.Get("use_conset", "active"))
    use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    bot.Properties.ApplyNow("use_conset", "active", use_conset)

    use_pcons = _as_bool(bot.Properties.Get("use_pcons", "active"))
    use_pcons = PyImGui.checkbox("Restock & use Pcons", use_pcons)
    bot.Properties.ApplyNow("use_pcons", "active", use_pcons)
    _sync_consumable_toggles(bot)


def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Norn Title Farm", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi Account, farm Norn title in Varajar Fells")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Wick Divinus")
    PyImGui.end_tooltip()


_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}


def _draw_title_track():
    global _session_baselines, _session_start_times
    import PyImGui
    title_idx = int(TitleID.Norn)
    tiers = TITLE_TIERS.get(TitleID.Norn, [])
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


REFORGED_TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "Wick Divinus bots", "Reforged_Icon.png")
# endregion


# region Entry Point
def main():
    bot.Update()
    bot.UI.draw_window(icon_path=REFORGED_TEXTURE, extra_tabs=[("Statistics", _draw_title_track)])


if __name__ == "__main__":
    main()
# endregion

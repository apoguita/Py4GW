# region Imports & Config
from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Agent, Player, ConsoleLog, IniManager
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
from Py4GWCoreLib.botting_src.property import Property
import Py4GW
import os
import time

MODULE_NAME = "Deldrimor Title Farm"
MODULE_ICON = "Textures/Skill_Icons/[2424] - Stout-Hearted.jpg"

bot = Botting("Deldrimor title farm by Wick Divinus",
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
def Routine(bot: Botting) -> None:
    PrepareForCombat(bot)
    Snowman(bot)


def PrepareForCombat(bot: Botting) -> None:
    bot.States.AddHeader("Enable Combat Mode")
    _load_behavior_setting(bot)
    bot.Templates.Multibox_Aggressive()
    _apply_behavior_mode(bot)
    _sync_consumable_toggles(bot)
    bot.Multibox.LeavePartyOnAllAccounts()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=639)
    bot.States.AddCustomState(lambda: _restock_consumables_if_enabled(bot), "Restock Consumables If Enabled")
    bot.Party.SetHardMode(True)


def Snowman(bot: Botting):
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    bot.States.AddHeader("Start Combat")
    bot.Move.XYAndDialog(-23884, 13954, 0x84)
    bot.Wait.ForMapToChange(target_map_id=701)
    bot.States.AddCustomState(lambda: _use_consumables_if_enabled(bot), "Use Consumables If Enabled")
    bot.States.AddManagedCoroutine("Upkeep Multibox Consumables", lambda: _upkeep_multibox_consumables(bot))
    bot.Move.XYAndInteractNPC(-14078.00, 15449.00)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Move.XY(-14804, 10703)
    bot.Move.XY(-15628, 9589)
    bot.Move.XY(-17602, 6858)
    bot.Wait.ForTime(1000)
    bot.Move.XY(-19769, 5046)
    bot.Move.XY(-16697.96, 1302.89)
    # bot.Move.XY(-14673.79, 2621.35) # Default
    bot.Move.XY(-15090.34, 2057.10) # Updated to avoid agroing both corridor and bridge groups
    bot.Move.XYAndInteractNPC(-12482.00, 3924.00)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Move.XY(-13824.00, 924.00)
    bot.Move.XY(-13752.06, -504.66)
    bot.Move.XY(-12084.77, -1592.58)
    bot.Move.XY(-12745.70, -3899.97)
    bot.Move.XY(-13262.00, -7346.00)
    bot.Move.XY(-14891.95, -10069.69)
    bot.Move.XY(-9573.00, -10963.00)
    bot.Move.FollowPath([(-9703.92, -10948.97)])
    bot.Wait.UntilOutOfCombat()
    bot.Items.LootItems()
    bot.Move.XYAndInteractNPC(-16093.00, -10723.00)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Move.XY(-15756.00, -12335.00)
    bot.Interact.WithGadgetAtXY(-15435.00, -12277.00) #lock
    bot.Wait.ForTime(3000)
    bot.Move.XY(-17542.00, -14048.00)
    bot.Move.XY(-13088.00, -17749.00)
    bot.Move.XY(-13004.20, -17304.91)
    bot.Wait.UntilOutOfCombat()
    bot.Items.LootItems()
    bot.Move.XY(-11136.00, -18043.00)
    bot.Interact.WithGadgetAtXY(-11136.00, -18043.00) #boss lock
    bot.Wait.ForTime(3000)
    bot.Move.XY(-7422.59, -18622.13)
    bot.Wait.ForTime(60000)
    bot.Interact.WithGadgetAtXY(-7594.00, -18657.00)
    bot.Items.LootItems()
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=639)
    bot.States.JumpToStepName("[H]Enable Combat Mode_1")


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


# region Upkeep
def _upkeep_multibox_consumables(bot: "Botting"):
    while True:
        yield from bot.Wait._coro_for_time(15000)
        if not Routines.Checks.Map.MapValid() or Routines.Checks.Map.IsOutpost():
            continue
        if _as_bool(bot.Properties.Get("use_conset", "active")):
            for model_id, skill_name in CONSET_ITEMS:
                yield from bot.helpers.Multibox._use_consumable_message(
                    (model_id, GLOBAL_CACHE.Skill.GetID(skill_name), 0, 0))
        if _as_bool(bot.Properties.Get("use_pcons", "active")):
            for model_id, skill_name in PCON_ITEMS:
                yield from bot.helpers.Multibox._use_consumable_message(
                    (model_id, GLOBAL_CACHE.Skill.GetID(skill_name), 0, 0))
            for _ in range(4):
                GLOBAL_CACHE.Inventory.UseItem(ModelID.Honeycomb.value)
                yield from bot.Wait._coro_for_time(250)
# endregion


# region Events
def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
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
    PyImGui.text_colored("Deldrimor Title Farm", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi Account, farm Deldrimor title in Slavers' Exile")
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
    title_idx = int(TitleID.Deldrimor)
    tiers = TITLE_TIERS.get(TitleID.Deldrimor, [])
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

from Py4GWCoreLib import Agent, Botting, ConsoleLog, GLOBAL_CACHE, Map, ModelID, Player, Routines, SharedCommandType
import Py4GW
import PyImGui
import os

BOT_NAME = "VQ Drazach Thicket"
MODULE_NAME = "Drazach Thicket (Vanquish)"
MODULE_ICON = "Textures\\Module_Icons\\Vanquish - Drazach Thicket.png"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "ApoSource", "textures", "VQ_Helmet.png")
OUTPOST_TO_START = 222
EXPLORABLE_TO_VANQUISH = 195
HOUSE_ZU_HELZER = 77
COORDS_TO_EXIT_OUTPOST = (-7544.00, 14343.00)
COORDS_FOR_PRIEST = (-5592.00, -16263.00)
DIALOG_FOR_PRIEST = 0x86

RETURN_TO_OUTPOST_HEADER = "[H]Return to Outpost_4"

restart_after_run = True
donate_after_run = True
watch_vanquish_completion = True

Vanquish_Path: list[tuple[float, float]] = [
    (-9878.31, -14870.55),
    (-6024.71, -10824.51),
    (-4546.84, -9157.54),
    (-6683.80, -8867.51),
    (-7756.96, -9672.30),
    (-5651.87, -6857.37),
    (-6603.41, -5635.55),
    (-11036.84, -8096.66),
    (-12024.07, -8840.55),
    (-10875.07, -5594.80),
    (-10516.25, -2471.60),
    (-9792.65, -536.86),
    (-11308.45, 3273.95),
    (-12730.60, 5712.96),
    (-7237.03, -2142.75),
    (-7105.36, -2426.90),
    (-4554.99, 776.04),
    (-1223.03, 2129.13),
    (-1896.83, 5606.69),
    (-1813.93, -2020.71),
    (-5234.42, -5652.45),
    (211.23, -5091.44),
    (1371.50, -4038.61),
    (3255.87, -4785.59),
    (1558.04, -6938.50),
    (668.36, -9314.83),
    (2366.87, -9547.91),
    (5625.59, -1360.20),
    (4755.49, 821.61),
    (7347.70, 311.06),
    (9152.04, 4514.65),
    (13031.58, 7149.48),
    (9152.04, 4514.65),
    (7016.99, 6483.00),
    (3104.65, 10852.02),
    (8982.88, 10737.52),
    (7201.44, 13909.25),
    (7109.79, 12134.53),
    (3154.82, 11441.71),
    (1574.23, 15445.42),
    (-1110.71, 15221.18),
    (-5693.68, 15871.91),
    (-6212.60, 13582.10),
    (-4150.74, 12059.19),
    (-5363.25, 10258.17),
    (-2856.84, 10372.21),
    (1247.34, 9651.55),
    (2498.04, 11076.82),
    (-2488.08, 8399.15),
    (-2095.59, 7311.56),
    (-3500.78, 6488.78),
    (-6663.06, 4662.32),
    (-5713.13, 8684.84),
    (-7201.17, 9957.66),
    (-7640.64, 12424.33),
    (-10422.90, 10846.65),
    (-12227.19, 7684.96),
    (-12730.60, 5712.96),
    (-10030.67, 4909.71),
]

FOLLOWER_CONSUMABLES: tuple[tuple[str, int, str], ...] = (
    ("essence_of_celerity", ModelID.Essence_Of_Celerity.value, "Essence_of_Celerity_item_effect"),
    ("grail_of_might", ModelID.Grail_Of_Might.value, "Grail_of_Might_item_effect"),
    ("armor_of_salvation", ModelID.Armor_Of_Salvation.value, "Armor_of_Salvation_item_effect"),
    ("birthday_cupcake", ModelID.Birthday_Cupcake.value, "Birthday_Cupcake_skill"),
    ("golden_egg", ModelID.Golden_Egg.value, "Golden_Egg_skill"),
    ("candy_corn", ModelID.Candy_Corn.value, "Candy_Corn_skill"),
    ("candy_apple", ModelID.Candy_Apple.value, "Candy_Apple_skill"),
    ("slice_of_pumpkin_pie", ModelID.Slice_Of_Pumpkin_Pie.value, "Pie_Induced_Ecstasy"),
    ("drake_kabob", ModelID.Drake_Kabob.value, "Drake_Skin"),
    ("bowl_of_skalefin_soup", ModelID.Bowl_Of_Skalefin_Soup.value, "Skale_Vigor"),
    ("pahnai_salad", ModelID.Pahnai_Salad.value, "Pahnai_Salad_item_effect"),
    ("war_supplies", ModelID.War_Supplies.value, "Well_Supplied"),
)

CONSET_PROPERTIES = ("essence_of_celerity", "grail_of_might", "armor_of_salvation")
PCON_PROPERTIES = (
    "birthday_cupcake",
    "golden_egg",
    "candy_corn",
    "candy_apple",
    "slice_of_pumpkin_pie",
    "drake_kabob",
    "bowl_of_skalefin_soup",
    "pahnai_salad",
)

bot = Botting(
    BOT_NAME,
    upkeep_auto_inventory_management_active=True,
    upkeep_auto_loot_active=True,
    upkeep_armor_of_salvation_active=True,
    upkeep_birthday_cupcake_active=True,
    upkeep_bowl_of_skalefin_soup_active=True,
    upkeep_candy_apple_active=True,
    upkeep_candy_corn_active=True,
    upkeep_drake_kabob_active=True,
    upkeep_essence_of_celerity_active=True,
    upkeep_golden_egg_active=True,
    upkeep_grail_of_might_active=True,
    upkeep_honeycomb_active=True,
    upkeep_pahnai_salad_active=True,
    upkeep_slice_of_pumpkin_pie_active=True,
    upkeep_war_supplies_active=True,
)


def _are_all_active(property_names: tuple[str, ...]) -> bool:
    return all(bool(bot.Properties.Get(name, "active")) for name in property_names)


def _set_all_active(property_names: tuple[str, ...], active: bool) -> None:
    for property_name in property_names:
        bot.Properties.ApplyNow(property_name, "active", active)


def _get_vanquish_progress() -> tuple[int, int, int, float]:
    if not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable() or not Map.IsVanquishable():
        return 0, 0, 0, 0.0

    foes_killed = Map.GetFoesKilled()
    foes_remaining = Map.GetFoesToKill()
    total_foes = foes_killed + foes_remaining
    progress = (foes_killed / total_foes) if total_foes > 0 else 0.0
    return foes_killed, foes_remaining, total_foes, progress


def _draw_settings():
    global donate_after_run, restart_after_run, watch_vanquish_completion

    PyImGui.text("Drazach Thicket Settings")
    PyImGui.separator()

    restart_after_run = PyImGui.checkbox("Restart after each run", restart_after_run)
    donate_after_run = PyImGui.checkbox("Donate faction after run", donate_after_run)
    watch_vanquish_completion = PyImGui.checkbox("Stop when vanquish completes", watch_vanquish_completion)

    PyImGui.separator()
    PyImGui.text("Automation")

    auto_loot = bool(bot.Properties.Get("auto_loot", "active"))
    auto_loot = PyImGui.checkbox("Auto loot", auto_loot)
    bot.Properties.ApplyNow("auto_loot", "active", auto_loot)

    auto_inventory = bool(bot.Properties.Get("auto_inventory_management", "active"))
    auto_inventory = PyImGui.checkbox("Auto inventory management", auto_inventory)
    bot.Properties.ApplyNow("auto_inventory_management", "active", auto_inventory)

    draw_path = bool(bot.Properties.Get("draw_path", "active"))
    draw_path = PyImGui.checkbox("Draw route overlay", draw_path)
    bot.Properties.ApplyNow("draw_path", "active", draw_path)

    PyImGui.separator()
    PyImGui.text("Leader Consumables")

    use_conset = _are_all_active(CONSET_PROPERTIES)
    new_use_conset = PyImGui.checkbox("Use native Conset upkeep", use_conset)
    if new_use_conset != use_conset:
        _set_all_active(CONSET_PROPERTIES, new_use_conset)

    use_pcons = _are_all_active(PCON_PROPERTIES)
    new_use_pcons = PyImGui.checkbox("Use native PCons upkeep", use_pcons)
    if new_use_pcons != use_pcons:
        _set_all_active(PCON_PROPERTIES, new_use_pcons)

    use_war_supplies = bool(bot.Properties.Get("war_supplies", "active"))
    use_war_supplies = PyImGui.checkbox("Use War Supplies upkeep", use_war_supplies)
    bot.Properties.ApplyNow("war_supplies", "active", use_war_supplies)

    use_honeycomb = bool(bot.Properties.Get("honeycomb", "active"))
    use_honeycomb = PyImGui.checkbox("Use Honeycomb upkeep", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)

    PyImGui.separator()
    PyImGui.text_wrapped(
        "Leader upkeep now uses native Botting properties. Followers stay synced through shared-memory consumable messages."
    )


def _draw_help():
    foes_killed, foes_remaining, total_foes, progress = _get_vanquish_progress()

    PyImGui.text("Drazach Thicket Notes")
    PyImGui.separator()
    if total_foes > 0:
        PyImGui.text(f"Vanquish progress: {foes_killed}/{total_foes} killed")
        PyImGui.progress_bar(progress, 260, 0, f"{progress * 100:.1f}%")
        PyImGui.text(f"Remaining foes: {foes_remaining}")
    else:
        PyImGui.text("Vanquish progress is available once the run is inside the explorable area.")

    PyImGui.separator()
    PyImGui.bullet_text("PrepareForFarm already wires regroup and party-danger callbacks.")
    PyImGui.bullet_text("Party wipe recovery now jumps to a stable return-to-outpost header.")
    PyImGui.bullet_text("The indoor path has several ambush rooms and pop-up groups.")


def _send_consumable_to_followers(model_id: int, skill_name: str):
    skill_id = GLOBAL_CACHE.Skill.GetID(skill_name)
    if skill_id == 0:
        ConsoleLog(BOT_NAME, f"Unable to resolve consumable effect for {skill_name}")
        yield
        return

    sender_email = Player.GetAccountEmail()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    for account in accounts:
        if account.AccountEmail == sender_email:
            continue

        GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            account.AccountEmail,
            SharedCommandType.PCon,
            (model_id, skill_id, 0, 0),
        )
    yield from Routines.Yield.wait(250)


def _upkeep_multibox_consumables(bot: "Botting"):
    while True:
        if Routines.Checks.Map.MapValid() and Routines.Checks.Map.IsExplorable():
            for property_name, model_id, skill_name in FOLLOWER_CONSUMABLES:
                if bot.Properties.IsActive(property_name):
                    yield from _send_consumable_to_followers(model_id, skill_name)

        yield from bot.Wait._coro_for_time(15000)


def _vanquish_watchdog(bot: "Botting"):
    last_remaining = None
    while True:
        yield from Routines.Yield.wait(1000, break_on_map_transition=True)

        if not watch_vanquish_completion:
            continue

        if not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable() or not Map.IsVanquishable():
            continue

        foes_killed, foes_remaining, total_foes, _ = _get_vanquish_progress()
        if foes_remaining != last_remaining and total_foes > 0:
            bot.UI.PrintMessageToConsole(
                BOT_NAME,
                f"Vanquish progress: {foes_killed}/{total_foes} killed, {foes_remaining} remaining.",
            )
            last_remaining = foes_remaining

        if Map.IsVanquishCompleted():
            bot.UI.PrintMessageToConsole(BOT_NAME, "Vanquish complete. Returning to outpost.")
            bot.config.FSM.pause()
            yield
            bot.config.FSM.jump_to_state_by_name(RETURN_TO_OUTPOST_HEADER)
            yield
            bot.config.FSM.resume()
            yield
            return


def bot_routine(bot: Botting) -> None:
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))

    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_START)

    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(*COORDS_TO_EXIT_OUTPOST, EXPLORABLE_TO_VANQUISH)
    bot.Wait.ForTime(4000)

    current_luxon = Player.GetLuxonData()[0]
    current_kurzick = Player.GetKurzickData()[0]

    bot.Move.XYAndInteractNPC(*COORDS_FOR_PRIEST)
    if current_luxon >= current_kurzick:
        bot.Multibox.SendDialogToTarget(0x84)
    bot.Multibox.SendDialogToTarget(DIALOG_FOR_PRIEST)

    bot.States.AddHeader("Start Combat")
    bot.UI.PrintMessageToConsole(BOT_NAME, "Starting Drazach Thicket kill route.")
    bot.Items.UseAllConsumables()
    bot.States.AddManagedCoroutine("DrazachFollowerConsumables", lambda: _upkeep_multibox_consumables(bot))
    bot.States.AddManagedCoroutine("DrazachVanquishWatchdog", lambda: _vanquish_watchdog(bot))
    bot.Move.FollowAutoPath(Vanquish_Path, "Kill Route")
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Return to Outpost")
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOnOutpost()
    bot.Wait.ForTime(3000)

    if donate_after_run:
        bot.Templates.Routines.PrepareForFarm(map_id_to_travel=HOUSE_ZU_HELZER)
        bot.States.AddHeader("Donate Faction")
        bot.Multibox.DonateFaction()
        bot.Wait.ForTime(20000)

    if restart_after_run:
        bot.States.JumpToStepName("[H]VQ Drazach Thicket_1")


def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return

    bot.States.JumpToStepName(RETURN_TO_OUTPOST_HEADER)
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog(BOT_NAME, "Party wipe detected. Returning to outpost.")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("DrazachOnWipe", lambda: _on_party_wipe(bot))


bot.SetMainRoutine(bot_routine)
bot.UI.override_draw_config(_draw_settings)
bot.UI.override_draw_help(_draw_help)


def configure():
    bot.UI.draw_configure_window()


def main():
    if not Routines.Checks.Map.MapValid():
        return
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)


if __name__ == "__main__":
    main()

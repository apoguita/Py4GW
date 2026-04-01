from Py4GWCoreLib import Agent, Botting, ConsoleLog, GLOBAL_CACHE, Map, ModelID, Player, Routines, SharedCommandType
import Py4GW
import PyImGui
import os

MODULE_NAME = "Ferndale (Vanquish)"
MODULE_ICON = "Textures\\Module_Icons\\Vanquish - Ferndale.png"

BOT_NAME = "VQ Ferndale"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "ApoSource", "textures", "VQ_Helmet.png")
HOUSE_ZU_HELZER = 77
FERNDALE = 210

RETURN_TO_OUTPOST_HEADER = "[H]Return to Outpost_4"

restart_after_run = True
donate_after_run = True
watch_vanquish_completion = True

Vanquish_Path: list[tuple[float, float]] = [
    (-9358.26, 12733.01),
    (-11763.50, 6875.62),
    (-8343.50, 10348.14),
    (-9358.26, 12733.01),
    (-11057.97, 20483.20),
    (-5486.26, 18571.37),
    (-5214.33, 15808.12),
    (-3129.34, 15116.34),
    (-1997.73, 19808.71),
    (937.34, 14460.03),
    (-1552.20, 12181.78),
    (-418.83, 9722.58),
    (1623.41, 11681.61),
    (2353.03, 8665.77),
    (3497.35, 7112.98),
    (4920.25, 14639.28),
    (4777.39, 8038.80),
    (6225.68, 14860.03),
    (7747.10, 12009.60),
    (9991.06, 11601.30),
    (9188.73, 16076.83),
    (12075.11, 18961.69),
    (11635.97, 9944.48),
    (3388.01, 5963.63),
    (-2324.46, 224.24),
    (4964.69, 4695.06),
    (9769.06, 3201.43),
    (11953.75, 9212.22),
    (14419.30, 1311.15),
    (8990.68, 518.77),
    (9532.74, -2186.87),
    (5588.56, -1831.51),
    (4358.47, -3596.96),
    (2391.71, -3199.59),
    (-811.80, -2427.94),
    (4681.77, -12246.70),
    (8444.18, -11786.52),
    (8241.50, -13956.31),
    (10657.37, -17255.84),
    (14073.04, -19839.37),
    (3291.92, -13745.13),
    (3629.04, -14834.70),
    (-7260.26, -18284.58),
    (1653.33, -10685.74),
    (-531.23, -10904.48),
    (-114.91, -9269.86),
    (-2798.66, -7118.50),
    (-7398.05, -6884.35),
    (-9947.11, -8920.49),
    (-8121.48, -5619.89),
    (-2614.03, -5811.48),
    (-2540.95, -3791.90),
    (-5708.50, -3462.03),
    (-7744.69, -4578.63),
    (-7268.23, -1897.74),
    (-4026.24, 152.70),
    (-10708.04, 1472.96),
    (-12390.78, 6997.02),
    (-10708.04, 1472.96),
    (-4870.12, 3132.08),
    (-4187.85, 6256.14),
    (-828.52, 8779.88),
    (-6834.56, 8525.84),
    (-1292.07, 14085.61),
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

    PyImGui.text("Ferndale Settings")
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

    PyImGui.text("Ferndale Notes")
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
    PyImGui.bullet_text("The route still contains a known sticky segment around the fork section.")


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
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=HOUSE_ZU_HELZER)

    bot.Party.SetHardMode(True)
    bot.Wait.ForTime(1000)
    bot.Move.XYAndExitMap(10446, -1147, FERNDALE)
    bot.Wait.ForTime(5000)

    current_luxon = Player.GetLuxonData()[0]
    current_kurzick = Player.GetKurzickData()[0]

    bot.Move.XYAndInteractNPC(-12909.00, 15616.00)
    if current_luxon >= current_kurzick:
        bot.Multibox.SendDialogToTarget(0x84)
    bot.Multibox.SendDialogToTarget(0x86)

    bot.States.AddHeader("Start Combat")
    bot.UI.PrintMessageToConsole(BOT_NAME, "Starting Ferndale kill route.")
    bot.Items.UseAllConsumables()
    bot.States.AddManagedCoroutine("FerndaleFollowerConsumables", lambda: _upkeep_multibox_consumables(bot))
    bot.States.AddManagedCoroutine("FerndaleVanquishWatchdog", lambda: _vanquish_watchdog(bot))
    bot.Move.FollowAutoPath(Vanquish_Path, "Kill Route")
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Return to Outpost")
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOnOutpost()
    bot.Wait.ForTime(3000)

    if donate_after_run:
        bot.States.AddHeader("Donate Faction")
        bot.Multibox.DonateFaction()
        bot.Wait.ForTime(25000)

    if restart_after_run:
        bot.States.JumpToStepName("[H]VQ Ferndale_1")


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
    fsm.AddManagedCoroutine("FerndaleOnWipe", lambda: _on_party_wipe(bot))


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

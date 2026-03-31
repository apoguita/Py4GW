from Py4GWCoreLib import Agent, Botting, ConsoleLog, GLOBAL_CACHE, Map, ModelID, Player, Routines, SharedCommandType
import Py4GW
import PyImGui
import os

BOT_NAME = "VQ Morostav Trail"
MODULE_NAME = "Morostav Trail (Vanquish)"
MODULE_ICON = "Textures\\Module_Icons\\Vanquish - Morostav Trail.png"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "ApoSource", "textures", "VQ_Helmet.png")
UNWAKING_WATERS = 298
MOROSTAV_TRAIL = 205
HOUSE_ZU_HELZER = 77

RETURN_TO_OUTPOST_HEADER = "[H]Return to Outpost_4"

restart_after_run = True
donate_after_run = True
watch_vanquish_completion = True

Vanquish_Path: list[tuple[float, float]] = [
    (19283.57, 12803.82),
    (20840.22, 8834.50),
    (16449.09, 9398.16),
    (17075.29, 11542.65),
    (16726.07, 8022.25),
    (14536.42, 7882.84),
    (14301.47, 10907.79),
    (11146.95, 11058.01),
    (9708.27, 10151.21),
    (9584.61, 7463.74),
    (7995.83, 2784.03),
    (6276.70, 3501.12),
    (5180.92, 961.27),
    (3809.45, -1779.69),
    (7216.56, -3962.05),
    (4233.68, -4846.76),
    (624.54, -5716.24),
    (7325.51, -7398.68),
    (6607.77, -7791.77),
    (10400.24, -6050.92),
    (10116.56, -3449.12),
    (11055.48, -2158.53),
    (8462.69, -1815.47),
    (13641.88, 165.81),
    (15200.67, -542.67),
    (15679.82, -1033.62),
    (14458.41, -2669.81),
    (9555.91, -765.55),
    (8071.68, 2811.61),
    (9708.27, 10151.21),
    (3864.64, 10955.62),
    (4661.88, 8195.97),
    (3717.29, 4726.01),
    (2058.90, 8523.23),
    (-2809.45, 5616.83),
    (-3830.95, 2980.44),
    (1208.90, 1636.80),
    (1808.52, -210.84),
    (-3830.95, 2980.44),
    (-4466.05, -3042.06),
    (-6317.80, -7314.83),
    (-4490.83, -8522.61),
    (-5057.49, -4348.15),
    (-2541.39, -3694.41),
    (-3897.96, -6575.30),
    (-1685.32, -4872.92),
    (-925.03, -2848.67),
    (-1099.51, -6853.82),
    (624.54, -5716.24),
    (-4466.05, -3042.06),
    (-3830.95, 2980.44),
    (-8124.41, 1811.43),
    (-10910.36, 3394.90),
    (-12340.56, 1729.70),
    (-11702.48, 392.32),
    (-9231.53, -559.27),
    (-8512.78, -6541.18),
    (-10520.19, -6615.22),
    (-12755.27, -6003.43),
    (-11865.10, -2936.87),
    (-15392.24, 229.49),
    (-13211.56, 5161.36),
    (-16117.06, 7344.00),
    (-15516.23, 5475.97),
    (-20066.16, 5669.60),
    (-17902.03, 10859.59),
    (-15516.23, 5475.97),
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

    PyImGui.text("Morostav Trail Settings")
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

    PyImGui.text("Morostav Trail Notes")
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
    PyImGui.bullet_text("This route has several large patrol clusters and long crossings.")


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
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=UNWAKING_WATERS)

    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(-14168, -8050, MOROSTAV_TRAIL)
    bot.Wait.ForTime(4000)

    current_luxon = Player.GetLuxonData()[0]
    current_kurzick = Player.GetKurzickData()[0]

    bot.Move.XYAndInteractNPC(22155.34, 12125.13)
    if current_luxon >= current_kurzick:
        bot.Multibox.SendDialogToTarget(0x84)
    bot.Multibox.SendDialogToTarget(0x86)

    bot.States.AddHeader("Start Combat")
    bot.UI.PrintMessageToConsole(BOT_NAME, "Starting Morostav Trail kill route.")
    bot.Items.UseAllConsumables()
    bot.States.AddManagedCoroutine("MorostavFollowerConsumables", lambda: _upkeep_multibox_consumables(bot))
    bot.States.AddManagedCoroutine("MorostavVanquishWatchdog", lambda: _vanquish_watchdog(bot))
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
        bot.States.JumpToStepName("[H]VQ Morostav Trail_1")


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
    fsm.AddManagedCoroutine("MorostavOnWipe", lambda: _on_party_wipe(bot))


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

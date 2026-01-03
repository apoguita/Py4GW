from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import *

UMBRAL_GROTTO = "Umbral Grotto"
EYE_OF_THE_NORTH_MAP_ID = 642


def AddHenchies():
    if GLOBAL_CACHE.Party.GetPartySize() == 8:
        yield
        return

    for i in range(1, 8):
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(i)
        yield from Routines.Yield.wait(250)


def ReturnToOutpost():
    yield from Routines.Yield.wait(4000)
    is_map_ready = Map.IsMapReady()
    is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
    is_explorable = Map.IsExplorable()
    is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()

    if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
        GLOBAL_CACHE.Party.ReturnToOutpost()
        yield from Routines.Yield.wait(4000)


def wait_until_item_looted(item_name: str, timeout_ms: int):
    """Wait until a specific item is looted into inventory or timeout occurs."""

    timeout = ThrottledTimer(timeout_ms)

    def search_item_id_by_name(item_name: str) -> int | None:
        item_array = AgentArray.GetItemArray()
        item_array = AgentArray.Filter.ByDistance(item_array, GLOBAL_CACHE.Player.GetXY(), Range.Spirit.value)
        for item_id in item_array:
            name = Agent.GetNameByID(item_id)
            # print(f"item {name}")

            # Clean both strings to remove non-printable characters (like NULL bytes) and whitespace
            name_cleaned = ''.join(char for char in name if char.isprintable()).strip()
            item_name_cleaned = ''.join(char for char in item_name if char.isprintable()).strip()

            # Check if the cleaned strings match
            if name_cleaned == item_name_cleaned:
                print("item found")
                # item found
                return item_id
        return None

    while not timeout.IsExpired():
        print(f"looking for {item_name}")
        item_id: int | None = search_item_id_by_name(item_name)

        if item_id is None:
            yield from Routines.Yield.wait(100)
            continue

        # LOOT
        pos = Agent.GetXY(item_id)
        follow_success = yield from Routines.Yield.Movement.FollowPath([pos], timeout=6000)
        if not follow_success:
            print("Failed to follow path to loot item, next attempt.")
            yield from Routines.Yield.wait(1000)
            continue

        GLOBAL_CACHE.Player.Interact(item_id, call_target=False)
        yield from Routines.Yield.wait(100)

        # ENSURE LOOT IS LOOTED
        pickup_timer = ThrottledTimer(3_000)
        while not pickup_timer.IsExpired():
            item_id = search_item_id_by_name(item_name)
            if item_id is None:
                return True

            # Yield control to prevent freezing and allow game state updates
            yield from Routines.Yield.wait(50)

    print(f"Nothing to loot after ({timeout_ms}ms), exiting.")
    return False


bot = Botting(
    "Deldrimor Leveler",
    upkeep_armor_of_salvation_active=True,
    upkeep_essence_of_celerity_active=True,
    upkeep_grail_of_might_active=True,
    upkeep_armor_of_salvation_restock=1,
    upkeep_essence_of_celerity_restock=1,
    upkeep_grail_of_might_restock=1,
)


def handle_custom_on_unmanaged_fail(bot: Botting):
    # This is dangerous, but stop failures but can be unpredictable
    return False


def deldrimor_leveler(bot: Botting) -> None:
    widget_handler = get_widget_handler()
    widget_handler.disable_widget('Return to outpost on defeat')

    bot.States.AddHeader("Farm Loop")
    bot.Map.Travel(target_map_name=UMBRAL_GROTTO)
    bot.States.AddCustomState(AddHenchies, "Add Henchmen")
    bot.helpers.Events.set_on_unmanaged_fail(lambda: handle_custom_on_unmanaged_fail(bot))

    bot.States.AddHeader("ENTER_DUNGEON")
    bot.Move.XY(-23886, 13874, "go to NPC")
    bot.Dialogs.AtXY(-23886, 13874, 0x838201)  # accept quest
    bot.Wait.ForTime(500)
    bot.Dialogs.AtXY(-23886, 13874, 0x84)  # enter instance
    bot.Wait.ForMapLoad(target_map_id=701)  # we are in the dungeon

    bot.States.AddHeader("LOOT_DUNGEON_LOCK_KEY")
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Enable("auto_combat")
    bot.Move.XY(-14159.74, 15452.50, "Go to shrine for blessing")
    bot.Dialogs.AtXY(-14078.00, 15449.00, 0x84, 'Take blessing')
    bot.Move.XY(-14603, 11927, "go to the key step0")
    bot.Move.XY(-19247, 5187, "go to the key step1")
    bot.Move.XY(-12568.72, 3948.79, 'Go to 2nd Shrine')
    bot.Interact.WithNpcAtXY(-12482.00, 3924.00, "Take blessing bonus")

    bot.Move.XY(-16086.42, -10698.30, "Go to 3rd Shrine")
    bot.Interact.WithNpcAtXY(-16086.42, -10698.30, "Take blessing bonus")
    bot.Move.XY(-10307, -11027, "go to the key step2")

    bot.States.AddCustomState(lambda: wait_until_item_looted("Dungeon Key", timeout_ms=15000), "Acquire Dungeon Key")
    bot.Wait.ForTime(2000)

    bot.States.AddHeader("OPEN_DUNGEON_LOCK")
    bot.Move.XY(-15419, -12252, "go to the dungeon lock")  # GadgetId=8728 IsGadget=true
    bot.Interact.WithGadgetAtXY(-15419, -12252)
    bot.Wait.ForTime(2000)

    bot.States.AddHeader("LOOT_BOSS_KEY")
    bot.Move.XY(-13206, -17459, "go to the boss")
    bot.States.AddCustomState(lambda: wait_until_item_looted("Boss Key", timeout_ms=15000), "Acquire Boss Key")

    bot.States.AddHeader("OPEN_BOSS_LOCK")
    bot.Move.XY(-11162, -18054, "go to the boss lock")  # GadgetId=8730 IsGadget=true
    bot.Interact.WithGadgetAtXY(-11162, -18054)
    bot.Wait.ForTime(2000)

    bot.States.AddHeader("END_CHEST")
    bot.Move.XY(-7851, -19001, "GO TO THE END CHEST")  # GadgetId=9274 IsGadget=true
    bot.Wait.ForTime(90000)  # 90 second wait
    bot.Interact.WithGadgetAtXY(-7594.00, -18657.00)

    bot.States.AddHeader("RESIGN")
    bot.Party.Resign()
    bot.States.AddCustomState(ReturnToOutpost, "Return to Umbral Grotto")
    bot.Wait.ForMapLoad(target_map_name=UMBRAL_GROTTO)  # we are back in outpost

    bot.States.AddHeader("FINALIZE_QUEST")
    bot.Move.XY(-23886, 13874, "go to NPC.")
    bot.Dialogs.AtXY(-23886, 13874, 0x838207, "finalize the quest, accept reward")

    bot.States.AddHeader("REFRESH_OUTPOST")
    bot.Map.Travel(target_map_id=EYE_OF_THE_NORTH_MAP_ID)

    bot.States.AddHeader("ENTER_OUTPOST_AGAIN")
    bot.Map.Travel(target_map_name=UMBRAL_GROTTO)

    # Loop back to farm loop
    bot.States.JumpToStepName("[H]Farm Loop_1")

    bot.States.AddHeader("END")
    bot.Wait.ForTime(120000)


bot.SetMainRoutine(deldrimor_leveler)


def main():
    bot.Update()
    projects_path = Py4GW.Console.get_projects_path()
    widgets_path = projects_path + "\\Bots\\marks_coding_corner\\textures\\"
    texture_icon_path = f'{widgets_path}\\dwarf_art.jpg'
    bot.UI.draw_window(icon_path=texture_icon_path)


if __name__ == "__main__":
    main()

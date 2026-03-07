import os
import time
from typing import Optional

import Py4GW
from Py4GWCoreLib import (
    Agent,
    Botting,
    ConsoleLog,
    GLOBAL_CACHE,
    Map,
    Player,
    Routines,
    SharedCommandType,
)
from Py4GW_widget_manager import get_widget_handler

# ==================== CONFIGURATION ====================
BOT_NAME = "Froggy Farm rezone"
MODULE_NAME = "Bogroot Growths (Froggy Farm)" 
MODULE_ICON = "Textures\\Module_Icons\\Bogroot Growths.png"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "textures", "froggy.png")

# Map IDs
MAP_GADDS_ENCAMPMENT = 638
MAP_SPARKFLY = 558
MAP_BOGROOT_L1 = 615
MAP_BOGROOT_L2 = 616

# Dialog IDs
DWARVEN_BLESSING_DIALOG = 0x84
TEKKS_QUEST_TAKE_DIALOG = 0x833901
TEKKS_QUEST_REWARD_DIALOG = 0x833907

# Coordinates
CHEST_POSITION = (14982.66, -19122.0)
TEKKS_POSITION = (14067.01, -17253.24)
DUNGEON_PORTAL_POSITION = (13097.0, 26393.0)

# ==================== GLOBAL VARIABLES ====================
bot = Botting(BOT_NAME)

# ==================== UTILITY FUNCTIONS ====================

def command_type_routine_in_message_is_active(account_email, shared_command_type):
    """Checks if a multibox command is active for an account"""
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
    if index == -1 or message is None:
        return False
    if message.Command != shared_command_type:
        return False
    return True


def open_bogroot_chest():
    """Multibox coordination for opening the final chest"""
    ConsoleLog(BOT_NAME, "Opening final chest with multibox...")
    yield from Routines.Yield.Agents.TargetNearestGadgetXY(CHEST_POSITION[0], CHEST_POSITION[1], 500)
    target = Player.GetTargetID()
    if target == 0:
        ConsoleLog(BOT_NAME, "No chest found!")
        return
    
    sender_email = Player.GetAccountEmail()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    
    # Wait for the leader to finish
    while command_type_routine_in_message_is_active(sender_email, SharedCommandType.InteractWithTarget):
        yield from Routines.Yield.wait(250)
    while command_type_routine_in_message_is_active(sender_email, SharedCommandType.PickUpLoot):
        yield from Routines.Yield.wait(1000)
    yield from Routines.Yield.wait(5000)
    
    # Command opening for all members
    for account in accounts:
        if not account.AccountEmail or sender_email == account.AccountEmail:
            continue
        ConsoleLog(BOT_NAME, f"Ordering {account.AccountEmail} to open chest")
        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target, 0, 0, 0))
        while command_type_routine_in_message_is_active(account.AccountEmail, SharedCommandType.InteractWithTarget):
            yield from Routines.Yield.wait(1000)
        while command_type_routine_in_message_is_active(account.AccountEmail, SharedCommandType.PickUpLoot):
            yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.wait(5000)
    
    ConsoleLog(BOT_NAME, "ALL accounts opened chest!")
    yield


def wait_for_map_change(target_map_id, timeout_seconds=60):
    """Wait for map change with timeout"""
    ConsoleLog(BOT_NAME, f"Waiting for map change to {target_map_id}...")
    timeout = time.time() + timeout_seconds
    while True:
        current_map = Map.GetMapID()
        if current_map == target_map_id:
            ConsoleLog(BOT_NAME, f"Map change detected! Now in map {target_map_id}")
            yield
            return
        if time.time() > timeout:
            ConsoleLog(BOT_NAME, f"Timeout waiting for map {target_map_id}")
            yield
            return
        yield from Routines.Yield.wait(500)


def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return
    # When the player is resurrected, resume combat
    bot.States.JumpToStepName("[H]Combat_3")
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "party wipe detected")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))
    
    
def UseTengu():
    """Uses Tengu (item ID 30209)"""
    ConsoleLog("UseTengu", "Searching for Tengu...", log=True)
    
    item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(30209)
    
    if item_id:
        ConsoleLog("UseTengu", f"Tengu found (item_id: {item_id}), using...", log=True)
        GLOBAL_CACHE.Inventory.UseItem(item_id)
        yield from Routines.Yield.wait(1000)
        ConsoleLog("UseTengu", "Tengu used!", log=True)
    else:
        ConsoleLog("UseTengu", "Tengu not found in inventory", log=True)
    
    yield    


def loop_marker():
    """Empty marker for loop restart point"""
    ConsoleLog(BOT_NAME, "Starting new dungeon run...")
    yield


# ==================== MAIN ROUTINE ====================

def farm_froggy_routine(bot: Botting) -> None:
    # ===== INITIAL CONFIGURATION =====
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('HeroAI')
    widget_handler.enable_widget('Return to outpost on defeat')
    
    # Register wipe callback
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    
    # Enable properties
    bot.Properties.Enable('auto_combat')
    bot.Properties.Enable('hero_ai')
    
    # ===== START OF BOT =====
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=MAP_GADDS_ENCAMPMENT)
    
    # ===== START OF LOOP =====
    bot.States.AddHeader(f"{BOT_NAME}_LOOP")
    bot.Party.SetHardMode(True)
    
    # ===== GO TO DUNGEON =====
    bot.States.AddHeader("Go to Dungeon")
    bot.Move.XYAndExitMap(-9451.37, -19766.40, target_map_id=MAP_SPARKFLY)
    bot.Wait.UntilOnExplorable()
    bot.Wait.ForTime(2000)
    
    # First blessing in Sparkfly
    bot.Move.XYAndInteractNPC(-8950.0, -19843.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    #bot.States.AddCustomState(UseTengu, "Use Tengu") test
    
    # Path to Tekks
    bot.Move.XY(-8933.0, -18909.0)
    bot.Move.XY(-10361.0, -16332.0)
    bot.Move.XY(-11211.0, -13459.0)
    bot.Move.XY(-10755.0, -10552.0)
    bot.Move.XY(-9544.0, -7814.0)
    bot.Move.XY(-7662.0, -5532.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(-6185.0, -4182.0)
    bot.Move.XY(-4742.0, -2793.0)
    bot.Move.XY(-2150.0, -1301.0)
    bot.Move.XY(71.0, 733.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(1480.0, 3385.0)
    bot.Move.XY(2928.0, 4790.0)
    bot.Move.XY(4280.0, 6273.0)
    bot.Move.XY(5420.0, 7923.0)
    bot.Move.XY(6912.62, 8937.64)
    bot.Move.XY(7771.0, 11123.0)
    bot.Move.XY(8968.0, 12699.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(10876.0, 13304.0)
    bot.Move.XY(12481.0, 14496.0)
    bot.Move.XY(13080.0, 16405.0)
    bot.Move.XY(13487.0, 18372.0)
    bot.Move.XY(13476.0, 20370.0)
    bot.Move.XY(12503.0, 22721.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    
    # Second blessing
    bot.Move.XYAndInteractNPC(12503.0, 22721.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    # ===== LOOP RESTART POINT =====
    bot.States.AddCustomState(loop_marker, "LOOP_RESTART_POINT")
    
    # Take Tekks' quest
    bot.Move.XYAndInteractNPC((12461.80, 22661.57)[0], (12461.80, 22661.57)[1])
    bot.Multibox.SendDialogToTarget(TEKKS_QUEST_TAKE_DIALOG)
    bot.Wait.ForTime(4000)
    
    # Enter the dungeon
    bot.Move.XY(11676.01, 22685.0)
    bot.Move.XY(11562.77, 24059.0)
    bot.Move.XY(13097.0, 26393.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(2000)
    
    # ===== LEVEL 1 =====
    bot.States.AddHeader("Level 1")
    bot.Move.XY(18092.0, 4315.0)
    bot.Move.XY(19045.95, 7877.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    
    # First blessing Level 1
    bot.Move.XYAndInteractNPC(19045.95, 7877.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    # Use consumables
    bot.Multibox.UseAllConsumables()
    bot.Wait.ForTime(3000)
    #bot.States.AddCustomState(UseTengu, "Use Tengu")
    
    # Full path Level 1
    bot.Move.XY(16541.48, 8558.94)
    bot.Move.XY(13038.90, 7792.40)
    bot.Move.XY(11666.15, 6464.53)
    bot.Move.XY(10030.42, 7026.09)
    bot.Move.XY(9752.17, 8241.79) #freez xy33
    bot.Move.XY(8238.36, 7434.97) # test antifreeze
    bot.Move.XY(6491.41, 5310.56)
    bot.Move.XY(5097.64, 2204.33)
    bot.Move.XY(1228.15, 54.49)
    bot.Wait.ForTime(8000)
    bot.Move.XY(-140.87, 2741.86)
    bot.Wait.ForTime(3000)
    bot.Move.XY(1228.15, 54.49)
    bot.Move.XY(141.23, -1965.14)
    bot.Move.XY(-1540.98, -5820.18)
    bot.Move.XY(-269.32, -8533.17)
    bot.Move.XY(-1230.10, -8608.68)
    bot.Wait.ForTime(8000)
    bot.Move.XY(853.90, -9041.68)
    bot.Move.XY(1868.0, -10647.0)
    bot.Move.XY(1645.0, -11810.0)
    bot.Move.XY(1604.90, -12033.70)
    bot.Move.XY(1579.39, -14311.38)
    bot.Move.XY(7319.99, -17202.99)
    bot.Move.XY(8450.01, -16460.50)
    bot.Move.XY(7356.56, -18272.24)
    bot.Move.XY(7865.0, -19350.0)
    bot.Wait.ForTime(5000)
    bot.Wait.UntilOutOfCombat()
    
    # Wait for change to Level 2
    bot.States.AddCustomState(lambda: wait_for_map_change(MAP_BOGROOT_L2, 60), "Wait for Level 2")
    bot.Wait.ForTime(2000)
    
    # ===== LEVEL 2 =====
    bot.States.AddHeader("Level 2")
    
    # Refresh consumables
    bot.Multibox.UseAllConsumables()
    bot.Wait.ForTime(3000)
    
    
    # Enter Level 2 and first blessing
    bot.Move.XY(-11055.0, -5551.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    bot.Move.XYAndInteractNPC(-11055.0, -5551.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    # Path to second blessing
    bot.Move.XY(-11522.0, -3486.0)
    bot.Move.XY(-10639.0, -4076.0)
    bot.Move.XY(-11321.0, -5033.0)
    bot.Move.XY(-11268.0, -3922.0)
    bot.Move.XY(-11187.0, -2190.0)
    bot.Move.XY(-10706.0, -1272.0)
    bot.Move.XY(-10535.0, -191.0)
    bot.Move.XY(-10262.0, -1167.0)
    bot.Wait.ForTime(8000)
    bot.States.AddCustomState(UseTengu, "Use Tengu")
    bot.Move.XY(-9390.0, -393.0)
    bot.Move.XY(-8427.0, 1043.0)
    bot.Move.XY(-7297.0, 2371.0)
    bot.Move.XY(-6460.0, 2964.0)
    bot.Move.XY(-5173.0, 3621.0)
    bot.Move.XY(-4225.0, 4452.0)
    bot.Move.XY(-3405.0, 5274.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(-2778.0, 6814.0)
    bot.Move.XY(-3725.0, 7823.0)
    bot.Move.XY(-3627.0, 8933.0)
    bot.Move.XY(-3014.0, 10554.0)
    bot.Move.XY(-1604.0, 11789.0)
    bot.Move.XY(-955.0, 10984.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    
    # Second blessing
    bot.Move.XYAndInteractNPC(-955.0, 10984.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    # Path to Patriarch's blessing
    bot.Move.XY(216.0, 11534.0)
    bot.Move.XY(1485.0, 12022.0)
    bot.Move.XY(2690.0, 12615.0)
    bot.Wait.ForTime(4000)
    bot.Move.XY(3343.0, 13721.0)
    bot.Move.XY(4693.0, 13577.0)
    bot.Move.XY(5693.0, 12927.0)
    bot.Move.XY(5942.0, 11067.0)
    bot.Move.XY(6878.0, 9657.0) #xy81
    bot.Wait.ForTime(8000) #here
    bot.Move.XY(8100.54, 8544.52)#a moddif  old
    bot.Move.XY(8725.26, 7115.42)# a modif  old (7485.0, 6406.0)
    bot.Move.XY(9234.03, 6843.0)
    bot.Move.XY(8591.0, 4285.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    
    # Patriarch's blessing
    bot.Move.XYAndInteractNPC(8591.0, 4285.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    # Path to boss door
    bot.Move.XY(8372.0, 3448.0)
    bot.Move.XY(8714.0, 2151.0)
    bot.Move.XY(9268.0, 1261.0)
    bot.Move.XY(10207.0, -201.0)
    bot.Move.XY(10999.0, -1356.0)
    bot.Move.XY(10593.0, -2846.0)
    bot.Move.XY(10280.0, -4144.0)
    bot.Move.XY(11016.0, -5384.0)
    bot.Move.XY(12943.0, -6511.0)
    bot.Move.XY(15127.0, -6231.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(16461.0, -6041.0)#here boss and key
    bot.Move.XY(16389.50, -4090.36)
    bot.Wait.ForTime(3000)
    bot.Move.XY(15309.36, -2904.08)
    bot.Wait.ForTime(3000)
    bot.Move.XY(14357.81, -5818.01)
    bot.Wait.ForTime(3000)
    bot.Move.XY(16461.0, -6041.0)#here boss and key
    bot.Wait.ForTime(9000)
    bot.Move.XY(17565.0, -6227.0)
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOutOfCombat()
    
    # Open boss door
    ConsoleLog(BOT_NAME, "Opening boss door...")
    bot.Move.XYAndInteractGadget(17867.55, -6250.63)
    bot.Wait.ForTime(2000)
    bot.Move.XYAndInteractGadget(17867.55, -6250.63)
    bot.Wait.ForTime(2000)
    ConsoleLog(BOT_NAME, "Door should be open!")
    bot.Wait.ForTime(1000)
    
    # Path to final blessing
    bot.Move.XY(17623.87, -6546.0)
    bot.Move.XY(18024.0, -9191.0)
    bot.Move.XY(17110.0, -9842.0)
    bot.Move.XY(15867.0, -10866.0)
    bot.Move.XY(17555.0, -11963.0)
    bot.Move.XY(18761.0, -12747.0)
    bot.Move.XY(19619.0, -11498.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    
    # Final blessing
    bot.Move.XYAndInteractNPC(19619.0, -11498.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    # ===== BOSS FIGHT =====
    bot.States.AddHeader("Boss Fight")
    bot.Move.XY(17582.52, -14231.0)
    bot.Move.XY(14794.47, -14929.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(13609.12, -17286.0)
    bot.Wait.ForTime(5000)
    bot.Move.XY(14079.80, -17776.0)
    bot.Move.XY(15116.40, -18733.0)
    bot.Move.XY(15914.68, -19145.53)
    bot.Wait.UntilOutOfCombat()
    
    # ===== OPEN FINAL CHEST =====
    bot.Wait.ForTime(5000)
    bot.Interact.WithGadgetAtXY(CHEST_POSITION[0], CHEST_POSITION[1])
    bot.States.AddCustomState(open_bogroot_chest, "Open Chest (All Accounts)")
    bot.Wait.ForTime(5000)
    
    # ===== WAIT FOR TELEPORTATION =====
    bot.States.AddCustomState(lambda: wait_for_map_change(MAP_SPARKFLY, 180), "Wait Dungeon End")
    bot.Wait.ForMapLoad(MAP_SPARKFLY)
    
    # ===== TURN IN QUEST =====
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(12638.55, 22499.37)
    bot.Move.XY(12397.78, 22595.02)
    bot.Move.XY(12459.26, 22668.62)
    bot.Move.XYAndInteractNPC(12503.0, 22721.0)
    bot.Multibox.SendDialogToTarget(TEKKS_QUEST_REWARD_DIALOG)
    bot.Wait.ForTime(7000)
    
    # ===== RESET DUNGEON =====
    bot.States.AddHeader("Reset Dungeon")
    ConsoleLog(BOT_NAME, "Resetting dungeon...")
    
    # Go back to dungeon portal
    bot.Move.XY(11676.01, 22685.0)
    bot.Move.XY(11562.77, 24059.0)
    bot.Move.XY(13097.0, 26393.0)
    bot.Wait.ForMapLoad(MAP_BOGROOT_L1)
    
    # Exit dungeon portal
    bot.Move.XY(14600.0, 470.0)
    bot.Wait.ForMapLoad(MAP_SPARKFLY)
    bot.Move.XY(11562.77, 24059.0)
    bot.Move.XY(11161.13, 23562.64)
    bot.Move.XY(12120.30, 22588.55)
    
    ConsoleLog(BOT_NAME, "Dungeon reset complete - Restarting...")
    
    # ===== LOOP =====
    bot.States.JumpToStepName("LOOP_RESTART_POINT")


# ==================== INITIALIZATION ====================

bot.SetMainRoutine(farm_froggy_routine)


# ==================== MAIN ====================

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE, main_child_dimensions=(400, 450))


if __name__ == "__main__":
    main()
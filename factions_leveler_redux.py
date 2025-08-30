from __future__ import annotations
from typing import List, Tuple

# REMOVE: `Botting` from the runtime import below
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Color, Botting,
                          AutoPathing)

import PyImGui
import re

MODULE_NAME = "Factions Leveler"

# ----------------------- BOT CONFIGURATION --------------------------------------------
bot = Botting("Factions Leveler")

#region MainRoutine
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot) #revisited
    ExitMonasteryOverlook(bot) #revisited
    ExitToCourtyard(bot) #revisited
    UnlockSecondaryProfession(bot) #revisited
    UnlockXunlaiStorage(bot) #revisited
    EquipWeapons(bot) #revisited
    ExitToSunquaVale(bot) #revisited
    TravelToMinisterCho(bot) #revisited
    EnterMinisterChoMission(bot) #revisited
    MinisterChoMission(bot) #revisited
    AttributePointQuest1(bot) #revisited
    TakeWarningTheTenguQuest(bot) #revisited
    WarningTheTenguQuest(bot) #revisited
    ExitToSunquaVale(bot) #revisited
    ExitToTsumeiVillage(bot) #revisited
    ExitToPanjiangPeninsula(bot) #revisited
    TheThreatGrows(bot) #revisited
    ExitToCourtyardAggressive(bot) #revisited
    AdvanceToSaoshangTrail(bot) #revisited
    TraverseSaoshangTrail(bot) #revisited
    TakeRewardAndCraftArmor(bot) #revisited
    ExitSeitungHarbor(bot) #revisited
    GoToZenDaijun(bot) #revisited
    EnterZenDaijunMission(bot) #revisited
    ZenDaijunMission(bot) #revisited
    FarmUntilLevel10(bot) #revisited
    AdvanceToMarketplace(bot) #revisited
    AdvanceToKainengCenter(bot) #revisited
    AdvanceToEOTN(bot) #revisited
    ExitBorealStation(bot) #revisited
    TraverseToEOTNOutpost(bot)
    bot.States.AddHeaderStep("Final Step")
    bot.Stop()

#Override the main routine for the bot
bot.SetMainRoutine(create_bot_routine)


#region EVENTS
def on_death(bot: "Botting"):
    print("I Died")

def on_party_wipe_coroutine(bot: "Botting", target_name: str):
    # optional but typical for wipe flow:
    GLOBAL_CACHE.Player.SendChatCommand("resign")
    yield from Routines.Yield.wait(6000)

    fsm = bot.config.FSM
    fsm.jump_to_state_by_name(target_name)  # jump while still paused
    fsm.resume()                            # <— important: unpause so next tick runs the target state
    yield                                    # keep coroutine semantics


def on_party_wipe(bot: "Botting"):
    """
    Clamp-jump to the nearest lower (or equal) waypoint when party is defeated.
    Uses existing FSM API only:
      - get_current_state_number()
      - get_state_name_by_number(step_num)
      - pause(), jump_to_state_by_name(), resume()
    Returns True if a jump occurred.
    """
    print ("Party Wiped! Jumping to nearest waypoint...")
    fsm = bot.config.FSM
    current_step = fsm.get_current_state_number()

    # Your distinct waypoints (as given)
    ENTER_MINISTER_CHO_MISSION = 72
    TAKE_WARNING_THE_TENGU_QUEST = 122
    EXIT_TO_PANJIANG_PENINSULA = 189
    EXIT_SEITUNG_HARBOR = 252
    ENTER_ZEN_DAIJUN_MISSION = 279
    FARM_UNTIL_LEVEL_10 = 336

    waypoints = [
        ENTER_MINISTER_CHO_MISSION,
        TAKE_WARNING_THE_TENGU_QUEST,
        EXIT_TO_PANJIANG_PENINSULA,
        EXIT_SEITUNG_HARBOR,
        ENTER_ZEN_DAIJUN_MISSION,
        FARM_UNTIL_LEVEL_10,
    ]

    # nearest <= current; if none, bail (or pick the first—your call)
    lower_or_equal = [w for w in waypoints if w <= current_step]
    if not lower_or_equal:
        return   # or: target_step = waypoints[0] to always jump somewhere

    target_step = max(lower_or_equal)
    target_name = fsm.get_state_name_by_number(target_step)
    if not target_name:
        return 

    fsm.pause()
    fsm.AddManagedCoroutine(f"{fsm.get_state_name_by_number(current_step)}_OPD", on_party_wipe_coroutine(bot, target_name))

#region Helpers
def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.Properties.disable("pause_on_danger")
    bot.Properties.enable("halt_on_death")
    bot.Properties.set("movement_timeout",value=15000)
    bot.Items.SpawnBonusItems()
    bot.Properties.disable("auto_combat")
    bot.Properties.disable("imp")
    bot.Properties.enable("birthday_cupcake")
    bot.Properties.disable("morale")
    bot.Items.Restock.BirthdayCupcake()
    
def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Properties.enable("pause_on_danger")
    bot.Properties.disable("halt_on_death")
    bot.Properties.set("movement_timeout",value=-1)
    bot.Properties.set("birthday_cupcake", field="restock_quantity", value=50)
    bot.Properties.set("honeycomb", field="restock_quantity", value=100)
    bot.Items.SpawnBonusItems()
    bot.Properties.enable("auto_combat")
    bot.Properties.enable("imp")
    bot.Properties.enable("birthday_cupcake")
    bot.Properties.enable("morale")
    
def EquipSkillBar(): 
    global bot
    def _load_skillbar(skillbar_id: str):
        yield from Routines.Yield.Skills.LoadSkillbar(skillbar_id, log=False)
        yield from Routines.Yield.wait(500)

    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if profession == "Warrior":
        yield from _load_skillbar("OQITEFskxQxw23AAAAAAAAA")
    elif profession == "Ranger":
        yield from _load_skillbar("OggjcJZIoMKGfz3EAAAAAAAAAA")
    elif profession == "Monk":
        yield from _load_skillbar("OwIT4EskxQxo03AAAAAAAAA")
    elif profession == "Necromancer":
        yield from _load_skillbar("OAJTYEskxQxw23AAAAAAAAA")
    elif profession == "Mesmer":
        yield from _load_skillbar("OQJTAEskxQxw23AAAAAAAAA")
    elif profession == "Elementalist":
        yield from _load_skillbar("OgJTwEskxQx+GAAAAAAAAAA")
    elif profession == "Ritualist":
        yield from _load_skillbar("OAKikhgzoYgNfTAAAAAAAAAA")
    elif profession == "Assassin":
        yield from _load_skillbar("OwJjkhfyoIKGs5yAAAAAAAAA")
        
def AddHenchmen():
    def _add_henchman(henchman_id: int):
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(henchman_id)
        ConsoleLog("addhenchman",f"Added Henchman: {henchman_id}", log=False)
        yield from Routines.Yield.wait(250)
        
    party_size = GLOBAL_CACHE.Map.GetMaxPartySize()

    if party_size <= 4:
        yield from _add_henchman(1) #HEALER_ID
        yield from _add_henchman(5) #SPIRITS_ID
        yield from _add_henchman(2) #GUARDIAN_ID
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor"):
        yield from _add_henchman(2) #GUARDIAN_ID
        yield from _add_henchman(3) #DEADLY_ID
        yield from _add_henchman(1) #SHOCK_ID
        yield from _add_henchman(4) #SPIRITS_ID
        yield from _add_henchman(5) #HEALER_ID
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("The Marketplace"):
        yield from _add_henchman(6) #HEALER_ID
        yield from _add_henchman(9) #SPIRIT_ID
        yield from _add_henchman(5) #EARTH_ID
        yield from _add_henchman(1) #SHOCK_ID
        yield from _add_henchman(4) #GRAVE_ID
        yield from _add_henchman(7) #FIGHTER_ID
        yield from _add_henchman(3) #ILLUSION_ID
    elif GLOBAL_CACHE.Map.GetMapID() == 213: #zen_daijun_map_id
        yield from _add_henchman(3) #FIGHTER_ID
        yield from _add_henchman(1) #EARTH_ID
        yield from _add_henchman(6) #GRAVE_ID
        yield from _add_henchman(8) #SPIRIT_ID
        yield from _add_henchman(5) #HEALER_ID
    elif GLOBAL_CACHE.Map.GetMapID() == 194: #kaineng_map_id
        yield from _add_henchman(2) #WARRIOR_ID
        yield from _add_henchman(10) #WARRIOR_ID
        yield from _add_henchman(4) #ELEMENTALIST_ID
        yield from _add_henchman(8) #ELEMENTALIST_ID
        yield from _add_henchman(7) #NECROMANCER_ID
        yield from _add_henchman(9) #MONK_ID
        yield from _add_henchman(12) #RITUALIST_ID
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Boreal Station"):
        yield from _add_henchman(7) #WARRIOR_ID
        yield from _add_henchman(9) #WARRIOR_ID
        yield from _add_henchman(2) #NECROMANCER_ID
        yield from _add_henchman(3) #ELEMENTALIST_ID
        yield from _add_henchman(4) #ELEMENTALIST_ID
        yield from _add_henchman(6) #MONK_ID
        yield from _add_henchman(5) #MONK_ID
    else:
        yield from _add_henchman(1)
        yield from _add_henchman(2)
        yield from _add_henchman(3)
        yield from _add_henchman(4)
        yield from _add_henchman(5)

def PrepareForBattle(bot: Botting):
    ConfigureAggressiveEnv(bot)
    bot.States.AddFSMCustomYieldState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    bot.States.AddFSMCustomYieldState(AddHenchmen, "Add Henchmen")
    bot.Items.Restock.BirthdayCupcake()
    bot.Items.Restock.Honeycomb()
  
def GetArmorMaterialPerProfession(headpiece = False) -> int:
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if primary == "Warrior":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Ranger":
        return ModelID.Tanned_Hide_Square.value
    elif primary == "Monk":
        if headpiece:
            return ModelID.Pile_Of_Glittering_Dust.value
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Assassin":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Mesmer":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Necromancer":
        if headpiece:
            return ModelID.Pile_Of_Glittering_Dust.value
        return ModelID.Tanned_Hide_Square.value
    elif primary == "Ritualist":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Elementalist":
        if headpiece:
            return ModelID.Pile_Of_Glittering_Dust.value
        return ModelID.Bolt_Of_Cloth.value
    else:
        return ModelID.Tanned_Hide_Square.value
      
def BuyMaterials():
    for _ in range(5):
        yield from Routines.Yield.Merchant.BuyMaterial(GetArmorMaterialPerProfession())

def GetArmorPiecesByProfession(bot: Botting):
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    HEAD,CHEST,GLOVES ,PANTS ,BOOTS = 0,0,0,0,0

    if primary == "Warrior":
        HEAD = 10046 #6 bolts of cloth
        CHEST = 10164 #18 bolts of cloth
        GLOVES = 10165 #6 bolts of cloth
        PANTS = 10166 #12 bolts of cloth
        BOOTS = 10163 #6 bolts of cloth
    if primary == "Ranger":
        HEAD = 10483 #6 tanned hides
        CHEST = 10613 #18 tanned hides
        GLOVES = 10614 #6 tanned hides
        PANTS = 10615 #12 tanned hides
        BOOTS = 10612 #6 tanned hides
    if primary == "Monk":
        HEAD = 9600 #6 piles of glittering dust
        CHEST = 9619 #18 tanned hides
        GLOVES = 9620 #6 tanned hides
        PANTS = 9621 #12 tanned hides
        BOOTS = 9618 #6 tanned hides
    if primary == "Assassin":
        HEAD = 7126 #6 tanned hides
        CHEST = 7193 #18 tanned hides
        GLOVES = 7194 #6 tanned hides
        PANTS = 7195 #12 tanned hides
        BOOTS = 7192 #6 tanned hides
    if primary == "Mesmer":
        HEAD = 7528 #6 bolts of cloth
        CHEST = 7546 #18 bolts of cloth
        GLOVES = 7547 #6 bolts of cloth
        PANTS = 7548 #12 bolts of cloth
        BOOTS = 7545 #6 bolts of cloth
    if primary == "Necromancer":
        HEAD = 8741 #6 piles of glittering dust
        CHEST = 8757 #18 tanned hides
        GLOVES = 8758 #6 tanned hides
        PANTS = 8759 #12 tanned hides
        BOOTS = 8756 #6 tanned hides
    if primary == "Ritualist":
        HEAD = 11203 #6 bolts of cloth
        CHEST = 11320 #18 bolts of cloth
        GLOVES = 11321 #6 bolts of cloth
        PANTS = 11323 #12 bolts of cloth
        BOOTS = 11319 #6 bolts of cloth
    if primary == "Elementalist":
        HEAD = 9183 #6 bolts of cloth
        CHEST = 9202 #18 bolts of cloth
        GLOVES = 9203 #6 bolts of cloth
        PANTS = 9204 #12 bolts of cloth
        BOOTS = 9201 #6 bolts of cloth

    return HEAD, CHEST, GLOVES, PANTS, BOOTS


def CraftArmor(bot: Botting):
    HEAD, CHEST, GLOVES, PANTS, BOOTS = GetArmorPiecesByProfession(bot)

    armor_pieces = [
        (CHEST, [GetArmorMaterialPerProfession()], [18]),
        (PANTS, [GetArmorMaterialPerProfession()], [12]),
        (BOOTS,   [GetArmorMaterialPerProfession()], [6]),
    ]

    for item_id, mats, qtys in armor_pieces:
        # --- Craft ---
        result = yield from Routines.Yield.Items.CraftItem(item_id, 200, mats, qtys)
        if not result:
            ConsoleLog("CraftArmor", f"Failed to craft item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return False

        # --- Equip ---
        result = yield from Routines.Yield.Items.EquipItem(item_id)
        if not result:
            ConsoleLog("CraftArmor", f"Failed to equip item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return False
        yield
    return True

def CraftRemainingArmor():
    HEAD, CHEST, GLOVES, PANTS, BOOTS = GetArmorPiecesByProfession(bot)

    armor_pieces = [
        (HEAD,  [GetArmorMaterialPerProfession(headpiece=True)], [6]),
        (GLOVES,  [GetArmorMaterialPerProfession()], [6]),
    ]
    
    if GetArmorMaterialPerProfession(headpiece=True) == ModelID.Pile_Of_Glittering_Dust.value:
        #delete HEAD from the list
        armor_pieces = [piece for piece in armor_pieces if piece[0] != HEAD]

    item_in_storage = GLOBAL_CACHE.Inventory.GetModelCount(GetArmorMaterialPerProfession())
    if item_in_storage > 12:

        path = yield from AutoPathing().get_path_to(20508.00, 9497.00)
        path = path.copy()

        yield from Routines.Yield.Movement.FollowPath(path_points=path)
        yield from Routines.Yield.Agents.InteractWithAgentXY(20508.00, 9497.00)

        for item_id, mats, qtys in armor_pieces:
            # --- Craft ---
            result = yield from Routines.Yield.Items.CraftItem(item_id, 200, mats, qtys)
            if not result:
                ConsoleLog("CraftArmor", f"Failed to craft item ({item_id}).", Py4GW.Console.MessageType.Error)
                bot.helpers.on_unmanaged_fail()
                return False

            # --- Equip ---
            result = yield from Routines.Yield.Items.EquipItem(item_id)
            if not result:
                ConsoleLog("CraftArmor", f"Failed to equip item ({item_id}).", Py4GW.Console.MessageType.Error)
                bot.helpers.on_unmanaged_fail()
                return False

    return True

def _FarmUntilLevel10(bot: Botting):
    level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())
    if level < 10:
        ConsoleLog("Farming until Level 10", f"current level: {level}")
        yield from Routines.Yield.wait(100)

        zen_daijun_map_id = 213
        GLOBAL_CACHE.Party.LeaveParty()
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Map.Travel(zen_daijun_map_id)
        yield from Routines.Yield.wait(1000)
        
        wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(zen_daijun_map_id)
        if not wait_of_map_load:
            Py4GW.Console.Log(MODULE_NAME, "Map load failed.", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
        yield from Routines.Yield.wait(1000)

        state_name = "[H]Enter Zen Daijun Mission_22"
        fsm = bot.config.FSM
        fsm.jump_to_state_by_name(state_name)
    else:
        ConsoleLog("Farming complete", f"current level: {level}")
        yield from Routines.Yield.wait(100)

#region Routines
def InitializeBot(bot: Botting) -> None:
    bot.States.AddHeaderStep("Initial Step")
    condition = lambda: on_party_wipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    bot.Events.OnPartyDefeatedCallback(condition)
    bot.Properties.set("birthday_cupcake", field="restock_quantity", value=50)
    bot.Properties.set("honeycomb", field="restock_quantity", value=100)


def ExitMonasteryOverlook(bot: Botting) -> None:
    bot.States.AddHeaderStep("Exit Monastery Overlook")
    bot.Movement.MoveAndDialog(-7048,5817,0x85) #Move to Ludo I_AM_SURE = 0x85
    bot.Wait.ForMapLoad(target_map_name="Shing Jea Monastery")
    
def ExitToCourtyard(bot: Botting) -> None:
    bot.States.AddHeaderStep("Exit To Courtyard")
    ConfigurePacifistEnv(bot)
    bot.Movement.MoveAndExitMap(-3480, 9460, target_map_name="Linnok Courtyard")
    
def UnlockSecondaryProfession(bot: Botting) -> None:
    def assign_profession_unlocker_dialog():
        global bot
        primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        if primary == "Ranger":
            yield from bot.helpers._interact_with_agent((-92, 9217),0x813D0A)
        else:
            yield from bot.helpers._interact_with_agent((-92, 9217),0x813D0F)
        yield from Routines.Yield.wait(500)

    bot.States.AddHeaderStep("Unlock Secondary Profession")
    bot.Movement.MoveTo(-159, 9174)
    bot.States.AddFSMCustomYieldState(assign_profession_unlocker_dialog, "Update Secondary Profession Dialog")
    bot.UI.CancelSkillRewardWindow()
    bot.UI.CancelSkillRewardWindow()
    bot.Dialogs.DialogAt(-92, 9217,  0x813D07) #TAKE_SECONDARY_REWARD
    bot.Dialogs.DialogAt(-92, 9217,  0x813E01) #TAKE_MINISTER_CHO_QUEST
    #ExitCourtyard
    bot.Movement.MoveAndExitMap(-3762, 9471, target_map_name="Shing Jea Monastery")

def UnlockXunlaiStorage(bot: Botting) -> None:
    bot.States.AddHeaderStep("Unlock Xunlai Storage")
    path_to_xunlai: List[Tuple[float, float]] = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3825.09, 10386.81),]
    bot.Movement.FollowPathAndDialog(path_to_xunlai, 0x84) #UNLOCK_XUNLAI_STORAGE

def EquipWeapons(bot: Botting):
    bot.Items.SpawnBonusItems()
    bot.Items.Equip(5831) #BOW
    
def ExitToSunquaVale(bot: Botting) -> None:
    bot.States.AddHeaderStep("Exit To Sunqua Vale")
    ConfigurePacifistEnv(bot)
    bot.Movement.MoveAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    
def TravelToMinisterCho(bot: Botting) -> None:
    bot.States.AddHeaderStep("Travel To Minister Cho")
    bot.Movement.MoveAndDialog(6637, 16147, 0x80000B, step_name="Talk to Guardman Zui")
    bot.Wait.WasteTime(5000)
    bot.Wait.ForMapLoad(target_map_id=214) #minister_cho_map_id
    bot.Movement.MoveAndDialog(7884, -10029, 0x813E07, step_name="Accept Minister Cho Reward")
    
def EnterMinisterChoMission(bot: Botting):
    bot.States.AddHeaderStep("Enter Minister Cho Mission")
    PrepareForBattle(bot)
    bot.Map.EnterChallenge(delay=4500, target_map_id=214) #minister_cho_map_id

def MinisterChoMission(bot: Botting) -> None:
    bot.States.AddHeaderStep("Minister Cho Mission")
    bot.Movement.MoveTo(6358, -7348, "Move to Activate Mission")
    bot.Movement.MoveTo(507, -8910, "Move to First Door")
    bot.Movement.MoveTo(4889, -5043, "Move to Map Tutorial")
    bot.Movement.MoveTo(6216, -1108, "Move to Bridge Corner")
    bot.Movement.MoveTo(2617, 642, "Move to Past Bridge")
    bot.Movement.MoveTo(0, 1137, "Move to Fight Area")
    bot.Movement.MoveTo(-7454, -7384, "Move to Zoo Entrance")
    bot.Movement.MoveTo(-9138, -4191, "Move to First Zoo Fight")
    bot.Movement.MoveTo(-7109, -25, "Move to Bridge Waypoint")
    bot.Movement.MoveTo(-7443, 2243, "Move to Zoo Exit")
    bot.Movement.MoveTo(-16924, 2445, "Move to Final Destination")
    bot.Interact.InteractNPCAt(-17031, 2448) #"Interact with Minister Cho"
    bot.Wait.ForMapChange(target_map_name="Ran Musu Gardens")
    
def AttributePointQuest1(bot: Botting):
    bot.States.AddHeaderStep("Attribute Point Quest 1")
    bot.Movement.MoveAndDialog(14363.00, 19499.00, 0x815A01)  # I Like treasure
    PrepareForBattle(bot)
    path = [(13713.27, 18504.61),(14576.15, 17817.62),(15824.60, 18817.90)]
    bot.Movement.FollowPath(path)
    map_id = 245
    bot.Movement.MoveAndExitMap(17005, 19787, target_map_id=map_id)
    bot.Movement.MoveTo(-17979.38, -493.08)
    GUARD_ID= 3042
    bot.Dialogs.DialogWithModel(GUARD_ID, 0x815A04)
    exit_function = lambda: (
        not (Routines.Checks.Agents.InDanger(aggro_area=Range.Spirit)) and
        GLOBAL_CACHE.Agent.HasQuest(Routines.Agents.GetAgentIDByModelID(GUARD_ID))
    )
    bot.Movement.FollowModelID(GUARD_ID, follow_range=(Range.Earshot.value /2), exit_condition=exit_function)
    bot.Dialogs.DialogWithModel(GUARD_ID, 0x815A07)
    bot.Map.Travel(target_map_name="Ran Musu Gardens")
    
def TakeWarningTheTenguQuest(bot: Botting):
    bot.States.AddHeaderStep("Take Warning the Tengu Quest")
    bot.Movement.MoveAndDialog(15846, 19013, 0x815301, step_name="Take Warning the Tengu Quest")
    PrepareForBattle(bot)
    ConfigurePacifistEnv(bot)
    bot.Movement.MoveAndExitMap(14730, 15176, target_map_name="Kinya Province")
    
def WarningTheTenguQuest(bot: Botting):
    bot.States.AddHeaderStep("Warning The Tengu Quest")
    bot.Movement.MoveTo(1429, 12768, "Move to Tengu Part2")
    ConfigureAggressiveEnv(bot)
    bot.Movement.MoveAndDialog(-1023, 4844, 0x815304, step_name="Continue Warning the Tengu Quest")
    bot.Movement.MoveTo(-5011, 732, "Move to Tengu Killspot")
    bot.Wait.WasteTimeUntilOOC()
    bot.Movement.MoveAndDialog(-1023, 4844, 0x815307, step_name="Take Warning the Tengu Reward")
    bot.Dialogs.DialogAt(-1023, 4844, 0x815401, step_name="Take The Threat Grows Quest")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")

def ExitToTsumeiVillage(bot: Botting):
    bot.States.AddHeaderStep("Exit To Tsumei Village")
    bot.Movement.MoveAndExitMap(-4900, -13900, target_map_name="Tsumei Village")
    
def ExitToPanjiangPeninsula(bot: Botting):
    bot.States.AddHeaderStep("Exit To Panjiang Peninsula")
    PrepareForBattle(bot)
    bot.Movement.MoveAndExitMap(-11600,-17400, target_map_name="Panjiang Peninsula")

def TheThreatGrows(bot: Botting):
    bot.States.AddHeaderStep("The Threat Grows")
    bot.Movement.MoveTo(9700, 7250, "Move to The Threat Grows Killspot")
    SISTER_TAI_MODEL_ID = 3316
    wait_function = lambda: (
        not (Routines.Checks.Agents.InDanger(aggro_area=Range.Spirit)) and
        GLOBAL_CACHE.Agent.HasQuest(Routines.Agents.GetAgentIDByModelID(SISTER_TAI_MODEL_ID))
    )
    bot.Wait.WasteTimeUntilConditionMet(wait_function)
    ConfigurePacifistEnv(bot)
    bot.Dialogs.DialogWithModel(SISTER_TAI_MODEL_ID, 0x815407, step_name="Accept The Threat Grows Reward")
    bot.Dialogs.DialogWithModel(SISTER_TAI_MODEL_ID, 0x815501, step_name="Take Go to Togo Quest")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    
def ExitToCourtyardAggressive(bot: Botting) -> None:
    bot.States.AddHeaderStep("Exit To Courtyard")
    PrepareForBattle(bot)
    bot.Movement.MoveAndExitMap(-3480, 9460, target_map_name="Linnok Courtyard")
    
def AdvanceToSaoshangTrail(bot: Botting):
    bot.States.AddHeaderStep("Advance To Saoshang Trail")
    bot.Movement.MoveAndDialog(-92, 9217, 0x815507, step_name="Move to Togo 002")
    bot.Dialogs.DialogAt(-92, 9217, 0x815601, step_name="Take Exit Quest")
    bot.Movement.MoveAndDialog(538, 10125, 0x80000B, step_name="Continue")
    bot.Wait.ForMapLoad(target_map_id=313) #saoshang_trail_map_id
    
def TraverseSaoshangTrail(bot: Botting):
    bot.States.AddHeaderStep("Traverse Saoshang Trail")
    bot.Movement.MoveAndDialog(1254, 10875, 0x815604) # Continue
    bot.Movement.MoveAndExitMap(16600, 13150, target_map_name="Seitung Harbor")
    
def TakeRewardAndCraftArmor(bot: Botting):
    bot.States.AddHeaderStep("Take Reward And Craft Armor")
    bot.Movement.MoveAndDialog(16368, 12011, 0x815607) #TAKE_REWARD
    bot.Movement.MoveAndInteractNPC(17520.00, 13805.00)
    bot.States.AddFSMCustomYieldState(BuyMaterials, "Buy Materials")
    bot.Movement.MoveAndInteractNPC(20508.00, 9497.00)
    exec_fn = lambda: CraftArmor(bot)
    bot.States.AddFSMCustomYieldState(exec_fn, "Craft Armor")
    
def ExitSeitungHarbor(bot: Botting):
    PrepareForBattle(bot)
    bot.Movement.MoveAndExitMap(16777, 17540, target_map_name="Jaya Bluffs")
    
def GoToZenDaijun(bot: Botting):
    bot.States.AddHeaderStep("Go To Zen Daijun")
    bot.Movement.MoveAndExitMap(23616, 1587, target_map_name="Haiju Lagoon")
    bot.Movement.MoveAndDialog(16489, -22213, 0x80000B) # CONTINUE
    bot.Wait.WasteTime(6000)
    bot.Wait.ForMapLoad(target_map_id=213) #zen_daijun_map_id
    
def EnterZenDaijunMission(bot:Botting):
    bot.States.AddHeaderStep("Enter Zen Daijun Mission")
    PrepareForBattle(bot)
    bot.Map.EnterChallenge(6000, target_map_id=213) #zen_daijun_map_id
    
def ZenDaijunMission(bot: Botting):
    bot.States.AddHeaderStep("Zen Daijun Mission")
    bot.Movement.MoveTo(11775.22, 11310.60)
    bot.Interact.InteractGadgetAt(11665, 11386)
    bot.Movement.MoveTo(10549,8070)
    bot.Movement.MoveTo(10945,3436)
    bot.Movement.MoveTo(7551,3810)
    bot.Movement.MoveTo(4855.66, 1521.21)
    bot.Interact.InteractGadgetAt(4754,1451)
    bot.Movement.MoveTo(4508, -1084)
    bot.Movement.MoveTo(528, 6271)
    bot.Movement.MoveTo(-9833, 7579)
    
    bot.Movement.MoveTo(-5057.49, 3021.30)
    bot.Interact.InteractGadgetAt(-4862.00, 3005.00)
    #bot.Movement.MoveTo(-4862.00, 3005.00)
    #bot.Movement.MoveTo(-14091.28, 6242.51)
    
    
    bot.Movement.MoveTo(-12983, 2191)
    bot.Movement.MoveTo(-12362, -263)
    bot.Movement.MoveTo(-9813, -114)
    bot.Party.FlagAllHeroes(-8222, -1078)
    bot.Movement.MoveTo(-7681.58, -1509.00)
    bot.Wait.ForMapChange(target_map_name="Seitung Harbor")
    
def FarmUntilLevel10(bot: Botting):
    bot.States.AddHeaderStep("Farm Until Level 10")
    bot.States.AddFSMCustomYieldState(CraftRemainingArmor, "Craft Remaining Armor")
    function_fn = lambda: _FarmUntilLevel10(bot)
    bot.States.AddFSMCustomYieldState(function_fn, "Farm Until Level 10")

def AdvanceToMarketplace(bot: Botting):
    bot.States.AddHeaderStep("Advance To Marketplace")
    bot.Movement.MoveAndDialog(16927, 9004, 0x815D01)  # "I Will Set Sail Immediately"
    bot.Dialogs.DialogAt(16927, 9004, 0x815D05)  # "a Master burden"
    bot.Dialogs.DialogAt(16927, 9004, 0x84)  # i am sure
    bot.Wait.ForMapLoad(target_map_name="Kaineng Docks")
    bot.Movement.MoveAndDialog(9955, 20033, 0x815D04)  # a masters burden
    bot.Movement.MoveAndExitMap(12003, 18529, target_map_name="The Marketplace")

def AdvanceToKainengCenter(bot: Botting):
    bot.States.AddHeaderStep("Advance To Kaineng Center")
    PrepareForBattle(bot)
    bot.Movement.MoveAndExitMap(16640,19882, target_map_name="Bukdek Byway")
    bot.Movement.MoveTo(-10254,-1759)
    bot.Movement.MoveTo(-10332,1442)
    bot.Movement.MoveTo(-10965,9309)
    bot.Movement.MoveTo(-9467,14207)
    path_to_kc = [(-8601.28, 17419.64),(-6857.17, 19098.28),(-6706,20388)]
    bot.Movement.FollowPathAndExitMap(path_to_kc, target_map_id=194) #Kaineng Center
    
def AdvanceToEOTN(bot: Botting):
    bot.States.AddHeaderStep("Advance To Eye of the North")
    bot.Movement.MoveTo(3444.90, -1728.31)
    bot.Movement.MoveAndDialog(3747.00, -2174.00, 0x833501)  # limitless monetary resources
    bot.Movement.MoveTo(3444.90, -1728.31)
    PrepareForBattle(bot)
    bot.Movement.MoveAndExitMap(3243, -4911, target_map_name="Bukdek Byway")
    bot.Movement.MoveAndDialog(-10103.00, 16493.00, 0x84)  # yes
    bot.Wait.ForMapLoad(target_map_id=692)  # tunnels_below_cantha_id
    bot.Movement.MoveTo(16738.77, 3046.05)
    bot.Movement.MoveTo(10968.19, 9623.72)
    bot.Movement.MoveTo(3918.55, 10383.79)
    bot.Movement.MoveTo(8435, 14378)
    bot.Movement.MoveTo(10134,16742)
    bot.Wait.WasteTime(3000)
    ConfigurePacifistEnv(bot)    
    bot.Movement.MoveTo(4523.25, 15448.03)
    bot.Movement.MoveTo(-43.80, 18365.45)
    bot.Movement.MoveTo(-10234.92, 16691.96)
    bot.Movement.MoveTo(-17917.68, 18480.57)
    bot.Movement.MoveTo(-18775, 19097)
    bot.Wait.WasteTime(8000)
    bot.Wait.ForMapLoad(target_map_id=675)  # boreal_station_id

def ExitBorealStation(bot: Botting):
    bot.States.AddHeaderStep("Exit Boreal Station")
    PrepareForBattle(bot)
    bot.Movement.MoveAndExitMap(4684, -27869, target_map_name="Ice Cliff Chasms")
    
def TraverseToEOTNOutpost(bot: Botting):
    bot.States.AddHeaderStep("Traverse To Eye of the North Outpost")
    bot.Movement.MoveTo(3579.07, -22007.27)
    bot.Wait.WasteTime(15000)
    bot.Dialogs.DialogAt(3537.00, -21937.00, 0x839104)
    bot.Movement.MoveTo(3743.31, -15862.36)
    bot.Movement.MoveTo(8267.89, -12334.58)
    bot.Movement.MoveTo(3607.21, -6937.32)
    bot.Movement.MoveAndExitMap(2557.23, -275.97, target_map_id=642) #eotn_outpost_id


#region NOT FIXED-----------------------------------------------------------------
    


selected_step = 0
filter_header_steps = True


def main():
    global selected_step, filter_header_steps
    try:
        bot.Update()
        
        if PyImGui.begin("PathPlanner Test", PyImGui.WindowFlags.AlwaysAutoResize):

            PyImGui.text("Bot is: " + ("Running" if bot.config.fsm_running else "Stopped"))
            current_step = bot.config.FSM.get_current_state_number()
            step_name = bot.config.FSM.get_state_name_by_number(current_step)
            PyImGui.text(f"Current Step: {current_step} - {step_name}")
            
            # --- find nearest header at or before current_step ---
            fsm_steps_all = bot.config.FSM.get_state_names()
            header_for_current = None
            for i in range(current_step - 1, -1, -1):   # walk backwards
                name = fsm_steps_all[i]
                if name.startswith("[H]"):
                    # clean the header formatting like you already do
                    header_for_current = re.sub(r'^\[H\]\s*', '', name)
                    header_for_current = re.sub(r'_(?:\[\d+\]|\d+)$', '', header_for_current)
                    break

            if header_for_current:
                PyImGui.text(f"Current Header: {header_for_current}")
            else:
                PyImGui.text("Current Header: (none found)")

            if PyImGui.button("Start Botting"):
                bot.Start()

            if PyImGui.button("Stop Botting"):
                bot.Stop()
                
            PyImGui.separator()
            
            filter_header_steps = PyImGui.checkbox("Show only Header Steps", filter_header_steps)

            fsm_steps_all = bot.config.FSM.get_state_names()
            

            # choose source list (original names) based on filter
            if filter_header_steps:
                fsm_steps_original = [s for s in fsm_steps_all if s.startswith("[H]")]
            else:
                fsm_steps_original = fsm_steps_all

            # display list: clean headers; leave non-headers as-is
            def _clean_header(name: str) -> str:
                #return name
                if name.startswith("[H]"):
                    name = re.sub(r'^\[H\]\s*', '', name)              # remove [H] (and optional space)
                    name = re.sub(r'_(?:\[\d+\]|\d+)$', '', name)       # remove _123 or _[123] at end
                return name

            fsm_steps = [_clean_header(s) for s in fsm_steps_original]
            

            if not fsm_steps:
                PyImGui.text("No steps to show (filter active).")
            else:
                if selected_step >= len(fsm_steps):
                    selected_step = max(0, len(fsm_steps) - 1)

                selected_step = PyImGui.combo("FSM Steps", selected_step, fsm_steps)
                
                sel_orig = fsm_steps_original[selected_step]
                state_num = bot.config.FSM.get_state_number_by_name(sel_orig)

                # display it (handle not-found defensively)
                if state_num is None or state_num == -1:
                    PyImGui.text(f"Selected step: {sel_orig}  (step #: N/A)")
                else:
                    PyImGui.text(f"Selected step: {sel_orig}  (step #: {state_num})")

                if PyImGui.button("start at Step"):
                    bot.config.fsm_running = True
                    bot.config.FSM.reset()
                    # jump with ORIGINAL name
                    bot.config.FSM.jump_to_state_by_name(fsm_steps_original[selected_step])
                    bot._start_coroutines()


            PyImGui.separator()

            bot.config.config_properties.draw_path.set_now("active",PyImGui.checkbox("Draw Path", bot.config.config_properties.draw_path.is_active()))
            bot.config.config_properties.use_occlusion.set_now("active",PyImGui.checkbox("Use Occlusion", bot.config.config_properties.use_occlusion.is_active()))
            bot.config.config_properties.snap_to_ground_segments.set_now("value", PyImGui.slider_int("Snap to Ground Segments", bot.config.config_properties.snap_to_ground_segments.get("value"), 1, 32))
            bot.config.config_properties.floor_offset.set_now("value", PyImGui.slider_float("Floor Offset", bot.config.config_properties.floor_offset.get("value"), -10.0, 50.0))

            PyImGui.separator()
            PyImGui.text(f"Current values:")
            
            bot.config.upkeep.auto_combat.set_now("active",PyImGui.checkbox("Auto Combat", bot.config.upkeep.auto_combat.is_active()))

        bot.UI.DrawPath(bot.config.config_properties.follow_path_color.get("value"), bot.config.config_properties.use_occlusion.is_active(), bot.config.config_properties.snap_to_ground_segments.get("value"), bot.config.config_properties.floor_offset.get("value"))

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()

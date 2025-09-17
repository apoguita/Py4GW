from __future__ import annotations
from typing import List, Tuple

# REMOVE: `Botting` from the runtime import below
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui)


bot = Botting("Factions Leveler",
              upkeep_birthday_cupcake_restock=50,
              upkeep_honeycomb_restock=100)

#region MainRoutine
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot) #revisited
    ExitMonasteryOverlook(bot) #revisited
    ExitToCourtyard(bot) #revisited
    UnlockSecondaryProfession(bot) #revisited
    UnlockXunlaiStorage(bot) #revisited
    EquipWeapons(bot) #revisited
    CapturePet(bot)
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
    CraftRemainingArmorFSM(bot)
    AttributePointQuest2(bot)
    AdvanceToMarketplace(bot) #revisited
    AdvanceToKainengCenter(bot) #revisited
    AdvanceToEOTN(bot) #revisited
    ExitBorealStation(bot) #revisited
    TraverseToEOTNOutpost(bot)
    bot.States.AddHeader("Final Step")
    bot.Stop()


#region EVENTS
def on_death(bot: "Botting"):
    print("I Died")

def on_party_wipe_coroutine(bot: "Botting", target_name: str):
    # optional but typical for wipe flow:
    GLOBAL_CACHE.Player.SendChatCommand("resign")
    yield from Routines.Yield.wait(8000)

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
    ENTER_MINISTER_CHO_MISSION = 82
    FIRST_ATTRIBUTE_MISSION = 126
    TAKE_WARNING_THE_TENGU_QUEST = 161
    EXIT_TO_PANJIANG_PENINSULA = 238
    ADVANCE_SHAOSHANG_TRAIL = 276
    RESTART_FROM_SEITUNG_HARBOR = 335
    ENTER_ZEN_DAIJUN_MISSION = 362
    SECOND_ATTRIBUTE_MISSION = 418
    ADVANCE_TO_KAINENG_CENTER = 635
    ADVANCE_TO_EOTN = 663
    EXIT_BOREAL_STATION = 727

    waypoints = [
        ENTER_MINISTER_CHO_MISSION,
        FIRST_ATTRIBUTE_MISSION,
        TAKE_WARNING_THE_TENGU_QUEST,
        EXIT_TO_PANJIANG_PENINSULA,
        ADVANCE_SHAOSHANG_TRAIL,
        RESTART_FROM_SEITUNG_HARBOR,
        ENTER_ZEN_DAIJUN_MISSION,
        SECOND_ATTRIBUTE_MISSION,
        ADVANCE_TO_KAINENG_CENTER,
        ADVANCE_TO_EOTN,
        EXIT_BOREAL_STATION,
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
def SpawnBonusItems(bot: Botting) -> None:
    if ((not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(ModelID.Bonus_Nevermore_Flatbow.value)) or
        (not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(ModelID.Igneous_Summoning_Stone.value))):
        bot.Items.SpawnBonusItems()
        bot.Items.DestroyBonusItems()
    
def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.Properties.Disable("pause_on_danger")
    bot.Properties.Enable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=15000)
    
    SpawnBonusItems(bot)

    bot.Properties.Disable("auto_combat")
    bot.Properties.Disable("imp")
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Disable("honeycomb")
    bot.Items.Restock.BirthdayCupcake()
    
def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("imp")
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Enable("honeycomb")
    SpawnBonusItems(bot)

    
def EquipSkillBar(): 
    global bot

    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())
    skillbar = ""
    
    if profession == "Warrior":
        if level <= 3: #10 attribute points available
            skillbar = "OQIRkpQxw23AAAAg2CA"
        elif level <= 4: #15 attribute points available
            skillbar = "OQIRkrQxw23AAAAg2CA"
        elif level <= 5: #20 attribute points available
            skillbar = "OQIUEDrgjcFKG2+GAAAA0WAA"
        elif level <= 6: #25 attribute points available
            skillbar = "OQITEDsktQxw23AAAAg2CAA"
        elif level <= 7: #45 attribute points available (including 15 attribute points from quests)
            skillbar = "OQIUED7gjMGKG2+GAAAA0WAA"
        elif level <= 8: #50 attribute points available
            skillbar = "OQITYDckzQxw23AAAAg2CAA"
        elif level <= 9: #55 attribute points available
            skillbar = "OQITYHckzQxw23AAAAg2CAA"
        elif level <= 10: #55 attribute points available
            skillbar = "OQIUEDLhjcGKG2+GAAAA0WAA"
        else: #20 attribute points available
            skillbar = "OQITYN8kzQxw23AAAAg2CAA"
    elif profession == "Ranger":
        skillbar = "OggjYZZIYMKG1pvBAAAAA0GBAA"
    elif profession == "Monk":
        skillbar = "OwISYxcGKG2o03AAA0WA"
    elif profession == "Necromancer":
        skillbar = "OAJTYJckzQxw23AAAAg2CAA"
    elif profession == "Mesmer":
        skillbar = "OQJTYJckzQxw23AAAAg2CAA"
    elif profession == "Elementalist":
        skillbar = "OgJUwCLhjcGKG2+GAAAA0WAA"
    elif profession == "Ritualist":
        skillbar = "OAKkYRYRWCGjiB24b+mAAAAtRAA"
    elif profession == "Assassin":
        skillbar = "OwJkYRZ5XMGiiBbuMAAAAAtJAA"

    yield from Routines.Yield.Skills.LoadSkillbar(skillbar)


def EquipCaptureSkillBar(): 
    global bot
    skillbar = ""
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if profession == "Warrior":
        skillbar = "OQIAEbGAAAAAAAAAAA"
    elif profession == "Ranger":
        skillbar = "OgAAEbGAAAAAAAAAAA"
    elif profession == "Monk":
        skillbar = "OwIAEbGAAAAAAAAAAA"
    elif profession == "Necromancer":
        skillbar = "OAJAEbGAAAAAAAAAAA"
    elif profession == "Mesmer":
        skillbar = "OQJAEbGAAAAAAAAAAA"
    elif profession == "Elementalist":
        skillbar = "OgJAEbGAAAAAAAAAAA"
    elif profession == "Ritualist":
        skillbar = "OAKkYRYRWCGxmBAAAAAAAAAA"
    elif profession == "Assassin":
        skillbar = "OwJkYRZ5XMGxmBAAAAAAAAAA"

    yield from Routines.Yield.Skills.LoadSkillbar(skillbar)




def AddHenchmen():
    def _add_henchman(henchman_id: int):
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(henchman_id)
        ConsoleLog("addhenchman",f"Added Henchman: {henchman_id}", log=False)
        yield from Routines.Yield.wait(250)
        
    party_size = GLOBAL_CACHE.Map.GetMaxPartySize()

    henchmen_list = []
    if party_size <= 4:
        henchmen_list.extend([1, 5, 2]) 
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor"):
        henchmen_list.extend([2, 3, 1, 4, 5]) 
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("The Marketplace"):
        henchmen_list.extend([6,9,5,1,4,7,3])
    elif GLOBAL_CACHE.Map.GetMapID() == 213: #zen_daijun_map_id
        henchmen_list.extend([3,1,6,8,5])
    elif GLOBAL_CACHE.Map.GetMapID() == 194: #kaineng_map_id
        henchmen_list.extend([2,10,4,8,7,9,12])
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Boreal Station"):
        henchmen_list.extend([7,9,2,3,4,6,5])
    else:
        henchmen_list.extend([1,2,3,4,5,6,7])
        
    for henchman_id in henchmen_list:
        yield from _add_henchman(henchman_id)

def PrepareForBattle(bot: Botting):
    ConfigureAggressiveEnv(bot)
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AddHenchmen, "Add Henchmen")
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
            bot.helpers.Events.on_unmanaged_fail()
            return False

        # --- Equip ---
        result = yield from Routines.Yield.Items.EquipItem(item_id)
        if not result:
            ConsoleLog("CraftArmor", f"Failed to equip item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
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
                bot.helpers.Events.on_unmanaged_fail()
                return False

            # --- Equip ---
            result = yield from Routines.Yield.Items.EquipItem(item_id)
            if not result:
                ConsoleLog("CraftArmor", f"Failed to equip item ({item_id}).", Py4GW.Console.MessageType.Error)
                bot.helpers.Events.on_unmanaged_fail()
                return False

    return True


#region Routines
def InitializeBot(bot: Botting) -> None:
    bot.States.AddHeader("Initial Step")
    condition = lambda: on_party_wipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    bot.Events.OnPartyDefeatedCallback(condition)

def ExitMonasteryOverlook(bot: Botting) -> None:
    bot.States.AddHeader("Exit Monastery Overlook")
    bot.Move.XYAndDialog(-7048,5817,0x85) #Move to Ludo I_AM_SURE = 0x85
    bot.Wait.ForMapLoad(target_map_name="Shing Jea Monastery")
    
def ExitToCourtyard(bot: Botting) -> None:
    bot.States.AddHeader("Exit To Courtyard")
    ConfigurePacifistEnv(bot)
    bot.Move.XYAndExitMap(-3480, 9460, target_map_name="Linnok Courtyard")
    
def UnlockSecondaryProfession(bot: Botting) -> None:
    def assign_profession_unlocker_dialog():
        global bot
        primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        if primary == "Ranger":
            yield from bot.helpers.Interact._with_agent((-92, 9217),0x813D0A)
        else:
            yield from bot.helpers.Interact._with_agent((-92, 9217),0x813D0F)
        yield from Routines.Yield.wait(500)

    bot.States.AddHeader("Unlock Secondary Profession")
    bot.Move.XY(-159, 9174)
    bot.States.AddCustomState(assign_profession_unlocker_dialog, "Update Secondary Profession Dialog")
    bot.UI.CancelSkillRewardWindow()
    bot.UI.CancelSkillRewardWindow()
    bot.Dialogs.AtXY(-92, 9217,  0x813D07) #TAKE_SECONDARY_REWARD
    bot.Dialogs.AtXY(-92, 9217,  0x813E01) #TAKE_MINISTER_CHO_QUEST
    #ExitCourtyard
    bot.Move.XYAndExitMap(-3762, 9471, target_map_name="Shing Jea Monastery")

def UnlockXunlaiStorage(bot: Botting) -> None:
    bot.States.AddHeader("Unlock Xunlai Storage")
    path_to_xunlai: List[Tuple[float, float]] = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3825.09, 10386.81),]
    bot.Move.FollowPathAndDialog(path_to_xunlai, 0x84) #UNLOCK_XUNLAI_STORAGE

def EquipWeapons(bot: Botting):
    SpawnBonusItems(bot)
    bot.Items.Equip(ModelID.Bonus_Nevermore_Flatbow.value)
    
    
def ExitToSunquaVale(bot: Botting) -> None:
    bot.States.AddHeader("Exit To Sunqua Vale")
    ConfigurePacifistEnv(bot)
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    
def RangerCapturePet(bot: Botting) -> None:
    bot.Move.XYAndDialog(-7782.00, 6687.00,0x810403) #Locate Sujun
    bot.Dialogs.AtXY(-7782.00, 6687.00,0x810401) #Accept Quest
    bot.UI.CancelSkillRewardWindow()
      
def RqangerGetSkills(bot: Botting) -> None:
    bot.Move.XYAndDialog(5103.00, -4769.00,0x810407) #accept reward
    bot.Dialogs.AtXY(5103.00, -4769.00,0x811401) #of course i will help

def CapturePet(bot: Botting) -> None:
    bot.States.AddHeader("Capture Pet")
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if primary == "Ranger":
        RangerCapturePet(bot)
     
    bot.States.AddCustomState(EquipCaptureSkillBar, "Equip Capture Skill Bar")
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")

    bot.Move.XY(13970.94, -13085.83)
    bot.Target.Model(2954) #Tiger
    bot.SkillBar.UseSkill(411) #Capture Pet
    bot.Wait.ForTime(22000)
    
    if primary == "Ranger":
        RqangerGetSkills(bot)
         
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    
def TravelToMinisterCho(bot: Botting) -> None:
    bot.States.AddHeader("Travel To Minister Cho")
    bot.Move.XYAndDialog(6637, 16147, 0x80000B, step_name="Talk to Guardman Zui")
    bot.Wait.ForTime(7000)
    bot.Wait.ForMapLoad(target_map_id=214) #minister_cho_map_id
    bot.Move.XYAndDialog(7884, -10029, 0x813E07, step_name="Accept Minister Cho Reward")
    
def EnterMinisterChoMission(bot: Botting):
    bot.States.AddHeader("Enter Minister Cho Mission")
    bot.Wait.ForTime(2000)
    PrepareForBattle(bot)
    bot.Map.EnterChallenge(delay=4500, target_map_id=214) #minister_cho_map_id

def MinisterChoMission(bot: Botting) -> None:
    bot.States.AddHeader("Minister Cho Mission")
    auto_path_list:List[Tuple[float, float]] = [
            (6358, -7348),   # Move to Activate Mission
            (507, -8910),    # Move to First Door
            (4889, -5043),   # Move to Map Tutorial
            (6216, -1108),   # Move to Bridge Corner
            (2617, 642),     # Move to Past Bridge
            (0, 1137),       # Move to Fight Area
            (-7454, -7384),  # Move to Zoo Entrance
            (-9138, -4191),  # Move to First Zoo Fight
            (-7109, -25),    # Move to Bridge Waypoint
            (-7443, 2243),   # Move to Zoo Exit
            (-16924, 2445),  # Move to Final Destination
    ]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Interact.WithNpcAtXY(-17031, 2448) #"Interact with Minister Cho"
    bot.Wait.ForMapToChange(target_map_name="Ran Musu Gardens")
    
def AttributePointQuest1(bot: Botting):
    bot.States.AddHeader("Attribute Point Quest 1")
    bot.Move.XYAndDialog(14363.00, 19499.00, 0x815A01)  # I Like treasure
    PrepareForBattle(bot)
    path = [(13713.27, 18504.61),(14576.15, 17817.62),(15824.60, 18817.90)]
    bot.Move.FollowPath(path)
    map_id = 245
    bot.Move.XYAndExitMap(17005, 19787, target_map_id=map_id)
    bot.Move.XY(-17979.38, -493.08)
    GUARD_ID= 3042
    bot.Dialogs.WithModel(GUARD_ID, 0x815A04)
    exit_function = lambda: (
        not (Routines.Checks.Agents.InDanger(aggro_area=Range.Spirit)) and
        GLOBAL_CACHE.Agent.HasQuest(Routines.Agents.GetAgentIDByModelID(GUARD_ID))
    )
    bot.Move.FollowModel(GUARD_ID, follow_range=(Range.Area.value), exit_condition=exit_function)
    bot.Dialogs.WithModel(GUARD_ID, 0x815A07)
    bot.Map.Travel(target_map_name="Ran Musu Gardens")
    
def TakeWarningTheTenguQuest(bot: Botting):
    bot.States.AddHeader("Take Warning the Tengu Quest")
    bot.Move.XYAndDialog(15846, 19013, 0x815301, step_name="Take Warning the Tengu Quest")
    PrepareForBattle(bot)
    ConfigurePacifistEnv(bot)
    bot.Move.XYAndExitMap(14730, 15176, target_map_name="Kinya Province")
    
def WarningTheTenguQuest(bot: Botting):
    bot.States.AddHeader("Warning The Tengu Quest")
    bot.Move.XY(1429, 12768, "Move to Tengu Part2")
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(-1023, 4844, 0x815304, step_name="Continue Warning the Tengu Quest")
    bot.Move.XY(-5011, 732, "Move to Tengu Killspot")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(-1023, 4844, 0x815307, step_name="Take Warning the Tengu Reward")
    bot.Dialogs.AtXY(-1023, 4844, 0x815401, step_name="Take The Threat Grows Quest")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")

def ExitToTsumeiVillage(bot: Botting):
    bot.States.AddHeader("Exit To Tsumei Village")
    bot.Move.XYAndExitMap(-4900, -13900, target_map_name="Tsumei Village")
    
def ExitToPanjiangPeninsula(bot: Botting):
    bot.States.AddHeader("Exit To Panjiang Peninsula")
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(-11600,-17400, target_map_name="Panjiang Peninsula")

def TheThreatGrows(bot: Botting):
    bot.States.AddHeader("The Threat Grows")
    bot.Move.XY(9793.73, 7470.04, "Move to The Threat Grows Killspot")
    SISTER_TAI_MODEL_ID = 3316
    wait_function = lambda: (
        not (Routines.Checks.Agents.InDanger(aggro_area=Range.Spirit)) and
        GLOBAL_CACHE.Agent.HasQuest(Routines.Agents.GetAgentIDByModelID(SISTER_TAI_MODEL_ID))
    )
    bot.Wait.UntilCondition(wait_function)
    ConfigurePacifistEnv(bot)
    bot.Dialogs.WithModel(SISTER_TAI_MODEL_ID, 0x815407, step_name="Accept The Threat Grows Reward")
    bot.Dialogs.WithModel(SISTER_TAI_MODEL_ID, 0x815501, step_name="Take Go to Togo Quest")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    
def ExitToCourtyardAggressive(bot: Botting) -> None:
    bot.States.AddHeader("Exit To Courtyard")
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(-3480, 9460, target_map_name="Linnok Courtyard")
    
def AdvanceToSaoshangTrail(bot: Botting):
    bot.States.AddHeader("Advance To Saoshang Trail")
    bot.Move.XYAndDialog(-92, 9217, 0x815507, step_name="Move to Togo 002")
    bot.Dialogs.AtXY(-92, 9217, 0x815601, step_name="Take Exit Quest")
    bot.Move.XYAndDialog(538, 10125, 0x80000B, step_name="Continue")
    bot.Wait.ForMapLoad(target_map_id=313) #saoshang_trail_map_id
    
def TraverseSaoshangTrail(bot: Botting):
    bot.States.AddHeader("Traverse Saoshang Trail")
    bot.Move.XYAndDialog(1254, 10875, 0x815604) # Continue
    bot.Move.XYAndExitMap(16600, 13150, target_map_name="Seitung Harbor")
    
def TakeRewardAndCraftArmor(bot: Botting):
    bot.States.AddHeader("Take Reward And Craft Armor")
    bot.Move.XYAndDialog(16368, 12011, 0x815607) #TAKE_REWARD
    bot.Move.XYAndInteractNPC(17520.00, 13805.00)
    bot.States.AddCustomState(BuyMaterials, "Buy Materials")
    bot.Move.XYAndInteractNPC(20508.00, 9497.00)
    exec_fn = lambda: CraftArmor(bot)
    bot.States.AddCustomState(exec_fn, "Craft Armor")
    
def ExitSeitungHarbor(bot: Botting):
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(16777, 17540, target_map_name="Jaya Bluffs")
    
def GoToZenDaijun(bot: Botting):
    bot.States.AddHeader("Go To Zen Daijun")
    bot.Move.XYAndExitMap(23616, 1587, target_map_name="Haiju Lagoon")
    bot.Move.XYAndDialog(16489, -22213, 0x80000B) # CONTINUE
    bot.Wait.ForTime(6000)
    bot.Wait.ForMapLoad(target_map_id=213) #zen_daijun_map_id
    
def EnterZenDaijunMission(bot:Botting):
    bot.States.AddHeader("Enter Zen Daijun Mission")
    PrepareForBattle(bot)
    bot.Map.EnterChallenge(6000, target_map_id=213) #zen_daijun_map_id
    
def ZenDaijunMission(bot: Botting):
    bot.States.AddHeader("Zen Daijun Mission")
    bot.Move.XY(11775.22, 11310.60)
    bot.Interact.WithGadgetAtXY(11665, 11386)
    auto_path_list:List[Tuple[float, float]] = [(10549,8070),(10945,3436),(7551,3810),(4855.66, 1521.21)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Interact.WithGadgetAtXY(4754,1451)
    auto_path_list:List[Tuple[float, float]] = [(4508, -1084),(528, 6271),(-9833, 7579),(-5057.49, 3021.30)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Interact.WithGadgetAtXY(-4862.00, 3005.00)
    auto_path_list:List[Tuple[float, float]] = [(-12983, 2191),(-12362, -263),(-9813, -114)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Party.FlagAllHeroes(-8222, -1078)
    bot.Move.XY(-7681.58, -1509.00)
    bot.Wait.ForMapToChange(target_map_name="Seitung Harbor")

def CraftRemainingArmorFSM(bot: Botting):
    bot.States.AddHeader("Craft Remaining Armor")
    bot.States.AddCustomState(CraftRemainingArmor, "Craft Remaining Armor")

def AttributePointQuest2(bot: Botting):
    def enable_combat_and_wait(ms:int):
        global bot
        bot.Properties.Enable("auto_combat")
        bot.Wait.ForTime(ms)
        bot.Properties.Disable("auto_combat")
        
        
        
    bot.States.AddHeader("Attribute Point Quest 2")
    bot.Move.XY(19698.33, 7504.35)
    bot.Interact.WithGadgetAtXY(19642.00, 7386.00)
    bot.Wait.ForTime(5000)
    bot.Dialogs.WithModel(3958,0x815C01) #Take Quest from Zunraa
    PrepareForBattle(bot)
    bot.Dialogs.AtXY(20350.00, 9087.00, 0x80000B)
    bot.Wait.ForMapLoad(target_map_id=246)  # zen_daijun_map_id
    auto_path_list:List[Tuple[float, float]] = [
    (-13959.50, 6375.26), #half the temple
    (-14567.47, 1775.31), #side of road
    (-12310.05, 2417.60), #across road
    (-12071.83, 294.29),  #bridge and patrol
    (-9972.85, 4141.29), #miasma passtrough
    (-9331.86, 7932.66), #in front of bridge
    (-6353.09, 9385.63), #past he miasma on way to waterfall
    (247.80, 12070.21), #waterfall
    (-8180.59, 12189.97), #back to kill patrols
    (-9540.45, 7760.86), #in front of bridge 2
    (-5038.08, 2977.42)] #to shrine
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Interact.WithGadgetAtXY(-4862.00, 3005.00)
    bot.Move.XY(-9643.93, 7759.69) #front of bridge 3
    bot.Wait.ForTime(5000)

    bot.Properties.Disable("auto_combat")
    player_pos = GLOBAL_CACHE.Player.GetXY()
    path =[(-8294.21, 10061.62)] #position zunraa
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    player_pos = GLOBAL_CACHE.Player.GetXY()
    path = [(-6473.26, 8771.21)] #clear miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    path =[(-6365.32, 10234.20)] #position zunraa2
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    bot.Properties.Enable("auto_combat")
    
    bot.Move.XY(-8655.04, -769.98) # to next Miasma on temple
    bot.Wait.ForTime(5000)
    bot.Properties.Disable("auto_combat")
    
    path = [(-6744.75, -1842.97)] #clear half the miasma 
    bot.Move.FollowPath(path)
    enable_combat_and_wait(10000)
    path = [(-7720.80, -905.19)] #finish miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    bot.Properties.Enable("auto_combat")
    
    auto_path_list:List[Tuple[float, float]] = [
    (-5016.76, -8800.93), #half the map
    (3268.68, -6118.96), #passtrough miasma
    (3808.16, -830.31), #back of bell
    (536.95, 2452.17), #yard
    (599.18, 12088.79), #waterfall
    (3605.82, 2336.79), #patrol kill
    (5509.49, 1978.54), #bell
    (11313.49, 3755.03), #side path (90)
    (12442.71, 8301.94), #middle aggro
    (8133.23, 7540.54), #enemies on the side
    (15029.96, 10187.60), #enemies on the loop
    (14062.33, 13088.72), #corner
    (11775.22, 11310.60)] #Zunraa
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Interact.WithGadgetAtXY(11665, 11386)
    
    bot.Properties.Disable("auto_combat")
    path = [(12954.96, 9288.47)] #miasma
    bot.Move.FollowPath(path) 
    enable_combat_and_wait(5000)

    path = [(12507.05, 11450.91)] #finish miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    bot.Properties.Enable("auto_combat")
    
    bot.Move.XY(7709.06, 4550.47) #past bridge trough miasma
    bot.Wait.ForTime(5000)
    
    bot.Properties.Disable("auto_combat")
    path = [(9334.25, 5746.98)] #1/3 miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    
    path = [(7554.94, 6159.84)] #2/3 miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)

    path =[(9242.30, 6127.45)] #finish miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    bot.Properties.Enable("auto_combat")
    
    bot.Move.XY(4855.66, 1521.21)
    bot.Interact.WithGadgetAtXY(4754,1451)
    bot.Move.XY(2958.13, 6410.57)
    
    bot.Properties.Disable("auto_combat")
    path = [(2683.69, 8036.28)] #clear miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(8000)
    bot.Move.XY(3366.55, -5996.11) #to the other miasma at the middle
    
    enable_combat_and_wait(10000)
    path =[(1866.87, -5454.60)]
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    path= [(3322.93, -5703.29)]
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    path =[(1855.78, -5376.80)]
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    bot.Properties.Enable("auto_combat")
    
    #bot.Movement.MoveTo(-11296.89, -5229.18)
    #bot.Interact.InteractGadgetAt(-11344.00, -5432.00)
    bot.Move.XY(-8655.04, -769.98)
    bot.Move.XY(-7453.22, -1483.71)
    wait_function = lambda: (
        not (Routines.Checks.Agents.InDanger(aggro_area=Range.Spirit)))
    bot.Wait.UntilCondition(wait_function)
    
    bot.Map.Travel(target_map_name="Seitung Harbor")
    bot.Move.XY(19698.33, 7504.35)
    bot.Interact.WithGadgetAtXY(19642.00, 7386.00)
    bot.Wait.ForTime(5000)
    ZUNRAA_MODEL_ID = 3958
    bot.Dialogs.WithModel(ZUNRAA_MODEL_ID,0x815C07) #Complete Quest from Zunraa
    

def AdvanceToMarketplace(bot: Botting):
    bot.States.AddHeader("Advance To Marketplace")
    bot.Move.XYAndDialog(16927, 9004, 0x815D01)  # "I Will Set Sail Immediately"
    bot.Dialogs.AtXY(16927, 9004, 0x815D05)  # "a Master burden"
    bot.Dialogs.AtXY(16927, 9004, 0x84)  # i am sure
    bot.Wait.ForMapLoad(target_map_name="Kaineng Docks")
    bot.Move.XYAndDialog(9955, 20033, 0x815D04)  # a masters burden
    bot.Move.XYAndExitMap(12003, 18529, target_map_name="The Marketplace")

def AdvanceToKainengCenter(bot: Botting):
    bot.States.AddHeader("Advance To Kaineng Center")
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(16640,19882, target_map_name="Bukdek Byway")
    bot.Move.XY(-10254,-1759)
    bot.Move.XY(-10332,1442)
    bot.Move.XY(-10965,9309)
    bot.Move.XY(-9467,14207)
    path_to_kc = [(-8601.28, 17419.64),(-6857.17, 19098.28),(-6706,20388)]
    bot.Move.FollowPathAndExitMap(path_to_kc, target_map_id=194) #Kaineng Center
    
def AdvanceToEOTN(bot: Botting):
    bot.States.AddHeader("Advance To Eye of the North")
    bot.Move.XY(3444.90, -1728.31)
    bot.Move.XYAndDialog(3747.00, -2174.00, 0x833501)  # limitless monetary resources
    bot.Move.XY(3444.90, -1728.31)
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(3243, -4911, target_map_name="Bukdek Byway")
    bot.Move.XYAndDialog(-10103.00, 16493.00, 0x84)  # yes
    bot.Wait.ForMapLoad(target_map_id=692)  # tunnels_below_cantha_id
    bot.Move.XY(16738.77, 3046.05)
    bot.Move.XY(10968.19, 9623.72)
    bot.Move.XY(3918.55, 10383.79)
    bot.Move.XY(8435, 14378)
    bot.Move.XY(10134,16742)
    bot.Wait.ForTime(3000)
    ConfigurePacifistEnv(bot)    
    bot.Move.XY(4523.25, 15448.03)
    bot.Move.XY(-43.80, 18365.45)
    bot.Move.XY(-10234.92, 16691.96)
    bot.Move.XY(-17917.68, 18480.57)
    bot.Move.XY(-18775, 19097)
    bot.Wait.ForTime(8000)
    bot.Wait.ForMapLoad(target_map_id=675)  # boreal_station_id

def ExitBorealStation(bot: Botting):
    bot.States.AddHeader("Exit Boreal Station")
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(4684, -27869, target_map_name="Ice Cliff Chasms")
    
def TraverseToEOTNOutpost(bot: Botting):
    bot.States.AddHeader("Traverse To Eye of the North Outpost")
    bot.Move.XY(3579.07, -22007.27)
    bot.Wait.ForTime(15000)
    bot.Dialogs.AtXY(3537.00, -21937.00, 0x839104)
    bot.Move.XY(3743.31, -15862.36)
    bot.Move.XY(8267.89, -12334.58)
    bot.Move.XY(3607.21, -6937.32)
    bot.Move.XYAndExitMap(2557.23, -275.97, target_map_id=642) #eotn_outpost_id
    


#region MAIN
selected_step = 0
filter_header_steps = True

iconwidth = 96


def _draw_texture():
    global iconwidth
    level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())

    path = "Widgets\\Config\\textures\\factions_leveler_art.png"
    size = (float(iconwidth), float(iconwidth))
    tint = (255, 255, 255, 255)
    border_col = (0, 0, 0, 0)  # <- ints, not normalized floats

    if level <= 5:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.0, 0.0),   uv1=(0.25, 1.0),
                                  tint=tint, border_color=border_col)
    elif level <= 8:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.25, 0.0), uv1=(0.5, 1.0),
                                  tint=tint, border_color=border_col)
    elif level <= 9:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.5, 0.0),  uv1=(0.75, 1.0),
                                  tint=tint, border_color=border_col)
    else:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.75, 0.0), uv1=(1.0, 1.0),
                                  tint=tint, border_color=border_col)


def _draw_settings(bot: Botting):
    import PyImGui
    PyImGui.text("Bot Settings")
    use_birthday_cupcake = bot.Properties.Get("birthday_cupcake", "active")
    bc_restock_qty = bot.Properties.Get("birthday_cupcake", "restock_quantity")

    use_honeycomb = bot.Properties.Get("honeycomb", "active")
    hc_restock_qty = bot.Properties.Get("honeycomb", "restock_quantity")

    use_birthday_cupcake = PyImGui.checkbox("Use Birthday Cupcake", use_birthday_cupcake)
    bc_restock_qty = PyImGui.input_int("Birthday Cupcake Restock Quantity", bc_restock_qty)

    use_honeycomb = PyImGui.checkbox("Use Honeycomb", use_honeycomb)
    hc_restock_qty = PyImGui.input_int("Honeycomb Restock Quantity", hc_restock_qty)

    bot.Properties.ApplyNow("birthday_cupcake", "active", use_birthday_cupcake)
    bot.Properties.ApplyNow("birthday_cupcake", "restock_quantity", bc_restock_qty)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "restock_quantity", hc_restock_qty)
    
def _draw_help():
    import PyImGui

    PyImGui.text("Bot Help")
    PyImGui.separator()

    PyImGui.text_wrapped("This bot will take your character from FACTIONS from level 1 to 10 by skipping most of the starter zone.")
    PyImGui.text_wrapped("It only completes the quests needed to hit level 10 as quickly as possible.")
    PyImGui.text_wrapped("It includes both Attribute Point Quests.")

    PyImGui.separator()
    PyImGui.text_wrapped("Because of the rushed nature of the run, you'll be fighting enemies that are much more stronger than you and your party.")
    PyImGui.text_colored("Tip: Use Birthday Cupcakes and Honeycombs to boost your survivability!", (255, 200, 0, 255))

    PyImGui.separator()
    PyImGui.text_wrapped("This script is completely standalone — no other bots are required.")
    PyImGui.text_wrapped("Make sure your Hero AI is turned OFF before you start.")

    PyImGui.separator()
    PyImGui.text_wrapped("Looting is disabled: the bot will NOT pick up any items.")
    PyImGui.text_wrapped("The entire focus is leveling speed.")

    PyImGui.separator()
    PyImGui.text_wrapped("You can restart the bot at any time - whether after an error or resuming from a previous session.")
    PyImGui.text_wrapped("Just be sure you are standing in the correct map before restarting at the matching step.")



bot.SetMainRoutine(create_bot_routine)
bot.UI.override_draw_texture(lambda: _draw_texture())
bot.UI.override_draw_config(lambda: _draw_settings(bot))
bot.UI.override_draw_help(lambda: _draw_help())


def configure():
    global bot
    bot.UI.draw_configure_window()
    
    
def main():
    global bot

    try:
        bot.Update()
        bot.UI.draw_window()

    except Exception as e:
        Py4GW.Console.Log(bot.config.bot_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()

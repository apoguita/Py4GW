from __future__ import annotations
from typing import List, Tuple, Generator, Any

from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui, ActionQueueManager)


bot = Botting("NF Leveler",
              upkeep_birthday_cupcake_restock=10,
              upkeep_honeycomb_restock=20,
              upkeep_war_supplies_restock=2,
              upkeep_auto_inventory_management_active=False,
              upkeep_auto_combat_active=False,
              upkeep_auto_loot_active=True)
 
def create_bot_routine(bot: Botting) -> None:
    # === PHASE 1: TUTORIAL AND INITIAL SETUP ===
    SkipTutorialDialog(bot)                    # Skip opening tutorial
    TravelToGuildHall(bot)                     # Go to guild hall
    ApproachJahdugar(bot)                      # Approach NPC Jahdugar
    CompleteRecruitQuiz(bot)                   # Quiz the recruits
    ConfigureFirstBattle(bot)                  # Configure first battle setup
    EnterChahbekMission(bot)                   # Enter Chahbek mission
    CompleteLearnMore(bot)                     # Learn more tutorial
    
    # === PHASE 2: INITIAL QUESTS AND PROGRESSION ===
    CompleteStorageQuests(bot)                 # Storage quests   
    ExtendInventorySpace(bot)                  # Buy bags to extend inventory
    CompleteHeroCommandQuest(bot)              # Hero command quest
    CompleteArmoredTransportQuest(bot)         # Armored transport quest
    #CompleteIdentityTheftQuest(bot)           # Identity theft quest (not working yet)
    TakeInitialQuests(bot)                     # Take initial quest set
    FarmQuestRequirements(bot)                 # Farm materials/items for quests
    CompleteSunspearGreatHallQuests(bot)       # SSGH (Sunspear Great Hall) quests
    CompleteMissingShipmentQuest(bot)          # Level 5+ Missing Shipment quest
    ContinueQuestProgression(bot)              # Continue with quest chain
    
    # === PHASE 3: PROFESSION AND CHARACTER DEVELOPMENT ===
    UnlockSecondProfession(bot)                # Unlock second profession
    ConfigureAfterSecondProfession(bot)     # Configure bot after second profession
    
    # === PHASE 4: EQUIPMENT CRAFTING ===
    if GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())[0] == "Paragon":
        CraftParagonArmor(bot)                 # Craft Paragon-specific armor
    else:
        TakeArmorRewardAndCraft(bot)           # Take reward and craft armor
    TakeWeaponRewardAndCraft(bot)              # Take reward and craft weapon
    
    # === PHASE 5: MID-GAME QUESTS AND PROGRESSION ===
    LoopFarmInJokanurDiggings(bot)
    GatherSecondSetOfAttributePoints(bot)    # Gather second set of attribute points
    UnlockSunspearSkills(bot)          # Unlock Sunspear skills
    # === PHASE 6: EYE OF THE NORTH EXPANSION ===
    TravelToEyeOfTheNorth(bot)                 # EOTN (Eye of the North) run
    ExitBorealStation(bot)                     # Exit Boreal Station
    TravelToEyeOfTheNorthOutpost(bot)          # Go to  EOTN outpost
    UnlockEyeOfTheNorthPool(bot)               # Unlock EOTN resurrection pool
    AdvanceToGunnarsHold(bot)                  # Advance to Gunnar's Hold
    UnlockKillroyStonekin(bot)
    AdvanceToLongeyeEdge(bot)
    UnlockNPCForVaettirFarm(bot)
    #AdvanceToDoomlore(bot)                   # Advance to Doomlore
    #AdvanceToSifhalla(bot)                   # Advance to Sifhalla
    #AdvanceToOlafstead(bot)                  # Advance to Olafstead
    #AdvanceToUmbralGrotto(bot)               # Advance to Umbral Grotto
    
    # === PHASE 7: FINAL UNLOCKS AND LOCATIONS ===
    UnlockConsulateDocks(bot)                  # Unlock Consulate Docks
    UnlockKainengCenter(bot)                   # Unlock KC (Kaineng Center)
    AdvanceToVizunahSquareForeignQuarter(bot)  # Advance to Vizunah Square (Foreign)
    AdvanceToMarketplaceOutpost(bot)            # Advance to Marketplace
    AdvanceToSeitungHarbor(bot)
    AdvanceToShinjeaMonastery(bot)
    AdvanceToTsumeiVillage(bot)
    AdvanceToMinisterCho(bot)                   # Advance to Minister Cho
    UnlockLionsArch(bot)                        # Unlock LA (Lion's Arch)
    UnlockRemainingSecondaryProfessions(bot)   # Unlock remaining secondary professions
    UnlockXunlaiMaterialStoragePanel(bot)
    UnlockMercenaryHeroes(bot)                  # Unlock Mercenary Heroes
#region Helpers

def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.Templates.Pacifist()
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Disable("honeycomb")
    bot.Properties.Disable("war_supplies")
    bot.Items.Restock.BirthdayCupcake()
    bot.Items.Restock.WarSupplies()
    bot.Items.Restock.Honeycomb()

def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Templates.Aggressive()
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Enable("honeycomb")
    bot.Properties.Enable("war_supplies")
    bot.Items.Restock.BirthdayCupcake()
    bot.Items.Restock.WarSupplies()
    bot.Items.Restock.Honeycomb()
    bot.Items.SpawnAndDestroyBonusItems([ModelID.Bonus_Serrated_Shield.value, ModelID.Igneous_Summoning_Stone.value])
    
    
def PrepareForBattle(bot: Botting, Hero_List = [], Henchman_List = []) -> None:
    ConfigureAggressiveEnv(bot)
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    bot.Party.AddHeroList(Hero_List)
    bot.Party.AddHenchmanList(Henchman_List)

def AddHenchmenFC():
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
        henchmen_list.extend([2,3,5,6,7,9,10])
        
    for henchman_id in henchmen_list:
        yield from _add_henchman(henchman_id)

def EquipSkillBar(): 
    global bot

    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())
    if profession == "Dervish":
        if level ==2:
           yield from Routines.Yield.Skills.LoadSkillbar("OgChkSj4V6KAGw/X7LCe8C")
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OgGjkirBbQiXSX7gDYjbaFYcCAA")    
        elif level == 6:
            yield from Routines.Yield.Skills.LoadSkillbar("OgGjkirBbQiXSX7gDYjbaFYcCAA")    
        elif level == 7:
            yield from Routines.Yield.Skills.LoadSkillbar("OgGjkirB7QiXSX7gDYjbaFYcCAA")    
        elif level == 8:
            yield from Routines.Yield.Skills.LoadSkillbar("OgGjkirCbRiXSX7gDYjbXFYcCAA")    
        elif level == 9:
            yield from Routines.Yield.Skills.LoadSkillbar("OgGjkirCbRiXSX7gDYjbXFYcCAA")    
        elif level == 10:
            yield from Routines.Yield.Skills.LoadSkillbar("OgGjkyrM7QiXSX7gDYAAAAYcCAA")
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OgGjkyrM7QiXSX7gDYAAAAYcCAA")

    elif profession == "Paragon":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OQCjUOmBqMw4HMQuCHjBAYcBAA")    
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OQCjUOmBqMw4HMQuCHjBAYcBAA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OQCjUWmCaNw4HMQuCDAAAYcBAA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGkUemyZgKEM2DmDGQ2VBQoAAGH")    
        elif level == 6:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGlUFlnpcGoDBj9g5gBkdVAEKAgxB")    
        elif level == 7:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGkUemzZgSEM2DmDGQ2VBQoAAGH")    
        elif level == 8:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGlUJlnpcGoEBj9g5gBkdVAEKAgxB")    
        elif level == 9:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGlUJlnpcGoEBj9g5gBkdVAEKAgxB")    
        elif level == 10:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGlUJlnpcGoEBj9g5gBkdVAEKAgxB")    
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGlUJlnpcGoEBj9g5gBkdVAEKAgxB")  


def GetArmorMaterialPerProfession(headpiece: bool = True) -> int:
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if primary == "Warrior":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Ranger":
        return ModelID.Tanned_Hide_Square.value
    elif primary == "Monk":
        if headpiece:
            return ModelID.Pile_Of_Glittering_Dust.value
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Dervish":
        return ModelID.Tanned_Hide_Square.value
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


def GetWeaponMaterialPerProfession(bot: Botting):
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if primary == "Warrior":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Ranger":
        return [ModelID.Wood_Plank.value]
    elif primary == "Dervish":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Paragon":
        return [ModelID.Iron_Ingot.value]
    return []

def withdraw_gold(target_gold=5000, deposit_all=True):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    if gold_on_char > target_gold and deposit_all:
        to_deposit = gold_on_char - target_gold
        GLOBAL_CACHE.Inventory.DepositGold(to_deposit)
        yield from Routines.Yield.wait(250)

    if gold_on_char < target_gold:
        to_withdraw = target_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)

def BuyMaterials():
    for _ in range(2):
        yield from Routines.Yield.Merchant.BuyMaterial(GetArmorMaterialPerProfession())

def BuyWeaponMaterials():
    materials = GetWeaponMaterialPerProfession(bot)
    if materials:
        for _ in range(1):
            yield from Routines.Yield.Merchant.BuyMaterial(materials[0])

def GetArmorPiecesByProfession(bot: Botting):
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    HEAD,CHEST,GLOVES ,PANTS ,BOOTS = 0,0,0,0,0

    if primary == "Warrior": 
        HEAD = 10046
        CHEST = 10164
        GLOVES = 10165
        PANTS = 10166
        BOOTS = 10163
    elif primary == "Dervish":
        HEAD = 17705
        CHEST = 17676
        GLOVES = 17677
        PANTS = 17678
        BOOTS = 17675

    return  HEAD, CHEST, GLOVES, PANTS, BOOTS 



def GetWeaponByProfession(bot: Botting):
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    SCYTHE = SPEAR = SHIELDWAR = SWORD = BOW = SHIELDPARA = 0

    if primary == "Warrior":
        SWORD = 18927
        SHIELDWAR = 18911
        return SWORD, SHIELDWAR
    elif primary == "Ranger":
        BOW = 18907
        return BOW,
    elif primary == "Paragon":
        SPEAR = 18913
        SHIELDPARA = 18856
        return SPEAR, SHIELDPARA
    elif primary == "Dervish":
        SCYTHE = 18910
        return SCYTHE,
    elif primary == "Elementalist":
        return ()

    return ()


def CraftArmor(bot: Botting):
    HEAD, CHEST, GLOVES, PANTS, BOOTS = GetArmorPiecesByProfession(bot)

    armor_pieces = [
        (HEAD, [GetArmorMaterialPerProfession()], [2]),
        (GLOVES, [GetArmorMaterialPerProfession()], [2]),
        (CHEST,  [GetArmorMaterialPerProfession()], [6]),
        (PANTS,  [GetArmorMaterialPerProfession()], [4]),
        (BOOTS,  [GetArmorMaterialPerProfession()], [2]),
    ]
    
    yield from Routines.Yield.Agents.InteractWithAgentXY(3944, 2378)
    yield

    for item_id, mats, qtys in armor_pieces:
        result = yield from Routines.Yield.Items.CraftItem(item_id, 75, mats, qtys)
        if not result:
            ConsoleLog("CraftArmor", f"Failed to craft item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield

        result = yield from Routines.Yield.Items.EquipItem(item_id)
        if not result:
            ConsoleLog("CraftArmor", f"Failed to equip item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True
def ParagonArmorMaterials(headpiece: bool = False):
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if primary == "Paragon":
        return ModelID.Tanned_Hide_Square.value
def GetParagonArmorPieces(bot: Botting):
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    HEAD, CHEST,GLOVES ,PANTS ,BOOTS = 0,0,0,0,0
    
    if primary == "Paragon":
        CHEST = 17791
        GLOVES = 17792
        PANTS = 17793
        BOOTS = 17790
    return  CHEST, GLOVES ,PANTS ,BOOTS


def CraftMostParaArmor(bot: Botting):
    CHEST, GLOVES, PANTS, BOOTS = GetParagonArmorPieces(bot)

    armor_pieces = [
        (GLOVES, [GetArmorMaterialPerProfession()], [2]),
        (CHEST,  [GetArmorMaterialPerProfession()], [6]),
        (PANTS,  [GetArmorMaterialPerProfession()], [4]),
        (BOOTS,  [GetArmorMaterialPerProfession()], [2]),
    ]
    
    yield from Routines.Yield.Agents.InteractWithAgentXY(3944, 2378)
    yield

    for item_id, mats, qtys in armor_pieces:
        result = yield from Routines.Yield.Items.CraftItem(item_id, 75, mats, qtys)
        if not result:
            ConsoleLog("CraftArmor", f"Failed to craft item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield

        result = yield from Routines.Yield.Items.EquipItem(item_id)
        if not result:
            ConsoleLog("CraftArmor", f"Failed to equip item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True

def CraftWeapon(bot: Botting):
    weapon_ids = GetWeaponByProfession(bot)
    materials = GetWeaponMaterialPerProfession(bot)
    
    # Structure weapon data like armor pieces - (weapon_id, materials_list, quantities_list)
    weapon_pieces = []
    for weapon_id in weapon_ids:
        weapon_pieces.append((weapon_id, materials, [1]))  # 1 = 10 materials per weapon minimum
    
    yield from Routines.Yield.Agents.InteractWithAgentXY(4101.25, 2194.41)
    yield

    for weapon_id, mats, qtys in weapon_pieces:
        result = yield from Routines.Yield.Items.CraftItem(weapon_id, 50, mats, qtys)
        if not result:
            ConsoleLog("CraftWeapon", f"Failed to craft weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield

        result = yield from Routines.Yield.Items.EquipItem(weapon_id)
        if not result:
            ConsoleLog("CraftWeapon", f"Failed to equip weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True
#region Start

def SkipTutorialDialog(bot: Botting) -> None:
    bot.States.AddHeader("Skipping Initial Tutorial Dialogs")
    bot.Move.XYAndDialog(10289, 6405, 0x82A503, step_name="Skip Tutorial Dialog 1")
    bot.Dialogs.AtXY(10289, 6405, 0x82A501, step_name="Skip Tutorial Dialog 2")  
    
def TravelToGuildHall(bot: Botting):
    bot.States.AddHeader("Phase 1: Traveling to Guild Hall")
    bot.Map.TravelGH()
    bot.Wait.ForTime(500)
    bot.Map.LeaveGH()
    bot.Wait.ForTime(5000) # Wait for cinematics to finish

def ApproachJahdugar(bot: Botting):
    bot.States.AddHeader("Phase 1: Meeting First Spear Jahdugar")
    bot.Move.XYAndDialog(3493, -5247, 0x82A507, step_name="Talk to First Spear Jahdugar")
    bot.Move.XYAndDialog(3493, -5247, 0x82C501, step_name="You can count on me")

def CompleteRecruitQuiz(bot: Botting):
    bot.States.AddHeader("Phase 1: Completing Recruit Aptitude Quiz")
    bot.Move.XY(4750, -6105, step_name="Move to Quiz NPC")
    bot.Move.XYAndDialog(4750, -6105, 0x82C504, step_name="Answer Quiz 1")
    bot.Move.XYAndDialog(5019, -6940, 0x82C504, step_name="Answer Quiz 2")
    bot.Move.XYAndDialog(3540, -6253, 0x82C504, step_name="Answer Quiz 3")
    bot.Wait.ForTime(1000)
    bot.Move.XY(3485, -5246, step_name="Return to Jahdugar")
    bot.Dialogs.AtXY(3485, -5246, 0x82C507, step_name="Accept Quest")
    bot.Move.XYAndDialog(3433, -5900, 0x82C701, step_name="My own henchmen")
    

def ConfigureFirstBattle(bot: Botting):
    bot.States.AddHeader("Phase 1: Preparing for First Battle")
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[1,2])
    def Equip_Weapon():
        global bot
        profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        if profession == "Dervish":
            bot.Items.Equip(15591)  # starter scythe
        elif profession == "Paragon":
            bot.Items.Equip(15593) 
            bot.Items.Equip(6514) #Bonus Shield
    Equip_Weapon()
    bot.Dialogs.AtXY(3433, -5900, 0x82C707, step_name="Accept")

def EnterChahbekMission(bot: Botting):
    bot.States.AddHeader("Phase 1: Entering Chahbek Village Mission")
    bot.Dialogs.AtXY(3485, -5246, 0x81)
    bot.Dialogs.AtXY(3485, -5246, 0x84)
    bot.Wait.ForTime(2000)
    bot.Wait.UntilOnExplorable()
    bot.Move.XY(2240, -3535)
    bot.Move.XY(227, -5658)
    bot.Move.XY(-1144, -4378)
    bot.Move.XY(-2058, -3494)
    bot.Move.XY(-4725, -1830)
    bot.Interact.WithGadgetAtXY(-4725, -1830) #Oil 1
    bot.Move.XY(-1725, -2551)
    bot.Wait.ForTime(1500)
    bot.Interact.WithGadgetAtXY(-1725, -2550) #Cata load
    bot.Wait.ForTime(1500)
    bot.Interact.WithGadgetAtXY(-1725, -2550) #Cata fire
    bot.Move.XY(-4725, -1830) #Back to Oil
    bot.Interact.WithGadgetAtXY(-4725, -1830) #Oil 2
    bot.Move.XY(-1731, -4138)
    bot.Interact.WithGadgetAtXY(-1731, -4138) #Cata 2 load
    bot.Wait.ForTime(2000)
    bot.Interact.WithGadgetAtXY(-1731, -4138) #Cata 2 fire
    bot.Move.XY(-2331, -419)
    bot.Move.XY(-1685, 1459)
    bot.Move.XY(-2895, -6247)
    bot.Move.XY(-3938, -6315) #Boss
    bot.Wait.ForMapToChange(target_map_id=456)

def Get_Skills():
    global bot
    ConfigurePacifistEnv(bot)
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if profession == "Dervish":
        bot.Move.XYAndDialog(-12107, -705, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)
                
    elif profession == "Paragon":
        bot.Move.XYAndDialog(-10724, -3364, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

def CompleteLearnMore(bot: Botting):
    bot.States.AddHeader("Phase 1: Learning from First Spear Dehvad")
    bot.Properties.Disable("hero_ai")
    bot.Move.XY(-7158, 4894)
    bot.Move.XYAndDialog(-7158, 4894, 0x825801, step_name="Couldn't hurt to learn")
    Get_Skills()
    bot.Move.XYAndDialog(-7139, 4891, 0x825807, step_name="Accept reward")
    bot.States.AddHeader("Phase 1: Honing Combat Skills")
    bot.Move.XYAndDialog(-7158, 4894, 0x828901, step_name="Honing your skills")
    bot.UI.CancelSkillRewardWindow()
    bot.Dialogs.AtXY(-7183, 4904, 0x828901, step_name="I'll be back in no time")
    bot.Move.XYAndDialog(-7383, 5706, 0x81, step_name="Take me to Kamadan")
    bot.Dialogs.AtXY(-7383, 5706, 0x84, step_name="Yes please")
    bot.Wait.ForMapToChange(target_map_id=449)

def CompleteStorageQuests(bot: Botting):
    bot.States.AddHeader("Phase 2: Completing Storage & Inventory Quests")
    bot.Move.XYAndDialog(-9251, 11826, 0x82A101, step_name="Storage Quest 0")
    bot.Move.XYAndDialog(-7761, 14393, 0x84, step_name="50 Gold please")
    bot.Move.XYAndDialog(-9251, 11826, 0x82A107, step_name="Accept reward")

def ExtendInventorySpace(bot: Botting):
    bot.States.AddHeader("Phase 2: Extending Inventory Space")
    bot.States.AddCustomState(withdraw_gold, "Get 5000 gold")
    bot.helpers.UI.open_all_bags()
    bot.Move.XYAndInteractNPC(-10597.11, 8742.66) # Merchant NPC in Kamadan
    bot.helpers.Merchant.buy_item(35, 1) # Buy Bag 1
    bot.Wait.ForTime(250)
    bot.helpers.Merchant.buy_item(35, 1) # Buy Bag 2
    bot.Wait.ForTime(250)
    bot.helpers.Merchant.buy_item(34, 1) # Buy Belt Pouch  
    bot.Wait.ForTime(250)
    bot.Items.MoveModelToBagSlot(34, 1, 0) # Move Belt Pouch to Bag 1 Slot 0
    bot.UI.BagItemDoubleClick(bag_id=1, slot=0) 
    bot.Wait.ForTime(500) # Wait for equip to complete
    bot.Items.MoveModelToBagSlot(35, 1, 0)
    bot.UI.BagItemDoubleClick(bag_id=1, slot=0)
    bot.Wait.ForTime(500)
    bot.Items.MoveModelToBagSlot(35, 1, 0)
    bot.UI.BagItemDoubleClick(bag_id=1, slot=0)

def CompleteArmoredTransportQuest(bot):
    bot.States.AddHeader("Phase 2: Completing Armored Transport Quest")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-11202, 9346,0x825F01) #+500xp protect quest
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-9326, 18151, target_map_id=430) # Plains of Jarin
    bot.Move.XYAndDialog(16448, 2320,0x825F04)
    bot.Move.XY(8701, 4156)
    bot.Move.XY(4176, 2800)
    bot.Wait.UntilOnCombat() #sometimes there is a stray corsair
    bot.Wait.ForTime(5000) #maybe enough time to aggro a loose mob
    bot.Move.XY(-2963, 1813)
    bot.Wait.ForTime(25000)
    #bot.Wait.UntilOnCombat()
    #bot.Wait.UntilOutOfCombat()
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-11202, 9346,0x825F07)

def IdentityTheft(bot):
    bot.States.AddHeader("Phase 2: Completing Identity Theft Quest")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-10461, 15229, 0x827201) #take quest
    bot.Map.Travel(target_map_id=479) #Champions Dawn
    bot.Move.XYAndDialog(25345, 8604, 0x827204)
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,6,7])
    bot.Move.XYAndExitMap(22483, 6115, target_map_id=432) #Cliffs of Dohjok
    bot.Move.XYAndDialog(20215, 5285, 0x85) #Blessing 
    bot.Move.XY(14429, 10337) #kill boss
    bot.Interact.WithModel(15850)#not working so comment out this quest for now
    bot.Wait.ForTime(4000)
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-10461, 15229, 0x827207) # +500xp

def CompleteHeroCommandQuest(bot):
    bot.States.AddHeader("Phase 2: Completing Hero Command Tutorial Quest")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-7874, 9799, 0x82C801)
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[3,4])
    bot.Move.XY(-4383, -2078)
    bot.Move.XYAndDialog(-7525, 6288, 0x81, step_name="Churrhir Fields")
    bot.Dialogs.AtXY(-7525, 6288, 0x84, step_name="We are ready")
    bot.Wait.ForMapToChange(target_map_id=456)
    bot.Move.XYAndDialog(-2000, -2825,0x8B) #Command Training
    bot.Party.FlagAllHeroes(1110, -4175); bot.Wait.ForTime(35000) #Flag 2
    bot.Party.FlagAllHeroes(-2362, -6126); bot.Wait.ForTime(35000) #Flag 3
    bot.Party.FlagAllHeroes(-222, -5832); bot.Wait.ForTime(7000) #Flag 1. use this order to avoid mob spawns
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-7874, 9799, 0x82C807)

def TakeInitialQuests(bot: Botting):
    bot.States.AddHeader("Phase 2: Accepting Equipment Quests")
    bot.Move.XYAndDialog(-11208, 8815, 0x826003, step_name="Quality Steel")
    bot.Dialogs.AtXY(-11208, 8815, 0x826001)
    bot.States.AddHeader("Phase 2: Taking Material Collection Quest")
    bot.Move.XYAndDialog(-11363, 9066, 0x826103, step_name="Material Girl")
    bot.Dialogs.AtXY(-11363, 9066, 0x826101)
    
def FarmQuestRequirements(bot: Botting):
    bot.States.AddHeader("Phase 2: Farming Required Materials & Items")
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.States.AddHeader("Phase 2: Farming in Plains of Jarin")
    bot.Move.XYAndExitMap(-9326, 18151, target_map_id=430) #Plains of Jarin
    #bot.Wait.ForMapToChange(target_map_id=430)
    bot.Move.XY(18460, 1002, step_name="Bounty")
    bot.Move.XYAndDialog(18460, 1002, 0x85) #Blessing 
    bot.Move.XY(9675, 1038)
    bot.Move.XYAndDialog(9282, -1199, 0x826104, step_name="Material Girl")
    bot.Wait.ForTime(2000)
    bot.Move.XY(9464, -2639, step_name="Killer Plants 1")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(11183, -7728, step_name="Killer Plants 2")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(9681, -9300, step_name="Killer Plants 3")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7555, -6791, step_name="Killer Plants 4")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(5073, -4850, step_name="Killer Plants 5")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(9292, -1220, 0x826104, step_name="Material Girl")
    bot.Move.XYAndDialog(-1782, 2790, 0x828801, step_name="Map Travel")
    bot.Move.XY(-3145, 2412)
    bot.Move.XYAndExitMap(-3236, 4503, target_map_id=431) #Sunspear Great Hall
    #bot.Wait.ForMapToChange(target_map_id=431) #don't need these anymore? the bot is wait for this 
    bot.States.AddHeader("Phase 2: Returning to Kamadan for Turn-in")
    bot.Wait.ForTime(2000)
    bot.Map.Travel(target_map_id=449) #Kamadan
    #bot.Wait.ForMapToChange(target_map_id=449)
    bot.Move.XYAndDialog(-10024, 8590, 0x828804, step_name="Map Travel Inventor")
    bot.Dialogs.AtXY(-10024, 8590, 0x828807)
    bot.Move.XYAndDialog(-11356, 9066, 0x826107, step_name="accept reward")
    bot.Wait.ForTime(2000)
   
def CompleteSunspearGreatHallQuests(bot: Botting):
    bot.States.AddHeader("Phase 2: Completing Sunspear Great Hall Quests")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    #bot.Wait.ForMapToChange(target_map_id=431) # no longer needed
    bot.Move.XYAndDialog(-4076, 5362, 0x826004, step_name="Quality Steel")
    bot.Move.XYAndDialog(-2888, 7024, 0x84, step_name="SS rebirth Signet")
    bot.Dialogs.AtXY(-2888, 7024, 0x82CB03, step_name="Attribute Points Quest 1")
    bot.Dialogs.AtXY(-2888, 7024, 0x82CB01)
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    #bot.Wait.ForMapToChange(target_map_id=430)
    bot.States.AddHeader("Phase 2: Second Plains of Jarin Farming Run")
    bot.Move.XYAndDialog(-1237.25, 3188.38, 0x85) #Blessing 
    bot.Move.XY(-3225, 1749)
    bot.Move.XY(-995, -2423) #fight
    bot.Move.XY(-513, 67) #fight more
    bot.Wait.UntilOutOfCombat()
    bot.Map.Travel(target_map_id=449) #Kamadan
    #bot.Wait.ForMapToChange(target_map_id=449)
    bot.Move.XYAndDialog(-11208, 8815, 0x826007, step_name="Accept reward")
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar") # Level 4 skill bar

def CompleteMissingShipmentQuest(bot):
    bot.States.AddHeader("Phase 2: Completing Missing Shipment Quest")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-10235, 16557, 0x827501) #need the ink crate
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[2,3,4])
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    bot.Move.XY(-3128, 2037)
    bot.Move.XY(-7005, 2178)
    bot.Move.XY(-9360, 16311) #gets me in range
    bot.Interact.WithGadgetID(7458)
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-10235, 16557, 0x827507) # +500xp +30 health rune
    #bot.Items.Equip(898) #didn't work
            
def ContinueQuestProgression(bot: Botting): 
    bot.States.AddHeader("Phase 2: Continuing Main Quest Progression")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    #bot.Wait.ForMapToChange(target_map_id=431)
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    #bot.Wait.ForMapToChange(target_map_id=430)
    bot.Move.XYAndDialog(-1237.25, 3188.38, 0x85) #Blessing 
    bot.Move.XY(-4507, 616)
    bot.Move.XY(-7611, -5953)
    bot.Move.XY(-18083, -11907) 
    bot.Move.XYAndExitMap(-19518, -13021, target_map_id=479) #unlockChampions Dawn
    #bot.Wait.ForMapToChange(target_map_id=479)
    bot.States.AddHeader("Phase 2: Third Sunspear Great Hall Visit")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    #bot.Wait.ForMapToChange(target_map_id=431)
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,2,4])
    bot.Move.XYAndDialog(-1835, 6505, 0x825A01, step_name="A Hidden Threat")
    bot.Move.XYAndDialog(-4358, 6535, 0x829301, step_name="Proof of Courage")
    bot.Move.XYAndDialog(-4558, 4693, 0x826201, step_name="Suwash the Pirate")
    bot.States.AddHeader("Phase 2: Third Plains of Jarin Exploration")
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    #bot.Wait.ForMapToChange(target_map_id=430)
    bot.Move.XYAndDialog(-1237.25, 3188.38, 0x85) #Blessing 
    bot.Move.XY(-3972, 1703) #proof of courage
    bot.Move.XY(-6784, -3484)
    bot.Wait.UntilOutOfCombat()
    bot.Interact.WithGadgetAtXY(-6418, -3759) #Corsair Chest
    bot.Wait.ForTime(2000)
    bot.Move.XY(-5950, -6889) #Suwash the Pirate 1
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-10278, -7011) #Suwash the Pirate 2
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-10581, -11798) #Suwash the Pirate 3
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(-16795, -12217, 0x85) #plant blessing
    bot.Move.XY(-15896, -10190) #Suwash the Pirate 4
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(-15573, -9638, 0x826204, step_name="Suwash the Pirate complete")
    bot.Move.XY(-13230, -148) #A Hidden Threat 1
    bot.Move.XY(-16920, 746) #A Hidden Threat 2
    bot.Move.XY(-17706, 3259)
    bot.Move.XYAndDialog(-17706, 3259, 0x85) #Blessing 
    bot.Wait.ForTime(2000)
    bot.Move.XY(-19751, 8180) # some more free xp
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-17673, 11492) #A Hidden Threat 3
    bot.Move.XY(-18751, 14973) #A Hidden Threat 4
    bot.Move.XY(-17535.23, 18600) #A Hidden Threat 5
    bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndExitMap(-20136, 16757, target_map_id=502) #The Astralarium
    #bot.Wait.ForMapToChange(target_map_id=502)
    bot.States.AddHeader("Phase 2: Visiting The Astralarium")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    #bot.Wait.ForMapToChange(target_map_id=431)
    bot.Move.XYAndDialog(-4367, 6542, 0x829307, step_name="Proof of Courage Reward")
    bot.Move.XYAndDialog(-4558, 4693, 0x826207, step_name="Suwash the Pirate reward")
    bot.Move.XYAndDialog(-1835, 6505, 0x825A07, step_name="A Hidden Threat reward")
    bot.Wait.ForTime(2000)

def UnlockSecondProfession(bot: Botting):  
    bot.States.AddHeader("Phase 3: Unlocking Second Profession")
    bot.Map.Travel(target_map_id=449) #Kamadan
    bot.Party.LeaveParty()
    bot.Move.XYAndDialog(-7910, 9740, 0x828907, step_name="Honing Your Skills complete")
    bot.Dialogs.AtXY(-7910, 9740, 0x825901, step_name="Secondary Training")
    bot.Move.XYAndDialog(-7525, 6288, 0x81, step_name="Churrhir Fields")
    bot.Dialogs.AtXY(-7525, 6288, 0x84, step_name="We are ready")
    bot.Wait.ForMapToChange(target_map_id=456) #need this to establish a path
    ConfigurePacifistEnv(bot)
    bot.Move.XYAndDialog(-6557.00, 1837, 0x7F, step_name="Closest Trainer Possible") #this is fine, need minimal skill bar for level 4 to avoid skill equip window
    bot.Move.XYAndDialog(-7161, 4808, 0x825907, step_name="Secondary Training complete")
    bot.Dialogs.AtXY(-7161, 4808, 0x88, step_name="Warrior 2nd Profession") #change to Warrior
    bot.Dialogs.AtXY(-7161, 4808, 0x825407, step_name="Accept")
    bot.Dialogs.AtXY(-7161, 4808, 0x827801, step_name="Right Away")

def ConfigureAfterSecondProfession(bot: Botting):    
    bot.States.AddHeader("Phase 3: Claiming 15 Attribute Points")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForMapToChange(target_map_id=431)
    bot.Move.XYAndDialog(-2864, 7031, 0x82CB07, step_name="Accept Attribute Points")
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if profession == "Dervish":
        bot.Move.XYAndDialog(-3317, 7053, 0x883B03, step_name="Learn Whirlwind Attack")
        bot.Dialogs.AtXY(-3317, 7053, 0x86E302, step_name="Learn Zealous Renewal")
    elif profession == "Paragon":
        bot.Move.XYAndDialog(-3317, 7053, 0x884003, step_name="Learn There's Nothing to Fear")
        bot.Dialogs.AtXY(-3317, 7053, 0x860E02, step_name="Learn Unblockable Throw")    
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Dialogs.AtXY(-2864, 7031, 0x82CC03, step_name='Rising to 1st Spear')
    bot.Dialogs.AtXY(-2864, 7031, 0x82CC01, step_name="Sounds good to me")
    bot.States.AddHeader("Phase 3: Starting Leaving A Legacy Quest")
    bot.Map.Travel(target_map_id=479) #Champions Dawn
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,2,7])
    bot.Move.XYAndDialog(22884, 7641, 0x827804)
    bot.Move.XYAndExitMap(22483, 6115, target_map_id=432) #Cliffs of Dohjok
    bot.Move.XY(20215, 5285)
    bot.Move.XYAndDialog(20215, 5285, 0x85) #Blessing 
    bot.Wait.ForTime(2000)
    bot.Move.XYAndDialog(18008, 6024, 0x827804) #Dunkoro
    bot.Move.XY(13677, 6800)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7255, 5150)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-13255, 6535)
    bot.Dialogs.AtXY(-13255, 6535, 0x84, step_name="Let's Go!") #Hamar
    bot.Move.XY(-11211, 5204)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-11572, 3116)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-11532, 583)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-10282, -4254)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-6608, -711)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-25149, 12787)
    bot.Move.XYAndExitMap(-27657, 14482, target_map_id=491) #Jokanur Diggings
    bot.States.AddHeader("Phase 3: Completing Jokanur Diggings Legacy Quest")
    bot.Move.XYAndDialog(2888, 2207, 0x827807, step_name="Leaving A Legacy complete")
    bot.Dialogs.AtXY(2888, 2207, 0x827901, step_name="Sounds Like Fun")


def TakeArmorRewardAndCraft(bot: Botting):
    bot.States.AddHeader("Phase 4: Taking Armor Reward & Crafting Equipment")
    bot.Move.XYAndInteractNPC(3857.42, 1700.62)  # Material merchant
    bot.States.AddCustomState(BuyMaterials, "Buy Materials")
    bot.Move.XYAndInteractNPC(3891.62, 2329.84)  # Armor crafter
    bot.Wait.ForTime(1000)  # small delay to let the window open
    exec_fn = lambda: CraftArmor(bot)
    bot.States.AddCustomState(exec_fn, "Craft Armor")

def CraftParagonArmor(bot: Botting):
    bot.States.AddHeader("Phase 4: Crafting Paragon-Specific Armor")
    bot.Move.XYAndInteractNPC(3857.42, 1700.62)  # Material merchant
    bot.States.AddCustomState(BuyMaterials, "Buy Materials")
    bot.Move.XYAndInteractNPC(3891.62, 2329.84)  # Armor crafter
    bot.Wait.ForTime(1000)  # small delay to let the window open
    exec_fn = lambda: CraftMostParaArmor(bot)
    bot.States.AddCustomState(exec_fn, "Craft Most Para Armor")

def TakeWeaponRewardAndCraft(bot: Botting):
    bot.States.AddHeader("Phase 4: Taking Weapon Reward & Crafting Weapons")
    bot.Move.XYAndInteractNPC(3857.42, 1700.62)  # Material merchant
    bot.States.AddCustomState(BuyWeaponMaterials, "Buy Weapon Materials")
    bot.Move.XY(4108.39, 2211.65)
    bot.Dialogs.WithModel(4727, 0x86)  # Weapon crafter
    bot.Wait.ForTime(1000)  # small delay to let the window open
    exec_fn = lambda: CraftWeapon(bot)
    bot.States.AddCustomState(exec_fn, "Craft Weapon")

def LoopFarmInJokanurDiggings(bot):
    bot.States.AddHeader(f"Farm_loop")
    for _ in range (16):
        bot.Map.Travel(target_map_id=491) #Jokanur Diggings
        bot.Party.LeaveParty()
        PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,2,7])
        bot.Move.FollowPath([
        (1268, -311),
        (-1618, -783),
        (-2600, -1119),
        (-3546, -1444)
        ])
        bot.Wait.ForMapLoad(target_map_id=481) # Fahranur The First City
        bot.Move.XYAndDialog(19651, 12237, 0x85) # Blessing
        bot.Move.XY(11182, 14880); bot.Wait.UntilOutOfCombat()
        bot.Move.XY(11543, 6466);  bot.Wait.UntilOutOfCombat()
        bot.Move.XY(15193, 5918);  bot.Wait.UntilOutOfCombat()
        bot.Move.XY(14485, 16);    bot.Wait.UntilOutOfCombat()
        bot.Move.XY(10256, -1393); bot.Wait.UntilOutOfCombat()
        bot.Move.XYAndDialog(11238, -2718, 0x85) # Bounty
        bot.Move.XY(13382, -6837); bot.Wait.UntilOutOfCombat()

def GatherSecondSetOfAttributePoints(bot: Botting):
    bot.States.AddHeader("Phase 5: Gathering 15 second set of attribute points")
    bot.States.AddCustomState(lambda: None, "SecondAttPoints_JumpHere")
    bot.Map.Travel(target_map_id=431) # Sunspear Great Hall
    bot.Move.XYAndDialog(-2864, 7031, 0x82CC07, step_name="15 more Attribute points")
    bot.Wait.ForTime(2000)

def UnlockSunspearSkills(bot: Botting):
    bot.States.AddHeader("Phase 5: Unlocking Sunspear Skills")
    bot.Map.Travel(target_map_id=431) # Sunspear Great Hall
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x801101) # Sunspear Skills Trainer
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x883503) # Learn Sunspear Assassin Skill
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x883603) # Learn Sunspear Mesmer Skill
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x883703) # Learn Sunspear Necromancer Skill
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x883803) # Learn Sunspear Elementalist Skill
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x883903) # Learn Sunspear Monk Skill
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x883B03) # Learn Sunspear Warrior Skill
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x883C03) # Learn Sunspear Ranger Skill
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x883D03) # Learn Sunspear Dervish Skill
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x883E03) # Learn Sunspear Ritualist Skill
    bot.Dialogs.AtXY(-3307.00, 6997.56, 0x884003) # Learn Sunspear Paragon Skill








def TravelToEyeOfTheNorth(bot: Botting): 
    bot.States.AddHeader("Phase 6: Starting Eye of the North Journey")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])

    bot.Move.XYAndDialog(-8739, 14200,0x833601) # Bendah
    bot.Move.XYAndExitMap(-9326, 18151, target_map_id=430) # Plains of Jarin

    bot.Move.XYAndDialog(18191, 167, 0x85) # get Mox
    bot.Move.XY(15407, 209)
    bot.Move.XYAndDialog(13761, -13108, 0x86) # Explore The Fissure
    bot.Move.XYAndDialog(13761, -13108, 0x84) # Yes
    bot.Wait.ForTime(5000) # load time

    bot.Move.XY(-5475, 8166);  bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-454, 10163);  bot.Wait.UntilOutOfCombat()
    bot.Move.XY(4450, 10950);  bot.Wait.UntilOutOfCombat()
    bot.Move.XY(8435, 14378)
    bot.Move.XY(10134,16742)
    bot.Wait.ForTime(3000) # skip movie

    ConfigurePacifistEnv(bot)

    bot.Move.XY(4523.25, 15448.03)
    bot.Move.XY(-43.80, 18365.45)
    bot.Move.XY(-10234.92, 16691.96)
    bot.Move.XY(-17917.68, 18480.57)
    bot.Move.XY(-18775, 19097)
    bot.Wait.ForTime(8000)
    bot.Wait.ForMapLoad(target_map_id=675)  # Boreal Station
    
def ExitBorealStation(bot: Botting):
    bot.States.AddHeader("Phase 6: Exiting Boreal Station")
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    bot.Move.XYAndExitMap(4684, -27869, target_map_name="Ice Cliff Chasms")
    
def TravelToEyeOfTheNorthOutpost(bot: Botting): 
    bot.States.AddHeader("Phase 6: Traveling to Eye of the North Outpost")
    bot.Move.XY(3579.07, -22007.27)
    bot.Wait.ForTime(15000)
    bot.Dialogs.AtXY(3537.00, -21937.00, 0x839104)
    bot.Move.XY(3743.31, -15862.36)
    bot.Move.XY(8267.89, -12334.58)
    bot.Move.XY(3607.21, -6937.32)
    bot.Move.XY(2557.23, -275.97) #eotn_outpost_id
    bot.Wait.ForMapLoad(target_map_id=642)

def UnlockEyeOfTheNorthPool(bot: Botting):
    bot.States.AddHeader("Phase 6: Unlocking Eye of the North Resurrection Pool")
    bot.Map.Travel(target_map_id=642)  # eotn_outpost_id
    auto_path_list = [(-4416.39, 4932.36), (-5198.00, 5595.00)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForMapLoad(target_map_id=646)  # hall of monuments id
    bot.Move.XY(-6572.70, 6588.83)
    bot.Dialogs.WithModel(5970, 0x800001) #eotn_pool_cinematic
    bot.Wait.ForTime(1000)
    bot.Dialogs.WithModel(5908, 0x630) #eotn_pool_cinematic
    bot.Wait.ForTime(1000)
    bot.Dialogs.WithModel(5908, 0x632) #eotn_pool_cinematic
    bot.Wait.ForTime(1000)
    bot.Wait.ForMapToChange(target_map_id=646)  # hall of monuments id
    bot.Dialogs.WithModel(5970, 0x89) #gwen dialog
    bot.Dialogs.WithModel(5970, 0x831904) #gwen dialog
    bot.Move.XYAndDialog(-6133.41, 5717.30, 0x838904) #ogden dialog
    bot.Move.XYAndDialog(-5626.80, 6259.57, 0x839304) #vekk dialog

def AdvanceToGunnarsHold(bot: Botting):
    bot.States.AddHeader("Phase 6: Advancing to Gunnar's Hold Outpost")
    bot.Map.Travel(target_map_id=642) # eotn_outpost_id
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    
    # Follow outpost exit path
    path = [(-1814.0, 2917.0), (-964.0, 2270.0), (-115.0, 1677.0), (718.0, 1060.0), 
            (1522.0, 464.0)]
    bot.Move.FollowPath(path)
    bot.Wait.ForMapLoad(target_map_id=499)  # Ice Cliff Chasms
    
    # Traverse through Ice Cliff Chasms
    bot.Move.XYAndDialog(2825, -481, 0x832801)  # Talk to Jora
    path = [(2548.84, 7266.08),
            (1233.76, 13803.42),
            (978.88, 21837.26),
            (-4031.0, 27872.0),]
    bot.Move.FollowAutoPath(path)
    bot.Wait.ForMapLoad(target_map_id=548)  # Norrhart Domains
 
    # Traverse through Norrhart Domains
    bot.Move.XY(14546.0, -6043.0)
    bot.Move.XYAndExitMap(15578, -6548, target_map_id=644)  # Gunnar's Hold
    bot.Wait.ForMapLoad(target_map_id=644)  # Gunnar's Hold
    
def UnlockKillroyStonekin(bot: Botting):
    bot.States.AddHeader("Phase 6: Unlocking Killroy Stonekin Dungeon")
    bot.Map.Travel(target_map_id=644)  # gunnars_hold_id
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x835A01)
    bot.Dialogs.AtXY(17341.00, -4796.00, 0x84)
    bot.Wait.ForMapLoad(target_map_id=703)  # killroy_map_id
    bot.Templates.Aggressive(enable_imp=False)
    bot.Items.Equip(24897) #brass_knuckles_item_id
    bot.Move.XY(19290.50, -11552.23)
    bot.Wait.UntilOnOutpost()
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x835A07)  # take reward
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if profession == "Dervish":
        bot.Items.Equip(18910) #crafted Scythe
    elif profession == "Paragon":
        bot.Items.Equip(18913)
def AdvanceToLongeyeEdge(bot: Botting):
    bot.States.AddHeader("Phase 6: Advancing to Longeye's Edge")
    bot.Map.Travel(target_map_id=644) # Gunnar's Hold
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    
    # Exit Gunnar's Hold outpost
    bot.Move.XY(15886.204101, -6687.815917)
    bot.Move.XY(15183.199218, -6381.958984)
    bot.Wait.ForMapLoad(target_map_id=548)  # Norrhart Domains
    
    # Traverse through Norrhart Domains to Bjora Marches
    bot.Move.XY(14233.820312, -3638.702636)
    bot.Move.XY(14944.690429,  1197.740966)
    bot.Move.XY(14855.548828,  4450.144531)
    bot.Move.XY(17964.738281,  6782.413574)
    bot.Move.XY(19127.484375,  9809.458984)
    bot.Move.XY(21742.705078, 14057.231445)
    bot.Move.XY(19933.869140, 15609.059570)
    bot.Move.XY(16294.676757, 16369.736328)
    bot.Move.XY(16392.476562, 16768.855468)
    bot.Wait.ForMapLoad(target_map_id=482)  # Bjora Marches
    
    # Traverse through Bjora Marches to Longeyes Ledge
    bot.Move.XY(-11232.550781, -16722.859375)
    bot.Move.XY(-7655.780273 , -13250.316406)
    bot.Move.XY(-6672.132324 , -13080.853515)
    bot.Move.XY(-5497.732421 , -11904.576171)
    bot.Move.XY(-3598.337646 , -11162.589843)
    bot.Move.XY(-3013.927490 ,  -9264.664062)
    bot.Move.XY(-1002.166198 ,  -8064.565429)
    bot.Move.XY( 3533.099609 ,  -9982.698242)
    bot.Move.XY( 7472.125976 , -10943.370117)
    bot.Move.XY(12984.513671 , -15341.864257)
    bot.Move.XY(17305.523437 , -17686.404296)
    bot.Move.XY(19048.208984 , -18813.695312)
    bot.Move.XY(19634.173828, -19118.777343)
    bot.Wait.ForMapLoad(target_map_id=650)  # Longeyes Ledge

def UnlockNPCForVaettirFarm(bot: Botting):
    bot.States.AddHeader("Unlocking NPC for Vaettir Farm")
    bot.Map.Travel(target_map_id=650)  # longeyes_ledge_id
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    bot.Move.XYAndExitMap(-26375, 16180, target_map_name="Bjora Marches")
    path_points_to_traverse_bjora_marches: List[Tuple[float, float]] = [
    (17810, -17649),(17516, -17270),(17166, -16813),(16862, -16324),(16472, -15934),
    (15929, -15731),(15387, -15521),(14849, -15312),(14311, -15101),(13776, -14882),
    (13249, -14642),(12729, -14386),(12235, -14086),(11748, -13776),(11274, -13450),
    (10839, -13065),(10572, -12590),(10412, -12036),(10238, -11485),(10125, -10918),
    (10029, -10348),(9909, -9778)  ,(9599, -9327)  ,(9121, -9009)  ,(8674, -8645)  ,
    (8215, -8289)  ,(7755, -7945)  ,(7339, -7542)  ,(6962, -7103)  ,(6587, -6666)  ,
    (6210, -6226)  ,(5834, -5788)  ,(5457, -5349)  ,(5081, -4911)  ,(4703, -4470)  ,
    (4379, -3990)  ,(4063, -3507)  ,(3773, -3031)  ,(3452, -2540)  ,(3117, -2070)  ,
    (2678, -1703)  ,(2115, -1593)  ,(1541, -1614)  ,(960, -1563)   ,(388, -1491)   ,
    (-187, -1419)  ,(-770, -1426)  ,(-1343, -1440) ,(-1922, -1455) ,(-2496, -1472) ,
    (-3073, -1535) ,(-3650, -1607) ,(-4214, -1712) ,(-4784, -1759) ,(-5278, -1492) ,
    (-5754, -1164) ,(-6200, -796)  ,(-6632, -419)  ,(-7192, -300)  ,(-7770, -306)  ,
    (-8352, -286)  ,(-8932, -258)  ,(-9504, -226)  ,(-10086, -201) ,(-10665, -215) ,
    (-11247, -242) ,(-11826, -262) ,(-12400, -247) ,(-12979, -216) ,(-13529, -53)  ,
    (-13944, 341)  ,(-14358, 743)  ,(-14727, 1181) ,(-15109, 1620) ,(-15539, 2010) ,
    (-15963, 2380) ,(-18048, 4223 ), (-19196, 4986),(-20000, 5595) ,(-20300, 5600)
    ]
    bot.Move.FollowPathAndExitMap(path_points_to_traverse_bjora_marches, target_map_name="Jaga Moraine")
    bot.Move.XY(13372.44, -20758.50)
    bot.Dialogs.AtXY(13367, -20771,0x84)
    bot.Wait.UntilOutOfCombat()
    bot.Dialogs.AtXY(13367, -20771,0x84)
    bot.Map.Travel(target_map_id=650)
    bot.Party.LeaveParty()

def AdvanceToDoomlore(bot: Botting):
    bot.States.AddHeader("Phase 6: Advancing to Doomlore")
    bot.Map.Travel(target_map_id=650) # Longeyes Ledge
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    
    # Exit Longeyes Ledge outpost
    bot.Move.XY(-22469.261718, 13327.513671)
    bot.Move.XY(-21791.328125, 12595.533203)
    bot.Wait.ForMapLoad(target_map_id=649)  # Grothmar Wardowns
    
    # Traverse through Grothmar Wardowns to Dalada Uplands
    bot.Move.XY(-18582.023437, 10399.527343)
    bot.Move.XY(-13987.378906, 10078.552734)
    bot.Move.XY(-10700.551757,  9980.495117)
    bot.Move.XY( -7340.849121,  9353.873046)
    bot.Move.XY( -4436.997070,  8518.824218)
    bot.Move.XY( -0445.930755,  8262.403320)
    bot.Move.XY(  3324.289062,  8156.203613)
    bot.Move.XY(  7149.326660,  8494.817382)
    bot.Move.XY( 11733.867187,  7774.760253)
    bot.Move.XY( 15031.326171,  9167.790039)
    bot.Move.XY( 18174.601562, 10689.784179)
    bot.Move.XY( 20369.773437, 12352.750000)
    bot.Move.XY( 22427.097656, 14882.499023)
    bot.Move.XY( 24355.289062, 15175.175781)
    bot.Move.XY( 25188.230468, 15229.357421)
    bot.Wait.ForMapLoad(target_map_id=647)  # Dalada Uplands
    
    # Traverse through Dalada Uplands to Doomlore Shrine
    bot.Move.XY(-16292.620117,  -715.887329)
    bot.Move.XY(-13617.916992,   405.243469)
    bot.Move.XY(-13256.524414,  2634.142089)
    bot.Move.XY(-15958.702148,  6655.416015)
    bot.Move.XY(-14465.992187,  9742.127929)
    bot.Move.XY(-13779.127929, 11591.517578)
    bot.Move.XY(-14929.544921, 13145.501953)
    bot.Move.XY(-15581.598632, 13865.584960)
    bot.Wait.ForMapLoad(target_map_id=655)  # Doomlore Shrine

def AdvanceToSifhalla(bot: Botting):
    bot.States.AddHeader("Phase 6: Advancing to Sifhalla")
    bot.Map.Travel(target_map_id=644) # Gunnar's Hold
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    
    # Exit Gunnar's Hold outpost
    bot.Move.XY(16003.853515, -6544.087402)
    bot.Move.XY(15193.037109, -6387.140625)
    bot.Wait.ForMapLoad(target_map_name="Norrhart Domains")
    
    # Traverse through Norrhart Domains to Drakkar Lake
    bot.Move.XY(13337.167968, -3869.252929)
    bot.Move.XY( 9826.771484,   416.337768)
    bot.Move.XY( 6321.207031,  2398.933349)
    bot.Move.XY( 2982.609619,  2118.243164)
    bot.Move.XY(  176.124359,  2252.913574)
    bot.Move.XY( -3766.605468,  3390.211669)
    bot.Move.XY( -7325.385253,  2669.518066)
    bot.Move.XY( -9555.996093,  5570.137695)
    bot.Move.XY(-14153.492187,  5198.475585)
    bot.Move.XY(-18538.169921,  7079.861816)
    bot.Move.XY(-22717.630859,  8757.812500)
    bot.Move.XY(-25531.134765, 10925.241210)
    bot.Move.XY(-26333.171875, 11242.023437)
    bot.Wait.ForMapLoad(target_map_name="Drakkar Lake")
    
    # Traverse through Drakkar Lake to Sifhalla
    bot.Move.XY(14399.201171, -16963.455078)
    bot.Move.XY(12510.431640, -13414.477539)
    bot.Move.XY(12011.655273,  -9633.283203)
    bot.Move.XY(11484.183593,  -5569.488769)
    bot.Move.XY(12456.843750,  -0411.864135)
    bot.Move.XY(13398.728515,   4328.439453)
    bot.Move.XY(14000.825195,   8676.782226)
    bot.Move.XY(14210.789062,  12432.768554)
    bot.Move.XY(13846.647460,  15850.121093)
    bot.Move.XY(13595.982421,  18950.578125)
    bot.Move.XY(13567.612304,  19432.314453)
    bot.Wait.ForMapLoad(target_map_name="Sifhalla")

def AdvanceToOlafstead(bot: Botting):
    bot.States.AddHeader("Phase 6: Advancing to Olafstead")
    bot.Map.Travel(target_map_id=643) # Sifhalla
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    
    # Exit Sifhalla outpost
    bot.Move.XY(13510.718750, 19647.238281)
    bot.Move.XY(13596.396484, 19212.427734)
    bot.Wait.ForMapLoad(target_map_name="Drakkar Lake")
    
    # Traverse through Drakkar Lake to Varajar Fells
    bot.Move.XY(13946, 14286)
    bot.Move.XY(13950, 2646)
    bot.Move.XY(10394, -3824)
    bot.Move.XY(-11019,-26164)
    bot.Wait.ForMapLoad(target_map_id=553)  # Varajar Fells
    
    # Traverse through Varajar Fells to Olafstead
    bot.Move.XY( -1605.245239, 12837.257812)
    bot.Move.XY( -2047.884399,  8718.327148)
    bot.Move.XY( -2288.647216,  4162.530273)
    bot.Move.XY( -3639.192138,  1637.482666)
    bot.Move.XY( -4178.047851, -2814.842773)
    bot.Move.XY( -4118.485107, -4432.247070)
    bot.Move.XY( -3315.862060, -1716.598754)
    bot.Move.XY( -1648.331054,  1095.387329)
    bot.Move.XY( -1196.614624,  1241.174560)
    bot.Wait.ForMapLoad(target_map_name="Olafstead")

def AdvanceToUmbralGrotto(bot: Botting):
    bot.States.AddHeader("Phase 6: Advancing to Umbral Grotto")
    bot.Map.Travel(target_map_id=645) # Olafstead
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    
    # Exit Olafstead outpost
    bot.Move.XY(-883.285644, 1212.171020)
    bot.Move.XY(-1452.154785, 1177.976684)
    bot.Wait.ForMapLoad(target_map_id=553)
    
    # Traverse through Varajar Fells to Verdant Cascades
    bot.Move.XY(-3127.843261, -2462.838867)
    bot.Move.XY(-4055.151855, -4363.498046)
    bot.Move.XY(-6962.863769, -3716.343017)
    bot.Move.XY(-11109.900390, -5252.222167)
    bot.Move.XY(-14969.330078, -6789.452148)
    bot.Move.XY(-19738.699218, -9123.355468)
    bot.Move.XY(-22088.320312,-10958.295898)
    bot.Move.XY(-24810.935546,-12084.257812)
    bot.Move.XY(-25980.177734,-13108.872070)
    bot.Wait.ForMapLoad(target_map_name="Verdant Cascades")
    
    # Traverse through Verdant Cascades to Umbral Grotto
    bot.Move.XY(22595.748046, 12731.708984)
    bot.Move.XY(18976.330078, 11093.851562)
    bot.Move.XY(15406.838867,  7549.499023)
    bot.Move.XY(13416.123046,  4368.934570)
    bot.Move.XY(13584.649414,   156.471313)
    bot.Move.XY(14162.473632, -1488.160766)
    bot.Move.XY(13519.756835, -3782.271240)
    bot.Move.XY(11266.111328, -4884.791992)
    bot.Move.XY( 7803.414550, -2783.716552)
    bot.Move.XY( 6404.752441,  1633.880249)
    bot.Move.XY( 6022.716796,  4174.048828)
    bot.Move.XY( 3498.960205,  7248.467773)
    bot.Move.XY(   49.460727,  6212.630371)
    bot.Move.XY(-2800.293701,  4795.620117)
    bot.Move.XY(-5035.972167,  2443.692382)
    bot.Move.XY(-7242.780273,  1866.100219)
    bot.Move.XY(-8373.044921,  2405.973632)
    bot.Move.XY(-11243.640625, 3636.515625)
    bot.Move.XY(-14829.459960, 4882.503417)
    bot.Move.XY(-18093.113281, 5579.701660)
    bot.Move.XY(-20726.955078, 5951.445312)
    bot.Move.XY(-22423.933593, 6339.730468)
    bot.Move.XY(-22984.621093, 6892.540527)
    bot.Wait.ForMapLoad(target_map_name="Umbral Grotto")  

def UnlockConsulateDocks(bot: Botting):
    bot.States.AddHeader("Phase 7: Unlocking Consulate Docks Outpost")
    bot.Map.Travel(target_map_id=449)
    bot.Wait.ForMapLoad(target_map_id=449)  # Kamadan
    bot.Move.XY(-8075.89, 14592.47)
    #bot.Move.XY(-7644.99, 15526.14)
    bot.Move.XY(-6743.29, 16663.21)
    bot.Move.XY(-5271.00, 16740.00)
    bot.Wait.ForMapLoad(target_map_id=429)
    bot.Move.XYAndDialog(-4631.86, 16711.79, 0x85)
    bot.Wait.ForMapToChange(target_map_id=493)  # Consulate Docks

def UnlockKainengCenter(bot: Botting):
    bot.States.AddHeader("Phase 7: Unlocking Kaineng Center Outpost")
    bot.Map.Travel(target_map_id=493)  # Consulate Docks
    bot.Wait.ForMapLoad(target_map_id=493)
    bot.Move.XYAndDialog(-2546.09, 16203.26, 0x88)
    bot.Wait.ForMapToChange(target_map_id=290)
    bot.Move.XY(-4230.84, 8008.28)
    bot.Move.XYAndDialog(-5134.16, 7004.48, 0x817901)
    bot.Map.Travel(target_map_id=194)  # KC
    bot.Wait.ForMapLoad(target_map_id=194)

def AdvanceToVizunahSquareForeignQuarter(bot: Botting):
    bot.States.AddHeader("Phase 7: Advancing to Vizunah Square Foreign Quarter")
    bot.Map.Travel(target_map_id=194)
    PrepareForBattle(bot)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AddHenchmenFC, "Add Henchmen")
    bot.Move.XY(3045, -1575)
    bot.Move.XY(3007, -2609)
    bot.Move.XY(2909, -3629)
    bot.Move.XY(3145, -4643)
    bot.Move.XY(3372, -5617)
    bot.Wait.ForMapLoad(target_map_id=240)
    bot.Properties.Enable("birthday_cupcake")
    bot.Move.XY(-6748, 19737)
    bot.Move.XY(-5917, 17893)
    bot.Move.XY(-4466, 16485)
    bot.Move.XY(-2989, 15105)
    bot.Move.XY(-1593, 13615)
    bot.Move.XY(-231, 12109)
    bot.Move.XY(938, 10443)
    bot.Move.XY(1282, 8408)
    bot.Move.XY(2057, 6514)
    bot.Move.XY(4042, 6223)
    bot.Move.XY(6052, 5848)
    bot.Move.XY(7924, 5071)
    bot.Move.XY(8211, 3045)
    bot.Move.XY(6473, 1948)
    bot.Move.XY(4437, 1648)
    bot.Move.XY(3380, -104)
    bot.Move.XY(5321, -696)
    bot.Move.XY(5583, -2684)
    bot.Move.XY(7584, -2703)
    bot.Move.XY(9404, -1817)
    bot.Move.XY(11278, -1107)
    bot.Move.XY(11311, 958)
    bot.Move.XY(11415, 2975)
    bot.Move.XY(12366.46, 5069.94)
    bot.Dialogs.WithModel(3228, 0x800009)
    bot.Dialogs.WithModel(3228, 0x80000B)  # talk to the guard
    bot.Wait.ForMapToChange(target_map_id=292) #Vizunah Square Foreign

def AdvanceToMarketplaceOutpost(bot: Botting):
    bot.States.AddHeader("Phase 7: Advancing to The Marketplace Outpost")
    bot.Map.Travel(target_map_id=194)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AddHenchmenFC, "Add Henchmen")
    bot.Move.XY(3045, -1575)
    bot.Move.XY(3007, -2609)
    bot.Move.XY(2909, -3629)
    bot.Move.XY(3145, -4643)
    bot.Move.XY(3372, -5617)
    bot.Wait.ForMapLoad(target_map_id=240)
    bot.Properties.Enable("birthday_cupcake")
    auto_path_list = [(-9467.0,14207.0), (-10965.0,9309.0), (-10332.0,1442.0), (-10254.0,-1759.0)]
    bot.Move.FollowAutoPath(auto_path_list)
    path_to_marketplace = [
        (-10324.0, -1213),
        (-10402, -2217),
        (-10704, -3213),
        (-11051, -4206),
        (-11483, -5143),
        (-11382, -6149),
        (-11024, -7085),
        (-10720, -8042),
        (-10404, -9039),
        (-10950, -9913),
        (-11937, -10246),
        (-12922, -10476),
        (-13745, -11050),
        (-14565, -11622)
    ]
    bot.Move.FollowPathAndExitMap(path_to_marketplace, target_map_name="The Marketplace") #MarketPlace

def AdvanceToSeitungHarbor(bot: Botting):
    bot.States.AddHeader("Phase 7: Advancing to Seitung Harbor Outpost")
    #PrepareForBattle(bot)
    bot.Map.Travel(target_map_id=303)
    #bot.Move.XY(11762, 17287)
    #bot.Move.XY(12041, 18273)
    bot.Move.XY(12313, 19236)
    bot.Move.XY(10343, 20329)
    bot.Wait.ForMapLoad(target_map_id=302)
    bot.Move.XY(8392, 20845)
    bot.Move.XYAndDialog(6912.20, 19912.12, 0x84)
    #bot.Dialogs.WithModel(3241, 0x81)
    #bot.Dialogs.WithModel(3241, 0x84)
    bot.Wait.ForMapToChange(target_map_id=250)

def AdvanceToShinjeaMonastery(bot: Botting):
    bot.States.AddHeader("Phase 7: Advancing to Shinjea Monastery")
    PrepareForBattle(bot)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AddHenchmenFC, "Add Henchmen")
    bot.Map.Travel(target_map_id=250)
    bot.Move.XY(17367.47, 12161.08)
    bot.Move.XYAndExitMap(15868.00, 13455.00, target_map_id=313)
    bot.Move.XY(574.21, 10806.26)
    bot.Move.XYAndExitMap(382.00, 9925.00, target_map_id=252)
    bot.Move.XYAndExitMap(-5004.50, 9410.41, target_map_id=242)

def AdvanceToTsumeiVillage(bot: Botting):
    bot.States.AddHeader("Phase 7: Advancing to Tsumei Village")
    bot.Map.Travel(target_map_id=242) #Shinjea Monastery
    bot.States.AddCustomState(AddHenchmenFC, "Add Henchmen")
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    bot.Move.XYAndExitMap(-4842, -13267, target_map_id=249) #tsumei_village_map_id

def AdvanceToMinisterCho(bot: Botting):
    bot.States.AddHeader("Phase 7: Advancing To Minister Cho")
    bot.Map.Travel(target_map_id=242) #Shinjea Monastery
    bot.States.AddCustomState(AddHenchmenFC, "Add Henchmen")
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    bot.Move.XY(6611.58, 15847.51)
    #bot.Move.XY(6892, 17079)
    bot.Move.FollowPath([(6874, 16391)])
    bot.Wait.ForMapLoad(target_map_id=214) #minister_cho_map_id

def UnlockLionsArch(bot: Botting):
    bot.States.AddHeader("Phase 7: Unlocking Lion's Arch Outpost")
    bot.Map.Travel(target_map_id=493)  # Consulate Docks
    bot.Wait.ForMapLoad(target_map_id=493)
    bot.Move.XYAndDialog(-2546.09, 16203.26, 0x89)
    bot.Wait.ForMapToChange(target_map_name="Lion's Gate")
    bot.Move.XY(-1181, 1038)
    bot.Dialogs.WithModel(1961, 0x85)  # Neiro dialog model id 1961
    bot.Move.XY(-1856.86, 1434.14)
    bot.Move.FollowPath([(-2144, 1450)])
    bot.Wait.ForMapLoad(target_map_id=55) #has built in wait time now

def UnlockRemainingSecondaryProfessions(bot: Botting):
    bot.States.AddHeader("Phase 7: Unlocking All Remaining Secondary Professions")
    bot.Map.Travel(target_map_id=248)  # GTOB
    bot.Move.XY(-3151.22, -7255.13)  # Move to profession trainers area
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    
    if primary == "Warrior":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x284)  # Ranger trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201
    elif primary == "Ranger":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201
    elif primary == "Monk":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x284)  # Ranger trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201
    elif primary == "Mesmer":
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x284)  # Ranger trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201
    elif primary == "Necromancer":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x284)  # Ranger trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201
    elif primary == "Elementalist":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x284)  # Ranger trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201
    elif primary == "Dervish":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x284)  # Ranger trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201
    elif primary == "Paragon":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x284)  # Ranger trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201

def UnlockXunlaiMaterialStoragePanel(bot: Botting) -> None:
    bot.States.AddHeader("Phase 7: Unlocking Xunlai Material Storage Panel")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=248)  # GTOB
    path_to_xunlai = [(-5540.40, -5733.11),(-7050.04, -6392.59),]
    bot.Move.FollowPath(path_to_xunlai) #UNLOCK_XUNLAI_STORAGE_MATERIAL_PANEL
    bot.Dialogs.WithModel(221, 0x800001)
    bot.Dialogs.WithModel(221, 0x800002)  # Unlock Material Storage Panel

def UnlockMercenaryHeroes(bot: Botting) -> None:
    bot.States.AddHeader("Phase 7: Unlocking Mercenary Heroes")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=248)  # GTOB
    bot.Move.XY(-4231.87, -8965.95)
    bot.Dialogs.WithModel(225, 0x800004) # Unlock Mercenary Heroes
#region MAIN
selected_step = 0
filter_header_steps = True

iconwidth = 96


def _draw_texture():
    global iconwidth
    level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())

    path = "SS Evos.png"
    size = (float(iconwidth), float(iconwidth))
    tint = (255, 255, 255, 255)
    border_col = (0, 0, 0, 0)  # <- ints, not normalized floats

    if level <= 3:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.0, 0.0),   uv1=(0.25, 1.0),
                                  tint=tint, border_color=border_col)
    elif level <= 5:
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

    # War Supplies controls
    use_war_supplies = bot.Properties.Get("war_supplies", "active")
    ws_restock_qty = bot.Properties.Get("war_supplies", "restock_quantity")

    use_war_supplies = PyImGui.checkbox("Use War Supplies", use_war_supplies)
    ws_restock_qty = PyImGui.input_int("War Supplies Restock Quantity", ws_restock_qty)

    bot.Properties.ApplyNow("war_supplies", "active", use_war_supplies)
    bot.Properties.ApplyNow("war_supplies", "restock_quantity", ws_restock_qty)
    bot.Properties.ApplyNow("birthday_cupcake", "active", use_birthday_cupcake)
    bot.Properties.ApplyNow("birthday_cupcake", "restock_quantity", bc_restock_qty)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "restock_quantity", hc_restock_qty)


bot.SetMainRoutine(create_bot_routine)
bot.UI.override_draw_texture(_draw_texture)
bot.UI.override_draw_config(lambda: _draw_settings(bot))

def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()

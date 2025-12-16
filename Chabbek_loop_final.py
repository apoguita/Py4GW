from __future__ import annotations
from typing import List, Tuple, Generator, Any
import os

from Py4GW import Console
import PyImGui
from AccountData import MODULE_NAME
from Py4GWCoreLib import (GLOBAL_CACHE, Inventory, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui, ActionQueueManager,)  # <- ajout de Timer


LAST_CHARACTER_NAME: str = ""


bot = Botting("Chabbek",
              upkeep_birthday_cupcake_restock=10,
              upkeep_honeycomb_restock=20,
              upkeep_war_supplies_restock=2,
              upkeep_auto_inventory_management_active=False,
              upkeep_auto_combat_active=False,
              upkeep_auto_loot_active=True)
 

def create_bot_routine(bot: Botting) -> None:

    global LAST_CHARACTER_NAME
    # capture tôt tant qu'on est bien en jeu
    LAST_CHARACTER_NAME = GLOBAL_CACHE.Player.GetName() or LAST_CHARACTER_NAME
   
    SkipTutorialDialog(bot)                    # Skip opening tutorial
    ApproachJahdugargate(bot)
    UnlockEmbarkBeach(bot)
    TravelToChabbek(bot)                       # Go to chabbek village
    ApproachJahdugar(bot)                      # Approach NPC Jahdugar
    TakeZM(bot)                                #Take ZM
    ConfigureFirstBattle(bot)                  # Configure first battle setup
    EnterChahbekMission(bot)                   # Enter Chahbek mission
    TravelToBeach(bot)                         # Travel to EB
    TakeReward(bot)                            # Take Reward 
    UnlockXunlai(bot)                          # Unlock Storage
    DepositReward(bot)
    DepositGold(bot)                           # Deposit Copper Z coins

    # 👉 Ajout du state de fin : logout + delete + recreate même nom

    bot.States.AddHeader("Reroll: Logout > Delete > Recreate")
    bot.States.AddCustomState(LogoutAndDeleteState, "Logout/Delete/Recreate same name")

    bot.States.AddHeader("Loop: restart routine")
    bot.States.AddCustomState(ScheduleNextRun, "Schedule next run")

    

#region Helpers



# ---------------------------------------------------------------------------
#  REROLL (Logout -> Delete -> Create same name)
# ---------------------------------------------------------------------------

def _resolve_character_name():
    global LAST_CHARACTER_NAME

    # 1) En jeu
    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(GLOBAL_CACHE.Player.GetAgentID())
    name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
    if name:
        LAST_CHARACTER_NAME = name
        yield
        return name
    
    print (f"name (beginning) = {LAST_CHARACTER_NAME}")

    # 2) Écran de sélection
    try:
        if GLOBAL_CACHE.Player.InCharacterSelectScreen():
            pregame = GLOBAL_CACHE.Player.GetPreGameContext()
            if pregame and hasattr(pregame, "chars") and hasattr(pregame, "index_1"):
                idx = int(pregame.index_1)
                if 0 <= idx < len(pregame.chars):
                    name = str(pregame.chars[idx])
                    if name:
                        LAST_CHARACTER_NAME = name
                        yield
                        return name
    except Exception:
        pass

    print (f"name (beginning) = {LAST_CHARACTER_NAME}")
    #add this to make it a generator
    yield 
    # 3) Dernier nom connu
    return LAST_CHARACTER_NAME


def LogoutAndDeleteState():
    """State final: logout -> delete -> recreate (même nom)."""
    ConsoleLog("Reroll", "Start: Logout > Delete > Recreate", Console.MessageType.Info)

    char_name = yield from _resolve_character_name()
    if not char_name:
        ConsoleLog(
            "Reroll",
            "Impossible de déterminer le nom du personnage (jeu + select + cache). Abandon reroll.",
            Console.MessageType.Error
        )
        return

    primary_prof, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    campaign_name = "Nightfall"

    print(f"Rerolling character '{char_name}' with profession '{primary_prof}' in campaign '{campaign_name}'.")

    yield from Routines.Yield.RerollCharacter.DeleteAndCreateCharacter(
        character_name_to_delete="Dialoguer Main",
        new_character_name="Dialoguer Main",
        campaign_name="Nightfall",
        profession_name="Dervish",
        timeout_ms=25000,
        log=True
    )

    ConsoleLog("Reroll", "Reroll finished.", Console.MessageType.Success)



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
    bot.Items.SpawnBonusItems()
    
    
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

def AddHenchmenLA():
    def _add_henchman(henchman_id: int):
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(henchman_id)
        ConsoleLog("addhenchman",f"Added Henchman: {henchman_id}", log=False)
        yield from Routines.Yield.wait(250)
        
    party_size = GLOBAL_CACHE.Map.GetMaxPartySize()

    henchmen_list = []
    if party_size <= 4:
        henchmen_list.extend([2, 3, 1]) 
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Lions Arch"):
        henchmen_list.extend([7, 2, 5, 3, 1]) 
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Ascalon City"):
        henchmen_list.extend([2, 3, 1])
    else:
        henchmen_list.extend([2,8,6,7,3,5,1])

    for henchman_id in henchmen_list:
        yield from _add_henchman(henchman_id)

def StandardHeroTeam():
    def _add_hero(hero_id: int):
        GLOBAL_CACHE.Party.Heroes.AddHero(hero_id)
        ConsoleLog("addhero",f"Added Hero: {hero_id}", log=False)
        yield from Routines.Yield.wait(250)

    party_size = GLOBAL_CACHE.Map.GetMaxPartySize()

    hero_list = []
    if party_size <= 6:
        hero_list.extend([24, 26, 27]) 
    else:
        hero_list.extend([10, 14, 24, 25, 26, 27, 21])
    
    for hero_id in hero_list:
        yield from _add_hero(hero_id)

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

    elif profession == "Elementalist":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDozGsAGTrwFbNAAIA")    
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDozGsAGTrwFbNAAIA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo0GsMGDahwoYYNAAAAMO") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMNGDahwoYYNAAAAMO")    
        elif level == 6:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMRGD0CCDFDWD4ggVYcA")    
        elif level == 7:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMRGD0CCDFDWD4ggVYcA")    
        elif level == 8:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMRGD0CCDFDWD4ggVYcA")    
        elif level == 9:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMRGD0CCDFDWD4ggVYcA")    
        elif level == 10:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMRGD0CCDFDWD4ggVYcA")    
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMRGD0CCDFDWD4ggVYcA")  

def GetArmorMaterialPerProfession(headpiece: bool = True) -> int:
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if primary == "Warrior":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Ranger":
        return ModelID.Tanned_Hide_Square.value
    elif primary == "Monk":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Dervish":
        return ModelID.Tanned_Hide_Square.value
    elif primary == "Mesmer":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Necromancer":
        return ModelID.Tanned_Hide_Square.value
    elif primary == "Ritualist":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Elementalist":
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
    elif primary == "Elementalist":
        return [ModelID.Wood_Plank.value]
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
    SCYTHE = SPEAR = SHIELDWAR = SWORD = BOW = SHIELDPARA = FIRESTAFF = DOMSTAFF = MONKSTAFF = 0

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
        FIRESTAFF = 18921
        return FIRESTAFF,
    elif primary == "Mesmer":
        DOMSTAFF = 18914
        return DOMSTAFF,
    elif primary == "Monk":
        MONKSTAFF = 18926
        return MONKSTAFF,
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

def NoHeadArmorMaterials(headpiece: bool = False):
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if primary == "Paragon":
        return ModelID.Tanned_Hide_Square.value
    elif primary == "Elementalist":
        return ModelID.Bolt_Of_Cloth.value
    
def GetNoHeadArmorPieces(bot: Botting):
    primary, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    HEAD, CHEST,GLOVES ,PANTS ,BOOTS = 0,0,0,0,0
    
    if primary == "Paragon":
        CHEST = 17791
        GLOVES = 17792
        PANTS = 17793
        BOOTS = 17790
    elif primary == "Elementalist":
        CHEST = 17350
        GLOVES = 17351
        PANTS = 17352
        BOOTS = 17349
    return  CHEST, GLOVES ,PANTS ,BOOTS

def CraftMostNoHeadArmor(bot: Botting):
    CHEST, GLOVES, PANTS, BOOTS = GetNoHeadArmorPieces(bot)

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

def ApproachJahdugargate(bot: Botting):
    bot.States.AddHeader("Quest: Meeting First Spear Jahdugar")
    bot.Move.XYAndDialog(4784,-1881, 0x82A504, step_name="Talk to First Spear Jahdugar")
    bot.Move.XYAndDialog(4784,-1881, 0x84, step_name="1")
    bot.Move.XYAndDialog(4784,-1881, 0x85, step_name="2")
    bot.Wait.ForTime(5000) 

def UnlockXunlai(bot : Botting) :
    bot.Move.XYAndDialog(2060, -2205, 0x84, step_name="Buy Storage")
    bot.Move.XYAndDialog(2060, -2205, 0x86, step_name="Open Storage")

def DepositReward(bot : Botting) :
    bot.States.AddHeader("Deposit Reward")
    bot.Items.AutoDepositItems() #deposit copper Z coins to bank model 31202 for config something after

def DepositGold(bot : Botting) :
    bot.States.AddHeader("Deposit Gold")
    bot.Items.AutoDepositGold() #deposit gold to bank

def TravelToBeach(bot: Botting):
    bot.States.AddHeader("Travel to Beach")
    bot.Map.Travel(target_map_id=857)  # beach_outpost_id
    bot.Wait.ForTime(5000) # Wait for cinematics to finish

def TravelToChabbek(bot: Botting):
    bot.States.AddHeader("Initial Setup: Travel to Chabbek")
    bot.Map.Travel(target_map_id=544)  # chabbek_outpost_id
    bot.Wait.ForTime(5000) # Wait for cinematics to finish

def UnlockEmbarkBeach(bot: Botting):
    bot.States.AddHeader("Initial Setup: Go to Embark Beach")
    bot.Move.XY(4626, -9617, step_name="Go to Zaishen Scoot")
    bot.Move.XYAndDialog(4626, -9617, 0x84, step_name="Yes, please take me to EB ")

def TakeZM(bot: Botting):
    bot.States.AddHeader("Go to take ZM")
    bot.Move.XY(2702.00, -2411, step_name="Go to ZM PNJ")
    bot.Move.XYAndDialog(2702.00, -2411, 0x83A801, step_name="Take Quest")


def TakeReward(bot: Botting):
    bot.States.AddHeader("Go to take Reward")
    bot.Move.XYAndDialog(-749,-3262,0x83F207, step_name="Go to ZM PNJ")
    bot.Move.XYAndDialog(-749,-3262, 0x83F207, step_name="Take Reward")

   

def ApproachJahdugar(bot: Botting):
    bot.States.AddHeader("Quest: Meeting First Spear Jahdugar")
    bot.Move.XYAndDialog(3482, -5167, 0x82A507, step_name="Talk to First Spear Jahdugar")
    bot.Move.XYAndDialog(3482, -5167, 0x83A801, step_name="You can count on me")


def ConfigureFirstBattle(bot: Botting):
    bot.States.AddHeader("Preparation: First Battle Setup")
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[1,2])
    def Equip_Weapon():
        global bot
        profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        if profession == "Dervish":
            bot.Items.Equip(15591)  # starter scythe
        elif profession == "Paragon":
            bot.Items.Equip(15593) #Starter Spear
            bot.Items.Equip(6514) #Bonus Shield
        elif profession == "Elementalist":
            bot.Items.Equip(6508) #Luminescent Scepter
            bot.Wait.ForTime(1000)
            bot.Items.Equip(6514)
        elif profession == "Mesmer":
            bot.Items.Equip(6508) #Luminescent Scepter
            bot.Wait.ForTime(1000)
            bot.Items.Equip(6514)
        elif profession == "Necromancer":
            bot.Items.Equip(6515) #Soul Shrieker   
        elif profession == "Ranger":
            bot.Items.Equip(5831) #Nevermore Flatbow 
        elif profession == "Warrior":
            bot.Items.Equip(2982) #Starter Sword  
            bot.Items.Equip(6514) #Bonus Shield  
        elif profession == "Monk":
            bot.Items.Equip(6508) #Luminescent Scepter 
            bot.Wait.ForTime(1000)
            bot.Items.Equip(6514)   
    Equip_Weapon()

    
def ConfigureFirstBattle_yield(bot: Botting):
    bot.States.AddHeader("Preparation: First Battle Setup")
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[1,2])
    def Equip_Weapon():
        global bot
        profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        if profession == "Dervish":
            bot.Items.Equip(15591)  # starter scythe
        elif profession == "Paragon":
            bot.Items.Equip(15593) #Starter Spear
            bot.Items.Equip(6514) #Bonus Shield
        elif profession == "Elementalist":
            bot.Items.Equip(6508) #Luminescent Scepter
            bot.Wait.ForTime(1000)
            bot.Items.Equip(6514)
        elif profession == "Mesmer":
            bot.Items.Equip(6508) #Luminescent Scepter
            bot.Wait.ForTime(1000)
            bot.Items.Equip(6514)
        elif profession == "Necromancer":
            bot.Items.Equip(6515) #Soul Shrieker   
        elif profession == "Ranger":
            bot.Items.Equip(5831) #Nevermore Flatbow 
        elif profession == "Warrior":
            bot.Items.Equip(2982) #Starter Sword  
            bot.Items.Equip(6514) #Bonus Shield  
        elif profession == "Monk":
            bot.Items.Equip(6508) #Luminescent Scepter 
            bot.Wait.ForTime(1000)
            bot.Items.Equip(6514)   
        yield
    bot.States.AddCustomState(Equip_Weapon, "Equip Starter Weapon")
    Equip_Weapon()
    bot.Dialogs.AtXY(3433, -5900, 0x82C707, step_name="Accept")

def EnterChahbekMission(bot: Botting):
    bot.States.AddHeader("Mission: Chahbek Village")
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

    elif profession == "Elementalist":
        bot.Move.XYAndDialog(-12011.00, -639.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Mesmer":
        bot.Move.XYAndDialog(-7149.00, 1830.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Necromancer":
        bot.Move.XYAndDialog(-6557.00, 1837.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Ranger":
        bot.Move.XYAndDialog(-9498.00, 1426.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Warrior":
        bot.Move.XYAndDialog(-9663.00, 1506.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Monk":
        bot.Move.XYAndDialog(-11658.00, -1414.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)    

def CompleteStorageQuests(bot: Botting):
    bot.States.AddHeader("Quest: Storage & Inventory Setup")
    bot.Move.XYAndDialog(-9251, 11826, 0x82A101, step_name="Storage Quest 0")
    bot.Move.XYAndDialog(-7761, 14393, 0x84, step_name="50 Gold please")
    bot.Move.XYAndDialog(-9251, 11826, 0x82A107, step_name="Accept reward")

 


selected_step = 0
filter_header_steps = True

iconwidth = 96


def _draw_texture():
    global iconwidth
    level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())

    path = os.path.join(Py4GW.Console.get_projects_path(),"Bots", "Leveling", "Nightfall","Nightfall_leveler-art.png")
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
bot.UI.override_draw_texture(_draw_texture)
bot.UI.override_draw_config(lambda: _draw_settings(bot))

# --- UI / Settings drawing ---------------------------------------------------
bot.UI.override_draw_texture(_draw_texture)
bot.UI.override_draw_config(lambda: _draw_settings(bot))

# ---------------------------------------------------------------------------
#  BOUCLE PRINCIPALE DU SCRIPT
# ---------------------------------------------------------------------------

def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()



# ---------------------------------------------------------------------------
#  LOOP CONTROLLER: planifie un nouveau run après le reroll
# ---------------------------------------------------------------------------

def ScheduleNextRun():
    """State: attend un peu, puis re-ajoute toute la routine (boucle infinie)."""
    yield from Routines.Yield.wait(1000)
    # On re-empile une nouvelle fois tous les steps (et donc le reroll + ScheduleNextRun)
    create_bot_routine(bot)



bot.SetMainRoutine(create_bot_routine)

from __future__ import annotations
from typing import List, Tuple, Generator, Any
import os
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Map, Player, Py4GW, ConsoleLog, ModelID, Botting,
                          Agent, ImGui, ActionQueueManager)


bot = Botting("Nightfall Leveler",
              upkeep_birthday_cupcake_restock=10,
              upkeep_honeycomb_restock=20,
              upkeep_war_supplies_restock=2,
              upkeep_auto_inventory_management_active=False,
              upkeep_auto_combat_active=False,
              upkeep_auto_loot_active=True)
 
def create_bot_routine(bot: Botting) -> None:
    # === TUTORIAL AND INITIAL SETUP ===
    Skip_Tutorial(bot)
    Into_Chahbek_Village(bot)
    Quiz_the_Recruits(bot)
    Configure_First_Battle(bot)
    Chahbek_Village_Mission(bot)
    Primary_Training(bot)
    Honing_Combat_Skills(bot)
    # === INITIAL QUESTS AND PROGRESSION ===
    A_Personal_Vault(bot)
    Extend_Inventory_Space(bot)
    Armored_Transport(bot)
    Material_Girl(bot)
    To_Champions_Dawn(bot)
    Quality_Steel(bot)
    Craft_First_Weapon(bot)
    Missing_Shipment(bot)
    Proof_of_Courage_and_Suwash_the_Pirate(bot)
    A_Hidden_Threat(bot)
    Identity_Theft(bot) 
    # === PROFESSION AND CHARACTER DEVELOPMENT ===
    Unlock_Secondary_Profession(bot)
    Configure_Player_Build(bot)
    Command_Training(bot)
    Leaving_A_Legacy(bot)  
    # === EQUIPMENT CRAFTING ===
    if Agent.GetProfessionNames(Player.GetAgentID())[0] in ["Paragon", "Elementalist", "Monk", "Necromancer"]:
        CraftArmorWithDoubleMats(bot)
    else:
        Craft_Player_Armor(bot)
    Craft_Player_Weapon(bot)
    Destroy_Starter_Armor_And_Useless_Items(bot)
    # === MID-GAME LEVELING ===
    Farm_Until_Level_10(bot)
    Unlock_Remaining_Secondary_Professions(bot)
    Unlock_Mercenary_Heroes(bot)
    Unlock_Xunlai_Material_Storage(bot)
    Attribute_Points_Quest_2(bot)
    Unlock_Sunspear_Skills(bot)
    # === EYE OF THE NORTH EXPANSION ===
    To_Boreal_Station(bot)
    To_Eye_Of_The_North_Outpost(bot)
    Unlock_Eye_Of_The_North_Pool(bot)
    To_Gunnars_Hold(bot)
    Unlock_Kilroy_Stonekin(bot)
    #To_Longeye_Edge(bot)
    #Unlock_NPC_For_Vaettir_Farm(bot)
    #To_Doomlore(bot)
    #To_Sifhalla(bot)
    #To_Olafstead(bot)
    #To_Umbral_Grotto(bot)
    # === FACTIONS CONTENT ===
    To_Consulate_Docks(bot)
    To_Kaineng_Center(bot)
    #To_Vizunah_Square_Foreign_Quarter(bot)
    To_Marketplace(bot)
    To_Seitung_Harbor(bot)
    To_Shinjea_Monastery(bot)
    To_Tsumei_Village(bot)
    To_Minister_Cho(bot)
    # === PROPHECIES CONTENT ===
    To_Lions_Arch(bot) 
    To_Temple_Of_The_Ages(bot)
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
    
def PrepareForBattle(bot: Botting, Hero_List = [], Henchman_List = []) -> None:
    ConfigureAggressiveEnv(bot)
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    bot.Party.AddHeroList(Hero_List)
    bot.Party.AddHenchmanList(Henchman_List)

def StandardHeroTeam():
    def _add_hero(hero_id: int):
        GLOBAL_CACHE.Party.Heroes.AddHero(hero_id)
        ConsoleLog("addhero",f"Added Hero: {hero_id}", log=False)
        yield from Routines.Yield.wait(250)

    party_size = Map.GetMaxPartySize()

    hero_list = []
    skill_templates = []
    
    if party_size <= 8:
        # Small party: Gwen, Vekk, Ogden
        hero_list.extend([24, 26, 27])
        skill_templates = [
            "OQhkAsC8gFKzJY6lDMd40hQG4iB",  # 1 Gwen
            "OgVDI8gsO5gTw0z0hTFAZgiA",     # 2 Vekk
            "OwUUMsG/E4SNgbE3N3ETfQgZAMEA"  # 3 Ogden
        ]
    # Add all heroes
    for hero_id in hero_list:
        yield from _add_hero(hero_id)
    
    # Load skillbars for all positions
    for position in range(len(hero_list)):
        GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(position + 1, skill_templates[position])
        ConsoleLog("skillbar", f"Loading skillbar for position {position + 1}", log=True)
        yield from Routines.Yield.wait(500)
    
def AddHenchmenFC():
    def _add_henchman(henchman_id: int):
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(henchman_id)
        ConsoleLog("addhenchman",f"Added Henchman: {henchman_id}", log=False)
        yield from Routines.Yield.wait(250)
        
    party_size = Map.GetMaxPartySize()

    henchmen_list = []
    if party_size <= 4:
        henchmen_list.extend([1, 5, 2]) 
    elif Map.GetMapID() == Map.GetMapIDByName("Seitung Harbor"):
        henchmen_list.extend([2, 3, 1, 4, 5]) 
    elif Map.GetMapID() == Map.GetMapIDByName("The Marketplace"):
        henchmen_list.extend([6,9,5,1,4,7,3])
    elif Map.GetMapID() == 213: #zen_daijun_map_id
        henchmen_list.extend([3,1,6,8,5])
    elif Map.GetMapID() == 194: #kaineng_map_id
        henchmen_list.extend([2,10,4,8,7,9,12])
    elif Map.GetMapID() == Map.GetMapIDByName("Boreal Station"):
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
        
    party_size = Map.GetMaxPartySize()

    henchmen_list = []
    if party_size <= 4:
        henchmen_list.extend([2, 3, 1]) 
    elif Map.GetMapID() == Map.GetMapIDByName("Lions Arch"):
        henchmen_list.extend([7, 2, 5, 3, 1]) 
    elif Map.GetMapID() == Map.GetMapIDByName("Ascalon City"):
        henchmen_list.extend([2, 3, 1])
    else:
        henchmen_list.extend([2,8,6,7,3,5,1])

    for henchman_id in henchmen_list:
        yield from _add_henchman(henchman_id)

def EquipSkillBar(): 
    global bot

    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    level = Agent.GetLevel(Player.GetAgentID())
    if profession == "Dervish":
        if level ==2:
           yield from Routines.Yield.Skills.LoadSkillbar("OgChkSj4V6KAGw/X7LCe8C")
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA")    
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OgGjkyrDLTiXSX7gDYPXfXjbYcA")

    elif profession == "Paragon":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OQCjUOmBqMw4HMQuCHjBAYcBAA")    
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OQCjUOmBqMw4HMQuCHjBAYcBAA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OQCjUWmCaNw4HMQuCDAAAYcBAA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGkUemyZgKEM2DmDGQ2VBQoAAGH")        
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGjUymDKTwYPYOYAZLYXFAhYcA")  

    elif profession == "Elementalist":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDozGsAGTrwFbNAAIA")    
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDozGsAGTrwFbNAAIA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMNGDahwoYYNAAAAMO") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMNGDahwoYYNAAAAMO")    
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OgVDErwsN0COwFAoeTzzgVMO")  

    elif profession == "Monk":    
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OwAU0C38CYEZEltkf5cmAImA")    
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OwAU0CH9CoEtElZkf5EAAImA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OwAU0CH9CoEtElZkf5EAAImA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OwAU0CH9CoEtElZkf5EAAImA")    
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OwUEEqwD6ywBuA308cPAKgSiJA")   

    elif profession == "Warrior":    
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OQARErprIUAABAuCGHAAAA")    
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OQARErprIUAABAuCGHAAAA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OQARErprIUAABAuCGHAAAA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OQARErprIUAABAuCGHAAAA")      
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OQojExVTKTdFCF/XDYcFBA7gYcA")            
    elif profession == "Necromancer":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OABDQRJWAplpAAAAAAAA")  
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OABDQTNmMphMRboK8IAAAAMO")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OABDQTNmMphMRboK8IAAAAMO") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OAVDIXN2McgqwFAo2DgCCAMO")      
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OAVEEqwFZ3wBqCXAgaPAKknx4A") 
    elif profession == "Mesmer":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OQBDAhITAoohAAAAAAAA")  
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OQBDAhMTAooBHEBFAAIA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OQBDAhgTAooBHEBFAAIA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OQBDAhgTMogLAHgIAF6BAVBA")      
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OQBEAaYCP2gCuAcg8MUoHAUx4A")        
    elif profession == "Ranger":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OgATcDskjQx+WAAAAAAAAAA")  
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OgATcDsknQx++4xGAAAACAA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OgAScLsMAAfzxZ5gxBAAABA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OgESIpLNdFfDUBAAA4KXFMO")     
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OgETI5LjHqrw3AqYHkqQvC1AjDA")              


def GetArmorMaterialPerProfession(headpiece: bool = True) -> int:
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary == "Warrior":
        return ModelID.Iron_Ingot.value
    elif primary == "Ranger":
        return ModelID.Bolt_Of_Cloth.value
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
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary == "Warrior":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Ranger":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Dervish":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Paragon":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Elementalist":
        return [ModelID.Wood_Plank.value]
    elif primary == "Monk":
        return [ModelID.Wood_Plank.value]
    elif primary == "Necromancer":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Mesmer":
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

#region Double Materials Armor Crafting (Common + Rare)

def GetRareArmorMaterial() -> int | None:
    """Returns the rare material type for classes that need it, None otherwise."""
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    # TODO: Fill in the rare materials for each profession
    # Example structure from Obsidian bot:
    # if primary == "Warrior":
    #     return ModelID.Deldrimor_Steel_Ingot.value
    # elif primary == "Ranger":
    #     return ModelID.Fur_Square.value
    # ... add other professions here
    
    return None  # Placeholder - will be filled with specific materials

def BuyDoubleMaterials(material_type: str = "common"):
    """Buy materials for double material armor crafting. Pass 'common' or 'rare' to specify which type."""
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    if material_type == "common":
        # Buy primary common materials (bought in x10 units)
        if primary == "Paragon":
            # Paragon needs 20 Iron Ingots + 10 Pile of Glittering Dust
            for _ in range(2):  # Buy 20 Iron Ingots (2 * 10)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Iron_Ingot.value)
            yield from Routines.Yield.wait(500)  # Wait between material types
            for _ in range(1):  # Buy 10 Pile of Glittering Dust (1 * 10)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Pile_Of_Glittering_Dust.value)
        elif primary == "Monk":
            # Monk needs 20 Bolt of Cloth + 10 Pile of Glittering Dust
            for _ in range(2):  # Buy 20 Bolts of Cloth (2 * 10)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Bolt_Of_Cloth.value)
            yield from Routines.Yield.wait(500)  # Wait between material types
            for _ in range(1):  # Buy 10 Pile of Glittering Dust (1 * 10)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Pile_Of_Glittering_Dust.value)
        elif primary == "Elementalist":
            # Elementalist needs 20 Bolt of Cloth + 10 Pile of Glittering Dust
            for _ in range(2):  # Buy 20 Bolts of Cloth (2 * 10)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Bolt_Of_Cloth.value)
            yield from Routines.Yield.wait(500)  # Wait between material types
            for _ in range(1):  # Buy 10 Pile of Glittering Dust (1 * 10)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Pile_Of_Glittering_Dust.value)
        elif primary == "Necromancer":
            # Necromancer needs 20 Tanned Hide Squares + 10 Pile of Glittering Dust
            for _ in range(2):  # Buy 20 Tanned Hide Squares (2 * 10)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Tanned_Hide_Square.value)
            yield from Routines.Yield.wait(500)  # Wait between material types
            for _ in range(1):  # Buy 10 Pile of Glittering Dust (1 * 10)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Pile_Of_Glittering_Dust.value)
        else:
            # Default for other professions (just their primary material)
            for _ in range(2):  # Buy 20 common materials (standard amount)
                yield from Routines.Yield.Merchant.BuyMaterial(GetArmorMaterialPerProfession())
            
    elif material_type == "rare":
        rare_material = GetRareArmorMaterial()
        if rare_material is not None:
            # TODO: Rare materials are bought in x1 units
            # Example structure from Obsidian bot:
            # if primary == "Warrior":
            #     for _ in range(40):  # Buy 40 Deldrimor Steel Ingots (40 * 1)
            #         yield from Routines.Yield.Merchant.BuyMaterial(rare_material)
            # elif primary == "Ranger":
            #     for _ in range(35):  # Buy 35 Fur Squares (35 * 1)
            #         yield from Routines.Yield.Merchant.BuyMaterial(rare_material)
            # ... add other professions here
            
            # Placeholder - default amount
            for _ in range(20):  # Buy 20 rare materials
                yield from Routines.Yield.Merchant.BuyMaterial(rare_material)

def DoCraftArmorWithDoubleMats(bot: Botting):
    """Craft armor using both common and rare materials."""
    HEAD, CHEST, GLOVES, PANTS, BOOTS = GetArmorPiecesByProfession(bot)
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    # Professions that need primary material + dust (both common)
    if primary in ["Paragon", "Monk", "Elementalist", "Necromancer"]:
        armor_pieces = [
            (HEAD, [ModelID.Pile_Of_Glittering_Dust.value], [2]),
            (CHEST, [GetArmorMaterialPerProfession()], [6]),
            (GLOVES, [GetArmorMaterialPerProfession()], [2]),
            (PANTS, [GetArmorMaterialPerProfession()], [4]),
            (BOOTS, [GetArmorMaterialPerProfession()], [2]),
        ]
    else:
        # Fallback to single material for other professions
        armor_pieces = [
            (HEAD, [GetArmorMaterialPerProfession()], [2]),
            (CHEST, [GetArmorMaterialPerProfession()], [6]),
            (GLOVES, [GetArmorMaterialPerProfession()], [2]),
            (PANTS, [GetArmorMaterialPerProfession()], [4]),
            (BOOTS, [GetArmorMaterialPerProfession()], [2]),
        ]

    for item_id, mats, qtys in armor_pieces:
        result = yield from Routines.Yield.Items.CraftItem(item_id, 75, mats, qtys)
        if not result:
            ConsoleLog("CraftArmorWithDoubleMats", f"Failed to craft item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield

        result = yield from Routines.Yield.Items.EquipItem(item_id)
        if not result:
            ConsoleLog("CraftArmorWithDoubleMats", f"Failed to equip item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True

def CraftArmorWithDoubleMats(bot: Botting):
    """Main routine to craft armor with double materials (common + rare)."""
    bot.States.AddHeader("Craft Armor")
    
    # Travel to crafting location
    bot.Map.Travel(target_map_id=491)
    
    # Withdraw gold
    bot.States.AddCustomState(withdraw_gold, "Withdraw Gold")
    
    # Buy common materials
    bot.Move.XY(3495.80, 2050.97)
    bot.Move.XYAndInteractNPC(3839.00, 1618.00)  # Material trader
    exec_fn_common = lambda: BuyDoubleMaterials("common")
    bot.States.AddCustomState(exec_fn_common, "Buy Common Materials")
    bot.Wait.ForTime(1500)  # Wait for common material purchases to complete
    
    # Buy rare materials if needed
    rare_material = GetRareArmorMaterial()
    if rare_material is not None:
        bot.Move.XYAndInteractNPC(-10997.00, 10022.00)  # Rare material merchant
        exec_fn_rare = lambda: BuyDoubleMaterials("rare")
        bot.States.AddCustomState(exec_fn_rare, "Buy Rare Materials")
        bot.Wait.ForTime(2000)  # Wait for rare material purchases to complete
    
    # Move to armor crafter and craft
    bot.Move.XYAndInteractNPC(3944, 2378)  # Armor crafter
    bot.Wait.ForTime(1000)  # Small delay to let the window open
    exec_fn = lambda: DoCraftArmorWithDoubleMats(bot)
    bot.States.AddCustomState(exec_fn, "Craft Armor with Double Materials")

#endregion

def GetArmorPiecesByProfession(bot: Botting):
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    HEAD,CHEST,GLOVES ,PANTS ,BOOTS = 0,0,0,0,0

    if primary == "Warrior": 
        HEAD = 17525 #Need Strength
        CHEST = 17531
        GLOVES = 17532
        PANTS = 17533
        BOOTS = 17530
    elif primary == "Dervish":
        HEAD = 17705
        CHEST = 17676
        GLOVES = 17677
        PANTS = 17678
        BOOTS = 17675
    elif primary == "Ranger":
        HEAD = 17619
        CHEST = 17621
        GLOVES = 17622
        PANTS = 17623
        BOOTS = 17620
    elif primary == "Mesmer":
        HEAD = 17191
        CHEST = 17196
        GLOVES = 17197
        PANTS = 17198
        BOOTS = 17195
    elif primary == "Paragon":
        HEAD = 17777
        CHEST = 17791
        GLOVES = 17792
        PANTS = 17793
        BOOTS = 17790
    elif primary == "Elementalist":
        HEAD = 17333
        CHEST = 17350
        GLOVES = 17351
        PANTS = 17352
        BOOTS = 17349
    elif primary == "Monk":
        HEAD = 17402
        CHEST = 17406
        GLOVES = 17407
        PANTS = 17408
        BOOTS = 17405
    elif primary == "Necromancer":
        HEAD = 17249
        CHEST = 17251
        GLOVES = 17252
        PANTS = 17253
        BOOTS = 17250

    return  HEAD, CHEST, GLOVES, PANTS, BOOTS 

def GetWeaponByProfession(bot: Botting):
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    SCYTHE = SPEAR = AXE = SHIELD = SHIELDPARA = FIRESTAFF = DOMSTAFF = MONKSTAFF = NECROSTAFF = 0

    if primary == "Warrior":
        SCYTHE = 18910
        return SCYTHE,
    elif primary == "Ranger":
        AXE = 18903
        SHIELD = 18912
        return AXE, SHIELD
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
    elif primary == "Necromancer":
        NECROSTAFF = 18914 #Dom Staff :)
        return NECROSTAFF,
    return ()

def GetFirstWeaponByProfession(bot: Botting):
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    SCYTHE = SPEAR = AXE = FIRESTAFF = DOMSTAFF = MONKSTAFF = NECROSTAFF = 0
    
    if primary == "Warrior":
        SCYTHE = 16227
        return SCYTHE,
    elif primary == "Ranger":
        AXE =  15777 #Winged Axe
        return AXE,
    elif primary == "Paragon":
        SPEAR = 18711
        return SPEAR,
    elif primary == "Dervish":
        SCYTHE = 16227
        return SCYTHE,
    elif primary == "Elementalist":
        FIRESTAFF = 18896
        return FIRESTAFF,
    elif primary == "Mesmer":
        DOMSTAFF = 18712
        return DOMSTAFF,
    elif primary == "Monk":
        MONKSTAFF = 18901 #Smiting Staff
        return MONKSTAFF,
    elif primary == "Necromancer":
        NECROSTAFF = 18893 #Death Staff
        return NECROSTAFF,
    return ()

def GetFirstWeaponMaterialPerProfession(bot: Botting):
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary == "Warrior":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Ranger":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Dervish":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Paragon":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Elementalist":
        return [ModelID.Wood_Plank.value]
    elif primary == "Monk":
        return [ModelID.Wood_Plank.value]
    elif primary == "Mesmer":
        return [ModelID.Iron_Ingot.value]  
    elif primary == "Necromancer":
        return [ModelID.Wood_Plank.value]        
    return []

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

def Craft1stWeapon(bot: Botting):
    weapon_ids = GetFirstWeaponByProfession(bot)
    materials = GetFirstWeaponMaterialPerProfession(bot)
    
    # Structure weapon data like armor pieces - (weapon_id, materials_list, quantities_list)
    weapon_pieces = []
    for weapon_id in weapon_ids:
        weapon_pieces.append((weapon_id, materials, [1]))  # 1 = 10 materials per weapon minimum
    
    yield from Routines.Yield.Agents.InteractWithAgentXY(-11270.00, 8785.00)
    yield

    for weapon_id, mats, qtys in weapon_pieces:
        result = yield from Routines.Yield.Items.CraftItem(weapon_id, 20, mats, qtys)
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

#region Tutorial and Initial Setup

def Skip_Tutorial(bot: Botting) -> None:
    bot.States.AddHeader("Skip Tutorial")
    bot.Move.XYAndDialog(10289, 6405, 0x82A503)
    bot.Dialogs.AtXY(10289, 6405, 0x82A501)
    bot.Map.LeaveGH()
    bot.Wait.ForMapToChange(target_map_id=544)

def Into_Chahbek_Village(bot: Botting):
    bot.States.AddHeader("Quest: Into Chahbek Village")
    bot.Map.Travel(target_map_id=544)
    bot.Move.XYAndDialog(3493, -5247, 0x82A507)
    bot.Move.XYAndDialog(3493, -5247, 0x82C501)

def Quiz_the_Recruits(bot: Botting):
    bot.States.AddHeader("Quest: Quiz the Recruits")
    bot.Map.Travel(target_map_id=544)
    bot.Move.XY(4750, -6105)
    bot.Move.XYAndDialog(4750, -6105, 0x82C504)
    bot.Move.XYAndDialog(5019, -6940, 0x82C504)
    bot.Move.XYAndDialog(3540, -6253, 0x82C504)
    bot.Wait.ForTime(1000)
    bot.Move.XY(3485, -5246)
    bot.Dialogs.AtXY(3485, -5246, 0x82C507)
    bot.Move.XYAndDialog(3433, -5900, 0x82C701)
    bot.Dialogs.AtXY(3433, -5900, 0x82C707)

def Equip_Weapon():
        global bot
        profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
        if profession == "Dervish":
            bot.Items.Equip(15591)  # starter scythe
        elif profession == "Paragon":
            bot.Items.Equip(15593) #Starter Spear
            #bot.Items.Equip(6514) #Bonus Shield
        elif profession == "Elementalist":
            #bot.Items.Equip(6508) #Luminescent Scepter
            bot.Items.Equip(2742) #Starter Elemental Rod
            #bot.Wait.ForTime(1000)
            #bot.Items.Equip(6514)
        elif profession == "Mesmer":
            #bot.Items.Equip(6508) #Luminescent Scepter
            bot.Items.Equip(2652) #Starter Cane
            #bot.Wait.ForTime(1000)
            #bot.Items.Equip(6514)
        elif profession == "Necromancer":
            #bot.Items.Equip(6515) #Soul Shrieker   
            bot.Items.Equip(2694) #Starter Truncheon
        elif profession == "Ranger":
            #bot.Items.Equip(5831) #Nevermore Flatbow 
            bot.Items.Equip(477) #Starter Bow
        elif profession == "Warrior":
            bot.Items.Equip(2982) #Starter Sword  
            #bot.Items.Equip(6514) #Bonus Shield  
        elif profession == "Monk":
            #bot.Items.Equip(6508) #Luminescent Scepter 
            bot.Items.Equip(2787) #Starter Holy Rod
            #bot.Wait.ForTime(1000)
            #bot.Items.Equip(6514)   
  
def Configure_First_Battle(bot: Botting):
    bot.States.AddHeader("Battle Setup")
    bot.Map.Travel(target_map_id=544)
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[1,2])
    bot.Items.SpawnAndDestroyBonusItems(exclude_list=[ModelID.Igneous_Summoning_Stone.value])
    Equip_Weapon()

def Chahbek_Village_Mission(bot: Botting):
    bot.States.AddHeader("Chahbek Village Mission")
    bot.Map.Travel(target_map_id=544)
    bot.SkillBar.LoadHeroSkillBar(1, "OQASEF6EC1vcNABWAAAA") #Koss
    bot.Dialogs.AtXY(3485, -5246, 0x81)
    bot.Dialogs.AtXY(3485, -5246, 0x84)
    bot.Wait.ForTime(2000)
    bot.Wait.UntilOnExplorable()
    ConfigureAggressiveEnv(bot)
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
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
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

    elif profession == "Necromancer":
        bot.Move.XYAndDialog(-6557.00, 1837.00, 0x7F, step_name="Teach me 1")
        

    elif profession == "Ranger":
        bot.Move.XYAndDialog(-9498.00, 1426.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Warrior":
        bot.Move.XYAndDialog(-9663.00, 1506.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Monk":
        bot.Move.XYAndDialog(-11658.00, -1414.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)    

def Primary_Training(bot: Botting):
    bot.States.AddHeader("Quest: Primary Training")
    bot.Properties.Disable("hero_ai")
    
    bot.Move.XY(-7234.90, 4793.62)
    bot.Move.XYAndDialog(-7234.90, 4793.62, 0x825801)
    Get_Skills()
    bot.Move.XYAndDialog(-7234.90, 4793.62, 0x825807)

def Honing_Combat_Skills(bot: Botting):
    bot.States.AddHeader("Quest: Honing your Skills")
    bot.Move.XY(-7234.90, 4793.62)
    bot.Move.XYAndDialog(-7234.90, 4793.62, 0x828901)
    bot.UI.CancelSkillRewardWindow()
    bot.Dialogs.AtXY(-7183, 4904, 0x828901)
    bot.Move.XYAndDialog(-7383, 5706, 0x81)
    bot.Dialogs.AtXY(-7383, 5706, 0x84)
    bot.Wait.ForMapToChange(target_map_id=449)

def A_Personal_Vault(bot: Botting):
    bot.States.AddHeader("Quest: A Personal Vault")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-9251, 11826, 0x82A101)
    bot.Move.XYAndDialog(-7761, 14393, 0x84)
    bot.Move.XYAndDialog(-9251, 11826, 0x82A107)

def Extend_Inventory_Space(bot: Botting):
    bot.States.AddHeader("Extend Inventory Space")
    bot.Map.Travel(target_map_id=449) # Kamadan
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
    bot.UI.BagItemDoubleClick(bag_id=1, slot=0) #Needs to be fixed
    bot.Wait.ForTime(500) # Wait for equip to complete
    bot.Items.MoveModelToBagSlot(35, 1, 0) 
    bot.UI.BagItemDoubleClick(bag_id=1, slot=0) #Needs to be fixed
    bot.Wait.ForTime(500)
    bot.Items.MoveModelToBagSlot(35, 1, 0)
    bot.UI.BagItemDoubleClick(bag_id=1, slot=0) #Needs to be fixed

def Armored_Transport(bot: Botting):
    bot.States.AddHeader("Quest: Armored Transport")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-11202, 9346,0x825F01) #+500xp protect quest
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-9326, 18151, target_map_id=430) # Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(16448, 2320,0x825F04)
    def _exit_condition():
        pos = Player.GetXY()
        if not pos:
            return False
        dx = pos[0] - -2750.0
        dy = pos[1] - 1741.0
        return (dx * dx + dy * dy) <= (1000.0 * 1000.0)
    exit_condition = lambda: _exit_condition()
    bot.Move.FollowModel(4881, 100, exit_condition) #Dec New ID
    bot.Move.XY(-2963, 1813)
    bot.Wait.ForTime(10000)
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-11202, 9346,0x825F07)

def Identity_Theft(bot: Botting):
    bot.States.AddHeader("Quest: Identity Theft")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XY(-7519.91, 14468.26)
    bot.Move.XYAndDialog(-10461, 15229, 0x827201) #take quest
    bot.Map.Travel(target_map_id=479) #Champions Dawn
    bot.Move.XYAndDialog(25345, 8604, 0x827204)
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,6,7])
    bot.Move.XYAndExitMap(22483, 6115, target_map_id=432) #Cliffs of Dohjok
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(20215, 5285, 0x85) #Blessing 
    bot.Items.AddModelToLootWhitelist(15850)
    bot.Move.XY(14429, 10337) #kill boss
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot) #To Stop all combat to loot item without timeout
    bot.Items.LootItems()
    bot.Wait.ForTime(1000)
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XY(-7519.91, 14468.26)
    bot.Move.XYAndDialog(-10461, 15229, 0x827207) # +500xp

def Command_Training(bot: Botting):
    bot.States.AddHeader("Quest: Command Training")
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

def Material_Girl(bot: Botting):
    bot.States.AddHeader("Quest: Quality Steel")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-11363, 9066, 0x826103)
    bot.Dialogs.AtXY(-11363, 9066, 0x826101)
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-9326, 18151, target_map_id=430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(18460, 1002, step_name="Bounty")
    bot.Move.XYAndDialog(18460, 1002, 0x85) #Blessing 
    bot.Move.XY(9675, 1038)
    bot.Move.XYAndDialog(9282, -1199, 0x826104)
    bot.Wait.ForTime(2000)
    bot.Move.XY(9464, -2639)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(11183, -7728)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(9681, -9300)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7555, -6791)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(5073, -4850)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(9292, -1220, 0x826104)
    bot.Move.XYAndDialog(-1782, 2790, 0x828801)
    bot.Move.XY(-3145, 2412)
    bot.Move.XYAndExitMap(-3236, 4503, target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForTime(2000)
    bot.Map.Travel(target_map_id=449) #Kamadan
    bot.Move.XYAndDialog(-10024, 8590, 0x828804)
    bot.Dialogs.AtXY(-10024, 8590, 0x828807)
    bot.Move.XYAndDialog(-11356, 9066, 0x826107)
    bot.Wait.ForTime(2000)
   
def Quality_Steel(bot: Botting):
    bot.States.AddHeader("Quest: Quality Steel")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-11208, 8815, 0x826003, step_name="Quality Steel")
    bot.Dialogs.AtXY(-11208, 8815, 0x826001)
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Move.XYAndDialog(-4076, 5362, 0x826004, step_name="Quality Steel")
    bot.Move.XYAndDialog(-2888, 7024, 0x84, step_name="SS rebirth Signet")
    bot.Dialogs.AtXY(-2888, 7024, 0x82CB03, step_name="Attribute Points Quest 1")
    bot.Dialogs.AtXY(-2888, 7024, 0x82CB01)
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(-1237.25, 3188.38, 0x85) #Blessing 
    bot.Move.XY(-3225, 1749)
    bot.Move.XY(-995, -2423) #fight
    bot.Move.XY(-513, 67) #fight more
    bot.Wait.UntilOutOfCombat()
    bot.Map.Travel(target_map_id=449) #Kamadan
    bot.Move.XYAndDialog(-11208, 8815, 0x826007, step_name="Accept reward")
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar") # Level 4 skill bar

def Craft_First_Weapon(bot: Botting):
    bot.States.AddHeader("Craft First Weapon")
    bot.Map.Travel(target_map_id=449) #Kamadan
    bot.Move.XYAndInteractNPC(-11270.00, 8785.00)
    bot.Wait.ForTime(1000)
    exec_fn = lambda: Craft1stWeapon(bot)
    bot.States.AddCustomState(exec_fn, "Craft 1st Weapon") 

def Missing_Shipment(bot: Botting):
    bot.States.AddHeader("Quest: Missing Shipment")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-10235, 16557, 0x827501) #need the ink crate
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[2,3,4])
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3128, 2037)
    bot.Move.XY(-7005, 2178)
    bot.Move.XY(-9360, 16311) #gets me in range
    bot.Interact.WithGadgetID(7458)
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-10235, 16557, 0x827507) # +500xp +30 health rune
            
def To_Champions_Dawn(bot: Botting): 
    bot.States.AddHeader("To Champions Dawn")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(-1237.25, 3188.38, 0x85) #Blessing 
    bot.Move.XY(-4507, 616)
    bot.Move.XY(-7611, -5953)
    bot.Move.XY(-18083, -11907) 
    bot.Move.XYAndExitMap(-19518, -13021, target_map_id=479) #unlockChampions Dawn

def Proof_of_Courage_and_Suwash_the_Pirate(bot: Botting):
    bot.States.AddHeader("Quests: Proof of Courage and Suwash the Pirate")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,2,4])
    bot.Move.XYAndDialog(-4358, 6535, 0x829301) #Proof of Courage
    bot.Move.XYAndDialog(-4558, 4693, 0x826201) #Suwash the Pirate
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
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
    bot.Move.XYAndDialog(-15573, -9638, 0x826204) #Suwash the Pirate turnin
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Move.XYAndDialog(-4367, 6542, 0x829307) #Proof of Courage Reward
    bot.Move.XYAndDialog(-4558, 4693, 0x826207) #Suwash the Pirate reward
    bot.Wait.ForTime(2000)

def A_Hidden_Threat(bot: Botting):
    bot.States.AddHeader("Quest: A Hidden Threat")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForMapToChange(target_map_id=431)
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,2,4])
    bot.Move.XYAndDialog(-1835, 6505, 0x825A01) #Shaurom
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3133.28, 1979.03)
    bot.Move.XY(-13230, -148) 
    bot.Move.XY(-16920, 746) 
    bot.Move.XY(-17706, 3259)
    bot.Move.XYAndDialog(-17706, 3259, 0x85) #Blessing 
    bot.Wait.ForTime(2000)
    bot.Move.XY(-19751, 8180) 
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-17673, 11492) 
    bot.Move.XY(-18751, 14973) 
    bot.Move.XY(-17535.23, 18600) 
    bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndExitMap(-20136, 16757, target_map_id=502) #The Astralarium
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Move.XYAndDialog(-1835, 6505, 0x825A07) #A Hidden Threat reward

def Unlock_Secondary_Profession(bot: Botting):  
    bot.States.AddHeader("Unlock Secondary  Profession")
    bot.Map.Travel(target_map_id=449) #Kamadan
    bot.Party.LeaveParty()
    bot.Move.XYAndDialog(-7910, 9740, 0x828907)
    bot.Dialogs.AtXY(-7910, 9740, 0x825901)
    bot.Move.XYAndDialog(-7525, 6288, 0x81)
    bot.Dialogs.AtXY(-7525, 6288, 0x84)
    bot.Wait.ForMapToChange(target_map_id=456)
    ConfigurePacifistEnv(bot)
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if profession == "Necromancer": 
        bot.Move.XYAndDialog(-7149, 1830, 0x7F) #Mesmer
        bot.Move.XYAndDialog(-7161, 4808, 0x825907)
    else:    
        bot.Move.XYAndDialog(-6557.00, 1837, 0x7F) #this is fine, need minimal skill bar for level 4 to avoid skill equip window
        bot.Move.XYAndDialog(-7161, 4808, 0x825907)
    
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if profession == "Warrior":
        bot.Move.XYAndDialog(-7161, 4808, 0x8A) #Dervish 2nd
        bot.Dialogs.AtXY(-7161, 4808, 0x825407)
        bot.Dialogs.AtXY(-7161, 4808, 0x827801)
    elif profession in ["Necromancer", "Monk", "Elementalist"]:
        bot.Move.XYAndDialog(-7161, 4808, 0x84) #Mes 2nd
        bot.Dialogs.AtXY(-7161, 4808, 0x825407)
        bot.Dialogs.AtXY(-7161, 4808, 0x827801)  
    else:   
        bot.Dialogs.AtXY(-7161, 4808, 0x88) #change to Warrior
        bot.Dialogs.AtXY(-7161, 4808, 0x825407)
        bot.Dialogs.AtXY(-7161, 4808, 0x827801)

def Configure_Player_Build(bot: Botting):
    bot.States.AddHeader("Configure Player Build")
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    # First: Buy Mesmer skills in Kamadan for specific professions
    if profession in ["Mesmer", "Elementalist", "Monk", "Necromancer"]:
        bot.Map.Travel(target_map_id=449) #Kamadan
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x853702) #Wastrels Demise
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x867902) #Signet of Clumsiness  
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x883603) #Cry of Pain
    elif profession == "Ranger":
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x857A02) # Critical Chop
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x815402) #Disrupting Chop
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x81A802) #Throw Dirt
    elif profession == "Paragon":
        bot.Move.XYAndDialog(-11385, 16140, 0x860B02) #Mighty Throw

    # Second: Travel to Sunspear Great Hall and get profession-specific skills
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForMapToChange(target_map_id=431)
    bot.Move.XYAndDialog(-2864, 7031, 0x82CB07)
    
    if profession == "Dervish":
        bot.Move.XYAndDialog(-3317, 7053, 0x883B03) #Whirlwind Attack"
        bot.Dialogs.AtXY(-3317, 7053, 0x86E302) #Zealous Renewal
        bot.Dialogs.AtXY(-3317, 7031, 0x85CF02) #Twin Moon Sweep
        bot.Dialogs.AtXY(-3317, 7053, 0x85) #Buy hero point
        bot.Dialogs.AtXY(-3317, 7031, 0x85DF02) #Mystic Vigor
    elif profession == "Paragon":
        bot.Move.XYAndDialog(-3317, 7053, 0x884003) #There's Nothing to Fear
        bot.Dialogs.AtXY(-3317, 7053, 0x860E02) #Unblockable Throw"
    elif profession == "Elementalist":
        bot.Move.XYAndDialog(-3317, 7053, 0x803D02) #Leech Signet
        bot.Dialogs.AtXY(-3317, 7053, 0x854002) #Web of Disruption
        bot.Dialogs.AtXY(-3317, 7053, 0x85) #Buy hero point
        bot.Dialogs.AtXY(-3317, 7053, 0x801702) #Power Spike"
    elif profession == "Mesmer":
        bot.Move.XYAndDialog(-3317, 7053, 0x803D02) #Leech Signet
        bot.Dialogs.AtXY(-3317, 7053, 0x854002) #Web of Disruption
        bot.Dialogs.AtXY(-3317, 7053, 0x85) #Buy hero point
        bot.Dialogs.AtXY(-3317, 7053, 0x801702) #Power Spike"
    elif profession == "Necromancer":
        bot.Move.XYAndDialog(-3317, 7053, 0x803D02) #Leech Signet
        bot.Dialogs.AtXY(-3317, 7053, 0x854002) #Web of Disruption
        bot.Dialogs.AtXY(-3317, 7053, 0x85) #Buy hero point
        bot.Dialogs.AtXY(-3317, 7053, 0x801702) #Power Spike
    elif profession == "Monk":
        bot.Move.XYAndDialog(-3317, 7053, 0x803D02) #Leech Signet
        bot.Dialogs.AtXY(-3317, 7053, 0x854002) #Web of Disruption
        bot.Dialogs.AtXY(-3317, 7053, 0x85) #Buy hero point
        bot.Dialogs.AtXY(-3317, 7053, 0x801702) #Power Spike
    elif profession == "Warrior":
        bot.Move.XYAndDialog(-3317, 7053, 0x883B03) #Whirlwind Attack"
        bot.Dialogs.AtXY(-3317, 7053, 0x86E302) #Zealous Renewal
    elif profession == "Ranger":
        bot.Move.XYAndDialog(-3317, 7053, 0x883B03) #Whirlwind Attack"
        

    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Dialogs.AtXY(-2864, 7031, 0x82CC03)
    bot.Dialogs.AtXY(-2864, 7031, 0x82CC01)

def Leaving_A_Legacy(bot: Botting):
    bot.States.AddHeader("Quest: Leaving A Legacy")
    bot.Map.Travel(target_map_id=479) #Champions Dawn
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,2,7])
    bot.Move.XYAndDialog(22884, 7641, 0x827804)
    bot.Move.XYAndExitMap(22483, 6115, target_map_id=432) #Cliffs of Dohjok
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(20215, 5285)
    bot.Move.XYAndDialog(20215, 5285, 0x85) #Blessing 
    bot.Wait.ForTime(2000)
    bot.Move.XYAndDialog(18008, 6024, 0x827804) #Dunkoro
    bot.Move.XY(13677, 6800)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7255, 5150)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-13255, 6535)
    bot.Dialogs.AtXY(-13255, 6535, 0x84) #Hamar
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
    bot.Move.XYAndDialog(2888, 2207, 0x827807)
    bot.Dialogs.AtXY(2888, 2207, 0x827901)

def Craft_Player_Armor(bot: Botting):
    bot.States.AddHeader("Craft Player Armor")
    bot.Map.Travel(target_map_id=491)
    bot.Move.XYAndInteractNPC(3857.42, 1700.62)  # Material merchant
    bot.States.AddCustomState(BuyMaterials, "Buy Materials")
    bot.Move.XYAndInteractNPC(3891.62, 2329.84)  # Armor crafter
    bot.Wait.ForTime(1000)  # small delay to let the window open
    exec_fn = lambda: CraftArmor(bot)
    bot.States.AddCustomState(exec_fn, "Craft Armor")

def Craft_Player_Weapon(bot: Botting):
    bot.States.AddHeader("Craft Weapon")
    bot.Move.XYAndInteractNPC(3857.42, 1700.62)  # Material merchant
    bot.States.AddCustomState(BuyWeaponMaterials, "Buy Weapon Materials")
    bot.Move.XY(4108.39, 2211.65)
    bot.Dialogs.WithModel(4778, 0x86)  # Weapon crafter Dec New ID
    bot.Wait.ForTime(1000)  # small delay to let the window open
    exec_fn = lambda: CraftWeapon(bot)
    bot.States.AddCustomState(exec_fn, "Craft Weapon")

def Destroy_Starter_Armor_And_Useless_Items(bot: Botting):
    bot.States.AddHeader("Destroy Starter Armor And Useless Items")
    bot.States.AddCustomState(destroy_starter_armor_and_useless_items, "Destroy starter armor and useless items")

def destroy_starter_armor_and_useless_items() -> Generator[Any, Any, None]:
    """Destroy starter armor pieces based on profession and useless items."""
    global starter_armor
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    # Profession-specific starter armor model IDs
    if primary == "Dervish":
        starter_armor = [15712,  # Head
                        15710,  # Chest
                        15711,  # Gloves
                        15713,  # Pants
                        15709   # Boots
                        ]
    elif primary == "Paragon":
        starter_armor = [15717,  # Head
                        15715,  # Chest
                        15716,  # Gloves
                        15718,  # Pants
                        15714   # Boots
                        ]
    elif primary == "Warrior":
        starter_armor = [15702,  # Head
                        15700,  # Chest
                        15701,  # Gloves
                        15703,  # Pants
                        15699   # Boots
                        ]
    elif primary == "Ranger":
        starter_armor = [15707,  # Head
                        15705,  # Chest
                        15706,  # Gloves
                        15708,  # Pants
                        15704   # Boots
                        ]
    elif primary == "Monk":
        starter_armor = [15697,  # Head
                        15695,  # Chest
                        15696,  # Gloves
                        15698,  # Pants
                        15694   # Boots
                        ]
    elif primary == "Elementalist":
        starter_armor = [15692,  # Head
                        15690,  # Chest
                        15691,  # Gloves
                        15693,  # Pants
                        15689   # Boots
                        ]
    elif primary == "Mesmer":
        starter_armor = [15682,  # Head
                        15680,  # Chest
                        15681,  # Gloves
                        15683,  # Pants
                        15679   # Boots
                        ]
    elif primary == "Necromancer":
        starter_armor = [15687,  # Head
                        15685,  # Chest
                        15686,  # Gloves
                        15688,  # Pants
                        15684   # Boots
                        ]
    
    useless_items = [17081,  # Battle Commendation
                     477,    # Starter Bow
                     2787,   # Starter Holy Rod
                     2652,   # Starter Cane
                     2694,   #Starter Truncheon
                     2982,   # Starter Sword
                     2742,   #Starter Elemental Rod
                     15591,  #Starter Scythe
                     15593,  #Starter Spear
                     18901,  #Monk 1st Staff
                     16227,   #1st Scythe Warrior and Dervish
                     30853, #MOX Manual
                    ]


    for model in starter_armor:
        result = yield from Routines.Yield.Items.DestroyItem(model)
    
    for model in useless_items:
        result = yield from Routines.Yield.Items.DestroyItem(model)

def Farm_Until_Level_10(bot):
    bot.States.AddHeader("Farm Until Level 10")
    bot.Map.Travel(target_map_id=491) #Jokanur Diggings
    bot.Party.LeaveParty()
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,2,7])
    for _ in range (17):
        bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
        bot.Move.FollowPath([
        (1268, -311),
        (-1618, -783),
        (-2600, -1119),
        (-3546, -1444)
        ])
        bot.Wait.ForMapLoad(target_map_id=481) # Fahranur The First City
        ConfigureAggressiveEnv(bot)
        bot.Move.XYAndDialog(19651, 12237, 0x85) # Blessing
        bot.Move.XY(11182, 14880)
        bot.Move.XY(11543, 6466)
        bot.Move.XY(15193, 5918)
        bot.Move.XY(14485, 16)
        bot.Move.XY(10256, -1393)
        bot.Move.XYAndDialog(11238, -2718, 0x85) # Bounty
        bot.Move.XY(13382, -6837)
        bot.Wait.UntilOutOfCombat()
        bot.Map.Travel(target_map_id=491) #Jokanur Diggings

def Unlock_Remaining_Secondary_Professions(bot: Botting):
    bot.States.AddHeader("Unlock Remaining Secondary Professions")
    bot.Map.Travel(target_map_id=248)  # GTOB
    bot.States.AddCustomState(withdraw_gold, "Get 5000 gold")
    bot.Move.XY(-3151.22, -7255.13)  # Move to profession trainers area
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
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

def Unlock_Mercenary_Heroes(bot: Botting) -> None:
    bot.States.AddHeader("Unlock Mercenary Heroes")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=248)  # GTOB
    bot.Move.XY(-4231.87, -8965.95)
    bot.Dialogs.WithModel(225, 0x800004) # Unlock Mercenary Heroes

def Unlock_Xunlai_Material_Storage(bot: Botting) -> None:
    bot.States.AddHeader("Unlock Xunlai Material Storage")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=248)  # GTOB
    path_to_xunlai = [(-5540.40, -5733.11),(-7050.04, -6392.59),]
    bot.Move.FollowPath(path_to_xunlai) #UNLOCK_XUNLAI_STORAGE_MATERIAL_PANEL
    bot.Dialogs.WithModel(221, 0x800001)
    bot.Dialogs.WithModel(221, 0x800002)  # Unlock Material Storage Panel

def Attribute_Points_Quest_2(bot: Botting):
    bot.States.AddHeader("Attribute Points Quest n. 2")
    bot.States.AddCustomState(lambda: None, "SecondAttPoints_JumpHere")
    bot.Map.Travel(target_map_id=431) # Sunspear Great Hall
    bot.Move.XYAndDialog(-2864, 7031, 0x82CC07)
    bot.Wait.ForTime(2000)

def Unlock_Sunspear_Skills(bot: Botting):
    bot.States.AddHeader("Unlock Sunspear Skills")
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

def To_Boreal_Station(bot: Botting): 
    bot.States.AddHeader("To Boreal Station")
    bot.Map.Travel(target_map_id=449) # Kamadan
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndDialog(-8739, 14200,0x833601) # Bendah
    bot.Move.XYAndExitMap(-9326, 18151, target_map_id=430) # Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(18191, 167, 0x85) #get Mox
    bot.Move.XY(15407, 209)
    #bot.Move.XYAndDialog(13761, -13108, 0x86) # Explore The Fissure
    bot.Move.XYAndDialog(13761, -13108, 0x84) # Yes
    bot.Wait.ForMapToChange(target_map_id=693)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-5475, 8166)
    bot.Move.XY(-454, 10163)
    bot.Move.XY(4450, 10950)
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
    
def To_Eye_Of_The_North_Outpost(bot: Botting): 
    bot.States.AddHeader("To Eye Of The North Outpost")
    bot.Map.Travel(target_map_id=675)  # Boreal Station
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    bot.Move.XYAndExitMap(4684, -27869, target_map_name="Ice Cliff Chasms")
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(3579.07, -22007.27)
    bot.Wait.ForTime(15000)
    bot.Dialogs.AtXY(3537.00, -21937.00, 0x839104)
    bot.Move.XY(3743.31, -15862.36)
    bot.Move.XY(8267.89, -12334.58)
    bot.Move.XY(3607.21, -6937.32)
    bot.Move.XY(2557.23, -275.97) #Eotn_outpost_id
    bot.Wait.ForMapLoad(target_map_id=642)

def Unlock_Eye_Of_The_North_Pool(bot: Botting):
    bot.States.AddHeader("Unlock Eye Of The North Pool")
    bot.Map.Travel(target_map_id=642)
    auto_path_list = [(-4416.39, 4932.36), (-5198.00, 5595.00)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForMapLoad(target_map_id=646)  # hall of monuments id
    bot.Move.XY(-6572.70, 6588.83)
    bot.Dialogs.WithModel(6021, 0x800001) #eotn_pool_cinematic Gwen Dec New ID
    bot.Wait.ForTime(1000)
    bot.Dialogs.WithModel(5959, 0x630) #eotn_pool_cinematic Dec New ID
    bot.Wait.ForTime(1000)
    bot.Dialogs.WithModel(5959, 0x632) #eotn_pool_cinematic Dec New ID
    bot.Wait.ForTime(1000)
    bot.Wait.ForMapToChange(target_map_id=646)  # hall of monuments id
    bot.Dialogs.WithModel(6021, 0x89) #gwen dialog Dec New ID
    bot.Dialogs.WithModel(6021, 0x831904) #gwen dialog Dec New ID
    bot.Move.XYAndDialog(-6133.41, 5717.30, 0x838904) #ogden dialog 
    bot.Move.XYAndDialog(-5626.80, 6259.57, 0x839304) #vekk dialog

def To_Gunnars_Hold(bot: Botting):
    bot.States.AddHeader("To Gunnar's Hold")
    bot.Map.Travel(target_map_id=642) # eotn_outpost_id
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    path = [(-1814.0, 2917.0), (-964.0, 2270.0), (-115.0, 1677.0), (718.0, 1060.0), 
            (1522.0, 464.0)]
    bot.Move.FollowPath(path)
    bot.Wait.ForMapLoad(target_map_id=499)  # Ice Cliff Chasms
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(2825, -481, 0x832801)  # Talk to Jora
    path = [(2548.84, 7266.08),
            (1233.76, 13803.42),
            (978.88, 21837.26),
            (-4031.0, 27872.0),]
    bot.Move.FollowAutoPath(path)
    bot.Wait.ForMapLoad(target_map_id=548)  # Norrhart Domains
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(14546.0, -6043.0)
    bot.Move.XYAndExitMap(15578, -6548, target_map_id=644)  # Gunnar's Hold
    bot.Wait.ForMapLoad(target_map_id=644)  # Gunnar's Hold
    
def Unlock_Kilroy_Stonekin(bot: Botting):
    bot.States.AddHeader("Unlock Kilroy Stonekin")
    bot.Map.Travel(target_map_id=644)  # gunnars_hold_id
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x835A01)
    bot.Dialogs.AtXY(17341.00, -4796.00, 0x84)
    bot.Wait.ForMapLoad(target_map_id=703)  # killroy_map_id
    bot.Templates.Aggressive(enable_imp=False)
    bot.Items.Equip(24897) #brass_knuckles_item_id
    bot.Move.XY(19290.50, -11552.23)
    bot.Wait.UntilOnOutpost()
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x835A07)  # take reward
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if profession == "Dervish":
        bot.Items.Equip(18910) #crafted Scythe
    elif profession == "Paragon":
        bot.Items.Equip(18913)
    elif profession == "Elementalist":
        bot.Items.Equip(6508)
        bot.Wait.ForTime(1000)
        bot.Items.Equip(6514)
    elif profession == "Mesmer":
        bot.Items.Equip(6508)
        bot.Wait.ForTime(1000)
        bot.Items.Equip(6514)
    elif profession == "Monk":
        bot.Items.Equip(18926)
        
def To_Longeyes_Edge(bot: Botting):
    bot.States.AddHeader("To Longeye's Edge")
    bot.Map.Travel(target_map_id=644) # Gunnar's Hold
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    bot.Move.XY(15886.204101, -6687.815917)
    bot.Move.XY(15183.199218, -6381.958984)
    bot.Wait.ForMapLoad(target_map_id=548)  # Norrhart Domains
    ConfigureAggressiveEnv(bot)
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
    ConfigureAggressiveEnv(bot)
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

def Unlock_NPC_For_Vaettir_Farm(bot: Botting):
    bot.States.AddHeader("Unlock NPC For Vaettir Farm")
    bot.Map.Travel(target_map_id=650)  # longeyes_ledge_id
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    bot.Move.XYAndExitMap(-26375, 16180, target_map_name="Bjora Marches")
    ConfigureAggressiveEnv(bot)
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

def To_Doomlore_Shrine(bot: Botting):
    bot.States.AddHeader("To Doomlore Shrine")
    bot.Map.Travel(target_map_id=650) # Longeyes Ledge
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    bot.Move.XY(-22469.261718, 13327.513671)
    bot.Move.XY(-21791.328125, 12595.533203)
    bot.Wait.ForMapLoad(target_map_id=649)  # Grothmar Wardowns
    ConfigureAggressiveEnv(bot)
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
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-16292.620117,  -715.887329)
    bot.Move.XY(-13617.916992,   405.243469)
    bot.Move.XY(-13256.524414,  2634.142089)
    bot.Move.XY(-15958.702148,  6655.416015)
    bot.Move.XY(-14465.992187,  9742.127929)
    bot.Move.XY(-13779.127929, 11591.517578)
    bot.Move.XY(-14929.544921, 13145.501953)
    bot.Move.XY(-15581.598632, 13865.584960)
    bot.Wait.ForMapLoad(target_map_id=655)  # Doomlore Shrine

def To_Sifhalla(bot: Botting):
    bot.States.AddHeader("To Sifhalla")
    bot.Map.Travel(target_map_id=644) # Gunnar's Hold
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    bot.Move.XY(16003.853515, -6544.087402)
    bot.Move.XY(15193.037109, -6387.140625)
    bot.Wait.ForMapLoad(target_map_name="Norrhart Domains")
    ConfigureAggressiveEnv(bot)
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
    ConfigureAggressiveEnv(bot)
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

def To_Olafstead(bot: Botting):
    bot.States.AddHeader("To Olafstead")
    bot.Map.Travel(target_map_id=643) # Sifhalla
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    bot.Move.XY(13510.718750, 19647.238281)
    bot.Move.XY(13596.396484, 19212.427734)
    bot.Wait.ForMapLoad(target_map_name="Drakkar Lake")
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(13946, 14286)
    bot.Move.XY(13950, 2646)
    bot.Move.XY(10394, -3824)
    bot.Move.XY(-11019,-26164)
    bot.Wait.ForMapLoad(target_map_id=553)  # Varajar Fells
    ConfigureAggressiveEnv(bot)
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

def To_Umbral_Grotto(bot: Botting):
    bot.States.AddHeader("To Umbral Grotto")
    bot.Map.Travel(target_map_id=645) # Olafstead
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[5, 6, 7, 9, 4, 3, 2])
    bot.Move.XY(-883.285644, 1212.171020)
    bot.Move.XY(-1452.154785, 1177.976684)
    bot.Wait.ForMapLoad(target_map_id=553)
    ConfigureAggressiveEnv(bot)
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
    ConfigureAggressiveEnv(bot)
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

def To_Consulate_Docks(bot: Botting):
    bot.States.AddHeader("To Consulate Docks")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=449)
    bot.Wait.ForMapLoad(target_map_id=449)  # Kamadan
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Move.XY(-8075.89, 14592.47)
    bot.Move.XY(-6743.29, 16663.21)
    bot.Move.XY(-5271.00, 16740.00)
    bot.Wait.ForMapLoad(target_map_id=429)
    bot.Move.XYAndDialog(-4631.86, 16711.79, 0x85)
    bot.Wait.ForMapToChange(target_map_id=493)  # Consulate Docks

def To_Kaineng_Center(bot: Botting):
    bot.States.AddHeader("To Kaineng Center")
    bot.Map.Travel(target_map_id=493)  # Consulate Docks
    bot.Wait.ForMapLoad(target_map_id=493)
    bot.Move.XYAndDialog(-2546.09, 16203.26, 0x88)
    bot.Wait.ForMapToChange(target_map_id=290)
    bot.Move.XY(-4230.84, 8008.28)
    bot.Move.XYAndDialog(-5134.16, 7004.48, 0x817901)
    bot.Map.Travel(target_map_id=194)  # KC
    bot.Wait.ForMapLoad(target_map_id=194)

def To_Vizunah_Square_Foreign_Quarter(bot: Botting):
    bot.States.AddHeader("To Vizunah Square Foreign Quarter")
    bot.Map.Travel(target_map_id=194)
    PrepareForBattle(bot)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    bot.Party.AddHenchmanList([2, 9, 10, 12])
    bot.Move.XY(3045, -1575)
    bot.Move.XY(3007, -2609)
    bot.Move.XY(2909, -3629)
    bot.Move.XY(3145, -4643)
    bot.Move.XY(3372, -5617)
    bot.Wait.ForMapLoad(target_map_id=240)
    ConfigureAggressiveEnv(bot)
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
    bot.Dialogs.WithModel(3279, 0x800009) # Dec New ID
    bot.Dialogs.WithModel(3279, 0x80000B)  # talk to the guard Dec New ID
    bot.Wait.ForMapToChange(target_map_id=292) #Vizunah Square Foreign

def To_Marketplace(bot: Botting):
    bot.States.AddHeader("To Marketplace")
    bot.Map.Travel(target_map_id=194)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AddHenchmenFC, "Add Henchmen")
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Move.XY(3045, -1575)
    bot.Move.XY(3007, -2609)
    bot.Move.XY(2909, -3629)
    bot.Move.XY(3145, -4643)
    bot.Move.XY(3372, -5617)
    bot.Wait.ForMapLoad(target_map_id=240)
    ConfigureAggressiveEnv(bot)
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

def To_Seitung_Harbor(bot: Botting):
    bot.States.AddHeader("To Seitung Harbor")
    bot.Map.Travel(target_map_id=303)
    bot.Move.XY(12313, 19236)
    bot.Move.XY(10343, 20329)
    bot.Wait.ForMapLoad(target_map_id=302)
    bot.Move.XY(8392, 20845)
    bot.Move.XYAndDialog(6912.20, 19912.12, 0x84)
    bot.Wait.ForMapToChange(target_map_id=250)

def To_Shinjea_Monastery(bot: Botting):
    bot.States.AddHeader("To Shinjea Monastery")
    PrepareForBattle(bot)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AddHenchmenFC, "Add Henchmen")
    bot.Map.Travel(target_map_id=250)
    bot.Move.XY(17367.47, 12161.08)
    bot.Move.XYAndExitMap(15868.00, 13455.00, target_map_id=313)
    bot.Move.XY(574.21, 10806.26)
    bot.Move.XYAndExitMap(382.00, 9925.00, target_map_id=252)
    bot.Move.XYAndExitMap(-5004.50, 9410.41, target_map_id=242)

def To_Tsumei_Village(bot: Botting):
    bot.States.AddHeader("To Tsumei Village")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=242) #Shinjea Monastery
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AddHenchmenFC, "Add Henchmen")
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    ConfigurePacifistEnv(bot)
    bot.Move.XYAndExitMap(-4842, -13267, target_map_id=249) #tsumei_village_map_id

def To_Minister_Cho(bot: Botting):
    bot.States.AddHeader("To Minister Cho")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=242) #Shinjea Monastery
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AddHenchmenFC, "Add Henchmen")
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    ConfigurePacifistEnv(bot)
    bot.Move.XY(6611.58, 15847.51)
    bot.Move.FollowPath([(6874, 16391)])
    bot.Wait.ForMapLoad(target_map_id=214) #minister_cho_map_id

def To_Lions_Arch(bot: Botting):
    bot.States.AddHeader("To Lion's Arch")
    bot.Map.Travel(target_map_id=493)  # Consulate Docks
    bot.Wait.ForMapLoad(target_map_id=493)
    bot.Move.XYAndDialog(-2546.09, 16203.26, 0x89)
    bot.Wait.ForMapToChange(target_map_name="Lion's Gate")
    bot.Move.XY(-1181, 1038)
    bot.Dialogs.WithModel(2011, 0x85)  # Neiro dialog model id 1961
    bot.Move.XY(-1856.86, 1434.14)
    bot.Move.FollowPath([(-2144, 1450)])
    bot.Wait.ForMapLoad(target_map_id=55) #has built in wait time now

def To_Temple_Of_The_Ages(bot: Botting):
    bot.States.AddHeader("To Temple of the Ages")
    bot.Map.Travel(target_map_id=55)  # Lion's Arch
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.AddHenchmanList([1, 3])
    bot.Move.XY(1219, 7222)
    bot.Move.XY(1021, 10651)
    bot.Move.XY(250, 12350)
    bot.Wait.ForMapLoad(target_map_id=58)  # North Kryta Province
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(5116.0, -17415.0)
    bot.Move.XY(2346.0, -17307.0)
    bot.Move.XY(757.0, -16768.0)
    bot.Move.XY(-1521.0, -16726.0)
    bot.Move.XY(-3246.0, -16407.0)
    bot.Move.XY(-6042.0, -16126.0)
    bot.Move.XY(-7706.0, -17248.0)
    bot.Move.XY(-8910.0, -17561.0)
    bot.Move.XY(-9893.0, -17625.0)
    bot.Move.XY(-11325.0, -18358.0)
    bot.Move.XY(-11553.0, -19246.0)
    bot.Move.XY(-11600.0, -19500.0)
    bot.Move.XY(-11708, -19957)
    bot.Wait.ForMapLoad(target_map_id=15)  # D'Alessio Seaboard outpost
    bot.Move.XY(16000, 17080)
    bot.Move.XY(16030, 17200)
    bot.Wait.ForMapLoad(target_map_id=58)  # North Kryta Province
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-11453.0, -18065.0)
    bot.Move.XY(-10991.0, -16776.0)
    bot.Move.XY(-10791.0, -15737.0)
    bot.Move.XY(-10130.0, -14138.0)
    bot.Move.XY(-10106.0, -13005.0)
    bot.Move.XY(-10558.0, -9708.0)
    bot.Move.XY(-10319.0, -7888.0)
    bot.Move.XY(-10798.0, -5941.0)
    bot.Move.XY(-10958.0, -1009.0)
    bot.Move.XY(-10572.0, 2332.0)
    bot.Move.XY(-10784.0, 3710.0)
    bot.Move.XY(-11125.0, 4650.0)
    bot.Move.XY(-11690.0, 5496.0)
    bot.Move.XY(-12931.0, 6726.0)
    bot.Move.XY(-13340.0, 7971.0)
    bot.Move.XY(-13932.0, 9091.0)
    bot.Move.XY(-13937.0, 11521.0)
    bot.Move.XY(-14639.0, 13496.0)
    bot.Move.XY(-15090.0, 14734.0)
    bot.Move.XY(-16653.0, 16226.0)
    bot.Move.XY(-18944.0, 14799.0)
    bot.Move.XY(-19468.0, 15449.0)
    bot.Move.XY(-19550.0, 15625.0)
    bot.Wait.ForMapLoad(target_map_id=59)  # Nebo Terrace
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(19271.0, 5207.0)
    bot.Move.XY(18307.0, 5369.0)
    bot.Move.XY(17704.0, 4786.0)
    bot.Move.XY(17801.0, 2710.0)
    bot.Move.XY(18221.0, 506.0)
    bot.Move.XY(18133.0, -1406.0)
    bot.Move.XY(16546.0, -4102.0)
    bot.Move.XY(15434.0, -6217.0)
    bot.Move.XY(14927.0, -8731.0)
    bot.Move.XY(14297.0, -10366.0)
    bot.Move.XY(14347.0, -12097.0)
    bot.Move.XY(15373.0, -14769.0)
    bot.Move.XY(15425.0, -15035.0)
    bot.Wait.ForMapLoad(target_map_id=57)  # Bergen Hot Springs
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    bot.Party.AddHenchmanList([1, 3])
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Move.XY(15521, -15378)
    bot.Move.XY(15450, -15050)
    bot.Wait.ForMapLoad(target_map_id=59)  # Nebo Terrace
    bot.Move.XY(15378, -14794)
    bot.Wait.ForMapLoad(target_map_id=59)  # Nebo Terrace
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(13276.0, -14317.0)
    bot.Move.XY(10761.0, -14522.0)
    bot.Move.XY(8660.0, -12109.0)
    bot.Move.XY(6637.0, -9216.0)
    bot.Move.XY(4995.0, -7951.0)
    bot.Move.XY(1522.0, -7990.0)
    bot.Move.XY(-924.0, -10670.0)
    bot.Move.XY(-3489.0, -11607.0)
    bot.Move.XY(-4086.0, -11692.0)
    bot.Move.XY(-4290.0, -11599.0)
    bot.Wait.ForMapLoad(target_map_id=56)  # Cursed Lands
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-4523.0, -9755.0)
    bot.Move.XY(-4067.0, -8786.0)
    bot.Move.XY(-4207.0, -7806.0)
    bot.Move.XY(-5497.0, -6137.0)
    bot.Move.XY(-7331.0, -6178.0)
    bot.Move.XY(-8784.0, -4598.0)
    bot.Move.XY(-9053.0, -2929.0)
    bot.Move.XY(-9610.0, -2136.0)
    bot.Move.XY(-10879.0, -1685.0)
    bot.Move.XY(-10731.0, -760.0)
    bot.Move.XY(-12517.0, 5459.0)
    bot.Move.XY(-15510.0, 7154.0)
    bot.Move.XY(-18010.0, 7033.0)
    bot.Move.XY(-18717.0, 7537.0)
    bot.Move.XY(-19896.0, 8964.0)
    bot.Move.XY(-20100.0, 9025.0)
    bot.Wait.ForMapLoad(target_map_id=18)  # The Black Curtain 
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(8716.0, 18587.0)
    bot.Move.XY(5616.0, 17732.0)
    bot.Move.XY(3795.0, 17750.0)
    bot.Move.XY(1938.0, 16994.0)
    bot.Move.XY(592.0, 16243.0)
    bot.Move.XY(-686.0, 14967.0)
    bot.Move.XY(-1968.0, 14407.0)
    bot.Move.XY(-3398.0, 14730.0)
    bot.Move.XY(-4340.0, 14938.0)
    bot.Move.XY(-5004.0, 15424.0)
    bot.Move.XY(-5207.0, 15882.0)
    bot.Move.XY(-5180.0, 16000.0)
    bot.Wait.ForMapLoad(target_map_id=138)  # Temple of the Ages
#region MAIN
selected_step = 0
filter_header_steps = True

iconwidth = 96

def _draw_texture():
    global iconwidth
    level = Agent.GetLevel(Player.GetAgentID())

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


bot.SetMainRoutine(create_bot_routine)
bot.UI.override_draw_texture(_draw_texture)
bot.UI.override_draw_config(lambda: _draw_settings(bot))

def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()

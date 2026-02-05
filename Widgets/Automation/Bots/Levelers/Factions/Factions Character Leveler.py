from __future__ import annotations
from typing import List, Tuple, Generator, Any
import PyImGui
import os
from Py4GW import Game
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui, ActionQueueManager, Map, Agent, Player, UIManager)
from Py4GWCoreLib.enums_src.UI_enums import UIMessage

bot = Botting("Factions Leveler",
              upkeep_birthday_cupcake_restock=10,
              upkeep_honeycomb_restock=20,
              upkeep_war_supplies_restock=2,
              upkeep_auto_inventory_management_active=False,
              upkeep_auto_combat_active=False,
              upkeep_auto_loot_active=True)

#region MainRoutine
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    Exit_Monastery_Overlook(bot)
    Forming_A_Party(bot)
    Unlock_Secondary_Profession(bot)
    Unlock_Xunlai_Storage(bot)
    Craft_Weapon(bot)
    #Charm_Pet(bot)
    To_Minister_Chos_Estate(bot)
    Unlock_Skills_Trainer(bot)
    Minister_Chos_Estate_Mission(bot)
    Attribute_Points_Quest_1(bot)
    Warning_The_Tengu(bot)
    The_Threat_Grows(bot)
    The_Road_Less_Traveled(bot)
    Craft_Seitung_Armor(bot)
    To_Zen_Daijun(bot)
    Zen_Daijun_Mission(bot)
    Craft_Remaining_Seitung_Armor(bot)
    Destroy_Starter_Armor_And_Useless_Items(bot)
    To_Marketplace(bot)
    To_Kaineng_Center(bot)
    Craft_Max_Armor(bot)
    Destroy_Seitung_Armor(bot)
    Extend_Inventory_Space(bot)
    To_Boreal_Station(bot)
    To_Eye_of_the_North(bot)
    Unlock_Eye_Of_The_North_Pool(bot)
    Attribute_Points_Quest_2(bot)
    To_Gunnars_Hold(bot)
    Unlock_Kilroy_Stonekin(bot)
    To_Longeyes_Edge(bot)
    Unlock_NPC_For_Vaettir_Farm(bot)
    To_Lions_Arch(bot)
    To_Temple_of_The_Ages(bot)
    To_Kamadan(bot)
    To_Consulate_Docks(bot)
    Unlock_Olias(bot)
    Unlock_Xunlai_Material_Panel(bot)
    Unlock_Remaining_Secondary_Professions(bot)
    Unlock_Mercenary_Heroes(bot)

#region Helpers
def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.Templates.Pacifist()
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Disable("honeycomb")
    bot.Properties.Disable("war_supplies")
    bot.Items.SpawnAndDestroyBonusItems()
    bot.Items.Restock.BirthdayCupcake()
    bot.Items.Restock.WarSupplies()
    
def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Templates.Aggressive()
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Enable("honeycomb")
    bot.Properties.Enable("war_supplies")
    bot.Items.SpawnAndDestroyBonusItems()

    
def EquipSkillBar(skillbar = ""): 
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    level = Agent.GetLevel(Player.GetAgentID())

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
        if level <= 3: #10 attribute points available
            skillbar = "OwVBIkkDcdGoBAAAAACA"
        elif level <= 4: #15 attribute points available
            skillbar = "OwVBIlkDcdGoBAAAAACA"
        elif level <= 5: #20 attribute points available
            skillbar = "OwVBIlkDcdGoBAAAAACA"
        elif level <= 6: #25 attribute points available
            skillbar = "OwVBImkDcdGoBAAAAACA"
        elif level <= 7: #45 attribute points available (including 15 attribute points from quests)
            skillbar = "OwVBIokDcdGoBAAAAACA"
        elif level <= 8: #50 attribute points available
            skillbar = "OwVBIpkDcdGoBAAAAACA"
        elif level <= 9: #55 attribute points available
            skillbar = "OwVCI5MSOw1ZgGAAAAAIAA"
        elif level <= 10: #55 attribute points available
            skillbar = "OwVCI5QSOw1ZgGAAAAAIAA"
        else: #20 attribute points available
            skillbar = "OwVBIpkDcdGoBAAAAACA"

    yield from Routines.Yield.Skills.LoadSkillbar(skillbar)

def EquipCaptureSkillBar(skillbar = ""): 
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if profession == "Warrior": skillbar = "OQIAEbGAAAAAAAAAAA"
    elif profession == "Ranger": skillbar = "OgAAEbGAAAAAAAAAAA"
    elif profession == "Monk": skillbar = "OwIAEbGAAAAAAAAAAA"
    elif profession == "Necromancer": skillbar = "OAJAEbGAAAAAAAAAAA"
    elif profession == "Mesmer": skillbar = "OQJAEbGAAAAAAAAAAA"
    elif profession == "Elementalist": skillbar = "OgJAEbGAAAAAAAAAAA"
    elif profession == "Ritualist": skillbar = "OAKkYRYRWCGxmBAAAAAAAAAA"
    elif profession == "Assassin": skillbar = "OwJkYRZ5XMGxmBAAAAAAAAAA"

    yield from Routines.Yield.Skills.LoadSkillbar(skillbar)

def AddHenchmen():
    def _add_henchman(henchman_id: int):
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(henchman_id)
        ConsoleLog("addhenchman",f"Added Henchman: {henchman_id}", log=False)
        yield from Routines.Yield.wait(250)
        
    party_size = Map.GetMaxPartySize()

    henchmen_list = []
    if party_size <= 4:
        henchmen_list.extend([2, 3, 1]) 
    elif Map.GetMapID() == Map.GetMapIDByName("Seitung Harbor"):
        henchmen_list.extend([2, 3, 1, 6, 5]) 
    elif Map.GetMapID() == 213: # Zen_daijun_map_id
        henchmen_list.extend([2,3,1,8,5])
    elif Map.GetMapID() == Map.GetMapIDByName("The Marketplace"):
        henchmen_list.extend([6,9,5,1,4,7,3])
    elif Map.GetMapID() == 194: # Kaineng_map_id
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
            "OQhkAsC8gFKgGckjHFRUGCA",  # 1 Gwen
            "OgVDI8gsCawROeUEtZIA",     # 2 Vekk
            "OwUUMsG/E4GgMnZskzkIZQAA"  # 3 Ogden
        ]
    # Add all heroes
    for hero_id in hero_list:
        yield from _add_hero(hero_id)
    
    # Load skillbars for all positions
    for position in range(len(hero_list)):
        GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(position + 1, skill_templates[position])
        ConsoleLog("skillbar", f"Loading skillbar for position {position + 1}", log=True)
        yield from Routines.Yield.wait(500)

def PrepareForBattle(bot: Botting):
    ConfigureAggressiveEnv(bot)
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AddHenchmen, "Add Henchmen")
    bot.Items.Restock.BirthdayCupcake()
    bot.Items.Restock.Honeycomb()
    bot.Items.Restock.WarSupplies()
  
def GetArmorMaterialPerProfession(headpiece = False) -> int:
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
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
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
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

def GetMaxArmorCommonMaterial() -> int:
    """Returns the common material type for max armor crafting in Kaineng."""
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary == "Warrior":
        return ModelID.Tanned_Hide_Square.value
    elif primary == "Ranger":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Monk":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Assassin":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Mesmer":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Necromancer":
        return ModelID.Tanned_Hide_Square.value
    elif primary == "Ritualist":
        return ModelID.Bolt_Of_Cloth.value
    elif primary == "Elementalist":
        return ModelID.Bolt_Of_Cloth.value
    else:
        return ModelID.Bolt_Of_Cloth.value

def GetMaxArmorRareMaterial() -> int | None:
    """Returns the rare material type for max armor, None if not needed.
    Note: Necromancer and Monk need 2 rare materials (handled in BuyMaxArmorMaterials and DoCraftMaxArmor)."""
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary == "Warrior":
        return ModelID.Steel_Ingot.value
    elif primary == "Ranger":
        return ModelID.Fur_Square.value
    elif primary == "Monk":
        return ModelID.Roll_Of_Parchment.value  # Also needs Bolt_Of_Linen (handled separately)
    elif primary == "Assassin":
        return ModelID.Leather_Square.value
    elif primary == "Mesmer":
        return ModelID.Bolt_Of_Silk.value
    elif primary == "Necromancer":
        return ModelID.Roll_Of_Parchment.value  # Also needs Vial_Of_Ink (handled separately)
    elif primary == "Ritualist":
        return ModelID.Leather_Square.value
    elif primary == "Elementalist":
        return ModelID.Bolt_Of_Silk.value
    else:
        return None

def GetArmorCrafterCoords() -> tuple[float, float]:
    """Returns the armor crafter coordinates based on profession."""
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary == "Warrior":
        return (-891.00, -5382.00) #Suki armor npc
    elif primary == "Ranger":
        return (-700.00, -5156.00) #Kakumei armor npc
    elif primary == "Monk":
        return (-891.00, -5382.00)  #Suki armor npc
    elif primary == "Assassin":
        return (-700.00, -5156.00) #Kakumei armor npc
    elif primary == "Mesmer":
        return (-1682.00, -3970.00) #Ryoko armor npc
    elif primary == "Necromancer":
        return (-1682.00, -3970.00) #Ryoko armor npc
    elif primary == "Ritualist":
        return (-1682.00, -3970.00) #Ryoko armor npc
    elif primary == "Elementalist":
        return (-1682.00, -3970.00) #Ryoko armor npc
    else:
        return (-1682.00, -3970.00) #default Ryoko armor npc

def GetMaxArmorPiecesByProfession(bot: Botting):
    """Returns model IDs for max armor pieces in Kaineng."""
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    HEAD, CHEST, GLOVES, PANTS, BOOTS = 0, 0, 0, 0, 0

    if primary == "Warrior":
        HEAD = 23391    # Ascalon
        CHEST = 23394
        GLOVES = 23395
        PANTS = 23396
        BOOTS = 23393
    elif primary == "Ranger":
        HEAD = 23794    # Canthan
        CHEST = 23797
        GLOVES = 23798
        PANTS = 23799
        BOOTS = 23796
    elif primary == "Monk":
        HEAD = 23201    # Ascalon
        CHEST = 23377
        GLOVES = 23378
        PANTS = 23379
        BOOTS = 23376
    elif primary == "Assassin":
        HEAD = 23435    # Canthan
        CHEST = 23441
        GLOVES = 23442
        PANTS = 23443
        BOOTS = 23440
    elif primary == "Mesmer":
        HEAD = 23576    # Shinjea
        CHEST = 23581
        GLOVES = 23582
        PANTS = 23583
        BOOTS = 23580
    elif primary == "Necromancer":
        HEAD = 23633    # Shinjea
        CHEST = 23637
        GLOVES = 23638
        PANTS = 23639
        BOOTS = 23636
    elif primary == "Ritualist":
        HEAD = 23939    # Shinjea
        CHEST = 23941
        GLOVES = 23942
        PANTS = 23943
        BOOTS = 23940
    elif primary == "Elementalist":
        HEAD = 23643    # Shinjea
        CHEST = 23670
        GLOVES = 23671
        PANTS = 23672
        BOOTS = 23669

    return HEAD, CHEST, GLOVES, PANTS, BOOTS

def BuyMaxArmorMaterials(material_type: str = "common"):
    """Buy max armor materials. Pass 'common' or 'rare' to specify which type."""
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    if material_type == "common":
        # Necromancer needs two common materials: Tanned Hide and Bone
        if primary == "Necromancer":
            for _ in range(18):  # Buy 180 tanned hide (18 purchases x 10 per unit = 180)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Tanned_Hide_Square.value)
            for _ in range(18):  # Buy 180 bone (18 purchases x 10 per unit = 180)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Bone.value)
        # Monk needs two common materials: Bolt of Cloth and Feathers
        elif primary == "Monk":
            for _ in range(18):  # Buy 180 bolt of cloth (18 purchases x 10 per unit = 180)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Bolt_Of_Cloth.value)
            yield from Routines.Yield.wait(500)  # Wait between material types
            for _ in range(1):  # Buy 10 feathers (1 purchase x 10 per unit = 10)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Feather.value)
        # Ranger needs only bolt of cloth as common material
        elif primary == "Ranger":
            for _ in range(20):  # Buy 200 bolt of cloth (20 purchases x 10 per unit = 200)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Bolt_Of_Cloth.value)
        # Elementalist needs two common materials: Bolt of Cloth and Pile of Glittering Dust
        elif primary == "Elementalist":
            for _ in range(18):  # Buy 180 bolt of cloth (18 purchases x 10 per unit = 180)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Bolt_Of_Cloth.value)
            yield from Routines.Yield.wait(500)  # Wait between material types
            for _ in range(3):  # Buy 30 pile of glittering dust (3 purchases x 10 per unit = 30)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Pile_Of_Glittering_Dust.value)
        # Ritualist needs standard 200 + additional 30 bolt of cloth
        elif primary == "Ritualist":
            for _ in range(23):  # Buy 230 bolt of cloth (23 purchases x 10 per unit = 230)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Bolt_Of_Cloth.value)
        else:
            for _ in range(20):  # Buy 200 common materials (20 purchases x 10 per unit = 200)
                yield from Routines.Yield.Merchant.BuyMaterial(GetMaxArmorCommonMaterial())
    elif material_type == "rare":
        # Necromancer needs two rare materials: Roll of Parchment and Vial of Ink
        if primary == "Necromancer":
            for _ in range(5):  # Buy 5 Roll of Parchment
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Roll_Of_Parchment.value)
            for _ in range(4):  # Buy 4 Vial of Ink
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Vial_Of_Ink.value)
        # Monk needs two rare materials: Roll of Parchment and Bolt of Linen
        elif primary == "Monk":
            for _ in range(25):  # Buy 25 Roll of Parchment
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Roll_Of_Parchment.value)
            yield from Routines.Yield.wait(500)  # Wait between material types
            for _ in range(28):  # Buy 28 Bolt of Linen
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Bolt_Of_Linen.value)
        # Ranger needs only fur square as rare material
        elif primary == "Ranger":
            for _ in range(32):  # Buy 32 Fur Square
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Fur_Square.value)
        # Elementalist needs two rare materials: Bolt of Silk and Tempered Glass Vial
        elif primary == "Elementalist":
            for _ in range(28):  # Buy 28 Bolt of Silk
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Bolt_Of_Silk.value)
            yield from Routines.Yield.wait(500)  # Wait between material types
            for _ in range(4):  # Buy 4 Tempered Glass Vial
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Tempered_Glass_Vial.value)
        # Ritualist needs standard 32 + additional 4 leather square
        elif primary == "Ritualist":
            for _ in range(36):  # Buy 36 Leather Square (32 + 4)
                yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Leather_Square.value)
        else:
            rare_material = GetMaxArmorRareMaterial()
            if rare_material is not None:
                for _ in range(32):  # Buy 32 rare materials (32 purchases x 1 per unit = 32)
                    yield from Routines.Yield.Merchant.BuyMaterial(rare_material)

def DoCraftMaxArmor(bot: Botting):
    """Core max armor crafting logic - assumes already at armor crafter NPC."""
    HEAD, CHEST, GLOVES, PANTS, BOOTS = GetMaxArmorPiecesByProfession(bot)
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    # Max armor needs both common and rare materials
    rare_mat = GetMaxArmorRareMaterial()
    if rare_mat is not None:
        # Necromancer has unique materials: 180 tanned hide + 180 bone + 5 parchment + 4 ink
        if primary == "Necromancer":
            armor_pieces = [
                (GLOVES, [ModelID.Tanned_Hide_Square.value, ModelID.Bone.value, ModelID.Roll_Of_Parchment.value, ModelID.Vial_Of_Ink.value], [20, 20, 1, 0]),
                (BOOTS, [ModelID.Tanned_Hide_Square.value, ModelID.Bone.value, ModelID.Roll_Of_Parchment.value, ModelID.Vial_Of_Ink.value], [20, 20, 1, 1]),
                (PANTS, [ModelID.Tanned_Hide_Square.value, ModelID.Bone.value, ModelID.Roll_Of_Parchment.value, ModelID.Vial_Of_Ink.value], [45, 45, 1, 1]),
                (CHEST, [ModelID.Tanned_Hide_Square.value, ModelID.Bone.value, ModelID.Roll_Of_Parchment.value, ModelID.Vial_Of_Ink.value], [70, 70, 1, 1]),
                (HEAD, [ModelID.Tanned_Hide_Square.value, ModelID.Bone.value, ModelID.Roll_Of_Parchment.value, ModelID.Vial_Of_Ink.value], [25, 25, 1, 1]),
            ]
        # Monk has unique materials: 180 bolt of cloth + 10 feathers + 25 parchment + 28 linen
        elif primary == "Monk":
            armor_pieces = [
                (GLOVES, [ModelID.Bolt_Of_Cloth.value, ModelID.Feather.value, ModelID.Roll_Of_Parchment.value, ModelID.Bolt_Of_Linen.value], [20, 2, 5, 4]),
                (BOOTS, [ModelID.Bolt_Of_Cloth.value, ModelID.Feather.value, ModelID.Roll_Of_Parchment.value, ModelID.Bolt_Of_Linen.value], [20, 2, 5, 4]),
                (PANTS, [ModelID.Bolt_Of_Cloth.value, ModelID.Feather.value, ModelID.Roll_Of_Parchment.value, ModelID.Bolt_Of_Linen.value], [45, 2, 5, 8]),
                (CHEST, [ModelID.Bolt_Of_Cloth.value, ModelID.Feather.value, ModelID.Roll_Of_Parchment.value, ModelID.Bolt_Of_Linen.value], [70, 2, 5, 8]),
                (HEAD, [ModelID.Bolt_Of_Cloth.value, ModelID.Feather.value, ModelID.Roll_Of_Parchment.value, ModelID.Bolt_Of_Linen.value], [25, 2, 5, 4]),
            ]
        # Ranger has standard materials: 200 bolt of cloth + 32 fur square (uses default case)
        elif primary == "Ranger":
            armor_pieces = [
                (GLOVES, [ModelID.Bolt_Of_Cloth.value, ModelID.Fur_Square.value], [25, 4]),
                (BOOTS, [ModelID.Bolt_Of_Cloth.value, ModelID.Fur_Square.value], [25, 4]),
                (PANTS, [ModelID.Bolt_Of_Cloth.value, ModelID.Fur_Square.value], [50, 8]),
                (CHEST, [ModelID.Bolt_Of_Cloth.value, ModelID.Fur_Square.value], [75, 12]),
                (HEAD, [ModelID.Bolt_Of_Cloth.value, ModelID.Fur_Square.value], [25, 4]),
            ]
        # Elementalist has unique materials: 180 bolt of cloth + 30 glittering dust + 28 bolt of silk + 4 glass vial
        elif primary == "Elementalist":
            armor_pieces = [
                (GLOVES, [ModelID.Bolt_Of_Cloth.value, ModelID.Pile_Of_Glittering_Dust.value, ModelID.Bolt_Of_Silk.value, ModelID.Tempered_Glass_Vial.value], [20, 3, 4, 0]),
                (BOOTS, [ModelID.Bolt_Of_Cloth.value, ModelID.Pile_Of_Glittering_Dust.value, ModelID.Bolt_Of_Silk.value, ModelID.Tempered_Glass_Vial.value], [20, 3, 4, 1]),
                (PANTS, [ModelID.Bolt_Of_Cloth.value, ModelID.Pile_Of_Glittering_Dust.value, ModelID.Bolt_Of_Silk.value, ModelID.Tempered_Glass_Vial.value], [45, 8, 8, 1]),
                (CHEST, [ModelID.Bolt_Of_Cloth.value, ModelID.Pile_Of_Glittering_Dust.value, ModelID.Bolt_Of_Silk.value, ModelID.Tempered_Glass_Vial.value], [70, 11, 8, 1]),
                (HEAD, [ModelID.Bolt_Of_Cloth.value, ModelID.Pile_Of_Glittering_Dust.value, ModelID.Bolt_Of_Silk.value, ModelID.Tempered_Glass_Vial.value], [25, 5, 4, 1]),
            ]
        else:
            # Standard quantities for other professions
            armor_pieces = [
                (GLOVES, [GetMaxArmorCommonMaterial(), rare_mat], [25, 4]),
                (BOOTS, [GetMaxArmorCommonMaterial(), rare_mat], [25, 4]),
                (PANTS, [GetMaxArmorCommonMaterial(), rare_mat], [50, 8]),
                (CHEST, [GetMaxArmorCommonMaterial(), rare_mat], [75, 12]),
                (HEAD, [GetMaxArmorCommonMaterial(), rare_mat], [25, 4]),
            ]
    else:
        # Fallback in case rare material not defined (shouldn't happen for max armor)
        armor_pieces = [
            (GLOVES, [GetMaxArmorCommonMaterial()], [25]),
            (BOOTS, [GetMaxArmorCommonMaterial()], [25]),
            (PANTS, [GetMaxArmorCommonMaterial()], [50]),
            (CHEST, [GetMaxArmorCommonMaterial()], [75]),
            (HEAD, [GetMaxArmorCommonMaterial()], [25]),
        ]
    
    for item_id, mats, qtys in armor_pieces:
        result = yield from Routines.Yield.Items.CraftItem(item_id, 1000, mats, qtys)
        if not result:
            ConsoleLog("CraftMaxArmor", f"Failed to craft item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield

        result = yield from Routines.Yield.Items.EquipItem(item_id)
        if not result:
            ConsoleLog("CraftMaxArmor", f"Failed to equip item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True

def GetWeaponCommonMaterial() -> int:
    """Returns the primary material type for weapon crafting (Wood Plank)."""
    return ModelID.Wood_Plank.value

def GetWeaponByProfession(bot: Botting):
    """Returns weapon IDs for the character's profession."""
    # All professions get Longbow
    return [11641]  # Longbow

def BuyWeaponMaterials():
    """Buy weapon materials (Wood Planks only).
    Note: Common materials are sold in stacks of 10, so quantity 1 = 10 materials."""
    for _ in range(1):  # Buy 1 unit = 10 Wood Planks (1 × 10)
        yield from Routines.Yield.Merchant.BuyMaterial(GetWeaponCommonMaterial())

def DoCraftWeapon(bot: Botting):
    """Core weapon crafting logic - assumes already at weapon crafter NPC."""
    weapon_ids = GetWeaponByProfession(bot)
    material = GetWeaponCommonMaterial()  # Returns Wood Plank
    
    # Structure weapon data like armor pieces - (weapon_id, materials_list, quantities_list)
    weapon_pieces = []
    for weapon_id in weapon_ids:
        weapon_pieces.append((weapon_id, [material], [10]))  # 10 Wood Planks per weapon
    
    for weapon_id, mats, qtys in weapon_pieces:
        result = yield from Routines.Yield.Items.CraftItem(weapon_id, 100, mats, qtys)
        if not result:
            ConsoleLog("DoCraftWeapon", f"Failed to craft weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield

        result = yield from Routines.Yield.Items.EquipItem(weapon_id)
        if not result:
            ConsoleLog("DoCraftWeapon", f"Failed to equip weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True

def withdraw_gold(target_gold=20000, deposit_all=True):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    if gold_on_char > target_gold and deposit_all:
        to_deposit = gold_on_char - target_gold
        GLOBAL_CACHE.Inventory.DepositGold(to_deposit)
        yield from Routines.Yield.wait(250)

    if gold_on_char < target_gold:
        to_withdraw = target_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)

def withdraw_gold_weapon(target_gold=500, deposit_all=True):
    """Withdraw gold for weapon crafting. Deposits all first if deposit_all is True."""
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    if deposit_all:
        GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
        yield from Routines.Yield.wait(250)
        gold_on_char = 0

    if gold_on_char < target_gold:
        to_withdraw = target_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)

def destroy_starter_armor_and_useless_items() -> Generator[Any, Any, None]:
    """Destroy starter armor pieces based on profession and useless items."""
    global starter_armor
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    # Profession-specific starter armor model IDs
    if primary == "Assassin":
        starter_armor = [7251,  # Head
                        7249,  # Chest
                        7250,  # Gloves
                        7252,  # Pants
                        7248   # Boots
                        ]
    elif primary == "Ritualist":
        starter_armor = [11332,  # Head
                        11330,  # Chest
                        11331,  # Gloves
                        11333,  # Pants
                        11329   # Boots
                        ]
    elif primary == "Warrior":
        starter_armor = [10174,  # Head
                        10172,  # Chest
                        10173,  # Gloves
                        10175,  # Pants
                        10171   # Boots
                        ]
    elif primary == "Ranger":
        starter_armor = [10623,  # Head
                        10621,  # Chest
                        10622,  # Gloves
                        10624,  # Pants
                        10620   # Boots
                        ]
    elif primary == "Monk":
        starter_armor = [9725,  # Head
                        9723,  # Chest
                        9724,  # Gloves
                        9726,  # Pants
                        9722   # Boots
                        ]
    elif primary == "Elementalist":
        starter_armor = [9324,  # Head
                        9322,  # Chest
                        9323,  # Gloves
                        9325,  # Pants
                        9321   # Boots
                        ]
    elif primary == "Mesmer":
        starter_armor = [8026,  # Head
                        8024,  # Chest
                        8025,  # Gloves
                        8054,  # Pants
                        8023   # Boots
                        ]
    elif primary == "Necromancer":
        starter_armor = [8863,  # Head
                        8861,  # Chest
                        8862,  # Gloves
                        8864,  # Pants
                        8860   # Boots
                        ]
    
    useless_items = [5819,  # Monastery Credit
                     6387,  # Starter Daggers
                     477,    # Starter Bow
                     30853, # MOX Manual
                     24897 #Brass Knuckles
                    ]
    
    for model in starter_armor:
        result = yield from Routines.Yield.Items.DestroyItem(model)
    
    for model in useless_items:
        result = yield from Routines.Yield.Items.DestroyItem(model)

def destroy_seitung_armor() -> Generator[Any, Any, None]:
    """Destroy Seitung armor pieces based on profession."""
    global seitung_armor
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    # Profession-specific Seitung armor model IDs
    if primary == "Warrior":
        seitung_armor = [10046, 10164, 10165, 10166, 10163]  # Head, Chest, Gloves, Pants, Boots
    elif primary == "Ranger":
        seitung_armor = [10483, 10613, 10614, 10615, 10612]
    elif primary == "Monk":
        seitung_armor = [9600, 9619, 9620, 9621, 9618]
    elif primary == "Assassin":
        seitung_armor = [7126, 7193, 7194, 7195, 7192]
    elif primary == "Mesmer":
        seitung_armor = [7528, 7546, 7547, 7548, 7545]
    elif primary == "Necromancer":
        seitung_armor = [8741, 8757, 8758, 8759, 8756]
    elif primary == "Ritualist":
        seitung_armor = [11203, 11320, 11321, 11323, 11319]
    elif primary == "Elementalist":
        seitung_armor = [9183, 9202, 9203, 9204, 9201]

    for model in seitung_armor:
        result = yield from Routines.Yield.Items.DestroyItem(model)

#region Routines
def _on_death(bot: "Botting"):
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("halt_on_death","active", True)
    bot.Properties.ApplyNow("movement_timeout","value", 15000)
    bot.Properties.ApplyNow("auto_combat","active", False)
    yield from Routines.Yield.wait(8000)
    fsm = bot.config.FSM
    fsm.resume()
    bot.Properties.ApplyNow("auto_combat","active", True)
    bot.Templates.Aggressive()
    yield  
    
def on_death(bot: "Botting"):
    print ("Player is dead. Run Failed, Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))
    
def InitializeBot(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)

def Exit_Monastery_Overlook(bot: Botting) -> None:
    bot.States.AddHeader("Exit Monastery Overlook")
    bot.Move.XYAndDialog(-7048,5817,0x85)
    bot.Wait.ForMapLoad(target_map_name="Shing Jea Monastery")

def Forming_A_Party(bot: Botting) -> None:
    bot.States.AddHeader("Quest: Forming A Party")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    PrepareForBattle(bot)
    bot.Move.XYAndDialog(-14063.00, 10044.00, 0x81B801)
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    bot.Move.XYAndDialog(19673.00, -6982.00, 0x81B807)
    
def Unlock_Secondary_Profession(bot: Botting) -> None:
    def assign_profession_unlocker_dialog():
        global bot
        primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
        if primary == "Ranger":
            yield from bot.Interact._coro_with_agent((-92, 9217),0x813D0A)
        else:
            yield from bot.Interact._coro_with_agent((-92, 9217),0x813D0E)

    bot.States.AddHeader("Unlock Secondary Profession")
    ConfigurePacifistEnv(bot)
    bot.Move.XYAndExitMap(-3480, 9460, target_map_name="Linnok Courtyard")
    bot.Move.XY(-159, 9174)
    bot.States.AddCustomState(assign_profession_unlocker_dialog, "Update Secondary Profession Dialog")
    bot.UI.CancelSkillRewardWindow()
    bot.UI.CancelSkillRewardWindow()
    bot.Dialogs.AtXY(-92, 9217,  0x813D07) #Reward
    bot.Dialogs.AtXY(-92, 9217,  0x813E01) #Minister Cho's Estate quest
    bot.Move.XYAndExitMap(-3762, 9471, target_map_name="Shing Jea Monastery")

def Unlock_Xunlai_Storage(bot: Botting) -> None:
    bot.States.AddHeader("Unlock Xunlai Storage")
    path_to_xunlai: List[Tuple[float, float]] = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3825.09, 10386.81),]
    bot.Move.FollowPathAndDialog(path_to_xunlai, 0x84)

def Craft_Weapon(bot: Botting):
    bot.States.AddHeader("Craft weapon")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    bot.States.AddCustomState(withdraw_gold_weapon, "Withdraw 500 Gold")
    bot.Move.XY(-10896.94, 10807.54)
    bot.Move.XY(-10942.73, 10783.19)
    bot.Move.XYAndInteractNPC(-10614.00, 10996.00)  # Common material merchant
    exec_fn_wood = lambda: BuyWeaponMaterials()
    bot.States.AddCustomState(exec_fn_wood, "Buy Wood Planks")
    bot.Move.XY(-10896.94, 10807.54)
    bot.Move.XY(-6519.00, 12335.00)
    bot.Move.XYAndInteractNPC(-6519.00, 12335.00)  # Weapon crafter in Shing Jea Monastery
    bot.Wait.ForTime(1000)
    exec_fn = lambda: DoCraftWeapon(bot)
    bot.States.AddCustomState(exec_fn, "Craft Weapons")

def Locate_Sujun(bot: Botting) -> Generator[Any, Any, None]:
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary != "Ranger": return
    yield from bot.Move._coro_get_path_to(-7782.00, 6687.00)
    yield from bot.Move._coro_follow_path_to()
    yield from bot.Interact._coro_with_agent((-7782.00, 6687.00), 0x810403) #Locate Sujun
    yield from bot.Interact._coro_with_agent((-7782.00, 6687.00), 0x810401)
    yield from bot.helpers.UI._cancel_skill_reward_window()

def RangerGetSkills(bot: Botting) -> Generator[Any, Any, None]:
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary != "Ranger": return
    yield from bot.Move._coro_get_path_to(5103.00, -4769.00)
    yield from bot.Move._coro_follow_path_to()
    yield from bot.Interact._coro_with_agent((5103.00, -4769.00), 0x810407) #npc to get skills from
    yield from bot.Interact._coro_with_agent((5103.00, -4769.00), 0x811401) #of course i will help

def switchFilter():
    # Switch to profession sort
    Game.enqueue(lambda: UIManager.SendUIMessage(UIMessage.kPreferenceValueChanged,[18,2], False))
    Game.enqueue(lambda: UIManager.SendUIMessage(UIMessage.kPreferenceValueChanged,[17,4], False))
    yield from Routines.Yield.wait(500)
    return

def TrainSkills():
    secondary_skills_grandparent = 1746895597
    secondary_skills_offset = [0,0,0,5,1]
    skills_to_train_frames = [
        UIManager.GetChildFrameID(secondary_skills_grandparent, secondary_skills_offset + [57,0]), # Cry of Pain
        UIManager.GetChildFrameID(secondary_skills_grandparent, secondary_skills_offset + [25,0]), # Power Drain
        UIManager.GetChildFrameID(secondary_skills_grandparent, secondary_skills_offset + [860,0]), # Signet of Disruption
    ]
    for skill_frame_id in skills_to_train_frames:
        Game.enqueue(lambda: UIManager.TestMouseClickAction(skill_frame_id, 0, 0))
        yield from Routines.Yield.wait(200)
        Game.enqueue(lambda: UIManager.FrameClick(UIManager.GetFrameIDByHash(4162812990)))
        yield from Routines.Yield.wait(200)
    return

def Unlock_Skills_Trainer(bot: Botting) -> None:
    bot.States.AddHeader("Unlock Skills Trainer")
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if profession == "Mesmer":
        return
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    bot.Move.XYAndDialog(-8790.00, 10366.00, 0x84)
    bot.States.AddCustomState(switchFilter, "Switch Skill Filter")
    bot.Wait.ForTime(3000)
    bot.States.AddCustomState(TrainSkills, "Train Skills")

def Charm_Pet(bot: Botting) -> None:
    bot.States.AddHeader("Charm Pet")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    bot.States.AddCustomState(lambda:Locate_Sujun(bot), "Unlock Skills")
    bot.States.AddCustomState(EquipCaptureSkillBar, "Equip Capture Skill Bar")
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    bot.Move.XY(13970.94, -13085.83)
    bot.Move.ToModel(3005) #Tiger model id updated 20.12.2025 GW Reforged
    bot.Wait.ForTime(500)
    bot.Target.Model(3005) #Tiger model id updated 20.12.2025 GW Reforged
    bot.SkillBar.UseSkill(411)
    bot.Wait.ForTime(14000)
    bot.States.AddCustomState(lambda: RangerGetSkills(bot), "Get Ranger Skills")

def To_Minister_Chos_Estate(bot: Botting):
    bot.States.AddHeader("To Minister Cho's Estate")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    ConfigurePacifistEnv(bot)
    bot.Move.XY(16182.62, -7841.86)
    bot.Move.XY(6611.58, 15847.51)
    bot.Move.XYAndDialog(6637, 16147, 0x80000B)
    bot.Wait.ForMapToChange(target_map_id=214)
    bot.Move.XYAndDialog(7884, -10029, 0x813E07)
    
def Minister_Chos_Estate_Mission(bot: Botting) -> None:
    bot.States.AddHeader("Minister Cho's Estate mission")
    bot.Map.Travel(target_map_id=214)
    PrepareForBattle(bot)
    bot.Map.EnterChallenge(delay=4500, target_map_id=214)
    bot.Move.XY(6220.76, -7360.73)
    bot.Move.XY(5523.95, -7746.41)
    bot.Wait.ForTime(15000)
    bot.Move.XY(591.21, -9071.10)
    bot.Wait.ForTime(30000)
    bot.Move.XY(4889, -5043)   # Move to Map Tutorial
    bot.Move.XY(4268.49, -3621.66)
    bot.Wait.ForTime(20000)
    bot.Move.XY(6216, -1108)   # Move to Bridge Corner
    bot.Move.XY(2617, 642)     # Move to Past Bridge
    bot.Move.XY(1706.90, 1711.44)
    bot.Wait.ForTime(30000)
    bot.Move.XY(333.32, 1124.44)
    bot.Move.XY(-3337.14, -4741.27)
    bot.Wait.ForTime(35000)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-4661.99, -6285.81)
    bot.Move.XY(-7454, -7384)  # Move to Zoo Entrance
    bot.Move.XY(-9138, -4191)  # Move to First Zoo Fight
    bot.Move.XY(-7109, -25)    # Move to Bridge Waypoint
    bot.Move.XY(-7443, 2243)   # Move to Zoo Exit
    bot.Move.XY(-16924, 2445)  # Move to Final Destination
    bot.Interact.WithNpcAtXY(-17031, 2448) #"Interact with Minister Cho"
    bot.Wait.ForMapToChange(target_map_id=251) #Ran Musu Gardens
    
def Attribute_Points_Quest_1(bot: Botting):
    bot.States.AddHeader("Attribute points quest n. 1")
    bot.Map.Travel(target_map_id=251) #Ran Musu Gardens
    bot.Move.XY(16184.75, 19001.78)
    bot.Move.XYAndDialog(14363.00, 19499.00, 0x815A01)  # I Like treasure
    PrepareForBattle(bot)
    path = [(13713.27, 18504.61),(14576.15, 17817.62),(15824.60, 18817.90),(17005, 19787)]
    bot.Move.FollowPathAndExitMap(path, target_map_id=245)
    bot.Move.XY(-17979.38, -493.08)
    bot.Dialogs.WithModel(3093, 0x815A04) #Guard model id updated 20.12.2025 GW Reforged
    exit_function = lambda: (
        not (Routines.Checks.Agents.InDanger(aggro_area=Range.Spirit)) and
        Agent.HasQuest(Routines.Agents.GetAgentIDByModelID(3093))
    )
    bot.Move.FollowModel(3093, follow_range=(Range.Area.value), exit_condition=exit_function) #Guard model id updated 20.12.2025 GW Reforged
    bot.Dialogs.WithModel(3093, 0x815A07) #Guard model id updated 20.12.2025 GW Reforged
    bot.Map.Travel(target_map_id=251) #Ran Musu Gardens
    
def Warning_The_Tengu(bot: Botting):
    bot.States.AddHeader("Quest: Warning the Tengu")
    bot.Map.Travel(target_map_id=251) #Ran Musu Gardens
    bot.Move.XYAndDialog(15846, 19013, 0x815301)
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(14730, 15176, target_map_name="Kinya Province")
    bot.Move.XY(1429, 12768)
    bot.Move.XYAndDialog(-1023, 4844, 0x815304)
    bot.Move.XY(-5011, 732, "Move to Tengu Killspot")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(-1023, 4844, 0x815307)

def The_Threat_Grows(bot: Botting):
    bot.States.AddHeader("Quest: The Threat Grows")
    bot.Dialogs.AtXY(-1023, 4844, 0x815401)
    bot.Map.Travel(target_map_id=242) #Shin Jea Monastery
    PrepareForBattle(bot)
    bot.Move.XY(-14961, 11453)
    bot.Wait.ForMapToChange(target_map_name="Sunqua Vale")
    ConfigurePacifistEnv(bot)
    bot.Move.XY(18245.78, -9448.29)
    bot.Move.FollowAutoPath([(-4842, -13267)])
    bot.Wait.ForMapToChange(target_map_id=249) # Tsumei Village
    PrepareForBattle(bot)
    bot.Move.XY(-11600,-17400)
    bot.Wait.ForMapToChange(target_map_name="Panjiang Peninsula")
    bot.Move.XY(10077.84, 8047.69) #Kill spot
    bot.Wait.UntilModelHasQuest(3367) #Sister Tai model id updated 20.12.2025 GW Reforged
    ConfigurePacifistEnv(bot)
    bot.Dialogs.WithModel(3367, 0x815407) #Sister Tai model id updated 20.12.2025 GW Reforged
    bot.Dialogs.WithModel(3367, 0x815501) #Sister Tai model id updated 20.12.2025 GW Reforged
     
def The_Road_Less_Traveled(bot: Botting):
    bot.States.AddHeader("Quest: The Road Less Traveled")
    bot.Map.Travel(target_map_id=242) #Shin Jea Monastery
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(-3480, 9460, target_map_name="Linnok Courtyard")
    bot.Move.XYAndDialog(-92, 9217, 0x815507)
    bot.Dialogs.AtXY(-92, 9217, 0x815601)
    bot.Move.XYAndDialog(538, 10125, 0x80000B)
    bot.Wait.ForMapToChange(target_map_id=313)
    bot.Move.XYAndDialog(1254, 10875, 0x815604)
    bot.Move.XYAndExitMap(16600, 13150, target_map_name="Seitung Harbor")
    bot.Move.XY(16852, 12812)
    bot.Move.XYAndDialog(16435, 12047, 0x815607)
    
def Craft_Seitung_Armor(bot: Botting):
    bot.States.AddHeader("Craft Seitung armor")
    bot.Map.Travel(target_map_id=250) #Seitung Harbor
    bot.Move.XYAndInteractNPC(17520.00, 13805.00)
    bot.States.AddCustomState(BuyMaterials, "Buy Materials")
    bot.Move.XY(19823.66, 9547.78)
    bot.Move.XYAndInteractNPC(20508.00, 9497.00)
    exec_fn = lambda: CraftArmor(bot)
    bot.States.AddCustomState(exec_fn, "Craft Armor")
    
def To_Zen_Daijun(bot: Botting):
    bot.States.AddHeader("To Zen Daijun")
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(16777, 17540, target_map_name="Jaya Bluffs")
    bot.Move.XYAndExitMap(23616, 1587, target_map_name="Haiju Lagoon")
    bot.Move.XYAndDialog(16489, -22213, 0x80000B)
    bot.Wait.ForTime(7000)
    bot.Wait.ForMapLoad(target_map_id=213) #Zen Daijun
    
def Zen_Daijun_Mission(bot:Botting):
    bot.States.AddHeader("Zen Daijun Mission")
    for _ in range (4):
        bot.Map.Travel(target_map_id=213)
        PrepareForBattle(bot)
        bot.Map.EnterChallenge(6000, target_map_id=213) #Zen Daijun
        bot.Move.XY(15120.68, 10456.73)
        bot.Wait.ForTime(15000)
        bot.Move.XY(11990.38, 10782.05)
        bot.Wait.ForTime(10000)
        bot.Move.XY(10161.92, 9751.41)
        bot.Move.XY(9723.10, 7968.76)
        bot.Wait.UntilOutOfCombat()
        bot.Interact.WithGadgetAtXY(9632.00, 8058.00)
        bot.Move.XY(9412.15, 7257.83)
        bot.Move.XY(9183.47, 6653.42)
        bot.Move.XY(8966.42, 6203.29)
        bot.Move.XY(3510.94, 2724.63)
        bot.Move.XY(2120.18, 1690.91)
        bot.Move.XY(928.27, 2782.67)
        bot.Move.XY(744.67, 4187.17)
        bot.Move.XY(242.27, 6558.48)
        bot.Move.XY(-4565.76, 8326.51)
        bot.Move.XY(-5374.88, 8626.30)
        bot.Move.XY(-10291.65, 8519.68)
        bot.Move.XY(-11009.76, 6292.73)
        bot.Move.XY(-12762.20, 6112.31)
        bot.Move.XY(-14029.90, 3699.97)
        bot.Move.XY(-13243.47, 1253.06)
        bot.Move.XY(-11907.05, 28.87)
        bot.Move.XY(-11306.09, 802.47)
        bot.Wait.ForTime(5000)
        bot.Move.XY(-10255.23, 178.48)
        bot.Move.XY(-9068.41, -553.94)
        bot.Wait.ForTime(5000)
        bot.Move.XY(-7949.79, -1376.02)
        bot.Move.XY(-7688.63, -1538.34)
        bot.Wait.ForMapToChange(target_map_name="Seitung Harbor")

def Craft_Remaining_Seitung_Armor(bot: Botting):
    bot.States.AddHeader("Craft remaining Seitung armor")
    bot.Map.Travel(target_map_name="Seitung Harbor")
    bot.States.AddCustomState(CraftRemainingArmor, "Craft Remaining Seitung Armor")

def Destroy_Starter_Armor_And_Useless_Items(bot: Botting):
    bot.States.AddHeader("Destroy starter armor and useless items")
    bot.States.AddCustomState(destroy_starter_armor_and_useless_items, "Destroy starter armor and useless items")

def To_Marketplace(bot: Botting):
    bot.States.AddHeader("To Marketplace")
    bot.Map.Travel(target_map_id=250) #Seitung Harbor
    bot.Move.XYAndDialog(16927, 9004, 0x815D01) #A Master's Burden pt. 1
    bot.Dialogs.AtXY(16927, 9004, 0x84)
    bot.Wait.ForMapLoad(target_map_name="Kaineng Docks")
    bot.Move.XYAndDialog(9955, 20033, 0x815D04) #A Master's Burden pt. 2
    bot.Move.XYAndExitMap(12003, 18529, target_map_name="The Marketplace")

def To_Kaineng_Center(bot: Botting):
    bot.States.AddHeader("To Kaineng Center")
    bot.Map.Travel(target_map_name="The Marketplace")
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(16640,19882, target_map_name="Bukdek Byway")
    auto_path_list = [(-10254.0,-1759.0), (-10332.0,1442.0), (-10965.0,9309.0), (-9467.0,14207.0)]
    bot.Move.FollowAutoPath(auto_path_list)
    path_to_kc = [(-8601.28, 17419.64),(-6857.17, 19098.28),(-6706,20388)]
    bot.Move.FollowPathAndExitMap(path_to_kc, target_map_id=194) #Kaineng Center

def Craft_Max_Armor(bot: Botting):
    bot.States.AddHeader("Craft max armor")
    # Buy common materials (cloth or hide)
    bot.Map.Travel(194)
    bot.Move.XY(1592.00, -796.00)  # Move to material merchant area
    bot.States.AddCustomState(withdraw_gold, "Withdraw 20k Gold")
    bot.Move.XYAndInteractNPC(1592.00, -796.00)  # Common material merchant
    exec_fn_common = lambda: BuyMaxArmorMaterials("common")
    bot.States.AddCustomState(exec_fn_common, "Buy Common Materials")
    bot.Wait.ForTime(1500)  # Wait for common material purchases to complete
    # Buy rare materials (steel ingot, linen, or damask)
    rare_material = GetMaxArmorRareMaterial()
    if rare_material is not None:
        bot.Move.XYAndInteractNPC(1495.00, -1315.00)  # Rare material merchant
        exec_fn_rare = lambda: BuyMaxArmorMaterials("rare")
        bot.States.AddCustomState(exec_fn_rare, "Buy Rare Materials")
        bot.Wait.ForTime(2000)  # Wait for rare material purchases to complete
    crafter_x, crafter_y = GetArmorCrafterCoords()
    bot.Move.XY(crafter_x, crafter_y)
    bot.Move.XYAndInteractNPC(crafter_x, crafter_y)  # Armor crafter in Kaineng Center
    bot.Wait.ForTime(1000)  # Small delay to let the window open
    exec_fn = lambda: DoCraftMaxArmor(bot)
    bot.States.AddCustomState(exec_fn, "Craft Max Armor")

def Destroy_Seitung_Armor(bot: Botting):
    bot.States.AddHeader("Destroy old armor")
    bot.States.AddCustomState(destroy_seitung_armor, "Destroy Seitung Armor")

def Extend_Inventory_Space(bot: Botting):
    bot.States.AddHeader("Extend Inventory Space")
    bot.Map.Travel(194)
    bot.States.AddCustomState(withdraw_gold, "Get 5000 gold")
    bot.helpers.UI.open_all_bags()
    bot.Move.XY(1448.00, -2024.00)
    bot.Move.XYAndInteractNPC(1448.00, -2024.00) # Merchant NPC in Kaineng Center
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

def To_Boreal_Station(bot: Botting):
    bot.States.AddHeader("To Boreal Station")
    bot.Map.Travel(target_map_id=194)
    bot.Move.XY(3444.90, -1728.31)
    bot.Move.XYAndDialog(3747.00, -2174.00, 0x833501)
    bot.Move.XY(3444.90, -1728.31)
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(3243, -4911, target_map_name="Bukdek Byway")
    bot.Move.XYAndDialog(-5803.48, 18951.70, 0x85)  # Unlock Mox
    bot.Move.XYAndDialog(-10103.00, 16493.00, 0x84)
    bot.Wait.ForMapLoad(target_map_id=692)
    auto_path_list = [(16738.77, 3046.05), (13028.36, 6146.36), (10968.19, 9623.72),
                      (3918.55, 10383.79), (8435, 14378), (10134,16742)]    
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForTime(3000)
    ConfigurePacifistEnv(bot)    
    auto_path_list = [(4523.25, 15448.03), (-43.80, 18365.45), (-10234.92, 16691.96),
                      (-17917.68, 18480.57), (-18775, 19097)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForTime(8000)
    bot.Wait.ForMapLoad(target_map_id=675)

def To_Eye_of_the_North(bot: Botting):
    bot.States.AddHeader("To Eye of the North")
    bot.Map.Travel(target_map_id=675) #Boreal Station
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(4684, -27869, target_map_name="Ice Cliff Chasms")
    bot.Move.XY(3579.07, -22007.27)
    bot.Wait.ForTime(15000)
    bot.Dialogs.AtXY(3537.00, -21937.00, 0x839104)
    auto_path_list = [(3743.31, -15862.36), (3607.21, -6937.32),(2557.23, -275.97)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Move.XY(-641.25, 2069.27)
    bot.Wait.ForMapToChange(target_map_id=642)

def Unlock_Eye_Of_The_North_Pool(bot: Botting):
    bot.States.AddHeader("Unlock Eye Of The North Pool")
    bot.Map.Travel(target_map_id=642)
    auto_path_list = [(-4416.39, 4932.36), (-5198.00, 5595.00)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForMapToChange(target_map_id=646)
    bot.Move.XY(-6572.70, 6588.83)
    bot.Dialogs.WithModel(6021, 0x800001) # Eotn_pool_cinematic. Model id updated 20.12.2025 GW Reforged
    bot.Wait.ForTime(1000)
    #bot.Dialogs.WithModel(5959, 0x630) # Eotn_pool_cinematic. Model id updated 20.12.2025 GW Reforged
    #bot.Wait.ForTime(1000)
    bot.Dialogs.WithModel(5959, 0x633) # Eotn_pool_cinematic. Model id updated 20.12.2025 GW Reforged
    bot.Wait.ForTime(1000)
    bot.Wait.ForMapToChange(target_map_id=646)
    bot.Dialogs.WithModel(6021, 0x89) # Gwen dialog. Model id updated 20.12.2025 GW Reforged
    bot.Dialogs.WithModel(6021, 0x831904) # Gwen dialog. Model id updated 20.12.2025 GW Reforged
    bot.Dialogs.WithModel(6021, 0x0000008A) # Gwen dialog to obtain Keiran's bow. Model id updated 20.12.2025 GW Reforged
    bot.Move.XYAndDialog(-6133.41, 5717.30, 0x838904) # Ogden dialog. Model id updated 20.12.2025 GW Reforged
    bot.Move.XYAndDialog(-5626.80, 6259.57, 0x839304) # Vekk dialog. Model id updated 20.12.2025 GW Reforged

def Attribute_Points_Quest_2(bot: Botting):
    def enable_combat_and_wait(ms:int):
        global bot
        bot.Properties.Enable("auto_combat")
        bot.Wait.ForTime(ms)
        bot.Properties.Disable("auto_combat")
 
    bot.States.AddHeader("Attribute points quest n. 2")
    bot.Map.Travel(target_map_name="Seitung Harbor")
    auto_path_list = [(16602.23, 11612.10), (16886.80, 9577.24), (16940.28, 9860.90), 
                      (19243.22, 9093.26), (19840.55, 7956.64)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Interact.WithGadgetAtXY(19642.00, 7386.00)
    bot.Wait.ForTime(5000)
    bot.Dialogs.WithModel(4009,0x815C01) #Zunraa model id updated 20.12.2025 GW Reforged
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    bot.Party.AddHenchmanList([1, 5])
    bot.Dialogs.AtXY(20350.00, 9087.00, 0x80000B)
    bot.Wait.ForMapLoad(target_map_id=246)  #Zen Daijun
    ConfigureAggressiveEnv(bot)
    auto_path_list:List[Tuple[float, float]] = [
    (-13959.50, 6375.26), #Half the temple
    (-14567.47, 1775.31), #Side of road
    (-12310.05, 2417.60), #Across road
    (-12071.83, 294.29),  #Bridge and patrol
    (-9972.85, 4141.29), #Miasma passtrough
    (-9331.86, 7932.66), #In front of bridge
    (-6353.09, 9385.63), #Past he miasma on way to waterfall
    (247.80, 12070.21), #Waterfall
    (-8180.59, 12189.97), #Back to kill patrols
    (-9540.45, 7760.86), #In front of bridge 2
    (-5038.08, 2977.42)] #To shrine
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Interact.WithGadgetAtXY(-4862.00, 3005.00)
    bot.Move.XY(-9643.93, 7759.69) #Front of bridge 3
    bot.Wait.ForTime(5000)
    bot.Properties.Disable("auto_combat")
    path =[(-8294.21, 10061.62)] #Position Zunraa
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    path = [(-6473.26, 8771.21)] #Clear miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    path =[(-6365.32, 10234.20)] #Position Zunraa2
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    bot.Properties.Enable("auto_combat")
    bot.Move.XY(-8655.04, -769.98) # To next Miasma on temple
    bot.Wait.ForTime(5000)
    bot.Properties.Disable("auto_combat")
    path = [(-6744.75, -1842.97)] #Clear half the miasma 
    bot.Move.FollowPath(path)
    enable_combat_and_wait(10000)
    path = [(-7720.80, -905.19)] #Finish miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    bot.Properties.Enable("auto_combat")
    auto_path_list:List[Tuple[float, float]] = [
    (-5016.76, -8800.93), #Half the map
    (3268.68, -6118.96), #Passtrough miasma
    (3808.16, -830.31), #Back of bell
    (536.95, 2452.17), #Yard
    (599.18, 12088.79), #Waterfall
    (3605.82, 2336.79), #Patrol kill
    (5509.49, 1978.54), #Bell
    (11313.49, 3755.03), #Side path (90)
    (12442.71, 8301.94), #Middle aggro
    (8133.23, 7540.54), #Enemies on the side
    (15029.96, 10187.60), #Enemies on the loop
    (14062.33, 13088.72), #Corner
    (11775.22, 11310.60)] #Zunraa
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Interact.WithGadgetAtXY(11665, 11386)
    bot.Properties.Disable("auto_combat")
    path = [(12954.96, 9288.47)] #Miasma
    bot.Move.FollowPath(path) 
    enable_combat_and_wait(5000)
    path = [(12507.05, 11450.91)] #Finish miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    bot.Properties.Enable("auto_combat")
    bot.Move.XY(7709.06, 4550.47) #Past bridge trough miasma
    bot.Wait.ForTime(5000)
    bot.Properties.Disable("auto_combat")
    path = [(9334.25, 5746.98)] #1/3 miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    path = [(7554.94, 6159.84)] #2/3 miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    path =[(9242.30, 6127.45)] #Finish miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(5000)
    bot.Properties.Enable("auto_combat")
    bot.Move.XY(4855.66, 1521.21)
    bot.Interact.WithGadgetAtXY(4754,1451)
    bot.Move.XY(2958.13, 6410.57)  
    bot.Properties.Disable("auto_combat")
    path = [(2683.69, 8036.28)] #Clear miasma
    bot.Move.FollowPath(path)
    enable_combat_and_wait(8000)
    bot.Move.XY(3366.55, -5996.11) #To the other miasma at the middle 
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
    bot.Move.XY(-8655.04, -769.98)
    bot.Move.XY(-7453.22, -1483.71)
    wait_function = lambda: (
        not (Routines.Checks.Agents.InDanger(aggro_area=Range.Spirit)))
    bot.Wait.UntilCondition(wait_function)
    bot.Map.Travel(target_map_name="Seitung Harbor")
    auto_path_list = [(16602.23, 11612.10), (16886.80, 9577.24), (16940.28, 9860.90),
                      (19243.22, 9093.26), (19840.55, 7956.64)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Interact.WithGadgetAtXY(19642.00, 7386.00)
    bot.Wait.ForTime(5000)
    bot.Dialogs.WithModel(4009,0x815C07) #Zunraa model id updated 20.12.2025 GW Reforged

def To_Gunnars_Hold(bot: Botting):
    bot.States.AddHeader("To Gunnar's Hold")
    bot.Map.Travel(target_map_id=642)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    bot.Party.AddHenchmanList([5, 6, 7, 9])
    bot.Items.Equip(35829)
    path = [(-1814.0, 2917.0), (-964.0, 2270.0), (-115.0, 1677.0), (718.0, 1060.0), 
            (1522.0, 464.0)]
    bot.Move.FollowPath(path)
    bot.Wait.ForMapLoad(target_map_id=499)
    bot.Move.XYAndDialog(2825, -481, 0x832801)
    path = [(2548.84, 7266.08),
            (1233.76, 13803.42),
            (978.88, 21837.26),
            (-4031.0, 27872.0),]
    bot.Move.FollowAutoPath(path)
    bot.Wait.ForMapLoad(target_map_id=548)
    bot.Move.XY(14546.0, -6043.0)
    bot.Move.XYAndExitMap(15578, -6548, target_map_id=644)
    bot.Wait.ForMapLoad(target_map_id=644)

def Unlock_Kilroy_Stonekin(bot: Botting):
    bot.States.AddHeader("Unlock Kilroy Stonekin")
    bot.Templates.Aggressive(enable_imp=False)
    bot.Map.Travel(target_map_id=644)
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x835A01)
    bot.Dialogs.AtXY(17341.00, -4796.00, 0x84)
    bot.Wait.ForMapLoad(target_map_id=703)
    bot.Items.Equip(24897) #Brass_knuckles_item_id
    bot.Wait.ForTime(3000)
    bot.Move.XY(19290.50, -11552.23)
    bot.Wait.UntilOnOutpost()
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x835A07)

def To_Longeyes_Edge(bot: Botting):
    bot.States.AddHeader("To Longeye's Edge")
    bot.Map.Travel(target_map_id=644)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    bot.Party.AddHenchmanList([5, 6, 7, 9])
    bot.Items.Equip(35829)
    bot.Move.XY(15886.204101, -6687.815917)
    bot.Move.XY(15183.199218, -6381.958984)
    bot.Wait.ForMapLoad(target_map_id=548)
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
    bot.Wait.ForMapLoad(target_map_id=482)
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
    bot.Wait.ForMapLoad(target_map_id=650)

def Unlock_NPC_For_Vaettir_Farm(bot: Botting):
    bot.States.AddHeader("Unlock NPC for vaettir farm")
    bot.Map.Travel(target_map_id=650)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    bot.Party.AddHenchmanList([5, 6, 7, 9])
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

def To_Lions_Arch(bot: Botting):
    bot.States.AddHeader("To Lion's Arch")
    bot.Map.Travel(target_map_id=194)
    auto_path_list = [(3049.35, -2020.75), (2739.30, -3710.67), 
                      (-648.30, -3493.72), (-1661.91, -636.09)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Move.XYAndDialog(-1006.97, -817.63, 0x81DF01)
    bot.Move.XYAndExitMap(-2439, 1732, target_map_id=290)
    auto_path_list =[(-2995.68, 2077.20), (-6938.10, 4286.61), (-6064.40, 5300.26),
                     (-2396.20, 5260.67), (-5031.77, 6001.52)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Move.XYAndDialog(-5626.17, 7017.33, 0x81DF04)
    bot.Move.XYAndDialog(-4661.13, 7479.86, 0x84)
    bot.Wait.ForMapToChange(target_map_name="Lion's Gate")
    bot.Move.XY(-1181, 1038)
    bot.Dialogs.WithModel(2011, 0x85) #Model id updated 20.12.2025 GW Reforged
    bot.Map.Travel(target_map_id=55)
    bot.Move.XYAndDialog(328.00, 9594.00, 0x81DF07)

def To_Temple_of_The_Ages(bot: Botting):
    bot.States.AddHeader("To Temple of the Ages")
    bot.Map.Travel(target_map_id=55)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
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
    bot.Move.XY(15521, -15378)
    bot.Move.XY(15450, -15050)
    bot.Wait.ForMapLoad(target_map_id=59) # Nebo Terrace
    bot.Move.XY(15378, -14794)
    bot.Wait.ForMapLoad(target_map_id=59) # Nebo Terrace
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
    bot.Wait.ForMapLoad(target_map_id=56) # Cursed Lands
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
    bot.Wait.ForMapLoad(target_map_id=18) # The Black Curtain
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
    bot.Wait.ForMapLoad(target_map_id=138) # Temple of the Ages

def To_Kamadan(bot: Botting):
    bot.States.AddHeader("To Kamadan")
    bot.Map.Travel(target_map_id=194)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    bot.Party.AddHenchmanList([2, 9, 10, 12])
    auto_path_list = [(3049.35, -2020.75), (2739.30, -3710.67), 
                      (-648.30, -3493.72), (-1661.91, -636.09)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Move.XYAndDialog(-1131.99, 818.35, 0x82D401)
    bot.Move.XYAndExitMap(-2439, 1732, target_map_id=290)
    auto_path_list = [(-2995.68, 2077.20), (-6938.10, 4286.61), (-6064.40, 5300.26),
                     (-2396.20, 5260.67), (-5031.77, 6001.52)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Move.XYAndDialog(-5899.57, 7240.19, 0x82D404)
    bot.Dialogs.WithModel(4914, 0x87)  # Model id updated 20.12.2025 GW Reforged
    bot.Wait.ForMapToChange(target_map_id=400)
    ConfigureAggressiveEnv(bot)
    auto_path_list = [(-1712.16, -700.23), (-907.97, -2862.29), (742.42, -4167.73)] 
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForTime(10000)
    auto_path_list = [(1352.94, -3694.75),
                      (2547.49, -3667.82),
                      (2541.67, -2582.88)] # Critical part, high aggro area
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForTime(10000)
    bot.Move.XY(1990.27, -1636.21)
    bot.Wait.ForTime(15000)
    auto_path_list = [(2651.48, -3750.63),
                      (3355.63, -2151.82)] # Critical part, high aggro area
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForTime(10000)
    bot.Move.XY(4565.37, -1630.73)
    bot.Wait.ForTime(15000)
    auto_path_list = [(2951.07, -723.50), (2875.84, 488.42), (1354.73, 583.06)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForMapToChange(target_map_id=290)
    bot.Wait.ForTime(2000)
    bot.Dialogs.WithModel(4914, 0x84)  # Model id updated 20.12.2025 GW Reforged
    bot.Wait.ForMapToChange(target_map_id=543)
    bot.Wait.ForTime(2000)
    bot.Dialogs.WithModel(4829, 0x82D407)  # Model id updated 20.12.2025 GW Reforged
    bot.Dialogs.WithModel(4829, 0x82E101)  # Model id updated 20.12.2025 GW Reforged

def To_Consulate_Docks(bot: Botting):
    bot.States.AddHeader("To Consulate Docks")
    bot.Map.Travel(target_map_id=194)
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=449)
    bot.Move.XY(-8075.89, 14592.47)
    bot.Move.XY(-6743.29, 16663.21)
    bot.Move.XY(-5271.00, 16740.00)
    bot.Wait.ForMapLoad(target_map_id=429)
    bot.Move.XYAndDialog(-4631.86, 16711.79, 0x85)
    bot.Wait.ForMapToChange(target_map_id=493)

def Unlock_Olias(bot:Botting):
    bot.States.AddHeader("Unlock Olias")
    bot.Map.Travel(target_map_id=493)  # Consulate Docks
    bot.Move.XYAndDialog(-2367.00, 16796.00, 0x830E01)
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=55)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    bot.Party.AddHenchmanList([1, 3])
    bot.Move.XY(1413.11, 9255.51)
    bot.Move.XY(242.96, 6130.82)
    bot.Move.XYAndDialog(-1137.00, 2501.00, 0x84)
    bot.Wait.ForMapToChange(target_map_id=471)
    bot.Wait.ForTime(3000)
    bot.Move.XYAndDialog(5117.00, 10515.00, 0x830E04)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(8518.10, 9309.66)
    bot.Move.XY(8067.40, 5703.23)
    bot.Move.XY(5657.20, 4485.55)
    bot.Move.XY(4461.65, -710.88)
    bot.Move.XY(9973.11, 1581.00)
    bot.Wait.ForTime(20000)
    bot.Wait.ForMapToChange(target_map_id=55)
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=449)
    bot.Move.XYAndDialog(-6480.00, 16331.00, 0x830E07)
    
def Unlock_Xunlai_Material_Panel(bot: Botting) -> None:
    bot.States.AddHeader("Unlock Xunlai Material Panel")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=248)  # GTOB
    path_to_xunlai = [(-5540.40, -5733.11),(-7050.04, -6392.59),]
    bot.Move.FollowPath(path_to_xunlai)
    bot.Dialogs.WithModel(221, 0x800001) # Model id updated 20.12.2025 GW Reforged
    bot.Dialogs.WithModel(221, 0x800002) # Model id updated 20.12.2025 GW Reforged

def Unlock_Remaining_Secondary_Professions(bot: Botting):
    bot.States.AddHeader("Unlock remaining secondary professions")
    bot.Map.Travel(target_map_id=248)  # GTOB
    bot.States.AddCustomState(withdraw_gold, "Get 5000 gold")
    bot.Move.XY(-5540.40, -5733.11)
    bot.Move.XY(-3151.22, -7255.13)
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    if primary == "Warrior":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
    elif primary == "Ranger":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201 . Model id updated 20.12.2025 GW Reforged
    elif primary == "Monk":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x284)  # Ranger trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
    elif primary == "Assassin":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
    elif primary == "Mesmer":
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201.  Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
    elif primary == "Necromancer":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
    elif primary == "Ritualist":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x684)  # Elementalist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
    elif primary == "Elementalist":
        bot.Dialogs.WithModel(201, 0x584)  # Mesmer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x484)  # Necromancer trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x384)  # Monk trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x184)  # Warrior trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x884)  # Ritualist trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x784)  # Assassin trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0x984)  # Paragon trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged
        bot.Dialogs.WithModel(201, 0xA84)  # Dervish trainer - Model ID 201. Model id updated 20.12.2025 GW Reforged

def Unlock_Mercenary_Heroes(bot: Botting) -> None:
    bot.States.AddHeader(" Unlock Mercenary Heroes")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=248)
    bot.Move.XY(-4231.87, -8965.95)
    bot.Dialogs.WithModel(225, 0x800004) # Model id updated 20.12.2025 GW Reforged
    #bot.States.AddCustomState(destroy_starter_armor_and_useless_items, "Destroy starter armor and useless items")
    
#region event handlers
def on_party_wipe_coroutine(bot: "Botting", target_name: str):
    # optional but typical for wipe flow:
    Player.SendChatCommand("resign")
    yield from Routines.Yield.wait(8000)

    fsm = bot.config.FSM
    fsm.jump_to_state_by_name(target_name)  # jump while still paused
    fsm.resume()                            # <— important: unpause so next tick runs the target state
    yield                                    # keep coroutine semantics

class WaypointData:
    def __init__(self, label: str, MapID: int,step_name: str):
        self.step_name = step_name
        self.MapID = MapID
        self.label = label
        
WAYPOINTS: dict[int, WaypointData] = {
    # step_num: WaypointData(label, MapID, step_name)
    # Based on actual AddHeader calls in the bot routine
    3: WaypointData(label="Unlock Secondary Profession", MapID=242, step_name="[H]Unlock Secondary Profession_2"),
    4: WaypointData(label="Unlock Xunlai Storage", MapID=242, step_name="[H]Unlock Xunlai Storage_3"),
    6: WaypointData(label="Charm Pet", MapID=242, step_name="[H]Charm Pet_5"),
    10: WaypointData(label="Minister Cho's Estate Mission", MapID=214, step_name="[H]Minister Cho's Estate mission_7"),
    12: WaypointData(label="Attribute point quest n. 1", MapID=251, step_name="[H]Attribute points quest n. 1_8"),
    17: WaypointData(label="Craft Seitung armor", MapID=250, step_name="[H]Craft Seitung armor_14"),
    19: WaypointData(label="Zen Daijun Mission", MapID=213, step_name="[H]Zen Daijun Mission_16"),
    22: WaypointData(label="Attribute point quest n. 2", MapID=250, step_name="[H]Attribute points quest n. 2_12"),
    23: WaypointData(label="To Marketplace", MapID=250, step_name="[H]To Marketplace_18"),
    24: WaypointData(label="To Kaineng Center", MapID=303, step_name="[H]To Kaineng Center_19"),
    26: WaypointData(label="Craft max armor", MapID=194, step_name="[H]Craft max armor_20"),
    34: WaypointData(label="To LA", MapID=194, step_name="[H]To Lion's Arch_30"),
    35: WaypointData(label="To Temple of Ages", MapID=55, step_name="[H]To Temple of the Ages_31"),
    36: WaypointData(label="To Kamadan", MapID=194, step_name="[H]To Kamadan_32"),
    37: WaypointData(label="To Consulate Docks", MapID=194, step_name="[H]To Consulate Docks_33"),
    38: WaypointData(label="Unlock Olias", MapID=493, step_name="[H]Unlock Olias_34"),
}

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


    # --- 1) Find all waypoint step numbers <= current ---
    lower_or_equal_steps = [step for step in WAYPOINTS.keys() if step <= current_step]

    if not lower_or_equal_steps:
        return  # Nothing to jump to

    # --- 2) Pick the nearest lower step ---
    target_step = max(lower_or_equal_steps)

    # --- 3) Convert step number → FSM state name ---
    target_name = fsm.get_state_name_by_number(target_step)
    if not target_name:
        # The waypoint exists, but the FSM doesn’t have a state for it
        return

    # --- 4) Perform jump using your existing coroutine system ---
    fsm.pause()
    fsm.AddManagedCoroutine(
        f"{fsm.get_state_name_by_number(current_step)}_OPD",
        on_party_wipe_coroutine(bot, target_name)
    )

    return True


#region MAIN
selected_step = 0
filter_header_steps = True

iconwidth = 96

def _draw_texture():
    global iconwidth
    level = Agent.GetLevel(Player.GetAgentID())
    path = os.path.join(Py4GW.Console.get_projects_path(),"Sources", "ApoSource", "textures","factions_leveler_art.png")
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
    main_child_dimensions: Tuple[int, int] = (350, 275)
    try:
        bot.Update()
        bot.UI.draw_window()
        if PyImGui.begin(bot.config.bot_name, PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.begin_tab_bar(bot.config.bot_name + "_tabs"):
                if PyImGui.begin_tab_item("Main"):
                    PyImGui.dummy(*main_child_dimensions)
                    if PyImGui.collapsing_header("Direct Navigation"):
                        for step_num, waypoint in WAYPOINTS.items():

                            map_name = Map.GetMapName(waypoint.MapID)

                            # Tree node: visible label is waypoint.label, ID is unique
                            if PyImGui.tree_node(f"{waypoint.label}##wp_{step_num}"):

                                # Travel button
                                if PyImGui.button(f"Travel##travel_{step_num}"):
                                    Map.Travel(waypoint.MapID)

                                PyImGui.same_line(0,-1)

                                # Jump to FSM step button
                                if PyImGui.button(f"Go to Step##step_{step_num}"):
               
                                    bot.config.fsm_running = True
                                    bot.config.FSM.reset()
                                    bot.config.FSM.jump_to_state_by_name(waypoint.step_name)

                                PyImGui.tree_pop()
                    PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
        PyImGui.end()
        

    except Exception as e:
        Py4GW.Console.Log(bot.config.bot_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()

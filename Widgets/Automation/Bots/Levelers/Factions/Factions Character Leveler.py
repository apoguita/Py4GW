from __future__ import annotations
from typing import List, Tuple, Generator, Any
import os
import PyImGui
from Py4GW import Game
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Bags, Botting,
                          AutoPathing, ImGui, ActionQueueManager, Map, Agent, Player, UIManager, GWUI, HeroType, Skill, AgentArray)
from Py4GWCoreLib.Builds.Any.KeiranThackerayEOTN import KeiranThackerayEOTN
from Py4GWCoreLib.Builds.Any.AutoCombat import AutoCombat
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.enums_src.UI_enums import UIMessage
from Py4GWCoreLib.py4gwcorelib_src.Color import Color

MODULE_NAME = "Factions Character Leveler"
MODULE_ICON = "Textures\\Module_Icons\\Leveler - Factions.png"

bot = Botting("Factions Leveler",
              upkeep_candy_apple_restock=10,
              upkeep_honeycomb_restock=20,
              upkeep_war_supplies_restock=10,
              upkeep_auto_inventory_management_active=False,
              upkeep_auto_combat_active=False,
              upkeep_auto_loot_active=True)

class BotSettings:
    CUSTOM_BOW_ID = 0 #Change this if you have already have a bow crafted for War supply farm runs.
    CRAFTED_BOW_ID = 11723

#region MainRoutine
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    Exit_Monastery_Overlook(bot)
    Forming_A_Party(bot)
    Unlock_Secondary_Profession(bot)
    Unlock_Xunlai_Storage(bot)
    Craft_Weapon(bot)
    Craft_Monastery_Armor(bot)
    Destroy_Starter_Armor_And_Useless_Items(bot)
    Extend_Inventory_Space(bot)
    To_Minister_Chos_Estate(bot)
    Unlock_Skills_Trainer(bot)
    Minister_Chos_Estate_Mission(bot)
    Attribute_Points_Quest_1(bot)
    Warning_The_Tengu(bot)
    The_Threat_Grows(bot)
    The_Road_Less_Traveled(bot)
    Craft_Seitung_Armor(bot)
    Destroy_Monastery_Armor(bot)
    To_Zen_Daijun(bot)
    Complete_Skills_Training(bot)
    Zen_Daijun_Mission(bot)
    To_Marketplace(bot)
    To_Kaineng_Center(bot)
    Craft_Max_Armor(bot)
    Destroy_Seitung_Armor(bot)
    The_Search_For_A_Cure(bot)
    A_Masters_Burden(bot)
    Unlock_Mox(bot)
    To_Boreal_Station(bot)
    To_Eye_of_the_North(bot)
    Unlock_Eye_Of_The_North_Pool(bot)
    Farm_Until_Level_20(bot)
    Attribute_Points_Quest_2(bot)
    To_Gunnars_Hold(bot)
    Unlock_Kilroy_Stonekin(bot)
    To_Longeyes_Edge(bot)
    Unlock_NPC_For_Vaettir_Farm(bot)
    To_Lions_Arch(bot)
    #To_Temple_of_The_Ages(bot)
    To_Kamadan(bot)
    To_Consulate_Docks(bot)
    Unlock_Olias(bot)
    Unlock_Remaining_Secondary_Professions(bot)
    Unlock_Mercenary_Heroes(bot)


#region Helpers
def _load_navmesh_object(bot) -> None:
    """Try to get the NavMesh for validation. If not cached yet, schedule async load."""
    try:
        nav = AutoPathing().get_navmesh()
        if nav is not None:
            navmesh = nav
            return
    except Exception as e:
        Py4GW.Console.Log("Navmesh", f"Navmesh load failed: {e}", Py4GW.Console.MessageType.Warning)
    def _load_coro():
        yield from AutoPathing().load_pathing_maps()
        nav = AutoPathing().get_navmesh()
        if nav is not None:
            navmesh = nav
    GLOBAL_CACHE.Coroutines.append(_load_coro())

def QuestLoop(quest_id, quest_x, quest_y, quest_dialog, mode="accept", quest_npc=0, multi=0):
    attempts = 0
    label = f"Quest {mode.capitalize()} Loop"
    action_inf  = "complete" if mode == "complete" else "accept"
    action_past = "completed" if mode == "complete" else "accepted"
    npc_id = 0
    current_map = Map.GetMapID()

    if quest_npc == 0:
        yield from bot.Move._coro_xy(quest_x, quest_y)
        npc_id = Routines.Agents.GetNearestNPC(200)
    elif quest_npc != 0:
        npc_id = Routines.Agents.GetAgentIDByModelID(quest_npc)

    if quest_x == 0 and quest_y == 0:
        ConsoleLog(label, f"NPC{quest_npc}", Py4GW.Console.MessageType.Info)
        npc_id = Routines.Agents.GetAgentIDByModelID(quest_npc)
        quest_x, quest_y = Agent.GetXY(npc_id)
        ConsoleLog(label, f"X{quest_x} Y{quest_y}", Py4GW.Console.MessageType.Info)
    
    def loop_condition():
        if mode == "complete":
            return bot.Quest.GetActiveQuest() == quest_id
        elif mode == "step":
            return Agent.HasQuest(npc_id)
        elif mode =="skip":
            return current_map == Map.GetMapID()
        else:
            return bot.Quest.GetActiveQuest() != quest_id

    def success_condition():
        if mode == "complete":
            return bot.Quest.GetActiveQuest() != quest_id
        elif mode == "step":
            return not Agent.HasQuest(npc_id) or current_map != Map.GetMapID()
        elif mode == "skip":
            return not Agent.HasQuest(npc_id) or current_map != Map.GetMapID()
        else:
            return bot.Quest.GetActiveQuest() == quest_id

    while loop_condition() and attempts < 5:
        ConsoleLog(label, f"Attempting to {action_inf} quest #{quest_id}", Py4GW.Console.MessageType.Info)
        yield from bot.Move._coro_xy_and_dialog(quest_x, quest_y, quest_dialog)
        if multi != 0:
            yield from bot.Move._coro_xy_and_dialog(quest_x, quest_y, multi)
        yield from Routines.Yield.wait(500)
        attempts += 1

    if success_condition():
        ConsoleLog(label, f"Successfully {action_past} quest #{quest_id}", Py4GW.Console.MessageType.Info)
        return
    else:
        fsm = bot.config.FSM
        fsm.pause()
        ConsoleLog(label, f"The bot attempted and failed to {action_inf} quest #{quest_id}. The bot has stopped.", Py4GW.Console.MessageType.Info)

#region Battle configuration
def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.Templates.Pacifist()
    
def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Templates.Aggressive()
    bot.Events.OnPartyMemberDeadBehindCallback(lambda: bot.Templates.Routines.OnPartyMemberDeathBehind())
    bot.Properties.Enable("candy_apple")
    bot.Properties.Enable("war_supplies")
    bot.Properties.Enable("honeycomb")
#endregion

#region Henchmen / Hero team
def AddHenchmen():
    party_size = Map.GetMaxPartySize()

    henchmen_list = []
    if party_size <= 4:
        henchmen_list.extend([2, 5, 1]) 
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
    
    # Add all henchmen quickly
    for henchman_id in henchmen_list:
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(henchman_id)
        ConsoleLog("addhenchman",f"Added Henchman: {henchman_id}", log=False)
    
    # Single wait for all henchmen to join
    yield from Routines.Yield.wait(1000)

def StandardHeroTeam():
    party_size = Map.GetMaxPartySize()

    hero_list = []
    skill_templates = []

    hero_list.extend([HeroType.Gwen, HeroType.Vekk, HeroType.Ogden, HeroType.MOX])
    skill_templates = [
            "OQhkAsC8gFKgGckjHFRUGCA",  # Gwen
            "OgVDI8gsCawROeUEtZIA",     # Vekk
            "OwUUMsG/E4GgMnZskzkIZQAA", # Ogden
            "OgCikys8wchuD4xb5VAAAAAA"  # MOX
        ]
    
    # Add all heroes quickly
    for hero in hero_list:
        GLOBAL_CACHE.Party.Heroes.AddHero(hero.value)
        ConsoleLog("addhero",f"Added Hero: {hero.name}", log=False)
    
    # Single wait for all heroes to join
    yield from Routines.Yield.wait(1000)
    
    # Load skillbars for all positions
    for position in range(len(hero_list)):
        GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(position + 1, skill_templates[position])
        ConsoleLog("skillbar", f"Loading skillbar for position {position + 1}", log=True)
        yield from Routines.Yield.wait(500)
    
    # Set all heroes to guard mode
    for position in range(1, len(hero_list) + 1):
        hero_agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(position)
        if hero_agent_id > 0:
            GLOBAL_CACHE.Party.Heroes.SetHeroBehavior(hero_agent_id, 1)  # 1 = Guard mode
            yield from Routines.Yield.wait(100)
#endregion

#region Skill template
def EquipSkillBar(skillbar = ""):
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    level = Agent.GetLevel(Player.GetAgentID())

    if level < 3: #10 attribute points available
        if profession == "Warrior":
            skillbar = "OQAAAAAAAAAAAAAA"
        elif profession == "Ranger":
            skillbar = "OgAAAAAAAAAAAAAA"
        elif profession == "Monk":
            skillbar = "OwAAAAAAAAAAAAAA"
        elif profession == "Necromancer":
            skillbar = "OABAAAAAAAAAAAAA"
        elif profession == "Mesmer":
            skillbar = "OQBAAAAAAAAAAAAA"
        elif profession == "Elementalist":
            skillbar = "OgBAAAAAAAAAAAAA"
        elif profession == "Ritualist":
            skillbar = "OACAAAAAAAAAAAAA"
        elif profession == "Assassin":
            skillbar = "OwBAAAAAAAAAAAAA"
    elif level < 20: #Domination at 12 for most damage
        if profession == "Warrior":
            skillbar = "OQUBIskDcdG0DaAKUECA"
        elif profession == "Ranger":
            skillbar = "OgUBIskDcdG0DaAKUECA"
        elif profession == "Monk":
            skillbar = "OwUBIskDcdG0DaAKUECA"
        elif profession == "Necromancer":
            skillbar = "OAVBIskDcdG0DaAKUECA"
        elif profession == "Mesmer":
            skillbar = "OQBBIskDcdG0DaAKUECA"
        elif profession == "Elementalist":
            skillbar = "OgVBIskDcdG0DaAKUECA"
        elif profession == "Ritualist":
            skillbar = "OAWBIskDcdG0DaAKUECA"
        elif profession == "Assassin":
            skillbar = "OAWBIskDcdG0DaAKUECA"
    else:   #Added Inspiration for addtional mana gains
        if profession == "Warrior":
            skillbar = "OQUCErwSOw1ZQPoBoQRIA"
        elif profession == "Ranger":
            skillbar = "OgUCErwSOw1ZQPoBoQRIA"
        elif profession == "Monk":
            skillbar = "OwUCErwSOw1ZQPoBoQRIA"
        elif profession == "Necromancer":
            skillbar = "OAVCErwSOw1ZQPoBoQRIA"
        elif profession == "Mesmer":
            skillbar = "OQBBIskDcdG0DaAHUECA"
        elif profession == "Elementalist":
            skillbar = "OgVCErwSOw1ZQPoBoQRIA"
        elif profession == "Ritualist":
            skillbar = "OAWCErwSOw1ZQPoBoQRIA"
        elif profession == "Assassin":
            skillbar = "OwVCErwSOw1ZQPoBoQRIA"
    yield from Routines.Yield.Skills.LoadSkillbar(skillbar)

#endregion

def PrepareForBattle(bot: Botting):
    ConfigureAggressiveEnv(bot)
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AddHenchmen, "Add Henchmen")
    bot.Items.Restock.CandyApple()
    bot.Items.Restock.WarSupplies()
    bot.Items.Restock.Honeycomb()

#endregion

#region Armor
# Per-profession monastery and seitung armor data.
# "buy": materials to purchase as (model_id, count) pairs.
# "monastery" / "seitung": pieces to craft in order as (item_id, [mat], [qty]).
_EARLY_ARMOR_DATA = {
    "Warrior": {
        "buy":       [(ModelID.Bolt_Of_Cloth.value, 6)],
        "monastery": [
            (10156, [ModelID.Bolt_Of_Cloth.value], [3]),   # Chest
            (10158, [ModelID.Bolt_Of_Cloth.value], [2]),   # Pants
            (10155, [ModelID.Bolt_Of_Cloth.value], [1]),   # Boots
            (10030, [ModelID.Bolt_Of_Cloth.value], [1]),   # Head
            (10157, [ModelID.Bolt_Of_Cloth.value], [1]),   # Gloves
        ],
        "seitung": [
            (10164, [ModelID.Bolt_Of_Cloth.value], [18]),  # Chest
            (10166, [ModelID.Bolt_Of_Cloth.value], [12]),  # Pants
            (10163, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Boots
            (10046, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Head
            (10165, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Gloves
        ],
    },
    "Ranger": {
        "buy":       [(ModelID.Tanned_Hide_Square.value, 6)],
        "monastery": [
            (10605, [ModelID.Tanned_Hide_Square.value], [3]),   # Chest
            (10607, [ModelID.Tanned_Hide_Square.value], [2]),   # Pants
            (10604, [ModelID.Tanned_Hide_Square.value], [1]),   # Boots
            (14655, [ModelID.Tanned_Hide_Square.value], [1]),   # Head
            (10606, [ModelID.Tanned_Hide_Square.value], [1]),   # Gloves
        ],
        "seitung": [
            (10613, [ModelID.Tanned_Hide_Square.value], [18]),  # Chest
            (10615, [ModelID.Tanned_Hide_Square.value], [12]),  # Pants
            (10612, [ModelID.Tanned_Hide_Square.value], [ 6]),  # Boots
            (10483, [ModelID.Tanned_Hide_Square.value], [ 6]),  # Head
            (10614, [ModelID.Tanned_Hide_Square.value], [ 6]),  # Gloves
        ],
    },
    "Monk": {
        "buy":       [(ModelID.Bolt_Of_Cloth.value, 6), (ModelID.Pile_Of_Glittering_Dust.value, 1)],
        "monastery": [
            (9611, [ModelID.Bolt_Of_Cloth.value],           [3]),   # Chest
            (9613, [ModelID.Bolt_Of_Cloth.value],           [2]),   # Pants
            (9610, [ModelID.Bolt_Of_Cloth.value],           [1]),   # Boots
            (9590, [ModelID.Pile_Of_Glittering_Dust.value], [1]),   # Head
            (9612, [ModelID.Bolt_Of_Cloth.value],           [1]),   # Gloves
        ],
        "seitung": [
            (9619, [ModelID.Bolt_Of_Cloth.value],           [18]),  # Chest
            (9621, [ModelID.Bolt_Of_Cloth.value],           [12]),  # Pants
            (9618, [ModelID.Bolt_Of_Cloth.value],           [ 6]),  # Boots
            (9600, [ModelID.Pile_Of_Glittering_Dust.value], [ 6]),  # Head
            (9620, [ModelID.Bolt_Of_Cloth.value],           [ 6]),  # Gloves
        ],
    },
    "Assassin": {
        "buy":       [(ModelID.Bolt_Of_Cloth.value, 6)],
        "monastery": [
            (7185, [ModelID.Bolt_Of_Cloth.value], [3]),   # Chest
            (7187, [ModelID.Bolt_Of_Cloth.value], [2]),   # Pants
            (7184, [ModelID.Bolt_Of_Cloth.value], [1]),   # Boots
            (7116, [ModelID.Bolt_Of_Cloth.value], [1]),   # Head
            (7186, [ModelID.Bolt_Of_Cloth.value], [1]),   # Gloves
        ],
        "seitung": [
            (7193, [ModelID.Bolt_Of_Cloth.value], [18]),  # Chest
            (7195, [ModelID.Bolt_Of_Cloth.value], [12]),  # Pants
            (7192, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Boots
            (7126, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Head
            (7194, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Gloves
        ],
    },
    "Mesmer": {
        "buy":       [(ModelID.Bolt_Of_Cloth.value, 6)],
        "monastery": [
            (7538, [ModelID.Bolt_Of_Cloth.value], [3]),   # Chest
            (7540, [ModelID.Bolt_Of_Cloth.value], [2]),   # Pants
            (7537, [ModelID.Bolt_Of_Cloth.value], [1]),   # Boots
            (7517, [ModelID.Bolt_Of_Cloth.value], [1]),   # Head
            (7539, [ModelID.Bolt_Of_Cloth.value], [1]),   # Gloves
        ],
        "seitung": [
            (7546, [ModelID.Bolt_Of_Cloth.value], [18]),  # Chest
            (7548, [ModelID.Bolt_Of_Cloth.value], [12]),  # Pants
            (7545, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Boots
            (7528, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Head
            (7547, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Gloves
        ],
    },
    "Necromancer": {
        "buy":       [(ModelID.Tanned_Hide_Square.value, 6), (ModelID.Pile_Of_Glittering_Dust.value, 1)],
        "monastery": [
            (8749, [ModelID.Tanned_Hide_Square.value],      [3]),   # Chest
            (8751, [ModelID.Tanned_Hide_Square.value],      [2]),   # Pants
            (8748, [ModelID.Tanned_Hide_Square.value],      [1]),   # Boots
            (8731, [ModelID.Pile_Of_Glittering_Dust.value], [1]),   # Head
            (8750, [ModelID.Tanned_Hide_Square.value],      [1]),   # Gloves
        ],
        "seitung": [
            (8757, [ModelID.Tanned_Hide_Square.value],      [18]),  # Chest
            (8759, [ModelID.Tanned_Hide_Square.value],      [12]),  # Pants
            (8756, [ModelID.Tanned_Hide_Square.value],      [ 6]),  # Boots
            (8741, [ModelID.Pile_Of_Glittering_Dust.value], [ 6]),  # Head
            (8758, [ModelID.Tanned_Hide_Square.value],      [ 6]),  # Gloves
        ],
    },
    "Ritualist": {
        "buy":       [(ModelID.Bolt_Of_Cloth.value, 6)],
        "monastery": [
            (11310, [ModelID.Bolt_Of_Cloth.value], [3]),   # Chest
            (11313, [ModelID.Bolt_Of_Cloth.value], [2]),   # Pants
            (11309, [ModelID.Bolt_Of_Cloth.value], [3]),   # Boots (costs 3 cloth)
            (11194, [ModelID.Bolt_Of_Cloth.value], [1]),   # Head
            (11311, [ModelID.Bolt_Of_Cloth.value], [1]),   # Gloves
        ],
        "seitung": [
            (11320, [ModelID.Bolt_Of_Cloth.value], [18]),  # Chest
            (11323, [ModelID.Bolt_Of_Cloth.value], [12]),  # Pants
            (11319, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Boots
            (11203, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Head
            (11321, [ModelID.Bolt_Of_Cloth.value], [ 6]),  # Gloves
        ],
    },
    "Elementalist": {
        "buy":       [(ModelID.Bolt_Of_Cloth.value, 6), (ModelID.Pile_Of_Glittering_Dust.value, 1)],
        "monastery": [
            (9194, [ModelID.Bolt_Of_Cloth.value],           [3]),   # Chest
            (9196, [ModelID.Bolt_Of_Cloth.value],           [2]),   # Pants
            (9193, [ModelID.Bolt_Of_Cloth.value],           [1]),   # Boots
            (9171, [ModelID.Pile_Of_Glittering_Dust.value], [1]),   # Head
            (9195, [ModelID.Bolt_Of_Cloth.value],           [1]),   # Gloves
        ],
        "seitung": [
            (9202, [ModelID.Bolt_Of_Cloth.value],           [18]),  # Chest
            (9204, [ModelID.Bolt_Of_Cloth.value],           [12]),  # Pants
            (9201, [ModelID.Bolt_Of_Cloth.value],           [ 6]),  # Boots
            (9183, [ModelID.Pile_Of_Glittering_Dust.value], [ 6]),  # Head
            (9203, [ModelID.Bolt_Of_Cloth.value],           [ 6]),  # Gloves
        ],
    },
}

def _get_early_armor_data() -> dict:
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    return _EARLY_ARMOR_DATA.get(primary, _EARLY_ARMOR_DATA["Warrior"])

def BuyMaterials():
    for mat, count in _get_early_armor_data()["buy"]:
        for _ in range(count):
            yield from Routines.Yield.Merchant.BuyMaterial(mat)
        yield from Routines.Yield.wait(500)

def _craft_armor_set(bot: Botting, armor_key: str, gold_cost: int):
    for item_id, mats, qtys in _get_early_armor_data()[armor_key]:
        result = yield from Routines.Yield.Items.CraftItem(item_id, gold_cost, mats, qtys)
        yield from Routines.Yield.wait(500)
        if not result:
            ConsoleLog("CraftArmor", f"Failed to craft item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        result = yield from Routines.Yield.Items.EquipItem(item_id)
        if not result:
            ConsoleLog("CraftArmor", f"Failed to equip item ({item_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True

def CraftMonasteryArmor(bot: Botting):
    return (yield from _craft_armor_set(bot, "monastery", 20))

def CraftArmor(bot: Botting):
    return (yield from _craft_armor_set(bot, "seitung", 200))

# All per-profession max armor data in one place.
# Each entry: crafter NPC coords, materials to buy (common/rare as lists of (model_id, count)),
# and pieces to craft in order: (item_id, [mats], [qtys]).
_MAX_ARMOR_DATA = {
    "Warrior": {  # Ascalon armor — crafter: Suki
        "crafter":     (-891.00, -5382.00),
        "buy_common":  [(ModelID.Tanned_Hide_Square.value, 20)],
        "buy_rare":    [(ModelID.Steel_Ingot.value, 32)],
        "pieces": [
            (23395, [ModelID.Tanned_Hide_Square.value, ModelID.Steel_Ingot.value], [25,  4]),   # Gloves
            (23393, [ModelID.Tanned_Hide_Square.value, ModelID.Steel_Ingot.value], [25,  4]),   # Boots
            (23396, [ModelID.Tanned_Hide_Square.value, ModelID.Steel_Ingot.value], [50,  8]),   # Pants
            (23394, [ModelID.Tanned_Hide_Square.value, ModelID.Steel_Ingot.value], [75, 12]),   # Chest
            (23391, [ModelID.Tanned_Hide_Square.value, ModelID.Steel_Ingot.value], [25,  4]),   # Head
        ],
    },
    "Ranger": {  # Canthan armor — crafter: Kakumei
        "crafter":     (-700.00, -5156.00),
        "buy_common":  [(ModelID.Bolt_Of_Cloth.value, 20)],
        "buy_rare":    [(ModelID.Fur_Square.value, 32)],
        "pieces": [
            (23798, [ModelID.Bolt_Of_Cloth.value, ModelID.Fur_Square.value], [25,  4]),         # Gloves
            (23796, [ModelID.Bolt_Of_Cloth.value, ModelID.Fur_Square.value], [25,  4]),         # Boots
            (23799, [ModelID.Bolt_Of_Cloth.value, ModelID.Fur_Square.value], [50,  8]),         # Pants
            (23797, [ModelID.Bolt_Of_Cloth.value, ModelID.Fur_Square.value], [75, 12]),         # Chest
            (23794, [ModelID.Bolt_Of_Cloth.value, ModelID.Fur_Square.value], [25,  4]),         # Head
        ],
    },
    "Monk": {  # Shinjea armor — crafter: Ryoko
        "crafter":     (-1682.00, -3970.00),
        "buy_common":  [(ModelID.Bolt_Of_Cloth.value, 18)],
        "buy_rare":    [(ModelID.Roll_Of_Parchment.value, 5), (ModelID.Vial_Of_Ink.value, 4), (ModelID.Bolt_Of_Linen.value, 28)],
        "pieces": [
            (23727, [ModelID.Bolt_Of_Cloth.value,     ModelID.Bolt_Of_Linen.value],   [25,  4]),  # Gloves
            (23725, [ModelID.Bolt_Of_Cloth.value,     ModelID.Bolt_Of_Linen.value],   [25,  4]),  # Boots
            (23728, [ModelID.Bolt_Of_Cloth.value,     ModelID.Bolt_Of_Linen.value],   [50,  8]),  # Pants
            (23726, [ModelID.Bolt_Of_Cloth.value,     ModelID.Bolt_Of_Linen.value],   [75, 12]),  # Chest
            (23721, [ModelID.Roll_Of_Parchment.value, ModelID.Vial_Of_Ink.value],     [ 5,  4]),  # Head
        ],
    },
    "Assassin": {  # Canthan armor — crafter: Kakumei
        "crafter":     (-700.00, -5156.00),
        "buy_common":  [(ModelID.Bolt_Of_Cloth.value, 20)],
        "buy_rare":    [(ModelID.Leather_Square.value, 32)],
        "pieces": [
            (23442, [ModelID.Bolt_Of_Cloth.value, ModelID.Leather_Square.value], [25,  4]),     # Gloves
            (23440, [ModelID.Bolt_Of_Cloth.value, ModelID.Leather_Square.value], [25,  4]),     # Boots
            (23443, [ModelID.Bolt_Of_Cloth.value, ModelID.Leather_Square.value], [50,  8]),     # Pants
            (23441, [ModelID.Bolt_Of_Cloth.value, ModelID.Leather_Square.value], [75, 12]),     # Chest
            (23435, [ModelID.Bolt_Of_Cloth.value, ModelID.Leather_Square.value], [25,  4]),     # Head
        ],
    },
    "Mesmer": {  # Shinjea armor — crafter: Ryoko
        "crafter":     (-1682.00, -3970.00),
        "buy_common":  [(ModelID.Bolt_Of_Cloth.value, 20)],
        "buy_rare":    [(ModelID.Bolt_Of_Silk.value, 32)],
        "pieces": [
            (23582, [ModelID.Bolt_Of_Cloth.value, ModelID.Bolt_Of_Silk.value], [25,  4]),       # Gloves
            (23580, [ModelID.Bolt_Of_Cloth.value, ModelID.Bolt_Of_Silk.value], [25,  4]),       # Boots
            (23583, [ModelID.Bolt_Of_Cloth.value, ModelID.Bolt_Of_Silk.value], [50,  8]),       # Pants
            (23581, [ModelID.Bolt_Of_Cloth.value, ModelID.Bolt_Of_Silk.value], [75, 12]),       # Chest
            (23576, [ModelID.Bolt_Of_Cloth.value, ModelID.Bolt_Of_Silk.value], [25,  4]),       # Head
        ],
    },
    "Necromancer": {  # Shinjea armor — crafter: Ryoko
        "crafter":     (-1682.00, -3970.00),
        "buy_common":  [(ModelID.Tanned_Hide_Square.value, 18), (ModelID.Bone.value, 18)],
        "buy_rare":    [(ModelID.Roll_Of_Parchment.value, 5), (ModelID.Vial_Of_Ink.value, 4)],
        "pieces": [
            (23638, [ModelID.Tanned_Hide_Square.value, ModelID.Bone.value],         [25, 25]),  # Gloves
            (23636, [ModelID.Tanned_Hide_Square.value, ModelID.Bone.value],         [25, 25]),  # Boots
            (23639, [ModelID.Tanned_Hide_Square.value, ModelID.Bone.value],         [50, 50]),  # Pants
            (23637, [ModelID.Tanned_Hide_Square.value, ModelID.Bone.value],         [75, 75]),  # Chest
            (23632, [ModelID.Roll_Of_Parchment.value,  ModelID.Vial_Of_Ink.value], [ 5,  4]),  # Head
        ],
    },
    "Ritualist": {  # Shinjea armor — crafter: Ryoko
        "crafter":     (-1682.00, -3970.00),
        "buy_common":  [(ModelID.Bolt_Of_Cloth.value, 23)],
        "buy_rare":    [(ModelID.Leather_Square.value, 32)],
        "pieces": [
            (23942, [ModelID.Bolt_Of_Cloth.value, ModelID.Leather_Square.value], [25,  4]),     # Gloves
            (23940, [ModelID.Bolt_Of_Cloth.value, ModelID.Leather_Square.value], [25,  4]),     # Boots
            (23943, [ModelID.Bolt_Of_Cloth.value, ModelID.Leather_Square.value], [50,  8]),     # Pants
            (23941, [ModelID.Bolt_Of_Cloth.value, ModelID.Leather_Square.value], [75, 12]),     # Chest
            (23939, [ModelID.Bolt_Of_Cloth.value, ModelID.Leather_Square.value], [25,  4]),     # Head
        ],
    },
    "Elementalist": {  # Shinjea armor — crafter: Ryoko
        "crafter":     (-1682.00, -3970.00),
        "buy_common":  [(ModelID.Bolt_Of_Cloth.value, 18), (ModelID.Pile_Of_Glittering_Dust.value, 3)],
        "buy_rare":    [(ModelID.Bolt_Of_Silk.value, 28), (ModelID.Tempered_Glass_Vial.value, 4)],
        "pieces": [
            (23671, [ModelID.Bolt_Of_Cloth.value,           ModelID.Bolt_Of_Silk.value],        [25,  4]),  # Gloves
            (23669, [ModelID.Bolt_Of_Cloth.value,           ModelID.Bolt_Of_Silk.value],        [25,  4]),  # Boots
            (23672, [ModelID.Bolt_Of_Cloth.value,           ModelID.Bolt_Of_Silk.value],        [50,  8]),  # Pants
            (23670, [ModelID.Bolt_Of_Cloth.value,           ModelID.Bolt_Of_Silk.value],        [75, 12]),  # Chest
            (23643, [ModelID.Pile_Of_Glittering_Dust.value, ModelID.Tempered_Glass_Vial.value], [25,  4]),  # Head
        ],
    },
}

def _get_max_armor_data() -> dict:
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    return _MAX_ARMOR_DATA.get(primary, _MAX_ARMOR_DATA["Elementalist"])

def GetArmorCrafterCoords() -> tuple[float, float]:
    return _get_max_armor_data()["crafter"]

def BuyMaxArmorMaterials(material_type: str = "common"):
    for mat, count in _get_max_armor_data()[f"buy_{material_type}"]:
        for _ in range(count):
            if not (yield from Routines.Yield.Merchant.BuyMaterial(mat)):
                yield from Routines.Yield.wait(500)
                yield from Routines.Yield.Merchant.BuyMaterial(mat)
        yield from Routines.Yield.wait(500)

def DoCraftMaxArmor(bot: Botting):
    for item_id, mats, qtys in _get_max_armor_data()["pieces"]:
        result = yield from Routines.Yield.Items.CraftItem(item_id, 1000, mats, qtys)
        yield from Routines.Yield.wait(500)
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

_WEAPON_DATA = {
    "buy":    [(ModelID.Wood_Plank.value, 1)],
    "pieces": [(11641, [ModelID.Wood_Plank.value], [10])],  # Longbow, 10 wood planks
}

def BuyWeaponMaterials():
    for mat, count in _WEAPON_DATA["buy"]:
        for _ in range(count):
            yield from Routines.Yield.Merchant.BuyMaterial(mat)

def DoCraftWeapon(bot: Botting):
    for weapon_id, mats, qtys in _WEAPON_DATA["pieces"]:
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

_SHORTBOW_DATA = {
    "buy":    [(ModelID.Wood_Plank.value, 10), (ModelID.Plant_Fiber.value, 5)],
    "pieces": [(11730, [ModelID.Wood_Plank.value, ModelID.Plant_Fiber.value], [100, 50])],  # Longbow, 10 wood planks
}

def BuyShortbowMaterials():
    for mat, count in _SHORTBOW_DATA["buy"]:
        for _ in range(count):
            yield from Routines.Yield.Merchant.BuyMaterial(mat)

def DoCraftShortbow(bot: Botting):
    for weapon_id, mats, qtys in _SHORTBOW_DATA["pieces"]:
        result = yield from Routines.Yield.Items.CraftItem(weapon_id, 5000, mats, qtys)
        if not result:
            ConsoleLog("DoCraftShortbow", f"Failed to craft shortbow ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
        result = yield from Routines.Yield.Items.EquipItem(weapon_id)
        if not result:
            ConsoleLog("DoCraftShortbow", f"Failed to equip shortbow ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True

def BuyLongbowMaterials():
    for mat, count in _LONGBOW_DATA["buy"]:
        for _ in range(count):
            yield from Routines.Yield.Merchant.BuyMaterial(mat)
_LONGBOW_DATA = {
    "buy":    [(ModelID.Wood_Plank.value, 10), (ModelID.Feather.value, 5)],
    "pieces": [(11723, [ModelID.Wood_Plank.value, ModelID.Feather.value], [100, 50])],  # Longbow, 10 wood planks
}
def DoCraftLongbow(bot: Botting):
    for weapon_id, mats, qtys in _LONGBOW_DATA["pieces"]:
        result = yield from Routines.Yield.Items.CraftItem(weapon_id, 5000, mats, qtys)
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
                     6387,  # A Starter Daggers
                     2724,  # E Starter Elemental Rod
                     2652,  # Me Starter Cane
                     2787,  # Mo Starter Holy Rod
                     2694,  # N Starter Truncheon
                     477,   # R Starter Bow
                     6498,  # Rt Starter Ritualist Wand                   
                     2982,  # W Starter Sword
                     30853, # MOX Manual
                     24897  #Brass Knuckles
                    ]
    
    for model in starter_armor:
        result = yield from Routines.Yield.Items.DestroyItem(model)
    
    for model in useless_items:
        result = yield from Routines.Yield.Items.DestroyItem(model)

def destroy_monastery_armor() -> Generator[Any, Any, None]:
    for item_id, _, _ in _get_early_armor_data()["monastery"]:
        yield from Routines.Yield.Items.DestroyItem(item_id)

def destroy_seitung_armor() -> Generator[Any, Any, None]:
    for item_id, _, _ in _get_early_armor_data()["seitung"]:
        yield from Routines.Yield.Items.DestroyItem(item_id)
#endregion

#endregion
#region Routines
def _on_death(bot: "Botting", step_name: str = ""):
    """Player died (in-map): halt movement, wait for outpost, then resume."""
    died_in_ab = (Map.GetMapID() == _AB_MAP_ID)  # capture before the wait
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("halt_on_death", "active", True)
    bot.Properties.ApplyNow("movement_timeout", "value", 15000)
    bot.Properties.ApplyNow("auto_combat", "active", False)
    if died_in_ab:
        yield from Routines.Yield.wait(8000)
        fsm = bot.config.FSM
        target_step = _resolve_waypoint_state_name(fsm, _FARM_RESTART_STEP)
        if target_step:
            fsm.jump_to_state_by_name(target_step)
        fsm.resume()
    else:
        Player.SendChatCommand("resign")
        yield from Routines.Yield.wait(1000)
        while True:
            yield from Routines.Yield.wait(500)
            if not Routines.Checks.Map.MapValid():
                continue
            if Routines.Checks.Map.IsOutpost() and Map.IsMapReady():
                break
            if GLOBAL_CACHE.Party.IsPartyDefeated():
                GLOBAL_CACHE.Party.ReturnToOutpost()
        fsm = bot.config.FSM
        if not step_name or not fsm.has_state(step_name):
            state_names = fsm.get_state_names()
            step_name = state_names[0] if state_names else ""
        if not step_name:
            fsm.resume()
            yield
            return
        fsm.ResetAndStartAtStep(step_name)
    bot.Properties.ApplyNow("auto_combat", "active", True)
    bot.Templates.Aggressive()
    yield


def _on_party_defeated(bot: "Botting", step_name: str):
    """Party wiped: trigger return to outpost, then restart from the same step."""
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("auto_combat", "active", False)
    # Short grace period, then keep retrying ReturnToOutpost until we reach the outpost
    yield from Routines.Yield.wait(1000)
    while True:
        yield from Routines.Yield.wait(500)
        if not Routines.Checks.Map.MapValid():
            continue
        if Routines.Checks.Map.IsOutpost() and Map.IsMapReady():
            break
        # Still in explorable / defeat screen — keep calling ReturnToOutpost
        if GLOBAL_CACHE.Party.IsPartyDefeated():
            GLOBAL_CACHE.Party.ReturnToOutpost()
    fsm = bot.config.FSM
    if not step_name or not fsm.has_state(step_name):
        state_names = fsm.get_state_names()
        step_name = state_names[0] if state_names else ""
    if not step_name:
        fsm.resume()
        yield
        return
    fsm.ResetAndStartAtStep(step_name)
    bot.Properties.ApplyNow("auto_combat", "active", True)
    bot.Templates.Aggressive()
    yield

def on_death(bot: "Botting"):
    player_morale  = Player.GetMorale()
    morale_trigger = (player_morale == 0)
    if (Map.GetMapID() == _AB_MAP_ID) or morale_trigger:
        print(f"Morale trigger fired (player={player_morale}. Run Failed, Restarting...")
        ActionQueueManager().ResetAllQueues()
        fsm = bot.config.FSM
        current_step = _get_mission_header_step(fsm) or (fsm.current_state.name if fsm.current_state else "")
        fsm.pause()
        fsm.AddManagedCoroutine("OnDeath", _on_death(bot, current_step))

def _get_mission_header_step(fsm) -> str | None:
    """Return the [H] header state name for the current state (so we restart the mission, not a sub-step)."""
    if not fsm.current_state or not fsm.states:
        return None
    try:
        idx = fsm.states.index(fsm.current_state)
    except ValueError:
        return None
    for i in range(idx, -1, -1):
        if fsm.states[i].name.startswith("[H]"):
            return fsm.states[i].name
    return None

def on_party_defeated(bot: "Botting"):
    # In AB the player is solo — OnDeathCallback fires first and handles it.
    # Skip here to avoid double-recovery.
    if Map.GetMapID() == _AB_MAP_ID:
        return
    print("Party defeated. Returning to outpost and retrying current step...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    current_step = _get_mission_header_step(fsm) or (fsm.current_state.name if fsm.current_state else "")
    fsm.pause()  # Stop main state (no movement/combat); recovery still runs (managed coroutines run before pause check)
    fsm.AddManagedCoroutine("OnPartyDefeated", _on_party_defeated(bot, current_step))

def InitializeBot(bot: Botting) -> None:
    bot.Events.OnDeathCallback(lambda: on_death(bot))
    bot.Events.OnPartyDefeatedCallback(lambda: on_party_defeated(bot))

def Exit_Monastery_Overlook(bot: Botting) -> None:
    bot.States.AddHeader("Exit Monastery Overlook")
    bot.Move.XYAndDialog(-7048,5817,0x85)
    bot.Wait.ForMapLoad(target_map_name="Shing Jea Monastery")

def Forming_A_Party(bot: Botting) -> None:
    bot.States.AddHeader("Quest: Forming A Party")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    PrepareForBattle(bot)
    bot.Items.SpawnAndDestroyBonusItems()
    exec_fn = lambda: QuestLoop(440, -14063.00, 10044.00, 0x81B801)
    bot.States.AddCustomState(exec_fn, "Accept - Forming A Party")
    #bot.Move.XYAndDialog(-14063.00, 10044.00, 0x81B801)
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    #bot.Move.XYAndDialog(19673.00, -6982.00, 0x81B807)
    exec_fn = lambda: QuestLoop(440, 19673.00, -6982.00, 0x81B807, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - Forming A Party")
    
def Unlock_Secondary_Profession(bot: Botting) -> None:
    def assign_profession_unlocker_dialog():
        global bot
        primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
        if primary == "Mesmer":
            #yield from bot.Interact._coro_with_agent((-92, 9217),0x813D08)
            exec_fn = lambda: QuestLoop(317, -92, 9217,  0x813D08)
            bot.States.AddCustomState(exec_fn, "Accept - Choose Your Secondary Profession (Factions quest)")
        else:
            #yield from bot.Interact._coro_with_agent((-92, 9217),0x813D0E)
            exec_fn = lambda: QuestLoop(317, -92, 9217,  0x813D0E)
            bot.States.AddCustomState(exec_fn, "Accept - Choose Your Secondary Profession (Factions quest)")

    bot.States.AddHeader("Unlock Secondary Profession")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    ConfigurePacifistEnv(bot)
    bot.Move.XYAndExitMap(-3480, 9460, target_map_name="Linnok Courtyard")
    bot.Move.XY(-159, 9174)
    #bot.States.AddCustomState(assign_profession_unlocker_dialog, "Update Secondary Profession Dialog")
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary == "Mesmer":
        #yield from bot.Interact._coro_with_agent((-92, 9217),0x813D08)
        exec_fn = lambda: QuestLoop(317, -92, 9217,  0x813D08)
        bot.States.AddCustomState(exec_fn, "Accept - Choose Your Secondary Profession (Factions quest)")
    elif primary != "Mesmer":
        #yield from bot.Interact._coro_with_agent((-92, 9217),0x813D0E)
        exec_fn = lambda: QuestLoop(317, -92, 9217,  0x813D0E)
        bot.States.AddCustomState(exec_fn, "Accept - Choose Your Secondary Profession (Factions quest)")
    #bot.Wait.ForTime(3000)
    #bot.UI.CancelSkillRewardWindow()
    #bot.Wait.ForTime(3000)
    #primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    #if primary != "Mesmer":
    #    bot.UI.CancelSkillRewardWindow()
    #bot.Dialogs.AtXY(-92, 9217,  0x813D07) 
    exec_fn = lambda: QuestLoop(317, -92, 9217,  0x813D07, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - Choose Your Secondary Profession (Factions quest)")
    bot.Wait.ForTime(3000)
    #bot.Dialogs.AtXY(-92, 9217,  0x813E01) #Minister Cho's Estate quest
    exec_fn = lambda: QuestLoop(318, -92, 9217, 0x813E01) # Accept - A Formal Introduction
    bot.States.AddCustomState(exec_fn, "Accept - A Formal Introduction")
    
    bot.Move.XYAndExitMap(-3762, 9471, target_map_name="Shing Jea Monastery")

def Unlock_Xunlai_Storage(bot: Botting) -> None:
    bot.States.AddHeader("Unlock Xunlai Storage")
    path_to_xunlai: List[Tuple[float, float]] = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3825.09, 10386.81),]
    bot.Move.FollowPathAndDialog(path_to_xunlai, 0x84)
    bot.Dialogs.WithModel(283, 0x800001) # Model id updated 20.12.2025 GW Reforged
    bot.Dialogs.WithModel(283, 0x800002) # Model id updated 20.12.2025 GW Reforged

def Craft_Weapon(bot: Botting):
    bot.States.AddHeader("Craft weapon")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    bot.Items.WithdrawGold(5000)
    bot.Move.XY(-10896.94, 10807.54)
    bot.Move.XY(-10942.73, 10783.19)
    bot.Move.XYAndInteractNPC(-10614.00, 10996.00)  # Common material merchant
    exec_fn_wood = lambda: BuyWeaponMaterials()
    bot.States.AddCustomState(exec_fn_wood, "Buy Wood Planks")
    bot.States.AddCustomState(BuyMaterials, "Buy Early Armor Materials")
    bot.Move.XY(-10896.94, 10807.54)
    bot.Move.XY(-6519.00, 12335.00)
    bot.Move.XYAndInteractNPC(-6519.00, 12335.00)  # Weapon crafter in Shing Jea Monastery
    bot.Wait.ForTime(1000)
    exec_fn = lambda: DoCraftWeapon(bot)
    bot.States.AddCustomState(exec_fn, "Craft Weapons")
    bot.States.AddCustomState(_handle_bonus_bow, "Equip Custom/Crafted Bow from previous run")

def Craft_Monastery_Armor(bot: Botting):
    bot.States.AddHeader("Craft monastery armor")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    bot.Move.XYAndInteractNPC(-7115.00, 12636.00)  # Armor crafter in Shing Jea Monastery
    exec_fn = lambda: CraftMonasteryArmor(bot)
    bot.States.AddCustomState(exec_fn, "Craft Armor")

def Extend_Inventory_Space(bot: Botting):
    bot.States.AddHeader("Extend Inventory Space")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    bot.Move.XY(-11866, 11444)
    bot.Move.XYAndInteractNPC(-11866, 11444) # Merchant NPC in Shingjea Monastery
    bot.helpers.Merchant.buy_item(ModelID.Bag.value, 1) # Buy Bag 1
    bot.Wait.ForTime(250)
    bot.helpers.Merchant.buy_item(ModelID.Bag.value, 1) # Buy Bag 2
    bot.Wait.ForTime(250)
    bot.helpers.Merchant.buy_item(ModelID.Belt_Pouch.value, 1) # Buy Belt Pouch
    bot.Wait.ForTime(250)
    bot.Items.EquipInventoryBag(ModelID.Belt_Pouch.value, Bags.BeltPouch)
    bot.Items.EquipInventoryBag(ModelID.Bag.value, Bags.Bag1)
    bot.Items.EquipInventoryBag(ModelID.Bag.value, Bags.Bag2)

def Unlock_Skills_Trainer(bot: Botting) -> None:
    bot.States.AddHeader("Unlock Skills Trainer")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    bot.Move.XYAndDialog(-8790.00, 10366.00, 0x84)
    bot.Wait.ForTime(3000)
    bot.Player.BuySkill(57)
    bot.Wait.ForTime(250)
    bot.Player.BuySkill(25)
    bot.Wait.ForTime(250)
    bot.Player.BuySkill(860)

def To_Minister_Chos_Estate(bot: Botting):
    bot.States.AddHeader("To Minister Cho's Estate")
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    bot.Move.XYAndExitMap(-14961, 11453, target_map_name="Sunqua Vale")
    ConfigurePacifistEnv(bot)
    bot.Move.XY(16182.62, -7841.86)
    bot.Move.XY(6611.58, 15847.51)
    #bot.Move.XYAndDialog(6637, 16147, 0x80000B)
    exec_fn = lambda: QuestLoop(318, 6637, 16147, 0x80000B, mode="skip")
    bot.States.AddCustomState(exec_fn, "Step 1 - A Formal Introduction")
    bot.Wait.ForMapToChange(target_map_id=214)
    #bot.Move.XYAndDialog(7884, -10029, 0x813E07)
    exec_fn = lambda: QuestLoop(318, 7884, -10029, 0x813E07, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - A Formal Introduction")
    
def Minister_Chos_Estate_Mission(bot: Botting) -> None:
    bot.States.AddHeader("Minister Cho's Estate mission")
    bot.Map.Travel(target_map_id=214)
    PrepareForBattle(bot)
    bot.Map.EnterChallenge(delay=4500, target_map_id=214)
    bot.Wait.ForMapToChange(target_map_id=214)
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
    bot.Wait.ForTime(5000)
    bot.Move.XY(-16924, 2445)  # Move to Final Destination
    bot.Interact.WithNpcAtXY(-17031, 2448) #"Interact with Minister Cho"
    bot.Wait.ForMapToChange(target_map_id=251) #Ran Musu Gard 
    
def Attribute_Points_Quest_1(bot: Botting):
    bot.States.AddHeader("Attribute points quest n. 1")
    bot.Map.Travel(target_map_id=251) #Ran Musu Gardens
    bot.Move.XY(16184.75, 19001.78)
    #bot.Move.XYAndDialog(14363.00, 19499.00, 0x815A01)  # I Like treasure
    exec_fn = lambda: QuestLoop(346, 14363.00, 19499.00, 0x815A01)
    bot.States.AddCustomState(exec_fn, "Accept - Lost Treasure")
    PrepareForBattle(bot)
    path = [(13713.27, 18504.61),(14576.15, 17817.62),(15824.60, 18817.90),(17005, 19787)]
    bot.Move.FollowPathAndExitMap(path, target_map_id=245)
    bot.Properties.Disable("auto_loot")
    bot.Move.XY(-17979.38, -493.08)
    #bot.Dialogs.WithModel(3093, 0x815A04) #Guard model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(346, 0, 0, 0x815A04, mode="step", quest_npc=3093)
    bot.States.AddCustomState(exec_fn, "Step 1 - Lost Treasure")
    bot.Wait.ForTime(5000)
    exit_function = lambda: (
        not (Routines.Checks.Agents.InDanger(aggro_area=Range.Spirit)) and
        Agent.HasQuest(Routines.Agents.GetAgentIDByModelID(3093))
    )
    bot.Move.FollowModel(3093, follow_range=(Range.Area.value), exit_condition=exit_function) #Guard model id updated 20.12.2025 GW Reforged
    #bot.Dialogs.WithModel(3093, 0x815A07) #Guard model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(346, 0, 0, 0x815A07, mode="complete", quest_npc=3093)
    bot.States.AddCustomState(exec_fn, "Step 2 - Lost Treasure")
    bot.Map.Travel(target_map_id=251) #Ran Musu Gardens
    
def Warning_The_Tengu(bot: Botting):
    bot.States.AddHeader("Quest: Warning the Tengu")
    bot.Map.Travel(target_map_id=251) #Ran Musu Gardens
    bot.States.AddCustomState(lambda: _handle_bonus_bow(bot), "HandleBonusBow")
    #bot.Move.XYAndDialog(15846, 19013, 0x815301)
    exec_fn = lambda: QuestLoop(339, 15846, 19013, 0x815301)
    bot.States.AddCustomState(exec_fn, "Accept - Warning the Tengu")
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(14730, 15176, target_map_name="Kinya Province")
    bot.Move.XY(1429, 12768)
    #bot.Move.XYAndDialog(-1023, 4844, 0x815304)
    exec_fn = lambda: QuestLoop(339, -1023, 4844, 0x815304, mode="step")
    bot.States.AddCustomState(exec_fn, "Step 1 - Warning the Tengu")
    bot.Move.XY(-5011, 732, "Move to Tengu Killspot")
    bot.Wait.UntilOutOfCombat()
    #bot.Move.XYAndDialog(-1023, 4844, 0x815307)
    exec_fn = lambda: QuestLoop(339, -1023, 4844, 0x815307, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - Warning the Tengu")

def The_Threat_Grows(bot: Botting):
    bot.States.AddHeader("Quest: The Threat Grows")
    #bot.Dialogs.AtXY(-1023, 4844, 0x815401)
    exec_fn = lambda: QuestLoop(340, -1023, 4844, 0x815401)
    bot.States.AddCustomState(exec_fn, "Accept - The Threat Grows")
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
    #bot.Dialogs.WithModel(3367, 0x815407) #Sister Tai model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(340, 0, 0, 0x815407, mode="complete", quest_npc=3367)
    bot.States.AddCustomState(exec_fn, "Complete - The Threat Grows")

    #bot.Dialogs.WithModel(3367, 0x815501) #Sister Tai model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(341, 0, 0, 0x815501, quest_npc=3367)
    bot.States.AddCustomState(exec_fn, "Accept - Journey of the Master")
     
def The_Road_Less_Traveled(bot: Botting):
    bot.States.AddHeader("Quest: The Road Less Traveled")
    bot.Map.Travel(target_map_id=242) #Shin Jea Monastery
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(-3480, 9460, target_map_name="Linnok Courtyard")
    #bot.Move.XYAndDialog(-92, 9217, 0x815507)
    exec_fn = lambda: QuestLoop(341, -92, 9217, 0x815507, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - Journey of the Master")
    #bot.Dialogs.AtXY(-92, 9217, 0x815601)
    exec_fn = lambda: QuestLoop(342, -92, 9217, 0x815601)
    bot.States.AddCustomState(exec_fn, "Accept - The Road Less Traveled")
    #bot.Move.XYAndDialog(538, 10125, 0x80000B)
    exec_fn = lambda: QuestLoop(342, 538, 10125, 0x80000B, mode="step")
    bot.States.AddCustomState(exec_fn, "Step 1 - The Road Less Traveled")
    bot.Wait.ForMapToChange(target_map_id=313)
    #bot.Move.XYAndDialog(1254, 10875, 0x815604)
    exec_fn = lambda: QuestLoop(342, 1254, 10875, 0x815604, mode="step")
    bot.States.AddCustomState(exec_fn, "Step 2 - The Road Less Traveled")
    bot.Move.XYAndExitMap(16600, 13150, target_map_name="Seitung Harbor")
    bot.Move.XY(16852, 12812)
    #bot.Move.XYAndDialog(16435, 12047, 0x815607)
    exec_fn = lambda: QuestLoop(342, 16435, 12047, 0x815607, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - The Road Less Traveled")
    
def Craft_Seitung_Armor(bot: Botting):
    bot.States.AddHeader("Craft Seitung armor")
    bot.Map.Travel(target_map_id=250) #Seitung Harbor
    bot.Move.XY(19823.66, 9547.78)
    bot.Move.XYAndInteractNPC(20508.00, 9497.00)
    exec_fn = lambda: CraftArmor(bot)
    bot.States.AddCustomState(exec_fn, "Craft Armor")
    
def To_Zen_Daijun(bot: Botting):
    bot.States.AddHeader("To Zen Daijun")
    PrepareForBattle(bot)
    bot.Move.XY(18000, 11650)
    bot.Move.XY(19000, 13000)
    bot.Move.XYAndExitMap(16777, 17540, target_map_name="Jaya Bluffs")
    bot.Move.XYAndExitMap(23616, 1587, target_map_name="Haiju Lagoon")
    bot.Move.XYAndDialog(16489, -22213, 0x80000B)
    bot.Wait.ForTime(7000)
    bot.Wait.ForMapLoad(target_map_id=213) #Zen Daijun

def Complete_Skills_Training(bot: Botting) -> None:
    bot.States.AddHeader("Complete Skills Training")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_name="Shing Jea Monastery")
    bot.Move.XYAndDialog(-8790.00, 10366.00, 0x84)
    bot.Wait.ForTime(3000)
    bot.Player.BuySkill(61)
    
def _register_spirit_rift_watcher():
    bot.config.FSM.AddManagedCoroutine("SpiritRiftWatcher", _zen_daijun_interrupt_loop())
    yield

def _zen_daijun_interrupt_loop():
    """Poll each tick for Spirit Rift casts (ID 910) and interrupt with unlocked mesmer skills."""
    SPIRIT_RIFT_ID = 910
    INTERRUPT_SKILLS = [57, 25, 860]  # Cry of Pain, Power Drain, Signet of Disruption
    cooldown = 0

    while Map.GetMapID() == 213:
        if cooldown > 0:
            cooldown -= 1
            yield
            continue

        for enemy_id in AgentArray.GetEnemyArray():
            if Agent.GetCastingSkillID(enemy_id) == SPIRIT_RIFT_ID:
                for skill_id in INTERRUPT_SKILLS:
                    slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)
                    if slot > 0:
                        Player.ChangeTarget(enemy_id)
                        GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=enemy_id)
                        cooldown = 30  # ~1 s before scanning again
                        break
                break
        yield

def Zen_Daijun_Mission(bot:Botting):
    bot.States.AddHeader("Zen Daijun Mission")
    bot.Map.Travel(target_map_id=213)
    PrepareForBattle(bot)
    bot.Map.EnterChallenge(6000, target_map_id=213) #Zen Daijun
    bot.Wait.ForMapToChange(target_map_id=213)
    bot.States.AddCustomState(_register_spirit_rift_watcher, "Start Spirit Rift Watcher")
    #ConfigureAggressiveEnv(bot)
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

def Destroy_Starter_Armor_And_Useless_Items(bot: Botting):
    bot.States.AddHeader("Destroy starter armor and useless items")
    bot.States.AddCustomState(destroy_starter_armor_and_useless_items, "Destroy starter armor and useless items")

def To_Marketplace(bot: Botting):
    bot.States.AddHeader("To Marketplace")
    bot.Map.Travel(target_map_id=250) #Seitung Harbor
    #bot.Move.XYAndDialog(16927, 9004, 0x815D01) #A Master's Burden pt. 1
    exec_fn = lambda: QuestLoop(349, 16927, 9004, 0x815D01)
    bot.States.AddCustomState(exec_fn, "Accept - A Master's Burden")
    #bot.Dialogs.AtXY(16927, 9004, 0x84)
    exec_fn = lambda: QuestLoop(349, 16927, 9004, 0x84, mode="step")
    bot.States.AddCustomState(exec_fn, "Step 1 - A Master's Burden")
    bot.Wait.ForMapLoad(target_map_name="Kaineng Docks")
    #bot.Move.XYAndDialog(9955, 20033, 0x815D04) #A Master's Burden pt. 2
    exec_fn = lambda: QuestLoop(349, 9955, 20033, 0x815D04, mode="step")
    bot.States.AddCustomState(exec_fn, "Step 2 - A Master's Burden")
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
    bot.Items.WithdrawGold(20000)
    bot.Move.XYAndInteractNPC(1592.00, -796.00)  # Common material merchant
    exec_fn_common = lambda: BuyMaxArmorMaterials("common")
    bot.States.AddCustomState(exec_fn_common, "Buy Common Materials")
    bot.Wait.ForTime(1500)  # Wait for common material purchases to complete
    # Buy rare materials (steel ingot, linen, or damask)
    if _get_max_armor_data()["buy_rare"]:
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

def _ensure_bonus_bow(bot: Botting):
    """Runtime check: craft the AB shortbow only if not already owned."""
    if BotSettings.CUSTOM_BOW_ID != 0 or Routines.Checks.Inventory.IsModelInInventory(BotSettings.CRAFTED_BOW_ID)or Routines.Checks.Inventory.IsModelEquipped(BotSettings.CRAFTED_BOW_ID):
        yield
        return
    if Map.GetMapID() != 194:
        Map.Travel(194)
        yield from Routines.Yield.Map.WaitforMapLoad(194, timeout=30000)
    yield from bot.Move._coro_xy(1592.00, -796.00)
    yield from Routines.Yield.Items.WithdrawGold(20000)
    yield from bot.Move._coro_xy_and_interact_npc(1592.00, -796.00)  # Common material merchant
    yield from Routines.Yield.wait(1000)
    yield from BuyLongbowMaterials()
    yield from bot.Move._coro_xy_and_interact_npc(-1387.00, -3910.00)  # Weapon crafter
    yield from Routines.Yield.wait(1000)
    yield from DoCraftLongbow(bot)
    yield

def Destroy_Monastery_Armor(bot: Botting):
    bot.States.AddHeader("Destroy old armor")
    bot.States.AddCustomState(destroy_monastery_armor, "Destroy Seitung Armor")

def Destroy_Seitung_Armor(bot: Botting):
    bot.States.AddHeader("Destroy old armor")
    bot.States.AddCustomState(destroy_seitung_armor, "Destroy Seitung Armor")

def The_Search_For_A_Cure(bot: Botting) -> None:
    bot.States.AddHeader("Quest: The Search For A Cure")
    bot.Map.Travel(194)
    #bot.Move.XYAndDialog(3772.00, -961.00, 0x815001)
    exec_fn = lambda: QuestLoop(336, 3772.00, -961.00, 0x815001)
    bot.States.AddCustomState(exec_fn, "Accept - The Search for a Cure")
    #bot.Move.XYAndDialog(1784.00, 991.00, 0x815004)
    exec_fn = lambda: QuestLoop(336, 1784.00, 991.00, 0x815004, mode="step")
    bot.States.AddCustomState(exec_fn, "Step 1 - The Search for a Cure")
    bot.Map.Travel(target_map_name="The Marketplace")
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(11430.00, 15200.00, target_map_name="Wajjun Bazaar")
    bot.Items.AddModelToLootWhitelist(6496)
    bot.Move.XY(10350.00, 14100.00)
    bot.Move.XY(8300.00, 14100.00)
    bot.Items.LootItems()
    bot.Wait.ForTime(5000)
    bot.Map.Travel(194)
    #bot.Move.XYAndDialog(1784.00, 991.00, 0x815007)
    exec_fn = lambda: QuestLoop(336, 1784.00, 991.00, 0x815007, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - The Search for a Cure")

def A_Masters_Burden(bot: Botting) -> None:
    bot.States.AddHeader("Quest: A Master's Burden")
    bot.Map.Travel(194)
    #bot.Move.XYAndDialog(1784.00, 991.00, 0x815101)
    exec_fn = lambda: QuestLoop(337, 1784.00, 991.00, 0x815101)
    bot.States.AddCustomState(exec_fn, "Accept - Seek out Brother Tosai")
    exec_fn = lambda: bot.Quest.SetActiveQuest(349)
    bot.States.AddCustomState(exec_fn, "Set Active - A Master's Burden")
    bot.Map.Travel(target_map_name="The Marketplace")
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(11430.00, 15200.00, target_map_name="Wajjun Bazaar")
    bot.Move.XY(10033.88, 13838.59)
    bot.Move.XY(11637.23, 11837.92)
    bot.Move.XY(10007.72, 10951.80)
    bot.Move.XY(8200.78, 12134.04)
    bot.Move.XY(8133.31, 7629.99)
    bot.Move.XY(5329.09, 7626.73)
    bot.Move.XY(4145.20, 6584.09)
    bot.Move.XY(-1663.82, 7113.72)
    #bot.Move.XYAndDialog(-1893.00, 6922.00, 0x815D04)
    exec_fn = lambda: QuestLoop(349, -1893.00, 6922.00, 0x815D04, mode="step", quest_npc=3171)
    bot.States.AddCustomState(exec_fn, "Step 3 - A Master's Burden")
    bot.Move.XY(4207.15, 6226.59)
    bot.Move.XY(4944.20, 3398.03)
    bot.Move.XY(4401.08, 618.24)
    bot.Move.XY(5802.95, -2295.56)
    bot.Move.XY(4671.93, -5007.46)
    bot.Move.XY(10774.00, -6636.00)
    #bot.Move.XYAndDialog(10774.00, -6636.00, 0x815D04)
    exec_fn = lambda: QuestLoop(349, 10774.00, -6636.00, 0x815D04, mode="step", quest_npc=3307)
    bot.States.AddCustomState(exec_fn, "Step 4 - A Master's Burden")
    bot.Map.Travel(target_map_name="The Marketplace")
    bot.Move.XY(12250, 18236)
    bot.Move.XY(10343, 20329)
    bot.Wait.ForMapLoad(target_map_id=302)
    #bot.Move.XYAndDialog(9950.00, 20033.00, 0x815D07)
    exec_fn = lambda: QuestLoop(349, 9950.00, 20033.00, 0x815D07, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - A Master's Burden")
    exec_fn = lambda: bot.Quest.SetActiveQuest(337)
    bot.States.AddCustomState(exec_fn, "Set Active - Seek Out Brother Tosai")
    exec_fn = lambda: bot.Quest.AbandonQuest(337)
    bot.States.AddCustomState(exec_fn, "Abandon - Seek Out Brother Tosai")

def Unlock_Mox(bot: Botting):
    bot.States.AddHeader("Unlock Mox")
    bot.Map.Travel(target_map_id=194)
    bot.Move.XYAndExitMap(3243, -4911, target_map_name="Bukdek Byway")
    bot.Move.XYAndDialog(-5803.48, 18951.70, 0x85)  # Unlock Mox
    bot.Wait.ForTime(1000)

def To_Boreal_Station(bot: Botting):
    bot.States.AddHeader("To Boreal Station")
    bot.Map.Travel(target_map_id=194)
    bot.Move.XY(3444.90, -1728.31)
    #bot.Move.XYAndDialog(3747.00, -2174.00, 0x833501)    
    exec_fn = lambda: QuestLoop(821, 3747.00, -2174.00, 0x833501)
    bot.States.AddCustomState(exec_fn, "Accept - I Feel the Earth Move Under Cantha's Feet")
    bot.Move.XY(3444.90, -1728.31)
    PrepareForBattle(bot)
    def _disable_dead_behind():
        bot.Events.OnPartyMemberDeadBehindCallback(lambda: None)
        yield
    bot.States.AddCustomState(_disable_dead_behind, "Disable DeadBehind Callback")
    bot.Move.XYAndExitMap(3243, -4911, target_map_name="Bukdek Byway")
    #bot.Move.XYAndDialog(-10103.00, 16493.00, 0x84)
    exec_fn = lambda: QuestLoop(821, -10103.00, 16493.00, 0x84, mode="step")
    bot.States.AddCustomState(exec_fn, "Step - I Feel the Earth Move Under Cantha's Feet")
    bot.Wait.ForMapLoad(target_map_id=692)
    auto_path_list = [(16738.77, 3046.05), (13028.36, 6146.36), (10968.19, 9623.72),
                      (3918.55, 10383.79), (8435, 14378), (10134,16742)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForTime(3000)
    ConfigurePacifistEnv(bot)
    bot.Items.UseAllConsumables()
    auto_path_list = [(4523.25, 15448.03), (-43.80, 18365.45), (-10234.92, 16691.96),
                      (-17917.68, 18480.57), (-18775, 19097)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForTime(8000)
    bot.Wait.ForMapLoad(target_map_id=675)
    def _enable_dead_behind():
        bot.Events.OnPartyMemberDeadBehindCallback(lambda: bot.Templates.Routines.OnPartyMemberDeathBehind())
        yield
    bot.States.AddCustomState(_enable_dead_behind, "Enable DeadBehind Callback")

def To_Eye_of_the_North(bot: Botting):
    bot.States.AddHeader("To Eye of the North")
    bot.Map.Travel(target_map_id=675) #Boreal Station
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(4684, -27869, target_map_name="Ice Cliff Chasms")
    bot.Move.XY(3579.07, -22007.27)
    bot.Wait.ForTime(15000)
    #bot.Dialogs.AtXY(3537.00, -21937.00, 0x839104)
    exec_fn = lambda: QuestLoop(913, 0, 0, 0x839104, mode="step", quest_npc=6034)
    bot.States.AddCustomState(exec_fn, "Step 1 - Against the Destroyers")
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
    #bot.Dialogs.WithModel(6021, 0x800001) # Eotn_pool_cinematic. Model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(913, 0, 0, 0x800001, mode="step", quest_npc=6021)
    bot.States.AddCustomState(exec_fn, "Step 2 - Against the Destroyers")
    bot.Wait.ForTime(1000)
    #bot.Dialogs.WithModel(5959, 0x633) # Eotn_pool_cinematic. Model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(913, 0, 0, 0x633, mode="step", quest_npc=5959)
    bot.States.AddCustomState(exec_fn, "Step 3 - Against the Destroyers")
    bot.Wait.ForTime(1000)
    bot.Wait.ForMapToChange(target_map_id=646)
    bot.Dialogs.WithModel(6021, 0x89) # Gwen dialog. Tapestry
    bot.Wait.ForTime(1000)
    #bot.Dialogs.WithModel(6021, 0x831904) # Gwen dialog. Model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(793, 0, 0, 0x831904, mode="step", quest_npc=6021)
    bot.States.AddCustomState(exec_fn, "Step 1 - The Missing Vanguard")
    bot.Dialogs.WithModel(6021, 0x0000008A) # Gwen dialog to obtain Keiran's bow. Model id updated 20.12.2025 GW Reforged
    #bot.Move.XYAndDialog(-6133.41, 5717.30, 0x838904) # Ogden dialog. Model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(905, 0, 0, 0x838904, mode="step", quest_npc=5983)
    bot.States.AddCustomState(exec_fn, "Step 1 - Northern Allies")
    #bot.Move.XYAndDialog(-5626.80, 6259.57, 0x839304) # Vekk dialog. Model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(915, 0, 0, 0x839304, mode="step", quest_npc=5964)
    bot.States.AddCustomState(exec_fn, "Step 1 - The Knowledgeable Asura")
    bot.Items.Equip(35829) #Keiran's bow
    bot.Map.Travel(target_map_id=642)

# Re-entry step when the AB farm run fails (re-equips bow, enters quest from HOM, waits for map)
_FARM_RESTART_STEP = "[H]Prepare for Quest (Farm)_34"
_AB_MAP_ID = 849

def _handle_bonus_bow(bot: Botting):
    bonus_bow_id = BotSettings.CRAFTED_BOW_ID

    if BotSettings.CUSTOM_BOW_ID != 0:
        bonus_bow_id = BotSettings.CUSTOM_BOW_ID
    has_bonus_bow = Routines.Checks.Inventory.IsModelInInventoryOrBank(bonus_bow_id)
    if has_bonus_bow:
        if not Routines.Checks.Inventory.IsModelInInventory(bonus_bow_id):
            yield from Routines.Yield.Items.WithdrawItems(bonus_bow_id, 1)
        yield from bot.helpers.Items._equip(bonus_bow_id)

def Farm_Until_Level_20(bot: Botting):
    """Farm Auspicious Beginnings until level 20 using KeiranThackerayEOTN build (solo, no heroes)."""
    FARM_PREPARE_STEP = "[H]Prepare for Quest (Farm)_33"
    NEXT_STEP_AFTER_FARM = "[H]Attribute points quest n. 2_35"
    EOTN_MAP_ID      = 642
    HOM_MAP_ID       = 646
    AB_MAP_ID        = 849

    # ── Header _32: loop entry / early exit check ──────────────────────────
    bot.States.AddHeader("Farm Until Level 20")

    def _level_check_entry():
        level = Player.GetLevel()
        ConsoleLog("FarmUntil20", f"[Farm] Entry level check: level={level}", Py4GW.Console.MessageType.Info)
        if level >= 20:
            fsm = bot.config.FSM
            target_step = _resolve_waypoint_state_name(fsm, NEXT_STEP_AFTER_FARM)
            if not target_step:
                ConsoleLog("FarmUntil20", f"[Farm] Target state not found: {NEXT_STEP_AFTER_FARM}", Py4GW.Console.MessageType.Error)
                yield
                return
            fsm.pause()
            yield
            fsm.jump_to_state_by_name(target_step)
            yield
            fsm.resume()
            yield
        # Keep coroutine semantics even when level < 20.
        yield

    bot.States.AddCustomState(_level_check_entry, "Level Check (Farm Entry)")
    bot.States.AddCustomState(lambda: _ensure_bonus_bow(bot), "Ensure Bonus Bow (Farm)")

    # Travel EotN → HOM (solo, no heroes)
    bot.Map.Travel(target_map_id=EOTN_MAP_ID)
    bot.Party.LeaveParty()
    bot.Move.XYAndExitMap(-4873.00, 5284.00, target_map_id=HOM_MAP_ID)

    # ── Header _33: prepare for quest ─────────────────────────────────────
    bot.States.AddHeader("Prepare for Quest (Farm)")
    bot.Wait.ForMapLoad(target_map_id=HOM_MAP_ID)

    def _equip_keirans_bow():
        if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(ModelID.Keirans_Bow.value):
            yield from bot.Move._coro_xy_and_dialog(-6583.00, 6672.00, dialog_id=0x0000008A)
        if not Routines.Checks.Inventory.IsModelEquipped(ModelID.Keirans_Bow.value):
            yield from bot.helpers.Items._equip(ModelID.Keirans_Bow.value)

    bot.States.AddCustomState(_equip_keirans_bow, "Equip Keiran's Bow (Farm)")
    bot.Move.XYAndDialog(-6662.00, 6584.00, 0x63F)   # enter quest via HOM pool
    bot.Wait.ForMapLoad(target_map_id=AB_MAP_ID)

    # ── Header _34: run the quest ─────────────────────────────────────────
    bot.States.AddHeader("Run Quest (Farm)")

    def _setup_keiran_combat():
        bot.OverrideBuild(KeiranThackerayEOTN(fsm=bot.config.FSM))
        bot.config.reset_pause_on_danger_fn(aggro_area=Range.Longbow)
        bot.Properties.ApplyNow("pause_on_danger", "active", True)
        bot.Properties.ApplyNow("halt_on_death",   "active", False)
        bot.Properties.ApplyNow("auto_combat",     "active", True)
        bot.Properties.ApplyNow("auto_loot",       "active", True)
        bot.Properties.ApplyNow("imp",             "active", False)
        yield

    exec_fn = lambda: _load_navmesh_object(bot)
    bot.States.AddCustomState(exec_fn, "Navmesh Init")
    bot.States.AddCustomState(_setup_keiran_combat, "Setup Keiran Combat (Farm)")

    # Quest path (from AuspiciousBeginnings.py)
    bot.Move.XY(11864.74, -4899.19)
    bot.States.AddCustomState(lambda: _handle_bonus_bow(bot), "HandleBonusBow")
    bot.Wait.UntilOnCombat(Range.Spirit)

    bot.Move.XY(10165.07, -6181.43, step_name="First Spawn")

    bot.Move.XY(8270,-9010)
    bot.Move.XY(4245,-7412)
    bot.Move.XY(2025,-10726)
    bot.Move.XY(-1822,-11230)
    bot.Move.XY(-3006,-8921)
    bot.Move.XY(-4190,-10460)
    bot.Move.XY(-5640,-10371)
    bot.Move.XY(-8748,-8329)
    bot.Move.XY(-12122,-7530)
    bot.Move.XY(-15170,-8951)
    bot.Wait.ForMapLoad(target_map_id=HOM_MAP_ID)

    def _disable_farm_combat():
        bot.Properties.ApplyNow("pause_on_danger", "active", False)
        bot.Properties.ApplyNow("auto_combat",     "active", False)
        yield

    bot.States.AddCustomState(_disable_farm_combat, "Disable Farm Combat")

    def _level_check_and_loop():
        level = Player.GetLevel()
        ConsoleLog("FarmUntil20", f"[Farm] End-of-run level check: level={level}", Py4GW.Console.MessageType.Info)
        if level < 20:
            fsm = bot.config.FSM
            target_step = _resolve_waypoint_state_name(fsm, FARM_PREPARE_STEP)
            if not target_step:
                ConsoleLog("FarmUntil20", f"[Farm] Target state not found: {FARM_PREPARE_STEP}", Py4GW.Console.MessageType.Error)
                yield
                return
            fsm.pause()
            yield
            fsm.jump_to_state_by_name(target_step)
            yield
            fsm.resume()
            yield
        # Keep coroutine semantics even when level >= 20.
        yield

    bot.States.AddCustomState(_level_check_and_loop, "Level Check and Loop (Farm)")

def Attribute_Points_Quest_2(bot: Botting):
    def enable_combat_and_wait(ms:int):
        global bot
        bot.Properties.Enable("auto_combat")
        bot.Wait.ForTime(ms)
        bot.Properties.Disable("auto_combat")
 
    bot.States.AddHeader("Attribute points quest n. 2")

    def _cleanup_farm_settings():
        """Clear Keiran's build override and reset farm-specific properties."""
        bot.OverrideBuild(AutoCombat())
        bot.config.reset_pause_on_danger_fn(aggro_area=Range.Earshot)
        bot.Properties.ApplyNow("halt_on_death",   "active", False)
        bot.Properties.ApplyNow("pause_on_danger", "active", False)
        bot.Properties.ApplyNow("auto_loot",       "active", False)
        bot.Properties.ApplyNow("imp",             "active", False)
        yield

    bot.States.AddCustomState(_cleanup_farm_settings, "Cleanup Farm Settings")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_name="Seitung Harbor")
    auto_path_list = [(16602.23, 11612.10), (16886.80, 9577.24), (16940.28, 9860.90), 
                      (19243.22, 9093.26), (19840.55, 7956.64)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Interact.WithGadgetAtXY(19642.00, 7386.00)
    bot.Wait.ForTime(5000)
    #bot.Dialogs.WithModel(4009,0x815C01) #Zunraa model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(348, 0, 0, 0x815C01, quest_npc=4009)
    bot.States.AddCustomState(exec_fn, "Accept - An Unwelcome Guest")
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    #bot.Party.AddHenchmanList([1, 5])
    bot.Party.AddHenchmanList([5])
    bot.Move.XYAndDialog(20350.00, 9087.00, 0x80000B)
    bot.Wait.ForMapLoad(target_map_id=246)  #Zen Daijun
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
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
    exec_fn = lambda: QuestLoop(348, 0, 0, 0x815C01, mode="complete", quest_npc=4009)
    bot.States.AddCustomState(exec_fn, "Accept - An Unwelcome Guest")

def To_Gunnars_Hold(bot: Botting):
    bot.States.AddHeader("To Gunnar's Hold")
    bot.Map.Travel(target_map_id=642)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    bot.Party.AddHenchmanList([4, 5, 6])
    path = [(-1814.0, 2917.0), (-964.0, 2270.0), (-115.0, 1677.0), (718.0, 1060.0), 
            (1522.0, 464.0)]
    bot.Move.FollowPath(path)
    bot.Wait.ForMapLoad(target_map_id=499)
    ConfigureAggressiveEnv(bot)
    jora_id   = Routines.Agents.GetAgentIDByModelID(6034)
    if jora_id != 0:
        #bot.Move.XYAndDialog(2825, -481, 0x832801)
        exec_fn = lambda: QuestLoop(808, 2825, -481, 0x832801)
        bot.States.AddCustomState(exec_fn, "Accept - Northern Allies -  Tracking the Nornbear")
    path = [(2548.84, 7266.08),
            (1233.76, 13803.42),
            (978.88, 21837.26),
            (-4031.0, 27872.0),]
    bot.Move.FollowAutoPath(path)
    bot.Wait.ForMapLoad(target_map_id=548)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(14546.0, -6043.0)
    bot.Move.XYAndExitMap(15578, -6548, target_map_id=644)
    bot.Wait.ForMapLoad(target_map_id=644)

def Unlock_Kilroy_Stonekin(bot: Botting):
    bot.States.AddHeader("Unlock Kilroy Stonekin")
    bot.States.AddManagedCoroutine("OnDeath_OPD", lambda: OnDeathKillroy(bot))
    bot.Templates.Aggressive(enable_imp=False)
    bot.Map.Travel(target_map_id=644)
    #bot.Move.XYAndDialog(17341.00, -4796.00, 0x835A01)
    exec_fn = lambda: QuestLoop(858, 17341.00, -4796.00, 0x835A01)
    bot.States.AddCustomState(exec_fn, "Accept - Punch the Clown")
    #bot.Dialogs.AtXY(17341.00, -4796.00, 0x84)
    exec_fn = lambda: QuestLoop(858, 17341.00, -4796.00, 0x84, mode="step")
    bot.States.AddCustomState(exec_fn, "Step 1 - Punch the Clown")
    bot.Wait.ForMapLoad(target_map_id=703)
    bot.Items.Equip(24897) #Brass knuckles
    bot.Wait.ForTime(3000)
    bot.Move.XY(19290.50, -11552.23)
    bot.Wait.UntilOnOutpost()
    #bot.Move.XYAndDialog(17341.00, -4796.00, 0x835A07)
    exec_fn = lambda: QuestLoop(858, 17341.00, -4796.00, 0x835A07, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - Punch the Clown")
    bot.UI.CancelSkillRewardWindow()
    #bot.Dialogs.AtXY(17341.00, -4796.00, 0x84)
    bot.States.RemoveManagedCoroutine("OnDeath_OPD")
    bot.Items.Equip(35829) #Keiran's bow

def OnDeathKillroy(bot: "Botting"):
    import PySkillbar
    skillbar = PySkillbar.Skillbar()
    slot = 8 # slot 8 is the default "revive" skill
    while True:
        if not Routines.Checks.Map.MapValid():
            yield from Routines.Yield.wait(1000)
            continue
        
        energy = Agent.GetEnergy(Player.GetAgentID())
        max_energy = Agent.GetMaxEnergy(Player.GetAgentID())
        if max_energy >= 80: #we can go much higher but were dying too much, not worth the time
            bot.config.FSM.pause()
            yield from bot.Map._coro_travel(644)
            bot.config.FSM.jump_to_state_by_name("[H]Killroy Stoneskin_1")
            bot.config.FSM.resume()
            yield from Routines.Yield.wait(1000)
            continue
        
        
        while energy < 0.9999:
            ActionQueueManager().AddAction("FAST", skillbar.UseSkillTargetless, slot)
            yield from Routines.Yield.wait(20)
            energy = Agent.GetEnergy(Player.GetAgentID())
            if energy >= 0.9999:
                ActionQueueManager().ResetAllQueues()

        yield from Routines.Yield.wait(500)

def To_Longeyes_Edge(bot: Botting):
    bot.States.AddHeader("To Longeye's Edge")
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary not in ("Assassin", "Mesmer"):
        return
    bot.Map.Travel(target_map_id=644)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    #bot.Party.AddHenchmanList([5, 6, 7, 9])
    bot.Party.AddHenchmanList([4, 5, 6])
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
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary not in ("Assassin", "Mesmer"):
        return
    bot.Map.Travel(target_map_id=650)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    #bot.Party.AddHenchmanList([5, 6, 7, 9])
    bot.Party.AddHenchmanList([4, 5, 6])
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
    #bot.Move.XYAndDialog(-1006.97, -817.63, 0x81DF01)
    exec_fn = lambda: QuestLoop(479, -1006.97, -817.63, 0x81DF01)
    bot.States.AddCustomState(exec_fn, "Accept - Chaos in Kryta")
    bot.Move.XYAndExitMap(-2439, 1732, target_map_id=290)
    auto_path_list =[(-2995.68, 2077.20), (-6938.10, 4286.61), (-6064.40, 5300.26),
                     (-2396.20, 5260.67), (-5031.77, 6001.52)]
    bot.Move.FollowAutoPath(auto_path_list)
    #bot.Move.XYAndDialog(-5626.17, 7017.33, 0x81DF04)
    bot.Move.XY(-5626.17, 7017.33)
    exec_fn = lambda: QuestLoop(479, 0, 0, 0x81DF04, mode="step", quest_npc=3267)
    bot.States.AddCustomState(exec_fn, "Step 1 - Chaos in Kryta")
    #bot.Move.XYAndDialog(-4661.13, 7479.86, 0x84)
    bot.Move.XY(-4661.13, 7479.86)
    exec_fn = lambda: QuestLoop(479, 0, 0, 0x84, mode="step", quest_npc=2020)
    bot.States.AddCustomState(exec_fn, "Step 2 - Chaos in Kryta")
    bot.Wait.ForMapToChange(target_map_name="Lion's Gate")
    bot.Move.XY(-1181, 1038)
    #bot.Dialogs.WithModel(2011, 0x85) #Model id updated 20.12.2025 GW Reforged
    exec_fn = lambda: QuestLoop(479, 0, 0, 0x85, mode="step", quest_npc=2011)
    bot.States.AddCustomState(exec_fn, "Step 3 - Chaos in Kryta")
    bot.Map.Travel(target_map_id=55)
    #bot.Move.XYAndDialog(328.00, 9594.00, 0x81DF07)
    exec_fn = lambda: QuestLoop(479, 328.00, 9594.00, 0x81DF07, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - Chaos in Kryta")

def To_Temple_of_The_Ages(bot: Botting):
    bot.States.AddHeader("To Temple of the Ages")
    bot.Map.Travel(target_map_id=55)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    #bot.Party.AddHenchmanList([1, 3])
    bot.Party.AddHenchmanList([1])
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
    #bot.Party.AddHenchmanList([1, 3])
    bot.Party.AddHenchmanList([1])
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
    bot.Party.AddHenchmanList([2, 12, 9])
    auto_path_list = [(3049.35, -2020.75), (2739.30, -3710.67), 
                      (-648.30, -3493.72), (-1661.91, -636.09)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Move.XYAndDialog(-1131.99, 818.35, 0x82D401)
    exec_fn = lambda: QuestLoop(724, -1131.99, 818.35, 0x82D401)
    bot.States.AddCustomState(exec_fn, "Accept - Sunspears in Cantha")
    bot.Move.XYAndExitMap(-2439, 1732, target_map_id=290)
    auto_path_list = [(-2995.68, 2077.20), (-6938.10, 4286.61), (-6064.40, 5300.26),
                     (-2396.20, 5260.67), (-5031.77, 6001.52)]
    bot.Move.FollowAutoPath(auto_path_list)
    #bot.Move.XYAndDialog(-5899.57, 7240.19, 0x82D404)
    bot.Move.XY(-5899.57, 7240.19)
    exec_fn = lambda: QuestLoop(724, 0, 0, 0x82D404, mode="step", quest_npc=4914, multi=0x87)
    bot.States.AddCustomState(exec_fn, "Step 1 - Sunspears in Cantha")
    #bot.Dialogs.WithModel(4914, 0x87)  # Model id updated 20.12.2025 GW Reforged
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
    exec_fn = lambda: QuestLoop(724, 0, 0, 0x84, mode="step", quest_npc=4914)
    bot.States.AddCustomState(exec_fn, "Step 2 - Sunspears in Cantha")
    #bot.Dialogs.WithModel(4914, 0x84)  # Model id updated 20.12.2025 GW Reforged
    bot.Wait.ForMapToChange(target_map_id=543)
    bot.Wait.ForTime(2000)
    exec_fn = lambda: QuestLoop(724, 0, 0, 0x82D407, mode="complete", quest_npc=4829)
    bot.States.AddCustomState(exec_fn, "Complete - Sunspears in Cantha")
    #bot.Dialogs.WithModel(4829, 0x82D407)  # Model id updated 20.12.2025 GW Reforged

def To_Consulate_Docks(bot: Botting):
    bot.States.AddHeader("To Consulate Docks")
    bot.Map.Travel(target_map_id=194)
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=449)
    bot.Move.XY(-8075.89, 14592.47)
    bot.Move.XY(-6743.29, 16663.21)
    bot.Move.XY(-5271.00, 16740.00)
    bot.Wait.ForMapLoad(target_map_id=429)
    #bot.Move.XYAndDialog(-4631.86, 16711.79, 0x85)
    exec_fn = lambda: QuestLoop(000, -4631.86, 16711.79, 0x85, mode="skip")
    bot.States.AddCustomState(exec_fn, "Unlock Docks")
    bot.Wait.ForMapToChange(target_map_id=493)

def Unlock_Olias(bot:Botting):
    bot.States.AddHeader("Unlock Olias")
    bot.Map.Travel(target_map_id=493)  # Consulate Docks
    #bot.Move.XYAndDialog(-2367.00, 16796.00, 0x830E01)
    exec_fn = lambda: QuestLoop(782, -2367.00, 16796.00, 0x830E01)
    bot.States.AddCustomState(exec_fn, "Accept - All for One and One for Justice")
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=55)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(StandardHeroTeam, name="Standard Hero Team")
    #bot.Party.AddHenchmanList([1, 3])
    bot.Party.AddHenchmanList([1])
    bot.Move.XY(1413.11, 9255.51)
    bot.Move.XY(242.96, 6130.82)
    #bot.Move.XYAndDialog(-1137.00, 2501.00, 0x84)
    exec_fn = lambda: QuestLoop(782, -1137.00, 2501.00, 0x84, mode="step")
    bot.States.AddCustomState(exec_fn, "Step 1 - All for One and One for Justice")
    bot.Wait.ForMapToChange(target_map_id=471)
    bot.Wait.ForTime(3000)
    #bot.Move.XYAndDialog(5117.00, 10515.00, 0x830E04)
    exec_fn = lambda: QuestLoop(782, 5117.00, 10515.00, 0x830E04, mode="step")
    bot.States.AddCustomState(exec_fn, "Step 2 - All for One and One for Justice")
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(8518.10, 9309.66)
    bot.Move.XY(8067.40, 5703.23)
    bot.Move.XY(5657.20, 4485.55)
    bot.Move.XY(4461.65, -710.88)
    bot.Move.XY(10750, 2100)
    bot.Wait.ForTime(20000)
    bot.Wait.ForMapToChange(target_map_id=55)
    bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=449)
    bot.Move.XY(-8149.02, 14900.65)
    #bot.Move.XYAndDialog(-6480.00, 16331.00, 0x830E07)
    exec_fn = lambda: QuestLoop(782, -6480.00, 16331.00, 0x830E07, mode="complete")
    bot.States.AddCustomState(exec_fn, "Complete - All for One and One for Justice")

def Unlock_Remaining_Secondary_Professions(bot: Botting):
    bot.States.AddHeader("Unlock remaining secondary professions")
    bot.Map.Travel(target_map_id=248)  # GTOB
    bot.Items.WithdrawGold(5000)
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
    def __init__(self, label: str, MapID: int, step_name: str, section: str = ""):
        self.step_name = step_name
        self.MapID = MapID
        self.label = label
        self.section = section

def _resolve_waypoint_state_name(fsm, configured_name: str) -> str:
    """Resolve a waypoint state name even if header index suffixes changed."""
    if not configured_name:
        return ""
    if fsm.has_state(configured_name):
        return configured_name
    if "_" not in configured_name:
        return ""
    # Convert "[H]Header Text_32" -> prefix "[H]Header Text_"
    prefix = configured_name.rsplit("_", 1)[0] + "_"
    for s in fsm.states:
        if s.name.startswith(prefix):
            return s.name
    return ""

WAYPOINTS: dict[int, WaypointData] = {
    # step_num : WaypointData(label, MapID, step_name, section)
    # step_name format: [H]<AddHeader text>_<1-based AddHeader call index in the routine>
    # ── Shing Jea Island ──────────────────────────────────────────────────────
     1: WaypointData(label="Forming A Party",               MapID=242, step_name="[H]Quest: Forming A Party_2",              section="Shing Jea Island"),
     2: WaypointData(label="Unlock Secondary Profession",   MapID=242, step_name="[H]Unlock Secondary Profession_3"),
     3: WaypointData(label="Craft Weapon",                  MapID=242, step_name="[H]Craft weapon_5"),
     4: WaypointData(label="Craft Monastery Armor",         MapID=242, step_name="[H]Craft monastery armor_6"),
     5: WaypointData(label="Unlock Skills Trainer",         MapID=242, step_name="[H]Unlock Skills Trainer_10"),
     6: WaypointData(label="Minister Cho's Estate Mission", MapID=214, step_name="[H]Minister Cho's Estate mission_11"),
     7: WaypointData(label="Attribute Points Quest 1",      MapID=251, step_name="[H]Attribute points quest n. 1_12"),
     8: WaypointData(label="Quest: Warning the Tengu",      MapID=251, step_name="[H]Quest: Warning the Tengu_13"),
     9: WaypointData(label="Quest: The Road Less Traveled", MapID=242, step_name="[H]Quest: The Road Less Traveled_15"),
    10: WaypointData(label="Craft Seitung Armor",           MapID=250, step_name="[H]Craft Seitung armor_16"),
    11: WaypointData(label="To Zen Daijun",                 MapID=250, step_name="[H]To Zen Daijun_18"),
    12: WaypointData(label="Complete Skills Training",      MapID=242, step_name="[H]Complete Skills Training_19"),
    13: WaypointData(label="Zen Daijun Mission",            MapID=213, step_name="[H]Zen Daijun Mission_20"),
    # ── Factions Mainland ─────────────────────────────────────────────────────
    14: WaypointData(label="To Marketplace",                MapID=250, step_name="[H]To Marketplace_21",                    section="Factions Mainland"),
    15: WaypointData(label="Craft Max Armor",               MapID=194, step_name="[H]Craft max armor_23"),
    16: WaypointData(label="Quest: The Search For A Cure",  MapID=194, step_name="[H]Quest: The Search For A Cure_25"),
    17: WaypointData(label="Quest: A Master's Burden",      MapID=194, step_name="[H]Quest: A Master's Burden_26"),
    18: WaypointData(label="To Boreal Station",             MapID=194, step_name="[H]To Boreal Station_27"),
    # ── Eye of the North ──────────────────────────────────────────────────────
    19: WaypointData(label="To Eye of the North",           MapID=675, step_name="[H]To Eye of the North_28",               section="Eye of the North"),
    20: WaypointData(label="Unlock EotN Pool",              MapID=642, step_name="[H]Unlock Eye Of The North Pool_29"),
    21: WaypointData(label="To Gunnar's Hold",              MapID=642, step_name="[H]To Gunnar's Hold_30"),
    22: WaypointData(label="Unlock Kilroy Stonekin",        MapID=644, step_name="[H]Unlock Kilroy Stonekin_31"),
    23: WaypointData(label="Farm Until Level 20",           MapID=642, step_name="[H]Farm Until Level 20_32"),
    24: WaypointData(label="Attribute Points Quest 2",      MapID=250, step_name="[H]Attribute points quest n. 2_35"),
    25: WaypointData(label="To Longeye's Edge",             MapID=644, step_name="[H]To Longeye's Edge_36"),
    26: WaypointData(label="Unlock Vaettir NPC",            MapID=650, step_name="[H]Unlock NPC for vaettir farm_37"),
    # ── Prophecies / NF / GToB ────────────────────────────────────────────────
    27: WaypointData(label="To Lion's Arch",                MapID=194, step_name="[H]To Lion's Arch_38",                    section="Prophecies / NF / GToB"),
    28: WaypointData(label="To Kamadan",                    MapID=194, step_name="[H]To Kamadan_39"),
    29: WaypointData(label="Unlock Olias",                  MapID=493, step_name="[H]Unlock Olias_41"),
    30: WaypointData(label="Unlock Secondary Professions",  MapID=449, step_name="[H]Unlock remaining secondary professions_42"),
    31: WaypointData(label="Unlock Mercenary Heroes",       MapID=248, step_name="[H] Unlock Mercenary Heroes_43"),
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


#region Deprecated
# Functions kept for reference / potential future use but not active in the bot routine.

def AddHenchmenLA():
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

    # Add all henchmen quickly
    for henchman_id in henchmen_list:
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(henchman_id)
        ConsoleLog("addhenchman",f"Added Henchman: {henchman_id}", log=False)

    # Single wait for all henchmen to join
    yield from Routines.Yield.wait(1000)

def switchFilter():
    # Switch to profession sort
    Game.enqueue(lambda: UIManager.SendUIMessage(UIMessage.kPreferenceValueChanged,[18,2], False))
    Game.enqueue(lambda: UIManager.SendUIMessage(UIMessage.kPreferenceValueChanged,[17,4], False))
    yield from Routines.Yield.wait(500)
    return

def TrainSkills():
    """Train Cry of Pain, Power Drain, Signet of Disruption via UI (same off-child path as workspace)."""
    secondary_skills_grandparent = 1746895597
    secondary_skills_offset = [0, 0, 0, 5, 1]
    skills_to_train_frames = [
        UIManager.GetChildFrameID(secondary_skills_grandparent, secondary_skills_offset + [57, 0]),   # Cry of Pain
        UIManager.GetChildFrameID(secondary_skills_grandparent, secondary_skills_offset + [25, 0]),   # Power Drain
        UIManager.GetChildFrameID(secondary_skills_grandparent, secondary_skills_offset + [860, 0]),  # Signet of Disruption
    ]
    for skill_frame_id in skills_to_train_frames:
        Game.enqueue(lambda fid=skill_frame_id: UIManager.TestMouseClickAction(fid, 0, 0))
        yield from Routines.Yield.wait(200)
        Game.enqueue(lambda: UIManager.FrameClick(UIManager.GetFrameIDByHash(4162812990)))
        yield from Routines.Yield.wait(200)
    return

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

#endregion

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
    use_candy_apple = bot.Properties.Get("candy_apple", "active")
    bc_restock_qty = bot.Properties.Get("candy_apple", "restock_quantity")

    use_honeycomb = bot.Properties.Get("honeycomb", "active")
    hc_restock_qty = bot.Properties.Get("honeycomb", "restock_quantity")

    use_candy_apple = PyImGui.checkbox("Use Candy Apple", use_candy_apple)
    bc_restock_qty = PyImGui.input_int("Candy Apple Restock Quantity", bc_restock_qty)

    use_honeycomb = PyImGui.checkbox("Use Honeycomb", use_honeycomb)
    hc_restock_qty = PyImGui.input_int("Honeycomb Restock Quantity", hc_restock_qty)

    # War Supplies controls
    use_war_supplies = bot.Properties.Get("war_supplies", "active")
    ws_restock_qty = bot.Properties.Get("war_supplies", "restock_quantity")

    use_war_supplies = PyImGui.checkbox("Use War Supplies", use_war_supplies)
    ws_restock_qty = PyImGui.input_int("War Supplies Restock Quantity", ws_restock_qty)

    bot.Properties.ApplyNow("war_supplies", "active", use_war_supplies)
    bot.Properties.ApplyNow("war_supplies", "restock_quantity", ws_restock_qty)
    bot.Properties.ApplyNow("candy_apple", "active", use_candy_apple)
    bot.Properties.ApplyNow("candy_apple", "restock_quantity", bc_restock_qty)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "restock_quantity", hc_restock_qty)

    
bot.SetMainRoutine(create_bot_routine)
bot.UI.override_draw_texture(lambda: _draw_texture())
bot.UI.override_draw_config(lambda: _draw_settings(bot))
bot.UI.override_draw_help(lambda: _draw_readme())


def _draw_readme():
    import PyImGui

    PyImGui.text_colored("Before You Start", (100, 220, 100, 255))
    PyImGui.separator()
    PyImGui.text_colored("  Required:", (255, 200, 0, 255))
    PyImGui.text_wrapped("  - At least 40k stored in your Xunlai Storage chest.")
    PyImGui.text_wrapped("  - Highly recommended to have Apples and War supplies in your Xunlai Storage chest.")
    PyImGui.text_wrapped("  - Character must be level 1, freshly created in Factions.")
    PyImGui.text_wrapped("  - No other bots or automation scripts running at the same time.")
    PyImGui.text_wrapped("  - Start from Monastery Overlook (the default Factions starting map).")

    PyImGui.spacing()
    PyImGui.text_colored("What the Bot Does", (100, 220, 100, 255))
    PyImGui.separator()
    PyImGui.text_wrapped("Levels your character through Factions and Eye of the North.")
    PyImGui.text_wrapped("Along the way it will:")
    PyImGui.text_wrapped("  - Craft Monastery, Seitung, and Max (Kaineng Center) armor sets.")
    PyImGui.text_wrapped("  - Craft a starter weapon in Shing Jea Monastery.")
    PyImGui.text_wrapped("  - Unlock secondary professions, heroes, and key skills.")
    PyImGui.text_wrapped("  - Unlock the Kilroy Stonekin and Vaettir farming runs for fast XP.")
    PyImGui.text_wrapped("  - Unlock Olias hero and remaining secondary professions.")

    PyImGui.spacing()
    PyImGui.text_colored("Important Notes", (100, 220, 100, 255))
    PyImGui.separator()
    PyImGui.text_wrapped("  - Gold is managed automatically: the bot withdraws and deposits as needed.")
    PyImGui.text_wrapped("  - Consumables (Candy Apple, Honeycomb, War Supplies) are restocked each fight.")
    PyImGui.text_colored("  - Do not manually move the character or interact with the game while the bot is running.", (255, 100, 100, 255))

    PyImGui.spacing()
    PyImGui.text_colored("Restarting / Resuming", (100, 220, 100, 255))
    PyImGui.separator()
    PyImGui.text_wrapped("If the bot stops or errors out, you can resume from any step.")
    PyImGui.text_wrapped("Use the 'Direct Navigation' panel in the Main tab to travel to the correct map,")
    PyImGui.text_wrapped("then use 'Go to Step' to jump the FSM to the matching point in the routine.")

def configure():
    global bot
    bot.UI.draw_configure_window()
    
    
def _draw_direct_nav():
    if PyImGui.collapsing_header("Direct Navigation"):
        if PyImGui.button("Dump FSM Header States to Console"):
            for s in bot.config.FSM.states:
                if s.name.startswith("[H]"):
                    Py4GW.Console.Log(bot.config.bot_name, s.name, Py4GW.Console.MessageType.Info)
        current_section = ""
        for step_num, waypoint in WAYPOINTS.items():
            if waypoint.section and waypoint.section != current_section:
                current_section = waypoint.section
                PyImGui.spacing()
                PyImGui.text_colored(current_section, (180, 160, 80, 255))
                PyImGui.separator()

            if PyImGui.tree_node(f"{waypoint.label}##wp_{step_num}"):
                if PyImGui.button(f"Travel##travel_{step_num}"):
                    Map.Travel(waypoint.MapID)
                PyImGui.same_line(0,-1)
                if PyImGui.button(f"Go to Step##step_{step_num}"):
                    target_state = _resolve_waypoint_state_name(bot.config.FSM, waypoint.step_name)
                    if not target_state:
                        Py4GW.Console.Log(
                            bot.config.bot_name,
                            f"Waypoint state not found: {waypoint.step_name}",
                            Py4GW.Console.MessageType.Error,
                        )
                        PyImGui.tree_pop()
                        continue
                    bot.config.fsm_running = True
                    bot.config.FSM.reset()
                    bot.config.FSM.jump_to_state_by_name(target_state)
                PyImGui.tree_pop()


def main():
    global bot
    try:
        bot.Update()
        bot.UI.draw_window(additional_ui=_draw_direct_nav)

    except Exception as e:
        Py4GW.Console.Log(bot.config.bot_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def tooltip():
    PyImGui.set_next_window_size((600, 0))
    PyImGui.begin_tooltip()
    
    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.image(MODULE_ICON, (32, 32))
    PyImGui.same_line(0, 10)
    ImGui.push_font("Regular", 20)
    ImGui.text_aligned(MODULE_NAME, alignment=Alignment.MidLeft, color=title_color.color_tuple, height=32)
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    
    #ellaborate a better description 
    PyImGui.text_wrapped("This bot levels a Factions character from 1 to 20, completing key quests and unlocking important content along the way. It manages gold and consumables automatically, allowing you to sit back and watch your character grow.")
    PyImGui.spacing()
    
    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Crafts Monastery, Seitung, and Max armor sets.")
    PyImGui.bullet_text("Crafts a starter weapon in Shing Jea Monastery.")
    PyImGui.bullet_text("Unlocks secondary professions, heroes, and key skills.")
    PyImGui.bullet_text("Unlocks the Kilroy Stonekin and Vaettir farming runs for fast XP.")
    PyImGui.bullet_text("...")
    PyImGui.spacing()
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo and Wick aka Divinus")
    
    PyImGui.end_tooltip()
    
if __name__ == "__main__":
    main()

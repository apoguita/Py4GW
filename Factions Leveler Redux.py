from __future__ import annotations

import math
from typing import Callable



from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.enums_src.Item_enums import Bags
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.routines_src.Agents import Agents as RoutinesAgents
from Py4GWCoreLib.routines_src.Checks import Checks


from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.native_src.internals.types import PointOrPath
from Py4GWCoreLib.native_src.internals.types import PointPath


MODULE_NAME = "Botting Tree Template"
INI_PATH = "Widgets/Automation/Bots/Templates"
INI_FILENAME = "BottingTreeTemplate.ini"

initialized = False
ini_key = ""
botting_tree: BottingTree | None = None

exit_to_sunqua_coords = (-14961, 11453)
tsumei_village_path = [(18245.78, -9448.29), (-4842, -13267)]
tsumei_village_map_id = 249

panjian_peninsula_map_id = 235
kinya_province_map_id = 236

LEVELING_SKILLBAR_MAP: dict[str, list[tuple[int | None, str]]] = {
    "Warrior": [
        (3, "OQAREpQoKlrBAAaFACA"),
        (20, "OQUBIskDcdG0DaAKUECA"),
        (None, "OQUCErwSOw1ZQPoBoQRIA"),
    ],
    "Ranger": [
        (2, "OgATYDcklQx+GAAAAAAAbGA"),
        (3, "OgARkpA2+GAAAA0ezCA"),
        (20, "OgUBIskDcdG0DaAKUECA"),
        (None, "OgUCErwSOw1ZQPoBoQRIA"),
    ],
    "Monk": [
        (2, "OwAC0hLBKzIIBAAAAAEA"),
        (3, "OwAAAAAAAAAAAAAA"),
        (20, "OwUBIskDcdG0DaAKUECA"),
        (None, "OwUCErwSOw1ZQPoBoQRIA"),
    ],
    "Necromancer": [
        (3, "OABAAAAAAAAAAAAA"),
        (20, "OAVBIskDcdG0DaAKUECA"),
        (None, "OAVCErwSOw1ZQPoBoQRIA"),
    ],
    "Mesmer": [
        (3, "OQBAAAAAAAAAAAAA"),
        (20, "OQBBIskDcdG0DaAKUECA"),
        (None, "OQBCErwSOw1ZQPoBoQRIA"),
    ],
    "Elementalist": [
        (3, "OgBAAAAAAAAAAAAA"),
        (20, "OgVBIskDcdG0DaAKUECA"),
        (None, "OgVCErwSOw1ZQPoBoQRIA"),
    ],
    "Ritualist": [
        (3, "OACAAAAAAAAAAAAA"),
        (20, "OAWBIskDcdG0DaAKUECA"),
        (None, "OAWCErwSOw1ZQPoBoQRIA"),
    ],
    "Assassin": [
        (3, "OwBAAAAAAAAAAAAA"),
        (20, "OAWBIskDcdG0DaAKUECA"),
        (None, "OwVCErwSOw1ZQPoBoQRIA"),
    ],
}


#region helpers
def _trace_step(name: str, tree: BehaviorTree) -> BehaviorTree:
    #_trace_step("Prepare For Battle: Configure Aggressive", bot.Config.Aggressive(auto_loot=False)),
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=f"Trace<{name}>",
            children=[
                BT.LogMessage(f"BEGIN: {name}", module_name=MODULE_NAME, print_to_console=True, print_to_blackboard=False),
                BT.Node(tree),
                BT.LogMessage(f"OK: {name}", module_name=MODULE_NAME, print_to_console=True, print_to_blackboard=False),
            ],
        )
    )


def _get_henchmen_for_current_map() -> list[int]:
    party_size = Map.GetMaxPartySize()
    current_map_id = Map.GetMapID()

    if party_size <= 4:
        return [2, 5, 1]
    if current_map_id == Map.GetMapIDByName("Seitung Harbor"):
        return [2, 3, 1, 6, 5]
    if current_map_id == 213:
        return [2, 3, 1, 8, 5]
    if current_map_id == Map.GetMapIDByName("The Marketplace"):
        return [6, 9, 5, 1, 4, 7, 3]
    if Map.IsMapIDMatch(current_map_id, 194):
        return [2, 10, 4, 8, 7, 9, 12]
    if current_map_id == Map.GetMapIDByName("Boreal Station"):
        return [7, 9, 2, 3, 4, 6, 5]
    return [2, 3, 5, 6, 7, 9, 10]


def PrepareForBattle() -> BehaviorTree:
    bot = ensure_botting_tree()
    restock_candy_apple_qty = 0# 10
    restock_war_supplies_qty = 0# 10
    restock_honeycomb_qty = 0# 20
    
    restock_list = [
        (ModelID.Candy_Apple.value, restock_candy_apple_qty), 
        (ModelID.War_Supplies.value, restock_war_supplies_qty), 
        (ModelID.Honeycomb.value, restock_honeycomb_qty),
    ]
    return BT.Sequence(
            name="Prepare For Battle",
            children=[
                bot.Config.Aggressive(auto_loot=False),
                BT.LoadSkillbarFromMap(LEVELING_SKILLBAR_MAP),
                BT.LeaveParty(),
                BT.AddHenchmanList(_get_henchmen_for_current_map()),
                BT.RestockItemsFromList(restock_list,allow_missing=True,),
            ],
        )

#region routines
def Exit_Monastery_Overlook() -> BehaviorTree:
    coords_by_profession = { 
        "Warrior": (-7039.83, 7325.59),
        "Ranger": (-7714.79, 6727.62),
        "Monk": (-7092.22, 7497.88),
        "Necromancer": (-7101.96, 7125.17),
        "Mesmer": (-7351.34, 7584.09),
        "Elementalist": (-7892.99, 6928.65),
        "Assassin": (-7849.87, 6814.73),
        "Ritualist": (-7785.90, 7335.15),
    }
    starter_weapon_model_ids = {
        "Warrior": 2982,
        "Ranger": 477,
        "Monk": 2787,
    }

    def _move_to_profession_coords(node: BehaviorTree.Node) -> BehaviorTree:
        return BT.HandleAutoQuest(
            pos=node.blackboard["profession_coords"],
            buttons=[0, 0],
        )
        
    def _equip_starter_weapon_by_profession(node: BehaviorTree.Node) -> BehaviorTree:
        return BT.EquipItemByModelID(node.blackboard["starter_weapon_model_id"])

    return BT.Sequence(
            name="Exit Monastery Overlook",
            children=[
                BT.HandleAutoQuest(pos=(-7048,5817), buttons=[0, 0, 1, 0, 0]),
                BT.WaitForMapLoad(map_name="Shing Jea Monastery"),
                BT.GetValuesByProfession(
                    profession_values=coords_by_profession,
                    target_key="profession_coords",
                ),
                BehaviorTree.SubtreeNode(
                    name="MoveToProfessionCoords",
                    subtree_fn=_move_to_profession_coords,
                ),
                BT.GetValuesByProfession(
                    profession_values=starter_weapon_model_ids,
                    target_key="starter_weapon_model_id",
                ),
                BehaviorTree.SubtreeNode(
                    name="EquipWeaponByProfession",
                    subtree_fn=_equip_starter_weapon_by_profession,
                ),
            ],
        )
    
 
def Forming_A_Party() -> BehaviorTree:
    return BT.Sequence(
            name="Forming A Party",
            map_id_or_name="Shing Jea Monastery",
            children=[
                PrepareForBattle(),
                BT.HandleAutoQuest(pos=(-14063.00, 10044.00)),
                BT.MoveAndExitMap((-14961, 11453), target_map_name="Sunqua Vale"),
                BT.HandleAutoQuest(pos=(19673.00, -6982.00)),
            ],
        )
    
#region profession specific quests
def WarriorPrimaryStarterQuests() -> BehaviorTree:
    bot = ensure_botting_tree()
    return BT.Sequence(
            name="Warrior Primary Starter Quests",
            children=[
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(pos=[(17065.27, -7227.24),(15051.48, -1352.39),(11398.17, 7258.22)],
                                   buttons=[0, 0],),
                BT.EquipItemByModelID(26),
                bot.Config.Aggressive(),
                BT.ClearEnemiesInArea((11398.17, 7258.22), Range.Longbow.value),
                BT.HandleAutoQuest(pos=[(11398.17, 7258.22)]),
                BT.ClearEnemiesInArea((11398.17, 7258.22), Range.Spellcast.value),
                BT.Wait(1000),
                BT.HandleAutoQuest(pos=[(11398.17, 7258.22)], buttons=[0, 0],),
                BT.Travel(target_map_name="Shing Jea Monastery"),
                PrepareForBattle(),
                bot.Config.Pacifist(),
                BT.MoveAndExitMap(exit_to_sunqua_coords, target_map_name="Sunqua Vale"),
                BT.MoveAndExitMap(tsumei_village_path, target_map_id=tsumei_village_map_id),
                BT.MoveAndExitMap((-11659, -17174), target_map_id=panjian_peninsula_map_id),
                #track down Weng Gah
                BT.HandleAutoQuest(pos=[(6678.91, 6318.28)], buttons=[0,0]),
                BT.MoveAndKill((10727.69, 10571.04)),
                BT.HandleAutoQuest(pos=[(6678.91, 6318.28)], buttons=[0,0]),
            ],
        )

def RangerPrimaryStarterQuests() -> BehaviorTree:
    bot = ensure_botting_tree()
    rabbit_pt1_coords = (9583.81, -5396.87)
    rabbit_pt2_coords = (7113.02, -8898.87)
    rabbit_pt3_coords = [(6339.18, -10887.55), (4371.29, -12062.85), (2083.06, -11528.21)]
    
    return BT.Sequence(
            name="Ranger Primary Starter Quests",
            children=[
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(pos=[(17065.27, -7227.24),(5153.02, -4831.28)],
                                   buttons=[0, 0]),
                BT.HandleAutoQuest(pos=[(5153.02, -4831.28)]),
                bot.Config.Aggressive(),
                BT.MoveAndInteractWithGadget(rabbit_pt1_coords),
                BT.ClearEnemiesInArea(rabbit_pt1_coords, Range.Spellcast.value),
                BT.Wait(5000, emote="dance", announce_delay=True),
                BT.MoveAndKill(rabbit_pt2_coords, Range.Spirit.value),
                BT.MoveAndInteractWithGadget(rabbit_pt2_coords),
                BT.Wait(5000, emote="dance", announce_delay=True),
                BT.WaitUntilOnCombat(Range.Spellcast.value),
                BT.ClearEnemiesInArea(rabbit_pt2_coords, Range.Spellcast.value),
                BT.Wait(5000, emote="dance", announce_delay=True),
                BT.MoveAndKill(rabbit_pt3_coords, Range.Spellcast.value),
                BT.MoveAndInteractWithGadget(rabbit_pt3_coords[2]),
                BT.Wait(5000, emote="dance", announce_delay=True),
                BT.HandleAutoQuest(pos=None, use_npc_model_or_enc_str="\\x5CD9\\xA792\\xB5D7\\x67C6", buttons=[0, 0],require_quest_marker=True,),
                BT.MoveAndExitMap((-5178, -13791), target_map_id=tsumei_village_map_id),
                #track down zho
                BT.MoveAndExitMap((-4678, -12903), target_map_name="Sunqua Vale"),
                BT.MoveAndExitMap((-20746, 7473), target_map_id=kinya_province_map_id),
                BT.HandleAutoQuest(pos=(9760.99, 5168.66), buttons=[0, 0],),
                BT.HandleAutoQuest(pos=(9760.99, 5168.66)),
                BT.Move([(8664.65, 1558.53),(10120.81, 2450.65)]),
                BT.WaitUntilOnCombat(Range.Spellcast.value),
                BT.ClearEnemiesInArea((10120.81, 2450.65), Range.Spellcast.value),
                BT.HandleAutoQuest(pos=(8426.00, 1537.00), 
                                   use_npc_model_or_enc_str="\\x5CDF\\x8329\\xF25F\\x1B43", 
                                   buttons=[0, 0],
                                   require_quest_marker=True,),
            ],
        )
    
def MonkPrimaryStarterQuests() -> BehaviorTree:
    bot = ensure_botting_tree()

    return BT.Sequence(
            name="Monk Primary Starter Quests",
            children=[
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(pos=[(17065.27, -7227.24),(9445.05, 3657.00)],
                                   buttons=[0, 0]),
                BT.HandleAutoQuest(pos=[(9445.05, 3657.00)],),
                bot.Config.Aggressive(),
                BT.MoveAndKill((9969.57, 2771.42), Range.Spellcast.value),
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(pos=[(9445.05, 3657.00)],buttons=[0, 0]),
                BT.MoveAndExitMap((-5178, -13791), target_map_id=tsumei_village_map_id),
                PrepareForBattle(),
                BT.MoveAndExitMap((-4678, -12903), target_map_name="Sunqua Vale"),
                bot.Config.Aggressive(),
                BT.MoveAndExitMap((-20746, 7473), target_map_id=kinya_province_map_id),
                #track down brother pe wan
                BT.HandleAutoQuest((4726.45, -2728.68),buttons=[0, 0]),
                BT.MoveAndInteractWithGadget((6608.74, 4559.66)),
                BT.MoveAndInteractWithGadget((9602.88, 12303.18)),
                BT.HandleAutoQuest((4726.45, -2728.68),buttons=[0, 0]),
            ],
        )

def Profession_Specific_Quests() -> BehaviorTree:
    return BT.GetNodeByProfession(
        WarriorNode=WarriorPrimaryStarterQuests(),
        RangerNode=RangerPrimaryStarterQuests(),
        MonkNode=MonkPrimaryStarterQuests(),
    )
    
def An_Audience_WithMasterTogo() -> BehaviorTree:
    bot = ensure_botting_tree()
    
    secondary_button_for_profession = {
        "Warrior": 5,
        "Ranger": 1,
        "Monk": 5,
    }

    def _profession_button_dialog(node: BehaviorTree.Node) -> BehaviorTree:
        return BT.HandleAutoQuest(
            pos=[(-159, 9174), (-92, 9217)],
            buttons=[node.blackboard["audience_with_master_togo_button"], 0],
        )
    
    return BT.Sequence(
            name="An Audience With Master Togo",
            map_id_or_name="Shing Jea Monastery",
            children=[
                bot.Config.Pacifist(),
                BT.MoveAndExitMap((-3480, 9460), target_map_name="Linnok Courtyard",),
                BT.HandleAutoQuest(pos=[(-159, 9174), (-92, 9217)]),
                BT.GetValuesByProfession(
                    profession_values=secondary_button_for_profession,
                    target_key="audience_with_master_togo_button",
                ),
                BehaviorTree.SubtreeNode(
                    name="AudienceWithMasterTogoProfessionButton",
                    subtree_fn=_profession_button_dialog,
                ),
                BT.MoveAndExitMap((-3762, 9471),target_map_name="Shing Jea Monastery",),
            ],
        )
     
    

def Unlock_Xunlai_Storage() -> BehaviorTree:
    path_to_xunlai = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3825.09, 10386.81),]
    xunlai_agent_coords = (-3825.09, 10386.81)
    
    return BT.Sequence(
            name="Unlock Xunlai Storage",
            map_id_or_name="Shing Jea Monastery",
            children=[
                BT.MoveAndDialog(path_to_xunlai, 0x84),
                BT.DialogAtXY(xunlai_agent_coords, 0x800001),
                BT.DialogAtXY(xunlai_agent_coords, 0x800002),
            ],
        )

#region old code

MONASTERY_ARMOR_DATA: dict[str, list[tuple[int, list[int], list[int]]]] = {
    "Warrior": [
        (10156, [ModelID.Bolt_Of_Cloth.value], [3]),
        (10158, [ModelID.Bolt_Of_Cloth.value], [2]),
        (10155, [ModelID.Bolt_Of_Cloth.value], [1]),
        (10030, [ModelID.Bolt_Of_Cloth.value], [1]),
        (10157, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
    "Ranger": [
        (10605, [ModelID.Tanned_Hide_Square.value], [3]),
        (10607, [ModelID.Tanned_Hide_Square.value], [2]),
        (10604, [ModelID.Tanned_Hide_Square.value], [1]),
        (14655, [ModelID.Tanned_Hide_Square.value], [1]),
        (10606, [ModelID.Tanned_Hide_Square.value], [1]),
    ],
    "Monk": [
        (9611, [ModelID.Bolt_Of_Cloth.value], [3]),
        (9613, [ModelID.Bolt_Of_Cloth.value], [2]),
        (9610, [ModelID.Bolt_Of_Cloth.value], [1]),
        (9590, [ModelID.Pile_Of_Glittering_Dust.value], [1]),
        (9612, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
    "Assassin": [
        (7185, [ModelID.Bolt_Of_Cloth.value], [3]),
        (7187, [ModelID.Bolt_Of_Cloth.value], [2]),
        (7184, [ModelID.Bolt_Of_Cloth.value], [1]),
        (7116, [ModelID.Bolt_Of_Cloth.value], [1]),
        (7186, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
    "Mesmer": [
        (7538, [ModelID.Bolt_Of_Cloth.value], [3]),
        (7540, [ModelID.Bolt_Of_Cloth.value], [2]),
        (7537, [ModelID.Bolt_Of_Cloth.value], [1]),
        (7517, [ModelID.Bolt_Of_Cloth.value], [1]),
        (7539, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
    "Necromancer": [
        (8749, [ModelID.Tanned_Hide_Square.value], [3]),
        (8751, [ModelID.Tanned_Hide_Square.value], [2]),
        (8748, [ModelID.Tanned_Hide_Square.value], [1]),
        (8731, [ModelID.Pile_Of_Glittering_Dust.value], [1]),
        (8750, [ModelID.Tanned_Hide_Square.value], [1]),
    ],
    "Ritualist": [
        (11310, [ModelID.Bolt_Of_Cloth.value], [3]),
        (11313, [ModelID.Bolt_Of_Cloth.value], [2]),
        (11309, [ModelID.Bolt_Of_Cloth.value], [3]),
        (11194, [ModelID.Bolt_Of_Cloth.value], [1]),
        (11311, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
    "Elementalist": [
        (9194, [ModelID.Bolt_Of_Cloth.value], [3]),
        (9196, [ModelID.Bolt_Of_Cloth.value], [2]),
        (9193, [ModelID.Bolt_Of_Cloth.value], [1]),
        (9171, [ModelID.Pile_Of_Glittering_Dust.value], [1]),
        (9195, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
}

STARTER_ARMOR_MODELS: dict[str, list[int]] = {
    "Assassin": [7251, 7249, 7250, 7252, 7248],
    "Ritualist": [11332, 11330, 11331, 11333, 11329],
    "Warrior": [10174, 10172, 10173, 10175, 10171],
    "Ranger": [10623, 10621, 10622, 10624, 10620],
    "Monk": [9725, 9723, 9724, 9726, 9722],
    "Elementalist": [9324, 9322, 9323, 9325, 9321],
    "Mesmer": [8026, 8024, 8025, 8054, 8023],
    "Necromancer": [8863, 8861, 8862, 8864, 8860],
}

TRASH_ITEM_MODELS: list[int] = [
    2982, #warrior Starter Sword
    1699, #warrior starter hammer
    
    5819,
    6387,
    2724,
    2652,
    2787,
    2694,
    477,
    6498,
    
    30853,
    24897,
]

def GetEarlyArmorMaterialsByProfession() -> list[tuple[int, int]]:
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    armor_data = MONASTERY_ARMOR_DATA.get(primary, MONASTERY_ARMOR_DATA["Warrior"])
    totals_by_model: dict[int, int] = {}

    for _, material_models, material_quantities in armor_data:
        for model_id, quantity in zip(material_models, material_quantities):
            totals_by_model[model_id] = totals_by_model.get(model_id, 0) + int(quantity)

    return [
        (model_id, max(1, math.ceil(total_quantity / 10)))
        for model_id, total_quantity in totals_by_model.items()
        if total_quantity > 0
    ]


def GetMonasteryArmorByProfession() -> list[tuple[int, list[int], list[int]]]:
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    return list(MONASTERY_ARMOR_DATA.get(primary, MONASTERY_ARMOR_DATA["Warrior"]))


def GetStarterArmorAndUselessItemsByProfession() -> list[int]:
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    starter_armor = STARTER_ARMOR_MODELS.get(primary, STARTER_ARMOR_MODELS["Warrior"])
    return list(starter_armor + TRASH_ITEM_MODELS)


def Unlock_Secondary_Profession() -> BehaviorTree:
    bot = ensure_botting_tree()
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    unlock_dialog = 0x813D08 if primary == "Mesmer" else 0x813D0E
    return BT.Sequence(
            name="Unlock Secondary Profession",
            map_id_or_name="Shing Jea Monastery",
            children=[
                bot.Config.Pacifist(),
                BT.MoveAndExitMap((-3480, 9460), target_map_name="Linnok Courtyard",),
                BT.HandleQuest(317, [(-159, 9174), (-92, 9217)], unlock_dialog, mode="accept"),
                BT.HandleQuest(317, (-92, 9217), 0x813D07, mode="complete", cancel_skill_reward_window=True),
                BT.HandleQuest(318, (-92, 9217), 0x813E01),
                BT.MoveAndExitMap((-3762, 9471),target_map_name="Shing Jea Monastery",),
            ],
        )
    
    
def Craft_Weapon() -> BehaviorTree:
    path_to_materials_merchant = [(-10896.94, 10807.54), (-10942.73, 10783.19), (-10614.00, 10996.00),]
    path_to_weapon_crafter = [(-10896.94, 10807.54), (-6519.00, 12335.00)]
    longbow_model_id = 11641
    
    return BT.Sequence(
            name="Craft Weapon",
            map_id_or_name="Shing Jea Monastery",
            children=[
                BT.EqualizeGold(target_gold=5000),
                BT.MoveAndBuyMaterials(path_to_materials_merchant, ModelID.Wood_Plank.value, batches=1),
                BT.BuyMaterialsFromList(GetEarlyArmorMaterialsByProfession()),
                BT.MoveAndCraftItem(pos=path_to_weapon_crafter, output_model_id=longbow_model_id,cost=100,trade_model_ids=[ModelID.Wood_Plank.value],quantity_list=[5],),
                BT.EquipItemByModelID(longbow_model_id),
            ],
        )

def Craft_Monastery_Armor() -> BehaviorTree:
    armor_crafter = (-7115.00, 12636.00)
    craft_nodes = []
    
    for index, (item_id, mats, qtys) in enumerate(GetMonasteryArmorByProfession(), start=1):
        craft_nodes.append(
            BT.Node(BT.CraftItem(output_model_id=item_id, cost=20, trade_model_ids=mats, quantity_list=qtys),)
        )
        craft_nodes.append(
            BT.Node(BT.EquipItemByModelID(item_id),)
            )
    
    return BT.Sequence(
            name="Craft Monastery Armor",
            map_id_or_name="Shing Jea Monastery",
            children = [
                BT.MoveAndInteract(armor_crafter),
                BehaviorTree.SequenceNode(
                    name="Craft And Equip Armor",
                    children=craft_nodes,
                ),
                BT.DestroyItems(GetStarterArmorAndUselessItemsByProfession()),
            ]
        )

def Extend_Inventory_Space() -> BehaviorTree:
    merchant = (-11866, 11444)
    return BT.Sequence(
            name="Extend Inventory Space",
            map_id_or_name="Shing Jea Monastery",
            children=[
                BT.MoveAndBuyMerchantItem(merchant, ModelID.Belt_Pouch.value, quantity=1),
                BT.EquipInventoryBag(ModelID.Belt_Pouch.value, Bags.BeltPouch),
                BT.BuyMerchantItem(ModelID.Bag.value, quantity=1),
                BT.EquipInventoryBag(ModelID.Bag.value, Bags.Bag1),
                BT.BuyMerchantItem(ModelID.Bag.value, quantity=1),
                BT.EquipInventoryBag(ModelID.Bag.value, Bags.Bag2),
            ],
        )
    
def To_Minister_Chos_Estate() -> BehaviorTree:
    togo_coords = (20036.72, -7821.50)
    
    intro_quest_path = [
        (17065.27, -7227.24),
        (15051.48, -1352.39),
        (10475.55, 7766.41),
        (7315.20, 10209.45),
        (6692.19, 16005.08)   
    ]
    minister_cho_state_map_id = 214
    
    return BT.Sequence(
            name="To Minister Cho's Estate",
            map_id_or_name="Shing Jea Monastery",
            children=[
                ensure_botting_tree().Config.Pacifist(),
                BT.MoveAndExitMap(exit_to_sunqua_coords, target_map_name="Sunqua Vale"),
                BT.HandleAutoQuest(togo_coords, log=True),
                BT.HandleQuest(318, intro_quest_path, 0x80000B, mode="skip", success_map_id=minister_cho_state_map_id),
                BT.WaitForMapToChange(map_id=minister_cho_state_map_id),
                BT.HandleQuest(318, (7884, -10029), 0x813E07, mode="complete"),
            ],
        )

def Minister_Chos_Estate_Mission() -> BehaviorTree:
    bot = ensure_botting_tree()
    minister_cho_state_map_id = 214
    ran_musu_gardens_map_id = 251
    return BT.Sequence(
            name="Minister Cho's Estate Mission",
            map_id_or_name=minister_cho_state_map_id,
            children=[
                PrepareForBattle(),
                BT.EnterChallenge(delay_ms=4500, target_map_id=minister_cho_state_map_id),
                BT.WaitForMapToChange(map_id=minister_cho_state_map_id),
                BT.Move([(6220.76, -7360.73),(5523.95, -7746.41)]),
                BT.Wait(13000, emote=True, announce_delay=True),
                BT.Move((591.21, -9071.10)),
                BT.Wait(26500, emote=True, announce_delay=True),
                BT.MoveDirect([(100.81, -8629.98), (1372.49, -6785.42), 
                               (2228.54, -5572.65),(4224.96, -4252.18),  
                               (5090.86, -4970.28), (4222.58, -3475.46)]),
                BT.Wait(49000, emote=True, announce_delay=True),
                BT.Move([(6216, -1108), (2617, 642), (1706.90, 1711.44)]),
                BT.Wait(23000, emote=True, announce_delay=True),
                BT.MoveAndKill([(333.32, 1124.44), (-3337.14, -4741.27)]),
                BT.WaitUntilOutOfCombat(Range.Spirit.value),
                BT.MoveAndKill([(-4496.70, -5983.27),(-7673.92, -7226.93),(-9214.53, -3880.80),(-6804.68, -1688.43), (-7132.62, 79.64) , (-7443, 2243)]),
                BT.Move((-16924, 2445)),
                BT.MoveAndInteract((-17031, 2448), target_distance=Range.Nearby.value),
                BT.WaitForMapToChange(map_id=ran_musu_gardens_map_id),
            ],
        )

def Attribute_Points_Quest_1() -> BehaviorTree:
    ran_musu_gardens_map_id = 251
    lost_treasure_quest_id = 346
    guard_model_id = 3093

    def _escort_complete() -> bool:
        guard_agent_id = int(RoutinesAgents.GetAgentIDByModelOrEncStr(guard_model_id) or 0)
        return (
            guard_agent_id != 0
            and Agent.HasQuest(guard_agent_id)
            and not Checks.Agents.InDanger(aggro_area=Range.Spirit)
        )

    return BT.Sequence(
            name="Attribute Points Quest 1",
            map_id_or_name=ran_musu_gardens_map_id,
            children=[
                BT.HandleQuest(lost_treasure_quest_id, [(15775.29, 18832.91),(14363.00, 19499.00)], 0x815A01, mode=BT.Questmode.Accept),
                PrepareForBattle(),
                BT.Move((14458.48, 17918.11)),
                BT.MoveDirect((15819.00, 18835.17)),
                BT.MoveAndExitMap((17005.00, 19787.00), target_map_id=245),
                BT.HandleQuest(
                    lost_treasure_quest_id,
                    (-17979.38, -493.08),
                    0x815A04,
                    mode=BT.Questmode.Step,
                    use_npc_model_or_enc_str=guard_model_id,
                ),
                BT.Wait(duration_ms=13000, emote=True, announce_delay=True),
                BT.FollowModel(
                    guard_model_id,
                    follow_range=Range.Area.value,
                    exit_condition=_escort_complete,
                    exit_by_area=((13796.71, -6514.31), Range.Spellcast.value),
                ),
                #touch waypoint to trigger movement
                BT.Move((13796.71, -6514.31)),
                BT.FollowModel(
                    guard_model_id,
                    follow_range=Range.Area.value,
                    exit_condition=_escort_complete,
                ),
                BT.HandleQuest(
                    lost_treasure_quest_id,
                    None,
                    0x815A07,
                    mode=BT.Questmode.Complete,
                    use_npc_model_or_enc_str=guard_model_id,
                    require_quest_marker=True,
                ),
                BT.Travel(target_map_id=ran_musu_gardens_map_id),
            ],
        )
    
def Warning_The_Tengu() -> BehaviorTree:
    ran_musu_gardens_map_id = 251
    warning_the_tengu_quest_id = 339
    the_threat_grows_quest_id = 340
    return BT.Sequence(
            name="Warning The Tengu",
            map_id_or_name=ran_musu_gardens_map_id,
            children=[
                BT.HandleQuest(warning_the_tengu_quest_id, (15846, 19013), 0x815301, mode=BT.Questmode.Accept),
                PrepareForBattle(),
                BT.MoveAndExitMap((14730, 15176), target_map_name="Kinya Province"),
                BT.HandleQuest(warning_the_tengu_quest_id, [(-1023, 4844)], 0x815304, mode=BT.Questmode.Skip),
                BT.MoveAndKill((-5011, 732), Range.Spellcast.value),
                BT.HandleQuest(warning_the_tengu_quest_id, (-1023, 4844), 0x815307, mode=BT.Questmode.Complete),
                BT.HandleQuest(the_threat_grows_quest_id, (-1023, 4844), 0x815401, mode=BT.Questmode.Accept),
            ],
        )

def _move_and_kneel(coords: PointOrPath) -> BehaviorTree:
    return BT.Sequence(
            name="Move And Kneel",
            children=[
                BT.Move(coords),
                BT.SendChatCommand("kneel"),
                BT.Wait(500),
            ],
        )
    
def The_Threat_Grows_CashCrops_Togos_Utimatum() -> BehaviorTree:
    bot = ensure_botting_tree()
    
    the_threat_grows_quest_id = 340
    sister_tai_model_id = 3367
    
    return BT.Sequence(
            name="The Threat Grows",
            map_id_or_name="Shing Jea Monastery",
            children=[
                PrepareForBattle(),
                bot.Config.Pacifist(),
                BT.MoveAndExitMap(exit_to_sunqua_coords, target_map_name="Sunqua Vale"),
                BT.MoveAndExitMap(tsumei_village_path, target_map_id=tsumei_village_map_id),
                PrepareForBattle(),
                BT.HandleAutoQuest((-5157.23, -15496.60)), #togos ultimatum
                BT.HandleAutoQuest((-10791.21, -15900.69)), #cahs crops
                BT.MoveAndExitMap((-11659, -17174), target_map_id=panjian_peninsula_map_id),
                BT.HandleAutoQuest((9037.09, 15381.85)),
                BT.Move((10077.84, 8047.69)),
                BT.WaitUntilOnCombat(Range.Spirit.value),
                BT.ClearEnemiesInArea((10077.84, 8047.69), Range.Spirit.value),
                BT.HandleQuest(quest_id=the_threat_grows_quest_id, 
                               pos=None, 
                               dialog_id=0x815407, 
                               use_npc_model_or_enc_str=sister_tai_model_id, 
                               mode=BT.Questmode.Complete, 
                               require_quest_marker=True),
                BT.HandleQuest(quest_id=the_threat_grows_quest_id, 
                               pos=None, 
                               dialog_id=0x815501, 
                               use_npc_model_or_enc_str=sister_tai_model_id, 
                               mode=BT.Questmode.Accept,),
                #cash crops
                _move_and_kneel((12817.42, 8358.96)),
                _move_and_kneel((17029.94, 7921.00)),
                _move_and_kneel((17039.33, 1927.72)),
                #togos ultimatum
                BT.HandleAutoQuest((-14308.30, -11235.08)),
                BT.Travel(target_map_id=tsumei_village_map_id),
                BT.HandleAutoQuest((-5157.23, -15496.60)), #togos ultimatum
                BT.AutoDialog(),
                BT.HandleAutoQuest((-10791.21, -15900.69)), #cahs crops
            ],
        )

#region main
def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Exit Monastery Overlook", Exit_Monastery_Overlook),
        ("Forming A Party", Forming_A_Party),
        ("Profession Specific Quests", Profession_Specific_Quests),
        ("An Audience With Master Togo", An_Audience_WithMasterTogo),
        ("Unlock Xunlai Storage", Unlock_Xunlai_Storage),
    ]
    
    """
        ("Unlock Secondary Profession", Unlock_Secondary_Profession),
        ("Unlock Xunlai Storage", Unlock_Xunlai_Storage),
        ("Craft Weapon", Craft_Weapon),
        ("Craft Monastery Armor", Craft_Monastery_Armor),
        ("Extend Inventory Space", Extend_Inventory_Space),
        ("To Minister Cho's Estate", To_Minister_Chos_Estate),
        ("Minister Cho's Estate Mission", Minister_Chos_Estate_Mission),
        ("Attribute Points Quest 1", Attribute_Points_Quest_1),
        ("Warning The Tengu", Warning_The_Tengu),
        ("The Threat Grows - Cash Crops & Togo's Ultimatum", The_Threat_Grows_CashCrops_Togos_Utimatum),
    ]
    """

def ensure_botting_tree() -> BottingTree:
    global botting_tree

    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            main_routine=get_execution_steps(),
            routine_name="Proof of Legend Sequence",
            repeat=False,
            reset=False,
            pause_on_combat=True,
            configure_fn=lambda tree: tree.Config.ConfigureUpkeepTrees(
                disable_looting=True,
                restore_isolation_on_stop=True,
                enable_outpost_imp_service=True,
                enable_explorable_imp_service=True,
                heroai_state_logging=False,
                imp_target_bag=1,
                imp_slot=0,
                imp_log=False,
                consumable_upkeeps=[
                    'candy_apple',
                    'war_supplies',
                    'honeycomb',
                ],
                enable_party_wipe_recovery=True,
            ),
        )

    return botting_tree


def main() -> None:
    global initialized, ini_key

    if not initialized:
        if not ini_key:
            ini_key = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not ini_key:
                return
            IniManager().load_once(ini_key)

        ensure_botting_tree()
        initialized = True

    tree = ensure_botting_tree()
    tree.tick()
    tree.UI.draw_window()


if __name__ == "__main__":
    main()

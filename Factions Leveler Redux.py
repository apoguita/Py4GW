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

LEVELING_SKILLBAR_MAP: dict[str, list[tuple[int | None, str]]] = {
    "Warrior": [
        (3, "OQAAAAAAAAAAAAAA"),
        (20, "OQUBIskDcdG0DaAKUECA"),
        (None, "OQUCErwSOw1ZQPoBoQRIA"),
    ],
    "Ranger": [
        (3, "OgAAAAAAAAAAAAAA"),
        (20, "OgUBIskDcdG0DaAKUECA"),
        (None, "OgUCErwSOw1ZQPoBoQRIA"),
    ],
    "Monk": [
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

USELESS_ITEM_MODELS: list[int] = [
    5819,
    6387,
    2724,
    2652,
    2787,
    2694,
    477,
    6498,
    2982,
    30853,
    24897,
]


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
    return list(starter_armor + USELESS_ITEM_MODELS)


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
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Prepare For Battle",
            children=[
                bot.Config.Aggressive(auto_loot=False),
                BT.LoadSkillbarFromMap(LEVELING_SKILLBAR_MAP),
                BT.LeaveParty(),
                BT.AddHenchmanList(_get_henchmen_for_current_map()),
                BT.RestockItemsFromList(restock_list,allow_missing=True,),
            ],
        )
    )

def Exit_Monastery_Overlook() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Exit Monastery Overlook",
            children=[
                BT.MoveAndDialog((-7048,5817), dialog_id=0x85),
                BT.WaitForMapLoad(map_name="Shing Jea Monastery"),
            ],
        )
    )
    
    
def Forming_A_Party() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Forming A Party",
            children=[
                BT.Travel(target_map_name="Shing Jea Monastery"),
                PrepareForBattle(),
                BT.HandleQuest(440, (-14063.00, 10044.00), 0x81B801, mode="accept"),
                BT.MoveAndExitMap((-14961, 11453), target_map_name="Sunqua Vale"),
                BT.HandleQuest(440, (19673.00, -6982.00), 0x81B807, mode="complete"),
            ],
        )
    )
    

def Unlock_Secondary_Profession() -> BehaviorTree:
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    unlock_dialog = 0x813D08 if primary == "Mesmer" else 0x813D0E
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Unlock Secondary Profession",
            children=[
                BT.Travel(target_map_name="Shing Jea Monastery"),
                ensure_botting_tree().Config.Pacifist(),
                BT.MoveAndExitMap((-3480, 9460), target_map_name="Linnok Courtyard",),
                BT.HandleQuest(317, [(-159, 9174), (-92, 9217)], unlock_dialog),
                BT.HandleQuest(317, (-92, 9217), 0x813D07, mode="complete"),
                BT.HandleQuest(318, (-92, 9217), 0x813E01),
                BT.MoveAndExitMap((-3762, 9471),target_map_name="Shing Jea Monastery",),
            ],
        )
    )
    
def Unlock_Xunlai_Storage() -> BehaviorTree:
    path_to_xunlai = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3825.09, 10386.81),]
    xunlai_agent_coords = (-3825.09, 10386.81)
    
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Unlock Xunlai Storage",
            children=[
                BT.Travel(target_map_name="Shing Jea Monastery"),
                BT.MoveAndDialog(path_to_xunlai, 0x84),
                BT.DialogAtXY(xunlai_agent_coords, 0x800001),
                BT.DialogAtXY(xunlai_agent_coords, 0x800002),
            ],
        )
    )
    
def Craft_Weapon() -> BehaviorTree:
    path_to_materials_merchant = [(-10896.94, 10807.54), (-10942.73, 10783.19), (-10614.00, 10996.00),]
    path_to_weapon_crafter = [(-10896.94, 10807.54), (-6519.00, 12335.00)]
    longbow_model_id = 11641
    
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Craft Weapon",
            children=[
                BT.Travel(target_map_name="Shing Jea Monastery"),
                BT.EqualizeGold(target_gold=5000),
                BT.MoveAndBuyMaterials(path_to_materials_merchant, ModelID.Wood_Plank.value, batches=1),
                BT.BuyMaterialsFromList(GetEarlyArmorMaterialsByProfession()),
                BT.MoveAndCraftItem(pos=path_to_weapon_crafter, output_model_id=longbow_model_id,cost=100,trade_model_ids=[ModelID.Wood_Plank.value],quantity_list=[5],),
                BT.EquipItemByModelID(longbow_model_id),
            ],
        )
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
    
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Craft Monastery Armor",
            children = [
                BT.Travel(target_map_name="Shing Jea Monastery"),
                BT.MoveAndInteract(armor_crafter),
                BehaviorTree.SequenceNode(
                    name="Craft And Equip Armor",
                    children=craft_nodes,
                ),
                BT.DestroyItems(GetStarterArmorAndUselessItemsByProfession()),
            ]
        )
    )

def Extend_Inventory_Space() -> BehaviorTree:
    merchant = (-11866, 11444)
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Extend Inventory Space",
            children=[
                BT.Travel(target_map_name="Shing Jea Monastery"),
                BT.MoveAndBuyMerchantItem(merchant, ModelID.Belt_Pouch.value, quantity=1),
                BT.EquipInventoryBag(ModelID.Belt_Pouch.value, Bags.BeltPouch),
                BT.BuyMerchantItem(ModelID.Bag.value, quantity=1),
                BT.EquipInventoryBag(ModelID.Bag.value, Bags.Bag1),
                BT.BuyMerchantItem(ModelID.Bag.value, quantity=1),
                BT.EquipInventoryBag(ModelID.Bag.value, Bags.Bag2),
            ],
        )
    )
    
def To_Minister_Chos_Estate() -> BehaviorTree:
    exit_to_sunqua_coords = (-14961, 11453)
    intro_quest_path = [
        (16182.62, -7841.86),
        (6611.58, 15847.51),
        (6661.90, 16081.70),
    ]
    minister_cho_state_map_id = 214
    
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="To Minister Cho's Estate",
            children=[
                BT.Travel(target_map_name="Shing Jea Monastery"),
                ensure_botting_tree().Config.Pacifist(),
                BT.MoveAndExitMap(exit_to_sunqua_coords, target_map_name="Sunqua Vale"),
                BT.HandleQuest(318, intro_quest_path, 0x80000B, mode="skip", success_map_id=minister_cho_state_map_id),
                BT.WaitForMapToChange(map_id=minister_cho_state_map_id),
                BT.HandleQuest(318, (7884, -10029), 0x813E07, mode="complete"),
            ],
        )
    )

def Minister_Chos_Estate_Mission() -> BehaviorTree:
    bot = ensure_botting_tree()
    minister_cho_state_map_id = 214
    ran_musu_gardens_map_id = 251
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Minister Cho's Estate Mission",
            children=[
                BT.Travel(target_map_id=minister_cho_state_map_id),
                PrepareForBattle(),
                BT.EnterChallenge(delay_ms=4500, target_map_id=minister_cho_state_map_id),
                BT.WaitForMapToChange(map_id=minister_cho_state_map_id),
                BT.Move([(6220.76, -7360.73),(5523.95, -7746.41)]),
                BT.Wait(13000, emote=True, announce_delay=True),
                BT.Move((591.21, -9071.10)),
                BT.Wait(26500, emote=True, announce_delay=True),
                BT.Move([(4889, -5043), (4222.58, -3475.46)]),
                BT.Wait(45000, emote=True, announce_delay=True),
                BT.Move([(6216, -1108), (2617, 642), (1706.90, 1711.44)]),
                BT.Wait(25000, emote=True, announce_delay=True),
                BT.Move([(333.32, 1124.44), (-3337.14, -4741.27)]),
                BT.Wait(35000, emote=True, announce_delay=True),
                BT.Move([(-4661.99, -6285.81), (-7454, -7384), (-9138, -4191), (-7109, -25), (-7443, 2243)]),
                BT.Wait(5000,  announce_delay=True),
                BT.Move((-16924, 2445)),
                BT.MoveAndInteract((-17031, 2448), target_distance=Range.Nearby.value),
                BT.WaitForMapToChange(map_id=ran_musu_gardens_map_id),
            ],
        )
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

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Attribute Points Quest 1",
            children=[
                BT.Travel(target_map_id=ran_musu_gardens_map_id),
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
    )

#main
def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Exit Monastery Overlook", Exit_Monastery_Overlook),
        ("Forming A Party", Forming_A_Party),
        ("Unlock Secondary Profession", Unlock_Secondary_Profession),
        ("Unlock Xunlai Storage", Unlock_Xunlai_Storage),
        ("Craft Weapon", Craft_Weapon),
        ("Craft Monastery Armor", Craft_Monastery_Armor),
        ("Extend Inventory Space", Extend_Inventory_Space),
        ("To Minister Cho's Estate", To_Minister_Chos_Estate),
        ("Minister Cho's Estate Mission", Minister_Chos_Estate_Mission),
        ("Attribute Points Quest 1", Attribute_Points_Quest_1),
    ]

def ensure_botting_tree() -> BottingTree:
    global botting_tree

    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            main_routine=get_execution_steps(),
            routine_name="Proof of Legend Sequence",
            repeat=False,
            reset=False,
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

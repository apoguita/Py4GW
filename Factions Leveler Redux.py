from __future__ import annotations

from typing import Callable
from typing import TypeAlias



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
from Py4GWCoreLib.routines_src.behaviourtrees_src.constants import *


from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.native_src.internals.types import PointOrPath
from Py4GWCoreLib.native_src.internals.types import PointPath


MODULE_NAME = "Beautiful Shing Jea"
INI_PATH = "Widgets/Automation/Bots/Templates"
INI_FILENAME = "BottingTreeTemplate.ini"

initialized = False
ini_key = ""
botting_tree: BottingTree | None = None
LOOTING_ACTIVE = False

EMPTY_SKILLBARS: dict[str, str] = {
    "Warrior": "OQAREJAAAAAAAAAAAA",
    "Ranger": "OgARkJAAAAAAAAAAAA",
    "Monk": "OwAAAAAAAAAAAAAA",
    "Necromancer": "OABBUFAAAAAAAAAAAA",
    "Mesmer": "OQBBIFAAAAAAAAAAAA",
    "Elementalist": "",
    "Ritualist": "",
    "Assassin": "",
}

LEVELING_SKILLBAR_MAP: dict[str, list[tuple[int | None, str]]] = {
    "Warrior": [
        (3, "OQAREpQoKlrBAAAAACA"),
        (5, "OQASEJJFCVpcNAAAAAQA"),
        (6, "OQASEJZFCVpcNA0W4AQA"),
        (10, "OQITELZZrQoKlrBAA0ezCAA"),
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
        (4, "OABBUFkZaAAAAAAgAA"),
        (20, "OAVBIskDcdG0DaAKUECA"),
        (None, "OAVCErwSOw1ZQPoBoQRIA"),
    ],
    "Mesmer": [
        (3, "OQBBIEoBKAAAAFNkAA"),
        (20, "OQBBIskDcdG0DaAKUECA"),
        (None, "OQBCErwSOw1ZQPoBoQRIA"),
    ],
    "Elementalist": [
        (3, "OgBBoEIMAAAAAlSrAA"),
        (20, "OgVBIskDcdG0DaAKUECA"),
        (None, "OgVCErwSOw1ZQPoBoQRIA"),
    ],
    "Ritualist": [
        (3, "OAChESCxnxOOAAAAAAIA"),
        (20, "OAWBIskDcdG0DaAKUECA"),
        (None, "OAWCErwSOw1ZQPoBoQRIA"),
    ],
    "Assassin": [
        (3, "OwBhMSyDzwIMAAAAgLLA"),
        (20, "OAWBIskDcdG0DaAKUECA"),
        (None, "OwVCErwSOw1ZQPoBoQRIA"),
    ],
}


STARTER_SWORD_MODEL_ID = 2982
STARTER_HAMMER_MODEL_ID = 1699
STARTER_AXE_MODEL_ID = 26
STARTER_BOW_MODEL_ID = 477
STARTER_HOLY_ROD = 2787
STARTER_TRUNCHEON = 2694
STARTER_CANE = 2652
STARTER_ELEMENTAL_ROD = 2742
STARTER_DAGGERS = 6387
STARTER_RITUALIST_WAND = 6498
MONASTERY_CREDIT = 5819

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
    STARTER_SWORD_MODEL_ID, #warrior Starter Sword
    STARTER_HAMMER_MODEL_ID, #warrior starter hammer
    STARTER_AXE_MODEL_ID, #warrior starter axe
    
    STARTER_DAGGERS,
    STARTER_ELEMENTAL_ROD,
    STARTER_CANE,
    STARTER_HOLY_ROD,
    STARTER_TRUNCHEON,
    STARTER_BOW_MODEL_ID,
    STARTER_RITUALIST_WAND,
    
    #30853,
    #24897,
]

TRASH_ITEM_MODELS += [model_id for model_ids in STARTER_ARMOR_MODELS.values() for model_id in model_ids]

BuyList: TypeAlias = list[tuple[int, int]]
CraftStep: TypeAlias = tuple[int, int, list[int], list[int]]
CraftStepList: TypeAlias = list[CraftStep]


MONASTERY_COMMON_BUY_BY_PROFESSION: dict[str, BuyList] = {
    "Warrior": [(ModelID.Bolt_Of_Cloth.value, 1), (ModelID.Iron_Ingot.value, 2), (ModelID.Wood_Plank.value, 1)],
    "Ranger": [(ModelID.Tanned_Hide_Square.value, 1), (ModelID.Wood_Plank.value, 1)],
    "Monk": [(ModelID.Bolt_Of_Cloth.value, 1), (ModelID.Pile_Of_Glittering_Dust.value, 1), (ModelID.Wood_Plank.value, 1)],
    "Necromancer": [(ModelID.Tanned_Hide_Square.value, 1), (ModelID.Pile_Of_Glittering_Dust.value, 1), (ModelID.Bone.value, 1)],
    "Mesmer": [(ModelID.Bolt_Of_Cloth.value, 1), (ModelID.Pile_Of_Glittering_Dust.value, 1), (ModelID.Wood_Plank.value, 1)],
    "Elementalist": [(ModelID.Bolt_Of_Cloth.value, 1), (ModelID.Pile_Of_Glittering_Dust.value, 1), (ModelID.Iron_Ingot.value, 1)],
    "Assassin": [(ModelID.Bolt_Of_Cloth.value, 1), (ModelID.Iron_Ingot.value, 1)],
    "Ritualist": [(ModelID.Bolt_Of_Cloth.value, 1), (ModelID.Bone.value, 1), (ModelID.Plant_Fiber.value, 1)],
}


TSUMEI_RARE_BUY_BY_PROFESSION: dict[str, BuyList] = {
    "Warrior": [(ModelID.Steel_Ingot.value, 1)],
    "Ranger": [],
    "Monk": [],
    "Necromancer": [],
    "Mesmer": [],
    "Elementalist": [],
    "Assassin": [],
    "Ritualist": [],
}


MONASTERY_ARMOR_CRAFT_BY_PROFESSION: dict[str, CraftStepList] = {
    "Warrior": [
        (10156, 20, [ModelID.Bolt_Of_Cloth.value], [3]),
        (10158, 20, [ModelID.Bolt_Of_Cloth.value], [2]),
        (10155, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
        (10030, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
        (10157, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
    "Ranger": [
        (10605, 20, [ModelID.Tanned_Hide_Square.value], [3]),
        (10607, 20, [ModelID.Tanned_Hide_Square.value], [2]),
        (10604, 20, [ModelID.Tanned_Hide_Square.value], [1]),
        (14655, 20, [ModelID.Tanned_Hide_Square.value], [1]),
        (10606, 20, [ModelID.Tanned_Hide_Square.value], [1]),
    ],
    "Monk": [
        (9611, 20, [ModelID.Bolt_Of_Cloth.value], [3]),
        (9613, 20, [ModelID.Bolt_Of_Cloth.value], [2]),
        (9610, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
        (9590, 20, [ModelID.Pile_Of_Glittering_Dust.value], [1]),
        (9612, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
    "Assassin": [
        (7185, 20, [ModelID.Bolt_Of_Cloth.value], [3]),
        (7187, 20, [ModelID.Bolt_Of_Cloth.value], [2]),
        (7184, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
        (7116, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
        (7186, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
    "Mesmer": [
        (7538, 20, [ModelID.Bolt_Of_Cloth.value], [3]),
        (7540, 20, [ModelID.Bolt_Of_Cloth.value], [2]),
        (7537, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
        (7517, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
        (7539, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
    "Necromancer": [
        (8749, 20, [ModelID.Tanned_Hide_Square.value], [3]),
        (8751, 20, [ModelID.Tanned_Hide_Square.value], [2]),
        (8748, 20, [ModelID.Tanned_Hide_Square.value], [1]),
        (8731, 20, [ModelID.Pile_Of_Glittering_Dust.value], [1]),
        (8750, 20, [ModelID.Tanned_Hide_Square.value], [1]),
    ],
    "Ritualist": [
        (11310, 20, [ModelID.Bolt_Of_Cloth.value], [3]),
        (11313, 20, [ModelID.Bolt_Of_Cloth.value], [2]),
        (11309, 20, [ModelID.Bolt_Of_Cloth.value], [3]),
        (11194, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
        (11311, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
    "Elementalist": [
        (9194, 20, [ModelID.Bolt_Of_Cloth.value], [3]),
        (9196, 20, [ModelID.Bolt_Of_Cloth.value], [2]),
        (9193, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
        (9171, 20, [ModelID.Pile_Of_Glittering_Dust.value], [1]),
        (9195, 20, [ModelID.Bolt_Of_Cloth.value], [1]),
    ],
}

TSUMEI_WEAPON_CRAFT_BY_PROFESSION: dict[str, CraftStepList] = {
    "Warrior": [
        (11664, 200, [ModelID.Iron_Ingot.value, ModelID.Wood_Plank.value], [8, 2]),
        (11669, 200, [ModelID.Iron_Ingot.value, ModelID.Steel_Ingot.value], [6, 1]),
    ],
    "Ranger": [
        (11666, 200, [ModelID.Wood_Plank.value], [10]),
    ],
    "Monk": [
        (11681, 200, [ModelID.Wood_Plank.value, ModelID.Pile_Of_Glittering_Dust.value], [5, 3]),
    ],
    "Necromancer": [
        (11675, 200, [ModelID.Bone.value, ModelID.Pile_Of_Glittering_Dust.value], [6, 2]),
    ],
    "Mesmer": [
        (11671, 200, [ModelID.Wood_Plank.value, ModelID.Pile_Of_Glittering_Dust.value], [6, 2]),
    ],
    "Elementalist": [
        (11678, 200, [ModelID.Iron_Ingot.value], [8]),
    ],
    "Assassin": [
        (11667, 200, [ModelID.Iron_Ingot.value], [8]),
    ],
    "Ritualist": [
        (15241, 200, [ModelID.Bone.value, ModelID.Plant_Fiber.value], [4, 4]),
    ],
}

HEADMASTER_ZHAN_COORDS = (-7039.83, 7325.59)
HEADMASTER_GREICO_COORDS = (-7714.79, 6727.62)
HEADMASTER_AMARA_COORDS = (-7092.22, 7497.88)
HEADMASTER_KUJU_COORDS = (-7101.96, 7125.17)
HEADMASTER_KAA_COORDS = (-7351.34, 7584.09)
HEADMASTER_VHANG_COORDS = (-7892.99, 6928.65)
HEADMASTER_LEE_COORDS = (-7849.87, 6814.73)
HEADMSTER_QUIN_COORDS = (-7785.90, 7335.15)

MASTER_COORDS_BY_PROFESSION = { 
        "Ranger": HEADMASTER_GREICO_COORDS,
        "Assassin": HEADMASTER_LEE_COORDS,
        "Elementalist": HEADMASTER_VHANG_COORDS,
        "Ritualist": HEADMSTER_QUIN_COORDS,
        "Mesmer": HEADMASTER_KAA_COORDS,
        "Monk": HEADMASTER_AMARA_COORDS,
        "Warrior": HEADMASTER_ZHAN_COORDS,
        "Necromancer": HEADMASTER_KUJU_COORDS,   
    }

OTHER_MASTER_COORDS_BY_PROFESSION: dict[str, list[PointOrPath]] = {
    profession: [
        coords
        for other_profession, coords in MASTER_COORDS_BY_PROFESSION.items()
        if other_profession != profession
    ]
    for profession in MASTER_COORDS_BY_PROFESSION
}


#region helpers
def Aggressive():
    bot = ensure_botting_tree()
    return bot.Config.Aggressive(auto_loot=LOOTING_ACTIVE)

def Pacifist():
    bot = ensure_botting_tree()
    return bot.Config.Pacifist(auto_loot=LOOTING_ACTIVE)


def _get_henchmen_for_current_map() -> list[int]:
    party_size = Map.GetMaxPartySize()
    current_map_id = Map.GetMapID()

    if party_size <= 4:
        return [2, 5, 1]
    if current_map_id == SEITUNG_HARBOR:
        return [2, 3, 1, 6, 5]
    if current_map_id == ZEN_DAIJUN:
        return [2, 3, 1, 8, 5]
    if current_map_id == THE_MARKETPLACE:
        return [6, 9, 5, 1, 4, 7, 3]
    if Map.IsMapIDMatch(current_map_id, KAINENG_CENTER):
        return [2, 10, 4, 8, 7, 9, 12]
    if current_map_id == BOREAL_STATION:
        return [7, 9, 2, 3, 4, 6, 5]
    return [2, 3, 5, 6, 7, 9, 10]


def PrepareForBattle() -> BehaviorTree:
    restock_candy_apple_qty = 0# 10
    restock_war_supplies_qty = 0# 10
    restock_honeycomb_qty = 0# 20
    
    def _add_henchmen_from_blackboard(node: BehaviorTree.Node) -> BehaviorTree:
        return BT.CreateParty(henchman_ids=node.blackboard.get("current_map_henchmen", []))

    
    restock_list = [
        (ModelID.Candy_Apple.value, restock_candy_apple_qty), 
        (ModelID.War_Supplies.value, restock_war_supplies_qty), 
        (ModelID.Honeycomb.value, restock_honeycomb_qty),
    ]
    return BT.Sequence(
            name="Prepare For Battle",
            children=[
                Aggressive(),
                BT.LoadSkillbarFromMap(LEVELING_SKILLBAR_MAP),
                BT.LeaveParty(),
                BT.SaveBlackboardValue("current_map_henchmen", _get_henchmen_for_current_map),
                BT.Subtree(name="AddHenchmenForCurrentMap",subtree_fn=_add_henchmen_from_blackboard,),
                BT.RestockItemsFromList(restock_list,allow_missing=True,),
            ],
        )

#region routines
def Exit_Monastery_Overlook() -> BehaviorTree:
    STARTER_WEAPON_MODEL_IDS = {
        "Warrior": STARTER_SWORD_MODEL_ID,
        "Ranger": STARTER_BOW_MODEL_ID,
        "Monk": STARTER_HOLY_ROD,
        "Necromancer": STARTER_TRUNCHEON,
        "Mesmer": STARTER_CANE,
        "Elementalist": STARTER_ELEMENTAL_ROD,
        "Assassin": STARTER_DAGGERS,
        "Ritualist": STARTER_RITUALIST_WAND,
    }
    LUDO_GREETING_COORDS = (-7048,5817)

    def _handle_profession_autoquest(node: BehaviorTree.Node) -> BehaviorTree:
        return BT.HandleAutoQuest(pos=node.blackboard.get("profession_coords"), buttons=[0, 0])
          
    def _equip_starter_weapon_from_blackboard(node: BehaviorTree.Node) -> BehaviorTree:
        starter_weapon_model_id = node.blackboard.get("starter_weapon_model_id")
        if starter_weapon_model_id is None:
            return BT.Failer(name="MissingStarterWeaponModelId")
        return BT.EquipItemByModelID(starter_weapon_model_id)

    return BT.Sequence(
            name="Exit Monastery Overlook",
            children=[
                BT.HandleAutoQuest(pos=LUDO_GREETING_COORDS, buttons=[0, 0, 1, 0, 0]),
                BT.WaitForMapLoad(map_id=SHING_JEA_MONASTERY),
                BT.GetValuesByProfession(profession_values=MASTER_COORDS_BY_PROFESSION, target_key="profession_coords"),
                BT.Subtree(name="MoveToProfessionCoords", subtree_fn=_handle_profession_autoquest),
                BT.GetValuesByProfession(
                    profession_values=STARTER_WEAPON_MODEL_IDS,
                    target_key="starter_weapon_model_id",
                ),
                BT.Subtree(name="EquipWeaponByProfession", subtree_fn=_equip_starter_weapon_from_blackboard),
            ],
        )
    
 
def Forming_A_Party() -> BehaviorTree:
    LUDO_PARTY_GIVE_COORDS = (-14063.00, 10044.00)
    LUDO_PARTY_RECEIVE_COORDS = (19673.00, -6982.00)
    return BT.Sequence(
            name="Forming A Party",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                BT.HandleAutoQuest(LUDO_PARTY_GIVE_COORDS),
                BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.HandleAutoQuest(LUDO_PARTY_RECEIVE_COORDS),
            ],
        )
    
def _take_quest_for_profession_from_master(node: BehaviorTree.Node, profession: str, COORDS:PointOrPath) -> BehaviorTree:
    if node.blackboard.get("player_primary_profession_name") != profession:
        return BT.HandleAutoQuest(pos=COORDS, buttons=[0, 0, 0])
    return BT.HandleAutoQuest(pos=COORDS, buttons=[0, 0])
    
      
#region warrior
def WarriorPrimaryStarterQuestsPart1() -> BehaviorTree:
    bot = ensure_botting_tree()
    TO_TALON_SILVERWING_COORDS = [(17065.27, -7227.24),(15051.48, -1352.39)]
    TALON_SILVERWING_COORDS = (11398.17, 7258.22)
    
    def _approach_talon_silverwing(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") in ("Warrior",):
            return BT.Move(TO_TALON_SILVERWING_COORDS)
        return BT.Succeeder(name="SkipApproachTalonSilverwing")
    
    def _exit_to_tsumei_if_warrior(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") == "Warrior":
            return BT.Sequence(
                name="Exit To Tsumei Village",
                children=[
                    BT.Travel(SHING_JEA_MONASTERY),
                    PrepareForBattle(),
                    Pacifist(),
                    BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                    BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE),
                ]
            )
        return BT.Succeeder(name="SkipExitToTsumei")
    
    return BT.Sequence(
            name="Warrior Primary Starter Quests Part 1",
            children=[
                Pacifist(),
                BT.Subtree(name="Approach Talon Silverwing", subtree_fn=_approach_talon_silverwing,),
                BT.Subtree(
                    name="Talon Silverwing Intro Quest",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master(node,"Warrior",TALON_SILVERWING_COORDS,),
                ),
                BT.EquipItemByModelID(STARTER_AXE_MODEL_ID),
                BT.HandleAutoQuest(TALON_SILVERWING_COORDS),
                Aggressive(),
                BT.ClearEnemiesInArea(TALON_SILVERWING_COORDS, Range.Spellcast.value),
                BT.Wait(1000),
                BT.HandleAutoQuest(TALON_SILVERWING_COORDS, require_quest_marker=True, buttons=[0, 0],),
                BT.Subtree(name="Exit To Tsumei If Warrior",subtree_fn=_exit_to_tsumei_if_warrior,),
            ],
        )

def WarriorPrimaryStarterQuestsPart2() -> BehaviorTree:
    WENG_GAH_COORDS = (6678.91, 6318.28)
    KILLSPOT_COORDS = (10887.11, 12441.24)
    
    def _get_to_panjian_if_warrior(node: BehaviorTree.Node) -> BehaviorTree: 
        if node.blackboard.get("player_primary_profession_name") != "Warrior":
            return BT.Succeeder(name="SkipGetToPanjian")
        
        return BT.Sequence(
            name="Get To Panjian Peninsula",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_PANJIAN_PENINSULA, target_map_id=PANJIAN_PENINSULA),
            ]
        )

    return BT.Sequence(
            name="Warrior Primary Starter Quests Part 2",
            children=[
                BT.Subtree(
                    name="Get To Panjian If Warrior",
                    subtree_fn=_get_to_panjian_if_warrior,
                ),
                #track down Weng Gah
                BT.Subtree(
                    name="Take Quest From Weng Gah If Warrior",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master( node, "Warrior",WENG_GAH_COORDS,),
                ),
                BT.MoveAndKill(KILLSPOT_COORDS),
                BT.HandleAutoQuest(WENG_GAH_COORDS, buttons=[0,0]),
            ],
        )

#region ranger
def RangerPrimaryStarterQuestsPart1() -> BehaviorTree:
    RABBIT_PT1_COORDS = (9583.81, -5396.87)
    RABBIT_PT2_COORDS = (7113.02, -8898.87)
    RABBIT_PT3_COORDS = [(6339.18, -10887.55), (4371.29, -12062.85), (2083.06, -11528.21)]
    TO_SUJUN_COORDS = [(17065.27, -7227.24),]
    SUJUN_COORDS = [(5153.02, -4831.28)]
    SUJUN_ENC_STR = "\\x5CD9\\xA792\\xB5D7\\x67C6"
    
    def _approach_sujun(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") in ("Ranger",):
            return BT.Move(TO_SUJUN_COORDS)
        return BT.Succeeder(name="SkipApproachSujun")
    
    return BT.Sequence(
            name="Ranger Primary Starter Quests Part 1",
            children=[
                Pacifist(),
                BT.Subtree( name="Approach Sujun",subtree_fn=_approach_sujun,),
                BT.Subtree(
                    name="Sujun Intro",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master(node,"Ranger", SUJUN_COORDS,),
                ),
                BT.HandleAutoQuest(pos=SUJUN_COORDS),
                Aggressive(),
                BT.MoveAndInteractWithGadget(RABBIT_PT1_COORDS),
                BT.ClearEnemiesInArea(RABBIT_PT1_COORDS, Range.Spellcast.value),
                BT.Wait(5000, emote="dance", announce_delay=True),
                BT.MoveAndKill(RABBIT_PT2_COORDS, Range.Spirit.value),
                BT.MoveAndInteractWithGadget(RABBIT_PT2_COORDS),
                BT.Wait(5000, emote="dance", announce_delay=True),
                BT.WaitUntilOnCombat(Range.Spellcast.value),
                BT.ClearEnemiesInArea(RABBIT_PT2_COORDS, Range.Spellcast.value),
                BT.Wait(5000, emote="dance", announce_delay=True),
                BT.MoveAndKill(RABBIT_PT3_COORDS, Range.Spellcast.value),
                BT.MoveAndInteractWithGadget(RABBIT_PT3_COORDS[2]),
                BT.Wait(5000, emote="dance", announce_delay=True),
                BT.HandleAutoQuest(pos=None, use_npc_model_or_enc_str=SUJUN_ENC_STR, buttons=[0, 0],require_quest_marker=True,),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE),
            ],
        )
    
def RangerPrimaryStarterQuestsPart2() -> BehaviorTree:
    ZHO_COORDS = (9760.99, 5168.66)
    KILLSPOT_COORDS = [(8664.65, 1558.53),(10120.81, 2450.65)]
    ZHO_REWARD_COORDS = (8426.00, 1537.00)
    ZHO_ENC_STR = "\\x5CDF\\x8329\\xF25F\\x1B43"
    
    def _get_to_kynya_if_ranger(node: BehaviorTree.Node) -> BehaviorTree: 
        if node.blackboard.get("player_primary_profession_name") != "Ranger":
            return BT.Succeeder(name="SkipGetToKinya")
        
        return BT.Sequence(
            name="Get To Kinya Province",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_KINYA_PROVINCE, target_map_id=KINYA_PROVINCE),
            ],
        )
        
    def _cancel_skill_reward_window_if_not_ranger(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") != "Ranger":
            return BT.CancelSkillRewardWindow()
        return BT.Succeeder(name="SkipCancelSkillRewardWindow")

    
    return BT.Sequence(
            name="Ranger Primary Starter Quests Part 2",
            children=[
                #track down zho
                BT.Subtree(name="Get To Kinya Province If Ranger",subtree_fn=_get_to_kynya_if_ranger,),
                BT.HandleAutoQuest(ZHO_COORDS, buttons=[0, 0],),
                BT.Subtree( name="Cancel Skill Reward Window If Not Ranger",subtree_fn=_cancel_skill_reward_window_if_not_ranger,),
                BT.HandleAutoQuest(ZHO_COORDS),
                BT.Move(KILLSPOT_COORDS),
                BT.SendChatCommand("dance"),
                BT.WaitUntilOnCombat(Range.Spellcast.value),
                BT.ClearEnemiesInArea(KILLSPOT_COORDS[0], Range.Spellcast.value),
                BT.HandleAutoQuest(ZHO_REWARD_COORDS, 
                                   use_npc_model_or_enc_str=ZHO_ENC_STR, 
                                   buttons=[0, 0],
                                   require_quest_marker=True,),
            ],
        )
    
#region monk
def MonkPrimaryStarterQuestsPart1() -> BehaviorTree:
    TO_SISTER_TAI_COORDS = [(17065.27, -7227.24)]
    SISTER_TAI_COORDS = [(9445.05, 3657.00)]
    KILLSPOT_COORDS = (9969.57, 2771.42)
    
    def _approach_sister_tai(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") in ("Monk",):
            return BT.Move(TO_SISTER_TAI_COORDS)
        return BT.Succeeder(name="SkipApproachSisterTai")
    
    def _exit_to_tsumei_if_monk(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") == "Monk":
            return BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE)
        return BT.Succeeder(name="SkipExitToTsumei")
    
    return BT.Sequence(
            name="Monk Primary Starter Quests Part 1",
            children=[
                Pacifist(),
                BT.Subtree( name="Approach Sister Tai", subtree_fn=_approach_sister_tai,),
                BT.Subtree(
                    name="Sister Tai Intro Quest",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master(node,"Monk",SISTER_TAI_COORDS,),
                ),
                BT.HandleAutoQuest(pos=SISTER_TAI_COORDS[0],),
                Aggressive(),
                BT.MoveAndKill(KILLSPOT_COORDS, Range.Spellcast.value),
                Pacifist(),
                BT.HandleAutoQuest(pos=SISTER_TAI_COORDS[0],buttons=[0, 0]),
                BT.Subtree(name="Exit To Tsumei If Monk",subtree_fn=_exit_to_tsumei_if_monk,),
            ],
        )
    
def MonkPrimaryStarterQuestsPart2() -> BehaviorTree:
    BROTHER_PE_WAN_COORDS = (4726.45, -2728.68)
    INGREDIENT1_COORDS = (6608.74, 4559.66)
    INGREDIENT2_COORDS = (9602.88, 12303.18)
    
    def _get_to_kynya_if_monk(node: BehaviorTree.Node) -> BehaviorTree: 
        if node.blackboard.get("player_primary_profession_name") != "Monk":
            return BT.Succeeder(name="SkipGetToKinya")
        
        return BT.Sequence(
            name="Get To Kinya Province",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_KINYA_PROVINCE, target_map_id=KINYA_PROVINCE),
            ],
        )
        
    return BT.Sequence(
            name="Monk Primary Starter Quests Part 2",
            children=[
                BT.Subtree(name="Get To Kinya Province If Monk",subtree_fn=_get_to_kynya_if_monk,),
                #track down brother pe wan
                BT.Subtree(
                    name="Take Quest With Brother Pe Wan",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master(node, "Monk", BROTHER_PE_WAN_COORDS,),
                ),
                BT.MoveAndInteractWithGadget(INGREDIENT1_COORDS),
                BT.MoveAndInteractWithGadget(INGREDIENT2_COORDS),
                BT.HandleAutoQuest(BROTHER_PE_WAN_COORDS,buttons=[0, 0]),
            ],
        )
    
#region necromancer
def NecromancerPrimaryStarterQuestsPart1() -> BehaviorTree:
    TO_RENG_KU_COORDS = [(17065.27, -7227.24),(15051.48, -1352.39)]
    RENG_KU_COORDS = [(16265.57, 3143.39)]
    RENG_KU_REWARD_COORDS = (16268.68, 3136.99)
    KILLSPOT_COORDS = (20268.91, 8145.42)

    def _exit_to_tsumei_if_necromancer(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") == "Necromancer":
            return BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE)
        return BT.Succeeder(name="SkipExitToTsumei")

    return BT.Sequence(
            name="Necromancer Primary Starter Quests Part 1",
            children=[
                Pacifist(),
                BT.Move(TO_RENG_KU_COORDS),
                BT.HandleAutoQuest(RENG_KU_COORDS,buttons=[0, 0],),
                Aggressive(),
                BT.MoveAndKill(KILLSPOT_COORDS, flag_heroes_to_waypoint=True),
                BT.Repeater( name="KillRepeater",repeat_count=4,
                    children=[
                        BT.ClearEnemiesInArea(KILLSPOT_COORDS, Range.Spellcast.value),
                        BT.Wait(2000),
                    ],
                ),
                Pacifist(),
                BT.HandleAutoQuest(RENG_KU_REWARD_COORDS, buttons=[0,0]),
                BT.Subtree(name="Exit To Tsumei If Necromancer",subtree_fn=_exit_to_tsumei_if_necromancer,),
            ],
        )
    
def NecromancerPrimaryStarterQuestsPart2() -> BehaviorTree:
    SU_COORDS = (1959.98, -8569.83)
    SU_ENC_STR = "\\x5CB4\\xA81D\\x9494\\x30F3"
    KILLSPOTS_COORDS = [(5934.45, -12796.59),
                        (11069.31, -13898.07),
                        (12615.04, -10692.58),
                        (9007.76, -9230.19)]
    
    def _get_to_panjian_if_necromancer(node: BehaviorTree.Node) -> BehaviorTree: 
        if node.blackboard.get("player_primary_profession_name") != "Necromancer":
            return BT.Succeeder(name="SkipGetToPanjian")
        return BT.Sequence(
            name="Get To Panjian Peninsula",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_PANJIAN_PENINSULA, target_map_id=PANJIAN_PENINSULA),
            ]
        )
    
    return BT.Sequence(
            name="Necromancer Primary Starter Quests Part 2",
            children=[
                BT.Subtree(name="Get To Panjian If Necromancer",subtree_fn=_get_to_panjian_if_necromancer,),
                BT.Subtree(
                    name="Take Quest From Su",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master(node,"Necromancer",SU_COORDS,),
                ),
                BT.HandleAutoQuest(SU_COORDS, buttons=[0,],),
                *[BT.MoveAndKill(coord, Range.Spellcast.value, flag_heroes_to_waypoint=True) for coord in KILLSPOTS_COORDS],
                BT.HandleAutoQuest(pos=None, use_npc_model_or_enc_str=SU_ENC_STR, require_quest_marker=True, buttons=[0, 0],), 
            ],
        )

#region mesmer
def MesmerPrimaryStarterQuestsPart1() -> BehaviorTree:
    TO_MEI_LING_COORDS = [(17065.27, -7227.24),]
    MEI_LING_COORDS = [(6805.08, -1273.33)]
    KILLSPOT_COORDS = (-8735.46, 3582.86)
    OVER_THE_BRIDGE_COORDS = (-7333.20, 6846.77)
    TO_TSUMEI_VILLAGE_COORDS = [(6240.77, -5034.47), (-5.33, -10856.58)] + FROM_SUNQUA_VALE_TO_TSUMEI_VILLAGE
    
    def _approach_mei_ling(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") in ("Mesmer",):
            return BT.Move(TO_MEI_LING_COORDS)
        return BT.Succeeder(name="SkipApproachMeiLing")
    
    def _exit_to_tsumei_if_mesmer(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") == "Mesmer":
            return BT.MoveAndExitMap(TO_TSUMEI_VILLAGE_COORDS, target_map_id=TSUMEI_VILLAGE)
        return BT.Succeeder(name="SkipExitToTsumei")
    
    return BT.Sequence(
            name="Mesmer Primary Starter Quests Part 1",
            children=[
                Pacifist(),
                BT.Subtree(name="Approach Mei Ling",subtree_fn=_approach_mei_ling,),
                BT.Subtree(
                    name="Mei Ling Intro Quest",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master( node,"Mesmer",MEI_LING_COORDS,),
                ),
                Aggressive(),
                BT.Move(KILLSPOT_COORDS),
                BT.MoveDirect(OVER_THE_BRIDGE_COORDS),
                BT.HandleAutoQuest(MEI_LING_COORDS, buttons=[0, 0],),
                BT.Subtree(name="Exit To Tsumei If Mesmer",subtree_fn=_exit_to_tsumei_if_mesmer,),
            ],
        )
    
def MesmerPrimaryStarterQuestsPart2() -> BehaviorTree:
    KILLSPOT_COORDS = [(11957.96, 3480.97),(8015.62, -2143.84),]
    KILLSPOT_END_COORDS = [(6868.74, -8670.04),(4061.85, -13737.38)]
    LO_SHA_COORDS = (5362.32, -13625.09)
    
    QUEST_KILL_SPOT1_COORDS = (9501.89, -10770.79)
    CHEST_LOCATION_COORDS = (11039.42, -13346.81)
    
    def _exit_to_kinya_if_mesmer(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") == "Mesmer":
            return BT.Sequence(
                name="Get To Kinya Province",
                map_id_or_name=TSUMEI_VILLAGE,
                map_prep=PrepareForBattle(),
                children=[
                    BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                    BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_KINYA_PROVINCE, target_map_id=KINYA_PROVINCE),
                    BT.MoveAndKill(KILLSPOT_COORDS),
                ],
            )
        return BT.Succeeder(name="SkipExitToKinya")
    
    return BT.Sequence(
            name="Mesmer Primary Starter Quests Part 2",
            children=[
                BT.Subtree(name="Exit To Kinya If Mesmer",subtree_fn=_exit_to_kinya_if_mesmer,),
                BT.MoveAndKill(KILLSPOT_END_COORDS),
                BT.Subtree(
                    name="Take Quest With Lo Sha",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master(node, "Mesmer", LO_SHA_COORDS,),
                ),
                BT.MoveAndKill(QUEST_KILL_SPOT1_COORDS, Range.Spellcast.value),
                BT.MoveAndKill(CHEST_LOCATION_COORDS, Range.Spellcast.value),
                BT.MoveAndInteractWithGadget(CHEST_LOCATION_COORDS),
                BT.HandleAutoQuest(LO_SHA_COORDS, buttons=[0, 0],),
            ],
        )
    
#region elementalist
def ElementalistPrimaryStarterQuestsPart1() -> BehaviorTree:
    RONSU_COORDS = [(10981.46, -8381.28)]
    KILLSPOT_COORDS = (14418.98, -18023.70)
    BACK_TO_RONSU_COORDS = [(14614.99, -15139.23),(12895.58, -11721.12)] + RONSU_COORDS
    
    def _exit_to_tsumei_if_elementalist(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") == "Elementalist":
            return BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE)
        return BT.Succeeder(name="SkipExitToTsumei")
    
    return BT.Sequence(
            name="Elementalist Primary Starter Quests Part 1",
            children=[
                Pacifist(),
                BT.Subtree(
                    name="Ronsu Intro Quest",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master( node,"Elementalist", RONSU_COORDS, ),
                ),
                Aggressive(),
                BT.MoveAndKill(KILLSPOT_COORDS),
                BT.MoveAndInteractWithGadget(KILLSPOT_COORDS),
                BT.HandleAutoQuest(BACK_TO_RONSU_COORDS, buttons=[0, 0],),
                BT.Subtree(name="Exit To Tsumei If Elementalist",subtree_fn=_exit_to_tsumei_if_elementalist,),
            ],
        )
    
def ElementalistPrimaryStarterQuestsPart2() -> BehaviorTree:
    KAI_YING_COORDS = (15066.79, 7242.23)
    KAI_YING_ENC_STR = "\\x5CC4\\xCCE5\\xCAA0\\x450B"
    KILLSPOT_COORDS = (14787.48, 5764.21)
    
    def _get_to_panjian_if_elementalist(node: BehaviorTree.Node) -> BehaviorTree: 
        if node.blackboard.get("player_primary_profession_name") != "Elementalist":
            return BT.Succeeder(name="SkipGetToPanjian")
        
        return BT.Sequence(
            name="Get To Panjian Peninsula",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_PANJIAN_PENINSULA, target_map_id=PANJIAN_PENINSULA)
            ]
        )
    
    return BT.Sequence(
            name="Elementalist Primary Starter Quests Part 2",
            children=[
                BT.Subtree( name="Get To Panjian If Elementalist",subtree_fn=_get_to_panjian_if_elementalist,),
                BT.Subtree(
                    name="Take Quest From Kai Ying If Elementalist",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master( node,"Elementalist",KAI_YING_COORDS,),
                ),
                BT.MoveAndKill(KILLSPOT_COORDS),
                BT.HandleAutoQuest(pos=None, use_npc_model_or_enc_str=KAI_YING_ENC_STR, buttons=[0, 0],require_quest_marker=True,),    
            ],
        )

#region assassin
def AssassinPrimaryStarterQuestsPart1() -> BehaviorTree:
    TO_JINZO_COORDS = [(17065.27, -7227.24),(15051.48, -1352.39),]
    JINZO_COORDS = (13882.44, 4427.73)
    
    def _approach_jinzo(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") in ("Assassin", "Necromancer"):
            return BT.Move(TO_JINZO_COORDS)
        return BT.Succeeder(name="SkipApproachJinzo")
    
    def _exit_to_tsumei_if_assassin(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") == "Assassin":
            return BT.Sequence(
                name="Exit To Tsumei Village",
                children=[
                    BT.Travel(SHING_JEA_MONASTERY),
                    PrepareForBattle(),
                    Pacifist(),
                    BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                    BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE),
                ]
            )
        return BT.Succeeder(name="SkipExitToTsumei")
    
    return BT.Sequence(
            name="Assassin Primary Starter Quests Part 1",
            children=[
                Pacifist(),
                BT.Subtree(name="Approach Jinzo",subtree_fn=_approach_jinzo, ),
                BT.Subtree(
                    name="Jinzo Intro Quest",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master(node, "Assassin",JINZO_COORDS,),
                ),
                BT.HandleAutoQuest(JINZO_COORDS,buttons=[0]),
                BT.Wait(1000),
                Aggressive(),
                BT.Repeater(name="KillRepeater",repeat_count=4,
                    children=[
                        BT.ClearEnemiesInArea(JINZO_COORDS, Range.Spellcast.value),
                        BT.Wait(2000),
                    ],
                ),
                BT.Wait(1000),
                BT.HandleAutoQuest(JINZO_COORDS, require_quest_marker=True, buttons=[0, 0],),
                BT.Subtree(name="Exit To Tsumei Village",subtree_fn=_exit_to_tsumei_if_assassin,),
            ],
        )
    
def AssassinPrimaryStarterQuestsPart2() -> BehaviorTree:
    PANAKU_COORDS = [(11957.96, 3480.97),(8015.62, -2143.84),(5694.44, -5869.79),(1767.95, -8105.97),(-324.27, -7779.27)]
    PANAKU_END_COORDS = [(1767.95, -8105.97),(-324.27, -7779.27)]
    PANAKU_MODEL_ID = 3350
    FINISH_SCORT_AREA_COORDS = (-3304.27, 1351.91)
    KILLSPOT_COORDS = (-2671.26, 2907.70)
    
    def _get_to_kynya_if_assassin(node: BehaviorTree.Node) -> BehaviorTree: 
        if node.blackboard.get("player_primary_profession_name") != "Assassin":
            return BT.Succeeder(name="SkipGetToKinya")
        
        return BT.Sequence(
            name="Get To Kinya Province",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_KINYA_PROVINCE, target_map_id=KINYA_PROVINCE),
                BT.Move(PANAKU_COORDS),
            ],
        )
    
    return BT.Sequence(
            name="Assassin Primary Starter Quests Part 2",
            children=[
                BT.Subtree(name="Get To Kinya If Assassin",subtree_fn=_get_to_kynya_if_assassin,),
                BT.Move(PANAKU_END_COORDS),
                BT.Subtree(
                    name="Take Quest With Panaku",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master( node,"Assassin",PANAKU_COORDS,),
                ),
                BT.HandleAutoQuest(PANAKU_END_COORDS[1],buttons=[0]),
                BT.FollowModel(
                    PANAKU_MODEL_ID,
                    follow_range=Range.Area.value,
                    exit_by_area=(FINISH_SCORT_AREA_COORDS, Range.Spellcast.value),
                ),
                BT.MoveAndKill(KILLSPOT_COORDS, Range.Spellcast.value),
                BT.Wait(1000),
                BT.HandleAutoQuest(None,
                                   use_npc_model_or_enc_str=PANAKU_MODEL_ID, 
                                   require_quest_marker=True, 
                                   buttons=[0, 0]),
            ],
        )
    
#region ritualist
def RitualistPrimaryStarterQuestsPart1() -> BehaviorTree:
    PROFESSOR_GAI_COORDS = (9037.29, -12521.27)
    KILLSPOT_COORDS = (8566.58, -13654.18)
    
    def _exit_to_tsumei_if_ritualist(node: BehaviorTree.Node) -> BehaviorTree:
        if node.blackboard.get("player_primary_profession_name") in ("Ritualist", "Ranger"):
            return BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE)
        return BT.Succeeder(name="SkipExitToTsumei")
    
    return BT.Sequence(
            name="Ritualist Primary Starter Quests Part 1",
            children=[
                Pacifist(),
                BT.Subtree(
                    name="Professor Gai Intro Quest",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master( node,"Ritualist",PROFESSOR_GAI_COORDS,),
                ),
                BT.HandleAutoQuest(PROFESSOR_GAI_COORDS,buttons=[0]),
                Aggressive(),
                BT.MoveAndKill(KILLSPOT_COORDS, Range.Spellcast.value),
                BT.Repeater(name="KillRepeater",repeat_count=4,
                    children=[
                        BT.ClearEnemiesInArea(KILLSPOT_COORDS, Range.Spellcast.value),
                        BT.Wait(1000),
                    ],
                ),
                BT.HandleAutoQuest(PROFESSOR_GAI_COORDS, require_quest_marker=True, buttons=[0, 0],),
                Pacifist(),
                BT.Subtree(name="Exit To Tsumei If Ritualist",subtree_fn=_exit_to_tsumei_if_ritualist,),
            ],
        )

def RitualistPrimaryStarterQuestsPart2() -> BehaviorTree:
    ANG_THE_EPHIMERAL_COORDS = (-6720.92, 9800.15)
    ANG_THE_EPHIMERAL_ENC_STR = "\\x5CE2\\x9DBC\\x976C\\x7AE9"
    KILLSPOTS_COORDS = [(-6732.93, 10686.14),
                        (-6149.21, 10055.54),
                        (-6990.32, 8779.83),
                        (-7513.96, 7960.66),
                        (-7867.96, 9335.21)]
    
    KILL_POINTS = [BT.Sequence(
                        name=f"KillPoint", 
                        children=[ 
                            BT.MoveAndInteractWithGadget(coord, Range.Spellcast.value),
                            BT.Wait(1000),
                            BT.ClearEnemiesInArea(coord, Range.Spellcast.value), 
                        ])
                    for coord in KILLSPOTS_COORDS]
    
    def _get_to_panjian_if_ritualist(node: BehaviorTree.Node) -> BehaviorTree: 
        if node.blackboard.get("player_primary_profession_name") != "Ritualist":
            return BT.Succeeder(name="SkipGetToPanjian")
        
        return BT.Sequence(
            name="Get To Panjian Peninsula",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_PANJIAN_PENINSULA, target_map_id=PANJIAN_PENINSULA)
            ]
        )
    
    return BT.Sequence(
            name="Ritualist Primary Starter Quests Part 2",
            children=[
                BT.Subtree(name="Get To Panjian If Ritualist",subtree_fn=_get_to_panjian_if_ritualist,),
                BT.Subtree(
                    name="Take Quest From Ang The Ephimeral If Ritualist",
                    subtree_fn=lambda node: _take_quest_for_profession_from_master(node,"Ritualist",ANG_THE_EPHIMERAL_COORDS,),
                ),
                BT.HandleAutoQuest(ANG_THE_EPHIMERAL_COORDS, buttons=[0,],),
                *KILL_POINTS,
                BT.HandleAutoQuest(pos=None, 
                                   use_npc_model_or_enc_str=ANG_THE_EPHIMERAL_ENC_STR, 
                                   require_quest_marker=True, buttons=[0, 0],), 
            ],
        )

def Profession_Specific_QuestsPart1() -> BehaviorTree:
    return BT.GetNodeByProfession(
        WarriorNode=WarriorPrimaryStarterQuestsPart1(),
        RangerNode=RangerPrimaryStarterQuestsPart1(),
        MonkNode=MonkPrimaryStarterQuestsPart1(),
        NecromancerNode=NecromancerPrimaryStarterQuestsPart1(),
        MesmerNode=MesmerPrimaryStarterQuestsPart1(),
        ElementalistNode=ElementalistPrimaryStarterQuestsPart1(),
        AssassinNode=AssassinPrimaryStarterQuestsPart1(),
        RitualistNode=RitualistPrimaryStarterQuestsPart1(),
    )
    
def Profession_Specific_QuestsPart2() -> BehaviorTree:
    return BT.GetNodeByProfession(
        WarriorNode=WarriorPrimaryStarterQuestsPart2(),
        RangerNode=RangerPrimaryStarterQuestsPart2(),
        MonkNode=MonkPrimaryStarterQuestsPart2(),
        NecromancerNode=NecromancerPrimaryStarterQuestsPart2(),
        MesmerNode=MesmerPrimaryStarterQuestsPart2(),
        ElementalistNode=ElementalistPrimaryStarterQuestsPart2(),
        AssassinNode=AssassinPrimaryStarterQuestsPart2(),
        RitualistNode=RitualistPrimaryStarterQuestsPart2(),
    )
    
def An_Audience_WithMasterTogo() -> BehaviorTree:
    return BT.Sequence(
            name="An Audience With Master Togo",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                Pacifist(),
                BT.MoveAndExitMap((-3480, 9460), target_map_name="Linnok Courtyard",),
                BT.HandleAutoQuest(pos=[(-159, 9174), (-92, 9217)]),
                BT.Repeater(name="Take All Dialog Options", repeat_count=7,
                    children=[
                        BT.HandleAutoQuest(pos=[(-92, 9217)], buttons=[0, 0],),
                    ],
                ),
                BT.MoveAndExitMap((-3762, 9471),target_map_id=SHING_JEA_MONASTERY,),
            ],
        )


#region xunlai
def Unlock_Xunlai_Storage() -> BehaviorTree:
    PATH_TO_XUNLAI = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3825.09, 10386.81),]
    XUNLAI_AGENT_COORDS = (-3825.09, 10386.81)
    
    return BT.Sequence(
            name="Unlock Xunlai Storage",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndDialog(PATH_TO_XUNLAI, 0x84),
                BT.DialogAtXY(XUNLAI_AGENT_COORDS, 0x800001),
                BT.DialogAtXY(XUNLAI_AGENT_COORDS, 0x800002),
            ],
        )
    
def DestroyTrash() -> BehaviorTree:
    return BT.Sequence(
            name="Destroy Trash Items",
            children = [
                BT.DestroyItems(TRASH_ITEM_MODELS),
            ]
        )


#region crafting
def BuyAndCraftMonasteryArmor() -> BehaviorTree:
    MATERIAL_MERCHANT_COORDS = [(-10896.94, 10807.54), (-10942.73, 10783.19), (-10614.00, 10996.00),]
    RARE_MATERIAL_MERCHANT_COORDS = (-10589.20, 10745.83)
    ARMOR_CRAFTER_COORDS = [(-10896.94, 10807.54), (-7115.00, 12636.00)]
    WEAPON_CRAFTER_COORDS  = (-8811.74, -15636.16)
    
    return BT.Sequence(
            name="Buy And Craft Monastery Armor",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                BT.EqualizeGold(target_gold=1600),
                BT.MoveAndInteract(MATERIAL_MERCHANT_COORDS),
                BT.BuyMaterialsByProfession(
                    profession_materials=MONASTERY_COMMON_BUY_BY_PROFESSION,
                    rare_trader=False,
                ),
                BT.MoveAndInteract(RARE_MATERIAL_MERCHANT_COORDS),
                BT.BuyMaterialsByProfession(
                    profession_materials=TSUMEI_RARE_BUY_BY_PROFESSION,
                    rare_trader=True,
                ),
                BT.MoveAndInteract(ARMOR_CRAFTER_COORDS),
                BT.CraftItemsByProfession(
                    profession_craft_steps=MONASTERY_ARMOR_CRAFT_BY_PROFESSION,
                    equip_log=False,
                ),
                DestroyTrash(),
                BT.Travel(TSUMEI_VILLAGE),
                BT.MoveAndInteract(WEAPON_CRAFTER_COORDS),
                BT.CraftItemsByProfession(
                    profession_craft_steps=TSUMEI_WEAPON_CRAFT_BY_PROFESSION,
                    equip_log=False,
                ),
            ],
        )



def _talk_with_other_masters(node: BehaviorTree.Node) -> BehaviorTree:
    master_coords = node.blackboard.get("other_master_coords", [])
    
    return BT.Sequence(
        name="Talk With Other Masters",
        map_id_or_name=SHING_JEA_MONASTERY,
        children=[
            BT.HandleAutoQuest(pos=coords, buttons=[0, 0] if index == 0 else [0, 0, 0])
            for index, coords in enumerate(master_coords)
        ],
    )


#region secondaries
def Talk_With_Masters() -> BehaviorTree:
    NEING_THE_TANNER_COORDS = (-9762.71, 9685.96)
    CAPTAIN_ZINGHU_COORDS = (-9786.34, 8348.70)

    def _equip_empty_skillbar(node: BehaviorTree.Node) -> BehaviorTree:
        def _load_empty_skillbar_from_blackboard(inner_node: BehaviorTree.Node) -> BehaviorTree:
            empty_skillbar = inner_node.blackboard.get("empty_skillbar")
            if empty_skillbar is None:
                return BT.Succeeder(name="NoEmptySkillbarToEquip")

            return BT.LoadSkillbar(empty_skillbar)

        return BT.Sequence(
            name="Equip Empty Skillbar",
            children=[
                BT.GetValuesByProfession(
                    profession_values=EMPTY_SKILLBARS,
                    target_key="empty_skillbar",
                ),
                BT.Subtree(
                    name="Load Empty Skillbar",
                    subtree_fn=_load_empty_skillbar_from_blackboard,
                ),
            ],
        )

    return BT.Sequence(
        name="Talk With Masters",
        map_id_or_name=SHING_JEA_MONASTERY,
        map_prep=PrepareForBattle(),
        children=[
            BT.Subtree(name="Equip Empty Skillbar", subtree_fn=_equip_empty_skillbar),
            BT.GetValuesByProfession(profession_values=OTHER_MASTER_COORDS_BY_PROFESSION, target_key="other_master_coords"),
            BT.Subtree(name="Talk With Masters Subtree", subtree_fn=_talk_with_other_masters),
            DestroyTrash(),
            BT.HandleAutoQuest(NEING_THE_TANNER_COORDS),
            BT.HandleAutoQuest(CAPTAIN_ZINGHU_COORDS),
            PrepareForBattle(),
            BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
        ],
    )
    
def FirstSecondaryBlock() -> BehaviorTree:
    return BT.Sequence(
            name="First Secondary Profession Block",
            children=[
                BT.SkipNodeByProfession("Necromancer", NecromancerPrimaryStarterQuestsPart1()),
                BT.SkipNodeByProfession("Assassin", AssassinPrimaryStarterQuestsPart1()),
                BT.SkipNodeByProfession("Warrior", WarriorPrimaryStarterQuestsPart1()),
                BT.SkipNodeByProfession("Monk", MonkPrimaryStarterQuestsPart1()),
                BT.SkipNodeByProfession("Mesmer", MesmerPrimaryStarterQuestsPart1()),
                BT.SkipNodeByProfession("Elementalist", ElementalistPrimaryStarterQuestsPart1()),
                BT.SkipNodeByProfession("Ritualist", RitualistPrimaryStarterQuestsPart1()),
                BT.SkipNodeByProfession("Ranger", RangerPrimaryStarterQuestsPart1()),
            ],
        )

def R_Mo_Me_A_secondaries_and_Appearance_of_the_naga() -> BehaviorTree:
    SISTER_CHOI_JU_COORDS = (-9999.64, -15870.08)
    WULK_ENC_STR = "\\x5D7C\\xE26C\\xE63B\\x5AD5"
    PATH_TO_WULK = [(-14675.84, -3652.20), (-17245.75, -1337.33), (-13281.57, -575.03), (-12287.93, 437.10)]
    PATH_TO_NAGA_KILLSPOT = [(-6239.60, -4249.77),(-15608.21, -6463.72)]
    
    ZHO_COORDS = (9760.99, 5168.66)

    def _escort_complete() -> bool:
        wulk_agent_id = int(RoutinesAgents.GetAgentIDByModelOrEncStr(WULK_ENC_STR) or 0)
        return (
            wulk_agent_id != 0
            and Agent.HasQuest(wulk_agent_id)
            and not Checks.Agents.InDanger(aggro_area=Range.Spirit)
        )
    
    return BT.Sequence(
        name="R/Mo/Me/A Secondaries and Appearance of the Naga",
        map_id_or_name=TSUMEI_VILLAGE,
        map_prep=PrepareForBattle(),
        children=[
            BT.HandleAutoQuest(SISTER_CHOI_JU_COORDS), #appearance of the naga
            BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
            BT.MoveAndKill(PATH_TO_NAGA_KILLSPOT), #kill the naga
            BT.MoveAndKill(PATH_TO_WULK), #wulk Cragfist
            BT.HandleAutoQuest(pos=None, use_npc_model_or_enc_str=WULK_ENC_STR, require_quest_marker=False), #revenge of the yeti
            BT.FollowModel(WULK_ENC_STR, exit_condition=_escort_complete, exit_by_area=((-13717.04, 7714.01), Range.Earshot.value)),
            BT.ClearEnemiesInArea((-13717.04, 7714.01)),
            BT.HandleAutoQuest(pos=None, use_npc_model_or_enc_str=WULK_ENC_STR, require_quest_marker=True), 
            BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_KINYA_PROVINCE, target_map_id=KINYA_PROVINCE),
            BT.Move(ZHO_COORDS),
            BT.SkipNodeByProfession("Ranger", RangerPrimaryStarterQuestsPart2()), 
            BT.SkipNodeByProfession("Monk", MonkPrimaryStarterQuestsPart2()),
            BT.SkipNodeByProfession("Mesmer", MesmerPrimaryStarterQuestsPart2()),
            BT.SkipNodeByProfession("Assassin", AssassinPrimaryStarterQuestsPart2()),
        ],
    )

    
def W_E_Rt_N_and_secondaries() -> BehaviorTree:
    HERDER_TSIYINJU_COORDS = (18180.43, 7276.40)
    CORSAIRS_KILLSPOT_COORDS = (19766.83, 10781.28)
    FARMER_ZINHAO_COORDS =  (12269.25, 5379.94)
    
    return BT.Sequence(
        name="R/Mo/Me/A Secondaries and Appearance of the Naga",
        map_id_or_name=TSUMEI_VILLAGE,
        map_prep=PrepareForBattle(),
        children=[
            BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_PANJIAN_PENINSULA, target_map_id=PANJIAN_PENINSULA),
            BT.SkipNodeByProfession("Warrior", WarriorPrimaryStarterQuestsPart2()), 
            BT.SkipNodeByProfession("Elementalist", ElementalistPrimaryStarterQuestsPart2()),
            #a belt pouch
            BT.HandleAutoQuest(HERDER_TSIYINJU_COORDS),
            BT.MoveAndKill(CORSAIRS_KILLSPOT_COORDS), #kill the bandits for the belt pouch
            BT.HandleAutoQuest(HERDER_TSIYINJU_COORDS),
            BT.HandleAutoQuest(FARMER_ZINHAO_COORDS), #pest control
            BT.SkipNodeByProfession("Ritualist", RitualistPrimaryStarterQuestsPart2()),
            BT.SkipNodeByProfession("Necromancer", NecromancerPrimaryStarterQuestsPart2()),

        ],
    )

def An_Audience_WithMasterTogo_Reward() -> BehaviorTree:
    TOGO_COORDS = (-92, 9217)
    return BT.Sequence(
            name="An Audience With Master Togo Reward",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                BT.Travel(SHING_JEA_MONASTERY),
                BT.HandleAutoQuest((-7446.29, 10364.74)), #pest control
                BT.HandleAutoQuest((-9765.87, 9702.94)), #belt pouch
                BT.EquipInventoryBag(ModelID.Belt_Pouch_Reward.value, Bags.BeltPouch),
                BT.HandleAutoQuest((-9756.65, 8339.55)),
                Pacifist(),
                BT.MoveAndExitMap((-3480, 9460), target_map_name="Linnok Courtyard",),
                BT.HandleAutoQuest(pos=[TOGO_COORDS]),
                BT.HandleAutoQuest(pos=[TOGO_COORDS], buttons=[0],),
                BT.Repeater(
                    name="Take All Dialog Options",
                    repeat_count=6,
                    children=[
                        BT.HandleAutoQuest(pos=[TOGO_COORDS], buttons=[1, 0],),
                    ],
                ),
                BT.HandleAutoQuest(pos=[TOGO_COORDS], buttons=[0],),
                BT.Repeater(
                    name="Cancel Skill Reward Window",
                    repeat_count=4,
                    children=[
                        BT.CancelSkillRewardWindow(),
                    ],
                ),
                BT.MoveAndExitMap((-3762, 9471),target_map_id=SHING_JEA_MONASTERY,),
            ],
        )



def CapturePet_And_to_minister_cho() -> BehaviorTree:
    bot = ensure_botting_tree()
    PET_CAPTURE_COORDS = (13585.15, -10782.06)
    PET_MODEL_ID = 3005
    CHARM_PET_SKILL_ID = 411
    
    togo_coords = (20036.72, -7821.50)
    intro_quest_path = [
        (17065.27, -7227.24),
        (15051.48, -1352.39),
        (10475.55, 7766.41),
        (7315.20, 10209.45),
        (6692.19, 16005.08)   
    ]
    
    return BT.Sequence(
            name="Capture Pet",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.HandleAutoQuest(togo_coords, log=True),
                Pacifist(),
                BT.Move(PET_CAPTURE_COORDS, pause_on_combat=False),
                BT.MoveAndTargetByModelID(PET_MODEL_ID, pause_on_combat=False),
                BT.CastSkillID(CHARM_PET_SKILL_ID),
                BT.Wait(15000),
                BT.HandleQuest(318, intro_quest_path, 0x80000B, mode="skip", success_map_id=MINISTER_CHO_STATE),
                BT.WaitForMapToChange(map_id=MINISTER_CHO_STATE),
                BT.HandleQuest(318, (7884, -10029), 0x813E07, mode="complete"),
            ],
        )

#region old code
def Minister_Chos_Estate_Mission() -> BehaviorTree:
    bot = ensure_botting_tree()
    minister_cho_state_map_id = 214
    ran_musu_gardens_map_id = 251
    return BT.Sequence(
            name="Minister Cho's Estate Mission",
            map_id_or_name=minister_cho_state_map_id,
            map_prep=PrepareForBattle(),
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
            map_prep=PrepareForBattle(),
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
            map_prep=PrepareForBattle(),
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
    

def Extend_Inventory_Space() -> BehaviorTree:
    merchant = (-11866, 11444)
    return BT.Sequence(
            name="Extend Inventory Space",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndBuyMerchantItem(merchant, ModelID.Belt_Pouch.value, quantity=1),
                BT.EquipInventoryBag(ModelID.Belt_Pouch.value, Bags.BeltPouch),
                BT.BuyMerchantItem(ModelID.Bag.value, quantity=1),
                BT.EquipInventoryBag(ModelID.Bag.value, Bags.Bag1),
                BT.BuyMerchantItem(ModelID.Bag.value, quantity=1),
                BT.EquipInventoryBag(ModelID.Bag.value, Bags.Bag2),
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
    FARMER_ZINHAO_COORDS =  (12269.25, 5379.94)
    
    return BT.Sequence(
            name="The Threat Grows",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                BT.HandleAutoQuest((-5157.23, -15496.60)), #togos ultimatum
                BT.HandleAutoQuest((-10791.21, -15900.69)), #cahs crops
                BT.MoveAndExitMap((-11659, -17174), target_map_id=PANJIAN_PENINSULA),
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
                #pest control
                BT.HandleAutoQuest(FARMER_ZINHAO_COORDS),
                #cash crops
                _move_and_kneel((12817.42, 8358.96)),
                _move_and_kneel((17029.94, 7921.00)),
                _move_and_kneel((17039.33, 1927.72)),
                #togos ultimatum
                BT.HandleAutoQuest((-14308.30, -11235.08)),
                BT.Travel(target_map_id=TSUMEI_VILLAGE),
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
        ("Profession Specific Quests Part 1", Profession_Specific_QuestsPart1),
        ("Profession Specific Quests Part 2", Profession_Specific_QuestsPart2),
        ("An Audience With Master Togo", An_Audience_WithMasterTogo),
        ("Unlock Xunlai Storage", Unlock_Xunlai_Storage),
        ("Buy And Craft Monastery Armor", BuyAndCraftMonasteryArmor),
        ("Talk With Masters", Talk_With_Masters),
        ("First Secondary Profession Block", FirstSecondaryBlock),
        ("Appearance of the Naga and R/Mo/Me/A Secondaries", R_Mo_Me_A_secondaries_and_Appearance_of_the_naga),
        ("W/E/Rt/N and Secondaries", W_E_Rt_N_and_secondaries),
        ("An Audience With Master Togo Reward", An_Audience_WithMasterTogo_Reward),
        ("Capture Pet", CapturePet_And_to_minister_cho),
        ("Minister Cho's Estate Mission", Minister_Chos_Estate_Mission),
        ("Attribute Points Quest 1", Attribute_Points_Quest_1),
        ("Warning The Tengu", Warning_The_Tengu),
        ("The Threat Grows - Cash Crops & Togo's Ultimatum", The_Threat_Grows_CashCrops_Togos_Utimatum),
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
            pause_on_combat=True,
            multi_account=False,
            configure_fn=lambda tree: tree.Config.ConfigureUpkeep(
                looting_enabled=LOOTING_ACTIVE,
                restore_isolation_on_stop=True,
                auto_inventory_handler_enabled=False,
                enable_outpost_imp_service=True,
                enable_explorable_imp_service=True,
                heroai_state_logging=False,
                consumable_upkeeps=[
                    ModelID.Candy_Apple.value,
                    ModelID.War_Supplies.value,
                    ModelID.Honeycomb.value,
                    ModelID.Candy_Apple.value,
                    ModelID.War_Supplies.value,
                    ModelID.Honeycomb.value,
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

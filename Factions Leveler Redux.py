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
from Py4GWCoreLib.routines_src.behaviourtrees_src.constants import *


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
        (3, "OACAAAAAAAAAAAAA"),
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

TRASH_ITEM_MODELS: list[int] = [
    STARTER_SWORD_MODEL_ID, #warrior Starter Sword
    STARTER_HAMMER_MODEL_ID, #warrior starter hammer
    STARTER_AXE_MODEL_ID, #warrior starter axe
    
    5819,
    STARTER_DAGGERS,
    STARTER_ELEMENTAL_ROD,
    STARTER_CANE,
    STARTER_HOLY_ROD,
    STARTER_TRUNCHEON,
    STARTER_BOW_MODEL_ID,
    6498,
    
    30853,
    24897,
]


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


def _add_henchmen_from_blackboard(node: BehaviorTree.Node) -> BehaviorTree:
    return BT.AddHenchmanList(node.blackboard["current_map_henchmen"])


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
                bot.Config.Aggressive(),
                BT.LoadSkillbarFromMap(LEVELING_SKILLBAR_MAP),
                BT.LeaveParty(),
                BT.SaveBlackboardValue("current_map_henchmen", _get_henchmen_for_current_map),
                BehaviorTree.SubtreeNode(
                    name="AddHenchmenForCurrentMap",
                    subtree_fn=_add_henchmen_from_blackboard,
                ),
                BT.RestockItemsFromList(restock_list,allow_missing=True,),
            ],
        )

#region routines
def Exit_Monastery_Overlook() -> BehaviorTree:
    MASTER_COORDS_BY_PROFESSION = { 
        "Warrior": (-7039.83, 7325.59),
        "Ranger": (-7714.79, 6727.62),
        "Monk": (-7092.22, 7497.88),
        "Necromancer": (-7101.96, 7125.17),
        "Mesmer": (-7351.34, 7584.09),
        "Elementalist": (-7892.99, 6928.65),
        "Assassin": (-7849.87, 6814.73),
        "Ritualist": (-7785.90, 7335.15),
    }
    
    STARTER_WEAPON_MODEL_IDS = {
        "Warrior": STARTER_SWORD_MODEL_ID,
        "Ranger": STARTER_BOW_MODEL_ID,
        "Monk": STARTER_HOLY_ROD,
        "Necromancer": STARTER_TRUNCHEON,
        "Mesmer": STARTER_CANE,
        "Elementalist": STARTER_ELEMENTAL_ROD,
        "Assassin": STARTER_DAGGERS,
    }

    def _move_to_profession_coords(node: BehaviorTree.Node) -> BehaviorTree:
        return BT.HandleAutoQuest(
            pos=node.blackboard["profession_coords"],
            buttons=[0, 0],
        )
        
    def _equip_starter_weapon_by_profession(node: BehaviorTree.Node) -> BehaviorTree:
        return BT.EquipItemByModelID(node.blackboard["starter_weapon_model_id"])

    LUDO_GREETING_COORDS = (-7048,5817)
    return BT.Sequence(
            name="Exit Monastery Overlook",
            children=[
                BT.HandleAutoQuest(pos=LUDO_GREETING_COORDS, buttons=[0, 0, 1, 0, 0]),
                BT.WaitForMapLoad(map_id=SHING_JEA_MONASTERY),
                BT.GetValuesByProfession(
                    profession_values=MASTER_COORDS_BY_PROFESSION,
                    target_key="profession_coords",
                ),
                BehaviorTree.SubtreeNode(
                    name="MoveToProfessionCoords",
                    subtree_fn=_move_to_profession_coords,
                ),
                BT.GetValuesByProfession(
                    profession_values=STARTER_WEAPON_MODEL_IDS,
                    target_key="starter_weapon_model_id",
                ),
                BehaviorTree.SubtreeNode(
                    name="EquipWeaponByProfession",
                    subtree_fn=_equip_starter_weapon_by_profession,
                ),
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
    
#region profession specific quests
def WarriorPrimaryStarterQuestsPart1() -> BehaviorTree:
    bot = ensure_botting_tree()
    TO_TALON_SILVERWING_COORDS = [(17065.27, -7227.24),(15051.48, -1352.39),(11398.17, 7258.22)]
    TALON_SILVERWING_COORDS = (11398.17, 7258.22)
    return BT.Sequence(
            name="Warrior Primary Starter Quests Part 1",
            children=[
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(TO_TALON_SILVERWING_COORDS,buttons=[0, 0]),
                BT.EquipItemByModelID(STARTER_AXE_MODEL_ID),
                bot.Config.Aggressive(),
                BT.ClearEnemiesInArea(TALON_SILVERWING_COORDS, Range.Longbow.value),
                BT.HandleAutoQuest(TALON_SILVERWING_COORDS),
                BT.ClearEnemiesInArea(TALON_SILVERWING_COORDS, Range.Spellcast.value),
                BT.Wait(1000),
                BT.HandleAutoQuest(TALON_SILVERWING_COORDS, require_quest_marker=True, buttons=[0, 0],),
                BT.Travel(SHING_JEA_MONASTERY),
                PrepareForBattle(),
                bot.Config.Pacifist(),
                BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE),
            ],
        )

def WarriorPrimaryStarterQuestsPart2() -> BehaviorTree:
    WENG_GAH_COORDS = (6678.91, 6318.28)
    KILLSPOT_COORDS = (10727.69, 10571.04)
    return BT.Sequence(
            name="Warrior Primary Starter Quests Part 2",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_PANJIAN_PENINSULA, target_map_id=PANJIAN_PENINSULA),
                #track down Weng Gah
                BT.HandleAutoQuest(WENG_GAH_COORDS, buttons=[0,0]),
                BT.MoveAndKill(KILLSPOT_COORDS),
                BT.HandleAutoQuest(WENG_GAH_COORDS, buttons=[0,0]),
            ],
        )

def RangerPrimaryStarterQuestsPart1() -> BehaviorTree:
    bot = ensure_botting_tree()
    RABBIT_PT1_COORDS = (9583.81, -5396.87)
    RABBIT_PT2_COORDS = (7113.02, -8898.87)
    RABBIT_PT3_COORDS = [(6339.18, -10887.55), (4371.29, -12062.85), (2083.06, -11528.21)]
    SUJUN_COORDS = [(17065.27, -7227.24),(5153.02, -4831.28)]
    SUJUN_ENC_STR = "\\x5CD9\\xA792\\xB5D7\\x67C6"
    
    return BT.Sequence(
            name="Ranger Primary Starter Quests Part 1",
            children=[
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(pos=SUJUN_COORDS, buttons=[0, 0]),
                BT.HandleAutoQuest(pos=SUJUN_COORDS[1]),
                bot.Config.Aggressive(),
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
    
    return BT.Sequence(
            name="Ranger Primary Starter Quests Part 2",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                #track down zho
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_KINYA_PROVINCE, target_map_id=KINYA_PROVINCE),
                BT.HandleAutoQuest(ZHO_COORDS, buttons=[0, 0],),
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
    
def MonkPrimaryStarterQuestsPart1() -> BehaviorTree:
    bot = ensure_botting_tree()
    SISTER_TAI_COORDS = [(17065.27, -7227.24),(9445.05, 3657.00)]
    KILLSPOT_COORDS = (9969.57, 2771.42)
    return BT.Sequence(
            name="Monk Primary Starter Quests Part 1",
            children=[
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(pos=SISTER_TAI_COORDS,
                                   buttons=[0, 0]),
                BT.HandleAutoQuest(pos=SISTER_TAI_COORDS[1],),
                bot.Config.Aggressive(),
                BT.MoveAndKill(KILLSPOT_COORDS, Range.Spellcast.value),
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(pos=SISTER_TAI_COORDS[1],buttons=[0, 0]),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE),
            ],
        )
    
def MonkPrimaryStarterQuestsPart2() -> BehaviorTree:
    BROTHER_PE_WAN_COORDS = (4726.45, -2728.68)
    INGREDIENT1_COORDS = (6608.74, 4559.66)
    INGREDIENT2_COORDS = (9602.88, 12303.18)
    return BT.Sequence(
            name="Monk Primary Starter Quests Part 2",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_KINYA_PROVINCE, target_map_id=KINYA_PROVINCE),
                #track down brother pe wan
                BT.HandleAutoQuest(BROTHER_PE_WAN_COORDS,buttons=[0, 0]),
                BT.MoveAndInteractWithGadget(INGREDIENT1_COORDS),
                BT.MoveAndInteractWithGadget(INGREDIENT2_COORDS),
                BT.HandleAutoQuest(BROTHER_PE_WAN_COORDS,buttons=[0, 0]),
            ],
        )
    
def NecromancerPrimaryStarterQuestsPart1() -> BehaviorTree:
    RENG_KU_COORDS = [(17065.27, -7227.24),(15051.48, -1352.39),(16265.57, 3143.39)]
    RENG_KU_REWARD_COORDS = (16268.68, 3136.99)
    KILLSPOT_COORDS = (20268.91, 8145.42)
    bot = ensure_botting_tree()
    return BT.Sequence(
            name="Necromancer Primary Starter Quests Part 1",
            children=[
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(RENG_KU_COORDS,buttons=[0, 0],),
                bot.Config.Aggressive(),
                BT.MoveAndKill(KILLSPOT_COORDS),
                BT.Repeater(
                    name="KillRepeater",
                    repeat_count=4,
                    children=[
                        BT.ClearEnemiesInArea(KILLSPOT_COORDS, Range.Spellcast.value),
                        BT.Wait(2000),
                    ],
                ),
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(RENG_KU_REWARD_COORDS, buttons=[0,0]),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE),
            ],
        )
    
def NecromancerPrimaryStarterQuestsPart2() -> BehaviorTree:
    SU_COORDS = (1959.98, -8569.83)
    SU_ENC_STR = "\\x5CB4\\xA81D\\x9494\\x30F3"
    KILLSPOTS_COORDS = [(5934.45, -12796.59),
                        (11069.31, -13898.07),
                        (12615.04, -10692.58),
                        (9007.76, -9230.19)]
    
    KILL_POINTS = [BT.MoveAndKill(coord, Range.Spellcast.value) for coord in KILLSPOTS_COORDS]
    
    return BT.Sequence(
            name="Necromancer Primary Starter Quests Part 2",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_PANJIAN_PENINSULA, target_map_id=PANJIAN_PENINSULA),
                BT.HandleAutoQuest(SU_COORDS, buttons=[0, 0],),
                BT.HandleAutoQuest(SU_COORDS, buttons=[0,],),
                *KILL_POINTS,
                BT.HandleAutoQuest(pos=None, 
                                   use_npc_model_or_enc_str=SU_ENC_STR, 
                                   require_quest_marker=True, buttons=[0, 0],), 
            ],
        )

def MesmerPrimaryStarterQuestsPart1() -> BehaviorTree:
    bot = ensure_botting_tree()
    MEI_LING_COORDS = [(17065.27, -7227.24),(6805.08, -1273.33)]
    KILLSPOT_COORDS = (-8735.46, 3582.86)
    OVER_THE_BRIDGE_COORDS = (-7333.20, 6846.77)
    TO_TSSUMEI_VILLAGE_COORDS = [(6240.77, -5034.47), (-5.33, -10856.58)] + FROM_SUNQUA_VALE_TO_TSUMEI_VILLAGE
    return BT.Sequence(
            name="Mesmer Primary Starter Quests Part 1",
            children=[
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(MEI_LING_COORDS, buttons=[0, 0]),
                bot.Config.Aggressive(),
                BT.Move(KILLSPOT_COORDS),
                BT.MoveDirect(OVER_THE_BRIDGE_COORDS),
                BT.HandleAutoQuest(MEI_LING_COORDS[1], buttons=[0, 0],),
                BT.MoveAndExitMap(TO_TSSUMEI_VILLAGE_COORDS, target_map_id=TSUMEI_VILLAGE),
            ],
        )
    
def MesmerPrimaryStarterQuestsPart2() -> BehaviorTree:
    KILLSPOT_COORDS = [(11957.96, 3480.97),(8015.62, -2143.84),(6868.74, -8670.04),(4061.85, -13737.38)]
    LO_SHA_COORDS = (5362.32, -13625.09)
    
    QUEST_KILL_SPOT1_COORDS = (9501.89, -10770.79)
    CHEST_LOCATION_COORDS = (11039.42, -13346.81)
    
    
    return BT.Sequence(
            name="Mesmer Primary Starter Quests Part 2",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                #track down Lo Sha
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_KINYA_PROVINCE, target_map_id=KINYA_PROVINCE),
                BT.MoveAndKill(KILLSPOT_COORDS),
                BT.HandleAutoQuest(LO_SHA_COORDS, buttons=[0, 0],),
                BT.MoveAndKill(QUEST_KILL_SPOT1_COORDS, Range.Spellcast.value),
                BT.MoveAndKill(CHEST_LOCATION_COORDS, Range.Spellcast.value),
                BT.MoveAndInteractWithGadget(CHEST_LOCATION_COORDS),
                BT.HandleAutoQuest(LO_SHA_COORDS, buttons=[0, 0],),
            ],
        )
    
def ElementalistPrimaryStarterQuestsPart1() -> BehaviorTree:
    bot = ensure_botting_tree()
    RONSU_COORDS = [(10981.46, -8381.28)]
    KILLSPOT_COORDS = (14418.98, -18023.70)
    BACK_TO_RONSU_COORDS = [(14614.99, -15139.23),(12895.58, -11721.12)] + RONSU_COORDS
    return BT.Sequence(
            name="Elementalist Primary Starter Quests Part 1",
            children=[
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(RONSU_COORDS, buttons=[0, 0]),
                bot.Config.Aggressive(),
                BT.MoveAndKill(KILLSPOT_COORDS),
                BT.MoveAndInteractWithGadget(KILLSPOT_COORDS),
                BT.HandleAutoQuest(BACK_TO_RONSU_COORDS, buttons=[0, 0],),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE),
            ],
        )
    
def ElementalistPrimaryStarterQuestsPart2() -> BehaviorTree:
    KAI_YING_COORDS = (15066.79, 7242.23)
    KAI_YING_ENC_STR = "\\x5CC4\\xCCE5\\xCAA0\\x450B"
    KILLSPOT_COORDS = (14787.48, 5764.21)
    return BT.Sequence(
            name="Elementalist Primary Starter Quests Part 2",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_PANJIAN_PENINSULA, target_map_id=PANJIAN_PENINSULA),
                #track down Kai Ying
                BT.HandleAutoQuest(KAI_YING_COORDS, buttons=[0,0]),
                BT.MoveAndKill(KILLSPOT_COORDS),
                BT.HandleAutoQuest(pos=None, use_npc_model_or_enc_str=KAI_YING_ENC_STR, buttons=[0, 0],require_quest_marker=True,),    
            ],
        )

def AssassinPrimaryStarterQuestsPart1() -> BehaviorTree:
    bot = ensure_botting_tree()
    TO_JINZO_COORDS = [(17065.27, -7227.24),(15051.48, -1352.39),(13890.21, 4449.79)]
    return BT.Sequence(
            name="Assassin Primary Starter Quests Part 1",
            children=[
                bot.Config.Pacifist(),
                BT.HandleAutoQuest(TO_JINZO_COORDS,buttons=[0, 0]),
                BT.HandleAutoQuest(TO_JINZO_COORDS[2],buttons=[0]),
                bot.Config.Aggressive(),
                BT.Repeater(
                    name="KillRepeater",
                    repeat_count=4,
                    children=[
                        BT.ClearEnemiesInArea(TO_JINZO_COORDS[2], Range.Spellcast.value),
                        BT.Wait(2000),
                    ],
                ),
                BT.HandleAutoQuest(TO_JINZO_COORDS[2], require_quest_marker=True, buttons=[0, 0],),
                BT.Travel(SHING_JEA_MONASTERY),
                PrepareForBattle(),
                bot.Config.Pacifist(),
                BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE),
            ],
        )
    
def AssassinPrimaryStarterQuestsPart2() -> BehaviorTree:
    PANAKU_COORDS = [(11957.96, 3480.97),(8015.62, -2143.84),(5694.44, -5869.79),(1767.95, -8105.97),(-324.27, -7779.27)]
    PANAKU_MODEL_ID = 3350
    FINISH_SCORT_AREA_COORDS = (-3304.27, 1351.91)
    KILLSPOT_COORDS = (-2671.26, 2907.70)
    return BT.Sequence(
            name="Assassin Primary Starter Quests Part 2",
            map_id_or_name=TSUMEI_VILLAGE,
            map_prep=PrepareForBattle(),
            children=[
                BT.MoveAndExitMap(FROM_TSUMEI_VILLAGE_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.MoveAndExitMap(FROM_SUNQUA_VALE_TO_KINYA_PROVINCE, target_map_id=KINYA_PROVINCE),
                #track down Panaku
                BT.HandleAutoQuest(PANAKU_COORDS,buttons=[0, 0]),
                BT.HandleAutoQuest(PANAKU_COORDS[4],buttons=[0]),
                BT.FollowModel(
                    PANAKU_MODEL_ID,
                    follow_range=Range.Area.value,
                    exit_by_area=(FINISH_SCORT_AREA_COORDS, Range.Spellcast.value),
                ),
                BT.MoveAndKill(KILLSPOT_COORDS, Range.Spellcast.value),
                BT.HandleAutoQuest(None,
                                   use_npc_model_or_enc_str=PANAKU_MODEL_ID, 
                                   require_quest_marker=True, 
                                   buttons=[0, 0]),
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
    )
    
def An_Audience_WithMasterTogo() -> BehaviorTree:
    bot = ensure_botting_tree()
    
    secondary_button_for_profession = {
        "Warrior": 5,
        "Ranger": 1,
        "Monk": 5,
        "Necromancer": 5,
        "Mesmer": 6,
        "Elementalist": 5,
    }

    def _profession_button_dialog(node: BehaviorTree.Node) -> BehaviorTree:
        return BT.HandleAutoQuest(
            pos=[(-159, 9174), (-92, 9217)],
            buttons=[node.blackboard["audience_with_master_togo_button"], 0],
        )
    
    return BT.Sequence(
            name="An Audience With Master Togo",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
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
                BT.MoveAndExitMap((-3762, 9471),target_map_id=SHING_JEA_MONASTERY,),
            ],
        )
     
    

def Unlock_Xunlai_Storage() -> BehaviorTree:
    path_to_xunlai = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3825.09, 10386.81),]
    xunlai_agent_coords = (-3825.09, 10386.81)
    
    return BT.Sequence(
            name="Unlock Xunlai Storage",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
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


def _build_early_armor_materials(
    armor_data: list[tuple[int, list[int], list[int]]],
) -> list[tuple[int, int]]:
    totals_by_model: dict[int, int] = {}

    for _, material_models, material_quantities in armor_data:
        for model_id, quantity in zip(material_models, material_quantities):
            totals_by_model[model_id] = totals_by_model.get(model_id, 0) + int(quantity)

    return [
        (model_id, max(1, math.ceil(total_quantity / 10)))
        for model_id, total_quantity in totals_by_model.items()
        if total_quantity > 0
    ]


EARLY_ARMOR_MATERIALS_BY_PROFESSION: dict[str, list[tuple[int, int]]] = {
    profession: _build_early_armor_materials(armor_data)
    for profession, armor_data in MONASTERY_ARMOR_DATA.items()
}

STARTER_AND_TRASH_ITEMS_BY_PROFESSION: dict[str, list[int]] = {
    profession: list(starter_armor + TRASH_ITEM_MODELS)
    for profession, starter_armor in STARTER_ARMOR_MODELS.items()
}


def _handle_unlock_secondary_profession(node: BehaviorTree.Node) -> BehaviorTree:
    return BT.HandleQuest(
        317,
        [(-159, 9174), (-92, 9217)],
        node.blackboard["unlock_secondary_dialog"],
        mode="accept",
    )


def _buy_early_armor_materials(node: BehaviorTree.Node) -> BehaviorTree:
    return BT.BuyMaterialsFromList(node.blackboard["early_armor_materials"])


def _craft_monastery_armor_from_blackboard(node: BehaviorTree.Node) -> BehaviorTree:
    craft_nodes = []

    for item_id, mats, qtys in node.blackboard["monastery_armor_data"]:
        craft_nodes.append(BT.Node(BT.CraftItem(output_model_id=item_id, cost=20, trade_model_ids=mats, quantity_list=qtys)))
        craft_nodes.append(BT.Node(BT.EquipItemByModelID(item_id)))

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Craft And Equip Armor",
            children=craft_nodes,
        )
    )


def _destroy_starter_and_trash_items(node: BehaviorTree.Node) -> BehaviorTree:
    return BT.DestroyItems(node.blackboard["starter_and_trash_items"])


def Unlock_Secondary_Profession() -> BehaviorTree:
    bot = ensure_botting_tree()
    unlock_dialog_by_profession = {
        "Mesmer": 0x813D08,
        "Warrior": 0x813D0E,
    }
    return BT.Sequence(
            name="Unlock Secondary Profession",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                bot.Config.Pacifist(),
                BT.MoveAndExitMap((-3480, 9460), target_map_name="Linnok Courtyard",),
                BT.GetValuesByProfession(
                    profession_values=unlock_dialog_by_profession,
                    target_key="unlock_secondary_dialog",
                ),
                BehaviorTree.SubtreeNode(
                    name="UnlockSecondaryProfessionDialog",
                    subtree_fn=_handle_unlock_secondary_profession,
                ),
                BT.HandleQuest(317, (-92, 9217), 0x813D07, mode="complete", cancel_skill_reward_window=True),
                BT.HandleQuest(318, (-92, 9217), 0x813E01),
                BT.MoveAndExitMap((-3762, 9471),target_map_id=SHING_JEA_MONASTERY,),
            ],
        )
    
    
def Craft_Weapon() -> BehaviorTree:
    path_to_materials_merchant = [(-10896.94, 10807.54), (-10942.73, 10783.19), (-10614.00, 10996.00),]
    path_to_weapon_crafter = [(-10896.94, 10807.54), (-6519.00, 12335.00)]
    longbow_model_id = 11641
    
    return BT.Sequence(
            name="Craft Weapon",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                BT.EqualizeGold(target_gold=5000),
                BT.MoveAndBuyMaterials(path_to_materials_merchant, ModelID.Wood_Plank.value, batches=1),
                BT.GetValuesByProfession(
                    profession_values=EARLY_ARMOR_MATERIALS_BY_PROFESSION,
                    target_key="early_armor_materials",
                ),
                BehaviorTree.SubtreeNode(
                    name="BuyEarlyArmorMaterials",
                    subtree_fn=_buy_early_armor_materials,
                ),
                BT.MoveAndCraftItem(pos=path_to_weapon_crafter, output_model_id=longbow_model_id,cost=100,trade_model_ids=[ModelID.Wood_Plank.value],quantity_list=[5],),
                BT.EquipItemByModelID(longbow_model_id),
            ],
        )

def Craft_Monastery_Armor() -> BehaviorTree:
    armor_crafter = (-7115.00, 12636.00)
    return BT.Sequence(
            name="Craft Monastery Armor",
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children = [
                BT.MoveAndInteract(armor_crafter),
                BT.GetValuesByProfession(
                    profession_values=MONASTERY_ARMOR_DATA,
                    target_key="monastery_armor_data",
                ),
                BehaviorTree.SubtreeNode(
                    name="CraftMonasteryArmorFromBlackboard",
                    subtree_fn=_craft_monastery_armor_from_blackboard,
                ),
                BT.GetValuesByProfession(
                    profession_values=STARTER_AND_TRASH_ITEMS_BY_PROFESSION,
                    target_key="starter_and_trash_items",
                ),
                BehaviorTree.SubtreeNode(
                    name="DestroyStarterAndTrashItems",
                    subtree_fn=_destroy_starter_and_trash_items,
                ),
            ]
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
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                ensure_botting_tree().Config.Pacifist(),
                BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
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
            map_id_or_name=SHING_JEA_MONASTERY,
            map_prep=PrepareForBattle(),
            children=[
                PrepareForBattle(),
                bot.Config.Pacifist(),
                BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_SUNQUA_VALE, target_map_id=SUNQUA_VALE),
                BT.MoveAndExitMap(FROM_SHING_JEA_MONASTERY_TO_TSUMEI_VILLAGE, target_map_id=TSUMEI_VILLAGE),
                PrepareForBattle(),
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

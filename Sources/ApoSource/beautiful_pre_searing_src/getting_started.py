from email.mime import message
from typing import Callable

from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.routines_src.behaviourtrees_src.constants import *

from Sources.ApoSource.ApoBottingLib import wrappers as BT
from .globals import *
from .helpers import *


def Sequence_001_Common() -> BehaviorTree:
    return BT.Sequence(
        name="Starting common sequence",
        map_id_or_name=ASCALON_CITY_PRESEARING,
        children=[
            LogMessage("Starting Absolute Pre-Searing"),
            LogMessage("Taking Quest with Town Crier"),
            BT.HandleAutoQuest(TOWN_CRYER_COORDS),
            LogMessage("Taking Quest with Sir Tydius"),
            BT.HandleAutoQuest(SIR_TYDIUS_COORDS, buttons=[0, 0]),
            LogMessage("Exiting map and moving to Lakeside County"),
            BT.MoveAndExitMap(EXIT_ASCALON_CITY_COORDS, target_map_id=LAKESIDE_COUNTY_MAP_ID),
        ],
    )

def Warrior_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4915.27, -2893.53)
    return BT.Sequence(
        name="Warrior 001 sequence",
        children=[
            LogMessage("Taking Quest with Van the Warrior"),
            BT.HandleAutoQuest(VAN_THE_WARRIOR_COORDS, buttons=[0, 0]),
            LogMessage("Moving to Skale killing spot"),
            BT.MoveAndKill(SKALE_KILLSPOT_COORDS, clear_area_radius=CLEAR_ENEMIES_AREA_RADIUS),
            LogMessage("area is clear, moving back to Van the Warrior"),
            BT.HandleAutoQuest(VAN_THE_WARRIOR_COORDS),
        ],
    )


def Ranger_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(5702.27, -4308.52)

    return BT.Sequence(
        name="Ranger 001 sequence",
        children=[
            LogMessage("Taking Quest with Artemis the Ranger"),
            BT.HandleAutoQuest(ARTEMIS_THE_RANGER_COORDS, buttons=[0, 0]),
            LogMessage("Moving to Skale killing spot"),
            BT.MoveAndKill(SKALE_KILLSPOT_COORDS, clear_area_radius=CLEAR_ENEMIES_AREA_RADIUS),
            LogMessage("area is clear, moving back to Artemis the Ranger"),
            BT.HandleAutoQuest(ARTEMIS_THE_RANGER_COORDS),
        ],
    )

def Monk_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4915.27, -2893.53)
    
    return BT.Sequence(
        name="Monk 001 sequence",
        children=[
            LogMessage("Returning to Cigio the Monk"),
            BT.HandleAutoQuest(CIGIO_THE_MONK_COORDS, buttons=[0, 0]),
            LogMessage("Moving to Skale killing spot"),
            BT.MoveAndKill(SKALE_KILLSPOT_COORDS, clear_area_radius=CLEAR_ENEMIES_AREA_RADIUS),
            LogMessage("area is clear, moving to Gwen"),
            BT.MoveAndInteract(LOST_GWEN_COORDS,target_distance=Range.Area.value),
            LogMessage("moving back to Cigio the Monk"),
            BT.HandleAutoQuest(CIGIO_THE_MONK_COORDS),
        ],
    )

def Necromancer_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4583.08, 726.40)
    
    return BT.Sequence(
        name="Necromancer 001 sequence",
        children=[
            LogMessage("Taking Quest with Verata the Necromancer"),
            BT.HandleAutoQuest(VERATA_THE_NECROMANCER_COORDS, buttons=[0, 0]),
            LogMessage("Moving to Skale killing spot"),
            BT.MoveAndKill(SKALE_KILLSPOT_COORDS, clear_area_radius=CLEAR_ENEMIES_AREA_RADIUS),
            LogMessage("Waiting for Verata to finish Casting"),
            BT.HandleAutoQuest(pos=None, use_npc_model_or_enc_str=VERATA_THE_NECROMANCER_ENC_STRING,require_quest_marker=True),
        ],
    )


def Mesmer_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4583.08, 726.40)

    return BT.Sequence(
        name="Mesmer 001 sequence",
        children=[
            LogMessage("Taking Quest with Sebedoh the Mesmer"),
            BT.HandleAutoQuest(SEBEDOH_THE_MESMER_COORDS, buttons=[0, 0]),
            LogMessage("Moving to Skale killing spot"),
            BT.MoveAndKill(SKALE_KILLSPOT_COORDS, clear_area_radius=CLEAR_ENEMIES_AREA_RADIUS),
            LogMessage("area is clear, moving back to Sebedoh the Mesmer"),
            BT.HandleAutoQuest(SEBEDOH_THE_MESMER_COORDS),
        ],
    )

def Elementalist_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4915.27, -2893.53)
    CLEANUP_MODEL_IDS: tuple[int, ...] = (ModelID.Shimmering_Scale.value,)

    return BT.Sequence(
        name="Elementalist 001 sequence",
        children=[
            LogMessage("Taking Quest with Howland the Elementalist"),
            BT.HandleAutoQuest(HOWLAND_THE_ELEMENTALIST_COORDS, buttons=[0, 0]),
            LogMessage("Moving to Skale killing spot"),
            BT.MoveAndKill(SKALE_KILLSPOT_COORDS, clear_area_radius=CLEAR_ENEMIES_AREA_RADIUS),
            LogMessage("area is clear, moving back to Howland the Elementalist"),
            BT.HandleAutoQuest(HOWLAND_THE_ELEMENTALIST_COORDS),
            LogMessage("Cleaning up remaining quest items"),
            BT.DestroyItems(model_ids=list(CLEANUP_MODEL_IDS)),
        ],
    )



def Profession_Specific_Quest_001_Sequence() -> BehaviorTree:
    return BT.GetNodeByProfession(
        WarriorNode=Warrior_001_Sequence(),
        RangerNode=Ranger_001_Sequence(),
        MonkNode=Monk_001_Sequence(),
        NecromancerNode=Necromancer_001_Sequence(),
        MesmerNode=Mesmer_001_Sequence(),
        ElementalistNode=Elementalist_001_Sequence(),
    )

def Sequence_002_Common() -> BehaviorTree: 
    HAVERSDAN_WAIT_MS: int = 18000

    tree = BehaviorTree.SequenceNode(
        name="Starting common sequence",
        children=[
            LogMessage("Waiting for Haversdan to arrive"),
            BT.Move(WAIT_FOR_HAVERSDAN_COORDS),
            BT.Wait(duration_ms=HAVERSDAN_WAIT_MS, log=True),
            LogMessage("Moving to Haversdan"),
            BT.HandleAutoQuest(HAVERSDAN_COORDS),
            LogMessage("Moving to Ashford Devona"),
            BT.HandleAutoQuest(DEVONA_COORDS, buttons=[0, 0]),
            LogMessage("Moving to Ashford Abbey"),
            BT.MoveAndExitMap(GO_TO_ASHFORD_ABBEY_COORDS, target_map_id=ASHFORD_ABBEY_MAP_ID),
            LogMessage("Moving to Meerak"),
            BT.HandleAutoQuest(MEERAK_COORDS),
            LogMessage("Traveling to Ascalon City to turn in quests"),
            BT.Travel(ASCALON_CITY_MAP_ID),
            LogMessage("Turning in quests to Amin Saberlin"),
            BT.HandleAutoQuest(AMIN_SABERLIN_COORDS, buttons=[0, 0]),
            LogMessage("Routines complete"),
        ],
    )
    return BehaviorTree(tree)



def GetGettingStartedSequence(print_to_console: bool = True) -> list[tuple[str, Callable[[], BehaviorTree]]]:
    global MODULE_NAME, PRINT_TO_CONSOLE
    MODULE_NAME = "GettingStartedSequence"
    PRINT_TO_CONSOLE = print_to_console
    return [
        ("Sequence_001_Common", lambda: Sequence_001_Common()),
        ("Profession_Specific_Quest_001_Sequence", lambda: Profession_Specific_Quest_001_Sequence()),
        ("Sequence_002_Common", lambda: Sequence_002_Common()),
    ]

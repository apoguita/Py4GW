from email.mime import message
from typing import Callable

from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.enums_src.Model_enums import ModelID

from Sources.ApoSource.ApoBottingLib import wrappers as BT
from .globals import *
from .helpers import *


def Sequence_001_Common() -> BehaviorTree:
    tree = BehaviorTree.SequenceNode(
        name="Starting common sequence",
        children=[
            LogMessage("Starting Absolute Pre-Searing"),
            LogMessage("Taking Quest with Town Crier"),
            BT.MoveAndAutoDialog(TOWN_CRYER_COORDS),
            LogMessage("Taking Quest with Sir Tydius"),
            BT.MoveAndAutoDialog(SIR_TYDIUS_COORDS),
            BT.AutoDialog(),
            LogMessage("Exiting map and moving to Lakeside County"),
            BT.Move(EXIT_ASCALON_CITY_COORDS),
            BT.WaitForMapLoad(LAKESIDE_COUNTY_MAP_ID),
        ],
    )
    return BehaviorTree(tree)

def Warrior_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4915.27, -2893.53)
    tree = BehaviorTree.SequenceNode(
        name="Warrior 001 sequence",
        children=[
            LogMessage("Taking Quest with Van the Warrior"),
            BT.MoveAndAutoDialog(VAN_THE_WARRIOR_COORDS),
            BT.AutoDialog(),
            LogMessage("Moving to Skale killing spot"),
            BT.Move(SKALE_KILLSPOT_COORDS),
            LogMessage("Arrived to Skale killing spot."),
            BT.ClearEnemiesInArea(pos=SKALE_KILLSPOT_COORDS,radius=CLEAR_ENEMIES_AREA_RADIUS,),
            LogMessage("area is clear, moving back to Van the Warrior"),
            BT.MoveAndAutoDialog(VAN_THE_WARRIOR_COORDS),
        ],
    )
    return BehaviorTree(tree)


def Ranger_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(5702.27, -4308.52)

    tree = BehaviorTree.SequenceNode(
        name="Ranger 001 sequence",
        children=[
            LogMessage("Taking Quest with Artemis the Ranger"),
            BT.MoveAndAutoDialog(ARTEMIS_THE_RANGER_COORDS),
            BT.AutoDialog(),
            LogMessage("Moving to Skale killing spot"),
            BT.Move(SKALE_KILLSPOT_COORDS),
            LogMessage("Arrived to Skale killing spot."),
            BT.ClearEnemiesInArea(pos=SKALE_KILLSPOT_COORDS,radius=CLEAR_ENEMIES_AREA_RADIUS,),
            LogMessage("area is clear, moving back to Artemis the Ranger"),
            BT.MoveAndAutoDialog(ARTEMIS_THE_RANGER_COORDS),
        ],
    )
    return BehaviorTree(tree)

def Monk_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4915.27, -2893.53)
    
    tree = BehaviorTree.SequenceNode(
        name="Monk 001 sequence",
        children=[
            LogMessage("Returning to Cigio the Monk"),
            BT.MoveAndAutoDialog(CIGIO_THE_MONK_COORDS),
            BT.AutoDialog(),
            LogMessage("Moving to Skale killing spot"),
            BT.Move(SKALE_KILLSPOT_COORDS),
            LogMessage("Arrived to Skale killing spot."),
            BT.ClearEnemiesInArea(pos=SKALE_KILLSPOT_COORDS,radius=CLEAR_ENEMIES_AREA_RADIUS,),
            LogMessage("area is clear, moving to Gwen"),
            BT.MoveAndInteract(LOST_GWEN_COORDS,target_distance=Range.Area.value),
            LogMessage("moving back to Cigio the Monk"),
            BT.MoveAndAutoDialog(CIGIO_THE_MONK_COORDS),
        ],
    )
    return BehaviorTree(tree)

def Necromancer_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4583.08, 726.40)
    
    tree = BehaviorTree.SequenceNode(
        name="Necromancer 001 sequence",
        children=[
            LogMessage("Taking Quest with Verata the Necromancer"),
            BT.MoveAndAutoDialog(VERATA_THE_NECROMANCER_COORDS),
            BT.AutoDialog(),
            LogMessage("Moving to Skale killing spot"),
            BT.Move(SKALE_KILLSPOT_COORDS),
            LogMessage("Arrived to Skale killing spot."),
            BT.ClearEnemiesInArea(pos=SKALE_KILLSPOT_COORDS, radius=CLEAR_ENEMIES_AREA_RADIUS),
            LogMessage("Waiting for Verata to finish Casting"),
            BT.Wait(4000),
            BT.MoveAndAutoDialogByModelID(modelID_or_encStr=VERATA_THE_NECROMANCER_ENC_STRING,
                button_number=0,
            ),
        ],
    )
    return BehaviorTree(tree)


def Mesmer_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4583.08, 726.40)

    tree = BehaviorTree.SequenceNode(
        name="Mesmer 001 sequence",
        children=[
            LogMessage("Taking Quest with Sebedoh the Mesmer"),
            BT.MoveAndAutoDialog(SEBEDOH_THE_MESMER_COORDS),
            BT.AutoDialog(),
            LogMessage("Moving to Skale killing spot"),
            BT.Move(SKALE_KILLSPOT_COORDS),
            LogMessage("Arrived to Skale killing spot."),
            BT.ClearEnemiesInArea(pos=SKALE_KILLSPOT_COORDS, radius=CLEAR_ENEMIES_AREA_RADIUS),
            LogMessage("area is clear, moving back to Sebedoh the Mesmer"),
            BT.MoveAndAutoDialog(SEBEDOH_THE_MESMER_COORDS),
        ],
    )
    return BehaviorTree(tree)


def Elementalist_001_Sequence() -> BehaviorTree:
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4915.27, -2893.53)
    CLEANUP_MODEL_IDS: tuple[int, ...] = (ModelID.Shimmering_Scale.value,)

    tree = BehaviorTree.SequenceNode(
        name="Elementalist 001 sequence",
        children=[
            LogMessage("Taking Quest with Howland the Elementalist"),
            BT.MoveAndAutoDialog(HOWLAND_THE_ELEMENTALIST_COORDS),
            BT.AutoDialog(),
            LogMessage("Moving to Skale killing spot"),
            BT.Move(SKALE_KILLSPOT_COORDS),
            LogMessage("Arrived to Skale killing spot."),
            BT.ClearEnemiesInArea(pos=SKALE_KILLSPOT_COORDS, radius=CLEAR_ENEMIES_AREA_RADIUS),
            LogMessage("area is clear, moving back to Howland the Elementalist"),
            BT.MoveAndAutoDialog(HOWLAND_THE_ELEMENTALIST_COORDS),
            LogMessage("Cleaning up remaining quest items"),
            BT.DestroyItems(model_ids=list(CLEANUP_MODEL_IDS)),
        ],
    )
    return BehaviorTree(tree)


def Profession_Specific_Quest_001_Sequence() -> BehaviorTree:
    tree = BehaviorTree.SequenceNode(
        name="Profession specific quest 001 sequence",
        children=[
            BT.StoreProfessionNames(),
            BehaviorTree.SwitchNode(
                selector_fn=lambda node: node.blackboard.get("player_primary_profession_name", ""),
                cases=[
                    ("Warrior", lambda: Warrior_001_Sequence()),
                    ("Ranger", lambda: Ranger_001_Sequence()),
                    ("Monk", lambda: Monk_001_Sequence()),
                    ("Necromancer", lambda: Necromancer_001_Sequence()),
                    ("Mesmer", lambda: Mesmer_001_Sequence()),
                    ("Elementalist", lambda: Elementalist_001_Sequence()),
                ],
                name="RunProfessionSequence",
            ),
        ],
    )
    return BehaviorTree(tree)


def Sequence_002_Common() -> BehaviorTree: 
    HAVERSDAN_WAIT_MS: int = 18000

    tree = BehaviorTree.SequenceNode(
        name="Starting common sequence",
        children=[
            LogMessage("Waiting for Haversdan to arrive"),
            BT.Move(WAIT_FOR_HAVERSDAN_COORDS),
            BT.Wait(duration_ms=HAVERSDAN_WAIT_MS, log=True),
            LogMessage("Moving to Haversdan"),
            BT.MoveAndAutoDialog(HAVERSDAN_COORDS),
            LogMessage("Moving to Ashford Devona"),
            BT.MoveAndAutoDialog(pos=DEVONA_COORDS),
            BT.AutoDialog(),
            LogMessage("Moving to Ashford Abbey"),
            BT.Move(GO_TO_ASHFORD_ABBEY_COORDS),
            BT.WaitForMapLoad(ASHFORD_ABBEY_MAP_ID),
            LogMessage("Moving to Meerak"),
            BT.MoveAndAutoDialog(MEERAK_COORDS),
            LogMessage("Traveling to Ascalon City to turn in quests"),
            BT.TravelToOutpost(ASCALON_CITY_MAP_ID),
            LogMessage("Turning in quests to Amin Saberlin"),
            BT.MoveAndAutoDialog(AMIN_SABERLIN_COORDS),
            BT.AutoDialog(),
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

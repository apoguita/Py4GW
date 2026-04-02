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


def LogMessage(message: str) -> BehaviorTree:
    return BT.LogMessage(
        message=message,
        module_name=MODULE_NAME,
        print_to_console=PRINT_TO_CONSOLE,
        print_to_blackboard=PRINT_TO_BLACKBOARD,
    )
    
def Sequence_001_Common() -> BehaviorTree:
    TOWN_CRYER_COORDS: Vec2f = Vec2f(9954.21, -472.19)
    SIR_TYDIUS_COORDS: Vec2f = Vec2f(11694.64, 3440.12)

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
    VAN_THE_WARRIOR_COORDS: Vec2f = Vec2f(6123.73, 3952.56)
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
    ARTEMIS_THE_RANGER_COORDS: Vec2f = Vec2f(6143.31, 4202.66)
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
    CIGIO_THE_MONK_COORDS: Vec2f = Vec2f(5983.98, 4181.18)
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4915.27, -2893.53)
    GWEN_COORDS: Vec2f = Vec2f(3876.63, -4540.65)
    
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
            BT.MoveAndInteract(GWEN_COORDS,target_distance=Range.Area.value),
            LogMessage("moving back to Cigio the Monk"),
            BT.MoveAndAutoDialog(CIGIO_THE_MONK_COORDS),
        ],
    )
    return BehaviorTree(tree)

def Necromancer_001_Sequence() -> BehaviorTree:
    VERATA_THE_NECROMANCER_COORDS: Vec2f = Vec2f(6158.20, 4195.64)
    SKALE_KILLSPOT_COORDS: Vec2f = Vec2f(4583.08, 726.40)
    VERATA_THE_NECROMANCER_ENC_STRING: str = "\\x171C\\x8FE8\\xAFAD\\x61EC"

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
            BT.MoveAndAutoDialogByModelID(
                model_id=Agent.GetModelIDByEncString(
                    VERATA_THE_NECROMANCER_ENC_STRING
                ),
                button_number=0,
            ),
        ],
    )
    return BehaviorTree(tree)


def Mesmer_001_Sequence() -> BehaviorTree:
    SEBEDOH_THE_MESMER_COORDS: Vec2f = Vec2f(6251.90, 3891.17)
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
    HOWLAND_THE_ELEMENTALIST_COORDS: Vec2f = Vec2f(6123.73, 3952.56)
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
    WAIT_FOR_HAVERSDAN_COORDS: Vec2f = Vec2f(5534.92, 3831.50)
    HAVERSDAN_WAIT_MS: int = 18000
    HAVERSDAN_COORDS: Vec2f = Vec2f(5984.58, 3823.78)
    PITNEY_COORDS: Vec2f = Vec2f(-8083.34, -15416.37)
    DEVONA_COORDS: Vec2f = Vec2f(-7868.41, -15038.71)
    MEERAK_COORDS: Vec2f = Vec2f(-12289.86, -6518.84)
    
    ASHFORD_ABBEY_MOVE_COORDS: Vec2f = Vec2f(-11890.0, -6071.0)
    
    AMIN_SABERLIN_COORDS_01: Vec2f = Vec2f(8284.25, 5596.36)
    AMIN_SABERLIN_COORDS_02: Vec2f = Vec2f(11952.64, 3115.04)

    tree = BehaviorTree.SequenceNode(
        name="Starting common sequence",
        children=[
            LogMessage("Waiting for Haversdan to arrive"),
            BT.Move(WAIT_FOR_HAVERSDAN_COORDS),
            BT.Wait(duration_ms=HAVERSDAN_WAIT_MS, log=True),
            LogMessage("Moving to Haversdan"),
            BT.MoveAndAutoDialog(HAVERSDAN_COORDS),
            LogMessage("Moving to Pitney"),
            BT.MoveAndAutoDialog(pos=PITNEY_COORDS,target_distance=Range.Area.value,),
            LogMessage("Moving to Ashford Devona"),
            BT.MoveAndAutoDialog(pos=DEVONA_COORDS),
            BT.AutoDialog(),
            LogMessage("Moving to Ashford Abbey"),
            BT.Move(ASHFORD_ABBEY_MOVE_COORDS),
            BT.WaitForMapLoad(ASHFORD_ABBEY_MAP_ID),
            LogMessage("Moving to Meerak"),
            BT.MoveAndAutoDialog(MEERAK_COORDS),
            LogMessage("Traveling to Ascalon City to turn in quests"),
            BT.TravelToOutpost(ASCALON_CITY_MAP_ID),
            LogMessage("Turning in quests to Amin Saberlin"),
            BT.Move(AMIN_SABERLIN_COORDS_01),
            BT.MoveAndAutoDialog(AMIN_SABERLIN_COORDS_02),
            BT.AutoDialog(),
            LogMessage("Routines complete"),
        ],
    )
    return BehaviorTree(tree)



def get_sequence_builders(module_name: str, print_to_console: bool = True) -> list[tuple[str, Callable[[], BehaviorTree]]]:
    global MODULE_NAME, PRINT_TO_CONSOLE
    MODULE_NAME = module_name
    PRINT_TO_CONSOLE = print_to_console
    return [
        ("Sequence_001_Common", lambda: Sequence_001_Common()),
        ("Profession_Specific_Quest_001_Sequence", lambda: Profession_Specific_Quest_001_Sequence()),
        ("Sequence_002_Common", lambda: Sequence_002_Common()),
    ]

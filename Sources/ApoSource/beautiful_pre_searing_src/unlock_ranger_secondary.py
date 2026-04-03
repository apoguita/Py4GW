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


#unlock ranger profession
def UnlockPet() -> BehaviorTree:
    def _is_ranger_primary()-> bool:
        primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
        return primary == "Ranger"
    
    LAKESIDE_COUNTY_EXIT_COORDS_001: Vec2f = Vec2f(-11556.36, -6257.30)
    LAKESIDE_COUNTY_EXIT_COORDS_002: Vec2f = Vec2f(-10905, -6287)
    
    REGENT_VALLEY_MID_001_EXIT_COORDS: Vec2f = Vec2f(-6316.87, -6808.10)
    REGENT_VALLEY_MID_002_EXIT_COORDS: Vec2f = Vec2f(-4833.97, -12199.93)
    REGENT_VALLEY_OVER_BRIDGE_EXIT_COORDS: list[Vec2f] = [Vec2f (-3464.73, -13135.62)]
    REGENT_VALLEY_EXIT_COORDS: Vec2f = Vec2f(6516, -19822)
    
    NEAR_MASTER_NENTE_COORDS:  Vec2f = Vec2f(-17117.03, 10879.81)
    MASTER_NENTE_ENC_STR: str = "\\x344C\\xAFF2\\xB725\\x65D8"

    
    
    MELANDRU_STATUE_COORDS: Vec2f = Vec2f(-14990.32, -1139.84)
    PET_MODEL_ID: int = 1345
    CHARM_PET_SKILL_ID: int = 411

    tree = BehaviorTree.SequenceNode(
        name="Unlocking Ranger Secondary Profession",
        children=[
            LogMessage("Traveling to Ashford Abbey to unlock Ranger Pet and secondary profession"),

            BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
            LogMessage("Exiting to Lakeside County"),
            
            BT.Move(LAKESIDE_COUNTY_EXIT_COORDS_001),
            BT.Move(LAKESIDE_COUNTY_EXIT_COORDS_002),
            BT.WaitForMapLoad(LAKESIDE_COUNTY_MAP_ID),
            
            LogMessage("Destroying summoning stones in bags"),
            BT.DestroyItems(model_ids=list([ModelID.Igneous_Summoning_Stone.value,]),),
            
            LogMessage("Exiting to Regent Valley"),
            
            BT.Move(REGENT_VALLEY_MID_001_EXIT_COORDS),
            BT.Move(REGENT_VALLEY_MID_002_EXIT_COORDS),
            BT.MoveDirect(REGENT_VALLEY_OVER_BRIDGE_EXIT_COORDS),
            BT.Move(REGENT_VALLEY_EXIT_COORDS),
            BT.WaitForMapLoad(REGENT_VALLEY_MAP_ID),
            
            BottingTree.DisableHeroAITree(),
            
            LogMessage("Going to Master Ranger Nente"),
            BT.Move(NEAR_MASTER_NENTE_COORDS),
            LogMessage("Interacting with Master Ranger Nente"),
            LogMessage(f"Debug: {Agent.GetModelIDByEncString(MASTER_NENTE_ENC_STR)} ENC_STR: {MASTER_NENTE_ENC_STR}"),
            
            BT.MoveAndAutoDialogByModelID(
                modelID_or_encStr= MASTER_NENTE_ENC_STR,
                button_number=0,
            ),
            
            BT.AutoDialog(),
            
            LogMessage("Interacting with Melandru Statue to charm pet"),
            BT.Move(MELANDRU_STATUE_COORDS),
            
            LogMessage("Disabling HeroAI to charm pet"),
            
            BT.MoveAndTargetByModelID(PET_MODEL_ID),

            BT.CastSkillID(CHARM_PET_SKILL_ID),
            BT.Wait(15000),
            
            LogMessage("Pet should be charmed, moving back to Master Ranger Nente"),
            BT.Move(NEAR_MASTER_NENTE_COORDS),
            LogMessage("Interacting with Master Ranger Nente to unlock Ranger secondary profession"),
            BT.MoveAndAutoDialogByModelID(
                modelID_or_encStr= MASTER_NENTE_ENC_STR,
                button_number=0,
            ),
            
            BehaviorTree.SelectorNode(
                name="Unlock Ranger Profession",
                children=[
                    BehaviorTree.ConditionNode(
                        name="Is Ranger Primary Profession",
                        condition_fn=_is_ranger_primary,
                    ),
                    BT.AutoDialog(button_number=0),
                ],
            ),
            
            LogMessage("Pet Charmed and Ranger secondary profession unlocked, activating HeroAI and traveling back to Ashford Abbey"),
            BottingTree.EnableHeroAITree(),
            BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
            
        ],
    )
    return BehaviorTree(tree)

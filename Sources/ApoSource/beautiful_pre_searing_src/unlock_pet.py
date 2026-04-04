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


#unlock ranger profession
def UnlockPet() -> BehaviorTree:
    def _is_ranger_primary()-> bool:
        primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
        return primary == "Ranger"

    PET_MODEL_ID: int = 1345
    CHARM_PET_SKILL_ID: int = 411

    tree = BehaviorTree.SequenceNode(
        name="Unlocking Ranger Secondary Profession",
        children=[
            LogMessage("Traveling to Ashford Abbey to unlock Ranger Pet and secondary profession"),

            BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
            LogMessage("Exiting to Lakeside County"),
             
            BT.Move(EXIT_TO_LAKESIDE_COUNTY_COORDS[0]),
            BT.Move(EXIT_TO_LAKESIDE_COUNTY_COORDS[1]),
            BT.WaitForMapLoad(LAKESIDE_COUNTY_MAP_ID),
            
            LogMessage("Destroying summoning stones in bags"),
            BT.DestroyItems(model_ids=list([ModelID.Igneous_Summoning_Stone.value,]),),
            
            LogMessage("Exiting to Regent Valley"),
             
            BT.Move(FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[0]),
            BT.Move(FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[1]),
            BT.MoveDirect([FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[2]]),
            BT.Move(FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[3]),
            BT.WaitForMapLoad(REGENT_VALLEY_MAP_ID),
            
            BottingTree.DisableHeroAITree(),
            
            LogMessage("Going to Master Ranger Nente"),
            BT.Move(NEAR_MASTER_NENTE_COORDS),
            LogMessage("Interacting with Master Ranger Nente"),
            
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
            LogMessage("Finished."),
            
        ],
    )
    return BehaviorTree(tree)

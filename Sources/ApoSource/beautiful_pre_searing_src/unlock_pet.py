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


#unlock ranger profession
def UnlockPet() -> BehaviorTree:
    def is_ranger_primary()-> bool:
        primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
        return primary == "Ranger"

    PET_MODEL_ID: int = 1345
    CHARM_PET_SKILL_ID: int = 411

    return BT.Sequence(
        name="Unlocking Ranger Secondary Profession",
        map_id_or_name=ASHFORD_ABBEY_MAP_ID,
        children=[
            LogMessage("Exiting to Lakeside County"),
            BT.MoveAndExitMap(EXIT_TO_LAKESIDE_COUNTY_COORDS, target_map_id=LAKESIDE_COUNTY_PRESEARING),
            LogMessage("Exiting to Regent Valley"),
            BT.MoveAndExitMap(FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS, target_map_id=REGENT_VALLEY_PRESEARING),
            LogMessage("Going to Master Ranger Nente"),
            BT.Move(NEAR_MASTER_NENTE_COORDS),
            BT.MoveAndKill(Vec2f(-17157.31, 10246.58)),
            LogMessage("Interacting with Master Ranger Nente"),
            BT.HandleAutoQuest(pos=None,use_npc_model_or_enc_str= MASTER_NENTE_ENC_STR, buttons=[0, 0],),
            BT.ExecuteIfProfession(profession_name="Ranger",NodeToRun=BT.EquipItemByModelID(STARTER_BOW_MODEL_ID),),
            LogMessage("Interacting with Melandru Statue to charm pet"),
            BT.Move(MELANDRU_STATUE_COORDS, pause_on_combat=False),
            BT.MoveAndTargetByModelID(PET_MODEL_ID),
            BT.CastSkillID(CHARM_PET_SKILL_ID),
            BT.Wait(15000),
            LogMessage("Pet should be charmed, moving back to Master Ranger Nente"),
            
            
            BT.Move(MELANDRU_STATUE_COORDS[1]),
            BT.Move(MELANDRU_STATUE_COORDS[0]),
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
                        condition_fn=is_ranger_primary,
                    ),
                    BT.AutoDialog(),
                ],
            ),
            
            LogMessage("Pet Charmed and Ranger secondary profession unlocked, activating HeroAI and traveling back to Ashford Abbey"),
            BT.Travel(ASHFORD_ABBEY_MAP_ID),
            LogMessage("Finished."),
            
        ],
    )
    return BehaviorTree(tree)

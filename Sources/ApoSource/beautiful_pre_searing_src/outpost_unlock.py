from Sources.ApoSource.beautiful_pre_searing_src.tree_builder import CommonMapExit, ensure_botting_tree
from Sources.ApoSource.beautiful_pre_searing_src.globals import *
from Sources.ApoSource.beautiful_pre_searing_src.helpers import *




def UnlockWizardsFolly() -> BehaviorTree:
    return CommonMapExit(
        travel_map_id=ASHFORD_ABBEY_MAP_ID,
        path_tree=BehaviorTree(
            BehaviorTree.SequenceNode(
                name="MoveToWizardsFollyExit",
                children=[
                    LogMessage("Moving to Wizard's Folly exit"),
                    BT.Move(GO_TO_WIZARDS_FOLLY_EXIT_COORDS),
                    BT.WaitForMapLoad(WIZARDS_FOLLY_MAP_ID),
                    BT.Move(GO_TO_FOIBLES_FAIR_COORDS),
                    BT.WaitForMapLoad(FOIBLES_FAIR_MAP_ID),
                    LogMessage("Wizard's Folly unlocked"),
                ],
            )
        ),
        exclude_models=ITEMS_BLACKLIST,
    )

def UnlockBarradinState() -> BehaviorTree:
    return CommonMapExit(
        travel_map_id=ASCALON_CITY_MAP_ID,
        path_tree=BehaviorTree(
            BehaviorTree.SequenceNode(
                name="MoveToBarradinStateExit",
                children=[
                    LogMessage("Moving to Barradin State exit"),
                    BT.Move(GO_TO_GREEN_HILLS_COUNTY_COORDS),
                    BT.WaitForMapLoad(GREEN_HILLS_COUNTY_MAP_ID),
                    BT.Move(GO_TO_BARRADIN_STATE_COORDS),
                    BT.WaitForMapLoad(BARRADIN_STATE_MAP_ID),
                    LogMessage("Barradin State unlocked"),
                ],
            )
        ),
        exclude_models=ITEMS_BLACKLIST,
    )
    
def UnlockFortRanik() -> BehaviorTree:
    return CommonMapExit(
        travel_map_id=ASHFORD_ABBEY_MAP_ID,
        path_tree=BehaviorTree(
            BehaviorTree.SequenceNode(
                name="MoveToFortRanikExit",
                children=[
                    LogMessage("Moving to Fort Ranik exit"),
                    BT.Move(FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[0]),
                    BT.Move(FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[1]),
                    BT.MoveDirect([FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[2]]),
                    BT.Move(FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[3]),
                    BT.WaitForMapLoad(REGENT_VALLEY_MAP_ID),
                    BT.Move(GO_TO_FORT_RANIK_COORDS),
                    BT.WaitForMapLoad(FORT_RANIK_MAP_ID),
                    LogMessage("Fort Ranik unlocked"),
                ],
            )
        ),
        exclude_models=ITEMS_BLACKLIST,
    )


def RunAllOutpostUnlocksTree() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="RunAllOutpostUnlocks",
            children=[
                subtree_step("Unlock Wizard's Folly", lambda: UnlockWizardsFolly()),
                subtree_step("Unlock Barradin State", lambda: UnlockBarradinState()),
                subtree_step("Unlock Fort Ranik", lambda: UnlockFortRanik()),
            ],
        )
    )

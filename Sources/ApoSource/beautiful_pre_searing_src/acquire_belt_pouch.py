from Py4GWCoreLib.enums_src.Item_enums import Bags

from .globals import *
from .helpers import *
from .farming_routines import *


def AcquireBeltPouch(
    exclude_models: list[int] | None = None,
) -> BehaviorTree:
    belt_pouch_exclude_models = list(exclude_models or [])
    for model_id in (SKALE_FIN_MODEL_ID, BELT_POUCH_MODEL_ID):
        if model_id not in belt_pouch_exclude_models:
            belt_pouch_exclude_models.append(model_id)

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="AcquireBeltPouch  ",
            children=[
                BehaviorTree.RepeaterUntilSuccessNode(
                    name="FarmUntilEnoughSkaleFinsForBeltPouch",
                    child=BehaviorTree.SequenceNode(
                        name="BeltPouchFarmLoop",
                        children=[
                            LogMessage("Traveling to Ascalon City before belt pouch farm"),
                            BT.TravelToOutpost(ASCALON_CITY_MAP_ID),
                            LogMessage("Handling merchant before belt pouch farm"),
                            merchant_cleanup(
                                exclude_models=belt_pouch_exclude_models,
                                destroy_zero_value_items=True,
                            ),
                            exit_current_map(),
                            LogMessage("Running belt pouch farming node"),
                            BehaviorTree.SubtreeNode(
                                name="PerformBeltPouchFarmingTree",
                                subtree_fn=lambda node: FarmSkale(),
                            ),
                            LogMessage("Returning to Ascalon City after belt pouch farm"),
                            BT.TravelToOutpost(ASCALON_CITY_MAP_ID),
                            LogMessage("Handling merchant after belt pouch farm"),
                            merchant_cleanup(
                                exclude_models=belt_pouch_exclude_models,
                                destroy_zero_value_items=True,
                            ),
                            BehaviorTree.SelectorNode(
                                name="EnoughSkaleFinsOrRepeatBeltPouchFarm",
                                children=[
                                    BehaviorTree.SequenceNode(
                                        name="EnoughSkaleFinsForBeltPouch",
                                        children=[
                                            BT.HasItemQuantity(SKALE_FIN_MODEL_ID, 5),
                                            LogMessage("Enough Skale Fins collected for belt pouch"),
                                        ],
                                    ),
                                    BehaviorTree.SequenceNode(
                                        name="RepeatBeltPouchFarm",
                                        children=[
                                            LogMessage("Not enough Skale Fins yet, restarting belt pouch farm"),
                                            BehaviorTree.FailerNode(
                                                name="RepeatBeltPouchFarmLoop",
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
                LogMessage("Traveling to Ascalon City for belt pouch exchange"),
                BT.TravelToOutpost(ASCALON_CITY_MAP_ID),
                exit_current_map(),
                LogMessage("Moving to Bronlow"),
                BT.MoveAndInteract(BRONLOW_COORDS, target_distance=Range.Area.value),
                LogMessage("Exchanging 5 Skale Fins for Belt Pouch"),
                BT.ExchangeCollectorItem(
                    output_model_id=BELT_POUCH_MODEL_ID,
                    trade_model_ids=[SKALE_FIN_MODEL_ID],
                    quantity_list=[5],
                ),
                BT.IsItemInInventoryBags(BELT_POUCH_MODEL_ID),
                LogMessage("Belt pouch acquired"),
                LogMessage("Equipping belt pouch"),
                BT.EquipInventoryBag(
                    modelID_or_encStr=BELT_POUCH_MODEL_ID,
                    target_bag=Bags.BeltPouch,
                ),
                LogMessage("Traveling to Ascalon City."),
                BT.TravelToOutpost(ASCALON_CITY_MAP_ID),
                LogMessage("Belt pouch equipped, Routine complete."),
            ],
        )
    )

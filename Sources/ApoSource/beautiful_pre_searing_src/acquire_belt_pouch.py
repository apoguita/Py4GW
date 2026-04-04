from Py4GWCoreLib.enums_src.Item_enums import Bags

from .globals import *
from .helpers import *
from .farming_routines import *


def AcquireBeltPouch(
    exclude_models: list[int] | None = None,
) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="AcquireBeltPouch  ",
            children=[
                FarmUntilItemQuantityReached(
                    start_map_id=ASCALON_CITY_MAP_ID,
                    perform_farming_tree=FarmSkale,
                    model_id=SKALE_FIN_MODEL_ID,
                    target_quantity=5,
                    exclude_models=exclude_models,
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
            ],
        )
    )

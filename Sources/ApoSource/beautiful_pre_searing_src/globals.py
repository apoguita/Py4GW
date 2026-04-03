from dataclasses import dataclass, field

from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT

def LogMessage(message: str) -> BehaviorTree:
    return BT.LogMessage(
        message=message,
        module_name=MODULE_NAME,
        print_to_console=PRINT_TO_CONSOLE,
        print_to_blackboard=PRINT_TO_BLACKBOARD,
    )
    
    
PRINT_TO_CONSOLE = True
PRINT_TO_BLACKBOARD = True
MODULE_NAME = "PrepareQuests"

#Map IDs
LAKESIDE_COUNTY_MAP_ID: int = 146
ASCALON_CITY_MAP_ID: int = 148
REGENT_VALLEY_MAP_ID: int = 162
ASHFORD_ABBEY_MAP_ID: int = 164


#Common coords
EXIT_ASCALON_CITY_COORDS: Vec2f = Vec2f(6817.0, 4892.0)


#common configs
CLEAR_ENEMIES_AREA_RADIUS: float = Range.Spirit.value

#useful items
IGNEOUS_SUMMONING_STONE_MODEL_ID = ModelID.Igneous_Summoning_Stone.value
NEVERMORE_FLATBOW_MODEL_ID = ModelID.Bonus_Nevermore_Flatbow.value
DULL_CARAPACES_MODEL_ID = ModelID.Dull_Carapace.value
SKALE_FIN_MODEL_ID = ModelID.Skale_Fin_PreSearing.value
RED_IRIS_FLOWER_MODEL_ID = ModelID.Red_Iris_Flower.value


STARTER_BOW_MODEL_ID = 477
ASCALON_HORNBOW_MODEL_ID = 427

ITEMS_BLACKLIST: list[int] = [
    STARTER_BOW_MODEL_ID,
    ASCALON_HORNBOW_MODEL_ID,
    IGNEOUS_SUMMONING_STONE_MODEL_ID,
    NEVERMORE_FLATBOW_MODEL_ID,
    
    DULL_CARAPACES_MODEL_ID,
    SKALE_FIN_MODEL_ID,
    RED_IRIS_FLOWER_MODEL_ID,
]
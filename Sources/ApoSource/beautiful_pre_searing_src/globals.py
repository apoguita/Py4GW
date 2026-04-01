from dataclasses import dataclass, field

from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.native_src.internals.types import Vec2f

    
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

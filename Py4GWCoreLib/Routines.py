from .GlobalCache import GLOBAL_CACHE 
#this import need to exists or it will break other imports
#need to adress circular import issues, for the time being we will just import everything here

from .routines_src.Agents import Agents as AgentRoutines
from .routines_src.Items import Items as Items
from .routines_src.Party import Party as PartyRoutines
from .routines_src.Checks import Checks as Checks
from .routines_src.Movement import Movement as MovementRoutines
from .routines_src.Targeting import Targeting as TargetingRoutines
from .routines_src.Transition import Transition as TransitionRoutines
from .routines_src.Sequential import Sequential as SequentialRoutines
from .routines_src.Yield import Yield as YieldRoutines
from .routines_src.BehaviourTrees import BT


class Routines:
    BT = BT
    Agents = AgentRoutines
    Items = Items
    Party = PartyRoutines
    Checks = Checks
    Movement = MovementRoutines
    Transition = TransitionRoutines
    Targeting = TargetingRoutines
    Sequential = SequentialRoutines
    Yield = YieldRoutines
    

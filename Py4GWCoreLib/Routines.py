from .GlobalCache import GLOBAL_CACHE

from .routines_src.Agents import Agents as AgentRoutines
from .routines_src.Party import Party as PartyRoutines
from .routines_src.Checks import Checks as CheckRoutines
from .routines_src.Movement import Movement as MovementRoutines
from .routines_src.Targeting import Targeting as TargetingRoutines
from .routines_src.Transition import Transition as TransitionRoutines
from .routines_src.Sequential import Sequential as SequentialRoutines
from .routines_src.Yield import Yield as YieldRoutines


class Routines:
    Agents = AgentRoutines
    Party = PartyRoutines
    Checks = CheckRoutines
    Movement = MovementRoutines
    Transition = TransitionRoutines
    Targeting = TargetingRoutines
    Sequential = SequentialRoutines
    Yield = YieldRoutines

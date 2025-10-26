from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable

#region MOVE
class _Move:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events

    def _follow_model(
        self,
        model_id: int,
        follow_range: float,
        exit_condition: Optional[Callable[[], bool]],
    ) -> Generator[Any, Any, bool]:
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        from ...Py4GWcorelib import Utils

        # default exit if none provided
        if exit_condition is None:
            exit_condition = lambda: False

        result: bool = True  # assume success unless we bail due to invalid map

        while True:
            if exit_condition():
                result = True
                break

            if not Routines.Checks.Map.MapValid():
                result = False
                break

            agent = Routines.Agents.GetAgentIDByModelID(model_id=model_id)
            agent_pos = GLOBAL_CACHE.Agent.GetXY(agent)
            player_pos = GLOBAL_CACHE.Player.GetXY()
            distance = Utils.Distance(agent_pos, player_pos)

            if distance > follow_range:
                path = [player_pos, agent_pos]
                self._config.path = path.copy()
                self._config.path_to_draw = path.copy()
                yield from Routines.Yield.Movement.FollowPath(
                    path_points=path,
                    timeout=self._config.config_properties.movement_timeout.get('value'),
                    tolerance=self._config.config_properties.movement_tolerance.get('value'),
                )

            yield from Routines.Yield.wait(500)

        # keep coroutine semantics consistent
        yield
        return result
    
    @_yield_step(label="FollowModelID", counter_key="FOLLOW_MODEL_ID")
    def follow_model(self, model_id, follow_range, exit_condition: Optional[Callable[[], bool]]=lambda:False) -> Generator[Any, Any, bool]:
        return (yield from self._follow_model(model_id, follow_range, exit_condition))
    
    

    

    


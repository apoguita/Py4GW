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


    def _follow_path(self) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        path = self._config.path
        exit_condition = lambda: Routines.Checks.Player.IsDead() or not Routines.Checks.Map.MapValid() if self._config.config_properties.halt_on_death.is_active() else not Routines.Checks.Map.MapValid()
        pause_condition = self._config.pause_on_danger_fn if self._config.config_properties.pause_on_danger.is_active() else None

        success_movement = yield from Routines.Yield.Movement.FollowPath(
            path_points=path,
            custom_exit_condition=exit_condition,
            log=self._config.config_properties.log_actions.is_active(),
            custom_pause_fn=pause_condition,
            timeout=self._config.config_properties.movement_timeout.get('value'),
            tolerance=self._config.config_properties.movement_tolerance.get('value')
        )

        self._config.config_properties.follow_path_succeeded.set_now("value",success_movement)
        if not success_movement:
            if exit_condition:
                return True
            self._Events.on_unmanaged_fail()
            return False
        
        return True
        
    @_yield_step(label="FollowPath", counter_key="FOLLOW_PATH")
    def follow_path(self) -> Generator[Any, Any, bool]:
        return (yield from self._follow_path())

    def _get_path_to(self, x: float, y: float) -> Generator[Any, Any, None]:
        from ...Pathing import AutoPathing
        from ...GlobalCache import GLOBAL_CACHE
        path = yield from AutoPathing().get_path_to(x, y)
        self._config.path = path.copy()
        current_pos = GLOBAL_CACHE.Player.GetXY()
        self._config.path_to_draw.clear()
        self._config.path_to_draw.append((current_pos[0], current_pos[1]))
        self._config.path_to_draw.extend(path.copy())
        yield

    @_yield_step(label="GetPathTo", counter_key="GET_PATH_TO")
    def get_path_to(self, x: float, y: float):
        yield from self._get_path_to(x, y)

    @_yield_step(label="SetPathTo", counter_key="SET_PATH_TO")
    def set_path_to(self, path: List[Tuple[float, float]]):
        self._config.path = path.copy()
        self._config.path_to_draw = path.copy()
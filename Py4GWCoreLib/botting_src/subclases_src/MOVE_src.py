#region STATES
from typing import TYPE_CHECKING, List, Tuple, Optional, Callable

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
from ..helpers_src.decorators import _yield_step
from typing import Any, Generator

#region MOVE
class _MOVE:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self._Events = parent.helpers.Events
        
    #region Coroutines (_coro_)
    def _coro_get_path_to(self, x: float, y: float) -> Generator[Any, Any, None]:
        from ...Pathing import AutoPathing
        from ...GlobalCache import GLOBAL_CACHE
        path = yield from AutoPathing().get_path_to(x, y)
        self._config.path = path.copy()
        current_pos = GLOBAL_CACHE.Player.GetXY()
        self._config.path_to_draw.clear()
        self._config.path_to_draw.append((current_pos[0], current_pos[1]))
        self._config.path_to_draw.extend(path.copy())
        yield
        
    def _coro_follow_path_to(self, forced_timeout = -1) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        from ...enums import Range
        from ...GlobalCache import GLOBAL_CACHE
        from ...Py4GWcorelib import ConsoleLog, Console
        
        log_actions = self._config.config_properties.log_actions.is_active()
        fsm = self.parent.config.FSM
        path = self._config.path

        exit_condition = (
            (lambda: Routines.Checks.Player.IsDead() or not Routines.Checks.Map.MapValid())
            if self._config.config_properties.halt_on_death.is_active()
            else (lambda: not Routines.Checks.Map.MapValid())
        )

        # --- pause sources ---
        danger_pause = (
            self._config.pause_on_danger_fn
            if self._config.config_properties.pause_on_danger.is_active()
            else None
        )

        loot_config_enabled = self._config.upkeep.auto_loot.is_active()
        loot_singleton = LootConfig()

        def loot_pause() -> bool:
            if not loot_config_enabled:
                return False
            loot_array = loot_singleton.GetfilteredLootArray(
                distance=Range.Earshot.value,
                multibox_loot=True,
                allow_unasigned_loot=False,
            )
            return len(loot_array) > 0

        def fsm_pause() -> bool:
            return fsm.is_paused()

        # --- merged pause condition ---
        def pause_condition() -> bool:
            if danger_pause and danger_pause():
                return True
            if loot_config_enabled and loot_pause():
                return True
            if fsm_pause():
                return True
            return False

        if forced_timeout > 0:
            f_timeout = forced_timeout
        else:
            f_timeout = self._config.config_properties.movement_timeout.get("value")
            
        success_movement = yield from Routines.Yield.Movement.FollowPath(
            path_points=path,
            custom_exit_condition=exit_condition,
            log=log_actions,
            custom_pause_fn=pause_condition,
            timeout=f_timeout,
            tolerance=self._config.config_properties.movement_tolerance.get("value"),
        )

        self._config.config_properties.follow_path_succeeded.set_now("value", success_movement)
        if not success_movement:
            if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
                ConsoleLog("_follow_path", "halting movement due to party wipe", Console.MessageType.Warning, log=True)
                self._config.FSM.pause()
                return True  # continue FSM without halting

            if exit_condition:
                return True

            self._Events.on_unmanaged_fail()
            return False

        return True

    def _coro_set_path_to(self, path: List[Tuple[float, float]]) -> Generator[Any, Any, None]:
        self._config.path = path.copy()
        self._config.path_to_draw = path.copy()
        yield
        
    def _coro_to_model(self, model_id: int) -> Generator[Any, Any, bool]:
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        agent_id = Routines.Agents.GetAgentIDByModelID(model_id)
        x,y = GLOBAL_CACHE.Agent.GetXY(agent_id)
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        return True
        
    def _coro_xy(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveTo_{self._config.get_counter('MOVE_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        
    def _coro_xy_and_exit_map(self, x: float, y: float, target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveAndExitMapTo_{self._config.get_counter('MOVE_AND_EXIT_MAP_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        yield from self.parent.Wait._coro_for_map_load(target_map_id=target_map_id, target_map_name=target_map_name)
        
    def _coro_xy_and_dialog(self, x: float, y: float, dialog_id: int, step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveAndDialogTo_{self._config.get_counter('MOVE_AND_DIALOG_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        yield from self.parent.Dialogs._coro_at_xy(x, y, dialog_id)
    
    def _coro_xy_and_interact_npc(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveAndInteractNPC_{self._config.get_counter('MOVE_AND_INTERACT_NPC_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        yield from self.parent.Interact._coro_with_npc_at_xy(x, y)
        
    def _coro_xy_and_interact_gadget(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveAndInteractGadget_{self._config.get_counter('MOVE_AND_INTERACT_GADGET_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        yield from self.parent.Interact._coro_with_gadget_at_xy(x, y)
        
    def _coro_xy_and_interact_item(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveAndInteractItem_{self._config.get_counter('MOVE_AND_INTERACT_ITEM_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        yield from self.parent.Interact._coro_with_item_at_xy(x, y)


    def _coro_follow_path(self, path: List[Tuple[float, float]]) -> Generator[Any, Any, bool]:
        yield from self._coro_set_path_to(path)
        result = yield from self._coro_follow_path_to()
        return result

    def _coro_follow_auto_path(self, points: List[Tuple[float, float]], step_name: str = "") -> Generator[Any, Any, None]:
        """
        For each (x, y) target point, compute an autopath and follow it.
        Input format matches FollowPath, but each point is autpathed independently.
        """
        if step_name == "":
            step_name = f"FollowAutoPath_{self._config.get_counter('FOLLOW_AUTOPATH')}"

        for x, y in points:
            yield from self._coro_get_path_to(x, y)   # autopath to this target
            yield from self._coro_follow_path_to()       # then execute the path
            
    def _coro_follow_path_and_dialog(self, path: List[Tuple[float, float]], dialog_id: int, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_follow_path(path)
        last_point = path[-1]
        yield from self.parent.Dialogs._coro_at_xy(last_point[0], last_point[1], dialog_id)
        
    def _coro_follow_path_and_exit_map(self, path: List[Tuple[float, float]], target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_follow_path(path)
        yield from self.parent.Wait._coro_for_map_load(target_map_id=target_map_id, target_map_name=target_map_name)
        
    #region Yield Steps (ys_)
    @_yield_step(label="GetPathTo", counter_key="GET_PATH_TO")
    def ys_get_path_to(self, x: float, y: float):
        yield from self._coro_get_path_to(x, y)

    @_yield_step(label="SetPathTo", counter_key="SET_PATH_TO")
    def ys_set_path_to(self, path: List[Tuple[float, float]]):
        yield from self._coro_set_path_to(path)
        
    @_yield_step(label="FollowPath", counter_key="FOLLOW_PATH")
    def ys_follow_path(self, path):
        yield from self._coro_follow_path(path)
    
    @_yield_step(label="FollowAutoPath", counter_key="FOLLOW_AUTOPATH")
    def ys_follow_auto_path(self, points: List[Tuple[float, float]], step_name: str = "") -> Generator[Any, Any, None]:
        yield from self._coro_follow_auto_path(points, step_name)
    
    @_yield_step(label="ToModelID", counter_key="TO_MODEL_ID")
    def ys_to_model(self, model_id: int, step_name: str="") -> Generator[Any, Any, bool]:
        result = yield from self._coro_to_model(model_id)
        return result
    
    @_yield_step(label="XY", counter_key="MOVE_TO")
    def ys_xy(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy(x, y, step_name)
        
    @_yield_step(label="XYAndExitMap", counter_key="MOVE_AND_EXIT_MAP_TO")
    def ys_xy_and_exit_map(self, x: float, y: float, target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy_and_exit_map(x, y, target_map_id, target_map_name, step_name)
        
    @_yield_step(label="XYAndDialog", counter_key="MOVE_AND_DIALOG_TO")
    def ys_xy_and_dialog(self, x: float, y: float, dialog_id: int, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy_and_dialog(x, y, dialog_id, step_name)
        
    @_yield_step(label="XYAndInteractNPC", counter_key="MOVE_AND_INTERACT_NPC_TO")
    def ys_xy_and_interact_npc(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy_and_interact_npc(x, y, step_name)

    @_yield_step(label="XYAndInteractGadget", counter_key="MOVE_AND_INTERACT_GADGET_TO")
    def ys_xy_and_interact_gadget(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy_and_interact_gadget(x, y, step_name)
    
    @_yield_step(label="XYAndInteractItem", counter_key="MOVE_AND_INTERACT_ITEM_TO")
    def ys_xy_and_interact_item(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy_and_interact_item(x, y, step_name)
        
    @_yield_step(label="FollowPathAndDialog", counter_key="FOLLOW_PATH_AND_DIALOG")
    def ys_follow_path_and_dialog(self, path: List[Tuple[float, float]], dialog_id: int, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_follow_path_and_dialog(path, dialog_id, step_name)
        
    @_yield_step(label="FollowPathAndExitMap", counter_key="FOLLOW_PATH_AND_EXIT_MAP")
    def ys_follow_path_and_exit_map(self, path: List[Tuple[float, float]], target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_follow_path_and_exit_map(path, target_map_id, target_map_name, step_name)


    #region public Helpers
    def XY(self, x:float, y:float, step_name: str=""):
        self.ys_xy(x, y, step_name=step_name)
        
    def XYAndDialog(self, x: float, y: float, dialog_id: int, step_name: str="") -> None:
        self.ys_xy_and_dialog(x, y, dialog_id, step_name=step_name)

    def XYAndInteractNPC(self, x: float, y: float, step_name: str="") -> None:
        self.ys_xy_and_interact_npc(x, y, step_name=step_name)

    def XYAndInteractGadget(self, x: float, y: float, step_name: str="") -> None:
        self.ys_xy_and_interact_gadget(x, y, step_name=step_name)

    def XYAndInteractItem(self, x: float, y: float, step_name: str="") -> None:
        self.ys_xy_and_interact_item(x, y, step_name=step_name)

    def XYAndExitMap(self, x: float, y: float, target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> None:
        self.ys_xy_and_exit_map(x, y, target_map_id, target_map_name, step_name=step_name)

    def FollowPath(self, path: List[Tuple[float, float]], step_name: str="") -> None:
        self.ys_follow_path(path)

    def FollowPathAndDialog(self, path: List[Tuple[float, float]], dialog_id: int, step_name: str="") -> None:
        self.ys_follow_path_and_dialog(path, dialog_id, step_name=step_name)

    def FollowPathAndExitMap(self, path: List[Tuple[float, float]], target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> None:
        self.ys_follow_path_and_exit_map(path, target_map_id, target_map_name, step_name=step_name)

    def FollowAutoPath(self, points: List[Tuple[float, float]], step_name: str = "") -> None:
        self.ys_follow_auto_path(points, step_name=step_name)

    def FollowModel(self, model_id: int, follow_range: float, exit_condition: Optional[Callable[[], bool]] = lambda:False) -> None:
        self._helpers.Move.follow_model(model_id, follow_range, exit_condition)
        
    def ToModel(self, model_id: int, step_name: str = "") -> None:
        self.ys_to_model(model_id, step_name=step_name)

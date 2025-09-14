from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple

#region INTERACT
class _Interact:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
            
    def _with_agent(self, coords: Tuple[float, float], dialog_id: int = 0):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        #ConsoleLog(MODULE_NAME, f"Interacting with agent at {coords} with dialog_id {dialog_id}", Py4GW.Console.MessageType.Info)
        while True:
            if GLOBAL_CACHE.Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(500)
                break
            else:
                break

        result = yield from Routines.Yield.Agents.InteractWithAgentXY(*coords)
        #ConsoleLog(MODULE_NAME, f"Interaction result: {result}", Py4GW.Console.MessageType.Info)
        if not result:
            self._Events.on_unmanaged_fail()
            self._config.config_properties.dialog_at_succeeded.set_now("value", False)
            return False

        if not self._config.fsm_running:
            yield from Routines.Yield.wait(100)
            self._config.config_properties.dialog_at_succeeded.set_now("value", False)
            return False

        if dialog_id != 0:
            GLOBAL_CACHE.Player.SendDialog(dialog_id)
            yield from Routines.Yield.wait(500)

        self._config.config_properties.dialog_at_succeeded.set_now("value", True)
        return True
    
    def _with_gadget(self, coords: Tuple[float, float]):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        #ConsoleLog(MODULE_NAME, f"Interacting with gadget at {coords}", Py4GW.Console.MessageType.Info)
        while True:
            if GLOBAL_CACHE.Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(500)
                break
            else:
                break
        result = yield from Routines.Yield.Agents.InteractWithGadgetXY(*coords)
        #ConsoleLog(MODULE_NAME, f"Interaction result: {result}", Py4GW.Console.MessageType.Info)
        if not result:
            self._Events.on_unmanaged_fail()
            self._config.config_properties.dialog_at_succeeded._apply("value", False)
            return False

        if not self._config.fsm_running:
            yield from Routines.Yield.wait(100)
            self._config.config_properties.dialog_at_succeeded._apply("value", False)
            return False

        return True
    
    def _with_item(self, coords: Tuple[float, float]):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        while True:
            if GLOBAL_CACHE.Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(500)
                break
            else:
                break
        result = yield from Routines.Yield.Agents.InteractWithItemXY(*coords)
        if not result:
            self._Events.on_unmanaged_fail()
            self._config.config_properties.dialog_at_succeeded._apply("value", False)
            return False

        if not self._config.fsm_running:
            yield from Routines.Yield.wait(100)
            self._config.config_properties.dialog_at_succeeded._apply("value", False)
            return False

        return True
    
    @_yield_step(label="InteractWithAgent", counter_key="DIALOG_AT")
    def with_npc_at_xy(self,coords: Tuple[float, float],dialog_id: int=0) -> Generator[Any, Any, bool]:
        return (yield from self._with_agent(coords, dialog_id))
    
    @_yield_step(label="InteractWithGadget", counter_key="DIALOG_AT")
    def with_gadget_at_xy(self, coords: Tuple[float, float]) -> Generator[Any, Any, bool]:
        return (yield from self._with_gadget(coords))

    @_yield_step(label="InteractWithItem", counter_key="DIALOG_AT")
    def with_item_at_xy(self, coords: Tuple[float, float]) -> Generator[Any, Any, bool]:
        return (yield from self._with_item(coords))

    @_yield_step(label="InteractWithModel", counter_key="DIALOG_AT")
    def with_model(self, model_id: int, dialog_id: int=0) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        agent_id = Routines.Agents.GetAgentIDByModelID(model_id)
        x,y = GLOBAL_CACHE.Agent.GetXY(agent_id)
        return (yield from self._with_agent((x, y), dialog_id))
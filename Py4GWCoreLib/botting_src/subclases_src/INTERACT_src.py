#region STATES
from typing import TYPE_CHECKING, Dict, Callable, Any, Tuple

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
from ..helpers_src.decorators import _yield_step
from ...Py4GWcorelib import ActionQueueManager

#region INTERACT
class _INTERACT:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self._Events = parent.helpers.Events
        self.combat_status = False
        
    #region Coroutines (_coro_)
    def _coro_with_agent(self, coords: Tuple[float, float], dialog_id: int = 0):
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
    
    def _coro_with_gadget(self, coords: Tuple[float, float]):
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
    
    def _coro_with_item(self, coords: Tuple[float, float]):
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
    
    def _coro_disable_auto_combat(self):
        self.combat_status = self._config.upkeep.auto_combat.is_active()
        self._config.upkeep.auto_combat.set_now("active", False)
        ActionQueueManager().ResetAllQueues()
        yield
    
    def _coro_restore_auto_combat(self):
        self._config.upkeep.auto_combat.set_now("active", self.combat_status)
        yield

    def _coro_with_npc_at_xy(self, x: float, y: float, dialog_id: int = 0, step_name: str = ""):
        yield from self._coro_disable_auto_combat()
        yield from self._coro_with_agent((x, y), dialog_id=dialog_id)
        yield from self._coro_restore_auto_combat()
        
    def _coro_with_gadget_at_xy(self, x: float, y: float, step_name: str=""):
        yield from self._coro_disable_auto_combat()
        yield from self._coro_with_gadget((x, y))
        yield from self._coro_restore_auto_combat()
        
    def _coro_with_item_at_xy(self, x: float, y: float, step_name: str=""):
        yield from self._coro_disable_auto_combat()
        yield from self._coro_with_item((x, y))
        yield from self._coro_restore_auto_combat()

    def _coro_with_model(self, model_id: int, dialog_id: int=0):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        agent_id = Routines.Agents.GetAgentIDByModelID(model_id)
        x,y = GLOBAL_CACHE.Agent.GetXY(agent_id)
        yield from self._coro_with_agent((x, y), dialog_id)
        
    def _coro_with_gadget_id(self, gadget_id: int):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        agent_id = Routines.Agents.GetNearestGadgetByID(gadget_id)
        yield from self._coro_with_gadget(GLOBAL_CACHE.Agent.GetXY(agent_id))
        
    def _coro_with_item_extra_type(self, extra_type: list[int]):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        agent_id = Routines.Agents.GetAgentIDByItemExtraType(extra_type)
        yield from self._coro_with_item(GLOBAL_CACHE.Agent.GetXY(agent_id))
        
    def _coro_with_key_by_bitmask(self):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        agent_id = Routines.Agents.GetClosestKeyByBitMask()
        yield from self._coro_with_item(GLOBAL_CACHE.Agent.GetXY(agent_id))
        
    def _coro_get_blessing(self):
        from Widgets.Blessed import Get_Blessed  # delayed import to avoid circular dependencies
        yield from self._coro_disable_auto_combat()
        Get_Blessed()  # starts the BlessingRunner (as in Blessed.py -> same as pushing the button in the widget)
        yield from self._coro_restore_auto_combat()


    #region Yield Steps (ys_)
    @_yield_step("DisableAutoCombat","AUTO_DISABLE_AUTO_COMBAT")
    def ys_disable_auto_combat(self):
        yield from self._coro_disable_auto_combat()

    @_yield_step("RestoreAutoCombat","AUTO_RESTORE_AUTO_COMBAT")
    def ys_restore_auto_combat(self):
        yield from self._coro_restore_auto_combat()
        
    @_yield_step("WithNpcAtXY","INTERACT_AT")
    def ys_with_npc_at_xy(self, x: float, y: float, dialog_id: int, step_name: str=""):
        yield from self._coro_with_npc_at_xy(x, y, dialog_id, step_name)
        
    @_yield_step("WithGadgetAtXY","INTERACT_GADGET_AT")
    def ys_with_gadget_at_xy(self, x: float, y: float, step_name: str=""):
        yield from self._coro_with_gadget_at_xy(x, y, step_name)
        
    @_yield_step("WithItemAtXY","INTERACT_WITH_ITEM")
    def ys_with_item_at_xy(self, x: float, y: float, step_name: str=""):
        yield from self._coro_with_item_at_xy(x, y, step_name)
        
    @_yield_step("WithGadgetID","INTERACT_WITH_GADGET_ID")
    def ys_with_gadget_id(self, gadget_id: int, step_name: str=""):
        yield from self._coro_with_gadget_id(gadget_id)

    @_yield_step("WithItemExtraType","INTERACT_WITH_ITEM_EXTRA_TYPE")
    def ys_with_item_extra_type(self, extra_type: list[int], step_name: str=""):
        yield from self._coro_with_item_extra_type(extra_type)
        
    @_yield_step("WithKeyByBitmask","INTERACT_WITH_KEY_BY_BITMASK")
    def ys_with_key_by_bitmask(self, step_name: str=""):
        yield from self._coro_with_key_by_bitmask()

    @_yield_step("WithModel","INTERACT_WITH_MODEL")
    def ys_with_model(self, model_id: int, step_name: str=""):
        yield from self._coro_with_model(model_id)
        
    @_yield_step("GetBlessing", "INTERACT_GET_BLESSING")
    def ys_get_blessing(self, step_name: str = ""):
        yield from self._coro_get_blessing()
        
    #region public Helpers

    def WithNpcAtXY(self, x: float, y: float, step_name: str="") -> None:
        self.ys_with_npc_at_xy(x, y, dialog_id=0, step_name=step_name)

    def WithGadgetAtXY(self, x: float, y: float, step_name: str="") -> None:
        self.ys_with_gadget_at_xy(x, y, step_name=step_name)
        
    def WithGadgetID(self, gadget_id: int, step_name: str="") -> None:
        self.ys_with_gadget_id(gadget_id, step_name=step_name)
        
    def WithItemExtraType(self, extra_type: list[int], step_name: str="") -> None:
        self.ys_with_item_extra_type(extra_type, step_name=step_name)
        
    def WithKeyByBitmask(self, step_name: str="") -> None:
        self.ys_with_key_by_bitmask(step_name=step_name)

    def WithItemAtXY(self, x: float, y: float, step_name: str="") -> None:
        self.ys_with_item_at_xy(x, y, step_name=step_name)

    def WithModel(self, model_id: int, step_name: str="") -> None:
        self.ys_with_model(model_id, step_name=step_name)
        
    @_yield_step("GetBlessing", "INTERACT_GET_BLESSING")
    def GetBlessing(self, step_name: str = ""):
        self.ys_get_blessing(step_name=step_name)

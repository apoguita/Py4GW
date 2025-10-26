#region STATES
from typing import TYPE_CHECKING, Dict, Callable, Any

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

from ..helpers_src.decorators import _yield_step
from ...Py4GWcorelib import ActionQueueManager

#region DIALOGS
class _DIALOGS:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self.combat_status = False


    #region Coroutines (_coro_)
    def _coro_disable_auto_combat(self):
        self.combat_status = self._config.upkeep.auto_combat.is_active()
        self._config.upkeep.auto_combat.set_now("active", False)
        ActionQueueManager().ResetAllQueues()
        yield
    
    def _coro_restore_auto_combat(self):
        self._config.upkeep.auto_combat.set_now("active", self.combat_status)
        yield
        
    def _coro_at_xy(self, x: float, y: float, dialog:int):
        yield from self._coro_disable_auto_combat()
        yield from self.parent.Interact._coro_with_npc_at_xy(x, y, dialog_id=dialog)
        yield from self._coro_restore_auto_combat()
        
    def _coro_with_model(self, model_id: int, dialog:int):
        yield from self._coro_disable_auto_combat()
        yield from self.parent.Interact._coro_with_model(model_id=model_id, dialog_id=dialog)
        yield from self._coro_restore_auto_combat()
    
    #region Yield Steps (ys_)
    @_yield_step("DisableAutoCombat","AUTO_DISABLE_AUTO_COMBAT")
    def ys_disable_auto_combat(self):
        yield from self._coro_disable_auto_combat()
        
    @_yield_step("RestoreAutoCombat","AUTO_RESTORE_AUTO_COMBAT")
    def ys_restore_auto_combat(self):
        yield from self._coro_restore_auto_combat()

    @_yield_step("AtXY","DIALOG_AT_XY")
    def ys_at_xy(self, x: float, y: float, dialog:int, step_name: str=""):
        yield from self._coro_at_xy(x, y, dialog)

    @_yield_step("WithModel","DIALOG_WITH_MODEL")
    def ys_with_model(self, model_id: int, dialog:int, step_name: str=""):
        yield from self._coro_with_model(model_id, dialog)

    #region Helpers
    def AtXY(self, x: float, y: float, dialog:int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"DialogAt_{self._config.get_counter('DIALOG_AT')}"
        self.ys_at_xy(x, y, dialog)

        
    def WithModel(self, model_id: int, dialog:int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"DialogWithModel_{self._config.get_counter('DIALOG_AT')}"
        self.ys_with_model(model_id, dialog)

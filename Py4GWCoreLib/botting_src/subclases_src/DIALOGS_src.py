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

    @_yield_step("DisableAutoCombat","AUTO_DISABLE_AUTO_COMBAT")
    def _disable_auto_combat(self):
        self.combat_status = self._config.upkeep.auto_combat.is_active()
        self._config.upkeep.auto_combat.set_now("active", False)
        ActionQueueManager().ResetAllQueues()
        yield

    @_yield_step("RestoreAutoCombat","AUTO_RESTORE_AUTO_COMBAT")
    def _restore_auto_combat(self):
        self._config.upkeep.auto_combat.set_now("active", self.combat_status)
        yield


    def AtXY(self, x: float, y: float, dialog:int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"DialogAt_{self._config.get_counter('DIALOG_AT')}"

        #disable combat to prevent interference
        self._disable_auto_combat()

        self._helpers.Interact.with_npc_at_xy((x, y), dialog_id=dialog)

        #re-enable combat
        self._restore_auto_combat()

    def WithModel(self, model_id: int, dialog:int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"DialogWithModel_{self._config.get_counter('DIALOG_AT')}"

        #disable combat to prevent interference
        self._disable_auto_combat()

        self._helpers.Interact.with_model(model_id=model_id, dialog_id=dialog)

        #re-enable combat
        self._restore_auto_combat()
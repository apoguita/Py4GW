#region STATES
from typing import TYPE_CHECKING, Dict, Callable, Any

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

    def WithNpcAtXY(self, x: float, y: float, step_name: str="") -> None:
        if step_name == "":
            step_name = f"InteractAt_{self._config.get_counter('INTERACT_AT')}"

        #disable combat to prevent interference
        self._disable_auto_combat()

        self._helpers.Interact.with_npc_at_xy((x, y))
        #re-enable combat
        self._restore_auto_combat()

    def WithGadgetAtXY(self, x: float, y: float, step_name: str="") -> None:
        if step_name == "":
            step_name = f"InteractGadgetAt_{self._config.get_counter('INTERACT_GADGET_AT')}"

        #disable combat to prevent interference
        self._disable_auto_combat()

        self._helpers.Interact.with_gadget_at_xy((x, y))

        #re-enable combat
        self._restore_auto_combat()
        
    def WithGadgetID(self, gadget_id: int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"InteractWithGadgetID_{self._config.get_counter('INTERACT_WITH_GADGET_ID')}"

        #disable combat to prevent interference
        self._disable_auto_combat()

        self._helpers.Interact.with_gadget_id(gadget_id=gadget_id)

        #re-enable combat
        self._restore_auto_combat()

    def WithItemAtXY(self, x: float, y: float, step_name: str="") -> None:
        if step_name == "":
            step_name = f"InteractWithItem_{self._config.get_counter('INTERACT_WITH_ITEM')}"


        #disable combat to prevent interference
        self._disable_auto_combat()

        self._helpers.Interact.with_item_at_xy((x, y))
        #re-enable combat
        self._restore_auto_combat()

    def WithModel(self, model_id: int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"InteractWithModel_{self._config.get_counter('INTERACT_WITH_MODEL')}"

        #disable combat to prevent interference
        self._disable_auto_combat()

        self._helpers.Interact.with_model(model_id=model_id)

        #re-enable combat
        self._restore_auto_combat()
        
    @_yield_step("GetBlessing", "INTERACT_GET_BLESSING")
    def GetBlessing(self, step_name: str = ""):
        if step_name == "":
            step_name = f"GetBlessing_{self._config.get_counter('INTERACT_GET_BLESSING')}"

        self._disable_auto_combat()

        from Widgets.Blessed import Get_Blessed  # same import as before
        Get_Blessed()  # starts the BlessingRunner (as in Blessed.py -> same as pushing the button in the widget)

        self._restore_auto_combat()

        yield # we have to make helpers generators for them to work with botting class

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
        self.hero_ai_status = False
        self.hero_ai_pause_status = False


    #region Coroutines (_coro_)
    def _coro_pause_hero_ai(self):
        self.hero_ai_status = self._config.upkeep.hero_ai.is_active()
        self.hero_ai_pause_status = bool(getattr(self._config.upkeep, "hero_ai_paused", None) and self._config.upkeep.hero_ai_paused.is_active())
        self._config.upkeep.hero_ai.set_now("active", False)
        if hasattr(self._config.upkeep, "hero_ai_paused"):
            self._config.upkeep.hero_ai_paused.set_now("active", True)
        ActionQueueManager().ResetAllQueues()
        yield
    
    def _coro_restore_hero_ai(self):
        from ...Routines import Routines
        # Give dialog/UI actions time to settle before AI resumes.
        yield from Routines.Yield.wait(350)
        self._config.upkeep.hero_ai.set_now("active", self.hero_ai_status)
        if hasattr(self._config.upkeep, "hero_ai_paused"):
            self._config.upkeep.hero_ai_paused.set_now("active", self.hero_ai_pause_status)
        yield
        
    def _coro_at_xy(self, x: float, y: float, dialog:int):
        yield from self._coro_pause_hero_ai()
        yield from self.parent.Interact._coro_with_npc_at_xy(x, y, dialog_id=dialog)
        yield from self._coro_restore_hero_ai()
        
    def _coro_with_model(self, model_id: int, dialog:int):
        yield from self._coro_pause_hero_ai()
        yield from self.parent.Interact._coro_with_model(model_id=model_id, dialog_id=dialog)
        yield from self._coro_restore_hero_ai()
    
    #region Yield Steps (ys_)
    @_yield_step("PauseHeroAI","PAUSE_HERO_AI")
    def ys_pause_hero_ai(self):
        yield from self._coro_pause_hero_ai()
        
    @_yield_step("RestoreHeroAI","RESTORE_HERO_AI")
    def ys_restore_hero_ai(self):
        yield from self._coro_restore_hero_ai()

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

from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING

from ...enums_src.Model_enums import ModelID

#region RESTOCK
class _Restock:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
    
    def _restock_item(self, model_id: int, desired_quantity: int) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        from ...Py4GWcorelib import ConsoleLog
        result = yield from Routines.Yield.Items.RestockItems(model_id, desired_quantity)
        if not result:
            yield
            return False
        yield
        return True
    
    @_yield_step(label="RestockBirthdayCupcake", counter_key="RESTOCK_BIRTHDAY_CUPCAKE")   
    def restock_birthday_cupcake (self):
        if self._config.upkeep.birthday_cupcake.is_active():
            qty = self._config.upkeep.birthday_cupcake.get("restock_quantity")
            yield from self._restock_item(ModelID.Birthday_Cupcake.value, qty)

    @_yield_step(label="RestockHoneycomb", counter_key="RESTOCK_HONEYCOMB")
    def restock_honeycomb(self):
        if (self._config.upkeep.honeycomb.is_active() or
            self._config.upkeep.morale.is_active()):
            qty = self._config.upkeep.honeycomb.get("restock_quantity")
            yield from self._restock_item(ModelID.Honeycomb.value, qty)
             
#region STATES
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

#region PARTY
class _PLAYER:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers

    def SetTitle(self, title_id: int):
        self._helpers.Player.set_title(title_id)
        
    def CallTarget(self):
        self._helpers.Player.call_target()
from __future__ import annotations
from ctypes import c_uint
from typing import Tuple, Any


from typing import Any, Generator, TYPE_CHECKING, List, Callable, Optional

from Py4GWCoreLib import ConsoleLog, Console
from Py4GWCoreLib.enums import SharedCommandType  

if TYPE_CHECKING:
    from .helpers import BottingHelpers  # for type checkers only
    from ..Botting import BottingClass  # for type checkers only

from functools import wraps

from .helpers_src.decorators import _yield_step, _fsm_step
from .helpers_src.States import _States
from .helpers_src.Events import _Events
from .helpers_src.Target import _Target
from .helpers_src.Skills import _Skills
from .helpers_src.Move import _Move
from .helpers_src.Upkeepers import _Upkeepers
from .helpers_src.Items import _Items
from .helpers_src.Party import _Party
from .helpers_src.Restock import _Restock
from .helpers_src.UI import _UI
from .helpers_src.Multibox import _Multibox
from .helpers_src.Merchant import _Merchant
from .helpers_src.Player import _Player

class BottingHelpers:
    from ..Py4GWcorelib import Color
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self.Events = _Events(self)
        self.Items = _Items(self)
        self.Merchant = _Merchant(self)
        self.Move = _Move(self)
        self.Multibox = _Multibox(self)
        self.Party = _Party(self)
        self.Player = _Player(self)
        self.Restock = _Restock(self)
        self.Skills = _Skills(self)
        self.States = _States(self)
        self.Target = _Target(self)
        self.UI = _UI(self)
        self.Upkeepers = _Upkeepers(self)

    
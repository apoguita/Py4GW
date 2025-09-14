from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
#region EVENTS
class _Events:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config

    def on_unmanaged_fail(self) -> bool:
        from ...Py4GWcorelib import ConsoleLog, Console
        ConsoleLog("On Unmanaged Fail", "there was an unmanaged failure, stopping bot.", Console.MessageType.Error)
        self.parent.Stop()
        return True
        
    def default_on_unmanaged_fail(self) -> bool:
        from ...Py4GWcorelib import ConsoleLog, Console
        ConsoleLog("On Unmanaged Fail", "there was an unmanaged failure, stopping bot.", Console.MessageType.Error)
        self.parent.Stop()
        return True
from functools import wraps
from typing import TYPE_CHECKING, Any, Generator, Optional, Callable

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
#region EVENTS
class _Events:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._custom_unmanaged_fail: Optional[Callable[[], bool]] = None
        
    def set_on_unmanaged_fail(self, fn: Optional[Callable[[], bool]]) -> None:
        """Set a custom function to be called on unmanaged fail.
        
        The function should return True if the bot should stop, False to continue.
        If None is provided, the default behavior will be used (stop the bot).
        """
        self._custom_unmanaged_fail = fn
        
    def reset_on_unmanaged_fail(self) -> None:
        """Reset to the default unmanaged fail behavior."""
        self._custom_unmanaged_fail = None

    def on_unmanaged_fail(self):
        from ...Py4GWcorelib import ConsoleLog, Console

        result = True
        if self._custom_unmanaged_fail:
            result =  self._custom_unmanaged_fail()
            result = result if result is not None else True

        if result:
            ConsoleLog("On Unmanaged Fail", "there was an unmanaged failure, stopping bot.", Console.MessageType.Error)
            self.parent.Stop()
            return True
        
    def default_on_unmanaged_fail(self) -> bool:
        from ...Py4GWcorelib import ConsoleLog, Console
        ConsoleLog("On Unmanaged Fail", "there was an unmanaged failure, stopping bot.", Console.MessageType.Error)
        self.parent.Stop()
        return True
    
    
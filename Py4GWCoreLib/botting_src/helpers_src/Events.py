from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers


# region EVENTS
class _Events:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self.custom_on_unmanaged_fail_fn = None

    def on_unmanaged_fail(self) -> bool:
        from ...Py4GWcorelib import ConsoleLog, Console

        if self.custom_on_unmanaged_fail_fn:
            should_stop = self.custom_on_unmanaged_fail_fn()
            if should_stop:
                self.parent.Stop()
            return True

        ConsoleLog("On Unmanaged Fail", "there was an unmanaged failure, stopping bot.", Console.MessageType.Error)
        self.parent.Stop()
        return True

    def default_on_unmanaged_fail(self) -> bool:
        from ...Py4GWcorelib import ConsoleLog, Console

        ConsoleLog("On Unmanaged Fail", "there was an unmanaged failure, stopping bot.", Console.MessageType.Error)
        self.parent.Stop()
        return True

    def set_custom_on_unmanaged_fail(self, on_unmanaged_fail_fn: Callable[[], bool]) -> None:
        self.custom_on_unmanaged_fail_fn = on_unmanaged_fail_fn

    def reset_custom_on_unmanaged_fail(self) -> None:
        self.custom_on_unmanaged_fail_fn = None

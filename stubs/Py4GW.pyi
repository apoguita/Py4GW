# Py4GW.pyi - Auto-generated .pyi file for Py4GW module

from typing import Any
class Console:
    class MessageType:
        """
        Enum for console message types.
        """
        Info: int
        Warning: int
        Error: int
        Debug: int
        Success: int
        Performance: int
        Notice: int

    def Log(
        module_name: str,
        message: str,
        type: int = Console.MessageType.Info  # Correct reference
    ) -> None:
        """
        Log a message to the console.

        :param module_name: Name of the module sending the message.
        :param message: The message to log.
        :param type: The type of the message (e.g., Info, Warning, Error).
        :return: None
        """
        ...
    
    def GetCredits(self) -> None: ...
    def get_gw_window_handle(self) -> Any: ...

# This file provides type hints for the PingTracker class in Python.
# It allows for IntelliSense to function correctly when using the C++ bindings.

class PingHandler:

    def Terminate(self) -> None:
        """
        Terminates the ping callback.
        Can be called manually for removing the callback.
        """
        pass


    def GetCurrentPing(self) -> int:
        """
        Returns the most recent ping that was recorded.
        :return: The current ping in milliseconds.
        """
        return 0

    def GetAveragePing(self) -> int:
        """
        Returns the average ping based on the ping history.
        :return: The average ping in milliseconds.
        """
        return 0

    def GetMinPing(self) -> int:
        """
        Returns the minimum ping recorded in the current history.
        :return: The minimum ping in milliseconds.
        """
        return 0

    def GetMaxPing(self) -> int:
        """
        Returns the maximum ping recorded in the current history.
        :return: The maximum ping in milliseconds.
        """
        return 0

# Py4GW.pyi - Auto-generated .pyi file for Py4GW module

from typing import Optional, List, Any  

class Console:
    class MessageType:
        Info :int
        Warning :int
        Error :int
        Debug :int
        Success :int
        Performance :int
        Notice :int
    
    @staticmethod
    def Log(
        module_name: str,
        message: str,
        type: int = Console.MessageType.Info
    ) -> None: ...
        
        
    @staticmethod
    def GetCredits() -> str: ...
    
    @staticmethod
    def get_gw_window_handle() -> Any: ...
    
    @staticmethod
    def get_projects_path() -> str: ...
    
class PingHandler():
    def __init__(self, history_size: int = 10) -> None: ...
    def Terminate(self) -> None: ...
    def GetCurrentPing(self) -> int: ...
    def GetAveragePing(self) -> int: ...
    def GetMinPing(self) -> int: ...
    def GetMaxPing(self) -> int: ...

from typing import Optional, List, Any


class Console:
    class MessageType:
        Info: int
        Warning: int
        Error: int
        Debug: int
        Success: int
        Performance: int
        Notice: int

    # --- Logging & Metadata ---
    @staticmethod
    def Log(
        module_name: str,
        message: str,
        type: int = Console.MessageType.Info
    ) -> None: ...

    @staticmethod
    def GetCredits() -> str: ...
    
    @staticmethod
    def GetLicense() -> str: ...

    @staticmethod
    def get_gw_window_handle() -> Any: ...

    @staticmethod
    def get_projects_path() -> str: ...

    # --- Script Control (Immediate) ---
    @staticmethod
    def load(path: str) -> None: ...
    
    @staticmethod
    def run() -> None: ...
    
    @staticmethod
    def stop() -> None: ...
    
    @staticmethod
    def pause() -> None: ...
    
    @staticmethod
    def resume() -> None: ...
    
    @staticmethod
    def status() -> str: ...

    # --- Script Control (Deferred wrappers) ---
    @staticmethod
    def defer_load(path: str, delay_ms: int = 1000) -> None: ...
    
    @staticmethod
    def defer_run(delay_ms: int = 1000) -> None: ...
    
    @staticmethod
    def defer_stop(delay_ms: int = 1000) -> None: ...
    
    @staticmethod
    def defer_pause(delay_ms: int = 1000) -> None: ...
    
    @staticmethod
    def defer_resume(delay_ms: int = 1000) -> None: ...

    # --- Mixed Deferred Wrappers ---
    @staticmethod
    def defer_load_and_run(path: str, delay_ms: int = 1000) -> None: ...
    
    @staticmethod
    def defer_stop_load_and_run(path: str, delay_ms: int = 1000) -> None: ...
    
    @staticmethod
    def defer_stop_and_run(delay_ms: int = 1000) -> None: ...


class PingHandler:
    def __init__(self, history_size: int = 10) -> None: ...
    def Terminate(self) -> None: ...
    def GetCurrentPing(self) -> int: ...
    def GetAveragePing(self) -> int: ...
    def GetMinPing(self) -> int: ...
    def GetMaxPing(self) -> int: ...

from typing import Callable, Any, TypeVar
T = TypeVar("T")


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
    def change_working_directory(path: str) -> None: ...
    @staticmethod
    def get_gw_window_handle() -> Any: ...
    @staticmethod
    def get_projects_path() -> str: ...
    @staticmethod
    def resize_window(width: int, height: int) -> None: ...
    @staticmethod
    def move_window_to(x: int, y: int) -> None: ...
    @staticmethod
    def set_window_active() -> None: ...
    @staticmethod
    def set_window_geometry(x: int, y: int, width: int, height: int) -> None: ...
    @staticmethod
    def get_window_rect() -> tuple[int, int, int, int]: ...
    @staticmethod
    def get_client_rect() -> tuple[int, int, int, int]: ...
    @staticmethod
    def set_window_title(title: str) -> None: ...
    @staticmethod
    def is_window_active() -> bool: ...
    @staticmethod
    def is_window_minimized() -> bool: ...
    @staticmethod
    def is_window_in_background() -> bool: ...
    @staticmethod
    def set_borderless(enable: bool) -> None: ...
    @staticmethod
    def set_always_on_top(enable: bool) -> None: ...
    @staticmethod
    def flash_window() -> None: ...
    @staticmethod
    def request_attention() -> None: ...
    @staticmethod
    def get_z_order() -> int: ...
    @staticmethod
    def set_z_order(insert_after_HWND: int) -> None: ...
    @staticmethod
    def send_window_to_back() -> None: ...
    @staticmethod
    def bring_window_to_front() -> None: ...
    @staticmethod
    def transparent_click_through(enable: bool) -> None: ...
    @staticmethod
    #0-255
    def adjust_window_opacity(opacity: int ) -> None: ...
    @staticmethod
    def hide_window() -> None: ...
    @staticmethod
    def show_window() -> None: ...

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

# py4gw_game.pyi – stubs for Py4GW.Game module

class Game:
    """
    Submodule for game functions.
    All functions run inside the Guild Wars game thread when appropriate.
    """

    @staticmethod
    def InCharacterSelectScreen() -> bool: ...

    # --- Functions ---
    @staticmethod
    def enqueue(callback: Callable[[], Any]) -> None:
        """
        Enqueue a Python callable to execute on the Guild Wars game thread.

        The callback is executed exactly once, the next time the internal
        game-thread hook fires.

        NOTE:
            - `callback` MUST be a zero-argument function or lambda.
              If arguments are needed, bind them using a lambda:

                Game.enqueue(lambda: func(arg1, arg2))

            - The callback runs with the Python GIL acquired.

        Parameters
        ----------
        callback : Callable[[], Any]
            A zero-argument Python function or lambda to run on the game thread.

        Returns
        -------
        None
        """
        ...
        
    @staticmethod
    def enqueue_and_wait(callback: Callable[[], T]) -> T:
        """
        Execute a Python callable on the Guild Wars game thread and wait
        for its return value.

        This function is THREAD-SAFE.

        Behavior:
            - If called FROM the game thread, the callback executes immediately.
            - If called FROM another thread, the callback is enqueued and this
              function blocks until execution completes.
            - The Python GIL is released while waiting, avoiding deadlocks.

        NOTE:
            - `callback` MUST be a zero-argument function or lambda.
            - Any Python object returned by the callback is returned here.
            - Exceptions raised inside the callback are re-raised to the caller.

        Parameters
        ----------
        callback : Callable[[], T]
            A zero-argument Python function or lambda to run on the game thread.

        Returns
        -------
        T
            The value returned by the callback.
        """
        ...
        
    @staticmethod
    def get_tick_count64() -> int:
        """
        Get the current GetTickCount64 value from the game.

        Returns
        -------
        int
            The current tick count in milliseconds since system boot.
        """
        ...

    # ----------------------------
    # Per-frame callbacks
    # ----------------------------

    @staticmethod
    def register_callback(name: str, callback: Callable[[], Any]) -> int:
        """
        Register a named Python callable to be executed every frame.

        Registration is idempotent by name:
        - If a callback with the same name already exists, it is NOT duplicated.
        - The existing callback id is returned.

        Parameters
        ----------
        name : str
            Unique identifier for the callback.
        callback : Callable[[], Any]
            Zero-argument Python callable.

        Returns
        -------
        int
            Callback id.
        """
        ...

    @staticmethod
    def remove_callback(name: str) -> bool:
        """
        Remove a per-frame callback by name.

        Parameters
        ----------
        name : str
            Callback name.

        Returns
        -------
        bool
            True if a callback was removed, False otherwise.
        """
        ...

    @staticmethod
    def remove_callback_by_id(callback_id: int) -> bool:
        """
        Remove a per-frame callback by id.

        Parameters
        ----------
        callback_id : int
            Callback id returned by register_callback().

        Returns
        -------
        bool
            True if a callback was removed, False otherwise.
        """
        ...

    @staticmethod
    def clear_callbacks() -> None:
        """
        Remove all registered per-frame callbacks.

        Typically called on script reload or shutdown.
        """
        ...
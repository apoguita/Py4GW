from typing import Callable, Any, TypeVar

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
    def get_tick_count64() -> int:
        """
        Get the current GetTickCount64 value from the game.

        Returns
        -------
        int
            The current tick count in milliseconds since system boot.
        """
        ...

    @staticmethod
    def get_shared_memory_name() -> str:
        """
        Get the current per-process runtime shared-memory name.
        """
        ...

    @staticmethod
    def get_shared_memory_size() -> int:
        """
        Get the runtime shared-memory region size in bytes.
        """
        ...

    @staticmethod
    def is_shared_memory_ready() -> bool:
        """
        Check whether the runtime shared-memory region is active.
        """
        ...

    @staticmethod
    def get_shared_memory_sequence() -> int:
        """
        Get the current sequence value for the runtime shared-memory region.
        """
        ...



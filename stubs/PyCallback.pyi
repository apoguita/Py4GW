from typing import Callable, List, Tuple
from enum import IntEnum

# Matches: using CallbackId = uint64_t
class Phase(IntEnum):
    PreUpdate = 0
    Data = 1
    Update = 2
    
class Context(IntEnum):
    Update = 0
    Draw = 1
    Main = 2

class PyCallback:
    """
    Global phased callback scheduler.

    All methods are static.
    """

    # -------------------------------------------------
    # Registration
    # -------------------------------------------------
    @staticmethod
    def Register(
        name: str,
        phase: Phase,
        fn: Callable[[], None],
        priority: int = 99,
        context: Context = Context.Draw
        
    ) -> int:
        """
        Register or replace a callback.

        Replacement rules:
        - Same name AND same phase → replaces function, keeps id and order

        Returns:
            CallbackId
        """
        ...

    # -------------------------------------------------
    # Removal
    # -------------------------------------------------
    @staticmethod
    def RemoveById(id: int) -> bool:
        """
        Remove callback by id.
        Returns True if removed.
        """
        ...

    @staticmethod
    def RemoveByName(name: str) -> bool:
        """
        Remove ALL callbacks matching name (any phase).
        Returns True if at least one was removed.
        """
        ...

    @staticmethod
    def Clear() -> None:
        """
        Alias for RemoveAll().
        """
        ...

    @staticmethod
    def GetCallbackInfo() -> List[
        Tuple[
            int,  # id
            str,         # name
            int,         # phase (int)
            int,        # context (int)
            int,         # priority
            int          # order
        ]
    ]:
        """
        Return a snapshot of all registered callbacks.
        """
        ...

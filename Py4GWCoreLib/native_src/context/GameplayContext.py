
import PyPointers
from Py4GW import Game
from ctypes import Structure, c_uint32, c_float, sizeof, POINTER, cast

class GameplayContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32 * 0x13),   # +h0000
        ("mission_map_zoom", c_float),
        ("unk", c_uint32 * 10),
    ]

assert sizeof(GameplayContextStruct) == 0x78

class GameplayContext:
    _ptr: int = 0
    _cached_ctx: GameplayContextStruct | None = None
    _callback_name = "GameplayContext.UpdatePtr"

    @staticmethod
    def get_ptr() -> int:
        return GameplayContext._ptr

    @staticmethod
    def _update_ptr():
        ptr = PyPointers.PyPointers.GetGameplayContextPtr()
        GameplayContext._ptr = ptr
        if not ptr:
            GameplayContext._cached_ctx = None
            return
        
        GameplayContext._cached_ctx = cast(
            ptr,
            POINTER(GameplayContextStruct)
        ).contents
        
    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            GameplayContext._callback_name,
            PyCallback.Phase.PreUpdate,
            GameplayContext._update_ptr,
            priority=7,
            context=PyCallback.Context.Draw
        )

    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(GameplayContext._callback_name)
        GameplayContext._ptr = 0
        GameplayContext._cached_ctx = None

    @staticmethod
    def get_context() -> GameplayContextStruct | None:
        return GameplayContext._cached_ctx
        
GameplayContext.enable()
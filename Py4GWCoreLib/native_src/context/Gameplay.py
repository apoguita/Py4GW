import PyMap
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
    _callback_name = "GameplayContext.UpdateGameplayContextPtr"

    @staticmethod
    def get_ptr() -> int:
        return GameplayContext._ptr

    @staticmethod
    def _update_ptr():
        GameplayContext._ptr = PyMap.PyMap().GetGameplayContextPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            GameplayContext._callback_name,
            GameplayContext._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(GameplayContext._callback_name)
        GameplayContext._ptr = 0

    @staticmethod
    def get_context() -> GameplayContextStruct | None:
        ptr = GameplayContext._ptr
        if not ptr:
            return None
        return cast(
            ptr,
            POINTER(GameplayContextStruct)
        ).contents
        
GameplayContext.enable()
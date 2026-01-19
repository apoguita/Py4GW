import PyPointers
from Py4GW import Game
from ctypes import Structure, POINTER,c_uint32, cast

#region CinematicStruct
class CinematicStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32),      # +0x0000
        ("h0004", c_uint32),      # +0x0004
    ]

#region Cinematic facade
class Cinematic:
    _ptr: int = 0
    _cached_ptr: int = 0
    _cached_ctx: CinematicStruct | None = None
    _callback_name = "Cinematic.UpdateCinematicPtr"

    @staticmethod
    def get_ptr() -> int:
        return Cinematic._ptr    
    @staticmethod
    def _update_ptr():
        Cinematic._ptr = PyPointers.PyPointers.GetCinematicPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            Cinematic._callback_name,
            Cinematic._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(Cinematic._callback_name)
        Cinematic._ptr = 0
        Cinematic._cached_ptr = 0
        Cinematic._cached_ctx = None

    @staticmethod
    def get_context() -> CinematicStruct | None:
        ptr = Cinematic._ptr
        if not ptr:
            Cinematic._cached_ptr = 0
            Cinematic._cached_ctx = None
            return None
        
        if ptr != Cinematic._cached_ptr:
            Cinematic._cached_ptr = ptr
            Cinematic._cached_ctx = cast(
                ptr,
                POINTER(CinematicStruct)
            ).contents
        return Cinematic._cached_ctx
        
        
        
Cinematic.enable()

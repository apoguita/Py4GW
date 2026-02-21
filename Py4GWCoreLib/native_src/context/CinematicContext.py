import PyPointers
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
    _cached_ctx: CinematicStruct | None = None
    _callback_name = "CinematicContext.UpdatePtr"

    @staticmethod
    def get_ptr() -> int:
        return Cinematic._ptr    
    @staticmethod
    def _update_ptr():
        ptr = PyPointers.PyPointers.GetCinematicPtr()
        Cinematic._ptr = ptr
        if not ptr:
            Cinematic._cached_ctx = None
            return
        Cinematic._cached_ctx = cast(
            ptr,
            POINTER(CinematicStruct)
        ).contents

    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            Cinematic._callback_name,
            PyCallback.Phase.PreUpdate,
            Cinematic._update_ptr,
            priority=99,
            context=PyCallback.Context.Draw
        )

    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(Cinematic._callback_name)
        Cinematic._ptr = 0
        Cinematic._cached_ctx = None

    @staticmethod
    def get_context() -> CinematicStruct | None:
        return Cinematic._cached_ctx
        
        
        
Cinematic.enable()

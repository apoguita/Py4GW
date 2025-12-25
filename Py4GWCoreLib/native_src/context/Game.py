import PyMap
from Py4GW import Game
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_void_p
from ..internals.types import Vec2f

#region WorldMapContext
class GameContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_void_p),                     # +0x0000
        ("h0004", c_void_p),                     # +0x0004
        #... many more fields not yet finished references
    ]
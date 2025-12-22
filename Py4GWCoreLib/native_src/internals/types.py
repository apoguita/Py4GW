import ctypes
from ctypes import Structure, c_uint32, c_float, sizeof

class Vec2f(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
    ]

class GamePos(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("zplane", c_uint32),
    ]
    
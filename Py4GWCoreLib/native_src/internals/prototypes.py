import ctypes

class CallingConvention:
    CDECL = "cdecl"
    STDCALL = "stdcall"

class NativeFunctionPrototype:
    """
    Describes a native function ABI signature.
    Reusable across many functions.
    """

    def __init__(
        self,
        restype,
        *argtypes,
        convention: str = CallingConvention.CDECL,
    ):
        self.restype = restype
        self.argtypes = argtypes
        self.convention = convention

    def build(self):
        """
        Returns the ctypes prototype factory
        (equivalent to ctypes.CFUNCTYPE / WINFUNCTYPE).
        """
        if self.convention == CallingConvention.STDCALL:
            return ctypes.WINFUNCTYPE(self.restype, *self.argtypes)
        return ctypes.CFUNCTYPE(self.restype, *self.argtypes)
    
Prototypes = {
    "Void_U32": NativeFunctionPrototype(
        None,
        ctypes.c_uint32,
    ),
    "Void_U32_U32": NativeFunctionPrototype(
        None,
        ctypes.c_uint32,
        ctypes.c_uint32,
    ),
    "Void_U32_U32_U32": NativeFunctionPrototype(
        None,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
    ),
    "Void_NoArgs": NativeFunctionPrototype(
        None,
    ),
    "Bool_U32": NativeFunctionPrototype(
        ctypes.c_bool,
        ctypes.c_uint32,
    ),
    "U32_NoArgs": NativeFunctionPrototype(
        ctypes.c_uint32,
    ),
    "Void_FloatPtr": NativeFunctionPrototype(
        None,
        ctypes.POINTER(ctypes.c_float),
    ),
}

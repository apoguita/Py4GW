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
    # --- Dat file reading ---
    # void* GetRecObjectBytes(void* handle, int* size_out)
    "VoidP_VoidP_I32P": NativeFunctionPrototype(
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_int32),
    ),
    # void func(void* handle)
    "Void_VoidP": NativeFunctionPrototype(
        None,
        ctypes.c_void_p,
    ),
    # void FreeFileBuffer(void* rec, void* bytes)
    "Void_VoidP_VoidP": NativeFunctionPrototype(
        None,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ),
    # void* OpenFileByFileId(uint32_t archive, uint32_t file_id, uint32_t stream_id, uint32_t flags, uint32_t* error_out)
    "VoidP_U32_U32_U32_U32_U32P": NativeFunctionPrototype(
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32),
    ),
    # void* FileHashToRecObj(const wchar_t* file_hash, int unk1, int unk2)
    "VoidP_WCharP_I32_I32": NativeFunctionPrototype(
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_int32,
        ctypes.c_int32,
    ),
}

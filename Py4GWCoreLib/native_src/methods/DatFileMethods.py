"""Generic gw.dat file reading via hooked game functions.

Locates five internal functions via pattern scanning:

    OpenFileByFileId  – open a dat entry by file_id + stream_id → record handle
                        (File.cpp, assertion on FILE_OPEN_READ / FILE_OPEN_WRITE)
    FileHashToRecObj  – open a dat entry by file hash string → record handle
                        (1st CALL after Amet.cpp assertion)
    GetRecObjectBytes – read decompressed bytes from a record handle
    FreeFileBuffer    – release a byte buffer obtained from GetRecObjectBytes
    CloseRecObj       – release a record handle

Provides synchronous ``read_dat_file()`` and ``read_dat_file_by_hash()`` for use
from any game-thread context (e.g. widget ``update()`` or ``Phase.Data`` callback).
Callers own their own caching.
"""

from ...Scanner import Scanner, ScannerSection
from ..internals.prototypes import Prototypes
from ..internals.native_function import NativeFunction
import ctypes
from typing import Optional

# ─── Hook resolution ──────────────────────────────────────────────────────

_OpenFileByFileId_ptr: int = 0
_FileHashToRecObj_ptr: int = 0
_GetRecObjectBytes_ptr: int = 0
_FreeFileBuffer_ptr: int = 0
_CloseRecObj_ptr: int = 0
_init_error: str = ""


def _init_dat_hooks() -> None:
    """Resolve dat-reading function addresses via pattern scanning."""
    global _OpenFileByFileId_ptr, _FileHashToRecObj_ptr
    global _GetRecObjectBytes_ptr, _FreeFileBuffer_ptr, _CloseRecObj_ptr
    global _init_error

    # OpenFileByFileId — assertion-based scan (resilient across game patches)
    # File.cpp validates: !(flags & (FILE_OPEN_READ | FILE_OPEN_WRITE) & ~source.m_flags)
    _file_assert = Scanner.FindAssertion(
        "File.cpp",
        "!(flags & (FILE_OPEN_READ | FILE_OPEN_WRITE) & ~source.m_flags)",
        0, 0,
    )
    if _file_assert:
        _OpenFileByFileId_ptr = Scanner.ToFunctionStart(_file_assert, 0xFFF)

    # FileHashToRecObj (1st CALL) + GetRecObjectBytes (2nd CALL) after Amet.cpp assertion
    amet_assert = Scanner.FindAssertion("Amet.cpp", "data", 0, 0)
    if amet_assert:
        call1 = Scanner.FindInRange(
            b"\xe8", "x", 0,
            amet_assert + 0xC, amet_assert + 0xFF,
        )
        if call1:
            _FileHashToRecObj_ptr = Scanner.FunctionFromNearCall(call1)
            call2 = Scanner.FindInRange(
                b"\xe8", "x", 0,
                call1 + 1, call1 + 0xFF,
            )
            if call2:
                _GetRecObjectBytes_ptr = Scanner.FunctionFromNearCall(call2)

    # CloseRecObj & FreeFileBuffer — backward scan from AMET cmp pattern
    amet_pattern = Scanner.Find(
        b"\x81\x3a\x41\x4d\x45\x54",
        "xxxxxx", 0,
        ScannerSection.TEXT,
    )
    if amet_pattern:
        close_call = Scanner.FindInRange(
            b"\xe8", "x", 0,
            amet_pattern, amet_pattern - 0xFF,
        )
        if close_call:
            _CloseRecObj_ptr = Scanner.FunctionFromNearCall(close_call)
            free_call = Scanner.FindInRange(
                b"\xe8", "x", 0,
                close_call - 1, close_call - 0xFF,
            )
            if free_call:
                _FreeFileBuffer_ptr = Scanner.FunctionFromNearCall(free_call)

    # Validate required hooks
    if not _OpenFileByFileId_ptr:
        _init_error = "Failed to resolve OpenFileByFileId"
    elif not _FileHashToRecObj_ptr:
        _init_error = "Failed to resolve FileHashToRecObj"
    elif not _GetRecObjectBytes_ptr:
        _init_error = "Failed to resolve GetRecObjectBytes"
    elif not _CloseRecObj_ptr:
        _init_error = "Failed to resolve CloseRecObj"
    elif not _FreeFileBuffer_ptr:
        _init_error = "Failed to resolve FreeFileBuffer"

    if _init_error:
        print(f"[DatHooks] ERROR: {_init_error}")


# ─── Lazy initialization ──────────────────────────────────────────────────

_OpenFileByFileId_Func: Optional[NativeFunction] = None
_FileHashToRecObj_Func: Optional[NativeFunction] = None
_GetRecObjectBytes_Func: Optional[NativeFunction] = None
_FreeFileBuffer_Func: Optional[NativeFunction] = None
_CloseRecObj_Func: Optional[NativeFunction] = None
_hooks_initialized: bool = False


def _ensure_hooks() -> None:
    """Lazily initialize dat hooks on first use (must be called ingame)."""
    global _OpenFileByFileId_Func, _FileHashToRecObj_Func
    global _GetRecObjectBytes_Func, _FreeFileBuffer_Func, _CloseRecObj_Func
    global _hooks_initialized, _init_error

    if _hooks_initialized:
        return
    _hooks_initialized = True

    try:
        _init_dat_hooks()
    except Exception as e:
        _init_error = f"Exception during hook init: {e}"
        return

    if _OpenFileByFileId_ptr:
        _OpenFileByFileId_Func = NativeFunction.from_address(
            name="OpenFileByFileId",
            address=_OpenFileByFileId_ptr,
            prototype=Prototypes["VoidP_U32_U32_U32_U32_U32P"],
        )

    if _FileHashToRecObj_ptr:
        _FileHashToRecObj_Func = NativeFunction.from_address(
            name="FileHashToRecObj",
            address=_FileHashToRecObj_ptr,
            prototype=Prototypes["VoidP_WCharP_I32_I32"],
        )

    if _GetRecObjectBytes_ptr:
        _GetRecObjectBytes_Func = NativeFunction.from_address(
            name="GetRecObjectBytes",
            address=_GetRecObjectBytes_ptr,
            prototype=Prototypes["VoidP_VoidP_I32P"],
        )

    if _FreeFileBuffer_ptr:
        _FreeFileBuffer_Func = NativeFunction.from_address(
            name="FreeFileBuffer",
            address=_FreeFileBuffer_ptr,
            prototype=Prototypes["Void_VoidP_VoidP"],
        )

    if _CloseRecObj_ptr:
        _CloseRecObj_Func = NativeFunction.from_address(
            name="CloseRecObj",
            address=_CloseRecObj_ptr,
            prototype=Prototypes["Void_VoidP"],
        )


# ─── Public API ───────────────────────────────────────────────────────────

def dat_hooks_available() -> bool:
    """Return True if all required dat-reading hooks resolved successfully."""
    _ensure_hooks()
    return (
        _OpenFileByFileId_Func is not None
        and _FileHashToRecObj_Func is not None
        and _GetRecObjectBytes_Func is not None
        and _FreeFileBuffer_Func is not None
        and _CloseRecObj_Func is not None
    )


def get_init_error() -> str:
    """Return a description of why hook init failed (empty on success)."""
    return _init_error


def _read_record(rec) -> Optional[bytes]:
    """Read bytes from an open record handle, then free and close it."""
    if not rec:
        return None
    data_ptr = None
    try:
        size = ctypes.c_int32(0)
        data_ptr = _GetRecObjectBytes_Func.directCall(rec, ctypes.byref(size))
        if not data_ptr or size.value <= 0:
            return None
        return ctypes.string_at(data_ptr, size.value)
    finally:
        if data_ptr:
            _FreeFileBuffer_Func.directCall(rec, data_ptr)
        _CloseRecObj_Func.directCall(rec)


def read_dat_file(
    file_id: int, stream_id: int = 1, flags: int = 1,
) -> Optional[bytes]:
    """Read a gw.dat entry by sequential file_id.

    Call from any game-thread context (e.g. widget ``update()`` or
    ``Phase.Data`` callback).
    Returns decompressed bytes, or ``None`` on failure.

    Parameters
    ----------
    file_id : int
        Sequential dat entry index.
    stream_id : int
        ``0`` = stub / header data (0x10000XXX chunks).
        ``1`` = full decompressed data (0x20000XXX chunks).
    flags : int
        Bitfield validated by File.cpp assertion:
        ``!(flags & (FILE_OPEN_READ | FILE_OPEN_WRITE) & ~source.m_flags)``

        ``1`` = ``FILE_OPEN_READ``  – read mode.
        ``2`` = ``FILE_OPEN_WRITE`` – write mode (untested).
    """
    _ensure_hooks()
    if not dat_hooks_available():
        return None
    rec = _OpenFileByFileId_Func.directCall(0, file_id, stream_id, flags, None)
    return _read_record(rec)


def read_dat_file_by_hash(file_hash: int) -> Optional[bytes]:
    """Read a gw.dat entry by file hash.

    The hash is the value decoded from ``AreaInfoStruct.file_id``
    (e.g. ``file_id1`` / ``file_id2``).  Internally converted to a
    null-terminated ``wchar_t`` string and passed to ``FileHashToRecObj``.

    Call from any game-thread context (e.g. widget ``update()`` or
    ``Phase.Data`` callback).
    Returns decompressed bytes, or ``None`` on failure.
    """
    _ensure_hooks()
    if not dat_hooks_available():
        return None
    # Null-terminated single-wchar string
    buf = (ctypes.c_wchar * 2)(chr(file_hash), '\0')
    rec = _FileHashToRecObj_Func.directCall(buf, 1, 0)
    return _read_record(rec)

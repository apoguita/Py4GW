import ctypes
from ctypes import Structure, c_uint32, c_float, sizeof

from typing import Generic, TypeVar

def read_wstr(ptr) -> str | None:
    return ctypes.wstring_at(ptr) if ptr else None

def encoded_wstr_to_str(s: str | None) -> str | None:
    """
    Make GW encoded strings visible by escaping
    control / non-printable characters.
    """
    if s is None:
        return None

    out = []
    for ch in s:
        o = ord(ch)

        # Printable ASCII
        if 32 <= o <= 126:
            out.append(ch)
        # Newlines / tabs (keep readable)
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        # Everything else: escape
        else:
            out.append(f"\\x{o:04X}")

    return "".join(out)

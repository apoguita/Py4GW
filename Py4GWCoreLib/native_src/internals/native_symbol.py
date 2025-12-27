from enum import IntEnum
from typing import Optional, Union
from .prototypes import NativeFunctionPrototype, Prototypes
import Py4GW
from ...Scanner import Scanner
from ctypes import (
    Structure, POINTER,
    c_uint32, c_float, c_void_p, c_wchar, c_uint8,c_uint16,
    cast
)

class ScannerSection(IntEnum):
    TEXT = 0
    RDATA = 1
    DATA = 2


class NativeSymbol:
    def __init__(
        self,
        name: str,
        pattern: bytes,
        mask: str,
        offset: int = 0,
        section: ScannerSection | int = ScannerSection.TEXT   # <-- FIX HERE
    ):
        self.name = name
        self.pattern = pattern
        self.mask = mask
        self.offset = offset
        self.section = ScannerSection(section)                 # <-- normalize to enum
        self.addr = None
        self.resolve()

    def resolve(self):
        found = Scanner.Find(self.pattern, self.mask, self.offset, self.section)
        if not found:
            raise RuntimeError(f"Symbol {self.name} not located")
        self.addr = found

    def read_ptr(self) -> int:
        """Reads a pointer-sized value from symbol address"""
        if not self.addr:
            return 0
        return cast(self.addr, POINTER(c_uint32)).contents.value  # dereference

    def cast(self, struct_type):
        ptr_value = self.read_ptr()
        if not ptr_value:
            return None
        return cast(ptr_value, POINTER(struct_type)).contents

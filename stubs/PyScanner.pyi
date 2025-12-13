#PyScanner.pyi

# Stubs for PyScanner module
# Auto-generated to match the C++ pybind11 bindings exactly.

from typing import Optional


class PyScanner:
    # ------------------------------
    # Initialization
    # ------------------------------
    @staticmethod
    def Initialize(module_name: str = "") -> None:
        """
        Initialize the scanner for the given module.
        If module_name is empty, the main module is scanned.
        """

    # ------------------------------
    # Pattern scanning
    # ------------------------------
    @staticmethod
    def Find(pattern: bytes, mask: str, offset: int, section: int) -> int:
        """
        Scan for a byte pattern inside a memory section.
        Returns the found address or 0.
        """

    @staticmethod
    def FindInRange(pattern: bytes, mask: str, offset: int,
                    start: int, end: int) -> int:
        """
        Scan for a byte pattern within an explicit address range.
        Returns the found address or 0.
        """

    # ------------------------------
    # Function resolution helpers
    # ------------------------------
    @staticmethod
    def FunctionFromNearCall(call_instruction_address: int,
                             check_valid_ptr: bool = True) -> int:
        """
        Given an address of a near CALL/JMP instruction,
        resolve the absolute target function address.
        """

    @staticmethod
    def ToFunctionStart(address: int, scan_range: int = 0xFF) -> int:
        """
        Scan backwards from 'address' to find a function prologue.
        Typically returns a function start or 0.
        """

    # ------------------------------
    # Pointer validation
    # ------------------------------
    @staticmethod
    def IsValidPtr(address: int, section: int) -> bool:
        """
        Check whether 'address' is inside the memory range
        of the specified section (.text, .rdata, .data).
        """

    # ------------------------------
    # Address usage scanning
    # ------------------------------
    @staticmethod
    def FindUseOfAddress(address: int, offset: int, section: int) -> int:
        """
        Find the first occurrence of a raw address inside instructions.
        Returns the location or 0.
        """

    @staticmethod
    def FindNthUseOfAddress(address: int, nth: int,
                            offset: int, section: int) -> int:
        """
        Find the nth occurrence of a raw address inside instructions.
        Returns the location or 0.
        """

    # ------------------------------
    # String usage scanning — ANSI
    # ------------------------------
    @staticmethod
    def FindUseOfStringA(string: str, offset: int, section: int) -> int:
        """
        Find the first code reference to an ANSI string.
        """

    @staticmethod
    def FindNthUseOfStringA(string: str, nth: int,
                            offset: int, section: int) -> int:
        """
        Find the nth reference to an ANSI string.
        """

    # ------------------------------
    # String usage scanning — WIDE
    # ------------------------------
    @staticmethod
    def FindUseOfStringW(string: str, offset: int, section: int) -> int:
        """
        Find the first code reference to a wide-character string.
        """

    @staticmethod
    def FindNthUseOfStringW(string: str, nth: int,
                            offset: int, section: int) -> int:
        """
        Find the nth reference to a wide-character string.
        """

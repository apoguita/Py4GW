import PyScanner

#region Scanner
class Scanner:
    _Scanner = PyScanner.PyScanner
    
    @staticmethod
    def Initialize(module_name: str = "") -> None:
        """
        Initialize the scanner for the given module.
        If module_name is empty, the main module is scanned.
        """
        Scanner._Scanner.Initialize(module_name)
        
    @staticmethod
    def Find(pattern: bytes, mask: str, offset: int, section: int) -> int:
        """
        Scan for a byte pattern inside a memory section.
        Returns the found address or 0.
        """
        return Scanner._Scanner.Find(pattern, mask, offset, section)
    
    @staticmethod
    def FindInRange(pattern: bytes, mask: str, offset: int,
                    start: int, end: int) -> int:
        """
        Scan for a byte pattern within an explicit address range.
        Returns the found address or 0.
        """
        return Scanner._Scanner.FindInRange(pattern, mask, offset, start, end)
    
    @staticmethod
    def FunctionFromNearCall(call_instruction_address: int,
                             check_valid_ptr: bool = True) -> int:
        """
        Given an address of a near CALL/JMP instruction,
        resolve the absolute target function address.
        """
        return Scanner._Scanner.FunctionFromNearCall(call_instruction_address, check_valid_ptr)
    
    @staticmethod
    def ToFunctionStart(address: int, scan_range: int = 0xFF) -> int:
        """
        Scan backwards from 'address' to find a function prologue.
        Typically returns a function start or 0.
        """
        return Scanner._Scanner.ToFunctionStart(address, scan_range)
    
    @staticmethod
    def IsValidPtr(address: int, section: int) -> bool:
        """
        Check whether 'address' is inside the memory range
        of the specified section (.text, .rdata, .data).
        """
        return Scanner._Scanner.IsValidPtr(address, section)
    
    @staticmethod
    def FindUseOfAddress(address: int, offset: int, section: int) -> int:
        """
        Find the first occurrence of a raw address inside instructions.
        Returns the location or 0.
        """
        return Scanner._Scanner.FindUseOfAddress(address, offset, section)
    
    @staticmethod
    def FindNthUseOfAddress(address: int, nth: int,
                            offset: int, section: int) -> int:
        """
        Find the nth occurrence of a raw address inside instructions.
        Returns the location or 0.
        """
        return Scanner._Scanner.FindNthUseOfAddress(address, nth, offset, section)
    
    @staticmethod
    def FindUseOfStringA(string: str, offset: int, section: int) -> int:
        """
        Find the first code reference to an ANSI string.
        """
        return Scanner._Scanner.FindUseOfStringA(string, offset, section)
    
    @staticmethod
    def FindNthUseOfStringA(string: str, nth: int,
                            offset: int, section: int) -> int:
        """
        Find the nth reference to an ANSI string.
        """
        return Scanner._Scanner.FindNthUseOfStringA(string, nth, offset, section)
    
    @staticmethod
    def FindUseOfStringW(string: str, offset: int, section: int) -> int:
        """
        Find the first code reference to a wide-character string.
        """
        return Scanner._Scanner.FindUseOfStringW(string, offset, section)
    
    @staticmethod
    def FindNthUseOfStringW(string: str, nth: int,
                            offset: int, section: int) -> int:
        """
        Find the nth reference to a wide-character string.
        """
        return Scanner._Scanner.FindNthUseOfStringW(string, nth, offset, section)
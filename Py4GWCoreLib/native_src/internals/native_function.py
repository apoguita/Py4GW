from enum import IntEnum
from typing import Optional, Union
from .prototypes import NativeFunctionPrototype, Prototypes
import Py4GW
from ...Scanner import Scanner
class ScannerSection(IntEnum):
    TEXT = 0
    RDATA = 1
    DATA = 2


class NativeFunction:
    def __init__(
        self,
        name: str,
        pattern: bytes,
        mask: str,
        offset: Optional[int] = None,
        section: Optional[Union[ScannerSection, int]] = None,
        prototype: Optional[NativeFunctionPrototype] = None,
        use_near_call: bool = True,
        near_call_offset: int = 0,
        report_success: bool = False,
    ):
        self.name: str = name
        self.pattern: bytes = pattern
        self.mask: str = mask
        self.offset: int = offset if offset is not None else 0
        self.section: Union[ScannerSection, int] = section if section is not None else ScannerSection.TEXT
        self.prototype: NativeFunctionPrototype | None = prototype
        self.initialized: bool = False
        self.func_ptr= None
        
        self.use_near_call: bool = use_near_call
        self.near_call_offset: int = near_call_offset
        self.report_success: bool = report_success
        
        
        self.initialize()
        
    def initialize(self):
        if self.initialized:
            return self.func_ptr
        
        addr = Scanner.Find(self.pattern, self.mask, self.offset, self.section)
        try:
            assert isinstance(addr, int)
            if addr == 0:
                raise ValueError(f"Pattern for {self.name} not found.")
            
            func_addr = addr
            if self.use_near_call:
                target_address = addr + self.near_call_offset
                func_addr = Scanner.FunctionFromNearCall(target_address, True)
                if func_addr == 0:
                    raise ValueError(f"Failed to resolve function for {self.name}.")

            
            if self.prototype:
                # build() should return a ctypes function factory;
                # calling it with func_addr yields the callable pointer.
                self.func_ptr = self.prototype.build()(func_addr)
            else:
                # direct raw address if no prototype is given
                self.func_ptr = func_addr
                
            self.initialized = True
            if self.report_success:
                print(f"Function {self.name} resolved at: {hex(func_addr)}")
            return self.func_ptr
        except Exception as e:
            print(f"Error initializing function {self.name}: {e}")
            return None

    def is_valid(self) -> bool:
        return self.initialized and self.func_ptr is not None
    
    def get_pointer(self):
        return self.func_ptr
    
    # -------------------------------------------------------------
    # UNSAFE — direct native call
    # -------------------------------------------------------------

    def directCall(self, *args):
        """
        Immediate execution on current thread.
        If func_ptr is an int address, wrap it using prototype.
        """
        if not self.is_valid():
            raise RuntimeError(f"Function {self.name} is not initialized properly.")

        # CASE 1: already a callable (normal natives)
        if callable(self.func_ptr):
            return self.func_ptr(*args)

        # CASE 2: raw address → wrap using prototype
        if isinstance(self.func_ptr, int) and self.prototype:
            raw_addr = self.func_ptr
            fn = self.prototype.build()(raw_addr)
            return fn(*args)

        # CASE 3: raw address and no prototype → cannot call
        raise RuntimeError(
            f"Function {self.name} has a raw address but no prototype, "
            "cannot perform directCall()"
        )
    
    # -------------------------------------------------------------
    # SAFE — always enqueued
    # -------------------------------------------------------------

    def __call__(self, *args):
        if not self.is_valid():
            raise RuntimeError(f"Function {self.name} is not initialized properly.")

        # when it's raw address → wrap it before enqueueing
        def _invoke():
            if callable(self.func_ptr):
                return self.func_ptr(*args)

            if isinstance(self.func_ptr, int) and self.prototype:
                fn = self.prototype.build()(self.func_ptr)
                return fn(*args)

        Py4GW.Game.enqueue(_invoke)
        
    def __repr__(self):
        status = "Initialized" if self.is_valid() else "Not Initialized"
        return f"<NativeFunction {self.name}: {status}>"
    

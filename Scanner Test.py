from Py4GWCoreLib import GLOBAL_CACHE, TitleID, UIManager, EnumPreference, FrameLimiter
import PyImGui
import PyScanner
import Py4GW
import ctypes
from enum import IntEnum

class ScannerSection(IntEnum):
    TEXT = 0
    RDATA = 1
    DATA = 2

Scanner = PyScanner.PyScanner

pattern = b"\x83\x3B\x00\x0F\x85\x00\x00\x00\x00\xFF\x70\x20"
mask    = "xxxxx????xxx"
call_instruction_addr = Scanner.Find(pattern, mask, 0x0C, ScannerSection.TEXT)
SetDifficulty_Func = None

if not call_instruction_addr:
    print("HardMode call instruction NOT found.")
    SetDifficulty_Func = None
else:
    print("Found CALL at:", hex(call_instruction_addr))

    # --- Step 2: resolve real target ---
    func_addr = Scanner.FunctionFromNearCall(call_instruction_addr, True)

    if not func_addr:
        print("Failed to resolve HardMode function.")
        SetDifficulty_Func = None
    else:
        print("HardMode function resolved at:", hex(func_addr))

        # --- Step 3: prepare ctypes function pointer ---
        DoActionPrototype = ctypes.CFUNCTYPE(None, ctypes.c_uint32)
        SetDifficulty_Func = DoActionPrototype(func_addr)
        
def SetHardMode(flag: bool):
    """Python wrapper matching C++ SetHardMode() behavior."""
    global SetDifficulty_Func

    if not SetDifficulty_Func:
        print("ERROR: HardMode function not available.")
        return False

    # Send 1 or 0 depending on flag
    SetDifficulty_Func(1 if flag else 0)
    return True

def draw_window():
    if PyImGui.begin("Adress tester"):
        if PyImGui.button("Execute call instruction"):
            Py4GW.Game.enqueue(lambda: SetHardMode(not GLOBAL_CACHE.Party.IsHardMode()))
        
    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()

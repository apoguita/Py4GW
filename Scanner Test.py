from Py4GWCoreLib import GLOBAL_CACHE, Console, ConsoleLog, UIManager, UIMessage, outposts
import PyImGui
from Py4GWCoreLib.native_src.prototypes import Prototypes
from Py4GWCoreLib.native_src.native_function import NativeFunction, ScannerSection
import ctypes
import PyMap

  
SetDifficulty_Func = NativeFunction(
    name="SetDifficulty_Func", #GWCA name
    pattern=b"\x83\x3B\x00\x0F\x85\x00\x00\x00\x00\xFF\x70\x20",
    mask="xxxxx????xxx",
    offset=0x0C,
    section=ScannerSection.TEXT,
    prototype=Prototypes["Void_U32"],
)


def SetHardMode(flag: bool, log: bool= True) -> bool:
    """
    Python wrapper matching C++ SetHardMode() behavior.
    SAFE by default (enqueued).
    """
    if not SetDifficulty_Func.is_valid():
        ConsoleLog("SetHardMode", "Function not initialized.", Console.MessageType.Error, log=log)
        return False

    SetDifficulty_Func(1 if flag else 0)
    return True

class TravelStruct(ctypes.Structure):
    _fields_ = [
        ("map_id", ctypes.c_uint32),       # MapID : uint32_t
        ("region", ctypes.c_int32),        # enum class ServerRegion (4 bytes)
        ("language", ctypes.c_int32),      # enum class Language (4 bytes)
        ("district_number", ctypes.c_int32)
    ]

assert ctypes.sizeof(TravelStruct) == 16
assert TravelStruct.map_id.offset == 0
assert TravelStruct.region.offset == 4
assert TravelStruct.language.offset == 8
assert TravelStruct.district_number.offset == 12
    
def Travel(map_id, region, district_number, language):
    t = TravelStruct()
    t.map_id = map_id
    t.region = region
    t.language = language
    t.district_number = district_number

    return UIManager.SendUIMessage(
        UIMessage.kTravel,
        ctypes.addressof(t),
        0,
        False
    )


def draw_window():
    if PyImGui.begin("Adress tester"):
        if PyImGui.button("Execute call instruction"):
            SetHardMode(not GLOBAL_CACHE.Party.IsHardMode())
            
        if PyImGui.button("Travel to eotn"):
            print("uimessagemapid=642, region=0, language=0, district_number=0")
            result = Travel(
                map_id=642,           # Constants.MapID.LionsArch
                region=0,             # Constants.ServerRegion.NA
                language=0,           # Constants.Language.English
                district_number=0     # Auto  
            )
            print ("Travel result:", result)
            
        if PyImGui.button("Travel by biding"):
            print("binding mapid=642, region=0, language=0, district_number=0")
            map_instance = PyMap.PyMap()
            result = map_instance.Travel(642,0,0,0)
            print("Travel by binding result:", result)
        
    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()

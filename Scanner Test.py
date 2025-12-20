from Py4GWCoreLib import GLOBAL_CACHE, Console, ConsoleLog, UIManager, UIMessage
import PyImGui
from Py4GWCoreLib.native_src.internals.prototypes import Prototypes
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction, ScannerSection
import ctypes
from ctypes import sizeof
import PyMap
from Py4GW import Game

world_map_ptr = 0
def get_world_map_context_ptr():
    global world_map_ptr
    world_map_ptr = PyMap.PyMap().GetWorldMapContextPtr()
    
#Game.clear_callbacks()
CallbackID = Game.register_callback("get_world_map_context_ptr", lambda: get_world_map_context_ptr())


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


def Travel(map_id: int, region: int, district_number: int, language: int) -> bool:
    return UIManager.SendUIMessage(
        UIMessage.kTravel,
        [map_id, region, language, district_number],
        False
    )
    
class TravelStruct(ctypes.Structure):
    _fields_ = [
        ("map_id", ctypes.c_uint32),        # GW::Constants::MapID
        ("region", ctypes.c_int32),         # ServerRegion
        ("language", ctypes.c_int32),       # Language
        ("district_number", ctypes.c_int32)
    ]

assert ctypes.sizeof(TravelStruct) == 16

def Travel_struct(map_id, region, district_number, language):
    t = TravelStruct()
    t.map_id = map_id
    t.region = region
    t.language = language
    t.district_number = district_number

    return UIManager.SendUIMessageRaw(
        UIMessage.kTravel,
        ctypes.addressof(t),
        0,
        False
    )

from ctypes import Structure, c_uint32, c_float

class Vec2f(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
    ]


class WorldMapContext(Structure):
    _pack_ = 1
    _fields_ = [
        ("frame_id", c_uint32),     # 0x0000
        ("h0004", c_uint32),        # 0x0004
        ("h0008", c_uint32),        # 0x0008
        ("h000c", c_float),         # 0x000C
        ("h0010", c_float),         # 0x0010
        ("h0014", c_uint32),        # 0x0014
        ("h0018", c_float),         # 0x0018
        ("h001c", c_float),         # 0x001C
        ("h0020", c_float),         # 0x0020
        ("h0024", c_float),         # 0x0024
        ("h0028", c_float),         # 0x0028
        ("h002c", c_float),         # 0x002C
        ("h0030", c_float),         # 0x0030
        ("h0034", c_float),         # 0x0034

        ("zoom", c_float),          # 0x0038

        ("top_left", Vec2f),        # 0x003C
        ("bottom_right", Vec2f),    # 0x0044

        ("h004c", c_uint32 * 7),    # 0x004C → 0x0068

        ("h0068", c_float),         # 0x0068
        ("h006c", c_float),         # 0x006C

        ("params", c_uint32 * 0x6D) # 0x0070 → 0x224
    ]

assert sizeof(WorldMapContext) == 0x224

def draw_window():
    global world_map_ptr
    if PyImGui.begin("Adress tester"):
        if PyImGui.button("Execute call instruction"):
            SetHardMode(not GLOBAL_CACHE.Party.IsHardMode())
            
        if PyImGui.button("Travel to eotn"):
            result = Travel(
                map_id=642,           # Constants.MapID.LionsArch
                region=0,             # Constants.ServerRegion.NA
                language=0,           # Constants.Language.English
                district_number=0     # Auto  
            )
            print ("Travel result:", result)
            
        if PyImGui.button("Travel to eotn (struct Raw)"):
            result = Travel_struct(
                map_id=642,           # Constants.MapID.LionsArch
                region=0,             # Constants.ServerRegion.NA
                language=0,           # Constants.Language.English
                district_number=0     # Auto  
            )
            print ("Travel (struct) result:", result)
        
        if world_map_ptr:
            world_map_context = ctypes.cast(world_map_ptr, ctypes.POINTER(WorldMapContext)).contents
            PyImGui.text(f"WorldMapContext zoom: {world_map_context.zoom}")
        PyImGui.text(f"WorldMapContext ptr: {hex(world_map_ptr)}")

        
    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()

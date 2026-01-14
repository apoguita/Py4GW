from Py4GWCoreLib import GLOBAL_CACHE, Console, ConsoleLog, UIManager, UIMessage
import PyImGui
import struct
from Py4GWCoreLib.native_src.internals.prototypes import Prototypes
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction, ScannerSection
from Py4GWCoreLib.native_src.internals.gw_array import GW_Array_View, GW_Array
from Py4GWCoreLib.native_src.context.PreGameContext import (
    PreGameContext,
    PreGameContextStruct,
    LoginCharacter,
)

import ctypes
from ctypes import sizeof
import PyPointers
from Py4GW import Game

world_map_ptr = 0
def get_world_map_context_ptr():
    global world_map_ptr
    world_map_ptr = PyPointers.PyPointers.GetWorldMapContextPtr()
    
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

#region memory location helpers
def scan_for_gw_array(base_ptr: int, size: int):
    for off in range(0, size - 0x10, 4):  # DWORD aligned
        try:
            arr = cast(base_ptr + off, POINTER(GW_Array)).contents

            # Basic sanity checks
            if not arr.m_buffer:
                continue
            if arr.m_size == 0 or arr.m_size > arr.m_capacity:
                continue
            if arr.m_capacity > 64:
                continue

            print(
                f"[+0x{off:04X}] GW_Array?"
                f" buffer={hex(arr.m_buffer)}"
                f" size={arr.m_size}"
                f" cap={arr.m_capacity}"
            )

        except Exception:
            pass
        
        
LOGINCHAR_SIZE = 0x2C  # 44 bytes

def probe_login_character(ptr: int):
    unk0 = cast(ptr, POINTER(c_uint32)).contents.value
    name_buf = cast(ptr + 4, POINTER(c_wchar * 40)).contents
    name = "".join(name_buf).rstrip("\x00")
    return unk0, name


from ctypes import cast, POINTER, c_wchar
import PyImGui


def probe_login_character_offsets(
    base_ptr: int,
    index: int,
    stride: int,
    max_offset: int = 0x40,
):
    """
    Manually probe wchar offsets for ONE element.
    You visually inspect the output and decide the correct offset.

    base_ptr : arr.m_buffer
    index    : which character index to probe (pick one with a visible name)
    stride   : your current best guess (ex: 0x2C)
    """

    elem_ptr = base_ptr + index * stride

    PyImGui.separator()
    PyImGui.text(f"Probing element {index} @ {hex(elem_ptr)}")

    for off in range(0, max_offset, 2):
        try:
            buf = cast(
                elem_ptr + off,
                POINTER(c_wchar * 20)
            ).contents

            raw = "".join(buf).split("\x00", 1)[0]

            if raw:
                # sanitize for imgui
                safe = (
                    raw.encode("utf-8", errors="replace")
                       .decode("utf-8", errors="replace")
                       .replace("\x00", "")
                )
                PyImGui.text(f"+0x{off:02X}: {safe}")
        except Exception:
            pass
        
LOGINCHAR_SIZE = 0x2C  # 44 bytes

def probe_field_ptr(ptr: int):
    unk0 = cast(ptr, POINTER(c_uint32)).contents.value
    name_buf = cast(ptr + 4, POINTER(c_wchar * 40)).contents
    name = "".join(name_buf).rstrip("\x00")
    return unk0, name


def draw_dword_probe_table(table_id: str, label: str, values):
    flags = (
        PyImGui.TableFlags.BordersInnerV
        | PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.SizingStretchProp
    )

    if not PyImGui.begin_table(table_id, 8, flags):
        return

    PyImGui.table_setup_column("Index", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Dec", PyImGui.TableColumnFlags.WidthFixed, 90)
    PyImGui.table_setup_column("Hex", PyImGui.TableColumnFlags.WidthFixed, 90)
    PyImGui.table_setup_column("Bytes", PyImGui.TableColumnFlags.WidthFixed, 110)
    PyImGui.table_setup_column("ASCII", PyImGui.TableColumnFlags.WidthFixed, 50)
    PyImGui.table_setup_column("WChar", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Float", PyImGui.TableColumnFlags.WidthFixed, 90)
    PyImGui.table_setup_column("Hints", PyImGui.TableColumnFlags.WidthStretch)

    PyImGui.table_headers_row()

    for i, val in enumerate(values):
        # ---- float reinterpretation ----
        try:
            fval = struct.unpack("<f", struct.pack("<I", val))[0]
            float_str = f"{fval:.3f}" if -1e6 < fval < 1e6 else "—"
        except Exception:
            float_str = "—"

        # ---- pointer heuristic ----
        is_ptr = 0x10000 <= val <= 0x7FFFFFFF
        hints = "PTR" if is_ptr else ""

        # ---- ASCII (low byte) ----
        ascii_char = chr(val) if 32 <= val <= 126 else "."

        # ---- UTF-16 (low word) hint ----
        low_wchar = val & 0xFFFF
        wchar_char = chr(low_wchar) if 32 <= low_wchar <= 0xD7FF else "."

        # ---- byte breakdown ----
        b0 = val & 0xFF
        b1 = (val >> 8) & 0xFF
        b2 = (val >> 16) & 0xFF
        b3 = (val >> 24) & 0xFF
        bytes_str = f"{b0:02X} {b1:02X} {b2:02X} {b3:02X}"

        PyImGui.table_next_row()

        PyImGui.table_next_column()
        PyImGui.text_unformatted(f"{label}[{i}]")

        PyImGui.table_next_column()
        PyImGui.text_unformatted(str(val))

        PyImGui.table_next_column()
        PyImGui.text_unformatted(f"{val:08X}")

        PyImGui.table_next_column()
        PyImGui.text_unformatted(bytes_str)

        PyImGui.table_next_column()
        PyImGui.text_unformatted(ascii_char)

        PyImGui.table_next_column()
        PyImGui.text_unformatted(wchar_char)

        PyImGui.table_next_column()
        PyImGui.text_unformatted(float_str)

        PyImGui.table_next_column()
        PyImGui.text_unformatted(hints)

    PyImGui.end_table()


pad = 0
def draw_window():
    global world_map_ptr, pad
    if PyImGui.begin("Adress tester"):
        if PyImGui.button("Execute call instruction"):
            SetHardMode(not GLOBAL_CACHE.Party.IsHardMode())
            
        if PyImGui.button("Travel to eotn"):
            result = Travel(
                map_id=248,           # Constants.MapID.LionsArch
                region=0,             # Constants.ServerRegion.NA
                language=0,           # Constants.Language.English
                district_number=0     # Auto  
            )
            print ("Travel result:", result)
            
        if PyImGui.button("Travel to eotn (struct Raw)"):
            result = Travel_struct(
                map_id=248,           # Constants.MapID.LionsArch
                region=0,             # Constants.ServerRegion.NA
                language=0,           # Constants.Language.English
                district_number=0     # Auto  
            )
            print ("Travel (struct) result:", result)
        
        """if world_map_ptr:
            world_map_context = ctypes.cast(world_map_ptr, ctypes.POINTER(WorldMapContext)).contents
            PyImGui.text(f"WorldMapContext zoom: {world_map_context.zoom}")
        PyImGui.text(f"WorldMapContext ptr: {hex(world_map_ptr)}")
        
        if PyImGui.button("Scan for GW_Array in PreGameContext"):
            base_ptr = PreGameContext.get_ptr()
            if base_ptr:
                scan_for_gw_array(base_ptr, 0x400)
            else:
                PyImGui.text("PreGameContext pointer not available.")
                
        PyImGui.separator()
        base_ptr = PreGameContext.get_ptr()
        arr = cast(base_ptr + 0x00DC, POINTER(GW_Array)).contents
        
        def safe_imgui_text(s: str) -> str:
            return (
                s
                .encode("utf-8", errors="replace")
                .decode("utf-8", errors="replace")
                .replace("\x00", "")
            )


        PyImGui.text("GW_Array<LoginCharacter>")
        PyImGui.text(safe_imgui_text(f"buffer = {hex(arr.m_buffer)}"))
        PyImGui.text(safe_imgui_text(f"size   = {arr.m_size}"))
        PyImGui.text(safe_imgui_text(f"cap    = {arr.m_capacity}"))

        PyImGui.separator()
        if PyImGui.collapsing_header("Probe LoginCharacter Entries"):
            PyImGui.text("Probing LoginCharacter entries:")
            LOGINCHAR_SIZE = 0x2C
            pad = PyImGui.input_int("Padding before entries", pad)
            for i in range(max(arr.m_size, 28)):
                unk0, name = probe_field_ptr(arr.m_buffer +pad  + i  * LOGINCHAR_SIZE)
                PyImGui.text(safe_imgui_text(f"{i}: unk0={unk0}, name={name}"))
                
            if PyImGui.button("print offsets"):
                for i in range(max(arr.m_size, 28)):
                    unk0, name = probe_field_ptr(arr.m_buffer + i * LOGINCHAR_SIZE)
                    print(safe_imgui_text(f"{i}: unk0={unk0}, name={name}"))
                

            PyImGui.separator()
            PyImGui.text("Probing LoginCharacter entries (with dupe offset):")
                
            LOGINCHAR_SIZE = 0x30   # ← example, YOU pick the correct one
            NAME_OFF = 0x0

            for i in range(min(arr.m_size, 14)):
                unk0, name = probe_field_ptr(
                    arr.m_buffer + i * LOGINCHAR_SIZE + NAME_OFF
                )
                PyImGui.text(
                    safe_imgui_text(f"{i}: unk0={unk0}, name={name}")
                )
                
            probe_login_character_offsets(
                base_ptr=arr.m_buffer,
                index=4,
                stride=0x2C,   # keep your current guess
                max_offset=0x40
            )
            """     


        
    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()

import PyImGui
import PyPlayer
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_wchar
from Py4GWCoreLib.native_src.internals.gw_array import GW_Array_View, GW_Array
from Py4GWCoreLib.native_src.context.GameplayContext import (
    GameplayContextStruct,
    GameplayContext,
)
from Py4GWCoreLib.native_src.context.WorldMapContext import (
    WorldMapContext,
    WorldMapContextStruct,
)
from Py4GWCoreLib.native_src.context.MissionMapContext import (
    MissionMapContext,
    MissionMapContextStruct,
    MissionMapSubContext,
)

from Py4GWCoreLib.native_src.context.PreGameContext import (
    PreGameContext,
    PreGameContextStruct,
    LoginCharacter,
)


def draw_kv_table(table_id: str, rows: list[tuple[str, str | int | float]]):
    flags = (
        PyImGui.TableFlags.BordersInnerV
        | PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.SizingStretchProp
    )

    if PyImGui.begin_table(table_id, 2, flags):
        PyImGui.table_setup_column("Field", PyImGui.TableColumnFlags.WidthFixed, 180)
        PyImGui.table_setup_column("Value", PyImGui.TableColumnFlags.WidthStretch)
        PyImGui.table_headers_row()

        for field, value in rows:
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            PyImGui.text_unformatted(str(field))
            PyImGui.table_next_column()
            PyImGui.text_unformatted(str(value))

        PyImGui.end_table()

def draw_world_map_context_tab(world_map_ptr: WorldMapContextStruct):
    rows: list[tuple[str, str | int | float]] = [
        ("frame_id", world_map_ptr.frame_id),
        ("h0004", world_map_ptr.h0004),
        ("h0008", world_map_ptr.h0008),
        ("h000c", world_map_ptr.h000c),
        ("h0010", world_map_ptr.h0010),
        ("h0014", world_map_ptr.h0014),
        ("h0018", world_map_ptr.h0018),
        ("h001c", world_map_ptr.h001c),
        ("h0020", world_map_ptr.h0020),
        ("h0024", world_map_ptr.h0024),
        ("h0028", world_map_ptr.h0028),
        ("h002c", world_map_ptr.h002c),
        ("h0030", world_map_ptr.h0030),
        ("h0034", world_map_ptr.h0034),
        ("zoom", world_map_ptr.zoom),
        (
            "top_left",
            f"({world_map_ptr.top_left.x}, {world_map_ptr.top_left.y})",
        ),
        (
            "bottom_right",
            f"({world_map_ptr.bottom_right.x}, {world_map_ptr.bottom_right.y})",
        ),
        ("h004c", str(list(world_map_ptr.h004c))),
        ("h0068", world_map_ptr.h0068),
        ("h006c", world_map_ptr.h006c),
        ("params", str(list(world_map_ptr.params))),
    ]

    draw_kv_table("WorldMapTable", rows)
    
def draw_mission_map_context_tab(mission_map_ptr: MissionMapContextStruct):
    rows: list[tuple[str, str | int | float]] = [
        ("size", f"{mission_map_ptr.size.x} x {mission_map_ptr.size.y}"),
        ("h0008", mission_map_ptr.h0008),
        (
            "last_mouse_location",
            f"({mission_map_ptr.last_mouse_location.x}, "
            f"{mission_map_ptr.last_mouse_location.y})",
        ),
        ("frame_id", mission_map_ptr.frame_id),
        (
            "player_mission_map_pos",
            f"({mission_map_ptr.player_mission_map_pos.x}, "
            f"{mission_map_ptr.player_mission_map_pos.y})",
        ),
        ("h0030", mission_map_ptr.h0030),
        ("h0034", mission_map_ptr.h0034),
        ("h0038", mission_map_ptr.h0038),
        ("h0040", mission_map_ptr.h0040),
        ("h0044", mission_map_ptr.h0044),
    ]

    draw_kv_table("MissionMapTable", rows)

    subcontexts = GW_Array_View(
        mission_map_ptr.h0020, MissionMapSubContext
    )
    items = subcontexts.to_list()

    sub_rows: list[tuple[str, str | int | float]] = []
    for i, sc in enumerate(items):
        sub_rows.append((f"Subcontext {i} h0000[0]", sc.h0000[0]))

    draw_kv_table(
        f"MissionMapSubcontexts ({len(items)})", sub_rows
    )

    sub2_ptr = mission_map_ptr.h003c
    if not sub2_ptr:
        PyImGui.text("MissionMapSubContext2 not available.")
    else:
        sub2 = sub2_ptr.contents
        sub2_rows: list[tuple[str, str | int | float]] = [
            ("h0000", sub2.h0000),
            (
                "player_mission_map_pos",
                f"({sub2.player_mission_map_pos.x}, "
                f"{sub2.player_mission_map_pos.y})",
            ),
            ("h000c", sub2.h000c),
            (
                "mission_map_size",
                f"({sub2.mission_map_size.x}, "
                f"{sub2.mission_map_size.y})",
            ),
            ("unk", sub2.unk),
            (
                "mission_map_pan_offset",
                f"({sub2.mission_map_pan_offset.x}, "
                f"{sub2.mission_map_pan_offset.y})",
            ),
            (
                "mission_map_pan_offset2",
                f"({sub2.mission_map_pan_offset2.x}, "
                f"{sub2.mission_map_pan_offset2.y})",
            ),
            ("unk2", str(list(sub2_ptr.contents.unk2))),
            ("unk3", str(list(sub2.unk3))),
        ]

        draw_kv_table("MissionMapSubContext2", sub2_rows)
        
def draw_gameplay_context_tab(gameplay_ctx: GameplayContextStruct):
    rows: list[tuple[str, str | int | float]] = []

    for i, value in enumerate(gameplay_ctx.h0000):
        rows.append((f"h0000[{i}]", value))

    rows.append(("mission_map_zoom", gameplay_ctx.mission_map_zoom))

    for i, value in enumerate(gameplay_ctx.unk):
        rows.append((f"unk[{i}]", value))

    draw_kv_table("GameplayTable", rows)
 
import struct


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

    
def draw_pregame_context_tab(pregame_ctx: PreGameContextStruct):
    # ---- Main PreGameContext fields ----
    rows: list[tuple[str, str | int | float]] = [
        ("frame_id", pregame_ctx.frame_id),
        ("chosen_character_index", pregame_ctx.chosen_character_index),
        ("UNK01", pregame_ctx.UNK01),
        #("index_2", pregame_ctx.index_2),
    ]

    draw_kv_table("PreGameContextTable", rows)
    PyImGui.separator()
    if PyImGui.collapsing_header("h0004 Probe Table"):
        draw_dword_probe_table(
            "PreGame_unk00_probe",
            "h0004",
            pregame_ctx.h0004
        )
    """
    PyImGui.separator()
    draw_dword_probe_table(
        "PreGame_unk00_probe",
        "unk00",
        pregame_ctx.unk00
    )
    """
        
    
    # ---- Characters array (GW::Array<LoginCharacter>) ----
    chars = pregame_ctx.chars

    if not chars.m_buffer or chars.m_size == 0:
        PyImGui.text("No login characters available.")
        return

    # IMPORTANT:
    # GW::Array<LoginCharacter>  ->  m_buffer is LoginCharacter*
    base = cast(chars.m_buffer, POINTER(LoginCharacter))

    char_rows: list[tuple[str, str | int | float]] = []

    for i in range(chars.m_size):
        try:
            ch = base[i]
        except Exception:
            char_rows.append((f"Char[{i}]", "<invalid access>"))
            continue

        name = (
            "".join(ch.character_name)
            .rstrip("\x00")
        )

        # Uncomment if you want unk0 shown later
        # char_rows.append((f"Char[{i}] unk0", ch.unk0))
        char_rows.append((f"Char[{i}] name", name))

    draw_kv_table(f"LoginCharacters ({chars.m_size})", char_rows)
    
    
pad = 0
def draw_window():
    global pad
    if PyImGui.begin("Native Map Tester", True, PyImGui.WindowFlags.AlwaysAutoResize):

        if PyImGui.begin_tab_bar("NativeMapTabs"):

            # ==================================================
            # World Map Context TAB
            # ==================================================
            if PyImGui.begin_tab_item("World Map Context"):
                world_map_ptr: WorldMapContextStruct | None = WorldMapContext.get_context()
                if not world_map_ptr:
                    PyImGui.text("WorldMapContext not available.")
                else:
                    draw_world_map_context_tab(world_map_ptr)
                PyImGui.end_tab_item()

            # ==================================================
            # Mission Map Context TAB
            # ==================================================
            if PyImGui.begin_tab_item("Mission Map Context"):
                mission_map_ptr: MissionMapContextStruct | None = (
                    MissionMapContext.get_context()
                )
                if not mission_map_ptr:
                    PyImGui.text("MissionMapContext not available.")
                else:
                    draw_mission_map_context_tab(mission_map_ptr)

                PyImGui.end_tab_item()

            # ==================================================
            # Gameplay Context TAB
            # ==================================================
            if PyImGui.begin_tab_item("Gameplay Context"):
                gameplay_ctx: GameplayContextStruct | None = GameplayContext.get_context()
                if not gameplay_ctx:
                    PyImGui.text("GameplayContext not available.")
                else:
                    draw_gameplay_context_tab(gameplay_ctx)

                PyImGui.end_tab_item()
                
            # ==================================================
            # PreGame Context TAB
            if PyImGui.begin_tab_item("PreGame Context"):
                pregame_ctx: PreGameContextStruct | None = PreGameContext.get_context()
                if not pregame_ctx:
                    PyImGui.text("PreGameContext not available.")
                    pregame = PyPlayer.PyPlayer().GetPreGameContext()
                    if not pregame:
                        PyImGui.text("PyPreGameContext not available.")
                    else:
                        PyImGui.text(f"frame_id: {pregame.frame_id}")
                else:
                    draw_pregame_context_tab(pregame_ctx)
                    
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
                    """
                    Make a string safe for ImGui by:
                    - removing nulls
                    - replacing invalid unicode
                    - keeping printable content only
                    """
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
                        unk0, name = probe_login_character(arr.m_buffer +pad  + i  * LOGINCHAR_SIZE)
                        PyImGui.text(safe_imgui_text(f"{i}: unk0={unk0}, name={name}"))
                        
                    if PyImGui.button("print offsets"):
                        for i in range(max(arr.m_size, 28)):
                            unk0, name = probe_login_character(arr.m_buffer + i * LOGINCHAR_SIZE)
                            print(safe_imgui_text(f"{i}: unk0={unk0}, name={name}"))
                        
    
                    PyImGui.separator()
                    PyImGui.text("Probing LoginCharacter entries (with dupe offset):")
                        
                    LOGINCHAR_SIZE = 0x30   # ← example, YOU pick the correct one
                    NAME_OFF = 0x0

                    for i in range(min(arr.m_size, 14)):
                        unk0, name = probe_login_character(
                            arr.m_buffer + i * LOGINCHAR_SIZE + NAME_OFF
                        )
                        PyImGui.text(
                            safe_imgui_text(f"{i}: unk0={unk0}, name={name}")
                        )
                    # Pick an index that clearly showed a name before (example: 4)
                    """probe_login_character_offsets(
                        base_ptr=arr.m_buffer,
                        index=4,
                        stride=0x2C,   # keep your current guess
                        max_offset=0x40
                    )
                    """     


                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()

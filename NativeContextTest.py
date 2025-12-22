import PyImGui
import PyPlayer
import struct
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_wchar
from Py4GWCoreLib.native_src.internals.gw_array import GW_Array_View, GW_Array
from Py4GWCoreLib.native_src.context.Gameplay import (
    GameplayContextStruct,
    GameplayContext,
)
from Py4GWCoreLib.native_src.context.WorldMap import (
    WorldMapContext,
    WorldMapContextStruct,
)
from Py4GWCoreLib.native_src.context.MissionMap import (
    MissionMapContext,
    MissionMapContextStruct,
    MissionMapSubContext,
)

from Py4GWCoreLib.native_src.context.PreGame import (
    PreGameContext,
    PreGameContextStruct,
    LoginCharacter,
)

#region draw_kv_table
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

#region draw_world_map_context_tab
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
    
#region draw_mission_map_context_tab
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
        
#region draw_gameplay_context_tab
def draw_gameplay_context_tab(gameplay_ctx: GameplayContextStruct):
    rows: list[tuple[str, str | int | float]] = []

    for i, value in enumerate(gameplay_ctx.h0000):
        rows.append((f"h0000[{i}]", value))

    rows.append(("mission_map_zoom", gameplay_ctx.mission_map_zoom))

    for i, value in enumerate(gameplay_ctx.unk):
        rows.append((f"unk[{i}]", value))

    draw_kv_table("GameplayTable", rows)
 
#region draw_dword_probe_table
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

#region draw_pregame_context_tab
def draw_pregame_context_tab(pregame_ctx: PreGameContextStruct):
    # ---- Main PreGameContext fields ----
    rows: list[tuple[str, str | int | float]] = [
        ("frame_id", pregame_ctx.frame_id),
        ("chosen_character_index", pregame_ctx.chosen_character_index),
        ("h0054", pregame_ctx.h0054),
        ("h0058", pregame_ctx.h0058),
        ("h0060", pregame_ctx.h0060),
        ("h0068", pregame_ctx.h0068),
        ("h0070", pregame_ctx.h0070),
        ("h0078", pregame_ctx.h0078),
        ("h00a0", pregame_ctx.h00a0),
        ("h00a4", pregame_ctx.h00a4),
        ("h00a8", pregame_ctx.h00a8),
    ]

    draw_kv_table("PreGameContextTable", rows)
    PyImGui.separator()

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

        if PyImGui.collapsing_header(f"[{name}] details"):
            rows: list[tuple[str, str | int | float]] = [
                ("character_name", name),
                ("Unk00", ch.Unk00),
                ("pvp_or_campaign", ch.pvp_or_campaign),
                ("level", ch.Level),
                ("current_map_id", ch.current_map_id),
                ("UnkPvPData01", ch.UnkPvPData01),
                ("UnkPvPData02", ch.UnkPvPData02),
                ("UnkPvPData03", ch.UnkPvPData03),
                ("UnkPvPData04", ch.UnkPvPData04),
            ]
            draw_kv_table(f"LoginCharacter[{i}]", rows)
            
            for i in range(0, len(ch.Unk01)):
                PyImGui.text(f"Unk01[{i}]: {ch.Unk01[i]}")
                
            for i in range(0, len(ch.Unk02)):
                PyImGui.text(f"Unk02[{i}]: {ch.Unk02[i]}")

    draw_kv_table(f"LoginCharacters ({chars.m_size})", char_rows)
    
    if PyImGui.collapsing_header("unknown arrays dump"):
        # ---- Dump unknown arrays ----
        draw_dword_probe_table(
            "Unk01_probe",
            "Unk01",
            pregame_ctx.Unk01
        )
        
        PyImGui.separator()
        
        draw_dword_probe_table(
            "Unk02_probe",
            "Unk02",
            pregame_ctx.Unk02
        )
        
        PyImGui.separator()
        
        draw_dword_probe_table(
            "Unk03_probe",
            "Unk03",
            pregame_ctx.Unk03
        )
        
        PyImGui.separator()
        
        PyImGui.text(f"Unk04: {pregame_ctx.Unk04}")
        PyImGui.text(f"Unk05: {pregame_ctx.Unk05}")
        
        PyImGui.separator()
        
        draw_dword_probe_table(
            "Unk06_probe",
            "Unk06",
            pregame_ctx.Unk06
        )
        
        PyImGui.separator()
        
        draw_dword_probe_table(
            "Unk07_probe",
            "Unk07",
            pregame_ctx.Unk07
        )
        
        PyImGui.separator()
        
        PyImGui.text(f"Unk08: {pregame_ctx.Unk08}")

#region draw_window
    
def draw_window():
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
                else:
                    draw_pregame_context_tab(pregame_ctx)
                    

                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()

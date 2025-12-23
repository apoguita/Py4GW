import ctypes
import PyImGui
import PyPlayer
import struct
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_wchar
from Py4GWCoreLib.native_src.internals.types import Vec2f, Vec3f
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

from Py4GWCoreLib.native_src.context.World import (
    WorldContext,
    WorldContextStruct,
    PartyAlly, PartyAttribute,
    AgentEffects, Buff, Effect, Quest,
    MissionObjective,
)


def true_false_text(value: bool) -> None:
    color = (0.0, 1.0, 0.0, 1.0) if value else (1.0, 0.0, 0.0, 1.0)
    PyImGui.text_colored("True", color) if value else PyImGui.text_colored("False", color)
    
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

    subcontexts = mission_map_ptr.subcontexts

    sub_rows: list[tuple[str, str | int | float]] = []
    for i, sc in enumerate(subcontexts):
        sub_rows.append((f"Subcontext {i} h0000[0]", sc.h0000[0]))

    draw_kv_table(
        f"MissionMapSubcontexts ({len(subcontexts)})", sub_rows
    )

    sub2 = mission_map_ptr.subcontext2

    if not sub2:
        PyImGui.text("MissionMapSubContext2 not available.")
    else:
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
            ("unk2", str(list(sub2.unk2))),
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
    chars = pregame_ctx.chars_list

    if not chars:
        PyImGui.text("No login characters available.")
        return

    for idx, ch in enumerate(chars):
        # character_name is a fixed wchar[20]
        name = "".join(ch.character_name).rstrip("\x00")

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

            draw_kv_table(f"LoginCharacter[{idx}]", rows)

            for i in range(len(ch.Unk01)):
                PyImGui.text(f"Unk01[{i}]: {ch.Unk01[i]}")

            for i in range(len(ch.Unk02)):
                PyImGui.text(f"Unk02[{i}]: {ch.Unk02[i]}")

        
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
        
#region draw_world_context_tab
def draw_world_context_tab(world_ctx: WorldContextStruct):
    account_info = world_ctx.account_info

    if not account_info:
        PyImGui.text("AccountInfo not available.")
    else:
        if PyImGui.collapsing_header("Account Info"):
            PyImGui.text(f"Account Name: {account_info.account_name_str}")
            PyImGui.text(f"Wins: {account_info.wins}")
            PyImGui.text(f"Losses: {account_info.losses}")
            PyImGui.text(f"Rating: {account_info.rating}")

            PyImGui.text(f"Qualifier Points: {account_info.qualifier_points}")
            PyImGui.text(f"Rank: {account_info.rank}")
            PyImGui.text(f"Unk00: {account_info.tournament_reward_points}")
        
    PyImGui.separator()
    message_buff:list[str] | None = world_ctx.message_buff
    if message_buff is None:
        PyImGui.text("Message Buff: <empty>")
    else:
        if PyImGui.collapsing_header("Message Buff"):
            for i, msg in enumerate(message_buff):
                PyImGui.text(f"[{i}]: {msg}")
      
    PyImGui.separator()      
    dialog_buff = world_ctx.dialog_buff
    if dialog_buff is None:
        PyImGui.text("Dialog Buff: <empty>")
    else:
        if PyImGui.collapsing_header("Dialog Buff"):
            for i, msg in enumerate(dialog_buff):
                PyImGui.text(f"[{i}]: {msg}")
                
    PyImGui.separator()
    merch_items = world_ctx.merch_items
    if merch_items is None:
        PyImGui.text("Merch Items: <empty>")
    else:
        if PyImGui.collapsing_header("Merch Items"):
            for i, item_id in enumerate(merch_items):
                PyImGui.text(f"[{i}]: {item_id}")

    PyImGui.separator()
    merch_items2 = world_ctx.merch_items2
    if merch_items2 is None:
        PyImGui.text("Merch Items 2: <empty>")
    else:
        if PyImGui.collapsing_header("Merch Items 2"):
            for i, item_id in enumerate(merch_items2):
                PyImGui.text(f"[{i}]: {item_id}")
                
    PyImGui.separator()
    PyImGui.text(f"accumMapInitUnk00: {world_ctx.accumMapInitUnk0}")
    PyImGui.text(f"accumMapInitUnk01: {world_ctx.accumMapInitUnk1}")
    PyImGui.text(f"accumMapInitOffset: {world_ctx.accumMapInitOffset}")
    PyImGui.text(f"accumMapInitLength: {world_ctx.accumMapInitLength}")
    PyImGui.text(f"h0054: {world_ctx.h0054}")
    PyImGui.text(f"accumMapInitUnk2: {world_ctx.accumMapInitUnk2}")
    all_flag : Vec3f | None = world_ctx.all_flag
    if all_flag is None:
        PyImGui.text("all_flag: <invalid>")
    else:
        PyImGui.text(f"all_flag: x{all_flag.x}, y{all_flag.y} z{all_flag.z}")
    PyImGui.text(f"h00A8: {world_ctx.h00A8}")
    PyImGui.text(f"h04D8: {world_ctx.h04D8}")
    
    if PyImGui.collapsing_header("h005C"):
        for i, val in enumerate(world_ctx.h005C):
            PyImGui.text(f"h005C[{i}]: {val}")
            
    PyImGui.separator()

    if PyImGui.collapsing_header("Map Agents"):
        map_agents = world_ctx.map_agents
        if map_agents is None:
            PyImGui.text("No map agents available.")
        else:
            for i, agent in enumerate(map_agents):
                if PyImGui.collapsing_header(f"agent_ID[{i}]"):
                    PyImGui.text(f"cur_energy: {agent.cur_energy}")
                    PyImGui.text(f"max_energy: {agent.max_energy}")
                    PyImGui.text(f"energy_regen: {agent.energy_regen}")
                    PyImGui.text(f"skill_timestamp: {agent.skill_timestamp}")
                    PyImGui.text(f"h0010: {agent.h0010}")
                    PyImGui.text(f"max_energy2: {agent.max_energy2}")
                    PyImGui.text(f"h0018: {agent.h0018}")
                    PyImGui.text(f"h001C: {agent.h001C}")
                    PyImGui.text(f"cur_health: {agent.cur_health}")
                    PyImGui.text(f"max_health: {agent.max_health}")
                    PyImGui.text(f"health_regen: {agent.health_regen}")
                    PyImGui.text(f"h002C: {agent.h002C}")
                    PyImGui.text(f"effects: {agent.effects}")
                    true_false_text(agent.is_bleeding)
                    true_false_text(agent.is_conditioned)
                    true_false_text(agent.is_crippled)
                    true_false_text(agent.is_dead)
                    true_false_text(agent.is_deep_wounded)
                    true_false_text(agent.is_poisoned)
                    true_false_text(agent.is_enchanted)
                    true_false_text(agent.is_degen_hexed)
                    true_false_text(agent.is_hexed)
                    true_false_text(agent.is_weapon_spelled)
                    PyImGui.separator()
                
    if PyImGui.collapsing_header("Party Allies"):
        party_allies = world_ctx.party_allies
        if party_allies is None:
            PyImGui.text("No party allies available.")
        else:
            for i, ally in enumerate(party_allies):
                if PyImGui.collapsing_header(f"ally_ID[{i}]"):
                    PyImGui.text(f"agent_id: {ally.agent_id}")
                    PyImGui.text(f"unk: {ally.unk}")
                    PyImGui.text(f"composite_id: {ally.composite_id}")
                    PyImGui.separator()
                    
    if PyImGui.collapsing_header("Party Attributes"):
        party_attributes:list[PartyAttribute] | None = world_ctx.party_attributes
        if party_attributes is None:
            PyImGui.text("No attributes available.")
        else:
            for party_attribute in party_attributes:
                if PyImGui.collapsing_header(f"agent_ID: {party_attribute.agent_id}"):
                    for i, attr in enumerate(party_attribute.attributes):
                        if PyImGui.collapsing_header(f"attribute[{i}]"):
                            PyImGui.text(f"attribute_id: {attr.attribute_id}")
                            PyImGui.text(f"level_base: {attr.level_base}")
                            PyImGui.text(f"level : {attr.level }")
                            PyImGui.text(f"decrement_points: {attr.decrement_points}")
                            PyImGui.text(f"increment_points: {attr.increment_points}")
                    PyImGui.separator()
      
    h04B8_ptrs  :list[int] | None = world_ctx.h04B8_ptrs
    if h04B8_ptrs is None:
        PyImGui.text("h04B8_ptrs: <empty>")
    else:
        if PyImGui.collapsing_header("h04B8_ptrs"):
            for i, val in enumerate(world_ctx.h04B8_ptrs or []): 
                PyImGui.text(f"h04B8_ptrs[{i}]: {val}")
                          
    h04C8_ptrs :list[int] | None = world_ctx.h04C8_ptrs
    if h04C8_ptrs is None:
        PyImGui.text("h04C8_ptrs: <empty>")
    else:
        if PyImGui.collapsing_header("h04C8_ptrs"):
            for i, val in enumerate(world_ctx.h04C8_ptrs or []): 
                PyImGui.text(f"h04C8_ptrs[{i}]: {val}")

    h04DC_ptrs :list[int] | None = world_ctx.h04DC_ptrs
    if h04DC_ptrs is None:
        PyImGui.text("h04DC_ptrs: <empty>")
    else:
        if PyImGui.collapsing_header("h04DC_ptrs"):
            for i, val in enumerate(world_ctx.h04DC_ptrs or []): 
                PyImGui.text(f"h04DC_ptrs[{i}]: {val}")
    
    h04EC :list[int] | None = world_ctx.h04EC
    if h04EC is None:
        PyImGui.text("h04EC: <empty>")
    else:        
        if PyImGui.collapsing_header("h04EC"):
            for i, val in enumerate(world_ctx.h04EC or []): 
                PyImGui.text(f"h04EC[{i}]: {val}")

    party_effects :list[AgentEffects] | None = world_ctx.party_effects
    
    if party_effects is None:
        PyImGui.text("party_effects: <empty>")
    else:
        if PyImGui.collapsing_header("party_effects"):
            for i, agent_effect in enumerate(party_effects):
                if PyImGui.collapsing_header(f"AgentEffects for agent_ID[{agent_effect.agent_id}]"):
                    buffs = agent_effect.buffs
                    if not buffs:
                        PyImGui.text("No buffs available.")
                        PyImGui.separator()
                    else:
                        for j, buff in enumerate(buffs):
                            if PyImGui.collapsing_header(f"Buff[{j}]"):
                                PyImGui.text(f"skill_id: {buff.skill_id}")
                                PyImGui.text(f"h0004: {buff.h0004}")
                                PyImGui.text(f"buff_id: {buff.buff_id}")
                                PyImGui.text(f"target_agent_id: {buff.target_agent_id}")
                                PyImGui.separator()
                    
                    effects = agent_effect.effects
                    if not effects:
                        PyImGui.text("No effects available.")
                        PyImGui.separator()
                    else:
                        for k, effect in enumerate(effects):
                            if PyImGui.collapsing_header(f"Effect[{k}]"):
                                PyImGui.text(f"skill_id: {effect.skill_id}")
                                PyImGui.text(f"attribute_level: {effect.attribute_level}")
                                PyImGui.text(f"effect_id: {effect.effect_id}")
                                PyImGui.text(f"agent_id: {effect.agent_id}")
                                PyImGui.text(f"duration: {effect.duration}")
                                PyImGui.text(f"timestamp: {effect.timestamp}")
                                PyImGui.separator()

    h0518_ptrs :list[int] | None = world_ctx.h0518_ptrs
    if h0518_ptrs is None:
        PyImGui.text("h0518_ptrs: <empty>")
    else:
        if PyImGui.collapsing_header("h0518_ptrs"):
            for i, val in enumerate(world_ctx.h0518_ptrs or []): 
                PyImGui.text(f"h0518_ptrs[{i}]: {val}")
                
    PyImGui.separator()
    PyImGui.text(f"active_quest_id: {world_ctx.active_quest_id}")
    
    quest_log :list[Quest] | None = world_ctx.quest_log
    if quest_log is None:
        PyImGui.text("quest_log: <empty>")
    else:
        if PyImGui.collapsing_header("quest_log"):
            for i, quest in enumerate(quest_log):
                if PyImGui.collapsing_header(f"Quest[{i}]"):
                    PyImGui.text(f"quest_id: {quest.quest_id}")
                    PyImGui.text(f"log_state: {quest.log_state}")
                    PyImGui.text(f"location: {quest.location_str}")
                    PyImGui.text(f"name: {quest.name_str}")
                    PyImGui.text(f"npc: {quest.npc_str}")
                    PyImGui.text(f"Map from: {quest.map_from}")
                    marker = quest.marker
                    if marker is None:
                        PyImGui.text("Marker: <invalid>")
                    else:
                        PyImGui.text(f"Marker: x:{marker.x}, y:{marker.y}, z:{marker.zplane}")
                    PyImGui.text(f"h0024: {quest.h0024}")
                    PyImGui.text(f"Map to: {quest.map_to}")
                    PyImGui.text(f"description: {quest.description_str}")
                    PyImGui.text(f"objectives: {quest.objectives_str}")
                    PyImGui.separator()
                    
    h053C :list[int] | None = world_ctx.h053C
    if h053C is None:
        PyImGui.text("h053C: <empty>")
    else:        
        if PyImGui.collapsing_header("h053C"):
            for i, val in enumerate(world_ctx.h053C or []): 
                PyImGui.text(f"h053C[{i}]: {val}")
                
    mission_objectives :list[MissionObjective] | None = world_ctx.mission_objectives
    if mission_objectives is None:
        PyImGui.text("mission_objectives: <empty>")
    else:
        if PyImGui.collapsing_header("mission_objectives"):
            for i, obj in enumerate(mission_objectives):
                if PyImGui.collapsing_header(f"MissionObjective[{i}]"):
                    PyImGui.text(f"objective_id: {obj.objective_id}")
                    PyImGui.text(f"enc_str: {obj.enc_str}")
                    PyImGui.text(f"type: {obj.type}")
                    PyImGui.separator()


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
                
            # ==================================================
            # World Context TAB
            if PyImGui.begin_tab_item("World Context"):
                world_ctx: WorldContextStruct | None = WorldContext.get_context()
                if not world_ctx:
                    PyImGui.text("WorldContext not available.")
                else:
                    draw_world_context_tab(world_ctx)

                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()

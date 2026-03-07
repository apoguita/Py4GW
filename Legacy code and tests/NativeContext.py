import ctypes
import PyImGui
import PyPlayer
import struct
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_wchar
from Py4GWCoreLib.native_src.internals.types import Vec2f, Vec3f
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

from Py4GWCoreLib.native_src.context.WorldContext import (
    WorldContext,
    WorldContextStruct,
    PartyAllyStruct, PartyAttributeStruct,
    AgentEffectsStruct, BuffStruct, EffectStruct, QuestStruct,
    MissionObjectiveStruct,
    HeroFlagStruct,
    ControlledMinionsStruct,
    PartyMoraleLinkStruct,
    PetInfoStruct, ProfessionStateStruct,
    SkillbarStruct,DupeSkillStruct,
    AgentNameInfoStruct, MissionMapIconStruct, NPC_ModelStruct,
    PlayerStruct,TitleStruct,TitleTierStruct,
)

from Py4GWCoreLib.native_src.context.PartyContext import (
    PartyContextStruct,PartyContext,
    PartyInfoStruct,
    PlayerPartyMember,
    HenchmanPartyMember,
    HeroPartyMember,PartySearchStruct
    
)

from Py4GWCoreLib.native_src.context.InstanceInfoContext import (
    InstanceInfoStruct,
    MapDimensionsStruct,
    AreaInfoStruct,
    InstanceInfo,
)

from Py4GWCoreLib.native_src.context.MapContext import (
    MapContext, MapContextStruct,
)

from Py4GWCoreLib.native_src.context.CharContext import (CharContextStruct, CharContext, ProgressBar)


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
        party_attributes:list[PartyAttributeStruct] | None = world_ctx.party_attributes
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

    party_effects :list[AgentEffectsStruct] | None = world_ctx.party_effects
    
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
    
    quest_log :list[QuestStruct] | None = world_ctx.quest_log
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
                
    mission_objectives :list[MissionObjectiveStruct] | None = world_ctx.mission_objectives
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

#region world_2
def draw_world_context_tab2(world_ctx: WorldContextStruct):
    account_info = world_ctx.account_info

    if not account_info:
        PyImGui.text("AccountInfo not available.")
    else:
        henchemen_ids = world_ctx.henchmen_agent_ids
        if henchemen_ids is None:
            PyImGui.text("No henchmen agent IDs available.")
        else:
            if PyImGui.collapsing_header("Henchmen List"):
                for i, agent_id in enumerate(henchemen_ids):
                    PyImGui.text(f"Henchman Agent ID[{i}]: {agent_id}")
        
    PyImGui.separator()
    
    hero_flags :list[HeroFlagStruct] | None = world_ctx.hero_flags
    if hero_flags is None:
        PyImGui.text("hero_flags: <empty>")
    else:
        if PyImGui.collapsing_header("hero_flags"):
            for i, flag in enumerate(hero_flags):
                if PyImGui.collapsing_header(f"HeroFlag[{i}]"):
                    PyImGui.text(f"hero_id: {flag.hero_id}")
                    PyImGui.text(f"agent_id: {flag.agent_id}")
                    PyImGui.text(f"level: {flag.level}")
                    PyImGui.text(f"hero behaviour: {flag.hero_behavior}")
                    flag_vec: Vec2f | None = flag.flag
                    if flag_vec is None:
                        PyImGui.text("flag: <invalid>")
                    else:
                        PyImGui.text(f"flag x: {flag_vec.x} y: {flag_vec.y}")
                    PyImGui.separator()
    
    hero_info_list = world_ctx.hero_info
    
    if not hero_info_list:
        PyImGui.text("HeroInfo not available.")
    else:
        if PyImGui.collapsing_header("Hero Info List"):
            for i, hero_info in enumerate(hero_info_list):
                if PyImGui.collapsing_header(f"HeroInfo[{i}]"):
                    PyImGui.text(f"hero_id: {hero_info.hero_id}")
                    PyImGui.text(f"agent_id: {hero_info.agent_id}")
                    PyImGui.text(f"level: {hero_info.level}")
                    PyImGui.text(f"primary: {hero_info.primary}")
                    PyImGui.text(f"secondary: {hero_info.secondary}")
                    PyImGui.text(f"hero_file_id: {hero_info.hero_file_id}")
                    PyImGui.text(f"name: {hero_info.name_str}")
                    h001C = hero_info.h001C
                    if h001C is None:
                        PyImGui.text("h001C: <invalid>")
                    else:
                        if PyImGui.collapsing_header("h001C"):
                            for j, val in enumerate(h001C):
                                if not val:
                                    PyImGui.text(f"h001C[{j}]: {val} (void)")
                                else:
                                    PyImGui.text(f"h001C[{j}]: {val}")
                            
                    PyImGui.separator()
        
    cartographed_areas :list[int] | None = world_ctx.cartographed_areas
    if cartographed_areas is None:
        PyImGui.text("cartographed_areas: <empty>")
    else:
        if PyImGui.collapsing_header("cartographed_areas"):
            if PyImGui.button("print list to console"):
                print("Cartographed Areas IDs:")
                for i, area_id in enumerate(cartographed_areas):
                    if area_id is None:
                        print(f"Area ID[{i}]: <invalid>")
                    else:
                        print(f"Area ID[{i}]: 0x{area_id:08X}")
            for i, area_id in enumerate(cartographed_areas):
                if area_id is None:
                    PyImGui.text(f"Area ID[{i}]: <invalid>")
                else:
                    PyImGui.text(f"Area ID[{i}]: 0x{area_id:08X}")
                    
    PyImGui.separator()
    
    h05B4 :list[int] | None = world_ctx.h05B4
    if h05B4 is None:
        PyImGui.text("h05B4: <empty>")
    else:        
        if PyImGui.collapsing_header("h05B4"):
            for i, val in enumerate(world_ctx.h05B4 or []): 
                PyImGui.text(f"h05B4[{i}]: {val}")
                
    
    controlled_minions :list[ControlledMinionsStruct] | None = world_ctx.controlled_minions
    if controlled_minions is None:
        PyImGui.text("controlled_minions: <empty>")
    else:
        if PyImGui.collapsing_header("controlled_minions"):
            for i, minion in enumerate(controlled_minions):
                if PyImGui.collapsing_header(f"ControlledMinions[{i}]"):
                    PyImGui.text(f"agent_id: {minion.agent_id}")
                    PyImGui.text(f"minion_count: {minion.minion_count}")
                    PyImGui.separator()
        
    missions_completed: list[int] | None = world_ctx.missions_completed
    if missions_completed is None:
        PyImGui.text("missions_completed: <empty>")
    else:
        if PyImGui.collapsing_header("missions_completed (BITMAP: each bit = mission completed)"):
            for i, mission_mask in enumerate(missions_completed):
                PyImGui.text(
                    f"[{i:02}] mask=0x{mission_mask:08X}  bits_set={mission_mask.bit_count()}"
                )

                
    missions_bonus: list[int] | None = world_ctx.missions_bonus
    if missions_bonus is None:
        PyImGui.text("missions_bonus: <empty>")
    else:
        if PyImGui.collapsing_header("missions_bonus (BITMAP: each bit = bonus completed)"):
            for i, mission_mask in enumerate(missions_bonus):
                PyImGui.text(
                    f"[{i:02}] mask=0x{mission_mask:08X}  bits_set={mission_mask.bit_count()}"
                )

                    
    missions_completed_hm: list[int] | None = world_ctx.missions_completed_hm
    if missions_completed_hm is None:
        PyImGui.text("missions_completed_hm: <empty>")
    else:
        if PyImGui.collapsing_header("missions_completed_hm (BITMAP: each bit = HM mission completed)"):
            for i, mission_mask in enumerate(missions_completed_hm):
                PyImGui.text(
                    f"[{i:02}] mask=0x{mission_mask:08X}  bits_set={mission_mask.bit_count()}"
                )

                
    missions_bonus_hm: list[int] | None = world_ctx.missions_bonus_hm
    if missions_bonus_hm is None:
        PyImGui.text("missions_bonus_hm: <empty>")
    else:
        if PyImGui.collapsing_header("missions_bonus_hm (BITMAP: each bit = HM bonus completed)"):
            for i, mission_mask in enumerate(missions_bonus_hm):
                PyImGui.text(
                    f"[{i:02}] mask=0x{mission_mask:08X}  bits_set={mission_mask.bit_count()}"
                )

    unlocked_maps: list[int] | None = world_ctx.unlocked_maps
    if unlocked_maps is None:
        PyImGui.text("unlocked_maps: <empty>")
    else:
        if PyImGui.collapsing_header("unlocked_maps (BITMAP: each bit = map unlocked)"):
            for i, map_mask in enumerate(unlocked_maps):
                PyImGui.text(
                    f"[{i:02}] mask=0x{map_mask:08X}  bits_set={map_mask.bit_count()}"
                )
    
    h061C :list[int] | None = world_ctx.h061C
    if h061C is None:
        PyImGui.text("h061C: <empty>")
    else:        
        if PyImGui.collapsing_header("h061C"):
            for i, val in enumerate(world_ctx.h061C or []): 
                PyImGui.text(f"h061C[{i}]: {val}")
    
    player_morale = world_ctx.player_morale
    if not player_morale:
        PyImGui.text("player_morale: <empty>")
    else:
        if PyImGui.collapsing_header("player_morale"):
            PyImGui.text(f"agent_id: {player_morale.agent_id}")
            PyImGui.text(f"agent_id_dupe: {player_morale.agent_id_dupe}")
            PyImGui.text(f"morale: {player_morale.morale}")
            unk = player_morale.unk
            for i, val in enumerate(unk):
                PyImGui.text(f"unk[{i}]: {val}")
                
    PyImGui.separator()
    
    PyImGui.text(f"h028C: {world_ctx.h028C}")
    
    party_morale :list[PartyMoraleLinkStruct] | None = world_ctx.party_morale
    
    if party_morale is None:
        PyImGui.text("party_morale: <empty>")
    else:
        if PyImGui.collapsing_header("party_morale"):
            for i, link in enumerate(party_morale):
                if PyImGui.collapsing_header(f"PartyMoraleLink[{i}]"):
                    PyImGui.text(f"unk: {link.unk}")
                    PyImGui.text(f"unk2: {link.unk2}")
                    party_member_info = link.party_member_info
                    if party_member_info is None:
                        PyImGui.text("party_member_info: <invalid>")
                    else:
                        PyImGui.text(f"agent_id: {party_member_info.agent_id}")
                        PyImGui.text(f"morale: {party_member_info.morale}")
                        unk = party_member_info.unk
                        for j, val in enumerate(unk):
                            PyImGui.text(f"unk[{j}]: {val}")
                            
    h063C :list[int] | None = world_ctx.h063C
    if h063C is None:
        PyImGui.text("h063C: <empty>")
    else:        
        if PyImGui.collapsing_header("h063C"):
            for i, val in enumerate(world_ctx.h063C or []): 
                PyImGui.text(f"h063C[{i}]: {val}")
                
    h06E0_ptrs :list[int] | None = world_ctx.h06E0_ptrs
    if h06E0_ptrs is None:
        PyImGui.text("h06E0_ptrs: <empty>")
  
#region world_3                  
def draw_world_context_tab3(world_ctx: WorldContextStruct):
    PyImGui.text(f"player_number: {world_ctx.player_number}")
    if PyImGui.collapsing_header("single fields dump"):
        rows: list[tuple[str, str | int | float]] = [
            ("field0_0x0", world_ctx.player_number),
            ("field1_0x4", world_ctx.is_hard_mode_unlocked),
            ("salvage_session_id", world_ctx.salvage_session_id),
            ("playerTeamToken", world_ctx.playerTeamToken),
            ("h06DC", world_ctx.h06DC),
            ("experience", world_ctx.experience),
            ("experience_dupe", world_ctx.experience_dupe),
            ("current_kurzick", world_ctx.current_kurzick),
            ("current_kurzick_dupe", world_ctx.current_kurzick_dupe),
            ("total_earned_kurzick", world_ctx.total_earned_kurzick),
            ("total_earned_kurzick_dupe", world_ctx.total_earned_kurzick_dupe),
            ("current_luxon", world_ctx.current_luxon),
            ("current_luxon_dupe", world_ctx.current_luxon_dupe),
            ("total_earned_luxon", world_ctx.total_earned_luxon),
            ("total_earned_luxon_dupe", world_ctx.total_earned_luxon_dupe),
            ("current_imperial", world_ctx.current_imperial),
            ("current_imperial_dupe", world_ctx.current_imperial_dupe),
            ("total_earned_imperial", world_ctx.total_earned_imperial),
            ("total_earned_imperial_dupe", world_ctx.total_earned_imperial_dupe),
            ("unk_faction4", world_ctx.unk_faction4),
            ("unk_faction4_dupe", world_ctx.unk_faction4_dupe),
            ("unk_faction5", world_ctx.unk_faction5),
            ("unk_faction5_dupe", world_ctx.unk_faction5_dupe),
            ("level", world_ctx.level),
            ("level_dupe", world_ctx.level_dupe),
            ("morale", world_ctx.morale),
            ("morale_dupe", world_ctx.morale_dupe),
            ("current_balth", world_ctx.current_balth),
            ("current_balth_dupe", world_ctx.current_balth_dupe),
            ("total_earned_balth", world_ctx.total_earned_balth),
            ("total_earned_balth_dupe", world_ctx.total_earned_balth_dupe),
            ("current_skill_points", world_ctx.current_skill_points),
            ("current_skill_points_dupe", world_ctx.current_skill_points_dupe),
            ("total_earned_skill_points", world_ctx.total_earned_skill_points),
            ("total_earned_skill_points_dupe", world_ctx.total_earned_skill_points_dupe),
            ("max_kurzick", world_ctx.max_kurzick),
            ("max_luxon", world_ctx.max_luxon),
            ("max_balth", world_ctx.max_balth),
            ("max_imperial", world_ctx.max_imperial),
            ("equipment_status", world_ctx.equipment_status),
            ("foes_killed", world_ctx.foes_killed),
            ("foes_to_kill", world_ctx.foes_to_kill)
        ]
        draw_kv_table("WorldContextStruct2", rows)
    PyImGui.separator()
    if PyImGui.collapsing_header("PlayerControlledCharacter"):
        player_controlled_char = world_ctx.player_controlled_character
        if not player_controlled_char:
            PyImGui.text("PlayerControlledCharacter not available.")
        else:
            rows: list[tuple[str, str | int | float]] = [
                ("field0_0x0", player_controlled_char.field0_0x0),
                ("field1_0x4", player_controlled_char.field1_0x4),
                ("field2_0x8", player_controlled_char.field2_0x8),
                ("field3_0xc", player_controlled_char.field3_0xc),
                ("field4_0x10", player_controlled_char.field4_0x10),
                ("agent_id", player_controlled_char.agent_id),
                ("composite_id", player_controlled_char.composite_id),
                ("field7_0x1c", player_controlled_char.field7_0x1c),
                ("field8_0x20", player_controlled_char.field8_0x20),
                ("field9_0x24", player_controlled_char.field9_0x24),
                ("field10_0x28", player_controlled_char.field10_0x28),
                ("field11_0x2c", player_controlled_char.field11_0x2c),
                ("field12_0x30", player_controlled_char.field12_0x30),
                ("field13_0x34", player_controlled_char.field13_0x34),
                ("field14_0x38", player_controlled_char.field14_0x38),
                ("field15_0x3c", player_controlled_char.field15_0x3c),
                ("field16_0x40", player_controlled_char.field16_0x40),
                ("field17_0x44", player_controlled_char.field17_0x44),
                ("field18_0x48", player_controlled_char.field18_0x48),
                ("field19_0x4c", player_controlled_char.field19_0x4c),
                ("field20_0x50", player_controlled_char.field20_0x50),
                ("field21_0x54", player_controlled_char.field21_0x54),
                ("field22_0x58", player_controlled_char.field22_0x58),
                ("field23_0x5c", player_controlled_char.field23_0x5c),
                ("field24_0x60", player_controlled_char.field24_0x60),
                ("more_flags", player_controlled_char.more_flags),
                ("field26_0x68", player_controlled_char.field26_0x68),
                ("field27_0x6c", player_controlled_char.field27_0x6c),
                ("field28_0x70", player_controlled_char.field28_0x70),
                ("field29_0x74", player_controlled_char.field29_0x74),
                ("field30_0x78", player_controlled_char.field30_0x78),
                ("field31_0x7c", player_controlled_char.field31_0x7c),
                ("field32_0x80", player_controlled_char.field32_0x80),
                ("field33_0x84", player_controlled_char.field33_0x84),
                ("field34_0x88", player_controlled_char.field34_0x88),
                ("field35_0x8c", player_controlled_char.field35_0x8c),
                ("field36_0x90", player_controlled_char.field36_0x90),
                ("field37_0x94", player_controlled_char.field37_0x94),
                ("field38_0x98", player_controlled_char.field38_0x98),
                ("field39_0x9c", player_controlled_char.field39_0x9c),
                ("field40_0xa0", player_controlled_char.field40_0xa0),
                ("field41_0xa4", player_controlled_char.field41_0xa4),
                ("field42_0xa8", player_controlled_char.field42_0xa8),
                ("field43_0xac", player_controlled_char.field43_0xac),
                ("field44_0xb0", player_controlled_char.field44_0xb0),
                ("field45_0xb4", player_controlled_char.field45_0xb4),
                ("field46_0xb8", player_controlled_char.field46_0xb8),
                ("field47_0xbc", player_controlled_char.field47_0xbc),
                ("field48_0xc0", player_controlled_char.field48_0xc0),
                ("field49_0xc4", player_controlled_char.field49_0xc4),
                ("field50_0xc8", player_controlled_char.field50_0xc8),
                ("field51_0xcc", player_controlled_char.field51_0xcc),
                ("field52_0xd0", player_controlled_char.field52_0xd0),
                ("field53_0xd4", player_controlled_char.field53_0xd4),
                ("field54_0xd8", player_controlled_char.field54_0xd8),
                ("field55_0xdc", player_controlled_char.field55_0xdc),
                ("field56_0xe0", player_controlled_char.field56_0xe0),
                ("field57_0xe4", player_controlled_char.field57_0xe4),
                ("field58_0xe8", player_controlled_char.field58_0xe8),
                ("field59_0xec", player_controlled_char.field59_0xec),
                ("field60_0xf0", player_controlled_char.field60_0xf0),
                ("field61_0xf4", player_controlled_char.field61_0xf4),
                ("field62_0xf8", player_controlled_char.field62_0xf8),
                ("field63_0xfc", player_controlled_char.field63_0xfc),
                ("field64_0x100", player_controlled_char.field64_0x100),
                ("field65_0x104", player_controlled_char.field65_0x104),
                ("field66_0x108", player_controlled_char.field66_0x108),
                ("flags", player_controlled_char.flags),
                ("field68_0x110", player_controlled_char.field68_0x110),
                ("field69_0x114", player_controlled_char.field69_0x114),
                ("field70_0x118", player_controlled_char.field70_0x118),
                ("field71_0x11c", player_controlled_char.field71_0x11c),
                ("field72_0x120", player_controlled_char.field72_0x120),
                ("field73_0x124", player_controlled_char.field73_0x124),
                ("field74_0x128", player_controlled_char.field74_0x128),
                ("field75_0x12c", player_controlled_char.field75_0x12c),
                ("field76_0x130", player_controlled_char.field76_0x130),
            ]

            draw_kv_table("WorldMapTable", rows)   

    PyImGui.separator()
    
    h0688 :list[int] | None = world_ctx.h0688
    if h0688 is None:
        PyImGui.text("h0688: <empty>")
    else:        
        if PyImGui.collapsing_header("h0688"):
            for i, val in enumerate(world_ctx.h0688 or []): 
                PyImGui.text(f"h0688[{i}]: {val}")
                
    h0694 :list[int] | None = world_ctx.h0694
    if h0694 is None:
        PyImGui.text("h0694: <empty>")
    else:        
        if PyImGui.collapsing_header("h0694"):
            for i, val in enumerate(world_ctx.h0694 or []): 
                PyImGui.text(f"h0694[{i}]: {val}")
    
    pets :list[PetInfoStruct] | None = world_ctx.pets
    if pets is None:
        PyImGui.text("pets: <empty>")
    else:
        if PyImGui.collapsing_header("pets"):
            for i, pet in enumerate(pets):
                if PyImGui.collapsing_header(f"PetInfo[{i}]"):
                    PyImGui.text(f"agent_id: {pet.agent_id}")
                    PyImGui.text(f"owner_agent_id: {pet.owner_agent_id}")
                    PyImGui.text(f"pet_name_str: {pet.pet_name_str}")
                    PyImGui.text(f"model_file_id1: {pet.model_file_id1}")
                    PyImGui.text(f"model_file_id2: {pet.model_file_id2}")
                    PyImGui.text(f"behavior: {pet.behavior}")
                    PyImGui.text(f"locked_target_id: {pet.locked_target_id}")
                    PyImGui.separator()
                    
    party_profession_states :list[ProfessionStateStruct] | None = world_ctx.party_profession_states    
    if party_profession_states is None:
        PyImGui.text("party_profession_states: <empty>")
    else:
        if PyImGui.collapsing_header("party_profession_states"):
            for i, prof_state in enumerate(party_profession_states):
                if PyImGui.collapsing_header(f"ProfessionState[{i}]"):
                    PyImGui.text(f"agent_id: {prof_state.agent_id}")
                    PyImGui.text(f"primary: {prof_state.primary}")
                    PyImGui.text(f"secondary: {prof_state.secondary}")
                    PyImGui.text(f"unlocked_professions: {hex(prof_state.unlocked_professions)}")
                    PyImGui.separator()   
                    
    h06CC_ptrs :list[int] | None = world_ctx.h06CC_ptrs
    if h06CC_ptrs is None:
        PyImGui.text("h06CC_ptrs: <empty>")
    else:        
        if PyImGui.collapsing_header("h06CC_ptrs"):
            for i, val in enumerate(world_ctx.h06CC_ptrs or []): 
                PyImGui.text(f"h06CC_ptrs[{i}]: {val}")    
                
    party_skillbars :list[SkillbarStruct] | None = world_ctx.party_skillbars     
    if party_skillbars is None:
        PyImGui.text("party_skillbars: <empty>")
    else:
        if PyImGui.collapsing_header("party_skillbars"):
            for i, skillbar in enumerate(party_skillbars):
                if PyImGui.collapsing_header(f"Skillbar[{i}]"):
                    true_false_text(skillbar.is_valid)
                    PyImGui.text(f"agent_id: {skillbar.agent_id}")
                    PyImGui.text(f"disabled: {skillbar.disabled}")
                    PyImGui.text(f"h00B8: {skillbar.h00B8}")
                    
                    casted_skills = skillbar.casted_skills
                    if not casted_skills:
                        PyImGui.text("No casted skills available.")
                        PyImGui.separator()
                    else:
                        for j, casted_skill in enumerate(casted_skills):
                            if PyImGui.collapsing_header(f"CastedSkill[{j}]"):
                                PyImGui.text(f"h0000: {casted_skill.h0000}")
                                PyImGui.text(f"skill_id: {casted_skill.skill_id}")
                                PyImGui.text(f"h0004: {casted_skill.h0004}")
                                PyImGui.separator()
                    
                    skills = skillbar.skills
                    if not skills:
                        PyImGui.text("No skills available.")
                        PyImGui.separator()
                    else:
                        for j, skill in enumerate(skills):
                            if PyImGui.collapsing_header(f"Skill[{j}]"):
                                PyImGui.text(f"adrenaline_a: {skill.adrenaline_a}")
                                PyImGui.text(f"adrenaline_b: {skill.adrenaline_b}")
                                PyImGui.text(f"recharge: {skill.recharge}")
                                PyImGui.text(f"skill_id: {skill.skill_id}")
                                PyImGui.text(f"event: {skill.event}")
                                PyImGui.separator()
                                

                    
                    PyImGui.separator()
    
    learnable_character_skills :list[int] | None = world_ctx.learnable_character_skills
    
    if learnable_character_skills is None:
        PyImGui.text("learnable_character_skills: <empty>")
    else:
        if PyImGui.collapsing_header("learnable_character_skills"):
            for i, skill_id in enumerate(learnable_character_skills):
                PyImGui.text(f"learnable_character_skill[{i}]: {skill_id}")
                
    unlocked_character_skills :list[int] | None = world_ctx.unlocked_character_skills
    if unlocked_character_skills is None:
        PyImGui.text("unlocked_character_skills: <empty>")
    else:
        if PyImGui.collapsing_header("unlocked_character_skills"):
            for i, skill_id in enumerate(unlocked_character_skills):
                PyImGui.text(f"unlocked_character_skill[{i}]: {hex(skill_id)}")
                
    duplicated_character_skills :list[DupeSkillStruct] | None = world_ctx.duplicated_character_skills
    if duplicated_character_skills is None:
        PyImGui.text("duplicated_character_skills: <empty>")
    else:
        if PyImGui.collapsing_header("duplicated_character_skills"):
            for i, dupe_skill in enumerate(duplicated_character_skills):
                if PyImGui.collapsing_header(f"DupeSkill[{i}]"):
                    PyImGui.text(f"skill_id: {dupe_skill.skill_id}")
                    PyImGui.text(f"count: {dupe_skill.count}")
                    PyImGui.separator()

    h0730_ptrs :list[int] | None = world_ctx.h0730_ptrs
    if h0730_ptrs is None:
        PyImGui.text("h0730_ptrs: <empty>")
    else:        
        if PyImGui.collapsing_header("h0730_ptrs"):
            for i, val in enumerate(world_ctx.h0730_ptrs or []): 
                PyImGui.text(f"h0730_ptrs[{i}]: {val}")
                
    agent_name_infos :list[AgentNameInfoStruct] | None = world_ctx.agent_name_info
    if agent_name_infos is None:
        PyImGui.text("agent_name_infos: <empty>")
    else:
        if PyImGui.collapsing_header("agent_name_infos"):
            for i, agent_info in enumerate(agent_name_infos):
                if PyImGui.collapsing_header(f"AgentNameInfo[{i}]"):
                    PyImGui.text(f"name_str: {agent_info.name_str}")
                    h0000_ptrs = agent_info.h0000
                    if h0000_ptrs is None:
                        PyImGui.text("h0000_ptrs: <empty>")
                    else:        
                        if PyImGui.collapsing_header("h0000_ptrs"):
                            for j, val in enumerate(h0000_ptrs): 
                                PyImGui.text(f"h0000_ptrs[{j}]: {val}")
                    PyImGui.separator()
                
    h07DC_ptrs :list[int] | None = world_ctx.h07DC_ptrs
    if h07DC_ptrs is None:
        PyImGui.text("h07DC_ptrs: <empty>")
    else:        
        if PyImGui.collapsing_header("h07DC_ptrs"):
            for i, val in enumerate(world_ctx.h07DC_ptrs or []): 
                PyImGui.text(f"h07DC_ptrs[{i}]: {val}")
                
    mission_map_icons :list[MissionMapIconStruct] | None = world_ctx.mission_map_icons
    
    if mission_map_icons is None:
        PyImGui.text("mission_map_icons: <empty>")
    else:
        if PyImGui.collapsing_header("mission_map_icons"):
            for i, icon in enumerate(mission_map_icons):
                if PyImGui.collapsing_header(f"MissionMapIcon[{i}]"):
                    PyImGui.text(f"index: {icon.index}")
                    PyImGui.text(f"X: {icon.X}")
                    PyImGui.text(f"Y: {icon.Y}")
                    PyImGui.text(f"h000C: {icon.h000C}")
                    PyImGui.text(f"h0010: {icon.h0010}")
                    PyImGui.text(f"option: {icon.option}")
                    PyImGui.text(f"h0018: {icon.h0018}")
                    PyImGui.text(f"model_id: {icon.model_id}")
                    PyImGui.text(f"h0020: {icon.h0020}")
                    PyImGui.text(f"h0024: {icon.h0024}")
                    PyImGui.separator()
                
    npcs :list[NPC_ModelStruct] | None = world_ctx.npc_models
    if npcs is None:
        PyImGui.text("npcs: <empty>")
    else:
        if PyImGui.collapsing_header("npcs"):
            for i, npc in enumerate(npcs):
                if npc is None or not npc.is_valid:
                    continue
                if PyImGui.collapsing_header(f"NPC[{i}]"):
                    PyImGui.text(f"model_file_id: {npc.model_file_id}")
                    PyImGui.text(f"h0004: {npc.h0004}")
                    PyImGui.text(f"scale: {npc.scale}")
                    PyImGui.text(f"sex: {npc.sex}")
                    PyImGui.text(f"npc_flags: {hex(npc.npc_flags)}")
                    PyImGui.text(f"primary: {npc.primary}")
                    PyImGui.text(f"h0018: {npc.h0018}")
                    PyImGui.text(f"default_level: {npc.default_level}")
                    PyImGui.text(f"padding1: {npc.padding1}")
                    PyImGui.text(f"padding2: {npc.padding2}")
                    PyImGui.text(f"name_str: {npc.name_str}")
                    PyImGui.text(f"files_count: {npc.files_count}")
                    PyImGui.text(f"files_capacity: {npc.files_capacity}")
                    PyImGui.text(f"is_henchman: "); PyImGui.same_line(0,-1); true_false_text(npc.is_henchman)
                    PyImGui.text(f"is_hero: "); PyImGui.same_line(0,-1); true_false_text(npc.is_hero)
                    PyImGui.text(f"is_spirit"); PyImGui.same_line(0,-1); true_false_text(npc.is_spirit)
                    PyImGui.text(f"is_minion"); PyImGui.same_line(0,-1); true_false_text(npc.is_minion)
                    PyImGui.text(f"is_pet"); PyImGui.same_line(0,-1); true_false_text(npc.is_pet)
                    model_files = npc.model_files

                    if not model_files:
                        PyImGui.text("model_files: <empty>")
                    else:
                        if PyImGui.collapsing_header("model_files"):
                            for j, file_id in enumerate(model_files):
                                PyImGui.text(f"model_file[{j}]: {file_id}")
                    PyImGui.separator()
                
    players :list[PlayerStruct] | None = world_ctx.players
    if players is None:
        PyImGui.text("players: <empty>")
    else:
        if PyImGui.collapsing_header("players"):
            for i, player in enumerate(players):
                if PyImGui.collapsing_header(f"Player[{i}]"):
                    PyImGui.text(f"agent_id: {player.agent_id}")
                    PyImGui.text(f"appearance_bitmap: {hex(player.appearance_bitmap)}")
                    PyImGui.text(f"flags: {hex(player.flags)}")
                    PyImGui.text(f"primary: {player.primary}")
                    PyImGui.text(f"secondary: {player.secondary}")
                    PyImGui.text(f"h0020: {player.h0020}")
                    PyImGui.text(f"name_enc: {player.name_enc_str}")
                    PyImGui.text(f"name: {player.name_str}")
                    PyImGui.text(f"party_leader_player_number: {player.party_leader_player_number}")
                    PyImGui.text(f"active_title_tier: {player.active_title_tier}")
                    PyImGui.text(f"reforged_or_dhuums_flags: {player.reforged_or_dhuums_flags}")
                    PyImGui.text(f"player_number: {player.player_number}")
                    PyImGui.text(f"party_size: {player.party_size}")
                    PyImGui.text(f"is_pvp: "); PyImGui.same_line(0,-1); true_false_text(player.is_pvp)
                    
                    h0004_ptrs :list[int] | None = player.h0004
                    if h0004_ptrs is None:
                        PyImGui.text("h0004_ptrs: <empty>")
                    else:        
                        if PyImGui.collapsing_header("h0004_ptrs"):
                            for j, val in enumerate(h0004_ptrs): 
                                PyImGui.text(f"h0004_ptrs[{j}]: {val}")
                    
                    
                    h0040_ptrs = player.h0040_ptrs
                    if h0040_ptrs is None:
                        PyImGui.text("h0040_ptrs: <empty>")
                    else:        
                        if PyImGui.collapsing_header("h0040_ptrs"):
                            for j, val in enumerate(h0040_ptrs): 
                                PyImGui.text(f"h0040_ptrs[{j}]: {val}")
                    PyImGui.separator()
                
    titles :list[TitleStruct] | None = world_ctx.titles
    if titles is None:
        PyImGui.text("titles: <empty>")
    else:
        if PyImGui.collapsing_header("titles"):
            for i, title in enumerate(titles):
                if PyImGui.collapsing_header(f"Title[{i}]"):
                    PyImGui.text(f"props: {title.props}")
                    PyImGui.text(f"current_points: {title.current_points}")
                    PyImGui.text(f"current_title_tier_index: {title.current_title_tier_index}")
                    PyImGui.text(f"points_needed_current_rank: {title.points_needed_current_rank}")
                    PyImGui.text(f"next_title_tier_index: {title.next_title_tier_index}")
                    PyImGui.text(f"points_needed_next_rank: {title.points_needed_next_rank}")
                    PyImGui.text(f"max_title_rank: {title.max_title_rank}")
                    PyImGui.text(f"max_title_tier_index: {title.max_title_tier_index}")
                    PyImGui.text(f"points_desc_str: {title.points_desc_str}")
                    PyImGui.text(f"h0028_str: {title.h0028_str}")
                    PyImGui.separator()
                    
    title_tiers :list[TitleTierStruct] | None = world_ctx.title_tiers
    if title_tiers is None:
        PyImGui.text("title_tiers: <empty>")
    else:
        if PyImGui.collapsing_header("title_tiers"):
            for i, tier in enumerate(title_tiers):
                if not tier.is_valid:
                    continue
                if PyImGui.collapsing_header(f"TitleTier[{i}]"):
                    PyImGui.text(f"props: {tier.props}")
                    PyImGui.text(f"tier_number: {tier.tier_number}")
                    PyImGui.text(f"tier_name_str: {tier.tier_name_str}")
                    PyImGui.separator()
                    
    vanquished_areas :list[int] | None = world_ctx.vanquished_areas
    if vanquished_areas is None:
        PyImGui.text("vanquished_areas: <empty>")
    else:
        if PyImGui.collapsing_header("vanquished_areas (BITMAP: each bit = area vanquished)"):
            for i, area_mask in enumerate(vanquished_areas):
                PyImGui.text(
                    f"[{i:02}] mask=0x{area_mask:08X}  bits_set={area_mask.bit_count()}"
                )
                
#region party_context_tab
def draw_party_context_tab(party_ctx: PartyContextStruct):
    # ---- Main PartyContext fields ----
    rows: list[tuple[str, str | int | float]] = [
        ("h0000", party_ctx.h0000),
        ("flag", party_ctx.flag),
        ("h0018", party_ctx.h0018),
        ("requests_count", party_ctx.requests_count),
        ("sending_count", party_ctx.sending_count),
        ("h003C", party_ctx.h003C),
        ("h0050", party_ctx.h0050),
        
    ]
    draw_kv_table("PartyContextTable", rows)
    
    h0004_ptrs :list[int] | None = party_ctx.h0004_ptrs
    if h0004_ptrs is None:
        PyImGui.text("h0004_ptrs: <empty>")
    else:        
        if PyImGui.collapsing_header("h0004_ptrs"):
            for i, val in enumerate(party_ctx.h0004_ptrs or []): 
                PyImGui.text(f"h0004_ptrs[{i}]: {val}")
    
    PyImGui.separator()
    player_party = party_ctx.player_party
    if not player_party:
        PyImGui.text("player_party: <invalid>")
    else:
        PyImGui.text("player_party:")
        PyImGui.text(f"party_id: {player_party.party_id}")
        players :list[PlayerPartyMember] | None = player_party.players
        if players is None:
            PyImGui.text("players: <empty>")    
        else:
            if PyImGui.collapsing_header("players"):
                for i, player in enumerate(players):
                    if PyImGui.collapsing_header(f"PlayerPartyMember[{i}]"):
                        PyImGui.text(f"login_number: {player.login_number}")
                        PyImGui.text(f"called_target_id: {player.called_target_id}")
                        PyImGui.text(f"state: {player.state}")
                        PyImGui.separator()
                        
        heroes :list[HeroPartyMember] | None = player_party.heroes
        if heroes is None:
            PyImGui.text("heroes: <empty>")
        else:
            if PyImGui.collapsing_header("heroes"):
                for i, hero in enumerate(heroes):
                    if PyImGui.collapsing_header(f"HeroPartyMember[{i}]"):
                        PyImGui.text(f"agent_id: {hero.agent_id}")
                        PyImGui.text(f"owner_player_id: {hero.owner_player_id}")
                        PyImGui.text(f"hero_id: {hero.hero_id}")
                        PyImGui.text(f"state: {hero.h000C}")
                        PyImGui.text(f"state: {hero.h0010}")
                        PyImGui.text(f"state: {hero.level}")
                        PyImGui.separator()
                        
        henchman :list[HenchmanPartyMember] | None = player_party.henchmen
        if henchman is None:
            PyImGui.text("henchman: <empty>")
        else:
            if PyImGui.collapsing_header("henchman"):
                for i, hench in enumerate(henchman):
                    if PyImGui.collapsing_header(f"HenchmanPartyMember[{i}]"):
                        PyImGui.text(f"agent_id: {hench.agent_id}")
                        PyImGui.text(f"profession: {hench.profession}")
                        PyImGui.text(f"level: {hench.level}")
                        h0004 :list[int] | None = hench.h0004
                        if h0004 is None:
                            PyImGui.text("h0004: <empty>")
                        else:        
                            if PyImGui.collapsing_header("h0004"):
                                for j, val in enumerate(hench.h0004 or []): 
                                    PyImGui.text(f"h0004[{j}]: {val}")
                                    
                        PyImGui.separator()
                        
        others :list[int] | None = player_party.others
        if others is None:
            PyImGui.text("others: <empty>")
        else:        
            if PyImGui.collapsing_header("others"):
                for i, val in enumerate(player_party.others or []): 
                    PyImGui.text(f"others[{i}]: {val}")
                    
        h0044 :list[int] | None = player_party.h0044
        if h0044 is None:
            PyImGui.text("h0044: <empty>")
        else:        
            if PyImGui.collapsing_header("h0044"):
                for i, val in enumerate(player_party.h0044 or []): 
                    PyImGui.text(f"h0044[{i}]: {val}")
        
    PyImGui.separator()
        
    party_searches :list[PartySearchStruct] | None = party_ctx.party_searches
    if party_searches is None:
        PyImGui.text("party_searches: <empty>")
    else:
        if PyImGui.collapsing_header("party_searches"):
            for i, search in enumerate(party_searches):
                if PyImGui.collapsing_header(f"PartySearchStruct[{i}]"):
                    PyImGui.text(f"party_search_id: {search.party_search_id}")
                    PyImGui.text(f"party_search_type: {hex(search.party_search_type)}")
                    PyImGui.text(f"hardmode: {search.hardmode}")
                    PyImGui.text(f"district: {search.district}")
                    PyImGui.text(f"language: {search.language}")
                    PyImGui.text(f"party_size: {search.party_size}")
                    PyImGui.text(f"hero_count: {search.hero_count}")
                    PyImGui.text(f"message: {search.message_str}")
                    PyImGui.text(f"party_leader: {search.party_leader_str}")
                    PyImGui.text(f"primary: {search.primary}")
                    PyImGui.text(f"secondary: {search.secondary}")
                    PyImGui.text(f"level: {search.level}")
                    PyImGui.text(f"timestamp: {search.timestamp}")
                    PyImGui.separator()
    
    
    PyImGui.separator()             
    
#region InstanceInfoPtr
def draw_InstanceInfoPtr_tab(instance_info_ptr: InstanceInfoStruct):
    # ---- Main PartyContext fields ----
    rows: list[tuple[str, str | int | float]] = [
        ("instance_type", instance_info_ptr.instance_type),
        ("terrain_count", instance_info_ptr.terrain_count),    
    ]
    draw_kv_table("InstanceInfoTable", rows)
    
    current_map_info: AreaInfoStruct | None= instance_info_ptr.current_map_info
    if not current_map_info:
        PyImGui.text("current_map_info: <invalid>")
    else:
        PyImGui.text("current_map_info:")
        rows: list[tuple[str, str | int | float]] = [
            ("campaign", current_map_info.campaign),
            ("continent", current_map_info.continent),
            ("region", current_map_info.region),
            ("type", current_map_info.type),
            ("flags", current_map_info.flags),
            ("thumbnail_id", current_map_info.thumbnail_id),
            ("min_party_size", current_map_info.min_party_size),
            ("max_party_size", current_map_info.max_party_size),
            ("min_player_size", current_map_info.min_player_size),
            ("max_player_size", current_map_info.max_player_size),
            ("controlled_outpost_id", current_map_info.controlled_outpost_id),
            ("fraction_mission", current_map_info.fraction_mission),
            ("min_level", current_map_info.min_level),
            ("min_level", current_map_info.min_level),
            ("max_level", current_map_info.max_level),
            ("needed_pq", current_map_info.needed_pq),
            ("mission_maps_to", current_map_info.mission_maps_to),
            ("x", current_map_info.x),
            ("y", current_map_info.y),
            ("icon_start_x", current_map_info.icon_start_x),
            ("icon_start_y", current_map_info.icon_start_y),
            ("icon_end_x", current_map_info.icon_end_x),
            ("icon_end_y", current_map_info.icon_end_y),
            ("icon_start_x_dupe", current_map_info.icon_start_x_dupe),
            ("icon_start_y_dupe", current_map_info.icon_start_y_dupe),
            ("icon_end_x_dupe", current_map_info.icon_end_x_dupe),
            ("icon_end_y_dupe", current_map_info.icon_end_y_dupe),
            ("file_id", current_map_info.file_id),
            ("mission_chronology", current_map_info.mission_chronology),
            ("ha_map_chronology", current_map_info.ha_map_chronology),
            ("name_id", current_map_info.name_id),
            ("description_id", current_map_info.description_id),
            ("file_id1", current_map_info.file_id1),
            ("file_id2", current_map_info.file_id2),
            ("has_enter_button", current_map_info.has_enter_button),
            ("is_on_world_map", current_map_info.is_on_world_map),
            ("is_pvp", current_map_info.is_pvp),
            ("is_guild_hall", current_map_info.is_guild_hall),
            ("is_vanquishable_area", current_map_info.is_vanquishable_area),
            ("is_unlockable", current_map_info.is_unlockable),
            ("has_mission_maps_to", current_map_info.has_mission_maps_to)
        ]
        draw_kv_table("CurrentMapInfoTable", rows)
   
#region MapContext   
def draw_MapContext_tab(map_context_ptr: MapContextStruct):
    # ---- Main PartyContext fields ----
    map_boundaries: list[float] = map_context_ptr.map_boundaries
    if not map_boundaries:
        PyImGui.text("map_boundaries: <invalid>")
    else:
        PyImGui.text("map_boundaries:")
        for i, boundary in enumerate(map_boundaries):
            PyImGui.text(f"boundary[{i}]: {boundary}")

    
#region CharContext   
def draw_CharContext_tab(char_context_ptr: CharContextStruct):
    # ---- Main PartyContext fields ----
    player_uuid: list[int] = char_context_ptr.player_uuid
    if not player_uuid:
        PyImGui.text("player_uuid: <invalid>")
    else:
        PyImGui.text("player_uuid:")
        for i, byte in enumerate(player_uuid):
            PyImGui.text(f"byte[{i}]: {byte}")
            
        current_map_id = char_context_ptr.current_map_id
        observe_map_id = char_context_ptr.observe_map_id
        PyImGui.text(f"current_map_id: {current_map_id}")
        PyImGui.text(f"observe_map_id: {observe_map_id}")
        is_observing = current_map_id != observe_map_id
        PyImGui.text("is_observing: "); PyImGui.same_line(0,-1); true_false_text(is_observing)

    
#region draw_window
_selected_view: str = "World Map Context"

VIEW_LIST = [
    "World Map Context",
    "Mission Map Context",
    "Gameplay Context",
    "PreGame Context",
    "World Context #1",
    "World Context #2",
    "World Context #3",
    "Party Context",
    "InstanceInfoPtr",
    "Map Context",
    "Char Context"
]

  
def draw_window():
    global _selected_view

    if PyImGui.begin("Memory Viewer", True, PyImGui.WindowFlags.AlwaysAutoResize):

        # ================= LEFT PANEL =================
        PyImGui.begin_child(
            "left_panel",
            (180.0, 600.0),   # fixed width, full height
            True,
            0
        )

        PyImGui.text("Views")
        PyImGui.separator()

        for name in VIEW_LIST:
            if PyImGui.selectable(
                name,
                _selected_view == name,
                PyImGui.SelectableFlags.NoFlag,
                (0.0, 0.0)
            ):
                _selected_view = name

        PyImGui.end_child()

        PyImGui.same_line(0,-1)

        # ================= RIGHT PANEL =================
        PyImGui.begin_child(
            "right_panel",
            (600.0, 0.0),     # take remaining space
            False,
            0
        )

        # ==================================================
        # World Map Context
        # ==================================================
        if _selected_view == "World Map Context":
            world_map_ptr: WorldMapContextStruct | None = WorldMapContext.get_context()
            if not world_map_ptr:
                PyImGui.text("WorldMapContext not available.")
            else:
                draw_world_map_context_tab(world_map_ptr)

        # ==================================================
        # Mission Map Context
        # ==================================================
        elif _selected_view == "Mission Map Context":
            mission_map_ptr: MissionMapContextStruct | None = MissionMapContext.get_context()
            if not mission_map_ptr:
                PyImGui.text("MissionMapContext not available.")
            else:
                draw_mission_map_context_tab(mission_map_ptr)

        # ==================================================
        # Gameplay Context
        # ==================================================
        elif _selected_view == "Gameplay Context":
            gameplay_ctx: GameplayContextStruct | None = GameplayContext.get_context()
            if not gameplay_ctx:
                PyImGui.text("GameplayContext not available.")
            else:
                draw_gameplay_context_tab(gameplay_ctx)

        # ==================================================
        # PreGame Context
        # ==================================================
        elif _selected_view == "PreGame Context":
            pregame_ctx: PreGameContextStruct | None = PreGameContext.get_context()
            if not pregame_ctx:
                PyImGui.text("PreGameContext not available.")
            else:
                draw_pregame_context_tab(pregame_ctx)

        # ==================================================
        # World Context #1
        # ==================================================
        elif _selected_view == "World Context #1":
            world_ctx: WorldContextStruct | None = WorldContext.get_context()
            if not world_ctx:
                PyImGui.text("WorldContext not available.")
            else:
                draw_world_context_tab(world_ctx)

        # ==================================================
        # World Context #2
        # ==================================================
        elif _selected_view == "World Context #2":
            world_ctx: WorldContextStruct | None = WorldContext.get_context()
            if not world_ctx:
                PyImGui.text("WorldContext not available.")
            else:
                draw_world_context_tab2(world_ctx)
                
        # ==================================================
        # World Context #3
        # ==================================================
        elif _selected_view == "World Context #3":
            world_ctx: WorldContextStruct | None = WorldContext.get_context()
            if not world_ctx:
                PyImGui.text("WorldContext not available.")
            else:
                draw_world_context_tab3(world_ctx)
        
        # ==================================================
        # Party Context
        # ==================================================
        elif _selected_view == "Party Context":
            party_ctx: PartyContextStruct | None = PartyContext.get_context()
            if not party_ctx:
                PyImGui.text("PartyContext not available.")
            else:
                draw_party_context_tab(party_ctx)
                
        # ==================================================
        # InstanceInfoPtr Context
        # ==================================================
        elif _selected_view == "InstanceInfoPtr":
            instance_info_ptr: InstanceInfoStruct | None = InstanceInfo.get_context()
            if not instance_info_ptr:
                PyImGui.text("InstanceInfoPtr not available.")
            else:
                draw_InstanceInfoPtr_tab(instance_info_ptr)
                
        # ==================================================
        # Map Context
        # ==================================================
        elif _selected_view == "Map Context":
            map_context_ptr: MapContextStruct | None = MapContext.get_context()
            if not map_context_ptr:
                PyImGui.text("MapContext not available.")
            else:
                draw_MapContext_tab(map_context_ptr)
                
        # ==================================================
        # Char Context
        # ==================================================
        elif _selected_view == "Char Context":
            char_context_ptr: CharContextStruct | None = CharContext.get_context()
            if not char_context_ptr:
                PyImGui.text("CharContext not available.")
            else:
                draw_CharContext_tab(char_context_ptr)
                

        PyImGui.end_child()

    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()

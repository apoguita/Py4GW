import json
import os
import struct
import ctypes

from Py4GWCoreLib import *


MODULE_NAME = "AgentEnemyDebugDump"
SAMPLE_DB_PATH = os.path.join(
    os.path.dirname(__file__) if "__file__" in globals() else ".",
    "AgentEnemyDebugDump_samples.json",
)
KNOWN_FLESH_LABELS = {
    149: "fleshy",
    152: "fleshy",
    153: "fleshy",
    154: "fleshy",
    155: "fleshy",
    157: "fleshy",
    160: "fleshy",
    161: "fleshy",
    163: "fleshy",
    165: "fleshy",
    5834: "fleshy",
    6531: "fleshy",
    6532: "fleshy",
    6533: "fleshy",
    6534: "fleshy",
    6535: "fleshy",
    6536: "fleshy",
    6537: "fleshy",
    6538: "fleshy",
    6539: "fleshy",
}
KNOWN_NONFLESH_LABELS = {
    5769: "non_fleshy",
    6528: "non_fleshy",
    6529: "non_fleshy",
    6541: "non_fleshy",
}

OBSERVED_MODEL_SUMMARY = {}
_CURRENT_DUMP_ENEMY_IDS = set()
_CURRENT_DUMP_DEAD_ENEMY_IDS = set()
_PAGE_NOACCESS = 0x01
_PAGE_GUARD = 0x100
_MEM_COMMIT = 0x1000


class _MemoryBasicInformation(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]


COMPARE_FIELDS = (
    "type_map",
    "effects",
    "corpse_state",
    "corpse_signature",
    "is_dead",
    "is_dead_by_type_map",
    "is_exploitable",
    "max_hp",
    "condition_bits",
    "spirit_type",
    "model_state",
    "anim_code",
    "anim_id",
    "animation_speed",
    "weapon_attack_speed",
    "weapon_type",
    "weapon_item_type",
    "offhand_item_type",
    "h00D4_2",
    "h00E4_0",
    "h00E4_target_0_15",
    "h00E4_target_1",
    "h00E4_target_5",
    "h00E4_target_6",
    "h00E4_target_8",
    "h00E4_target_9",
    "h00E4_target_10",
    "h00E4_target_14",
    "base_name_properties",
    "base_visual_effects",
    "base_h0092",
    "base_h0094",
    "base_size",
    "equipment",
    "equip_maps",
    "tag_data",
)


def _hex(value: int, width: int = 8) -> str:
    return f"0x{int(value) & ((1 << (width * 4)) - 1):0{width}X}"


def _u32_to_float(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", int(value) & 0xFFFFFFFF))[0]


def _format_u32_list(values) -> str:
    return "[" + ",".join(_hex(value) for value in values) + "]"


def _format_float_list(values) -> str:
    return "[" + ",".join(f"{_u32_to_float(value):.3f}" for value in values) + "]"


def _format_byte_groups(values) -> str:
    raw = [int(value) & 0xFF for value in values]
    groups = []
    for i in range(0, len(raw), 4):
        chunk = raw[i:i + 4]
        value = 0
        for shift, byte in enumerate(chunk):
            value |= byte << (shift * 8)
        groups.append(value)
    return _format_u32_list(groups)


def _is_readable_process_address(address: int, size: int) -> bool:
    if address <= 0 or size <= 0:
        return False
    try:
        mbi = _MemoryBasicInformation()
        result = ctypes.windll.kernel32.VirtualQuery(
            ctypes.c_void_p(address),
            ctypes.byref(mbi),
            ctypes.sizeof(mbi),
        )
        if not result:
            return False
        protect = int(mbi.Protect)
        if int(mbi.State) != _MEM_COMMIT:
            return False
        if protect & (_PAGE_NOACCESS | _PAGE_GUARD):
            return False
        base = int(mbi.BaseAddress or 0)
        region_size = int(mbi.RegionSize)
        return base <= address and address + size <= base + region_size
    except Exception:
        return False


def _read_u32_words(address: int, count: int = 16) -> tuple[int, ...]:
    byte_count = count * 4
    if not _is_readable_process_address(int(address), byte_count):
        return tuple()
    try:
        return tuple(
            int(ctypes.c_uint32.from_address(int(address) + index * 4).value)
            for index in range(count)
        )
    except Exception:
        return tuple()


def _format_h00e4_target(living) -> str:
    address = int(living.h00E4[0])
    words = _read_u32_words(address, 16)
    if not words:
        return "h00E4_target_u32=[]"
    return f"h00E4_target_u32={_format_u32_list(words)}"


def _safe_name(agent_id: int) -> str:
    try:
        return Agent.GetNameByID(agent_id)
    except Exception:
        return ""


def _safe_enc_name(agent_id: int) -> str:
    try:
        return Agent.GetEncNameStrByID(agent_id, literal=True)
    except Exception:
        return ""


def _safe_int(value) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _vec2(value) -> str:
    try:
        return f"({float(value.x):.3f},{float(value.y):.3f})"
    except Exception:
        return "(?,?)"


def _vec3(value) -> str:
    try:
        return f"({float(value.x):.3f},{float(value.y):.3f},{float(value.z):.3f})"
    except Exception:
        return "(?,?,?)"


def _game_pos(value) -> str:
    try:
        return f"({float(value.x):.3f},{float(value.y):.3f},plane={int(value.zplane)})"
    except Exception:
        try:
            return f"({float(value.x):.3f},{float(value.y):.3f})"
        except Exception:
            return "(?,?)"


def _format_base_agent(agent_id: int) -> str:
    agent = Agent.GetAgentByID(agent_id)
    if agent is None:
        return "base_agent=False"

    return (
        f"base_agent=True "
        f"base_agent_id={_safe_int(agent.agent_id)} base_type={_hex(agent.type, 4)} "
        f"base_vtable={_hex(agent.vtable)} base_timer={_safe_int(agent.timer)} base_timer2={_safe_int(agent.timer2)} "
        f"base_z={float(agent.z):.3f} "
        f"base_width1={float(agent.width1):.3f} base_height1={float(agent.height1):.3f} "
        f"base_width2={float(agent.width2):.3f} base_height2={float(agent.height2):.3f} "
        f"base_width3={float(agent.width3):.3f} base_height3={float(agent.height3):.3f} "
        f"base_rotation_angle={float(agent.rotation_angle):.3f} "
        f"base_rotation_cos={float(agent.rotation_cos):.3f} base_rotation_sin={float(agent.rotation_sin):.3f} "
        f"base_rotation_cos2={float(agent.rotation_cos2):.3f} base_rotation_sin2={float(agent.rotation_sin2):.3f} "
        f"base_name_properties={_hex(agent.name_properties)} base_ground={_hex(agent.ground)} "
        f"base_h0004={_hex(agent.h0004)} base_h0008={_hex(agent.h0008)} base_h000C={list(agent.h000C)} "
        f"base_h0060={_hex(agent.h0060)} base_terrain_normal={_vec3(agent.terrain_normal)} "
        f"base_h0070={list(agent.h0070)} base_pos={_game_pos(agent.pos)} base_h0080={list(agent.h0080)} "
        f"base_name_tag=({float(agent.name_tag_x):.3f},{float(agent.name_tag_y):.3f},{float(agent.name_tag_z):.3f}) "
        f"base_visual_effects={_hex(agent.visual_effects, 4)} base_h0092={_hex(agent.h0092, 4)} "
        f"base_h0094={list(agent.h0094)} base_velocity={_vec2(agent.velocity)} base_h00A8={_hex(agent.h00A8)} "
        f"base_h00B4={list(agent.h00B4)} "
        f"base_is_item={bool(agent.is_item_type)} base_is_gadget={bool(agent.is_gadget_type)} "
        f"base_is_living={bool(agent.is_living_type)}"
    )


def _format_array_membership(agent_id: int) -> str:
    return (
        f"in_enemy_array={agent_id in _CURRENT_DUMP_ENEMY_IDS} "
        f"in_dead_enemy_array={agent_id in _CURRENT_DUMP_DEAD_ENEMY_IDS}"
    )


def _corpse_exploit_state(living) -> str:
    try:
        return str(living.corpse_exploit_state)
    except Exception:
        if bool(living.is_alive):
            return "alive"
        if bool(living.is_used_corpse):
            return "used_corpse"
        return "exploitable"


def _corpse_exploit_signature(living) -> tuple[int, ...]:
    try:
        return tuple(int(value) for value in living.corpse_exploit_signature)
    except Exception:
        return (
            int(living.effects),
            int(living.model_state),
            int(living.type_map),
            int(living.player_number),
            int(living.agent_model_type),
            int(living.animation_code),
            int(living.animation_id),
            int(living.h00D4[0]),
            int(living.h00D4[1]),
            int(living.h00D4[2]),
            int(living.h00E4[0]),
            int(living.h00E4[1]),
            int(living.h0140),
            int(living.h0160[0]),
            int(living.h0160[1]),
            int(living.h0160[2]),
            int(living.h0160[3]),
            int(living.h0180),
        )


def _format_corpse_evidence(living) -> str:
    effects = int(living.effects)
    type_map = int(living.type_map)
    gwca_dead = (effects & 0x0010) != 0
    gwca_used_corpse = (effects & 0x0004) != 0
    gwca_alive = not gwca_dead and float(living.hp) > 0.0
    gwca_exploitable = not gwca_alive and not gwca_used_corpse
    return (
        f"corpse_state={_corpse_exploit_state(living)} "
        f"corpse_sig={_corpse_exploit_signature(living)} "
        f"gwca_dead_effect={gwca_dead} "
        f"gwca_dead_type={(type_map & 0x000008) != 0} "
        f"gwca_used_corpse={gwca_used_corpse} "
        f"gwca_alive={gwca_alive} "
        f"gwca_exploitable={gwca_exploitable} "
        f"used_corpse_bit_set={(effects & 0x0004) != 0} "
        f"dead_effect_bit_set={(effects & 0x0010) != 0}"
    )


def _format_agent_corpse_helpers(agent_id: int, living) -> str:
    npc = Agent.GetNPCModelByID(int(living.player_number)) if bool(living.is_npc) else None
    npc_flags = Agent.GetNPCFlags(agent_id)
    return (
        f"agent_is_dead={bool(Agent.IsDead(agent_id))} "
        f"agent_is_alive={bool(Agent.IsAlive(agent_id))} "
        f"agent_is_used_corpse={bool(Agent.IsUsedCorpse(agent_id))} "
        f"agent_is_exploited_corpse={bool(Agent.IsExploitedCorpse(agent_id))} "
        f"agent_is_exploitable={bool(Agent.IsExploitable(agent_id))} "
        f"agent_is_fleshy={bool(Agent.IsFleshy(agent_id))} "
        f"agent_is_exploitable_corpse={bool(Agent.IsExploitableCorpse(agent_id))} "
        f"npc_lookup_found={npc is not None} "
        f"npc_model_file_id={int(npc.model_file_id) if npc else 0} "
        f"npc_flags={_hex(npc_flags)} npc_fleshy_bit={(int(npc_flags) & 0x8) != 0} "
        f"player_corpse={bool(living.is_player)} npc_corpse={bool(living.is_npc)}"
    )


def _format_direct_evidence(living) -> str:
    is_spirit_type = (int(living.type_map) & 0x00040000) != 0
    condition_bits = int(living.effects) & 0x0000007B
    has_condition_evidence = (
        bool(living.is_bleeding)
        or bool(living.is_conditioned)
        or bool(living.is_crippled)
        or bool(living.is_deep_wounded)
        or bool(living.is_poisoned)
    )
    has_corpse_evidence = bool(living.is_exploitable)
    evidence = []
    if bool(living.is_bleeding):
        evidence.append("bleeding")
    if bool(living.is_conditioned):
        evidence.append("conditioned")
    if bool(living.is_crippled):
        evidence.append("crippled")
    if bool(living.is_deep_wounded):
        evidence.append("deep_wound")
    if bool(living.is_poisoned):
        evidence.append("poisoned")
    if has_corpse_evidence:
        evidence.append("exploitable_corpse")
    if is_spirit_type:
        evidence.append("spirit_type")

    return (
        f"direct_flesh_evidence={has_condition_evidence or has_corpse_evidence} "
        f"direct_nonflesh_evidence={is_spirit_type} "
        f"direct_evidence_reasons={','.join(evidence) if evidence else 'none'} "
        f"condition_bits={_hex(condition_bits)}"
    )


def _known_flesh_label(model_id: int) -> str:
    if model_id in KNOWN_FLESH_LABELS:
        return KNOWN_FLESH_LABELS[model_id]
    if model_id in KNOWN_NONFLESH_LABELS:
        return KNOWN_NONFLESH_LABELS[model_id]
    return "unknown"


def _format_candidate_features(living, agent=None) -> str:
    model_id = int(living.player_number)
    base_name_properties = int(agent.name_properties) if agent is not None else 0
    base_visual_effects = int(agent.visual_effects) if agent is not None else 0
    base_h0092 = int(agent.h0092) if agent is not None else 0
    right_map = -1
    right_model = 0
    right_type = 0
    try:
        equipment = living.equipment
    except Exception:
        equipment = None
    if equipment is not None:
        right_map = int(equipment.right_hand_map)
        right = equipment.right_hand
        right_model = int(_safe_equipment_field(right, "model_file_id"))
        right_type = int(_safe_equipment_field(right, "type"))

    return (
        f"known_label={_known_flesh_label(model_id)} "
        f"candidate_effects={_hex(living.effects)} "
        f"candidate_type_map={_hex(living.type_map)} "
        f"candidate_weapon_type={int(living.weapon_type)} "
        f"candidate_weapon_attack_speed={float(living.weapon_attack_speed):.3f} "
        f"candidate_anim_code={int(living.animation_code)} "
        f"candidate_anim_id={int(living.animation_id)} "
        f"candidate_max_hp={int(living.max_hp)} "
        f"candidate_base_name_properties={_hex(base_name_properties)} "
        f"candidate_base_visual_effects={_hex(base_visual_effects, 4)} "
        f"candidate_base_h0092={_hex(base_h0092, 4)} "
        f"candidate_equip_right_map={right_map} "
        f"candidate_equip_right_model={right_model} "
        f"candidate_equip_right_type={right_type}"
    )


def _format_unknown_interpretations(living) -> str:
    return (
        f"h00D4_hex={_format_u32_list(living.h00D4)} h00D4_float={_format_float_list(living.h00D4)} "
        f"h00E4_hex={_format_u32_list(living.h00E4)} h00E4_float={_format_float_list(living.h00E4)} "
        f"{_format_h00e4_target(living)} "
        f"h0112_hex={_format_byte_groups(living.h0112)} "
        f"h0145_u32={_format_byte_groups(living.h0145)} "
        f"h0160_hex={_format_u32_list(living.h0160)} h0160_float={_format_float_list(living.h0160)} "
        f"h0194_u32={_format_byte_groups(living.h0194)} "
    )


def _safe_equipment_field(item, field_name: str, default=0):
    if item is None:
        return default
    try:
        return getattr(item, field_name)
    except Exception:
        return default


def _format_equipment(living) -> str:
    try:
        equipment = living.equipment
    except Exception:
        equipment = None
    try:
        tags = living.tags
    except Exception:
        tags = None

    if equipment is None:
        equipment_data = "equipment=False"
    else:
        left = equipment.left_hand
        right = equipment.right_hand
        shield = equipment.shield
        equipment_data = (
            "equipment=True "
            f"equip_left_map={int(equipment.left_hand_map)} equip_right_map={int(equipment.right_hand_map)} "
            f"equip_head_map={int(equipment.head_map)} equip_shield_map={int(equipment.shield_map)} "
            f"equip_left_model={int(_safe_equipment_field(left, 'model_file_id'))} "
            f"equip_left_type={int(_safe_equipment_field(left, 'type'))} "
            f"equip_left_interaction={_hex(_safe_equipment_field(left, 'interaction'))} "
            f"equip_right_model={int(_safe_equipment_field(right, 'model_file_id'))} "
            f"equip_right_type={int(_safe_equipment_field(right, 'type'))} "
            f"equip_right_interaction={_hex(_safe_equipment_field(right, 'interaction'))} "
            f"equip_shield_model={int(_safe_equipment_field(shield, 'model_file_id'))} "
            f"equip_shield_type={int(_safe_equipment_field(shield, 'type'))} "
            f"equip_shield_interaction={_hex(_safe_equipment_field(shield, 'interaction'))}"
        )

    if tags is None:
        tag_data = "tags=False"
    else:
        tag_data = (
            "tags=True "
            f"tag_guild={int(tags.guild_id)} tag_primary={int(tags.primary)} "
            f"tag_secondary={int(tags.secondary)} tag_level={int(tags.level)}"
        )

    return f"{equipment_data} {tag_data}"


def _format_agent(agent_id: int) -> str:
    living = Agent.GetLivingAgentByID(agent_id)
    x, y = Agent.GetXY(agent_id)
    _, allegiance = Agent.GetAllegiance(agent_id)
    base_agent_data = _format_base_agent(agent_id)

    if living is None:
        return (
            f"id={agent_id} name='{_safe_name(agent_id)}' enc='{_safe_enc_name(agent_id)}' "
            f"living=False xy=({x:.1f},{y:.1f}) zplane={Agent.GetZPlane(agent_id)} "
            f"allegiance={allegiance} model_id={Agent.GetModelID(agent_id)} "
            f"{base_agent_data}"
        )

    return (
        f"id={agent_id} name='{_safe_name(agent_id)}' enc='{_safe_enc_name(agent_id)}' "
        f"xy=({x:.1f},{y:.1f}) zplane={Agent.GetZPlane(agent_id)} "
        f"{_format_array_membership(agent_id)} "
        f"hp={float(living.hp):.3f} max_hp={int(living.max_hp)} "
        f"hp_pips={float(living.hp_pips):.3f} energy={float(living.energy):.3f} "
        f"max_energy={int(living.max_energy)} energy_regen={float(living.energy_regen):.3f} "
        f"type_map={_hex(living.type_map)} effects={_hex(living.effects)} hex={_hex(living.hex, 2)} "
        f"bleeding={bool(living.is_bleeding)} conditioned={bool(living.is_conditioned)} "
        f"crippled={bool(living.is_crippled)} dead={bool(living.is_dead)} "
        f"dead_type={bool(living.is_dead_by_type_map)} exploitable={bool(living.is_exploitable)} "
        f"deep_wounded={bool(living.is_deep_wounded)} poisoned={bool(living.is_poisoned)} "
        f"enchanted={bool(living.is_enchanted)} degen_hexed={bool(living.is_degen_hexed)} "
        f"hexed={bool(living.is_hexed)} weapon_spelled={bool(living.is_weapon_spelled)} "
        f"combat_stance={bool(living.is_in_combat_stance)} quest={bool(living.has_quest)} "
        f"female={bool(living.is_female)} hiding_cape={bool(living.is_hiding_cape)} "
        f"party_view={bool(living.can_be_viewed_in_party_window)} observed={bool(living.is_being_observed)} "
        f"spawned={bool(living.is_spawned)} boss={bool(living.has_boss_glow)} "
        f"knocked_down={bool(living.is_knocked_down)} moving={bool(living.is_moving)} "
        f"attacking={bool(living.is_attacking)} casting={bool(living.is_casting)} "
        f"idle={bool(living.is_idle)} alive={bool(living.is_alive)} "
        f"player={bool(living.is_player)} npc={bool(living.is_npc)} "
        f"{_format_agent_corpse_helpers(agent_id, living)} "
        f"model_state={int(living.model_state)} model_id={Agent.GetModelID(agent_id)} "
        f"player_number={int(living.player_number)} agent_model_type={_hex(living.agent_model_type, 4)} "
        f"transmog={int(living.transmog_npc_id)} primary={int(living.primary)} secondary={int(living.secondary)} "
        f"anim_code={int(living.animation_code)} anim_id={int(living.animation_id)} "
        f"anim_type={float(living.animation_type):.3f} anim_speed={float(living.animation_speed):.3f} "
        f"weapon_attack_speed={float(living.weapon_attack_speed):.3f} "
        f"attack_speed_modifier={float(living.attack_speed_modifier):.3f} "
        f"weapon_type={int(living.weapon_type)} weapon_item_type={int(living.weapon_item_type)} "
        f"offhand_item_type={int(living.offhand_item_type)} weapon_item_id={int(living.weapon_item_id)} "
        f"offhand_item_id={int(living.offhand_item_id)} skill={int(living.skill)} "
        f"allegiance={allegiance}:{int(living.allegiance)} owner={int(living.owner)} "
        f"login={int(living.login_number)} team={int(living.team_id)} level={int(living.level)} "
        f"h00C8={_hex(living.h00C8)} h00CC={_hex(living.h00CC)} h00D0={_hex(living.h00D0)} "
        f"h0100={_hex(living.h0100)} h0104={_hex(living.h0104)} h010C={_hex(living.h010C, 4)} "
        f"h0114={_hex(living.h0114)} h011C={_hex(living.h011C)} h0128={_hex(living.h0128)} "
        f"h0130={_hex(living.h0130)} h0140={_hex(living.h0140)} h0180={_hex(living.h0180)} "
        f"h00D4={list(living.h00D4)} h00E4={list(living.h00E4)} h0112={list(living.h0112)} "
        f"h0145={list(living.h0145)} h0160={list(living.h0160)} h0194={list(living.h0194)} "
        f"{_format_corpse_evidence(living)} "
        f"{_format_direct_evidence(living)} "
        f"{_format_candidate_features(living, Agent.GetAgentByID(agent_id))} "
        f"{_format_unknown_interpretations(living)} "
        f"{_format_equipment(living)} "
        f"{base_agent_data}"
    )


def _collect_model_summary(agent_ids: list[int]) -> dict[int, dict]:
    summary = {}
    for agent_id in agent_ids:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            continue

        model_id = int(living.player_number)
        agent = Agent.GetAgentByID(agent_id)
        model = summary.setdefault(
            model_id,
            {
                "count": 0,
                "known_label": set(),
                "names": set(),
                "enc": set(),
                "type_map": set(),
                "effects": set(),
                "corpse_state": set(),
                "corpse_signature": set(),
                "is_dead": set(),
                "is_dead_by_type_map": set(),
                "is_exploitable": set(),
                "max_hp": set(),
                "model_state": set(),
                "anim_code": set(),
                "anim_id": set(),
                "animation_type": set(),
                "animation_speed": set(),
                "weapon_attack_speed": set(),
                "attack_speed_modifier": set(),
                "weapon_type": set(),
                "weapon_item_type": set(),
                "offhand_item_type": set(),
                "primary": set(),
                "secondary": set(),
                "h00D4_2": set(),
                "h00D4": set(),
                "h00E4": set(),
                "h00E4_0": set(),
                "h00E4_target_0_15": set(),
                "h00E4_target_1": set(),
                "h00E4_target_5": set(),
                "h00E4_target_6": set(),
                "h00E4_target_8": set(),
                "h00E4_target_9": set(),
                "h00E4_target_10": set(),
                "h00E4_target_14": set(),
                "h0112": set(),
                "h0145": set(),
                "h0145_0_3": set(),
                "h0160": set(),
                "h0194": set(),
                "base_name_properties": set(),
                "base_visual_effects": set(),
                "base_h0092": set(),
                "base_h0094": set(),
                "base_size": set(),
                "spirit_type": set(),
                "condition_bits": set(),
                "equipment": set(),
                "equip_maps": set(),
                "tag_data": set(),
            },
        )
        model["count"] += 1
        model["known_label"].add(_known_flesh_label(model_id))
        model["names"].add(_safe_name(agent_id))
        model["enc"].add(_safe_enc_name(agent_id))
        model["type_map"].add(int(living.type_map))
        model["effects"].add(int(living.effects))
        model["corpse_state"].add(_corpse_exploit_state(living))
        model["corpse_signature"].add(_corpse_exploit_signature(living))
        model["is_dead"].add(bool(living.is_dead))
        model["is_dead_by_type_map"].add(bool(living.is_dead_by_type_map))
        model["is_exploitable"].add(bool(living.is_exploitable))
        model["max_hp"].add(int(living.max_hp))
        model["model_state"].add(int(living.model_state))
        model["anim_code"].add(int(living.animation_code))
        model["anim_id"].add(int(living.animation_id))
        model["animation_type"].add(round(float(living.animation_type), 3))
        model["animation_speed"].add(round(float(living.animation_speed), 3))
        model["weapon_attack_speed"].add(round(float(living.weapon_attack_speed), 3))
        model["attack_speed_modifier"].add(round(float(living.attack_speed_modifier), 3))
        model["weapon_type"].add(int(living.weapon_type))
        model["weapon_item_type"].add(int(living.weapon_item_type))
        model["offhand_item_type"].add(int(living.offhand_item_type))
        model["primary"].add(int(living.primary))
        model["secondary"].add(int(living.secondary))
        model["h00D4_2"].add(int(living.h00D4[2]))
        model["h00D4"].add(tuple(int(value) for value in living.h00D4))
        model["h00E4"].add(tuple(int(value) for value in living.h00E4))
        model["h00E4_0"].add(int(living.h00E4[0]))
        h00e4_target = _read_u32_words(int(living.h00E4[0]), 16)
        if h00e4_target:
            model["h00E4_target_0_15"].add(h00e4_target)
            for index in (1, 5, 6, 8, 9, 10, 14):
                model[f"h00E4_target_{index}"].add(int(h00e4_target[index]))
        model["h0112"].add(tuple(int(value) for value in living.h0112))
        model["h0145"].add(tuple(int(value) for value in living.h0145))
        model["h0145_0_3"].add(tuple(int(living.h0145[i]) for i in range(4)))
        model["h0160"].add(tuple(int(value) for value in living.h0160))
        model["h0194"].add(tuple(int(value) for value in living.h0194))
        model["spirit_type"].add((int(living.type_map) & 0x00040000) != 0)
        model["condition_bits"].add(int(living.effects) & 0x0000007B)
        try:
            equipment = living.equipment
        except Exception:
            equipment = None
        if equipment is None:
            model["equipment"].add(False)
            model["equip_maps"].add(None)
        else:
            model["equipment"].add(True)
            model["equip_maps"].add((
                int(equipment.left_hand_map),
                int(equipment.right_hand_map),
                int(equipment.head_map),
                int(equipment.shield_map),
            ))
        try:
            tags = living.tags
        except Exception:
            tags = None
        if tags is None:
            model["tag_data"].add(None)
        else:
            model["tag_data"].add((
                int(tags.guild_id),
                int(tags.primary),
                int(tags.secondary),
                int(tags.level),
            ))

        if agent is not None:
            model["base_name_properties"].add(int(agent.name_properties))
            model["base_visual_effects"].add(int(agent.visual_effects))
            model["base_h0092"].add(int(agent.h0092))
            model["base_h0094"].add(tuple(int(value) for value in agent.h0094))
            model["base_size"].add((
                round(float(agent.width1), 3),
                round(float(agent.height1), 3),
                round(float(agent.width2), 3),
                round(float(agent.height2), 3),
            ))

    return summary


def _format_summary_values(values, formatter=str) -> str:
    ordered = sorted(values, key=lambda value: str(value))
    if len(ordered) > 5:
        shown = ordered[:5]
        return "[" + ",".join(formatter(value) for value in shown) + f",...+{len(ordered) - 5}]"
    return "[" + ",".join(formatter(value) for value in ordered) + "]"


def _format_model_summary(model_id: int, data: dict) -> str:
    return (
        f"model_id={model_id} count={data['count']} "
        f"known_label={_format_summary_values(data['known_label'])} "
        f"names={_format_summary_values(data['names'])} "
        f"type_map={_format_summary_values(data['type_map'], _hex)} "
        f"effects={_format_summary_values(data['effects'], _hex)} "
        f"corpse_state={_format_summary_values(data['corpse_state'])} "
        f"corpse_signature={_format_summary_values(data['corpse_signature'])} "
        f"is_dead={_format_summary_values(data['is_dead'])} "
        f"is_dead_by_type_map={_format_summary_values(data['is_dead_by_type_map'])} "
        f"is_exploitable={_format_summary_values(data['is_exploitable'])} "
        f"max_hp={_format_summary_values(data['max_hp'])} "
        f"condition_bits={_format_summary_values(data['condition_bits'], _hex)} "
        f"spirit_type={_format_summary_values(data['spirit_type'])} "
        f"model_state={_format_summary_values(data['model_state'])} "
        f"anim_code={_format_summary_values(data['anim_code'])} "
        f"anim_id={_format_summary_values(data['anim_id'])} "
        f"animation_type={_format_summary_values(data['animation_type'])} "
        f"animation_speed={_format_summary_values(data['animation_speed'])} "
        f"weapon_attack_speed={_format_summary_values(data['weapon_attack_speed'])} "
        f"attack_speed_modifier={_format_summary_values(data['attack_speed_modifier'])} "
        f"weapon_type={_format_summary_values(data['weapon_type'])} "
        f"weapon_item_type={_format_summary_values(data['weapon_item_type'])} "
        f"offhand_item_type={_format_summary_values(data['offhand_item_type'])} "
        f"primary={_format_summary_values(data['primary'])} "
        f"secondary={_format_summary_values(data['secondary'])} "
        f"h00D4_2={_format_summary_values(data['h00D4_2'])} "
        f"h00D4={_format_summary_values(data['h00D4'])} "
        f"h00E4_0={_format_summary_values(data['h00E4_0'], _hex)} "
        f"h00E4={_format_summary_values(data['h00E4'])} "
        f"h00E4_target_0_15={_format_summary_values(data['h00E4_target_0_15'])} "
        f"h00E4_target_1={_format_summary_values(data['h00E4_target_1'])} "
        f"h00E4_target_5={_format_summary_values(data['h00E4_target_5'])} "
        f"h00E4_target_6={_format_summary_values(data['h00E4_target_6'])} "
        f"h00E4_target_8={_format_summary_values(data['h00E4_target_8'])} "
        f"h00E4_target_9={_format_summary_values(data['h00E4_target_9'])} "
        f"h00E4_target_10={_format_summary_values(data['h00E4_target_10'])} "
        f"h00E4_target_14={_format_summary_values(data['h00E4_target_14'])} "
        f"h0112={_format_summary_values(data['h0112'])} "
        f"h0145_0_3={_format_summary_values(data['h0145_0_3'])} "
        f"h0145={_format_summary_values(data['h0145'])} "
        f"h0160={_format_summary_values(data['h0160'])} "
        f"h0194={_format_summary_values(data['h0194'])} "
        f"base_name_properties={_format_summary_values(data['base_name_properties'], _hex)} "
        f"base_visual_effects={_format_summary_values(data['base_visual_effects'], lambda value: _hex(value, 4))} "
        f"base_h0092={_format_summary_values(data['base_h0092'], lambda value: _hex(value, 4))} "
        f"base_h0094={_format_summary_values(data['base_h0094'])} "
        f"base_size={_format_summary_values(data['base_size'])} "
        f"equipment={_format_summary_values(data['equipment'])} "
        f"equip_maps={_format_summary_values(data['equip_maps'])} "
        f"tag_data={_format_summary_values(data['tag_data'])}"
    )


def _clone_model_summary(data: dict) -> dict:
    cloned = {}
    for key, value in data.items():
        if isinstance(value, set):
            cloned[key] = set(value)
        else:
            cloned[key] = value
    return cloned


def _merge_observed_model_summary(summary: dict[int, dict]) -> None:
    for model_id, data in summary.items():
        existing = OBSERVED_MODEL_SUMMARY.get(model_id)
        if existing is None:
            OBSERVED_MODEL_SUMMARY[model_id] = _clone_model_summary(data)
            continue

        existing["count"] += data["count"]
        for key, value in data.items():
            if key == "count":
                continue
            if isinstance(value, set):
                existing.setdefault(key, set()).update(value)


def _model_name(data: dict) -> str:
    names = [name for name in sorted(data.get("names", set())) if name]
    return names[0] if names else "?"


def _format_compare_value(field: str, value) -> str:
    if value is None:
        return "None"
    if field in {"type_map", "effects", "condition_bits", "h00E4_0", "base_name_properties"}:
        return _hex(value)
    if field in {"base_visual_effects", "base_h0092"}:
        return _hex(value, 4)
    return str(value)


def _field_values_for_label(field: str, label: str) -> dict:
    values = {}
    for model_id, data in OBSERVED_MODEL_SUMMARY.items():
        if _known_flesh_label(model_id) != label:
            continue
        for value in data.get(field, set()):
            values.setdefault(value, set()).add(model_id)
    return values


def _format_value_models(field: str, value_to_models: dict) -> str:
    parts = []
    for value in sorted(value_to_models, key=lambda item: str(item)):
        models = sorted(value_to_models[value])
        model_names = ",".join(f"{model_id}:{_model_name(OBSERVED_MODEL_SUMMARY[model_id])}" for model_id in models)
        parts.append(f"{_format_compare_value(field, value)}=>{{{model_names}}}")
    if len(parts) > 8:
        return "[" + "; ".join(parts[:8]) + f"; ...+{len(parts) - 8}]"
    return "[" + "; ".join(parts) + "]"


def _format_known_field_comparisons() -> list[str]:
    known_model_count = sum(
        1
        for model_id in OBSERVED_MODEL_SUMMARY
        if _known_flesh_label(model_id) in {"fleshy", "non_fleshy"}
    )
    if known_model_count < 2:
        return []

    lines = [
        f"KNOWN_FIELD_COMPARE_BEGIN observed_known_models={known_model_count} "
        "note=disjoint means no observed overlap yet; it is not proof until more labels are added"
    ]
    for field in COMPARE_FIELDS:
        fleshy = _field_values_for_label(field, "fleshy")
        non_fleshy = _field_values_for_label(field, "non_fleshy")
        if not fleshy or not non_fleshy:
            continue

        overlap = set(fleshy).intersection(non_fleshy)
        lines.append(
            f"KNOWN_FIELD_COMPARE field={field} "
            f"disjoint={not overlap} overlap={_format_summary_values(overlap, lambda value: _format_compare_value(field, value))} "
            f"fleshy={_format_value_models(field, fleshy)} "
            f"non_fleshy={_format_value_models(field, non_fleshy)}"
        )
    lines.append("KNOWN_FIELD_COMPARE_END")
    return lines


def _load_sample_db() -> dict:
    if not os.path.exists(SAMPLE_DB_PATH):
        return {"models": {}}
    try:
        with open(SAMPLE_DB_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict) or not isinstance(data.get("models"), dict):
            return {"models": {}}
        return data
    except Exception as exc:
        ConsoleLog(
            MODULE_NAME,
            f"Failed to load sample DB '{SAMPLE_DB_PATH}': {exc}",
            Console.MessageType.Warning,
        )
        return {"models": {}}


def _save_sample_db(db: dict) -> None:
    try:
        with open(SAMPLE_DB_PATH, "w", encoding="utf-8") as handle:
            json.dump(db, handle, indent=2, sort_keys=True)
    except Exception as exc:
        ConsoleLog(
            MODULE_NAME,
            f"Failed to save sample DB '{SAMPLE_DB_PATH}': {exc}",
            Console.MessageType.Warning,
        )


def _update_sample_db(summary: dict[int, dict]) -> dict:
    db = _load_sample_db()
    models = db.setdefault("models", {})
    changed = False

    for model_id, data in summary.items():
        label = _known_flesh_label(model_id)
        if label not in {"fleshy", "non_fleshy"}:
            continue

        key = str(model_id)
        record = models.setdefault(
            key,
            {
                "model_id": model_id,
                "label": label,
                "name": _model_name(data),
                "count": 0,
                "fields": {},
            },
        )
        record["label"] = label
        record["name"] = _model_name(data)
        record["count"] = int(record.get("count", 0)) + int(data.get("count", 0))
        fields = record.setdefault("fields", {})

        for field in COMPARE_FIELDS:
            values = fields.setdefault(field, [])
            existing = set(values)
            for value in data.get(field, set()):
                formatted = _format_compare_value(field, value)
                if formatted not in existing:
                    values.append(formatted)
                    existing.add(formatted)
                    changed = True
            values.sort()
        changed = True

    if changed:
        _save_sample_db(db)
    return db


def _format_db_value_models(value_to_models: dict) -> str:
    parts = []
    for value in sorted(value_to_models):
        parts.append(f"{value}=>{{{','.join(sorted(value_to_models[value]))}}}")
    if len(parts) > 8:
        return "[" + "; ".join(parts[:8]) + f"; ...+{len(parts) - 8}]"
    return "[" + "; ".join(parts) + "]"


def _format_persistent_known_field_comparisons(db: dict) -> list[str]:
    models = db.get("models", {})
    known_records = [
        record
        for record in models.values()
        if record.get("label") in {"fleshy", "non_fleshy"}
    ]
    if len(known_records) < 2:
        return [
            f"KNOWN_FIELD_DB_COMPARE_SKIPPED persisted_known_models={len(known_records)} "
            f"path='{SAMPLE_DB_PATH}' reason=need both fleshy and non_fleshy observed samples"
        ]

    lines = [
        f"KNOWN_FIELD_DB_COMPARE_BEGIN persisted_known_models={len(known_records)} "
        f"path='{SAMPLE_DB_PATH}'"
    ]
    for field in COMPARE_FIELDS:
        fleshy = {}
        non_fleshy = {}
        for model_id, record in models.items():
            label = record.get("label")
            if label not in {"fleshy", "non_fleshy"}:
                continue
            model_name = f"{model_id}:{record.get('name', '?')}"
            values = record.get("fields", {}).get(field, [])
            target = fleshy if label == "fleshy" else non_fleshy
            for value in values:
                target.setdefault(value, set()).add(model_name)

        if not fleshy or not non_fleshy:
            continue
        overlap = sorted(set(fleshy).intersection(non_fleshy))
        lines.append(
            f"KNOWN_FIELD_DB_COMPARE field={field} "
            f"disjoint={not overlap} overlap=[{','.join(overlap)}] "
            f"fleshy={_format_db_value_models(fleshy)} "
            f"non_fleshy={_format_db_value_models(non_fleshy)}"
        )
    lines.append("KNOWN_FIELD_DB_COMPARE_END")
    return lines


def _format_compact_agent(agent_id: int) -> str:
    living = Agent.GetLivingAgentByID(agent_id)
    agent = Agent.GetAgentByID(agent_id)
    if living is None:
        return (
            f"COMPACT id={agent_id} name='{_safe_name(agent_id)}' living=False "
            f"model_id={Agent.GetModelID(agent_id)}"
        )

    is_spirit_type = (int(living.type_map) & 0x00040000) != 0
    condition_bits = int(living.effects) & 0x0000007B
    base_visual_effects = int(agent.visual_effects) if agent is not None else 0
    base_name_properties = int(agent.name_properties) if agent is not None else 0
    base_h0092 = int(agent.h0092) if agent is not None else 0
    base_h0094 = tuple(int(value) for value in agent.h0094) if agent is not None else ()
    base_size = (
        round(float(agent.width1), 3),
        round(float(agent.height1), 3),
        round(float(agent.width2), 3),
        round(float(agent.height2), 3),
    ) if agent is not None else ()
    h00e4_target = _read_u32_words(int(living.h00E4[0]), 16)

    return (
        f"COMPACT id={agent_id} name='{_safe_name(agent_id)}' "
        f"{_format_array_membership(agent_id)} "
        f"model_id={int(living.player_number)} known_label={_known_flesh_label(int(living.player_number))} "
        f"level={int(living.level)} "
        f"type_map={_hex(living.type_map)} effects={_hex(living.effects)} "
        f"dead={bool(living.is_dead)} dead_type={bool(living.is_dead_by_type_map)} "
        f"alive={bool(living.is_alive)} used_corpse={bool(living.is_used_corpse)} "
        f"fleshy={bool(Agent.IsFleshy(agent_id))} exploitable_corpse={bool(Agent.IsExploitableCorpse(agent_id))} "
        f"npc_flags={_hex(Agent.GetNPCFlags(agent_id))} "
        f"corpse_state={_corpse_exploit_state(living)} "
        f"corpse_sig={_corpse_exploit_signature(living)} "
        f"condition_bits={_hex(condition_bits)} spirit_type={is_spirit_type} "
        f"conditioned={bool(living.is_conditioned)} bleeding={bool(living.is_bleeding)} "
        f"poisoned={bool(living.is_poisoned)} exploitable={bool(living.is_exploitable)} "
        f"spawned={bool(living.is_spawned)} enchanted={bool(living.is_enchanted)} "
        f"model_state={int(living.model_state)} anim_code={int(living.animation_code)} "
        f"anim_id={int(living.animation_id)} anim_speed={float(living.animation_speed):.3f} "
        f"weapon_type={int(living.weapon_type)} weapon_item_type={int(living.weapon_item_type)} "
        f"offhand_item_type={int(living.offhand_item_type)} "
        f"h00D4={tuple(int(value) for value in living.h00D4)} "
        f"h00E4={tuple(int(value) for value in living.h00E4)} "
        f"h00E4_target_0_15={h00e4_target} "
        f"h0145_0_7={tuple(int(living.h0145[i]) for i in range(8))} "
        f"h0160={tuple(int(value) for value in living.h0160)} "
        f"h0194_0_15={tuple(int(living.h0194[i]) for i in range(16))} "
        f"base_name_properties={_hex(base_name_properties)} "
        f"base_visual_effects={_hex(base_visual_effects, 4)} "
        f"base_h0092={_hex(base_h0092, 4)} base_h0094={base_h0094} "
        f"base_size={base_size}"
    )


def dump_enemy_array() -> None:
    global _CURRENT_DUMP_ENEMY_IDS, _CURRENT_DUMP_DEAD_ENEMY_IDS
    enemy_array = AgentArray.GetEnemyArray()
    dead_enemy_array = AgentArray.GetDeadEnemyArray()
    exploitable_array = Routines.Agents.GetExploitableCorpses()
    _CURRENT_DUMP_ENEMY_IDS = set(enemy_array)
    _CURRENT_DUMP_DEAD_ENEMY_IDS = set(dead_enemy_array)
    dump_array = sorted(
        _CURRENT_DUMP_ENEMY_IDS
        .union(_CURRENT_DUMP_DEAD_ENEMY_IDS)
        .union(int(agent_id) for agent_id in exploitable_array)
    )
    ConsoleLog(
        MODULE_NAME,
        f"Enemy array count={len(enemy_array)} dead_enemy_array count={len(dead_enemy_array)} "
        f"exploitable_corpse_count={len(exploitable_array)} exploitable_ids={list(exploitable_array)} "
        f"dump_count={len(dump_array)}",
        Console.MessageType.Info,
    )
    summary = _collect_model_summary(dump_array)
    _merge_observed_model_summary(summary)
    sample_db = _update_sample_db(summary)
    for model_id in sorted(summary):
        ConsoleLog(
            MODULE_NAME,
            "MODEL_SUMMARY " + _format_model_summary(model_id, summary[model_id]),
            Console.MessageType.Info,
        )
    for line in _format_known_field_comparisons():
        ConsoleLog(MODULE_NAME, line, Console.MessageType.Info)
    for line in _format_persistent_known_field_comparisons(sample_db):
        ConsoleLog(MODULE_NAME, line, Console.MessageType.Info)
    for agent_id in dump_array:
        ConsoleLog(MODULE_NAME, _format_compact_agent(agent_id), Console.MessageType.Info)
    for agent_id in dump_array:
        ConsoleLog(MODULE_NAME, _format_agent(agent_id), Console.MessageType.Debug)


def main():
    if PyImGui.begin("Agent Enemy Debug Dump", PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text("Dumps enemy and dead-enemy agents to the console.")
        PyImGui.text("Names are identifiers only. No filtering by name or model is done.")
        if PyImGui.button("Dump Enemy Array"):
            dump_enemy_array()
    PyImGui.end()


if __name__ == "__main__":
    main()

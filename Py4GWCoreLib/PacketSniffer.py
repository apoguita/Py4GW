from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Literal

import PyPacketSniffer

from .enums_src.Packet_enums import CTO_OPCODES

PacketDirection = Literal['CToS', 'StoC']

STOC_HEADER_NAMES: dict[int, str] = {
    0x0000: 'TRADE_REQUEST',
    0x0001: 'TRADE_TERMINATE',
    0x0002: 'TRADE_CHANGE_OFFER',
    0x0003: 'TRADE_RECEIVE_OFFER',
    0x0004: 'TRADE_ADD_ITEM',
    0x0005: 'TRADE_ACKNOWLEDGE',
    0x0006: 'TRADE_ACCEPT',
    0x0008: 'TRADE_OFFERED_COUNT',
    0x000C: 'PING_REQUEST',
    0x000D: 'PING_REPLY',
    0x000E: 'FRIENDLIST_MESSAGE',
    0x000F: 'ACCOUNT_FEATURE',
    0x0018: 'PVP_UPDATE_UNLOCKED_HEROES',
    0x001A: 'PVP_ITEM_STREAM_ADD',
    0x001B: 'PVP_ITEM_STREAM_END',
    0x001D: 'PVP_UPDATE_UNLOCKED_SKILLS',
    0x001E: 'WORLD_SIMULATION_TICK',
    0x001F: 'WORLD_UPDATE_LOAD_TIME',
    0x0020: 'WORLD_CREATE_AGENT',
    0x0021: 'WORLD_REMOVE_AGENT',
    0x0022: 'WORLD_UPDATE_CONTROLLED_AGENT',
    0x0025: 'AGENT_UPDATE_DIRECTION',
    0x0027: 'AGENT_UPDATE_SPEED_BASE',
    0x0028: 'AGENT_STOP_MOVING',
    0x0029: 'AGENT_MOVE_TO_POINT',
    0x002A: 'AGENT_UPDATE_DESTINATION',
    0x002B: 'AGENT_UPDATE_SPEED',
    0x002C: 'AGENT_UPDATE_POSITION',
    0x002D: 'AGENT_PLAYER_DIE',
    0x002E: 'AGENT_UPDATE_ROTATION',
    0x002F: 'AGENT_UPDATE_ALLEGIANCE',
    0x0030: 'CHARACTER_UPDATE_INFO',
    0x0031: 'CHARACTER_UPDATE_NAME',
    0x0033: 'MESSAGE_OF_THE_DAY',
    0x0034: 'AGENT_PINGED',
    0x0037: 'AGENT_UPDATE_ATTRIBUTE_POINTS',
    0x003A: 'AGENT_UPDATE_ATTRIBUTES',
    0x003B: 'AGENT_UPDATE_ATTRIBUTE',
    0x003E: 'AGENT_ALLY_DESTROY',
    0x003F: 'EFFECT_UPKEEP_ADDED',
    0x0040: 'EFFECT_UPKEEP_REMOVED',
    0x0041: 'EFFECT_UPKEEP_APPLIED',
    0x0042: 'EFFECT_APPLIED',
    0x0043: 'EFFECT_RENEWED',
    0x0044: 'EFFECT_REMOVED',
    0x0046: 'SCREEN_SHAKE',
    0x0048: 'AGENT_DISPLAY_CAPE',
    0x0049: 'QUEST_ADD',
    0x004C: 'QUEST_DESCRIPTION',
    0x0050: 'QUEST_GENERAL_INFO',
    0x0051: 'QUEST_UPDATE_MARKER',
    0x0052: 'QUEST_REMOVE',
    0x0053: 'QUEST_ADD_MARKER',
    0x0054: 'QUEST_UPDATE_NAME',
    0x0056: 'NPC_UPDATE_PROPERTIES',
    0x0057: 'NPC_UPDATE_MODEL',
    0x0059: 'PLAYER_UPDATE_AGENT_INFO',
    0x005A: 'AGENT_DESTROY_PLAYER',
    0x005D: 'CHAT_MESSAGE_CORE',
    0x005E: 'CHAT_MESSAGE_SERVER',
    0x005F: 'CHAT_MESSAGE_NPC',
    0x0060: 'CHAT_MESSAGE_GLOBAL',
    0x0061: 'CHAT_MESSAGE_LOCAL',
    0x0062: 'HERO_BEHAVIOR',
    0x0064: 'HERO_SKILL_STATUS',
    0x0065: 'HERO_SKILL_STATUS_BITMAP',
    0x006B: 'POST_PROCESS',
    0x006C: 'DUNGEON_REWARD',
    0x006D: 'NPC_UPDATE_WEAPONS',
    0x006E: 'UPDATE_AGENT_VISUAL_EQUIPMENT',
    0x0070: 'HARD_MODE_UNLOCKED',
    0x0074: 'MERCENARY_INFO',
    0x007E: 'DIALOG_BUTTON',
    0x0080: 'DIALOG_BODY',
    0x0081: 'DIALOG_SENDER',
    0x0083: 'WINDOW_OPEN',
    0x0084: 'WINDOW_ADD_ITEMS',
    0x0085: 'WINDOW_ITEMS_END',
    0x0086: 'WINDOW_ITEM_STREAM_END',
    0x008A: 'CARTOGRAPHY_DATA',
    0x0091: 'COMPASS_DRAWING',
    0x0094: 'MAP_UPDATE_UNLOCKED_LIST',
    0x0099: 'MAP_UPDATE_CURRENT',
    0x009A: 'AGENT_UPDATE_SCALE',
    0x009B: 'AGENT_UPDATE_NPC_NAME',
    0x009E: 'AGENT_DISPLAY_DIALOG',
    0x009F: 'AGENT_PROPERTY_UPDATE_INT',
    0x00A0: 'AGENT_PROPERTY_UPDATE_INT_TARGET',
    0x00A1: 'AGENT_PROPERTY_PLAY_EFFECT',
    0x00A2: 'AGENT_PROPERTY_UPDATE_FLOAT',
    0x00A3: 'AGENT_PROPERTY_UPDATE_FLOAT_TARGET',
    0x00A4: 'AGENT_PROJECTILE_LAUNCHED',
    0x00A5: 'AGENT_UPDATE_SPEECH_BUBBLE',
    0x00A6: 'AGENT_UPDATE_PROFESSION',
    0x00AA: 'AGENT_CREATE_NPC',
    0x00AC: 'AGENT_UPDATE_OBSERVED_TARGET',
    0x00AE: 'AGENT_UPDATE_MODEL',
    0x00B0: 'PLAYER_UPDATE_PARTY_SIZE',
    0x00B1: 'PLAYER_UPDATE_PARTY',
    0x00B6: 'PLAYER_UPDATE_UNLOCKED_PROFESSIONS',
    0x00B7: 'PLAYER_UPDATE_PROFESSION',
    0x00B9: 'MISSION_INFOBOX_ADD',
    0x00BA: 'MISSION_STREAM_START',
    0x00BB: 'MISSION_OBJECTIVE_ADD',
    0x00BC: 'MISSION_OBJECTIVE_COMPLETE',
    0x00BD: 'MISSION_OBJECTIVE_UPDATE_STRING',
    0x00C3: 'MERCHANT_WINDOW_OPEN',
    0x00C4: 'MERCHANT_WINDOW_UPDATE_OWNER',
    0x00C6: 'TRADER_TRANSACTION_REJECT',
    0x00CC: 'TRADER_TRANSACTION_DONE',
    0x00CD: 'TRADER_WINDOW_OPEN',
    0x00D9: 'SKILLBAR_UPDATE_SKILL',
    0x00DA: 'SKILLBAR_UPDATE',
    0x00DB: 'UPDATE_UNLOCKED_SKILLS',
    0x00DC: 'SKILL_WINDOW_COUNT',
    0x00DD: 'SKILL_WINDOW_COUNT_2',
    0x00E0: 'SKILL_WINDOW_DATA',
    0x00E1: 'SKILL_WINDOW_END',
    0x00E2: 'SKILL_INTERRUPTED',
    0x00E3: 'SKILL_ACTIVATED',
    0x00E4: 'SKILL_ACTIVATE',
    0x00E5: 'SKILL_RECHARGE',
    0x00E6: 'SKILL_RECHARGED',
    0x00E9: 'CHARACTER_UPDATE_FACTIONS',
    0x00EA: 'CHARACTER_FACTION_MAX_KURZICK',
    0x00EB: 'CHARACTER_FACTION_MAX_LUXON',
    0x00EC: 'CHARACTER_FACTION_MAX_BALTHAZAR',
    0x00ED: 'CHARACTER_FACTION_MAX_IMPERIAL',
    0x00EE: 'CHARACTER_FACTION_UPDATE',
    0x00F0: 'AGENT_INITIAL_EFFECTS',
    0x00F1: 'AGENT_UPDATE_EFFECTS',
    0x00F2: 'INSTANCE_LOADED',
    0x00F3: 'TITLE_RANK_DATA',
    0x00F4: 'TITLE_RANK_DISPLAY',
    0x00F5: 'TITLE_UPDATE',
    0x00F6: 'TITLE_TRACK_INFO',
    0x00F7: 'ITEM_PRICE_QUOTE',
    0x00F9: 'ITEM_PRICES',
    0x00FA: 'VANQUISH_PROGRESS',
    0x00FB: 'VANQUISH_COMPLETE',
    0x00FE: 'CINEMATIC_SKIP_EVERYONE',
    0x00FF: 'CINEMATIC_SKIP_COUNT',
    0x0100: 'CINEMATIC_START',
    0x0102: 'CINEMATIC_TEXT',
    0x0103: 'CINEMATIC_DATA_END',
    0x0104: 'CINEMATIC_DATA',
    0x0105: 'CINEMATIC_END',
    0x010A: 'SIGNPOST_BUTTON',
    0x010B: 'SIGNPOST_BODY',
    0x010C: 'SIGNPOST_SENDER',
    0x010E: 'MANIPULATE_MAP_OBJECT',
    0x0111: 'MANIPULATE_MAP_OBJECT2',
    0x0118: 'GUILD_PLAYER_ROLE',
    0x011A: 'TOWN_ALLIANCE_OBJECT',
    0x011C: 'GUILD_CONTROL_011C',
    0x0120: 'GUILD_ALLIANCE_INFO',
    0x0121: 'GUILD_GENERAL_INFO',
    0x0122: 'GUILD_CHANGE_FACTION',
    0x0123: 'GUILD_INVITE_RECEIVED',
    0x0127: 'GUILD_PLAYER_INFO',
    0x0128: 'GUILD_PLAYER_REMOVE',
    0x012A: 'GUILD_PLAYER_CHANGE_COMPLETE',
    0x012B: 'GUILD_CHANGE_PLAYER_CONTEXT',
    0x012C: 'GUILD_CHANGE_PLAYER_STATUS',
    0x012D: 'GUILD_CHANGE_PLAYER_TYPE',
    0x012E: 'GUILD_CONTROL_012E',
    0x0135: 'ITEM_UPDATE_OWNER',
    0x0139: 'ITEM_UPDATE_QUANTITY',
    0x013A: 'ITEM_UPDATE_CUSTOMIZED_NAME',
    0x013E: 'ITEM_MOVED_TO_LOCATION',
    0x013F: 'INVENTORY_CREATE_BAG',
    0x0140: 'UPDATE_GOLD_CHARACTER',
    0x0141: 'UPDATE_GOLD_STORAGE',
    0x0144: 'ITEM_STREAM_CREATE',
    0x0145: 'ITEM_STREAM_DESTROY',
    0x0147: 'ITEM_WEAPON_SET',
    0x0148: 'ITEM_SET_ACTIVE_WEAPON_SET',
    0x014B: 'ITEM_CHANGE_LOCATION',
    0x014D: 'ITEM_REMOVE',
    0x014F: 'GOLD_CHARACTER_REMOVE',
    0x0150: 'GOLD_STORAGE_REMOVE',
    0x0154: 'TOME_SHOW_SKILLS',
    0x015A: 'ITEM_SET_PROFESSION',
    0x015F: 'CREATE_UNNAMED_ITEM',
    0x0161: 'CREATE_NAMED_ITEM',
    0x0162: 'ITEM_REUSE_ID',
    0x0163: 'ITEM_SALVAGE_SESSION_START',
    0x0164: 'ITEM_SALVAGE_SESSION_CANCEL',
    0x0165: 'ITEM_SALVAGE_SESSION_DONE',
    0x0166: 'ITEM_SALVAGE_SESSION_SUCCESS',
    0x0167: 'ITEM_SALVAGE_SESSION_ITEM_KEPT',
    0x016E: 'ACCOUNT_UNLOCK_STREAM_FINALIZE',
    0x016F: 'ACCOUNT_UNLOCK_HERO_BEGIN',
    0x0170: 'ACCOUNT_UNLOCK_HERO_END',
    0x0171: 'ACCOUNT_UNLOCKED_HERO',
    0x017B: 'INSTANCE_SHOW_WIN',
    0x017C: 'INSTANCE_LOAD_HEAD',
    0x017D: 'INSTANCE_LOAD_PLAYER_NAME',
    0x017E: 'INSTANCE_COUNTDOWN_STOP',
    0x0180: 'INSTANCE_COUNTDOWN',
    0x0186: 'INSTANCE_PLAYER_DATA_START',
    0x0188: 'CHAR_CREATION_SUCCESS',
    0x0189: 'CHAR_CREATION_START',
    0x018A: 'INSTANCE_PLAYER_DATA_DONE',
    0x018B: 'CHAR_CREATION_ERROR',
    0x018E: 'INSTANCE_LOAD_FINISH',
    0x0190: 'JUMBO_MESSAGE',
    0x0191: 'INSTANCE_REDIRECT',
    0x0195: 'INSTANCE_LOAD_SPAWN_POINT',
    0x0196: 'INSTANCE_MANIFEST_DATA',
    0x0197: 'INSTANCE_MANIFEST_DONE',
    0x0198: 'INSTANCE_MANIFEST_PHASE',
    0x0199: 'INSTANCE_LOAD_INFO',
    0x01A0: 'CREATE_MISSION_PROGRESS',
    0x01A2: 'UPDATE_MISSION_PROGRESS',
    0x01A5: 'TRANSFER_GAME_SERVER_INFO',
    0x01AB: 'READY_FOR_MAP_SPAWN',
    0x01AF: 'DOA_COMPLETE_ZONE',
    0x01B2: 'CHARACTER_UPDATE_PARTY',
    0x01BB: 'INSTANCE_TRAVEL_TIMER',
    0x01BC: 'INSTANCE_TRAVEL_FAILURE',
    0x01BE: 'PARTY_SET_DIFFICULTY',
    0x01BF: 'PARTY_HENCHMAN_ADD',
    0x01C0: 'PARTY_HENCHMAN_REMOVE',
    0x01C2: 'PARTY_HERO_ADD',
    0x01C3: 'PARTY_HERO_REMOVE',
    0x01C4: 'PARTY_INVITE_ADD',
    0x01C5: 'PARTY_JOIN_REQUEST',
    0x01C6: 'PARTY_INVITE_CANCEL',
    0x01C7: 'PARTY_REQUEST_CANCEL',
    0x01C8: 'PARTY_REQUEST_RESPONSE',
    0x01C9: 'PARTY_INVITE_RESPONSE',
    0x01CA: 'PARTY_YOU_ARE_LEADER',
    0x01CB: 'PARTY_PLAYER_ADD',
    0x01D0: 'PARTY_PLAYER_REMOVE',
    0x01D1: 'PARTY_PLAYER_READY',
    0x01D2: 'PARTY_CREATE',
    0x01D3: 'PARTY_MEMBER_STREAM_END',
    0x01D8: 'PARTY_DEFEATED',
    0x01D9: 'PARTY_LOCK',
    0x01DB: 'PARTY_SEARCH_REQUEST_JOIN',
    0x01DC: 'PARTY_SEARCH_REQUEST_DONE',
    0x01DD: 'PARTY_SEARCH_ADVERTISEMENT',
    0x01DE: 'PARTY_SEARCH_SEEK',
    0x01DF: 'PARTY_SEARCH_REMOVE',
    0x01E0: 'PARTY_SEARCH_SIZE',
    0x01E1: 'PARTY_SEARCH_TYPE',
}

GENERIC_VALUE_IDS: dict[int, str] = {
    1: 'melee_attack_finished',
    3: 'attack_stopped',
    8: 'disabled',
    10: 'skill_damage',
    32: 'max_hp_reached',
    35: 'interrupted',
    46: 'attack_skill_finished',
    48: 'instant_skill_activated',
    49: 'attack_skill_stopped',
    50: 'attack_skill_activated',
    58: 'skill_finished',
    59: 'skill_stopped',
    60: 'skill_activated',
}

KNOWN_CTOS_LENGTHS: dict[int, int] = {
    0x26: 12,
    0x28: 4,
    0x2C: 12,
    0x30: 8,
    0x39: 12,
    0x3D: 28,
    0x3E: 16,
    0x40: 12,
    0x45: 264,
    0x46: 20,
    0x4F: 8,
    0x51: 8,
}

NAME_RE_STOC_HEADERS: set[int] = {
    0x000E,
    0x0031,
    0x0034,
    0x0118,
    0x011C,
    0x0120,
    0x0121,
    0x0127,
    0x0128,
    0x012A,
    0x012B,
    0x012C,
    0x012D,
    0x012E,
    0x017D,
}


@dataclass(frozen=True, slots=True)
class PacketLogEntry:
    direction: PacketDirection
    tick: int
    header: int
    size: int
    data: bytes


class PacketSniffer:
    _instance: 'PacketSniffer | None' = None
    _VALID_DIRECTIONS = frozenset({'CToS', 'StoC', 'both'})

    def __init__(self) -> None:
        self._sniffer = PyPacketSniffer.PacketSniffer.instance()

    @classmethod
    def instance(cls) -> 'PacketSniffer':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self, direction: PacketDirection | Literal['both'] = 'both') -> bool:
        normalized = self._normalize_direction(direction)
        if normalized == 'both':
            return bool(self._sniffer.initialize())
        if normalized == 'StoC':
            return bool(self._sniffer.initialize_stoc())
        return bool(self._sniffer.initialize_ctos())

    def terminate(self, direction: PacketDirection | Literal['both'] = 'both') -> None:
        normalized = self._normalize_direction(direction)
        if normalized == 'both':
            self._sniffer.terminate()
        elif normalized == 'StoC':
            self._sniffer.terminate_stoc()
        else:
            self._sniffer.terminate_ctos()

    def get_logs(self, direction: PacketDirection | Literal['both'] = 'both') -> list[PacketLogEntry]:
        normalized = self._normalize_direction(direction)
        if normalized == 'both':
            native_logs = self._sniffer.get_logs()
        elif normalized == 'StoC':
            native_logs = self._sniffer.get_stoc_logs()
        else:
            native_logs = self._sniffer.get_ctos_logs()
        return [self._convert_entry(entry) for entry in native_logs]

    def clear_logs(self, direction: PacketDirection | Literal['both'] = 'both') -> None:
        normalized = self._normalize_direction(direction)
        if normalized == 'both':
            self._sniffer.clear_logs()
        elif normalized == 'StoC':
            self._sniffer.clear_stoc_logs()
        else:
            self._sniffer.clear_ctos_logs()

    def get_packet_name(self, direction: PacketDirection, header: int) -> str:
        if direction == 'StoC':
            return STOC_HEADER_NAMES.get(header, f'0x{header:04X}')
        return CTO_OPCODES.get(header, f'0x{header:04X}')

    def decode_packet(self, direction: PacketDirection, header: int, size: int, raw: bytes) -> str:
        if direction == 'StoC':
            return self._decode_stoc_packet(header, size, raw)
        return self._decode_ctos_packet(header, size, raw)

    @classmethod
    def _normalize_direction(cls, direction: PacketDirection | Literal['both']) -> PacketDirection | Literal['both']:
        if direction not in cls._VALID_DIRECTIONS:
            raise ValueError(f'Unsupported packet direction: {direction!r}')
        return direction

    @staticmethod
    def _convert_entry(entry: PyPacketSniffer.PacketLogEntry) -> PacketLogEntry:
        direction = 'StoC' if entry.direction == PyPacketSniffer.PacketDirection.StoC else 'CToS'
        return PacketLogEntry(
            direction=direction,
            tick=int(getattr(entry, 'tick', 0)),
            header=int(entry.header),
            size=int(entry.size),
            data=bytes(entry.data),
        )

    @staticmethod
    def _u32(data: bytes, offset: int) -> int | None:
        if len(data) < offset + 4:
            return None
        return struct.unpack_from('<I', data, offset)[0]

    @staticmethod
    def _f32(data: bytes, offset: int) -> float | None:
        if len(data) < offset + 4:
            return None
        return struct.unpack_from('<f', data, offset)[0]

    @staticmethod
    def _format_fields(fields: dict[str, object]) -> str:
        if not fields:
            return ''
        return ', '.join(f'{key}={value}' for key, value in fields.items())

    def _format_u32_words(self, raw: bytes, start: int = 4) -> dict[str, object]:
        fields: dict[str, object] = {}
        word_index = 0
        for offset in range(start, len(raw), 4):
            value = self._u32(raw, offset)
            if value is None:
                break
            word_index += 1
            fields[f'u32_{word_index}'] = value
        return fields

    def _format_u32_words_compact(self, raw: bytes, start: int = 4, max_words: int = 12) -> str:
        words: list[str] = []
        for offset in range(start, len(raw), 4):
            if len(words) >= max_words:
                words.append('...')
                break
            value = self._u32(raw, offset)
            if value is None:
                break
            words.append(f'@{offset}=0x{value:08X}')
        return ' '.join(words)

    @staticmethod
    def _utf16le_fixed(raw: bytes, offset: int, wchar_count: int) -> str:
        end = min(len(raw), offset + (wchar_count * 2))
        if end <= offset:
            return ''
        chunk = raw[offset:end]
        try:
            text = chunk.decode('utf-16le', errors='ignore')
        except Exception:
            return ''
        return text.split('\x00', 1)[0]

    def _utf16le_preview(self, raw: bytes, start: int = 4, min_chars: int = 3, max_hits: int = 6) -> str:
        hits: list[str] = []
        seen_offsets: set[int] = set()
        offset = start
        while offset + (min_chars * 2) <= len(raw) and len(hits) < max_hits:
            if offset in seen_offsets:
                offset += 2
                continue
            chars: list[str] = []
            cursor = offset
            while cursor + 1 < len(raw):
                code_unit = raw[cursor] | (raw[cursor + 1] << 8)
                if code_unit == 0:
                    break
                if code_unit < 0x20 or code_unit > 0x7E:
                    chars.clear()
                    break
                chars.append(chr(code_unit))
                cursor += 2
            if len(chars) >= min_chars and cursor + 1 < len(raw) and raw[cursor] == 0 and raw[cursor + 1] == 0:
                hits.append(f"@{offset}='{"".join(chars)}'")
                seen_offsets.update(range(offset, cursor + 2, 2))
                offset = cursor + 2
                continue
            offset += 2
        return ' | '.join(hits)

    def _name_re_probe(self, raw: bytes, start: int = 4) -> dict[str, object]:
        fields: dict[str, object] = {'body_len': max(0, len(raw) - start)}
        words = self._format_u32_words_compact(raw, start=start)
        if words:
            fields['u32'] = words
        utf16 = self._utf16le_preview(raw, start=start)
        if utf16:
            fields['utf16'] = utf16
        return fields

    def _find_known_subpackets(self, raw: bytes) -> list[str]:
        found: list[str] = []
        seen: set[tuple[int, int]] = set()
        for offset in range(0, max(0, len(raw) - 1), 2):
            header = int.from_bytes(raw[offset:offset + 2], 'little', signed=False)
            if header in KNOWN_CTOS_LENGTHS and (offset, header) not in seen:
                seen.add((offset, header))
                found.append(f'@{offset}:{self.get_packet_name("CToS", header)}')
        return found

    def _decode_stoc_packet(self, header: int, size: int, raw: bytes) -> str:
        fields: dict[str, object] = {}
        if header == 0x009F and len(raw) >= 16:
            value_id = self._u32(raw, 4)
            fields = {'type': GENERIC_VALUE_IDS.get(value_id or 0, value_id), 'agent_id': self._u32(raw, 8), 'value': self._u32(raw, 12)}
        elif header == 0x00A0 and len(raw) >= 20:
            fields = {'type': GENERIC_VALUE_IDS.get(self._u32(raw, 4) or 0, self._u32(raw, 4)), 'target_id': self._u32(raw, 8), 'caster_id': self._u32(raw, 12), 'value': self._u32(raw, 16)}
        elif header == 0x00A2 and len(raw) >= 16:
            fields = {'type': self._u32(raw, 4), 'agent_id': self._u32(raw, 8), 'value': round(self._f32(raw, 12) or 0.0, 4)}
        elif header == 0x00A3 and len(raw) >= 20:
            fields = {'type': self._u32(raw, 4), 'target_id': self._u32(raw, 8), 'cause_id': self._u32(raw, 12), 'value': round(self._f32(raw, 16) or 0.0, 4)}
        elif header == 0x00E4 and len(raw) >= 16:
            fields = {'agent_id': self._u32(raw, 4), 'skill_id': self._u32(raw, 8), 'skill_instance': self._u32(raw, 12)}
        elif header == 0x00E5 and len(raw) >= 20:
            fields = {'agent_id': self._u32(raw, 4), 'skill_id': self._u32(raw, 8), 'skill_instance': self._u32(raw, 12), 'recharge': self._u32(raw, 16)}
        elif header == 0x00E6 and len(raw) >= 16:
            fields = {'agent_id': self._u32(raw, 4), 'skill_id': self._u32(raw, 8), 'skill_instance': self._u32(raw, 12)}
        elif header == 0x0171 and len(raw) >= 24:
            fields = {'hero_id': self._u32(raw, 4), 'profession': self._u32(raw, 8), 'arg3': self._u32(raw, 12), 'arg4': self._u32(raw, 16), 'arg5': self._u32(raw, 20)}
        elif header == 0x0127 and len(raw) >= 180:
            fields = {'invited_name': self._utf16le_fixed(raw, 4, 20), 'current_name': self._utf16le_fixed(raw, 44, 20), 'invited_by': self._utf16le_fixed(raw, 84, 20), 'context_info': self._utf16le_fixed(raw, 124, 28), 'minutes_since_login': self._u32(raw, 176), 'join_date': self._u32(raw, 180), 'status': self._u32(raw, 184), 'member_type': self._u32(raw, 188)}
        elif header == 0x0121 and len(raw) >= 128:
            fields = {'guild_id': self._u32(raw, 4), 'name': self._utf16le_fixed(raw, 24, 32), 'tag': self._utf16le_fixed(raw, 88, 6), 'features': self._u32(raw, 100), 'territory': self._u32(raw, 104), 'faction': self._u32(raw, 132), 'factions_count': self._u32(raw, 136), 'qualifier_points': self._u32(raw, 140), 'rating': self._u32(raw, 144), 'rank': self._u32(raw, 148)}
        elif header in {0x0029, 0x002B, 0x002E} and len(raw) >= 16:
            fields = {'agent_id': self._u32(raw, 4), 'x': round(self._f32(raw, 8) or 0.0, 4), 'y': round(self._f32(raw, 12) or 0.0, 4)}
        elif header == 0x001E and len(raw) >= 8:
            fields = {'delta_or_tick': self._u32(raw, 4)}
        elif header in NAME_RE_STOC_HEADERS:
            fields = self._name_re_probe(raw)
        base = f'{self.get_packet_name("StoC", header)} size={size}'
        suffix = self._format_fields(fields)
        return f'{base} | {suffix}' if suffix else base

    def _decode_ctos_packet(self, header: int, size: int, raw: bytes) -> str:
        fields: dict[str, object] = {}
        if header == 0x23 and len(raw) >= 12:
            fields = {'target_id': self._u32(raw, 4), 'call_type_or_flag': self._u32(raw, 8)}
        elif header == 0x26 and len(raw) >= 12:
            fields = {'agent_id': self._u32(raw, 4), 'flag': self._u32(raw, 8)}
        elif header == 0x2C and len(raw) >= 12:
            fields = {'item_id': self._u32(raw, 4), 'quantity': self._u32(raw, 8)}
        elif header == 0x30 and len(raw) >= 8:
            fields = {'item_id': self._u32(raw, 4)}
        elif header == 0x39 and len(raw) >= 12:
            fields = {'agent_id': self._u32(raw, 4), 'flag': self._u32(raw, 8)}
        elif header == 0x3D and len(raw) >= 28:
            fields = {'x': round(self._f32(raw, 4) or 0.0, 4), 'y': round(self._f32(raw, 8) or 0.0, 4), 'z_plane_or_unk': self._u32(raw, 12), 'dir_x': round(self._f32(raw, 16) or 0.0, 4), 'dir_y': round(self._f32(raw, 20) or 0.0, 4), 'flags': self._u32(raw, 24)}
        elif header == 0x3E and len(raw) >= 16:
            fields = {'x': round(self._f32(raw, 4) or 0.0, 4), 'y': round(self._f32(raw, 8) or 0.0, 4), 'z_plane_or_unk': self._u32(raw, 12)}
        elif header == 0x40 and len(raw) >= 12:
            fields = {'heading': round(self._f32(raw, 4) or 0.0, 4), 'pitch': round(self._f32(raw, 8) or 0.0, 4)}
        elif header == 0x46 and len(raw) >= 20:
            fields = {'skill_id': self._u32(raw, 4), 'type': self._u32(raw, 8), 'target_id': self._u32(raw, 12), 'flags': self._u32(raw, 16)}
        elif header == 0x00C1 and len(raw) >= 12:
            fields = self._format_u32_words(raw)
        else:
            subpackets = self._find_known_subpackets(raw)
            if subpackets:
                fields = {'stream_fragment': subpackets}
            elif len(raw) >= 8:
                fields = self._name_re_probe(raw)
        base = f'{self.get_packet_name("CToS", header)} size={size}'
        suffix = self._format_fields(fields)
        return f'{base} | {suffix}' if suffix else base


SNIFFER = PacketSniffer.instance()

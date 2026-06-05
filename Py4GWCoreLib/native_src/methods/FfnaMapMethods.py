"""Pathing data loading for arbitrary maps via gw.dat FFNA files.

Reads FFNA type-3 pathing data from the game's dat file, parses trapezoid
geometry and adjacency, and returns PathingMap objects compatible with
the live-map pathing structures in MapContext.

Usage::

    maps = FfnaMapMethods.GetPathingMapsForMap(639)
"""

import struct
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List

from ..context.MapContext import (
    PathingMap, PathingTrapezoid, Portal, Node, SpawnPoint,
    TravelPortal, _PORTAL_MODEL_FILE_IDS,
)


# ── FFNA constants ────────────────────────────────────────────────────────

FFNA_MAGIC = 0x616E6666  # 'ffna' as LE uint32
CHUNK_TYPE_TRAPEZOID = 0x20000008
CHUNK_TYPE_PROPINFO = 0x20000004        # prop instance placements (was CHUNK_TYPE_TRANSITION)
CHUNK_TYPE_TRANSITION = CHUNK_TYPE_PROPINFO  # backward compat alias
CHUNK_TYPE_SPAWN = 0x20000007
CHUNK_TYPE_PROPFILENAMES = 0x21000004   # model file hash array
CHUNK_TYPE_PROPFILENAMES_ALT = 0x21000003


@dataclass(slots=True)
class FFNASpawnData:
    spawns1: list[SpawnPoint] = field(default_factory=list)
    spawns2: list[SpawnPoint] = field(default_factory=list)
    spawns3: list[SpawnPoint] = field(default_factory=list)


@dataclass(slots=True)
class GWPathingTrapezoid:
    adjacent1: int
    adjacent2: int
    adjacent3: int
    adjacent4: int
    transition1: int
    transition2: int
    yt: float
    yb: float
    xtl: float
    xtr: float
    xbl: float
    xbr: float


@dataclass(slots=True)
class FFNAPortalRecord:
    count: int          # traps in this portal on this plane
    trap_offset: int    # starting index into portal_trap_ids
    portal_index: int   # global portal ID (shared between 2 planes)


@dataclass(slots=True)
class FFNAPlaneData:
    trapezoids: list[GWPathingTrapezoid] = field(default_factory=list)
    portal_records: list[FFNAPortalRecord] = field(default_factory=list)
    portal_trap_ids: list[int] = field(default_factory=list)


# ── High-level API ────────────────────────────────────────────────────────

_SpawnResult = tuple[list[SpawnPoint], list[SpawnPoint], list[SpawnPoint]]
_EMPTY_SPAWNS: _SpawnResult = ([], [], [])


class FfnaMapMethods:
    _pathing_cache: dict[int, List[PathingMap]] = {}
    _spawn_cache: dict[int, _SpawnResult] = {}
    _portal_cache: dict[int, list[TravelPortal]] = {}

    @staticmethod
    def _read_ffna(map_id: int) -> Optional[bytes]:
        """Read raw FFNA bytes for a map. Returns None on failure."""
        from .DatFileMethods import dat_hooks_available, read_dat_file

        file_id = _MAP_ID_TO_DAT_FILE_ID.get(map_id)
        if not file_id or not dat_hooks_available():
            return None
        return read_dat_file(file_id, stream_id=1)

    @staticmethod
    def GetPathingMapsForMap(map_id: int) -> List[PathingMap]:
        """Get pathing for any map. Synchronous: cache hit or read/parse/cache."""
        if map_id in FfnaMapMethods._pathing_cache:
            return FfnaMapMethods._pathing_cache[map_id]

        data = FfnaMapMethods._read_ffna(map_id)
        if data is None:
            FfnaMapMethods._pathing_cache[map_id] = []
            return []

        plane_data = parse_ffna_pathing(data)
        FfnaMapMethods._pathing_cache[map_id] = _build_pathing_maps(plane_data) if plane_data else []
        return FfnaMapMethods._pathing_cache[map_id]

    @staticmethod
    def GetSpawnData(map_id: int) -> _SpawnResult:
        """Get (spawns1, spawns2, spawns3) for any map from .dat file."""
        if map_id in FfnaMapMethods._spawn_cache:
            return FfnaMapMethods._spawn_cache[map_id]

        data = FfnaMapMethods._read_ffna(map_id)
        if data is None:
            FfnaMapMethods._spawn_cache[map_id] = _EMPTY_SPAWNS
            return _EMPTY_SPAWNS

        sd = parse_ffna_spawns(data)
        if sd is None:
            FfnaMapMethods._spawn_cache[map_id] = _EMPTY_SPAWNS
            return _EMPTY_SPAWNS

        result = (sd.spawns1, sd.spawns2, sd.spawns3)
        FfnaMapMethods._spawn_cache[map_id] = result
        return result

    @staticmethod
    def GetTravelPortalsForMap(map_id: int) -> list[TravelPortal]:
        """Get travel portal positions for any map from .dat file (offline)."""
        if map_id in FfnaMapMethods._portal_cache:
            return FfnaMapMethods._portal_cache[map_id]

        data = FfnaMapMethods._read_ffna(map_id)
        if data is None:
            FfnaMapMethods._portal_cache[map_id] = []
            return []

        result = _parse_travel_portals(data)
        FfnaMapMethods._portal_cache[map_id] = result
        return result

    @staticmethod
    def ClearCache(map_id: Optional[int] = None) -> None:
        if map_id is None:
            FfnaMapMethods._pathing_cache.clear()
            FfnaMapMethods._spawn_cache.clear()
            FfnaMapMethods._portal_cache.clear()
        else:
            FfnaMapMethods._pathing_cache.pop(map_id, None)
            FfnaMapMethods._spawn_cache.pop(map_id, None)
            FfnaMapMethods._portal_cache.pop(map_id, None)

    @staticmethod
    def CacheResult(map_id: int, maps: List[PathingMap]) -> None:
        FfnaMapMethods._pathing_cache[map_id] = maps

    @staticmethod
    def HasDatEntry(map_id: int) -> bool:
        return map_id in _MAP_ID_TO_DAT_FILE_ID

    @staticmethod
    def GetAvailableMapIds() -> set[int]:
        return set(_MAP_ID_TO_DAT_FILE_ID.keys())


# ── Portal detection (offline, .dat file) ─────────────────────────────────

def _file_hash_to_file_id_offline(id0: int, id1: int) -> int:
    """Convert raw uint16 hash pair to .dat file ID (offline version)."""
    return ((id0 - 0xFF00FF) + id1 * 0xFF00) & 0xFFFFFFFF


def parse_ffna_prop_filenames(data: bytes) -> list[int]:
    """Parse PropFilenames chunk (0x21000004) → list of model file IDs."""
    if not is_ffna_pathing(data):
        return []

    chunks = _parse_chunks(data)

    chunk_data = None
    for ct, _cl, cd in chunks:
        if ct in (CHUNK_TYPE_PROPFILENAMES, CHUNK_TYPE_PROPFILENAMES_ALT):
            chunk_data = cd
            break

    if chunk_data is None or len(chunk_data) < 5:
        return []

    # Skip 5-byte Chunk4DataHeader (uint32 signature + uint8 version)
    entry_data = chunk_data[5:]
    num_entries = len(entry_data) // 6
    file_ids: list[int] = []
    for i in range(num_entries):
        off = i * 6
        id0, id1 = struct.unpack_from('<HH', entry_data, off)
        file_ids.append(_file_hash_to_file_id_offline(id0, id1))
    return file_ids


def parse_ffna_prop_positions(
    data: bytes,
) -> list[tuple[int, float, float, float]]:
    """Parse PropInfo chunk (0x20000004) → list of (filename_index, x, y, z).

    On-disk order at +2: x (float), y (float), z (float).
    GuildWarsMapBrowser labels field 2 as 'z' and field 3 as 'y' (negated),
    but GW runtime convention is x=X, y=Y, z=height(negative).
    """
    if not is_ffna_pathing(data):
        return []

    chunks = _parse_chunks(data)

    chunk_data = None
    for ct, _cl, cd in chunks:
        if ct == CHUNK_TYPE_PROPINFO:
            chunk_data = cd
            break

    if chunk_data is None:
        return []

    # Chunk3 header: uint32 magic + uint16 magic2 + uint32 prop_array_size = 10 bytes
    if len(chunk_data) < 12:
        return []
    off = 10

    num_props = struct.unpack_from('<H', chunk_data, off)[0]
    off += 2

    props: list[tuple[int, float, float, float]] = []
    for _ in range(num_props):
        if off + 48 > len(chunk_data):
            break
        filename_index = struct.unpack_from('<H', chunk_data, off)[0]
        x, y, z = struct.unpack_from('<fff', chunk_data, off + 2)
        num_trailing = chunk_data[off + 47]
        off += 48 + num_trailing * 8
        props.append((filename_index, x, y, z))

    return props


def _parse_travel_portals(data: bytes) -> list[TravelPortal]:
    """Extract travel portals from raw FFNA data."""
    filenames = parse_ffna_prop_filenames(data)
    if not filenames:
        return []

    positions = parse_ffna_prop_positions(data)
    if not positions:
        return []

    portals: list[TravelPortal] = []
    for filename_index, x, y, z in positions:
        if filename_index >= len(filenames):
            continue
        fid = filenames[filename_index]
        if fid in _PORTAL_MODEL_FILE_IDS:
            portals.append(TravelPortal(x=x, y=y, z=z, model_file_id=fid))
    return portals


# ── FFNA parsing ──────────────────────────────────────────────────────────

def _parse_chunks(data: bytes) -> list[tuple[int, int, bytes]]:
    pos = 5  # skip 4-byte magic + 1-byte type
    chunks: list[tuple[int, int, bytes]] = []
    while pos + 8 <= len(data):
        chunk_type, chunk_length = struct.unpack_from('<ii', data, pos)
        pos += 8
        if pos + chunk_length > len(data):
            break
        chunks.append((chunk_type, chunk_length, data[pos:pos + chunk_length]))
        pos += chunk_length
    return chunks


def is_ffna_pathing(data: bytes) -> bool:
    if len(data) < 5:
        return False
    magic = struct.unpack_from('<I', data, 0)[0]
    return magic == FFNA_MAGIC and data[4] == 3


def parse_ffna_trapezoids(
    data: bytes,
) -> Optional[list[list[GWPathingTrapezoid]]]:
    """Parse FFNA file, extract trapezoids grouped by plane.

    Legacy wrapper — prefer parse_ffna_pathing() for full portal data.
    """
    plane_data = parse_ffna_pathing(data)
    if plane_data is None:
        return None
    return [pd.trapezoids for pd in plane_data]


def parse_ffna_pathing(data: bytes) -> Optional[list[FFNAPlaneData]]:
    """Parse FFNA pathing chunk: trapezoids + portal data per plane."""
    if not is_ffna_pathing(data):
        return None

    chunks = _parse_chunks(data)

    trap_chunk = None
    for ct, cl, cd in chunks:
        if ct == CHUNK_TYPE_TRAPEZOID:
            trap_chunk = (cl, cd)
            break

    if trap_chunk is None:
        return None

    chunk_length, chunk_data = trap_chunk

    if chunk_length < 17:
        return None

    cur_pos = 13
    if cur_pos + 4 > chunk_length:
        return None
    skip_len = struct.unpack_from('<i', chunk_data, cur_pos)[0]
    cur_pos += skip_len + 5 + 4

    if cur_pos + 4 > chunk_length or cur_pos < 0:
        return None

    _section_count = struct.unpack_from('<i', chunk_data, cur_pos)[0]
    cur_pos += 4

    planes: list[FFNAPlaneData] = []
    current_plane: FFNAPlaneData | None = None

    while cur_pos < chunk_length:
        section_header = chunk_data[cur_pos]
        cur_pos += 1

        if cur_pos + 4 > chunk_length:
            break

        if section_header != 0x0B:
            section_length = struct.unpack_from('<i', chunk_data, cur_pos)[0]
        else:
            section_length = struct.unpack_from('<i', chunk_data, cur_pos)[0] // 2
        cur_pos += 4

        sec_end = cur_pos + section_length

        # Section 0x00: plane header — start a new plane
        if section_header == 0x00:
            current_plane = FFNAPlaneData()
            planes.append(current_plane)

        # Section 0x02: trapezoids
        elif section_header == 0x02 and current_plane is not None:
            tmp_pos = cur_pos
            while tmp_pos + 44 <= sec_end:
                if tmp_pos + 44 > chunk_length:
                    break
                adj1, adj2, adj3, adj4 = struct.unpack_from('<iiii', chunk_data, tmp_pos)
                tmp_pos += 16
                trans1, trans2 = struct.unpack_from('<HH', chunk_data, tmp_pos)
                tmp_pos += 4
                yt, yb, xtl, xtr, xbl, xbr = struct.unpack_from('<ffffff', chunk_data, tmp_pos)
                tmp_pos += 24
                current_plane.trapezoids.append(GWPathingTrapezoid(
                    adjacent1=adj1, adjacent2=adj2,
                    adjacent3=adj3, adjacent4=adj4,
                    transition1=trans1, transition2=trans2,
                    yt=yt, yb=yb, xtl=xtl, xtr=xtr, xbl=xbl, xbr=xbr,
                ))

        # Section 0x09: portal records (9 bytes each: u16 count, u16 offset, u16 field2, u16 portal_index, u8 pad)
        elif section_header == 0x09 and current_plane is not None:
            tmp_pos = cur_pos
            while tmp_pos + 9 <= sec_end:
                cnt, off, _f2, pidx = struct.unpack_from('<HHHH', chunk_data, tmp_pos)
                current_plane.portal_records.append(FFNAPortalRecord(
                    count=cnt, trap_offset=off, portal_index=pidx,
                ))
                tmp_pos += 9

        # Section 0x0A: portal trap indices (uint32 per-plane trap IDs)
        elif section_header == 0x0A and current_plane is not None:
            tmp_pos = cur_pos
            while tmp_pos + 4 <= sec_end:
                tid = struct.unpack_from('<I', chunk_data, tmp_pos)[0]
                current_plane.portal_trap_ids.append(tid)
                tmp_pos += 4

        # Inter-plane sections signal end of per-plane data
        elif section_header in (0x0C, 0x0D, 0x0E, 0xFF):
            break

        cur_pos = sec_end

    return planes if planes else None


def _angle_byte_to_float(b: int) -> float:
    """Convert quantized uint8 angle to float radians in [-pi, pi].

    The game uses signed int8 * (2π / 254), matching runtime float values exactly.
    """
    import math
    signed = b if b < 128 else b - 256
    return signed * (2.0 * math.pi / 254.0)


def _parse_tagged_entries(chunk: bytes, off: int) -> tuple[list[SpawnPoint], int]:
    """Parse uint16 count + N×13-byte entries (int32 x, int32 y, uint8 angle, uint32 tag)."""
    if off + 2 > len(chunk):
        return [], off
    count = struct.unpack_from('<H', chunk, off)[0]
    off += 2
    entries: list[SpawnPoint] = []
    for _ in range(count):
        if off + 13 > len(chunk):
            break
        x, y = struct.unpack_from('<ii', chunk, off)
        angle_byte = chunk[off + 8]
        tag_u32 = struct.unpack_from('<I', chunk, off + 9)[0]
        tag_be = struct.pack('>I', tag_u32)
        tag_str = ''.join(chr(c) if 32 <= c < 127 else '' for c in tag_be)
        entries.append(SpawnPoint(
            x=float(x), y=float(y),
            angle=_angle_byte_to_float(angle_byte),
            tag=tag_str,
        ))
        off += 13
    return entries, off


def _parse_float_entries(chunk: bytes, off: int) -> tuple[list[SpawnPoint], int]:
    """Parse uint16 count + N×8-byte entries (float x, float y)."""
    if off + 2 > len(chunk):
        return [], off
    count = struct.unpack_from('<H', chunk, off)[0]
    off += 2
    entries: list[SpawnPoint] = []
    for _ in range(count):
        if off + 8 > len(chunk):
            break
        x, y = struct.unpack_from('<ff', chunk, off)
        entries.append(SpawnPoint(x=x, y=y, angle=0.0, tag=''))
        off += 8
    return entries, off


_SPAWN_HEADER_SIZE = 0x1D  # 29-byte header (uint32 flags + 25 bytes metadata)


def parse_ffna_spawns(data: bytes) -> Optional[FFNASpawnData]:
    """Parse FFNA spawn chunk (0x20000007) into three spawn groups.

    spawns1: tagged spawns (map ID tags assign to zones, outpost portals, default)
    spawns2: tagged spawns (map ID tags, named markers like mars/badl/town, sub-areas)
    spawns3: untagged positions (no angle/tag in file, float coords only)
    """
    if not is_ffna_pathing(data):
        return None

    chunks = _parse_chunks(data)
    spawn_chunk = None
    for ct, _cl, cd in chunks:
        if ct == CHUNK_TYPE_SPAWN:
            spawn_chunk = cd
            break

    if spawn_chunk is None or len(spawn_chunk) < _SPAWN_HEADER_SIZE + 2:
        return None

    off = _SPAWN_HEADER_SIZE
    spawns1, off = _parse_tagged_entries(spawn_chunk, off)
    spawns2, off = _parse_tagged_entries(spawn_chunk, off)
    spawns3, off = _parse_float_entries(spawn_chunk, off)

    return FFNASpawnData(spawns1=spawns1, spawns2=spawns2, spawns3=spawns3)


def parse_ffna_transitions(data: bytes) -> list[tuple[float, float, float, float]]:
    """Parse FFNA file and extract transition vectors."""
    if not is_ffna_pathing(data):
        return []

    chunks = _parse_chunks(data)

    trans_chunk = None
    for ct, cl, cd in chunks:
        if ct == CHUNK_TYPE_TRANSITION:
            trans_chunk = (cl, cd)
            break

    if trans_chunk is None:
        return []

    chunk_length, chunk_data = trans_chunk
    result: list[tuple[float, float, float, float]] = []

    if chunk_length < 10:
        return []

    cur_pos = 6
    sec1_len = struct.unpack_from('<i', chunk_data, cur_pos)[0]
    cur_pos = 11 + sec1_len
    if chunk_length < cur_pos + 4:
        return []

    sec2_len = struct.unpack_from('<i', chunk_data, cur_pos)[0]
    cur_pos = 20 + sec1_len + sec2_len
    if chunk_length < cur_pos + 4:
        return []

    sec3_len = 2 * struct.unpack_from('<i', chunk_data, cur_pos)[0]
    cur_pos = 25 + sec1_len + sec2_len + sec3_len
    if chunk_length < cur_pos + 4:
        return []

    sec4_len = struct.unpack_from('<i', chunk_data, cur_pos)[0]
    cur_pos += 4
    if chunk_length < cur_pos + 4:
        return []

    cur_pos = 33 + sec1_len + sec2_len + sec3_len
    end = 29 + sec1_len + sec2_len + sec3_len + sec4_len
    while cur_pos + 16 <= end:
        if cur_pos + 16 > chunk_length:
            break
        x1, y1, x2, y2 = struct.unpack_from('<ffff', chunk_data, cur_pos)
        result.append((x1, y1, x2, y2))
        cur_pos += 16

    return result


# ── PathingMap builder ────────────────────────────────────────────────────

def _build_pathing_maps(plane_data: list[FFNAPlaneData]) -> List[PathingMap]:
    UINT32_MAX = 0xFFFFFFFF

    # Compute per-plane ID offsets so trap IDs are globally unique.
    plane_offsets: list[int] = []
    offset = 0
    for pd in plane_data:
        plane_offsets.append(offset)
        offset += len(pd.trapezoids)

    # Build portal_index → list of (plane, portal_list_idx) for pairing.
    portal_to_planes: dict[int, list[int]] = defaultdict(list)
    portal_index_to_loc: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for plane_idx, pd in enumerate(plane_data):
        for portal_list_idx, rec in enumerate(pd.portal_records):
            portal_to_planes[rec.portal_index].append(plane_idx)
            portal_index_to_loc[rec.portal_index].append((plane_idx, portal_list_idx))

    result: List[PathingMap] = []
    for plane_idx, pd in enumerate(plane_data):
        base = plane_offsets[plane_idx]
        trapezoids = [
            PathingTrapezoid(
                id=base + i,
                portal_left=t.transition1,
                portal_right=t.transition2,
                XTL=t.xtl, XTR=t.xtr, YT=t.yt,
                XBL=t.xbl, XBR=t.xbr, YB=t.yb,
                neighbor_ids=[
                    base + a for a in (t.adjacent1, t.adjacent2,
                                       t.adjacent3, t.adjacent4)
                    if a >= 0
                ],
            )
            for i, t in enumerate(pd.trapezoids)
        ]

        # Build Portal objects from section 0x9/0xA data.
        portals: list[Portal] = []
        for rec in pd.portal_records:
            # Find the other plane sharing this portal_index.
            other_planes = portal_to_planes.get(rec.portal_index, [])
            right_layer = -1
            for op in other_planes:
                if op != plane_idx:
                    right_layer = op
                    break

            # Resolve pair_index: find the matching portal on right_layer.
            pair_index = UINT32_MAX
            if right_layer >= 0:
                for loc_plane, loc_idx in portal_index_to_loc[rec.portal_index]:
                    if loc_plane == right_layer:
                        pair_index = loc_idx
                        break

            # Resolve per-plane trap IDs to global IDs via section 0xA.
            trap_indices: list[int] = []
            for k in range(rec.count):
                idx = rec.trap_offset + k
                if idx < len(pd.portal_trap_ids):
                    trap_indices.append(base + pd.portal_trap_ids[idx])

            portals.append(Portal(
                left_layer_id=plane_idx,
                right_layer_id=right_layer,
                flags=0,  # FFNA doesn't store flags; game sets at runtime
                pair_index=pair_index,
                count=rec.count,
                trapezoid_indices=trap_indices,
            ))

        result.append(PathingMap(
            zplane=plane_idx,
            h0004=0, h0008=0, h000C=0, h0010=0,
            trapezoid_count=len(trapezoids),
            sink_node_count=0, x_node_count=0,
            y_node_count=0, portal_count=len(portals),
            trapezoids=trapezoids,
            sink_nodes=[], x_nodes=[], y_nodes=[], portals=portals,
            h0034=0, h0038=0,
            root_node=Node(type=0, id=0),
            root_node_id=UINT32_MAX,
            h0048=None, h004C=None, h0050=None,
        ))
    return result


# ── map_id -> dat file_id table ───────────────────────────────────────────

_MAP_ID_TO_DAT_FILE_ID = {
    2: 127428, 3: 213190, 6: 127532, 7: 127484, 8: 127496, 9: 127532, 10: 13531, 11: 40796,
    12: 13105, 13: 14936, 14: 35379, 15: 33663, 16: 33665, 17: 34039, 18: 34045, 19: 37216,
    20: 33642, 21: 13265, 22: 12040, 23: 11565, 24: 47660, 25: 13019, 26: 46589, 28: 13824,
    29: 13906, 30: 13907, 31: 157168, 32: 13913, 33: 14937, 34: 63058, 35: 55563, 36: 14936,
    37: 152265, 38: 52837, 39: 14937, 40: 51061, 41: 40803, 42: 40809, 43: 40812, 44: 40798,
    45: 40802, 46: 40808, 47: 40801, 48: 40811, 49: 40759, 51: 157168, 52: 127565, 53: 41192,
    54: 41193, 55: 13565, 56: 34216, 57: 34216, 58: 321286, 59: 34216, 60: 34320, 61: 34321,
    62: 34222, 63: 34281, 64: 34225, 67: 127565, 68: 127589, 69: 127592, 71: 127643, 72: 63059,
    73: 10682, 75: 14004, 77: 155155, 78: 13989, 80: 15282, 81: 22052, 82: 166048, 84: 16428,
    87: 46591, 88: 46592, 89: 46593, 90: 46594, 91: 12244, 92: 46597, 94: 46598, 95: 46599,
    96: 46600, 97: 46601, 98: 46602, 99: 46603, 100: 46604, 101: 51060, 102: 51061, 103: 51062,
    104: 51063, 105: 51064, 106: 51064, 107: 51066, 108: 52166, 109: 52918, 110: 52821, 111: 52822,
    112: 52830, 113: 52835, 114: 52836, 115: 52837, 116: 52838, 117: 52839, 118: 52840, 119: 52837,
    120: 52842, 121: 55563, 122: 55552, 123: 55559, 124: 55560, 126: 55617, 128: 155165, 129: 154590,
    130: 155165, 131: 51063, 132: 46593, 133: 46594, 134: 46603, 135: 51066, 136: 34222, 137: 34281,
    138: 34045, 139: 40798, 140: 40803, 141: 40811, 142: 40812, 144: 155167, 145: 116016, 146: 113021,
    147: 116025, 148: 113021, 152: 52835, 153: 52836, 154: 52166, 155: 12244, 156: 46597, 157: 46598,
    158: 46599, 159: 46602, 162: 113437, 163: 113190, 164: 113021, 165: 113355, 166: 113437, 181: 46603,
    188: 165083, 189: 165176, 191: 152201, 193: 155157, 194: 157175, 195: 154527, 196: 156966, 197: 157169,
    198: 155075, 199: 154893, 200: 155089, 201: 154590, 202: 155121, 203: 155150, 204: 155168, 205: 154638,
    206: 152201, 209: 157242, 210: 154676, 211: 155151, 212: 156969, 213: 156882, 214: 156827, 215: 157176,
    216: 157177, 217: 157178, 218: 155158, 219: 155159, 220: 157179, 222: 155165, 224: 155167, 225: 157212,
    226: 157213, 227: 155168, 230: 155172, 232: 157176, 233: 157212, 234: 155176, 235: 157021, 236: 157048,
    237: 157079, 238: 157087, 239: 157167, 240: 321291, 241: 157172, 242: 156969, 243: 157214, 244: 155158,
    245: 156827, 246: 156882, 247: 155159, 248: 165811, 249: 157087, 250: 156969, 251: 157048, 252: 156969,
    256: 157179, 265: 157177, 266: 167860, 269: 157178, 272: 155155, 273: 155157, 274: 167864, 277: 155168,
    278: 155089, 279: 155167, 280: 165811, 281: 165826, 282: 165842, 283: 155151, 284: 157178, 286: 154527,
    287: 157242, 288: 154893, 289: 155121, 290: 157175, 291: 157176, 292: 157176, 293: 155164, 294: 155164,
    295: 155166, 296: 155166, 297: 155168, 298: 155168, 301: 157212, 302: 157167, 303: 157167, 307: 188821,
    313: 156969, 318: 127428, 319: 52918, 320: 59894, 321: 154123, 322: 46603, 330: 165788, 344: 14004,
    345: 13989, 347: 16428, 348: 155151, 349: 154676, 350: 154893, 360: 165764, 361: 157215, 362: 157221,
    363: 165686, 364: 165764, 365: 246766, 369: 218083, 371: 212775, 373: 212844, 375: 212976, 376: 212976,
    377: 215315, 379: 215191, 380: 218847, 382: 215155, 384: 214069, 386: 218925, 387: 216120, 388: 155164,
    389: 155164, 390: 155166, 391: 155166, 392: 211038, 393: 211038, 394: 215636, 395: 216883, 396: 211075,
    397: 217149, 398: 211957, 399: 217403, 402: 212420, 403: 212420, 404: 215818, 406: 217955, 407: 212438,
    413: 212497, 414: 216071, 415: 195066, 416: 156969, 419: 211935, 424: 212586, 425: 214069, 426: 213215,
    427: 215315, 428: 217403, 429: 214476, 430: 321293, 431: 210513, 433: 212428, 434: 212497, 435: 211935,
    436: 216120, 437: 210198, 438: 210198, 439: 210292, 440: 210292, 441: 216292, 442: 210307, 443: 216305,
    444: 215929, 446: 210324, 449: 214476, 450: 214315, 451: 219215, 456: 249289, 461: 16428, 463: 16428,
    468: 219186, 469: 214315, 470: 216012, 473: 214315, 474: 214315, 476: 212000, 477: 212775, 478: 214076,
    479: 210612, 480: 210324, 481: 216337, 482: 290923, 483: 216351, 484: 216372, 485: 287262, 486: 210727,
    487: 210727, 488: 216388, 489: 210732, 491: 210623, 492: 210629, 493: 214476, 494: 214315, 495: 214315,
    496: 214168, 497: 216140, 499: 288299, 501: 290897, 502: 210626, 513: 288769, 531: 208982, 532: 209436,
    537: 209230, 539: 209230, 540: 210082, 543: 214476, 544: 249289, 545: 210316, 546: 290943, 548: 289087,
    549: 246766, 553: 289616, 554: 212792, 558: 287493, 559: 214315, 566: 287674, 569: 287783, 572: 288071,
    593: 290186, 598: 290232, 607: 292090, 624: 287262, 625: 292300, 638: 287493, 639: 287674, 640: 287783,
    641: 288071, 642: 288299, 643: 288769, 644: 289087, 645: 289616, 646: 288299, 647: 289960, 648: 289960,
    649: 290181, 650: 290181, 651: 291140, 652: 290182, 673: 325399, 675: 288299, 682: 325404, 683: 325404,
    684: 325404, 685: 325404, 691: 292198, 692: 292198, 693: 292198, 704: 292319, 726: 289087, 808: 13565,
    809: 13565, 810: 13565, 811: 22052, 812: 33642, 813: 33642, 814: 166048, 815: 156969, 816: 156969,
    818: 214476, 819: 214476, 820: 214476, 821: 288299,
}

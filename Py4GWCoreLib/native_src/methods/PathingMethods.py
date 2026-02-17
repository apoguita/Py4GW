"""Pathing data loading for arbitrary maps via gw.dat FFNA files.

Reads FFNA type-3 pathing data from the game's dat file, parses trapezoid
geometry and adjacency, and returns ``PathingMap`` objects compatible with
the live-map pathing structures in ``MapContext``.

Usage (from widget or corelib wrapper)::

    maps = PathingMethods.GetPathingMapsForMap(639)
    # Returns cached data on hit, or reads/parses/caches synchronously on miss.
"""

import struct
from dataclasses import dataclass
from typing import Optional, List

from ..context.MapContext import PathingMap, PathingTrapezoid, Node


# ─── FFNA constants ───────────────────────────────────────────────────────

FFNA_MAGIC = 0x616E6666  # 'ffna' as LE uint32
CHUNK_TYPE_TRAPEZOID = 0x20000008
CHUNK_TYPE_TRANSITION = 0x20000004


@dataclass(slots=True)
class GWPathingTrapezoid:
    """Raw trapezoid as stored in the FFNA file."""
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


# ─── High-level API ───────────────────────────────────────────────────────

class PathingMethods:
    _cache: dict[int, List[PathingMap]] = {}

    @staticmethod
    def GetPathingMapsForMap(map_id: int) -> List[PathingMap]:
        """Get pathing for any map.  Synchronous: cache hit or read/parse/cache."""
        if map_id in PathingMethods._cache:
            return PathingMethods._cache[map_id]

        from .DatFileMethods import dat_hooks_available, read_dat_file

        file_id = _MAP_ID_TO_DAT_FILE_ID.get(map_id)
        if not file_id or not dat_hooks_available():
            return []

        data = read_dat_file(file_id, stream_id=1)
        if data is None:
            PathingMethods._cache[map_id] = []
            return []

        planes = parse_ffna_trapezoids(data)
        PathingMethods._cache[map_id] = _build_pathing_maps(planes) if planes else []
        return PathingMethods._cache[map_id]

    @staticmethod
    def ClearCache(map_id: Optional[int] = None) -> None:
        """Clear cached pathing data.  No args = clear all."""
        if map_id is None:
            PathingMethods._cache.clear()
        else:
            PathingMethods._cache.pop(map_id, None)

    @staticmethod
    def CacheResult(map_id: int, maps: List[PathingMap]) -> None:
        """Store an externally-obtained pathing result (e.g. live data)."""
        PathingMethods._cache[map_id] = maps

    @staticmethod
    def HasDatEntry(map_id: int) -> bool:
        """Return True if the static table has a dat file_id for this map."""
        return map_id in _MAP_ID_TO_DAT_FILE_ID

    @staticmethod
    def GetAvailableMapIds() -> set[int]:
        """Return the set of map IDs that offline pathing can be loaded for."""
        return set(_MAP_ID_TO_DAT_FILE_ID.keys())


# ─── FFNA parsing helpers ─────────────────────────────────────────────────

def _parse_chunks(data: bytes) -> list[tuple[int, int, bytes]]:
    """Split an FFNA file into (chunk_type, chunk_length, chunk_data) tuples."""
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
    """Return True if *data* is an FFNA type-3 file (pathing data)."""
    if len(data) < 5:
        return False
    magic = struct.unpack_from('<I', data, 0)[0]
    return magic == FFNA_MAGIC and data[4] == 3


def parse_ffna_trapezoids(
    data: bytes,
) -> Optional[list[list[GWPathingTrapezoid]]]:
    """Parse an FFNA file and extract trapezoids grouped by plane.

    Returns ``trapezoids_by_plane[plane_index]`` which is a list of
    :class:`GWPathingTrapezoid`.  Returns ``None`` on parse failure.
    """
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
    trapezoids_by_plane: list[list[GWPathingTrapezoid]] = []

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

    plane = 0
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

        if section_header == 2:
            tmp_pos = cur_pos
            while tmp_pos + 44 <= cur_pos + section_length:
                if tmp_pos + 44 > chunk_length:
                    break

                adj1, adj2, adj3, adj4 = struct.unpack_from('<iiii', chunk_data, tmp_pos)
                tmp_pos += 16
                trans1, trans2 = struct.unpack_from('<hh', chunk_data, tmp_pos)
                tmp_pos += 4
                yt, yb, xtl, xtr, xbl, xbr = struct.unpack_from('<ffffff', chunk_data, tmp_pos)
                tmp_pos += 24

                if yt != yb:
                    while plane >= len(trapezoids_by_plane):
                        trapezoids_by_plane.append([])
                    trapezoids_by_plane[plane].append(GWPathingTrapezoid(
                        adjacent1=adj1, adjacent2=adj2,
                        adjacent3=adj3, adjacent4=adj4,
                        transition1=trans1, transition2=trans2,
                        yt=yt, yb=yb, xtl=xtl, xtr=xtr, xbl=xbl, xbr=xbr,
                    ))

            plane += 1

        cur_pos += section_length

    return trapezoids_by_plane if trapezoids_by_plane else None


def parse_ffna_transitions(data: bytes) -> list[tuple[float, float, float, float]]:
    """Parse FFNA file and extract transition vectors.

    Returns list of ``(x1, y1, x2, y2)`` tuples.
    """
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


# ─── PathingMap builder ───────────────────────────────────────────────────

def _build_pathing_maps(planes: list[list[GWPathingTrapezoid]]) -> List[PathingMap]:
    """Convert parsed FFNA planes into PathingMap objects."""
    UINT32_MAX = 0xFFFFFFFF
    result: List[PathingMap] = []
    for plane_idx, gw_traps in enumerate(planes):
        trapezoids = [
            PathingTrapezoid(
                id=i,
                portal_left=t.transition1,
                portal_right=t.transition2,
                XTL=t.xtl, XTR=t.xtr, YT=t.yt,
                XBL=t.xbl, XBR=t.xbr, YB=t.yb,
                neighbor_ids=[
                    a for a in (t.adjacent1, t.adjacent2,
                                t.adjacent3, t.adjacent4)
                    if a >= 0
                ],
            )
            for i, t in enumerate(gw_traps)
        ]
        result.append(PathingMap(
            zplane=plane_idx,
            h0004=0, h0008=0, h000C=0, h0010=0,
            trapezoid_count=len(trapezoids),
            sink_node_count=0, x_node_count=0,
            y_node_count=0, portal_count=0,
            trapezoids=trapezoids,
            sink_nodes=[], x_nodes=[], y_nodes=[], portals=[],
            h0034=0, h0038=0,
            root_node=Node(type=0, id=0),
            root_node_id=UINT32_MAX,
            h0048=None, h004C=None, h0050=None,
        ))
    return result


# ─── map_id → dat file_id table ───────────────────────────────────────────
# Static because AreaInfoStruct.file_id is zero for most maps at runtime;
# no known dynamic source exists for this mapping. Static mapping also used by
# GWMapBrowser and GW-Pathing-Map-Visualizer.  
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

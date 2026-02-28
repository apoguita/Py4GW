"""Game string table: load from gw.dat once, decode on demand.

Pipeline (encoded codepoints → display text):

  1. The game represents translatable strings as uint16 codepoint arrays,
     not text. These encode a (table_index, encryption_key) pair using
     variable-length base-0x7F00 encoding (see _parse_codepoints).

  2. The string table (loaded once from gw.dat, ~100K entries per language)
     maps table_index → raw entry bytes.

  3. Each entry is [u16 size | u16 base_char | u8 bits_per_char | u8 flags | payload].
     If key != 0, payload is RC4-encrypted with a key derived from the
     uint64 via a custom game-specific hash (not standard SHA-1). After
     decryption, payload is bit-unpacked: values < 32 map through a fixed
     character table, >= 32 offset from base_char. Special case:
     base_char=0 + bpc=16 means raw UTF-16LE.

  4. Player names bypass all of this — codepoint prefix 0xBA9 followed
     by inline ASCII.

  5. Results are cached by codepoint tuple. Grammar tags ([M], [F], etc.)
     are stripped in postprocessing.
"""

import ctypes
import ctypes.wintypes
import re
import struct
from typing import Optional

from ..context.TextContext import TextParser


# ─── Codepoint parsing (base-0x7F00 encoding) ────────────────────────────

_BASE = 0x0100
_MORE = 0x8000
_RANGE = _MORE - _BASE  # 0x7F00


def _parse_codepoints(codepoints: tuple[int, ...]) -> tuple[int, int]:
    """Parse encoded codepoints → (string_index, uint64_key)."""
    if not codepoints:
        return (0, 0)

    idx = 0
    pos = 0
    for pos, cp in enumerate(codepoints):
        if cp == 0:
            break
        digit = (cp & 0x7FFF) - _BASE
        if digit < 0:
            break
        if cp & _MORE:
            idx = (idx + digit) * _RANGE
        else:
            idx = idx + digit
            pos += 1
            break

    key = 0
    if pos < len(codepoints) and codepoints[pos] != 0 and (codepoints[pos] & _MORE):
        for i in range(pos, len(codepoints)):
            cp = codepoints[i]
            if cp == 0:
                break
            digit = (cp & 0x7FFF) - _BASE
            if digit < 0:
                break
            if cp & _MORE:
                key = (key + digit) * _RANGE
            else:
                key = key + digit
                break

    return (idx, key)


# ─── Entry decoding (key derivation + RC4 + bit-unpack) ──────────────────

# Bit-packed char table (values 0-31). Stored as tuple: tuple[i] returns an
# existing str ref; str[i] allocates a new single-char str every time.
_CHAR_TUPLE = (
    '\x00', '0', '1', '2', '3', '4', '5', '6',
    's', 't', 'r', 'n', 'u', 'm', '(', ')',
    '[', ']', '<', '>', '%', '#', '/', ':',
    '-', "'", '"', ' ', ',', '.', '!', '\n',
)

# Pre-compiled struct operations
_unpack_hdr = struct.Struct('<HHB').unpack_from
_pack_Q = struct.Struct('<Q').pack
_pack_5I = struct.Struct('<5I').pack
_unpack_5I = struct.Struct('<5I').unpack

# Cached (base_char, bpc) → full char lookup table. Merges the <0x20 char
# table with the base_char offset range into one flat tuple, eliminating a
# branch + chr() call per character in the bit-unpack loop.
_char_table_cache: dict[tuple[int, int], tuple[str, ...]] = {}


def _rc4_python(key: bytes, data: bytes) -> bytes:
    """Pure-Python RC4."""
    s = list(range(256))
    j = 0
    for i, ek in enumerate((key * 13)[:256]):
        j = (j + s[i] + ek) & 0xFF
        s[i], s[j] = s[j], s[i]
    out = bytearray(len(data))
    ri = rj = 0
    for n, rb in enumerate(data):
        ri = (ri + 1) & 0xFF
        rj = (rj + s[ri]) & 0xFF
        s[ri], s[rj] = s[rj], s[ri]
        out[n] = rb ^ s[(s[ri] + s[rj]) & 0xFF]
    return bytes(out)


def _decode_entry(
    entry_data: bytes, key: int,
    _CT=_CHAR_TUPLE,
    _hdr=_unpack_hdr, _packQ=_pack_Q, _pack5I=_pack_5I, _unpack5I=_unpack_5I,
    _ct_cache=_char_table_cache,
) -> Optional[str]:
    """Decode a string table entry (key derivation + RC4 decrypt + bit-unpack)."""
    if len(entry_data) < 6:
        return None

    total_size, base_char, bpc = _hdr(entry_data)

    if total_size <= 6 or total_size > len(entry_data):
        return None
    payload_len = total_size - 6

    if key != 0:
        # Key derivation: uint64 → 20-byte pad → custom hash → 20-byte RC4 key
        kb = _packQ(key & 0xFFFFFFFFFFFFFFFF)
        buf20 = kb + kb + kb[:4]

        w0, w1, w2, w3, w4 = _unpack5I(buf20)
        M = 0xFFFFFFFF

        a = (w0 + 0x9fb498b3) & M
        b = (w1 + 0x66b0cd0d + (((a << 5) | (a >> 27)) & M)) & M
        a30 = ((a << 30) | (a >> 2)) & M

        f_a = (~(a & 0x22222222) & 0x7bf36ae2) & M
        c = ((((b << 5) | (b >> 27)) & M) + w2 + f_a + 0xf33d5697) & M
        b30 = ((b << 30) | (b >> 2)) & M

        g = (((a30 ^ 0x59d148c0) & b) ^ 0x59d148c0) & M
        d = (w3 + (((c << 5) | (c >> 27)) & M) + g + 0xd675e47b) & M

        c30 = ((c << 30) | (c >> 2)) & M
        h = (((a30 ^ b30) & c) ^ a30) & M
        e = (h + w4 + (((d << 5) | (d >> 27)) & M) + 0xb453c259 + w0) & M

        rc4_key = _pack5I(e, (w1 + d) & M, (w2 + c30) & M, (b30 + w3) & M, (a30 + w4) & M)
        payload = _rc4_decrypt(rc4_key, entry_data[6:total_size])
    else:
        payload = entry_data[6:total_size]

    # Raw UTF-16LE (base_char=0, bpc=16) — C-level codec
    if base_char == 0 and bpc == 0x10:
        text = payload[:len(payload) & ~1].decode('utf-16-le')
        null = text.find('\x00')
        return text[:null] if null >= 0 else text

    if bpc == 0:
        return None

    # Bit-unpack — unified char table eliminates per-char branch + chr()
    ct_key = (base_char, bpc)
    ct = _ct_cache.get(ct_key)
    if ct is None:
        bo = base_char - 0x20
        ct = tuple(_CT[v] if v < 0x20 else chr(bo + v) for v in range(1 << bpc))
        _ct_cache[ct_key] = ct

    bit_buf = int.from_bytes(payload, 'little')
    mask = (1 << bpc) - 1
    max_chars = (payload_len * 8) // bpc

    chars = []
    _append = chars.append
    for _ in range(max_chars):
        val = bit_buf & mask
        bit_buf >>= bpc
        if val == 0:
            break
        _append(ct[val])

    return ''.join(chars)


# ─── String table state ──────────────────────────────────────────────────

_string_table: dict[int, bytes] = {}
_string_table_loaded: bool = False
_load_enqueued: bool = False

_decode_cache: dict[bytes, str] = {}
_pending: set[bytes] = set()

from concurrent.futures import ThreadPoolExecutor as _TPE
_decode_pool = _TPE(max_workers=1)


# ─── Postprocessing ──────────────────────────────────────────────────────

_BRACKET_SUBS = {
    "[lbracket]": "[",
    "[rbracket]": "]",
}

_GRAMMAR_TAG_RE = re.compile(
    r'^\[(M|F|N|U|P|PM|PF|PN|m|u|null|proper|plur|sing)\]'
)


def _postprocess(text: str) -> str:
    text = _GRAMMAR_TAG_RE.sub('', text)
    for old, new in _BRACKET_SUBS.items():
        if old in text:
            text = text.replace(old, new)
    return text


# ─── Loading ─────────────────────────────────────────────────────────────

def _load_dat_file(file_hash: str) -> Optional[bytes]:
    """Load a single dat file by its hash string. Must run on game thread."""
    from ..methods.DatFileMethods import read_dat_file_by_hash
    return read_dat_file_by_hash(file_hash)


def _parse_string_file(file_data: bytes, start_index: int) -> int:
    """Parse all entries from a string file into _string_table. Returns count."""
    count = 0
    pos = 0
    idx = start_index
    while pos < len(file_data) - 2:
        entry_size = struct.unpack_from('<H', file_data, pos)[0]
        if entry_size < 6 or entry_size > 8192:
            break
        _string_table[idx] = file_data[pos:pos + entry_size]
        pos += entry_size
        idx += 1
        count += 1
    return count


def _do_load_string_table(language: int) -> None:
    """Synchronous load — must run on the game thread.

    Reads file slot metadata from TextParser, loads each dat file via
    DatFileMethods, and parses all entries into _string_table.
    Caller must ensure TextParser context is fresh (e.g. _update_ptr ran).
    """
    global _string_table_loaded
    if _string_table_loaded:
        return

    tp = TextParser.get_context()
    if tp is None:
        return

    epf = tp.entries_per_file
    if not epf:
        return

    lang_slot = tp.language_slots[language]

    for slot_idx in range(lang_slot.slot_count):
        file_slot = tp.get_file_slot(slot_idx, language)
        if file_slot is None or not file_slot.file_hash_ptr:
            continue
        try:
            file_data = _load_dat_file(file_slot.file_hash)
        except Exception:
            continue
        if not file_data:
            continue
        _parse_string_file(file_data, slot_idx * epf)

    _string_table_loaded = True


def load_string_table(language: int = 0) -> None:
    """Enqueue string table load on the game thread.

    Safe to call from any context. The actual load runs on the next
    game frame via Game.enqueue. After completion, _string_table_loaded
    is True and decode functions return results.
    """
    global _load_enqueued
    if _string_table_loaded or _load_enqueued:
        return
    _load_enqueued = True

    import Py4GW
    Py4GW.Game.enqueue(lambda: _do_load_string_table(language))


def _get_client_language() -> int:
    """Read the client's text language from TextParser context."""
    tp = TextParser.get_context()
    if tp is None:
        return 0
    return tp.language_id


# ─── RC4 backend (Windows CNG, pure-Python fallback) ─────────────────────

def _rc4_cng():
    """Try to bind RC4 from Windows CNG (bcrypt.dll).

    bcrypt.dll is a system DLL loaded into every Windows process.
    GetModuleHandleW retrieves the existing handle without LoadLibrary,
    so no DllMain runs — safe in injected process contexts.
    """
    try:
        GMH = ctypes.windll.kernel32.GetModuleHandleW
        GMH.restype = ctypes.wintypes.HMODULE
        GMH.argtypes = [ctypes.wintypes.LPCWSTR]
        handle = GMH('bcrypt.dll')
        if not handle:
            return None

        bc = ctypes.WinDLL('bcrypt.dll', handle=handle)
        P = ctypes.POINTER
        vp, ul, cp = ctypes.c_void_p, ctypes.c_ulong, ctypes.c_char_p

        bc.BCryptOpenAlgorithmProvider.argtypes = [P(vp), ctypes.c_wchar_p, ctypes.c_wchar_p, ul]
        bc.BCryptGenerateSymmetricKey.argtypes  = [vp, P(vp), vp, ul, cp, ul, ul]
        bc.BCryptEncrypt.argtypes               = [vp, cp, ul, vp, vp, ul, cp, ul, P(ul), ul]
        bc.BCryptDestroyKey.argtypes            = [vp]
        bc.BCryptGetProperty.argtypes           = [vp, ctypes.c_wchar_p, vp, ul, P(ul), ul]

        alg = vp()
        if bc.BCryptOpenAlgorithmProvider(ctypes.byref(alg), 'RC4', None, 0) != 0:
            return None

        kos = ul()
        bc.BCryptGetProperty(alg, 'ObjectLength', ctypes.byref(kos), 4, ctypes.byref(ul()), 0)

        key_obj = ctypes.create_string_buffer(kos.value)
        hkey = vp()
        hkey_ref = ctypes.byref(hkey)
        outbuf = ctypes.create_string_buffer(8192)
        rlen = ul()
        rlen_ref = ctypes.byref(rlen)
        gen, enc, destroy = bc.BCryptGenerateSymmetricKey, bc.BCryptEncrypt, bc.BCryptDestroyKey

        def rc4(key: bytes, data: bytes) -> bytes:
            n = len(data)
            gen(alg, hkey_ref, key_obj, kos.value, key, len(key), 0)
            enc(hkey, data, n, None, None, 0, outbuf, n, rlen_ref, 0)
            destroy(hkey)
            return outbuf.raw[:rlen.value]

        return rc4
    except Exception:
        return None


_rc4_decrypt = _rc4_cng() or _rc4_python


# ─── Threaded decode helper ───────────────────────────────────────────

def _decode_and_cache(raw: bytes) -> None:
    """Unpack, parse, decode, postprocess in background thread, cache result."""
    try:
        n = len(raw) & ~1
        cp = struct.unpack_from(f'<{n >> 1}H', raw)
        try:
            cp = cp[:cp.index(0)]
        except ValueError:
            pass
        idx, key = _parse_codepoints(cp)
        if idx == 0:
            return
        entry = _string_table.get(idx)
        if entry is None:
            return
        text = _decode_entry(entry, key)
        if text:
            text = _postprocess(text)
            _decode_cache[raw] = text
    finally:
        _pending.discard(raw)


# ─── Public decode API ────────────────────────────────────────────────

_PLAYER_PREFIX = b'\xa9\x0b'  # 0xBA9 as little-endian uint16


def decode(raw: bytes) -> str:
    """Decode raw encoded-name bytes to a display string.

    Accepts the raw wchar_t bytes from GetAgentEncName (little-endian uint16
    with null terminator). Handles player names, cache, and async decode.
    """
    if len(raw) < 4:
        return ""

    # Player names: prefix 0xBA9, inline ASCII
    if raw[0:2] == _PLAYER_PREFIX:
        chars: list[int] = []
        for i in range(4, len(raw) - 1, 2):
            lo = raw[i]
            hi = raw[i + 1]
            if lo <= 1 and hi == 0:
                break
            chars.append(lo)
        return bytes(chars).decode('ascii', 'ignore')

    # Cache hit
    cached = _decode_cache.get(raw)
    if cached is not None:
        return cached

    # Kick off string table load if needed
    if not _string_table_loaded and not _load_enqueued:
        load_string_table(_get_client_language())

    if not _string_table or raw in _pending:
        return ""

    # Submit decode to background thread — return "" now, cache hit next frame
    _pending.add(raw)
    _decode_pool.submit(_decode_and_cache, raw)
    return ""

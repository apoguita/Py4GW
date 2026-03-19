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

from Py4GWCoreLib.native_src.context.TextContext import TextParser
from Py4GWCoreLib.native_src.internals.helpers import read_wstr
from Py4GWCoreLib.native_src.methods.DatFileMethods import read_dat_file_by_hash


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
_loaded_language: int = 0
_string_tables_by_language: dict[int, dict[int, bytes]] = {}

_decode_cache: dict[bytes, str] = {}
_decode_cache_by_language: dict[tuple[int, bytes], str] = {}
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
_INLINE_STYLE_TAG_RE = re.compile(r'\[(?:/?[bB])\]')
_INLINE_GENDER_TAG_RE = re.compile(r'\[(f|m):"([^"]*)"\]')
_INLINE_GENDER_PAIR_RE = re.compile(r'\[(m|f):"([^"]*)"\]\[(m|f):"([^"]*)"\]')
_INDEFINITE_ARTICLE_RE = re.compile(r'\[(?:a|an)\](\s+)([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\'-]*)')
_COLOR_TAG_RE = re.compile(r"<c=@[^>]+>(.*?)</c>")


def _apply_inline_gender_tags(text: str, prefer_male: bool = True) -> str:
    def _replace_pair(match: re.Match[str]) -> str:
        first_tag, first_value, second_tag, second_value = match.groups()
        preferred_tag = "m" if prefer_male else "f"
        if first_tag == preferred_tag:
            return first_value
        if second_tag == preferred_tag:
            return second_value
        return first_value or second_value

    def _replace_single(match: re.Match[str]) -> str:
        tag, value = match.groups()
        preferred_tag = "m" if prefer_male else "f"
        return value if tag == preferred_tag else ""

    text = _INLINE_GENDER_PAIR_RE.sub(_replace_pair, text)
    return _INLINE_GENDER_TAG_RE.sub(_replace_single, text)


def _postprocess_basic(text: str) -> str:
    text = _GRAMMAR_TAG_RE.sub('', text)
    text = _INLINE_STYLE_TAG_RE.sub('', text)
    text = _apply_inline_gender_tags(text, prefer_male=True)
    for old, new in _BRACKET_SUBS.items():
        if old in text:
            text = text.replace(old, new)
    return text


def _choose_indefinite_article(word: str) -> str:
    lower = word.lower()
    if lower.startswith(("honest", "honor", "hour", "heir")):
        return "an"
    if lower.startswith(("uni", "use", "user", "euro", "one", "once")):
        return "a"
    return "an" if lower[:1] in {"a", "e", "i", "o", "u"} else "a"


def _apply_indefinite_articles(text: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        spacing = match.group(1)
        word = match.group(2)
        return f"{_choose_indefinite_article(word)}{spacing}{word}"

    return _INDEFINITE_ARTICLE_RE.sub(_replace, text)


def _postprocess(text: str, table: Optional[dict[int, bytes]] = None) -> str:
    text = _postprocess_basic(text)
    if "%str" in text:
        text = _apply_substitutions(text, table)
    if "[an]" in text or "[a]" in text:
        text = _apply_indefinite_articles(text)
    if "%%" in text:
        text = text.replace("%%", "%")
    return text


def _get_substitute_text(slot: int, table: Optional[dict[int, bytes]] = None) -> str:
    """Resolve TextParser substitute_1/substitute_2 to display text."""
    tp = TextParser.get_context()
    if tp is None:
        return ""

    sub = tp.substitute_1 if slot == 1 else tp.substitute_2
    if not sub:
        return ""

    # Most common path in our custom decoder: substitute is another string-table index.
    source_table = table if table is not None else _string_table
    entry = source_table.get(sub)
    if entry is not None:
        text = _decode_entry(entry, 0)
        if text:
            return _postprocess_basic(text)

    # Fallback: game may store a direct wchar pointer in substitute fields.
    if sub >= 0x10000:
        try:
            return read_wstr(sub) or ""
        except Exception:
            return ""
    return ""


def _apply_substitutions(text: str, table: Optional[dict[int, bytes]] = None) -> str:
    if "%str1%" in text:
        sub1 = _get_substitute_text(1, table)
        if sub1:
            text = text.replace("%str1%", sub1)
    if "%str2%" in text:
        sub2 = _get_substitute_text(2, table)
        if sub2:
            text = text.replace("%str2%", sub2)
    return text


# ─── Inline formatted encoded-string parser (0x0101/0x010A/...) ──────────

_NUM_TAG_BASE = 0x0101
_NUM_TAG_MAX = 0x0109
_STR_TAG_BASE = 0x010A
_STR_TAG_MAX = 0x011F


def _is_arg_tag(cp: int) -> bool:
    return (_NUM_TAG_BASE <= cp <= _NUM_TAG_MAX) or (_STR_TAG_BASE <= cp <= _STR_TAG_MAX)


def _is_num_tag(cp: int) -> bool:
    return _NUM_TAG_BASE <= cp <= _NUM_TAG_MAX


def _is_str_tag(cp: int) -> bool:
    return _STR_TAG_BASE <= cp <= _STR_TAG_MAX


def _decode_codepoints_segment(segment: tuple[int, ...], table: Optional[dict[int, bytes]] = None) -> str:
    """Decode one codepoint segment (no inline arg tags inside)."""
    if not segment:
        return ""
    idx, key = _parse_codepoints(segment)
    if idx == 0:
        return ""
    source_table = table if table is not None else _string_table
    entry = source_table.get(idx)
    if entry is None:
        return ""
    text = _decode_entry(entry, key)
    if not text:
        return ""
    return _postprocess_basic(text)


def _parse_number_codepoints(codepoints: tuple[int, ...], start: int) -> tuple[int, int]:
    """Parse one inline numeric argument encoded with base-0x7F00 digits."""
    n = len(codepoints)
    i = start
    value = 0
    parsed_any = False

    while i < n:
        cp = codepoints[i]
        if cp == 0 or cp == 1 or cp == 2:
            break
        digit = (cp & 0x7FFF) - _BASE
        if digit < 0:
            break
        parsed_any = True
        if cp & _MORE:
            value = (value + digit) * _RANGE
        else:
            value = value + digit
            i += 1
            break
        i += 1

    if not parsed_any:
        return 0, i

    if i < n and codepoints[i] == 1:
        i += 1

    return value, i


_PL_TAG_RE = re.compile(r'([^\s\[\]]+)\[pl:"([^"]*)"\]')
# Optional suffix plural marker attached to a word, e.g. Cacho[s], Robe[s]
_PL_SUFFIX_RE = re.compile(r'([A-Za-zÀ-ÖØ-öø-ÿ]+)\[([A-Za-zÀ-ÖØ-öø-ÿ]{1,3})\]')


def _has_plural_markers(text: str) -> bool:
    return ('[pl:"' in text) or bool(_PL_SUFFIX_RE.search(text))


def _apply_plural_tags(text: str, num_value: Optional[int]) -> str:
    if '[' not in text:
        return text
    use_plural = (num_value is not None and num_value != 1)
    text = _PL_TAG_RE.sub(lambda m: m.group(2) if use_plural else m.group(1), text)
    # Supports localized optional suffix markers like: Cacho[s]
    text = _PL_SUFFIX_RE.sub(lambda m: (m.group(1) + m.group(2)) if use_plural else m.group(1), text)
    return text


_NUM_PLACEHOLDER_RE = re.compile(r'%num\d+%')


def _normalize_plain_text(text: str) -> str:
    text = _apply_inline_gender_tags(text, prefer_male=True)
    text = _apply_plural_tags(text, 1)
    text = _NUM_PLACEHOLDER_RE.sub('', text)
    text = _COLOR_TAG_RE.sub(r"\1", text)
    return re.sub(r'\s{2,}', ' ', text).strip()


def _best_arg_text(node: dict) -> str:
    """Pick the best resolved text from a node, descending through wrappers."""
    txt = (node.get("rendered") or "").strip()
    if txt and not re.search(r"%str\d+%", txt):
        return txt
    for k in sorted((node.get("args") or {}).keys()):
        child_txt = _best_arg_text(node["args"][k])
        if child_txt:
            return child_txt
    return ""


def _consume_encoded_ref(codepoints: tuple[int, ...], start: int) -> int:
    """Consume one encoded string reference (index + optional key) and return end pos."""
    n = len(codepoints)
    i = start
    if i >= n:
        return i
    if codepoints[i] in (0, 1, 2):
        return i

    parsed_any = False
    while i < n:
        cp = codepoints[i]
        if cp in (0, 1, 2):
            break
        digit = (cp & 0x7FFF) - _BASE
        if digit < 0:
            break
        parsed_any = True
        i += 1
        if not (cp & _MORE):
            break

    if not parsed_any:
        return start

    # Optional key stream starts only when next codepoint has MORE set.
    if i < n and codepoints[i] not in (0, 1, 2) and (codepoints[i] & _MORE):
        while i < n:
            cp = codepoints[i]
            if cp in (0, 1, 2):
                break
            digit = (cp & 0x7FFF) - _BASE
            if digit < 0:
                break
            i += 1
            if not (cp & _MORE):
                break

    return i


def _parse_arg_blocks(codepoints: tuple[int, ...], i: int, table: Optional[dict[int, bytes]] = None) -> tuple[dict[int, dict], dict[int, int], int]:
    """Parse 0x0101..0x011F arg blocks starting at i."""
    n = len(codepoints)
    args: dict[int, dict] = {}
    num_args: dict[int, int] = {}

    while i < n and _is_arg_tag(codepoints[i]):
        tag = codepoints[i]
        if _is_num_tag(tag):
            slot = tag - 0x0100
            value, i = _parse_number_codepoints(codepoints, i + 1)
            num_args[slot] = value
        else:
            slot = tag - 0x0109
            arg_node, i = _decode_formatted_tree(codepoints, i + 1, table)
            args[slot] = arg_node

    return args, num_args, i


def _decode_formatted_tree(codepoints: tuple[int, ...], start: int = 0, table: Optional[dict[int, bytes]] = None) -> tuple[dict, int]:
    """Decode one formatted expression and return ({template, rendered, args}, next_pos)."""
    n = len(codepoints)
    i = start

    # Head segment: encoded string ref until arg-tag/terminator.
    head_start = i
    while i < n:
        cp = codepoints[i]
        if cp == 0 or cp == 1 or cp == 2 or _is_arg_tag(cp):
            break
        i += 1

    template = _decode_codepoints_segment(codepoints[head_start:i], table) if i > head_start else ""
    rendered = template
    args: dict[int, dict] = {}
    num_args: dict[int, int] = {}

    # Parse arg blocks: 0x0101 => num1, 0x010A => str1, ...
    if i < n and _is_arg_tag(codepoints[i]):
        args, num_args, i = _parse_arg_blocks(codepoints, i, table)

        # Ambiguous case: first token looked like num-tag but was actually a
        # string-ref digit (e.g. 0x0108), leaving unresolved tail data.
        if (
            not template
            and not args
            and bool(num_args)
            and _is_num_tag(codepoints[start])
            and i < n
            and codepoints[i] not in (0, 1, 2)
            and not _is_arg_tag(codepoints[i])
        ):
            alt_end = _consume_encoded_ref(codepoints, start)
            if alt_end > start:
                alt_template = _decode_codepoints_segment(codepoints[start:alt_end], table)
                if alt_template:
                    template = alt_template
                    rendered = template
                    args, num_args, i = _parse_arg_blocks(codepoints, alt_end)

        for slot, arg_node in args.items():
            arg_text = arg_node.get("rendered", "")
            if arg_text and rendered:
                rendered = rendered.replace(f"%str{slot}%", arg_text)
        # Second pass: if wrappers left unresolved "%strN%", use deepest resolved child text.
        for slot, arg_node in args.items():
            marker = f"%str{slot}%"
            if marker in rendered:
                arg_text = _best_arg_text(arg_node)
                if arg_text:
                    rendered = rendered.replace(marker, arg_text)
        has_plural_markers = _has_plural_markers(rendered)
        for slot, value in num_args.items():
            if slot == 1 and value == 1 and has_plural_markers:
                rendered = rendered.replace(f"%num{slot}%", "")
            else:
                rendered = rendered.replace(f"%num{slot}%", str(value))
        rendered = _apply_plural_tags(rendered, num_args.get(1))
        rendered = re.sub(r'\s{2,}', ' ', rendered).strip()

        # Some payloads are wrapper nodes with only control tags and nested args.
        # Forward first non-empty child so outer %strN% can still resolve.
        if not rendered and args:
            child = args.get(1)
            if child is None or not child.get("rendered", ""):
                for k in sorted(args.keys()):
                    if args[k].get("rendered", ""):
                        child = args[k]
                        break
            if child is not None:
                rendered = child.get("rendered", "")

    # Consume expression terminator (0x0001) if present.
    if i < n and codepoints[i] == 1:
        i += 1

    return {
        "template": template,
        "rendered": rendered,
        "args": args,
        "num_args": num_args,
        "expr_cp": codepoints[start:i],
        "head_cp": codepoints[head_start:i] if i > head_start else (),
    }, i


def _decode_formatted_stream(codepoints: tuple[int, ...], table: Optional[dict[int, bytes]] = None) -> tuple[str, Optional[dict]]:
    """Decode full formatted stream with 0x0002 segment separators."""
    out: list[str] = []
    first_tree: Optional[dict] = None
    i = 0
    n = len(codepoints)

    while i < n:
        cp = codepoints[i]
        if cp == 0:
            break
        if cp == 1:
            i += 1
            continue
        if cp == 2:
            i += 1
            continue

        tree, ni = _decode_formatted_tree(codepoints, i, table)
        if ni <= i:
            i += 1
            continue
        txt = tree.get("rendered", "").strip()
        if txt:
            out.append(txt)
            if first_tree is None:
                first_tree = tree
        i = ni

    # Compact unresolved "%strN%" wrapper lines by consuming the next plain line.
    compact: list[str] = []
    i = 0
    while i < len(out):
        cur = out[i]
        cur_lstripped = cur.lstrip()
        if re.search(r'%str\d+%', cur) and (i + 1) < len(out):
            nxt = out[i + 1]
            if nxt and not nxt.startswith("<c=@"):
                cur = re.sub(r'%str\d+%', nxt, cur)
                i += 1
                cur_lstripped = cur.lstrip()
        # Parenthetical dull segments belong to the previous stat line.
        if compact and cur.startswith("<c=@ItemDull>("):
            compact[-1] = f"{compact[-1]} {cur}"
        # Plain continuation fragments like ", ..." also belong to the previous line.
        elif compact and not cur_lstripped.startswith("<c=@") and cur_lstripped[:1] in {",", ";", ":", ")", "]"}:
            if "<c=@ItemDull>" in compact[-1] and compact[-1].endswith("</c>"):
                compact[-1] = f"{compact[-1][:-4]}{cur_lstripped}</c>"
            else:
                compact[-1] = f"{compact[-1]}{cur_lstripped}"
        elif compact and not cur_lstripped.startswith("<c=@"):
            prev = compact[-1]
            if "<c=@ItemDull>" in prev and prev.endswith(",</c>"):
                if prev.endswith("),</c>"):
                    compact[-1] = f"{prev[:-6]}, {cur_lstripped})</c>"
                else:
                    compact[-1] = f"{prev[:-4]} {cur_lstripped}</c>"
            else:
                compact.append(cur)
        else:
            compact.append(cur)
        i += 1

    return ('\n'.join(compact).strip(), first_tree)


def _decode_formatted_codepoints(codepoints: tuple[int, ...], start: int = 0, table: Optional[dict[int, bytes]] = None) -> tuple[str, int]:
    node, i = _decode_formatted_tree(codepoints, start, table)
    return node.get("rendered", ""), i


# ─── Loading ─────────────────────────────────────────────────────────────

def _load_dat_file(file_hash: str) -> Optional[bytes]:
    """Load a single dat file by its hash string. Must run on game thread."""
    return read_dat_file_by_hash(file_hash)


def _parse_string_file(file_data: bytes, start_index: int, target_table: Optional[dict[int, bytes]] = None) -> int:
    """Parse all entries from a string file into _string_table. Returns count."""
    table = target_table if target_table is not None else _string_table
    count = 0
    pos = 0
    idx = start_index
    while pos < len(file_data) - 2:
        entry_size = struct.unpack_from('<H', file_data, pos)[0]
        if entry_size < 6 or entry_size > 8192:
            break
        table[idx] = file_data[pos:pos + entry_size]
        pos += entry_size
        idx += 1
        count += 1
    return count


def _load_table_for_language(language: int) -> dict[int, bytes]:
    existing = _string_tables_by_language.get(language)
    if existing is not None:
        return existing

    tp = TextParser.get_context()
    if tp is None:
        return {}

    epf = tp.entries_per_file
    if not epf:
        return {}

    lang_slot = tp.language_slots[language]
    table: dict[int, bytes] = {}

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
        _parse_string_file(file_data, slot_idx * epf, table)

    if table:
        _string_tables_by_language[language] = table

    return table


def _do_load_string_table(language: int) -> None:
    """Synchronous load — must run on the game thread.

    Reads file slot metadata from TextParser, loads each dat file via
    DatFileMethods, and parses all entries into _string_table.
    Caller must ensure TextParser context is fresh (e.g. _update_ptr ran).
    """
    global _string_table_loaded, _loaded_language
    if _string_table_loaded and _loaded_language == language:
        return
    table = _load_table_for_language(language)
    if not table:
        return

    _string_table.clear()
    _string_table.update(table)
    _string_table_loaded = True
    _loaded_language = language


def load_string_table(language: int = 0) -> None:
    """Enqueue string table load on the game thread.

    Safe to call from any context. The actual load runs on the next
    game frame via Game.enqueue. After completion, _string_table_loaded
    is True and decode functions return results.
    """
    global _load_enqueued, _loaded_language
    if _string_table_loaded or _load_enqueued:
        return
    _load_enqueued = True
    _loaded_language = language

    import Py4GW
    Py4GW.Game.enqueue(lambda: _do_load_string_table(language))


def _get_client_language() -> int:
    """Read the client's text language from TextParser context."""
    tp = TextParser.get_context()
    if tp is None:
        return 0
    return tp.language_id

def switch_language(language: int) -> None:
    global _string_table, _decode_cache, _decode_cache_by_language, _string_table_loaded, _load_enqueued, _loaded_language
    _decode_cache.clear()
    _decode_cache_by_language.clear()
    _string_table_loaded = False
    _load_enqueued = False
    _loaded_language = language
    load_string_table(language)

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

def _decode_sync(raw: bytes, table: dict[int, bytes]) -> str:
    n = len(raw) & ~1
    if n < 2:
        return ""

    cp = struct.unpack_from(f'<{n >> 1}H', raw)
    try:
        cp = cp[:cp.index(0)]
    except ValueError:
        pass
    if not cp:
        return ""

    idx, key = _parse_codepoints(cp)
    legacy_text = ""
    if idx != 0:
        entry = table.get(idx)
        if entry is not None:
            t = _decode_entry(entry, key)
            if t:
                legacy_text = _postprocess(t, table)

    has_arg_tags = any(_is_arg_tag(v) for v in cp)
    has_term = any(v == 1 for v in cp)
    has_sep = any(v == 2 for v in cp)
    looks_formatted = has_arg_tags and (has_term or has_sep)
    unresolved = bool(re.search(r'%str\d+%|%num\d+%|\[pl:"', legacy_text))

    if looks_formatted or unresolved:
        if has_sep:
            text, _ = _decode_formatted_stream(cp, table)
            if text:
                return _postprocess(text, table)
        else:
            tree, _ = _decode_formatted_tree(cp, 0, table)
            text = tree.get("rendered", "")
            if text:
                return _postprocess(text, table)

    return legacy_text


def _decode_and_cache(raw: bytes) -> None:
    """Unpack, parse, decode, postprocess in background thread, cache result."""
    try:
        decoded = _decode_sync(raw, _string_table)
        if decoded:
            _decode_cache[raw] = decoded
    finally:
        _pending.discard(raw)


# ─── Public decode API ────────────────────────────────────────────────

_PLAYER_PREFIX = b'\xa9\x0b'  # 0xBA9 as little-endian uint16


def decode(raw: bytes, language: Optional[int] = None) -> str:
    """Decode raw encoded-name bytes to a display string.

    Accepts the raw wchar_t bytes from GetAgentEncName (little-endian uint16
    with null terminator). Handles player names, cache, and async decode.
    """
    if len(raw) < 2:
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

    requested_language = _loaded_language if language is None else int(language)
    if language is not None and requested_language != _loaded_language:
        cache_key = (requested_language, raw)
        cached = _decode_cache_by_language.get(cache_key)
        if cached is not None:
            return cached

        table = _load_table_for_language(requested_language)
        if not table:
            return ""

        decoded = _decode_sync(raw, table)
        if decoded:
            _decode_cache_by_language[cache_key] = decoded
        return decoded

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


def decode_plain(raw: bytes, language: Optional[int] = None) -> str:
    text = decode(raw, language=language)
    if not text:
        return ""

    return _normalize_plain_text(text)

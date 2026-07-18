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
from typing import NamedTuple, Optional

from Py4GWCoreLib.native_src.context.TextContext import TextParser
from Py4GWCoreLib.native_src.internals.helpers import read_wstr
from Py4GWCoreLib.native_src.methods.DatFileMethods import read_dat_file_by_hash


class ItemNameParts(NamedTuple):
    markdown: Optional[str]
    prefix: Optional[str]
    item_name: Optional[str]
    suffix: Optional[str]
    num: Optional[int]
    singular_form: Optional[str] = None
    plural_form: Optional[str] = None

    @property
    def singular(self) -> Optional[str]:
        return self.singular_form if self.singular_form is not None else self.item_name

    @property
    def plural(self) -> Optional[str]:
        if self.plural_form is not None:
            return self.plural_form
        return self.item_name
    


class ItemNamePartsEncoded(NamedTuple):
    markdown: Optional[bytes]
    prefix: Optional[bytes]
    item_name: Optional[bytes]
    suffix: Optional[bytes]
    num: Optional[int]
    singular_form: Optional[bytes] = None
    plural_form: Optional[bytes] = None

    @property
    def singular(self) -> Optional[bytes]:
        return self.singular_form if self.singular_form is not None else self.item_name

    @property
    def plural(self) -> Optional[bytes]:
        return self.plural_form if self.plural_form is not None else self.item_name


class DecodedSubstring(NamedTuple):
    encoded: bytes
    decoded: str


class DecodedStringInspection(NamedTuple):
    encoded: bytes
    decoded: str
    substrings: tuple[DecodedSubstring, ...]


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
_INLINE_STYLE_TAG_RE = re.compile(r'\[(?:/?[bB])\]')


def _postprocess_basic(text: str) -> str:
    text = _GRAMMAR_TAG_RE.sub('', text)
    text = _INLINE_STYLE_TAG_RE.sub('', text)
    for old, new in _BRACKET_SUBS.items():
        if old in text:
            text = text.replace(old, new)
    return text


def _postprocess(text: str) -> str:
    text = _postprocess_basic(text)
    if "%str" in text:
        text = _apply_substitutions(text)
    return text


def _get_substitute_text(slot: int) -> str:
    """Resolve TextParser substitute_1/substitute_2 to display text."""
    tp = TextParser.get_context()
    if tp is None:
        return ""

    sub = tp.substitute_1 if slot == 1 else tp.substitute_2
    if not sub:
        return ""

    # Most common path in our custom decoder: substitute is another string-table index.
    entry = _string_table.get(sub)
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


def _apply_substitutions(text: str) -> str:
    if "%str1%" in text:
        sub1 = _get_substitute_text(1)
        if sub1:
            text = text.replace("%str1%", sub1)
    if "%str2%" in text:
        sub2 = _get_substitute_text(2)
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


def _decode_codepoints_segment(segment: tuple[int, ...]) -> str:
    """Decode one codepoint segment (no inline arg tags inside)."""
    if not segment:
        return ""
    idx, key = _parse_codepoints(segment)
    if idx == 0:
        return ""
    entry = _string_table.get(idx)
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

    while i < n:
        cp = codepoints[i]
        if cp == 0 or cp == 1 or _is_arg_tag(cp):
            break
        digit = (cp & 0x7FFF) - _BASE
        if digit < 0:
            break
        if cp & _MORE:
            value = (value + digit) * _RANGE
        else:
            value = value + digit
            i += 1
            break
        i += 1

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


def _parse_arg_blocks(codepoints: tuple[int, ...], i: int) -> tuple[dict[int, dict], dict[int, int], int]:
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
            arg_node, i = _decode_formatted_tree(codepoints, i + 1)
            args[slot] = arg_node

    return args, num_args, i


def _decode_formatted_tree(codepoints: tuple[int, ...], start: int = 0) -> tuple[dict, int]:
    """Decode one formatted expression and return ({template, rendered, args}, next_pos)."""
    n = len(codepoints)
    i = start

    # Head segment: encoded string ref until arg-tag/terminator.
    head_start = i
    while i < n:
        cp = codepoints[i]
        if cp == 0 or cp == 1 or _is_arg_tag(cp):
            break
        i += 1

    template = _decode_codepoints_segment(codepoints[head_start:i]) if i > head_start else ""
    rendered = template
    args: dict[int, dict] = {}
    num_args: dict[int, int] = {}

    # Parse arg blocks: 0x0101 => num1, 0x010A => str1, ...
    if i < n and _is_arg_tag(codepoints[i]):
        args, num_args, i = _parse_arg_blocks(codepoints, i)

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
                alt_template = _decode_codepoints_segment(codepoints[start:alt_end])
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


def _decode_formatted_codepoints(codepoints: tuple[int, ...], start: int = 0) -> tuple[str, int]:
    node, i = _decode_formatted_tree(codepoints, start)
    return node.get("rendered", ""), i


def _decode_formatted_stream_nodes(codepoints: tuple[int, ...]) -> tuple[str, list[dict]]:
    """Decode full formatted stream and return text plus all top-level trees."""
    out: list[str] = []
    trees: list[dict] = []
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

        tree, ni = _decode_formatted_tree(codepoints, i)
        if ni <= i:
            i += 1
            continue
        txt = tree.get("rendered", "").strip()
        if txt:
            out.append(txt)
            trees.append(tree)
        i = ni

    compact: list[str] = []
    i = 0
    while i < len(out):
        cur = out[i]
        if re.search(r'%str\d+%', cur) and (i + 1) < len(out):
            nxt = out[i + 1]
            if nxt and not nxt.startswith("<c=@"):
                cur = re.sub(r'%str\d+%', nxt, cur)
                i += 1
        compact.append(cur)
        i += 1

    return ('\n'.join(compact).strip(), trees)


def _walk_decoded_substrings(node: dict, out: list[DecodedSubstring], seen: set[tuple[bytes, str]]) -> None:
    encoded = _codepoints_to_raw(node.get("expr_cp") or ())
    decoded = (node.get("rendered") or "").strip()
    if encoded and decoded:
        key = (encoded, decoded)
        if key not in seen:
            seen.add(key)
            out.append(DecodedSubstring(encoded, decoded))

    for child in (node.get("args") or {}).values():
        _walk_decoded_substrings(child, out, seen)


def inspect_decoded(raw: bytes) -> DecodedStringInspection:
    """Return the full decoded string and every decoded subtree with its raw bytes."""
    full = decode(raw)

    if len(raw) < 2:
        return DecodedStringInspection(raw, full, ())

    if raw[0:2] == _PLAYER_PREFIX:
        text = full or bytes(raw[4::2]).decode('ascii', 'ignore')
        substrings = [DecodedSubstring(raw, text)] if text else []
        return DecodedStringInspection(raw, full, tuple(substrings))

    n = len(raw) & ~1
    if n < 2:
        return DecodedStringInspection(raw, full, ())

    cp = struct.unpack_from(f'<{n >> 1}H', raw)
    try:
        cp = cp[:cp.index(0)]
    except ValueError:
        pass
    if not cp:
        return DecodedStringInspection(raw, full, ())

    idx, key = _parse_codepoints(cp)
    has_arg_tags = any(_is_arg_tag(v) for v in cp)
    has_term = any(v == 1 for v in cp)
    has_sep = any(v == 2 for v in cp)

    if not has_arg_tags or not has_term:
        if idx != 0:
            return DecodedStringInspection(raw, full, (DecodedSubstring(raw, full),) if full else ())
        return DecodedStringInspection(raw, full, ())

    seen: set[tuple[bytes, str]] = set()
    substrings: list[DecodedSubstring] = []

    if has_sep:
        _, trees = _decode_formatted_stream_nodes(cp)
        for tree in trees:
            _walk_decoded_substrings(tree, substrings, seen)
    else:
        tree, _ = _decode_formatted_tree(cp, 0)
        _walk_decoded_substrings(tree, substrings, seen)

    if full and (raw, full) not in seen:
        substrings.insert(0, DecodedSubstring(raw, full))

    return DecodedStringInspection(raw, full, tuple(substrings))


def _find_num_arg(tree: dict, slot: int = 1) -> Optional[int]:
    nums = tree.get("num_args") or {}
    if slot in nums:
        return nums[slot]
    for child in (tree.get("args") or {}).values():
        v = _find_num_arg(child, slot)
        if v is not None:
            return v
    return None


def _render_item_node(node: dict, num_override: Optional[int] = None, include_num: bool = False) -> str:
    text = node.get("template") or node.get("rendered") or ""
    if not text:
        return ""

    for slot, child in (node.get("args") or {}).items():
        child_text = child.get("rendered", "")
        if child_text:
            text = text.replace(f"%str{slot}%", child_text)
    # Wrapper fallback: if placeholder remains, use deepest resolved child text.
    for slot, child in (node.get("args") or {}).items():
        marker = f"%str{slot}%"
        if marker in text:
            child_text = _best_arg_text(child)
            if child_text:
                text = text.replace(marker, child_text)

    nums = node.get("num_args") or {}
    num1 = num_override if num_override is not None else nums.get(1)
    has_plural_markers = _has_plural_markers(text)
    if "%num1%" in text:
        if include_num and num1 is not None and not (num1 == 1 and has_plural_markers):
            text = text.replace("%num1%", str(num1))
        else:
            text = text.replace("%num1%", "")

    for slot, value in nums.items():
        if slot == 1:
            continue
        text = text.replace(f"%num{slot}%", str(value))

    text = _apply_plural_tags(text, num1)
    return re.sub(r'\s{2,}', ' ', text).strip()


def _unwrap_placeholder_item_node(node: dict) -> dict:
    """Descend through single-child placeholder wrappers like '%str1%'."""
    cur = node
    for _ in range(6):
        tpl = (cur.get("template") or "").strip()
        args = cur.get("args") or {}
        if len(args) != 1:
            break
        if not tpl or re.fullmatch(r"%str\d+%", tpl):
            only_key = next(iter(args.keys()))
            child = args.get(only_key)
            if isinstance(child, dict):
                cur = child
                continue
        break
    return cur


def _select_item_name_node(tree: dict) -> Optional[dict]:
    args = tree.get("args") or {}
    str1 = args.get(1)
    if not str1:
        return None
    str1 = _unwrap_placeholder_item_node(str1)
    tpl = str1.get("template") or ""
    if "%num" in tpl or _has_plural_markers(tpl):
        return str1
    str1_args = str1.get("args") or {}
    if 1 in str1_args:
        return _unwrap_placeholder_item_node(str1_args[1])
    return str1


def _extract_item_name_forms_from_tree(tree: dict) -> tuple[Optional[str], Optional[str]]:
    node = _select_item_name_node(tree)
    if node is None:
        base = tree.get("rendered") or None
        return (base, base)
    singular = _render_item_node(node, num_override=1, include_num=False) or None
    plural = _render_item_node(node, num_override=2, include_num=False) or singular
    return (singular, plural)


def _codepoints_to_raw(codepoints: tuple[int, ...]) -> Optional[bytes]:
    if not codepoints:
        return None
    return struct.pack(f'<{len(codepoints)}H', *codepoints)


def _assign_prefix_suffix_by_language(
    before_item: list[tuple[object, int]],
    after_item: list[tuple[object, int]],
    unknown: list[object],
) -> tuple[Optional[object], Optional[object]]:
    """Assign prefix/suffix from candidates using client-language order."""
    lang = _loaded_language if _string_table_loaded else _get_client_language()
    order = ItemName._PART_ORDER_BY_LANG.get(lang, ("prefix", "item", "suffix"))
    p_idx = order.index("prefix")
    s_idx = order.index("suffix")

    p_side = "before" if p_idx < order.index("item") else "after"
    s_side = "before" if s_idx < order.index("item") else "after"

    before_item = sorted(before_item, key=lambda x: x[1])  # left -> right
    after_item = sorted(after_item, key=lambda x: x[1])    # left -> right

    prefix: Optional[object] = None
    suffix: Optional[object] = None

    def _pick_from_side(side: str) -> list[tuple[object, int]]:
        return before_item if side == "before" else after_item

    p_candidates = _pick_from_side(p_side)
    s_candidates = _pick_from_side(s_side)

    if p_side == s_side:
        side_candidates = list(p_candidates)
        if len(side_candidates) == 1:
            # Ambiguous single extra part: map by language order proximity to item.
            if p_idx < s_idx:
                prefix = side_candidates[0][0]
            else:
                suffix = side_candidates[0][0]
        elif len(side_candidates) >= 2:
            first = side_candidates[0][0]
            second = side_candidates[1][0]
            if p_idx < s_idx:
                prefix, suffix = first, second
            else:
                suffix, prefix = first, second
    else:
        if p_candidates:
            prefix = p_candidates[0][0]
        if s_candidates:
            suffix = s_candidates[0][0]

    for u in unknown:
        if prefix is None:
            prefix = u
        elif suffix is None:
            suffix = u

    return prefix, suffix


def _extract_parts_from_tree(tree: dict) -> ItemNameParts:
    """Return (markdown, prefix, item_name, suffix, num)."""
    markdown = tree.get("template") or None
    prefix: Optional[str] = None
    item_name: Optional[str] = None
    suffix: Optional[str] = None
    num = _find_num_arg(tree, 1)

    args = tree.get("args") or {}
    str1 = args.get(1)

    if str1:
        str1_args = str1.get("args") or {}
        if str1_args:
            item_node = _select_item_name_node(tree)
            if item_node is not None:
                item_name = _render_item_node(item_node, num_override=num, include_num=False) or None
            else:
                item_name = str1_args.get(1, {}).get("rendered") or None
            tpl = str1.get("template") or ""
            item_pos = tpl.find("%str1%") if tpl else -1

            def _slot_info(slot: int, raw: str) -> tuple[str, bool, int, str, str]:
                if not tpl:
                    return raw, False, -1, "", ""
                marker = f"%str{slot}%"
                pos = tpl.find(marker)
                if pos < 0:
                    return raw, False, -1, "", ""

                # Language-agnostic: placeholders after %str1% are suffix-side;
                # keep localized literal context around this slot.
                is_suffix = item_pos >= 0 and pos > item_pos
                left = tpl[:pos]
                m = list(re.finditer(r'%str\d+%', left))
                context = left[m[-1].end():] if m else left
                right = tpl[pos + len(marker):]
                m2 = re.search(r'%str\d+%', right)
                right_ctx = right[:m2.start()] if m2 else right
                # Keep trailing punctuation/spaces (e.g. ')' in '(%str3%)').
                tail = right_ctx if (m2 is None and not any(ch.isalnum() for ch in right_ctx)) else ""
                text = (context + raw + tail).strip() if (context or tail) else raw
                return text, is_suffix, pos, context, tail

            after_item: list[tuple[object, int]] = []
            before_item: list[tuple[object, int]] = []
            unknown: list[object] = []
            for slot in sorted(k for k in str1_args.keys() if k != 1):
                node = str1_args.get(slot, {}) or {}
                raw = node.get("rendered") or None
                if (not raw) or re.search(r'%str\d+%', raw):
                    raw = _best_arg_text(node) or raw
                if not raw:
                    continue
                text, is_suffix, pos, context, tail = _slot_info(slot, raw)
                if item_name and text == item_name:
                    continue
                if pos >= 0 and item_pos >= 0:
                    if pos > item_pos:
                        after_item.append((text, pos))
                    else:
                        before_item.append((text, pos))
                else:
                    unknown.append(text)

            p, s = _assign_prefix_suffix_by_language(before_item, after_item, unknown)
            if prefix is None:
                prefix = p  # type: ignore[assignment]
            if suffix is None:
                suffix = s  # type: ignore[assignment]
            if not item_name:
                item_name = str1.get("rendered") or None
        else:
            item_name = str1.get("rendered") or None
    else:
        item_name = tree.get("rendered") or None
        # If there is no wrapper args, "template" is just plain text.
        markdown = None

    if markdown and "%str" not in markdown and "<c=" not in markdown:
        markdown = None

    singular, plural = _extract_item_name_forms_from_tree(tree)
    return ItemNameParts(markdown, prefix, item_name, suffix, num, singular, plural)


def _extract_parts_encoded_from_tree(tree: dict) -> ItemNamePartsEncoded:
    """Return encoded (markdown, prefix, item_name, suffix, num)."""
    markdown = _codepoints_to_raw(tree.get("head_cp") or ())
    prefix: Optional[bytes] = None
    item_name: Optional[bytes] = None
    suffix: Optional[bytes] = None
    num = _find_num_arg(tree, 1)
    singular_form: Optional[bytes] = None
    plural_form: Optional[bytes] = None

    args = tree.get("args") or {}
    str1 = args.get(1)

    if str1:
        item_node = _select_item_name_node(tree)
        if item_node is not None:
            item_name = _codepoints_to_raw(item_node.get("expr_cp") or ())
            singular_form = item_name
            plural_form = item_name
        else:
            item_name = _codepoints_to_raw(str1.get("expr_cp") or ())
            singular_form = item_name
            plural_form = item_name

        str1_args = str1.get("args") or {}
        tpl = str1.get("template") or ""
        item_pos = tpl.find("%str1%") if tpl else -1
        after_item: list[tuple[object, int]] = []
        before_item: list[tuple[object, int]] = []
        unknown: list[object] = []
        for slot in sorted(k for k in str1_args.keys() if k != 1):
            node = str1_args.get(slot)
            if not node:
                continue
            enc = _codepoints_to_raw(node.get("expr_cp") or ())
            if not enc:
                continue
            marker_pos = tpl.find(f"%str{slot}%") if tpl else -1
            if marker_pos >= 0 and item_pos >= 0:
                if marker_pos > item_pos:
                    after_item.append((enc, marker_pos))
                else:
                    before_item.append((enc, marker_pos))
            else:
                unknown.append(enc)
        p, s = _assign_prefix_suffix_by_language(before_item, after_item, unknown)
        if prefix is None:
            prefix = p  # type: ignore[assignment]
        if suffix is None:
            suffix = s  # type: ignore[assignment]
    else:
        item_name = _codepoints_to_raw(tree.get("expr_cp") or ())
        singular_form = item_name
        plural_form = item_name
        # If there is no wrapper args, this is plain text; no markdown wrapper.
        markdown = None

    return ItemNamePartsEncoded(markdown, prefix, item_name, suffix, num, singular_form, plural_form)


# ─── Loading ─────────────────────────────────────────────────────────────

def _load_dat_file(file_hash: str) -> Optional[bytes]:
    """Load a single dat file by its hash string. Must run on game thread."""
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
    global _string_table_loaded, _loaded_language
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
    global _string_table, _decode_cache, _string_table_loaded, _load_enqueued, _loaded_language
    _string_table.clear()
    _decode_cache.clear()
    ItemName._parts_cache.clear()
    ItemName._parts_encoded_cache.clear()
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

def _decode_and_cache(raw: bytes) -> None:
    """Unpack, parse, decode, postprocess in background thread, cache result."""
    try:
        n = len(raw) & ~1
        if n < 2:
            return
        cp = struct.unpack_from(f'<{n >> 1}H', raw)
        try:
            cp = cp[:cp.index(0)]
        except ValueError:
            pass
        if not cp:
            return

        # 1) Legacy path first: this keeps skills/agents/general strings stable.
        idx, key = _parse_codepoints(cp)
        legacy_text = ""
        if idx != 0:
            entry = _string_table.get(idx)
            if entry is not None:
                t = _decode_entry(entry, key)
                if t:
                    legacy_text = _postprocess(t)

        # 2) Use formatted-tree decoding only when payload looks formatted
        #    or legacy output still contains unresolved placeholders.
        has_arg_tags = any(_is_arg_tag(v) for v in cp)
        has_term = any(v == 1 for v in cp)
        looks_formatted = has_arg_tags and has_term
        unresolved = bool(re.search(r'%str\d+%|%num\d+%|\[pl:"', legacy_text))

        if looks_formatted or unresolved:
            tree, _ = _decode_formatted_tree(cp, 0)
            text = tree.get("rendered", "")
            if text:
                text = _postprocess(text)
                _decode_cache[raw] = text
                ItemName._parts_cache[raw] = _extract_parts_from_tree(tree)
                ItemName._parts_encoded_cache[raw] = _extract_parts_encoded_from_tree(tree)
                return

        if legacy_text:
            _decode_cache[raw] = legacy_text
            ItemName._parts_cache[raw] = ItemNameParts(None, None, legacy_text, None, None, legacy_text, legacy_text)
            ItemName._parts_encoded_cache[raw] = ItemNamePartsEncoded(None, None, raw, None, None, raw, raw)
    finally:
        _pending.discard(raw)


# ─── Public decode API ────────────────────────────────────────────────

_PLAYER_PREFIX = b'\xa9\x0b'  # 0xBA9 as little-endian uint16


def decode(raw: bytes) -> str:
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

    # Cache hit
    cached = _decode_cache.get(raw)
    if cached is not None:
        return cached

    # Kick off string table load if needed
    if not _string_table_loaded and not _load_enqueued:
        load_string_table(_get_client_language())

    if not _string_table_loaded or not _string_table or raw in _pending:
        return ""

    # Submit decode to background thread — return "" now, cache hit next frame
    _pending.add(raw)
    _decode_pool.submit(_decode_and_cache, raw)
    return ""

class ItemName:
    """Structured facade for item/encoded name decoding helpers."""
    _parts_cache: dict[bytes, ItemNameParts] = {}
    _parts_encoded_cache: dict[bytes, ItemNamePartsEncoded] = {}
    _PART_ORDER_BY_LANG: dict[int, tuple[str, str, str]] = {
        0: ("prefix", "item", "suffix"),   # English
        1: ("prefix", "item", "suffix"),   # Korean
        2: ("item", "prefix", "suffix"),   # French
        3: ("prefix", "item", "suffix"),   # German
        4: ("item", "suffix", "prefix"),   # Italian
        5: ("item", "prefix", "suffix"),   # Spanish
        6: ("suffix", "prefix", "item"),   # Traditional Chinese
        8: ("prefix", "item", "suffix"),   # Japanese
        9: ("item", "prefix", "suffix"),   # Polish
        10: ("prefix", "item", "suffix"),  # Russian
        17: ("prefix", "item", "suffix"),  # BorkBorkBork
    }

    decode = staticmethod(decode)
    inspect_decoded = staticmethod(inspect_decoded)
    
    @staticmethod
    def decode_parts(raw: bytes) -> ItemNameParts:
        """Decode to (markdown, prefix, item_name, suffix, num)."""
        if len(raw) < 2:
            return ItemNameParts(None, None, None, None, None)

        # Player names: plain ASCII inline data.
        if raw[0:2] == _PLAYER_PREFIX:
            chars: list[int] = []
            for i in range(4, len(raw) - 1, 2):
                lo = raw[i]
                hi = raw[i + 1]
                if lo <= 1 and hi == 0:
                    break
                chars.append(lo)
            name = bytes(chars).decode('ascii', 'ignore') or None
            return ItemNameParts(None, None, name, None, None, name, name)

        cached = ItemName._parts_cache.get(raw)
        if cached is not None:
            return cached

        # Back-compat: if full text is already cached but parts are not.
        cached_text = _decode_cache.get(raw)
        if cached_text is not None:
            return ItemNameParts(None, None, cached_text or None, None, None)

        if not _string_table_loaded and not _load_enqueued:
            load_string_table(_get_client_language())

        if not _string_table_loaded or not _string_table or raw in _pending:
            return ItemNameParts(None, None, None, None, None)

        _pending.add(raw)
        _decode_pool.submit(_decode_and_cache, raw)
        return ItemNameParts(None, None, None, None, None)

    @staticmethod
    def encoded_parts(raw: bytes) -> ItemNamePartsEncoded:
        """Decode to encoded parts: (markdown, prefix, item_name, suffix, num)."""
        if len(raw) < 2:
            return ItemNamePartsEncoded(None, None, None, None, None)

        # Player names are inline plain data; keep item part as original bytes.
        if raw[0:2] == _PLAYER_PREFIX:
            return ItemNamePartsEncoded(None, None, raw, None, None, raw, raw)

        cached = ItemName._parts_encoded_cache.get(raw)
        if cached is not None:
            return cached

        if not _string_table_loaded and not _load_enqueued:
            load_string_table(_get_client_language())

        if not _string_table_loaded or not _string_table or raw in _pending:
            return ItemNamePartsEncoded(None, None, None, None, None)

        _pending.add(raw)
        _decode_pool.submit(_decode_and_cache, raw)
        return ItemNamePartsEncoded(None, None, None, None, None)

import re
import time
import zlib


def make_name_signature(item_name: str) -> str:
    clean = re.sub(r"<[^>]+>", "", item_name or "").strip().lower()
    if not clean:
        return ""
    checksum = zlib.crc32(clean.encode("utf-8")) & 0xFFFFFFFF
    return f"{checksum:08x}"


def make_event_id(sequence: int, now_ms: int | None = None) -> str:
    timestamp_ms = int(now_ms) if now_ms is not None else int(time.time() * 1000.0)
    return f"{timestamp_ms & 0xFFFFFFFF:08x}{int(sequence) & 0xFFFF:04x}"


def _normalize_time_code(display_time: str) -> str:
    text = (display_time or "").strip()
    if not text:
        return ""
    # Prefer compact 24h HHMM code to stay within shared payload limits.
    # Accept "HH:MM AM/PM" and fallback to first 4 digits found.
    am_pm_match = re.match(r"^\s*(\d{1,2}):(\d{2})\s*([APap][Mm])\s*$", text)
    if am_pm_match:
        hour = int(am_pm_match.group(1))
        minute = int(am_pm_match.group(2))
        ampm = am_pm_match.group(3).lower()
        if ampm == "pm" and hour != 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}{minute:02d}"

    digits = re.sub(r"[^0-9]", "", text)
    return digits[:4] if len(digits) >= 4 else ""


def build_drop_meta(event_id: str, name_signature: str, display_time: str = "") -> str:
    event_part = (event_id or "")[:16]
    sig_part = (name_signature or "")[:8]
    time_part = _normalize_time_code(display_time)
    # v2|<event>|<sig>|<hhmm>
    return f"v2|{event_part}|{sig_part}|{time_part}"[:31]


def parse_drop_meta(meta_text: str) -> dict[str, str]:
    text = (meta_text or "").strip()
    result = {
        "version": "v1",
        "event_id": "",
        "name_signature": "",
        "display_time": "",
    }
    if not text:
        return result

    if text.startswith("v2|"):
        parts = text.split("|", 3)
        result["version"] = "v2"
        result["event_id"] = parts[1].strip() if len(parts) > 1 else ""
        result["name_signature"] = parts[2].strip() if len(parts) > 2 else ""
        result["display_time"] = parts[3].strip() if len(parts) > 3 else ""
        return result

    # Legacy: "<display_time>|<signature>" or just "<display_time>"
    if "|" in text:
        display_part, sig_part = text.split("|", 1)
        result["display_time"] = display_part.strip()
        result["name_signature"] = sig_part.strip()
    else:
        result["display_time"] = text
    return result


def build_name_chunks(full_name: str, chunk_size: int = 31) -> list[tuple[int, int, str]]:
    clean = full_name or ""
    if chunk_size <= 0:
        chunk_size = 31
    if not clean:
        return [(1, 1, "")]

    chunks = [clean[i:i + chunk_size] for i in range(0, len(clean), chunk_size)]
    total = len(chunks)
    return [(idx + 1, total, chunks[idx]) for idx in range(total)]


def encode_name_chunk_meta(index: int, total: int) -> str:
    return f"{max(1, int(index))}/{max(1, int(total))}"[:31]


def decode_name_chunk_meta(meta_text: str) -> tuple[int, int]:
    text = (meta_text or "").strip()
    match = re.match(r"^\s*(\d{1,4})\s*/\s*(\d{1,4})\s*$", text)
    if not match:
        return 1, 1
    idx = max(1, int(match.group(1)))
    total = max(1, int(match.group(2)))
    if idx > total:
        idx = total
    return idx, total


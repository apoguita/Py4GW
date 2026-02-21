import random
import string
import sys
from pathlib import Path
from collections import defaultdict

# Allow running as a standalone script from repository root.
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import (
    build_drop_meta,
    build_name_chunks,
    decode_name_chunk_meta,
    encode_name_chunk_meta,
    make_event_id,
    make_name_signature,
    parse_drop_meta,
)


def _rand_name(min_len=8, max_len=80):
    size = random.randint(min_len, max_len)
    chars = string.ascii_letters + string.digits + " -'"
    return "".join(random.choice(chars) for _ in range(size)).strip() or "Item"


def test_meta_roundtrip():
    event_id = make_event_id(42, 1711111111111)
    sig = make_name_signature("Raven Staff of the Mists")
    meta = build_drop_meta(event_id, sig, "03:47 PM")
    parsed = parse_drop_meta(meta)
    assert parsed["event_id"] == event_id
    assert parsed["name_signature"] == sig
    assert parsed["version"] == "v2"


def test_chunk_roundtrip():
    full_name = "Legendary Very Long Item Name " * 4
    chunks = build_name_chunks(full_name, chunk_size=31)
    bucket = {}
    total = 0
    for idx, chunk_total, chunk in chunks:
        meta = encode_name_chunk_meta(idx, chunk_total)
        got_idx, got_total = decode_name_chunk_meta(meta)
        bucket[got_idx] = chunk
        total = got_total
    merged = "".join(bucket.get(i, "") for i in range(1, total + 1))
    assert merged == full_name


def stress_delivery_simulation(total_events=2000, duplicate_rate=0.35, drop_rate=0.0):
    random.seed(1337)
    sender_email = "sender@test"

    generated = []
    packets = []

    for seq in range(1, total_events + 1):
        full_name = _rand_name()
        short_name = full_name[:31]
        sig = make_name_signature(full_name)
        event_id = make_event_id(seq, 1711111111111 + seq)
        meta = build_drop_meta(event_id, sig, "04:01 PM")
        generated.append((event_id, full_name))

        # Name side-channel packets
        if len(full_name) > 31 or full_name != short_name:
            for idx, count, chunk in build_name_chunks(full_name, chunk_size=31):
                packets.append({
                    "type": "TrackerNameV2",
                    "sig": sig,
                    "chunk": chunk,
                    "meta": encode_name_chunk_meta(idx, count),
                })

        # Main drop packet
        packets.append({
            "type": "TrackerDrop",
            "event_id": event_id,
            "sender": sender_email,
            "short_name": short_name,
            "meta": meta,
        })

        # Add duplicates for retry simulation
        if random.random() < duplicate_rate:
            packets.append(dict(packets[-1]))
        if random.random() < duplicate_rate * 0.5:
            packets.append(dict(packets[-1]))

    random.shuffle(packets)

    # Receiver model
    seen = set()
    chunk_buf = defaultdict(lambda: {"total": 0, "chunks": {}})
    names_by_sig = {}
    received_unique = {}

    for pkt in packets:
        if random.random() < drop_rate:
            continue
        if pkt["type"] == "TrackerNameV2":
            sig = pkt["sig"]
            idx, total = decode_name_chunk_meta(pkt["meta"])
            buf = chunk_buf[sig]
            buf["total"] = max(buf["total"], total)
            buf["chunks"][idx] = pkt["chunk"]
            if len(buf["chunks"]) >= buf["total"]:
                names_by_sig[sig] = "".join(buf["chunks"].get(i, "") for i in range(1, buf["total"] + 1))
            continue

        parsed = parse_drop_meta(pkt["meta"])
        event_id = parsed["event_id"]
        sig = parsed["name_signature"]
        key = (pkt["sender"], event_id)
        if key in seen:
            continue
        seen.add(key)
        resolved = names_by_sig.get(sig, pkt["short_name"])
        received_unique[event_id] = resolved

    generated_ids = {ev for ev, _ in generated}
    received_ids = set(received_unique.keys())
    missing = generated_ids - received_ids
    extra = received_ids - generated_ids

    assert not extra, f"Unexpected extra events: {len(extra)}"
    assert len(missing) == 0, f"Missing events: {len(missing)}"
    print(f"[HARNESS] events={total_events} unique_received={len(received_ids)} missing=0 duplicates_filtered={len(packets)-len(received_ids)}")


if __name__ == "__main__":
    test_meta_roundtrip()
    test_chunk_roundtrip()
    stress_delivery_simulation(total_events=2500)
    print("[HARNESS] OK")

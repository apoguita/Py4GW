# Packet Sniffers Reference

## Scope

This document is the dedicated reference for Py4GW packet sniffing surfaces.

It covers:

- the unified packet sniffer architecture across Python and C++
- the Python and C++ file locations
- what data is actually captured
- the current strengths and limitations of the capture path
- the operator-facing packet capture tools that consume the sniffers

Use this file when the task is about packet identification, packet capture fidelity, packet dump tooling, or deciding where live packet bytes can be observed without new native RE.

## Available Sniffers

| Layer | Surface | Notes |
|------|---------|-------|
| Python facade | `Py4GWCoreLib/PacketSniffer.py` | Single `PacketSniffer` class exposing both directions |
| Native module | `PyPacketSniffer` | Embedded pybind11 module exposing one `PacketSniffer` singleton |
| Native implementation | `Py4GW\src\py_packet_sniffer.cpp` | Unified StoC and CToS capture logic |
| Native header | `Py4GW\include\py_packet_sniffer.h` | Shared native packet log types and sniffer state |

The unified Python and C++ surfaces expose packet entries with:

- `direction`
- `tick`
- `header`
- `size`
- `data`

The hook mechanisms are still direction-specific internally, but they now feed a single native class and a single Python-facing module.

## Unified Python Facade

### Python surface

- `Py4GWCoreLib/PacketSniffer.py`
- singleton: `SNIFFER`

Behavior:

- initializes either one direction or both directions
- returns normalized packet entries with an explicit `direction` field
- preserves per-direction log clearing and teardown
- does not require separate StoC and CToS wrapper modules

## StoC Capture Path

### Python surface

- native implementation is part of `PyPacketSniffer`
- consumed in Python through `Py4GWCoreLib/PacketSniffer.py`

Behavior:

- initializes once
- registers callbacks for all StoC headers
- returns copied packet logs
- does not clear logs unless `clear_logs()` is called

### Native implementation

- `Py4GW\include\py_packet_sniffer.h`
- `Py4GW\src\py_packet_sniffer.cpp`

### Capture model

The StoC sniffer:

1. resolves the live StoC handler table
2. reads the template size for each header
3. registers a passive callback for every header via `GW::StoC::RegisterPacketCallback`
4. copies packet bytes into a thread-safe log buffer

Important implementation details:

- `STOC_HEADER_COUNT = 0x1E7`
- size source is the live `StoCHandlerArray` template size, not a fixed guessed size
- copied bytes are bounded by `kMaxPacketBuffer = 512`
- `entry.size` stores the resolved packet size
- `entry.data` stores the safely copied bytes

Practical consequence:

- for packet-identification work, StoC logs are already far better than an opcode-only event stream

## CToS Capture Path

### Python surface

- native implementation is part of `PyPacketSniffer`
- consumed in Python through `Py4GWCoreLib/PacketSniffer.py`

Behavior:

- initializes once
- places a detour on the outbound send wrapper
- returns copied packet logs
- does not clear logs unless `clear_logs()` is called

### Native implementation

- `Py4GW\include\py_packet_sniffer.h`
- `Py4GW\src\py_packet_sniffer.cpp`

### Capture model

The CToS sniffer hooks the higher-level explicit send wrapper instead of a lower-level encoded transport function.

That wrapper preserves:

- packet pointer
- packet size
- wrapper calling convention

Important implementation details:

- packet size ceiling: `kMaxReasonablePacketSize = 4096`
- the hook reads the header directly from the outbound packet bytes
- the copied `entry.size` is the actual wrapper-provided packet byte length
- the copied `entry.data` is the raw outbound packet body

Practical consequence:

- for CToS packet RE, the captured size and bytes are authoritative for the wrapper-level packet struct being sent

## Operator Tools

### General packet test widget

- `Widgets/Coding/Debug/Guild Wars/PacketSnifferTester.py`

Purpose:

- minimal start/stop packet capture
- logs buffered StoC and CToS packets to the console

### Name-surface capture tool

- `capture_name_surfaces.py`

Purpose:

- scenario-based capture workflow for:
  - `guild`
  - `friends`
  - `call_target`
- marker-based capture windows
- per-window header summaries
- unique-payload grouping by header
- observed-name cache inspection

Recent findings:

- guild load captures confirmed identity/bootstrap traffic such as `0x0121` and `0x0118`
- those same guild captures did not yet confirm roster-member packets such as `0x0127` / `0x0128` / `0x012A` / `0x012B` / `0x012C` / `0x012D`
- toggling the guild window locally without travel produced no guild-family network traffic
- call-target testing on the current build surfaced outbound `0x0039 INTERACT_LIVING`, not the older assumed `0x0023 TARGET_CALL`

Practical consequence:

- the sniffers are still useful for proving what does and does not replay over the network
- but current evidence says guild roster names and call-target displayed names likely require consumer-side RE in WASM/native code, not just more packet capture

### Packet decoder

- `Py4GWCoreLib/PacketSniffer.py`

Purpose:

- map packet headers to human-readable names
- provide lightweight packet-body decoding
- provide `u32` and UTF-16 probes for name-related packet identification work

## What The Sniffers Already Solve

The sniffers already solve the hard part of packet visibility:

- live interception
- packet direction
- header capture
- size capture
- raw byte capture

So when packet identification is blocked, the cause is usually not missing native access. It is usually one of:

1. the Python dump layer is too shallow
2. the wrong scenario is being captured
3. the packet body still needs field interpretation

## Current Limitation

The main visibility loss currently happens after capture:

- a decoder may only expose a few named fields
- a dump tool may show only a truncated hex preview
- repeated captures may not yet be compared side by side

This means future work on packet identification should usually start by improving the dump/decoder workflow before escalating to deeper native changes.

## Recommended Workflow

1. choose the exact surface being investigated
2. capture with the existing sniffers
3. dump full raw bytes for the relevant packet family
4. compare repeated captures with one controlled variable changed
5. only then move to static RE or hook planning if field meaning is still unclear

## Related Files

- `docs/RE/name_obfuscation_reverse_engineering.md`
- `docs/RE/map_travel_research.md`
- `Py4GWCoreLib/PacketSniffer.py`
- `Py4GWCoreLib/PacketSniffer.py`
- `capture_name_surfaces.py`

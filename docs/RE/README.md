# RE Documentation Index

This folder is the maintained reverse-engineering library for Py4GW.

Use these files by subject area, not by history:

| File | Purpose | Use It When |
|------|---------|-------------|
| `reverse_engineering_reference.md` | Canonical RE reference for tools, architecture, bridging methods, key function maps, UI message architecture, and travel findings | Starting a new RE task or re-orienting to the stack |
| `CPP_WASM_MAPPING.md` | Procedure for translating C++ or GWCA functions into WASM and stripped EXE addresses | Bridging functions across layers |
| `packet_sniffers_reference.md` | Dedicated reference for StoC/CToS sniffers, packet capture architecture, and dump tooling | Working on live packet capture, packet identification, or sniffer capabilities |
| `rosetta_stone.txt` | GwA2 to Py4GW mapping | Looking up legacy equivalents |
| `map_travel_reverse_engineering.md` | Travel-pipeline RE log and conclusions | Working on travel, redirect, or map-load sequencing |
| `map_travel_research.md` | Packet-focused travel notes | Working from packet captures |
| `name_obfuscation_reverse_engineering.md` | Name-obfuscation hook architecture, timing model, packet candidates, unresolved surfaces, and the current friend/guild/comm subsystem split | Working on name aliasing, original-name accessors, or missing name-bearing UI surfaces |
| `name_tag_color_reverse_engineering.md` | Agent/item name-tag COLOR pipeline: the `GetConsiderColor` resolver (EXE `FUN_007f02e0`) + `AvCharGetConsiderColor` (`FUN_007d9cf0`) detour recipe/ABI, allegiance→ARGB table, item-rarity markup, proposed `PyAgentTagColor` module, and the functional tests | Coloring agent/enemy/item name tags natively (per-agent/per-allegiance) |
| `native_ui_controls_handover.md` | ★ **HANDOVER — read first.** Honest state: per-control status matrix, root causes, fixes that stuck, dead-ends (reverted — do not repeat), open problems, next steps, build/test workflow | **Picking up the native UI-controls effort** |
| `native_button_pipeline.md` | **AUTHORITATIVE** native UI-control creation reference: master address/flag/status table, per-control recipes (button, checkbox, radio, hyperlink, edit, progress, tabs, slider, group header), teardown, and cross-cutting gotchas | Creating or fixing a specific native UI control |
| `ui_controls_master_catalog.md` | Swarm-produced master catalog: the decompiler-verified UI creation/dispatch **model** + **166 discovered control FrameProcs** (addresses/roles) + 40 deep per-control RE writeups | Looking for a control that isn't yet wrapped, or the authoritative model |
| `ui_elements_creation_recipes.md` | Per-control recipe deep-dives (root cause / recipe / fix), Ghidra-swarm-derived | Need the decompile-level "why" behind a control's recipe |
| `ui_controls_catalog.md` | Native UI control inventory (FrameProc addresses, struct layouts, assertion strings, tiers) | Looking up a control's FrameProc/struct/assertion, or its historical status |
| `ui_frame_system_mapping.md` | UI frame taxonomy and mapping notes | Working on frame types or frame behavior |
| `window_creation_architecture.md` | End-to-end window creation architecture notes | Working on frame/window creation internals |
| `native_gw_window_creation_investigation.md` | Lower-level historical window-creation investigation | Need raw prior window findings |
| `native_ui_title_and_encoded_string_reference.md` | Encoded string, title, and text handling reference | Working on encoded UI text or labels |
| `title_rendering_research.md` | Title rendering experiments and outcomes | Working on titles or overhead text |
| `player_skill_system_callable_functions.md` | Skill-system callable-function notes | Working on skill invocation |
| `struct_identification_methodology.md` | Methodology for identifying unknown structs | Need a repeatable struct RE workflow |
| `gw_combat_ai_reverse_engineering.md` | Combat AI analysis | Working on combat AI behavior |
| `native_gw_ui_function_catalog.json` | Machine-readable catalog of native GW UI functions | Need address lookups or scripting input |

## Method: WASM-First

Reverse-engineer on `/Gw.wasm` **first** (it keeps full debug symbols — `CCharAgent::GetConsiderColor`, `CtlTextMl::Markup`, etc.), then map the confirmed finding to the stripped `/Gw.exe` only at the end, where the injector needs the concrete address. Reading architecture in the EXE first (`FUN_xxxxxxxx`) is slower and error-prone. Always pass the explicit `program` path on Ghidra MCP calls — several same-named `Gw.exe` images may be loaded. Full procedure in `reverse_engineering_reference.md` → "WASM-First Workflow" and `CPP_WASM_MAPPING.md`.

## Recommended Reading Order

1. `reverse_engineering_reference.md` (start with "WASM-First Workflow")
2. `CPP_WASM_MAPPING.md`
3. The subsystem-specific document for the task at hand

## Naming Rule

Avoid generic filenames such as `handover.md` for long-lived references. Use descriptive filenames based on the system or topic being documented.

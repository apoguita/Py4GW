# AGENTS.md

- No repo-level CI/test runner is configured: no `.github/workflows`, no `pytest`/`tox` config, no `Makefile`, and `requirements.txt` is empty. Verify with targeted scripts instead of guessing a global command.
- `pyproject.toml` only configures formatting. Preserve Black at `line-length = 120`, keep single quotes if already present (`skip-string-normalization = true`), and keep `isort`'s one-import-per-line style (`force_single_line = true`).
- `pyrightconfig.json` only sets `stubPath = ./stubs` and suppresses missing module source noise. Use `pyright` only if it is installed in the environment.
- README explicitly targets Python 3.13.0 32-bit for injected/runtime work. Do not casually switch interpreter versions when debugging launcher or injection issues.
- `Py4GWCoreLib/__init__.py` is a broad convenience facade, not a minimal import surface: it manually appends system `site-packages`, re-exports most high-level modules, and redirects `sys.stdout`/`sys.stderr` into the Py4GW console. Avoid treating `import Py4GWCoreLib` as a neutral import when debugging startup/import side effects.

## Docs Hierarchy

- `docs/Py4GW_Conceptual_Model.md` is the canonical architecture/source-of-truth document for project layers and terminology.
- `docs/MCP_bridge.md` is the MCP-facing bridge planning summary; use it for bridge/MCP modeling, not as the primary architecture source.
- `BridgeRuntime/README.md` is the operator/runtime usage reference for daemon + injected bridge client + CLI.
- `docs/Py4GW_Model_Features_Detail.txt` is a derived plain-text export for quick scanning, not a separate authority.
- `docs/widget_manager_and_catalog.md` is the highest-value reference before changing widget discovery, widget metadata defaults, `WidgetHandler`, or `WidgetCatalog` behavior.

## RE (Reverse Engineering) — `docs/RE/`

- **Start with `docs/RE/reverse_engineering_reference.md`** — the comprehensive library reference. Covers the three-layer architecture (Python `native_src`, C++ GWCA, Ghidra), key function catalogs with EXE↔WASM↔CPP mappings, bridging techniques, UI message dispatch architecture, and workflows for adding new functions.
- `docs/RE/CPP_WASM_MAPPING.md` — the full CPP↔WASM↔EXE translation procedure with worked examples and pitfall notes.
- `docs/RE/rosetta_stone.txt` — GwA2 (AutoIt) to Py4GW function mapping reference.
- `docs/RE/gw_combat_ai_reverse_engineering.md` — combat AI RE analysis.
- `docs/RE/native_gw_ui_function_catalog.json` — catalog of native GW UI functions with addresses.
- `docs/RE/native_gw_window_creation_investigation.md` — window proc creation RE.
- `docs/RE/native_ui_title_and_encoded_string_reference.md` — UI title and encoding reference.

### RE Tool Locations

| Layer | Path | Key Files |
|-------|------|-----------|
| **C++ (GWCA)** | `C:\Users\Apo\Py4GW\vendor\gwca\Source\` | `AgentMgr.cpp`, `UIMgr.cpp`, `GameThreadMgr.cpp` |
| **C++ (GWCA headers)** | `C:\Users\Apo\Py4GW\vendor\gwca\Include\GWCA\` | `Managers/AgentMgr.h`, `Utilities/Scanner.h` |
| **Python native** | `Py4GWCoreLib\native_src\` | `methods/PlayerMethods.py`, `internals/native_function.py` |
| **Python Scanner** | `Py4GWCoreLib\Scanner.py` | FindAssertion, FindInRange, ToFunctionStart |
| **Ghidra EXE** | `/Gw.exe(Symbols)` via MCP | 18,017 functions, x86:LE:32, base `0x00400000` |
| **Ghidra WASM** | `/Gw.wasm` via MCP | 18,004 functions, Wasm:LE:32, base `ram:80000000` |

### Key Function Mappings (quick reference)

| GWCA Name | WASM Symbol | EXE Address |
|-----------|-------------|-------------|
| `DoWorldActon_Func` | `CoreActionExecuteWorldAction` | `0x0050e5e0` |
| `CallTarget_Func` | `CharCliPlayerOrderAlertSimple` | `0x00917740` |
| `ChangeTarget_Func` | `IAgentView::SetSelections` | `0x007e0f60` |
| `MoveTo_Func` | `IUi::Game::Walk*` | `0x00534fa0` |
| `SendAgentDialog_Func` | (thunk) | `0x008105b0` |

Full catalog with sub-function breakdowns in `docs/RE/reverse_engineering_reference.md`.

### UI Message System

The game uses a **hash table** (`THashTable<IFrame::Msg::CHandler>` at `DAT_ram_005a0338`) for message dispatch, not a switch statement. Messages fall into three ranges:
- `0x00–0x55` — base frame lifecycle
- `0x100000xx` — server→client notifications (~90 mapped, ~15 unknown, ~6 newly discovered via WASM)
- `0x300000xx` — client→server commands (~30 mapped, all send-to-server actions)

The authoritative UIMessage enum is at `C:\Users\Apo\Py4GW\vendor\gwca\Include\GWCA\Managers\UIMgr.h:294` (~120 entries). To discover missing messages, either hook `SendUIMessage_Func` at runtime (GWCA already does this) or run a Ghidra script against WASM callers of `FrameMsgSendRegistered`. Full procedure including the script is in `docs/RE/reverse_engineering_reference.md` Section 4.

### RE Tool Locations

| Layer | Path | Key Files |
|-------|------|-----------|
| **C++ (GWCA)** | `C:\Users\Apo\Py4GW\vendor\gwca\Source\` | `AgentMgr.cpp`, `UIMgr.cpp`, `GameThreadMgr.cpp` |
| **C++ (GWCA headers)** | `C:\Users\Apo\Py4GW\vendor\gwca\Include\GWCA\` | `Managers/AgentMgr.h`, `Utilities/Scanner.h` |
| **Python native** | `Py4GWCoreLib\native_src\` | `methods/PlayerMethods.py`, `internals/native_function.py` |
| **Python Scanner** | `Py4GWCoreLib\Scanner.py` | FindAssertion, FindInRange, ToFunctionStart |
| **Ghidra EXE** | `/Gw.exe(Symbols)` via MCP | 18,017 functions, x86:LE:32, base `0x00400000` |
| **Ghidra WASM** | `/Gw.wasm` via MCP | 18,004 functions, Wasm:LE:32, base `ram:80000000` |

### Key Function Mappings (quick reference)

| GWCA Name | WASM Symbol | EXE Address |
|-----------|-------------|-------------|
| `DoWorldActon_Func` | `CoreActionExecuteWorldAction` | `0x0050e5e0` |
| `CallTarget_Func` | `CharCliPlayerOrderAlertSimple` | `0x00917740` |
| `ChangeTarget_Func` | `IAgentView::SetSelections` | `0x007e0f60` |
| `MoveTo_Func` | `IUi::Game::Walk*` | `0x00534fa0` |
| `SendAgentDialog_Func` | (thunk) | `0x008105b0` |

Full catalog with sub-function breakdowns in `docs/RE/reverse_engineering_reference.md`.

## Entry Points

- `Py4GW_widget_manager.py` is the in-client widget bootstrap: it creates the manager INI key, runs widget discovery, and hands off to `Widgets/WidgetCatalog/Py4GW_widget_catalog.py`.
- `Py4GW_Launcher.py` is the external launcher/injector UI.
- Bridge stack wiring is split across:
  - injected widget: `Widgets/Coding/Tools/Bridge Client.py`
  - daemon: `bridge_daemon.py`
  - operator CLI: `bridge_cli.py`
- MCP adapter entrypoint is `py4gw_mcp_server.py`; it talks to the daemon over stdio->daemon bridging rather than directly to injected clients.
- Bridge defaults are verified in code: widget server `127.0.0.1:47811`, control server `127.0.0.1:47812`, and the CLI targets control port `47812` by default.
- `Sources/modular_bot/` contains the real ModularBot implementation. Files under `Widgets/Automation/modularbot/` are mostly thin wrappers that expose those tools/prebuilts through Widget Manager.

## Focused Checks

- Bridge help / argument discovery:
  - `python "bridge_daemon.py" --help`
  - `python "bridge_cli.py" --help`
- MCP adapter help / surface discovery:
  - `python "py4gw_mcp_server.py" --help`
- ModularBot docs coverage check:
  - `python "Sources/modular_bot/tools/validate_modular_docs.py"`
- Merchant Rules offline regression harness:
  - `python "Widgets/Data/test_merchant_rules_regression.py"`

## Repo-Specific Gotchas

- For architecture questions, prefer module-specific imports and docs over the broad `Py4GWCoreLib` facade. The conceptual model treats `Py4GWCoreLib` as the single Python-facing source-of-truth layer, `py4gwcorelib_src` as support infrastructure, and `GLOBAL_CACHE` as a derivative consumer/cache layer.
- The current MCP adapter intentionally exposes a narrow safe tool set over daemon control, not generic arbitrary bridge calls: `list_clients`, `list_namespaces`, `list_commands`, `describe_runtime`, `get_map_state`, `get_player_state`, and `list_agents`.
- Widget discovery is folder-based, not file-based: `WidgetHandler` walks `Widgets/`, and only folders containing a `.widget` marker are discovery roots; every `.py` file in that same folder is loaded as a widget.
- Widget metadata defaults are non-obvious and come from `Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py`: `MODULE_CATEGORY` defaults to the first `widget_path` segment, `MODULE_TAGS` defaults to all path segments, and `OPTIONAL` defaults to `False` only for `System` and `Py4GW` categories.
- Before touching follow-system code, read `FOLLOW_REFACTOR_HANDOVER.md`.
- `Py4GWCoreLib/GlobalCache/SharedMemory.py` is startup-sensitive and currently imports `HeroAI.follow.leader_publish` directly. Do not replace that with broad package-root imports.
- `HeroAI/follow/__init__.py` intentionally exports nothing. Import exact submodules such as `HeroAI.follow.leader_publish`, not `HeroAI.follow`.
- Avoid committing local runtime/config churn unless the task is specifically about them: `Py4GW.ini`, `Py4GW_Launcher.ini`, and `Py4GW_injection_log.txt`. README documents `git update-index --skip-worktree` for those files.

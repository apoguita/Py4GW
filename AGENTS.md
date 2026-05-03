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

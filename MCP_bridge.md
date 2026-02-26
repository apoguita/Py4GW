diff --git a/c:\Users\Apo\Py4GW_python_files\BridgeRuntime/README.md b/c:\Users\Apo\Py4GW_python_files\BridgeRuntime/README.md
new file mode 100644
--- /dev/null
+++ b/c:\Users\Apo\Py4GW_python_files\BridgeRuntime/README.md
@@ -0,0 +1,492 @@
+# Py4GW Bridge Runtime (Daemon + Injected Client + CLI)
+
+This document explains the bridge infrastructure added for Py4GW and how to use it.
+
+The bridge lets you talk to **live injected Py4GW clients** from a normal Python process (outside injection) using a local TCP protocol.
+
+It is designed for:
+
+- AI-assisted scripting and code generation
+- live runtime introspection
+- multi-client orchestration
+- stress testing / repeated action execution
+- future MCP adapter integration
+
+## Components
+
+### 1. Injected Bridge Client (widget)
+
+Expected widget path:
+
+- `Widgets/System/Bridge Client.py`
+
+This runs inside each injected GW/Py4GW client and:
+
+- connects to the daemon over TCP
+- executes requests on the injected/runtime side
+- exposes library layers (raw/native wrappers, cache/services, shared memory)
+- tracks async operations (queued actions, shmem commands)
+
+### 2. Bridge Daemon (server)
+
+File:
+
+- `bridge_daemon.py`
+
+This runs outside injection and:
+
+- accepts connections from multiple injected clients
+- identifies clients by `HWND` (primary) and `PID` (fallback)
+- exposes a control API for tools/CLI/MCP
+- routes requests to a specific target client
+
+### 3. Bridge CLI (tester/operator tool)
+
+File:
+
+- `bridge_cli.py`
+
+This is a local CLI for testing and using the daemon without writing raw socket code.
+
+## Architecture (brief)
+
+```text
+[bridge_cli.py / future MCP adapter]
+            |
+            v
+      [bridge_daemon.py]
+            |
+   (routes by HWND / PID)
+            |
+            v
+[Injected Bridge Client widget]  (one per GW client/account)
+            |
+            +--> native/raw layers (Map, Player, Agent, AgentArray, ...)
+            +--> cache/service layers (GLOBAL_CACHE.*)
+            +--> shmem / multibox commands (GLOBAL_CACHE.ShMem)
+```
+
+## Protocol notes (implementation)
+
+- Local TCP
+- Length-prefixed JSON (4-byte little-endian length + UTF-8 JSON)
+- Request/response protocol
+- Immediate ack for async/queued operations + status polling
+
+## Prerequisites
+
+- Py4GW environment working (injection already working)
+- Python (same Win32 Python runtime is recommended for consistency)
+- At least one injected client with the bridge widget enabled
+
+## Start the server (daemon)
+
+Run outside injection:
+
+```powershell
+python bridge_daemon.py --token mytoken
+```
+
+Defaults:
+
+- Widget ingress server: `127.0.0.1:47811`
+- Control API server (CLI/MCP talks here): `127.0.0.1:47812`
+
+Optional flags:
+
+- `--widget-host`
+- `--widget-port`
+- `--control-host`
+- `--control-port`
+- `--token`
+
+Example custom ports:
+
+```powershell
+python bridge_daemon.py --widget-port 50011 --control-port 50012 --token mytoken
+```
+
+## Connect the injected bridge client (widget)
+
+In the Py4GW Widget Manager:
+
+1. Enable `Bridge Client`
+2. Set:
+   - `Host`: `127.0.0.1`
+   - `Port`: `47811`
+   - `Token`: `mytoken`
+3. Click `Apply Connection Settings`
+
+The widget UI should show:
+
+- connection status
+- daemon endpoint
+- `HWND`
+- `PID`
+- session id
+- pending op count / request counts
+
+## CLI quick start
+
+The CLI talks to the daemon **control API** (default `47812`).
+
+### Ping the daemon
+
+```powershell
+python bridge_cli.py ping
+```
+
+### List connected clients
+
+```powershell
+python bridge_cli.py list-clients
+```
+
+This returns connected injected clients with:
+
+- `hwnd`
+- `pid`
+- `account_email`
+- `character_name`
+- session metadata
+
+## Typical workflow
+
+1. Start daemon
+2. Connect one or more injected clients (via widget)
+3. Get `HWND` from `list-clients`
+4. Query data or call methods on that client using `bridge_cli.py request`
+
+## CLI command reference
+
+### `ping`
+
+Ping the daemon.
+
+```powershell
+python bridge_cli.py ping
+```
+
+### `list-clients`
+
+List all connected injected clients.
+
+```powershell
+python bridge_cli.py list-clients
+```
+
+### `namespaces`
+
+List bridge namespaces available on a specific client.
+
+By `HWND` (preferred):
+
+```powershell
+python bridge_cli.py namespaces --hwnd 123456
+```
+
+By `PID` (fallback):
+
+```powershell
+python bridge_cli.py namespaces --pid 12340
+```
+
+### `request`
+
+Send a bridge request to a target client.
+
+```powershell
+python bridge_cli.py request --hwnd 123456 --cmd player.get_state
+```
+
+Parameters:
+
+- `--hwnd` or `--pid`
+- `--cmd` bridge command
+- `--params-json` JSON object for payload params
+- `--request-id` optional custom request id
+- `--poll` poll async status after request
+- `--poll-timeout`
+- `--poll-interval`
+
+### `status`
+
+Poll the status of a previously submitted async/queued request.
+
+```powershell
+python bridge_cli.py status --hwnd 123456 --tracked-request-id abc123
+```
+
+## Testing plan (recommended)
+
+Run these in order.
+
+### 1. Infrastructure test
+
+```powershell
+python bridge_cli.py ping
+python bridge_cli.py list-clients
+```
+
+Expected:
+
+- daemon responds
+- at least one client appears
+
+### 2. Basic runtime state reads
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd player.get_state
+python bridge_cli.py request --hwnd <HWND> --cmd map.get_state
+python bridge_cli.py request --hwnd <HWND> --cmd agent.list --params-json "{\"group\":\"enemy\"}"
+```
+
+### 3. Namespace discovery
+
+```powershell
+python bridge_cli.py namespaces --hwnd <HWND>
+```
+
+### 4. Method introspection (whole layer)
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd player.list_methods
+python bridge_cli.py request --hwnd <HWND> --cmd agent.list_methods
+python bridge_cli.py request --hwnd <HWND> --cmd agent_array.list_methods
+python bridge_cli.py request --hwnd <HWND> --cmd party.list_methods
+python bridge_cli.py request --hwnd <HWND> --cmd inventory.list_methods
+python bridge_cli.py request --hwnd <HWND> --cmd shmem.list_methods
+```
+
+### 5. Generic method calls (read-only first)
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd player.call --params-json "{\"method\":\"GetName\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd player.call --params-json "{\"method\":\"GetAgentID\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd map.call --params-json "{\"method\":\"GetMapID\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd agent_array.call --params-json "{\"method\":\"GetEnemyArray\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd party.call --params-json "{\"method\":\"GetPartyID\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd inventory.call --params-json "{\"method\":\"GetFreeSlotCount\",\"args\":[]}"
+```
+
+### 6. Curated queued action test (safe)
+
+Travel example (polls until completion/timeout):
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd map.travel --params-json "{\"map_id\":55}" --poll
+```
+
+Skip cinematic (only when in cinematic):
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd map.skip_cinematic --poll
+```
+
+### 7. Async status polling (manual)
+
+If you want to control request IDs yourself:
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd map.travel --params-json "{\"map_id\":55}" --request-id travel_test_001
+python bridge_cli.py status --hwnd <HWND> --tracked-request-id travel_test_001
+```
+
+## Curated bridge commands (stable helpers)
+
+These are explicitly implemented and useful for common tasks.
+
+- `system.ping`
+- `system.list_namespaces`
+- `client.describe`
+- `map.get_state`
+- `player.get_state`
+- `agent.list`
+- `agent.get_info`
+- `map.travel`
+- `map.skip_cinematic`
+- `ops.get_status`
+- `shmem.send_command`
+
+## Layer namespaces (generic access)
+
+The bridge exposes complete layers via `<namespace>.list_methods` and `<namespace>.call`.
+
+### Native/raw wrapper layers
+
+- `map`
+- `player`
+- `agent`
+- `agent_array`
+- `party_raw`
+- `skill`
+- `skillbar_raw`
+- `inventory_raw`
+- `quest_raw`
+- `effects_raw`
+
+### Cache/service layers
+
+- `party`
+- `party.players`
+- `party.heroes`
+- `party.henchmen`
+- `party.pets`
+- `skillbar`
+- `inventory`
+- `quest`
+- `effects`
+- `shmem`
+
+## Generic call examples by layer
+
+### Player
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd player.call --params-json "{\"method\":\"GetXY\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd player.call --params-json "{\"method\":\"GetTargetID\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd player.call --params-json "{\"method\":\"IsPlayerLoaded\",\"args\":[]}"
+```
+
+### Agent / AgentArray
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd agent_array.call --params-json "{\"method\":\"GetAllyArray\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd agent.call --params-json "{\"method\":\"GetXY\",\"args\":[12345]}"
+python bridge_cli.py request --hwnd <HWND> --cmd agent.call --params-json "{\"method\":\"IsDead\",\"args\":[12345]}"
+```
+
+### Party (cache/service layer)
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd party.call --params-json "{\"method\":\"GetPartyID\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd party.call --params-json "{\"method\":\"GetPartySize\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd party.call --params-json "{\"method\":\"IsPartyLoaded\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd party.players.call --params-json "{\"method\":\"GetAgentIDByLoginNumber\",\"args\":[1]}"
+```
+
+### Inventory (cache/service layer)
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd inventory.call --params-json "{\"method\":\"GetFreeSlotCount\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd inventory.call --params-json "{\"method\":\"GetGoldOnCharacter\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd inventory.call --params-json "{\"method\":\"GetModelCount\",\"args\":[2992]}"
+```
+
+### Skillbar (cache/service layer)
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd skillbar.call --params-json "{\"method\":\"GetZeroFilledSkillbar\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd skillbar.call --params-json "{\"method\":\"GetCasting\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd skillbar.call --params-json "{\"method\":\"GetHoveredSkillID\",\"args\":[]}"
+```
+
+### Quest
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd quest.call --params-json "{\"method\":\"GetActiveQuest\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd quest_raw.call --params-json "{\"method\":\"GetQuestLogIds\",\"args\":[]}"
+```
+
+### Shared Memory / Multibox state
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd shmem.call --params-json "{\"method\":\"GetNumActivePlayers\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd shmem.call --params-json "{\"method\":\"GetAllMessages\",\"args\":[]}"
+python bridge_cli.py request --hwnd <HWND> --cmd shmem.call --params-json "{\"method\":\"GetAllAccountData\",\"args\":[]}"
+```
+
+## Cross-account command examples (shmem)
+
+Use the curated `shmem.send_command` helper when you want to send commands through the existing Messaging/shared-memory pipeline.
+
+### Example: Send a remote message (generic)
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd shmem.send_command --params-json "{\"receiver_email\":\"alt@example.com\",\"command\":\"TravelToMap\",\"msg_params\":[55,0,1,0]}" --poll
+```
+
+Notes:
+
+- `command` can be enum name (string) or numeric enum value
+- `msg_params` maps to `SharedMessageStruct.Params` (up to 4 numbers)
+- `extra_data` can be provided as a list of strings
+
+With `extra_data`:
+
+```powershell
+python bridge_cli.py request --hwnd <HWND> --cmd shmem.send_command --params-json "{\"receiver_email\":\"alt@example.com\",\"command\":\"LoadSkillTemplate\",\"msg_params\":[0,0,0,0],\"extra_data\":[\"OQhjUxmM5QAA\"]}" --poll
+```
+
+## Async / status model
+
+For queued or shmem-backed operations:
+
+- the bridge returns an immediate response
+- the daemon request id is the tracked operation id
+- poll with `status` or `request --poll`
+
+States typically include:
+
+- `queued`
+- `running`
+- `completed`
+- `failed`
+- `expired`
+
+## What this is useful for (practical)
+
+### AI-assisted scripting
+
+An AI tool (later MCP adapter) can:
+
+- inspect methods on real runtime layers
+- read live state
+- test generated calls against a real client
+- iterate faster with less guesswork
+
+### Multi-client orchestration
+
+One daemon can manage multiple clients and route by `HWND`.
+
+### Stress testing (live)
+
+You can script repeated calls via CLI or a future adapter and collect structured responses/status from real clients.
+
+## Troubleshooting
+
+### `list-clients` is empty
+
+- Ensure daemon is running
+- Ensure the Bridge Client widget is enabled
+- Verify host/port/token match in widget UI
+- Click `Apply Connection Settings`
+
+### Auth token mismatch
+
+- The daemon token and widget token must match exactly
+- If daemon runs without `--token`, token check is effectively disabled
+
+### `client_not_found`
+
+- The target `HWND`/`PID` is not currently connected
+- Run `list-clients` again and use the current value
+
+### `guard_*` errors (e.g., map loading/cinematic)
+
+- These are runtime guard checks from the bridge/action layer
+- Retry when the client is in a valid state
+
+### Generic `.call` returns `repr(...)`
+
+- Some return values are complex native/Python objects
+- Use curated endpoints for stable structured output where available
+- Or call smaller methods that return primitives/lists
+
+## Next steps (recommended)
+
+1. Build an MCP adapter on top of `bridge_daemon.py` control API
+2. Add more curated commands for common workflows (`party.*`, `inventory.*`, `skillbar.*`)
+3. Add `test.*` namespace for stress/repeat/analyze helpers
+4. Add logging/capture tools for automated test runs
+

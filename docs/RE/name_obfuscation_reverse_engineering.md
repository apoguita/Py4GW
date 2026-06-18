# Name Obfuscation Reverse Engineering

## Scope

This document records the current reverse-engineering state of the name-obfuscation feature used by Py4GW.

It covers:

- the native hook architecture
- the packet/timing model
- the current Python test harnesses
- validated behavior
- unresolved name-bearing surfaces
- the current packet candidates and next RE steps

This is the dedicated subsystem reference for name obfuscation. It replaces relying on scattered notes in generic handover files.

## Problem Statement

The goal is to replace visible character names in the live client with configured aliases while still preserving access to the original names for automation and tooling.

The key constraint is that the current implementation works at packet-rewrite time, not by walking every UI surface and mutating already-materialized client state afterward.

That has two immediate consequences:

1. A surface only changes if its backing data is delivered through a packet path we intercept.
2. If names were already loaded before obfuscation was enabled, there is nothing to rewrite until the game replays the relevant packets again, usually after travel/load.

## Files And Layers

### Native C++ implementation

- `Py4GW\include\py_name_obfuscator.h`
- `Py4GW\src\py_name_obfuscator.cpp`

### Python operator/test surfaces

- `test_name_obfuscation_smoke.py`
- `capture_name_surfaces.py`
- `Py4GWCoreLib/PacketSniffer.py`

### Supporting packet hooks

- `Py4GWCoreLib/PacketSniffer.py`
- `docs/RE/packet_sniffers_reference.md`

### What the sniffers already give us

For this subsystem, the sniffers are not opcode-only guess tools.

They already expose:

- raw packet header
- authoritative packet size
- copied packet bytes
- capture tick

Important capability split:

- StoC sniffer:
  - passive capture on all 487 StoC headers
  - uses the live handler table to resolve expected packet size
- CToS sniffer:
  - hooks the higher-level outbound wrapper
  - captures the explicit wrapper size and raw packet bytes

That means packet-identification work for name obfuscation should start from captured payload bytes first, then move to static RE only when the packet body still needs interpretation.

## Current Architecture

### Native hook point

The working native implementation hooks:

- `GW::Packet::StoC::PlayerJoinInstance`

Registration happens in `NameObfuscator::Initialize()` through:

```cpp
GW::StoC::RegisterPacketCallback<GW::Packet::StoC::PlayerJoinInstance>(..., -0x8000)
```

The callback runs early enough to overwrite the inbound packet before downstream client consumers materialize the visible name.

### Core data flow

The current flow is:

1. The game receives `PlayerJoinInstance`.
2. `NameObfuscator::OnPlayerJoinInstance(...)` captures the original player name.
3. The real name is looked up in the alias snapshot.
4. If a mapping exists, the packet name buffer is overwritten in place.
5. The original/display pair is recorded in the observed-player cache.
6. Downstream client systems consume the modified packet.

This is why the implementation must reuse the live packet path. Local-only Python name substitution is not acceptable for this subsystem because it misses real engine consumers and diverges from actual client state.

### Alias model

The native alias store uses snapshot-based lookup:

- `AliasEntry { real, fake }`
- `shared_ptr<const AliasSnapshot>`

That design keeps lookups simple inside the packet callback and avoids mutating the active alias map while a packet is being processed.

### Observed-player cache

The native layer also stores observed name pairs:

- `ObservedPlayer`
- `ObservedRecord`
- `kMaxObservedPlayers = 256`

The purpose of this cache is not obfuscation itself. It exists so Python can still resolve:

- display name -> real name
- real name -> display name

even after the client is already showing obfuscated names.

## Timing And Load Behavior

### Map-ready nuance

The important behavioral finding is that names are hot data delivered during instance loading and player-join replay.

The current `IsMapReady()` logic is:

```cpp
GW::Map::GetIsMapLoaded() &&
!GW::Map::GetIsObserving() &&
instance_type != Loading
```

But the packet callback intentionally does not abort when `IsMapReady()` is false. It only increments diagnostics and continues processing.

That matters because the relevant player-name packets often arrive during the same load window where a strict readiness gate would otherwise suppress the feature completely.

### Why "no change" happened until travel

If obfuscation is enabled after the map has already loaded, the names already cached by the client are not retroactively rebuilt.

So the expected behavior is:

- enable obfuscation
- see no visible change immediately
- travel or otherwise trigger a fresh player-name replay
- observe the feature working on the replayed names

This was validated in live testing. The feature appeared unchanged until the user traveled, after which the aliased names started showing correctly.

### Stale-data risk

There are two distinct stale-data concerns:

1. Client-side stale presentation:
   Existing UI surfaces will keep previously materialized names until their underlying packets are replayed.
2. Observed-cache incompleteness:
   `get_real_name()` can only resolve names that have either:
   - been seen through the observed-player cache, or
   - been configured explicitly in the alias map

So the system is not globally stale in the sense of reading dead pointers, but it can be incomplete if the relevant packet path has not been seen yet in the current session.

## Native Diagnostics

The native implementation exposes these counters:

- `initialized`
- `player_join_hook_registered`
- `enabled`
- `current_map_ready`
- `player_packets_seen`
- `player_packets_empty_name`
- `player_packets_disabled`
- `player_packets_map_not_ready`
- `observed_captures`
- `observed_trylock_skips`
- `alias_hits`

Interpretation:

- `player_packets_seen > 0` confirms the hook is live.
- `player_packets_disabled` rising means names arrived before the feature was enabled.
- `player_packets_map_not_ready` rising during load is not automatically a bug because the callback now continues past this condition.
- `observed_captures > 0` confirms original/display pairs are being recorded.
- `alias_hits > 0` confirms at least one packet matched a configured alias.

Example validated live state from testing:

- `enabled: True`
- `map_ready: True`
- `player_packets_seen: 27`
- `player_packets_disabled: 26`
- `observed_captures: 1`
- `alias_hits: 0`

That pattern is consistent with enabling the feature after most load-time packets had already passed.

## Python Test Surfaces

### 1. Manual smoke harness

`test_name_obfuscation_smoke.py` is the safe manual harness.

Important properties:

- passive on import
- lazy import of `PyNameObfuscator`
- no auto-enable
- no polling loop
- no sleeps

Exported manual actions include:

- `check_import_api()`
- `status()`
- `set_alias(real, fake)`
- `enable()`
- `disable()`
- `dump_aliases()`
- `observed()`
- `diagnostics()`
- `reset_diagnostics()`
- `clear_observed_cache()`

Use this harness to validate that the native module is present and the hook is behaving as expected without introducing extra runtime behavior.

### 2. Unified packet capture tool

`capture_name_surfaces.py` is the consolidated operator-facing capture tool for unresolved name surfaces.

Scenarios:

- `guild`
- `friends`
- `call_target`

Important workflow rule:

- travel-based scenarios must start capture before travel because the relevant names are replayed during load

Scenario intent:

- `guild`: inspect load-time guild-related name-bearing traffic
- `friends`: inspect load-time friend-list related traffic
- `call_target`: inspect the interaction-time path that produces the call-target chat announcement

The tool provides:

- capture baselines
- named markers
- packet dumps since baseline
- packet dumps between markers
- packet dumps around the last marker
- observed-name dumps
- original/display name resolution helpers

## Python Name Accessors

The current Python accessors are implemented in `capture_name_surfaces.py`:

- `get_alias_map()`
- `get_observed_records()`
- `get_real_name(display_name)`
- `get_display_name(real_name)`
- `require_real_name(name)`

Current resolution behavior:

- `get_real_name(display_name)` first searches the observed-player cache
- if not found there, it falls back to reversing the configured alias map
- `require_real_name(name)` returns the resolved real name if known, otherwise the input unchanged

This is the current answer to the requirement that the game can show obfuscated names while automation still needs the real character name for native/game calls.

Limitation:

These accessors are only as complete as the observed cache and alias map. They do not magically recover names for surfaces that never passed through the current capture path.

## Surfaces Confirmed Working

The validated working path is the instance player-name replay reached through `PlayerJoinInstance`.

Observed behavior:

- aliasing works after travel/load replays the names
- original/display pairs are captured in the observed cache
- Python can resolve names from the observed cache after replay

## Surfaces Still Missing

The following surfaces are still not fully covered:

- guild roster
- guild name and guild tag in the guild window
- guild name and guild tag in the player name tag
- friends roster entries for other players
- call-target chat announcement

Important nuance:

- self in friends appears okay
- other friend entries do not
- guild and friends population happen at load
- call-target is interaction-time and should be isolated separately from load noise

This strongly suggests not all visible name surfaces are driven by the `PlayerJoinInstance` path.

## Packet Candidates And Current Observations

### Packet families already treated as interesting

For the current capture workflow, these StoC packets are treated as primary candidates.

#### Guild scenario

- `0x0031` `CHARACTER_UPDATE_NAME`
- `0x0118` `GUILD_PLAYER_ROLE`
- `0x0120` `GUILD_ALLIANCE_INFO`
- `0x0121` `GUILD_GENERAL_INFO`
- `0x0127` `GUILD_PLAYER_INFO`
- `0x0128` `GUILD_PLAYER_REMOVE`
- `0x012A` `GUILD_PLAYER_CHANGE_COMPLETE`
- `0x012B` `GUILD_CHANGE_PLAYER_CONTEXT`
- `0x012C` `GUILD_CHANGE_PLAYER_STATUS`
- `0x012D` `GUILD_CHANGE_PLAYER_TYPE`
- `0x017D` `INSTANCE_LOAD_PLAYER_NAME`

#### Friends scenario

- `0x000E` `FRIENDLIST_MESSAGE`
- `0x0031` `CHARACTER_UPDATE_NAME`
- `0x005D` `CHAT_MESSAGE_CORE`
- `0x005E` `CHAT_MESSAGE_SERVER`
- `0x0060` `CHAT_MESSAGE_GLOBAL`
- `0x0061` `CHAT_MESSAGE_LOCAL`
- `0x017D` `INSTANCE_LOAD_PLAYER_NAME`

#### Call-target scenario

- `0x0034` `AGENT_PINGED`
- `0x005D` `CHAT_MESSAGE_CORE`
- `0x005E` `CHAT_MESSAGE_SERVER`
- `0x0060` `CHAT_MESSAGE_GLOBAL`
- `0x0061` `CHAT_MESSAGE_LOCAL`
- `0x017D` `INSTANCE_LOAD_PLAYER_NAME`

### Additional inferred or partially identified opcodes

The recent trace work also established or labeled:

- `0x011C` `GUILD_CONTROL_011C`
- `0x012E` `GUILD_CONTROL_012E`
- `0x016E` `ACCOUNT_UNLOCK_STREAM_FINALIZE`
- `0x016F` `ACCOUNT_UNLOCK_HERO_BEGIN`
- `0x0170` `ACCOUNT_UNLOCK_HERO_END`
- `0x0171` `ACCOUNT_UNLOCKED_HERO`

`0x0171` is backed by Ghidra/decompile work and corresponds to the account unlocked-hero path, not the missing name-obfuscation surfaces themselves.

The `0x016E/0x016F/0x0170/0x0171` burst is therefore load noise that should be filtered out when analyzing guild/friends traces unless a later dependency is discovered.

### Practical conclusion from traces so far

Repeated identical travel captures have diminishing value if they are collected with the same interaction pattern and without new decoding information.

The current bottleneck is not "more raw travel logs" by itself. It is:

1. decoding more of the relevant packet bodies
2. identifying which packets actually carry names, guild tags, or friend-entry payloads
3. correlating those packets with the specific missing UI surfaces

## Current RE Model

The working model for this subsystem is:

- `PlayerJoinInstance` covers the general instance-load character-name replay.
- Some UI surfaces reuse that replayed name directly and already work.
- Guild/friends/call-target missing surfaces likely use separate packet payloads, separate decode paths, or separate UI-side cached structures.
- Some of those structures may carry real names, encoded names, guild tags, or preformatted composite strings that bypass the currently hooked packet.

That is why simply "adding more sanity checks" to the old implementation broke usability: the feature depends on intercepting the correct live packet path at the correct time window, not on post hoc cleanup alone.

## 2026-06-16 Static RE Findings

Recent WASM-side static RE materially narrowed the missing-surface problem.

### Friends are a separate auth-side subsystem

The friend roster is not populated from `PlayerJoinInstance`.

The current auth-side flow is:

1. `0x000E FRIENDLIST_MESSAGE` reaches auth handlers such as:
   - `Gc::RecvAuthSrv_FriendListData`
   - `Gc::RecvAuthSrv_FriendNotify`
   - `Gc::RecvAuthSrv_FriendLocationUpdated`
2. Those handlers normalize the raw packet into auth events posted with:
   - event `0x26` for friend-list data
   - event `0x2C` for friend notify
   - event `0x28` for friend location update
3. `Friend::OnEventNetMsg(...)` consumes those events.
4. `Friend::CFriendTable` stores the friend entry.
5. The friends UI consumes `FriendData` from that table.

Important consequence:

- name obfuscation on `PlayerJoinInstance` cannot be sufficient for friend-list entries belonging to other players because the friend roster has its own storage and update path.

### Friend entries store two distinct names

`Friend::CFriendTable::Add(...)` takes:

- category
- status
- guid
- friend name
- character name

It stores both name strings independently.

Observed behavior from the add path:

- friend name is copied first
- character name is copied separately
- if the incoming character name is empty, the code falls back to the friend name

That directly matches the unresolved symptom where some friend surfaces remain unaliased even though general instance names are already covered.

### Friends UI consumes both names, not just one

`IUi::Game::FriendsList::CFriend::OnFrameMsgCreate(...)` uses the friend entry in a way that confirms the UI is name-aware beyond a single field:

- it reads category and status to choose the row type
- it compares friend name vs character name
- when they differ, it renders a composite text path rather than a single raw name
- it also appends mission/location text for relevant states

So for friends, the unresolved issue is not just "missing packet replay." The UI is explicitly built from friend-table data that already has two separate name-bearing fields.

### Guild member and guild identity data are also separate from `PlayerJoinInstance`

Guild member population is handled by dedicated guild-client code, not by the generic instance-load player replay.

Confirmed handlers:

- `GuildCliOnMemberAdd(...)`
- `GuildCliOnMemberUpdateCharName(...)`
- `GuildCliOnMemberUpdateRank(...)`
- `GuildCliOnMemberUpdateFinalize(...)`
- `GuildCliOnGuildDataFull(...)`
- `GuildCliOnGuildDataAlly(...)`

What this establishes:

- guild member rows are built from `GuildClient::CMemberTable`
- guild identity surfaces are built from `GuildClient::CGuildTable`
- guild name/tag UI cannot be assumed to reuse the same field that drives ordinary instance player names

### Guild member rows carry multiple name-bearing fields

`GuildCliOnMemberAdd(...)` passes four separate wide-string inputs into `GuildClient::CMemberTable::Add(...)`.

Confirmed behavior:

- the packet field at `+0x2C` falls back to the string at `+0x04` if empty
- `CMemberTable::Add(...)` stores four distinct string slots in the member object
- later member updates are staged through a temporary `memberUpdate` buffer at `context + 0x3B8`
- `GuildCliOnMemberUpdateFinalize(...)` applies staged bitfield-controlled updates into the member object and then broadcasts UI message `0x100000DA`

This means the guild roster problem is not a single missing string rewrite. The roster has its own staged-update model with multiple candidate name fields.

### Guild name and tag come from the guild table

The authoritative accessors are:

- `GuildCliGetGuildName(guild_id)` -> guild object `+0x30`
- `GuildCliGetGuildTag(guild_id)` -> guild object `+0x80`

`GuildCliOnGuildDataFull(...)` and `GuildCliOnGuildDataAlly(...)` populate those guild objects through `GuildClient::CGuildTable::AddFull(...)` and `AddAlly(...)`.

Practical implication:

- unresolved guild window and overhead guild tag/name surfaces are most likely blocked on guild-table population or later guild UI formatting, not on `PlayerJoinInstance`

### 2026-06-17 guild packet findings narrow the remaining gap

The latest focused guild captures sharpened the packet-side conclusion.

Observed during a real load window:

- `0x0121` `GUILD_GENERAL_INFO`
- `0x0118` `GUILD_PLAYER_ROLE`
- `0x017D` `INSTANCE_LOAD_PLAYER_NAME`

Not observed in the same load window:

- `0x0127` `GUILD_PLAYER_INFO`
- `0x0128` `GUILD_PLAYER_REMOVE`
- `0x012A`
- `0x012B`
- `0x012C`
- `0x012D`
- `0x0031`

Observed when only toggling the guild window locally without travel:

- no guild-family StoC packets at all
- no relevant CToS packets at all
- only background movement/tick traffic

What this means:

- map load can carry general instance-name replay and some guild identity/bootstrap data
- local guild-window visibility toggles are client-only and do not trigger a server replay
- the missing guild roster names are not currently explained by a simple "open guild window and watch packets" model
- the unresolved gap is now best modeled as either:
  - guild member-table population that is gated differently than the tested load windows, or
  - roster/UI formatting that consumes already-cached member data without a fresh packet burst in the observed window

So the packet evidence now supports a tighter guild-side statement:

- `PlayerJoinInstance` is not the missing guild roster source
- `CGuildTable` identity/bootstrap traffic exists at load
- the next high-value RE target is the `CMemberTable` write/read path, not more undifferentiated packet capture

### Concrete runtime guild storage already exposed by GWCA

The local native layer already gives a concrete model for the runtime guild storage that the client keeps after packet handling.

Relevant structs:

- `GWCA\\Include\\GWCA\\Context\\GuildContext.h`
- `GWCA\\Include\\GWCA\\GameEntities\\Guild.h`
- `GWCA\\Source\\GuildMgr.cpp`

Important runtime anchors:

- `GameContext + 0x3C` -> `GuildContext*`
- `GuildContext + 0x02F8` -> `GuildArray guilds`
- `GuildContext + 0x0358` -> `GuildRoster player_roster`
- UI message `0x100000DA` / `kGuildMemberUpdated`

Concrete `GuildPlayer` layout from GWCA:

- `+0x04` -> `name_ptr`
- `+0x08` -> `invited_name[20]`
- `+0x30` -> `current_name[20]`
- `+0x58` -> `inviter_name[20]`
- `+0x84` -> `promoter_name[20]`
- `+0xDC` -> `offline`
- `+0xE0` -> `member_type`
- `+0xE4` -> `status`

Concrete `Guild` layout from GWCA:

- `+0x24` -> `index`
- `+0x2C` -> `features`
- `+0x30` -> `name[32]`
- `+0x80` -> `tag[8]`

What this changes:

- the roster is not an abstract RE target anymore; there is a concrete live `player_roster` array to reason about
- the guild identity table is not abstract either; `guilds` already exposes `name` and `tag` storage
- the member update path can now be framed as:
  - packet handler populates or updates a `GuildPlayer`
  - UI message `kGuildMemberUpdated` notifies consumers
  - roster UI reads one or more of the concrete string fields above

This gives two realistic narrow hook strategies for the guild surface:

1. rewrite at member-table write time
2. rewrite at roster/UI read time using the already-materialized `GuildPlayer`

The next guild RE pass should determine which `GuildPlayer` field the roster renderer prefers:

- `name_ptr`
- `invited_name`
- `current_name`
- another formatted source derived from those fields

### Call-target chat text goes through the comm-finalize pipeline

The visible call-target announcement path is not just `AGENT_PINGED`.

Confirmed pieces:

- `CharCliOnAssistRequest(player_id, agent_id)` forwards to `PartyCliPlayerAssist(...)`
- `CharCliOnCommData(wchar_t const*)` accumulates coded chat text in world context state
- `CharCliOnCommFinalizeChatPlayer(player_id, comm_type)` formats player-based chat output and sends UI message `0x10000082`
- `CharCliOnCommFinalizeChatAgent(agent_id, text, comm_type)` sends UI message `0x10000080`
- `CharCliOnCommFinalizeChatExternal(name, text, comm_type)` sends UI message `0x10000081`

Critical detail from `CharCliOnCommFinalizeChatPlayer(...)`:

- when it needs a name, it can read the player table entry directly
- it pulls a name field from the player record rather than relying solely on the already-rendered UI
- it runs that name through `TextEncodeAffixNames(...)`
- it may append profession/category text before dispatch

So the missing call-target alias is now best modeled as a comm/chat consumer problem:

- either the relevant player-table name is still real
- or the coded comm payload itself carries real text
- or the finalize path formats a name source that bypasses the currently hooked packet

### What the current static RE changes

Before this pass, the working statement was "guild/friends/call-target probably use separate payloads or caches."

That is now stronger:

- friends definitively use an auth event pipeline plus `Friend::CFriendTable`
- guild roster definitively uses `GuildClient::CMemberTable`
- guild name/tag definitively use `GuildClient::CGuildTable`
- call-target chat definitively goes through the comm-finalize/UI-message path

The remaining work is now about tying raw packet opcodes to those named consumers and deciding the narrowest hook or rewrite point for each unresolved surface.

## Recommended Test Method

Use one consolidated workflow:

1. Configure aliases.
2. Enable obfuscation.
3. Start `capture_name_surfaces.py`.
4. Select the scenario being investigated.
5. Start capture before travel for load-time scenarios.
6. Mark `travel_start`.
7. Travel.
8. Mark arrival and load completion when the replay finishes.
9. Dump the phase window or the window around the last marker.
10. Inspect `get_observed_records()` alongside the packet dump.

For `call_target`:

1. Travel only if a fresh replay is needed.
2. Reset baseline after load settles.
3. Perform exactly one manual call-target action.
4. Mark the action completion.
5. Dump around the last marker.

This keeps the capture method stable while isolating the only part of the sequence that differs by surface.

## Next RE Steps

### 1. Decode packet bodies with subsystem-aware priorities

The next high-value step is to decode the payload structure for:

- `0x000E`
- `0x0031`
- `0x0034`
- `0x0118`
- `0x011C`
- `0x0120`
- `0x0121`
- `0x0127`
- `0x012A`
- `0x012B`
- `0x012C`
- `0x012D`
- `0x012E`
- `0x017D`

But the priority is no longer flat.

Friends first:

- split `0x000E FRIENDLIST_MESSAGE` into the distinct auth message layouts that feed:
  - friend-list data
  - friend notify
  - friend location update
- identify the raw fields that become:
  - friend id or slot
  - friend status
  - guid
  - friend name
  - character name
  - location data

Guild next:

- decode the guild member and guild identity payloads that feed:
  - `GuildCliOnMemberAdd`
  - `GuildCliOnMemberUpdateCharName`
  - `GuildCliOnMemberUpdateFinalize`
  - `GuildCliOnGuildDataFull`
  - `GuildCliOnGuildDataAlly`

Call-target after that:

- map which incoming chat or notification packets lead into:
  - `CharCliOnCommData`
  - `CharCliOnCommFinalizeChatPlayer`
  - `CharCliOnCommFinalizeChatAgent`

Across those packet families, we still need to know which fields are:

- account name
- character name
- guild name
- guild tag
- agent id
- player number
- friend slot/index

Use the sniffers aggressively here:

- do not stop at opcode counts
- inspect full raw hex
- inspect `u32` words across stable repeated captures
- inspect UTF-16 slices for inline names, guild names, and guild tags

### 2. Correlate packets to specific surfaces

Use controlled runs where the scenario is known in advance:

- travel with guild tab already open
- travel with friends tab expected to populate on load
- one isolated call-target action after load

Then compare the packets around the marker with the exact missing surface.

### 3. Reverse missing consumers in native code only where packet decode stops helping

If packet decoding alone is insufficient, RE the native consumers for:

- guild roster population
- friend-list population
- call-target chat message generation
- overhead name-tag guild-tag composition

The current named consumer targets are now:

- `Friend::OnEventNetMsg(...)`
- `IUi::Game::FriendsList::*`
- `GuildCliOnMember*`
- `GuildCliOnGuildData*`
- `GuildCliGetGuildName`
- `GuildCliGetGuildTag`
- `CharCliOnCommFinalizeChatPlayer`

The question is no longer only "which opcode exists," but "which named consumer turns that payload into visible text."

Guild-first concrete target:

- trace `GuildCliOnMemberAdd(...)` into `GuildClient::CMemberTable::Add(...)`
- trace `GuildCliOnMemberUpdateFinalize(...)` into the staged member-update apply path
- identify which member-object string slot the roster renderer actually consumes
- only after that decide whether the correct hook point is:
  - packet-to-member-table write time, or
  - member-table/UI read time

### 4. Extend the original-name cache only after the source path is known

Do not add speculative local name tables for unresolved surfaces.

Instead:

- identify the real source packet or native structure
- capture the real/display pair at that point
- feed the existing observed-name accessor model

That preserves a single consistent source of truth for original-name resolution.

## Current Status Summary

Working:

- native packet rewrite on `PlayerJoinInstance`
- aliasing after travel/load replay
- observed original/display cache
- Python original-name accessors for observed names
- consolidated capture tool for unresolved surfaces

Not yet solved:

- guild roster and guild-tag/name surfaces
- friend-list entries for other players
- call-target announced name path
- full raw packet-body definitions for the relevant missing-surface candidates
- the narrowest safe hook point for each of the three separate subsystems:
  - friends auth/friend-table path
  - guild member or guild-table path
  - comm-finalize chat path

Latest guild-specific conclusion:

- guild identity/bootstrap packet traffic has been confirmed at load
- guild roster member packets have still not been confirmed in the tested windows
- toggling the guild window locally does not generate guild network activity
- the next pass should start from the guild member-table consumer path in WASM/native code

That is the current baseline for future name-obfuscation RE work.

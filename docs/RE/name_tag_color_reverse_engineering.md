# Agent / Item Name-Tag Color Reverse Engineering

> **STATUS: SHIPPED & VALIDATED IN-CLIENT.** Agent name-tag recoloring works via
> the `PyAgentTagColor` native module (resolver detour on `FUN_007f02e0`).
> Per-agent and per-allegiance overrides recolor tags natively; the RE color
> table validated PASS across all living agents. Item-rarity recolor (markup
> path, §4) remains future work. Feature/usage guide: `docs/agent_name_tag_color.md`.

## Scope

This document records the reverse-engineering state of **how Guild Wars colors overhead name tags** (players, NPCs, enemies) and **ground-item labels**, and the concrete native interception point for recoloring them per-agent from Py4GW.

It is the dedicated subsystem reference for name-tag coloring. It is a sibling to `name_obfuscation_reverse_engineering.md`: the obfuscator rewrites the *text* of names at packet time; this subsystem changes the *color* of name tags at render-resolve time.

RE was performed WASM-first on `/Gw.wasm` (named symbols) and mapped to `/Gw.exe (06-14)` (the injected build). See `reverse_engineering_reference.md` → "WASM-First Workflow".

## Problem statement

We want to display agent/enemy/item name tags in arbitrary colors, using the game's **own** rendering — no ImGui/overlay reimplementation, no packet faking. That means finding where the engine decides a tag's color and overriding it in place.

The key finding is that Guild Wars uses **two different coloring mechanisms** depending on tag type, so there is no single lever:

| Tag type | Mechanism | Where color is decided |
|----------|-----------|------------------------|
| **Agent** (player / NPC / enemy) | **Direct `Color4b`** passed as an argument down the render chain | `CCharAgent::GetConsiderColor` resolver |
| **Ground item** | **In-band `<c=@…>` markup** embedded in the coded item name | `ItemCliGetCodedName` / `CNameComposer` |

## Executive summary

- **Agent tags are the easy, high-value win.** Color is resolved game-side by a single function from the agent's allegiance/team/state and handed down as a raw `Color4b`. Detour that resolver, overwrite the output for the agents you care about, done. One hook covers players, NPCs, and enemies — and the target/consider ring, which shares the resolver.
- **Item rarity color is markup**, not a color argument, so recoloring item rarity is a separate (harder) job that means intercepting the coded-name string.
- The engine's color format is **ARGB `0xAARRGGBB`** end-to-end on the agent path (pure opaque red = `0xFFFF0000`). No channel swap on that path.

---

## 1. Agent name-tag pipeline

Color flows top-down as a direct `Color4b` argument (WASM symbols shown; EXE map in §5):

```
CCharAgent::GetConsiderColor        ← THE resolver: reads allegiance/team/state, writes the ARGB
  → CCharAgent::GetTextData         (packs the Color4b + coded name into a TextData)
  → CBaseAgent::NameUpdate          (builds UiMsgAgentName, sends FrameMsgSendRegistered
                                       0x10000019 kShowAgentNameTag / 0x1000001b kSetAgentNameTagAttribs)
  → IUi::Game::OnAgentNameUpdate    (GameViewFrameProc dispatch)
  → CName::OnUpdate                 (reads Color4b from msg+0x14)
  → CtlTextMlSetColor               (applies it to the tag frame; FrameMsg 0x5e)
```

`CBaseAgent::NameUpdate` is driven by `Advance`, `Hover`, `SelectPrimary/Secondary`, `CCharAgent::ApplyTeam`, and `UpdateStatusDeath` — i.e. the color is re-resolved on essentially every meaningful agent state change. **This is why a static one-shot `SendUIMessage` recolor does not stick: the game overwrites it on the next update. A durable recolor must hook the resolver, which is the source of truth the game itself re-reads.**

The GWCA-documented `AgentNameTagInfo` struct is the message payload here: `text_color` (ARGB) lives at `+0x14`, delivered via `kShowAgentNameTag (0x10000019)` / `kSetAgentNameTagAttribs (0x1000001b)`.

---

## 2. The resolver — detour target and ABI (CLOSED OUT, instruction-verified on `/Gw.exe (06-14)`)

> **CORRECTION (validated in-client):** the **resolver `FUN_007f02e0` is the hook target**, NOT the wrapper. The game's name-tag path (`CCharAgent::GetTextData`) and the consider ring call the resolver **directly** (thiscall, with the view pointer); they do **not** go through the id-addressable wrapper `FUN_007d9cf0`. Hooking the wrapper compiles and lets `read_consider_color` work (we call the wrapper ourselves), but recolors **nothing visually** — the game bypasses it. The wrapper is still the right **anchor**: its body CALLs `ManagerFindChar` at `+0x07` and the resolver at `+0x31`, so we derive both from it. Hook the resolver; recover the id from `view+0x2C`.

### The wrapper (anchor + reads only): `AvCharGetConsiderColor` = `FUN_007d9cf0` (`0x007d9cf0`)

Agent-id-addressable C wrapper. Use it to derive addresses and to service `read_consider_color`, **but do not hook it** (not on the render path).

```c
Color4b* __cdecl AvCharGetConsiderColor(
    Color4b* out,      // [ebp+8]  hidden struct-return buffer; the ARGB u32 is written here
    uint     agentId,  // [ebp+0xc]
    int      flag);    // [ebp+0x10]  text vs non-text color variant
// returns EAX = out ; plain cdecl (caller cleans)
```

Internally: `ManagerFindChar(agentId)` (= `FUN_007fc920`, bounds-checked `DAT_00bf35c4[id]`, validates the `0xdb` living type tag) → `GetConsiderColor`. Matches WASM `AvCharGetConsiderColor` `ram:80bbaf46`; the `PUSH 0x1e9` "invalid agent" assert (`…\Gw\AgentView\AvApi.c`) is a 1:1 WASM↔EXE match.

### Hook target: the resolver `GetConsiderColor` = `FUN_007f02e0` (`0x007f02e0`)

```c
Color4b* __thiscall GetConsiderColor(
    CCharAgent* this,      // ECX  agent-view object
    Color4b*    outColor,  // [esp+4]  the ARGB u32 is written *through this pointer*
    int         flag);     // [esp+8]
// returns EAX = outColor ; RET 8 (callee-cleanup, 2 stack args)
```

**Critical ABI facts (both functions):**
- The resolved color is **written through the `out` pointer**, NOT returned in EAX as a value. EAX just returns the same `out` pointer.
- To recolor: **call the original first, then overwrite `*(uint32_t*)out`**, then return `out`. Overwriting after the original ran is robust regardless of which internal branch fired.
- If hooking the `__thiscall` resolver directly, recover the id from the view object: **`agentId = *(uint32_t*)(this + 0x2C)`** (the view stores its agent id at `+0x2C`; the base ctor `FUN_007e5af0` sets `view+0x2C = agentId`). Avoid `view+0xF4` — that is a derived agent *handle*, not the plain id. And preserve the `RET 8` cleanup.

### Detour recipe (verbatim — implemented in `py_agent_tag_color.cpp`)

Hook the resolver `FUN_007f02e0` (thiscall) via a `__fastcall` detour so a free
function matches the ABI: `this`→ECX (fastcall arg 1), unused EDX (arg 2), then
the two stack args (`out`, `flag`). RET 8 ↔ fastcall cleans 8.

```c
using ResolverFn = uint32_t* (__fastcall*)(void* view, void* edx, uint32_t* out, int flag);
ResolverFn Original;  // MinHook trampoline

uint32_t* __fastcall Detour_GetConsiderColor(void* view, void* edx, uint32_t* out, int flag) {
    Original(view, edx, out, flag);            // let the game resolve the default
    if (out && view) {
        uint32_t agentId = *(uint32_t*)((uintptr_t)view + 0x2C);  // id at view+0x2C
        uint32_t argb;
        if (LookupRule(agentId, &argb))        // per-agent, then per-allegiance
            *out = argb;                       // ARGB 0xAARRGGBB, e.g. 0xFFFF0000 red
    }
    return out;
}
```

Resolution (build-portable): `FindAssertion("AvApi.cpp","agent",0x1e9)` →
`ToFunctionStart` gives the wrapper; validate `E8` at `+0x07`/`+0x31`, then
`FunctionFromNearCall(wrapper+0x31)` = resolver (hook this),
`FunctionFromNearCall(wrapper+0x07)` = `ManagerFindChar` (id→view for reads).

---

## 3. Color constants and selector fields (the game's defaults)

`GetConsiderColor` picks the ARGB from the `CCharAgent` view object fields:

| View field | Meaning |
|------------|---------|
| `+0x1B5` (byte) | allegiance / relation (`ECharRelation`) — primary selector |
| `+0x15C` (byte flags) | bit `0x08` = dead/dim gate (forces gray / 75% dim); bit `0x04` = self / your-party |
| `+0x184` (dword) | owning player id (nonzero ⇒ player-controlled ⇒ blue/green family) |
| `+0x108` (ptr) | team data; byte `+5` = team-color palette index into `ConstGetColor` |
| `+0x2C` (dword) | agent id (recovered in the resolver detour) |

Resulting default colors (**ARGB `0xAARRGGBB`**):

| ARGB | Category | Condition |
|------|----------|-----------|
| `0xFFFF0000` red | **Enemy/Foe** | allegiance `+0x1B5 == 3` |
| `0xFFA0FF00` yellow-green | **NPC minipet / special** | allegiance `== 6` |
| `0xFF00FF00` green | **Ally/friendly** | allegiance 1/2/4/5 |
| `0xFF40FF40` bright green | **Self / your party** (outpost) | player-owned, `+0x15C & 4` |
| `0xFF6060FF` periwinkle | **Party member** | player-owned, party size > 1 |
| `0xFF9BBEFF` pale blue | **Other player** (non-party) | player-owned, otherwise |
| `0xFFA0A0A0` gray | **Default / dead / dimmed** | `+0x15C & 8`, or mission team>1 & enemy |
| `ConstGetColor(idx)` | **Team color** (PvP/mission) | map flag `0x40000`; idx = `*(this+0x108)+5`; dimmed ×0xC0/256 if `+0x15C & 8` |

Allegiance byte maps to `Py4GWCoreLib.enums_src.GameData_enums.Allegiance`: `1=Ally, 2=Neutral, 3=Enemy, 4=SpiritPet, 5=Minion, 6=NpcMinipet`.

### Color4b in-memory order

The u32 is the literal integer `0xAARRGGBB`. In little-endian memory the bytes are `[B, G, R, A]` (byte0=B … byte3=A), proven by the dead/dim alpha-scaling code scaling bytes 0/1/2 and leaving byte3 (alpha). No channel swap occurs anywhere on the tag path (`GetTextData` copies verbatim; `CtlTextMlSetColor` consumes the same u32). **A Python caller supplies the plain `0xAARRGGBB` integer** (opaque red = `0xFFFF0000`).

---

## 4. Item ground labels — rarity color is markup

`CItemAgent::GetTextData` (WASM `80b20fb6`) passes only an **ownership** `Color4b` (`0x00000000` if reserved to you, `0xFF808080` dim gray if reserved to another player). The **rarity** color (white/blue/purple/gold/green) is NOT a color argument here — it is embedded as `<c=@…>` markup inside the coded name returned by `ItemCliGetCodedName(itemId, 0xFF/0xFE, 0)`.

Name composition uses `ItemCommon::CNameComposer` (`Compose` `80a9d32f`), which stores an `EColor` at composer `+0x30` and emits it through the encoded-string system via `TextEncodeCat`. So recoloring item rarity means intercepting the coded-name/markup — a separate effort from the agent resolver. (The `IsBlue` check keying off `single_item_name[0] == 0xA3F` is a leading color-control wchar of exactly this kind.)

This path is **not yet fully RE'd**: the specific rarity→`EColor` mapping inside `ItemCliGetCodedName` was not decompiled. It is out of scope for the agent-tag hook and tracked in "Open questions".

---

## 5. Markup color system (reference — for items and any label text)

`<c=#RRGGBB>…</c>` / `<c=@Name>…</c>` is in-band literal text parsed at render time by `CtlTextMl` (source `P:\Code\Engine\Controls\CtlTextMl.cpp`). It is NOT a dedicated `0x01xx` encoded-stream word; the `0x0108/0x0107/0x0001/0x0002` wrapper only carries the literal text that *contains* the markup.

- Color-arg parser `CtlTextMl::ConvertParamUnsigned` = WASM `80dae0c0` = **EXE `FUN_00609600`**. Dispatch on first value char: `#` → 6 hex `RRGGBB`, alpha forced `0xFF`; `0x…` → raw ARGB (allows custom alpha); `@Name` → named-color table lookup; decimal → plain uint.
- `<c` is tag id **7** in the tag table (`005a8390`); open flag `0x40000000`, close `0xC0000000`.
- Named-color table = WASM `ram:005a8370` = **EXE `0x00bef348`** (18 entries, byte-identical WASM/EXE):

| `@`-name | ARGB | | `@`-name | ARGB |
|----------|------|---|----------|------|
| `@ItemCommon` | `0xFFFFFFFF` white | | `@ItemUnique` | `0xFF00FF00` green |
| `@ItemUncommon` | `0xFFB38AEC` violet | | `@ItemUniquePvp` | `0xFFED1C24` red |
| `@ItemRare` | `0xFFFFD24F` gold | | `@ItemDull` | `0xFFA0A0A0` gray |
| `@ItemEnhance` | `0xFFA0F5F8` cyan | | `@Warning` | `0xFFED0002` red |
| `@Quest` | `0xFF00FF00` green | | `@Label` | `0xFFFFEAB8` cream |

- `CtlTextMlSetColor` (the external "set whole control base color" API) sends FrameMsg `0x5e`.

---

## 6. EXE ↔ WASM address map (`/Gw.exe (06-14)`)

| Item | Gw.wasm | Gw.exe (06-14) | Status |
|------|---------|----------------|--------|
| `GetConsiderColor` resolver — **HOOK TARGET** | `ram:80b51f32` | **`FUN_007f02e0`** | verified + hooked |
| `AvCharGetConsiderColor(out,id,flag)` — anchor + reads only | `ram:80bbaf46` | **`FUN_007d9cf0`** | verified |
| `ManagerFindChar(id)` | — | `FUN_007fc920` | verified |
| `CCharAgent::GetTextData` | `ram:80b7faa7` | `FUN_007f0620` | verified |
| `CBaseAgent::NameUpdate` | `ram:80a4afb4` | not pinned | — |
| `CName::OnUpdate` (reads msg+0x14) | `ram:812a47ab` | not pinned | — |
| Markup color parser `ConvertParamUnsigned` | `ram:80dae0c0` | **`FUN_00609600`** | verified |
| Named-color table | `ram:005a8370` | **`0x00bef348`** | verified |
| `CItemAgent::GetTextData` | `ram:80b20fb6` | not pinned | — |

---

## 7. Native module `PyAgentTagColor` (IMPLEMENTED)

Built as `Py4GW\include\py_agent_tag_color.h` + `Py4GW\src\py_agent_tag_color.cpp`, wired into `Py4GW::Initialize/Terminate`. It follows the obfuscator template — a self-contained module owning its hook, a snapshot-based rule store, and a passive Python control surface — but the hook is a **function detour** (MinHook via `GW::HookBase`, as in `py_ui.h` `UIManagerTitleHook`) on the **resolver `FUN_007f02e0`** (thiscall, emulated `__fastcall`), not a packet callback. Resolution is anchored on the wrapper's `"agent"` assertion (§2). Build/deploy: RelWithDebInfo → repo-root `Py4GW.dll` → re-inject.

Embedded module `PyAgentTagColor`:

| Function | Purpose |
|----------|---------|
| `enable()` / `disable()` / `is_enabled()` | master gate (detour stays installed; gate short-circuits it) |
| `set_agent_color(agent_id, argb)` / `remove_agent_color(agent_id)` | per-agent override (highest precedence) |
| `set_allegiance_color(allegiance, argb)` / `remove_allegiance_color(allegiance)` | per-category override (`Allegiance` 1–6) |
| `clear_rules()` | drop all overrides |
| `get_agent_rules()` / `get_allegiance_rules()` | inspect current rule maps |
| `read_consider_color(agent_id)` | **read-only**: `ManagerFindChar(id)`→view (null-guards non-living), then the resolver **trampoline** (game default, unaffected by overrides) → ARGB. Works even when disabled |
| `is_hook_installed()` | true if the resolver detour resolved + installed at DLL init |
| `get_diagnostics()` / `reset_diagnostics()` | counters: `hook_installed`, `resolver_calls_seen`, `agent_rule_hits`, `allegiance_rule_hits`, `last_agent_id`, `last_color` |

**Rule precedence:** per-agent → per-allegiance → game default. Colors are ARGB `0xAARRGGBB`. The detour must run the original first, then apply the highest-precedence matching rule to `*out`.

---

## 8. Functional tests

The harness lives at **`tests/name_tag_color/name_tag_color_test.py`** (folder README alongside it), in the UI_RE in-client style — passive except on button clicks, per-frame `main()`, crash-safe logging to `results.txt` / `log.txt`. It covers both jobs in one window:

- **Validation** — enumerates visible agents via the `Agent`/`AgentArray` API, computes the **expected** default color from §3, and (via `PyAgentTagColor.read_consider_color`) reads the game's **actual** computed color, reporting PASS/FAIL/UNKNOWN per agent. This verifies the RE color table against the live client.
- **Overrides** — per-agent (`set_agent_color`) and per-allegiance (`set_allegiance_color`) controls, `enable`/`disable`, `clear_rules`, plus quick actions (Enemies→magenta, Allies→cyan) and a live diagnostics line. This exercises the resolver detour end-to-end.

Run it on a loaded map the same way the `UI_RE/` harnesses are loaded (requires the current rebuilt DLL injected). Type stub: `stubs/PyAgentTagColor.pyi`.

---

## 9. Confidence and open questions

**Confirmed in-client (SHIPPED):** the resolver `FUN_007f02e0` is the correct hook (the wrapper `FUN_007d9cf0` is bypassed by the game — hooking it recolored nothing); the `__fastcall`-emulated thiscall detour + `view+0x2C` id recovery + `*out = argb` recolor tags natively; `read_consider_color` validated the §3 color table PASS across all living agents; ARGB `0xAARRGGBB` is correct (magenta/cyan overrides render as expected); non-living agents must be guarded (they trip the `charAgent` assert and crash).

**High confidence (static):** the agent pipeline and its addresses; the resolver ABI (instruction-verified on 06-14); the color constants; agent-tag color is a direct arg while item rarity is markup; the markup color parser + named-color table (byte-identical WASM/EXE).

**Medium:** exact bit semantics of `+0x15C` (0x08 dead/dim, 0x04 self/party — inferred from use, not a symbol); the `flag` int's per-call value on the name-tag path (irrelevant to an unconditional `*out` override); EXE addresses for `NameUpdate` / `CName::OnUpdate` / `CItemAgent::GetTextData` (not pinned — not needed for the resolver hook).

**Open:**
- Item rarity recolor: decompile `ItemCliGetCodedName` / `CNameComposer` to get the rarity→`EColor` switch, then decide between intercepting the coded name vs. the markup.
- The `ConstGetColor` team-color palette (`DAT_ram_002798ec`, 8 entries) was not dumped — needed only for exact PvP/mission team-color replication.

## 10. Next steps

1. Build `PyAgentTagColor` per §7 (detour `FUN_007d9cf0`, obfuscator-pattern rule store + Python API).
2. Run `test_name_tag_color_mapping.py` in-client to confirm the §3 table matches live tags via `read_consider_color`.
3. Run `test_name_tag_color_smoke.py` to validate override behavior (per-agent, then per-allegiance).
4. Only if item rarity recolor is wanted, open the §4/§9 item-markup work as a separate pass.

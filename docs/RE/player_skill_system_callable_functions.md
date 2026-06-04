# Player Skill System — Callable Functions Reference

Date: 2026-05-30
Source: `/Gw.exe(Symbols)` and `/Gw.wasm` via Ghidra MCP

## Overview

This document catalogs the native functions you can call to:
1. Query skill state (recharge, pending, availability)
2. Use skills on targets
3. Select and validate targets
4. Check agent state

All addresses are from `/Gw.exe(Symbols)`. WASM equivalents listed where available.

## Core Skill Execution Pipeline

```
SkillOrderActivation(agent_id, slot)           @ 0x004f4d00
  │  WASM: ram:812475a1
  │  Validates: agent != 0, slot <= 7, ownership
  │  Calls CharCliSkillGetHotKey → ConstGetSkill
  │  Checks skill_data[0x31] for castability
  │  Target selection (auto → self → manual → fallback)
  │
  └─► CharCliPlayerOrderSkill(agent_id, slot, target, call_target_flag)  @ 0x007edbc0
        │  WASM: ram:80c4e74c
        │  Validates: slot <= 7, map loaded, agent alive
        │  Calls HotKeyLookup → HotKeyGetRechargeMs
        │  ConstGetSkill, campaign/mission checks
        │  HotKeyState::OnSkillOrderIssue
        │
        └─► CharMsgSendOrderSkill(skill_id, ..., target, call_target)
               OR
            CharMsgSendOrderAttackSkill(attack_id, ..., target, call_target)
                WASM: ram:80a16931 / ram:80a13bed
```

## Function Reference

### 1. Skill Execution

#### SkillOrderActivation — Use a skill by slot

```
Address:  0x004f4d00 (EXE) / ram:812475a1 (WASM)
Calling:  __stdcall or __thiscall
Args:     (uint agent_id, uint slot)  // slot = 0-7
Returns:  0 on success, error code on failure
```

**What it does:**
1. Validates agent_id ≠ 0, slot ≤ 7
2. Calls `CharCliAgentGetControlled()` — asserts you own this skillbar
3. `CharCliSkillGetHotKey(agent, slot, &skill_id, &unknown)`
4. `ConstGetSkill(skill_id)` → checks `skill[0x31]` (castability flag)
5. If skill is self-only (skill[0x31] == 0) → calls `CharCliPlayerOrderSkill(agent, slot, 0, chat_flag)` — no target needed
6. For targeted skills:
   - Tries auto-target: `AvSelectGetAuto()` → `AvValidate()` → `AvSelectHasAutoIntent()` → `CharCliPlayerCheckTargetType(skill_type, auto)`
   - Tries self: `CharCliPlayerCheckTargetType(skill_type, self)`
   - Tries manual target: `CharCliPlayerCheckTargetType(skill_type, manual)` → `AvSelectSetManual()` (marks as primary target)
   - Falls back to local_8 value

**Skip the target selection**: call `CharCliPlayerOrderSkill` directly with your own target.

#### CharCliPlayerOrderSkill — Execute a skill with explicit target

```
Address:  0x007edbc0 (EXE) / ram:80c4e74c (WASM)
Calling:  __stdcall (4 args)
Args:     (uint agent_id, uint slot, uint target_id, int call_target_flag)
Returns:  void (sends packet to server)
```

**What it does:**
1. Gets player property `EProp_(0xB)`
2. Validates slot ≤ 7
3. Checks map is loaded (`MissionCliGetMap`)
4. Checks agent state: `*(agent_state + 0x10C) & 0x10` — agent must not be dead/disabled
5. `CSkillHotKeyState::HotKeyLookup(agent, slot, &skill_id, &...)`
6. **`HotKeyGetRechargeMs(agent, slot)`** — if > 0, aborts (skill on cooldown)
7. `ConstGetSkill(skill_id)` → checks mission/campaign availability
8. `CharCliPlayerIsPrebuilt()` — prebuilt character check
9. Campaign mask check (`MissionCliGetChapterMaskPvm/Pvp`)
10. Skill type validation (array of 0-17 values against skill type)
11. `CSkillHotKeyState::OnSkillOrderIssue(agent, slot, ...)` — marks hotkey as used
12. Sends packet: `CharMsgSendOrderSkill` or `CharMsgSendOrderAttackSkill`

**Key insight**: You can call this directly with your chosen target. It performs all validation — if it returns, the skill was sent to the server.

### 2. Skill State Queries

#### CharCliSkillGetHotKey — Resolve skill in slot

```
Address:  thunk → ram:80c52126 (WASM)
Args:     (uint agent_id, uint slot, uint* out_skill_id, int* out_unknown)
Returns:  void, fills out_skill_id
```

Gets the skill_id currently in the given slot for the agent.

#### HotKeyGetRechargeMs — Check cooldown

```
Address:  via CSkillHotKeyState::HotKeyGetRechargeMs @ ram:80bc816e (WASM)
Args:     (uint agent_id, uint slot)
Returns:  int — milliseconds remaining, 0 = ready
```

Returns > 0 if the skill is still recharging. Returns 0 if ready to use.

#### HotKeyGetPending — Check if skill is queued

```
Address:  via CSkillHotKeyState::HotKeyGetPending @ (WASM)
Args:     (uint agent_id, uint slot)
Returns:  int — non-zero if skill activation is pending/queued
```

#### HotKeyGetPrioritized — Check hero priority

```
Address:  ram:80c5289e (WASM)
Args:     (uint agent_id, uint slot)
Returns:  int — non-zero if skill is prioritized for hero AI
```

#### ConstGetSkill — Get skill constant data

```
Address:  thunk → ram:818b3d99 (WASM)
Args:     (uint skill_id)
Returns:  SkillData* — pointer to skill constant data structure
```

**SkillData structure** (partial, from decompilation):
```
  +0x0C    skill_type        (0=normal, 0x0E=attack skill, 0x1B=resurrection?)
  +0x31    castability_flag  (0 = self-only/no-target, non-zero = targeted)
  +0x32    animation_timing  (used by PlanCombatActionTimeline)
  +0x3C    cast_time         (total cast duration in seconds)
  +0x50    timing_value_1    (used for skill action records)
  +0x54    timing_value_2 
  +0x74    sound_effect_id
  +0x98    name_string_id
  +0x9C    concise_string_id
  +0xA0    description_string_id
```

### 3. Target Selection & Validation

#### AvSelectGetAuto — Get auto-target

```
Address:  thunk → ram:80bc2a0a (WASM)
Args:     ()
Returns:  uint agent_id (0 if none)
```

#### AvSelectGetManual — Get manual selection

```
Address:  thunk → ram:80bc2a40 (WASM)
Args:     ()
Returns:  uint agent_id (0 if none)
```

#### AvSelectHasAutoIntent — Is auto-target intentional?

```
Address:  thunk → ram:80bc2a5b (WASM)
Args:     ()
Returns:  int bool
```

#### AvSelectSetManual — Set manual/primary target

```
Address:  thunk → ram:80bc35d7 (WASM)
Args:     (uint agent_id)
Returns:  void
```

Sets the manual selection and marks as the primary combat target.

#### AvSelectNearest — Select nearest target

```
Address:  ram:80bc2a77 (WASM)
Args:     (uint flags)
Returns:  uint agent_id
```

#### AvSelectNext / AvSelectPrev — Tab-target cycling

```
Address:  ram:80bc2c26 / ram:80bc3133 (WASM)
Args:     (uint flags)
Returns:  uint agent_id
```

#### CharCliPlayerCheckTargetType — Validate target for skill

```
Address:  thunk → ram:80c47c38 (WASM)
Args:     (ECharTarget skill_target_type, uint agent_id)
Returns:  int bool — 1 if target is valid for this skill type
```

The `skill_target_type` comes from `skill_data[0x31]`.

#### AvValidate — Check agent exists/is valid

```
Address:  thunk → ram:80bba0f5 (WASM)
Args:     (uint agent_id)
Returns:  int bool
```

#### SetCombatTargetSelection — Set auto-target (AI path)

```
Address:  0x007be240 (EXE)
Args:     (int mode, uint agent_id)
Returns:  void
```

Mode 0 = nearest, mode 1 = priority. Sets the auto-target and broadcasts UI update.

### 4. Agent State Queries

#### CharCliAgentGetControlled — Get controlled agent

```
Address:  thunk → ram:80c13a2c (WASM)
Args:     ()
Returns:  uint agent_id
```

#### AvCharIsHenchman — Check if agent is a henchman

```
Address:  ram:80bbba66 (WASM)
Args:     (uint agent_id)
Returns:  int bool
```

#### Enabled agent enumeration

```
AvSelectGetActive()          @ ram:80bc29ef   → agent_id
AvSelectGetHover()           @ ram:80bc2a25   → agent_id  
CharCliHeroGetHero(agent_id) @ ram:80c45a69   → hero_id
```

### 5. Combat AI Mode Control (Heroes)

#### CharCliCommandAiMode — Set AI mode

```
Address:  ram:80c44017 (WASM)
Args:     (uint agent_id, ECharAiMode mode)
Returns:  void
```

AI modes: passive, defensive, aggressive.

#### CharCliCommandAiPriorityTarget — Set AI priority target

```
Address:  ram:80c4414e (WASM)
Args:     (uint agent_id, uint target_id)
Returns:  void
```

#### CharCliCommandSkillPrioritize — Prioritize a hero skill

```
Address:  ram:80c44655 (WASM)
Args:     (uint agent_id, uint slot, uint target_id)
Returns:  void
```

#### CharCliCommandSkillUnprioritize — Remove priority

```
Address:  ram:80c447ba (WASM)
Args:     (uint agent_id, uint slot)
Returns:  void
```

#### CharCliCommandHotKeyDisableAi — Lock skill from AI

```
Address:  ram:80c442d9 (WASM)
Args:     (uint agent_id, uint slot)
Returns:  void
```

### 6. Combat State / Chat Checks

#### ChatAllowAlert — Check if chat is open

```
Address:  thunk → IUi::Game::ChatAllowAlert (WASM)
Args:     ()
Returns:  int bool — 0 if chat is blocking input
```

#### MissionCliGetMap — Check if map is loaded

```
Address:  thunk → (WASM)
Args:     ()
Returns:  int map_id — 0 = no map loaded / transitioning
```

#### MissionCliGetChapterMaskPvm — Campaign availability

```
Address:  thunk → (WASM)
Args:     ()
Returns:  uint chapter_mask
```

---

## Practical Usage Patterns

### Pattern 1: Use a skill on a target (one-liner)

```python
# From Python, call the native function:
# CharCliPlayerOrderSkill(controlled_agent, slot, target_id, 1)
```

This does all validation. If it returns, the skill packet was sent.

### Pattern 2: Check if a skill is ready before using

```python
agent_id = CharCliAgentGetControlled()
recharge = HotKeyGetRechargeMs(agent_id, slot)
if recharge == 0:
    skill_id, _ = CharCliSkillGetHotKey(agent_id, slot)
    skill = ConstGetSkill(skill_id)
    if skill.castability_flag != 0:  # targeted skill
        target = choose_target()
        if CharCliPlayerCheckTargetType(skill.castability_flag, target):
            CharCliPlayerOrderSkill(agent_id, slot, target, 1)
    else:
        CharCliPlayerOrderSkill(agent_id, slot, 0, 0)  # self-skill
```

### Pattern 3: Let the game pick the target

```python
# Call SkillOrderActivation — it does all the targeting for you
SkillOrderActivation(agent_id, slot)
```

### Pattern 4: Override auto-target selection

```python
# Force the auto-target to a specific agent
AvSelectSetManual(desired_target_id)
# Now SkillOrderActivation will use this as its manual target
SkillOrderActivation(agent_id, slot)
```

### Pattern 5: Control a hero's AI targeting

```python
# Set hero to aggressive mode
CharCliCommandAiMode(hero_agent_id, AI_MODE_AGGRESSIVE)
# Tell hero to prioritize a skill on a target
CharCliCommandSkillPrioritize(hero_agent_id, slot, target_id)
# Tell hero to attack a specific target
CharCliCommandAiPriorityTarget(hero_agent_id, target_id)
```

---

## Key Addresses Summary

| Function | EXE Address | WASM Address | Notes |
|----------|------------|-------------|-------|
| `SkillOrderActivation` | `0x004f4d00` | `ram:812475a1` | Full target selection included |
| `CharCliPlayerOrderSkill` (TryUseCombatSkillBySlot) | `0x007edbc0` | `ram:80c4e74c` | Direct skill execution with explicit target |
| `CharCliSkillGetHotKey` | `0x007ee400` | `ram:80c52126` | Resolve skill_id from slot |
| `ConstGetSkill` | `0x005a1010` | `ram:818b3d99` | Get skill constant data |
| `CharCliAgentGetControlled` | `0x007e4b30` | `ram:80c13a2c` | Get player's agent ID |
| `CharCliPlayerCheckTargetType` | `0x007ec930` | `ram:80c47c38` | Validate target for skill type |
| `AvSelectGetAuto` | `0x007b87e0`* | `ram:80bc2a0a` | *(via thunk_FUN_007bdba0)* |
| `AvSelectGetManual` | `0x007b8800`* | `ram:80bc2a40` | *(via thunk_FUN_007bdbb0)* |
| `AvSelectSetManual` (SetPrimaryCombatTarget) | `0x007b89e0` | `ram:80bc35d7` | Set manual/primary target |
| `AvSelectHasAutoIntent` | `0x007b8810`* | `ram:80bc2a5b` | *(via thunk_FUN_007bdbe0)* |
| `AvValidate` | `0x007b8ba0` | `ram:80bba0f5` | Validate agent exists |
| `AvSelectNearest` | — | `ram:80bc2a77` | WASM only |
| `AvSelectNext` | — | `ram:80bc2c26` | WASM only |
| `CharCliCommandAiMode` | — | `ram:80c44017` | WASM only |
| `CharCliCommandAiPriorityTarget` | — | `ram:80c4414e` | WASM only |
| `CharCliCommandSkillPrioritize` | — | `ram:80c44655` | WASM only |
| `ChatAllowAlert` | `0x005152a0` | `IUi::Game::ChatAllowAlert` | Chat blocking check |
| `CharMsgSendOrderSkill` | *(thunk)* | `ram:80a16931` | Final packet send |
| `SetCombatTargetSelection` | `0x007be240` | *(unnamed)* | Set auto-target |
| `EnumerateMatchingCombatAgents` | `0x007b8110` | *(unnamed)* | Filter combat agents |

*Thunks are at different addresses than the underlying function. The WASM address is the authoritative function address.

# Guild Wars Combat AI Reverse Engineering

Date: 2026-03-26
Program: `/Gw.exe(Symbols)`
Tooling: REVA / Ghidra MCP

## Objective

This document summarizes the current reverse-engineering state of the client-side combat AI-related systems in `Gw.exe`.

The practical goal is not to fully rewrite the AI.

The practical goal is to identify the smallest native decision/output boundary that could later be hooked so a player-controlled account can consume game-owned combat decisions and translate them into player-safe actions.

In short:

- preferred outcome: let the game decide, capture the output, adapt it
- less desirable outcome: replicate the logic manually

## Executive Summary

The investigation started from heroes, pets, skills, and movement, but the strongest result is a shared `CombatAgentView` system for generic combat-capable agents.

The most important current finding is that the client appears to contain:

- a real shared combat-agent registry
- a per-tick combat subsystem
- a per-agent update method
- internal action codes and action-state transitions
- action-record dispatchers
- a planner that turns chosen actions into timed internal execution records
- a timed trigger / timed phase system that appears to stage execution over time

Current best reusable output chain:

`UpdateCombatAgentView`
-> action-specific record handlers
-> `PlanCombatActionTimeline`
-> `ApplyCombatAgentActionState`
-> `QueueCombatTimedActionRecord`
-> timed trigger buckets
-> `HandleCombatAgentActionEvent`

That chain currently looks more promising for hooking than the public skill-use or movement entry points.

## High-Level Conclusion

We did not prove one neat monolithic client-side "combat brain."

We did find a structured native combat-agent framework that is probably good enough to hook.

Current judgment:

- hooking looks more plausible than full AI replication
- full custom-agent integration does not currently look necessary
- the better strategy is likely to observe and reuse the game's internal action/timeline outputs

## Investigation Path

### Hero and pet command layer

Early passes found client-side activation, commander, and mode handling for heroes and pets.

Important renamed functions:

- `0x008e9270` `RecvHeroActivatePacket`
- `0x007e8c70` `HandleHeroActivatePacket`
- `0x007f5090` `HeroActivate`
- `0x007f5170` `HeroDataAdd`
- `0x007f52a0` `HeroDeactivate`
- `0x007f5380` `HeroDisable`
- `0x007f4ff0` `HeroCommandMoveToPoint`
- `0x007f48c0` `HeroPoolFindByAgentId`
- `0x007f4970` `HeroPoolFindByHeroId`
- `0x004f59c0` `GmAgentCommander_FrameMsgHandler`
- `0x007e56f0` `SendAgentCommanderAiMode`
- `0x008eacd0` `SendAgentCommanderAiModePacket`
- `0x00508130` `PetCommander_InitFrames`
- `0x00507650` `PetCommander_FrameMsgHandler`
- `0x00508060` `PetCommander_CommitSelection`

Interpretation:

- real client-side command/state logic exists
- useful as context, but not yet the tactical combat brain

### Shared combat-agent context layer

This was the first strong generic pivot.

Renamed functions:

- `0x004f56f0` `IsAgentCommanderEligible`
- `0x005075d0` `IsPetCommanderEligibleAgent`
- `0x0050e290` `BuildAgentContextActions`
- `0x0050e830` `ExecuteAgentContextAction`

Repeated checks:

- `FUN_007b8ba0(agent)` validates an agent
- `FUN_007b84e0(agent) == 0xdb` strongly looks like a combat-capable/living agent type
- `FUN_007b6fb0(agent)` and `FUN_007b6fe0(agent)` look like classification/state helpers

Interpretation:

- heroes, henchmen, pets, and likely enemies converge on a shared combat-agent layer

### Shared skill and movement execution layers

Skill-side:

- `0x004f4d00` `TryUseSkillOnBestAvailableTarget`
- `0x007edbc0` `TryUseCombatSkillBySlot`
- `0x008eb900` `SendUseCombatSkillPacket`

Movement-side:

- `0x005da310` `AgentMovementStateSetTargetPoint`
- `0x007f23f0` `IssueMoveToWorldPoint`
- `0x007eda20` `IssueMoveToClickedPoint`
- `0x007ed900` `IssueMoveByDirectionOrOffset`
- `0x007f1f30` `TryPlanMoveWithHeadingMode`
- `0x007f2bc0` `AdvanceAgentQueuedMovement`
- `0x008eb740` `SendMoveToPointPacket`
- `0x008eb6f0` `SendDirectionalMovePacket`

Interpretation:

- both movement and skill usage clearly have shared client-side execution paths
- however, later passes suggest the shared combat-agent AI layer sits above these and does not directly emit them yet

### Native target-selection layer

Renamed functions:

- `0x007be000` `SetAutoTargetMode`
- `0x007bd610` `UpdateAutoTargetSelection`
- `0x007bd7b0` `UpdateAutoTargetSelectionMode1`
- `0x007be240` `SetCombatTargetSelection`
- `0x007be0e0` `SetPrimaryCombatTarget`

Interpretation:

- target selection is native, shared, and sits above raw execution
- this was the first strong "brain-adjacent" subsystem

### Combat subsystem wrapper

Renamed functions:

- `0x007b69c0` `UpdateCombatSubsystemTick`
- `0x007bda80` `TickAutoTargetSelection`
- `0x007bdef0` `SetAutoTargetNearestEnabled`
- `0x007bdf30` `SetAutoTargetPriorityEnabled`
- `0x007bddb0` `RefreshLockedCombatTarget`
- `0x007c0880` `RunScheduledCombatCallbacks`
- `0x007d8dc0` `UpdateCombatAgentSequences`
- `0x007cb070` `AdvanceCombatSequenceQueues`
- `0x007cdb10` `IsCombatSequenceQueueCongested`
- `0x007c5730` `UpdateCombatPressureState`
- `0x007b8dd0` `UpdateCombatTimedEffects`
- `0x007cb0c0` `DispatchCombatSequenceSetupQueue`
- `0x007c78c0` `FlushCombatSequenceVisualState`

Interpretation:

- `UpdateCombatSubsystemTick` is the high-level per-tick wrapper
- `UpdateCombatAgentSequences` is the most important behavior-side branch under it

### Shared combat-agent registry validation

Renamed functions:

- `0x007d8c00` `RegisterCombatAgentView`
- `0x007d9890` `GetAgentViewByAgentId`
- `0x007d98b0` `GetCombatAgentViewByAgentId`
- `0x007d9120` `EnumerateMatchingCombatAgents`
- `0x007d9450` `SelectBestCombatAgentView`
- `0x007b83f0` `FindBestCombatAgentId`
- `0x007d8f10` `ResetCombatAgentViewSystem`
- `0x007d9e70` `QueueCombatAgentViewCleanup`
- `0x007b8090` `InitializeCombatAgentViewSystem`
- `0x007da670` `AdvanceCombatAgentFocusGeneration`

Interpretation:

- the branch is real and shared
- this is not just UI or commander code
- `0xdb` combat-agent views are being registered, filtered, enumerated, scored, and updated

### Concrete combat-agent class

Renamed functions:

- `0x007c96f0` `ConstructCombatAgentView`
- `0x007c9e60` `DestructCombatAgentView`
- `0x007caa00` `UpdateCombatAgentView`
- `0x007cce20` `ProcessCombatAgentQueuedActions`
- `0x007cda20` `EvaluateCombatAgentSelectionScore`
- `0x007d3c60` `MatchCombatAgentSelectionFilter`
- `0x007d3e50` `HandleCombatAgentActionEvent`

Interpretation:

- this was the main structural breakthrough
- `UpdateCombatAgentView` became the best decision-side hook candidate
- `HandleCombatAgentActionEvent` became the best downstream action/event-side hook candidate

### Internal action-state layer

Renamed functions:

- `0x007d30e0` `ComputeCombatAgentMovementActionCode`
- `0x007d32a0` `SelectCombatAgentFallbackActionCode`
- `0x007c9270` `ResolveCombatActionVariant`
- `0x007d3370` `ApplyCombatAgentActionState`
- `0x007d3940` `UpdateCombatAgentActionVisuals`
- `0x007d14e0` `TickCombatActionCharQueue`
- `0x007cfc70` `DispatchCombatActionCharQueue`
- `0x007d16c0` `DispatchCombatQueuedActionRecord`

Interpretation:

- the combat-agent branch computes and applies internal action state before reaching lower public execution layers

### Action-specific record handlers

Renamed functions:

- `0x007d0d10` `ProcessCombatSkillActionRecord`
- `0x007cfa20` `ProcessCombatAttackActionRecord`
- `0x007d1070` `ProcessCombatTimedSkillActionRecord`

Interpretation:

- skills and attacks are clearly handled inside the same shared internal record pipeline
- this was a major positive sign for hookability

### Internal planner and timed trigger queue

Renamed functions:

- `0x007cb500` `PlanCombatActionTimeline`
- `0x007d2ff0` `QueueCombatTimedActionRecord`
- `0x007c11f0` `CreateCombatTimedActionTrigger`
- `0x007ccd80` `FindCombatTimedActionTriggerByType`
- `0x007d0920` `AttachCombatRecordToTimedTriggerPhaseA`
- `0x007d0a60` `AttachCombatRecordToTimedTriggerPhaseB`
- `0x007d4860` `ProcessCombatLinkedEffectActionEvent`
- `0x007d4a70` `MergeCombatActionEventIntoTimedPhases`

Interpretation:

- `PlanCombatActionTimeline` is one of the most important functions found
- it turns a chosen action into immediate state plus staged follow-up records
- timed ids such as `6`, `7`, and `8` look like shared trigger buckets / phase buckets

## Current Best Architecture Model

Current best model:

1. combat-capable agents are represented as shared `CombatAgentView` objects
2. `UpdateCombatSubsystemTick` runs broader combat systems
3. `UpdateCombatAgentSequences` dispatches per-agent updates
4. `UpdateCombatAgentView` performs local evaluation / coordination work
5. actions are converted into internal codes and variants
6. `PlanCombatActionTimeline` stages those actions into immediate state plus timed follow-ups
7. timed records are queued into shared trigger buckets
8. `HandleCombatAgentActionEvent` drains and merges later stages
9. lower-level movement, skill, effect, UI, and sync layers consume or reflect the result

## Best Current Hook Candidates

Decision-side:

- `0x007caa00` `UpdateCombatAgentView`
- `0x007cb500` `PlanCombatActionTimeline`

Internal output-state:

- `0x007d3370` `ApplyCombatAgentActionState`
- `0x007d2ff0` `QueueCombatTimedActionRecord`

Skill-side:

- `0x007d0d10` `ProcessCombatSkillActionRecord`
- `0x007d1070` `ProcessCombatTimedSkillActionRecord`

Attack / coordination-side:

- `0x007cfa20` `ProcessCombatAttackActionRecord`
- `0x007d4a70` `MergeCombatActionEventIntoTimedPhases`

Target-evaluation-side:

- `0x007d3c60` `MatchCombatAgentSelectionFilter`
- `0x007cda20` `EvaluateCombatAgentSelectionScore`
- `0x007bd610` `UpdateAutoTargetSelection`
- `0x007be240` `SetCombatTargetSelection`

## Why Hooking Still Looks Better Than Replication

Reasons hooking looks better:

- the branch is shared and structured
- the game already computes internal action codes, variants, and timing
- skill and attack behavior are already represented inside the shared pipeline
- the timed trigger system offers natural interception points

Reasons replication looks worse:

- the logic is distributed across flags, tables, queued records, timelines, and trigger buckets
- there is no one clean standalone AI function to copy
- reproducing the exact timing and coordination behavior would be much harder than observing it

## Important Unknowns

Still unproven:

- how much final tactical authority remains server-side
- where the internal timeline branch finally reaches public movement execution
- where it finally reaches public skill execution
- full semantics of every action code
- full semantics of each timed trigger id

Important negative result:

the shared combat-agent branch has not yet been shown to directly call:

- `TryUseCombatSkillBySlot`
- `IssueMoveToWorldPoint`
- `AgentMovementStateSetTargetPoint`

That strongly suggests the combat-agent layer stays above those public/shared execution functions and feeds them later through a deeper adapter path.

## False Lead

`0x00516db0` `RunAutoCombatRoutine` looked promising early because it casted, moved, and targeted.

It is very likely not the native shared combat AI because:

- it is tied to a `GmChat` path
- related strings include `/.hotkey 8 4`, `/.t %f, %f`, and `Rage mode deactivated.`

Current interpretation:

- local helper / debug / automation feature
- not the main built-in PvE combat AI branch

## Bookmarks

Bookmarks created or referenced during the session:

- `AI_FirstPass`
- `AI_CommonLayer`
- `AI_SkillUse`
- `AI_Movement`
- `AI_Brain_Clues`
- `AI_SkillCoord` at `0x007d0d10`
- `AI_OutputPort` at `0x007cb500`
- `AI_TimedPhases` at `0x007d4a70`

## Recommended Next Research

Highest-value next passes:

1. Decode the remaining timed trigger ids that appear central to execution:
   - `0xe`
   - `0x10`
   - `0x13`
   - `0x15`
2. Keep classifying action-record types inside:
   - `DispatchCombatActionCharQueue`
   - `DispatchCombatQueuedActionRecord`
3. Find where the internal planner/timeline branch finally meets:
   - public skill execution
   - public movement execution
   - outbound server synchronization
4. Test whether a small hook cluster around:
   - `UpdateCombatAgentView`
   - `PlanCombatActionTimeline`
   - `ApplyCombatAgentActionState`
   - `QueueCombatTimedActionRecord`
   is sufficient to capture reusable combat outputs

## Stability Note

REVA remained responsive throughout this investigation. No restart was needed during these passes.

## Skill Description Access Map

Date: 2026-03-26

This session also mapped the native text path relevant to obtaining skill descriptions directly, without wiki scraping.

### Core native fact

GWCA's native `Skill` layout already documents these three fields as string ids:

- `name` at `+0x98`
- `concise` at `+0x9C`
- `description` at `+0xA0`

Relevant local source:

- `vendor/gwca/Include/GWCA/GameEntities/Skill.h`
- `src/py_skills.cpp`

That means the game does not store full decoded skill descriptions in the constant skill record.
It stores text ids that must be resolved through the text subsystem.

### Confirmed local bridge path

The current Python/C++ bridge already exposes the exact primitives needed to resolve these ids:

1. read `skill.description` / `skill.concise` / `skill.name`
2. convert the uint32 id to encoded-string form with `GW::UI::UInt32ToEncStr(...)`
3. decode it with `GW::UI::AsyncDecodeStr(...)`

Relevant local source:

- `include/py_ui.h`
- `include/py_quest.h`
- `vendor/gwca/Examples/WorldInformation/main.cpp`

The map-name example in GWCA proves this pattern is valid for plain text ids:

- `area_info->name_id`
- `UInt32ToEncStr(...)`
- `AsyncDecodeStr(...)`

Skill descriptions are the strongest next candidate for the same treatment because their native fields are explicitly marked as string ids.

### Confirmed offline text-table path

The project also already contains a custom decoder for the game's string-table system in `gw.dat`:

- `Py4GWCoreLib/native_src/internals/string_table.py`
- `Py4GWCoreLib/native_src/context/TextContext.py`
- `Py4GWCoreLib/native_src/methods/DatFileMethods.py`

Important mapped facts:

- `GameContext + 0x18` -> `TextParser*`
- `TextParser` exposes current `language_id`
- `TextParser` exposes per-language file slots that point to hashed `gw.dat` text files
- the custom decoder already handles:
  - packed uint32/string-index encoding
  - optional key parsing
  - RC4-based entry decryption
  - bit-packed character decoding
  - raw UTF-16 entries
  - grammar/postprocessing cleanup

So there are now two viable direct paths:

- live/native path: `description_id -> UInt32ToEncStr -> AsyncDecodeStr`
- offline/dat path: `description_id -> encoded/string-table decode via TextParser + gw.dat`

### Ghidra anchors

Useful native functions identified in `/Gw.exe(Symbols)`:

- `0x007a1540` `Ui_CreateEncodedTextFromStringId`
- `0x007a1560` `Ui_CreateEncodedText`
- `0x005a1f90` `Ui_GetEncodedTextResourceById`
- `0x005ea970` `Ui_MultiLineTextControlProc`
- `0x005eb4b0` `Ui_ProcessMultiLineTextSegments`

Interpretation:

- `Ui_CreateEncodedTextFromStringId` is the simplest generic "string id -> encoded payload" helper
- `Ui_MultiLineTextControlProc` / `Ui_ProcessMultiLineTextSegments` are good tooltip/description-side UI anchors because long descriptions are likely rendered through the multiline text path
- `Ui_GetEncodedTextResourceById` is useful context for resource-driven text, but skill descriptions are more likely to come from runtime string ids than this smaller UI resource-id catalog

### Recommended next RE pass

Best next step is not a broad string hunt.

Best next step is:

1. pick a known skill tooltip UI frame or tooltip specimen
2. trace the frame creation path into `Ui_MultiLineTextControlProc`
3. identify the caller that supplies the encoded payload for the description body
4. confirm whether that caller pulls `skill->description` directly or routes through another small adapter

### Practical implementation hypothesis

Before deeper RE, test this directly in Python:

1. get a skill object's `description_id`
2. call the existing `UInt32ToEncStr`
3. call the existing `AsyncDecodeStr`

If that succeeds, the direct source-of-truth problem is already solved for descriptions and concise text.

If it fails, the fallback route is still local and direct:

- use the existing `TextParser` + `gw.dat` decoder to resolve the string id offline

Current judgment:

- wiki scraping should no longer be treated as the primary strategy
- the likely real source of truth is already present in-client and already partially exposed by this project

# Tower of Courage Obsidian Shard Farmer Design

## Summary

Add a dedicated solo Ranger/Assassin Tower of Courage farmer widget for repeated Normal Mode Obsidian Shard runs in the Fissure of Woe.

The farmer ports the supplied AutoIt route and combat timing into the existing Py4GW `Botting` harness. It reuses the established Dragon Moss farmer patterns for defensive upkeep, non-blocking movement, loot retries, death recovery, reset handling, and inventory checkpoints without coupling the two farms together.

## Scope

The first version:

- Runs solo as Ranger/Assassin.
- Uses the proven AutoIt farmer skill template: `OgcTc5+8Z6ASn5uU4ABimsBKuEA`.
- Forces Normal Mode.
- Enters FoW from Temple of the Ages using `/kneel` only.
- Clears the supplied Tower of Courage Abyssal and ranger route.
- Picks up only the explicitly selected valuable drops.
- Uses MerchantRules for Guild Hall inventory checkpoints.
- Returns to Temple of the Ages and loops after a successful run, failure recovery, or inventory checkpoint.

The first version does not:

- Enter FoW using passage scrolls.
- Run the full modular FoW quest sequence.
- Support multibox parties or heroes.
- Add Hard Mode timing.
- Embed a second merchant rules engine inside the farmer.

## Widget Placement

Create:

`Widgets/Automation/Bots/Farmers/Materials/Obsidian Shards/tower_of_courage_farmer.py`

The widget remains a focused standalone farmer. It does not modify the Dragon Moss farmer or Modular FoW widget.

## Runtime Architecture

Use the `Botting` harness with named states and coroutine-backed custom states. The top-level `main()` remains frame-cheap and advances:

- failure recovery;
- death and party-defeat watchdog checks;
- `bot.Update()`;
- the existing Botting UI.

The main state progression is:

1. Ensure Temple of the Ages.
2. Check inventory capacity.
3. Run MerchantRules checkpoint when required.
4. Validate Ranger/Assassin and load the farm skillbar.
5. Leave party and force Normal Mode.
6. Enter FoW through the Temple statue.
7. Run the Tower of Courage farm.
8. Reset to Temple of the Ages.
9. Jump back to the inventory check.

## Temple Entry

Use the existing Temple entry values already present in Modular FoW:

- Temple of the Ages map ID from `name_to_map_id["Temple of the Ages"]`.
- FoW map ID from `name_to_map_id["The Fissure of Woe"]`.
- Statue coordinates: `(-2435.05, 18678.10)`.
- Spawned NPC: `Champion of Balthazar`.
- Entry dialog IDs: `0x85`, then `0x86`.

The entry coroutine:

1. Travels to Temple of the Ages when needed.
2. Moves to the statue.
3. Sends `Player.SendChatCommand("kneel")`.
4. Waits for the `Champion of Balthazar` NPC to appear.
5. Moves into range and interacts with the Champion.
6. Sends entry dialogs `0x85`, then `0x86`.
7. Waits for FoW map load.

Failure to confirm FoW entry returns control to the reset flow rather than continuing on an unexpected map.

## Build And Skill Upkeep

Add a farmer-specific `BuildMgr` subclass that requires Ranger/Assassin and the proven AutoIt template:

| Slot | Skill |
| --- | --- |
| 1 | Shroud of Distress |
| 2 | Shadow Form |
| 3 | Dwarven Stability |
| 4 | Whirling Defense |
| 5 | Heart of Shadow |
| 6 | "I Am Unstoppable!" |
| 7 | Dark Escape |
| 8 | Mental Block |

The build ticker remains non-blocking while a farm run is active:

- maintain Shadow Form and Shroud of Distress during movement and combat waits;
- refresh `I Am Unstoppable!` during kill windows when available;
- refresh Mental Block during the Abyssal kill window when its effect is absent;
- cast Heart of Shadow during the Abyssal phase when health is below `30%`, or below `40%` while conditioned;
- suppress Heart of Shadow during the ranger kill window to preserve the old farmer's positioning;
- avoid blocking `main()`;
- stop upkeep immediately during reset, town handling, or failure recovery.

The route coroutine owns the exact opening sequence and phase casts such as Dark Escape, Dwarven Stability, `I Am Unstoppable!`,
Mental Block, and Whirling Defense so their timing stays readable and faithful to the proven farmer.

## Farm Route

Port the proven AutoIt coordinates and sequencing without inventing alternate pull points.

### Abyssal Phase

1. Cast Shadow Form, Dwarven Stability, and Dark Escape before leaving the FoW entrance.
2. Follow the initial pull through:
   - `(-21131, -2390)`
   - `(-16494, -3113)`
3. Interrupt the initial movement when an Abyssal enters earshot range. Pause background upkeep, clear stale queued movement or
   upkeep actions, and cast `I Am Unstoppable!` immediately. Do not add Mental Block to this emergency reaction.
4. When no Abyssal interrupts the initial movement, wait `1000 ms` after the initial pull and cast `I Am Unstoppable!`.
5. Cast Dwarven Stability when available, then Mental Block.
6. Move to `(-14453, -3536)`.
7. Cast Dwarven Stability, then Whirling Defense.
8. Move through:
   - `(-13684, -2077)`
   - `(-14113, -418)`
9. Run the active Abyssal survival loop until nearby Abyssals are cleared, Whirling Defense expires, or the `38000 ms`
   Whirling window expires.

### Ranger Phase

1. Move through:
   - `(-13684, -2077)`
   - `(-15826, -3046)`
   - `(-16002, -3031)`
2. Wait until Mental Block and Whirling Defense are ready while maintaining defenses.
3. Move through:
   - `(-16004, -3202)`
   - `(-15272, -3004)`
4. Cast `I Am Unstoppable!`, Dwarven Stability, Mental Block, and Whirling Defense when available.
5. Move through:
   - `(-14453, -3536)`
   - `(-14209, -2935)`
   - `(-14535, -2615)`
6. Run the active ranger survival loop for `27000 ms`, maintaining defenses while suppressing Heart of Shadow.
7. Move to `(-14506, -2633)`.
8. Loot selected drops.

The route follows the old farmer's scripted phases rather than a permanent grouped-buff cadence. The original opening sequence is
intentional: Shadow Form, Dwarven Stability, Dark Escape, then movement. The Abyssal protection casts occur after the first pull
anchors and the original `1000 ms` wait unless an Abyssal reaches earshot range first. In that case, movement stops and
`I Am Unstoppable!` is cast immediately to avoid a knockdown. The ranger phase uses the old direct balling route rather than the
newer Death's Charge jump.

Route movement keeps the proven pull coordinates as ordered anchors. For each anchor, resolve an intelligent navmesh route with
`AutoPathing().get_path_to(...)`, then follow the generated path with `Routines.Yield.Movement.FollowPath(..., autopath=True)`.
This retains the intended aggro sequence while using recovery autopathing when movement needs to be rebuilt. Death and map-loading
conditions abort movement cleanly.

## Ground Loot Policy

Filter item agents before pickup. Pick up only:

- `ModelID.Obsidian_Shard`;
- `ModelID.Dark_Remains`;
- `ModelID.Ruby`;
- `ModelID.Sapphire`;
- `ModelID.Passage_Scroll_Fow`;
- any weapon with requirement `7`;
- any weapon with requirement `8`;
- Chaos Axe with requirement `9`.

Leave every other ground drop untouched.

For ground item classification:

- resolve item ID with `Agent.GetItemAgentItemID(agent_id)`;
- inspect weapon requirement using `Item.Properties.GetRequirement(item_id)`;
- identify Chaos Axe by model ID `111`.

Use `Routines.Yield.Items.LootItemsWithMaxAttempts(...)` for bounded pickup retries. Failure to collect an eligible nearby drop marks the run unsuccessful so reset and recovery remain explicit.

## Inventory Checkpoint

Check free inventory slots before each FoW entry. When the configured minimum threshold is breached:

1. Return safely to Temple of the Ages.
2. Enable the local `MerchantRules` widget if needed.
3. Travel to Guild Hall.
4. Resolve its `WIDGET_INSTANCE`.
5. Queue local `MerchantRules` execution with `_queue_execute_here()`.
6. Wait for `execution_running` to finish with a bounded timeout.
7. Log `last_error` when MerchantRules reports a failure.
8. Confirm that the minimum free-slot threshold has been restored.
9. Travel back to Temple of the Ages and continue the farm loop.

If MerchantRules fails, times out, or does not restore the minimum free-slot threshold, stop the farmer safely in Guild Hall. Do not enter a repeated checkpoint loop with insufficient bag space.

MerchantRules remains configured through its existing UI. The farmer does not rewrite its profile.

The operator-configured MerchantRules profile must:

- retain materials;
- deposit retained loot when desired;
- protect requirement `7`, `8`, and `9` weapon candidates from destructive actions;
- avoid selling protected Chaos Axes.

The narrow ground filter means MerchantRules primarily performs storage checkpoints rather than routine cleanup of unwanted drops.

## Recovery

Use the Dragon Moss farmer's recovery shape:

- register death, party wipe, and party defeat callbacks;
- run a frame-level watchdog for missed callbacks;
- reset action queues before recovery;
- disable build upkeep during recovery;
- resign and return to outpost when alive in FoW;
- issue `Party.ReturnToOutpost()` and fall back to `Routines.Yield.Map.TravelToOutpost(...)` when needed;
- resume at the Temple setup state.

Map mismatches, failed entry, movement timeout, and kill timeout also exit through reset instead of continuing with stale state.

## UI And Documentation

Use the default `Botting` UI and add a concise tooltip covering:

- Ranger/Assassin requirement;
- skill template;
- Normal Mode;
- Temple `/kneel` entry;
- selected ground loot;
- required MerchantRules setup;
- recovery behavior;

Use the standard Main-tab `additional_ui` callback to display session-local `Successful runs` and `Failed runs` counters.
Reloading the widget resets both counters.
- armor, weapon, shield, and title-rank recommendations from the supplied farmer.

## Verification

There is no repo-level test runner. Verify with targeted checks:

1. Run a Python syntax compilation check on the new widget.
2. Confirm the widget imports only existing CoreLib surfaces.
3. Confirm the pickup predicate with a focused offline harness using mocked item-agent records for:
   - Obsidian Shard;
   - Dark Remains;
   - Ruby;
   - Sapphire;
   - FoW passage scroll;
   - generic `q7` weapon;
   - generic `q8` weapon;
   - `q9` Chaos Axe;
   - generic `q9` weapon rejection;
   - `q10+` Chaos Axe rejection;
   - unrelated material rejection.
4. In-client smoke test:
   - travel to Temple;
   - `/kneel` entry;
   - FoW map confirmation;
   - opening Shadow Form, Dwarven Stability, and Dark Escape;
   - immediate `I Am Unstoppable!` cast when an Abyssal reaches earshot during the initial pull;
   - first-pull `1000 ms` fallback followed by `I Am Unstoppable!`, Dwarven Stability, and Mental Block;
   - first ball Dwarven Stability and Whirling Defense cast;
   - Abyssal pull with active protection refreshes and emergency Heart of Shadow;
   - ranger pull with active protection refreshes and Heart of Shadow suppressed;
   - selective looting;
   - resign and return loop;
   - forced low-slot MerchantRules checkpoint;
   - death recovery.

## Success Criteria

The feature is complete when the widget can repeatedly enter Normal Mode FoW from Temple of the Ages, clear the supplied Tower of Courage farm route as solo Ranger/Assassin, collect only the approved drops, recover to Temple after failures, and run a MerchantRules Guild Hall checkpoint when inventory capacity is low.

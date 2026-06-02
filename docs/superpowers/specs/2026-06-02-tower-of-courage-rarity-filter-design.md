# Tower of Courage Weapon Rarity Filter Design

## Goal

Prevent the Tower of Courage Obsidian Shard farmer from picking up white and blue weapons while preserving its existing
selected-drop behavior.

## Scope

Change only the Tower of Courage farmer's ground-loot policy:

- continue picking up Obsidian Shards, Dark Remains, Rubies, Sapphires, and FoW passage scrolls;
- pick up requirement `7` and requirement `8` weapons only when their rarity is `Purple` or `Gold`;
- continue picking up requirement `9` Chaos Axes;
- leave all other drops on the ground.

The requirement `9` Chaos Axe rule remains unchanged and does not gain a rarity restriction.

## Implementation

Keep `Sources/tower_of_courage/loot_policy.py` independent of the injected Py4GW runtime so its regression script remains
offline-safe.

At the widget boundary in
`Widgets/Automation/Bots/Farmers/Materials/Obsidian Shards/tower_of_courage_farmer.py`, read the item's rarity once with
`Item.Rarity.GetRarity(item_id)` and pass the rarity name into `should_pick_up_item(...)`.

Extend the pure policy helper signature to accept the rarity name. For requirement `7` and requirement `8` weapons,
return `True` only when that name is `Purple` or `Gold`. Preserve the existing early return for always-picked-up model
IDs and the existing requirement `9` Chaos Axe condition.

Update the widget tooltip so it advertises purple and gold requirement `7` or requirement `8` weapons rather than any
requirement `7` or requirement `8` weapon.

## Verification

Extend `Widgets/Data/test_tower_of_courage_loot_policy.py` with focused offline cases:

- reject white requirement `7` weapons;
- reject blue requirement `7` weapons;
- accept purple requirement `7` weapons;
- accept gold requirement `7` weapons;
- reject white requirement `8` weapons;
- reject blue requirement `8` weapons;
- accept purple requirement `8` weapons;
- accept gold requirement `8` weapons;
- preserve selected non-weapon pickup behavior;
- preserve the requirement `9` Chaos Axe rule;
- preserve generic requirement `9`, requirement `10+` Chaos Axe, and unrelated-item rejection.

Run:

```powershell
python "Widgets/Data/test_tower_of_courage_loot_policy.py"
```

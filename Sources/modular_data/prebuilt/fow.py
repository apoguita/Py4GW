"""BT-native FoW prebuilt runner."""
from __future__ import annotations

from Py4GWCoreLib.modular import BTRecipeRunner
from Py4GWCoreLib.modular import RecipeSpec


FOW_QUEST_ORDER: list[tuple[str, str]] = [
    ("tower_of_courage", "Tower Of Courage"),
    ("eternal_forgemaster", "Eternal Forgemaster"),
    ("defend_the_temple", "Defend The Temple"),
    ("restore_the_temple", "Restore The Temple"),
    ("khobay", "Khobay"),
    ("tower_of_strength", "Tower Of Strength"),
    ("slaves_of_menzies", "Slaves Of Menzies"),
    ("army_of_darkness", "Army Of Darkness"),
    ("wailing_lord", "Wailing Lord"),
    ("gift_of_griffons", "Gift Of Griffons"),
    ("reward_time", "Reward Time"),
]

def create_modular_fow_bot(*, debug_hook=None) -> BTRecipeRunner:
    if debug_hook is not None:
        debug_hook("FoW BT runner initialized.")
    specs = [RecipeSpec(kind="quest", key=f"FoW/{key}", title=title) for key, title in FOW_QUEST_ORDER]
    return BTRecipeRunner(
        name="ModularFow",
        specs=specs,
        loop=True,
        debug_hook=debug_hook,
    )

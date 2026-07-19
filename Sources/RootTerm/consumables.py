"""Conset and summoning-stone helpers for mission enter."""

from __future__ import annotations

from typing import Any
from typing import Generator

from Py4GWCoreLib import Agent
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Effects
from Py4GWCoreLib import Inventory
from Py4GWCoreLib import Map
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import Player
from Py4GWCoreLib import Routines

from Sources.RootTerm.options import OPTIONS

CONSET_EFFECT_IDS = {
    'essence': 2522,
    'armor': 2520,
    'grail': 2521,
}

CONSET_MODELS = {
    'essence': ModelID.Essence_Of_Celerity.value,
    'armor': ModelID.Armor_Of_Salvation.value,
    'grail': ModelID.Grail_Of_Might.value,
}

CONSET_LABELS = {
    'essence': 'Essence of Celerity',
    'armor': 'Armor of Salvation',
    'grail': 'Grail of Might',
}

STONE_ENTRIES: list[tuple[str, int]] = [
    ('Mercantile Summoning Stone', ModelID.Merchant_Summon.value),
    ('Tengu Support Flare', ModelID.Tengu_Summon.value),
    ('Imperial Guard Reinforcement Order', ModelID.Imperial_Guard_Summon.value),
    ('Automaton Summoning Stone', ModelID.Automaton_Summon.value),
    ('Igneous Summoning Stone (Imp)', ModelID.Igneous_Summoning_Stone.value),
    ('Chitinous Summoning Stone', ModelID.Chitinous_Summon.value),
    ('Mystical Summoning Stone', ModelID.Mystical_Summon.value),
    ('Amber Summoning Stone', ModelID.Amber_Summon.value),
    ('Arctic Summoning Stone', ModelID.Arctic_Summon.value),
    ('Demonic Summoning Stone', ModelID.Demonic_Summon.value),
    ('Gelatinous Summoning Stone', ModelID.Gelatinous_Summon.value),
    ('Fossilized Summoning Stone', ModelID.Fossilized_Summon.value),
    ('Jadeite Summoning Stone', ModelID.Jadeite_Summon.value),
    ('Mischievous Summoning Stone', ModelID.Mischievous_Summon.value),
    ('Frosty Summoning Stone', ModelID.Frosty_Summon.value),
    ('Mysterious Summoning Stone', ModelID.Mysterious_Summon.value),
    ('Zaishen Summoning Stone', ModelID.Zaishen_Summon.value),
    ('Ghastly Summoning Stone', ModelID.Ghastly_Summon.value),
    ('Celestial Summoning Stone', ModelID.Celestial_Summon.value),
    ('Shining Blade War Horn', ModelID.Shining_Blade_Summon.value),
    ('Legionnaire Summoning Stone', ModelID.Legionnaire_Summoning_Crystal.value),
]

STONE_LABELS = [label for label, _ in STONE_ENTRIES]
SUMMONING_SICKNESS_EFFECT_ID = 2886

_consumables_applied = False


def reset_mission_consumables() -> None:
    global _consumables_applied
    _consumables_applied = False


def _any_conset_enabled() -> bool:
    return OPTIONS.use_essence or OPTIONS.use_armor or OPTIONS.use_grail


def _has_effect(effect_id: int) -> bool:
    try:
        return bool(Effects.HasEffect(Player.GetAgentID(), effect_id))
    except Exception:
        return False


def _use_model(model_id: int) -> Generator[Any, Any, bool]:
    if Inventory.GetModelCount(model_id) <= 0:
        return False
    ok = yield from Routines.Yield.Items.UseItem(model_id)
    yield from Routines.Yield.wait(750)
    return bool(ok)


def apply_mission_consumables() -> Generator[Any, Any, None]:
    """Use enabled consets / stone once after entering explorable."""
    global _consumables_applied
    if _consumables_applied:
        return
    if not _any_conset_enabled() and not OPTIONS.use_stone:
        return

    waited = 0
    while waited < 15000 and not Map.IsExplorable():
        yield from Routines.Yield.wait(250)
        waited += 250
    if not Map.IsExplorable():
        return

    _consumables_applied = True

    if OPTIONS.use_essence and not _has_effect(CONSET_EFFECT_IDS['essence']):
        if (yield from _use_model(CONSET_MODELS['essence'])):
            ConsoleLog('RMA', f"Used {CONSET_LABELS['essence']}.")
        else:
            ConsoleLog('RMA', f"{CONSET_LABELS['essence']} enabled but not found.")

    if OPTIONS.use_armor and not _has_effect(CONSET_EFFECT_IDS['armor']):
        if (yield from _use_model(CONSET_MODELS['armor'])):
            ConsoleLog('RMA', f"Used {CONSET_LABELS['armor']}.")
        else:
            ConsoleLog('RMA', f"{CONSET_LABELS['armor']} enabled but not found.")

    if OPTIONS.use_grail and not _has_effect(CONSET_EFFECT_IDS['grail']):
        if (yield from _use_model(CONSET_MODELS['grail'])):
            ConsoleLog('RMA', f"Used {CONSET_LABELS['grail']}.")
        else:
            ConsoleLog('RMA', f"{CONSET_LABELS['grail']} enabled but not found.")

    if OPTIONS.use_stone:
        yield from _use_summoning_stone()


def _use_summoning_stone() -> Generator[Any, Any, None]:
    if _has_effect(SUMMONING_SICKNESS_EFFECT_ID):
        return
    idx = OPTIONS.stone_index
    if idx < 0 or idx >= len(STONE_ENTRIES):
        idx = len(STONE_ENTRIES) - 1
    label, model_id = STONE_ENTRIES[idx]
    if model_id == ModelID.Igneous_Summoning_Stone.value:
        try:
            level = Agent.GetLevel(Player.GetAgentID())
        except Exception:
            level = 20
        if level and level > 19:
            ConsoleLog('RMA', f'Igneous Imp skipped (level {level} > 19).')
            return
    if (yield from _use_model(model_id)):
        ConsoleLog('RMA', f'Used {label}.')
    else:
        ConsoleLog('RMA', f'{label} enabled but not found.')

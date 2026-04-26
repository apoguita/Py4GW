from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HeroAICombatRangeState:
    in_aggro: bool
    party_in_aggro: bool
    combat_distance: float
    enemy_in_combat_distance: bool

    @property
    def in_combat(self) -> bool:
        return self.in_aggro or self.enemy_in_combat_distance


def get_hero_ai_combat_range_state() -> HeroAICombatRangeState:
    from HeroAI.cache_data import CacheData
    from Py4GWCoreLib import AgentArray, Range

    cached_data = CacheData()
    cached_data.Update()
    cached_data.UpdateCombat()

    combat_handler = getattr(cached_data, "combat_handler", None)
    if combat_handler is not None and hasattr(combat_handler, "get_combat_distance"):
        combat_distance = float(combat_handler.get_combat_distance())
    else:
        combat_distance = Range.Spellcast.value if bool(cached_data.data.in_aggro) else Range.Earshot.value

    enemy_in_combat_distance = bool(cached_data.InAggro(AgentArray.GetEnemyArray(), combat_distance))
    return HeroAICombatRangeState(
        in_aggro=bool(cached_data.data.in_aggro),
        party_in_aggro=bool(getattr(cached_data.data, "party_in_aggro", cached_data.data.in_aggro)),
        combat_distance=combat_distance,
        enemy_in_combat_distance=enemy_in_combat_distance,
    )


def hero_ai_combat_detected(include_party: bool = False) -> bool:
    state = get_hero_ai_combat_range_state()
    if include_party:
        return state.in_combat or state.party_in_aggro
    return state.in_combat


def get_hero_ai_combat_distance() -> float:
    return get_hero_ai_combat_range_state().combat_distance

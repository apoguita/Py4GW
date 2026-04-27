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
    from Py4GWCoreLib import AgentArray

    cached_data = CacheData()
    cached_data.Update()
    cached_data.UpdateCombat()

    combat_distance = float(cached_data.GetActiveScanRange())

    enemy_in_combat_distance = bool(cached_data.InAggro(AgentArray.GetEnemyArray(), combat_distance))
    return HeroAICombatRangeState(
        in_aggro=bool(cached_data.data.in_aggro),
        party_in_aggro=bool(cached_data.data.party_in_aggro),
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

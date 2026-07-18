"""Per-mission runner metadata (town, maps, party size, completion)."""

from __future__ import annotations

from dataclasses import dataclass

# Map IDs (Py4GW / GWCA)
MAP_GREAT_NORTHERN_WALL = 28
MAP_FORT_RANIK = 29
MAP_FRONTIER_GATE = 135
MAP_CHAHBEK_VILLAGE = 544
MAP_CHURRHIR_FIELDS = 456

# Hero IDs used by Nightfall missions (from GwAu3 / HeroType)
HERO_KOSS = 6


@dataclass(frozen=True)
class MissionConfig:
    quest_id: int
    town_map: int
    town_label: str
    mission_map: int
    map2: int
    map3: int
    map4: int
    party_size: int
    required_hero: int
    completion_map: int


# Phase 1 configs from MissionConfigData.au3 (numeric map IDs resolved).
MISSION_CONFIG: dict[int, MissionConfig] = {
    936: MissionConfig(
        quest_id=936,
        town_map=MAP_GREAT_NORTHERN_WALL,
        town_label='The Great Northern Wall',
        mission_map=MAP_GREAT_NORTHERN_WALL,
        map2=MAP_FORT_RANIK,
        map3=0,
        map4=0,
        party_size=4,
        required_hero=0,
        completion_map=MAP_FORT_RANIK,
    ),
    937: MissionConfig(
        quest_id=937,
        town_map=MAP_FORT_RANIK,
        town_label='Fort Ranik',
        mission_map=MAP_FORT_RANIK,
        map2=MAP_FRONTIER_GATE,
        map3=0,
        map4=0,
        party_size=4,
        required_hero=0,
        completion_map=MAP_FRONTIER_GATE,
    ),
    978: MissionConfig(
        quest_id=978,
        town_map=MAP_CHAHBEK_VILLAGE,
        town_label='Chahbek Village',
        mission_map=MAP_CHAHBEK_VILLAGE,
        map2=MAP_CHURRHIR_FIELDS,
        map3=0,
        map4=0,
        party_size=4,
        required_hero=HERO_KOSS,
        completion_map=MAP_CHURRHIR_FIELDS,
    ),
}

# Quest IDs that have a playable Python mission script in Phase 1.
PLAYABLE_QUEST_IDS: frozenset[int] = frozenset(MISSION_CONFIG.keys())


def get_config(quest_id: int) -> MissionConfig | None:
    return MISSION_CONFIG.get(quest_id)


def is_playable(quest_id: int) -> bool:
    return quest_id in PLAYABLE_QUEST_IDS

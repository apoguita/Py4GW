"""Per-mission runner metadata (town, maps, party size, completion)."""

from __future__ import annotations

from dataclasses import dataclass

# Map IDs (Py4GW / GWCA)
MAP_GREAT_NORTHERN_WALL = 28
MAP_FORT_RANIK = 29
MAP_RUINS_OF_SURMIA = 30
MAP_NOLANI_ACADEMY = 32
MAP_FRONTIER_GATE = 135
MAP_CHAHBEK_VILLAGE = 544
MAP_CHURRHIR_FIELDS = 456
MAP_SIFHALLA = 643
MAP_GUNNARS_HOLD = 644
MAP_OLAFSTEAD = 645
MAP_GROTHMAR_WARDOWNS = 649
MAP_LONGEYES_LEDGE = 650
MAP_CENTRAL_TRANSFER_CHAMBER = 652
MAP_CURSE_OF_THE_NORNBEAR = 653
MAP_BLOOD_WASHES_BLOOD = 654
MAP_GATE_TOO_FAR_1 = 655
MAP_GATE_TOO_FAR_2 = 656
MAP_GATE_TOO_FAR_3 = 657
MAP_AGAINST_THE_CHARR = 665
MAP_A_TIME_FOR_HEROES = 673
MAP_EPILOGUE = 710

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
    938: MissionConfig(
        quest_id=938,
        town_map=MAP_RUINS_OF_SURMIA,
        town_label='Ruins of Surmia',
        mission_map=MAP_RUINS_OF_SURMIA,
        map2=MAP_NOLANI_ACADEMY,
        map3=0,
        map4=0,
        party_size=4,
        required_hero=0,
        completion_map=MAP_NOLANI_ACADEMY,
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
    1003: MissionConfig(1003, MAP_LONGEYES_LEDGE, 'Against the Charr', MAP_AGAINST_THE_CHARR,
                        MAP_GROTHMAR_WARDOWNS, 0, 0, 8, 0, MAP_LONGEYES_LEDGE),
    1006: MissionConfig(1006, MAP_SIFHALLA, 'Curse of the Nornbear', MAP_CURSE_OF_THE_NORNBEAR,
                        0, 0, 0, 8, 0, MAP_SIFHALLA),
    1007: MissionConfig(1007, MAP_LONGEYES_LEDGE, 'Blood Washes Blood', MAP_BLOOD_WASHES_BLOOD,
                        482, 546, 0, 8, 0, MAP_GUNNARS_HOLD),
    1008: MissionConfig(1008, MAP_OLAFSTEAD, 'A Gate Too Far', MAP_GATE_TOO_FAR_1,
                        MAP_GATE_TOO_FAR_2, MAP_GATE_TOO_FAR_3, 0, 8, 0, MAP_OLAFSTEAD),
    1010: MissionConfig(1010, MAP_CENTRAL_TRANSFER_CHAMBER, 'A Time for Heroes', MAP_A_TIME_FOR_HEROES,
                        0, 0, 0, 8, 0, MAP_EPILOGUE),
}

# Quest IDs that have a playable Python mission script in Phase 1.
PLAYABLE_QUEST_IDS: frozenset[int] = frozenset(MISSION_CONFIG.keys())


def get_config(quest_id: int) -> MissionConfig | None:
    return MISSION_CONFIG.get(quest_id)


def is_playable(quest_id: int) -> bool:
    return quest_id in PLAYABLE_QUEST_IDS

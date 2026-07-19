"""Per-mission runner metadata (town, maps, party size, completion)."""

from __future__ import annotations

from dataclasses import dataclass

# Map IDs (Py4GW / GWCA)
MAP_GREAT_NORTHERN_WALL = 28
MAP_FORT_RANIK = 29
MAP_RUINS_OF_SURMIA = 30
MAP_NOLANI_ACADEMY = 32
MAP_YAKS_BEND = 134
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
MAP_VIZUNAH_SQUARE_LOCAL = 291
MAP_VIZUNAH_SQUARE_MISSION = 215
MAP_DRAGONS_THROAT = 274
MAP_NAHPUI_QUARTER = 216
MAP_SENJIS_CORNER = 51
MAP_TAHNNAKAI_TEMPLE = 217
MAP_ZIN_KU_CORRIDOR = 284
MAP_BORLIS_PASS = 25
MAP_THE_FROST_GATE = 21
MAP_BEACONS_PERCH = 133
MAP_MINISTER_CHOS_ESTATE = 214
MAP_RAN_MUSU_GARDENS = 251
MAP_ZEN_DAIJUN = 213
MAP_SEITUNG_HARBOR = 250
MAP_SUNJIANG_DISTRICT = 220
MAP_MAATU_KEEP = 283

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
    939: MissionConfig(
        quest_id=939,
        town_map=MAP_NOLANI_ACADEMY,
        town_label='Nolani Academy',
        mission_map=MAP_NOLANI_ACADEMY,
        map2=MAP_YAKS_BEND,
        map3=0,
        map4=0,
        party_size=4,
        required_hero=0,
        completion_map=MAP_YAKS_BEND,
    ),
    940: MissionConfig(
        quest_id=940,
        town_map=MAP_BORLIS_PASS,
        town_label='Borlis Pass',
        mission_map=MAP_BORLIS_PASS,
        map2=MAP_THE_FROST_GATE,
        map3=0,
        map4=0,
        party_size=6,
        required_hero=0,
        completion_map=MAP_THE_FROST_GATE,
    ),
    941: MissionConfig(
        quest_id=941,
        town_map=MAP_THE_FROST_GATE,
        town_label='The Frost Gate',
        mission_map=MAP_THE_FROST_GATE,
        map2=MAP_BEACONS_PERCH,
        map3=0,
        map4=0,
        party_size=6,
        required_hero=0,
        completion_map=MAP_BEACONS_PERCH,
    ),
    961: MissionConfig(961, MAP_ZEN_DAIJUN, 'Zen Daijun', MAP_ZEN_DAIJUN,
                       0, 0, 0, 6, 0, MAP_SEITUNG_HARBOR),
    962: MissionConfig(962, MAP_VIZUNAH_SQUARE_LOCAL, 'Vizunah Square', MAP_VIZUNAH_SQUARE_MISSION,
                       0, 0, 0, 8, 0, MAP_DRAGONS_THROAT),
    963: MissionConfig(963, MAP_NAHPUI_QUARTER, 'Nahpui Quarter', MAP_NAHPUI_QUARTER,
                       0, 0, 0, 8, 0, MAP_SENJIS_CORNER),
    964: MissionConfig(964, MAP_TAHNNAKAI_TEMPLE, 'Tahnnakai Temple', MAP_TAHNNAKAI_TEMPLE,
                       0, 0, 0, 8, 0, MAP_ZIN_KU_CORRIDOR),
    967: MissionConfig(967, MAP_SUNJIANG_DISTRICT, 'Sunjiang District', MAP_SUNJIANG_DISTRICT,
                       0, 0, 0, 8, 0, MAP_MAATU_KEEP),
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
    1119: MissionConfig(1119, MAP_MINISTER_CHOS_ESTATE, "Minister Cho's Estate",
                        MAP_MINISTER_CHOS_ESTATE, 0, 0, 0, 4, 0, MAP_RAN_MUSU_GARDENS),
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

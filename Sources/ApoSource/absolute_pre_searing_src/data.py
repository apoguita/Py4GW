from dataclasses import dataclass, field

from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.enums_src.Model_enums import ModelID

Coords = tuple[float, float]


@dataclass(frozen=True)
class MapConfigData:
    LAKESIDE_COUNTY_MAP_ID: int = 146
    ASCALON_CITY_MAP_ID: int = 148
    REGENT_VALLEY_MAP_ID: int = 162
    ASHFORD_ABBEY_MAP_ID: int = 164


@dataclass(frozen=True)
class Sequence_001_Common_Data:
    town_cryer_coords: Coords = (9954.21, -472.19)
    town_cryer_message: str = "Taking Quest with Town Crier"
    sir_tydius_coords: Coords = (11694.64, 3440.12)
    sir_tydius_message: str = "Taking Quest with Sir Tydius"
    exit_map_coords: Coords = (6817.0, 4892.0)
    exit_map_message: str = "Exiting map and moving to Lakeside County"
    lakeside_county_map_id: int = MapConfigData.LAKESIDE_COUNTY_MAP_ID


@dataclass(frozen=True)
class Sequence_002_Common_Data:
    Travel_to_ascalon_city_message: str = "Traveling to Ascalon City to turn in quests"
    ascalon_city_map_id: int = MapConfigData.ASCALON_CITY_MAP_ID
    amin_saberlin_001_coords: Coords = (8284.25, 5596.36)
    amin_saberlin_coords: Coords = (11952.64, 3115.04)
    amin_saberlin_message: str = "Turning in quests to Amin Saberlin"


@dataclass(frozen=True)
class Quest_001_Common_Data:
    haversdan_coords: Coords = (5984.58, 3823.78)
    pitney_coords: Coords = (-8083.34, -15416.37)
    devona_coords: Coords = (-7868.41, -15038.71)
    meerak_coords: Coords = (-12289.86, -6518.84)
    wait_for_haversdan_coords: Coords = (5534.92, 3831.50)
    ashford_abbey_move_coords: Coords = (-11890.0, -6071.0)
    ashford_abbey_map_id: int = MapConfigData.ASHFORD_ABBEY_MAP_ID
    haversdan_wait_ms: int = 20000
    clear_area_radius: float = Range.Spellcast.value
    skale_kill_spot_message: str = "Moving to Skale killing spot"
    skale_kill_spot_arrival_message: str = "Arrived to Skale killing spot."


@dataclass(frozen=True)
class Quest_001_Warrior_Data:
    van_the_warrior_coords: Coords = (6123.73, 3952.56)
    van_the_warrior_message: str = "Taking Quest with Van the Warrior"
    skale_coords: Coords = (4915.27, -2893.53)
    return_message: str = "area is clear, moving back to Van the Warrior"


@dataclass(frozen=True)
class Quest_001_Ranger_Data:
    artemis_the_ranger_coords: Coords = (6143.31, 4202.66)
    artemis_the_ranger_message: str = "Taking Quest with Artemis the Ranger"
    skale_coords: Coords = (5702.27, -4308.52)
    return_message: str = "area is clear, moving back to Artemis the Ranger"


@dataclass(frozen=True)
class Quest_001_Monk_Data:
    cigio_the_monk_coords: Coords = (5983.98, 4181.18)
    cigio_the_monk_message: str = "Taking Quest with Cigio the Monk"
    skale_coords: Coords = (4915.27, -2893.53)
    return_message: str = "Returning to Cigio the Monk"
    gwen_coords: Coords = (3876.63, -4540.65)
    gwen_message: str = "area is clear, moving to Gwen"


@dataclass(frozen=True)
class Quest_001_Necromancer_Data:
    verata_the_necromancer_message: str = "Taking Quest with Verata the Necromancer"
    verata_the_necromancer_coords: Coords = (6158.20, 4195.64)
    skale_coords: Coords = (4583.08, 726.40)
    verata_the_necromancer_enc_string: str = "\\x171C\\x8FE8\\xAFAD\\x61EC"


@dataclass(frozen=True)
class Quest_001_Mesmer_Data:
    sebedoh_the_mesmer_message: str = "Taking Quest with Sebedoh the Mesmer"
    sebedoh_the_mesmer_coords: Coords = (6251.90, 3891.17)
    skale_coords: Coords = (4583.08, 726.40)
    return_message: str = "area is clear, Moving to Sebedoh the Mesmer"


@dataclass(frozen=True)
class Quest_001_Elementalist_Data:
    quest_giver_message: str = "Taking Quest with Howland the Elementalist"
    quest_giver_coords: Coords = (6123.73, 3952.56)
    skale_coords: Coords = (4915.27, -2893.53)
    return_message: str = "area is clear, moving back to Howland the Elementalist"
    cleanup_model_ids: tuple[int, ...] = (ModelID.Shimmering_Scale.value,)
    cleanup_message: str = "deleting remaining quest items in bags"
    
@dataclass(frozen=True)
class UnlockRangerSecondary:
    ashford_abbey_map_id: int = MapConfigData.ASHFORD_ABBEY_MAP_ID
    ashford_abbey_travel_message: str = "Traveling to Ashford Abbey to unlock Ranger secondary profession"
    lakeside_county_exit_coords_001: Coords = (-12508.46, -6135.42)
    lakeside_county_exit_coords: Coords = (-10905, -6287)
    lakeside_county_map_id: int = MapConfigData.LAKESIDE_COUNTY_MAP_ID
    lakeside_county_travel_message: str = "Exiting to Lakeside County"
    regent_valley_travel_message: str = "Traveling to Regent Valley to unlock Ranger secondary profession"
    regent_valley_map_id: int = MapConfigData.REGENT_VALLEY_MAP_ID
    
    regent_valley_mid_001_exit_coords: Coords = (-6316.87, -6808.10)
    regent_valley_mid_002_exit_coords: Coords = (-4833.97, -12199.93)
    
    regent_valley_over_bridge_exit_coords: list[Coords] = field(default_factory=lambda: [(-3464.73, -13135.62)])
    
    regent_valley_exit_coords: Coords = (6516, -19822)
    
    destroy_summoning_stones_message: str = "Destroying summoning stone in bags"
    master_ranger_nente_coords: Coords = (-17002.32, 10390.88)
    master_ranger_nente_message: str = "Interacting with Master Ranger Nente"
    
    melandru_statue_coords: Coords = (-14990.32, -1139.84)
    melandru_statue_message: str = "Interacting with Melandru Statue to charm pet"
    
    hero_ai_disable_message: str = "Disabling HeroAI to charm pet"
    hero_ai_enable_message: str = "Re-enabling HeroAI"
    charm_pet_message: str = "Capturing pet with HeroAI disabled"
    pet_model_id: int = 1345
    charm_pet_skill_id: int = 411
    charm_pet_pre_wait_ms: int = 500
    charm_pet_wait_ms: int = 15000

@dataclass(frozen=True)
class GenesisData:
    sequence_001_common_data: Sequence_001_Common_Data = Sequence_001_Common_Data()
    sequence_002_common_data: Sequence_002_Common_Data = Sequence_002_Common_Data()
    quest_001_common_data: Quest_001_Common_Data = Quest_001_Common_Data()
    quest_001_warrior_data: Quest_001_Warrior_Data = Quest_001_Warrior_Data()
    quest_001_ranger_data: Quest_001_Ranger_Data = Quest_001_Ranger_Data()
    quest_001_monk_data: Quest_001_Monk_Data = Quest_001_Monk_Data()
    quest_001_necromancer_data: Quest_001_Necromancer_Data = Quest_001_Necromancer_Data()
    quest_001_mesmer_data: Quest_001_Mesmer_Data = Quest_001_Mesmer_Data()
    quest_001_elementalist_data: Quest_001_Elementalist_Data = Quest_001_Elementalist_Data()

    unlock_ranger_secondary_data: UnlockRangerSecondary = UnlockRangerSecondary()

GENESIS_DATA = GenesisData()

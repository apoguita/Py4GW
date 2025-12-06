# PyMap.pyi - Auto-generated .pyi file for PyMap module

from typing import List, Optional, Any, overload

# Enum InstanceType
class InstanceType:
    Outpost: int
    Explorable: int
    Loading: int

# Class Instance
class Instance:
    def __init__(self, instance_type: 'InstanceType') -> None: ...
    def Set(self, instance_type: 'InstanceType') -> None: ...
    def Get(self) -> 'InstanceType': ...
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...

# Enum ServerRegionType
class ServerRegionType:
    International: int
    America: int
    Korea: int
    Europe: int
    China: int
    Japan: int
    Unknown: int

# Class ServerRegion
class ServerRegion:
    def __init__(self, region: int) -> None: ...
    def Set(self, region: int) -> None: ...
    def Get(self) -> 'ServerRegionType': ...
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...

# Enum LanguageType
class LanguageType:
    English: int
    Korean: int
    French: int
    German: int
    Italian: int
    Spanish: int
    TraditionalChinese: int
    Japanese: int
    Polish: int
    Russian: int
    BorkBorkBork: int
    Unknown: int

# Class Language
class Language:
    def __init__(self, language: int) -> None: ...
    def Set(self, language: int) -> None: ...
    def Get(self) -> 'LanguageType': ...
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...

# Enum CampaignType
class CampaignType:
    Core: int
    Prophecies: int
    Factions: int
    Nightfall: int
    EyeOfTheNorth: int
    BonusMissionPack: int
    Undefined: int

# Class Campaign
class Campaign:
    def __init__(self, campaign: int) -> None: ...
    def Set(self, campaign: int) -> None: ...
    def Get(self) -> 'CampaignType': ...
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...

# Enum RegionType
class RegionType:
    AllianceBattle: int
    Arena: int
    ExplorableZone: int
    GuildBattleArea: int
    GuildHall: int
    MissionOutpost: int
    CooperativeMission: int
    CompetitiveMission: int
    EliteMission: int
    Challenge: int
    Outpost: int
    ZaishenBattle: int
    HeroesAscent: int
    City: int
    MissionArea: int
    HeroBattleOutpost: int
    HeroBattleArea: int
    EotnMission: int
    Dungeon: int
    Marketplace: int
    Unknown: int
    DevRegion: int

# Class Region
class Region:
    def __init__(self, region_type: int) -> None: ...
    def Set(self, region_type: int) -> None: ...
    def Get(self) -> 'RegionType': ...
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...

# Enum ContinentType
class ContinentType:
    Kryta: int
    DevContinent: int
    Cantha: int
    BattleIsles: int
    Elona: int
    RealmOfTorment: int
    Undefined: int

# Class Continent
class Continent:
    def __init__(self, continent: int) -> None: ...
    def Set(self, continent: int) -> None: ...
    def Get(self) -> 'ContinentType': ...
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...

# Class MapID
class MapID:
    def __init__(self, id: int) -> None: ...
    def Set(self, new_id: int) -> None: ...
    def Get(self) -> int: ...
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...
    def GetOutpostIDs(self) -> List[int]: ...
    def GetOutpostNames(self) -> List[str]: ...

# Class PyMap
class PyMap:
    instance_type: Instance
    is_map_ready: bool
    instance_time: int
    map_id: MapID
    server_region: ServerRegion
    district: int
    language: Language
    foes_killed: int
    foes_to_kill: int
    is_in_cinematic: bool
    campaign: Campaign
    continent: Continent
    region_type: Region
    has_enter_button: bool
    is_on_world_map: bool
    is_pvp: bool
    is_guild_hall: bool
    is_vanquishable_area: bool
    amount_of_players_in_instance: int
    flags: int
    thumbnail_id: int
    min_party_size: int
    max_party_size: int
    min_player_size: int
    max_player_size: int
    controlled_outpost_id: int
    fraction_mission: int
    min_level: int
    max_level: int
    needed_pq: int
    mission_maps_to: List[int]
    icon_position_x: int
    icon_position_y: int
    icon_start_x: int
    icon_start_y: int
    icon_end_x: int
    icon_end_y: int
    icon_start_x_dupe: int
    icon_start_y_dupe: int
    icon_end_x_dupe: int
    icon_end_y_dupe: int
    file_id: int
    mission_chronology: int
    ha_map_chronology: int
    name_id: int
    description_id: int
    map_boundaries: List[float]
    
    def __init__(self) -> None: ...
    def GetContext(self) -> None: ...
    @overload
    def Travel(self, map_id: int) -> bool: ...
    @overload
    def Travel(self, map_id: int, district: int, district_number: int) -> bool: ...
    @overload
    def Travel(self, map_id: int, server_region: int, district_number: int, language: int) -> bool: ...
    def TravelGH(self) -> bool: ...
    def LeaveGH(self) -> bool: ...
    def RegionFromDistrict(self, district: int) -> ServerRegion: ...
    def LanguageFromDistrict(self, district: int) -> Language: ...
    def GetIsMapUnlocked(self, map_id: int) -> bool: ...
    def SkipCinematic(self) -> bool: ...
    def EnterChallenge(self) -> bool: ...
    def CancelEnterChallenge(self) -> bool: ...
    def GetMapID(self) -> int: ...
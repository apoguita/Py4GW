from enum import Enum
from enum import IntEnum

# region ServerRegion
class ServerRegion(IntEnum):
    International = -2
    America = 0
    Korea = 1
    Europe = 2
    China = 3
    Japan = 4
    Unknown = 255


# endregion
# region ServerRegionName
ServerRegionName = {
    ServerRegion.International.value: "International",
    ServerRegion.America.value: "America",
    ServerRegion.Korea.value: "Korea",
    ServerRegion.Europe.value: "Europe",
    ServerRegion.China.value: "Traditional Chinese",
    ServerRegion.Japan.value: "Japanese",
    ServerRegion.Unknown.value: "Unknown",
}


# endregion
# region Language
class Language(IntEnum):
    English = 0
    Korean = 1
    French = 2
    German = 3
    Italian = 4
    Spanish = 5
    TraditionalChinese = 6
    Japanese = 8
    Polish = 9
    Russian = 10
    BorkBorkBork = 17
    Unknown = 255


# endregion
# region ServerLanguage
class ServerLanguage(IntEnum):
    English = 0
    Korean = 1
    French = 2
    German = 3
    Italian = 4
    Spanish = 5
    TraditionalChinese = 6
    Japanese = 8
    Polish = 9
    Russian = 10
    BorkBorkBork = 17
    Unknown = 255


# endregion
# region ServerLanguageName
ServerLanguageName: dict[int, str] = {
    ServerLanguage.English.value: "English",
    ServerLanguage.Korean.value: "Korean",
    ServerLanguage.French.value: "French",
    ServerLanguage.German.value: "German",
    ServerLanguage.Italian.value: "Italian",
    ServerLanguage.Spanish.value: "Spanish",
    ServerLanguage.TraditionalChinese.value: "Traditional Chinese",
    ServerLanguage.Japanese.value: "Japanese",
    ServerLanguage.Polish.value: "Polish",
    ServerLanguage.Russian.value: "Russian",
    ServerLanguage.BorkBorkBork.value: "Bork Bork Bork",
    ServerLanguage.Unknown.value: "Unknown",
}

# endregion


# region District
class District(IntEnum):
    Current = 0
    International = 1
    American = 2
    EuropeEnglish = 3
    EuropeFrench = 4
    EuropeGerman = 5
    EuropeItalian = 6
    EuropeSpanish = 7
    EuropePolish = 8
    EuropeRussian = 9
    AsiaKorean = 10
    AsiaChinese = 11
    AsiaJapanese = 12
    Unknown = 255


DistrictName: dict[int, str] = {
    District.Current.value: "Current",
    District.International.value: "International",
    District.American.value: "American",
    District.EuropeEnglish.value: "Europe - English",
    District.EuropeFrench.value: "Europe - French",
    District.EuropeGerman.value: "Europe - German",
    District.EuropeItalian.value: "Europe - Italian",
    District.EuropeSpanish.value: "Europe - Spanish",
    District.EuropePolish.value: "Europe - Polish",
    District.EuropeRussian.value: "Europe - Russian",
    District.AsiaKorean.value: "Asia - Korean",
    District.AsiaChinese.value: "Asia - Traditional Chinese",
    District.AsiaJapanese.value: "Asia - Japanese",
    District.Unknown.value: "Unknown",
}

# endregion

# region District


# region ampaign
class Campaign(IntEnum):
    Core = 0
    Prophecies = 1
    Factions = 2
    Nightfall = 3
    EyeOfTheNorth = 4
    BonusMissionPack = 5
    Undefined = 6
    
CampaignName: dict[int, str] = {
    Campaign.Core.value: "Core",
    Campaign.Prophecies.value: "Prophecies",
    Campaign.Factions.value: "Factions",
    Campaign.Nightfall.value: "Nightfall",
    Campaign.EyeOfTheNorth.value: "Eye Of The North",
    Campaign.BonusMissionPack.value: "Bonus Mission Pack",
    Campaign.Undefined.value: "Undefined",
}


# endregion
# region RegionType
class RegionType(IntEnum):
    AllianceBattle = 0
    Arena = 1
    ExplorableZone = 2
    GuildBattleArea = 3
    GuildHall = 4
    MissionOutpost = 5
    CooperativeMission = 6
    CompetitiveMission = 7
    EliteMission = 8
    Challenge = 9
    Outpost = 10
    ZaishenBattle = 11
    HeroesAscent = 12
    City = 13
    MissionArea = 14
    HeroBattleOutpost = 15
    HeroBattleArea = 16
    EotnMission = 17
    Dungeon = 18
    Marketplace = 19
    Unknown = 20
    DevRegion = 21
    
RegionTypeName: dict[int, str] = {
    RegionType.AllianceBattle.value: "Alliance Battle",
    RegionType.Arena.value: "Arena",
    RegionType.ExplorableZone.value: "Explorable Zone",
    RegionType.GuildBattleArea.value: "Guild Battle Area",
    RegionType.GuildHall.value: "Guild Hall",
    RegionType.MissionOutpost.value: "Mission Outpost",
    RegionType.CooperativeMission.value: "Cooperative Mission",
    RegionType.CompetitiveMission.value: "Competitive Mission",
    RegionType.EliteMission.value: "Elite Mission",
    RegionType.Challenge.value: "Challenge",
    RegionType.Outpost.value: "Outpost",
    RegionType.ZaishenBattle.value: "Zaishen Battle",
    RegionType.HeroesAscent.value: "Heroes' Ascent",
    RegionType.City.value: "City",
    RegionType.MissionArea.value: "Mission Area",
    RegionType.HeroBattleOutpost.value: "Hero Battle Outpost",
    RegionType.HeroBattleArea.value: "Hero Battle Area",
    RegionType.EotnMission.value: "Eotn Mission",
    RegionType.Dungeon.value: "Dungeon",
    RegionType.Marketplace.value: "Marketplace",
    RegionType.Unknown.value: "Unknown",
    RegionType.DevRegion.value: "Dev Region",
}


# endregion
# region Continent
class Continent(IntEnum):
    Kryta = 0
    DevContinent = 1
    Cantha = 2
    BattleIsles = 3
    Elona = 4
    RealmOfTorment = 5
    Undefined = 6
    
ContinentName: dict[int, str] = {
    Continent.Kryta.value: "Kryta",
    Continent.DevContinent.value: "Dev Continent",
    Continent.Cantha.value: "Cantha",
    Continent.BattleIsles.value: "Battle Isles",
    Continent.Elona.value: "Elona",
    Continent.RealmOfTorment.value: "Realm Of Torment",
    Continent.Undefined.value: "Undefined",
}
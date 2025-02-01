from enum import Enum, IntEnum

class Range(Enum):
    Touch = 144.0
    Adjacent = 166.0
    Nearby = 252.0
    Area = 322.0
    Earshot = 1012.0
    Spellcast = 1248.0
    Spirit = 2500.0
    SafeCompass = 4800.0 #made up distance to make easy checks
    Compass = 5000.0

# ServerRegion
class ServerRegion(Enum):
    International = 0
    America = 1
    Korea = 2
    Europe = 3
    China = 4
    Japan = 5
    Unknown = 6

# Language
class Language(Enum):
    English = 0
    Korean = 1
    French = 2
    German = 3
    Italian = 4
    Spanish = 5
    TraditionalChinese = 6
    Japanese = 7
    Polish = 8
    Russian = 9
    BorkBorkBork = 10
    Unknown = 0xff

class District(Enum):
    Current = 0
    International =1
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
    Unknown = 0xff


# Campaign
class Campaign(Enum):
    Core = 0
    Prophecies = 1
    Factions = 2
    Nightfall = 3
    EyeOfTheNorth = 4
    BonusMissionPack = 5
    Undefined = 6

# RegionType
class RegionType(Enum):
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

# Continent
class Continent(Enum):
    Kryta = 0
    DevContinent = 1
    Cantha = 2
    BattleIsles = 3
    Elona = 4
    RealmOfTorment = 5
    Undefined = 6

# GW Constants: Rarity
class Rarity(IntEnum):
    White = 0
    Blue = 1
    Purple = 2
    Gold = 3
    Green = 4

# SalvageAllType
class SalvageAllType(IntEnum):
    None_ = 0
    White = 1
    BlueAndLower = 2
    PurpleAndLower = 3
    GoldAndLower = 4

# IdentifyAllType
class IdentifyAllType(IntEnum):
    None_ = 0
    All = 1
    Blue = 2
    Purple = 3
    Gold = 4

# ItemType
class ItemType(Enum):
    Salvage = 0
    Axe = 1
    Bag = 2
    Boots = 3
    Bow = 4
    Bundle = 5
    Chestpiece = 6
    Rune_Mod = 7
    Usable = 8
    Dye = 9
    Materials_Zcoins = 10
    Offhand = 11
    Gloves = 12
    Hammer = 13
    Headpiece = 14
    CC_Shards = 15
    Key = 16
    Leggings = 17
    Gold_Coin = 18
    Quest_Item = 19
    Wand = 20
    Shield = 21
    Staff = 22
    Sword = 23
    Kit = 24
    Trophy = 25
    Scroll = 26
    Daggers = 27
    Present = 28
    Minipet = 29
    Scythe = 30
    Spear = 31
    Storybook = 32
    Costume = 33
    Costume_Headpiece = 34
    Unknown = 35

# DyeColor
class DyeColor(Enum):
    NoColor = 0
    Blue = 1
    Green = 2
    Purple = 3
    Red = 4
    Yellow = 5
    Brown = 6
    Orange = 7
    Silver = 8
    Black = 9
    Gray = 10
    White = 11
    Pink = 12

# Profession
class Profession(Enum):
    None_ = 0  # Avoiding reserved keyword "None"
    Warrior = 1
    Ranger = 2
    Monk = 3
    Necromancer = 4
    Mesmer = 5
    Elementalist = 6
    Assassin = 7
    Ritualist = 8
    Paragon = 9
    Dervish = 10

# Allegiance
class Allegiance(Enum):
    Unknown = 0
    Ally = 1  # 0x1 = ally/non-attackable
    Neutral = 2  # 0x2 = neutral
    Enemy = 3  # 0x3 = enemy
    SpiritPet = 4  # 0x4 = spirit/pet
    Minion = 5  # 0x5 = minion
    NpcMinipet = 6  # 0x6 = npc/minipet
    
# AllieganceDonation
class FactionAllegiance(Enum):
    Kurzick = 0
    Luxon = 1

#WeaponType
class Weapon(Enum):
    Unknown = 0
    Bow = 1
    Axe = 2
    Hammer = 3
    Daggers = 4
    Scythe = 5
    Spear = 6
    Sword = 7
    Scepter = 8
    Scepter2 = 9
    Wand = 10
    Staff1 = 11
    Staff = 12
    Staff2 = 13
    Staff3 = 14
    Unknown1 = 15
    Unknown2 = 16
    Unknown3 = 17
    Unknown4 = 18
    Unknown5 = 19
    Unknown6 = 20
    Unknown7 = 21
    Unknown8 = 22
    Unknown9 = 23
    Unknown10 = 24

# Attribute
class Attribute(Enum):
    FastCasting = 0
    IllusionMagic = 1
    DominationMagic = 2
    InspirationMagic = 3
    BloodMagic = 4
    DeathMagic = 5
    SoulReaping = 6
    Curses = 7
    AirMagic = 8
    EarthMagic = 9
    FireMagic = 10
    WaterMagic = 11
    EnergyStorage = 12
    HealingPrayers = 13
    SmitingPrayers = 14
    ProtectionPrayers = 15
    DivineFavor = 16
    Strength = 17
    AxeMastery = 18
    HammerMastery = 19
    Swordsmanship = 20
    Tactics = 21
    BeastMastery = 22
    Expertise = 23
    WildernessSurvival = 24
    Marksmanship = 25
    Unknown1 = 26
    Unknown2 = 27
    Unknown3 = 28
    DaggerMastery = 29
    DeadlyArts = 30
    ShadowArts = 31
    Communing = 32
    RestorationMagic = 33
    ChannelingMagic = 34
    CriticalStrikes = 35
    SpawningPower = 36
    SpearMastery = 37
    Command = 38
    Motivation = 39
    Leadership = 40
    ScytheMastery = 41
    WindPrayers = 42
    EarthPrayers = 43
    Mysticism = 44
    None_ = 45  # Avoiding reserved keyword "None"

# HeroType
class HeroType(Enum):
    None_ = 0  # Avoiding reserved keyword "None"
    Norgu = 1
    Goren = 2
    Tahlkora = 3
    MasterOfWhispers = 4
    AcolyteJin = 5
    Koss = 6
    Dunkoro = 7
    AcolyteSousuke = 8
    Melonni = 9
    ZhedShadowhoof = 10
    GeneralMorgahn = 11
    MagridTheSly = 12
    Zenmai = 13
    Olias = 14
    Razah = 15
    MOX = 16
    KeiranThackeray = 17
    Jora = 18
    PyreFierceshot = 19
    Anton = 20
    Livia = 21
    Hayda = 22
    Kahmu = 23
    Gwen = 24
    Xandra = 25
    Vekk = 26
    Ogden = 27
    MercenaryHero1 = 28
    MercenaryHero2 = 29
    MercenaryHero3 = 30
    MercenaryHero4 = 31
    MercenaryHero5 = 32
    MercenaryHero6 = 33
    MercenaryHero7 = 34
    MercenaryHero8 = 35
    Miku = 36
    ZeiRi = 37

class TitleID(IntEnum):
    Hero = 0
    TyrianCarto = 1
    CanthanCarto = 2
    Gladiator = 3
    Champion = 4
    Kurzick = 5
    Luxon = 6
    Drunkard = 7
    Deprecated_SkillHunter = 8  # Pre hard mode update version
    Survivor = 9
    KoaBD = 10
    Deprecated_TreasureHunter = 11  # Old title, non-account bound
    Deprecated_Wisdom = 12  # Old title, non-account bound
    ProtectorTyria = 13
    ProtectorCantha = 14
    Lucky = 15
    Unlucky = 16
    Sunspear = 17
    ElonianCarto = 18
    ProtectorElona = 19
    Lightbringer = 20
    LDoA = 21
    Commander = 22
    Gamer = 23
    SkillHunterTyria = 24
    VanquisherTyria = 25
    SkillHunterCantha = 26
    VanquisherCantha = 27
    SkillHunterElona = 28
    VanquisherElona = 29
    LegendaryCarto = 30
    LegendaryGuardian = 31
    LegendarySkillHunter = 32
    LegendaryVanquisher = 33
    Sweets = 34
    GuardianTyria = 35
    GuardianCantha = 36
    GuardianElona = 37
    Asuran = 38
    Deldrimor = 39
    Vanguard = 40
    Norn = 41
    MasterOfTheNorth = 42
    Party = 43
    Zaishen = 44
    TreasureHunter = 45
    Wisdom = 46
    Codex = 47
    None_ = 0xff  # Use 'None_' to avoid using the reserved keyword 'None'

TITLE_NAME = {
    TitleID.Hero: "Hero",
    TitleID.TyrianCarto: "Tyrian Cartographer",
    TitleID.CanthanCarto: "Canthan Cartographer",
    TitleID.Gladiator: "Gladiator",
    TitleID.Champion: "Champion",
    TitleID.Kurzick: "Kurzick",
    TitleID.Luxon: "Luxon",
    TitleID.Drunkard: "Drunkard",
    TitleID.Deprecated_SkillHunter: "Skill Hunter",  # Pre hard mode update version
    TitleID.Survivor: "Survivor",
    TitleID.KoaBD: "Kind Of A Big Deal",
    TitleID.Deprecated_TreasureHunter: "Treasure Hunter",  # Old title, non-account bound
    TitleID.Deprecated_Wisdom: "Wisdom",  # Old title, non-account bound
    TitleID.ProtectorTyria: "Protector of Tyria",
    TitleID.ProtectorCantha: "Protector of Cantha",
    TitleID.Lucky: "Lucky",
    TitleID.Unlucky: "Unlucky",
    TitleID.Sunspear: "Sunspear",
    TitleID.ElonianCarto: "Elonian Cartographer",
    TitleID.ProtectorElona: "Protector of Elona",
    TitleID.Lightbringer: "Lightbringer",
    TitleID.LDoA: "Legendary Defender of Ascalon",
    TitleID.Commander: "Commander",
    TitleID.Gamer: "Gamer",
    TitleID.SkillHunterTyria: "Tyrian Skill Hunter",
    TitleID.VanquisherTyria: "Tyrian Vanquisher",
    TitleID.SkillHunterCantha: "Canthan Skill Hunter",
    TitleID.VanquisherCantha: "Canthan Vanquisher",
    TitleID.SkillHunterElona: "Elonian Skill Hunter",
    TitleID.VanquisherElona: "Elonian Vanquisher",
    TitleID.LegendaryCarto: "Legendary Cartographer",
    TitleID.LegendaryGuardian: "Legendary Guardian",
    TitleID.LegendarySkillHunter: "Legendary Skill Hunter",
    TitleID.LegendaryVanquisher: "Legendary Vanquisher",
    TitleID.Sweets: "Sweet Tooth",
    TitleID.GuardianTyria: "Tyrian Guardian",
    TitleID.GuardianCantha: "Canthan Guardian",
    TitleID.GuardianElona: "Elonian Guardian",
    TitleID.Asuran: "Asuran",
    TitleID.Deldrimor: "Deldrimor",
    TitleID.Vanguard: "Vanguard",
    TitleID.Norn: "Norn",
    TitleID.MasterOfTheNorth: "Master of the North",
    TitleID.Party: "Party Animal",
    TitleID.Zaishen: "Zaishen",
    TitleID.TreasureHunter: "Treasure Hunter",
    TitleID.Wisdom: "Wisdom",
    TitleID.Codex: "Codex",
    TitleID.None_: "None",  # Use 'None_' to avoid Python reserved keyword
}

explorables = {
    7: "Warrior's Isle",
    8: "Hunter's Isle",
    9: "Wizard's Isle",
    13: "Diessa Lowlands",
    17: "Talmark Wilderness",
    18: "The Black Curtain",
    26: "Talus Chute",
    27: "Griffon's Mouth",
    31: "Xaquang Skyway",
    33: "Old Ascalon",
    34: "The Fissure of Woe",
    41: "Sage Lands",
    42: "Mamnoon Lagoon",
    43: "Silverwood",
    44: "Ettin's Back",
    45: "Reed Bog",
    46: "The Falls",
    47: "Dry Top",
    48: "Tangle Root",
    53: "Tears of the Fallen",
    54: "Scoundrel's Rise",
    56: "Cursed Lands",
    58: "North Kryta Province",
    59: "Nebo Terrace",
    60: "Majesty's Rest",
    61: "Twin Serpent Lakes",
    62: "Watchtower Coast",
    63: "Stingray Strand",
    64: "Kessex Peak",
    67: "Burning Isle",
    68: "Frozen Isle",
    69: "Nomad's Isle",
    70: "Druid's Isle",
    71: "Isle of the Dead (guild hall)",
    72: "The Underworld",
    87: "Icedome",
    88: "Iron Horse Mine",
    89: "Anvil Rock",
    90: "Lornar's Pass",
    91: "Snake Dance",
    92: "Tasca's Demise",
    93: "Spearhead Peak",
    94: "Ice Floe",
    95: "Witman's Folly",
    96: "Mineral Springs",
    97: "Dreadnought's Drift",
    98: "Frozen Forest",
    99: "Traveler's Vale",
    100: "Deldrimor Bowl",
    101: "Regent Valley",
    102: "The Breach",
    103: "Ascalon Foothills",
    104: "Pockmark Flats",
    105: "Dragon's Gullet",
    106: "Flame Temple Corridor",
    107: "Eastern Frontier",
    108: "The Scar",
    110: "Diviner's Ascent",
    111: "Vulture Drifts",
    112: "The Arid Sea",
    113: "Prophet's Path",
    114: "Salt Flats",
    115: "Skyward Reach",
    121: "Perdition Rock",
    127: "Scarred Earth",
    128: "The Eternal Grove (explorable area)",
    144: "Gyala Hatchery (explorable area)",
    145: "The Catacombs",
    146: "Lakeside County",
    147: "The Northlands",
    149: "Ascalon Academy",
    151: "Ascalon Academy",
    160: "Green Hills County",
    161: "Wizard's Folly",
    162: "Regent Valley (pre-Searing)",
    190: "Sorrow's Furnace",
    191: "Grenth's Footprint",
    195: "Drazach Thicket",
    196: "Jaya Bluffs",
    197: "Shenzun Tunnels",
    198: "Archipelagos",
    199: "Maishang Hills",
    200: "Mount Qinkai",
    201: "Melandru's Hope",
    202: "Rhea's Crater",
    203: "Silent Surf",
    205: "Morostav Trail",
    209: "Mourning Veil Falls",
    210: "Ferndale",
    211: "Pongmei Valley",
    212: "Monastery Overlook",
    227: "Unwaking Waters (explorable area)",
    232: "Shadow's Passage",
    233: "Raisu Palace (explorable area)",
    235: "Panjiang Peninsula",
    236: "Kinya Province",
    237: "Haiju Lagoon",
    238: "Sunqua Vale",
    239: "Wajjun Bazaar",
    240: "Bukdek Byway",
    241: "The Undercity",
    244: "Arborstone (explorable area)",
    245: "Minister Cho's Estate (explorable area)",
    246: "Zen Daijun (explorable area)",
    247: "Boreas Seabed (explorable area)",
    252: "Linnok Courtyard",
    256: "Sunjiang District (explorable area)",
    265: "Nahpui Quarter (explorable area)",
    269: "Tahnnakai Temple (explorable area)",
    280: "Isle of the Nameless",
    285: "Monastery Overlook",
    290: "Bejunkan Pier",
    301: "Raisu Pavilion",
    302: "Kaineng Docks",
    313: "Saoshang Trail",
    344: "The Hall of Heroes",
    345: "The Courtyard",
    346: "Scarred Earth",
    347: "The Underworld (explorable area)",
    351: "Divine Path",
    361: "Isle of Weeping Stone",
    362: "Isle of Jade",
    363: "Imperial Isle",
    364: "Isle of Meditation",
    369: "Jahai Bluffs",
    371: "Marga Coast",
    373: "Sunward Marches",
    375: "Barbarous Shore",
    377: "Badhok Caverns",
    379: "Dejarin Estate",
    380: "Arkjok Ward",
    382: "Gandara, the Moon Fortress",
    384: "The Floodplain of Mahnkelon",
    385: "Lion's Arch (Sunspears in Kryta)",
    386: "Turai's Procession",
    392: "Yatendi Canyons",
    394: "Garden of Seborhin",
    395: "Holdings of Chokhin",
    397: "Vehjin Mines",
    399: "Forum Highlands",
    400: "Kaineng Center (Sunspears in Cantha)",
    402: "Resplendent Makuun",
    404: "Wilderness of Bahdza",
    406: "Vehtendi Valley",
    413: "The Hidden City of Ahdashim",
    415: "Lion's Gate",
    419: "The Mirror of Lyss",
    420: "Secure the Refuge",
    422: "Bad Tide Rising#NPCs - Kamadan, Jewel of Istan (explorable area)",
    423: "The Tribunal",
    429: "Consulate",
    430: "Plains of Jarin",
    432: "Cliffs of Dohjok",
    436: "Command Post",
    437: "Joko's Domain",
    439: "The Ruptured Heart",
    441: "The Shattered Ravines",
    443: "Poisoned Outcrops",
    444: "The Sulfurous Wastes",
    446: "The Alkali Pan",
    447: "A Land of Heroes",
    448: "Crystal Overlook",
    455: "Nightfallen Garden",
    456: "Churrhir Fields",
    461: "The Underworld",
    462: "Heart of Abaddon",
    463: "The Underworld",
    465: "Nightfallen Jahai",
    466: "Depths of Madness",
    468: "Domain of Fear",
    470: "Domain of Pain",
    471: "Bloodstone Fen (explorable area)",
    472: "Domain of Secrets",
    474: "Domain of Anguish",
    481: "Fahranur, The First City",
    482: "Bjora Marches",
    483: "Zehlon Reach",
    484: "Lahtenda Bog",
    485: "Arbor Bay",
    486: "Issnur Isles",
    488: "Mehtani Keys",
    490: "Island of Shehkah",
    499: "Ice Cliff Chasms",
    500: "Bokka Amphitheatre",
    501: "Riven Earth",
    503: "Throne of Secrets",
    505: "Shing Jea Monastery (mission)",
    506: "Haiju Lagoon (mission)",
    507: "Jaya Bluffs (mission)",
    508: "Seitung Harbor (mission)",
    509: "Tsumei Village (mission)",
    510: "Seitung Harbor (mission 2)",
    511: "Tsumei Village (mission 2)",
    513: "Drakkar Lake",
    531: "Uncharted Isle",
    532: "Isle of Wurms",
    539: "Corrupted Isle",
    540: "Isle of Solitude",
    543: "Sun Docks",
    546: "Jaga Moraine",
    548: "Norrhart Domains",
    553: "Varajar Fells",
    558: "Sparkfly Swamp",
    561: "The Troubled Keeper",
    566: "Verdant Cascades",
    569: "Magus Stones",
    572: "Alcazia Tangle",
    625: "Battledepths",
    646: "Hall of Monuments",
    647: "Dalada Uplands",
    649: "Grothmar Wardowns",
    651: "Sacnoth Valley",
    653: "Curse of the Nornbear",
    654: "Blood Washes Blood",
    664: "Genius Operated Living Enchanted Manifestation",
    665: "Against the Charr",
    669: "Assault on the Stronghold",
    673: "A Time for Heroes",
    674: "Warband Training",
    678: "Attack of the Nornbear",
    686: "Polymock Coliseum",
    687: "Polymock Glacier",
    688: "Polymock Crossing",
    690: "Cold as Ice",
    691: "Beneath Lion's Arch",
    692: "Tunnels Below Cantha",
    693: "Caverns Below Kamadan",
    695: "Service: In Defense of the Eye",
    696: "Mano a Norn-o",
    697: "Service: Practice, Dummy",
    698: "Hero Tutorial",
    700: "The Norn Fighting Tournament",
    702: "Norn Brawling Championship",
    703: "Kilroy's Punchout Training",
    705: "The Justiciar's End",
    707: "The Great Norn Alemoot",
    708: "Varajar Fells",
    710: "Epilogue",
    711: "Insidious Remnants",
    717: "Attack on Jalis's Camp",
    726: "Kilroy's Punchout Tournament",
    727: "Special Ops: Flame Temple Corridor",
    728: "Special Ops: Dragon's Gullet",
    729: "Special Ops: Grendich Courthouse",
    770: "The Tengu Accords",
    771: "The Battle of Jahai",
    772: "The Flight North",
    773: "The Rise of the White Mantle",
    781: "Secret Lair of the Snowmen",
    782: "Secret Lair of the Snowmen",
    783: "Droknar's Forge (explorable area)",
    788: "Deactivating R.O.X.#NPCs",
    789: "Deactivating P.O.X.",
    790: "Deactivating N.O.X.",
    791: "Secret Underground Lair",
    792: "Golem Tutorial Simulation",
    793: "Snowball Dominance",
    794: "Zaishen Menagerie Grounds",
    806: "The Underworld (Something Wicked This Way Comes)",
    807: "The Underworld (Don't Fear the Reapers)",
    837: "Talmark Wilderness (War in Kryta)",
    838: "Trial of Zinn",
    839: "Divinity Coast (explorable area)",
    840: "Lion's Arch Keep",
    841: "D'Alessio Seaboard (explorable area)",
    842: "The Battle for Lion's Arch (explorable area)",
    843: "Riverside Province (explorable area)",
    844: "Lion's Arch (War in Kryta)",
    845: "The Mausoleum",
    846: "Rise",
    847: "Shadows in the Jungle",
    848: "A Vengeance of Blades",
    849: "Auspicious Beginnings",
    854: "Olafstead (explorable area)",
    855: "The Great Snowball Fight of the Gods (Operation: Crush Spirits)",
    856: "The Great Snowball Fight of the Gods (Fighting in a Winter Wonderland)",
    860: "What Waits in Shadow#NPCs - Dragon's Throat (explorable area)",
    861: "A Chance Encounter#NPCs - Kaineng Center (Winds of Change)",
    862: "Tracking the Corruption#NPCs - The Marketplace (explorable area)",
    863: "Cantha Courier Crisis#NPCs - Bukdek Byway (Winds of Change)",
    864: "A Treaty's a Treaty#NPCs - Tsumei Village (Winds of Change)",
    865: "Deadly Cargo#NPCs - Seitung Harbor (explorable area)",
    866: "The Rescue Attempt#NPCs - Tahnnakai Temple (Winds of Change)",
    867: "Violence in the Streets#NPCs - Wajjun Bazaar (Winds of Change)",
    869: "Calling All Thugs#NPCs - Shadow's Passage (Winds of Change)",
    870: "Finding Jinnai#NPCs - Altrumm Ruins",
    871: "Raid on Shing Jea Monastery#NPCs - Shing Jea Monastery",
    872: "Raid on Kaineng Center#NPCs - Kaineng Center (Winds of Change)",
    873: "Ministry of Oppression#NPCs - Wajjun Bazaar (Winds of Change)",
    874: "The Final Confrontation#NPCs - The Final Confrontation",
    875: "Lakeside County: 1070 AE",
    876: "Ashford Catacombs: 1070 AE",
}

explorable_name_to_id = {name: id for id, name in explorables.items()}

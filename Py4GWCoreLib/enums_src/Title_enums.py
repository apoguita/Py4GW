from enum import Enum
from enum import IntEnum
from typing import Dict, List

# region Titles
class TitleID(IntEnum):
    Hero = 0
    CartographerProphecies = 1
    CartographerFactions = 2
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
    CartographerNightfall = 18
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
    LegendaryCartographer = 30
    LegendaryGuardian = 31
    LegendarySkillHunter = 32
    LegendaryVanquisher = 33
    Sweet_Tooth = 34
    GuardianTyria = 35
    GuardianCantha = 36
    GuardianElona = 37
    Asuran = 38
    Deldrimor = 39
    Ebon_Vanguard = 40
    Norn = 41
    MasterOfTheNorth = 42
    PartyAnimal = 43
    Zaishen = 44
    TreasureHunter = 45
    Wisdom = 46
    Codex = 47
    None_ = 0xFF  # Use 'None_' to avoid using the reserved keyword 'None'


TITLE_NAME: dict[int, str] = {
    TitleID.Hero: "Hero",
    TitleID.CartographerProphecies: "Tyria Exploration",
    TitleID.CartographerFactions: "Cantha Exploration",
    TitleID.Gladiator: "Gladiator",
    TitleID.Champion: "Champion",
    TitleID.Kurzick: "Kurzick",
    TitleID.Luxon: "Luxon",
    TitleID.Drunkard: "Drunkard",
    TitleID.Deprecated_SkillHunter: "Deprecated Skill Hunter (pre-hard mode)",  # Pre hard mode update version
    TitleID.Survivor: "Survivor",
    TitleID.KoaBD: "Kind Of A Big Deal",
    TitleID.Deprecated_TreasureHunter: "Deprecated Treasure Hunter (non-account wide)",  # Old title, non-account bound
    TitleID.Deprecated_Wisdom: "Deprecated Wisdom (non-account wide)",  # Old title, non-account bound
    TitleID.ProtectorTyria: "Protector of Tyria",
    TitleID.ProtectorCantha: "Protector of Cantha",
    TitleID.Lucky: "Lucky",
    TitleID.Unlucky: "Unlucky",
    TitleID.Sunspear: "Sunspear",
    TitleID.CartographerNightfall: "Elona Exploration",
    TitleID.ProtectorElona: "Protector of Elona",
    TitleID.Lightbringer: "Lightbringer",
    TitleID.LDoA: "Defender of Ascalon",
    TitleID.Commander: "Commander",
    TitleID.Gamer: "Gamer",
    TitleID.SkillHunterTyria: "Tyrian Skill Hunter",
    TitleID.VanquisherTyria: "Tyrian Vanquisher",
    TitleID.SkillHunterCantha: "Canthan Skill Hunter",
    TitleID.VanquisherCantha: "Canthan Vanquisher",
    TitleID.SkillHunterElona: "Elonian Skill Hunter",
    TitleID.VanquisherElona: "Elonian Vanquisher",
    TitleID.LegendaryCartographer: "Legendary Cartographer",
    TitleID.LegendaryGuardian: "Legendary Guardian",
    TitleID.LegendarySkillHunter: "Legendary Skill Hunter",
    TitleID.LegendaryVanquisher: "Legendary Vanquisher",
    TitleID.Sweet_Tooth: "Sweet Tooth",
    TitleID.GuardianTyria: "Tyrian Guardian",
    TitleID.GuardianCantha: "Canthan Guardian",
    TitleID.GuardianElona: "Elonian Guardian",
    TitleID.Asuran: "Asuran",
    TitleID.Deldrimor: "Deldrimor",
    TitleID.Ebon_Vanguard: "Vanguard",
    TitleID.Norn: "Norn",
    TitleID.MasterOfTheNorth: "Master of the North",
    TitleID.PartyAnimal: "Party Animal",
    TitleID.Zaishen: "Zaishen",
    TitleID.TreasureHunter: "Treasure Hunter",
    TitleID.Wisdom: "Wisdom",
    TitleID.Codex: "Codex",
    TitleID.None_: "None",  # Use 'None_' to avoid Python reserved keyword
}

#region Title Tiers
class TitleTier:
    def __init__(self, tier: int, name: str, required: int):
        self.tier = tier
        self.name = name
        self.required = required
                
TITLE_TIERS: Dict[int, List[TitleTier]] = {
    TitleID.Kurzick: [  # Kurzick
        TitleTier(1,  "Kurzick Supporter",      100_000),
        TitleTier(2,  "Friend of the Kurzicks", 250_000),
        TitleTier(3,  "Companion of the Kurzicks", 400_000),
        TitleTier(4,  "Ally of the Kurzicks",   550_000),
        TitleTier(5,  "Sentinel of the Kurzicks", 875_000),
        TitleTier(6,  "Steward of the Kurzicks", 1_200_000),
        TitleTier(7,  "Defender of the Kurzicks", 1_850_000),
        TitleTier(8,  "Warden of the Kurzicks", 2_500_000),
        TitleTier(9,  "Bastion of the Kurzicks", 3_750_000),
        TitleTier(10, "Champion of the Kurzicks", 5_000_000),
        TitleTier(11, "Hero of the Kurzicks",  7_500_000),
        TitleTier(12, "Savior of the Kurzicks", 10_000_000),
    ],
    TitleID.Luxon: [  # Luxon
        TitleTier(1,  "Luxon Supporter",        100_000),
        TitleTier(2,  "Friend of the Luxons",   250_000),
        TitleTier(3,  "Companion of the Luxons", 400_000),
        TitleTier(4,  "Ally of the Luxons",     550_000),
        TitleTier(5,  "Sentinel of the Luxons", 875_000),
        TitleTier(6,  "Steward of the Luxons",  1_200_000),
        TitleTier(7,  "Defender of the Luxons", 1_850_000),
        TitleTier(8,  "Warden of the Luxons",   2_500_000),
        TitleTier(9,  "Bastion of the Luxons",  3_750_000),
        TitleTier(10, "Champion of the Luxons", 5_000_000),
        TitleTier(11, "Hero of the Luxons",    7_500_000),
        TitleTier(12, "Savior of the Luxons",  10_000_000),
    ],
    TitleID.Asuran: [  # Asuran
        TitleTier(1,  "Not Too Smelly",              1_000),
        TitleTier(2,  "Not Too Dopey",       4_000),
        TitleTier(3,  "Not Too Clumsy",      8_000),
        TitleTier(4,  "Not Too Boring",   16_000),
        TitleTier(5,  "Not Too Annoying",       26_000),
        TitleTier(6,  "Not Too Grumpy",  40_000),
        TitleTier(7,  "Not Too Silly",      56_000),
        TitleTier(8,  "Not Too Lazy",       80_000),
        TitleTier(9,  "Not Too Foolish",     110_000),
        TitleTier(10, "Not Too Shabby",       160_000),
    ],
    TitleID.Deldrimor: [  # Deldrimor
        TitleTier(1,  "Delver",              1_000),
        TitleTier(2,  "Stout Delver",       4_000),
        TitleTier(3,  "Gutsy Delver",      8_000),
        TitleTier(4,  "Risky Delver",   16_000),
        TitleTier(5,  "Bold Delver",       26_000),
        TitleTier(6,  "Daring Delver",  40_000),
        TitleTier(7,  "Adventurous Delver",      56_000),
        TitleTier(8,  "Courageous Delver",       80_000),
        TitleTier(9,  "Epic Delver",     110_000),
        TitleTier(10, "Legendary Delver",       160_000),
    ],
    TitleID.Ebon_Vanguard: [  # Ebon Vanguard
        TitleTier(1,  "Agent",              1_000),
        TitleTier(2,  "Covert Agent",       4_000),
        TitleTier(3,  "Stealth Agent",      8_000),
        TitleTier(4,  "Mysterious Agent",   16_000),
        TitleTier(5,  "Shadow Agent",       26_000),
        TitleTier(6,  "Underground Agent",  40_000),
        TitleTier(7,  "Special Agent",      56_000),
        TitleTier(8,  "Valued Agent",       80_000),
        TitleTier(9,  "Superior Agent",     110_000),
        TitleTier(10, "Secret Agent",       160_000),
    ],
    TitleID.Norn: [  # Norn
        TitleTier(1,  "Slayer of Imps",              1_000),
        TitleTier(2,  "Slayer of Beasts",       4_000),
        TitleTier(3,  "Slayer of Nightmares",      8_000),
        TitleTier(4,  "Slayer of Giants",   16_000),
        TitleTier(5,  "Slayer of Wurms",       26_000),
        TitleTier(6,  "Slayer of Demons",  40_000),
        TitleTier(7,  "Slayer of Heroes",      56_000),
        TitleTier(8,  "Slayer of Champions",       80_000),
        TitleTier(9,  "Slayer of Hordes",     110_000),
        TitleTier(10, "Slayer of All",       160_000),
    ],
    TitleID.MasterOfTheNorth: [  # Master of the North
        TitleTier(1,  "Adventurer of the North", 100),
        TitleTier(2,  "Pioneer of the North",   200),
        TitleTier(3,  "Veteran of the North",      350),
        TitleTier(4,  "Conqueror of the North",   550),
        TitleTier(5,  "Master of the North",       750),
        TitleTier(6,  "Legendary Master of the North",  1000),
    ],
    TitleID.Lightbringer: [  # Lightbringer
        TitleTier(1,  "Lightbringer",          100),
        TitleTier(2,  "Adept Lightbringer",     300),
        TitleTier(3,  "Brave Lightbringer",     1_000),
        TitleTier(4,  "Mighty Lightbringer",    2_500),
        TitleTier(5,  "Conquering Lightbringer",7_500),
        TitleTier(6,  "Vanquishing Lightbringer",15_000),
        TitleTier(7,  "Revered Lightbringer",   25_000),
        TitleTier(8,  "Holy Lightbringer",      50_000),
    ],
    TitleID.Sunspear: [  # Sunspear
        TitleTier(1,  "Sunspear Sergeant",          50),
        TitleTier(2,  "Sunspear Master Sergeant",   100),
        TitleTier(3,  "Second Spear",               175),
        TitleTier(4,  "First Spear",                300),
        TitleTier(5,  "Sunspear Captain",           500),
        TitleTier(6,  "Sunspear Commander",         1_000),
        TitleTier(7,  "Sunspear General",           2_500),
        TitleTier(8,  "Sunspear Castellan",         7_500),
        TitleTier(9,  "Spearmarshal",               15_000),
        TitleTier(10, "Legendary Spearmarshal",     50_000),
    ],
    TitleID.Hero: [  # Hero
        TitleTier(1,  "Hero", 25),
        TitleTier(2,  "Fierce Hero", 75),
        TitleTier(3,  "Mighty Hero", 180),
        TitleTier(4,  "Deadly Hero", 360),
        TitleTier(5,  "Terrifying Hero", 600),
        TitleTier(6,  "Conquering Hero", 1_000),
        TitleTier(7,  "Subjugating Hero", 1_680),
        TitleTier(8,  "Vanquishing Hero", 2_800),
        TitleTier(9,  "Renowned Hero", 4_665),
        TitleTier(10, "Illustrious Hero", 7_750),
        TitleTier(11, "Eminent Hero", 12_960),
        TitleTier(12, "King's Hero", 21_600),
        TitleTier(13, "Emperor's Hero", 36_000),
        TitleTier(14, "Balthazar's Hero", 60_000),
        TitleTier(15, "Legendary Hero", 100_000),
    ],
    TitleID.Wisdom: [  # Wisdom
        TitleTier(1,  "Seeker of Wisdom", 100),
        TitleTier(2,  "Collector of Wisdom", 250),
        TitleTier(3,  "Devotee of Wisdom", 550),
        TitleTier(4,  "Devourer of Wisdom", 1_200),
        TitleTier(5,  "Font of Wisdom", 2_500),
        TitleTier(6,  "Oracle of Wisdom", 5_000),
        TitleTier(7,  "Source of Wisdom", 10_000),
    ],
    TitleID.PartyAnimal: [  # Party Animal
        TitleTier(1,  "Party Animal", 1_000),
        TitleTier(2,  "Life of the Party", 10_000),
    ],
    TitleID.Drunkard: [  # Drunkard
        TitleTier(1,  "Drunkard", 1_000),
        TitleTier(2,  "Incorrigible Ale-Hound", 10_000),
    ],
    TitleID.Sweet_Tooth: [  # Sweet Tooth
        TitleTier(1,  "Sweet Tooth", 1_000),
        TitleTier(2,  "Connoisseur of Confectionaries", 10_000),
    ],
    TitleID.Survivor: [  # Survivor
        TitleTier(1,  "Survivor", 140_600),
        TitleTier(2,  "Indomitable Survivor", 587_500),
        TitleTier(3,  "Legendary Survivor", 1_337_500),
    ],
    TitleID.TreasureHunter: [  # Treasure Hunter
        TitleTier(1,  "Treasure Hunter", 100),
        TitleTier(2,  "Adept Treasure Hunter", 250),
        TitleTier(3,  "Advanced Treasure Hunter", 550),
        TitleTier(4,  "Expert Treasure Hunter", 1_200),
        TitleTier(5,  "Elite Treasure Hunter", 2_500),
        TitleTier(6,  "Master Treasure Hunter", 5_000),
        TitleTier(7,  "Grandmaster Treasure Hunter", 10_000),
    ],
    TitleID.Lucky: [  # Lucky
        TitleTier(1,  "Charmed", 50_000),
        TitleTier(2,  "Lucky", 100_000),
        TitleTier(3,  "Favored", 250_000),
        TitleTier(4,  "Prosperous", 500_000),
        TitleTier(5,  "Golden", 1_000_000),
        TitleTier(6,  "Blessed by Fate", 2_500_000),
    ],
    TitleID.Unlucky: [  # Unlucky
        TitleTier(1,  "Hapless", 5_000),
        TitleTier(2,  "Unlucky", 10_000),
        TitleTier(3,  "Unfavored", 25_000),
        TitleTier(4,  "Tragic", 50_000),
        TitleTier(5,  "Wretched", 100_000),
        TitleTier(6,  "Jinxed", 250_000),
        TitleTier(7,  "Cursed by Fate", 500_000),
    ],
    TitleID.KoaBD: [  # Big Deal
        TitleTier(1,  "Kind Of A Big Deal", 5),
        TitleTier(2,  "People Know Me", 10),
        TitleTier(3,  "I'm Very Important", 15),
        TitleTier(4,  "I Have Many Leather-Bound Books", 20),
        TitleTier(5,  "My Guild Hall Smells of Rich Mahogany", 25),
        TitleTier(6,  "God Walking Amongst Mere Mortals", 30),
    ],
    TitleID.Gladiator: [  # Gladiator
        TitleTier(1,  "Gladiator", 500),
        TitleTier(2,  "Fierce Gladiator", 1_000),
        TitleTier(3,  "Mighty Gladiator", 2_000),
        TitleTier(4,  "Deadly Gladiator", 3_360),
        TitleTier(5,  "Terrifying Gladiator", 5_600),
        TitleTier(6,  "Conquering Gladiator", 9_320),
        TitleTier(7,  "Subjugating Gladiator", 15_500),
        TitleTier(8,  "Vanquishing Gladiator", 25_920),
        TitleTier(9,  "King's Gladiator", 43_200),
        TitleTier(10, "Emperor's Gladiator", 72_000),
        TitleTier(11, "Balthazar's Gladiator", 120_000),
        TitleTier(12, "Legendary Gladiator", 200_000),
    ],
    TitleID.Gamer: [  # Gamer
        TitleTier(1,  "Skillz", 1_000),
        TitleTier(2,  "Pro Skillz", 2_000),
        TitleTier(3,  "Numchuck Skillz", 4_000),
        TitleTier(4,  "Mad Skillz", 7_000),
        TitleTier(5,  "Über Micro Skillz", 12_000),
        TitleTier(6,  "Gosu Skillz", 20_000),
        TitleTier(7,  "1337 Skillz", 32_500),
        TitleTier(8,  "iddqd Skillz", 50_000),
        TitleTier(9,  "T3h Haxz0rz Skillz", 70_000),
        TitleTier(10, "Pure Pwnage Skillz", 90_000),
        TitleTier(11, "These skillz go to", 110_000),
        TitleTier(12, "Real Ultimate Power Skillz", 135_000),
    ],
    TitleID.Codex: [  # Codex title track
        TitleTier(1,  "Codex Initiate",      500),
        TitleTier(2,  "Codex Acolyte",       1_000),
        TitleTier(3,  "Codex Disciple",      2_000),
        TitleTier(4,  "Codex Zealot",        3_360),
        TitleTier(5,  "Codex Stalwart",      5_600),
        TitleTier(6,  "Codex Adept",         9_320),
        TitleTier(7,  "Codex Exemplar",      15_500),
        TitleTier(8,  "Codex Prodigy",       25_920),
        TitleTier(9,  "Codex Champion",      43_200),
        TitleTier(10, "Codex Paragon",       72_000),
        TitleTier(11, "Codex Master",        120_000),
        TitleTier(12, "Codex Grandmaster",  200_000),
    ],
    TitleID.Champion: [  # Champion title track
        TitleTier(1,  "Champion",      25),
        TitleTier(2,  "Fierce Champion",       50),
        TitleTier(3,  "Mighty Champion",      100),
        TitleTier(4,  "Deadly Champion",        168),
        TitleTier(5,  "Terrifying Champion",      280),
        TitleTier(6,  "Conquering Champion",         466),
        TitleTier(7,  "Subjugating Champion",      775),
        TitleTier(8,  "Vanquishing Champion",       1_296),
        TitleTier(9,  "King's Champion",      2_160),
        TitleTier(10, "Emperor's Champion",       3_600),
        TitleTier(11, "Balthazar's Champion",        6_000),
        TitleTier(12, "Legendary Champion",      10_000),
    ],
    TitleID.Commander: [  # Commander title track
        TitleTier(1,  "Commander",      125),
        TitleTier(2,  "Victorious Commander",       250),
        TitleTier(3,  "Triumphant Commander",      500),
        TitleTier(4,  "Keen Commander",      840),
        TitleTier(5,  "Battle Commander",      1_400),
        TitleTier(6,  "Field Commander",      2_330),
        TitleTier(7,  "Lieutenant Commander",      3_875),
        TitleTier(8,  "Wing Commander",      6_480),
        TitleTier(9,  "Cobra Commander",      10_800),
        TitleTier(10, "Supreme Commander",       18_000),
        TitleTier(11, "Master And Commander",        30_000),
        TitleTier(12, "Legendary Commander",      50_000),
    ],
    TitleID.Zaishen: [  # Zaishen
        TitleTier(1,  "Zaishen Supporter",      250),
        TitleTier(2,  "Friend of the Zaishen",       500),
        TitleTier(3,  "Companion of the Zaishen",      1_000),
        TitleTier(4,  "Ally of the Zaishen",      1_680),
        TitleTier(5,  "Sentinel of the Zaishen",      2_800),
        TitleTier(6,  "Steward of the Zaishen",      4_660),
        TitleTier(7,  "Defender of the Zaishen",      7_750),
        TitleTier(8,  "Warden of the Zaishen",      12_960),
        TitleTier(9,  "Bastion of the Zaishen",      21_600),
        TitleTier(10, "Champion of the Zaishen",      36_000),
        TitleTier(11, "Hero of the Zaishen",      60_000),
        TitleTier(12, "Legendary Hero of the Zaishen",      100_000),
    ],
    TitleID.LDoA: [  # LDoA
        TitleTier(1,  "Legendary Defender of Ascalon",20),
    ],
    TitleID.CartographerProphecies: [  # Cartographer - Prophecies
        TitleTier(1,  "Tyrian Explorer",      600),
        TitleTier(2,  "Tyrian Pathfinder",       700),
        TitleTier(3,  "Tyrian Trailblazer",      800),
        TitleTier(4,  "Tyrian Cartographer",     900),
        TitleTier(5,  "Tyrian Master Cartographer", 950),
        TitleTier(6,  "Tyrian Grandmaster Cartographer", 1000),
    ],
    TitleID.CartographerFactions: [  # Cartographer - Factions
        TitleTier(1,  "Canthan Explorer",      600),
        TitleTier(2,  "Canthan Pathfinder",       700),
        TitleTier(3,  "Canthan Trailblazer",      800),
        TitleTier(4,  "Canthan Cartographer",     900),
        TitleTier(5,  "Canthan Master Cartographer", 950),
        TitleTier(6,  "Canthan Grandmaster Cartographer", 1000),
    ],
    TitleID.CartographerNightfall: [  # Cartographer - Nightfall
        TitleTier(1,  "Elonian Explorer",      600),
        TitleTier(2,  "Elonian Pathfinder",       700),
        TitleTier(3,  "Elonian Trailblazer",      800),
        TitleTier(4,  "Elonian Cartographer",     900),
        TitleTier(5,  "Elonian Master Cartographer", 950),
        TitleTier(6,  "Elonian Grandmaster Cartographer", 1000),
    ],
    TitleID.LegendaryCartographer: [  # Legendary Cartographer
        TitleTier(1,  "Legendary Cartographer", 3),
    ],
    TitleID.ProtectorTyria: [  # Protector of Tyria
        TitleTier(1,  "Protector of Tyria", 25),
    ],
    TitleID.ProtectorCantha: [  # Protector of Cantha
        TitleTier(1,  "Protector of Cantha", 13),
    ],
    TitleID.ProtectorElona: [  # Protector of Elona
        TitleTier(1,  "Protector of Elona", 20),
    ],
    TitleID.GuardianTyria: [  # Guardian of Tyria
        TitleTier(1,  "Guardian of Tyria", 25),
    ],
    TitleID.GuardianCantha: [  # Guardian of Cantha
        TitleTier(1,  "Guardian of Cantha", 13),
    ],
    TitleID.GuardianElona: [  # Guardian of Elona
        TitleTier(1,  "Guardian of Elona", 20),
    ],
    TitleID.LegendaryGuardian: [  # Legendary Guardian
        TitleTier(1,  "Legendary Guardian", 6),
    ],
    TitleID.VanquisherTyria: [  # Vanquisher of Tyria
        TitleTier(1,  "Tyrian Vanquisher", 54),
    ],
    TitleID.VanquisherCantha: [  # Vanquisher of Cantha
        TitleTier(1,  "Canthan Vanquisher", 33),
    ],
    TitleID.VanquisherElona: [  # Vanquisher of Elona
        TitleTier(1,  "Elonian Vanquisher", 34),
    ],
    TitleID.LegendaryVanquisher: [  # Legendary Vanquisher
        TitleTier(1,  "Legendary Vanquisher", 3),
    ],
    TitleID.SkillHunterTyria: [  # Skill Hunter - Tyria
        TitleTier(1,  "Tyrian Elite Skill Hunter", 90),
    ],
    TitleID.SkillHunterCantha: [  # Skill Hunter - Cantha
        TitleTier(1,  "Canthan Elite Skill Hunter", 120),
    ],
    TitleID.SkillHunterElona: [  # Skill Hunter - Elona
        TitleTier(1,  "Elonian Elite Skill Hunter", 140),
    ],
    TitleID.LegendarySkillHunter: [  # Legendary Skill Hunter
        TitleTier(1,  "Legendary Skill Hunter", 3),
    ],
}

TITLE_CATEGORIES = {
    "Reputation": [TitleID.Asuran,
                    TitleID.Deldrimor,
                    TitleID.Ebon_Vanguard,
                    TitleID.Norn,
                    TitleID.Lightbringer,
                    TitleID.Sunspear,
    ],
    "Competitive": [TitleID.Kurzick,
                    TitleID.Luxon,
                    TitleID.Hero,
                    TitleID.Gladiator,
                    TitleID.Codex,
                    TitleID.Champion,
                    TitleID.Commander,
                    TitleID.Zaishen,   
                    TitleID.Gamer,                
    ],
    "Cartographer": [TitleID.CartographerProphecies,
                        TitleID.CartographerFactions,
                        TitleID.CartographerNightfall,
                        TitleID.LegendaryCartographer,
    ],
    "Protector / Guardian":    [TitleID.ProtectorTyria,
                        TitleID.ProtectorCantha,
                        TitleID.ProtectorElona,
                        TitleID.GuardianTyria,
                        TitleID.GuardianCantha,
                        TitleID.GuardianElona,
                        TitleID.LegendaryGuardian,
        ],
    "Vanquisher":  [TitleID.VanquisherTyria,
                        TitleID.VanquisherCantha,
                        TitleID.VanquisherElona,
                        TitleID.LegendaryVanquisher,
        ],
    "Skill Hunter": [TitleID.SkillHunterTyria,
                        TitleID.SkillHunterCantha,
                        TitleID.SkillHunterElona,
                        TitleID.LegendarySkillHunter,
        ],
    "Item Consumption": [TitleID.PartyAnimal,
                            TitleID.Drunkard,
                            TitleID.Sweet_Tooth,
    ],
    "Completion": [TitleID.Wisdom, 
                    TitleID.KoaBD, 
                    TitleID.LDoA,                    
                    TitleID.Lucky,
                    TitleID.Unlucky,
                    TitleID.MasterOfTheNorth,
                    TitleID.TreasureHunter,
        ],
}
# endregion
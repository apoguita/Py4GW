from enum import Enum
from enum import IntEnum

# region Titles
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
    None_ = 0xFF  # Use 'None_' to avoid using the reserved keyword 'None'


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

# endregion
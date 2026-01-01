from enum import Enum
from enum import IntEnum




# region Range
class Range(Enum):
    Touch = 144.0
    Adjacent = 166.0
    Nearby = 252.0
    Area = 322.0
    Earshot = 1012.0
    Spellcast = 1248.0
    Spirit = 2500.0
    SafeCompass = 4800.0  # made up distance to make easy checks
    Compass = 5000.0

# endregion


# region DyeColor
class DyeColor(IntEnum):
    NoColor = 0
    Blue = 2
    Green = 3
    Purple = 4
    Red = 5
    Yellow = 6
    Brown = 7
    Orange = 8
    Silver = 9
    Black = 10
    Gray = 11
    White = 12
    Pink = 13


# endregion
# region Profession
class Profession(IntEnum):
    _None = 0
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


Profession_Names = {
    Profession._None: "None",
    Profession.Warrior: "Warrior",
    Profession.Ranger: "Ranger",
    Profession.Monk: "Monk",
    Profession.Necromancer: "Necromancer",
    Profession.Mesmer: "Mesmer",
    Profession.Elementalist: "Elementalist",
    Profession.Assassin: "Assassin",
    Profession.Ritualist: "Ritualist",
    Profession.Paragon: "Paragon",
    Profession.Dervish: "Dervish",
}

class ProfessionShort(IntEnum):
    _ = 0
    W = 1
    R = 2
    Mo = 3
    N = 4
    Me = 5
    E = 6
    A = 7
    Rt = 8
    P = 9
    D = 10
    
ProfessionShort_Names = {
    ProfessionShort._: "None",
    ProfessionShort.W: "W",
    ProfessionShort.R: "R",
    ProfessionShort.Mo: "Mo",
    ProfessionShort.N: "N",
    ProfessionShort.Me: "Me",
    ProfessionShort.E: "E",
    ProfessionShort.A: "A",
    ProfessionShort.Rt: "Rt",
    ProfessionShort.P: "P",
    ProfessionShort.D: "D",
}


# endregion
# region Allegiance
class Allegiance(IntEnum):
    Unknown = 0
    Ally = 1  # 0x1 = ally/non-attackable
    Neutral = 2  # 0x2 = neutral
    Enemy = 3  # 0x3 = enemy
    SpiritPet = 4  # 0x4 = spirit/pet
    Minion = 5  # 0x5 = minion
    NpcMinipet = 6  # 0x6 = npc/minipet
    
AllegianceNames = {
    Allegiance.Unknown: "Unknown",
    Allegiance.Ally: "Ally",
    Allegiance.Neutral: "Neutral",
    Allegiance.Enemy: "Enemy",
    Allegiance.SpiritPet: "Spirit/Pet",
    Allegiance.Minion: "Minion",
    Allegiance.NpcMinipet: "NPC/Minipet",
}


# AllieganceDonation
class FactionAllegiance(IntEnum):
    Kurzick = 0
    Luxon = 1

#FactionType
class FactionType(IntEnum):
    Kurzick = 0
    Luxon = 1
    Imperial = 2
    Balthazar = 3

# endregion
# region Mod structs
class Ailment(IntEnum):
    Bleeding = 222
    Blind = 223
    Crippled = 225
    Deep_Wound = 226
    Disease = 227
    Poison = 228
    Dazed = 229
    Weakness = 230


class Reduced_Ailment(IntEnum):
    Bleeding = 0
    Blind = 1
    Crippled = 3
    Deep_Wound = 4
    Disease = 5
    Poison = 6
    Dazed = 7
    Weakness = 8


#region DamageType
class DamageType(IntEnum):
    Blunt = 0
    Piercing = 1
    Slashing = 2
    Cold = 3
    Lightning = 4
    Fire = 5
    Chaos = 6
    Dark = 7
    Holy = 8
    unknown_9 = 9
    unknown_10 = 10
    Earth = 11
    unknown_12 = 12
    unknown_13 = 13
    unknown_14 = 14
    unknown_15 = 15


#region WeaponType
class Weapon(IntEnum):
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
    
Weapon_Names = {
    Weapon.Unknown: "Unknown",
    Weapon.Bow: "Bow",  
    Weapon.Axe: "Axe",
    Weapon.Hammer: "Hammer",
    Weapon.Daggers: "Daggers",
    Weapon.Scythe: "Scythe",
    Weapon.Spear: "Spear",
    Weapon.Sword: "Sword",
    Weapon.Scepter: "Scepter",
    Weapon.Scepter2: "Scepter2",
    Weapon.Wand: "Wand",
    Weapon.Staff1: "Staff1",
    Weapon.Staff: "Staff",
    Weapon.Staff2: "Staff2",
    Weapon.Staff3: "Staff3",
    Weapon.Unknown1: "Unknown1",
    Weapon.Unknown2: "Unknown2",
    Weapon.Unknown3: "Unknown3",
    Weapon.Unknown4: "Unknown4",
    Weapon.Unknown5: "Unknown5",
    Weapon.Unknown6: "Unknown6",
    Weapon.Unknown7: "Unknown7",
    Weapon.Unknown8: "Unknown8",
    Weapon.Unknown9: "Unknown9",
    Weapon.Unknown10: "Unknown10",
}
   
#region WeaporReq 
class WeaporReq(IntEnum):
    None_ = 0
    Axe = 1
    Bow = 2
    Dagger = 8
    Hammer = 16
    Scythe = 32
    Spear = 64
    Sword = 128
    Melee = 185
    

#region SkillType  
class SkillType ( IntEnum):
    None_ = 0
    Bounty = 1
    Scroll = 2
    Stance = 3
    Hex = 4
    Spell = 5
    Enchantment = 6
    Signet = 7
    Condition = 8
    Well = 9
    Skill = 10
    Ward = 11
    Glyph = 12
    Title = 13
    Attack = 14
    Shout = 15
    Skill2 = 16
    Passive = 17
    Environmental = 18
    Preparation = 19
    PetAttack = 20
    Trap = 21
    Ritual = 22
    EnvironmentalTrap = 23
    ItemSpell = 24
    WeaponSpell = 25
    Form = 26
    Chant = 27
    EchoRefrain = 28
    Disguise = 29


#region Attribute
class Attribute(IntEnum):
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


#region Inscription
class Inscription(IntEnum):
    Fear_Cuts_Deeper = 0
    I_Can_See_Clearly_Now = 1
    Swift_as_the_Wind = 3
    Strenght_of_Body = 4
    Cast_Out_the_Unclean = 5
    Pure_of_Heart = 6
    Soundness_of_Mind = 7
    Only_the_Strong_Survive = 8

    Not_the_Face = 134
    Leaf_on_the_Wind = 136
    Like_a_Rolling_Stone = 138
    Riders_on_the_Storm = 140
    Sleep_Now_in_the_Fire = 142
    Trough_Thick_and_Thin = 144
    The_Riddle_of_Steel = 146


# endregion

#region Experience
CAP_EXPERIENCE = 182600
CAP_STEP = 15000
EXPERIENCE_PROGRESSION = [
    (1, 0, 2000),
    (2, 2000, 2600),
    (3, 4600, 3200),
    (4, 7800, 3800),
    (5, 11600, 4400),
    (6, 16000, 5000),
    (7, 21000, 5600),
    (8, 26600, 6200),
    (9, 32800, 6800),
    (10, 39600, 7400),
    (11, 47000, 8000),
    (12, 55000, 8600),
    (13, 63600, 9200),
    (14, 72800, 9800),
    (15, 82600, 10400),
    (16, 93000, 11000),
    (17, 104000, 11600),
    (18, 115600, 12200),
    (19, 127800, 12800),
    (20, 140600, 13400),
    (21, 154000, 14000),
    (22, 168000, 14600),
]
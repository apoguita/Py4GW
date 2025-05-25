from ctypes import Structure, c_int, c_float, c_bool
from enum import Enum, IntEnum
from .constants import (
    MAX_NUM_PLAYERS,
    NUMBER_OF_SKILLS,
    MAX_NUMBER_OF_BUFFS
)


class PlayerBuff(Structure):
    _fields_ = [
        ("PlayerID", c_int),
        ("Buff_id", c_int),
        ("LastUpdated", c_int),
    ]
    

class PlayerStruct(Structure):
    _fields_ = [
        ("PlayerID", c_int),
        ("Energy_Regen", c_float),
        ("Energy", c_float),
        ("IsActive", c_bool),
        ("IsHero", c_bool),
        ("IsFlagged", c_bool),
        ("FlagPosX", c_float),
        ("FlagPosY", c_float),
        ("FollowAngle", c_float),
        ("LastUpdated", c_int),
    ]


class CandidateStruct(Structure):
    _fields_ = [
        ("PlayerID", c_int),
        ("MapID", c_int),
        ("MapRegion", c_int),
        ("MapDistrict", c_int),
        ("InvitedBy", c_int), 
        ("SummonedBy", c_int),
        ("LastUpdated", c_int),
    ]


class MemSkill(Structure):
    _fields_ = [
        ("Active", c_bool),
    ]

class GameOptionStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Following", c_bool),
        ("Avoidance", c_bool), 
        ("Looting", c_bool), 
        ("Targeting", c_bool),
        ("Combat", c_bool),
        ("Skills", MemSkill * NUMBER_OF_SKILLS),
        ("WindowVisible", c_bool),
    ] 

class GameStruct(Structure):
    _fields_ = [
        ("Players", PlayerStruct * MAX_NUM_PLAYERS),
        ("Candidates", CandidateStruct * MAX_NUM_PLAYERS),
        ("GameOptions", GameOptionStruct * MAX_NUM_PLAYERS),
        ("PlayerBuffs", PlayerBuff * MAX_NUMBER_OF_BUFFS),
    ]


class Skilltarget (IntEnum):
    Enemy = 0
    EnemyCaster = 1
    EnemyMartial = 2
    EnemyMartialMelee = 3
    EnemyMartialRanged = 4
    Ally = 5
    AllyCaster = 6
    AllyMartial = 7
    AllyMartialMelee = 8
    AllyMartialRanged = 9
    OtherAlly = 10
    DeadAlly = 11
    Self = 12
    Corpse = 13
    Minion = 14
    Spirit = 15
    Pet = 16
    #added targets
    
    EnemyClustered = 22
    EnemyAttacking = 23
    EnemyCasting = 24
    EnemyCastingSpell = 25
    EnemyInjured = 26
    EnemyConditioned = 27
    EnemyHexed = 28
    EnemyDegenHexed = 29
    EnemyEnchanted = 30
    EnemyMoving = 31
    EnemyKnockedDown = 32
    
    
    
   
class SkillNature (Enum):
    Offensive = 0
    Enchantment_Removal = 1
    Healing = 2
    Hex_Removal = 3
    Condi_Cleanse = 4
    Buff = 5
    EnergyBuff = 6
    Neutral = 7
    SelfTargeted = 8
    Resurrection = 9
    Interrupt = 10
    CustomA = 11
    CustomB = 12
    CustomC = 13
    CustomD = 14
    CustomE = 15
    CustomF = 16
    CustomG = 17
    CustomH = 18
    CustomI = 19
    CustomJ = 20
    CustomK = 21
    CustomL = 22
    CustomM = 23
    CustomN = 24
    OffensiveA = 25
    OffensiveB = 26
    OffensiveC = 27
    



class SkillType (Enum):
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




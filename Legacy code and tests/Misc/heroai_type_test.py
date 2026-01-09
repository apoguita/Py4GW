from Py4GWCoreLib import *

from ctypes import Structure, c_int, c_float, c_bool
from enum import Enum

NUMBER_OF_SKILLS = 8
MAX_NUM_PLAYERS = 8
MAX_NUMBER_OF_BUFFS = 240

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
        ("Targetting", c_bool),
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


class Skilltarget (Enum):
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
    
    
   
class SkillNature (Enum):
    Offensive = 0
    Enchantment_Removal = 1
    Healing = 2
    Hex_Removal = 3
    Condi_Cleanse = 4
    Buff = 5
    EnergyBuff = 6
    Neutral = 7
    SelfTargetted = 8
    Resurrection = 9
    Interrupt = 10


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





MODULE_NAME = "type_tester"

def test_structure(struct_cls, struct_name):
    """Helper function to test if a structure can be instantiated."""
    try:
        instance = struct_cls()
        Py4GW.Console.Log(MODULE_NAME, f"[SUCCEED] {struct_name} instantiated successfully.", Py4GW.Console.MessageType.Info)
    except AttributeError as e:
        Py4GW.Console.Log(MODULE_NAME, f"[FAIL] {struct_name} FAILED: {str(e)}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"[FAIL] {struct_name} ERROR: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, traceback.format_exc(), Py4GW.Console.MessageType.Debug)

        
def DrawWindow():
    try:
        if PyImGui.begin("type_tester"):
            if PyImGui.button("Run Tests"):
                Py4GW.Console.Log(MODULE_NAME, "=== Testing ctypes Structures in types.py ===", Py4GW.Console.MessageType.Info)

                test_structure(PlayerBuff, "PlayerBuff")
                test_structure(PlayerStruct, "PlayerStruct")
                test_structure(CandidateStruct, "CandidateStruct")
                test_structure(MemSkill, "MemSkill")
                test_structure(GameOptionStruct, "GameOptionStruct")
                test_structure(GameStruct, "GameStruct")
                
                Py4GW.Console.Log(MODULE_NAME, "=== Test Complete ===", Py4GW.Console.MessageType.Info)

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)


def main():
    DrawWindow()

if __name__ == "__main__":
    main()

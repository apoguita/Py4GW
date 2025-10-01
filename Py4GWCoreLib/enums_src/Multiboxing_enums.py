from enum import Enum
from enum import IntEnum

class SharedCommandType(IntEnum):
    NoCommand = 0
    TravelToMap = 1
    InviteToParty = 2
    InteractWithTarget = 3
    TakeDialogWithTarget = 4
    GetBlessing = 5
    OpenChest = 6
    PickUpLoot = 7
    UseSkill = 8
    Resign = 9
    PixelStack = 10
    PCon = 11
    IdentifyItems = 12
    SalvageItems = 13
    MerchantItems = 14
    MerchantMaterials = 15
    DisableHeroAI = 16
    EnableHeroAI = 17
    LeaveParty = 18
    PressKey = 19
    DonateToGuild = 20
    SendDialogToTarget = 21
    LootEx = 999 # privately Handled Command, by Frenkey
    


class CombatPrepSkillsType(IntEnum):
    SpiritsPrep = 1
    ShoutsPrep = 2

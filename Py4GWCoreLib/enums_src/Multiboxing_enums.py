from enum import auto
from enum import IntEnum

class SharedCommandType(IntEnum):
    NoCommand = auto()
    TravelToMap = auto()
    InviteToParty = auto()
    InteractWithTarget = auto()
    TakeDialogWithTarget = auto()
    GetBlessing = auto()
    OpenChest = auto()
    PickUpLoot = auto()
    UseSkill = auto()
    Resign = auto()
    PixelStack = auto()
    PCon = auto()
    IdentifyItems = auto()
    SalvageItems = auto()
    MerchantItems = auto()
    MerchantMaterials = auto()
    DisableHeroAI = auto()
    EnableHeroAI = auto()
    LeaveParty = auto()
    PressKey = auto()
    DonateToGuild = auto()
    SendDialogToTarget = auto()
    BruteForceUnstuck = auto()
    SetWindowGeometry = auto()
    SetWindowActive = auto()
    SetWindowTitle = auto()
    SetBorderless = auto()
    SetAlwaysOnTop = auto()
    FlashWindow = auto()
    RequestAttention = auto()
    SetTransparentClickThrough = auto()
    SetOpacity = auto()
    UseItem = auto()
    PauseWidgets = auto()
    ResumeWidgets = auto()
    SwitchCharacter = auto()
    LoadSkillTemplate = auto()
    SkipCutscene = auto()
    SendDialog = auto()
    TravelToGuildHall = auto()
    
    SetActiveQuest = auto()
    AbandonQuest = auto()

    RestockAllPcons = auto()
    RestockConset = auto()
    RestockResurrectionScroll = auto()
    EnableWidget = auto()
    DisableWidget = auto()
    InventoryQuery = auto()
    EquipItem = auto()
    MerchantRules = auto()
    RefreshHeroAIBuilds = auto()

    #region privately Handled Commands
    MultiBoxing = auto() # privately Handled Command, by frenkey
    CustomBehaviors = auto() # privately Handled Command, used in CustomBehaviors widget
    UseSkillCombatPrep = auto() #handled in CombatPrep only by Mark
    LootEx = auto() # privately Handled Command, by frenkey
    Pycons = auto()
    #endregion
    


class CombatPrepSkillsType(IntEnum):
    SpiritsPrep = auto()
    ShoutsPrep = auto()

from __future__ import annotations
from typing import List, Tuple

# REMOVE: `Botting` from the runtime import below
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Utils, Botting
import PyImGui
import re

MODULE_NAME = "sequential bot test"

auto_attack_timer = 0
auto_attack_threshold = 0
is_expired = False

# ----------------------- BOT CONFIGURATION --------------------------------------------

UNLOCK_SECONDARY = 0x813D08
UNLOCK_STORAGE = 0x84
ACCEPT_THE_THREAT_GROWS_REWARD = 0x815407
TAKE_GO_TO_TOGO_QUEST = 0x815501

bot = Botting("Factions Leveler")

#region bot_helpers
class BotLocals:
    def __init__(self):
        self.target_cupcake_count = 50
        self.target_honeycomb_count = 100

bot_locals = BotLocals()

#Helpers
def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.config.config_properties.pause_on_danger.disable()
    bot.config.config_properties.halt_on_death.enable()
    bot.config.config_properties.movement_timeout.set("value", 15000)
    bot.SpawnBonusItems()
    bot.config.upkeep.auto_combat.disable()
    bot.config.upkeep.imp.disable()
    bot.config.upkeep.birthday_cupcake.enable()
    bot.config.upkeep.morale.disable()
    bot.AddFSMCustomYieldState(withdraw_cupcakes, "Withdraw Cupcakes")

def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.config.config_properties.pause_on_danger.enable()
    bot.config.config_properties.halt_on_death.disable()
    bot.config.config_properties.movement_timeout.set("value",-1)
    bot.SpawnBonusItems()
    bot.config.upkeep.auto_combat.enable()
    bot.config.upkeep.imp.enable()
    bot.config.upkeep.birthday_cupcake.enable()
    bot.config.upkeep.morale.enable()

def EquipSkillBar(): 
    global bot, bot_locals
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if profession == "Warrior":
        yield from Routines.Yield.Skills.LoadSkillbar("OQcUEvq0jvIClLHAAAAAAAAAAA",log=False)
    elif profession == "Ranger":
        yield from Routines.Yield.Skills.LoadSkillbar("OgcUcLs1jvIPsv5yAAAAAAAAAA",log=False)
    elif profession == "Monk":
        yield from Routines.Yield.Skills.LoadSkillbar("OwcB0lkRuMAAAAAAAAAA",log=False)
    elif profession == "Necromancer":
        yield from Routines.Yield.Skills.LoadSkillbar("OAdTUOj8FxlTDAAAAAAAAAAA",log=False)
    elif profession == "Mesmer":
        yield from Routines.Yield.Skills.LoadSkillbar("OQdTAEx9FRDcZAAAAAAAAAAA",log=False)
    elif profession == "Elementalist":
        yield from Routines.Yield.Skills.LoadSkillbar("OgdToO28FRYcZAAAAAAAAAAA",log=False)
    elif profession == "Ritualist":
        yield from Routines.Yield.Skills.LoadSkillbar("OAej8JgGpNusvJAAAAAAAAAAAA",log=False)
    elif profession == "Assassin":
        yield from Routines.Yield.Skills.LoadSkillbar("OwBj0VfyoJPsLDAAAAAAAAAA",log=False)
    yield from Routines.Yield.wait(500)
    
def AddHenchmen():
    party_size = bot.GetProperty("live_data.Map.max_party_size") or 0
    zen_daijun_map_id = 213
    kaineng_map_id = 194

    if party_size <= 4:
        HEALER_ID = 1
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
        ConsoleLog("addhenchman",f"Added Henchman: {HEALER_ID}")
        yield from Routines.Yield.wait(250)
        SPIRITS_ID = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRITS_ID)
        ConsoleLog("addhenchman",f"Added Henchman: {SPIRITS_ID}")
        yield from Routines.Yield.wait(250)
        GUARDIAN_ID = 2
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(GUARDIAN_ID)
        ConsoleLog("addhenchman",f"Added Henchman: {GUARDIAN_ID}")
        yield from Routines.Yield.wait(250)
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor"):
        GUARDIAN_ID = 2
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(GUARDIAN_ID)
        yield from Routines.Yield.wait(250)
        DEADLY_ID = 3
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(DEADLY_ID)
        yield from Routines.Yield.wait(250)
        SHOCK_ID = 1
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SHOCK_ID)
        yield from Routines.Yield.wait(250)
        SPIRITS_ID = 4
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRITS_ID)
        yield from Routines.Yield.wait(250)
        HEALER_ID = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
        yield from Routines.Yield.wait(250)
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("The Marketplace"):
        HEALER_ID = 6
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
        yield from Routines.Yield.wait(250)
        SPIRIT_ID = 9
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRIT_ID)
        yield from Routines.Yield.wait(250)
        EARTH_ID = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(EARTH_ID)
        yield from Routines.Yield.wait(250)
        SHOCK_ID = 1
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SHOCK_ID)
        yield from Routines.Yield.wait(250)
        GRAVE_ID = 4
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(GRAVE_ID)
        yield from Routines.Yield.wait(250)
        FIGHTER_ID = 7
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(FIGHTER_ID)
        yield from Routines.Yield.wait(250)
        ILLUSION_ID = 3
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(ILLUSION_ID)
        yield from Routines.Yield.wait(250)
    elif GLOBAL_CACHE.Map.GetMapID() == zen_daijun_map_id:
        FIGHTER_ID = 3
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(FIGHTER_ID)
        yield from Routines.Yield.wait(250)
        EARTH_ID = 1
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(EARTH_ID)
        yield from Routines.Yield.wait(250)
        GRAVE_ID = 6
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(GRAVE_ID)
        yield from Routines.Yield.wait(250) 
        SPIRIT_ID = 8
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRIT_ID)
        yield from Routines.Yield.wait(250)
        HEALER_ID = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
        yield from Routines.Yield.wait(250)
    elif GLOBAL_CACHE.Map.GetMapID() == kaineng_map_id:
        warr1 = 2
        warr2 = 10
        ele = 4
        ele2 = 8
        necro = 7
        monk = 9
        ritu = 12
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(warr1)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(warr2)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(ele)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(ele2)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(necro)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(monk)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(ritu)
        yield from Routines.Yield.wait(250)
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Boreal Station"):
        warr1 = 7
        warr2 = 9
        necro =2
        ele1 = 3
        ele2 = 4
        monk1 = 6
        monk2 = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(warr1)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(warr2)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(necro)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(ele1)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(ele2)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(monk1)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(monk2)
        yield from Routines.Yield.wait(250)
    else:
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(1)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(2)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(3)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(4)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(5)
        yield from Routines.Yield.wait(250)

def ExitMonasteryOverlook(bot: Botting) -> None:
    bot.AddHeaderStep("Exit Monastery Overlook")
    bot.MoveTo(-7011, 5750,"Move to Ludo")
    LUDO_I_AM_SURE = 0x85
    bot.DialogAt(-7048,5817,LUDO_I_AM_SURE)
    bot.WaitForMapLoad(target_map_name="Shing Jea Monastery")
    
def ExitToCourtyard(bot: Botting) -> None:
    bot.AddHeaderStep("Exit To Courtyard")
    PrepareForBattle(bot)
    bot.MoveTo(-3480, 9460)
    bot.WaitForMapLoad(target_map_name="Linnok Courtyard")
    
def UnlockSecondaryProfession(bot: Botting) -> None:
    def assign_profession_unlocker_dialog():
        global bot
        if bot.GetProperty("live_data.Player.primary_profession") == "Assassin":
            yield from bot.helpers._interact_with_agent((-92, 9217),0x813D0E)
        else:
            yield from bot.helpers._interact_with_agent((-92, 9217),0x813D08)
        yield from Routines.Yield.wait(250)


    bot.AddHeaderStep("Unlock Secondary Profession")
    bot.MoveTo(-159, 9174)
    bot.AddFSMCustomYieldState(assign_profession_unlocker_dialog, "Update Secondary Profession Dialog")
    bot.CancelSkillRewardWindow()
    bot.CancelSkillRewardWindow()
    TAKE_SECONDARY_REWARD = 0x813D07
    bot.DialogAt(-92, 9217, TAKE_SECONDARY_REWARD)
    TAKE_MINISTER_CHO_QUEST = 0x813E01
    bot.DialogAt(-92, 9217, TAKE_MINISTER_CHO_QUEST)
    #ExitCourtyard
    bot.MoveTo(-3762, 9471)
    bot.WaitForMapLoad(target_map_name="Shing Jea Monastery")

def UnlockXunlaiStorage(bot: Botting) -> None:
    bot.AddHeaderStep("Unlock Xunlai Storage")
    path_to_xunlai: List[Tuple[float, float]] = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3869, 10346),]
    bot.FollowPath(path_to_xunlai,"Follow Path to Xunlai")
    bot.DialogAt(-3749, 10367, UNLOCK_STORAGE, step_name="Unlock Xunlai Storage")
    
def CraftWeapons(bot: Botting) -> None:
    def craft_and_equip_items():
        MELEE_CLASSES = ["Warrior", "Ranger", "Assassin","None"]
        if bot.GetProperty("live_data.Player.primary_profession") in MELEE_CLASSES:
            yield from bot.helpers._interact_with_agent((-6519, 12335))
            result = yield from Routines.Yield.Items.WithdrawItems(ModelID.Iron_Ingot.value, 5)
            if not result:
                ConsoleLog("CraftWeapons", "Failed to withdraw Iron Ingots.", Py4GW.Console.MessageType.Error)
                bot.helpers.on_unmanaged_fail()
                return

            SAI_MODEL_ID = 11643
            result = yield from Routines.Yield.Items.CraftItem(SAI_MODEL_ID, 100,[ModelID.Iron_Ingot.value],[5])
            if not result:
                ConsoleLog("CraftWeapons", "Failed to craft SAI_MODEL_ID.", Py4GW.Console.MessageType.Error)
                bot.helpers.on_unmanaged_fail()
                return

            result = yield from Routines.Yield.Items.EquipItem(SAI_MODEL_ID)
            if not result:
                ConsoleLog("CraftWeapons", f"Failed to equip item ({SAI_MODEL_ID}).", Py4GW.Console.MessageType.Error)
                bot.helpers.on_unmanaged_fail()
                return False

            return True
        
        else:
            yield from Routines.Yield.Items.SpawnBonusItems()
            WAND_MODEL_ID = 6508
            yield from Routines.Yield.Items.EquipItem(WAND_MODEL_ID)
            SHIELD_MODEL_ID = 6514
            yield from Routines.Yield.Items.EquipItem(SHIELD_MODEL_ID)

    bot.AddHeaderStep("Craft Weapons")

    bot.MoveTo(-6423, 12183, "Move to Weapon Crafter")
    bot.AddFSMCustomYieldState(craft_and_equip_items, "Craft and Equip Items")


def ExitToSunquaVale(bot: Botting) -> None:
    bot.AddHeaderStep("Exit To Sunqua Vale")
    ConfigurePacifistEnv(bot)
    bot.MoveTo(-14961,11453)
    bot.WaitForMapLoad(target_map_name="Sunqua Vale")

def TravelToMinisterCho(bot: Botting) -> None:
    bot.AddHeaderStep("Travel To Minister Cho")
    ConfigurePacifistEnv(bot)
    bot.MoveTo(6698, 16095, "Move to Minister Cho")
    GUARDMAN_ZUI_DLG4 = 0x80000B
    bot.DialogAt(6637, 16147, GUARDMAN_ZUI_DLG4, step_name="Talk to Guardman Zui")
    bot.WasteTime(5000)
    minister_cho_map_id = 214
    bot.WaitForMapLoad(target_map_id=minister_cho_map_id)
    ACCEPT_MINISTER_CHO_REWARD = 0x813E07
    bot.DialogAt(7884, -10029, ACCEPT_MINISTER_CHO_REWARD, step_name="Accept Minister Cho Reward")
    

def withdraw_cupcakes():
    global bot_locals
    target_cupcake_count = bot_locals.target_cupcake_count
    if bot.GetProperty("upkeep.birthday_cupcake.active"):
        model_id = ModelID.Birthday_Cupcake.value
        cupcake_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        cupcake_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)

        cupcakes_needed = target_cupcake_count - cupcake_in_bags
        if cupcakes_needed > 0 and cupcake_in_storage > 0:
            # First, try to withdraw exactly what we need
            items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, cupcakes_needed)
            yield from Routines.Yield.wait(250)

            if not items_withdrawn:
                # Try withdrawing as much as possible instead
                fallback_amount = min(cupcakes_needed, cupcake_in_storage)
                items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, fallback_amount)
                yield from Routines.Yield.wait(250)

                if not items_withdrawn:
                    Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw cupcakes from storage.", Py4GW.Console.MessageType.Error)

    yield from Routines.Yield.wait(250)

def withdraw_honeycombs():
    target_honeycomb_count = bot_locals.target_honeycomb_count
    if bot.GetProperty("upkeep.morale.active"):
        model_id = ModelID.Honeycomb.value
        honey_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        honey_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)

        honey_needed = target_honeycomb_count - honey_in_bags
        if honey_needed > 0 and honey_in_storage > 0:
            # Try withdrawing the full amount first
            items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, honey_needed)
            yield from Routines.Yield.wait(250)

            if not items_withdrawn:
                # Fallback to withdraw whatever is available
                fallback_amount = min(honey_needed, honey_in_storage)
                items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, fallback_amount)
                yield from Routines.Yield.wait(250)

                if not items_withdrawn:
                    Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw honeycombs from storage.", Py4GW.Console.MessageType.Error)
    yield from Routines.Yield.wait(250)

def PrepareForBattle(bot: Botting):
    ConfigureAggressiveEnv(bot)
    bot.AddFSMCustomYieldState(EquipSkillBar, "Equip Skill Bar")
    bot.LeaveParty()
    bot.AddFSMCustomYieldState(AddHenchmen, "Add Henchmen")
    bot.AddFSMCustomYieldState(withdraw_cupcakes, "Withdraw Cupcakes")
    bot.AddFSMCustomYieldState(withdraw_honeycombs, "Withdraw Honeycombs")

def EnterMinisterChoMission(bot: Botting):
    bot.AddHeaderStep("Enter Minister Cho Mission")
    PrepareForBattle(bot)
    bot.EnterChallenge(wait_for=4500)
    minister_cho_map_id = 214
    bot.WaitForMapLoad(target_map_id=minister_cho_map_id)
    
def MinisterChoMission(bot: Botting) -> None:
    bot.AddHeaderStep("Minister Cho Mission")
    bot.MoveTo(6358, -7348, "Move to Activate Mission")
    bot.MoveTo(507, -8910, "Move to First Door")
    bot.MoveTo(4889, -5043, "Move to Map Tutorial")
    bot.MoveTo(6216, -1108, "Move to Bridge Corner")
    bot.MoveTo(2617, 642, "Move to Past Bridge")
    bot.MoveTo(0, 1137, "Move to Fight Area")
    bot.MoveTo(-7454, -7384, "Move to Zoo Entrance")
    bot.MoveTo(-9138, -4191, "Move to First Zoo Fight")
    bot.MoveTo(-7109, -25, "Move to Bridge Waypoint")
    bot.MoveTo(-7443, 2243, "Move to Zoo Exit")
    bot.MoveTo(-16924, 2445, "Move to Final Destination")
    bot.InteractNPCAt(-17031, 2448) #"Interact with Minister Cho"
    wait_condition = lambda: (Routines.Checks.Map.MapValid() and (GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Ran Musu Gardens")))
    bot.WasteTimeUntilConditionMet(wait_condition)

def TakeWarningTheTenguQuest(bot: Botting):
    bot.AddHeaderStep("Take Warning the Tengu Quest")
    TAKE_WARNING_THE_TENGU = 0x815301
    bot.DialogAt(15846, 19013, TAKE_WARNING_THE_TENGU, step_name="Take Warning the Tengu Quest")
    PrepareForBattle(bot)
    ConfigurePacifistEnv(bot)
    bot.MoveTo(14730,15176)
    bot.WaitForMapLoad(target_map_name="Kinya Province")

def WarningTheTenguQuest(bot: Botting):
    bot.AddHeaderStep("Warning The Tengu Quest")
    bot.MoveTo(1429, 12768, "Move to Tengu Part2")
    #part 2
    ConfigureAggressiveEnv(bot)
    bot.MoveTo(-983, 4931, "Move to Tengu NPC")
    CONTINUE_WARNING_THE_TENGU_QUEST = 0x815304
    bot.DialogAt(-1023, 4844, CONTINUE_WARNING_THE_TENGU_QUEST, step_name="Continue Warning the Tengu Quest")
    bot.MoveTo(-5011, 732, "Move to Tengu Killspot")
    bot.WasteTimeUntilOOC()
    bot.MoveTo(-983, 4931, "Move back to Tengu NPC")
    TAKE_WARNING_THE_TENGU_REWARD = 0x815307
    bot.DialogAt(-1023, 4844, TAKE_WARNING_THE_TENGU_REWARD, step_name="Take Warning the Tengu Reward")
    TAKE_THE_THREAT_GROWS = 0x815401
    bot.DialogAt(-1023, 4844, TAKE_THE_THREAT_GROWS, step_name="Take The Threat Grows Quest")
    bot.Travel(target_map_name="Shing Jea Monastery")
    bot.WaitForMapLoad(target_map_name="Shing Jea Monastery")

def ExitToTsumeiVillage(bot: Botting):
    bot.AddHeaderStep("Exit To Tsumei Village")
    bot.MoveTo(-4900, -13900, "Move to Tsumei Village")
    bot.WaitForMapLoad(target_map_name="Tsumei Village")

def ExitToPanjiangPeninsula(bot: Botting):
    bot.AddHeaderStep("Exit To Panjiang Peninsula")
    PrepareForBattle(bot)
    bot.MoveTo(-11600,-17400, "Move to Panjiang Peninsula")
    bot.WaitForMapLoad(target_map_name="Panjiang Peninsula")

def TheThreatGrows(bot: Botting):
    bot.AddHeaderStep("The Threat Grows")
    bot.MoveTo(9700, 7250, "Move to The Threat Grows Killspot")
    SISTER_TAI_MODEL_ID = 3316
    wait_function = lambda: (not Routines.Checks.Agents.InDanger(aggro_area=Range.Spellcast)) and GLOBAL_CACHE.Agent.HasQuest(Routines.Agents.GetAgentIDByModelID(SISTER_TAI_MODEL_ID))
    bot.WasteTimeUntilConditionMet(wait_function)
    ConfigurePacifistEnv(bot)
    ACCEPT_REWARD = 0x815407
    bot.DialogWithModel(SISTER_TAI_MODEL_ID, ACCEPT_REWARD, step_name="Accept The Threat Grows Reward")
    TAKE_QUEST = 0x815501
    bot.DialogWithModel(SISTER_TAI_MODEL_ID, TAKE_QUEST, step_name="Take Go to Togo Quest")
    bot.Travel(target_map_name="Shing Jea Monastery")
    bot.WaitForMapLoad(target_map_name="Shing Jea Monastery")

def AdvanceToSaoshangTrail(bot: Botting):
    bot.AddHeaderStep("Advance To Saoshang Trail")
    bot.MoveTo(-159, 9174, "Move to Togo 002")
    ACCEPT_TOGO_QUEST = 0x815507
    bot.DialogAt(-92, 9217, ACCEPT_TOGO_QUEST, step_name="Accept Togo Quest")
    TAKE_EXIT_QUEST = 0x815601
    bot.DialogAt(-92, 9217, TAKE_EXIT_QUEST, step_name="Take Exit Quest")
    CONTINUE = 0x80000B
    bot.DialogAt(538, 10125, CONTINUE, step_name="Continue")
    saoshang_trail_map_id = 313
    bot.WaitForMapLoad(target_map_id=saoshang_trail_map_id)

def TraverseSaoshangTrail(bot: Botting):
    bot.AddHeaderStep("Traverse Saoshang Trail")
    CONTINUE = 0x815604
    bot.DialogAt(1254, 10875, CONTINUE)
    bot.MoveTo(16600, 13150)
    bot.WaitForMapLoad(target_map_name="Seitung Harbor")

def TakeRewardAndExitSeitungHarbor(bot: Botting):
    bot.AddHeaderStep("Take Reward And Exit Seitung Harbor")
    TAKE_REWARD = 0x815607
    bot.DialogAt(16368, 12011, TAKE_REWARD)
    PrepareForBattle(bot)
    bot.MoveTo(16777,17540)
    bot.WaitForMapLoad(target_map_name="Jaya Bluffs")

def GoToZenDaijun(bot: Botting):
    bot.AddHeaderStep("Go To Zen Daijun")
    bot.MoveTo(23616, 1587)
    bot.WaitForMapLoad(target_map_name="Haiju Lagoon")
    bot.MoveTo(16571, -22196)
    CONTINUE = 0x80000B
    bot.DialogAt(16489, -22213, CONTINUE)
    bot.WasteTime(6000)
    zen_daijun_map_id = 213
    bot.WaitForMapLoad(target_map_id=zen_daijun_map_id)
    
def PrepareForZenDaijunMission(bot:Botting):
    bot.AddHeaderStep("Prepare for Zen Daijun Mission")
    PrepareForBattle(bot)
    bot.EnterChallenge(6000)
    

def ZenDaijunMission(bot: Botting):
    bot.AddHeaderStep("Zen Daijun Mission")
    bot.MoveTo(11903, 11235)
    bot.InteractGadgetAt(11665, 11386)
    bot.MoveTo(10549,8070)
    bot.MoveTo(10945,3436)
    bot.MoveTo(7551,3810)
    bot.MoveTo(5538,1993)
    bot.InteractGadgetAt(4754,1451)
    bot.MoveTo(4508, -1084)
    bot.MoveTo(528, 6271)
    bot.MoveTo(-9833, 7579)
    #?
    bot.MoveTo(-12983, 2191)
    bot.MoveTo(-12362, -263)
    bot.MoveTo(-9813, -114)
    bot.FlagAllHeroes(-8656, -771)
    bot.MoveTo(-7851, -1458)
    wait_condition = lambda: (Routines.Checks.Map.MapValid() and (GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor")))
    bot.WasteTimeUntilConditionMet(wait_condition)

def jump_to_state(bot: Botting, state_name: str):
    bot.config.FSM.jump_to_state_by_name(state_name)
    yield from Routines.Yield.wait(100)

def _FarmUntilLevel10(bot: Botting):
    level = bot.config.live_data.Player.get("level")
    if level < 10:
        ConsoleLog("Farming until Level 10", f"current level: {level}")
        yield from Routines.Yield.wait(100)
        zen_daijun_map_id = 213
        GLOBAL_CACHE.Party.LeaveParty()
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Map.Travel(zen_daijun_map_id)
        yield from Routines.Yield.wait(1000)
        
        wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(zen_daijun_map_id)
        if not wait_of_map_load:
            Py4GW.Console.Log(MODULE_NAME, "Map load failed.", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
        yield from Routines.Yield.wait(1000)

        state_name = "[H]Prepare for Zen Daijun Mission_22"
        #exec_fn = lambda: jump_to_state(bot, state_name)
        #bot.AddFSMCustomYieldState(exec_fn, f"Jump to {state_name}")
        fsm = bot.config.FSM
        #fsm.reset()
        fsm.jump_to_state_by_name(state_name)
    else:
        ConsoleLog("Farming complete", f"current level: {level}")
        yield from Routines.Yield.wait(100)
        
def FarmUntilLevel10(bot: Botting):
    bot.AddHeaderStep("Farm Until Level 10")
    bot.AddFSMCustomYieldState(_FarmUntilLevel10(bot),"Farm Until Level 10")

def AdvanceToMarketplace(bot: Botting):
    bot.AddHeaderStep("Advance To Marketplace")
    bot.MoveTo(17470, 9029)
    bot.DialogAt(16927, 9004, 0x815D01)  # "I Will Set Sail Immediately"
    bot.DialogAt(16927, 9004, 0x815D05)  # "a Master burden"
    #bot.DialogAt(16927, 9004, 0x81)  # book a passage to kaineng
    bot.DialogAt(16927, 9004, 0x84)  # i am sure
    bot.WaitForMapLoad(target_map_name="Kaineng Docks")
    bot.MoveTo(9866, 20041) #headmaster Greico
    bot.DialogAt(9955, 20033, 0x815D04)  # a masters burden
    bot.MoveTo(12003, 18529) 
    bot.WaitForMapLoad(target_map_name="The Marketplace")
    
def AdvanceToKainengCenter(bot: Botting):
    bot.AddHeaderStep("Advance To Kaineng Center")
    PrepareForBattle(bot)
    bot.MoveTo(16640,19882)
    bot.WaitForMapLoad(target_map_name="Bukdek Byway")
    bot.MoveTo(-10254,-1759)
    bot.MoveTo(-10332,1442)
    bot.MoveTo(-10965,9309)
    bot.MoveTo(-9467,14207)
    path_to_kc = [
        (-8601.28, 17419.64),
        (-6857.17, 19098.28),
        (-6706,20388)
    ]
    bot.FollowPath(path_to_kc, "Follow Path to Kaineng Center")
    bot.WasteTime(1000)
    kc_id = 194
    bot.WaitForMapLoad(target_map_id=kc_id)
    
def AdvanceToEOTN(bot: Botting):
    bot.AddHeaderStep("Advance To Eye of the North")
    bot.MoveTo(3742.08, -2087.97)
    bot.DialogAt(3747.00, -2174.00, 0x833501)  # limitless monetary resources
    PrepareForBattle(bot)
    bot.MoveTo(3243, -4911)
    bot.WaitForMapLoad(target_map_name="Bukdek Byway")
    bot.MoveTo(-10066.81, 16547.19)
    bot.DialogAt(-10103.00, 16493.00, 0x84)  # yes
    tunnels_below_cantha_id = 692
    bot.WaitForMapLoad(target_map_id=tunnels_below_cantha_id)
    bot.MoveTo(16738.77, 3046.05)
    bot.MoveTo(10968.19, 9623.72)
    bot.MoveTo(3918.55, 10383.79)
    bot.MoveTo(8435, 14378)
    bot.MoveTo(10134,16742)
    bot.WasteTime(3000)
    ConfigurePacifistEnv(bot)    
    bot.MoveTo(4523.25, 15448.03)
    bot.MoveTo(-43.80, 18365.45)
    bot.MoveTo(-10234.92, 16691.96)
    bot.MoveTo(-17917.68, 18480.57)
    bot.MoveTo(-18775, 19097)
    bot.WasteTime(3000)
    bot.WaitForMapLoad(target_map_name="Boreal Station")

def ExitBorealStation(bot: Botting):
    bot.AddHeaderStep("Exit Boreal Station")
    PrepareForBattle(bot)
    bot.MoveTo(4684, -27869)
    bot.WaitForMapLoad(target_map_name="Ice Cliff Chasms")

def TraverseToEOTNOutpost(bot: Botting):
    bot.AddHeaderStep("Traverse To Eye of the North Outpost")
    bot.MoveTo(3579.07, -22007.27)
    bot.WasteTime(15000)
    bot.DialogAt(3537.00, -21937.00, 0x839104)
    bot.MoveTo(3743.31, -15862.36)
    bot.MoveTo(8267.89, -12334.58)
    bot.MoveTo(3607.21, -6937.32)
    bot.MoveTo(2557.23, -275.97)
    eotn_map_id =642
    bot.WaitForMapLoad(target_map_id=eotn_map_id)


def on_death(bot: "Botting"):
    print("I Died")

def on_party_wipe_coroutine(bot: "Botting", target_name: str):
    GLOBAL_CACHE.Player.SendChatCommand("resign")
    yield from Routines.Yield.wait(6000)
    fsm = bot.config.FSM
    fsm.reset()
    fsm.jump_to_state_by_name(target_name)

def on_party_wipe(bot: "Botting"):
    """
    Clamp-jump to the nearest lower (or equal) waypoint when party is defeated.
    Uses existing FSM API only:
      - get_current_state_number()
      - get_state_name_by_number(step_num)
      - pause(), jump_to_state_by_name(), resume()
    Returns True if a jump occurred.
    """
    print ("Party Wiped! Jumping to nearest waypoint...")
    fsm = bot.config.FSM
    current_step = fsm.get_current_state_number()

    # Your distinct waypoints (as given)
    ENTER_MINISTER_CHO_MISSION = 72
    TAKE_WARNING_THE_TENGU_QUEST = 122
    EXIT_TO_PANJIANG_PENINSULA = 189
    EXIT_SEITUNG_HARBOR = 252
    ENTER_ZEN_DAIJUN_MISSION = 279
    FARM_UNTIL_LEVEL_10 = 336

    waypoints = [
        ENTER_MINISTER_CHO_MISSION,
        TAKE_WARNING_THE_TENGU_QUEST,
        EXIT_TO_PANJIANG_PENINSULA,
        EXIT_SEITUNG_HARBOR,
        ENTER_ZEN_DAIJUN_MISSION,
        FARM_UNTIL_LEVEL_10,
    ]

    # nearest <= current; if none, bail (or pick the first—your call)
    lower_or_equal = [w for w in waypoints if w <= current_step]
    if not lower_or_equal:
        return   # or: target_step = waypoints[0] to always jump somewhere

    target_step = max(lower_or_equal)
    target_name = fsm.get_state_name_by_number(target_step)
    if not target_name:
        return 

    fsm.pause()
    fsm.AddManagedCoroutine(f"{fsm.get_state_name_by_number(current_step)}_OPD", on_party_wipe_coroutine(bot, target_name))


def InitializeBot(bot: Botting) -> None:
    bot.AddHeaderStep("Initial Step")
    # Add any initialization steps here
    #condition = lambda: on_death(bot)
    #bot.config.events.on_death.set_callback(condition)
    condition = lambda: on_party_wipe(bot)
    bot.config.events.on_party_defeated.set_callback(condition)
    bot.config.events.on_party_wipe.set_callback(condition)

def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    ExitMonasteryOverlook(bot)
    ExitToCourtyard(bot)
    UnlockSecondaryProfession(bot)
    UnlockXunlaiStorage(bot)
    CraftWeapons(bot)
    ExitToSunquaVale(bot)
    TravelToMinisterCho(bot)
    EnterMinisterChoMission(bot)
    MinisterChoMission(bot)
    ConfigurePacifistEnv(bot)
    TakeWarningTheTenguQuest(bot)
    WarningTheTenguQuest(bot)
    ExitToSunquaVale(bot)
    ExitToTsumeiVillage(bot)
    ExitToPanjiangPeninsula(bot)
    TheThreatGrows(bot)
    ExitToCourtyard(bot)
    AdvanceToSaoshangTrail(bot)
    TraverseSaoshangTrail(bot)
    TakeRewardAndExitSeitungHarbor(bot)
    GoToZenDaijun(bot)
    PrepareForZenDaijunMission(bot)
    ZenDaijunMission(bot)
    FarmUntilLevel10(bot)
    AdvanceToMarketplace(bot)
    AdvanceToKainengCenter(bot)
    AdvanceToEOTN(bot)
    ExitBorealStation(bot)
    TraverseToEOTNOutpost(bot)
    bot.AddHeaderStep("Final Step")
    bot.Stop()


bot.Routine = create_bot_routine.__get__(bot)



selected_step = 0
filter_header_steps = True
def main():
    global selected_step, filter_header_steps
    try:
        bot.Update()
        
        if PyImGui.begin("PathPlanner Test", PyImGui.WindowFlags.AlwaysAutoResize):

            PyImGui.text("Bot is: " + ("Running" if bot.config.fsm_running else "Stopped"))
            current_step = bot.config.FSM.get_current_state_number()
            step_name = bot.config.FSM.get_state_name_by_number(current_step)
            PyImGui.text(f"Current Step: {current_step} - {step_name}")
            
            # --- find nearest header at or before current_step ---
            fsm_steps_all = bot.config.FSM.get_state_names()
            header_for_current = None
            for i in range(current_step - 1, -1, -1):   # walk backwards
                name = fsm_steps_all[i]
                if name.startswith("[H]"):
                    # clean the header formatting like you already do
                    header_for_current = re.sub(r'^\[H\]\s*', '', name)
                    header_for_current = re.sub(r'_(?:\[\d+\]|\d+)$', '', header_for_current)
                    break

            if header_for_current:
                PyImGui.text(f"Current Header: {header_for_current}")
            else:
                PyImGui.text("Current Header: (none found)")

            if PyImGui.button("Start Botting"):
                bot.Start()

            if PyImGui.button("Stop Botting"):
                bot.Stop()
                
            PyImGui.separator()
            
            filter_header_steps = PyImGui.checkbox("Show only Header Steps", filter_header_steps)

            fsm_steps_all = bot.config.FSM.get_state_names()
            

            # choose source list (original names) based on filter
            if filter_header_steps:
                fsm_steps_original = [s for s in fsm_steps_all if s.startswith("[H]")]
            else:
                fsm_steps_original = fsm_steps_all

            # display list: clean headers; leave non-headers as-is
            def _clean_header(name: str) -> str:
                #return name
                if name.startswith("[H]"):
                    name = re.sub(r'^\[H\]\s*', '', name)              # remove [H] (and optional space)
                    name = re.sub(r'_(?:\[\d+\]|\d+)$', '', name)       # remove _123 or _[123] at end
                return name

            fsm_steps = [_clean_header(s) for s in fsm_steps_original]
            

            if not fsm_steps:
                PyImGui.text("No steps to show (filter active).")
            else:
                if selected_step >= len(fsm_steps):
                    selected_step = max(0, len(fsm_steps) - 1)

                selected_step = PyImGui.combo("FSM Steps", selected_step, fsm_steps)
                
                sel_orig = fsm_steps_original[selected_step]
                state_num = bot.config.FSM.get_state_number_by_name(sel_orig)

                # display it (handle not-found defensively)
                if state_num is None or state_num == -1:
                    PyImGui.text(f"Selected step: {sel_orig}  (step #: N/A)")
                else:
                    PyImGui.text(f"Selected step: {sel_orig}  (step #: {state_num})")

                if PyImGui.button("start at Step"):
                    bot.config.fsm_running = True
                    bot.config.FSM.reset()
                    # jump with ORIGINAL name
                    bot.config.FSM.jump_to_state_by_name(fsm_steps_original[selected_step])
                    bot._start_coroutines()

    
            PyImGui.separator()
            PyImGui.text(f"auto_attack_timer: {auto_attack_timer}")
            PyImGui.text(f"auto_attack_threshold: {auto_attack_threshold}")
            PyImGui.text(f"is_expired: {is_expired}")

            PyImGui.separator()

            bot.config.config_properties.draw_path.set_active(PyImGui.checkbox("Draw Path", bot.config.config_properties.draw_path.is_active()))

            # Segment-by-segment distances
            if bot.config.path and len(bot.config.path) >= 2:
                if PyImGui.collapsing_header("Path Segments"):
                    total = 0.0
                    for i in range(len(bot.config.path) - 1):
                        p0 = bot.config.path[i][:2]
                        p1 = bot.config.path[i + 1][:2]
                        d = Utils.Distance(p0, p1)
                        total += d
                        PyImGui.text(f"{i:02d} {bot.config.path[i]} -> {i+1:02d} {bot.config.path[i+1]}  |  d={d:.1f}")
                    PyImGui.separator()
                    PyImGui.text(f"Total: {total:.1f}")


        PyImGui.end()

        bot.DrawPath()

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()

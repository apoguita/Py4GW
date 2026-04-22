from __future__ import annotations
from typing import List, Tuple, Generator, Any
import os
import random

import PyImGui
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Map, Player, Py4GW, ConsoleLog, ModelID, Bags, Botting,
                          Agent, ImGui, ActionQueueManager, HeroType, Key, Keystroke, CHAR_MAP)
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.Context import GWContext

LAST_CHARACTER_NAME: str = ""
LAST_PRIMARY_PROF: str = ""
LAST_CAMPAIGN: str = "Nightfall"

MODULE_NAME = "Proof of Legend Bot 2.0 by Wick Divinus"
MODULE_ICON = "Textures\\Module_Icons\\Proof of Legend.png"

bot = Botting("Proof of Legend Bot 2.0 by Wick Divinus", MODULE_NAME, MODULE_ICON,
              upkeep_auto_inventory_management_active=False,
              upkeep_auto_combat_active=False,
              upkeep_auto_loot_active=False)


def _on_party_defeated(bot: Botting, step_name: str):
    """Party wiped: wait for 'Return to Outpost' widget to bring us back, then restart from the same step."""
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("auto_combat", "active", False)
    while True:
        yield from Routines.Yield.wait(500)
        if not Routines.Checks.Map.MapValid():
            continue
        if Routines.Checks.Map.IsOutpost() and Map.IsMapReady():
            break
    fsm = bot.config.FSM
    if not step_name or not fsm.has_state(step_name):
        state_names = fsm.get_state_names()
        step_name = state_names[0] if state_names else ""
    if not step_name:
        fsm.resume()
        yield
        return
    fsm.ResetAndStartAtStep(step_name)
    bot.Properties.ApplyNow("auto_combat", "active", True)
    bot.Templates.Aggressive()
    yield


def _get_mission_header_step(fsm):
    """Return the [H] header state name for the current state (so we restart the mission, not a sub-step)."""
    if not fsm.current_state or not fsm.states:
        return None
    try:
        idx = fsm.states.index(fsm.current_state)
    except ValueError:
        return None
    for i in range(idx, -1, -1):
        if fsm.states[i].name.startswith("[H]"):
            return fsm.states[i].name
    return None


def on_party_defeated(bot: Botting):
    ConsoleLog("PartyDefeated", "Party defeated. Returning to outpost and retrying current step...", log=True)
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    current_step = _get_mission_header_step(fsm) or (fsm.current_state.name if fsm.current_state else "")
    fsm.pause()
    fsm.AddManagedCoroutine("OnPartyDefeated", _on_party_defeated(bot, current_step))


def InitializeBot(bot: Botting) -> None:
    bot.Events.OnPartyDefeatedCallback(lambda: on_party_defeated(bot))


def create_bot_routine(bot: Botting) -> None:
    global LAST_CHARACTER_NAME, LAST_PRIMARY_PROF, LAST_CAMPAIGN
    LAST_CHARACTER_NAME = Player.GetName() or LAST_CHARACTER_NAME
    try:
        p, _ = Agent.GetProfessionNames(Player.GetAgentID())
        if p:
            LAST_PRIMARY_PROF = p
    except Exception:
        pass

    InitializeBot(bot)
    Skip_Tutorial(bot)
    Into_Chahbek_Village(bot)
    Quiz_the_Recruits(bot)
    Never_Fight_Alone(bot)
    Chahbek_Village_Mission(bot)
    Primary_Training(bot)
    A_Personal_Vault(bot)
    Material_Girl(bot)
    Hog_Hunt(bot)
    To_Champions_Dawn(bot)
    Identity_Theft(bot)
    Quality_Steel(bot)
    Craft_First_Weapon(bot)
    A_Hidden_Threat(bot)
    Chahbek_Village_Mission_2(bot)
    Deposit_Proof_Of_Legend(bot)

    bot.States.AddHeader("Reroll: Logout > Delete > Recreate")
    bot.States.AddCustomState(LogoutAndDeleteState, "Logout/Delete/Recreate same name")
    bot.States.AddHeader("Loop: restart routine")
    bot.States.AddCustomState(ScheduleNextRun, "Schedule next run")

def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.Templates.Pacifist()

def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Templates.Aggressive()
    
def PrepareForBattle(bot: Botting, Hero_List = [], Henchman_List = []) -> None:
    ConfigureAggressiveEnv(bot)
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    bot.Party.AddHeroList(Hero_List)
    bot.Party.AddHenchmanList(Henchman_List)

def StandardHeroTeam():
    party_size = Map.GetMaxPartySize()

    hero_list = []
    skill_templates = []
    
    if party_size <= 8:
        # Small party: Gwen, Vekk, Ogden
        hero_list.extend([24, 26, 27])
        skill_templates = [
            "OQhkAsC8gFKzJY6lDMd40hQG4iB",  # 1 Gwen
            "OgVDI8gsO5gTw0z0hTFAZgiA",     # 2 Vekk
            "OwUUMsG/E4SNgbE3N3ETfQgZAMEA"  # 3 Ogden
        ]
    
    # Add all heroes quickly
    for hero_id in hero_list:
        GLOBAL_CACHE.Party.Heroes.AddHero(hero_id)
        ConsoleLog("addhero",f"Added Hero: {hero_id}", log=False)
    
    # Single wait for all heroes to join
    yield from Routines.Yield.wait(1000)
    
    # Load skillbars for all positions
    for position in range(len(hero_list)):
        GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(position + 1, skill_templates[position])
        ConsoleLog("skillbar", f"Loading skillbar for position {position + 1}", log=True)
        yield from Routines.Yield.wait(500)
    
def EquipSkillBar(): 
    global bot

    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    level = Agent.GetLevel(Player.GetAgentID())
    if profession == "Dervish":
        if level ==2:
           yield from Routines.Yield.Skills.LoadSkillbar("OgChkSj4V6KAGw/X7LCe8C")
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA")    
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OgGjkyrDLTiXSX7gDYPXfXjbYcA")

    elif profession == "Paragon":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OQCjUOmBqMw4HMQuCHjBAYcBAA")    
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OQCjUOmBqMw4HMQuCHjBAYcBAA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OQCjUWmCaNw4HMQuCDAAAYcBAA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGkUemyZgKEM2DmDGQ2VBQoAAGH")        
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OQGjUymDKTwYPYOYAZLYXFAhYcA")  

    elif profession == "Elementalist":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDozGsAGTrwFbNAAIA")    
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDozGsAGTrwFbNAAIA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMNGDahwoYYNAAAAMO") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OgBDo2OMNGDahwoYYNAAAAMO")    
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OgVDErwsN0COwFAoeTzzgVMO")  

    elif profession == "Monk":    
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OwAU0C38CYEZEltkf5cmAImA")    
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OwAU0CH9CoEtElZkf5EAAImA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OwAU0CH9CoEtElZkf5EAAImA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OwAU0CH9CoEtElZkf5EAAImA")    
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OwUEEqwD6ywBuA308cPAKgSiJA")   

    elif profession == "Warrior":    
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OQARErprIUAABAuCGHAAAA")    
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OQARErprIUAABAuCGHAAAA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OQARErprIUAABAuCGHAAAA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OQARErprIUAABAuCGHAAAA")      
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OQojExVTKTdFCF/XDYcFBA7gYcA")            
    elif profession == "Necromancer":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OABDQRJWAplpAAAAAAAA")  
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OABDQTNmMphMRboK8IAAAAMO")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OABDQTNmMphMRboK8IAAAAMO") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OAVDIXN2McgqwFAo2DgCCAMO")      
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OAVEEqwFZ3wBqCXAgaPAKknx4A") 
    elif profession == "Mesmer":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OQBDAhITAoohAAAAAAAA")  
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OQBDAhMTAooBHEBFAAIA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OQBDAhgTAooBHEBFAAIA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OQBDAhgTMogLAHgIAF6BAVBA")      
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OQBEAaYCP2gCuAcg8MUoHAUx4A")        
    elif profession == "Ranger":
        if level == 2:
            yield from Routines.Yield.Skills.LoadSkillbar("OgATcDskjQx+WAAAAAAAAAA")  
        elif level == 3:
            yield from Routines.Yield.Skills.LoadSkillbar("OgATcDsknQx++4xGAAAACAA")    
        elif level == 4:
            yield from Routines.Yield.Skills.LoadSkillbar("OgAScLsMAAfzxZ5gxBAAABA") #leave 2 holes in the skill bar to avoid the pop up for 2nd profession   
        elif level == 5:
            yield from Routines.Yield.Skills.LoadSkillbar("OgESIpLNdFfDUBAAA4KXFMO")     
        else:
            yield from Routines.Yield.Skills.LoadSkillbar("OgETI5LjHqrw3AqYHkqQvC1AjDA")              


def GetFirstWeaponByProfession(bot: Botting):
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    SCYTHE = SPEAR = AXE = FIRESTAFF = DOMSTAFF = MONKSTAFF = NECROSTAFF = 0
    
    if primary == "Warrior":
        SCYTHE = 16227
        return SCYTHE,
    elif primary == "Ranger":
        AXE =  15777 #Winged Axe
        return AXE,
    elif primary == "Paragon":
        SPEAR = 18711
        return SPEAR,
    elif primary == "Dervish":
        SCYTHE = 16227
        return SCYTHE,
    elif primary == "Elementalist":
        FIRESTAFF = 18896
        return FIRESTAFF,
    elif primary == "Mesmer":
        DOMSTAFF = 18712
        return DOMSTAFF,
    elif primary == "Monk":
        MONKSTAFF = 18901 #Smiting Staff
        return MONKSTAFF,
    elif primary == "Necromancer":
        NECROSTAFF = 18893 #Death Staff
        return NECROSTAFF,
    return ()

def GetFirstWeaponMaterialPerProfession(bot: Botting):
    primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if primary == "Warrior":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Ranger":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Dervish":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Paragon":
        return [ModelID.Iron_Ingot.value]
    elif primary == "Elementalist":
        return [ModelID.Wood_Plank.value]
    elif primary == "Monk":
        return [ModelID.Wood_Plank.value]
    elif primary == "Mesmer":
        return [ModelID.Iron_Ingot.value]  
    elif primary == "Necromancer":
        return [ModelID.Wood_Plank.value]        
    return []

def Craft1stWeapon(bot: Botting):
    weapon_ids = GetFirstWeaponByProfession(bot)
    materials = GetFirstWeaponMaterialPerProfession(bot)
    
    # Structure weapon data like armor pieces - (weapon_id, materials_list, quantities_list)
    weapon_pieces = []
    for weapon_id in weapon_ids:
        weapon_pieces.append((weapon_id, materials, [1]))  # 1 = 10 materials per weapon minimum
    
    for weapon_id, mats, qtys in weapon_pieces:
        result = yield from Routines.Yield.Items.CraftItem(weapon_id, 20, mats, qtys)
        if not result:
            ConsoleLog("CraftWeapon", f"Failed to craft weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield

        result = yield from Routines.Yield.Items.EquipItem(weapon_id)
        if not result:
            ConsoleLog("CraftWeapon", f"Failed to equip weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True

#region Tutorial and Initial Setup

def Skip_Tutorial(bot: Botting) -> None:
    bot.States.AddHeader("Skip Tutorial") # 2,000 XP
    bot.Move.XYAndDialog(10289, 6405, 0x82A501)
    bot.Map.LeaveGH()
    bot.Wait.ForMapToChange(target_map_id=544)

def Into_Chahbek_Village(bot: Botting):
    bot.States.AddHeader("Quest: Into Chahbek Village")
    bot.Map.Travel(target_map_id=544)
    bot.Move.XYAndDialog(3493, -5247, 0x82A507)
    bot.Move.XYAndDialog(3493, -5247, 0x82C501)
    def PressHandKKeys():
        Keystroke.PressAndRelease(Key.H.value)
        yield from Routines.Yield.wait(100)
        Keystroke.PressAndRelease(Key.K.value)
        yield from Routines.Yield.wait(100)
        yield
    bot.States.AddCustomState(PressHandKKeys, "Press H and K Keys") #Close Hero and Skills tabs

def Quiz_the_Recruits(bot: Botting):
    bot.States.AddHeader("Quest: Quiz the Recruits") # 250 XP
    bot.Map.Travel(target_map_id=544)
    bot.Move.XY(4750, -6105)
    bot.Move.XYAndDialog(4750, -6105, 0x82C504)
    bot.Move.XYAndDialog(5019, -6940, 0x82C504)
    bot.Move.XYAndDialog(3540, -6253, 0x82C504)
    bot.Move.XYAndDialog(3485, -5246, 0x82C507)

def Equip_Weapon():
        global bot
        profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
        if profession == "Dervish":
            bot.Items.Equip(15591)  # starter scythe
        elif profession == "Paragon":
            bot.Items.Equip(15593) #Starter Spear
            #bot.Items.Equip(6514) #Bonus Shield
        elif profession == "Elementalist":
            #bot.Items.Equip(6508) #Luminescent Scepter
            bot.Items.Equip(2742) #Starter Elemental Rod
            #bot.Wait.ForTime(1000)
            #bot.Items.Equip(6514)
        elif profession == "Mesmer":
            #bot.Items.Equip(6508) #Luminescent Scepter
            bot.Items.Equip(2652) #Starter Cane
            #bot.Wait.ForTime(1000)
            #bot.Items.Equip(6514)
        elif profession == "Necromancer":
            #bot.Items.Equip(6515) #Soul Shrieker   
            bot.Items.Equip(2694) #Starter Truncheon
        elif profession == "Ranger":
            #bot.Items.Equip(5831) #Nevermore Flatbow 
            bot.Items.Equip(477) #Starter Bow
        elif profession == "Warrior":
            bot.Items.Equip(2982) #Starter Sword  
            #bot.Items.Equip(6514) #Bonus Shield  
        elif profession == "Monk":
            #bot.Items.Equip(6508) #Luminescent Scepter 
            bot.Items.Equip(2787) #Starter Holy Rod
            #bot.Wait.ForTime(1000)
            #bot.Items.Equip(6514)   
  
def Never_Fight_Alone(bot: Botting):
    bot.States.AddHeader("Quest: Never Fight Alone") # 250 XP
    bot.Map.Travel(target_map_id=544)
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[1,2])
    bot.Items.SpawnAndDestroyBonusItems(exclude_list=[ModelID.Igneous_Summoning_Stone.value])
    Equip_Weapon()
    bot.Move.XYAndDialog(3433, -5900, 0x82C701)
    bot.Dialogs.AtXY(3433, -5900, 0x82C707)
    

def Chahbek_Village_Mission(bot: Botting):
    bot.States.AddHeader("Chahbek Village Mission") # 1,000 XP for Master's
    bot.Map.Travel(target_map_id=544)
    bot.SkillBar.LoadHeroSkillBar(1, "OQASEF6EC1vcNABWAAAA") #Koss
    bot.Dialogs.AtXY(3485, -5246, 0x81)
    bot.Dialogs.AtXY(3485, -5246, 0x84)
    bot.Wait.ForTime(2000)
    bot.Wait.UntilOnExplorable()
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(2240, -3535)
    bot.Move.XY(227, -5658)
    bot.Move.XY(-1144, -4378)
    bot.Move.XY(-2058, -3494)
    bot.Move.XY(-4725, -1830)
    bot.Interact.WithGadgetAtXY(-4725, -1830) #Oil 1
    bot.Move.XY(-1725, -2551)
    bot.Wait.ForTime(1500)
    bot.Interact.WithGadgetAtXY(-1725, -2550) #Cata load
    bot.Wait.ForTime(1500)
    bot.Interact.WithGadgetAtXY(-1725, -2550) #Cata fire
    bot.Move.XY(-4725, -1830) #Back to Oil
    bot.Interact.WithGadgetAtXY(-4725, -1830) #Oil 2
    bot.Move.XY(-1731, -4138)
    bot.Interact.WithGadgetAtXY(-1731, -4138) #Cata 2 load
    bot.Wait.ForTime(2000)
    bot.Interact.WithGadgetAtXY(-1731, -4138) #Cata 2 fire
    bot.Move.XY(-2331, -419)
    bot.Move.XY(-1685, 1459)
    bot.Move.XY(-2895, -6247)
    bot.Move.XY(-3938, -6315) #Boss
    bot.Wait.ForMapToChange(target_map_id=456)

def Get_Skills():
    global bot
    ConfigurePacifistEnv(bot)
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if profession == "Dervish":
        bot.Move.XYAndDialog(-12107, -705, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)
                
    elif profession == "Paragon":
        bot.Move.XYAndDialog(-10724, -3364, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Elementalist":
        bot.Move.XYAndDialog(-12011.00, -639.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Mesmer":
        bot.Move.XYAndDialog(-7149.00, 1830.00, 0x7F, step_name="Teach me 1")

    elif profession == "Necromancer":
        bot.Move.XYAndDialog(-6557.00, 1837.00, 0x7F, step_name="Teach me 1")
        

    elif profession == "Ranger":
        bot.Move.XYAndDialog(-9498.00, 1426.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Warrior":
        bot.Move.XYAndDialog(-9663.00, 1506.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)

    elif profession == "Monk":
        bot.Move.XYAndDialog(-11658.00, -1414.00, 0x7F, step_name="Teach me 1")
        bot.Move.XY(-12200, 473)    

def Primary_Training(bot: Botting):
    bot.States.AddHeader("Quest: Primary Training") # 250 XP
    bot.Move.XYAndDialog(-7234.90, 4793.62, 0x825801)
    Get_Skills()
    bot.Move.XYAndDialog(-7234.90, 4793.62, 0x825807)
    bot.UI.CancelSkillRewardWindow()

def A_Personal_Vault(bot: Botting):
    bot.States.AddHeader("Quest: A Personal Vault") # 500 XP
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-9251, 11826, 0x82A101)
    bot.Move.XYAndDialog(-7761, 14393, 0x84)
    bot.Move.XYAndDialog(-9251, 11826, 0x82A107)

def Armored_Transport(bot: Botting):
    bot.States.AddHeader("Quest: Armored Transport")  # +500 XP
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-11202, 9346,0x825F01) 
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-9326, 18151, target_map_id=430) # Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(18460, 1002, step_name="Bounty")
    bot.Move.XYAndDialog(18460, 1002, 0x85) #Blessing 
    bot.Properties.Disable("auto_loot")
    bot.Move.XYAndDialog(16448, 2320,0x825F04)
    def _exit_condition_1():
        pos = Player.GetXY()
        if not pos:
            return False
        dx = pos[0] - 5516.0
        dy = pos[1] - 6262.0
        return (dx * dx + dy * dy) <= (1000.0 * 1000.0)
    exit_condition_1= lambda: _exit_condition_1()
    def _exit_condition_2():
        pos = Player.GetXY()
        if not pos:
            return False
        dx = pos[0] - -2750.0
        dy = pos[1] - 1741.0
        return (dx * dx + dy * dy) <= (1000.0 * 1000.0)
    exit_condition_2= lambda: _exit_condition_2()
    bot.Move.FollowModel(4881, 100, exit_condition_1) #Spot 1 is the commonly stuck at area.
    bot.Move.XY(6948.40, 12120.75) #Corsair Spawn Point maybe
    bot.Move.FollowModel(4881, 100, exit_condition_2) #Spot 2 is the good spot from Spot 1
    bot.Move.XY(-2963, 1813)
    bot.Wait.ForTime(10000)
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-11202, 9346,0x825F07)

def Material_Girl(bot: Botting):
    bot.States.AddHeader("Quest: Material Girl") # 500 XP
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XY(-10839.96, 9197.05)
    bot.Move.XYAndDialog(-11363, 9066, 0x826101)
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-9326, 18151, target_map_id=430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(18460, 1002, step_name="Bounty")
    bot.Move.XYAndDialog(18460, 1002, 0x85) #Blessing 
    bot.Move.XY(9675, 1038)
    bot.Move.XYAndDialog(9282, -1199, 0x826104)
    bot.Wait.ForTime(2000)
    bot.Move.XY(9464, -2639)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(11183, -7728)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(9681, -9300)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7555, -6791)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(5073, -4850)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(9292, -1220, 0x826104)
    bot.Move.XYAndDialog(-1782, 2790, 0x828801)
    bot.Move.XY(-3145, 2412)
    bot.Move.XYAndExitMap(-3236, 4503, target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForTime(2000)
    bot.Travel_To_Random_District(target_map_id=449) #Kamadan
    bot.Move.XYAndDialog(-10024, 8590, 0x828804)
    bot.Dialogs.AtXY(-10024, 8590, 0x828807)
    bot.Move.XYAndDialog(-11356, 9066, 0x826107)

def Hog_Hunt(bot:Botting):
    bot.States.AddHeader("Quest: Hog Hunt") # 1,000 XP
    bot.Travel_To_Random_District(431) #SSGH
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-3172, 3271, 430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-1840.23, 2432.96)
    bot.Move.XYAndDialog(-1297.00, 3229.00, 0x85) #Insect Bounty
    bot.Move.XY(-269.29, 1981.00)
    bot.Move.XY(-1894.08, 2403.29)
    bot.Wait.ForTime(90000)
    def interact_Nehdukah():
        from Py4GWCoreLib.native_src.methods.PlayerMethods import PlayerMethods
        import PyDialog
        agent_id = Agent.GetAgentIDByEncString("\\x8101\\x246C\\xFDB5\\xB6AD\\x56AB")
        if agent_id != 0:
            PlayerMethods.InteractAgent(agent_id)
        elapsed_ms = 0
        timeout_ms = 10_000
        while elapsed_ms < timeout_ms:
            try:
                if PyDialog.PyDialog.is_dialog_active():
                    buttons = [
                        button for button in PyDialog.PyDialog.get_active_dialog_buttons()
                        if getattr(button, "dialog_id", 0) != 0
                    ]
                    if buttons:
                        # Send dialog ID 0x828D01 to accept Hog Hunt quest
                        Player.SendDialog(0x828D01)
                        ConsoleLog("Hog Hunt", "Quest accepted from Nehdukah", log=True)
                        yield
                        return
            except Exception:
                pass
            yield from Routines.Yield.wait(250)
            elapsed_ms += 250
        ConsoleLog("Hog Hunt", "Failed to accept quest from Nehdukah", log=True)
        yield
    bot.States.AddCustomState(interact_Nehdukah, "Interact with Nehdukah")
    bot.Move.XY(-6038.05, 2229.41)
    bot.Move.XY(-10117.84, 3935.15)
    bot.Move.XY(-12969.55, 9102.46) #Protect Area
    bot.Wait.UntilOnCombat()
    bot.Move.XY(-12743.11, 8789.06) #2nd spawn wave
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-8175.91, 7331.07)
    bot.Move.XY(-6762.51, 2301.88)
    bot.Move.XY(-149.15, 1838.02)
    bot.Move.XY(-1158.39, 1917.86)
    bot.Dialogs.WithModel(4869, 0x828D07) #Done
    bot.Travel_To_Random_District(target_map_id=431) #Sunspear Great Hall

def To_Champions_Dawn(bot: Botting): 
    bot.States.AddHeader("To Champion's Dawn")
    bot.Travel_To_Random_District(target_map_id=431) #Sunspear Great Hall
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-3172, 3271, 430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-1840.23, 2432.96)
    bot.Move.XYAndDialog(-1297.00, 3229.00, 0x85) #Insect Bounty
    bot.Move.XY(-4507, 616)
    bot.Move.XY(-7611, -5953)
    bot.Move.XY(-18083, -11907) 
    bot.Move.XYAndExitMap(-19518, -13021, target_map_id=479) #Champions Dawn

def Quality_Steel(bot: Botting):
    bot.States.AddHeader("Quest: Quality Steel") #500 XP
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-11208, 8815, 0x826001)
    bot.Travel_To_Random_District(target_map_id=431) #Sunspear Great Hall
    bot.Move.XYAndDialog(-4076, 5362, 0x826004)
    bot.Move.XYAndDialog(-2866, 7093, 0x84) #New Location
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,3,4])
    bot.Move.XYAndExitMap(-3172, 3271, 430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-1840.23, 2432.96)
    bot.Move.XYAndDialog(-1297.00, 3229.00, 0x85) #Insect Bounty
    bot.Move.XY(-3225, 1749)
    bot.Move.XY(-995, -2423)
    bot.Move.XY(-513, 67)
    bot.Wait.UntilOutOfCombat()
    bot.Travel_To_Random_District(target_map_id=449) #Kamadan
    bot.Move.XYAndDialog(-11208, 8815, 0x826007)

def Attribute_Points_Quest_1(bot: Botting):
    bot.States.AddHeader("Attribute points quest n. 1") # 
    bot.Travel_To_Random_District(target_map_id=431) #Sunspear Great Hall
    bot.Move.XYAndDialog(-2866, 7093, 0x82CB01) #fixed. Same Dialog ID but new position for the NPC....weird

def Craft_First_Weapon(bot: Botting):
    bot.States.AddHeader("Craft first weapon")
    bot.Travel_To_Random_District(target_map_id=449) #Kamadan
    bot.Move.XYAndInteractNPC(-11270.00, 8785.00)
    bot.Wait.ForTime(1000)
    exec_fn = lambda: Craft1stWeapon(bot)
    bot.States.AddCustomState(exec_fn, "Craft 1st Weapon")
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")

def Missing_Shipment(bot: Botting):
    bot.States.AddHeader("Quest: Missing Shipment") # 500 XP
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-10235, 16557, 0x827501)
    bot.Travel_To_Random_District(target_map_id=431) #Sunspear Great Hall
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[2,3,4])
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(-1237.25, 3188.38, 0x85) #Blessing 
    bot.Move.XY(-4638.69, 1484.08)
    bot.Move.XY(-7226.91, 3327.59)
    bot.Move.XY(-8478.89, 9617.20)
    bot.Move.XY(-9389.65, 16276.98)
    bot.Wait.UntilOutOfCombat()
    bot.Interact.WithGadgetID(7458)
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-10235, 16557, 0x827507)

def Proof_of_Courage_and_Suwash_the_Pirate(bot: Botting):
    bot.States.AddHeader("Quests: Proof of Courage and Suwash the Pirate") # 500 XP each
    bot.Travel_To_Random_District(target_map_id=431) #Sunspear Great Hall
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,2,4])
    bot.Move.XYAndDialog(-4358, 6535, 0x829301) #Proof of Courage
    bot.Move.XYAndDialog(-4558, 4693, 0x826201) #Suwash the Pirate
    bot.Move.XYAndExitMap(-3172, 3271, 430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-1840.23, 2432.96)
    bot.Move.XYAndDialog(-1297.00, 3229.00, 0x85) #Insect Bounty
    bot.Move.XY(-3972, 1703) #Proof of courage
    bot.Move.XY(-6784, -3484)
    bot.Wait.UntilOutOfCombat()
    bot.Interact.WithGadgetAtXY(-6418, -3759) #Corsair Chest
    bot.Wait.ForTime(2000)
    bot.Move.XY(-5950, -6889) #Suwash the Pirate 1
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-10278, -7011) #Suwash the Pirate 2
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-10581, -11798) #Suwash the Pirate 3
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(-16795, -12217, 0x85) #Blessing
    bot.Move.XY(-15896, -10190) #Suwash the Pirate 4
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(-15573, -9638, 0x826204) #Suwash the Pirate turnin
    bot.Travel_To_Random_District(target_map_id=431) #Sunspear Great Hall
    bot.Move.XYAndDialog(-4367, 6542, 0x829307) #Proof of Courage Reward
    bot.Move.XYAndDialog(-4558, 4693, 0x826207) #Suwash the Pirate reward
    bot.Wait.ForTime(2000)

def A_Hidden_Threat(bot: Botting):
    bot.States.AddHeader("Quest: A Hidden Threat") # 500 XP
    bot.Travel_To_Random_District(target_map_id=431) #Sunspear Great Hall
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,2,4])
    bot.Move.XYAndDialog(-1835, 6505, 0x825A01) #Shaurom
    bot.Move.XYAndExitMap(-3172, 3271, 430) #Plains of Jarin
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-1840.23, 2432.96)
    bot.Move.XYAndDialog(-1297.00, 3229.00, 0x85) #Insect Bounty
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-4680.29, 1867.42)
    bot.Move.XY(-13276.00, -151.00)
    bot.Move.XY(-17946.33, 2426.69)
    bot.Move.XY(-17614.74, 11699.77)
    bot.Move.XY(-18657.45, 14601.87)
    bot.Move.XY(-16911.47, 19039.31)
    bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    # bot.Move.XYAndExitMap(-20136, 16757, target_map_id=502) #The Astralarium skip for Proof Farm
    bot.Travel_To_Random_District(target_map_id=431) #Sunspear Great Hall
    bot.Move.XYAndDialog(-1835, 6505, 0x825A07) #A Hidden Threat reward

def Identity_Theft(bot: Botting):
    bot.States.AddHeader("Quest: Identity Theft") # 500 XP
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XY(-7519.91, 14468.26)
    bot.Move.XYAndDialog(-10461, 15229, 0x827201) #take quest
    bot.Travel_To_Random_District(target_map_id=479) #Champions Dawn
    bot.Move.XYAndDialog(25345, 8604, 0x827204)
    PrepareForBattle(bot, Hero_List=[], Henchman_List=[1,6,7])
    bot.Move.XYAndExitMap(22483, 6115, target_map_id=432) #Cliffs of Dohjok
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(20215, 5285, 0x85) #Blessing 
    bot.Items.AddModelToLootWhitelist(15850)
    bot.Move.XY(14429, 10337) #kill boss
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot) #To Stop all combat to loot item without timeout
    bot.Items.LootItems()
    bot.Wait.ForTime(1000)
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XY(-7519.91, 14468.26)
    bot.Move.XYAndDialog(-10461, 15229, 0x827207) # +500xp

def Configure_Player_Build(bot: Botting):
    bot.States.AddHeader("Configure Player Build")
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    
    # First: Buy Mesmer skills in Kamadan for specific professions
    if profession in ["Mesmer", "Elementalist", "Monk", "Necromancer"]:
        bot.Travel_To_Random_District(target_map_id=449) #Kamadan
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x853702) #Wastrels Demise
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x867902) #Signet of Clumsiness  
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x883603) #Cry of Pain
    elif profession == "Ranger":
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x857A02) # Critical Chop
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x815402) #Disrupting Chop
        bot.Move.XYAndDialog(-11385, 16140, 0x85) #Buy a hero point
        bot.Dialogs.AtXY(-11385, 16140, 0x81A802) #Throw Dirt
    elif profession == "Paragon":
        bot.Move.XYAndDialog(-11385, 16140, 0x860B02) #Mighty Throw

    # Second: Travel to Sunspear Great Hall and get profession-specific skills
    bot.Travel_To_Random_District(target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForMapToChange(target_map_id=431)
    bot.Move.XYAndDialog(-2864, 7031, 0x82CB07)
    
    if profession == "Dervish":
        bot.Move.XYAndDialog(-3317, 7053, 0x883B03) #Whirlwind Attack"
        bot.Dialogs.AtXY(-3317, 7053, 0x86E302) #Zealous Renewal
        bot.Dialogs.AtXY(-3317, 7031, 0x85CF02) #Twin Moon Sweep
        bot.Dialogs.AtXY(-3317, 7053, 0x85) #Buy hero point
        bot.Dialogs.AtXY(-3317, 7031, 0x85DF02) #Mystic Vigor
    elif profession == "Paragon":
        bot.Move.XYAndDialog(-3317, 7053, 0x884003) #There's Nothing to Fear
        bot.Dialogs.AtXY(-3317, 7053, 0x860E02) #Unblockable Throw"
    elif profession == "Elementalist":
        bot.Move.XYAndDialog(-3317, 7053, 0x803D02) #Leech Signet
        bot.Dialogs.AtXY(-3317, 7053, 0x854002) #Web of Disruption
        bot.Dialogs.AtXY(-3317, 7053, 0x85) #Buy hero point
        bot.Dialogs.AtXY(-3317, 7053, 0x801702) #Power Spike"
    elif profession == "Mesmer":
        bot.Move.XYAndDialog(-3317, 7053, 0x803D02) #Leech Signet
        bot.Dialogs.AtXY(-3317, 7053, 0x854002) #Web of Disruption
        bot.Dialogs.AtXY(-3317, 7053, 0x85) #Buy hero point
        bot.Dialogs.AtXY(-3317, 7053, 0x801702) #Power Spike"
    elif profession == "Necromancer":
        bot.Move.XYAndDialog(-3317, 7053, 0x803D02) #Leech Signet
        bot.Dialogs.AtXY(-3317, 7053, 0x854002) #Web of Disruption
        bot.Dialogs.AtXY(-3317, 7053, 0x85) #Buy hero point
        bot.Dialogs.AtXY(-3317, 7053, 0x801702) #Power Spike
    elif profession == "Monk":
        bot.Move.XYAndDialog(-3317, 7053, 0x803D02) #Leech Signet
        bot.Dialogs.AtXY(-3317, 7053, 0x854002) #Web of Disruption
        bot.Dialogs.AtXY(-3317, 7053, 0x85) #Buy hero point
        bot.Dialogs.AtXY(-3317, 7053, 0x801702) #Power Spike
    elif profession == "Warrior":
        bot.Move.XYAndDialog(-3317, 7053, 0x883B03) #Whirlwind Attack"
        bot.Dialogs.AtXY(-3317, 7053, 0x86E302) #Zealous Renewal
    elif profession == "Ranger":
        bot.Move.XYAndDialog(-3317, 7053, 0x883B03) #Whirlwind Attack"
        
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")

def Honing_your_Skills(bot: Botting):
    bot.States.AddHeader("Quest: Honing your Skills")
    bot.Travel_To_Random_District(target_map_id=449)
    bot.Move.XYAndDialog(-7874.00, 9799.00, 0x828901)
    bot.Wait.ForTime(1000)
    bot.Move.XYAndDialog(-7874.00, 9799.00, 0x828907)

def Command_Training(bot: Botting):
    bot.States.AddHeader("Quest: Command Training") # 250 XP
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-7874, 9799, 0x82C801)
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[3,4])
    bot.Move.XY(-4383, -2078)
    bot.Move.XYAndDialog(-7525, 6288, 0x84, step_name="Churrhir Fields") 
    bot.Wait.ForMapToChange(target_map_id=456)
    bot.Move.XYAndDialog(-2000, -2825,0x8B) #Command Training
    bot.Party.FlagAllHeroes(1110, -4175)
    bot.Wait.ForTime(35000) #Flag 2
    bot.Party.FlagAllHeroes(-2362, -6126)
    bot.Wait.ForTime(35000) #Flag 3
    bot.Party.FlagAllHeroes(-222, -5832)
    bot.Wait.ForTime(7000) #Flag 1. use this order to avoid mob spawns
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Move.XYAndDialog(-7874, 9799, 0x82C807)

def Secondary_Training(bot: Botting):  
    bot.States.AddHeader("Quest: Secondary Training")
    bot.Travel_To_Random_District(target_map_id=449) #Kamadan
    bot.Party.LeaveParty()
    bot.Move.XYAndDialog(-7910, 9740, 0x825901)
    bot.Move.XYAndDialog(-7525, 6288, 0x84)
    bot.Wait.ForMapToChange(target_map_id=456)
    ConfigurePacifistEnv(bot)
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if profession == "Necromancer": 
        bot.Move.XYAndDialog(-7149, 1830, 0x7F) #Mesmer
        bot.Move.XYAndDialog(-7161, 4808, 0x825907)
    else:    
        bot.Move.XYAndDialog(-6557.00, 1837, 0x7F) #this is fine, need minimal skill bar for level 4 to avoid skill equip window
        bot.Move.XYAndDialog(-7161, 4808, 0x825907)
    
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if profession == "Warrior":
        bot.Move.XYAndDialog(-7161, 4808, 0x8A) #Dervish 2nd
        bot.Dialogs.AtXY(-7161, 4808, 0x825407)
        bot.Dialogs.AtXY(-7161, 4808, 0x827801)
    elif profession in ["Necromancer", "Monk", "Elementalist"]:
        bot.Move.XYAndDialog(-7161, 4808, 0x84) #Mes 2nd
        bot.Dialogs.AtXY(-7161, 4808, 0x825407)
        bot.Dialogs.AtXY(-7161, 4808, 0x827801)  
    else:   
        bot.Dialogs.AtXY(-7161, 4808, 0x88) #change to Warrior
        bot.Dialogs.AtXY(-7161, 4808, 0x825407)
        bot.Dialogs.AtXY(-7161, 4808, 0x827801)

def Chahbek_Village_Mission_2(bot: Botting):
    bot.States.AddHeader("Chahbek Village Mission_2")
    bot.Map.Travel(target_map_id=544)
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[1,2])
    bot.SkillBar.LoadHeroSkillBar(1, "OQASEF6EC1vcNABWAAAA") #Koss
    bot.Move.XYAndDialog(3485, -5246, 0x81)
    bot.Dialogs.AtXY(3485, -5246, 0x84)
    bot.Wait.ForTime(2000)
    bot.Wait.UntilOnExplorable()
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(2240, -3535)
    bot.Move.XY(227, -5658)
    bot.Move.XY(-1144, -4378)
    bot.Move.XY(-2058, -3494)
    bot.Move.XY(-4725, -1830)
    bot.Interact.WithGadgetAtXY(-4725, -1830) #Oil 1
    bot.Move.XY(-1725, -2551)
    bot.Wait.ForTime(1500)
    bot.Interact.WithGadgetAtXY(-1725, -2550) #Cata load
    bot.Wait.ForTime(1500)
    bot.Interact.WithGadgetAtXY(-1725, -2550) #Cata fire
    bot.Move.XY(-4725, -1830) #Back to Oil
    bot.Interact.WithGadgetAtXY(-4725, -1830) #Oil 2
    bot.Move.XY(-1731, -4138)
    bot.Interact.WithGadgetAtXY(-1731, -4138) #Cata 2 load
    bot.Wait.ForTime(2000)
    bot.Interact.WithGadgetAtXY(-1731, -4138) #Cata 2 fire
    bot.Move.XY(-2331, -419)
    bot.Move.XY(-1685, 1459)
    bot.Move.XY(-2895, -6247)
    bot.Move.XY(-3938, -6315) #Boss
    bot.Wait.ForMapToChange(target_map_id=456)

def Deposit_Proof_Of_Legend(bot: Botting):
    bot.States.AddHeader("Deposit Proof of Legend")
    bot.Travel_To_Random_District(target_map_id=449) # Kamadan
    bot.Items.Deposit(37841)  # Proof of Legend model ID
    bot.Items.WithdrawGold(0)  # deposit all gold, keep 0 on character

#region Reroll (Logout -> Delete -> Recreate)

def _resolve_character_name():
    global LAST_CHARACTER_NAME

    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(Player.GetAgentID())
    name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
    if name:
        LAST_CHARACTER_NAME = name
        yield from Routines.Yield.wait(100)
        return name

    try:
        if Map.Pregame.InCharacterSelectScreen():
            pregame = GWContext.PreGame.GetContext()
            if pregame and hasattr(pregame, "chars_list") and hasattr(pregame, "chosen_character_index"):
                idx = int(pregame.chosen_character_index)
                if 0 <= idx < len(pregame.chars_list):
                    name = str(pregame.chars_list[idx])
                    if name:
                        LAST_CHARACTER_NAME = name
                        yield from Routines.Yield.wait(100)
                        return name
    except Exception:
        pass

    yield from Routines.Yield.wait(100)
    return LAST_CHARACTER_NAME


def _generate_fallback_name(current_name: str) -> str:
    suffixes = ["A", "B", "C", "D", "E", "F", "K", "H", "I", "J"]

    cleaned = "".join(ch for ch in (current_name or "") if ch.isalpha() or ch == " ")
    cleaned = " ".join(cleaned.split())

    if not cleaned:
        return "Fallback A"

    parts = cleaned.split()

    current_suffix = None
    if parts and parts[-1] in suffixes:
        current_suffix = parts[-1]

    while parts and parts[-1] in suffixes:
        parts.pop()

    base_name = " ".join(parts).strip()
    if not base_name:
        base_name = "Fallback"

    if current_suffix in suffixes:
        idx = suffixes.index(current_suffix)
        suffix = suffixes[(idx + 1) % len(suffixes)]
    else:
        suffix = suffixes[0]

    return f"{base_name} {suffix}"


def type_text_keystroke(text: str, delay_ms: int = 50):
    """Type text character-by-character using keystrokes to avoid clipboard conflicts."""
    yield from Routines.Yield.wait(1000)
    for char in text:
        if char in CHAR_MAP:
            key, needs_shift = CHAR_MAP[char]
            if needs_shift:
                Keystroke.Press(Key.LShift.value)
                yield from Routines.Yield.wait(50)
            Keystroke.PressAndRelease(key.value)
            yield from Routines.Yield.wait(delay_ms)
            if needs_shift:
                Keystroke.Release(Key.LShift.value)
                yield from Routines.Yield.wait(50)
        else:
            ConsoleLog("TextInput", f"Skipping unmapped character: '{char}'", Py4GW.Console.MessageType.Warning)


def custom_delete_character(character_name: str, timeout_ms: int = 45000):
    """Delete a character using keystrokes instead of clipboard."""
    from Py4GWCoreLib.routines_src.Yield import Yield

    try:
        WindowFrames = getattr(Yield, "WindowFrames", None)
        if WindowFrames and hasattr(WindowFrames, "DeleteCharacterButton"):
            WindowFrames.DeleteCharacterButton.FrameClick()
            yield from Routines.Yield.wait(2000)

            yield from type_text_keystroke(character_name)
            yield from Routines.Yield.wait(2000)

            if hasattr(WindowFrames, "FinalDeleteCharacterButton"):
                WindowFrames.FinalDeleteCharacterButton.FrameClick()
                yield from Routines.Yield.wait(5000)

            return True
    except Exception as e:
        ConsoleLog("CustomDelete", f"Error in custom delete: {e}", Py4GW.Console.MessageType.Error)
        return False


def custom_create_character(character_name: str, campaign_name: str, profession_name: str, timeout_ms: int = 60000):
    """Create a character using keystrokes instead of clipboard."""
    from Py4GWCoreLib.routines_src.Yield import Yield

    try:
        WindowFrames = getattr(Yield, "WindowFrames", None)
        if not WindowFrames:
            return False

        if hasattr(WindowFrames, "CreateCharacterNextButtonGeneric"):
            WindowFrames.CreateCharacterNextButtonGeneric.FrameClick()
            yield from Routines.Yield.wait(3000)

            yield from type_text_keystroke(character_name)
            yield from Routines.Yield.wait(2000)

            if hasattr(WindowFrames, "FinalCreateCharacterButton"):
                WindowFrames.FinalCreateCharacterButton.FrameClick()
                yield from Routines.Yield.wait(1000)

            return True
    except Exception as e:
        ConsoleLog("CustomCreate", f"Error in custom create: {e}", Py4GW.Console.MessageType.Error)
        return False


def LogoutAndDeleteState():
    """State: logout -> delete -> recreate -> restart routine."""
    ConsoleLog("Reroll", "Start: Logout > Delete > Recreate", Py4GW.Console.MessageType.Info)

    char_name = yield from _resolve_character_name()
    if not char_name:
        ConsoleLog("Reroll", "Unable to resolve character name. Abort.", Py4GW.Console.MessageType.Error)
        return

    primary_prof, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if not primary_prof:
        primary_prof = LAST_PRIMARY_PROF or "Warrior"
    campaign_name = "Nightfall"

    RC = getattr(getattr(Routines, "Yield", None), "RerollCharacter", None)
    if not RC:
        ConsoleLog("Reroll", "RerollCharacter API not found.", Py4GW.Console.MessageType.Error)
        return

    ConsoleLog("Reroll", f"Target='{char_name}' prof='{primary_prof}' camp='{campaign_name}'", Py4GW.Console.MessageType.Info)

    # 1) Logout
    Map.Pregame.LogoutToCharacterSelect()
    yield from Routines.Yield.wait(7000)

    # 2) Delete character (keystroke-based to avoid clipboard conflicts)
    success = yield from custom_delete_character(char_name)
    if not success:
        ConsoleLog("Reroll", "Custom delete failed, falling back to framework method", Py4GW.Console.MessageType.Warning)
        try:
            yield from RC.DeleteCharacter(character_name_to_delete=char_name, timeout_ms=45000, log=True)
        except TypeError:
            yield from RC.DeleteCharacter(character_name=char_name, timeout_ms=45000, log=True)

    yield from Routines.Yield.wait(7000)

    # 3) Resolve final name (handle case where original name is still locked)
    try:
        names = [c.player_name for c in Map.Pregame.GetAvailableCharacterList()]
    except Exception:
        names = []

    if char_name in names:
        final_name = _generate_fallback_name(char_name)
        ConsoleLog("Reroll", f"Original name still locked. Using '{final_name}'.", Py4GW.Console.MessageType.Warning)
    else:
        final_name = char_name

    # 4) Create character (keystroke-based to avoid clipboard conflicts)
    success = yield from custom_create_character(final_name, campaign_name, primary_prof)
    if not success:
        ConsoleLog("Reroll", "Custom create failed, falling back to framework method", Py4GW.Console.MessageType.Warning)
        yield from RC.CreateCharacter(
            character_name=final_name,
            campaign_name=campaign_name,
            profession_name=primary_prof,
            timeout_ms=60000,
            log=True
        )

    yield from Routines.Yield.wait(7000)

    ConsoleLog("Reroll", "Reroll finished. Restarting routine.", Py4GW.Console.MessageType.Info)
    yield from Routines.Yield.wait(3000)

    ActionQueueManager().ResetAllQueues()
    bot.SetMainRoutine(create_bot_routine)
    return


def ScheduleNextRun():
    """State: wait until in game, then re-add the entire routine (infinite loop)."""
    for _ in range(200):  # ~20s max
        if not Map.Pregame.InCharacterSelectScreen():
            break
        yield from Routines.Yield.wait(100)

    yield from Routines.Yield.wait(1000)
    create_bot_routine(bot)

#endregion

#region MAIN
selected_step = 0
filter_header_steps = True

iconwidth = 64

def _draw_texture():
    global iconwidth
    level = Agent.GetLevel(Player.GetAgentID())

    projects_path = Py4GW.Console.get_projects_path()
    art_path = os.path.join(projects_path, "Bots", "Leveling", "Nightfall", "Nightfall_leveler-art.png")
    fallback_path = os.path.join(projects_path, MODULE_ICON)
    has_leveler_art = os.path.exists(art_path)
    path = art_path if has_leveler_art else fallback_path
    size = (float(iconwidth), float(iconwidth))
    tint = (255, 255, 255, 255)
    border_col = (0, 0, 0, 0)  # <- ints, not normalized floats

    if not has_leveler_art:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.0, 0.0), uv1=(1.0, 1.0),
                                  tint=tint, border_color=border_col)
    elif level <= 3:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.0, 0.0),   uv1=(0.25, 1.0),
                                  tint=tint, border_color=border_col)
    elif level <= 5:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.25, 0.0), uv1=(0.5, 1.0),
                                  tint=tint, border_color=border_col)
    elif level <= 9:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.5, 0.0),  uv1=(0.75, 1.0),
                                  tint=tint, border_color=border_col)
    else:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.75, 0.0), uv1=(1.0, 1.0),
                                  tint=tint, border_color=border_col)

def _draw_help():
    title_color = Color(255, 200, 100, 255)

    PyImGui.text_wrapped(
        "This bot runs a fresh Nightfall character through the Proof of Legend route."
    )
    PyImGui.spacing()

    PyImGui.text_colored("Quick Explanation:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Create a new Nightfall character before starting the bot.")
    PyImGui.bullet_text("The bot progresses the character to level 5.")
    PyImGui.bullet_text("It then farms Chahbek Village again and deposits the Proof of Legend.")
    PyImGui.bullet_text("After the deposit is complete, that character is intended to be deleted and recreated for the next run.")
    PyImGui.spacing()

    PyImGui.text_colored("Notes:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("This is a reroll-style farming bot, not a normal long-term character leveler.")
    PyImGui.bullet_text("Make sure you start on a disposable character you are willing to delete.")

bot.SetMainRoutine(create_bot_routine)
bot.UI.override_draw_texture(_draw_texture)
bot.UI.override_draw_help(_draw_help)

def main():
    bot.Update()
    bot.UI.draw_window()

def tooltip():
    PyImGui.set_next_window_size((600, 0))
    PyImGui.begin_tooltip()
    
    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.image(MODULE_ICON, (32, 32))
    PyImGui.same_line(0, 10)
    ImGui.push_font("Regular", 20)
    ImGui.text_aligned(MODULE_NAME, alignment=Alignment.MidLeft, color=title_color.color_tuple, height=32)
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.spacing()
    
    # Quick explanation
    PyImGui.text_colored("Quick Explanation:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Start with a newly created Nightfall character.")
    PyImGui.bullet_text("The bot reaches level 5, farms Chahbek Village again and deposits the Proof of Legend.")
    PyImGui.bullet_text("After the deposit, the character is deleted and recreated for the next run.")
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Wick aka Divinus")
    
    PyImGui.end_tooltip()
    
if __name__ == "__main__":
    main()

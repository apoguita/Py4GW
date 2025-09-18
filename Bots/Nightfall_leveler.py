from Py4GWCoreLib import (Botting, Routines, GLOBAL_CACHE, ModelID, ImGui)

bot = Botting("NF Leveler")
     
def create_bot_routine(bot: Botting) -> None:
    skip_tutorial_dialog(bot)
    travel_to_guild_hall(bot)
    approach_jahdugar(bot)
    Quiz_the_recruits(bot)
    Configure_first_Battle(bot)
    Enter_Chahbek_Mission(bot)
    Learn_more(bot)
    storage_quests(bot)
    Take_Quests(bot)
    Farm_for_quests(bot)
    SSGH_quests(bot)
    second_profession(bot)
    after_level_5(bot)
    jokanur_diggings_quests(bot)
#region Helpers

def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.Properties.Disable("pause_on_danger")
    bot.Properties.Enable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=15000)
    bot.Properties.Disable("auto_combat")
    bot.Properties.Disable("imp")
    
def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("imp")
    bot.Items.SpawnBonusItems()
    bot.Items.DestroyBonusItems(exclude_list = [ModelID.Igneous_Summoning_Stone.value, ModelID.Bonus_Nevermore_Flatbow.value])
    
def PrepareForBattle(bot: Botting, Hero_List = [], Henchman_List = []) -> None:
    ConfigureAggressiveEnv(bot)
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    bot.Party.AddHeroList(Hero_List)
    bot.Party.AddHenchmanList(Henchman_List)

def EquipSkillBar(): 
    global bot

    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())
    if profession == "Dervish":
        if level <= 2: #5 attribute points available
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkKrBbMiXprAAAAAAAAAAAA")
        elif level <= 3: #10 attribute points available
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkOqxqMiXpb1dA/fBAAABAA")
        elif level <= 4: #15 attribute points available
            yield from Routines.Yield.Skills.LoadSkillbar("OgCkkSqxqwGj4V6WdHw/XAAAAjD")
        elif level <= 5: #20 attribute points available
            yield from Routines.Yield.Skills.LoadSkillbar("OgCkkWqxqwGDCW6WdHw/Xx74FjD")
        elif level <= 6: #40 attribute points available (Ranger 2nd profession available)
            yield from Routines.Yield.Skills.LoadSkillbar("OgKjYRZ3aMVXFDAAAAAEv0mNDA")
        elif level <= 8: #50 attribute points available
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkKrBbMiXprAAAAAAAAAAAA")
        elif level <= 9: #55 attribute points available
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkKrBbMiXprAAAAAAAAAAAA")
        elif level <= 10: #55 attribute points available
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkKrBbMiXprAAAAAAAAAAAA")
        else: #20 attribute points available
            yield from Routines.Yield.Skills.LoadSkillbar("OgCjkKrBbMiXprAAAAAAAAAAAA")
    elif profession == "Paragon":
        yield from Routines.Yield.Skills.LoadSkillbar("OwJkYRZ5XMGiiBbuMAAAAAtJAA")   

def EquipHeroSkillBar(): 
    global bot

    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if profession == "Dervish":
        yield from Routines.Yield.Skills.LoadHeroSkillbar("OgKjYRZ3aMVXFDAAAAAEv0mNDA")
    elif profession == "Assassin":
        yield from Routines.Yield.Skills.LoadHeroSkillbar("OQKjkKrBbMiXprAAAAAAAAAAAA")
    elif profession == "Ritualist":
        yield from Routines.Yield.Skills.LoadHeroSkillbar("OQKjkKrBbMiXprAAAAAAAAAAAA")       
    elif profession == "Ranger":
        yield from Routines.Yield.Skills.LoadHeroSkillbar("OggjYZZIYMKG1pvBAAAAA0GBAA")
    elif profession == "Monk":
        yield from Routines.Yield.Skills.LoadHeroSkillbar("OwUTIkHBppkkRortEQSRIHETAA")
    elif profession == "Necromancer":
        yield from Routines.Yield.Skills.LoadHeroSkillbar("OAJTYJckzQxw23AAAAg2CAA")
    elif profession == "Mesmer":
        yield from Routines.Yield.Skills.LoadHeroSkillbar("OQJTYJckzQxw23AAAAg2CAA")
    elif profession == "Elementalist":
        yield from Routines.Yield.Skills.LoadHeroSkillbar("OgJUwCLhjcGKG2+GAAAA0WAA")
    elif profession == "Warrior":
        yield from Routines.Yield.Skills.LoadHeroSkillbar("OQgkQNVCoEGjQxvwVCAPuvp68iB")
    elif profession == "Paragon":
        yield from Routines.Yield.Skills.LoadHeroSkillbar("OwJkYRZ5XMGiiBbuMAAAAAtJAA")   

#region Start

def skip_tutorial_dialog(bot: Botting) -> None:
    bot.States.AddHeader("Skipping Tutorial Dialogs")
    bot.Move.XYAndDialog(10289, 6405, 0x82A503, step_name="Skip Tutorial Dialog 1")
    bot.Dialogs.AtXY(10289, 6405, 0x82A501, step_name="Skip Tutorial Dialog 2")  
    
def travel_to_guild_hall(bot: Botting):
    bot.States.AddHeader("Traveling to Guild Hall")
    bot.Map.TravelGH()
    bot.Map.LeaveGH()
    bot.Wait.ForTime(5000) # Wait for cinematics to finish

def approach_jahdugar(bot: Botting):
    bot.States.AddHeader("Approaching Jahdugar")
    bot.Move.XYAndDialog(3493, -5247, 0x82A507, step_name="Talk to First Spear Jahdugar")
    bot.Move.XYAndDialog(3493, -5247, 0x82C501, step_name="You can count on me")

def Quiz_the_recruits(bot: Botting):
    bot.States.AddHeader("Quiz the Recruits")
    bot.Move.XY(4750, -6105, step_name="Move to Quiz NPC")
    bot.Move.XYAndDialog(4750, -6105, 0x82C504, step_name="Answer Quiz 1")
    bot.Move.XYAndDialog(5019, -6940, 0x82C504, step_name="Answer Quiz 2")
    bot.Move.XYAndDialog(3540, -6253, 0x82C504, step_name="Answer Quiz 3")
    bot.Wait.ForTime(1000)
    bot.Move.XY(3485, -5246, step_name="Return to Jahdugar")
    bot.Dialogs.AtXY(3485, -5246, 0x82C507, step_name="Accept Quest")
    bot.Move.XYAndDialog(3433, -5900, 0x82C701, step_name="My own henchmen")
    

def Configure_first_Battle(bot: Botting):
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[1,2])
    bot.States.AddCustomState(EquipHeroSkillBar, "Koss Skill Bar")
    bot.Items.Equip(15591) #starter schythe
    bot.Dialogs.AtXY(3433, -5900, 0x82C707, step_name="Accept")

def Enter_Chahbek_Mission(bot: Botting):
    bot.States.AddHeader("Enter Chahbek Mission")
    bot.Dialogs.AtXY(3485, -5246, 0x81)
    bot.Dialogs.AtXY(3485, -5246, 0x84)
    bot.Wait.ForTime(2000)
    bot.Wait.UntilOnExplorable()
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

def Learn_more(bot: Botting):
    bot.States.AddHeader("First Spear Dehvad")
    ConfigurePacifistEnv(bot) #we dont want to fight, we are pascifist
    bot.Move.XY(-7158, 4894)
    bot.Move.XYAndDialog(-7158, 4894, 0x825801, step_name="Couldn't hurt to learn")
    bot.Move.XY(-12092, -704)
    bot.Move.XYAndDialog(-12107, -705, 0x7F, step_name="Teach me 1")
    bot.Move.XY(-12200, 473)
    bot.Move.XYAndDialog(-7139, 4891, 0x825807, step_name="Accept reward")
    bot.States.AddHeader("Honing Your Skills")
    bot.Move.XYAndDialog(-7158, 4894, 0x828901, step_name="Honing your skills")
    bot.UI.CancelSkillRewardWindow()
    bot.Dialogs.AtXY(-7183, 4904, 0x828901, step_name="I'll be back in no time")
    bot.Move.XYAndDialog(-7383, 5706, 0x81, step_name="Take me to Kamadan")
    bot.Dialogs.AtXY(-7383, 5706, 0x84, step_name="Yes please")
    bot.Wait.ForMapToChange(target_map_id=449)

def storage_quests(bot: Botting):
    bot.States.AddHeader("Storage Quests")
    bot.Move.XYAndDialog(-9251, 11826, 0x82A101, step_name="Storage Quest 0")
    bot.Move.XYAndDialog(-7761, 14393, 0x84, step_name="50 Gold please")
    bot.Move.XYAndDialog(-9251, 11826, 0x82A107, step_name="Accept reward")
    
def Take_Quests(bot: Botting):
    bot.States.AddHeader("Quality Weapons")
    bot.Move.XYAndDialog(-11208, 8815, 0x826003, step_name="Quality Steel")
    bot.Dialogs.AtXY(-11208, 8815, 0x826001)
    bot.States.AddHeader("Material Girl")
    bot.Move.XYAndDialog(-11363, 9066, 0x826103, step_name="Material Girl")
    bot.Dialogs.AtXY(-11363, 9066, 0x826101)
    #bot.Move.XYAndDialog(-10470, 15141, 0x827203, step_name="Identity Theft")
    #bot.Dialogs.AtXY(-10470, 15141, 0x827201)
    
def Farm_for_quests(bot: Botting):
    bot.States.AddHeader("Prepare for quests")
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[2,4])
    bot.States.AddHeader("Plains of Jarin")
    bot.Move.XYAndExitMap(-9326, 18151, target_map_id=430) #Plains of Jarin
    bot.Wait.ForMapToChange(target_map_id=430)
    bot.Move.XY(18460, 1002, step_name="Bounty")
    bot.Move.XYAndDialog(18460, 1002, 0x85) #Blessing 
    #bot.Dialogs.AtXY(18460, 1002, 0x85, step_name="We'll do our best")
    bot.Move.XY(12900, 3474)
    bot.Move.XYAndDialog(9100, -1239, 0x826104, step_name="Material Girl")
    bot.Move.XY(9464, -2639, step_name="Killer Plants 1")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(10183, -6428, step_name="Killer Plants 2")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(9681, -9300, step_name="Killer Plants 3")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7555, -6791, step_name="Killer Plants 4")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(5073, -4850, step_name="Killer Plants 5")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(9292, -1220, 0x826104, step_name="Material Girl")
    bot.Move.XY(6257, -1432, step_name="Kill Suneh boss")
    bot.Move.XYAndDialog(-1782, 2790, 0x828801, step_name="Map Travel")
    bot.Move.XY(-3492, 2612)
    bot.Move.XYAndExitMap(-3236, 4503, target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForMapToChange(target_map_id=431)
    bot.States.AddHeader("Back to Kamadan")
    bot.Map.Travel(target_map_id=449) #Kamadan
    bot.Wait.ForMapToChange(target_map_id=449)
    bot.Move.XYAndDialog(-10024, 8590, 0x828804, step_name="Map Travel Inventor")
    bot.Dialogs.AtXY(-10024, 8590, 0x828807)
    bot.Move.XYAndDialog(-11356, 9066, 0x826107, step_name="accept reward")
    
def SSGH_quests(bot: Botting):
    bot.States.AddHeader("Back to Sunspear Great Hall")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForMapToChange(target_map_id=431)
    bot.Move.XYAndDialog(-4076, 5362, 0x826004, step_name="Quality Steel")
    bot.Move.XYAndDialog(-2888, 7024, 0x84, step_name="SS rebirth Signet")
    bot.Dialogs.AtXY(-2888, 7024, 0x82CB03, step_name="Attribute Points Quest 1")
    bot.Dialogs.AtXY(-2888, 7024, 0x82CB01)
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[2,4])
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    bot.Wait.ForMapToChange(target_map_id=430)
    bot.States.AddHeader("Plains of Jarin 2")
    bot.Move.XYAndDialog(-1237.25, 3188.38, 0x85) #Blessing 
    bot.Move.XY(-3225, 1749)
    bot.Move.XY(-995, -2423) #fight
    bot.Move.XY(-513, 67) #fight more
    bot.Wait.UntilOutOfCombat()
    bot.Map.Travel(target_map_id=449) #Kamadan
    bot.Wait.ForMapToChange(target_map_id=449)
    bot.Move.XYAndDialog(-11208, 8815, 0x826007, step_name="Accept reward")
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar") # Level 4 skill bar
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForMapToChange(target_map_id=431)
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    bot.Wait.ForMapToChange(target_map_id=430)
    bot.Move.XYAndDialog(-1237.25, 3188.38, 0x85) #Blessing 
    bot.Move.XY(-4507, 616)
    bot.Move.XY(-7611, -5953)
    bot.Move.XY(-18083, -11907) 
    bot.Move.XYAndExitMap(-19518, -13021, target_map_id=479) #Champions Dawn
    bot.Wait.ForMapToChange(target_map_id=479)
    bot.States.AddHeader("Champions Dawn")
    #bot.Move.XYAndDialog(25300, 8669, 0x827204, step_name="Identity Theft continued")
    #bot.Move.XYAndExitMap(22483, 6115, target_map_id=432) #Cliffs of Dohjok
    #bot.Wait.ForMapToChange(target_map_id=432)
    #bot.Move.XY(20319, 5280)
    #bot.Move.XYAndDialog(20319, 5280, 0x85) #Blessing 
    #bot.Wait.ForTime(2000)
    #bot.Move.XY(14675, 10279)
    #bot.Wait.UntilOutOfCombat()
    #bot.Interact.WithItemAtXY(13818, 10304) #Shipment Crate
    #bot.Map.Travel(target_map_id=449) #Kamadan
    #bot.Wait.ForMapToChange(target_map_id=449)
    #bot.Move.XYAndDialog(-10461, 15229, 0x827207, step_name="Identity Theft complete")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForMapToChange(target_map_id=431)
    bot.States.AddHeader("Sunspear Great Hall 3")
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[2,4])

    bot.Move.XYAndDialog(-1835, 6505, 0x825A01, step_name="A Hidden Threat")
    bot.Move.XYAndDialog(-4358, 6535, 0x829301, step_name="Proof of Courage")
    bot.Move.XYAndDialog(-4558, 4693, 0x826201, step_name="Suwash the Pirate")
    bot.States.AddHeader("Plains of Jarin 3")
    bot.Move.XYAndExitMap(-3172, 3271, target_map_id=430) #Plains of Jarin
    bot.Wait.ForMapToChange(target_map_id=430)
    bot.Move.XYAndDialog(-1237.25, 3188.38, 0x85) #Blessing 
    bot.Move.XY(-3972, 1703) #proof of courage
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
    bot.Move.XY(-15896, -10190) #Suwash the Pirate 4
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndDialog(-15573, -9638, 0x826204, step_name="Suwash the Pirate complete")
    bot.Move.XY(-13230, -148) #A Hidden Threat 1
    bot.Move.XY(-16920, 746) #A Hidden Threat 2
    bot.Move.XY(-17706, 3259)
    bot.Move.XYAndDialog(-17706, 3259, 0x85) #Blessing 
    bot.Wait.ForTime(2000)
    bot.Move.XY(-17673, 11492) #A Hidden Threat 3
    bot.Move.XY(-18751, 14973) #A Hidden Threat 4
    bot.Move.XY(-17535.23, 18600) #A Hidden Threat 5
    bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndExitMap(-20136, 16757, target_map_id=502) #The Astralarium
    bot.Wait.ForMapToChange(target_map_id=502)
    bot.States.AddHeader("The Astralarium")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForMapToChange(target_map_id=431)
    bot.Move.XYAndDialog(-4367, 6542, 0x829307, step_name="Proof of Courage Reward")
    bot.Move.XYAndDialog(-4558, 4693, 0x826207, step_name="Suwash the Pirate reward")
    bot.Move.XYAndDialog(-1835, 6505, 0x825A07, step_name="A Hidden Threat reward")

def second_profession(bot: Botting):  
    bot.Map.Travel(target_map_id=449) #Kamadan
    bot.Wait.ForMapToChange(target_map_id=449)
    bot.Move.XYAndDialog(-7910, 9740, 0x828907, step_name="Honing Your Skills complete")
    bot.Dialogs.AtXY(-7910, 9740, 0x825901, step_name="Secondary Training")
    bot.Move.XYAndDialog(-7525, 6288, 0x81, step_name="Churrhir Fields")
    bot.Dialogs.AtXY(-7525, 6288, 0x84, step_name="We are ready")
    bot.Wait.ForMapToChange(target_map_id=456)
    bot.States.AddHeader("Churrhir Fields")
    ConfigurePacifistEnv(bot)
    bot.Items.Equip(ModelID.Bonus_Nevermore_Flatbow.value)
    #bot.Move.XYAndDialog(-9498, 1426, 0x7F, step_name="Ranger Skills")
    bot.Move.XYAndDialog(-11571, -3726, 0x7F, step_name="Ranger Skills 2")
    bot.Move.XY(-11031, -3326) #get pet
    bot.Target.Model(4242) #Flamingo
    bot.SkillBar.UseSkill(411) #Capture Pet
    bot.Wait.ForTime(22000)
    #bot.Move.XYAndDialog(-10549, -3350, 0x7F, step_name="Ranger Skills 3")
    bot.Move.XYAndDialog(-7161, 4808, 0x825907, step_name="Secondary Training complete")
    bot.Dialogs.AtXY(-7161, 4808, 0x89, step_name="Ranger 2nd Profession")
    bot.Dialogs.AtXY(-7161, 4808, 0x825407, step_name="Accept")
    bot.Dialogs.AtXY(-7161, 4808, 0x827801, step_name="Right Away")

def after_level_5(bot: Botting):    
    bot.States.AddHeader("15 Att Point")
    bot.Map.Travel(target_map_id=431) #Sunspear Great Hall
    bot.Wait.ForMapToChange(target_map_id=431)
    bot.Move.XYAndDialog(-2864, 7031, 0x82CB07, step_name="Accept Attribute Points")
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Dialogs.AtXY(-2864, 7031, 0x82CC03, step_name='Rising to 1st Spear')
    bot.Dialogs.AtXY(-2864, 7031, 0x82CC01, step_name="Sounds good to me")
    bot.States.AddHeader("Champions Dawn 2")
    bot.Map.Travel(target_map_id=479) #Champions Dawn
    bot.Wait.ForMapToChange(target_map_id=479)
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[6,7])
    bot.Move.XYAndDialog(22884, 7641, 0x827804, step_name="Leaving A Legacy")
    bot.Move.XYAndExitMap(22483, 6115, target_map_id=432) #Cliffs of Dohjok
    bot.Wait.ForMapToChange(target_map_id=432)
    bot.Move.XY(20215, 5285)
    bot.Move.XYAndDialog(20215, 5285, 0x85) #Blessing 
    bot.Wait.ForTime(2000)
    bot.Move.XYAndDialog(18008, 6024, 0x827804) #Dunkoro
    bot.Move.XY(13677, 6800)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7255, 5150)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-13255, 6535)
    bot.Dialogs.AtXY(-13255, 6535, 0x84, step_name="Let's Go!")
    bot.Move.XY(-11600, 5600)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-11572, 3116)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-11532, 583)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-10300, -4500)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-6864, -155)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-25149, 12787)
    bot.Move.XYAndExitMap(-27657, 14482, target_map_id=491) #Jokanur Diggings
    bot.Wait.ForMapToChange(target_map_id=491)
    bot.States.AddHeader("Jokanur Diggings")
    bot.Move.XYAndDialog(2888, 2207, 0x827807, step_name="Leaving A Legacy complete")
    bot.Dialogs.AtXY(2888, 2207, 0x827901, step_name="Sounds Like Fun")
    
def jokanur_diggings_quests(bot):
    bot.States.AddHeader("Jokanur Diggings 2")
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.Party.LeaveParty()
    bot.Party.AddHero(6) #Koss
    bot.Party.AddHero(7) #Dunkoro
    bot.States.AddCustomState(EquipHeroSkillBar, "OQgkQNVCoEGjQxvwVCAPuvp68iB")
    bot.Party.AddHenchman(6)

    # go get a pet here

#region MAIN
selected_step = 0
filter_header_steps = True

iconwidth = 96


def _draw_texture():
    global iconwidth
    level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())

    path = "SS Evos.png"
    size = (float(iconwidth), float(iconwidth))
    tint = (255, 255, 255, 255)
    border_col = (0, 0, 0, 0)  # <- ints, not normalized floats

    if level <= 3:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.0, 0.0),   uv1=(0.25, 1.0),
                                  tint=tint, border_color=border_col)
    elif level <= 5:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.25, 0.0), uv1=(0.5, 1.0),
                                  tint=tint, border_color=border_col)
    elif level <= 10:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.5, 0.0),  uv1=(0.75, 1.0),
                                  tint=tint, border_color=border_col)
    else:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.75, 0.0), uv1=(1.0, 1.0),
                                  tint=tint, border_color=border_col)


bot.SetMainRoutine(create_bot_routine)
bot.UI.override_draw_texture(_draw_texture)

def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
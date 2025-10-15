from typing import List, Tuple, Generator, Any
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, PyImGui)

#QUEST TO INCREASE SPAWNS https://wiki.guildwars.com/wiki/Lady_Mukei_Musagi
BOT_NAME = "PVE Skills Unlock Bot"


bot = Botting(BOT_NAME)

def EquipSkillBar(skillbar = ""): 
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())

    if profession == "Warrior":
            skillbar = "OQITYN8kzQxw23AAAAg2CAA"
    elif profession == "Ranger":
        skillbar = "OggjYZZIYMKG1pvBAAAAA0GBAA" #done
    elif profession == "Monk":
        skillbar = "OwISYxcGKG2o03AAA0WA"
    elif profession == "Necromancer":
        skillbar = "OgQCU8x0WocwnQZglAAAAAAA"
    elif profession == "Mesmer":
        skillbar = "OQJTYJckzQxw23AAAAg2CAA"
    elif profession == "Elementalist":
        skillbar = "OgJUwCLhjcGKG2+GAAAA0WAA"
    elif profession == "Ritualist":
        skillbar = "OAKkYRYRWCGjiB24b+mAAAAtRAA"
    elif profession == "Assassin":
        skillbar = "OwRCU8x0WocwnQZglAAAAAAA" #done
    elif profession == "Dervish":
        skillbar = "OgSCU8x0WocwnQZglAAAAAAA" #done
    elif profession == "Paragon":
        skillbar = "OQSjUwHM6QbhyBfClBWCAAAAAAA" #done

    yield from Routines.Yield.Skills.LoadSkillbar(skillbar)

def FinishHimSkillBar(skillbar = ""): 
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())

    if profession == "Warrior":
        skillbar = "OQITYN8kzQxw23AAAAg2CAA" #not done
    elif profession == "Ranger":
        skillbar = "OggjYNgsITVTXTfTlTnN+g0GOTA" #done
    elif profession == "Monk":
        skillbar = "OwISYxcGKG2o03AAA0WA" #not done
    elif profession == "Necromancer":
        skillbar = "OAhjYMgsITVTXTfTlTnN+gOT7iAAA" #done
    elif profession == "Mesmer":
        skillbar = "OQhjAMgsITVTXTlTnNfT+g7iOTA" #done
    elif profession == "Elementalist":
        skillbar = "OgJUwCLhjcGKG2+GAAAA0WAA" #not done
    elif profession == "Ritualist":
        skillbar = "OACjAqiK5SVTXTfTlTnN+gOTAAA" #done
    elif profession == "Assassin":
        skillbar = "OwhiAyiMVNdN9NVOd2sL6D6MBA" #done
    elif profession == "Dervish":
        skillbar = "OgiiAyiMVNdNVOd28N5DCA4MBA" #done

    yield from Routines.Yield.Skills.LoadSkillbar(skillbar)   

def PreCastSkills(bot: Botting) -> None:
    bot.SkillBar.UseSkill(1239); bot.Wait.ForTime(1000) # Signet of Spirits
    bot.SkillBar.UseSkill(1253); bot.Wait.ForTime(1250) # Blood Song
    bot.SkillBar.UseSkill(871); bot.Wait.ForTime(1250) # Shadow Song
    bot.SkillBar.UseSkill(1247); bot.Wait.ForTime(1250) # Pain
    bot.SkillBar.UseSkill(2110); bot.Wait.ForTime(1250) # Vampirism 

def withdraw_gold(target_gold=500, deposit_all=True):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    if gold_on_char > target_gold and deposit_all:
        to_deposit = gold_on_char - target_gold
        GLOBAL_CACHE.Inventory.DepositGold(to_deposit)
        yield from Routines.Yield.wait(250)

    if gold_on_char < target_gold:
        to_withdraw = target_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader("Unlock Skill #1") #[H] 1
    bot.UI.PrintMessageToConsole("Starting", "Beginning Dwarven Stability quest routine")
    
    # Travel to Sifhalla
    bot.Map.Travel(target_map_name="Sifhalla")
    bot.Wait.ForMapLoad(target_map_id=643)
    
    # Configure bot properties
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout", value=-1)
    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("essence_of_celerity")
    bot.Properties.Enable("grail_of_might")
    bot.Properties.Enable("armor_of_salvation")
    
    # Talk to Big Unfriendly Jotun and take quest
    bot.Move.XYAndDialog(12009, 24726, 0x837E03) # Big Unfriendly Jotun
    bot.Dialogs.AtXY(12009, 24726, 0x837E01) # take quest
    
    # Move to quest area
    bot.Move.XYAndExitMap(13583, 18781, target_map_id=513)
    bot.Wait.ForMapLoad(target_map_id=513)
    bot.Move.XY(15159, 12506)
    bot.Wait.UntilOutOfCombat()
    
    # Complete quest actions
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.ForMapToChange(target_map_id=643)
    
    # Collect reward
    bot.Move.XYAndDialog(12009, 24726, 0x837E07) # Big Unfriendly Jotun Reward
    bot.States.JumpToStepName("[H]End_8")
    
    bot.States.AddHeader("Unlock Skill #2") #[H] 2
    bot.UI.PrintMessageToConsole("Starting", "Beginning You move like a Dwarf quest routine")
    
    # Travel to Sifhalla
    bot.Map.Travel(target_map_name="Sifhalla")
    bot.Wait.ForMapLoad(target_map_id=643)
    
    # Configure bot properties
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout", value=-1)
    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("essence_of_celerity")
    bot.Properties.Enable("grail_of_might")
    bot.Properties.Enable("armor_of_salvation")

    # Talk to Worthy Deeds NPC and take quest
    bot.Move.XYAndDialog(14380, 23968, 0x833A01) # Worthy Deeds
    
    # Enter quest area
    bot.Move.XYAndExitMap(8832, 23870, target_map_id=513)
    bot.Wait.ForMapLoad(target_map_id=513)
    
    # Navigate through quest area
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.Multibox.UseConsumable(28431, 0) #Apple
    bot.Multibox.UseConsumable(28432, 0) #Candy
    bot.Multibox.UseConsumable(22752, 0) #Egg
    bot.Multibox.UseConsumable(28436, 0) #Pies
    bot.Multibox.UseConsumable(35121, 0) #WarSupplies
    
    bot.Move.XY(11434, 19708)
    bot.Move.XY(14164, 2682)
    bot.Move.XY(9435, -5806) # if you got here and no boss restart
    bot.Wait.UntilOutOfCombat()
    
    # Fight Myish, Lady of the Lake
    bot.Move.XY(1914, -6963) # Myish, Lady of the Lake
    bot.Wait.UntilOutOfCombat()
    
    # Continue quest path
    bot.Move.XY(4735, -14202)
    bot.Move.XY(5752, -15236)
    bot.Move.XY(8924, -15922)
    bot.Move.XY(14134, -16744)
    
    # Rabbit hole section
    bot.Move.XY(12581, -19343) # Rabbit hole start
    bot.Move.XY(12702, -23855) # around the bend
    bot.Move.XY(13952, -23063) # Nulfastu, Earthbound
    bot.Wait.ForTime(45000) # 45 seconds max to kill this guy and back to town after
    
    # Complete quest
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.ForMapLoad(target_map_id=643)
    
    # Collect reward
    bot.Move.XYAndDialog(14380, 23968, 0x833A07) # Rewards
    bot.States.JumpToStepName("[H]End_8")

    # Begin Quest #3
    bot.States.AddHeader("Unlock Skill #3")  # [H] 3

    bot.UI.PrintMessageToConsole("Starting", "Beginning Anything you can do quest routine")
    
    # Travel to Sifhalla
    bot.Map.Travel(target_map_name="Sifhalla")
    bot.Wait.ForMapLoad(target_map_id=643)
    
    # Configure bot properties
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout", value=-1)
    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("essence_of_celerity")

    # Start "Anything you can do" quest
    bot.Move.XYAndDialog(14380, 23874, 0x833E01) # Anything you can do
    bot.Move.XY(14682, 22900)
    bot.Move.XYAndExitMap(17000, 22872, target_map_id=546)
    bot.Wait.ForMapLoad(target_map_id=546)
    
    # Navigate to first boss area
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.Multibox.UseConsumable(28431, 0) #Apple
    bot.Multibox.UseConsumable(28432, 0) #Candy
    bot.Multibox.UseConsumable(22752, 0) #Egg
    bot.Multibox.UseConsumable(28436, 0) #Pies
    bot.Multibox.UseConsumable(35121, 0) #WarSupplies
    bot.Move.XY(-9431, -20124)
    bot.Move.XY(-8441, -13685)
    bot.Move.XY(-9743, -6744)
    bot.Move.XY(-10672, 4815) # wall hugging
    bot.Move.XY(-8464, 17239) # up to Avarr the Fallen
    bot.Move.XY(-11700, 24101)
    bot.Wait.UntilOutOfCombat()
    
    # Fight Whiteout
    bot.Move.XY(-8464, 17239) # back down the hill
    bot.Move.XY(-638, 17801) # up to Whiteout look out for boulder
    bot.Move.XY(-933, 15368) # run away from boulder
    bot.Wait.ForTime(6000)
    bot.Move.XY(-1339, 22089) # Kill Whiteout
    bot.Wait.ForTime(5000) # extra time here incase of party wipe
    bot.Multibox.ResignParty()
    bot.Wait.ForMapLoad(target_map_id=643)
    
    # Fragment of Antiquities section
    bot.States.AddHeader("Fragment of Antiquities") #[H] 4
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout", value=-1)
    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("essence_of_celerity")
    
    bot.Move.XYAndExitMap(8832, 23870, target_map_id=513)
    bot.Wait.ForMapLoad(target_map_id=513)
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.Move.XYAndDialog(-10926, 24732, 0x832901) # Fragment of Antiquities
    bot.Move.XYAndExitMap(-12138, 26829, target_map_id=628)
    bot.Wait.ForMapLoad(target_map_id=628)
    
    # Navigate to Fragment boss
    bot.Multibox.UsePConSet() #Conset
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.Multibox.UseConsumable(28431, 0) #Apple
    bot.Multibox.UseConsumable(28432, 0) #Candy
    bot.Multibox.UseConsumable(22752, 0) #Egg
    bot.Multibox.UseConsumable(28436, 0) #Pies
    bot.Multibox.UseConsumable(35121, 0) #WarSupplies
    bot.Move.XY(-5343, -15773) # proof of strength
    bot.Move.XY(-6614.39, -11600.95)
    bot.Move.XY(-5386.19, -8941.30)
    bot.Move.XY(-8244.77, -7445.38)
    bot.Move.XY(-11958.68, -2933.47)
    bot.Move.XY(-12740.31, 1040.36) # Defeat the Fragment of Antiquities
    bot.Wait.ForTime(5000) # extra time here incase of party wipe
    bot.Multibox.ResignParty()
    #bot.Wait.ForTime(3000)
    bot.Wait.ForMapLoad(target_map_id=643)
    
    # Collect reward
    bot.Move.XYAndDialog(14380, 23968, 0x833E07) # Rewards
    bot.States.JumpToStepName("[H]End_8")
    
    bot.States.AddHeader("Unlock Skill #4")
    bot.UI.PrintMessageToConsole("Starting", "Beginning I am Unstoppable quest routine")
    
    # Travel to Sifhalla
    bot.Map.Travel(target_map_name="Sifhalla")
    bot.Wait.ForMapLoad(target_map_id=643)
    
    # Configure bot properties
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout", value=-1)
    bot.Properties.Enable("auto_combat")
    
    # Equip bonus items and skill bar before starting the quest
    bot.Items.SpawnBonusItems()
    bot.Items.Equip(6515) # Necro Bonus Staff
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    
    # Start Cold As Ice quest
    bot.Move.XYAndDialog(14380, 23968, 0x834401) # Cold As Ice
    bot.Dialogs.AtXY(14380, 23968, 0x85) # I am Ready
    bot.Wait.ForMapLoad(target_map_id=690) # Special Sifhalla Map
    bot.Wait.ForTime(5000)
    
    # Fight sequence
    bot.Move.XY(14553, 23043)
    bot.Wait.ForTime(2000)
    bot.SkillBar.UseSkill(114)
    bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForMapToChange(target_map_id=643)
    
    # Collect reward
    bot.Move.XYAndDialog(14380, 23968, 0x834407) # Rewards
    bot.States.JumpToStepName("[H]End_8")
    
    bot.States.AddHeader("Unlock Skill #5")
    bot.UI.PrintMessageToConsole("Starting", "Beginning Smooth Criminal quest routine")
    
    # Travel to Boreal Station
    bot.Map.Travel(target_map_id=641)
    bot.Wait.ForMapLoad(target_map_id=641)
    
    # Configure bot properties
    bot.Properties.ApplyNow("pause_on_danger", "active", True)
    bot.Properties.ApplyNow("halt_on_death", "active", True)
    bot.Properties.ApplyNow("movement_timeout", "value", 15000)
    bot.Properties.ApplyNow("auto_combat", "active", True)
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.Multibox.UseConsumable(28431, 0) #Apple
    bot.Multibox.UseConsumable(28432, 0) #Candy
    bot.Multibox.UseConsumable(22752, 0) #Egg
    bot.Multibox.UseConsumable(28436, 0) #Pies
    bot.Multibox.UseConsumable(35121, 0) #WarSupplies
    
    # Start Melandru quest
    bot.Move.XYAndDialog(25203, -10694, 0x837C01) # Melandru
    bot.Move.XY(18781, -10477)
    bot.Wait.ForMapLoad(target_map_name="Alcazia Tangle")
    
    # Navigate to hunting spots
    bot.Move.XY(17024, -600)
    bot.Move.XY(18237, 6691) # res shrine 1
    bot.Move.XY(15518, 8375)
    bot.Move.XY(13200, 15000) # Spot 1 confirmed
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOutOfCombat() # move on to spot 2
    
    # Move to second area
    bot.Move.XY(19516, 4686) # rez shrine 2 cliff
    bot.Move.XY(12184, 370) # midway
    bot.Move.XY(4802, -4990) # Rez Shrine 3
    bot.Move.XY(-8760, -3378) # Rez Shrine 4
    bot.Move.XY(-5555, -2108)
    bot.Move.XY(-6678, 6477) # Spot 3 Confirmed
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOutOfCombat() # move on to spot 3
    
    # Final hunting spot
    bot.Move.XY(-8860, -3178) # Rez Shrine 4 again
    bot.Move.XY(-11202, 758) # Spot 3 Confirmed
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOutOfCombat()
    
    # Complete quest
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.ForMapLoad(target_map_id=641)
    
    # Collect reward
    bot.Move.XYAndDialog(25203, -10694, 0x837C07) # Rewards
    bot.States.JumpToStepName("[H]End_8")
    
    bot.States.AddHeader("Unlock Skill #6")
    bot.UI.PrintMessageToConsole("Starting", "Beginning Mental Block quest routine")
    
    # Travel to Boreal Station
    bot.Map.Travel(target_map_id=641)
    bot.Wait.ForMapLoad(target_map_id=641)
    
    # Configure bot properties
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout", value=-1)
    bot.Properties.Enable("auto_combat")
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.Multibox.UseConsumable(28431, 0) #Apple
    bot.Multibox.UseConsumable(28432, 0) #Candy
    bot.Multibox.UseConsumable(22752, 0) #Egg
    bot.Multibox.UseConsumable(28436, 0) #Pies
    bot.Multibox.UseConsumable(35121, 0) #WarSupplies
    
    # Start Balthazar quest
    bot.Move.XYAndDialog(25203, -10694, 0x837701) # Balthazar
    
    # Travel to quest area
    bot.Map.Travel(target_map_id=639)
    bot.Wait.ForMapLoad(target_map_id=639)
    bot.Move.XY(-22999, 6530)
    bot.Wait.ForMapLoad(target_map_id=566)
    
    # Navigate through hunting spots
    bot.Move.XY(-9761, -8000) # spot 1
    bot.Move.XY(7833, -8293) # spot 2
    bot.Move.XY(11690, -6215) # spot 3
    bot.Move.XY(15918, -2667) # spot 4
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOutOfCombat()
    
    # Complete quest
    bot.Multibox.ResignParty()
    bot.Wait.ForMapLoad(target_map_id=639)
    bot.Map.Travel(target_map_id=641)
    bot.Wait.ForMapLoad(target_map_id=641)
    
    # Collect reward
    bot.Move.XYAndDialog(25203, -10694, 0x837707) # Rewards
    bot.States.JumpToStepName("[H]End_8")

    bot.States.AddHeader("Unlock Skill #7")
    bot.UI.PrintMessageToConsole("Starting", "Beginning Ebon battle standard of honor skill unlock quest routine")
    
    # Travel to Longeye's Ledge
    bot.Map.Travel(target_map_id=650)
    # Configure bot properties
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout", value=-1)
    bot.Properties.Enable("auto_combat")
    #bot.Wait.ForMapLoad(target_map_id=639)
    bot.Move.XY(-21902, 12807)
    bot.Wait.ForMapLoad(target_map_id=649)
    bot.Move.XYAndDialog(-21141.81, 12378.68, 0x836001) # Battle Honor Stand
    bot.Multibox.UsePConSet() #Conset
    # Navigate through hunting spots - Map 649
    bot.Move.XY(-21593, 12517)
    bot.Move.XY(-20064, 11212)
    bot.Move.XY(-18659, 9768)
    bot.Move.XY(-17352, 8246)
    bot.Move.XY(-16126, 6640)
    bot.Move.XY(-14663, 5256)
    bot.Move.XY(-13347, 3732)
    bot.Move.XY(-11993, 2247)
    bot.Move.XY(-11088, 402)
    bot.Move.XY(-9414, -699)
    bot.Move.XY(-7532, 132)
    bot.Move.XY(-5576, -322)
    bot.Move.XY(-3621, -814)
    bot.Move.XY(-1677, -1304)
    bot.Move.XY(177, -2140)
    bot.Move.XY(1759, -3373)
    bot.Move.XY(3730, -3747)
    bot.Move.XY(5650, -4349)
    bot.Move.XY(7421, -5292)
    bot.Move.XY(8547, -6957)
    bot.Move.XY(10587, -6733)
    bot.Move.XY(12591, -6583)
    bot.Move.XY(14521, -7151)
    bot.Move.XY(16095, -8448)
    bot.Move.XY(17681, -9721)
    bot.Move.XY(19282, -11005)
    bot.Move.XY(20765, -12412)
    bot.Move.XY(22538, -13411)
    bot.Move.XY(23410, -13901)
    # Navigate through hunting spots - Map 651
    bot.Wait.ForMapLoad(target_map_id=651)
    bot.Multibox.UseAllConsumables()
    bot.Move.XY(-17861, 16317)
    bot.Move.XY(-16404, 14900)
    bot.Move.XY(-16459, 12851)
    bot.Move.XY(-17542, 11132)
    bot.Move.XY(-17939, 9166)
    bot.Move.XY(-16308, 7932)
    bot.Move.XY(-15150, 6294)
    bot.Move.XY(-14010, 4577)
    bot.Move.XY(-13622, 2552)
    bot.Move.XY(-13094, 598)
    bot.Move.XY(-11367, -490)
    bot.Move.XY(-9393, -831)
    bot.Move.XY(-7616, -1762)
    bot.Move.XY(-5677, -2456)
    bot.Move.XY(-4372, -4015)
    bot.Move.XY(-3143, -5620)
    bot.Move.XY(-2954, -7657)
    bot.Move.XY(-2423, -9586)
    bot.Move.XY(-593, -10426)
    bot.Move.XY(1413, -10033)
    bot.Move.XY(3432, -9958)
    bot.Move.XY(4945, -8637)
    bot.Move.XY(6962, -8362)
    bot.Move.XY(8991, -8392)
    bot.Move.XY(4471, -7294)
    bot.Move.XY(6525, -7403)
    bot.Move.XY(8415, -8062)
    bot.Move.XY(10082, -9228)
    bot.Move.XY(11715, -8045)
    bot.Wait.UntilOutOfCombat()
    
    # Collect reward
    bot.Map.Travel(target_map_id=650)
    bot.Move.XY(-21902, 12807)
    bot.Wait.ForMapLoad(target_map_id=649)
    bot.Move.XYAndDialog(-21141.81, 12378.68, 0x836007) # Rewards
    bot.States.JumpToStepName("[H]End_8")

    bot.States.AddHeader("Unlock Skill #8")
    bot.Map.Travel(target_map_id=642)
    bot.Move.XYAndDialog(-1904.21, 3112.10, 0x835601)
    bot.Map.Travel(target_map_id=644)
    bot.Move.XY(14758, -6425)
    bot.Wait.ForMapLoad(target_map_id=548)

    bot.Move.XY(12655, 409)
    bot.Wait.ForTime(60000)
    bot.Move.XY(11921, -2798)
    bot.Move.XY(12102.08, -1703.92)
    bot.Move.XY(11225.68, -7690.49)
    bot.Wait.UntilOutOfCombat()
    bot.Map.Travel(target_map_id=642)
    bot.Move.XYAndDialog(-1904.21, 3112.10, 0x835607)

    bot.States.AddHeader("Unlock Skill #9")
    bot.UI.PrintMessageToConsole("Starting", "Beginning Vanguard Ebon Sin quest routine")
    
    # Travel to Eotn Outpost
    bot.Map.Travel(target_map_id=642)
    bot.Move.XYAndDialog(-1904.21, 3112.10, 0x836A01)
    bot.Move.XYAndDialog(-1904.21, 3112.10, 0x86)
    bot.Wait.ForMapLoad(target_map_id=697) # Special Eotn Map
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Map.Travel(target_map_id=642)
    #bot.Wait.ForMapToChange(target_map_id=642)  
    # Collect reward
    bot.Move.XYAndDialog(-1904.21, 3112.10, 0x836A07) # Rewards
    bot.States.JumpToStepName("[H]End_8")

    
    bot.States.AddHeader("Unlock Skill #10")
    bot.UI.PrintMessageToConsole("Starting", "Beginning Finish Him quest routine")
    
    # Travel to Sifhalla
    bot.Map.Travel(target_map_name="Gunnar's Hold")
    
    # Configure bot properties
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout", value=-1)
    bot.Properties.Enable("auto_combat")
    
    # Equip bonus items and skill bar before starting the quest
    #bot.Items.SpawnBonusItems()
    #bot.Items.Equip(6515) # Necro Bonus Staff
    bot.States.AddCustomState(FinishHimSkillBar, "Equip Skill Bar")
    bot.States.AddCustomState(withdraw_gold, "Get 500 gold")
    
    # Start Finish Him quest
    bot.Move.XY(17266.78, -8667.82)
    bot.Move.XY(16609.11, -10126.19)
    bot.Move.XY(17680, -11493) #just for testing since I am not running around
    bot.Move.XYAndDialog(17680.50, -11493.22, 0x834A01) # Finish Him
    bot.Move.XYAndDialog(17884.19, -11921.57, 0x84)
    bot.Wait.ForMapLoad(target_map_id=700)
    
        # Fight sequence 1
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.Wait.ForTime(10000) #
    bot.SkillBar.UseSkill(1230); bot.Wait.ForTime(2000) #Boon of Creation 2sec cast
    bot.Move.XY(18806, -11057)
    PreCastSkills(bot)
    #bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(5000)
    bot.Wait.ForMapLoad(target_map_id=700)
        # Fight sequence 2
    bot.Wait.ForTime(10000) #
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.SkillBar.UseSkill(1230); bot.Wait.ForTime(2000) #Boon of Creation 2sec cast
    bot.Move.XY(18806, -11057)
    PreCastSkills(bot)
    #bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(5000)
    bot.Wait.ForMapLoad(target_map_id=700)
        # Fight sequence 3
    bot.Wait.ForTime(10000) #
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.SkillBar.UseSkill(1230); bot.Wait.ForTime(2000) #Boon of Creation 2sec cast
    bot.Move.XY(18806, -11057)
    PreCastSkills(bot)
    #bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(5000)
    bot.Wait.ForMapLoad(target_map_id=700)
        # Fight sequence 4
    bot.Wait.ForTime(10000) #
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.SkillBar.UseSkill(1230); bot.Wait.ForTime(2000) #Boon of Creation 2sec cast
    bot.Move.XY(18806, -11057)
    PreCastSkills(bot)
    #bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(5000)
    bot.Wait.ForMapLoad(target_map_id=700)
        # Fight sequence 5
    bot.Wait.ForTime(10000) #
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.SkillBar.UseSkill(1230); bot.Wait.ForTime(2000) #Boon of Creation 2sec cast
    bot.Move.XY(18806, -11057)
    PreCastSkills(bot)
    #bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(5000)
    bot.Wait.ForMapLoad(target_map_id=700)
        # Final Round
    bot.Wait.ForTime(8000) # -2sec to cast Boon of Creation
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.SkillBar.UseSkill(1230); bot.Wait.ForTime(2000) #Boon of Creation 2sec cast
    bot.Move.XY(18806, -11057)
    PreCastSkills(bot)
    bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForMapToChange(target_map_id=644)

    # Collect reward
    bot.Move.XYAndDialog(17683.13, -11468.46, 0x834F07) # Rewards
    bot.States.JumpToStepName("[H]End_8")
    
    bot.States.AddHeader("End") #H 8
    bot.UI.PrintMessageToConsole("End", "This is the end of the bot routine")



bot.SetMainRoutine(bot_routine)

def Draw_Window():
    if PyImGui.begin("PVE skills unlock by Wick Divinus and Kendor", True, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text("PVE Skills Unlock Bot with Multiple Quest Options")
        PyImGui.separator()
        
        if PyImGui.button("Start Dwarven Stability Quest (Skill #1)"):
            bot.StartAtStep("[H]Unlock Skill #1_1")

        if PyImGui.button("Start You move like a Dwarf Quest (Skill #2)"):
            bot.StartAtStep("[H]Unlock Skill #2_2")

        if PyImGui.button("Start Anything you can do Quest Pt1 (Skill #3)"):
            bot.StartAtStep("[H]Unlock Skill #3_3")
        
        if PyImGui.button("Start Anything you can do Quest Pt2 (Skill #3)"):
            bot.StartAtStep("[H]Fragment of Antiquities_4")

        if PyImGui.button("Start I am Unstoppable Quest (Skill #4)"):
            bot.StartAtStep("[H]Unlock Skill #4_5")

        if PyImGui.button("Start Smooth Criminal Quest (Skill #5)"):
            bot.StartAtStep("[H]Unlock Skill #5_6")

        if PyImGui.button("Start Mental Block Quest (Skill #6)"):
            bot.StartAtStep("[H]Unlock Skill #6_7")

        if PyImGui.button("Start Ebon battle standard of honor Quest (Skill #7)"):
            bot.StartAtStep("[H]Unlock Skill #7_8")

        if PyImGui.button("Start Unlock Wind Skill #8"):
            bot.StartAtStep("[H]Unlock Skill #8_9")

        if PyImGui.button("Start Vanguard Ebon Sin Quest (Skill #9)"):
            bot.StartAtStep("[H]Unlock Skill #9_10")

        if PyImGui.button("Start Finish Him Quest (Skill #10)"):
            bot.StartAtStep("[H]Unlock Skill #10_11")

        PyImGui.end()

def main():
    bot.Update()
    Draw_Window()
    #you can still use the bots window or not, 
    #you can use it to see step names or debug messages
    #you can hide it if you want
    # bot.UI.draw_window()


if __name__ == "__main__":
    main()

from Py4GWCoreLib import *

bot = Botting("Eotn storyline bot")
#region Helpers
def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.Templates.Pacifist()
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Disable("honeycomb")
    bot.Properties.Disable("war_supplies")
    bot.Items.Restock.BirthdayCupcake()
    bot.Items.Restock.WarSupplies()
    bot.Items.Restock.Honeycomb()

def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Templates.Aggressive()
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Enable("honeycomb")
    bot.Properties.Enable("war_supplies")
    bot.Items.Restock.BirthdayCupcake()
    bot.Items.Restock.WarSupplies()
    bot.Items.Restock.Honeycomb()
#region Start
def Routine(bot: Botting) -> None:
    # === PHASE 1: INITIAL SETUP AND RESURRECTION POOL ===
    UnlockEyeOfTheNorthPool(bot)
    ObtainStoryBook(bot)              # Unlock EOTN resurrection pool
    TravelToGunnarsHold(bot)                   # Travel to Gunnar's Hold
    
    # === PHASE 2: INITIAL NORN QUESTS ===
    TalkToGunnar(bot)                          # Talk to Gunnar
    TravelToSifhalla(bot)                      # Travel to Sifhalla
    CompleteTrackingTheNornbear(bot)           # Complete tracking quest
    CompleteCurseOfTheNornbear(bot)            # Complete curse quest
    
    # === PHASE 3: OLAFSTEAD MISSIONS ===
    TravelToOlafstead(bot)                     # Travel to Olafstead
    CompleteShrineOfRavenSpirit(bot)           # Complete shrine quest
    CompleteAGateTooFar(bot)                   # Complete gate mission
    
    # === PHASE 4: VANGUARD MISSIONS ===
    AdvanceToLongeyeEdge(bot)                  # Advance to Longeye's Edge
    SearchForTheEbonVanguard(bot)
    WarbandOfBrothers(bot)                      # Complete Ebon Vanguard mission
    WhatMustBeDone(bot)
    AssaultOnTheStrongHold(bot)
    
    # === PHASE 5: ASURAN MISSIONS ===
    FindingGadd(bot)
    FindingTheBloodstone(bot)
    GOLEM(bot)
    


def UnlockEyeOfTheNorthPool(bot) -> None:
    bot.States.AddHeader("Unlocking Eye of the North Resurrection Pool")
    bot.Map.Travel(target_map_id=642)  # eotn_outpost_id
    auto_path_list = [(-4416.39, 4932.36), (-5198.00, 5595.00)]
    bot.Move.FollowAutoPath(auto_path_list)
    bot.Wait.ForMapLoad(target_map_id=646)  # hall of monuments id
    bot.Move.XY(-6572.70, 6588.83)
    bot.Dialogs.WithModel(5970, 0x800001) #eotn_pool_cinematic
    bot.Wait.ForTime(1000)
    bot.Dialogs.WithModel(5908, 0x630) #eotn_pool_cinematic
    bot.Wait.ForTime(1000)
    bot.Dialogs.WithModel(5908, 0x632) #eotn_pool_cinematic
    bot.Wait.ForTime(1000)
    bot.Wait.ForMapToChange(target_map_id=646)  # hall of monuments id
    bot.Dialogs.WithModel(5970, 0x89) #gwen dialog
    bot.Dialogs.WithModel(5970, 0x831904) #gwen dialog
    bot.Move.XYAndDialog(-6133.41, 5717.30, 0x838904) #ogden dialog
    bot.Move.XYAndDialog(-5626.80, 6259.57, 0x839304) #vekk dialog

def ObtainStoryBook(bot) -> None:
    bot.States.AddHeader("Obtain Story Book")
    bot.Move.XY(-1998.00, 2797.00)
    bot.Dialogs.AtXY(-1998.00, 2797.00, 0x1006913) #Obtain Story Book

def TravelToGunnarsHold(bot) -> None:
    bot.States.AddHeader("Run to Gunnar's Hold")
    bot.Map.Travel(target_map_id=642) # eotn_outpost_id
    
    # Follow outpost exit path
    path = [(-1814.0, 2917.0), (-964.0, 2270.0), (-115.0, 1677.0), (718.0, 1060.0),  (1522.0, 464.0)]
    bot.Move.FollowPath(path)
    bot.Wait.ForMapLoad(target_map_id=499)  # Ice Cliff Chasms
    
    # Traverse through Ice Cliff Chasms
    bot.Move.XYAndDialog(2825, -481, 0x832801)  # Talk to Jora
    path = [(2548.84, 7266.08), (1233.76, 13803.42), (978.88, 21837.26), (-4031.0, 27872.0),]
    bot.Move.FollowAutoPath(path)
    bot.Wait.ForMapLoad(target_map_id=548)  # Norrhart Domains
 
    # Traverse through Norrhart Domains
    bot.Move.XY(14546.0, -6043.0)
    bot.Move.XYAndExitMap(15578, -6548, target_map_id=644)  # Gunnar's Hold
    bot.Wait.ForMapLoad(target_map_id=644)  # Gunnar's Hold

def TalkToGunnar(bot) -> None:
    bot.States.AddHeader("Talk to Gunnar")
    bot.Map.Travel(target_map_name="Gunnar's Hold")
    bot.Move.XYAndDialog(24078, -7512, 0x832804) #Tracking the Nornbear

def TravelToSifhalla(bot) -> None:
    bot.States.AddHeader("Run To Sifhalla")
    bot.Map.Travel(target_map_id=644) # Gunnar's Hold
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(16003.853515, -6544.087402)
    bot.Move.XY(15193.037109, -6387.140625)
    bot.Wait.ForMapLoad(target_map_name="Norrhart Domains")
    
    # Traverse through Norrhart Domains to Drakkar Lake
    bot.Move.XY(13337.167968, -3869.252929)
    bot.Move.XY( 9826.771484,   416.337768)
    bot.Move.XY( 6321.207031,  2398.933349)
    bot.Move.XY( 2982.609619,  2118.243164)
    bot.Move.XY(  176.124359,  2252.913574)
    bot.Move.XY( -3766.605468,  3390.211669)
    bot.Move.XY( -7325.385253,  2669.518066)
    bot.Move.XY( -9555.996093,  5570.137695)
    bot.Move.XY(-14153.492187,  5198.475585)
    bot.Move.XY(-18538.169921,  7079.861816)
    bot.Move.XY(-22717.630859,  8757.812500)
    bot.Move.XY(-25531.134765, 10925.241210)
    bot.Move.XY(-26333.171875, 11242.023437)
    bot.Wait.ForMapLoad(target_map_name="Drakkar Lake")
    
    # Traverse through Drakkar Lake to Sifhalla
    bot.Move.XY(14399.201171, -16963.455078)
    bot.Move.XY(12510.431640, -13414.477539)
    bot.Move.XY(12011.655273,  -9633.283203)
    bot.Move.XY(11484.183593,  -5569.488769)
    bot.Move.XY(12456.843750,  -0411.864135)
    bot.Move.XY(13398.728515,   4328.439453)
    bot.Move.XY(14000.825195,   8676.782226)
    bot.Move.XY(14210.789062,  12432.768554)
    bot.Move.XY(13846.647460,  15850.121093)
    bot.Move.XY(13595.982421,  18950.578125)
    bot.Move.XY(13567.612304,  19432.314453)
    bot.Wait.ForMapLoad(target_map_name="Sifhalla")

def CompleteTrackingTheNornbear(bot) -> None:
    bot.States.AddHeader("Tracking the Nornbear")
    bot.Map.Travel(target_map_name="Sifhalla") #Sifhalla
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(14353, 23905, 0x84) #Tracking the Nornbear
    bot.Wait.ForMapLoad(target_map_id=678); bot.Wait.ForTime(2000) #Special Sifhalla Instance
    bot.Move.XY(10388, 23888); bot.Wait.ForTime(8500); bot.Wait.UntilOnCombat #Fight the bear
    bot.Wait.ForTime(40000)
    bot.Wait.ForMapLoad(target_map_name="Sifhalla") #Wait to be ported back to Sifhalla
    bot.Move.XYAndDialog(14353, 23905, 0x832807)

def CompleteCurseOfTheNornbear(bot) -> None:
    bot.States.AddHeader("Curse of the Nornbear")
    bot.Map.Travel(target_map_name="Sifhalla")
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(14353, 23905, 0x86) #hunting the nornbear
    bot.Wait.ForMapLoad(target_map_id=653); bot.Wait.ForTime(2000)#Special Instance Map of Drakkar Lake
    bot.Multibox.UseAllConsumables() #Conset
    bot.Move.XY(-2638, 20433); bot.Wait.ForTime(5000)
    bot.Move.XY(-5793, 15818); bot.Wait.ForTime(2000)
    bot.Move.XY(8105, 14089); bot.Wait.ForTime(2000)
    bot.Move.XY(4940, 6551); bot.Wait.UntilOnCombat; bot.Wait.ForTime(5000)
    bot.Wait.ForMapToChange(target_map_id=643); bot.Wait.ForTime(2000)
    bot.Move.XYAndDialog(14353, 23905, 0x838904) #Northern Allies
    bot.Dialogs.AtXY(14353, 23905, 0x89) #Olaf Olafson
    bot.Dialogs.AtXY(14353, 23905, 0x8A) #Egil Fireteller

def TravelToOlafstead(bot) -> None:
    bot.States.AddHeader("Run to Olafstead")
    bot.Map.Travel(target_map_name="Sifhalla") #Sifhalla
    ConfigureAggressiveEnv(bot)	
    bot.Move.XY(16163, 22852)
    bot.Move.XY(16717, 22789)
    bot.Wait.ForMapLoad(target_map_name="Jaga Moraine") #Jaga Moraine
    auto_path_list = [(-11949.0, -23710,),  (-8929, -21112),(-6111, -14675), (-5757, -13735), (-4855, -10881), (-3702, -8096), (-2962, -7412), (-1397, -6161), (1055, -3190), (2170, -397), (2659, 484), (3151, 1355), (3726, 4064), (4229, 4944)]
    bot.Move.FollowAutoPath(auto_path_list) #path to Olafstead
    bot.Wait.ForMapLoad(target_map_name="Olafstead") #Olafstead

def CompleteShrineOfRavenSpirit(bot) -> None:
    bot.States.AddHeader("Shrine of the Raven Spirit")
    bot.Map.Travel(target_map_name="Olafstead") #Olafstead
    bot.Move.FollowAutoPath([(132, -684)]) #Talk to Olaf Olafson
    bot.Dialogs.AtXY(132, -684, 0x832E01) #Talk to Olaf Olafson
    ConfigureAggressiveEnv(bot)
    bot.Move.FollowPath([(-1440, 1147.5)])
    bot.Wait.ForMapLoad(target_map_id=553) #Varajar Fells
    bot.Multibox.UseAllConsumables()
    auto_path_list = [(-2252.0, 831), (-2887, -2894), (-3211, -3843), (-3940, -3155),(-4941, 728), (-5310, 3693),  (-8984, 4861), (-12866, 5695), (-13612, 6369), (-14355, 7040), (-14909, 7880), (-15520, 8680)] 
    bot.Move.XYAndDialog(-15696, 8732, 0x85) #I'm Always Ready to Talk
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(50500) #wait for destroyers
    bot.Wait.UntilOutOfCombat()
    bot.Dialogs.WithModel(6352, 0x832E07)

def CompleteAGateTooFar(bot) -> None:
    bot.States.AddHeader("A Gate Too Far")
    bot.Map.Travel(target_map_name="Olafstead") #Olafstead
    ConfigureAggressiveEnv(bot)
    bot.Move.FollowPath([(132, -684)])
    bot.Dialogs.AtXY(132, -684, 0x81) #Let me at them!
    bot.Dialogs.AtXY(132, -684, 0x86) #Let me at them!
    bot.Wait.ForMapLoad(target_map_id=655)
    bot.Wait.ForTime(2000) #Special Instance Map for a Gate too far Level 1
    bot.Multibox.UseAllConsumables()
    bot.Move.XY(-6814, -2984)
    bot.Move.XY(-3947, -226)
    bot.Move.XY(-6545, 6730); bot.Wait.UntilOutOfCombat
    bot.Move.XY(-7653, 5072); bot.Wait.UntilOutOfCombat
    bot.Move.XY(-6282, 6545) #don't even waste time with the spirits
    bot.Move.XY(-6334, -1712); bot.Wait.UntilOutOfCombat #tremor 1
    bot.Move.XY(-8244, 576); bot.Wait.UntilOutOfCombat #tremor 2
    bot.Move.XY(-10132, 807); bot.Wait.UntilOutOfCombat #tremor 3
    bot.Move.XY(-13368, 1995); bot.Wait.UntilOutOfCombat #tremor 4
    bot.Move.XY(-14761, 3282); bot.Wait.UntilOutOfCombat #tremor 5
    bot.Move.XY(-15036, 5711); bot.Wait.UntilOutOfCombat #tremor 6
    bot.Move.XY(-15976, 7767); bot.Wait.UntilOutOfCombat #tremor 7
    bot.Move.XY(-18697, 9416); bot.Wait.UntilOutOfCombat #tremor 8
    bot.Move.XY(-20211, 9897)
    bot.Wait.ForMapLoad(target_map_id=656); bot.Wait.ForTime(2000) #Special Instance Map for a Gate too far Level 2
    bot.Multibox.UseAllConsumables() 
    bot.Move.XY(17054, 6568); bot.Wait.UntilOutOfCombat
    bot.Move.XY(13357, 11594); bot.Wait.UntilOutOfCombat
    bot.Move.XY(11271, 17040); bot.Wait.UntilOutOfCombat
    bot.Move.XY(5244, 17207); bot.Wait.UntilOutOfCombat
    bot.Move.XY(3249, 17858)
    bot.Wait.ForMapLoad(target_map_id=657); bot.Wait.ForTime(2000) #Special Instance Map for a Gate too far Level 3
    bot.Multibox.UseAllConsumables() 
    bot.Move.XY(6360, 16486); bot.Wait.UntilOutOfCombat
    bot.Move.XY(5233, 12570); bot.Wait.UntilOutOfCombat
    bot.Move.XY(6210, 10139)
    bot.Move.XY(6716, 6344); bot.Wait.UntilOutOfCombat
    bot.Move.XY(7702, 4015); bot.Wait.UntilOutOfCombat
    bot.Move.XY(7510, 2854); bot.Wait.UntilOutOfCombat
    bot.Wait.ForMapLoad(target_map_id=645); bot.Wait.ForTime(2000) #Olafstead

def AdvanceToLongeyeEdge(bot):
    bot.States.AddHeader("Advancing to Longeye's Edge")
    bot.Map.Travel(target_map_id=644) # Gunnar's Hold
    
    # Exit Gunnar's Hold outpost
    bot.Move.XY(15886.204101, -6687.815917)
    bot.Move.XY(15183.199218, -6381.958984)
    bot.Wait.ForMapLoad(target_map_id=548)  # Norrhart Domains
    
    # Traverse through Norrhart Domains to Bjora Marches
    bot.Move.XY(14233.820312, -3638.702636)
    bot.Move.XY(14944.690429,  1197.740966)
    bot.Move.XY(14855.548828,  4450.144531)
    bot.Move.XY(17964.738281,  6782.413574)
    bot.Move.XY(19127.484375,  9809.458984)
    bot.Move.XY(21742.705078, 14057.231445)
    bot.Move.XY(19933.869140, 15609.059570)
    bot.Move.XY(16294.676757, 16369.736328)
    bot.Move.XY(16392.476562, 16768.855468)
    bot.Wait.ForMapLoad(target_map_id=482)  # Bjora Marches
    
    # Traverse through Bjora Marches to Longeyes Ledge
    bot.Move.XY(-11232.550781, -16722.859375)
    bot.Move.XY(-7655.780273 , -13250.316406)
    bot.Move.XY(-6672.132324 , -13080.853515)
    bot.Move.XY(-5497.732421 , -11904.576171)
    bot.Move.XY(-3598.337646 , -11162.589843)
    bot.Move.XY(-3013.927490 ,  -9264.664062)
    bot.Move.XY(-1002.166198 ,  -8064.565429)
    bot.Move.XY( 3533.099609 ,  -9982.698242)
    bot.Move.XY( 7472.125976 , -10943.370117)
    bot.Move.XY(12984.513671 , -15341.864257)
    bot.Move.XY(17305.523437 , -17686.404296)
    bot.Move.XY(19048.208984 , -18813.695312)
    bot.Move.XY(19634.173828, -19118.777343)
    bot.Wait.ForMapLoad(target_map_id=650)  # Longeyes Ledge

def SearchForTheEbonVanguard(bot):
    """Complete Search for the Ebon Vanguard mission"""
    bot.States.AddHeader("Search for the Ebon Vanguard")
    bot.Map.Travel(target_map_id=650)  # Longeyes Ledge if not already here
    bot.Move.XY(-25160, 13505)
    bot.Dialogs.AtXY(-25160, 13505, 0x831801) #Longeyes
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndExitMap(-21502, 12458, target_map_name="Grothmar Wardowns")
    bot.Move.XY(-14000, 4297)
    bot.Move.XY(-9580.00, -2860) #Helmet
    bot.Dialogs.AtXY(-9580.00, -2860, 0x831807) #Helmet give a reward? ok
    bot.Dialogs.AtXY(-9580.00, -2860, 0x84) #Examine helmet
    bot.Wait.ForMapToChange(target_map_id=665)  # Instanced Grothmar Wardowns
    bot.Multibox.UseAllConsumables() 
    path = [(-10011, -2509), (5221, -3019), (18715, -3896), (20010, -66), (17938, 2493), (19705, 3742)]
    bot.Move.FollowAutoPath(path) #Charr Explosive ModelID for later maybe is 22262
    bot.Wait.ForMapToChange(target_map_id=649)  # Grothmar Wardowns
    bot.Move.XYAndDialog(19106,413,0x838C01) #Pyre Dialog
    bot.Move.XY(11484, 1898)
    bot.Move.XY(11388, 4143) #wall hugging
    bot.Move.XY(23634, 15333)
    bot.Move.XYAndExitMap(25604, 15412,target_map_id=647) #Dalada Uplands
    bot.Multibox.UseAllConsumables() 
    bot.Move.XY(-13181, 3067)
    bot.Move.XY(-14576, 10999)
    bot.Move.XY(-15193, 13347) ; bot.Interact.WithGadgetAtXY(-15369, 13087) #Charr Lock to make Pyre hold it open
    bot.Move.XY(-17533, 14473)
    bot.Move.XY(-16740, 17124) ; bot.Wait.UntilOutOfCombat()
    bot.Wait.ForMapToChange(target_map_id=648) #Doomlore Shrine
    bot.Move.XYAndDialog(-19090.86, 18003.03, 0x838C07) #Doomlore Dialog

def WarbandOfBrothers(bot):
    bot.States.AddHeader("Warband Of Brothers Mission")
    bot.Map.Travel(target_map_id=648)  # Doomlore Shrine
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(-19094, 17945, 0x84)
    bot.Wait.ForMapToChange(target_map_id=666)
    #Level 1
    bot.Multibox.UseAllConsumables() 
    bot.Move.XY(-13404, -2958)
    bot.Move.XY(-7696, 4576)
    bot.Items.AddModelToLootWhitelist(25413)
    bot.Move.XY(-4608.37, 6540.96)
    bot.Items.LootItems()
    bot.Move.XY(-7635.53, 6734.37)
    bot.Items.LootItems()
    bot.Move.XY(-9029.55, 5824.05)
    bot.Items.LootItems()
    bot.Move.XY(-6440.49, 7335.86)
    bot.Items.LootItems()
    bot.Move.XY(-4043.76, 6405.57)
    bot.Interact.WithGadgetAtXY(-4043.76, 6405.57) #Open Door
    bot.Wait.ForTime(2000)
    bot.Move.XY(-1959.15, 7955.19)
    bot.Move.XY(1490.38, 8409.88)
    bot.Move.XY(3217.90, 8404.31)
    bot.Move.XY(-4608.37, 6540.96)
    bot.Move.XY(-16482.00, 1716.68)
    bot.Move.XY(-18616.02, 806.14)
    bot.Move.FollowAutoPath([(-19704, 318)])
    bot.Wait.ForMapLoad(target_map_id=667)
    #Level 2
    bot.Multibox.UseAllConsumables() 
    bot.Move.XY(-3290.88, 15187.92)
    bot.Move.XY(-1760.07, 12088.74)
    bot.Move.XY(-475.83, 11932.78)
    bot.Items.AddModelToLootWhitelist(25413)
    bot.Items.LootItems()
    bot.Move.XY(-2164.81, 11785.08)
    bot.Items.LootItems()
    bot.Move.XY(-2061.81, 12930.91)
    bot.Items.LootItems()
    bot.Move.XY(-2407.16, 14068.22)
    bot.Items.LootItems()
    bot.Move.XY(-2254.00, 11176.00)
    bot.Interact.WithGadgetAtXY(-2254.00, 11176.00)
    bot.Wait.ForTime(2000)
    bot.Move.XY(-2404.72, 9076.48)
    bot.Move.XY(2683.45, 12114.46)
    bot.Move.XY(6634.50, 17973.61)
    bot.Move.XY(7429.30, 13458.01)
    bot.Move.XY(13162.54, 9219.06)
    bot.Move.XY(15923.27, 8823.71)
    bot.Move.FollowAutoPath([(16782, 8642)])
    bot.Wait.ForMapLoad(target_map_id=668)
    # Level 3
    bot.Multibox.UseAllConsumables() 
    bot.Move.XY(17337.79, -5963.91)
    bot.Items.AddModelToLootWhitelist(25413)
    bot.Items.LootItems()
    bot.Move.XY(16669.06, -4763.91)
    bot.Items.LootItems()
    bot.Move.XY(16089.83, -3724.50)
    bot.Items.LootItems()
    bot.Move.XY(17159.00, -6461.00)
    bot.Interact.WithGadgetAtXY(17159.00, -6461.00)
    bot.Wait.ForTime(2000)
    bot.Move.XY(17808.17, -9149.82)
    bot.Move.XY(18827.79, -10402.15)
    bot.Move.XY(18742.40, -12129.31)
    bot.Move.XY(18194.92, -14704.77)
    bot.Items.LootItems()
    bot.Move.XY(18334.16, -13903.64)
    bot.Items.LootItems()
    bot.Move.XY(18704.73, -12773.99)
    bot.Items.LootItems()
    bot.Interact.WithGadgetAtXY(18147.00, -14974.00)
    bot.Wait.ForTime(2000)
    bot.Move.XY(14379.01, -15352.70)
    bot.Move.XY(10392.54, -14173.80)
    bot.Items.LootItems()
    bot.Move.XY(9714.57, -12360.55)
    bot.Items.LootItems()
    bot.Move.XY(8907.67, -11354.53)
    bot.Items.LootItems()
    bot.Move.XY(8425.21, -9845.09)
    bot.Items.LootItems()
    bot.Move.XY(9908.98, -12902.71)
    bot.Interact.WithGadgetAtXY(10034.00, -14899.00)
    bot.Wait.ForTime(2000)
    bot.Move.XY(7685.12, -16387.24)
    bot.Move.XY(3930.38, -13150.31)
    bot.Move.XY(1072.90, -8136.26)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForMapToChange(target_map_id=648) #Doomlore Shrine

def WhatMustBeDone(bot): #Done!!!
    bot.States.AddHeader("What Must Be Done")
    bot.Map.Travel(target_map_id=648) #Doomlore Shrine
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(-14185, 17040, 0x838D01) #the Dialog here
    bot.Move.XYAndExitMap(-15479, 13484,target_map_id=647) #Dalada Upland
    bot.Wait.ForMapToChange(target_map_id=647)
    bot.Move.XY(-12085, 8447)
    bot.Move.XY(-9360, -298)
    bot.Move.XY(-6856, -7620) ; bot.Wait.UntilOutOfCombat() #Armored Saurus 
    bot.Map.Travel(target_map_id=648)
    bot.Move.XYAndDialog(-14185, 17040, 0x84) #Let's Rumble
    bot.Wait.ForMapToChange(target_map_id=674) #Warband Training
    bot.Move.XY(-16946, 17319) ; bot.Wait.UntilOnCombat() #Warband Fight
    bot.Wait.ForTime(30000) #30 second after mission countdown
    bot.Wait.ForMapToChange(target_map_id=648) #Doomlore Shrine
    bot.Move.XYAndDialog(-14185, 17040, 0x838D07) 
    #done. 
   

def AssaultOnTheStrongHold(bot): #Done!!!
    bot.States.AddHeader("Assault on the Stronghold")
    bot.Map.Travel(target_map_id=648) #Doomlore Shrine
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndExitMap(-15479, 13484,target_map_id=647) #Dalada Upland
    bot.Wait.ForMapToChange(target_map_id=647)
    bot.Move.XYAndDialog(-13849, 11217, 0x84)
    bot.Wait.ForMapToChange(target_map_id=669)
    bot.Multibox.UseAllConsumables()
    bot.Move.XY(5203, 12344) #Right Siege
    bot.Move.XY(5843, 9145) #Left Siege
    bot.Move.XYAndDialog(5843, 9145, 0x84)
    bot.Move.XYAndDialog(5203, 12344, 0x84)
    bot.Move.XY(936, 10709) #Gate
    bot.Wait.ForTime(30000) #adjust as needed for gate to come down.
    bot.Move.XY(-1671, 11103)
    bot.Move.XY(-4202, 11045)
    bot.Move.XY(-6271, 12087)
    bot.Move.XY(-6896, 13899)
    bot.Move.XY(-6393, 9770)
    bot.Move.XY(-6895, 8102)
    bot.Wait.ForMapToChange(target_map_id=649)
    bot.Dialogs.AtXY(-21069.00, 12353.00, 0x831907)
    #Done
def FindingGadd(bot):
    bot.States.AddHeader("Finding Gadd")
    bot.Map.Travel(target_map_id=624) #Vlox's Falls
    bot.Move.XYAndDialog(16363, 15909, 0x833301) #Livia
    bot.Map.Travel(target_map_id=638) #Gadd's Encampment
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-8755, -23240) #Camp Fire to avoid stuck on Julia
    bot.Move.XYAndDialog(-8295, -23572, 0x833304) #Talk to Bartholos for right Dialog 
    bot.Move.XY(-8755, -23240) #Camp Fire to avoid stuck on Julia
    bot.Move.XYAndExitMap(-9690, -19524, target_map_id=558) #sparkfly swamp
    bot.Multibox.UseAllConsumables()
    bot.Move.XY(-6967.77, -19810.06)
    bot.Move.XY(11669, -23829)
    bot.Dialogs.AtXY(11881.00, -23802.00, 0x833304)
    bot.Move.XY(8017.92, -20124.24)
    bot.Move.XY(11184.85, -14188.88) #Ettin 1
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(5000)
    bot.Move.XY(-5740.47, -13723.29) #Ettin 2
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(5000)
    bot.Move.XY(2417.11, -25444.55) #Ettin 3
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(5000)
    bot.Move.XY(11758.78, -24063.51)
    bot.Wait.ForTime(20000) #Return to Inscription Plate
    bot.Dialogs.AtXY(11496.13, -23878.08, 0x833304) #Gadd Dialog model id 6721

def FindingTheBloodstone(bot): #started but need Finding Gadd before this
    bot.States.AddHeader("Finding the Bloodstone")
    bot.Map.Travel(target_map_id=638) #Gadd's Encampment
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndExitMap(-9690, -19524, target_map_id=558) #sparkfly swamp
    bot.Multibox.UseAllConsumables()
    bot.Move.XY(-6967.77, -19810.06)
    bot.Move.XY(11669, -23829)
    bot.Dialogs.AtXY(11795.00, -24125.00, 0x833307)
    bot.Dialogs.AtXY(11795.00, -24125.00, 0x84)
    bot.Wait.ForMapToChange(target_map_id=661) #Finding The Bloodstone Map Level 1
    bot.Multibox.UseAllConsumables()
    bot.Move.XY(12437, 16557)
    bot.Move.XY(12588, 14755)
    bot.Move.XY(15387, 6941)
    bot.Wait.UntilOutOfCombat() #Inscribed Sentry #1
    bot.Wait.ForTime(6000) #time to extract essence
    bot.Move.XY(16165.77, 10441.95)
    bot.Move.XY(17149.38, 13434.60)
    bot.Move.XY(18529, 15977)
    bot.Wait.ForTime(3000) #wait for Gadd to exit to level 2
    bot.Move.XYAndExitMap(19212, 16155,target_map_id=662) #Finding The Bloodstone Map Level 2
    bot.Multibox.UseAllConsumables()
    bot.Move.XY(-611.51, 5115.83)
    bot.Move.XY(3574.70, 3567.62)
    bot.Move.XY(4827.10, 1968.97)
    bot.Move.XY(11548.76, -2795.90)
    bot.Move.XY(14596, -7708)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(10000) #time to extract essence
    bot.Move.XY(16743, -10170)
    bot.Wait.ForTime(3000) #wait for Gadd to exit to level 3
    bot.Move.XYAndExitMap(18450, -10273,target_map_id=663) #Finding The Bloodstone Map Level 3
    bot.Multibox.UseAllConsumables()
    bot.Move.XY(-7249, -16397)
    bot.Move.XY(-10466, -16166)
    bot.Move.XY(-15377, -16565)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForMapToChange(target_map_id=638) #Gadd's Encampment

def LabSpace(bot):
    bot.States.AddHeader("Lab Space - Placeholder")
    bot.Map.Travel(target_map_id=624) #Vlox's Falls
    bot.Move.XY(16202.00, 16092.00)
    bot.Dialogs.AtXY(16202.00, 16092.00, 0x832C01) #Lab Space
    bot.Map.Travel(target_map_id=640) #Rata Sum
    bot.Move.XY(16024.00, 18468.00)
    bot.Dialogs.AtXY(16024.00, 18468.00, 0x832C04) #Lab Space
    bot.Move.XY(-6062, -2688,"Exit Outpost")
    bot.Wait.ForMapLoad(target_map_name="Magus Stones")
    bot.Move.XYAndDialog(10228.00, 11488.00, 0x832C04) #Lab Space
    bot.Move.XY(8329.03, 9954.58)
    bot.Move.XY(7258.69, 10987.36)
    bot.Move.XY(4812.16, 11197.93)
    bot.Move.XY(2778.98, 13297.53)
    bot.Move.XY(499.76, 14253.58)
    bot.Move.XY(-4305.25, 13044.76)
    bot.Move.XY(-11493.07, 16584.55)
    bot.Move.XY(-17671.37, 14695.37)
    bot.Wait.UntilOutOfCombat()
    bot.Items.AddModelToLootWhitelist(24628)
    bot.Items.LootItems()
    bot.Dialogs.AtXY(-15946.10, 14596.89, 0x832C07) #Lab Space Reward

def GOLEM(bot):
    bot.States.AddHeader("G.O.L.E.M")
    bot.Dialogs.AtXY(-15946.10, 14596.89, 0x86) #GOLEM Entry
    bot.Dialogs.AtXY(-15946.10, 14596.89, 0x84) #GOLEM Entry
    bot.Move.XY(-17745.97, 15428.50)
    bot.Move.XY(-19058.36, 16374.06)
    bot.Move.XY(-19842.83, 14895.14)
    bot.Move.XY(-11381.00, 15598.00)
    bot.Wait.ForMapLoad(target_map_id=658) #G.O.L.E.M Level 1
    bot.Move.XY(-14507.94, 12302.58)
    bot.Dialogs.AtXY(-14542.00, 12237.00, 0x81) #GOLEM Activation
    bot.Move.XY(-17204.16, 8545.91)
    bot.Interact.WithGadgetAtXY(-17601.00, 8150.00)
    bot.Wait.ForTime(30000)
    bot.Move.XY(-15960.14, 3309.37)
    bot.Move.XY(-13369.91, -965.44)
    bot.Interact.WithGadgetAtXY(-11737.00, -3710.00)
    bot.Move.XY(-15108.84, -2793.48)
    bot.Move.XY(-16518.94, -662.78)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(18755.00, -19827.00)
    bot.Wait.ForMapLoad(target_map_id=659) #G.O.L.E.M Level 2
    bot.Interact.WithGadgetAtXY(15979.00, -17531.00)
    bot.Move.XY(18031.51, -13929.63)
    bot.Interact.WithGadgetAtXY(15551.00, -13705.00)
    bot.Move.XY(15551.00, -13705.00)
    bot.Move.XY(9928.16, -10998.24)
    bot.Move.XY(5953.36, -9815.89)
    bot.Move.XY(4531.82, -9827.91)
    bot.Move.XY(3035.53, -9450.54)
    bot.Move.XY(3485.59, -11380.60)
    bot.Move.XY(-229.00, -12033.00)
    bot.Dialogs.AtXY(-229.00, -12033.00, 0x84) #Golem worker n. 1
    bot.Move.XY(-2639.00, -15247.00)
    bot.Dialogs.AtXY(-2639.00, -15247.00, 0x84) #Golem worker n. 2
    bot.Move.XY(3833.00, -16855.00)
    bot.Dialogs.AtXY(3833.00, -16855.00, 0x84) #Golem worker n. 3
    bot.Move.XY(3042.09, -16940.08)
    bot.Wait.ForTime(10000)
    bot.Move.XY(3348.06, -16214.14)
    bot.Wait.ForTime(10000)
    bot.Move.XY(5107.97, -17710.35)
    bot.Interact.WithItemAtXY(7701.87, -19207.43)
    bot.Interact.WithGadgetAtXY(5356.00, -19374.00)
    bot.Wait.ForTime(30000)
    bot.UI.DropBundle # first spike
    bot.Interact.WithItemAtXY(5356.00, -19374.00)
    bot.Interact.WithGadgetAtXY(5356.00, -19374.00)
    bot.Wait.ForTime(30000)
    bot.UI.DropBundle # second spike
    bot.Interact.WithItemAtXY(5356.00, -19374.00)
    bot.Interact.WithGadgetAtXY(5356.00, -19374.00)
    bot.Wait.ForTime(30000)
    bot.UI.DropBundle # third spike
    bot.Move.XY(6966.59, -19962.61)
    bot.Move.XY(-14728.00, 8556.00)
    bot.Wait.ForMapLoad(target_map_id=660) #G.O.L.E.M Level 3
    bot.Move.XY(-12164.00, 10409.53)
    bot.Move.XY(-12584.28, 13570.28)
    bot.Move.XY(-15062.15, 16139.62)
    bot.Wait.ForMapToChange(target_map_id=640) #Rata Sum







    
bot.SetMainRoutine(Routine)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path="EOTN.png")

if __name__ == "__main__":
    main()

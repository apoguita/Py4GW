
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
    UnlockEyeOfTheNorthPool(bot)               # Unlock EOTN resurrection pool
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
    
    # === PHASE 4: ADVANCED MISSIONS ===
    AdvanceToLongeyeEdge(bot)                  # Advance to Longeye's Edge
    SearchForTheEbonVanguard(bot)
    WarbandOfBrothers(bot)                      # Complete Ebon Vanguard mission

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
    bot.Move.XYAndDialog(-19094, 17945, 0x84)
    ConfigureAggressiveEnv(bot)
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



bot.SetMainRoutine(Routine)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path="Norn Story.png")

if __name__ == "__main__":
    main()

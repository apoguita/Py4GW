from Py4GWCoreLib import*


#VARIABLES
module_name = "Py4GW - LDoA"

class AppState :
    def __init__(self) :
        self.radio_button_selected = 20

state = AppState()

class BotVars:
    def __init__(self, map_id=0):
        self.ascalon_map = 148 #ASCALON
        self.foible_map = 165 #FOIBLE
        self.abbey_map = 164 #ABBEY  
        self.barradin_map = 163 #BARRADIN ESTATE
        self.ranik_map = 166 #FORT RANIK
        self.bot_started = False
        self.window_module = None
        self.variables = {}

follow_delay_timer = Timer()
loot_timer = Timer() 

class GameAreas:
    def __init__(self):
        self.Area = 1600 
        self.Area_1 = 2000

ModelData = {}
text_input = "resign"
text_bonus = "bonus"
text_dialog = "dialog take"
area_distance = GameAreas()
PyPlayer.PyPlayer()
player_instance = PyPlayer.PyPlayer()


bot_vars = BotVars(map_id=148) #ASCALON
bot_vars.window_module = ImGui.WindowModule(module_name, window_name="Py4GW - LDoA", window_size=(300, 350))

agent_id = Player.GetAgentID()

#COORDS
#LVL 1 - COMMON CORDS
town_crier_coordinate_list = [(9800, -453),(9983, -483)]
sir_tydus_coordinate_list = [(10780, 1039),(11686, 3444)]
going_out_ascalon_coordinate_list = [(7669, 5776),(7416, 5527),(7400, 5450)]
althea_coordinate_list = [(5132, 5130),(2785, 7726)]
leveling_coordinate_list = [(1787, 6051),(-1598, 5442),(-1504, 3937),(-4862, 4357),(-4780, 6813),(-6099, 5896),(-4443, 7583),(-5463, 11334),(-8548, 11318),(-8749, 7125),(-8766, 5884),(-7931, 4779),(-7064, 2961)]
taking_quest_coordinate_list = [(7555, 10673),(5703, 10663)]

#WARRIOR
van_coordinate_list = [(6435, 4295),(6126, 3997)]
warrior_quest_coordinate_list = [(5639, 2509),(5055, -82),(5793, -3249),(4668, -3311)]

#RANGER
artemis_coordinate_list = [(6382, 4349),(6152, 4203)]
ranger_quest_coordinate_list = [(4873, 1278),(5005, -1706),(5546, -4058)]

#MONK 
ciglo_coordinate_list = [(6355, 4323),(6008, 4203)]
monk_quest_coordinate_list_1 = [(5241, 1122),(4353, -2354),(3820, -4486)]
monk_quest_coordinate_list_2 = [(4406, -1190),(5229, 1849),(5905, 4164)]

#NECROMANCER
verata_coordinate_list = [(6427, 4368),(6146, 4197)]
necromancer_quest_coordinate_list = [(4807, 1228),(4321, 339)]

#MESMER
sebedoh_coordinate_list = [(6540, 4215),(6232, 3924)]
mesmer_quest_coordinate_list = [(4917, 1313),(4732, 989)]

#ELEMENTALIST
howland_coordinate_list = [(6489, 4341),(6189, 4058)]
elementalist_quest_coordinate_list = [(4668, 899),(5061, -3072),(5416, -3868),(4628, -3326),(4912, -2723)]

#DULL CARAPACES
dull_carapaces_coordinate_list_1 = [(6172, 3424),(5622, -1252),(6846, -4826),(8672, -8150)]
dull_carapaces_coordinate_list_2 = [(9780, -9295),(12204, -8720),(9406, -11301),(6718, -11119),(5545, -9860),(5652, -10396),(3570, -12713),(3338, -14367)]

#GARGOYLE SKULLS
gargoyle_skull_coordinate_list = [(-6865, 16314),(-6110, 15653),(-3609, 18598),(319, 17870),(4637, 18761),(8681, 18328),(12009, 18320),(8850, 18318),(4803, 18858),(3978, 13475),(2475, 10590),(2363, 8723),(6730, 9137),(7973, 7602),(10277, 7417),(12404, 9434),(10383, 7245),(10153, 6107)]

#GRAWL NECKLACES
grawl_necklace_coordinate_list = [(-7907, 1420),(-7604, -174),(-1761, 302),(1534, 427),(3561, 3397),(5011, 4977),(6771, 5189),(4407, 5696),(2897, 6742),(6016, 9555),(5084, 12217),(10102, 10290),(10446, 11629),(10523, 9636),(9650, 12299),(10809, 14616),(11965, 12534),(13720, 11643),(15842, 12116)]

#ICY LODESTONES
icy_lodestone_coordinate_list = [(1929, 6567),(2756, 3318),(2925, 685),(801, 2199),(-1758, 4377),(-3870, 3716),(-5544, 1239),(-5822, -46),(-5907, -3149),(-5403, -5352),(-4042, -6547),(-5660, -9938),(-8195, -10859),(-9841, -10663),(-12558, -11765),(-14690, -12464),(-17297, -11145),(-16217, -8138),(-15125, -6660)]

#ENCHANTED LODESTONES
barradin_goingtofarm_coordinate_list = [(-7218, 1426), (-7400,1441)]
enchanted_lodestone_coordinate_list = [(-7921, 1440),(-5399, 5794),(-6767, 8561),(-8279, 10731),(-9908, 12031),(-12251, 10228),(-14230, 12048),(-15170, 13810),(-16298, 14700),(-18429, 14048),(-20027, 12365),(-18622, 10544),(-15839, 7664),(-13401, 8732),(-11610, 7356),(-9953, 5829),(-12260, 3482),(-11355, 963),(-11205, -1713),(-8553, -3224),(-10732, -3983),(-13355, -3293),(-8234, -8273),(-5533, -7010),(-1779, -4108),(-1779, -4108),(6834, -1757),(10554, -2699),(10554, -2699),(12037, -716),(9518, -280),(7715, 1582),(10290, 2364),(12597, 4909),(14283, 4709),(13888, 5908),(17120, 3392),(17183, -1059),(15351, -3086),(15434, -87),(13876, -2130),(15506, -6090),(11521, -6408),(8473, -8671),(7724, -4358)]

#RED IRIS FLOWERS
red_iris_flowers_coordinate_list_1 = [(3933, 6375),(-1421, 9928),(-1916, 10016)]
red_iris_flowers_coordinate_list_2 = [(-5258, 11577),(-8414, 11233),(-9791, 4834),(-11879, 2053),(-9744, -1949)]
red_iris_flowers_coordinate_list_3 = [(-11003, -7776),(-12006, -12989)]
red_iris_flowers_coordinate_list_4 = [(-9578, -16011),(-4681, -12246),(-3060, -13281),(-468, -10929)]
red_iris_flowers_coordinate_list_5 = [(2432, -8082),(5837, -6406),(9905, -7336),(11280, -6987)]

#SKELETAL LIMBS
greenhills_to_catacombs = [(-5677, 5335), (-5356, 8272), (-3150, 9200)]
skele_limbs_coordinate_list = (-7439, 13679), (-4499, 10305), (-4468, 8420), (-6126, 8229), (-7305, 9075), (-8043, 9784), (-9305, 10684), (-11632, 10827), (-12712, 9802), (-13320, 9242), (-13514, 7688), (-13335, 6960), (-12263, 5545), (-11292, 5096), (-9862, 4795), (-8895, 5093), (-8260, 5806), (-7267, 6571)

#SKALE FIN
skale_fin_coordinate_list = [(22578, 6846),(22323, 4048),(21443, 1909),(18033, 2908),(16335, 3362),(15881, 7289),(16861, 6427),(15501, 2865),(13711, 2461),(13511, 1802),(15186, 39),(17397, 903),(19531, 946)]  

#SPIDER LEGS
ranik_goingtofarm_coordinate_list = [(22858, 10512),(22554, 8048),(22529, 7569),(22527, 7450)]
spider_leg_coordinate_list_1 = [(22532, 5576),(21978, 3604),(19968, 1388),(18462, -1529),(18444, -3023),(19911, -5170),(20548, -6388),(21722, -7002)]
spider_leg_coordinate_list_2 = [(21072, -6376),(19635, -4807),(17780, -3376),(16003, -5076),(15449, -8006),(17323, -11240),(18931, -12260),(19979, -12162),(21141, -12814),(21915, -12167),(21007, -11370),(18961, -12306),(17074, -10430),(14527, -10426),(12768, -10614),(10277, -11768),(8869, -11638),(8172, -12088),(7111, -12836),(4879, -13254),(2820, -12874),(1823, -12239),(637, -11093),(-190, -10429),(2104, -10838),(3435, -8681),(5221, -5253),(5163, -3186),(5661, -2630),(7170, -3541),(7845, -8356),(9010, -9787),(7856, -10328)]

#UNNATURAL SEEDS
unnatural_seeds_coordinate_list = [(-7910, 1418),(-7555, -1752),(-8062, -3071),(-12424, -3125),(-10948, -5876),(-8324, -8323),(-13903, -2822),(-14847, -707),(-15180, 2976),(-16849, 70448),(-20397, 8233),(-20550, 6263),(-20964, 3164),(-18933, 3676),(-17504, 3399),(-20758, -1853),(-20250, -5231),(-19147, -6511),(-16715, -7669),(-16317, -9650),(-16739, -11548),(-12792, -14235),(-15378, -15096)]

ascalon_coordinate_list = [(7420, 5450)]
rurikpause_coordinate_list = [(5987, 4087),(6537,4449)]
rurik_coordinate_list = [(6068, 4180),(5835, 4323),(5602, 4493),(5371, 4672),(5147, 4858),(4933, 5058),(4721, 5255),(4504, 5446),(4283, 5637),(4068, 5825),(3845, 6010),(3577, 6131),(3299, 6199),(3012, 6249),(2720, 6290),(2438, 6324),(2147, 6362),(1860, 6416),(1575, 6433),(1284, 6437),(995, 6441),(702, 6477),(428, 6576),(208, 6759),(-7, 6959),(-221, 7157),(-437, 7358),(-649, 7555),(-861, 7751),(-1080, 7944),(-1301, 8129),(-1522, 8312),(-1750, 8496),(-1997, 8641),(-2260, 8776),(-2519, 8910),(-2753, 9078),(-2902, 9324),(-3020, 9584),(-3137, 9847),(-3252, 10115),(-3367, 10386),(-3486, 10655),(-3724, 10822),(-3981, 10957),(-4241, 11095),(-4483, 11222)]


foible_coordinate_list = [(344, 7832), (367, 7790)]
bandit_coordinate_list = [(2312, 5970), (2586,4429)]

abbeyout_coordinate_list = [(7954, 5862),(7430, 5480),(7410, 5480)]
abbey_coordinate_list = [(3386, -1112), (-220, -5393), (-3710, -6761), (-6529, -6570), (-11028, -6230), (-11060, -6200)]

foibleout_coordinate_list = [(-11436, -6243), (-11400, -6250)]
foible_coordinate_list_one = [(-10981, -7090),(-11122, -8523),(-11432, -9934),(-11764, -11343),(-12125, -12705),(-12434, -14111),(-12674, -15526),(-12195, -16875),(-11589, -18186),(-11426, -19353),(-12765, -19885),(-13353, -20080),(-13900, -20115)]
foible_coordinate_list_two = [(9449, 19702),(8930, 18412),(8359, 17098),(7452, 16009),(6267, 15195),(5451, 14006),(4664, 12799),(3873, 11587),(3097, 10374),(2432, 9087),(1727, 7834),(724, 7238),(533, 7395),(400, 7600)]

ranikout_coordinate_list = [(-11436, -6243), (-11400, -6250)]
ranik_coordinate_list_one = [(-10932, -6205),(-9515, -6346),(-8090, -6555),(-6729, -7002),(-6127, -8304),(-5594, -9649),(-5082, -10996),(-4517, -12318),(-3366, -13136),(-2190, -13980),(-1022, -14822),(135, -15678),(1116, -16709),(1898, -17926),(2973, -18873),(4168, -19684),(4021, -19758),(4200, -19700)]
ranik_coordinate_list_two = [(-14893, 16791),(-14206, 15600),(-13866, 15095),(-12586, 14586),(-11475, 13725),(-10498, 12872),(-9315, 12098),(-8090, 11395),(-6881, 10672),(-5675, 9957),(-4718, 9350),(-3505, 8623),(-800, 7122),(255, 6260),(736, 6445),(2141, 6244),(3407, 5858),(4699, 5564),(6082, 5353),(6991, 4725),(7820, 3665),(8972, 2951),(10137, 2640),(11540, 2574),(12891, 2200),(15271, 1458),(16644, 1483),(18046, 1557),(18737, 1920),(19933, 2595),(21107, 3367),(22013, 4355),(22253, 5513),(22309, 6178),(22547, 7142),(22500, 7100)]

barradinout_coordinate_list = [(7954, 5862),(7430, 5480),(7410, 5480)]
barradin_coordinate_list_one = [(6558, 4489),(5233, 5033),(3979, 5754),(2732, 6470),(1491, 7069),(258, 7412),(-962, 8152),(-2149, 8973),(-3284, 9842),(-3890, 10510),(-5070, 11302),(-6496, 11491),(-7890, 11304),(-8648, 10100),(-9374, 8859),(-10468, 7955),(-11728, 8344),(-12897, 9191),(-14117, 9957),(-14600, 10060)]
barradin_coordinate_list_two = [(21932, 12966),(20720, 13561),(19394, 13174),(18149, 12450),(17131, 11462),(16396, 10223),(15660, 8984),(14871, 7778),(14080, 6573),(13372, 5317),(12640, 4076),(11617, 3237),(10499, 2614),(10646,1180),(11326, -16),(11564, -1417),(10516, -2215),(9233, -2842),(7825, -3180),(6458, -3523),(5016, -3411),(3579, -3350),(2140, -3313),(696, -3293),(-512, -2603),(-1779, -1983),(-2953, -1141),(-4317, -695),(-5735, -423),(-7139, -154),(-7815, 751),(-7511, 1442),(-7310, 1456)]

#FUNCTIONS
def StartBot():
    global bot_vars
    bot_vars.bot_started = True

def StopBot():
    global bot_vars
    bot_vars.bot_started = False

def IsBotStarted():
    global bot_vars
    return bot_vars.bot_started

def ResetEnvironment():
    global FSM_vars

    #COMMONS LVL 1
    FSM_vars.town_crier_pathing.reset()
    FSM_vars.sir_tydus_pathing.reset()
    FSM_vars.going_out_ascalon_pathing.reset()
    FSM_vars.althea_pathing.reset()
    FSM_vars.leveling_pathing.reset()
    FSM_vars.taking_quest_pathing.reset()

    #WARRIOR LVL 1
    FSM_vars.state_machine_warrior.reset()
    FSM_vars.van_pathing.reset()
    FSM_vars.van_pathing_1.reset()
    FSM_vars.warrior_quest_pathing.reset()

    #RANGER LVL 1
    FSM_vars.state_machine_ranger.reset()
    FSM_vars.artemis_pathing.reset()
    FSM_vars.artemis_pathing_1.reset()
    FSM_vars.ranger_quest_pathing.reset()

    #MONK LVL 1
    FSM_vars.state_machine_monk.reset()
    FSM_vars.ciglo_pathing.reset()
    FSM_vars.monk_quest_pathing_1.reset()
    FSM_vars.monk_quest_pathing_2.reset()

    #NECROMANCER LVL 1
    FSM_vars.state_machine_necromancer.reset()
    FSM_vars.verata_pathing.reset()
    FSM_vars.verata_pathing_1.reset()
    FSM_vars.necromancer_quest_pathing.reset()

    #MESMER LVL 1
    FSM_vars.state_machine_mesmer.reset()
    FSM_vars.sebedoh_pathing.reset()
    FSM_vars.sebedoh_pathing_1.reset()
    FSM_vars.mesmer_quest_pathing.reset()

    #ELEMENTALIST LVL 1
    FSM_vars.state_machine_elementalist.reset()
    FSM_vars.howland_pathing.reset()
    FSM_vars.howland_pathing_1.reset()
    FSM_vars.elementalist_quest_pathing.reset()

    #DULL CARAPACES
    FSM_vars.state_machine_dull_carapaces.reset()
    FSM_vars.dull_carapaces_pathing_1.reset()
    FSM_vars.dull_carapaces_pathing_2.reset()

    #GARGOYLE SKULLS
    FSM_vars.state_machine_gargoyle_skulls.reset()
    FSM_vars.gargoyle_skulls_pathing.reset()

    #GRAWL NECKLACES
    FSM_vars.state_machine_grawl_necklaces.reset()
    FSM_vars.grawl_necklaces_pathing.reset()

    #ICY LODESTONES 
    FSM_vars.state_machine_icy_lodestones.reset()
    FSM_vars.icy_lodestones_pathing.reset()

    #ENCHANTED LODESTONES
    FSM_vars.state_machine_lodestone.reset()
    FSM_vars.barradin_goingtofarm_pathing.reset()
    FSM_vars.enchanted_lodestone_pathing.reset()

    #RED IRIS FLOWERS
    FSM_vars.state_machine_red_iris_flowers.reset()
    FSM_vars.red_iris_flowers_pathing_1.reset()
    FSM_vars.red_iris_flowers_pathing_2.reset()
    FSM_vars.red_iris_flowers_pathing_3.reset()
    FSM_vars.red_iris_flowers_pathing_4.reset()
    FSM_vars.red_iris_flowers_pathing_5.reset()

    #SKELETAL LIMBS
    FSM_vars.state_machine_skele_limbs.reset()
    FSM_vars.greenhills_to_catacombs_pathing.reset()
    FSM_vars.skele_limbs_pathing.reset()

    #SKALE FINS
    FSM_vars.state_machine_skale_fin.reset()
    FSM_vars.skale_fin_pathing.reset()

    #SPIDER LEGS
    FSM_vars.state_machine_spider_leg.reset()
    FSM_vars.ranik_goingtofarm_pathing.reset()
    FSM_vars.spider_leg_pathing_1.reset()
    FSM_vars.spider_leg_pathing_2.reset()

    #UNNATURAL SEEDS
    FSM_vars.state_machine_unnatural_seeds.reset()
    FSM_vars.unnatural_seeds_pathing.reset()   

    FSM_vars.ascalon_pathing.reset()
    FSM_vars.ascalon_pathing_1.reset()
    FSM_vars.rurikpause_pathing.reset()
    FSM_vars.rurik_pathing.reset()
    FSM_vars.foible_pathing.reset()
    FSM_vars.bandit_pathing.reset()
    FSM_vars.abbeyout_pathing.reset()
    FSM_vars.abbey_pathing.reset()
    FSM_vars.foibleout_pathing.reset()
    FSM_vars.foible_coordinate_list_one_pathing.reset()
    FSM_vars.foible_coordinate_list_two_pathing.reset()
    FSM_vars.ranikout_pathing.reset()
    FSM_vars.ranik_coordinate_list_one_pathing.reset()
    FSM_vars.ranik_coordinate_list_two_pathing.reset()
    FSM_vars.barradinout_pathing.reset()
    FSM_vars.barradin_coordinate_list_one_pathing.reset()
    FSM_vars.barradin_coordinate_list_two_pathing.reset()    

    

    FSM_vars.state_machine_lvl2_10.reset()
    FSM_vars.state_machine_lvl11_20.reset()
    FSM_vars.state_machine_abbey.reset()
    FSM_vars.state_machine_foible.reset()
    FSM_vars.state_machine_ranik.reset()
    FSM_vars.state_machine_barradin.reset()
    FSM_vars.state_machine_grandtour.reset()
    FSM_vars.movement_handler.reset()
    
def useitem(model_id):
    item = Item.GetItemIdFromModelID(model_id)
    Inventory.UseItem(item)

def quantityitem(model_id):
    item = Item.GetItemIdFromModelID(model_id)
    Item.Properties.GetQuantity(item)

def equipitem(model_id, agent_id):
    item = Item.GetItemIdFromModelID(model_id)
    agent_id = Player.GetAgentID() 

    Inventory.EquipItem(item, agent_id)

inventory = PyInventory.PyInventory()

#USED TO FOLLOW RURIK
def FollowPathwithDelayTimer(path_handler,follow_handler, log_actions=False, delay=3000):
    global follow_delay_timer
    follow_handler.update()
    if follow_handler.is_following():
        return
    if follow_delay_timer.IsStopped():
        follow_delay_timer.Start()
        return
    if follow_delay_timer.HasElapsed(delay):
        follow_delay_timer.Stop()
        point = path_handler.advance()
        if point is not None:
            follow_handler.move_to_waypoint(point[0], point[1])
            if log_actions:
                Py4GW.Console.Log("FollowPath", f"Moving to {point}", Py4GW.Console.MessageType.Info)

def set_killing_routine():
    global FSM_vars
    FSM_vars.in_waiting_routine = True
    FSM_vars.in_killing_routine = True

#STANDARD KILLING ROUTINE
def end_killing_routine():
    global FSM_vars, bot_vars
    global area_distance
    player_x, player_y = Player.GetXY()
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), area_distance.Area_1)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')


    if len(enemy_array) < 1:
        FSM_vars.in_waiting_routine = False
        FSM_vars.in_killing_routine = False
        return True

    return False

#RURIK KILLING ROUTINE
def end_killing_routine_1():
    global FSM_vars, bot_vars
    global area_distance
    player_x, player_y = Player.GetXY()
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), area_distance.Area)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    if len(enemy_array) < 2:
        FSM_vars.in_waiting_routine = False
        FSM_vars.in_killing_routine = False
        return True

    return False

#SURVIVOR FUNCTION TO AVOID DEAD, SET YOUR THRESHOLD AS YOU WISH
def Survivor():
    max_health = Agent.GetMaxHealth(Player. GetAgentID())
    current_health = Agent.GetHealth(Player. GetAgentID()) * max_health    
    
    if current_health < 55:
        return True  
    return False 

def Survivor_Hamnet():
    max_health = Agent.GetMaxHealth(Player. GetAgentID())
    current_health = Agent.GetHealth(Player. GetAgentID()) * max_health    
    
    if current_health < 120:
        return True  
    return False 

#FIGHT FUNCTIONS
def get_called_target():
    """Get the first called target from party members, if it's alive."""
    players = Party.GetPlayers()
    for player in players:
        if player.called_target_id != 0:
            target = PyAgent.PyAgent(player.called_target_id)
            if target.is_alive:
                return player.called_target_id
    return 0

def IsSkillReady2(skill_slot):
    skill = SkillBar.GetSkillData(skill_slot)
    return skill.recharge == 0

#STANDARD
def handle_map_path(map_pathing):
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()
    
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1320)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    if len(enemy_array) > 0:
        target_id = enemy_array[0]
        
        if target_id and Agent.IsAlive(target_id):
            Player.ChangeTarget(target_id)
            target_x, target_y = Agent.GetXY(target_id)
            distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5
            
            if distance_to_target > 1200:
                Routines.Targeting.InteractTarget()
                return
            
            if current_time - FSM_vars.last_skill_time >= 2.0:
                if IsSkillReady2(FSM_vars.current_skill_index):
                    SkillBar.UseSkill(FSM_vars.current_skill_index)
                    FSM_vars.last_skill_time = current_time
                    FSM_vars.current_skill_index = FSM_vars.current_skill_index % 8 + 1
    else:
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler) 

#LOOT MAP PATHING FUNCTION WORKING
def handle_map_path_loot(map_pathing):  
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()
    
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1200)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    item_array = AgentArray.GetItemArray()
    item_array = AgentArray.Filter.ByDistance(item_array, (my_x, my_y), 1200)

    agent_to_item_map = {
        agent_id: Agent.GetItemAgent(agent_id).item_id
        for agent_id in item_array
    }

    filtered_items = list(agent_to_item_map.values())
    filtered_items = ItemArray.Filter.ByCondition(
        filtered_items, lambda item_id: Item.GetItemType(item_id)[0] == 30 or Item.GetItemType(item_id)[0] == 10 or Item.GetItemType(item_id)[0] == 20
    )

    filtered_agent_ids = [
        agent_id for agent_id, item_id in agent_to_item_map.items()
        if item_id in filtered_items
    ]

    if len(enemy_array) > 0:
        target_id = enemy_array[0]
        if target_id and Agent.IsAlive(target_id):
            Player.Interact(target_id, call_target=False)
            target_x, target_y = Agent.GetXY(target_id)
            distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5

            if distance_to_target > 1200:
                Routines.Targeting.InteractTarget()
                return

            if current_time - FSM_vars.last_skill_time >= 2.0:
                if IsSkillReady2(FSM_vars.current_skill_index):
                    SkillBar.UseSkill(FSM_vars.current_skill_index)
                    FSM_vars.last_skill_time = current_time
                    FSM_vars.current_skill_index = (FSM_vars.current_skill_index % 8) + 1

    elif len(filtered_agent_ids) > 0:
        looting_item = filtered_agent_ids[0]
        
        if Player.GetTargetID() != looting_item:
            Player.ChangeTarget(looting_item)
            loot_timer.Reset()
            return

        if loot_timer.HasElapsed(1000) and Player.GetTargetID() == looting_item:
            Keystroke.PressAndRelease(Key.Space.value)
            loot_timer.Reset()
            return  

    Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)




#FOR WARRIOR LVL 1
def handle_map_path_warrior(map_pathing):

    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()
    
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1320)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    if len(enemy_array) > 0:
        target_id = enemy_array[0]
        
        if target_id and Agent.IsAlive(target_id):
            Player.ChangeTarget(target_id)
            target_x, target_y = Agent.GetXY(target_id)
            distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5
            
            if distance_to_target > 1200:
                Routines.Targeting.InteractTarget()
                return
            
            if current_time - FSM_vars.last_skill_time >= 2.0:
                if IsSkillReady2(FSM_vars.current_skill_index):
                    SkillBar.UseSkill(FSM_vars.current_skill_index)
                    FSM_vars.last_skill_time = current_time
                    
                    FSM_vars.current_skill_index = (FSM_vars.current_skill_index - 1) % 3 + 2
    else:
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)

#FOR MESMER LVL 1
def handle_map_path_mesmer(map_pathing):

    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()
    
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1320)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    if len(enemy_array) > 0:
        target_id = enemy_array[0]
        
        if target_id and Agent.IsAlive(target_id):
            Player.ChangeTarget(target_id)
            target_x, target_y = Agent.GetXY(target_id)
            distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5
            
            if distance_to_target > 1200:
                Routines.Targeting.InteractTarget()
                return
            
            if current_time - FSM_vars.last_skill_time >= 2.0:
                if IsSkillReady2(FSM_vars.current_skill_index):
                    SkillBar.UseSkill(FSM_vars.current_skill_index)
                    FSM_vars.last_skill_time = current_time
                    
                    FSM_vars.current_skill_index = FSM_vars.current_skill_index % 3 + 1
    else:
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)

#FOR EVERYONE LVL 1
def handle_map_path_early(map_pathing):

    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()
    
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1320)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    if len(enemy_array) > 0:
        target_id = enemy_array[0]
        
        if target_id and Agent.IsAlive(target_id):
            Player.ChangeTarget(target_id)
            target_x, target_y = Agent.GetXY(target_id)
            distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5
            
            if distance_to_target > 1200:
                Routines.Targeting.InteractTarget()
                return
            
            if current_time - FSM_vars.last_skill_time >= 2.0:
                if IsSkillReady2(FSM_vars.current_skill_index):
                    SkillBar.UseSkill(FSM_vars.current_skill_index)
                    FSM_vars.last_skill_time = current_time
                    
                    FSM_vars.current_skill_index = FSM_vars.current_skill_index % 4 + 1


    else:
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)

#FSM
class StateMachineVars:
    def __init__(self):

        self.movement_handler = Routines.Movement.FollowXY()
        self.last_skill_time = 0
        self.current_skill_index = 1
        self.last_item_pickup_time = 0

        #FSM for lvl 1
        self.town_crier_pathing =  Routines.Movement.PathHandler(town_crier_coordinate_list)
        self.sir_tydus_pathing = Routines.Movement.PathHandler(sir_tydus_coordinate_list)
        self.going_out_ascalon_pathing = Routines.Movement.PathHandler(going_out_ascalon_coordinate_list)
        self.ascalon_pathing_1 = Routines.Movement.PathHandler(ascalon_coordinate_list)
        self.althea_pathing = Routines.Movement.PathHandler(althea_coordinate_list)
        self.leveling_pathing = Routines.Movement.PathHandler(leveling_coordinate_list)
        self.taking_quest_pathing = Routines.Movement.PathHandler(taking_quest_coordinate_list)

        #FSM for WARRIOR lvl 1
        self.state_machine_warrior = FSM("WARRIOR")
        self.van_pathing = Routines.Movement.PathHandler(van_coordinate_list)
        self.van_pathing_1 = Routines.Movement.PathHandler(van_coordinate_list)
        self.warrior_quest_pathing = Routines.Movement.PathHandler(warrior_quest_coordinate_list)

        #FSM for RANGER lvl 1
        self.state_machine_ranger = FSM("RANGER")
        self.artemis_pathing = Routines.Movement.PathHandler(artemis_coordinate_list)
        self.artemis_pathing_1 = Routines.Movement.PathHandler(artemis_coordinate_list)
        self.ranger_quest_pathing = Routines.Movement.PathHandler(ranger_quest_coordinate_list)

        #FSM for MONK lvl 1
        self.state_machine_monk = FSM("MONK")
        self.ciglo_pathing = Routines.Movement.PathHandler(ciglo_coordinate_list)
        self.monk_quest_pathing_1 = Routines.Movement.PathHandler(monk_quest_coordinate_list_1)
        self.monk_quest_pathing_2 = Routines.Movement.PathHandler(monk_quest_coordinate_list_2)

        #FSM for NECROMANCER lvl 1
        self.state_machine_necromancer = FSM("NECROMANCER")
        self.verata_pathing = Routines.Movement.PathHandler(verata_coordinate_list)
        self.verata_pathing_1 = Routines.Movement.PathHandler(verata_coordinate_list)
        self.necromancer_quest_pathing = Routines.Movement.PathHandler(necromancer_quest_coordinate_list)

        #FSM for MESMER lvl 1
        self.state_machine_mesmer = FSM("MESMER")
        self.sebedoh_pathing = Routines.Movement.PathHandler(sebedoh_coordinate_list)
        self.sebedoh_pathing_1 = Routines.Movement.PathHandler(sebedoh_coordinate_list)
        self.mesmer_quest_pathing = Routines.Movement.PathHandler(mesmer_quest_coordinate_list)
        
        #FSM for MESMER lvl 1
        self.state_machine_elementalist = FSM("ELEMENTALIST")
        self.howland_pathing = Routines.Movement.PathHandler(howland_coordinate_list)
        self.howland_pathing_1 = Routines.Movement.PathHandler(howland_coordinate_list)
        self.elementalist_quest_pathing = Routines.Movement.PathHandler(elementalist_quest_coordinate_list)

        #FSM for lvl 2-10
        self.state_machine_lvl2_10 = FSM("LEVEL 2-10")
        self.ascalon_pathing = Routines.Movement.PathHandler(ascalon_coordinate_list)
        self.rurikpause_pathing = Routines.Movement.PathHandler(rurikpause_coordinate_list)
        self.rurik_pathing = Routines.Movement.PathHandler(rurik_coordinate_list)
        
        #FSM for lvl 11-20
        self.state_machine_lvl11_20 = FSM("LEVEL 11-20")
        self.foible_pathing = Routines.Movement.PathHandler(foible_coordinate_list)
        self.bandit_pathing = Routines.Movement.PathHandler(bandit_coordinate_list)

        #FSM for DULL CARAPACES
        self.state_machine_dull_carapaces = FSM("DULL CARAPACES")
        self.dull_carapaces_pathing_1 = Routines.Movement.PathHandler(dull_carapaces_coordinate_list_1)
        self.dull_carapaces_pathing_2 = Routines.Movement.PathHandler(dull_carapaces_coordinate_list_2)

        #FSM for GARGOYLE SKULLS
        self.state_machine_gargoyle_skulls = FSM("GARGOYLE SKULLS")
        self.gargoyle_skulls_pathing = Routines.Movement.PathHandler(gargoyle_skull_coordinate_list)

        #FSM for GRAWL NECKLACES
        self.state_machine_grawl_necklaces = FSM("GRAWL NECKLACES")
        self.grawl_necklaces_pathing = Routines.Movement.PathHandler(grawl_necklace_coordinate_list)

        #FSM for GRAWL NECKLACES
        self.state_machine_icy_lodestones = FSM("ICY LODESTONES")
        self.icy_lodestones_pathing = Routines.Movement.PathHandler(icy_lodestone_coordinate_list)

        #FSM for ENCHANTED LODESTONES
        self.state_machine_lodestone = FSM("ENCHANTED LODESTONES")
        self.barradin_goingtofarm_pathing = Routines.Movement.PathHandler(barradin_goingtofarm_coordinate_list)
        self.enchanted_lodestone_pathing = Routines.Movement.PathHandler(enchanted_lodestone_coordinate_list)
        
        #FSM for RED IRIS FLOWERS
        self.state_machine_red_iris_flowers = FSM("RED IRIS FLOWERS")
        self.red_iris_flowers_pathing_1 = Routines.Movement.PathHandler(red_iris_flowers_coordinate_list_1)
        self.red_iris_flowers_pathing_2 = Routines.Movement.PathHandler(red_iris_flowers_coordinate_list_2)
        self.red_iris_flowers_pathing_3 = Routines.Movement.PathHandler(red_iris_flowers_coordinate_list_3)
        self.red_iris_flowers_pathing_4 = Routines.Movement.PathHandler(red_iris_flowers_coordinate_list_4)
        self.red_iris_flowers_pathing_5 = Routines.Movement.PathHandler(red_iris_flowers_coordinate_list_5)

        #FSM for SKELETAL LIMBS
        self.state_machine_skele_limbs = FSM("SKELETAL LIMBS")
        self.greenhills_to_catacombs_pathing = Routines.Movement.PathHandler(greenhills_to_catacombs)
        self.skele_limbs_pathing = Routines.Movement.PathHandler(skele_limbs_coordinate_list)

        #FSM for SKELETAL LIMBS
        self.state_machine_skale_fin = FSM("SKALE FINS")
        self.skale_fin_pathing = Routines.Movement.PathHandler(skale_fin_coordinate_list)

        #FSM for SPIDER LEGS
        self.state_machine_spider_leg = FSM("SPIDER LEGS")
        self.ranik_goingtofarm_pathing = Routines.Movement.PathHandler(ranik_goingtofarm_coordinate_list)
        self.spider_leg_pathing_1 = Routines.Movement.PathHandler(spider_leg_coordinate_list_1)
        self.spider_leg_pathing_2 = Routines.Movement.PathHandler(spider_leg_coordinate_list_2)

        #FSM for UNNATURAL SEEDS
        self.state_machine_unnatural_seeds = FSM("UNNATURAL SEEDS")
        self.unnatural_seeds_pathing = Routines.Movement.PathHandler(unnatural_seeds_coordinate_list)

        #FSM for Ashford Abbey
        self.state_machine_abbey = FSM("ASHFORD ABBEY")
        self.abbeyout_pathing = Routines.Movement.PathHandler(abbeyout_coordinate_list)
        self.abbey_pathing = Routines.Movement.PathHandler(abbey_coordinate_list)

        #FSM for Foible's Fair
        self.state_machine_foible = FSM("FOIBLE'S FAIR")
        self.foibleout_pathing = Routines.Movement.PathHandler(foibleout_coordinate_list)
        self.foible_coordinate_list_one_pathing = Routines.Movement.PathHandler(foible_coordinate_list_one)
        self.foible_coordinate_list_two_pathing = Routines.Movement.PathHandler(foible_coordinate_list_two)

        #FSM for Fort Ranik
        self.state_machine_ranik = FSM("FORT RANIK")
        self.ranikout_pathing = Routines.Movement.PathHandler(ranikout_coordinate_list)
        self.ranik_coordinate_list_one_pathing = Routines.Movement.PathHandler(ranik_coordinate_list_one)
        self.ranik_coordinate_list_two_pathing = Routines.Movement.PathHandler(ranik_coordinate_list_two)

        #FSM for Barradin's Estate
        self.state_machine_barradin = FSM("THE BARRADIN ESTATE")
        self.barradinout_pathing = Routines.Movement.PathHandler(barradinout_coordinate_list)
        self.barradin_coordinate_list_one_pathing = Routines.Movement.PathHandler(barradin_coordinate_list_one)
        self.barradin_coordinate_list_two_pathing = Routines.Movement.PathHandler(barradin_coordinate_list_two)

        #FSM Grand Tour
        self.state_machine_grandtour = FSM("THE BARRADIN ESTATE")
        
FSM_vars = StateMachineVars()

#FSM LVL 1 - WARRIOR
FSM_vars.state_machine_warrior.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ascalon_map,6,0)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="BONUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "CREATING BONUS ITEMS", Py4GW.Console.MessageType.Info),player_instance.SendChatCommand(text_bonus)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="EQUIP WAND",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING WAND", Py4GW.Console.MessageType.Info),equipitem(6508,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="EQUIP SHIELD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING SHIELD", Py4GW.Console.MessageType.Info),equipitem(6514,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="GOING NEAR TOWN CRIER",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM TOWN CRIER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805001", 16))),
                       transition_delay_ms=100,
                       run_once=True)
 
FSM_vars.state_machine_warrior.AddState(name="GOING NEAR SIR TYDUS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH SIR TYDUS WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING REWARD QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805007", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendChatCommand(text_dialog)),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_warrior.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000)

#WARRIOR ROUTINE
FSM_vars.state_machine_warrior.AddState(name="GOING NEAR VAN",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.van_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.van_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "INTERACTING WITH VAN THE WARRIOR WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "INTERACTING WITH VAN THE WARRIOR WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "TAKING REWARD FROM VAN THE WARRIOR", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80DD07", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "TAKING QUEST FROM VAN THE WARRIOR", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805501", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="GOING TO KILL",
                       execute_fn=lambda: handle_map_path(FSM_vars.warrior_quest_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.warrior_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_warrior.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="GOING NEAR VAN",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.van_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.van_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "INTERACTING WITH VAN THE WARRIOR WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "INTERACTING WITH VAN THE WARRIOR WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "TAKING REWARD FROM VAN THE WARRIOR", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805507", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

#END WARRIOR ROUTINE

FSM_vars.state_machine_warrior.AddState(name="GOING NEAR ALTHEA",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804703", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="TAKING SKILL",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING SKILL LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804701", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="SECOND MAP PATH",
                       execute_fn=lambda: handle_map_path_warrior(FSM_vars.leveling_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_warrior.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 WARRIOR", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="GOING NEAR PRINCE RURIK",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_warrior.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM RURIK", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x802E01", 16))),
                       transition_delay_ms=100,
                       run_once=True)

#FSM LVL 1 - RANGER
FSM_vars.state_machine_ranger.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ascalon_map,6,0)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="BONUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "CREATING BONUS ITEMS", Py4GW.Console.MessageType.Info),player_instance.SendChatCommand(text_bonus)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="EQUIP WAND",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING WAND", Py4GW.Console.MessageType.Info),equipitem(6508,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="EQUIP SHIELD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING SHIELD", Py4GW.Console.MessageType.Info),equipitem(6514,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="GOING NEAR TOWN CRIER",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM TOWN CRIER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805001", 16))),
                       transition_delay_ms=100,
                       run_once=True)
 
FSM_vars.state_machine_ranger.AddState(name="GOING NEAR SIR TYDUS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH SIR TYDUS WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING REWARD QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805007", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80DE01", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranger.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000)

#RANGER ROUTINE
FSM_vars.state_machine_ranger.AddState(name="GOING NEAR ARTEMIS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.artemis_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.artemis_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH ",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "INTERACTING WITH ARTEMIS THE RANGER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "INTERACTING WITH ARTEMIS THE RANGER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "TAKING REWARD ARTEMIS THE RANGER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80DE07", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "TAKING QUEST FROM ARTEMIS THE RANGER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805601", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="GOING TO KILL",
                       execute_fn=lambda: handle_map_path(FSM_vars.ranger_quest_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranger_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranger.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranger.AddState(name="RUNNIN OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="GOING NEAR VAN",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.artemis_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.artemis_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH ARTEMIS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "INTERACTING WITH ARTEMIS THE RANGER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "INTERACTING WITH ARTEMIS THE RANGER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 RANGER", "TAKING REWARD FROM ARTEMIS THE RANGER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805607", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

#END RANGER ROUTINE
FSM_vars.state_machine_ranger.AddState(name="GOING NEAR ALTHEA",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804703", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="TAKING SKILL",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING SKILL LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804701", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="SECOND MAP PATH",
                       execute_fn=lambda: handle_map_path_early(FSM_vars.leveling_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranger.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="GOING NEAR PRINCE RURIK",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranger.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM RURIK", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x802E01", 16))),
                       transition_delay_ms=100,
                       run_once=True)

 #FSM LVL 1 - MONK
FSM_vars.state_machine_monk.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ascalon_map,6,0)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="BONUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "CREATING BONUS ITEMS", Py4GW.Console.MessageType.Info),player_instance.SendChatCommand(text_bonus)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="EQUIP WAND",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING WAND", Py4GW.Console.MessageType.Info),equipitem(6508,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="EQUIP SHIELD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING SHIELD", Py4GW.Console.MessageType.Info),equipitem(6514,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="GOING NEAR TOWN CRIER",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM TOWN CRIER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805001", 16))),
                       transition_delay_ms=1000,
                       run_once=True)
 
FSM_vars.state_machine_monk.AddState(name="GOING NEAR SIR TYDUS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH SIR TYDUS WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING REWARD QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805007", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80DC01", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_monk.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000)

#MONK ROUTINE
FSM_vars.state_machine_monk.AddState(name="GOING NEAR CIGLO",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ciglo_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ciglo_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH CIGLO THE MONK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MONK", "INTERACTING WITH CIGLO THE MONK WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH CIGLO",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MONK", "INTERACTING WITH CIGLO THE MONK WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MONK", "TAKING REWARD CIGLO THE MONK", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80DC07", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MONK", "TAKING QUEST FROM CIGLO THE MONK", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805401", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="GOING TO GWEN",
                       execute_fn=lambda: handle_map_path(FSM_vars.monk_quest_pathing_1),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.monk_quest_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH GWEN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MONK", "INTERACTING WITH GWEN WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH GWEN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MONK", "INTERACTING WITH GWEN WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="GOING BACK TO CIGLO",
                       execute_fn=lambda: handle_map_path(FSM_vars.monk_quest_pathing_2),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.monk_quest_pathing_2, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH CIGLO THE MONK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MONK", "INTERACTING WITH CIGLO THE MONK WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH CIGLO",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MONK", "INTERACTING WITH CIGLO THE MONK WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MONK", "TAKING REWARD CIGLO THE MONK", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805407", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

#END MONK ROUTINE

FSM_vars.state_machine_monk.AddState(name="GOING NEAR ALTHEA",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804703", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="TAKING SKILL",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING SKILL LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804701", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="SECOND MAP PATH",
                       execute_fn=lambda: handle_map_path_early(FSM_vars.leveling_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_monk.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="GOING NEAR PRINCE RURIK",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM RURIK", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x802E01", 16))),
                       transition_delay_ms=100,
                       run_once=True)                   
  
#FSM LVL 1 - NECROMANCER
FSM_vars.state_machine_necromancer.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ascalon_map,6,0)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="BONUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "CREATING BONUS ITEMS", Py4GW.Console.MessageType.Info),player_instance.SendChatCommand(text_bonus)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="EQUIP WAND",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING WAND", Py4GW.Console.MessageType.Info),equipitem(6508,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_monk.AddState(name="EQUIP SHIELD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING SHIELD", Py4GW.Console.MessageType.Info),equipitem(6514,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR TOWN CRIER",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM TOWN CRIER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805001", 16))),
                       transition_delay_ms=100,
                       run_once=True)
 
FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR SIR TYDUS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH SIR TYDUS WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING REWARD QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805007", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80DA01", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_necromancer.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000)          
                       
#NECROMANCER ROUTINE
FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR ARTEMIS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.verata_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.verata_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH ",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "INTERACTING WITH VERATA THE NECROMANCER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "INTERACTING WITH VERATA THE NECROMANCER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "TAKING REWARD VERATA THE NECROMANCER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80DA07", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "TAKING QUEST FROM VERATA THE NECROMANCER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805201", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="GOING TO KILL",
                       execute_fn=lambda: handle_map_path(FSM_vars.necromancer_quest_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.necromancer_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_necromancer.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_necromancer.AddState(name="RUNNIN OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR VAN",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.verata_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.verata_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH ARTEMIS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "INTERACTING WITH VERATA THE NECROMANCER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "INTERACTING WITH VERATA THE NECROMANCER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 NECROMANCER", "TAKING REWARD FROM VERATA THE NECROMANCER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805207", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

#END NECROMANCER ROUTINE

FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR ALTHEA",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804703", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="TAKING SKILL",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING SKILL LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804701", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="SECOND MAP PATH",
                       execute_fn=lambda: handle_map_path_early(FSM_vars.leveling_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_necromancer.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR PRINCE RURIK",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_necromancer.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM RURIK", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x802E01", 16))),
                       transition_delay_ms=100,
                       run_once=True)

#FSM LVL 1 - MESMER
FSM_vars.state_machine_mesmer.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ascalon_map,6,0)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="BONUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "CREATING BONUS ITEMS", Py4GW.Console.MessageType.Info),player_instance.SendChatCommand(text_bonus)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="EQUIP WAND",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING WAND", Py4GW.Console.MessageType.Info),equipitem(6508,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="EQUIP SHIELD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING SHIELD", Py4GW.Console.MessageType.Info),equipitem(6514,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR TOWN CRIER",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM TOWN CRIER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805001", 16))),
                       transition_delay_ms=100,
                       run_once=True)
 
FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR SIR TYDUS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH SIR TYDUS WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING REWARD QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805007", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80D901", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_mesmer.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000)  

#MESMER ROUTINE
FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR SEBEDOH",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.sebedoh_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sebedoh_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH ",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "INTERACTING WITH SEBEDOH THE MESMER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "INTERACTING WITH SEBEDOH THE MESMER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "TAKING REWARD SEBEDOH THE MESMER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80D907", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "TAKING QUEST FROM SEBEDOH THE MESMER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805101", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="GOING TO KILL",
                       execute_fn=lambda: handle_map_path(FSM_vars.mesmer_quest_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.mesmer_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_mesmer.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_mesmer.AddState(name="RUNNIN OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR VAN",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.sebedoh_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sebedoh_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH ARTEMIS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "INTERACTING WITH SEBEDOH THE MESMER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "INTERACTING WITH SEBEDOH THE MESMER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 MESMER", "TAKING REWARD FROM SEBEDOH THE MESMER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805107", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

#END MESMER ROUTINE

FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR ALTHEA",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804703", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="TAKING SKILL",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING SKILL LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804701", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="SECOND MAP PATH",
                       execute_fn=lambda: handle_map_path_mesmer(FSM_vars.leveling_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_mesmer.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR PRINCE RURIK",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_mesmer.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM RURIK", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x802E01", 16))),
                       transition_delay_ms=100,
                       run_once=True)

#FSM LVL 1 - ELEMENTALIST
FSM_vars.state_machine_elementalist.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ascalon_map,6,0)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="BONUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "CREATING BONUS ITEMS", Py4GW.Console.MessageType.Info),player_instance.SendChatCommand(text_bonus)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="EQUIP WAND",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING WAND", Py4GW.Console.MessageType.Info),equipitem(6508,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="EQUIP SHIELD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "EQUIPPING SHIELD", Py4GW.Console.MessageType.Info),equipitem(6514,agent_id)),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR TOWN CRIER",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM TOWN CRIER", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805001", 16))),
                       transition_delay_ms=100,
                       run_once=True)
 
FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR SIR TYDUS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH SIR TYDUS WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH SIR TYDUS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH TOWN CRIER WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING REWARD QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805007", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM SIR TYDUS", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80DB01", 16))),
                       transition_delay_ms=1500,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_elementalist.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000) 

#ELEMENTALIST ROUTINE

FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR SEBEDOH",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.howland_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.howland_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH ",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "INTERACTING WITH HOWLAND THE ELEMENTALIST WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "INTERACTING WITH HOWLAND THE ELEMENTALIST WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "TAKING REWARD HOWLAND THE ELEMENTALIST", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x80DB07", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "TAKING QUEST FROM HOWLAND THE ELEMENTALIST", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805301", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="GOING TO KILL",
                       execute_fn=lambda: handle_map_path(FSM_vars.elementalist_quest_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.elementalist_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_elementalist.AddState(name="LOOTING 1",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "INTERACTING WITH LOOT WITH NUMPAD1", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Numpad1.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="LOOTING 1",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "INTERACTING WITH LOOT WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=7000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="LOOTING 2",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "INTERACTING WITH LOOT WITH NUMPAD1", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Numpad1.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="LOOTING 2",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "INTERACTING WITH LOOT WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=7000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="LOOTING 3",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "INTERACTING WITH LOOT WITH NUMPAD1", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Numpad1.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="LOOTING 3",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "INTERACTING WITH LOOT WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=7000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_elementalist.AddState(name="RUNNIN OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR HOWLAND",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.howland_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.howland_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH ARTEMIS",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "INTERACTING WITH HOWLAND THE ELEMENTALIST WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "INTERACTING WITH HOWLAND THE ELEMENTALIST WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="TAKING REWARD",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1 ELEMENTALIST", "TAKING REWARD FROM HOWLAND THE ELEMENTALIST", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x805307", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

#END ELEMENTALIST ROUTINE

FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR ALTHEA",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH VAN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH LADY ALTHEA WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804703", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="TAKING SKILL",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING SKILL LADY ALTHEA", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x804701", 16))),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="USING IMP STONE",
                       execute_fn=lambda:(Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "USING IMP STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="SECOND MAP PATH",
                       execute_fn=lambda: handle_map_path_early(FSM_vars.leveling_pathing),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_elementalist.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.Travel(bot_vars.ascalon_map)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "WAITING FOR OUTPOST MAP", Py4GW.Console.MessageType.Info),Map.IsOutpost()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR PRINCE RURIK",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="INTERACTING WITH PRINCE RURIK",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "INTERACTING WITH PRINCE RURIK WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_elementalist.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 1", "TAKING QUEST FROM RURIK", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x802E01", 16))),
                       transition_delay_ms=100,
                       run_once=True)

#FSM LVL 2-10
FSM_vars.state_machine_lvl2_10.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_lvl2_10.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 2-10", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_lvl2_10.AddState(name="PAUSE BEFORE FOLLOWING",
                       execute_fn=lambda: FollowPathwithDelayTimer(FSM_vars.rurikpause_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.rurikpause_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False)

FSM_vars.state_machine_lvl2_10.AddState(name="MESSAGE",
                       execute_fn=lambda: Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 2-10", "GOING TO KILL SOME CHARRS", Py4GW.Console.MessageType.Info),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_lvl2_10.AddState(name="FOLLOWING RURIK",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.rurik_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.rurik_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False)

FSM_vars.state_machine_lvl2_10.AddState(name="WAITING RURIK KILLING",
                       execute_fn=lambda: set_killing_routine(),
                       exit_condition=lambda: end_killing_routine_1() or Survivor(),
                       run_once=False)

FSM_vars.state_machine_lvl2_10.AddState(name="LEAVING MAP",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 2-10", "GOING BACK TO ASCALON", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ascalon_map,6,0)),
                       exit_condition=lambda: Map.IsOutpost(),
                       run_once=True)

#FSM LVL 11-20
FSM_vars.state_machine_lvl11_20.AddState(name="ARE WE IN HOGWARTS?", 
                       execute_fn=lambda: Map.Travel(bot_vars.foible_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_lvl11_20.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False)

FSM_vars.state_machine_lvl11_20.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000)

FSM_vars.state_machine_lvl11_20.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_lvl11_20.AddState(name="LUCKILY THERE IS A PRIEST",
                       execute_fn=lambda: handle_map_path(FSM_vars.bandit_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.bandit_pathing, FSM_vars.movement_handler) or Map.IsMapLoading() or Survivor_Hamnet(),
                       run_once=False)

FSM_vars.state_machine_lvl11_20.AddState(name="FIRE IMP IS FIRING",
                       execute_fn=lambda: set_killing_routine(),
                       exit_condition=lambda: end_killing_routine() or Survivor_Hamnet(),
                       run_once=False)

#DULL CARAPACES
FSM_vars.state_machine_dull_carapaces.AddState(name="ASCALON", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - DULL CARAPACES FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ascalon_map,6,0)),  
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_dull_carapaces.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_dull_carapaces.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - DULL CARAPACES FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=1000)

FSM_vars.state_machine_dull_carapaces.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.dull_carapaces_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.dull_carapaces_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_dull_carapaces.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - DULL CARAPACES FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_dull_carapaces.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.dull_carapaces_pathing_2),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.dull_carapaces_pathing_2, FSM_vars.movement_handler),
                       run_once=False)

#GARGOYLE SKULLS
FSM_vars.state_machine_gargoyle_skulls.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - GARGOYLE SKULLS FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.barradin_map,6,0)),  
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - GARGOYLE SKULLS FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=1000)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - GARGOYLE SKULLS FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.greenhills_to_catacombs_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.greenhills_to_catacombs_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - GARGOYLE SKULLS FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=1000)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - GARGOYLE SKULLS FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.gargoyle_skulls_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.gargoyle_skulls_pathing, FSM_vars.movement_handler),
                       run_once=False)

#GRAWL NECKLACES
FSM_vars.state_machine_grawl_necklaces.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - GRAWL NECKLACES FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.barradin_map,6,0)),  
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_grawl_necklaces.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_grawl_necklaces.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GRAWL NECKLACES FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=000)

FSM_vars.state_machine_grawl_necklaces.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GRAWL NECKLACES FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_grawl_necklaces.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.grawl_necklaces_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.grawl_necklaces_pathing, FSM_vars.movement_handler),
                       run_once=False)

#ICY LODESTONES
FSM_vars.state_machine_icy_lodestones.AddState(name="ARE WE IN HOGWARTS?", 
                       execute_fn=lambda: Map.Travel(bot_vars.foible_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_icy_lodestones.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False)

FSM_vars.state_machine_icy_lodestones.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000)

FSM_vars.state_machine_icy_lodestones.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_icy_lodestones.AddState(name="LUCKILY THERE IS A PRIEST",
                       execute_fn=lambda: handle_map_path_loot(FSM_vars.icy_lodestones_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.icy_lodestones_pathing, FSM_vars.movement_handler),
                       run_once=False)


#ENCHANTED LODESTONES
FSM_vars.state_machine_lodestone.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - ENCHANTED LODESTONE FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.barradin_map,6,0)),  
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_lodestone.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_lodestone.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - ENCHANTED LODESTONE FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=000)

FSM_vars.state_machine_lodestone.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - ENCHANTED LODESTONE FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_lodestone.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.enchanted_lodestone_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.enchanted_lodestone_pathing, FSM_vars.movement_handler),
                       run_once=False)
#RED IRIS FLOWERS
FSM_vars.state_machine_red_iris_flowers.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ascalon_map,6,0)),                                             
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000)

FSM_vars.state_machine_red_iris_flowers.AddState(name="PATH 1",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.red_iris_flowers_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.red_iris_flowers_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Numpad1.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=11000,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="PATH 2",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.red_iris_flowers_pathing_2, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.red_iris_flowers_pathing_2, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Numpad1.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=11000,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="PATH 3",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.red_iris_flowers_pathing_3, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.red_iris_flowers_pathing_3, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Numpad1.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=11000,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="PATH 4",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.red_iris_flowers_pathing_4, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.red_iris_flowers_pathing_4, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Numpad1.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=11000,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="PATH 5",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.red_iris_flowers_pathing_5, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.red_iris_flowers_pathing_5, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Numpad1.value)),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=11000,
                       run_once=True)

#SKELETAL LIMBS
FSM_vars.state_machine_skele_limbs.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKELETAL LIMBS", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.barradin_map,6,0)),  
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_skele_limbs.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_skele_limbs.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKELETAL LIMBS", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=1000)

FSM_vars.state_machine_skele_limbs.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKELETAL LIMBS", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_skele_limbs.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.greenhills_to_catacombs_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.greenhills_to_catacombs_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False)

FSM_vars.state_machine_skele_limbs.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKELETAL LIMBS", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=1000)

FSM_vars.state_machine_skele_limbs.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKELETAL LIMBS", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_skele_limbs.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.skele_limbs_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.skele_limbs_pathing, FSM_vars.movement_handler),
                       run_once=False)

#ENCHANTED LODESTONES
FSM_vars.state_machine_skale_fin.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKALE FIN FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ranik_map,6,0)),  
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_skale_fin.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ranik_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranik_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_skale_fin.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKALE FIN FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=1000)

FSM_vars.state_machine_skale_fin.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKALE FIN FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_skale_fin.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.skale_fin_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.skale_fin_pathing, FSM_vars.movement_handler),
                       run_once=False)

#SPIDER LEGS
FSM_vars.state_machine_spider_leg.AddState(name="FORT RANIK", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SPIDER LEGS FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.ranik_map,6,0)),  
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_spider_leg.AddState(name="MESSAGE", 
                       execute_fn=lambda: Py4GW.Console.Log("TH3KUM1KO - SPIDER LEGS FARM", "GOING OUT", Py4GW.Console.MessageType.Info),  
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_spider_leg.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ranik_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranik_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_spider_leg.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - SPIDER LEGS FARM","WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=1000)

FSM_vars.state_machine_spider_leg.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SPIDER LEGS FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_spider_leg.AddState(name="MESSAGE", 
                       execute_fn=lambda: Py4GW.Console.Log("TH3KUM1KO - SPIDER LEGS FARM", "HUNTING SPIDERS", Py4GW.Console.MessageType.Info),  
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_spider_leg.AddState(name="FARMING SPIDER LEGS",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.spider_leg_pathing_1),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.spider_leg_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_spider_leg.AddState(name="INTERACTING WITH BASKET OF APPLES ",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SPIDER LEGS FARM", "INTERACTING WITH BASKET OF APPLES", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Numpad1.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_spider_leg.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: Keystroke.PressAndRelease(Key.Space.value),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_spider_leg.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SPIDER LEGS FARM", "DROPPING THE BASKET OF APPLES", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Numpad2.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_spider_leg.AddState(name="MESSAGE", 
                       execute_fn=lambda: Py4GW.Console.Log("TH3KUM1KO - SPIDER LEGS FARM", "HUNTING SPIDERS", Py4GW.Console.MessageType.Info),  
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_spider_leg.AddState(name="FARMING SPIDER LEGS",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.spider_leg_pathing_2),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.spider_leg_pathing_2, FSM_vars.movement_handler),
                       run_once=False)

#UNNATURAL SEEDS
FSM_vars.state_machine_unnatural_seeds.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - UNNATURAL SEEDS FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),Map.TravelToDistrict(bot_vars.barradin_map,6,0)),  
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_unnatural_seeds.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_unnatural_seeds.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO -  UNNATURAL SEEDS FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=3000)

FSM_vars.state_machine_unnatural_seeds.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  UNNATURAL SEEDS FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_unnatural_seeds.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.unnatural_seeds_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.unnatural_seeds_pathing, FSM_vars.movement_handler),
                       run_once=False)

#FSM TRAVEL TO ASHFORD ABBEY
FSM_vars.state_machine_abbey.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.ascalon_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_abbey.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.abbeyout_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.abbeyout_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False)

FSM_vars.state_machine_abbey.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000)

FSM_vars.state_machine_abbey.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_abbey.AddState(name="GOING TO FIND HOGWARTS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.abbey_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.abbey_pathing, FSM_vars.movement_handler) or Map.IsOutpost(),             
                       run_once=False)

FSM_vars.state_machine_abbey.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.ascalon_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

#FSM TRAVEL TO FOIBLE'S FAIR
FSM_vars.state_machine_foible.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.abbey_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_foible.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.foibleout_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foibleout_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_foible.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000)

FSM_vars.state_machine_foible.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_foible.AddState(name="GOING TO FIND HOGWARTS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_coordinate_list_one_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_coordinate_list_one_pathing, FSM_vars.movement_handler),             
                       run_once=False)

FSM_vars.state_machine_foible.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=3000)

FSM_vars.state_machine_foible.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_foible.AddState(name="GOING TO FIND HOGWARTS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_coordinate_list_two_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_coordinate_list_two_pathing, FSM_vars.movement_handler),           
                       run_once=False)

FSM_vars.state_machine_foible.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.abbey_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

#FSM TRAVEL TO FORT RANIK
FSM_vars.state_machine_ranik.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.abbey_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_ranik.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ranikout_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranikout_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_ranik.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000)

FSM_vars.state_machine_ranik.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_ranik.AddState(name="GOING TO FIND HOGWARTS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ranik_coordinate_list_one_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranik_coordinate_list_one_pathing, FSM_vars.movement_handler),             
                       run_once=False)

FSM_vars.state_machine_ranik.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=3000)

FSM_vars.state_machine_ranik.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_ranik.AddState(name="GOING TO FIND HOGWARTS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ranik_coordinate_list_two_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranik_coordinate_list_two_pathing, FSM_vars.movement_handler) or Map.IsOutpost(),           
                       run_once=False)

FSM_vars.state_machine_ranik.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.abbey_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

#FSM TRAVEL TO THE BARRADIN ESTATE
FSM_vars.state_machine_barradin.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.ascalon_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_barradin.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradinout_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradinout_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_barradin.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000)

FSM_vars.state_machine_barradin.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_barradin.AddState(name="GOING TO FIND THE DUKE",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler),             
                       run_once=False)

FSM_vars.state_machine_barradin.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=3000)

FSM_vars.state_machine_barradin.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_barradin.AddState(name="GOING TO FIND THE DUKE",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_two_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_two_pathing, FSM_vars.movement_handler) or Map.IsOutpost(),           
                       run_once=False)

FSM_vars.state_machine_barradin.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.ascalon_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

#THE GRAND TOUR
FSM_vars.state_machine_grandtour.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.ascalon_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_grandtour.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.abbeyout_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.abbeyout_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000)

FSM_vars.state_machine_grandtour.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="GOING TO FIND HOGWARTS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.abbey_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.abbey_pathing, FSM_vars.movement_handler) or Map.IsOutpost(),             
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.abbey_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_grandtour.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.foibleout_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foibleout_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000)

FSM_vars.state_machine_grandtour.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="GOING TO FIND HOGWARTS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_coordinate_list_one_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_coordinate_list_one_pathing, FSM_vars.movement_handler),             
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=3000)

FSM_vars.state_machine_grandtour.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="GOING TO FIND HOGWARTS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_coordinate_list_two_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_coordinate_list_two_pathing, FSM_vars.movement_handler),           
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.abbey_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_grandtour.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.abbey_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_grandtour.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ranikout_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranikout_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000)

FSM_vars.state_machine_grandtour.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="GOING TO FIND HOGWARTS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ranik_coordinate_list_one_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranik_coordinate_list_one_pathing, FSM_vars.movement_handler),             
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=3000)

FSM_vars.state_machine_grandtour.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="GOING TO FIND HOGWARTS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ranik_coordinate_list_two_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranik_coordinate_list_two_pathing, FSM_vars.movement_handler) or Map.IsOutpost(),           
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.abbey_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_grandtour.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.ascalon_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_grandtour.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradinout_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradinout_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000)

FSM_vars.state_machine_grandtour.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="GOING TO FIND THE DUKE",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler),             
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=3000)

FSM_vars.state_machine_grandtour.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="GOING TO FIND THE DUKE",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_two_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_two_pathing, FSM_vars.movement_handler) or Map.IsOutpost(),           
                       run_once=False)

FSM_vars.state_machine_grandtour.AddState(name="ARE WE IN HEAVEN?", 
                       execute_fn=lambda: Map.Travel(bot_vars.ascalon_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

def show_info_table():
    headers_info = ["INFO", "DATA"] 
    headers_items = ["ITEM", "QUANTITY"]

    agent_id = agent_id = Player.GetAgentID()
    level = Agent.GetLevel(agent_id) 
    experience = Player.GetExperience()

    max_level = 20  
    max_experience = 140000  

    data_info = [
        ("LEVEL", f"{level}/{max_level}"),
        ("EXPERIENCE", f"{experience}/{max_experience}"),
    ]

    item_data = [
        ("BAKED HUSKS", str(Inventory.GetModelCount(433))),  
        ("CHARR CARVINGS", str(Inventory.GetModelCount(423))),
        ("DULL CARAPACES", str(Inventory.GetModelCount(425))),
        ("ENCHANTED LODESTONES", str(Inventory.GetModelCount(431))),
        ("GARGOYLE SKULLS", str(Inventory.GetModelCount(426))),
        ("GRAWL NECKLACES", str(Inventory.GetModelCount(432))),
        ("ICY LODESTONES", str(Inventory.GetModelCount(424))),
        ("RED IRIS FLOWERS", str(Inventory.GetModelCount(2994))),
        ("SKALE FINS", str(Inventory.GetModelCount(429))),
        ("SKELETAL LIMBS", str(Inventory.GetModelCount(430))),
        ("SPIDER LEGS", str(Inventory.GetModelCount(422))),
        ("UNNATURAL SEEDS", str(Inventory.GetModelCount(428))),
        ("WORN BELTS", str(Inventory.GetModelCount(427))),
        ("GIFTS OF THE HUNTSMAN", str(Inventory.GetModelCount(31149))),
    ]

    ImGui.table("PLAYER INFO", headers_info, data_info)
    ImGui.table("ITEM INFO", headers_items, item_data)
    

#GUI
def DrawWindow():
    global module_name
    global state

    if PyImGui.begin("TH3KUM1KO'S LDoA"):
        if PyImGui.begin_tab_bar("MainTabBar"): 

            if PyImGui.begin_tab_item("LDoA"):
                state.radio_button_selected = PyImGui.radio_button(" \uf132 LEVEL 1 - WARRIOR", state.radio_button_selected, 20)
                state.radio_button_selected = PyImGui.radio_button(" \uf1bb LEVEL 1 - RANGER", state.radio_button_selected, 21)
                state.radio_button_selected = PyImGui.radio_button(" \uf644  LEVEL 1 - MONK", state.radio_button_selected, 22)
                state.radio_button_selected = PyImGui.radio_button(" \uf54c LEVEL 1 - NECROMANCER", state.radio_button_selected, 23)
                state.radio_button_selected = PyImGui.radio_button(" \ue2ca LEVEL 1 - MESMER", state.radio_button_selected, 24)
                state.radio_button_selected = PyImGui.radio_button(" \uf6e8 LEVEL 1 - ELEMENTALIST", state.radio_button_selected, 25)
                state.radio_button_selected = PyImGui.radio_button(" \uf443 LEVEL 2-10 - CHARR AT THE GATE", state.radio_button_selected, 0)
                state.radio_button_selected = PyImGui.radio_button(" \uf43f LEVEL 11-20 - FARMER HAMNET", state.radio_button_selected, 1) 

                if IsBotStarted():        
                    if PyImGui.button(" \uf04d   STOP"):
                        ResetEnvironment()
                        StopBot()
                else:
                    if PyImGui.button(" \uf04b   START"):
                        ResetEnvironment()
                        StartBot()

                PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("TRAVEL"):        
                state.radio_button_selected = PyImGui.radio_button("\uf51d GO TO ASHFORD ABBEY", state.radio_button_selected, 2)
                state.radio_button_selected = PyImGui.radio_button("\uf6e8 GO TO FOIBLE'S FAIR", state.radio_button_selected, 3)
                state.radio_button_selected = PyImGui.radio_button("\uf447 GO TO FORT RANIK", state.radio_button_selected, 4)
                state.radio_button_selected = PyImGui.radio_button(" \uf43a GO TO THE BARRADIN ESTATE", state.radio_button_selected, 5)
                state.radio_button_selected = PyImGui.radio_button("\uf5a0 THE GRAND TOUR", state.radio_button_selected, 19)

                if IsBotStarted():        
                    if PyImGui.button(" \uf04d   STOP"):
                        ResetEnvironment()
                        StopBot()
                else:
                    if PyImGui.button(" \uf04b   START"):
                        ResetEnvironment()
                        StartBot()

                PyImGui.end_tab_item()


        if PyImGui.begin_tab_item("NIC ITEMS"):                
               # state.radio_button_selected = PyImGui.radio_button("\ue599 BAKED HUSKS", state.radio_button_selected, 6)
               # state.radio_button_selected = PyImGui.radio_button("\uf1b0 CHARR CARVINGS", state.radio_button_selected, 7)
               state.radio_button_selected = PyImGui.radio_button("\uf188 DULL CARAPACES", state.radio_button_selected, 8)
               state.radio_button_selected = PyImGui.radio_button("\uf54c GARGOYLE SKULLS", state.radio_button_selected, 9)
               state.radio_button_selected = PyImGui.radio_button("\uf4d6 GRAWL NECKLACES", state.radio_button_selected, 10)
               state.radio_button_selected = PyImGui.radio_button("\uf7ad ICY LODESTONES", state.radio_button_selected, 11)
               state.radio_button_selected = PyImGui.radio_button("\uf3a5 ENCHANTED LODESTONES", state.radio_button_selected, 12)
               state.radio_button_selected = PyImGui.radio_button("\uf5bb RED IRIS FLOWERS", state.radio_button_selected, 13)
               state.radio_button_selected = PyImGui.radio_button("\uf5d7 SKELETAL LIMBS", state.radio_button_selected, 14)
               state.radio_button_selected = PyImGui.radio_button("\ue4f2 SKALE FINS", state.radio_button_selected, 15)
               state.radio_button_selected = PyImGui.radio_button("\uf717 SPIDER LEGS", state.radio_button_selected, 16)
               state.radio_button_selected = PyImGui.radio_button("\uf4d8 UNNATURAL SEEDS", state.radio_button_selected, 17)
               # state.radio_button_selected = PyImGui.radio_button("\ue19b WORN BELTS", state.radio_button_selected, 18)
               if IsBotStarted():        
                    if PyImGui.button(" \uf04d   STOP"):
                        ResetEnvironment()
                        StopBot()
               else:
                    if PyImGui.button(" \uf04b   START"):
                        ResetEnvironment()
                        StartBot()

               PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("STATS"):
               
               show_info_table()

        PyImGui.spacing()


        
    PyImGui.end()

def main():
    global bot_vars,FSM_vars
    try:
        DrawWindow()

        if IsBotStarted():
            
            # LEVEL 2-10
            if state.radio_button_selected == 0:  
                if FSM_vars.state_machine_lvl2_10.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_lvl2_10.update()

            #LEVEL 1 - WARRIOR
            elif state.radio_button_selected == 20:  
                if FSM_vars.state_machine_warrior.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_warrior.update()

            #LEVEL 1 - RANGER
            elif state.radio_button_selected == 21:  
                if FSM_vars.state_machine_ranger.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_ranger.update()   
                    
            #LEVEL 1 - MONK
            elif state.radio_button_selected == 22:  
                if FSM_vars.state_machine_monk.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_monk.update()   

            #LEVEL 1 - NECROMANCER
            elif state.radio_button_selected == 23:  
                if FSM_vars.state_machine_necromancer.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_necromancer.update()   

            #LEVEL 1 - MESMER
            elif state.radio_button_selected == 24:  
                if FSM_vars.state_machine_mesmer.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_mesmer.update() 

            #LEVEL 1 - MESMER
            elif state.radio_button_selected == 25:  
                if FSM_vars.state_machine_elementalist.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_elementalist.update() 

            # LEVEL 11-20       
            elif state.radio_button_selected == 1:  
                if FSM_vars.state_machine_lvl11_20.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_lvl11_20.update()
                    
            # ASHFORD'S ABBEY TRAVEL      
            elif state.radio_button_selected == 2:  
                if FSM_vars.state_machine_abbey.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_abbey.update()

            # FOIBLE'S FAIR TRAVEL      
            elif state.radio_button_selected == 3:  
                if FSM_vars.state_machine_foible.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_foible.update()
                    
            # FORT RANIK TRAVEL      
            elif state.radio_button_selected == 4:  
                if FSM_vars.state_machine_ranik.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_ranik.update()
                    
            # THE BARRADIN ESTATE TRAVEL      
            elif state.radio_button_selected == 5:  
                if FSM_vars.state_machine_barradin.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_barradin.update()
                    
            # THE GRAND TOUR     
            elif state.radio_button_selected == 19:  
                if FSM_vars.state_machine_grandtour.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_grandtour.update()

            # DULL CARAPACES    
            elif state.radio_button_selected == 8:  
                if FSM_vars.state_machine_dull_carapaces.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_dull_carapaces.update()

            # GARGOYLE SKULLS   
            elif state.radio_button_selected == 9:  
                if FSM_vars.state_machine_gargoyle_skulls.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_gargoyle_skulls.update()

            # GARGOYLE SKULLS   
            elif state.radio_button_selected == 10:  
                if FSM_vars.state_machine_grawl_necklaces.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_grawl_necklaces.update()

            # GARGOYLE SKULLS   
            elif state.radio_button_selected == 11:  
                if FSM_vars.state_machine_icy_lodestones.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_icy_lodestones.update()

            # ENCHANTED LODESTONES     
            elif state.radio_button_selected == 12:  
                if FSM_vars.state_machine_lodestone.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_lodestone.update()

            # ENCHANTED LODESTONES     
            elif state.radio_button_selected == 13:  
                if FSM_vars.state_machine_red_iris_flowers.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_red_iris_flowers.update()

            # SKELE LIMBS     
            elif state.radio_button_selected == 14:  
                if FSM_vars.state_machine_skele_limbs.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_skele_limbs.update()

            # SKALE FINS     
            elif state.radio_button_selected == 15:  
                if FSM_vars.state_machine_skale_fin.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_skale_fin.update()

            # SPIDER LEGS    
            elif state.radio_button_selected == 16:  
                if FSM_vars.state_machine_spider_leg.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_spider_leg.update()

            # UNNATURAL SEEDS  
            elif state.radio_button_selected == 17:  
                if FSM_vars.state_machine_unnatural_seeds.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_unnatural_seeds.update()


    except ImportError as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == "__main__":
    main()

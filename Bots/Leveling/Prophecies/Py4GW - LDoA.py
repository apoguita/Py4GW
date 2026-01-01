from Py4GWCoreLib import*
import time
import traceback
from Py4GWCoreLib import Key


#VARIABLES
module_name = "Py4GW - LDoA"
window_name = module_name

# Original combat system - no smart combat handler

class AppState :
    def __init__(self) :
        self.radio_button_selected = 39

state = AppState()

class BotVars:
    def __init__(self, map_id=0):
        self.ascalon_map = 148 #ASCALON
        self.foible_map = 165 #FOIBLE
        self.abbey_map = 164 #ABBEY  
        self.barradin_map = 163 #BARRADIN ESTATE
        self.ranik_map = 166 #FORT RANIK
        self.bot_started = False
        self.window_module = ImGui.WindowModule()
        self.variables = {}
        self.CharrAtTheGate = 46

follow_delay_timer = Timer()
loot_timer = Timer() 
start_time = time.time()  
run_counter = 0  

class GameAreas:
    def __init__(self):
        self.Area = 1600 
        self.Area_1 = 2000
        self.Area_2 = 2500

ModelData = {}
text_input = "resign"
text_bonus = "bonus"
text_dialog = "dialog take"
area_distance = GameAreas()
PyPlayer.PyPlayer()
player_instance = PyPlayer.PyPlayer()
action_queue = ActionQueue()

bot_vars = BotVars(map_id=148) #ASCALON
bot_vars.window_module = ImGui.WindowModule(module_name, window_name, (300, 300), (0, 0), PyImGui.WindowFlags.AlwaysAutoResize)
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
monk_quest_coordinate_list_1 = [(4832, -54),(5948, -2922),(6710, -3284),(5894, -4254),(4011, -2569),(3886, -4384)]
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
skele_limbs_coordinate_list = [(-7439, 13679), (-4499, 10305), (-4468, 8420), (-6126, 8229), (-7305, 9075), (-8043, 9784), (-9305, 10684), (-11632, 10827), (-12712, 9802), (-13320, 9242), (-13514, 7688), (-13335, 6960), (-12263, 5545), (-11292, 5096), (-9862, 4795), (-8895, 5093), (-8260, 5806), (-7267, 6571)]

#SKALE FIN
skale_fin_coordinate_list = [(22578, 6846),(22323, 4048),(21443, 1909),(18033, 2908),(16335, 3362),(15881, 7289),(16861, 6427),(15501, 2865),(13711, 2461),(13511, 1802),(15186, 39),(17397, 903),(19531, 946)]  

#SPIDER LEGS
ranik_goingtofarm_coordinate_list = [(22858, 10512),(22554, 8048),(22529, 7569),(22527, 7450)]
spider_leg_coordinate_list_1 = [(22532, 5576),(21978, 3604),(19968, 1388),(18462, -1529),(18444, -3023),(19911, -5170),(20548, -6388),(21722, -7002)]
spider_leg_coordinate_list_2 = [(21072, -6376),(19635, -4807),(17780, -3376),(16003, -5076),(15449, -8006),(17323, -11240),(18931, -12260),(19979, -12162),(21141, -12814),(21915, -12167),(21007, -11370),(18961, -12306),(17074, -10430),(14527, -10426),(12768, -10614),(10277, -11768),(8869, -11638),(8172, -12088),(7111, -12836),(4879, -13254),(2820, -12874),(1823, -12239),(637, -11093),(-190, -10429),(2104, -10838),(3435, -8681),(5221, -5253),(5163, -3186),(5661, -2630),(7170, -3541),(7845, -8356),(9010, -9787),(7856, -10328)]

#UNNATURAL SEEDS
unnatural_seeds_coordinate_list = [(-7910, 1418),(-7555, -1752),(-8062, -3071),(-12424, -3125),(-10948, -5876),(-8324, -8323),(-13903, -2822),(-14847, -707),(-15180, 2976),(-16849, 70448),(-20397, 8233),(-20550, 6263),(-20964, 3164),(-18933, 3676),(-17504, 3399),(-20758, -1853),(-20250, -5231),(-19147, -6511),(-16715, -7669),(-16317, -9650),(-16739, -11548),(-12792, -14235),(-15378, -15096)]

#WORN BELTS
worn_belts_coordinate_list = [(-7926, 1415),(-11055, 1227),(-12315, -2885),(-14281, -2275),(-15024, 1351),(-16472, 6562),(-18774, 8704),(-20803, 9038),(-20203, 7347),(-19635, 5800),(-18700, 2386),(-20420, 1201),(-21388, -174),(-18041, -1241),(-18791, -3534),(-20430, -6529),(-17984, -6975),(-21071, -8679),(-17327, -10461),(-16030, -11243),(-16017, -14750),(-14710, -15286),(-11258, -14416),(-10075, -14528),(-7392, -12948),(-5987, -15648),(-10315, -14775),(-14548, -13886),(-17675, -12879),(-18913, -11854),(-20070, -13160),(-20386, -14388),(-22363, -15209),(-22475, -12587)]

#BAKED HUSKS
baked_husk_coordinate_list = [(-10220, -5000), (-10507, -3583), (-10813, -1725), (-11045, -485), (-6711, -1690)]
baked_husk_location_1 = [(-10220, -5000)]
baked_husk_location_2 = [(-10507, -3583)]
baked_husk_location_3 = [(-10813, -1725)]
baked_husk_location_4 = [(-11045, -485)]
baked_husk_location_5 = [(-9467, 673)]
baked_husk_location_6 = [(-6711, -1690)]

#NICHOLAS GIFTS
nicholas_sandford_coordinate_list = [(22237, 4061),(17213, 2817),(16320, 3621),(16757, 8255),(17315, 8812),(14385, 11414),(14159, 13931),(15257, 16442)]

#LVL 2-10
ascalon_coordinate_list = [(7420, 5450)]
rurikpause_coordinate_list = [(5987, 4087),(5977, 4077)]
rurik_coordinate_list = [(6068, 4180),(5835, 4323),(5602, 4493),(5371, 4672),(5147, 4858),(4933, 5058),(4721, 5255),(4504, 5446),(4283, 5637),(4068, 5825),(3845, 6010),(3577, 6131),(3299, 6199),(3012, 6249),(2720, 6290),(2438, 6324),(2147, 6362),(1860, 6416),(1575, 6433),(1284, 6437),(995, 6441),(702, 6477),(428, 6576),(208, 6759),(-7, 6959),(-221, 7157),(-437, 7358),(-649, 7555),(-861, 7751),(-1080, 7944),(-1301, 8129),(-1522, 8312),(-1750, 8496),(-1997, 8641),(-2260, 8776),(-2519, 8910),(-2753, 9078),(-2902, 9324),(-3020, 9584),(-3137, 9847),(-3252, 10115),(-3367, 10386),(-3486, 10655),(-3724, 10822),(-3981, 10957),(-4241, 11095),(-4483, 11222),(-3823, 11060),(-5253, 11672)]

#TAME PET
goingout_ashfordabbey = [(-11962, -6244),(-11445, -6239),(-11400, -6273)]
tamepet_coordinate_list_1 = [(-6395, -7016),(-4560, -12326),(1040, -16292),(4070, -19779),(4200, -19700)]
tamepet_coordinate_list_2 = [(-15573, 14259),(-17445, 11742),(-17017, 10411)]
tamepet_coordinate_list_3 = [(-17263, 10142),(-18774, 8436),(-20164, 6922),(-19424, 4220),(-14998, -475)]

#WARRIOR REQ
warrior_skill_coordinate_list_1 = [(21932, 12966),(21258, 13066)]
warrior_skill_coordinate_list_2 = [(-6407, 1383),(-6475, 1551)]
warrior_skill_coordinate_list_3 = [(-6670, 1402),(-6781, 1231)]

#RANGER REQ
ranger_skill_coordinate_list_1 = [(-13152, 1449),(-10295, 3989),(-6644, 5097),(-4889, 5031),(-4455, 5902)]
ranger_skill_coordinate_list_2 = [(1618, 7084),(2605, 9654),(4034, 10546),(7977, 9735),(11355, 6369),(11250, 2739),(11274, -2882),(13194, -7177),(12257, -10820),(13254, -15838),(16327, -17666)]
ranger_skill_coordinate_list_3 = [(17195, -17559),(18077, -17350)]

#MONK REQ
monk_skill_coordinate_list_1 = [(-12786, -6952),(-12209, -8014)]
monk_skill_coordinate_list_2 = [(20844, 13667),(19248, 13103),(17793, 12599)]

#NECRO REQ
necro_skill_coordinate_list_1 = [(-13247, -7111),(-13610, -7095),(-13900, -7075)]
necro_skill_coordinate_list_2 = [(13776, 2598),(13775, 3515)]
necro_skill_coordinate_list_3 = [(13755, 2156),(13580, -344),(10919, -230),(10595, -123),(9375, -1084),(9621, -4537),(7041, -5399),(7163, -7846),(5923, -8610),(3219, -9292),(1139, -8041),(-190, -9648),(-1397, -11243),(-3260, -9333),(-3905, -8209),(-8007, -7860),(-7836, -5523),(-6484, -3899),(-7420, -2054),(-10793, -1681),(-10772, 4092)]
necro_skill_coordinate_list_4 = [(20635, 13722),(19086, 12838),(17482, 12210)]


#CHARR GATE OPENER
# Coordinates for just opening the gate and reaching The Northlands
charr_gate_opener_coordinate_list_1 = [(6602, 4485)]
charr_gate_opener_coordinate_list_2 = [(3220, 6900),(-1681, 11876),(-5475, 12865)]
charr_gate_opener_fast_gate_run = [(-5390, 12810), (-5258, 12851), (-5448, 12353), (-5575, 13600), (-5535, 13800)]

# Town exit coordinates for spawn points too far from exit
ascalon_town_exit_coordinate_list = [(7465, 5461)]  # Move closer to exit before pressing R


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
    global bot_vars, start_time
    bot_vars.bot_started = True
    start_time = time.time()  

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
    FSM_vars.ascalon_pathing.reset()
    FSM_vars.ascalon_pathing_1.reset()

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

    #WORN BELTS
    FSM_vars.state_machine_worn_belts.reset()
    FSM_vars.worn_belts_pathing.reset()  

    #BAKED HUSKS
    FSM_vars.state_machine_baked_husks.reset()
    FSM_vars.baked_husk_pathing.reset()

    
    #CHARR GATE OPENER
    FSM_vars.state_machine_charr_gate_opener.reset()
    FSM_vars.charr_gate_opener_pathing_1.reset()
    FSM_vars.charr_gate_opener_pathing_2.reset()
    FSM_vars.ascalon_town_exit_pathing.reset()
    FSM_vars.charr_gate_opener_fast_gate_run.reset()


    #NICHOLAS SANDFORD
    FSM_vars.state_machine_nicholas_sandford.reset()
    FSM_vars.nicholas_sandford_pathing.reset()   

    #TAME PET
    FSM_vars.state_machine_TamePet.reset()
    FSM_vars.goingout_ashfordabbey.reset()
    FSM_vars.tamepet_pathing_1.reset()
    FSM_vars.tamepet_pathing_2.reset()
    FSM_vars.tamepet_pathing_3.reset()

    #WARRIOR REQ
    FSM_vars.state_machine_warrior_req.reset()
    FSM_vars.warrior_skill_pathing_1.reset()
    FSM_vars.warrior_skill_pathing_2.reset()
    FSM_vars.warrior_skill_pathing_3.reset()

    #WARRIOR NO REQ
    FSM_vars.state_machine_warrior_noreq.reset()

    #RANGER REQ
    FSM_vars.state_machine_ranger_req.reset()
    FSM_vars.ranger_skill_pathing_1.reset()
    FSM_vars.ranger_skill_pathing_2.reset()
    FSM_vars.ranger_skill_pathing_3.reset()

    #RANGER NO REQ
    FSM_vars.state_machine_ranger_noreq.reset()

    #MONK REQ
    FSM_vars.state_machine_monk_req.reset()
    FSM_vars.monk_skill_pathing_1.reset()
    FSM_vars.monk_skill_pathing_2.reset()

    #RANGER NO REQ
    FSM_vars.state_machine_monk_noreq.reset()

    #NECRO REQ
    FSM_vars.state_machine_necro_req.reset()
    FSM_vars.necro_skill_pathing_1.reset()
    FSM_vars.necro_skill_pathing_2.reset()
    FSM_vars.necro_skill_pathing_3.reset()

    #NECRO NO REQ
    FSM_vars.state_machine_necro_noreq.reset()



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
    FSM_vars.state_machine_ResetQuest.reset()
    FSM_vars.state_machine_lvl11_20.reset()
    FSM_vars.state_machine_abbey.reset()
    FSM_vars.state_machine_foible.reset()
    FSM_vars.state_machine_ranik.reset()
    FSM_vars.state_machine_barradin.reset()
    FSM_vars.state_machine_grandtour.reset()
    FSM_vars.movement_handler.reset()

def LDoA_GetPetBehavior(player_id=Player.GetAgentID()):
    PetInfo = Party.Pets.GetPetInfo(player_id)
    return PetInfo.behavior

def LDoA_IsOutpost():
    map_id = Map.GetMapID()
    """Check if the map instance is an outpost."""
    if map_id == bot_vars.ascalon_map: #ASCALON
        return True
    if map_id == bot_vars.foible_map: #FOIBLE
        return True
    if map_id == bot_vars.abbey_map: #ABBEY
        return True
    if map_id == bot_vars.barradin_map: #BARRADIN ESTATE
        return True
    if map_id == bot_vars.ranik_map: #FORT RANIK
        return True
    return False

def LDoA_TravelToOutpost(map_id=148):
    if not Map.GetMapID() == map_id:
        Map.Travel(map_id)

def LDoA_TravelToDistrict(map_id=148, district=0, district_number=0):
    if not Map.GetMapID() == map_id:
        if not Map.GetDistrict() == district:
            #Map.TravelToDistrict(map_id, district, district_number)
            Map.TravelToRegion(map_id, district, district_number)

#ITEMS FUNCTIONS   
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

def GetFirstFromArray(array):
    if array is None:
        return 0
    
    if len(array) > 0:
        return array[0]
    return 0

def TargetNearestItem():
    distance = Range.Spellcast.value
    item_array = AgentArray.GetItemArray()
    item_array = AgentArray.Filter.ByDistance(item_array, Player.GetXY(), distance)
    item_array = AgentArray.Sort.ByDistance(item_array, Player.GetXY())
    return GetFirstFromArray(item_array)

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
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (player_x, player_y))

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
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), area_distance.Area_2)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (player_x, player_y))

    if len(enemy_array) < 2:
        FSM_vars.in_waiting_routine = False
        FSM_vars.in_killing_routine = False
        return True

    return False

#SURVIVOR FUNCTION TO AVOID DEAD, SET YOUR THRESHOLD AS YOU WISH
def Survivor():
    try:
        # Check if game is ready before accessing health data
        if not Map.IsMapReady() or Player.GetAgentID() <= 0:
            return False
            
        max_health = Agent.GetMaxHealth(Player.GetAgentID())
        if max_health <= 0:
            return False  # Can't calculate health percentage if max health is 0 or negative
        current_health = Agent.GetHealth(Player.GetAgentID()) * max_health
        current_health_pct = current_health / max_health * 100
        
        if current_health_pct < 45:
            return True  
        return False
    except Exception as e:
        # If there's any error getting health info, assume we're not in danger
        return False 

def Death():
    try:
        # Check if game is ready before accessing health data
        if not Map.IsMapReady() or Player.GetAgentID() <= 0:
            return False
            
        max_health = Agent.GetMaxHealth(Player.GetAgentID())
        if max_health <= 0:
            return False  # Can't calculate health if max health is 0 or negative
        current_health = Agent.GetHealth(Player.GetAgentID()) * max_health
        
        if current_health < 1:
            return True  
        return False
    except Exception as e:
        # If there's any error getting health info, assume we're not dead
        return False 

def Survivor_Hamnet():
    try:
        # Check if game is ready before accessing health data
        if not Map.IsMapReady() or Player.GetAgentID() <= 0:
            return False
            
        max_health = Agent.GetMaxHealth(Player.GetAgentID())
        if max_health <= 0:
            return False  # Can't calculate health percentage if max health is 0 or negative
        current_health = Agent.GetHealth(Player.GetAgentID()) * max_health
        current_health_pct = current_health / max_health * 100
        
        if current_health_pct < 45:
            return True  
        return False
    except Exception as e:
        # If there's any error getting health info, assume we're not in danger
        return False 

#FIGHT FUNCTIONS
def get_called_target():
    """Get the first called target from party members, if it's alive."""
    players = Party.GetPlayers()
    for player in players:
        if player.called_target_id != 0:
            if Agent.IsAlive(player.called_target_id):
                return player.called_target_id
    return 0

def GetAbsoluteEnergy():
    my_id = Player.GetAgentID()
    max_energy = Agent.GetMaxEnergy(my_id) 
    current_energy = Agent.GetEnergy(my_id) * max_energy  
    return current_energy

def IsSkillReady2(slot):
    skill_id = SkillBar.GetSkillIDBySlot(slot)

    if not skill_id or skill_id == 0:
        return False  

    recharge_time = Skill.Data.GetRecharge(skill_id) or 0
    if recharge_time > 0:
        return False 

    energy_cost = Skill.Data.GetEnergyCost(skill_id) or 0
    if GetAbsoluteEnergy() < energy_cost:
        return False  

    return True  


#STANDARD
def handle_map_path(map_pathing):
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    my_p_prof, my_s_prof = Agent.GetProfessionIDs(my_id)
    current_time = time.time()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1150)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (my_x, my_y))

    if not enemy_array:
        FSM_vars.current_target_id = None
        FSM_vars.last_target_id = None
        FSM_vars.has_interacted = False 
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)  
        return

    if FSM_vars.current_target_id is None or not Agent.IsAlive(FSM_vars.current_target_id) or not FSM_vars.current_target_id == FSM_vars.last_target_id:
        FSM_vars.current_target_id = enemy_array[0]  
        FSM_vars.has_interacted = False  

    if FSM_vars.current_target_id:
        target_id = FSM_vars.current_target_id
        target_x, target_y = Agent.GetXY(target_id)
        distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5

        if not FSM_vars.has_interacted:
            if my_p_prof == Profession.Ranger.value or my_s_prof == Profession.Ranger.value:
                Party.Pets.SetPetBehavior(0, target_id)
            Player.Interact(target_id, call_target=False)
            FSM_vars.last_target_id = target_id
            FSM_vars.has_interacted = True  
        
        if Agent.IsAlive(target_id):
            if current_time - FSM_vars.last_skill_time >= 2.0:
                skill_slot = FSM_vars.current_skill_index
                Player.ChangeTarget(target_id)
                Player.Interact(target_id, call_target=False)                 
                SkillBar.UseSkill(skill_slot)  
                FSM_vars.last_skill_time = current_time  
                FSM_vars.current_skill_index = (skill_slot % 8) + 1  

            return 

def handle_loot():
    """
    Function to handle the looting logic separately from the main map handling.
    """
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    item_distance = 1200

    item_array = AgentArray.GetItemArray()
    item_array = AgentArray.Filter.ByDistance(item_array, (my_x, my_y), item_distance)

    agent_to_item_map = {
        agent_id: Agent.GetItemAgentItemID(agent_id)
        for agent_id in item_array
    }

    filtered_items = list(agent_to_item_map.values())
    filtered_items = ItemArray.Filter.ByCondition(
        filtered_items, lambda item_id: Item.GetItemType(item_id)[0] in {30, 10, 20, 9}
    )

    filtered_agent_ids = [
        agent_id for agent_id, item_id in agent_to_item_map.items()
        if item_id in filtered_items
    ]

    filtered_agent_ids = AgentArray.Sort.ByDistance(filtered_agent_ids, Agent.GetXY(my_id))

    if len(filtered_agent_ids) > 0:
        looting_item = filtered_agent_ids[0]

        if Player.GetTargetID() != looting_item:
            Player.ChangeTarget(looting_item)
            loot_timer.Reset()
            return

        if loot_timer.HasElapsed(1200) and Player.GetTargetID() == looting_item:
            Keystroke.PressAndRelease(Key.Space.value)
            loot_timer.Reset()
            return

def handle_lootFlower():
    """
    Function to handle the looting logic separately from the main map handling.
    """
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    item_distance = 2500

    item_array = AgentArray.GetItemArray()
    item_array = AgentArray.Filter.ByDistance(item_array, (my_x, my_y), item_distance)

    agent_to_item_map = {
        agent_id: Agent.GetItemAgentItemID(agent_id)
        for agent_id in item_array
    }

    filtered_items = list(agent_to_item_map.values())
    filtered_items = ItemArray.Filter.ByCondition(
        filtered_items, lambda item_id: Item.GetItemType(item_id)[0] in {30, 10, 20, 9}
    )

    filtered_agent_ids = [
        agent_id for agent_id, item_id in agent_to_item_map.items()
        if item_id in filtered_items
    ]

    filtered_agent_ids = AgentArray.Sort.ByDistance(filtered_agent_ids, Agent.GetXY(my_id))

    if len(filtered_agent_ids) > 0:
        looting_item = filtered_agent_ids[0]

        if Player.GetTargetID() != looting_item:
            Player.ChangeTarget(looting_item)
            loot_timer.Reset()
            return

        if loot_timer.HasElapsed(1200) and Player.GetTargetID() == looting_item:
            Keystroke.PressAndRelease(Key.Space.value)
            loot_timer.Reset()
            return

def handle_map_path_loot(map_pathing):
    """
    Main function to handle combat, loot, and movement separately.
    """
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    my_p_prof, my_s_prof = Agent.GetProfessionIDs(my_id)
    current_time = time.time()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1200)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (my_x, my_y))

    if not enemy_array:
        FSM_vars.current_target_id = None
        FSM_vars.last_target_id = None
        FSM_vars.has_interacted = False 
        handle_loot()  
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)  
        return

    if FSM_vars.current_target_id is None or not Agent.IsAlive(FSM_vars.current_target_id) or not FSM_vars.current_target_id == FSM_vars.last_target_id:
        FSM_vars.current_target_id = enemy_array[0]  
        FSM_vars.has_interacted = False  

    if FSM_vars.current_target_id:
        target_id = FSM_vars.current_target_id
        target_x, target_y = Agent.GetXY(target_id)
        distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5

        if not FSM_vars.has_interacted:
            if my_p_prof == Profession.Ranger.value or my_s_prof == Profession.Ranger.value:
                Party.Pets.SetPetBehavior(0, target_id)
            Player.Interact(target_id, call_target=False)
            FSM_vars.has_interacted = True  
        
        if Agent.IsAlive(target_id):
            if current_time - FSM_vars.last_skill_time >= 2.0:
                skill_slot = FSM_vars.current_skill_index
                Player.ChangeTarget(target_id)
                Player.Interact(target_id, call_target=False)                 
                SkillBar.UseSkill(skill_slot)  
                FSM_vars.last_skill_time = current_time  
                FSM_vars.current_skill_index = (skill_slot % 8) + 1  

            return 

def handle_map_path_Red_Iris_Flower(map_pathing):
    """
    Main function to handle combat, loot, and movement separately.
    """
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    my_p_prof, my_s_prof = Agent.GetProfessionIDs(my_id)
    current_time = time.time()
    enemy_distance = 1500

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), enemy_distance)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAgressive')
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (my_x, my_y))

    if not enemy_array:
        FSM_vars.current_target_id = None
        FSM_vars.last_target_id = None
        FSM_vars.has_interacted = False 
        handle_lootFlower()  
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)  
        return

 
    if FSM_vars.current_target_id is None or not Agent.IsAlive(FSM_vars.current_target_id) or not FSM_vars.current_target_id == FSM_vars.last_target_id:
        FSM_vars.current_target_id = enemy_array[0]  
        FSM_vars.has_interacted = False  

    if FSM_vars.current_target_id:
        target_id = FSM_vars.current_target_id
        target_x, target_y = Agent.GetXY(target_id)
        distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5

        if not FSM_vars.has_interacted:
            if my_p_prof == Profession.Ranger.value or my_s_prof == Profession.Ranger.value:
                Party.Pets.SetPetBehavior(0, target_id)
            Player.Interact(target_id, call_target=False)
            FSM_vars.last_target_id = target_id
            FSM_vars.has_interacted = True  
        
        if Agent.IsAlive(target_id):
            if current_time - FSM_vars.last_skill_time >= 2.0:
                skill_slot = FSM_vars.current_skill_index
                Player.ChangeTarget(target_id)
                Player.Interact(target_id, call_target=False)                 
                SkillBar.UseSkill(skill_slot)  
                FSM_vars.last_skill_time = current_time  
                FSM_vars.current_skill_index = (skill_slot % 8) + 1  

            return 

#FOR WARRIOR LVL 1
def warrior_handle_map_path(map_pathing):
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    my_p_prof, my_s_prof = Agent.GetProfessionIDs(my_id)
    current_time = time.time()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1200)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (my_x, my_y))

    if not enemy_array:
        FSM_vars.current_target_id = None
        FSM_vars.last_target_id = None
        FSM_vars.has_interacted = False 
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)  
        return

    if FSM_vars.current_target_id is None or not Agent.IsAlive(FSM_vars.current_target_id) or not FSM_vars.current_target_id == FSM_vars.last_target_id:
        FSM_vars.current_target_id = enemy_array[0]  
        FSM_vars.has_interacted = False  

    if FSM_vars.current_target_id:
        target_id = FSM_vars.current_target_id
        target_x, target_y = Agent.GetXY(target_id)
        distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5

        if not FSM_vars.has_interacted:
            if my_p_prof == Profession.Ranger.value or my_s_prof == Profession.Ranger.value:
                Party.Pets.SetPetBehavior(0, target_id)
            Player.Interact(target_id, call_target=False)
            FSM_vars.last_target_id = target_id
            FSM_vars.has_interacted = True  
        
        if Agent.IsAlive(target_id):
            if current_time - FSM_vars.last_skill_time >= 2.0:
                skill_slot = FSM_vars.current_skill_index
                Player.ChangeTarget(target_id)
                Player.Interact(target_id, call_target=False)                 
                SkillBar.UseSkill(skill_slot)  
                FSM_vars.last_skill_time = current_time  

                FSM_vars.current_skill_index = 2 if skill_slot >= 8 else skill_slot + 1  

            return


#FOR MESMER LVL 1
def mesmer_handle_map_path(map_pathing):

    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    my_p_prof, my_s_prof = Agent.GetProfessionIDs(my_id)
    current_time = time.time()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1200)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (my_x, my_y))

    if not enemy_array:
        FSM_vars.current_target_id = None
        FSM_vars.last_target_id = None
        FSM_vars.has_interacted = False 
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)  
        return

    if FSM_vars.current_target_id is None or not Agent.IsAlive(FSM_vars.current_target_id) or not FSM_vars.current_target_id == FSM_vars.last_target_id:
        FSM_vars.current_target_id = enemy_array[0]  
        FSM_vars.has_interacted = False  

    if FSM_vars.current_target_id:
        target_id = FSM_vars.current_target_id
        target_x, target_y = Agent.GetXY(target_id)
        distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5

        if not FSM_vars.has_interacted:
            if my_p_prof == Profession.Ranger.value or my_s_prof == Profession.Ranger.value:
                Party.Pets.SetPetBehavior(0, target_id)
            Player.Interact(target_id, call_target=False)
            FSM_vars.last_target_id = target_id
            FSM_vars.has_interacted = True  
        
        if Agent.IsAlive(target_id):
            if current_time - FSM_vars.last_skill_time >= 2.0:
                skill_slot = FSM_vars.current_skill_index
                Player.ChangeTarget(target_id)
                Player.Interact(target_id, call_target=False)                 
                SkillBar.UseSkill(skill_slot)  
                FSM_vars.last_skill_time = current_time  

                FSM_vars.current_skill_index = 1 if skill_slot >= 3 else skill_slot + 1  

            return  
    else:
        Party.Pets.SetPetBehavior(1, my_id)
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)


#FOR EVERYONE LVL 1
def early_handle_map_path(map_pathing):
    global FSM_vars
    FSM_vars.PetBehavior = LDoA_GetPetBehavior()
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    my_p_prof, my_s_prof = Agent.GetProfessionIDs(my_id)
    current_time = time.time()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1150)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (my_x, my_y))

    if not enemy_array:
        FSM_vars.current_target_id = None
        FSM_vars.last_target_id = None
        if my_p_prof == 2 or my_s_prof == 2:
            if not FSM_vars.PetBehavior == 1:
                FSM_vars.PetBehavior = 1 #0=Fight, 1=Guard, 2=Avoid
            Party.Pets.SetPetBehavior(FSM_vars.PetBehavior, my_id)
        FSM_vars.has_interacted = False 
        handle_loot() 
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)  
        return

    if FSM_vars.current_target_id is None or not Agent.IsAlive(FSM_vars.current_target_id):
        FSM_vars.current_target_id = enemy_array[0]  
        FSM_vars.has_interacted = False  

    if FSM_vars.current_target_id:
        target_id = FSM_vars.current_target_id
        target_x, target_y = Agent.GetXY(target_id)
        distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5

        if FSM_vars.last_target_id == None:
            FSM_vars.last_target_id = target_id

        if not FSM_vars.current_target_id == FSM_vars.last_target_id:
            FSM_vars.has_interacted = False

        if not FSM_vars.has_interacted:
            Player.ChangeTarget(target_id)
            Player.Interact(target_id, call_target=False)
            FSM_vars.last_target_id = target_id
            FSM_vars.has_interacted = True  
            if my_p_prof == Profession.Ranger.value or my_s_prof == Profession.Ranger.value:
                if not FSM_vars.PetBehavior == 0:
                    FSM_vars.PetBehavior = 0 #0=Fight, 1=Guard, 2=Avoid
                Party.Pets.SetPetBehavior(FSM_vars.PetBehavior, target_id)
        
        if Agent.IsAlive(target_id):
            if current_time - FSM_vars.last_skill_time >= 2.0:
                skill_slot = FSM_vars.current_skill_index
                Player.ChangeTarget(target_id)
                Player.Interact(target_id, call_target=False)                 
                SkillBar.UseSkill(skill_slot)  
                FSM_vars.last_skill_time = current_time  

                FSM_vars.current_skill_index = 1 if skill_slot >= 4 else skill_slot + 1  

            return  

    else:
        Party.Pets.SetPetBehavior(1, my_id)
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)

#FOR FARMER HAMNET
def hamnet_handle_map_path(map_pathing):
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    my_p_prof, my_s_prof = Agent.GetProfessionIDs(my_id)
    current_time = time.time()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1200)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (my_x, my_y))

    if not enemy_array:
        FSM_vars.current_target_id = None
        FSM_vars.last_target_id = None
        FSM_vars.has_interacted = False 
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)  
        return

    if FSM_vars.current_target_id is None or not Agent.IsAlive(FSM_vars.current_target_id) or not FSM_vars.current_target_id == FSM_vars.last_target_id:
        FSM_vars.current_target_id = enemy_array[0]  
        FSM_vars.has_interacted = False  

    if FSM_vars.current_target_id:
        target_id = FSM_vars.current_target_id
        target_x, target_y = Agent.GetXY(target_id)
        distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5

        if not FSM_vars.has_interacted:
            if my_p_prof == Profession.Ranger.value or my_s_prof == Profession.Ranger.value:
                Party.Pets.SetPetBehavior(0, target_id)
            Player.Interact(target_id, call_target=False)
            FSM_vars.last_target_id = target_id
            FSM_vars.has_interacted = True  
        
        if Agent.IsAlive(target_id):
            if current_time - FSM_vars.last_skill_time >= 2.0:
                skill_slot = FSM_vars.current_skill_index
                Player.ChangeTarget(target_id)
                Player.Interact(target_id, call_target=False)                 
                SkillBar.UseSkill(skill_slot)  
                FSM_vars.last_skill_time = current_time  

                FSM_vars.current_skill_index = 1 if skill_slot >= 4 else skill_slot + 1  

            return  

    else:
        Party.Pets.SetPetBehavior(1, my_id)
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)

def handle_npc_interaction():
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()

    npc_array = AgentArray.GetNPCMinipetArray()
    npc_array = AgentArray.Filter.ByDistance(npc_array, (my_x, my_y), 800)

    if not npc_array:
        FSM_vars.current_target_id = None
        FSM_vars.has_interacted = False
        FSM_vars.last_interaction_time = 0 
        return  

    if FSM_vars.current_target_id is None or FSM_vars.current_target_id not in npc_array:
        FSM_vars.current_target_id = npc_array[0]  
        FSM_vars.has_interacted = False  

    target_id = FSM_vars.current_target_id

    if not FSM_vars.has_interacted or (current_time - FSM_vars.last_interaction_time >= 5):  
        Player.Interact(target_id, call_target=False)
        FSM_vars.has_interacted = True
        FSM_vars.last_interaction_time = current_time  

def handle_item_interaction():
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()

    item_array = AgentArray.GetItemArray()
    item_array = AgentArray.Filter.ByDistance(item_array, (my_x, my_y), 1200)

    if not item_array:
        FSM_vars.current_target_id = None
        FSM_vars.has_interacted = False
        FSM_vars.last_interaction_time = 0  
        return  

    item_array = AgentArray.Sort.ByDistance(item_array, (my_x, my_y))

    if FSM_vars.current_target_id is None or FSM_vars.current_target_id not in item_array:
        FSM_vars.current_target_id = None  
        FSM_vars.has_interacted = False  

    for target_id in item_array:
        if current_time - FSM_vars.last_interaction_time >= 6:
            Player.Interact(target_id, call_target=False)
            FSM_vars.last_interaction_time = current_time   
            FSM_vars.has_interacted = True  

def handle_quest_interaction():
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time() 

    ally_array = AgentArray.GetNPCMinipetArray()
    ally_array = AgentArray.Filter.ByDistance(ally_array, (my_x, my_y), 5000)

    allies_with_quest = [agent_id for agent_id in ally_array if Agent.HasQuest(agent_id)]

    if not allies_with_quest:
        FSM_vars.current_target_id = None
        FSM_vars.has_interacted = False
        return  

    if FSM_vars.current_target_id is None or not Agent.HasQuest(FSM_vars.current_target_id):
        FSM_vars.current_target_id = allies_with_quest[0]
        FSM_vars.has_interacted = False
        FSM_vars.last_interaction_time = 0 

    if FSM_vars.current_target_id:
        target_id = FSM_vars.current_target_id

        if not FSM_vars.has_interacted:
            Player.Interact(target_id, call_target=False)
            FSM_vars.has_interacted = True
            FSM_vars.last_interaction_time = current_time  

        if FSM_vars.has_interacted and (current_time - FSM_vars.last_interaction_time >= 5):
            FSM_vars.has_interacted = False  
            FSM_vars.current_target_id = None  

def TargetNearestNeutral():
    distance = 5000 
    neutral_array = AgentArray.GetNeutralArray() 
    neutral_array = AgentArray.Filter.ByDistance(neutral_array, Player.GetXY(), distance)
    neutral_array = AgentArray.Sort.ByDistance(neutral_array, Player.GetXY())  

    
    return GetFirstFromArray(neutral_array)

def UseSkillByID(skill_id):
    for slot in range(1, 9): 
        if SkillBar.GetSkillIDBySlot(slot) == skill_id:
            SkillBar.UseSkill(slot)
            return True  
    return False  

def UseSkillByIDOnNearestNeutral(skill_id):
    target = TargetNearestNeutral()  
    if not target:
        return False

    for slot in range(1, 9):
        if SkillBar.GetSkillIDBySlot(slot) == skill_id:
            SkillBar.UseSkill(slot, target)  
            return True 
    
    return False 

def InteractPet():
    pet = TargetNearestNeutral()
    if pet:
        Player.Interact(pet)

def handle_loot_baked_husk():
    """
    Loot handling for Baked Husks using the same pattern as dull carapaces farm.
    """
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    item_distance = 2500  # Expanded loot vision like flower farm

    try:
        item_array = AgentArray.GetItemArray()
        item_array = AgentArray.Filter.ByDistance(item_array, (my_x, my_y), item_distance)

        agent_to_item_map = {
            agent_id: Agent.GetItemAgentItemID(agent_id)
            for agent_id in item_array
        }

        filtered_items = list(agent_to_item_map.values())
        filtered_items = ItemArray.Filter.ByCondition(
            filtered_items, lambda item_id: Item.GetItemType(item_id)[0] in {30, 10, 20, 9}
        )

        filtered_agent_ids = [
            agent_id for agent_id, item_id in agent_to_item_map.items()
            if item_id in filtered_items
        ]

        filtered_agent_ids = AgentArray.Sort.ByDistance(filtered_agent_ids, Agent.GetXY(my_id))

        if len(filtered_agent_ids) > 0:
            looting_item = filtered_agent_ids[0]

            # Check if we're already targeting this item
            if Player.GetTargetID() != looting_item:
                Player.ChangeTarget(looting_item)
                loot_timer.Reset()
                # Store the current loot target to prevent moving away
                FSM_vars.current_loot_target = looting_item
                FSM_vars.loot_target_start_time = time.time()  # Track when we started targeting
                return

            # If we're targeting the item, try to loot it
            if loot_timer.HasElapsed(800) and Player.GetTargetID() == looting_item:
                Keystroke.PressAndRelease(Key.Space.value)
                loot_timer.Reset()
                # Clear the loot target after attempting to loot
                FSM_vars.current_loot_target = None
                return
                
            # Timeout check - if we've been targeting the same loot for more than 10 seconds, give up
            if (hasattr(FSM_vars, 'loot_target_start_time') and 
                FSM_vars.loot_target_start_time > 0 and 
                time.time() - FSM_vars.loot_target_start_time > 10.0):
                Py4GW.Console.Log("Baked Husk Loot", "Loot target timeout - giving up", Py4GW.Console.MessageType.Warning)
                FSM_vars.current_loot_target = None
                FSM_vars.loot_target_start_time = 0.0
                return
                
            # If we have a loot target but it's not in range anymore, clear it
            if hasattr(FSM_vars, 'current_loot_target') and FSM_vars.current_loot_target:
                if FSM_vars.current_loot_target not in filtered_agent_ids:
                    FSM_vars.current_loot_target = None
                    
        else:
            # No loot items found, clear any existing loot target
            if hasattr(FSM_vars, 'current_loot_target'):
                FSM_vars.current_loot_target = None
                
    except Exception as e:
        # Clear loot target on any error to prevent getting stuck
        if hasattr(FSM_vars, 'current_loot_target'):
            FSM_vars.current_loot_target = None
        Py4GW.Console.Log("Baked Husk Loot", f"Error in loot handling: {str(e)}", Py4GW.Console.MessageType.Warning)

# Removed handle_loot_worn_belts() function since loot table will automatically pick up worn belts

def sweep_area_for_loot():
    """
    Sweep the area for any missed loot items.
    """
    try:
        my_id = Player.GetAgentID()
        my_x, my_y = Agent.GetXY(my_id)
        
        # Get all items in bags
        bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
        item_array = ItemArray.GetItemArray(bags_to_check)
        
        if item_array:
            for item_id in item_array:
                if Item.Properties.GetQuantity(item_id) > 0:
                    TargetNearestItem()
                    time.sleep(0.1)
                    
    except Exception as e:
        Py4GW.Console.Log("Baked Husk Loot", f"Error in area sweep: {str(e)}", Py4GW.Console.MessageType.Error)

def comprehensive_loot_sweep():
    """
    Final comprehensive loot sweep with multiple attempts.
    """
    try:
        for _ in range(5):  # Try 5 times for more thorough sweep
            handle_loot()
            time.sleep(0.3)
            
            # Additional targeting
            TargetNearestItem()
            time.sleep(0.2)
            
            # Also try baked husk specific loot
            handle_loot_baked_husk()
            time.sleep(0.2)
            
    except Exception as e:
        Py4GW.Console.Log("Baked Husk Loot", f"Error in comprehensive sweep: {str(e)}", Py4GW.Console.MessageType.Error)

def check_movement_stuck():
    """
    Check if the bot is stuck in one position and reset movement if needed.
    """
    global FSM_vars
    try:
        my_id = Player.GetAgentID()
        current_pos = Agent.GetXY(my_id)
        
        # Check if we're in the same position for too long
        if FSM_vars.last_position == current_pos:
            if FSM_vars.position_stuck_time == 0.0:
                FSM_vars.position_stuck_time = time.time()
            elif time.time() - FSM_vars.position_stuck_time > 15.0:  # 15 seconds stuck
                Py4GW.Console.Log("Movement", "Bot appears stuck - resetting movement", Py4GW.Console.MessageType.Warning)
                FSM_vars.movement_handler.reset()
                FSM_vars.current_loot_target = None
                FSM_vars.position_stuck_time = 0.0
                return True
        else:
            # We moved, reset stuck timer
            FSM_vars.position_stuck_time = 0.0
            
        FSM_vars.last_position = current_pos
        return False
        
    except Exception as e:
        Py4GW.Console.Log("Movement", f"Error checking movement: {str(e)}", Py4GW.Console.MessageType.Warning)
        return False


def handle_gadget_interaction():
    """
    Simple lever interaction - just target with semicolon and activate with spacebar.
    """
    global FSM_vars
    current_time = time.time()

    # Simple interaction - just press semicolon to target closest object (the lever)
    if not hasattr(FSM_vars, 'lever_targeted_logged'):
        Py4GW.Console.Log("Gadget Interaction", "Targeting lever with semicolon key", Py4GW.Console.MessageType.Info)
        FSM_vars.lever_targeted_logged = True
    
    # Press semicolon to target closest object
    Keystroke.PressAndRelease(Key.Semicolon.value)
    time.sleep(0.02)  # Small delay to ensure targeting is complete
    
    # Press spacebar to activate the lever
    if not FSM_vars.has_interacted or (current_time - FSM_vars.last_interaction_time >= 3):
        if not hasattr(FSM_vars, 'lever_activated_logged'):
            Py4GW.Console.Log("Gadget Interaction", "Activating lever with spacebar", Py4GW.Console.MessageType.Info)
            FSM_vars.lever_activated_logged = True
        
        # Press spacebar to activate lever
        Keystroke.PressAndRelease(Key.Space.value)
        
        # Wait 100ms to ensure lever activation completes
        time.sleep(0.1)
        
        FSM_vars.has_interacted = True
        FSM_vars.last_interaction_time = current_time
        
        time.sleep(0.03)
        return True
    
    return False

def move_to_gate_portal():
    """
    Enhanced movement to gate portal with improved coordinates and timing from found code.
    """
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()

    # Enhanced coordinates from found code
    gate_portal_x, gate_portal_y = -5507, 12917  # Gate portal position
    northlands_approach_x, northlands_approach_y = -5700, 14200  # Approach to Northlands
    
    # Check if we've already reached the gate portal
    if not hasattr(FSM_vars, 'reached_gate_portal'):
        FSM_vars.reached_gate_portal = False
    
    if not FSM_vars.reached_gate_portal:
        # Move towards the gate portal
        if current_time - FSM_vars.last_interaction_time > 5.0:
            FSM_vars.last_interaction_time = current_time
            
            # Use movement to go to the gate portal
            Routines.Movement.MoveTo(gate_portal_x, gate_portal_y)
            
            # Check if we're close enough to the gate portal
            distance = ((my_x - gate_portal_x) ** 2 + (my_y - gate_portal_y) ** 2) ** 0.5
            
            if distance < 200:  # Close enough to consider "reached"
                FSM_vars.reached_gate_portal = True
    else:
        # Now move to Northlands approach position
        if current_time - FSM_vars.last_interaction_time > 5.0:
            FSM_vars.last_interaction_time = current_time
            
            # Use movement to go to the Northlands approach position
            Routines.Movement.MoveTo(northlands_approach_x, northlands_approach_y)
            
            # Check if we're close enough to the Northlands approach position
            distance = ((my_x - northlands_approach_x) ** 2 + (my_y - northlands_approach_y) ** 2) ** 0.5
            
            if distance < 200:  # Close enough to consider "reached"
                FSM_vars.reached_northlands_approach = True 

def handle_map_path_gate_opener(map_pathing):
    """
    Optimized path handler for gate opener with minimal performance impact.
    """
    global FSM_vars
    
    # Safety check - validate game state first
    try:
        if not Map.IsMapReady() or Player.GetAgentID() <= 0:
            return
    except Exception as e:
        return
        
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    
    # Check if we're stuck and need to reset movement (reduced frequency)
    current_time = time.time()
    if not hasattr(FSM_vars, 'last_stuck_check_time'):
        FSM_vars.last_stuck_check_time = 0.0
    
    if current_time - FSM_vars.last_stuck_check_time > 1.0:  # Only check every second
        FSM_vars.last_stuck_check_time = current_time
        if check_movement_stuck():
            return  # Let the movement reset take effect
    
    # Optimized movement without delays
    try:
        # Follow the path directly without stabilization delays
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)
        
        # Log movement status periodically (reduced frequency)
        if not hasattr(FSM_vars, 'last_debug_time'):
            FSM_vars.last_debug_time = time.time()
            
    except Exception as e:
        # Try to recover by resetting movement handler (without delays)
        FSM_vars.movement_handler.reset()
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)

def handle_map_path_baked_husk(map_pathing):
    """
    Optimized function for Baked Husks farming with reduced lag.
    """
    global FSM_vars
    
    # Safety check - validate game state first
    try:
        if not Map.IsMapReady() or Player.GetAgentID() <= 0:
            return
    except:
        return
        
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    my_p_prof, my_s_prof = Agent.GetProfessionIDs(my_id)
    current_time = time.time()

    # SPECIAL HANDLING FOR 5TH COORDINATE (-9467, 673) - LAG SPIKE AREA
    # Check if we're near the problematic coordinate
    target_coord_x, target_coord_y = -9467, 673
    distance_to_problem_coord = ((my_x - target_coord_x) ** 2 + (my_y - target_coord_y) ** 2) ** 0.5
    
    if distance_to_problem_coord < 500:  # Within 500 units of the laggy coordinate
        # Add extra delay and reduced processing for this area
        time.sleep(0.1)  # Extra 100ms delay
        # Skip some processing to reduce lag
        if hasattr(FSM_vars, 'last_problem_coord_time') and current_time - FSM_vars.last_problem_coord_time < 0.5:
            # Only process every 500ms in the problem area
            return
        FSM_vars.last_problem_coord_time = current_time

    # Check for enemies in a larger area to ensure we don't miss any
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 2500)  # Increased from 1200 to 2500
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (my_x, my_y))

    # PRIORITIZE LOOT BEFORE COMBAT
    # Always try to loot first, regardless of enemy presence
    # Most enemies won't attack unless provoked
    
    # Check if we're at the end of the path (near teleport location)
    # If so, do a comprehensive loot sweep before teleporting
    if map_pathing.is_finished() and not FSM_vars.final_loot_sweep_done:
        # Final loot sweep before teleporting
        comprehensive_loot_sweep()
        FSM_vars.final_loot_sweep_done = True
        time.sleep(0.5)  # Give time for loot to be picked up
        return
    
    # Always try to loot first (enemies won't attack unless provoked)
    handle_loot_baked_husk()
    
    # Check if we're stuck and need to reset movement
    if check_movement_stuck():
        return  # Let the movement reset take effect
    
    # Continue movement regardless of loot status - don't get stuck on loot
    try:
        # Add extra delay if in problem coordinate area
        if distance_to_problem_coord < 500:
            time.sleep(0.05)  # Extra 50ms delay for smoother movement in lag area
        
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)
        # Log movement status periodically
        if hasattr(FSM_vars, 'last_debug_time') and time.time() - FSM_vars.last_debug_time > 30.0:
            Py4GW.Console.Log("Baked Husk Movement", "Continuing path movement", Py4GW.Console.MessageType.Info)
            FSM_vars.last_debug_time = time.time()
        elif not hasattr(FSM_vars, 'last_debug_time'):
            FSM_vars.last_debug_time = time.time()
    except Exception as e:
        Py4GW.Console.Log("Baked Husk Movement", f"Movement error: {str(e)}", Py4GW.Console.MessageType.Warning)
        # Try to recover by resetting movement handler
        FSM_vars.movement_handler.reset()
        time.sleep(0.1)
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)
        
    # Handle enemies if they exist - kill all enemies in 2500 range
    if enemy_array:
        if FSM_vars.current_target_id is None or not Agent.IsAlive(FSM_vars.current_target_id) or not FSM_vars.current_target_id == FSM_vars.last_target_id:
            FSM_vars.current_target_id = enemy_array[0]  
            FSM_vars.has_interacted = False  

        if FSM_vars.current_target_id:
            target_id = FSM_vars.current_target_id
            target_x, target_y = Agent.GetXY(target_id)
            distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5

            if not FSM_vars.has_interacted:
                if my_p_prof == Profession.Ranger.value or my_s_prof == Profession.Ranger.value:
                    Party.Pets.SetPetBehavior(0, target_id)
                Player.Interact(target_id, call_target=False)
                FSM_vars.last_target_id = target_id
                FSM_vars.has_interacted = True  
            
            if Agent.IsAlive(target_id):
                if current_time - FSM_vars.last_skill_time >= 2.0:
                    skill_slot = FSM_vars.current_skill_index
                    Player.ChangeTarget(target_id)
                    Player.Interact(target_id, call_target=False)                 
                    SkillBar.UseSkill(skill_slot)  
                    FSM_vars.last_skill_time = current_time  
                    FSM_vars.current_skill_index = (skill_slot % 8) + 1  

                return
    else:
        # No enemies, clear target variables
        FSM_vars.current_target_id = None
        FSM_vars.last_target_id = None
        FSM_vars.has_interacted = False

#FSM
class StateMachineVars:
    def __init__(self):     
  
        self.movement_handler = Routines.Movement.FollowXY(300)  # Add 300ms delay for smoother movement
        self.last_skill_time = 0.0
        self.current_skill_index = 1
        self.last_item_pickup_time = 0.0
        
        # Loot tracking variables
        self.current_lootable = 0
        self.current_loot_tries = 0
        self.current_loot_target = None
        self.loot_target_start_time = 0.0  # Track when we started targeting loot
        self.final_loot_sweep_done = False
        self.current_target_id = None
        self.last_target_id = None
        self.has_interacted = False 
        self.last_interaction_time = 0.0
        self.PetBehavior = 1
        
        # Movement stuck detection
        self.last_position = (0, 0)
        self.position_stuck_time = 0.0
        self.last_debug_time = 0.0
        
        self.in_waiting_routine = True
        self.in_killing_routine = True
        self.reached_althea_stage = False
        self.reached_first_coordinate = False

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

        #FSM for lvl 2-10 - SUBROUTINE
        self.state_machine_ResetQuest = FSM("RESET QUEST")

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

        #FSM for UNNATURAL SEEDS
        self.state_machine_worn_belts = FSM("WORN BELTS")
        self.worn_belts_pathing = Routines.Movement.PathHandler(worn_belts_coordinate_list)

        #FSM for BAKED HUSKS
        self.state_machine_baked_husks = FSM("BAKED HUSKS")
        self.baked_husk_pathing = Routines.Movement.PathHandler(baked_husk_coordinate_list)
        self.baked_husk_location_1_pathing = Routines.Movement.PathHandler(baked_husk_location_1)
        self.baked_husk_location_2_pathing = Routines.Movement.PathHandler(baked_husk_location_2)
        self.baked_husk_location_3_pathing = Routines.Movement.PathHandler(baked_husk_location_3)
        self.baked_husk_location_4_pathing = Routines.Movement.PathHandler(baked_husk_location_4)
        self.baked_husk_location_5_pathing = Routines.Movement.PathHandler(baked_husk_location_5)
        self.baked_husk_location_6_pathing = Routines.Movement.PathHandler(baked_husk_location_6)

        #FSM for CHARR GATE OPENER
        self.state_machine_charr_gate_opener = FSM("CHARR GATE OPENER")
        self.charr_gate_opener_pathing_1 = Routines.Movement.PathHandler(charr_gate_opener_coordinate_list_1)
        self.charr_gate_opener_pathing_2 = Routines.Movement.PathHandler(charr_gate_opener_coordinate_list_2)
        self.charr_gate_opener_fast_gate_run = Routines.Movement.PathHandler(charr_gate_opener_fast_gate_run)
        self.ascalon_town_exit_pathing = Routines.Movement.PathHandler(ascalon_town_exit_coordinate_list)

        #FSM for NICHOLAS SANDFORD
        self.state_machine_nicholas_sandford = FSM("NICHOLAS SANDFORD")
        self.nicholas_sandford_pathing = Routines.Movement.PathHandler(nicholas_sandford_coordinate_list)

        #FSM for TAME PET
        self.state_machine_TamePet = FSM("TAME PET")
        self.goingout_ashfordabbey = Routines.Movement.PathHandler(goingout_ashfordabbey)
        self.tamepet_pathing_1 = Routines.Movement.PathHandler(tamepet_coordinate_list_1)
        self.tamepet_pathing_2 = Routines.Movement.PathHandler(tamepet_coordinate_list_2)
        self.tamepet_pathing_3 = Routines.Movement.PathHandler(tamepet_coordinate_list_3)

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

        #FSM WARRIOR SKILL REQ
        self.state_machine_warrior_req = FSM("WARRIOR REQ")
        self.warrior_skill_pathing_1 = Routines.Movement.PathHandler(warrior_skill_coordinate_list_1)
        self.warrior_skill_pathing_2 = Routines.Movement.PathHandler(warrior_skill_coordinate_list_2)
        self.warrior_skill_pathing_3 = Routines.Movement.PathHandler(warrior_skill_coordinate_list_3)

        #FSM WARRIOR SKILL REQ
        self.state_machine_warrior_noreq = FSM("WARRIOR NO REQ")

        #FSM RANGER REQ
        self.state_machine_ranger_req = FSM("RANGER REQ")
        self.ranger_skill_pathing_1 = Routines.Movement.PathHandler(ranger_skill_coordinate_list_1)
        self.ranger_skill_pathing_2 = Routines.Movement.PathHandler(ranger_skill_coordinate_list_2)
        self.ranger_skill_pathing_3 = Routines.Movement.PathHandler(ranger_skill_coordinate_list_3)

        #FSM RANGER SKILL REQ
        self.state_machine_ranger_noreq = FSM("RANGER NO REQ")

        #FSM MONK REQ
        self.state_machine_monk_req = FSM("MONK REQ")
        self.monk_skill_pathing_1 = Routines.Movement.PathHandler(monk_skill_coordinate_list_1)
        self.monk_skill_pathing_2 = Routines.Movement.PathHandler(monk_skill_coordinate_list_2)

        #FSM MONK SKILL NOREQ
        self.state_machine_monk_noreq = FSM("MONK NO REQ")

        #FSM NECRO REQ
        self.state_machine_necro_req = FSM("NECRO REQ")
        self.necro_skill_pathing_1 = Routines.Movement.PathHandler(necro_skill_coordinate_list_1)
        self.necro_skill_pathing_2 = Routines.Movement.PathHandler(necro_skill_coordinate_list_2)
        self.necro_skill_pathing_3 = Routines.Movement.PathHandler(necro_skill_coordinate_list_3)
        self.necro_skill_pathing_4 = Routines.Movement.PathHandler(necro_skill_coordinate_list_4)

        #FSM NECRO SKILL NOREQ
        self.state_machine_necro_noreq = FSM("NECRO NO REQ")

FSM_vars = StateMachineVars()

#region Warrior
#___________________________ WARRIOR LVL 1 ___________________________#
#START COMMON ROUTINE PART ONE
FSM_vars.state_machine_warrior.AddState(name="COMMAND BONUS", execute_fn=lambda: player_instance.SendChatCommand(text_bonus), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="EQUIP WAND", execute_fn=lambda: equipitem(6508, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="EQUIP SHIELD", execute_fn=lambda: equipitem(6514, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="GOING NEAR TOWN CRIER", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805001", 16)), transition_delay_ms=300, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="GOING NEAR SIR TYDUS", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805007", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80DD01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_warrior.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART ONE
#START WARRIOR ROUTINE
FSM_vars.state_machine_warrior.AddState(name="GOING NEAR VAN", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.van_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.van_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80DD07", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805501", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_warrior.AddState(name="GOING TO KILL", execute_fn=lambda: handle_map_path(FSM_vars.warrior_quest_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.warrior_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_warrior.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="GOING NEAR VAN", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.van_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.van_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805507", 16)), transition_delay_ms=1500, run_once=True)
#END WARRIOR ROUTINE
#START COMMON ROUTINE PART TWO
FSM_vars.state_machine_warrior.AddState(name="GOING NEAR ALTHEA", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804703", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x804701", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_warrior.AddState(name="SECOND MAP PATH", execute_fn=lambda: warrior_handle_map_path(FSM_vars.leveling_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="GOING NEAR PRINCE RURIK", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_warrior.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802E01", 16)), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART TWO

#region Ranger
#___________________________ RANGER LVL 1 ___________________________#
#START COMMON ROUTINE PART ONE
FSM_vars.state_machine_ranger.AddState(name="COMMAND BONUS", execute_fn=lambda: player_instance.SendChatCommand(text_bonus), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="EQUIP BOW", execute_fn=lambda: equipitem(5831, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="EQUIP SHIELD", execute_fn=lambda: equipitem(6514, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="GOING NEAR TOWN CRIER", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805001", 16)), transition_delay_ms=300, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="GOING NEAR SIR TYDUS", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805007", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80DE01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_ranger.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART ONE
#START RANGER ROUTINE
FSM_vars.state_machine_ranger.AddState(name="GOING NEAR ARTEMIS", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.artemis_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.artemis_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80DE07", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805601", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_ranger.AddState(name="GOING TO KILL", execute_fn=lambda: handle_map_path(FSM_vars.ranger_quest_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranger_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_ranger.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="GOING NEAR VAN", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.artemis_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.artemis_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805607", 16)), transition_delay_ms=1500, run_once=True)
#END RANGER ROUTINE
#START COMMON ROUTINE PART TWO
FSM_vars.state_machine_ranger.AddState(name="GOING NEAR ALTHEA", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804703", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x804701", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_ranger.AddState(name="SECOND MAP PATH", execute_fn=lambda: hamnet_handle_map_path(FSM_vars.leveling_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="GOING NEAR PRINCE RURIK", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802E01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger.AddState(name="EQUIP WAND", execute_fn=lambda: equipitem(6508, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
#END COMMON ROUTINE PART TWO

#region Monk
#___________________________ MONK LVL 1 ___________________________#
#START COMMON ROUTINE PART ONE
FSM_vars.state_machine_monk.AddState(name="COMMAND BONUS", execute_fn=lambda: player_instance.SendChatCommand(text_bonus), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="EQUIP WAND", execute_fn=lambda: equipitem(6508, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="EQUIP SHIELD", execute_fn=lambda: equipitem(6514, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="GOING NEAR TOWN CRIER", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_monk.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805001", 16)), transition_delay_ms=300, run_once=True)
FSM_vars.state_machine_monk.AddState(name="GOING NEAR SIR TYDUS", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_monk.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805007", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80DC01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_monk.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART ONE
#START MONK ROUTINE
FSM_vars.state_machine_monk.AddState(name="GOING NEAR CIGLO", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ciglo_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ciglo_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_monk.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80DC07", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805401", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk.AddState(name="GOING TO GWEN", execute_fn=lambda: handle_map_path(FSM_vars.monk_quest_pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.monk_quest_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_monk.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="GOING BACK TO CIGLO", execute_fn=lambda: handle_map_path(FSM_vars.monk_quest_pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.monk_quest_pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_monk.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805407", 16)), transition_delay_ms=1500, run_once=True)
#END MONK ROUTINE
#START COMMON ROUTINE PART TWO
FSM_vars.state_machine_monk.AddState(name="GOING NEAR ALTHEA", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_monk.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804703", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x804701", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_monk.AddState(name="SECOND MAP PATH", execute_fn=lambda: early_handle_map_path(FSM_vars.leveling_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_monk.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk.AddState(name="GOING NEAR PRINCE RURIK", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_monk.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_monk.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802E01", 16)), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART TWO

#region Necromancer
#___________________________ NECROMANCER LVL 1 ___________________________#
#START COMMON ROUTINE PART ONE
FSM_vars.state_machine_necromancer.AddState(name="COMMAND BONUS", execute_fn=lambda: player_instance.SendChatCommand(text_bonus), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="EQUIP WAND", execute_fn=lambda: equipitem(6508, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="EQUIP SHIELD", execute_fn=lambda: equipitem(6514, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR TOWN CRIER", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necromancer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805001", 16)), transition_delay_ms=300, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR SIR TYDUS", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necromancer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805007", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80DA01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_necromancer.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART ONE
#START NECROMANCER ROUTINE
FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR ARTEMIS", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.verata_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.verata_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necromancer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80DA07", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805201", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="GOING TO KILL", execute_fn=lambda: handle_map_path(FSM_vars.necromancer_quest_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.necromancer_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necromancer.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_necromancer.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR VAN", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.verata_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.verata_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necromancer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805207", 16)), transition_delay_ms=1500, run_once=True)
#END NECROMANCER ROUTINE
#START COMMON ROUTINE PART TWO
FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR ALTHEA", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necromancer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804703", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x804701", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="SECOND MAP PATH", execute_fn=lambda: early_handle_map_path(FSM_vars.leveling_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necromancer.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="GOING NEAR PRINCE RURIK", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necromancer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_necromancer.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802E01", 16)), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART TW0

#region Mesmer
#___________________________ MESMER LVL 1 ___________________________#
#START COMMON ROUTINE PART ONE
FSM_vars.state_machine_mesmer.AddState(name="COMMAND BONUS", execute_fn=lambda: player_instance.SendChatCommand(text_bonus), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="EQUIP WAND", execute_fn=lambda: equipitem(6508, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="EQUIP SHIELD", execute_fn=lambda: equipitem(6514, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR TOWN CRIER", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_mesmer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805001", 16)), transition_delay_ms=300, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR SIR TYDUS", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_mesmer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805007", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80D901", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_mesmer.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART ONE
#START MESMER ROUTINE
FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR SEBEDOH", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.sebedoh_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sebedoh_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_mesmer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80D907", 16)), transition_delay_ms=300, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805101", 16)), transition_delay_ms=300, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="GOING TO KILL", execute_fn=lambda: handle_map_path(FSM_vars.mesmer_quest_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.mesmer_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_mesmer.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_mesmer.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR VAN", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.sebedoh_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sebedoh_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_mesmer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805107", 16)), transition_delay_ms=300, run_once=True)
#END MESMER ROUTINE
#START COMMON ROUTINE PART TWO
FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR ALTHEA", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_mesmer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804703", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x804701", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="SECOND MAP PATH", execute_fn=lambda: early_handle_map_path(FSM_vars.leveling_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_mesmer.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="GOING NEAR PRINCE RURIK", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_mesmer.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_mesmer.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802E01", 16)), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART TWO

#region Elementalist
#___________________________ ELEMENTALIST LVL 1 ___________________________#
#START COMMON ROUTINE PART ONE
FSM_vars.state_machine_elementalist.AddState(name="COMMAND BONUS", execute_fn=lambda: player_instance.SendChatCommand(text_bonus), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="EQUIP WAND", execute_fn=lambda: equipitem(6508, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="EQUIP SHIELD", execute_fn=lambda: equipitem(6514, agent_id), exit_condition=lambda: LDoA_IsOutpost(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR TOWN CRIER", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.town_crier_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_elementalist.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805001", 16)), transition_delay_ms=300, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR SIR TYDUS", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.sir_tydus_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_elementalist.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x805007", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80DB01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_elementalist.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART ONE
#START ELEMENTALIST ROUTINE
FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR SEBEDOH", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.howland_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.howland_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_elementalist.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="TAKING REWARD", execute_fn=lambda: Player.SendDialog(int("0x80DB07", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805301", 16)), transition_delay_ms=300, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="GOING TO KILL", execute_fn=lambda: handle_map_path_loot(FSM_vars.elementalist_quest_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.elementalist_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_elementalist.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_elementalist.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR HOWLAND", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.howland_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.howland_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_elementalist.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805307", 16)), transition_delay_ms=300, run_once=True)
#END ELEMENTALIST ROUTINE
#START COMMON ROUTINE PART TWO
FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR ALTHEA", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.althea_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.althea_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_elementalist.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804703", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x804701", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="SECOND MAP PATH", execute_fn=lambda: early_handle_map_path(FSM_vars.leveling_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.leveling_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_elementalist.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="GOING NEAR PRINCE RURIK", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_elementalist.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_elementalist.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802E01", 16)), transition_delay_ms=1500, run_once=True)
#END COMMON ROUTINE PART TWO

#___________________________ CHARR AT THE GATE ___________________________#
FSM_vars.state_machine_lvl2_10.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_lvl2_10.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_lvl2_10.AddState(name="PAUSE BEFORE FOLLOWING", execute_fn=lambda: FollowPathwithDelayTimer(FSM_vars.rurikpause_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.rurikpause_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_lvl2_10.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_lvl2_10.AddState(name="FOLLOWING RURIK", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.rurik_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.rurik_pathing, FSM_vars.movement_handler) or Survivor() or Death(), run_once=False)
FSM_vars.state_machine_lvl2_10.AddState(name="WAITING RURIK KILLING", execute_fn=lambda: set_killing_routine(), exit_condition=lambda: end_killing_routine_1() or Survivor() or Death(), run_once=False)
FSM_vars.state_machine_lvl2_10.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_lvl2_10.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_lvl2_10.AddState(name="COUNTER", execute_fn=lambda: increment_run_counter(), exit_condition=lambda: Party.IsPartyLoaded() and Map.IsMapReady(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_lvl2_10.AddSubroutine(name="CHECK QUEST STATUS", sub_fsm = FSM_vars.state_machine_ResetQuest,  condition_fn=lambda: Quest.IsQuestCompleted(bot_vars.CharrAtTheGate))
FSM_vars.state_machine_lvl2_10.AddState(name="RESET CHECK QUEST ROUTINE", execute_fn=lambda: FSM_vars.state_machine_ResetQuest.reset())

FSM_vars.state_machine_ResetQuest.AddState(name="ABANDON QUEST", execute_fn=lambda: Quest.AbandonQuest(bot_vars.CharrAtTheGate),transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ResetQuest.AddState(name="GOING NEAR PRINCE RURIK", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.taking_quest_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ResetQuest.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_ResetQuest.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802E01", 16)), transition_delay_ms=1500, run_once=True)

#___________________________ FARMER HAMNET ___________________________#
FSM_vars.state_machine_lvl11_20.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.foible_map), exit_condition=lambda: Map.GetMapID() == bot_vars.foible_map or Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_lvl11_20.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_lvl11_20.AddState(name="GOING OUT IN DANGEROUS LANDS", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_lvl11_20.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_lvl11_20.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_lvl11_20.AddState(name="LUCKILY THERE IS A PRIEST", execute_fn=lambda: early_handle_map_path(FSM_vars.bandit_pathing), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.bandit_pathing, FSM_vars.movement_handler) or Survivor_Hamnet(), run_once=False)
FSM_vars.state_machine_lvl11_20.AddState(name="FIRE IMP IS FIRING", execute_fn=lambda: set_killing_routine(), exit_condition=lambda: end_killing_routine() or Survivor_Hamnet(), run_once=False)
FSM_vars.state_machine_lvl11_20.AddState(name="COUNTER", execute_fn=lambda: increment_run_counter(), exit_condition=lambda: Party.IsPartyLoaded() and Map.IsMapReady(), transition_delay_ms=1000, run_once=True)

#___________________________ TAME PET ___________________________#
FSM_vars.state_machine_TamePet.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_TamePet.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_TamePet.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.tamepet_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TamePet.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_TamePet.AddState(name="SECOND MAP PATH", execute_fn=lambda: handle_map_path(FSM_vars.tamepet_pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TamePet.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TamePet.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804C03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TamePet.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x804C01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TamePet.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x85", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TamePet.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.tamepet_pathing_3, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TamePet.AddState(name="CHECK QUEST", execute_fn=lambda: InteractPet(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_TamePet.AddState(name="TAME PET", execute_fn=lambda: UseSkillByIDOnNearestNeutral(411), transition_delay_ms=20000, run_once=True)
FSM_vars.state_machine_TamePet.AddState(name="GOING BACK TO ASHFORD ABBEY", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.abbey_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TamePet.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)

#___________________________ TRAVEL TO ASHFORD ABBEY ___________________________#
FSM_vars.state_machine_abbey.AddState(name="GOING BACK TO ASHFORD ABBEY", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_abbey.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_abbey.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_abbey.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_abbey.AddState(name="WALKING TO ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.abbey_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.abbey_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_abbey.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)

#___________________________ TRAVEL TO FOIBLE'S FAIR ___________________________#
FSM_vars.state_machine_foible.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_foible.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_foible.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_foible.AddState(name="WALKING TO WIZARD'S FOLLY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_coordinate_list_one_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_coordinate_list_one_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_foible.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_foible.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_foible.AddState(name="WALKING TO WIZARD'S FOLLY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_coordinate_list_two_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_coordinate_list_two_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_foible.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)

#___________________________ TRAVEL TO FORT RANIK ___________________________#
FSM_vars.state_machine_ranik.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_ranik.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_ranik.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_ranik.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.tamepet_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranik.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_ranik.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_ranik.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ranik_coordinate_list_two_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranik_coordinate_list_two_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_ranik.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)

#___________________________ TRAVEL TO BARRADIN ESTATE  ___________________________#
FSM_vars.state_machine_barradin.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_barradin.AddState(name="ABANDON QUEST", execute_fn=lambda: Quest.AbandonQuest(bot_vars.CharrAtTheGate),transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_barradin.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_barradin.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_barradin.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler) and Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), run_once=False)
FSM_vars.state_machine_barradin.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_barradin.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_barradin.AddState(name="WALKING TO BARRADIN ESTATE", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_two_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_two_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_barradin.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)

#___________________________ THE GRAND TOUR  ___________________________#
FSM_vars.state_machine_grandtour.AddState(name="GOING BACK TO ASHFORD ABBEY", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="WALKING TO ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.abbey_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.abbey_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="WALKING TO WIZARD'S FOLLY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_coordinate_list_one_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_coordinate_list_one_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="WALKING TO WIZARD'S FOLLY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_coordinate_list_two_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_coordinate_list_two_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="GOING BACK TO ASHFORD ABBEY", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.abbey_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.tamepet_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ranik_coordinate_list_two_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranik_coordinate_list_two_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="ABANDON QUEST", execute_fn=lambda: Quest.AbandonQuest(bot_vars.CharrAtTheGate),transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler) and Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_grandtour.AddState(name="WALKING TO BARRADIN ESTATE", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_two_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_two_pathing, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_grandtour.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)

#___________________________ WARRIOR REQ  ___________________________#
FSM_vars.state_machine_warrior_req.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="ABANDON QUEST", execute_fn=lambda: Quest.AbandonQuest(bot_vars.CharrAtTheGate),transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_warrior_req.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler) and Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), run_once=False)
FSM_vars.state_machine_warrior_req.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="WALKING TO QUEST", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.warrior_skill_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.warrior_skill_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804B03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804B01", 16)), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="GOING TO BARRADIN", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.barradin_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="WALKING TO QUEST", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.warrior_skill_pathing_2, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.warrior_skill_pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x803C03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x803C01", 16)), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="WALKING TO QUEST", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.warrior_skill_pathing_2, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.warrior_skill_pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802803", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802801", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)

#___________________________ WARRIOR NO REQ  ___________________________#
FSM_vars.state_machine_warrior_noreq.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_warrior_noreq.AddState(name="ABANDON QUEST", execute_fn=lambda: Quest.AbandonQuest(bot_vars.CharrAtTheGate),transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior_noreq.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_warrior_noreq.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_warrior_noreq.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler) and Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), run_once=False)
FSM_vars.state_machine_warrior_noreq.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_warrior_noreq.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_warrior_noreq.AddState(name="WALKING TO QUEST", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.warrior_skill_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.warrior_skill_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_warrior_noreq.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_warrior_noreq.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804B03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior_noreq.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804B01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior_noreq.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x85", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_warrior_noreq.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)

#___________________________ RANGER REQ  ___________________________#
FSM_vars.state_machine_ranger_req.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="GOING BACK TO ABBEY", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.abbey_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_ranger_req.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.tamepet_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger_req.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="SECOND MAP PATH", execute_fn=lambda: handle_map_path(FSM_vars.tamepet_pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804C03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x804C01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x85", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.tamepet_pathing_3, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger_req.AddState(name="CHECK QUEST", execute_fn=lambda: InteractPet(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="TAME PET", execute_fn=lambda: UseSkillByIDOnNearestNeutral(411), transition_delay_ms=20000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ranger_skill_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranger_skill_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802A03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802A01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.foible_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="GOING OUT IN DANGEROUS LANDS", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_pathing, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_ranger_req.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ranger_skill_pathing_2, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranger_skill_pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger_req.AddState(name="SECOND MAP PATH", execute_fn=lambda: handle_map_path(FSM_vars.ranger_skill_pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranger_skill_pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805803", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805801", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_req.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)

#___________________________ RANGER NO REQ  ___________________________#
FSM_vars.state_machine_ranger_noreq.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_ranger_noreq.AddState(name="GOING BACK TO ABBEY", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.abbey_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_ranger_noreq.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_ranger_noreq.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_ranger_noreq.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.tamepet_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger_noreq.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_ranger_noreq.AddState(name="SECOND MAP PATH", execute_fn=lambda: handle_map_path(FSM_vars.tamepet_pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger_noreq.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_ranger_noreq.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804C03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_noreq.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x804C01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_noreq.AddState(name="TAKING SKILLS", execute_fn=lambda: Player.SendDialog(int("0x85", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_ranger_noreq.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.tamepet_pathing_3, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.tamepet_pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_ranger_noreq.AddState(name="CHECK QUEST", execute_fn=lambda: InteractPet(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_ranger_noreq.AddState(name="TAME PET", execute_fn=lambda: UseSkillByIDOnNearestNeutral(411), transition_delay_ms=20000, run_once=True)
FSM_vars.state_machine_ranger_noreq.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)

#___________________________ MONK REQ  ___________________________#
FSM_vars.state_machine_monk_req.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="GOING BACK TO ABBEY", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.abbey_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.monk_skill_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.monk_skill_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_monk_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805703", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x805701", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804A03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804A01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="ABANDON QUEST", execute_fn=lambda: Quest.AbandonQuest(bot_vars.CharrAtTheGate),transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_monk_req.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler) and Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), run_once=False)
FSM_vars.state_machine_monk_req.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.monk_skill_pathing_2, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.monk_skill_pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_monk_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804D03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804D01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_req.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)

#___________________________ MONK NO REQ  ___________________________#
FSM_vars.state_machine_monk_noreq.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_monk_noreq.AddState(name="GOING BACK TO ABBEY", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.abbey_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_monk_noreq.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.monk_skill_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.monk_skill_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_monk_noreq.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_monk_noreq.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804A03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_noreq.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804A01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_noreq.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x85", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_noreq.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_noreq.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_monk_noreq.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)

#___________________________ NECRO REQ  ___________________________#
FSM_vars.state_machine_necro_req.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="GOING BACK TO ABBEY", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.abbey_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.necro_skill_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.necro_skill_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_necro_req.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.necro_skill_pathing_2, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.necro_skill_pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necro_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804803", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804801", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.necro_skill_pathing_3, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.necro_skill_pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necro_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802F03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802F01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="ABANDON QUEST", execute_fn=lambda: Quest.AbandonQuest(bot_vars.CharrAtTheGate),transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="GOING OUT ASCALON", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_necro_req.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="WALKING TO REGENT VALLEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_coordinate_list_one_pathing, FSM_vars.movement_handler) and Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), run_once=False)
FSM_vars.state_machine_necro_req.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="USING IMP STONE", execute_fn=lambda: useitem(30847), run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.necro_skill_pathing_4, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.necro_skill_pathing_4, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necro_req.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802B03", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x802B01", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_req.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)

#___________________________ NECRO NO REQ  ___________________________#
FSM_vars.state_machine_necro_noreq.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_necro_noreq.AddState(name="GOING BACK TO ABBEY", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.abbey_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_necro_noreq.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.necro_skill_pathing_1, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.necro_skill_pathing_1, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), run_once=False)
FSM_vars.state_machine_necro_noreq.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_necro_noreq.AddState(name="GOING OUT ASHFORD ABBEY", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.necro_skill_pathing_2, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.necro_skill_pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_necro_noreq.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_necro_noreq.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804803", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_noreq.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x804801", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_noreq.AddState(name="TAKING QUEST", execute_fn=lambda: Player.SendDialog(int("0x85", 16)), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_noreq.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_noreq.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_necro_noreq.AddState(name="GOING BACK TO ASCALON", execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map), exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=5000, run_once=True)

#DULL CARAPACES
FSM_vars.state_machine_dull_carapaces.AddState(name="ASCALON", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - DULL CARAPACES FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.ascalon_map,6,0)) if not Map.IsExplorable() else None,  
                       exit_condition=lambda: LDoA_IsOutpost() or Map.IsExplorable(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_dull_carapaces.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_dull_carapaces.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - DULL CARAPACES FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=3000)

FSM_vars.state_machine_dull_carapaces.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.dull_carapaces_pathing_1, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.dull_carapaces_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_dull_carapaces.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - DULL CARAPACES FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_dull_carapaces.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.dull_carapaces_pathing_2),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.dull_carapaces_pathing_2, FSM_vars.movement_handler) or Death(),
                       run_once=False)

FSM_vars.state_machine_dull_carapaces.AddState(name="COUNTER", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - DULL CARAPACES FARM", "ADD COUNTER", Py4GW.Console.MessageType.Info),increment_run_counter()),  
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_dull_carapaces.AddState(name="RETURN TO TOWN",
                       execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ascalon_map),
                       exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(),
                       transition_delay_ms=1000,
                       run_once=True
)
FSM_vars.state_machine_dull_carapaces.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(),
                       transition_delay_ms=1500,
                       run_once=True
)
#GARGOYLE SKULLS
FSM_vars.state_machine_gargoyle_skulls.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - GARGOYLE SKULLS FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.barradin_map,6,0)) if not Map.IsExplorable() else None,  
                       exit_condition=lambda: LDoA_IsOutpost() or Map.IsExplorable(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - GARGOYLE SKULLS FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=5000)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - GARGOYLE SKULLS FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.greenhills_to_catacombs_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.greenhills_to_catacombs_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - GARGOYLE SKULLS FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=5000)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - GARGOYLE SKULLS FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.gargoyle_skulls_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.gargoyle_skulls_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_gargoyle_skulls.AddState(name="COUNTER", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - LDoA LVL 2-10", "ADD COUNTER", Py4GW.Console.MessageType.Info),increment_run_counter()),  
                       transition_delay_ms=1000,
                       run_once=True)

#GRAWL NECKLACES
FSM_vars.state_machine_grawl_necklaces.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - GRAWL NECKLACES FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.barradin_map,6,0)) if not Map.IsExplorable() else None,  
                       exit_condition=lambda: LDoA_IsOutpost() or Map.IsExplorable(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_grawl_necklaces.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_grawl_necklaces.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - GRAWL NECKLACES FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=3000)

FSM_vars.state_machine_grawl_necklaces.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - GRAWL NECKLACES FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_grawl_necklaces.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.grawl_necklaces_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.grawl_necklaces_pathing, FSM_vars.movement_handler) or Survivor(),
                       run_once=False)

FSM_vars.state_machine_grawl_necklaces.AddState(name="COUNTER", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - GRAWL NECKLACES FARM", "ADD COUNTER", Py4GW.Console.MessageType.Info),increment_run_counter()),  
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_grawl_necklaces.AddState(name="RETURN TO TOWN",
                       execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.barradin_map),
                       exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(),
                       transition_delay_ms=1000,
                       run_once=True
)
FSM_vars.state_machine_grawl_necklaces.AddState(name="WAITING OUTPOST MAP",
                       exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(),
                       transition_delay_ms=1500,
                       run_once=True
)
#ICY LODESTONES
FSM_vars.state_machine_icy_lodestones.AddState(name="ARE WE IN HOGWARTS?", 
                       execute_fn=lambda: Map.Travel(bot_vars.foible_map),
                       exit_condition=lambda: LDoA_IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_icy_lodestones.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.foible_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.foible_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False)

FSM_vars.state_machine_icy_lodestones.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=3000)

FSM_vars.state_machine_icy_lodestones.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: useitem(30847),
                       run_once=False)

FSM_vars.state_machine_icy_lodestones.AddState(name="LUCKILY THERE IS A PRIEST",
                       execute_fn=lambda: handle_map_path_loot(FSM_vars.icy_lodestones_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.icy_lodestones_pathing, FSM_vars.movement_handler) or Survivor(),
                       run_once=False)

FSM_vars.state_machine_icy_lodestones.AddState(name="COUNTER", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - ICY LODESTONES FARM", "ADD COUNTER", Py4GW.Console.MessageType.Info),increment_run_counter()), 
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000,
                       run_once=True)


#ENCHANTED LODESTONES
FSM_vars.state_machine_lodestone.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - ENCHANTED LODESTONE FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.barradin_map,6,0)) if not Map.IsExplorable() else None,  
                       exit_condition=lambda: LDoA_IsOutpost() or Map.IsExplorable(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_lodestone.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_lodestone.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - ENCHANTED LODESTONE FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=3000)

FSM_vars.state_machine_lodestone.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - ENCHANTED LODESTONE FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_lodestone.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.enchanted_lodestone_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.enchanted_lodestone_pathing, FSM_vars.movement_handler),
                       run_once=False)

#RED IRIS FLOWERS
FSM_vars.state_machine_red_iris_flowers.AddState(name="ARE WE IN ASCALON?", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.ascalon_map,6,0)) if not Map.IsExplorable() else None,                                             
                       exit_condition=lambda: LDoA_IsOutpost() or Map.IsExplorable(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="GOING OUT ASCALON",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler) if not Map.IsExplorable() else None,
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler) or Map.IsExplorable(),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="RUNNING OUT OF TOWN",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "RUNNING OUT OF TOWN", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.R.value)) if not Map.IsExplorable() else None,
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_red_iris_flowers.AddState(name="WAITING EXPLORABLE MAP",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=2000)

FSM_vars.state_machine_red_iris_flowers.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="PATH 1",
                       execute_fn=lambda: handle_map_path_Red_Iris_Flower(FSM_vars.red_iris_flowers_pathing_1),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.red_iris_flowers_pathing_1, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="PATH 2",
                       execute_fn=lambda: handle_map_path_Red_Iris_Flower(FSM_vars.red_iris_flowers_pathing_2),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.red_iris_flowers_pathing_2, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="PATH 3",
                       execute_fn=lambda: handle_map_path_Red_Iris_Flower(FSM_vars.red_iris_flowers_pathing_3),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.red_iris_flowers_pathing_3, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="PATH 4",
                       execute_fn=lambda: handle_map_path_Red_Iris_Flower(FSM_vars.red_iris_flowers_pathing_4),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.red_iris_flowers_pathing_4, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="PATH 5",
                       execute_fn=lambda: handle_map_path_Red_Iris_Flower(FSM_vars.red_iris_flowers_pathing_5),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.red_iris_flowers_pathing_5, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_red_iris_flowers.AddState(name="COUNTER", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - RED IRIS FLOWERS FARM", "ADD COUNTER", Py4GW.Console.MessageType.Info),increment_run_counter()), 
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000,
                       run_once=True)

#SKELETAL LIMBS
FSM_vars.state_machine_skele_limbs.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKELETAL LIMBS", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.barradin_map,6,0)),  
                       exit_condition=lambda: LDoA_IsOutpost(),
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

#SKALE FINS
FSM_vars.state_machine_skale_fin.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKALE FIN FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.ranik_map,6,0)),  
                       exit_condition=lambda: LDoA_IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_skale_fin.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ranik_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranik_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_skale_fin.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKALE FIN FARM", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=5000)

FSM_vars.state_machine_skale_fin.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SKALE FIN FARM", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=False)

FSM_vars.state_machine_skale_fin.AddState(name="FARMING LODESTONES",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.skale_fin_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.skale_fin_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_skale_fin.AddState(name="COUNTER", 
    execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO  WORN BELTS", "ADD COUNTER", Py4GW.Console.MessageType.Info),increment_run_counter()), 
    exit_condition=lambda: Map.IsExplorable(),
    transition_delay_ms=1000,
    run_once=True)

FSM_vars.state_machine_skale_fin.AddState(
    name="RETURN TO TOWN",
    execute_fn=lambda: LDoA_TravelToOutpost(bot_vars.ranik_map),  # or your desired outpost map id
    exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(),
    transition_delay_ms=1000,
    run_once=True
)
FSM_vars.state_machine_skale_fin.AddState(
    name="WAITING OUTPOST MAP",
   exit_condition=lambda: Map.IsMapReady() and LDoA_IsOutpost() and Party.IsPartyLoaded(),
   transition_delay_ms=1500,
   run_once=True
)

#SPIDER LEGS
FSM_vars.state_machine_spider_leg.AddState(name="FORT RANIK", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - SPIDER LEGS FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.ranik_map,6,0)),  
                       exit_condition=lambda: LDoA_IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_spider_leg.AddState(name="MESSAGE", 
                       execute_fn=lambda: Py4GW.Console.Log("TH3KUM1KO - SPIDER LEGS FARM", "GOING OUT", Py4GW.Console.MessageType.Info),  
                       exit_condition=lambda: LDoA_IsOutpost(),
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
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - UNNATURAL SEEDS FARM", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.barradin_map,6,0)),  
                       exit_condition=lambda: LDoA_IsOutpost(),
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

#WORN BELTS
FSM_vars.state_machine_worn_belts.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - WORN BELTS", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.barradin_map,6,0)),  
                       exit_condition=lambda: LDoA_IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_worn_belts.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.barradin_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_worn_belts.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO -  TH3KUM1KO - WORN BELTS", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=3000)

FSM_vars.state_machine_worn_belts.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  TH3KUM1KO - WORN BELTS", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_worn_belts.AddState(name="FARMING WORN BELTS",
                       execute_fn=lambda:handle_map_path_loot(FSM_vars.worn_belts_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.worn_belts_pathing, FSM_vars.movement_handler) or Survivor(),
                       run_once=False)

FSM_vars.state_machine_worn_belts.AddState(name="COUNTER", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO  WORN BELTS", "ADD COUNTER", Py4GW.Console.MessageType.Info),increment_run_counter()), 
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000,
                       run_once=True)

#BAKED HUSKS
FSM_vars.state_machine_baked_husks.AddState(name="ASHFORD ABBEY", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GOING TO BAKED HUSKS", "MOVING TO ASHFORD ABBEY", Py4GW.Console.MessageType.Info),Py4GW.Console.Log("BAKED HUSKS", "Executing travel function", Py4GW.Console.MessageType.Info),Py4GW.Console.Log("BAKED HUSKS", f"Traveling to map ID: {bot_vars.abbey_map}", Py4GW.Console.MessageType.Info),LDoA_TravelToOutpost(bot_vars.abbey_map)),  
                       exit_condition=lambda: LDoA_IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_baked_husks.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.goingout_ashfordabbey, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_baked_husks.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GOING TO BAKED HUSKS", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=3000)

FSM_vars.state_machine_baked_husks.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GOING TO BAKED HUSKS", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_baked_husks.AddState(name="FARMING BAKED HUSKS",
                       execute_fn=lambda:handle_map_path_baked_husk(FSM_vars.baked_husk_pathing),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.baked_husk_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_baked_husks.AddState(name="COUNTER", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO  BAKED HUSKS", "ADD COUNTER", Py4GW.Console.MessageType.Info),increment_run_counter()), 
                       exit_condition=lambda: Map.IsExplorable(),
                       transition_delay_ms=1000,
                       run_once=True)

#CHARR GATE OPENER
FSM_vars.state_machine_charr_gate_opener.AddState(name="ASCALON", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - CHARR GATE OPENER", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.ascalon_map,6,0)) if not Map.IsExplorable() else None,  
                       exit_condition=lambda: LDoA_IsOutpost() or Map.IsExplorable(),
                       transition_delay_ms=2000,
                       run_once=True)

FSM_vars.state_machine_charr_gate_opener.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ascalon_pathing, FSM_vars.movement_handler) if not Map.IsExplorable() else None,
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ascalon_pathing, FSM_vars.movement_handler) or Map.IsExplorable(),
                       run_once=False)

FSM_vars.state_machine_charr_gate_opener.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO - CHARR GATE OPENER", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=3000)

FSM_vars.state_machine_charr_gate_opener.AddState(name="GOING TO LEVER",
                       execute_fn=lambda: handle_map_path_gate_opener(FSM_vars.charr_gate_opener_pathing_2),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.charr_gate_opener_pathing_2, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_charr_gate_opener.AddState(name="WAITING TO STABILIZE",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO - CHARR GATE OPENER", "WAITING TO STABILIZE BEFORE LEVER INTERACTION", Py4GW.Console.MessageType.Info), None),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_charr_gate_opener.AddState(name="INTERACTING WITH LEVER",
                       execute_fn=lambda: handle_gadget_interaction(),
                       transition_delay_ms=50,
                       run_once=True)

FSM_vars.state_machine_charr_gate_opener.AddState(name="WALKING TO PORTAL EDGE",
                       execute_fn=lambda: handle_map_path_gate_opener(FSM_vars.charr_gate_opener_fast_gate_run),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.charr_gate_opener_fast_gate_run, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_charr_gate_opener.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(),
                       transition_delay_ms=3000,
                       run_once=True)

#NICHOLAS SANDFORD
FSM_vars.state_machine_nicholas_sandford.AddState(name="BARRADIN", 
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GOING TO NICHOLAS SANDFORD", "MOVING TO A SAFER DISTRICT", Py4GW.Console.MessageType.Info),LDoA_TravelToDistrict(bot_vars.ranik_map,6,0)),  
                       exit_condition=lambda: LDoA_IsOutpost(),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_nicholas_sandford.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.ranik_goingtofarm_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.ranik_goingtofarm_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_nicholas_sandford.AddState(name="WAITING YOUR SLOW PC TO LOAD",
                       exit_condition=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GOING TO NICHOLAS SANDFORD", "WAITING FOR EXPLORABLE MAP", Py4GW.Console.MessageType.Info),Map.IsExplorable()),
                       transition_delay_ms=3000)

FSM_vars.state_machine_nicholas_sandford.AddState(name="HEY THERE IS A FIRE ALLY",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  TH3KUM1KO - GOING TO NICHOLAS SANDFORD", "USING FIRE STONE", Py4GW.Console.MessageType.Info), useitem(30847)),
                       run_once=True)

FSM_vars.state_machine_nicholas_sandford.AddState(name="GOING OUT IN DANGEROUS LANDS",
                       execute_fn=lambda:Routines.Movement.FollowPath(FSM_vars.nicholas_sandford_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.nicholas_sandford_pathing, FSM_vars.movement_handler),
                       run_once=False)

FSM_vars.state_machine_nicholas_sandford.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GOING TO NICHOLAS SANDFORD", "INTERACTING WITH NICHOLAS SANDFORD WITH V", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.V.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_nicholas_sandford.AddState(name="INTERACTING WITH TOWN CRIER",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GOING TO NICHOLAS SANDFORD", "INTERACTING WITH NICHOLAS SANDFORD WITH SPACE", Py4GW.Console.MessageType.Info),Keystroke.PressAndRelease(Key.Space.value)),
                       transition_delay_ms=1000,
                       run_once=True)

FSM_vars.state_machine_nicholas_sandford.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GOING TO NICHOLAS SANDFORD", "TAKING GIFTS FROM NICHOLAS SANDFORD", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x85", 16))),
                       transition_delay_ms=100,
                       run_once=True)

FSM_vars.state_machine_nicholas_sandford.AddState(name="TAKING QUEST",
                       execute_fn=lambda: (Py4GW.Console.Log("TH3KUM1KO -  GOING TO NICHOLAS SANDFORD", "TAKING GIFTS FROM NICHOLAS SANDFORD", Py4GW.Console.MessageType.Info),Player.SendDialog(int("0x86", 16))),
                       transition_delay_ms=100,
                       run_once=True)


#STATS MANAGER
class InventoryTracker:
    def __init__(self):
        self.initial_quantities = {} 
        self.tracked_model_ids = {  
            ModelID.Vial_Of_Dye: "VIALS OF DYE",
            ModelID.Spider_Leg: "SPIDER LEGS",
            ModelID.Charr_Carving: "CHARR CARVINGS",
            ModelID.Icy_Lodestone: "ICY LODESTONES",
            ModelID.Dull_Carapace: "DULL CARAPACES",
            ModelID.Gargoyle_Skull: "GARGOYLE SKULLS",
            ModelID.Worn_Belt: "WORN BELTS",
            ModelID.Unnatural_Seed: "UNNATURAL SEEDS",
            ModelID.Skale_Fin_PreSearing: "SKALE FINS",
            ModelID.Skeletal_Limb: "SKELETAL LIMBS",
            ModelID.Enchanted_Lodestone: "ENCHANTED LODESTONES",
            ModelID.Grawl_Necklace: "GRAWL NECKLACES",
            ModelID.Baked_Husk: "BAKED HUSKS",
            ModelID.Red_Iris_Flower: "RED IRIS FLOWERS",
            ModelID.Gift_Of_The_Huntsman: "GIFTS OF THE HUNTSMAN"
        }

    def initialize(self):
        self.initial_quantities = {}
        try:
            bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)  
            item_array = ItemArray.GetItemArray(bags_to_check)

            for item_id in item_array:
                model_id = Item.GetModelID(item_id)
                if model_id in self.tracked_model_ids: 
                    quantity = Item.Properties.GetQuantity(item_id)
                    self.initial_quantities[model_id] = self.get_count_items().get(model_id, 0)
        except Exception as e:
            Py4GW.Console.Log("INVENTORY TRACKER", f"Error initializing: {e}", Py4GW.Console.MessageType.Warning)

    def get_count_items(self):
        count_items = {model_id: 0 for model_id in self.tracked_model_ids}
        try:
            bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
            item_array = ItemArray.GetItemArray(bags_to_check)
            
            for item_id in item_array:
                model_id = Item.GetModelID(item_id)
                if model_id in self.tracked_model_ids:
                    quantity = Item.Properties.GetQuantity(item_id)
                    count_items[model_id] += max(0, quantity)
        except Exception as e:
            Py4GW.Console.Log("INVENTORY TRACKER", f"Error counting items: {e}", Py4GW.Console.MessageType.Warning)

        return count_items

    def get_farmed_items(self):
        farmed_items = {model_id: 0 for model_id in self.tracked_model_ids}  
        try:
            bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
            item_array = ItemArray.GetItemArray(bags_to_check)

            for item_id in item_array:
                model_id = Item.GetModelID(item_id)
                if model_id in self.tracked_model_ids:  
                    initial_quantity = self.initial_quantities.get(model_id, 0)
                    current_quantity = self.get_count_items().get(model_id, 0)
                    farmed_items[model_id] = max(0, current_quantity - initial_quantity)  
        except Exception as e:
            Py4GW.Console.Log("INVENTORY TRACKER", f"Error getting farmed items: {e}", Py4GW.Console.MessageType.Warning)

        return farmed_items

inventory_tracker = InventoryTracker()

def show_info_table_item():
    try:
        headers = ["ITEM NAME", "FARMED ITEMS / (COUNT)"] 

        farmed_items = inventory_tracker.get_farmed_items()  
        count_items = inventory_tracker.get_count_items()

        data = []
        
        for model_id, name in inventory_tracker.tracked_model_ids.items():
            farmed = farmed_items.get(model_id, 0)  
            count = count_items.get(model_id, 0)
            farmed_text = f"+{farmed}" if farmed > 0 else "0"
            count_text = f"{count}" if count > 0 else "0"
            farmed_text = f"{farmed_text} / ({count_text})"

            data.append((name, farmed_text))

        ImGui.table("INVENTARY", headers, data)
    except Exception as e:
        Py4GW.Console.Log("INVENTORY DISPLAY", f"Error showing inventory: {e}", Py4GW.Console.MessageType.Warning)



def increment_run_counter():
    global run_counter
    run_counter += 1  

def GetElapsedRunTime():
    if bot_vars.bot_started:
        return time.time() - start_time
    return 0  

level_experience = {
    1: 2000, 2: 4600, 3: 7800, 4: 11600, 5: 16000,
    6: 21000, 7: 26600, 8: 32800, 9: 39600, 10: 47000,
    11: 55000, 12: 63600, 13: 72800, 14: 82600, 15: 93000,
    16: 104000, 17: 115600, 18: 127800, 19: 140600, 20: 140600
}

def get_required_experience(level):
    return level_experience.get(level, 140600)

def show_info_table_run():
    headers_info = ["INFO", "DATA"]

    agent_id = Player.GetAgentID()
    level = Agent.GetLevel(agent_id)
    experience = Player.GetExperience()

    required_experience = get_required_experience(level)

    elapsed_time = GetElapsedRunTime()
    elapsed_time_formatted = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

    average_run_time = elapsed_time / run_counter if run_counter > 0 else 0
    average_run_time_formatted = time.strftime("%H:%M:%S", time.gmtime(average_run_time))



    data_info = [
        ("TIMER", elapsed_time_formatted),
        ("RUN COUNTER", str(run_counter)),
        ("AVERAGE RUN TIMER", average_run_time_formatted),
        ("LEVEL", f"{level}/20"),
        ("EXPERIENCE", f"{experience}/{required_experience}"),
    ]

    ImGui.table("PLAYER INFO", headers_info, data_info)


#GUI
def DrawWindow():
    global module_name
    global state
   
    try:
        if bot_vars.window_module.first_run:
            PyImGui.set_next_window_size(bot_vars.window_module.window_size[0], bot_vars.window_module.window_size[1])     
            PyImGui.set_next_window_pos(bot_vars.window_module.window_pos[0], bot_vars.window_module.window_pos[1])
            bot_vars.window_module.first_run = False

        if PyImGui.begin("\uf647  TH3KUM1KO'S PRESEARING BIBLE", bot_vars.window_module.window_flags):

            if PyImGui.begin_tab_bar("MainTabBar"): 
                if PyImGui.begin_tab_item("LDoA"):
                    PyImGui.spacing()
                    PyImGui.text_wrapped("WITH THESE FUNCTIONS, THE BOT WILL LEVEL UP YOUR CHARACTER BASED ON ITS PROFESSION, REACHING LEVEL 2 THROUGH THE INITIAL QUESTS. ONCE LEVEL 2 IS ACHIEVED, THE BOT WILL AUTOMATICALLY TAKE THE 'CHARR AT THE GATE' QUEST.")
                    state.radio_button_selected = PyImGui.radio_button(" \uf132 WARRIOR", state.radio_button_selected, 20)
                    PyImGui.same_line(200, -1.0)
                    state.radio_button_selected = PyImGui.radio_button(" \uf54c NECROMANCER", state.radio_button_selected, 23)
                    state.radio_button_selected = PyImGui.radio_button(" \uf1bb RANGER", state.radio_button_selected, 21)
                    PyImGui.same_line(200, -1.0)
                    state.radio_button_selected = PyImGui.radio_button(" \ue2ca MESMER", state.radio_button_selected, 24)
                    state.radio_button_selected = PyImGui.radio_button(" \uf644 MONK", state.radio_button_selected, 22)
                    PyImGui.same_line(200, -1.0)
                    state.radio_button_selected = PyImGui.radio_button(" \uf6e8 ELEMENTALIST", state.radio_button_selected, 25)
                    PyImGui.spacing()
                    PyImGui.text_wrapped("WITH THIS FUNCTION, THE BOT WILL LEAVE ASCALON USING THE 'CHARR AT THE GATE' QUEST, FOLLOW RURIK, AND WAIT FOR THE PRINCE TO KILL THREE CHARR BEFORE RETURNING TO THE CITY AND RESTARTING THE LOOP. THIS FUNCTION ENSURES SURVIVOR TITLE PROGRESSION.")
                    state.radio_button_selected = PyImGui.radio_button(" \uf443 LEVEL 2-10 - CHARR AT THE GATE", state.radio_button_selected, 0)
                    PyImGui.spacing()
                    PyImGui.text_wrapped("ONCE YOU REACH LEVEL 10, WAIT FOR THE ROTATION OF THE VANGUARD QUESTS UNTIL THE 'FARMER HAMNET' QUEST BECOMES AVAILABLE. THE BOT WILL KILL THE FIRST TWO MOBS OUTSIDE FOIBLE'S FAIR AND REPEAT THE LOOP UNTIL LEVEL 20. THIS FUNCTION ENSURES SURVIVOR TITLE PROGRESSION.")
                    state.radio_button_selected = PyImGui.radio_button(" \uf43f LEVEL 11-20 - FARMER HAMNET", state.radio_button_selected, 1) 
                    PyImGui.spacing()
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
                    PyImGui.spacing()
                    state.radio_button_selected = PyImGui.radio_button("\ue599 BAKED HUSKS", state.radio_button_selected, 6)
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
                    state.radio_button_selected = PyImGui.radio_button("\ue19b WORN BELTS", state.radio_button_selected, 18)
                    state.radio_button_selected = PyImGui.radio_button("\uf06b NICHOLAS SANDFORD", state.radio_button_selected, 26)
                    PyImGui.spacing()

                    if IsBotStarted():        
                        if PyImGui.button(" \uf04d   STOP"):
                            ResetEnvironment()
                            StopBot()
                    else:
                        if PyImGui.button(" \uf04b   START"):
                            ResetEnvironment()
                            StartBot()
                    PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("INVENTORY"):            
                    show_info_table_item()
                    PyImGui.spacing()
                    PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("MISC"):   
                        
                    state.radio_button_selected = PyImGui.radio_button("\uf6be TAME PET", state.radio_button_selected, 27)
                    state.radio_button_selected = PyImGui.radio_button("\uf70c CHARR GATE OPENER", state.radio_button_selected, 42)

                    if IsBotStarted():        
                        if PyImGui.button(" \uf04d   STOP"):
                            ResetEnvironment()
                            StopBot()
                    else:
                        if PyImGui.button(" \uf04b   START"):
                            ResetEnvironment()
                            StartBot()

                    PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("SKILLS"):  
                        PyImGui.spacing()                    
                        PyImGui.text_colored("\uf132 UNLOCK WARRIOR SKILL", (1.0, 1.0, 0.2, 1.0))
                        PyImGui.pop_style_color(1)
                        PyImGui.same_line(300, -1.0)
                        PyImGui.text_colored("\uf54c UNLOCK NECROMANCER SKILL", (0.0, 0.8, 0.3, 1.0))
                        PyImGui.pop_style_color(1)

                        state.radio_button_selected = PyImGui.radio_button(" \uf00c PRIMARY/SECONDARY REQUIRED##WARRIOR_REQ", state.radio_button_selected, 28)
                        PyImGui.same_line(300, -1.0)
                        state.radio_button_selected = PyImGui.radio_button(" \uf00c PRIMARY/SECONDARY REQUIRED##NECRO_REQ", state.radio_button_selected, 34)
                        state.radio_button_selected = PyImGui.radio_button(" \uf00d PRIMARY/SECONDARY NO REQ##WARRRIOR_NOREQ", state.radio_button_selected, 29)               
                        PyImGui.same_line(300, -1.0)
                        state.radio_button_selected = PyImGui.radio_button(" \uf00d PRIMARY/SECONDARY NO REQ##NECRO_NOREQ", state.radio_button_selected, 35)

                        PyImGui.text_colored("\uf1bb UNLOCK RANGER SKILL", (1.0, 0.5, 0.0, 1.0))
                        PyImGui.pop_style_color(1)
                        PyImGui.same_line(300, -1.0)
                        PyImGui.text_colored("\ue2ca UNLOCK MESMER SKILL", (1.0, 0.1, 0.8, 1.0))
                        PyImGui.pop_style_color(1)

                        state.radio_button_selected = PyImGui.radio_button(" \uf00c PRIMARY/SECONDARY REQUIRED##RANGER_REQ", state.radio_button_selected, 30)
                        PyImGui.same_line(300, -1.0)
                        state.radio_button_selected = PyImGui.radio_button(" \uf00c PRIMARY/SECONDARY REQUIRED##MESMER_REQ", state.radio_button_selected, 36)
                        state.radio_button_selected = PyImGui.radio_button(" \uf00d PRIMARY/SECONDARY NO REQ##RANGER_NOREQ", state.radio_button_selected, 31)               
                        PyImGui.same_line(300, -1.0)
                        state.radio_button_selected = PyImGui.radio_button(" \uf00d PRIMARY/SECONDARY NO REQ##MESMER_NOREQ", state.radio_button_selected, 37)

                        PyImGui.text_colored("\uf644 UNLOCK MONK SKILL", (0.2, 1.0, 1.0, 1.0))
                        PyImGui.pop_style_color(1)
                        PyImGui.same_line(300, -1.0)
                        PyImGui.text_colored("\uf6e8 UNLOCK ELEMENTALIST SKILL", (1.0, 0.0, 0.2, 1.0))  
                        PyImGui.pop_style_color(1)

                        state.radio_button_selected = PyImGui.radio_button(" \uf00c PRIMARY/SECONDARY REQUIRED##MONK_REQ", state.radio_button_selected, 32)
                        PyImGui.same_line(300, -1.0)
                        state.radio_button_selected = PyImGui.radio_button(" \uf00c PRIMARY/SECONDARY REQUIRED##ELEMENTALIST_REQ", state.radio_button_selected, 38)
                        state.radio_button_selected = PyImGui.radio_button(" \uf00d PRIMARY/SECONDARY NO REQ##MONK_NOREQ", state.radio_button_selected, 33)               
                        PyImGui.same_line(300, -1.0)
                        state.radio_button_selected = PyImGui.radio_button(" \uf00d PRIMARY/SECONDARY NO REQ##ELEMENTALIST_NOREQ", state.radio_button_selected, 39)
                        PyImGui.spacing()


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
                    show_info_table_run()
                    PyImGui.spacing()
                    PyImGui.end_tab_item()

        
        PyImGui.end()

    except Exception as e:
        frame = inspect.currentframe()
        current_function = frame.f_code.co_name if frame else "Unknown"
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Error in {current_function}: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def main():
    global bot_vars, FSM_vars, inventory_tracker
    try:
        # Global safety check - prevent any bot operation if game isn't ready
        try:
            if not Map.IsMapReady() or Player.GetAgentID() <= 0:
                # Don't log every frame, just return silently
                return
        except Exception as e:
            # If we can't even check basic game state, something is wrong
            return
            
        if Party.IsPartyLoaded() and Map.IsMapReady():
            DrawWindow()

        if not inventory_tracker.initial_quantities: 
            inventory_tracker.initialize() 

        if IsBotStarted():

            inventory_tracker.get_farmed_items()  
            
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
                    StopBot()
                else:
                    FSM_vars.state_machine_abbey.update()

            # FOIBLE'S FAIR TRAVEL      
            elif state.radio_button_selected == 3:  
                if FSM_vars.state_machine_foible.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_foible.update()
                    
            # FORT RANIK TRAVEL      
            elif state.radio_button_selected == 4:  
                if FSM_vars.state_machine_ranik.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_ranik.update()
                    
            # THE BARRADIN ESTATE TRAVEL      
            elif state.radio_button_selected == 5:  
                if FSM_vars.state_machine_barradin.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_barradin.update()
                    
            # THE GRAND TOUR     
            elif state.radio_button_selected == 19:  
                if FSM_vars.state_machine_grandtour.is_finished():
                    ResetEnvironment()
                    StopBot()
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

             # UNNATURAL SEEDS  
            elif state.radio_button_selected == 18:  
                if FSM_vars.state_machine_worn_belts.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_worn_belts.update()   

            # BAKED HUSKS  
            elif state.radio_button_selected == 6:  
                if FSM_vars.state_machine_baked_husks.is_finished():
                    ResetEnvironment()
                else:
                    FSM_vars.state_machine_baked_husks.update()   

            # NICHOLAS SANDFORD  
            elif state.radio_button_selected == 26:  
                if FSM_vars.state_machine_nicholas_sandford.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_nicholas_sandford.update()

            # TAME PET 
            elif state.radio_button_selected == 27:  
                if FSM_vars.state_machine_TamePet.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_TamePet.update()

            # CHARR GATE OPENER (MISC TAB)
            elif state.radio_button_selected == 42:  # (or whatever value is for Charr Gate Opener)
                if FSM_vars.state_machine_charr_gate_opener.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_charr_gate_opener.update()

            # WARRIOR REQ 
            elif state.radio_button_selected == 28:  
                if FSM_vars.state_machine_warrior_req.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_warrior_req.update()

            # WARRIOR NO REQ 
            elif state.radio_button_selected == 29:  
                if FSM_vars.state_machine_warrior_noreq.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_warrior_noreq.update()                    

            # RANGER  REQ 
            elif state.radio_button_selected == 30:  
                if FSM_vars.state_machine_ranger_req.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_ranger_req.update()     

            # RANGER NO REQ 
            elif state.radio_button_selected == 31:  
                if FSM_vars.state_machine_ranger_noreq.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_ranger_noreq.update()  

            # MONK  REQ 
            elif state.radio_button_selected == 32:  
                if FSM_vars.state_machine_monk_req.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_monk_req.update()     

            # MONK NO REQ 
            elif state.radio_button_selected == 33:  
                if FSM_vars.state_machine_monk_noreq.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_monk_noreq.update()  

            # NECRO  REQ 
            elif state.radio_button_selected == 34:  
                if FSM_vars.state_machine_necro_req.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_necro_req.update()     

            # NECRO NO REQ 
            elif state.radio_button_selected == 35:  
                if FSM_vars.state_machine_necro_noreq.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_necro_noreq.update()  
        if not IsBotStarted():
            inventory_tracker.initialize()

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

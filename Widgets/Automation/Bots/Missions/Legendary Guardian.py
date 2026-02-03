from Py4GWCoreLib import*
import time

#VARIABLES
module_name = "TH3KUM1KO'S LEGENDARY GUARDIAN BOT"

class AppState :
    def __init__(self) :
        self.radio_button_selected = 0
        self.combo_selected_1 = 30
        self.combo_selected_2 = 31
        self.combo_selected_3 = 32
        self.combo_selected_4 = 33
        self.combo_selected_5 = 34
        self.combo_selected_6 = 35
        self.combo_selected_7 = 36
        self.checkbox_state_1 = False
        self.checkbox_state_2 = False
        self.checkbox_state_3 = False
        self.checkbox_state_4 = False
        self.checkbox_state_5 = False

state = AppState()

class GameAreas:
    def __init__(self):
        self.Touch = 144
        self.Adjacent = 166
        self.Nearby = 252
        self.Area = 322
        self.Earshot = 1012
        self.Spellcast = 1248
        self.Spirit = 2500
        self.Compass = 5000

area_distance = GameAreas()

class BotVars:
    def __init__(self, map_id=0):
        self.bot_started = False
        self.window_module:ImGui.WindowModule
        self.variables = {}

        #HEROES SECTION
        self.koss = 6
        self.goren = 2
        self.jora = 18
        self.acolyte_jin = 5
        self.margrid_the_sly = 12
        self.pyre_fierceshot = 19
        self.tahlkora = 3
        self.dunkoro = 7
        self.ogden_stonehealer = 27
        self.master_of_whispers = 4
        self.olias = 14
        self.livia = 21
        self.norgu = 1
        self.gwen = 24
        self.acolyte_sousuke = 8
        self.zhed_shadowhoof = 10
        self.vekk = 26
        self.zenmai = 13
        self.anton = 20
        self.miku = 36
        self.xandra = 25
        self.zei_ri = 37
        self.razah = 15
        self.general_morgahn = 11
        self.keiran_thackeray = 17
        self.hayda = 22
        self.melonni = 9
        self.mox = 16
        self.kahmu = 23
        self.mercenary_1 = 28
        self.mercenary_2 = 29
        self.mercenary_3 = 30
        self.mercenary_4 = 31
        self.mercenary_5 = 32
        self.mercenary_6 = 33
        self.mercenary_7 = 34
        self.mercenary_8 = 35

        #TITLES
        self.Deldrimor_id = 39
        self.Asura_id = 38
        self.Vanguard_Title = 40

        #THE GREAT NORTHERN WALL
        self.TheGreatNorthernWall = 28
        self.TheGreatNorthernWall_CoordinateList_1 =[(5770, -12799),(5085, -12095)]
        self.TheGreatNorthernWall_CoordinateList_2 =[(6269, -10220),(3830, -6054),(1387, -4164),(-906, -4404),(-2681, -3745),(-3085, -3264),(-3723, -571),(-2779, 564),(-2638, 2329),(-3389, 4087)]
        self.TheGreatNorthernWall_CoordinateList_3 =[(-5649, 5018),(-8075, 4441),(-9222, 5128),(-11310, 6711)]
        self.TheGreatNorthernWall_CoordinateList_4 =[(-10558, 7708),(-8964, 9797),(-7750, 11127),(-5940, 11081),(-5507, 11167),(-4816, 9922),(-5226, 7795)]
        self.TheGreatNorthernWall_CoordinateList_5 =[(-3666, 10811),(-4721, 13321),(-5707, 14442),(-5494, 15835),(-7308, 15897),(-7982, 14823),(-8886, 14078),(-7909, 14186)]
        self.TheGreatNorthernWall_CoordinateList_6 =[(-8974, 14371),(-7386, 16049),(-5739, 18268),(-3350, 17785),(-3050, 19476),(-2293, 19035)]
        self.TheGreatNorthernWall_CoordinateList_7 =[(282, 18305),(1223, 16793),(-470, 14762),(-217, 14295)]
        self.TheGreatNorthernWall_CoordinateList_8 =[(-477, 15126),(1404, 17353),(-1192, 19559),(-3019, 19725),(-3353, 17674),(-5203, 18650),(-7450, 16834),(-7751, 15058),(-9977, 13941),(-12866, 11817),(-16775, 11870),(-16915, 15220),(-14498, 12744)]
        self.TheGreatNorthernWall_CoordinateList_9 =[(-14464, 4187),(-8647, 79),(-7699, -2235),(-2332, -5860),(2899, -7794),(6334, -10506),(4961, -12069)]

        #FORT RANIK
        self.FortRanik = 29
        self.FortRanik_CoordinateList_1 =[(-4509, -28034),(-3951, -24822),(-3493, -20759),(-4274, -18566),(-5095, -17266),(-4535, -14566),(-3230, -14440),(-3351, -15873),(-2320, -11885),(-893, -9440)]
        self.FortRanik_CoordinateList_2 =[(-268, -9207),(1494, -7661),(2317, -6770),(3687, -7241),(6062, -6875),(6166, -5851),(3521, -5748),(2980, -4783),(852, -4244),(-1442, -2267),(-1676, -1097),(-550, 40),(1179, 86),(4965, -591),(5266, 3501),(6663, 1358),(6882, -1108),(6641, -1894)]
        self.FortRanik_CoordinateList_3 =[(6736, -1393),(6664, 1229),(5244, 3467),(2586, 5261),(1581, 6169),(-629, 8833),(-1227, 10178),(-2600, 12093),(-1349, 12823),(425, 13412),(1356, 15415),(1909, 15695)]
        self.FortRanik_CoordinateList_4 =[(2905, 16950),(2434, 17931),(3942, 18006)]
        self.FortRanik_CoordinateList_5 =[(2993, 16988),(2111, 15657)]
        self.FortRanik_CoordinateList_5a =[(2993, 16988),(2111, 15657)]
        self.FortRanik_CoordinateList_6 =[(2907, 16873),(4414, 15004)]
        self.FortRanik_CoordinateList_7 =[(863, 14732),(2578, 12828)]
        self.FortRanik_CoordinateList_8 =[(3082, 12586),(1102, 14612),(2014, 15649)]
        self.FortRanik_CoordinateList_9 =[(124, 16756),(1034, 20924),(-3575, 16829),(-4531, 16479),(-1934, 18277),(-1173, 19370),(-2346, 19174)]
        self.FortRanik_CoordinateList_10 =[(-2022, 18352),(-4317, 17500),(-6316, 18870),(-5866, 19400),(-5751, 19565)]

        #RUINS OF SURMIA
        self.RuinsOfSurmia = 30
        self.RuinsOfSurmia_CoordinateList_1 = [(-3134, -11907),(-757, -9155),(-2201, -7296),(-3836, -6823),(-4563, -5380),(-3317, -3312),(-3241, -1427),(-2494, -1064),(511, -1986),(1722, -2407),(1452, -5264),(1192, -5849),(3018, -5996),(3984, -5088),(5588, -3456),(6426, -2619),(7665, -1797),(9613, -960),(8411, 1302),(5262, 2613),(3739, 5010),(4968, 7155),(5189, 9432),(2392, 8745),(2052, 9693),(815, 8927),(-1032, 10584),(-2099, 9370),(-2432, 4909),(-3564, 3990),(-6342, 5354),(-8419, 6968),(-6781, 9177),(-5935, 9889),(-3815, 12283),(-3180, 13705),(-2099, 13993),(-1717, 14800),(-2174, 15096),(-2160, 15089)]
        self.RuinsOfSurmia_CoordinateList_2 = [(-1923, 16707),(-3878, 18778),(-1989, 20932),(3077, 20568),(526, 19680)]
        self.RuinsOfSurmia_CoordinateList_3 = [(4614, 18013),(7719, 18626),(7717, 20293)]
        self.RuinsOfSurmia_CoordinateList_4 = [(8028, 18967),(5503, 17839),(1339, 18994),(-1007, 20385),(-3153, 20615)]
        self.RuinsOfSurmia_CoordinateList_5 = [(-4701, 20894),(-6913, 22295),(-8881, 22737)]
        self.RuinsOfSurmia_CoordinateList_6 = [(-9321, 20289),(-9425, 20877)]
        self.RuinsOfSurmia_CoordinateList_7 = [(-8762, 18662),(-8750, 16236),(-8639, 14939),(-9964, 15661),(-10586, 15016),(-8691, 17377),(-9343, 20921),(-9514, 23782),(-8283, 26688),(-5322, 24590),(-4350, 23575),(-1529, 24962),(-1050, 26782),(1816, 26854),(2162, 25389),(4586, 22435)]
        self.RuinsOfSurmia_CoordinateList_8 = [(9547, 23274),(9808, 26873),(10303, 28840),(9139, 31260),(8864, 32894),(6078, 32276),(5193, 33954),(3194, 33730),(2884, 32442),(2193, 34006),(492, 33767),(3158, 32877),(3026, 34856)]

        #NOLANI ACADEMY
        self.NolaniAcademy = 32
        self.NolaniAcademy_CoordinateList_1 =  [(-1574, 13049),(-2068, 11923),(632, 12809),(926, 11537),(4182, 16510),(5340, 15805),(7607, 18436),(7477, 15773),(6115, 14469),(8271, 13981),(8666, 12340),(10757, 9198),(11136, 7810),(12649, 6572),(10855, 4763),(10591, 1549)]
        self.NolaniAcademy_CoordinateList_2 =  [(9785, 4132),(7403, 5689),(5922, 5479),(6803, 2028),(6096, -836),(3755, -642),(-2357, -1731),(-3935, -503),(-5950, -242),(-7130, -1956),(-7682, -3219),(-8180, -4032),(-10026, -5372),(-11215, -5981),(-12478, -6389),(-13451, -5990)]
        self.NolaniAcademy_CoordinateList_3 =  [(-12489, -6389),(-10366, -5642),(-8082, -3865),(-6798, -1585),(-4298, -480),(-477, -69),(-868, 2334),(-3078, 3708),(-2028, 5164),(-770, 5850),(569, 5991),(930, 6545),(-648, 7387),(505, 8301),(-578, 9450),(-40, 13106),(446, 9158),(-679, 5803),(-3012, 3694),(-843, 445),(497, -1231)]
        self.NolaniAcademy_CoordinateList_4 =  [(4957, -2770),(7089, -4433),(9589, -5261),(11418, -5969),(13170, -10593),(12881, -13551),(11153, -12164),(11588, -10834),(10659, -8359)]
        self.NolaniAcademy_CoordinateList_5 =  [(8941, -7633),(7915, -8596),(7756, -9062),(6937, -10029),(7215, -12938),(9266, -13663),(9152, -16193),(7849, -17079),(6592, -16976),(5460, -13213)]

        #BORLIS PASS
        self.BorlisPass = 25
        self.BorlisPass_CoordinateList_1 = [(20227, 1541),(19962, 1637)]
        self.BorlisPass_CoordinateList_2 = [(19842, 1489),(19609, 1500)]
        self.BorlisPass_CoordinateList_3 = [(19665, 4006),(19552, 5692),(19176, 5398)]
        self.BorlisPass_CoordinateList_4 = [(19508, 5626),(18293, 7239),(17844, 7557)]
        self.BorlisPass_CoordinateList_5 = [(18182, 7315),(16781, 4765),(16218, 4264)]
        self.BorlisPass_CoordinateList_6 = [(16640, 4425),(15531, 1983),(13809, 1103),(13758, 1883)]
        self.BorlisPass_CoordinateList_7 = [(13140, 14),(12537, -1737),(12382, -1914)]
        self.BorlisPass_CoordinateList_8 = [(12679, -1669),(13842, -3549),(14060, -3808)]
        self.BorlisPass_CoordinateList_9 = [(13745, -3559),(11766, -4674)]
        self.BorlisPass_CoordinateList_10 = [(9669, -4305),(7918, -1634),(8236, 1326)]
        self.BorlisPass_CoordinateList_11 = [(6803, 1438),(5296, 2781),(3043, 2752)]
        self.BorlisPass_CoordinateList_12 = [(2143, 2869),(508, 2609),(-1339, 3485),(-945, 963),(-269, -2034),(63, -3779),(1846, -4346),(2211, -3299)]
        self.BorlisPass_CoordinateList_13 = [(2029, -4688),(931, -7135)]
        self.BorlisPass_CoordinateList_14 = [(962, -7345),(992, -7544)]
        self.BorlisPass_CoordinateList_15 = [(1024, -6698),(1949, -4987),(2225, -3287)]
        self.BorlisPass_CoordinateList_16 = [(1798, -5971),(2059, -6771)]
        self.BorlisPass_CoordinateList_17 = [(1804, -5832),(2224, -3289)]
        self.BorlisPass_CoordinateList_18 = [(1844, -6066),(1589, -6330),(957, -7113),(1376, -8041)]
        self.BorlisPass_CoordinateList_19 = [(2153, -9157),(3803, -9267),(5687, -8775),(9528, -9258),(12841, -8930),(14689, -8597),(16665, -8868),(14088, -8314),(9424, -9293),(5233, -8761),(2264, -9161),(931, -6777),(2219, -3305)]
        self.BorlisPass_CoordinateList_20 = [(-243, -4082),(-304, -4348)]
        self.BorlisPass_CoordinateList_21 = [(-878, -5419),(-2756, -5098),(-6123, -4629),(-9086, -5156),(-9632, -3483),(-9235, -2395),(-8921, -2098),(-10321, -1970),(-10230, -1476),(-9821, -703),(-9585, 438),(-8285, 4479)]
        self.BorlisPass_CoordinateList_22 = [(-14170, 6066),(-18092, 4544),(-17622, 1374),(-15412, -2347),(-12931, -5663),(-13886, -7909),(-13857, -10528),(-13113, -10941),(-13161, -10022),(-12800, -10082)]
        self.BorlisPass_CoordinateList_23 = [(-13230, -10043),(-13019, -11045),(-11922, -11160),(-12072, -10726)]
        self.BorlisPass_CoordinateList_24 = [(-11798, -11222),(-11400, -9351),(-11888, -9762)]

        #THE FROST GATE
        self.TheFrostGate = 21
        self.TheFrostGate_CoordinateList_1 = [(1720, 28972),(168, 28288),(-1465, 27585),(-1951, 28577),(-1909, 25013),(1194, 23147),(242, 21414),(-148, 19251),(-71, 17464),(-1630, 16762),(703, 17318),(1820, 16166),(5426, 15486),(6232, 15248),(5210, 14187),(5451, 10523),(4816, 7274),(2317, 7151),(-806, 5526),(-1998, 5142),(-878, 5434),(2583, 7239),(5613, 6794),(8484, 4713),(8257, 2209),(5747, 1227),(5675, 550),(7356, -653),(6945, -3393),(8537, -3983),(9304, -3891)]
        self.TheFrostGate_CoordinateList_2 = [(7209, -3653),(7653, -932),(4971, 761),(1751, -413),(2511, -2755),(-780, -3301),(-3421, -2827),(-4321, -6118),(-6091, -8170),(-3667, -8449),(-4053, -8360),(-4815, -6523),(-5994, -8280),(-3733, -8425)]
        self.TheFrostGate_CoordinateList_3 = [(-5957, -7875),(-4199, -4686),(-3194, -2666),(-2378, -3149),(151, -6084),(386, -6575),(1342, -6572),(3938, -6521),(5283, -6559),(7172, -7936)]
        self.TheFrostGate_CoordinateList_4 = [(5058, -6409),(423, -6364),(-2423, -3094),(-3549, -2917),(-4815, -6523),(-5994, -8280),(-3733, -8425)]
        self.TheFrostGate_CoordinateList_5 = [(-5959, -7940),(-3211, -2798),(-2144, -3333),(216, -6443),(609, -7518)]
        self.TheFrostGate_CoordinateList_6 = [(4612, -11827),(5586, -15381),(5010, -14724)]
        self.TheFrostGate_CoordinateList_7 = [(5391, -15153),(5255, -15812),(2952, -16918),(686, -19303),(-75, -19842)]
        self.TheFrostGate_CoordinateList_8 = [(492, -19859),(867, -21573),(400, -21817)]
        self.TheFrostGate_CoordinateList_9 = [(854, -21383),(-925, -20509),(-1917, -19896),(-2181, -20154)]

        #GATES OF KRYTA
        self.GatesOfKryta = 14
        self.GatesOfKryta_CoordinateList_1 = [(2650, 22275),(2654, 18548),(4844, 17439)]
        self.GatesOfKryta_CoordinateList_2 = [(2900, 18428),(1781, 16370),(885, 15728),(-784, 17210),(-1560, 20907),(-2380, 22282),(-3630, 21823),(-4540, 17267),(-5029, 16380),(-6306, 14815),(-7976, 13057),(-8520, 11080),(-8365, 9465),(-6344, 8576),(-8333, 4189),(-8280, 1138),(-6495, -2275)]
        self.GatesOfKryta_CoordinateList_3 = [(-7659, -1678),(-9032, -260)]
        self.GatesOfKryta_CoordinateList_4 = [(-7794, -1604),(-8508, -4074),(-7545, -7102),(-6824, -8185),(-2839, -10834),(-902, -13301),(-424, -14420),(1106, -13337),(2895, -9493),(1463, -6259),(-1163, -3790),(-2817, -659),(-1068, 1818),(2072, 3513),(769, 4981),(-3592, 7218),(-3593, 8574),(-3062, 8768)]
        self.GatesOfKryta_CoordinateList_5 = [(-3756, 8355),(-3154, 6633),(1224, 4814),(1711, 2861),(-1224, 1570),(-2918, -916),(-1086, -4015),(1500, -6418),(2918, -9605),(806, -13619),(-862, -14250),(-1887, -11777),(-7256, -7651),(-8466, -3590),(-6387, -2165),(-5987, -1871)]
        self.GatesOfKryta_CoordinateList_6 = [(-8483, -3477),(-7441, -7498),(-2986, -10872),(258, -12823),(2624, -13785),(4761, -14157),(7464, -14286),(9776, -13692)]
        self.GatesOfKryta_CoordinateList_7 = [(10787, -11322),(11704, -9324),(12872, -8430),(12878, -4664),(10735, -1168),(9238, 2055),(10374, 4343),(11928, 5153),(13713, 6858),(13901, 8362),(12103, 8893),(9874, 9194),(11809, 10487),(13073, 11739),(14064, 13252),(14302, 14361),(11474, 6271)]

        #GATES OF KRYTA
        self.DAlessioSeabord = 15
        self.DAlessioSeabord_CoordinateList_1 = [(20076, 6497),(21070, 4409),(20377, 2544),(17922, 1885),(19012, -652),(16880, -3384),(15260, -3817),(13516, -3152),(11212, -262),(9635, 953),(11365, -686),(8919, -2025),(9573, -3534),(7542, -400),(7955, -2269)]
        self.DAlessioSeabord_CoordinateList_2 = [(7695, -583),(8928, 1582),(8860, 3190),(10109, 3501),(9571, 5072)]
        self.DAlessioSeabord_CoordinateList_3 = [(10287, 6829),(9242, 8149),(11227, 8273),(8764, 11561),(8006, 14164),(5996, 14544),(3564, 13113),(1882, 13100),(2301, 14791),(524, 14035),(-1208, 12964),(-4630, 12177),(-6241, 13935),(-9696, 13233),(-10537, 13322),(-11626, 12510)]
        self.DAlessioSeabord_CoordinateList_4 = [(-10221, 13260),(-9482, 12302)]
        self.DAlessioSeabord_CoordinateList_5 = [(-9671, 11209),(-9740, 8390),(-8995, 5916),(-5817, 4232),(-6421, 3043),(-10889, 2573)]
        self.DAlessioSeabord_CoordinateList_6 = [(-12358, 4289),(-13863, 3011),(-14967, 1859),(-16700, 4012),(-16675, 5184),(-18361, 6664),(-20379, 6354),(-20760, 7156),(-20382, 8588),(-20802, 11120),(-19839, 12080),(-20139, 13459),(-19235, 14031),(-16127, 14383),(-15121, 14177),(-14777, 13577)]
        self.DAlessioSeabord_CoordinateList_7 = [(-16806, 13253),(-17844, 13968),(-19695, 13918),(-20150, 12918),(-21069, 10842),(-20294, 8241),(-20850, 6699),(-19666, 5965),(-19572, 3172),(-19939, 1515),(-19296, 594),(-21545, -931),(-22579, -2175),(-23864, -2795)]

        #DIVINITY COAST
        self.DivinityCoast = 16
        self.DivinityCoast_CoordinateList_1 = [(16689, -6138),(16723, -3945),(20771, -3354),(21665, 2231),(18792, 2665),(17340, 3449),(14742, 7230),(15843, 9778),(16969, 11061),(17002, 12752),(17734, 13559)]
        self.DivinityCoast_CoordinateList_2 = [(16965, 12672),(17207, 11014),(18264, 10118),(19123, 9635),(19895, 10323),(21625, 12481),(22779, 10649),(22307, 9524),(22377, 9321),(21999, 9398),(21526, 10244),(21012, 9190),(20266, 10855),(19285, 9894),(18273, 10089),(16986, 11103),(17099, 13126),(17770, 13623)]
        self.DivinityCoast_CoordinateList_3 = [(16421, 13052),(14392, 12452),(12732, 12158),(8627, 12203),(7140, 11155),(7734, 8766),(9862, 6768),(8848, 1669),(5427, 1429)]
        self.DivinityCoast_CoordinateList_4 = [(2848, 975),(-1790, 177)]
        self.DivinityCoast_CoordinateList_5 = [(379, -3050),(790, -6371),(706, -6549),(3, -6335),(957, -5167),(33, -2445),(-2014, 434),(-2346, -643),(-4047, -2561),(-4940, -2807),(-6727, -6181),(-7053, -7798),(-8353, -9308),(-9988, -9413),(-10832, -9316),(-13725, -5054),(-15867, -5332),(-18594, -5882),(-20789, -6035),(-19494, -4101),(-21877, -2145),(-21233, 1215),(-20360, 2920),(-18000, 3063),(-17627, 4303),(-17669, 6227),(-17508, 7583),(-18000, 8094),(-16595, 11324),(-14924, 11756),(-13161, 11730),(-11961, 9901),(-11106, 9312),(-9014, 8537),(-7824, 10365)]
        self.DivinityCoast_CoordinateList_6 = [(-8144, 10744),(-8618, 11888)]

        #THE WILDS
        self.TheWilds = 11
        self.TheWilds_CoordinateList_1 = [(15697, -9078),(15993, -6660),(16228, -4981),(14238, -5132),(13663, -5325),(11794, -8248),(10462, -10732),(10117, -12495),(8546, -12935),(7207, -12876),(4647, -12872),(2748, -12521),(823, -12575),(58, -12561)]
        self.TheWilds_CoordinateList_2 = [(-1228, -12699),(-1858, -12620)]
        self.TheWilds_CoordinateList_3 = [(20, -12495),(3096, -12485),(7033, -12735),(9614, -12965),(10512, -11547),(11784, -8232),(12155, -5416),(9623, -6161),(8933, -7661),(7535, -7409),(5673, -6493),(5133, -3941),(3649, -1840),(3722, 44),(3173, 376),(1526, 166),(2321, 2003)]
        self.TheWilds_CoordinateList_4 = [(2321, 2003),(4200, 2852),(5667, 3875),(7624, 6976),(9377, 7617),(9881, 8479),(10097, 9780),(9921, 11564),(11291, 11787),(12270, 13293)]
        self.TheWilds_CoordinateList_5 = [(13834, 12693),(14179, 10825),(13669, 9083),(13709, 7733),(14523, 6434),(14347, 5559),(13347, 4631),(13789, 3300),(13411, 1093),(13863, 3533),(14000, 6810),(13821, 9510),(14270, 11335),(13738, 12805),(12026, 13269),(10959, 11668),(8409, 11079),(6560, 10769),(2668, 8143),(1457, 6142),(-254, 4832),(-2628, 3535),(-5337, 3295),(-6352, 3956),(-8625, 5577),(-10788, 4665),(-10460, 3012),(-12964, 4912),(-15917, 6233),(-15701, 7492),(-12292, 9807),(-9986, 11368),(-8705, 12396),(-5769, 12505),(-4418, 12470),(-2264, 12824),(-1134, 11940),(-2200, 9604),(-2256, 7008),(-1315, 4339),(-514, 1335),(-1864, 234),(-3343, -1071),(-3697, -2558),(-5187, -3569),(-7957, -2677),(-8495, -3159)]
        self.TheWilds_CoordinateList_6 = [(-10063, -4381),(-9887, -5138),(-9653, -5695),(-10485, -6260)]

bot_vars = BotVars() 
bot_vars.window_module = ImGui.WindowModule(module_name, window_name="TH3KUM1KO'S LEGENDARY GUARDIAN BOT", window_size=(800, 800), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

timer_instance = Timer()
elapsed_time = timer_instance.GetElapsedTime()
follow_delay_timer = Timer()

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

    #GENERAL
    FSM_vars.movement_handler.reset()

    #GREAT NORTHERN WALL
    FSM_vars.state_machine_TheGreatNorthernWall.reset()
    FSM_vars.TheGreatNorthernWall_Pathing_1.reset()    
    FSM_vars.TheGreatNorthernWall_Pathing_2.reset()    
    FSM_vars.TheGreatNorthernWall_Pathing_3.reset()  
    FSM_vars.TheGreatNorthernWall_Pathing_4.reset()    
    FSM_vars.TheGreatNorthernWall_Pathing_5.reset()    
    FSM_vars.TheGreatNorthernWall_Pathing_6.reset()  
    FSM_vars.TheGreatNorthernWall_Pathing_7.reset()    
    FSM_vars.TheGreatNorthernWall_Pathing_8.reset()    
    FSM_vars.TheGreatNorthernWall_Pathing_9.reset()  

    #FORT RANIK
    FSM_vars.state_machine_FortRanik.reset()
    FSM_vars.FortRanik_Pathing_1.reset() 
    FSM_vars.FortRanik_Pathing_2.reset() 
    FSM_vars.FortRanik_Pathing_3.reset() 
    FSM_vars.FortRanik_Pathing_4.reset() 
    FSM_vars.FortRanik_Pathing_5.reset() 
    FSM_vars.FortRanik_Pathing_5a.reset() 
    FSM_vars.FortRanik_Pathing_6.reset() 
    FSM_vars.FortRanik_Pathing_7.reset() 
    FSM_vars.FortRanik_Pathing_8.reset() 
    FSM_vars.FortRanik_Pathing_9.reset() 
    FSM_vars.FortRanik_Pathing_10.reset() 

    #RUINS OF SURMIA
    FSM_vars.state_machine_RuinsOfSurmia.reset()
    FSM_vars.RuinsOfSurmia_Pathing_1.reset() 
    FSM_vars.RuinsOfSurmia_Pathing_2.reset() 
    FSM_vars.RuinsOfSurmia_Pathing_3.reset() 
    FSM_vars.RuinsOfSurmia_Pathing_4.reset() 
    FSM_vars.RuinsOfSurmia_Pathing_5.reset() 
    FSM_vars.RuinsOfSurmia_Pathing_6.reset() 
    FSM_vars.RuinsOfSurmia_Pathing_7.reset() 
    FSM_vars.RuinsOfSurmia_Pathing_8.reset() 

    #NOLANI ACADEMY
    FSM_vars.state_machine_NolaniAcademy.reset()
    FSM_vars.NolaniAcademy_Pathing_1.reset() 
    FSM_vars.NolaniAcademy_Pathing_2.reset() 
    FSM_vars.NolaniAcademy_Pathing_3.reset() 
    FSM_vars.NolaniAcademy_Pathing_4.reset() 
    FSM_vars.NolaniAcademy_Pathing_5.reset() 

    #BORLIS PASS
    FSM_vars.state_machine_BorlisPass.reset()
    FSM_vars.BorlisPass_Pathing_1.reset() 
    FSM_vars.BorlisPass_Pathing_2.reset() 
    FSM_vars.BorlisPass_Pathing_3.reset() 
    FSM_vars.BorlisPass_Pathing_4.reset() 
    FSM_vars.BorlisPass_Pathing_5.reset() 
    FSM_vars.BorlisPass_Pathing_6.reset() 
    FSM_vars.BorlisPass_Pathing_7.reset() 
    FSM_vars.BorlisPass_Pathing_8.reset() 
    FSM_vars.BorlisPass_Pathing_9.reset() 
    FSM_vars.BorlisPass_Pathing_10.reset() 
    FSM_vars.BorlisPass_Pathing_11.reset() 
    FSM_vars.BorlisPass_Pathing_12.reset() 
    FSM_vars.BorlisPass_Pathing_13.reset() 
    FSM_vars.BorlisPass_Pathing_14.reset() 
    FSM_vars.BorlisPass_Pathing_15.reset() 
    FSM_vars.BorlisPass_Pathing_16.reset() 
    FSM_vars.BorlisPass_Pathing_17.reset() 
    FSM_vars.BorlisPass_Pathing_18.reset() 
    FSM_vars.BorlisPass_Pathing_19.reset() 
    FSM_vars.BorlisPass_Pathing_20.reset() 
    FSM_vars.BorlisPass_Pathing_21.reset() 
    FSM_vars.BorlisPass_Pathing_22.reset() 
    FSM_vars.BorlisPass_Pathing_23.reset() 
    FSM_vars.BorlisPass_Pathing_24.reset() 

    #THE FROST GATE
    FSM_vars.state_machine_TheFrostGate.reset()
    FSM_vars.TheFrostGate_Pathing_1.reset() 
    FSM_vars.TheFrostGate_Pathing_2.reset() 
    FSM_vars.TheFrostGate_Pathing_3.reset() 
    FSM_vars.TheFrostGate_Pathing_4.reset() 
    FSM_vars.TheFrostGate_Pathing_5.reset() 
    FSM_vars.TheFrostGate_Pathing_6.reset() 
    FSM_vars.TheFrostGate_Pathing_7.reset() 
    FSM_vars.TheFrostGate_Pathing_8.reset() 
    FSM_vars.TheFrostGate_Pathing_9.reset() 

    #GATES OF KRYTA
    FSM_vars.state_machine_GatesOfKryta.reset()
    FSM_vars.GatesOfKryta_Pathing_1.reset() 
    FSM_vars.GatesOfKryta_Pathing_2.reset() 
    FSM_vars.GatesOfKryta_Pathing_3.reset() 
    FSM_vars.GatesOfKryta_Pathing_4.reset() 
    FSM_vars.GatesOfKryta_Pathing_5.reset() 
    FSM_vars.GatesOfKryta_Pathing_6.reset() 
    FSM_vars.GatesOfKryta_Pathing_7.reset() 

    #D'ALESSIO SEABOARD
    FSM_vars.state_machine_DAlessioSeaboard.reset()
    FSM_vars.DAlessioSeaboard_Pathing_1.reset() 
    FSM_vars.DAlessioSeaboard_Pathing_2.reset() 
    FSM_vars.DAlessioSeaboard_Pathing_3.reset() 
    FSM_vars.DAlessioSeaboard_Pathing_4.reset() 
    FSM_vars.DAlessioSeaboard_Pathing_5.reset() 
    FSM_vars.DAlessioSeaboard_Pathing_6.reset() 
    FSM_vars.DAlessioSeaboard_Pathing_7.reset() 

    #DIVINITY COAST
    FSM_vars.state_machine_DivinityCoast.reset()
    FSM_vars.DivinityCoast_Pathing_1.reset() 
    FSM_vars.DivinityCoast_Pathing_2.reset() 
    FSM_vars.DivinityCoast_Pathing_3.reset() 
    FSM_vars.DivinityCoast_Pathing_4.reset() 
    FSM_vars.DivinityCoast_Pathing_5.reset() 
    FSM_vars.DivinityCoast_Pathing_6.reset() 

    #THE WILDS
    FSM_vars.state_machine_TheWilds.reset()
    FSM_vars.TheWilds_Pathing_1.reset() 
    FSM_vars.TheWilds_Pathing_2.reset() 
    FSM_vars.TheWilds_Pathing_3.reset() 
    FSM_vars.TheWilds_Pathing_4.reset() 
    FSM_vars.TheWilds_Pathing_5.reset() 
    FSM_vars.TheWilds_Pathing_6.reset() 



#SETTINGS
def SetGameMode():
    if state.checkbox_state_1:
        Party.SetHardMode()
    else:
        Party.SetNormalMode()

#HEROES
def AddSelectedHeroes8():

    Party.LeaveParty()

    selected_heroes = [
        state.combo_selected_1,
        state.combo_selected_2,
        state.combo_selected_3,
        state.combo_selected_4,
        state.combo_selected_5,
        state.combo_selected_6,
        state.combo_selected_7,
    ]

    hero_mapping = {
        "KOSS": bot_vars.koss,
        "GOREN": bot_vars.goren,
        "JORA": bot_vars.jora,
        "ACOLYTE JIN": bot_vars.acolyte_jin,
        "MARGRID THE SLY": bot_vars.margrid_the_sly,
        "PYRE FIERCESHOT": bot_vars.pyre_fierceshot,
        "DUNKORO": bot_vars.dunkoro,
        "TAHLKORA": bot_vars.tahlkora,
        "OGDEN STONEHEALER": bot_vars.ogden_stonehealer,
        "MASTER OF WHISPERS": bot_vars.master_of_whispers,
        "OLIAS": bot_vars.olias,
        "LIVIA": bot_vars.livia,
        "NORGU": bot_vars.norgu,
        "GWEN": bot_vars.gwen,
        "ACOLYTE SOUSUKE": bot_vars.acolyte_sousuke,
        "ZHED SHADOWHOOF": bot_vars.zhed_shadowhoof,
        "VEKK": bot_vars.vekk,
        "ZENMAI": bot_vars.zenmai,
        "ANTON": bot_vars.anton,
        "MIKU": bot_vars.miku,
        "XANDRA": bot_vars.xandra,
        "ZEI RI": bot_vars.zei_ri,
        "MELONNI": bot_vars.melonni,
        "KAHMU": bot_vars.kahmu,
        "M.O.X.": bot_vars.mox,
        "GENERAL MORGAHN": bot_vars.general_morgahn,
        "HAYDA": bot_vars.hayda,
        "KEIRAN THACKERAY": bot_vars.keiran_thackeray,
        "RAZAH": bot_vars.razah,
        "MERCENARY HERO: 1": bot_vars.mercenary_1,
        "MERCENARY HERO: 2": bot_vars.mercenary_2,
        "MERCENARY HERO: 3": bot_vars.mercenary_3,
        "MERCENARY HERO: 4": bot_vars.mercenary_4,
        "MERCENARY HERO: 5": bot_vars.mercenary_5,
        "MERCENARY HERO: 6": bot_vars.mercenary_6,
        "MERCENARY HERO: 7": bot_vars.mercenary_7,
        "MERCENARY HERO: 8": bot_vars.mercenary_8,
    }


    for selected_hero in selected_heroes:
        if selected_hero == 0:
            continue
        
        hero_name = list(hero_mapping.keys())[selected_hero - 1]
        if hero_name in hero_mapping:
            hero_id = hero_mapping[hero_name]
            Party.Heroes.AddHero(hero_id)

def AddSelectedHeroes6():

    Party.LeaveParty()

    selected_heroes = [
        state.combo_selected_1,
        state.combo_selected_2,
        state.combo_selected_3,
        state.combo_selected_4,
        state.combo_selected_5,
    ]

    hero_mapping = {
        "KOSS": bot_vars.koss,
        "GOREN": bot_vars.goren,
        "JORA": bot_vars.jora,
        "ACOLYTE JIN": bot_vars.acolyte_jin,
        "MARGRID THE SLY": bot_vars.margrid_the_sly,
        "PYRE FIERCESHOT": bot_vars.pyre_fierceshot,
        "DUNKORO": bot_vars.dunkoro,
        "TAHLKORA": bot_vars.tahlkora,
        "OGDEN STONEHEALER": bot_vars.ogden_stonehealer,
        "MASTER OF WHISPERS": bot_vars.master_of_whispers,
        "OLIAS": bot_vars.olias,
        "LIVIA": bot_vars.livia,
        "NORGU": bot_vars.norgu,
        "GWEN": bot_vars.gwen,
        "ACOLYTE SOUSUKE": bot_vars.acolyte_sousuke,
        "ZHED SHADOWHOOF": bot_vars.zhed_shadowhoof,
        "VEKK": bot_vars.vekk,
        "ZENMAI": bot_vars.zenmai,
        "ANTON": bot_vars.anton,
        "MIKU": bot_vars.miku,
        "XANDRA": bot_vars.xandra,
        "ZEI RI": bot_vars.zei_ri,
        "MELONNI": bot_vars.melonni,
        "KAHMU": bot_vars.kahmu,
        "M.O.X.": bot_vars.mox,
        "GENERAL MORGAHN": bot_vars.general_morgahn,
        "HAYDA": bot_vars.hayda,
        "KEIRAN THACKERAY": bot_vars.keiran_thackeray,
        "RAZAH": bot_vars.razah,
        "MERCENARY HERO: 1": bot_vars.mercenary_1,
        "MERCENARY HERO: 2": bot_vars.mercenary_2,
        "MERCENARY HERO: 3": bot_vars.mercenary_3,
        "MERCENARY HERO: 4": bot_vars.mercenary_4,
        "MERCENARY HERO: 5": bot_vars.mercenary_5,
        "MERCENARY HERO: 6": bot_vars.mercenary_6,
        "MERCENARY HERO: 7": bot_vars.mercenary_7,
        "MERCENARY HERO: 8": bot_vars.mercenary_8,
    }

    for selected_hero in selected_heroes:
        if selected_hero == 0:
            continue
        
        hero_name = list(hero_mapping.keys())[selected_hero - 1] 
        if hero_name in hero_mapping:
            hero_id = hero_mapping[hero_name]
            Party.Heroes.AddHero(hero_id)

def AddSelectedHeroes4():

    Party.LeaveParty()

    selected_heroes = [
        state.combo_selected_1,
        state.combo_selected_2,
        state.combo_selected_3,
    ]

    hero_mapping = {
        "KOSS": bot_vars.koss,
        "GOREN": bot_vars.goren,
        "JORA": bot_vars.jora,
        "ACOLYTE JIN": bot_vars.acolyte_jin,
        "MARGRID THE SLY": bot_vars.margrid_the_sly,
        "PYRE FIERCESHOT": bot_vars.pyre_fierceshot,
        "DUNKORO": bot_vars.dunkoro,
        "TAHLKORA": bot_vars.tahlkora,
        "OGDEN STONEHEALER": bot_vars.ogden_stonehealer,
        "MASTER OF WHISPERS": bot_vars.master_of_whispers,
        "OLIAS": bot_vars.olias,
        "LIVIA": bot_vars.livia,
        "NORGU": bot_vars.norgu,
        "GWEN": bot_vars.gwen,
        "ACOLYTE SOUSUKE": bot_vars.acolyte_sousuke,
        "ZHED SHADOWHOOF": bot_vars.zhed_shadowhoof,
        "VEKK": bot_vars.vekk,
        "ZENMAI": bot_vars.zenmai,
        "ANTON": bot_vars.anton,
        "MIKU": bot_vars.miku,
        "XANDRA": bot_vars.xandra,
        "ZEI RI": bot_vars.zei_ri,
        "MELONNI": bot_vars.melonni,
        "KAHMU": bot_vars.kahmu,
        "M.O.X.": bot_vars.mox,
        "GENERAL MORGAHN": bot_vars.general_morgahn,
        "HAYDA": bot_vars.hayda,
        "KEIRAN THACKERAY": bot_vars.keiran_thackeray,
        "RAZAH": bot_vars.razah,
        "MERCENARY HERO: 1": bot_vars.mercenary_1,
        "MERCENARY HERO: 2": bot_vars.mercenary_2,
        "MERCENARY HERO: 3": bot_vars.mercenary_3,
        "MERCENARY HERO: 4": bot_vars.mercenary_4,
        "MERCENARY HERO: 5": bot_vars.mercenary_5,
        "MERCENARY HERO: 6": bot_vars.mercenary_6,
        "MERCENARY HERO: 7": bot_vars.mercenary_7,
        "MERCENARY HERO: 8": bot_vars.mercenary_8,
    }

    for selected_hero in selected_heroes:
        if selected_hero == 0:
            continue
        
        hero_name = list(hero_mapping.keys())[selected_hero - 1]
        if hero_name in hero_mapping:
            hero_id = hero_mapping[hero_name]
            Party.Heroes.AddHero(hero_id)

def GetEnergyAgentCost(skill_id, agent_id):
    """Retrieve the actual energy cost of a skill by its ID and effects.
    [... rest of docstring ...]
    """
    # [... entire function implementation ...]

def get_energy_cost(skill_id):
    player_agent_id = Player.GetAgentID()
    return GetEnergyAgentCost(skill_id, player_agent_id)    

def HasEnoughEnergy(skill_id):
    player_agent_id = Player.GetAgentID()
    energy = Agent.GetEnergy(player_agent_id)
    max_energy = Agent.GetMaxEnergy(player_agent_id)
    energy_points = int(energy * max_energy)
    
    # Add error checking for energy cost
    energy_cost = GetEnergyAgentCost(skill_id, player_agent_id)
    if energy_cost is None:
        return False  # If we can't determine energy cost, assume we don't have enough
    
    return energy_cost <= energy_points

def IsSkillReady(skill_id):
    skill = SkillBar.GetSkillData(SkillBar.GetSlotBySkillID(skill_id))
    recharge = skill.recharge
    return recharge == 0

def IsSkillReady2(skill_slot):
    skill = SkillBar.GetSkillData(skill_slot)
    return skill.recharge == 0

def handle_map_path(map_pathing):
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1200)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    if not enemy_array:
        FSM_vars.current_target_id = None
        FSM_vars.has_interacted = False 
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)  
        return

 
    if FSM_vars.current_target_id is None or not Agent.IsAlive(FSM_vars.current_target_id):
        FSM_vars.current_target_id = enemy_array[0]  
        FSM_vars.has_interacted = False  

    if FSM_vars.current_target_id:
        target_id = FSM_vars.current_target_id
        target_x, target_y = Agent.GetXY(target_id)
        distance_to_target = ((my_x - target_x) ** 2 + (my_y - target_y) ** 2) ** 0.5

        if not FSM_vars.has_interacted:
            Player.Interact(target_id, call_target=False)
            FSM_vars.has_interacted = True  
        
        if Agent.IsAlive(target_id):
            if current_time - FSM_vars.last_skill_time >= 2.0:
                skill_slot = FSM_vars.current_skill_index
                Player.Interact(target_id, call_target=False)                 
                SkillBar.UseSkill(skill_slot)  
                FSM_vars.last_skill_time = current_time  
                FSM_vars.current_skill_index = (skill_slot % 8) + 1  

            return 

def handle_map_path_peace(map_pathing):
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (my_x, my_y), 1200)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    if not enemy_array:
        FSM_vars.current_target_id = None
        FSM_vars.has_interacted = False
        Routines.Movement.FollowPath(map_pathing, FSM_vars.movement_handler)
        return

    if FSM_vars.current_target_id is None or not Agent.IsAlive(FSM_vars.current_target_id):
        FSM_vars.current_target_id = enemy_array[0]
        FSM_vars.has_interacted = False
        FSM_vars.last_interact_time = 0  

    target_id = FSM_vars.current_target_id

    if current_time - FSM_vars.last_interact_time >= 2.0:
        Player.Interact(target_id, call_target=False)
        FSM_vars.has_interacted = True
        FSM_vars.last_interact_time = current_time

def FollowPathwithDelayTimer(path_handler,follow_handler, log_actions=False, delay=35000):
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

def handle_gadget_interaction():
    global FSM_vars
    my_id = Player.GetAgentID()
    my_x, my_y = Agent.GetXY(my_id)
    current_time = time.time()

    gadget_array = AgentArray.GetGadgetArray()
    gadget_array = AgentArray.Filter.ByDistance(gadget_array, (my_x, my_y), 800)

    if not gadget_array:
        FSM_vars.current_target_id = None
        FSM_vars.has_interacted = False
        FSM_vars.last_interaction_time = 0  
        return  

    if FSM_vars.current_target_id is None or FSM_vars.current_target_id not in gadget_array:
        FSM_vars.current_target_id = gadget_array[0]  
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
        FSM_vars.current_target_id = item_array[0]  
        FSM_vars.has_interacted = False  

    target_id = FSM_vars.current_target_id

    if not FSM_vars.has_interacted or (current_time - FSM_vars.last_interaction_time >= 5):  
        Player.Interact(target_id, call_target=False)
        FSM_vars.has_interacted = True
        FSM_vars.last_interaction_time = current_time  


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

#FSM
class StateMachineVars:
    def __init__(self):
        
        #COMMONS
        self.movement_handler = Routines.Movement.FollowXY()
        self.last_skill_time = 0.0
        self.current_skill_index = 1
        self.last_item_pickup_time = 0
        self.current_target_id = None  
        self.has_interacted = False 
        self.interacted_gadgets = set()
        self.last_interaction_time = 0.0    
        self.last_interact_time = 0.0
 

        #THE GREAT NORTHERN WALL
        self.state_machine_TheGreatNorthernWall = FSM("THE GREAT NORTHERN WALL")
        self.TheGreatNorthernWall_Pathing_1 = Routines.Movement.PathHandler(bot_vars.TheGreatNorthernWall_CoordinateList_1)
        self.TheGreatNorthernWall_Pathing_2 = Routines.Movement.PathHandler(bot_vars.TheGreatNorthernWall_CoordinateList_2)
        self.TheGreatNorthernWall_Pathing_3 = Routines.Movement.PathHandler(bot_vars.TheGreatNorthernWall_CoordinateList_3)
        self.TheGreatNorthernWall_Pathing_4 = Routines.Movement.PathHandler(bot_vars.TheGreatNorthernWall_CoordinateList_4)
        self.TheGreatNorthernWall_Pathing_5 = Routines.Movement.PathHandler(bot_vars.TheGreatNorthernWall_CoordinateList_5)
        self.TheGreatNorthernWall_Pathing_6 = Routines.Movement.PathHandler(bot_vars.TheGreatNorthernWall_CoordinateList_6)
        self.TheGreatNorthernWall_Pathing_7 = Routines.Movement.PathHandler(bot_vars.TheGreatNorthernWall_CoordinateList_7)
        self.TheGreatNorthernWall_Pathing_8 = Routines.Movement.PathHandler(bot_vars.TheGreatNorthernWall_CoordinateList_8)
        self.TheGreatNorthernWall_Pathing_9 = Routines.Movement.PathHandler(bot_vars.TheGreatNorthernWall_CoordinateList_9)

        #FORT RANIK
        self.state_machine_FortRanik = FSM("FORT RANIK")
        self.FortRanik_Pathing_1 = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_1)
        self.FortRanik_Pathing_2 = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_2)
        self.FortRanik_Pathing_3 = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_3)
        self.FortRanik_Pathing_4 = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_4)
        self.FortRanik_Pathing_5 = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_5)
        self.FortRanik_Pathing_5a = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_5a)
        self.FortRanik_Pathing_6 = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_6)
        self.FortRanik_Pathing_7 = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_7)
        self.FortRanik_Pathing_8 = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_8)
        self.FortRanik_Pathing_9 = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_9)
        self.FortRanik_Pathing_10 = Routines.Movement.PathHandler(bot_vars.FortRanik_CoordinateList_10)

        #RUINS OF SURMIA
        self.state_machine_RuinsOfSurmia = FSM("RUINS OF SURMIA")
        self.RuinsOfSurmia_Pathing_1 = Routines.Movement.PathHandler(bot_vars.RuinsOfSurmia_CoordinateList_1)
        self.RuinsOfSurmia_Pathing_2 = Routines.Movement.PathHandler(bot_vars.RuinsOfSurmia_CoordinateList_2)
        self.RuinsOfSurmia_Pathing_3 = Routines.Movement.PathHandler(bot_vars.RuinsOfSurmia_CoordinateList_3)
        self.RuinsOfSurmia_Pathing_4 = Routines.Movement.PathHandler(bot_vars.RuinsOfSurmia_CoordinateList_4)
        self.RuinsOfSurmia_Pathing_5 = Routines.Movement.PathHandler(bot_vars.RuinsOfSurmia_CoordinateList_5)
        self.RuinsOfSurmia_Pathing_6 = Routines.Movement.PathHandler(bot_vars.RuinsOfSurmia_CoordinateList_6)
        self.RuinsOfSurmia_Pathing_7 = Routines.Movement.PathHandler(bot_vars.RuinsOfSurmia_CoordinateList_7)
        self.RuinsOfSurmia_Pathing_8 = Routines.Movement.PathHandler(bot_vars.RuinsOfSurmia_CoordinateList_8)

        #NOLANI ACADEMY
        self.state_machine_NolaniAcademy = FSM("NOLANI ACADEMY")
        self.NolaniAcademy_Pathing_1 = Routines.Movement.PathHandler(bot_vars.NolaniAcademy_CoordinateList_1)
        self.NolaniAcademy_Pathing_2 = Routines.Movement.PathHandler(bot_vars.NolaniAcademy_CoordinateList_2)
        self.NolaniAcademy_Pathing_3 = Routines.Movement.PathHandler(bot_vars.NolaniAcademy_CoordinateList_3)
        self.NolaniAcademy_Pathing_4 = Routines.Movement.PathHandler(bot_vars.NolaniAcademy_CoordinateList_4)
        self.NolaniAcademy_Pathing_5 = Routines.Movement.PathHandler(bot_vars.NolaniAcademy_CoordinateList_5)

        #BORLIS PASS
        self.state_machine_BorlisPass = FSM("BORLIS PASS")
        self.BorlisPass_Pathing_1 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_1)
        self.BorlisPass_Pathing_2 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_2)
        self.BorlisPass_Pathing_3 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_3)
        self.BorlisPass_Pathing_4 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_4)
        self.BorlisPass_Pathing_5 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_5)
        self.BorlisPass_Pathing_6 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_6)
        self.BorlisPass_Pathing_7 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_7)
        self.BorlisPass_Pathing_8 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_8)
        self.BorlisPass_Pathing_9 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_9)
        self.BorlisPass_Pathing_10 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_10)
        self.BorlisPass_Pathing_11 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_11)
        self.BorlisPass_Pathing_12 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_12)
        self.BorlisPass_Pathing_13 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_13)
        self.BorlisPass_Pathing_14 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_14)
        self.BorlisPass_Pathing_15 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_15)
        self.BorlisPass_Pathing_16 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_16)
        self.BorlisPass_Pathing_17 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_17)
        self.BorlisPass_Pathing_18 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_18)
        self.BorlisPass_Pathing_19 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_19)
        self.BorlisPass_Pathing_20 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_20)
        self.BorlisPass_Pathing_21 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_21)
        self.BorlisPass_Pathing_22 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_22)
        self.BorlisPass_Pathing_23 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_23)
        self.BorlisPass_Pathing_24 = Routines.Movement.PathHandler(bot_vars.BorlisPass_CoordinateList_24)

        #THE FROST GATE
        self.state_machine_TheFrostGate = FSM("THE FROST GATE")
        self.TheFrostGate_Pathing_1 = Routines.Movement.PathHandler(bot_vars.TheFrostGate_CoordinateList_1)
        self.TheFrostGate_Pathing_2 = Routines.Movement.PathHandler(bot_vars.TheFrostGate_CoordinateList_2)
        self.TheFrostGate_Pathing_3 = Routines.Movement.PathHandler(bot_vars.TheFrostGate_CoordinateList_3)
        self.TheFrostGate_Pathing_4 = Routines.Movement.PathHandler(bot_vars.TheFrostGate_CoordinateList_4)
        self.TheFrostGate_Pathing_5 = Routines.Movement.PathHandler(bot_vars.TheFrostGate_CoordinateList_5)
        self.TheFrostGate_Pathing_6 = Routines.Movement.PathHandler(bot_vars.TheFrostGate_CoordinateList_6)
        self.TheFrostGate_Pathing_7 = Routines.Movement.PathHandler(bot_vars.TheFrostGate_CoordinateList_7)
        self.TheFrostGate_Pathing_8 = Routines.Movement.PathHandler(bot_vars.TheFrostGate_CoordinateList_8)
        self.TheFrostGate_Pathing_9 = Routines.Movement.PathHandler(bot_vars.TheFrostGate_CoordinateList_9)

        #GATES OF KRYTA
        self.state_machine_GatesOfKryta = FSM("GATES OF KRYTA")
        self.GatesOfKryta_Pathing_1 = Routines.Movement.PathHandler(bot_vars.GatesOfKryta_CoordinateList_1)
        self.GatesOfKryta_Pathing_2 = Routines.Movement.PathHandler(bot_vars.GatesOfKryta_CoordinateList_2)
        self.GatesOfKryta_Pathing_3 = Routines.Movement.PathHandler(bot_vars.GatesOfKryta_CoordinateList_3)
        self.GatesOfKryta_Pathing_4 = Routines.Movement.PathHandler(bot_vars.GatesOfKryta_CoordinateList_4)
        self.GatesOfKryta_Pathing_5 = Routines.Movement.PathHandler(bot_vars.GatesOfKryta_CoordinateList_5)
        self.GatesOfKryta_Pathing_6 = Routines.Movement.PathHandler(bot_vars.GatesOfKryta_CoordinateList_6)
        self.GatesOfKryta_Pathing_7 = Routines.Movement.PathHandler(bot_vars.GatesOfKryta_CoordinateList_7)

        #D'ALESSIO SEABOARD
        self.state_machine_DAlessioSeaboard = FSM("D'ALESSIO SEABOARD")
        self.DAlessioSeaboard_Pathing_1 = Routines.Movement.PathHandler(bot_vars.DAlessioSeabord_CoordinateList_1)
        self.DAlessioSeaboard_Pathing_2 = Routines.Movement.PathHandler(bot_vars.DAlessioSeabord_CoordinateList_2)
        self.DAlessioSeaboard_Pathing_3 = Routines.Movement.PathHandler(bot_vars.DAlessioSeabord_CoordinateList_3)
        self.DAlessioSeaboard_Pathing_4 = Routines.Movement.PathHandler(bot_vars.DAlessioSeabord_CoordinateList_4)
        self.DAlessioSeaboard_Pathing_5 = Routines.Movement.PathHandler(bot_vars.DAlessioSeabord_CoordinateList_5)
        self.DAlessioSeaboard_Pathing_6 = Routines.Movement.PathHandler(bot_vars.DAlessioSeabord_CoordinateList_6)
        self.DAlessioSeaboard_Pathing_7 = Routines.Movement.PathHandler(bot_vars.DAlessioSeabord_CoordinateList_7)

        #DIVINITY COAST
        self.state_machine_DivinityCoast = FSM("DIVINITY COAST")
        self.DivinityCoast_Pathing_1 = Routines.Movement.PathHandler(bot_vars.DivinityCoast_CoordinateList_1)
        self.DivinityCoast_Pathing_2 = Routines.Movement.PathHandler(bot_vars.DivinityCoast_CoordinateList_2)
        self.DivinityCoast_Pathing_3 = Routines.Movement.PathHandler(bot_vars.DivinityCoast_CoordinateList_3)
        self.DivinityCoast_Pathing_4 = Routines.Movement.PathHandler(bot_vars.DivinityCoast_CoordinateList_4)
        self.DivinityCoast_Pathing_5 = Routines.Movement.PathHandler(bot_vars.DivinityCoast_CoordinateList_5)
        self.DivinityCoast_Pathing_6 = Routines.Movement.PathHandler(bot_vars.DivinityCoast_CoordinateList_6)

        #THE WILDS
        self.state_machine_TheWilds = FSM("THE WILDS")
        self.TheWilds_Pathing_1 = Routines.Movement.PathHandler(bot_vars.TheWilds_CoordinateList_1)
        self.TheWilds_Pathing_2 = Routines.Movement.PathHandler(bot_vars.TheWilds_CoordinateList_2)
        self.TheWilds_Pathing_3 = Routines.Movement.PathHandler(bot_vars.TheWilds_CoordinateList_3)
        self.TheWilds_Pathing_4 = Routines.Movement.PathHandler(bot_vars.TheWilds_CoordinateList_4)
        self.TheWilds_Pathing_5 = Routines.Movement.PathHandler(bot_vars.TheWilds_CoordinateList_5)
        self.TheWilds_Pathing_6 = Routines.Movement.PathHandler(bot_vars.TheWilds_CoordinateList_6)

FSM_vars = StateMachineVars()

#_____________________THE GREAT NORTHERN WALL_____________________#
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="TRAVEL TO OUTPOST", execute_fn=lambda: Map.Travel(bot_vars.TheGreatNorthernWall), exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="SET GAME MODE", execute_fn=lambda: SetGameMode(), exit_condition=lambda: Map.IsOutpost(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="ADD HEROES 4", execute_fn=lambda: AddSelectedHeroes4(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="SET VANGUARD TITLE", execute_fn=lambda: Player.SetActiveTitle(bot_vars.Vanguard_Title), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="ENTER BATTLE", execute_fn=lambda: Map.EnterChallenge(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="MAP PATH 1", execute_fn=lambda: handle_map_path(FSM_vars.TheGreatNorthernWall_Pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheGreatNorthernWall_Pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="MAP PATH 2", execute_fn=lambda: handle_map_path(FSM_vars.TheGreatNorthernWall_Pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheGreatNorthernWall_Pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="MAP PATH 3", execute_fn=lambda: handle_map_path(FSM_vars.TheGreatNorthernWall_Pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheGreatNorthernWall_Pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="MAP PATH 4", execute_fn=lambda: handle_map_path(FSM_vars.TheGreatNorthernWall_Pathing_4), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheGreatNorthernWall_Pathing_4, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="MAP PATH 5", execute_fn=lambda: handle_map_path(FSM_vars.TheGreatNorthernWall_Pathing_5), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheGreatNorthernWall_Pathing_5, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="MAP PATH 6", execute_fn=lambda: handle_map_path(FSM_vars.TheGreatNorthernWall_Pathing_6), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheGreatNorthernWall_Pathing_6, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="MAP PATH 7", execute_fn=lambda: handle_map_path(FSM_vars.TheGreatNorthernWall_Pathing_7), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheGreatNorthernWall_Pathing_7, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="PRESS SPACE", execute_fn=lambda: Keystroke.PressAndRelease(Key.Space.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="MAP PATH 8", execute_fn=lambda: handle_map_path(FSM_vars.TheGreatNorthernWall_Pathing_8), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheGreatNorthernWall_Pathing_8, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic()), run_once=False)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="WAITING CINEMATIC", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=500, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="MAP PATH 9", execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.TheGreatNorthernWall_Pathing_9, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheGreatNorthernWall_Pathing_9, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="WAITING CINEMATIC", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=500, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheGreatNorthernWall.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)

#_____________________FORT RANIK_____________________#
FSM_vars.state_machine_FortRanik.AddState(name="TRAVEL TO OUTPOST", execute_fn=lambda: Map.Travel(bot_vars.FortRanik), exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="SET GAME MODE", execute_fn=lambda: SetGameMode(), exit_condition=lambda: Map.IsOutpost(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="ADD HEROES 4", execute_fn=lambda: AddSelectedHeroes4(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="SET VANGUARD TITLE", execute_fn=lambda: Player.SetActiveTitle(bot_vars.Vanguard_Title), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="ENTER BATTLE", execute_fn=lambda: Map.EnterChallenge(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 1", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 2", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 3", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 4", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_4), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_4, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 5", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_5), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_5, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 6", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_6), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_6, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 5a", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_5a), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_5a, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 7", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_7), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_7, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 8", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_8), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_8, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=7000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="PRESS SPACE", execute_fn=lambda: Keystroke.PressAndRelease(Key.Space.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 9", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_9), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_9, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=7000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="PRESS SPACE", execute_fn=lambda: Keystroke.PressAndRelease(Key.Space.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_FortRanik.AddState(name="MAP PATH 10", execute_fn=lambda: handle_map_path(FSM_vars.FortRanik_Pathing_10), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.FortRanik_Pathing_10, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_FortRanik.AddState(name="PRESS ESC END MAP", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value),exit_condition=lambda: Map.IsOutpost(), run_once=True)

#_____________________RUINS OF SURMIA_____________________#
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="TRAVEL TO OUTPOST", execute_fn=lambda: Map.Travel(bot_vars.RuinsOfSurmia), exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="SET GAME MODE", execute_fn=lambda: SetGameMode(), exit_condition=lambda: Map.IsOutpost(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="ADD HEROES 4", execute_fn=lambda: AddSelectedHeroes4(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="SET VANGUARD TITLE", execute_fn=lambda: Player.SetActiveTitle(bot_vars.Vanguard_Title), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="ENTER BATTLE", execute_fn=lambda: Map.EnterChallenge(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="MAP PATH 1", execute_fn=lambda: handle_map_path(FSM_vars.RuinsOfSurmia_Pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.RuinsOfSurmia_Pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="MAP PATH 2", execute_fn=lambda: handle_map_path(FSM_vars.RuinsOfSurmia_Pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.RuinsOfSurmia_Pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="MAP PATH 3 - PEACE", execute_fn=lambda: handle_map_path_peace(FSM_vars.RuinsOfSurmia_Pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.RuinsOfSurmia_Pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=45000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="MAP PATH 4 - FOLLOW WITH DELAY TIMER", execute_fn=lambda: FollowPathwithDelayTimer(FSM_vars.RuinsOfSurmia_Pathing_4, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.RuinsOfSurmia_Pathing_4, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="MAP PATH 5", execute_fn=lambda: handle_map_path(FSM_vars.RuinsOfSurmia_Pathing_5), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.RuinsOfSurmia_Pathing_5, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="MAP PATH 6 - FOLLOW WITH DELAY TIMER", execute_fn=lambda: FollowPathwithDelayTimer(FSM_vars.RuinsOfSurmia_Pathing_6, FSM_vars.movement_handler), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.RuinsOfSurmia_Pathing_6, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="MAP PATH 7", execute_fn=lambda: handle_map_path(FSM_vars.RuinsOfSurmia_Pathing_7), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.RuinsOfSurmia_Pathing_7, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=10000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="MAP PATH 8", execute_fn=lambda: handle_map_path(FSM_vars.RuinsOfSurmia_Pathing_8), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.RuinsOfSurmia_Pathing_8, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="PRESS ESC END MAP", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value),exit_condition=lambda: Map.IsOutpost(),transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_RuinsOfSurmia.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)

#_____________________NOLANI ACADEMY_____________________#
FSM_vars.state_machine_NolaniAcademy.AddState(name="TRAVEL TO OUTPOST", execute_fn=lambda: Map.Travel(bot_vars.NolaniAcademy), exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="SET GAME MODE", execute_fn=lambda: SetGameMode(), exit_condition=lambda: Map.IsOutpost(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="ADD HEROES 4", execute_fn=lambda: AddSelectedHeroes4(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="SET VANGUARD TITLE", execute_fn=lambda: Player.SetActiveTitle(bot_vars.Vanguard_Title), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="ENTER BATTLE", execute_fn=lambda: Map.EnterChallenge(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="MAP PATH 1", execute_fn=lambda: handle_map_path(FSM_vars.NolaniAcademy_Pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.NolaniAcademy_Pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_NolaniAcademy.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=10000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="MAP PATH 2", execute_fn=lambda: handle_map_path(FSM_vars.NolaniAcademy_Pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.NolaniAcademy_Pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_NolaniAcademy.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="MAP PATH 3", execute_fn=lambda: handle_map_path(FSM_vars.NolaniAcademy_Pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.NolaniAcademy_Pathing_3, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic()), run_once=False)
FSM_vars.state_machine_NolaniAcademy.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="MAP PATH 4", execute_fn=lambda: handle_map_path(FSM_vars.NolaniAcademy_Pathing_4), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.NolaniAcademy_Pathing_4, FSM_vars.movement_handler) or Map.IsOutpost(), run_once=False)
FSM_vars.state_machine_NolaniAcademy.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="MAP PATH 5", execute_fn=lambda: handle_map_path(FSM_vars.NolaniAcademy_Pathing_5), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.NolaniAcademy_Pathing_5, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_NolaniAcademy.AddState(name="PRESS ESC", execute_fn=lambda: Keystroke.PressAndRelease(Key.Escape.value), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_NolaniAcademy.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)

#_____________________BORLIS PASS_____________________#
FSM_vars.state_machine_BorlisPass.AddState(name="TRAVEL TO OUTPOST", execute_fn=lambda: Map.Travel(bot_vars.BorlisPass), exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="SET GAME MODE", execute_fn=lambda: SetGameMode(), exit_condition=lambda: Map.IsOutpost(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="ADD HEROES 6", execute_fn=lambda: AddSelectedHeroes6(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="ENTER BATTLE", execute_fn=lambda: Map.EnterChallenge(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 1", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 2", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 3", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 4", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_4), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_4, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 5", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_5), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_5, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 6", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_6), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_6, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 7", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_7), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_7, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 8", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_8), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_8, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 9", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_9), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_9, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 10", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_10), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_10, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 11", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_11), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_11, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHANGE WEAPONSET 2", execute_fn=lambda: Keystroke.PressAndRelease(Key.F2.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="CHANGE WEAPONSET 1", execute_fn=lambda: Keystroke.PressAndRelease(Key.F1.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 12", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_12), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_12, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 13", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_13), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_13, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHANGE WEAPONSET 2", execute_fn=lambda: Keystroke.PressAndRelease(Key.F2.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="CHANGE WEAPONSET 1", execute_fn=lambda: Keystroke.PressAndRelease(Key.F1.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 14", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_14), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_14, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 15", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_15), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_15, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 16", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_16), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_16, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHANGE WEAPONSET 2", execute_fn=lambda: Keystroke.PressAndRelease(Key.F2.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="CHANGE WEAPONSET 1", execute_fn=lambda: Keystroke.PressAndRelease(Key.F1.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 17", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_17), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_17, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 18", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_18), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_18, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHANGE WEAPONSET 2", execute_fn=lambda: Keystroke.PressAndRelease(Key.F2.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="CHANGE WEAPONSET 1", execute_fn=lambda: Keystroke.PressAndRelease(Key.F1.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 19", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_19), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_19, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 20", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_20), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_20, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHANGE WEAPONSET 2", execute_fn=lambda: Keystroke.PressAndRelease(Key.F2.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="CHANGE WEAPONSET 1", execute_fn=lambda: Keystroke.PressAndRelease(Key.F1.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 21", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_21), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_21, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 22", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_22), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_22, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 23", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_23), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_23, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="MAP PATH 24", execute_fn=lambda: handle_map_path(FSM_vars.BorlisPass_Pathing_24), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.BorlisPass_Pathing_24, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_BorlisPass.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_BorlisPass.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)

#_____________________THE FROST GATE_____________________#
FSM_vars.state_machine_TheFrostGate.AddState(name="TRAVEL TO OUTPOST", execute_fn=lambda: Map.Travel(bot_vars.TheFrostGate), exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="SET GAME MODE", execute_fn=lambda: SetGameMode(), exit_condition=lambda: Map.IsOutpost(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="ADD HEROES 6", execute_fn=lambda: AddSelectedHeroes6(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="ENTER BATTLE", execute_fn=lambda: Map.EnterChallenge(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="MAP PATH 1", execute_fn=lambda: handle_map_path(FSM_vars.TheFrostGate_Pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheFrostGate_Pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="MAP PATH 2", execute_fn=lambda: handle_map_path(FSM_vars.TheFrostGate_Pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheFrostGate_Pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=6000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="PRESS SPACE", execute_fn=lambda: Keystroke.PressAndRelease(Key.Space.value),transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="MAP PATH 3", execute_fn=lambda: handle_map_path(FSM_vars.TheFrostGate_Pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheFrostGate_Pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=4000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=4000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="MAP PATH 4", execute_fn=lambda: handle_map_path(FSM_vars.TheFrostGate_Pathing_4), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheFrostGate_Pathing_4, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="MAP PATH 5", execute_fn=lambda: handle_map_path(FSM_vars.TheFrostGate_Pathing_5), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheFrostGate_Pathing_5, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic()) , run_once=False)
FSM_vars.state_machine_TheFrostGate.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="MAP PATH 6", execute_fn=lambda: handle_map_path(FSM_vars.TheFrostGate_Pathing_6), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheFrostGate_Pathing_6, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=4000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=15000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=4000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=15000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="MAP PATH 7", execute_fn=lambda: handle_map_path(FSM_vars.TheFrostGate_Pathing_7), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheFrostGate_Pathing_7, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=15000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="MAP PATH 8", execute_fn=lambda: handle_map_path(FSM_vars.TheFrostGate_Pathing_8), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheFrostGate_Pathing_8, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=15000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="MAP PATH 9", execute_fn=lambda: handle_map_path(FSM_vars.TheFrostGate_Pathing_9), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheFrostGate_Pathing_9, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=15000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheFrostGate.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)

#_____________________GATES OF KRYTA_____________________#
FSM_vars.state_machine_GatesOfKryta.AddState(name="TRAVEL TO OUTPOST", execute_fn=lambda: Map.Travel(bot_vars.GatesOfKryta), exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="SET GAME MODE", execute_fn=lambda: SetGameMode(), exit_condition=lambda: Map.IsOutpost(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="ADD HEROES 6", execute_fn=lambda: AddSelectedHeroes6(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="ENTER BATTLE", execute_fn=lambda: Map.EnterChallenge(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="WAITING EXPLORABLE MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="MAP PATH 1", execute_fn=lambda: handle_map_path(FSM_vars.GatesOfKryta_Pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.GatesOfKryta_Pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_GatesOfKryta.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="MAP PATH 2", execute_fn=lambda: handle_map_path(FSM_vars.GatesOfKryta_Pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.GatesOfKryta_Pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_GatesOfKryta.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=7500, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="MAP PATH 3", execute_fn=lambda: handle_map_path(FSM_vars.GatesOfKryta_Pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.GatesOfKryta_Pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_GatesOfKryta.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="MAP PATH 4", execute_fn=lambda: handle_map_path(FSM_vars.GatesOfKryta_Pathing_4), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.GatesOfKryta_Pathing_4, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_GatesOfKryta.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="MAP PATH 5", execute_fn=lambda: handle_map_path(FSM_vars.GatesOfKryta_Pathing_5), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.GatesOfKryta_Pathing_5, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_GatesOfKryta.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="MAP PATH 6", execute_fn=lambda: handle_map_path(FSM_vars.GatesOfKryta_Pathing_6), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.GatesOfKryta_Pathing_6, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_GatesOfKryta.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="MAP PATH 7", execute_fn=lambda: handle_map_path(FSM_vars.GatesOfKryta_Pathing_7), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.GatesOfKryta_Pathing_7, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic()) , run_once=False)
FSM_vars.state_machine_GatesOfKryta.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_GatesOfKryta.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)

#_____________________D'ALESSIO SEABOARD_____________________#
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="TRAVEL TO OUTPOST", execute_fn=lambda: Map.Travel(bot_vars.DAlessioSeabord), exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="SET GAME MODE", execute_fn=lambda: SetGameMode(), exit_condition=lambda: Map.IsOutpost(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="ADD HEROES 6", execute_fn=lambda: AddSelectedHeroes6(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="ENTER BATTLE", execute_fn=lambda: Map.EnterChallenge(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="MAP PATH 1", execute_fn=lambda: handle_map_path(FSM_vars.DAlessioSeaboard_Pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DAlessioSeaboard_Pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="MAP PATH 2", execute_fn=lambda: handle_map_path(FSM_vars.DAlessioSeaboard_Pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DAlessioSeaboard_Pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="MAP PATH 3", execute_fn=lambda: handle_map_path(FSM_vars.DAlessioSeaboard_Pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DAlessioSeaboard_Pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="MAP PATH 4", execute_fn=lambda: handle_map_path(FSM_vars.DAlessioSeaboard_Pathing_4), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DAlessioSeaboard_Pathing_4, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="MAP PATH 5", execute_fn=lambda: handle_map_path(FSM_vars.DAlessioSeaboard_Pathing_5), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DAlessioSeaboard_Pathing_5, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="CHECK NPC", execute_fn=lambda: handle_npc_interaction(), transition_delay_ms=600000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="MAP PATH 6", execute_fn=lambda: handle_map_path(FSM_vars.DAlessioSeaboard_Pathing_6), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DAlessioSeaboard_Pathing_6, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="CHECK GADGET", execute_fn=lambda: handle_gadget_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="MAP PATH 6", execute_fn=lambda: handle_map_path(FSM_vars.DAlessioSeaboard_Pathing_7), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DAlessioSeaboard_Pathing_7, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_DAlessioSeaboard.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)

#_____________________DIVINITY COAST_____________________#
FSM_vars.state_machine_DivinityCoast.AddState(name="TRAVEL TO OUTPOST", execute_fn=lambda: Map.Travel(bot_vars.DivinityCoast), exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="SET GAME MODE", execute_fn=lambda: SetGameMode(), exit_condition=lambda: Map.IsOutpost(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="ADD HEROES 6", execute_fn=lambda: AddSelectedHeroes6(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="ENTER BATTLE", execute_fn=lambda: Map.EnterChallenge(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="MAP PATH 1", execute_fn=lambda: handle_map_path(FSM_vars.DivinityCoast_Pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DivinityCoast_Pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DivinityCoast.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="MAP PATH 2", execute_fn=lambda: handle_map_path(FSM_vars.DivinityCoast_Pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DivinityCoast_Pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DivinityCoast.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="MAP PATH 3", execute_fn=lambda: handle_map_path(FSM_vars.DivinityCoast_Pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DivinityCoast_Pathing_3, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DivinityCoast.AddState(name="FLAG HEROES", execute_fn=lambda: Party.Heroes.FlagAllHeroes(-1790, 177), transition_delay_ms=25000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="MAP PATH 4", execute_fn=lambda: handle_map_path(FSM_vars.DivinityCoast_Pathing_4), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DivinityCoast_Pathing_4, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DivinityCoast.AddState(name="FLAG HEROES", execute_fn=lambda: Party.Heroes.UnflagAllHeroes(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="MAP PATH 5", execute_fn=lambda: handle_map_path(FSM_vars.DivinityCoast_Pathing_5), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.DivinityCoast_Pathing_5, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_DivinityCoast.AddState(name="CHECK QUEST", execute_fn=lambda: handle_quest_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="MAP PATH 6", execute_fn=lambda: handle_map_path(FSM_vars.GatesOfKryta_Pathing_6), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.GatesOfKryta_Pathing_6, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic()) , run_once=False)
FSM_vars.state_machine_DivinityCoast.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_DivinityCoast.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)

#_____________________THE WILDS_____________________#
FSM_vars.state_machine_TheWilds.AddState(name="TRAVEL TO OUTPOST", execute_fn=lambda: Map.Travel(bot_vars.TheWilds), exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="WAITING OUTPOST MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded(), transition_delay_ms=3000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="SET GAME MODE", execute_fn=lambda: SetGameMode(), exit_condition=lambda: Map.IsOutpost(), transition_delay_ms=5000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="ADD HEROES 6", execute_fn=lambda: AddSelectedHeroes6(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="ENTER BATTLE", execute_fn=lambda: Map.EnterChallenge(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="MAP PATH 1", execute_fn=lambda: handle_map_path(FSM_vars.TheWilds_Pathing_1), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheWilds_Pathing_1, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheWilds.AddState(name="PRESS ENTER", execute_fn=lambda: Keystroke.PressAndRelease(Key.Enter.value), exit_condition=lambda: (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()), transition_delay_ms=90000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="MAP PATH 2", execute_fn=lambda: handle_map_path(FSM_vars.TheWilds_Pathing_2), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheWilds_Pathing_2, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheWilds.AddState(name="CHECK ITEM", execute_fn=lambda: handle_item_interaction(), transition_delay_ms=2000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="MAP PATH 3", execute_fn=lambda: handle_map_path(FSM_vars.TheWilds_Pathing_3), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheWilds_Pathing_3, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic()) , run_once=False)
FSM_vars.state_machine_TheWilds.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="MAP PATH 4", execute_fn=lambda: handle_map_path(FSM_vars.TheWilds_Pathing_4), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheWilds_Pathing_4, FSM_vars.movement_handler), run_once=False)
FSM_vars.state_machine_TheWilds.AddState(name="CHANGE WEAPONSET 2", execute_fn=lambda: Keystroke.PressAndRelease(Key.F2.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="CHANGE WEAPONSET 1", execute_fn=lambda: Keystroke.PressAndRelease(Key.F1.value), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="MAP PATH 5", execute_fn=lambda: handle_map_path(FSM_vars.TheWilds_Pathing_5), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheWilds_Pathing_5, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic()) , run_once=False)
FSM_vars.state_machine_TheWilds.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="MAP PATH 6", execute_fn=lambda: handle_map_path(FSM_vars.TheWilds_Pathing_6), exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.TheWilds_Pathing_6, FSM_vars.movement_handler) or (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic()) , run_once=False)
FSM_vars.state_machine_TheWilds.AddState(name="WAITING CINEMATIC MAP", exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and Map.IsInCinematic(), transition_delay_ms=1500, run_once=True)
FSM_vars.state_machine_TheWilds.AddState(name="SKIP CINEMATIC", execute_fn=lambda: Map.SkipCinematic(), transition_delay_ms=1000, run_once=True)

#GUI
def DrawWindow():
    global module_name
    global state

    if PyImGui.begin("TH3KUM1KO'S LEGENDARY GUARDIAN BOT"):
        if PyImGui.begin_tab_bar("MAINTABBAR"): 

            if PyImGui.begin_tab_item("PROPHECIES"):
                PyImGui.spacing()
                state.radio_button_selected = PyImGui.radio_button("THE GREAT NORTHERN WALL", state.radio_button_selected, 0)
                state.radio_button_selected = PyImGui.radio_button("FORT RANIK", state.radio_button_selected, 1)
                state.radio_button_selected = PyImGui.radio_button("RUINS OF SURMIA", state.radio_button_selected, 2)
                state.radio_button_selected = PyImGui.radio_button("NOLANI ACADEMY", state.radio_button_selected, 3)
                state.radio_button_selected = PyImGui.radio_button("BORLIS PASS", state.radio_button_selected, 4)
                state.radio_button_selected = PyImGui.radio_button("THE FROST GATE", state.radio_button_selected, 5)
                state.radio_button_selected = PyImGui.radio_button("GATES OF KRYTA", state.radio_button_selected, 6)
                state.radio_button_selected = PyImGui.radio_button("D'ALESSIO SEABOARD", state.radio_button_selected, 7)
                state.radio_button_selected = PyImGui.radio_button("DIVINITY COAST", state.radio_button_selected, 8)
                state.radio_button_selected = PyImGui.radio_button("THE WILDS", state.radio_button_selected, 9)
                state.radio_button_selected = PyImGui.radio_button("BLOODSTONE FEN", state.radio_button_selected, 10)
                state.radio_button_selected = PyImGui.radio_button("AURORA GLADE", state.radio_button_selected, 11)
                state.radio_button_selected = PyImGui.radio_button("RIVERSIDE PROVINCE", state.radio_button_selected, 12)
                state.radio_button_selected = PyImGui.radio_button("SANCTUM CAY", state.radio_button_selected, 13)
                state.radio_button_selected = PyImGui.radio_button("DUNES OF DESPAIR", state.radio_button_selected, 14)
                state.radio_button_selected = PyImGui.radio_button("THIRSTY REACH", state.radio_button_selected, 15)
                state.radio_button_selected = PyImGui.radio_button("AUGURY ROCK", state.radio_button_selected, 16)
                state.radio_button_selected = PyImGui.radio_button("THE DRAGON'S LAIR", state.radio_button_selected, 17)
                state.radio_button_selected = PyImGui.radio_button("ICE CAVE OF SORROW", state.radio_button_selected, 18)
                state.radio_button_selected = PyImGui.radio_button("IRON MINES OF MOLADUNE", state.radio_button_selected, 19)
                state.radio_button_selected = PyImGui.radio_button("THUNDERHEAD KEEP", state.radio_button_selected, 20)
                state.radio_button_selected = PyImGui.radio_button("RING OF FIRE", state.radio_button_selected, 21)
                state.radio_button_selected = PyImGui.radio_button("ABADDON'S MOUTH", state.radio_button_selected, 22)
                state.radio_button_selected = PyImGui.radio_button("HELL'S PRECIPICE", state.radio_button_selected, 23)            
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


            if PyImGui.begin_tab_item("FACTIONS"):
                PyImGui.spacing()
                state.radio_button_selected = PyImGui.radio_button("MINISTER CHO'S ESTATE", state.radio_button_selected, 24)
                state.radio_button_selected = PyImGui.radio_button("ZEN DAIJUN", state.radio_button_selected, 25)
                state.radio_button_selected = PyImGui.radio_button("VIZUNAH SQUARE", state.radio_button_selected, 26)
                state.radio_button_selected = PyImGui.radio_button("NAHPUI QUARTER", state.radio_button_selected, 27)
                state.radio_button_selected = PyImGui.radio_button("TAHNNAKAI TEMPLE", state.radio_button_selected, 28)
                state.radio_button_selected = PyImGui.radio_button("ARBORSTONE", state.radio_button_selected, 29)
                state.radio_button_selected = PyImGui.radio_button("BOREAS SEABED", state.radio_button_selected, 30)
                state.radio_button_selected = PyImGui.radio_button("SUNJIANG DISTRICT", state.radio_button_selected, 31)
                state.radio_button_selected = PyImGui.radio_button("THE ETERNAL GROVE", state.radio_button_selected, 32)
                state.radio_button_selected = PyImGui.radio_button("GYALA HATCHERY", state.radio_button_selected, 33)
                state.radio_button_selected = PyImGui.radio_button("UNWAKING WATERS", state.radio_button_selected, 34)
                state.radio_button_selected = PyImGui.radio_button("RAISU PALACE", state.radio_button_selected, 35)
                state.radio_button_selected = PyImGui.radio_button("IMPERIAL SANCTUM", state.radio_button_selected, 36)
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

            if PyImGui.begin_tab_item("NIGHTFALL"):
                PyImGui.spacing()
                state.radio_button_selected = PyImGui.radio_button("CHAHBEK VILLAGE", state.radio_button_selected, 37)
                PyImGui.show_tooltip("REMEMBER TO ADD KOSS")
                state.radio_button_selected = PyImGui.radio_button("JOKANUR DIGGINS", state.radio_button_selected, 38)
                PyImGui.show_tooltip("REMEMBER TO ADD MELONNI")
                state.radio_button_selected = PyImGui.radio_button("BLACKTIDE DEN", state.radio_button_selected, 39)
                PyImGui.show_tooltip("REMEMBER TO ADD TAHLKORA")
                state.radio_button_selected = PyImGui.radio_button("CONSULATE DOCKS", state.radio_button_selected, 40)
                PyImGui.show_tooltip("REMEMBER TO ADD ZHED SHADOWHOOF")
                state.radio_button_selected = PyImGui.radio_button("VENTA CEMETERY", state.radio_button_selected, 41)
                PyImGui.show_tooltip("REMEMBER TO ADD KOSS")
                state.radio_button_selected = PyImGui.radio_button("KODONUR CROSSROADS", state.radio_button_selected, 42)
                PyImGui.show_tooltip("REMEMBER TO ADD ZHED SHADOWHOOF")
                state.radio_button_selected = PyImGui.radio_button("POGAHN PASSAGE", state.radio_button_selected, 43)
                PyImGui.show_tooltip("REMEMBER TO ADD MARGRID THE SLY")
                state.radio_button_selected = PyImGui.radio_button("RILOHN REFUGE", state.radio_button_selected, 44)
                PyImGui.show_tooltip("REMEMBER TO ADD MASTER OF WHISPERS")
                state.radio_button_selected = PyImGui.radio_button("MODDOK CREVICE", state.radio_button_selected, 45)
                PyImGui.show_tooltip("REMEMBER TO ADD DUNKORO")
                state.radio_button_selected = PyImGui.radio_button("TIHARK ORCHARD", state.radio_button_selected, 46)
                state.radio_button_selected = PyImGui.radio_button("DASHA VESTIBULE", state.radio_button_selected, 47)
                PyImGui.show_tooltip("REMEMBER TO ADD MARGRID THE SLY")
                state.radio_button_selected = PyImGui.radio_button("DZAGONUR BASTION", state.radio_button_selected, 48)
                PyImGui.show_tooltip("REMEMBER TO ADD MASTER OF WHISPERS")
                state.radio_button_selected = PyImGui.radio_button("GRAND COURT OF SEBELKEH", state.radio_button_selected, 49)
                PyImGui.show_tooltip("REMEMBER TO ADD TAHLKORA")
                state.radio_button_selected = PyImGui.radio_button("JENNUR'S HORDE", state.radio_button_selected, 50)
                PyImGui.show_tooltip("REMEMBER TO ADD KOSS")
                state.radio_button_selected = PyImGui.radio_button("NUNDU BAY", state.radio_button_selected, 51)
                PyImGui.show_tooltip("REMEMBER TO ADD MELONNI")
                state.radio_button_selected = PyImGui.radio_button("GATE OF DESOLATION", state.radio_button_selected, 52)
                PyImGui.show_tooltip("REMEMBER TO ADD ZHED SHADOWHOOF")
                state.radio_button_selected = PyImGui.radio_button("RUINS OF MORAH", state.radio_button_selected, 53)
                PyImGui.show_tooltip("REMEMBER TO ADD GENERAL MORGAHN")
                state.radio_button_selected = PyImGui.radio_button("GATE OF PAIN", state.radio_button_selected, 54)
                PyImGui.show_tooltip("REMEMBER TO ADD ZHED DUNKORO")
                state.radio_button_selected = PyImGui.radio_button("GATE OF MADNESS", state.radio_button_selected, 55)
                state.radio_button_selected = PyImGui.radio_button("ABADDON'S GATE", state.radio_button_selected, 56)
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

            if PyImGui.begin_tab_item("EYE OF THE NORTH"):
                PyImGui.spacing()
                state.radio_button_selected = PyImGui.radio_button("FINDING THE BLOODSTONE", state.radio_button_selected, 57)
                state.radio_button_selected = PyImGui.radio_button("THE ELUSIVE GOLEMANCER", state.radio_button_selected, 58)
                state.radio_button_selected = PyImGui.radio_button("G.O.L.E.M.", state.radio_button_selected, 59)
                state.radio_button_selected = PyImGui.radio_button("AGAINST THE CHARR", state.radio_button_selected, 60)
                state.radio_button_selected = PyImGui.radio_button("WARBAND OF BROTHERS", state.radio_button_selected, 61)
                state.radio_button_selected = PyImGui.radio_button("ASSAULT ON THE STRONGHOLD", state.radio_button_selected, 62)
                state.radio_button_selected = PyImGui.radio_button("CURSE OF THE NORNBEAR", state.radio_button_selected, 63)
                state.radio_button_selected = PyImGui.radio_button("BLOOD WASHES BLOOD", state.radio_button_selected, 64)
                state.radio_button_selected = PyImGui.radio_button("A GATE TOO FAR", state.radio_button_selected, 65)
                state.radio_button_selected = PyImGui.radio_button("DESTRUCTION'S DEPTHS", state.radio_button_selected, 66)
                state.radio_button_selected = PyImGui.radio_button("A TIME FOR HEROES", state.radio_button_selected, 67)          
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
            
            if PyImGui.begin_tab_item("HEROES"):
                PyImGui.spacing()            
                items = ["","KOSS", "GOREN", "JORA", "ACOLYTE JIN", "MARGRID THE SLY", "PYRE FIERCESHOT", "DUNKORO", "TAHLKORA", "OGDEN STONEHEALER", "MASTER OF WHISPERS", "LIVIA", "OLIAS", "NORGU", "GWEN", "ACOLYTE SOUSUKE", "ZHED SHADOWHOOF", "VEKK", "ANTON", "ZENMAI", "MIKU", "XANDRA", "ZEI RI", "MELONNI", "KAHMU", "M.O.X.", "GENERAL MORGAHN", "HAYDA", "KEIRAN THACKERAY", "RAZAH", "MERCENARY HERO: 1", "MERCENARY HERO: 2", "MERCENARY HERO: 3", "MERCENARY HERO: 4", "MERCENARY HERO: 5", "MERCENARY HERO: 6", "MERCENARY HERO: 7", "MERCENARY HERO: 8"]
                state.combo_selected_1 = PyImGui.combo("HERO 1", state.combo_selected_1, items)
                state.combo_selected_2 = PyImGui.combo("HERO 2", state.combo_selected_2, items)
                state.combo_selected_3 = PyImGui.combo("HERO 3", state.combo_selected_3, items)
                state.combo_selected_4 = PyImGui.combo("HERO 4", state.combo_selected_4, items)
                state.combo_selected_5 = PyImGui.combo("HERO 5", state.combo_selected_5, items)
                state.combo_selected_6 = PyImGui.combo("HERO 6", state.combo_selected_6, items)
                state.combo_selected_7 = PyImGui.combo("HERO 7", state.combo_selected_7, items)
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("SETTINGS"):
                PyImGui.spacing()            
                state.checkbox_state_1 = PyImGui.checkbox("HM", state.checkbox_state_1)
                state.checkbox_state_2 = PyImGui.checkbox("USE LEGIONNAIRE STONE", state.checkbox_state_2)
                state.checkbox_state_3 = PyImGui.checkbox("USE BU", state.checkbox_state_3)
                state.checkbox_state_4 = PyImGui.checkbox("USE CONSET", state.checkbox_state_4)
                state.checkbox_state_5 = PyImGui.checkbox("TAKE ZAISHEN QUEST", state.checkbox_state_5)
                PyImGui.spacing()  
                PyImGui.end_tab_item()


    PyImGui.end()

def main():
    global bot_vars, FSM_vars
    global Py4GW_window_state, Py4GW_descriptions, description_index, ping_handler, timer_instance
    global overlay, show_mouse_world_pos, show_area_rings, mark_target

    try:
        if Party.IsPartyLoaded() and Map.IsMapReady():
            DrawWindow()

        if IsBotStarted():    
        
            if state.radio_button_selected == 0:
                if FSM_vars.state_machine_TheGreatNorthernWall.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_TheGreatNorthernWall.update() 
                    
            elif state.radio_button_selected == 1:
                if FSM_vars.state_machine_FortRanik.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_FortRanik.update() 

            elif state.radio_button_selected == 2:
                if FSM_vars.state_machine_RuinsOfSurmia.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_RuinsOfSurmia.update() 

            elif state.radio_button_selected == 3:
                if FSM_vars.state_machine_NolaniAcademy.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_NolaniAcademy.update()    

            elif state.radio_button_selected == 4:
                if FSM_vars.state_machine_BorlisPass.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_BorlisPass.update()     

            elif state.radio_button_selected == 5:
                if FSM_vars.state_machine_TheFrostGate.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_TheFrostGate.update()  

            elif state.radio_button_selected == 6:
                if FSM_vars.state_machine_GatesOfKryta.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_GatesOfKryta.update()       
                    
            elif state.radio_button_selected == 7:
                if FSM_vars.state_machine_DAlessioSeaboard.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_DAlessioSeaboard.update()  

            elif state.radio_button_selected == 8:
                if FSM_vars.state_machine_DivinityCoast.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_DivinityCoast.update()  

            elif state.radio_button_selected == 9:
                if FSM_vars.state_machine_TheWilds.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_TheWilds.update()  

    except ImportError as e:
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"ImportError encountered: {str(e)}",
            Py4GW.Console.MessageType.Error
        )
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error
        )
    except ValueError as e:
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"ValueError encountered: {str(e)}",
            Py4GW.Console.MessageType.Error
        )
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error
        )
    except TypeError as e:
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"TypeError encountered: {str(e)}",
            Py4GW.Console.MessageType.Error
        )
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error
        )
    except Exception as e:
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"Unexpected error encountered: {str(e)}",
            Py4GW.Console.MessageType.Error
        )
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error
        )
    finally:
        pass

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Legendary Guardian Bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi Account Bot for Legendary Guardian Missions")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by TH3KUM1KO")
    PyImGui.end_tooltip()
    

if __name__ == "__main__":
    main()

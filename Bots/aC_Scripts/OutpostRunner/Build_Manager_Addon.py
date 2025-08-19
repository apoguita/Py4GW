import time
from Py4GWCoreLib import *

jotun = [6480, 6481, 6482, 6483]
modniir = [6475, 6476, 6473]
frozen_elementals = [6478]
mandragor = [4400, 4930, 4396, 4402, 4932, 4401, 4931, 4307, 4306, 6658, 6657]
wurms = [1802, 4323, 7326, 6491, 2547] 
mountain_pinesoul = [6488]
skeletons = [7038, 7040, 2740]
zombie = [7043]
enchanted = [6862, 1866, 6869]
quetzal = [6337, 6338, 6339, 6340]
stone_summit_scout = [2646]
minotaur = [1797, 2493, 2486]
summit_giant = [2657]
skree = [4678]
spiders = [2312]
roots = [2307]
gouls = [2732, 2731]
azura = [2535]
thundra_giant = [2530] # special case, uses ranged attach but is a warrior

#== variable for scan throttle ==
scan_throttle_ms = 0.1
danger_check_cooldown = 0.1
spell_caster_check_cooldown = 1
#== variables for anti cripple/kd danger check ==
cripple_kd_models = set(jotun + modniir + frozen_elementals + mandragor + wurms + mountain_pinesoul + skeletons + zombie + enchanted + quetzal + stone_summit_scout + minotaur + summit_giant + skree + spiders + roots + gouls + azura)
tundra_giant_ids = set(thundra_giant)
last_cripple_kd_check = 0
last_cripple_kd_scan_time = 0
#== variables for spellcaster danger check ==
last_spellcaster_check = 0
last_scan_time_spellcaster = 0
#== variables for stuck detection ==
prev_pos = None
last_move_time = time.time()

# Initialize FSM runner


def get_cripple_kd_enemies(model_id):
    """Return the category name based on which list contains the model_id."""
    if model_id in jotun:
        return "Jotun"
    elif model_id in modniir:
        return "Modniir"
    elif model_id in frozen_elementals:
        return "Frozen Elemental"
    elif model_id in mandragor:
        return "Mandragor"
    elif model_id in wurms:
        return "Wurm"
    elif model_id in mountain_pinesoul:
        return "Mountain Pinesouls"
    elif model_id in enchanted:
        return "Enchanted sword or axe"
    elif model_id in skeletons:
        return "Skeletons"
    elif model_id in zombie:
        return "Zombie Brute"
    elif model_id in quetzal:
        return "Quetzal Stark"
    elif model_id in minotaur:
        return "Minotuar"
    elif model_id in stone_summit_scout:
        return "Stone Summit Scout"
    elif model_id in summit_giant:
        return "Summit Giants"
    elif model_id in skree:
        return "Skree"
    elif model_id in spiders:
        return "Spiders"
    elif model_id in roots:
        return "Roots"
    elif model_id in gouls:
        return "Gouls"
    elif model_id in azura:
        return "Azura"
    return "Unknown"

def CheckCrippleKDanger(x, y):
    """
    Checks if any dangerous foe is within the correct range:
    - Most enemies: 500 units
    - Special case (Tundra Giant): 2000 units
    """
    global last_cripple_kd_check, last_cripple_kd_scan_time, scan_throttle_ms, danger_check_cooldown

    now = time.time()
    if now - last_cripple_kd_check < danger_check_cooldown:
        return  

    if now - last_cripple_kd_scan_time < scan_throttle_ms:
        return
    last_cripple_kd_scan_time = now

    close_enemies = Routines.Agents.GetFilteredEnemyArray(x, y, max_distance=500.0)
    far_enemies = Routines.Agents.GetFilteredEnemyArray(x, y, max_distance=2000.0)

    for enemy_id in close_enemies:
        model_id = GLOBAL_CACHE.Agent.GetModelID(enemy_id)
        if model_id in cripple_kd_models:
            enemy_category = get_cripple_kd_enemies(model_id)
            Player.SendFakeChat(ChatChannel.CHANNEL_WARNING, f"Cripple/KD danger - {enemy_category} spotted!")
            last_cripple_kd_check = now
            return True

    for enemy_id in far_enemies:
        model_id = GLOBAL_CACHE.Agent.GetModelID(enemy_id)
        if model_id in tundra_giant_ids:
            enemy_category = get_cripple_kd_enemies(model_id)
            Player.SendFakeChat(ChatChannel.CHANNEL_WARNING, f"Cripple/KD danger - {enemy_category} spotted!")
            last_cripple_kd_check = now
            return True
    return False


def CheckSpellcasterDanger(custom_distance=2000):
    """
    Checks if any dangerous spellcaster enemy
    is within 2000 units. If found, logs a warning and starts a 20s cooldown before next check.
    """
    global last_spellcaster_check, last_scan_time_spellcaster, scan_throttle_ms, spell_caster_check_cooldown
    checkdistance = custom_distance

    player_pos = GLOBAL_CACHE.Player.GetXY()
    special_casters = [6481, 6482, 6483, 6634, 4316, 4315, 4317]

    now_spellcaster = time.time()
    if now_spellcaster - last_spellcaster_check < spell_caster_check_cooldown:
        return
    
    if now_spellcaster - last_scan_time_spellcaster < scan_throttle_ms:
        return
    last_scan_time_spellcaster = now_spellcaster

    nearby_enemies = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance=2000.0)
    special_caster_found = False
    for enemy_id in nearby_enemies:
        model_id = GLOBAL_CACHE.Agent.GetModelID(enemy_id)
        if model_id in special_casters:
            special_caster_found = True
            break

    nearby_spellcaster = Routines.Agents.GetNearestEnemyCaster(checkdistance, aggressive_only = False)
    
    if special_caster_found or nearby_spellcaster:
            Player.SendFakeChat(ChatChannel.CHANNEL_WARNING, f"Spellcaster - spotted!")
            #ConsoleLog("Build Manager",f"Spellcaster - spotted!",Console.MessageType.Debug)
            last_spellcaster_check = now_spellcaster
            return True 
    return False

def BodyBlockDetection(seconds=2.0):
    nearby_enemies = Routines.Agents.GetNearestEnemy(Range.Touch.value)
    global last_move_time, prev_pos
    if nearby_enemies:
        pos = GLOBAL_CACHE.Player.GetXY()
        if not pos:
            return False
    
        if not prev_pos:
            prev_pos = pos
            last_move_time = time.time()
            return False

        if Utils.Distance(pos, prev_pos) > Range.Touch.value:
            prev_pos = pos
            last_move_time = time.time()
            return False

        return time.time() - last_move_time >= seconds

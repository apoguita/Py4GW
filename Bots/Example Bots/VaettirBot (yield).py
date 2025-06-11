import Py4GW
from Py4GWCoreLib import Timer
from Py4GWCoreLib import ImGui, PyImGui
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import ModelID, TitleID
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Range
from Py4GWCoreLib import Utils, Color
from Py4GWCoreLib import LootConfig


from time import sleep
from typing import Generator, List, Tuple

MODULE_NAME = "Apo's YAVB (yield example)"
#region paths

path_points_to_merchant: List[Tuple[float, float]] = [(-23041, 14939)]
path_points_to_leave_outpost: List[Tuple[float, float]] = [(-24380, 15074), (-26375, 16180)]
path_points_to_traverse_bjora_marches: List[Tuple[float, float]] = [
    (17810, -17649), (16582, -17136), (15257, -16568), (14084, -15748), (12940, -14873),
    (11790, -14004), (10640, -13136), (9404 , -12411), (8677 , -11176), (8581 , -9742 ),
    (7892 , -8494 ), (6989 , -7377 ), (6184 , -6180 ), (5384 , -4980 ), (4549 , -3809 ),
    (3622 , -2710 ), (2601 , -1694 ), (1185 , -1535 ), (-251 , -1514 ), (-1690, -1626 ),
    (-3122, -1771 ), (-4556, -1752 ), (-5809, -1109 ), (-6966,  -291 ), (-8390,  -142 ),
    (-9831,  -138 ), (-11272, -156 ), (-12685, -198 ), (-13933,  267 ), (-14914, 1325 ),
    (-15822, 2441 ), (-16917, 3375 ), (-18048, 4223 ), (-19196, 4986 ), (-20000, 5595 ),
    (-20300, 5600 )
]

path_points_to_npc:List[Tuple[float, float]]  = [(13367, -20771)]

path_points_to_farming_route1: List[Tuple[float, float]] = [
    (12496, -22600), (11375, -22761), (10925, -23466), (10917, -24311), (9910, -24599),
    (8995, -23177), (8307, -23187), (8213, -22829), (8307, -23187), (8213, -22829),
    (8740, -22475), (8880, -21384), (8684, -20833), (9665, -20415)
]

path_points_to_farming_route2: List[Tuple[float, float]] = [
    (10196, -20124), (9976, -18338), (11316, -18056), (10392, -17512), (10114, -16948),
    (10729, -16273), (10810, -15058), (11120, -15105), (11670, -15457), (12604, -15320),
    (12476, -16157)
]

path_points_to_killing_spot: List[Tuple[float, float]] = [
    (12890, -16450),
    (12920, -17032),
    (12847, -17136),
    (12720, -17222),
    (12617, -17273),
    (12518, -17305),
    (12445, -17327)
]

path_points_to_exit_jaga_moraine: List[Tuple[float, float]] = [(12289, -17700) ,(13970, -18920), (15400, -20400),(15850,-20550)]

path_points_to_return_to_jaga_moraine: List[Tuple[float, float]] = [(-20300, 5600 )] ## A Dekoy Accadia: removed unnecessary coordinates to re-enter Jaga.


#endregion

#region globals
class build:
    deadly_paradox:int = 0
    shadow_form:int = 0
    shroud_of_distress:int = 0
    way_of_perfection:int = 0
    heart_of_shadow:int = 0
    wastrels_demise:int = 0
    arcane_echo:int = 0
    channeling:int = 0
    zealous_renewal:int = 0
    heart_of_holy_flame:int = 0
    pious_fury:int = 0

class InventoryConfig:
    def __init__(self):
        self.leave_free_slots = 3
        self.keep_id_kit = 2
        self.keep_salvage_kit = 5
        self.keep_gold_amount = 5000
        
class SellConfig:
    def __init__(self):
        self.sell_whites = True
        self.sell_blues = True
        self.sell_purples = True
        self.sell_golds = False
        self.sell_materials = True
        self.sell_wood = True
        self.sell_iron = True
        self.sell_dust = True
        self.sell_bones = True
        self.sell_cloth = True
        self.sell_granite = True
        
class IDConfig:
    def __init__(self):
        self.id_blues = True
        self.id_purples = True
        self.id_golds = False
        
class SalvageConfig:
    def __init__(self):
        self.salvage_whites = True
        self.salvage_blues = True
        self.salvage_purples = True
        self.salvage_golds = False
        self.salvage_glacial_stones = False
        self.salvage_purple_with_sup_kit = False
        self.salvage_gold_with_sup_kit = False
        
class LootConfigclass:
    def __init__(self):
        self.loot_blues = True
        self.loot_purples = True
        self.loot_golds = True
        self.loot_tomes = False
        self.loot_white_dyes = True
        self.loot_black_dyes = True
        self.loot_lockpicks = True
        self.loot_whites = True
        self.loot_dyes = False
        self.loot_glacial_stones = True
        self.loot_event_items = True
        self.loot_map_pieces = False
        
class Botconfig:
    def __init__(self):
        self.in_killing_routine = False
        self.pause_stuck_routine = False
        self.finished_routine = False
        self.reset_from_jaga_moraine = False
        self.is_script_running = False
        self.log_to_console = True # Controls whether to print to console
        self.auto_stuck_command_timer = Timer()
        self.auto_stuck_command_timer.Start()
        self.stuck_count = 0
        self.non_movement_timer = Timer()
        self.old_player_x = 0.0
        self.old_player_y = 0.0
        self.window_module = ImGui.WindowModule()

class BOTVARIABLES:
    def __init__(self):
        self.inventory_config = InventoryConfig()
        self.sell_config = SellConfig()
        self.id_config = IDConfig()
        self.salvage_config = SalvageConfig()
        self.config = Botconfig()
        self.loot_config = LootConfigclass()
        
        self.skillbar = build()
        
bot_variables = BOTVARIABLES()
bot_variables.config.window_module = ImGui.WindowModule(MODULE_NAME, window_name=MODULE_NAME, window_size=(300, 300), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

#endregion

#region helpers

def IsSkillBarLoaded():
    global bot_variables
    global skillbar

    primary_profession, secondary_profession = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if ((primary_profession == "Assassin" and secondary_profession != "Mesmer")):

        ConsoleLog(IsSkillBarLoaded, f"This bot requires A/Me to work, halting.", Py4GW.Console.MessageType.Error, log=True)
        return False

    bot_variables.skillbar.deadly_paradox = GLOBAL_CACHE.Skill.GetID("Deadly_Paradox")
    bot_variables.skillbar.shadow_form = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
    bot_variables.skillbar.shroud_of_distress = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
    bot_variables.skillbar.way_of_perfection = GLOBAL_CACHE.Skill.GetID("Way_of_Perfection")
    bot_variables.skillbar.heart_of_shadow = GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow")
    bot_variables.skillbar.wastrels_demise = GLOBAL_CACHE.Skill.GetID("Wastrel's_Demise")
    bot_variables.skillbar.arcane_echo = GLOBAL_CACHE.Skill.GetID("Arcane_Echo")
    bot_variables.skillbar.channeling = GLOBAL_CACHE.Skill.GetID("Channeling")
    #added for allowing more classes
    bot_variables.skillbar.zealous_renewal = GLOBAL_CACHE.Skill.GetID("Zealous_Renewal")
    bot_variables.skillbar.heart_of_holy_flame = GLOBAL_CACHE.Skill.GetID("Heart_of_Holy_Flame")
    bot_variables.skillbar.pious_fury = GLOBAL_CACHE.Skill.GetID("Pious_Fury")
    
    ConsoleLog(MODULE_NAME, f"SkillBar Loaded.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)       
    return True

def SetHardMode():
    global bot_variables
    GLOBAL_CACHE.Party.SetHardMode()
    ConsoleLog(MODULE_NAME, "Hard mode set.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
    
def reset_environment():
    global bot_variables
    bot_variables.config.is_script_running = False
    bot_variables.config.reset_from_jaga_moraine = False
    bot_variables.config.in_killing_routine = False
    bot_variables.config.stuck_count = 0
    GLOBAL_CACHE._ActionQueueManager.ResetAllQueues()

def NeedsToHandleInventory():
    global bot_variables
    free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
    count_of_id_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value) #5899 model for ID kit
    count_of_salvage_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value) #2992 model for salvage kit
    items_to_sell = get_filtered_materials_to_sell()
    
    needs_to_handle_inventory = False
    if free_slots_in_inventory < bot_variables.inventory_config.leave_free_slots:
        needs_to_handle_inventory = True
    if count_of_id_kits < bot_variables.inventory_config.keep_id_kit:
        needs_to_handle_inventory = True
    if count_of_salvage_kits < bot_variables.inventory_config.keep_salvage_kit:
        needs_to_handle_inventory = True
    if len(items_to_sell) > 0:
        needs_to_handle_inventory = True
    if len(filter_identify_array()) > 0:
        needs_to_handle_inventory = True
    if len(filter_salvage_array()) > 0:
        needs_to_handle_inventory = True
    if len(filter_items_to_deposit()) > 0:
        needs_to_handle_inventory = True
    
    return needs_to_handle_inventory

def GetIDKitsToBuy():
    global bot_variables
    count_of_id_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value) #5899 model for ID kit
    id_kits_to_buy = bot_variables.inventory_config.keep_id_kit - count_of_id_kits
    return id_kits_to_buy

def GetSalvageKitsToBuy():
    global bot_variables
    count_of_salvage_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value) #2992 model for salvage kit
    salvage_kits_to_buy = bot_variables.inventory_config.keep_salvage_kit - count_of_salvage_kits
    return salvage_kits_to_buy

def IsMaterial(item_id):
    material_model_ids = {ModelID.Wood_Plank.value, 
                          ModelID.Iron_Ingot.value, 
                          ModelID.Pile_Of_Glittering_Dust.value, 
                          ModelID.Bone.value, 
                          ModelID.Bolt_Of_Cloth.value, 
                          ModelID.Granite_Slab.value}  # Add all known material IDs
    
    return GLOBAL_CACHE.Item.GetModelID(item_id) in material_model_ids
	
def IsGranite(item_id):
    """Check if the item is granite."""
    granite_model_ids = {ModelID.Granite_Slab.value}  # Granite ID
    return GLOBAL_CACHE.Item.GetModelID(item_id) in granite_model_ids
	
def IsWood(item_id):
    """Check if the item is wood."""
    wood_model_ids = {ModelID.Wood_Plank.value}  # Replace with the correct IDs for wood
    return GLOBAL_CACHE.Item.GetModelID(item_id) in wood_model_ids

def IsIron(item_id):
    """Check if the item is iron."""
    iron_model_ids = {ModelID.Iron_Ingot.value}  # Replace with the correct IDs for iron
    return GLOBAL_CACHE.Item.GetModelID(item_id) in iron_model_ids

def IsDust(item_id):
    """Check if the item is glittering dust."""
    dust_model_ids = {ModelID.Pile_Of_Glittering_Dust.value}  # Replace with the correct IDs for dust
    return GLOBAL_CACHE.Item.GetModelID(item_id) in dust_model_ids

def IsBones(item_id):
    """Check if the item is bones."""
    bone_model_ids = {ModelID.Bone.value}  # Replace with the correct IDs for bones
    return GLOBAL_CACHE.Item.GetModelID(item_id) in bone_model_ids

def IsCloth(item_id):
    """Check if the item is cloth."""
    cloth_model_ids = {ModelID.Bolt_Of_Cloth.value}  # Replace with the correct IDs for cloth
    return GLOBAL_CACHE.Item.GetModelID(item_id) in cloth_model_ids


def get_filtered_materials_to_sell():
    global bot_variables
    # Get items from the specified bags
    bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    items_to_sell = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)

    # Filter materials first using the centralized definition
    items_to_sell = ItemArray.Filter.ByCondition(items_to_sell, lambda item_id: IsMaterial(item_id))

    # Apply individual material filters
    filtered_items = []
    if bot_variables.sell_config.sell_wood:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsWood))
    if bot_variables.sell_config.sell_iron:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsIron))
    if bot_variables.sell_config.sell_dust:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsDust))
    if bot_variables.sell_config.sell_bones:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsBones))
    if bot_variables.sell_config.sell_cloth:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsCloth))
    if bot_variables.sell_config.sell_granite:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsGranite))
        
    return filtered_items

def filter_identify_array():
    global bot_variables
    bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1,2,3,4)
    unidentified_items = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
    unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not GLOBAL_CACHE.Item.Rarity.IsWhite(item_id))
    unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not GLOBAL_CACHE.Item.Usage.IsIdentified(item_id))

    return unidentified_items

def filter_salvage_array():
    global bot_variables
    bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1,2,3,4)
    salvageable_items = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)

    salvageable_items = ItemArray.Filter.ByCondition(salvageable_items,lambda item_id: GLOBAL_CACHE.Item.Usage.IsIdentified(item_id) or GLOBAL_CACHE.Item.Rarity.IsWhite(item_id))

    salvageable_items = ItemArray.Filter.ByCondition(salvageable_items,lambda item_id: GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id))

    return salvageable_items
          
def filter_items_to_deposit():
    bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1,2,3,4)
    items_to_deposit = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
    banned_models = {ModelID.Salvage_Kit.value,ModelID.Superior_Identification_Kit.value}
    items_to_deposit = ItemArray.Filter.ByCondition(items_to_deposit, lambda item_id: GLOBAL_CACHE.Item.GetModelID(item_id) not in banned_models)
    return items_to_deposit

def player_is_dead_or_map_loading(destination_map_id=0):
    if GLOBAL_CACHE.Map.IsMapLoading():
        return True
    if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        return True
    
    if GLOBAL_CACHE.Map.GetMapID() == destination_map_id:
        return True
    return False

    
def player_is_dead():
    return GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID())

def handle_death():
    if (GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()) or not bot_variables.config.is_script_running):
        ConsoleLog(MODULE_NAME, f"Player is dead while traversing {GLOBAL_CACHE.Map.GetMapName(GLOBAL_CACHE.Map.GetMapID())} . Reseting Environment.", Py4GW.Console.MessageType.Error, log=bot_variables.config.log_to_console)
        return True
    return False

    
def handle_return_inventory_check():
    global bot_variables
    if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < bot_variables.inventory_config.leave_free_slots:
        ConsoleLog(MODULE_NAME, f"Inventory is full, going to merchant.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
        return True
    
    count_of_id_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value) #5899 model for ID kit
    if count_of_id_kits <=0:
        ConsoleLog(MODULE_NAME, f"Need to buy ID kits, going to merchant.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
        return True
    
    count_of_salvage_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value) #2992 model for salvage kit
    if count_of_salvage_kits <=0:
        ConsoleLog(MODULE_NAME, f"Need to buy Salvage kits, going to merchant.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
        return True
    
    return False

def GetNotHexedEnemy():
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id:not GLOBAL_CACHE.Agent.IsHexed(agent_id))
    if len(enemy_array) == 0:
        return 0
    
    return enemy_array[0]


def get_escape_location(scaling_factor=50):
    """
    Moves the player to a calculated escape location based on enemy repulsion.
    
    Args:
        scaling_factor (float): Factor to scale the escape vector magnitude. Default is 5.
    
    Returns:
        tuple: The escape destination (x, y).
    """
    # Get the player's current position
    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
    
    # Initialize VectorFields with the player's position
    vector_fields = Utils.VectorFields(probe_position=(player_x, player_y))

    # Get and filter the enemy array
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), Range.Area.value)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    
    # Configure the enemy array and add it to the vector fields
    agent_arrays = [
        {
            'name': 'enemies',
            'array': enemy_array,
            'radius': Range.Area.value,  # Use the appropriate range
            'is_dangerous': True  # Enemies are repulsive (dangerous)
        }
    ]
    
    # Generate the escape vector
    escape_vector = vector_fields.generate_escape_vector(agent_arrays)
    
    # Scale the escape vector
    scaled_escape_vector = (
        escape_vector[0] * scaling_factor,
        escape_vector[1] * scaling_factor
    )
    
    # Calculate the destination coordinates
    destination = (
        player_x - scaled_escape_vector[0],
        player_y - scaled_escape_vector[1]
    )
 
    # Return the destination for reference
    return destination
        
def InventoryHandler(log_to_console=False):
    if NeedsToHandleInventory():
        #going to merchant
        if log_to_console:
            ConsoleLog(MODULE_NAME, "Going to merchant.", Py4GW.Console.MessageType.Info, log=log_to_console)
        yield from Routines.Yield.Agents.InteractWithAgentXY(-23110, 14942)
        
        if bot_variables.sell_config.sell_materials:
            items_to_sell = get_filtered_materials_to_sell()
            #sell materials to make space
            if log_to_console:
                ConsoleLog(MODULE_NAME, "Selling materials.", Py4GW.Console.MessageType.Info, log=log_to_console)
            yield from Routines.Yield.Merchant.SellItems(items_to_sell, log_to_console)
        if log_to_console:
            ConsoleLog(MODULE_NAME, "Buying ID and Salvage kits.", Py4GW.Console.MessageType.Info, log=log_to_console)
        yield from Routines.Yield.Merchant.BuyIDKits(GetIDKitsToBuy(),log_to_console)
        yield from Routines.Yield.Merchant.BuySalvageKits(GetSalvageKitsToBuy(),log_to_console)
        
        items_to_idenfity = filter_identify_array()
        if log_to_console:
            ConsoleLog(MODULE_NAME,f"IDing {len(items_to_idenfity)} items.", Py4GW.Console.MessageType.Info, log=log_to_console)
        yield from Routines.Yield.Items.IdentifyItems(items_to_idenfity, log_to_console)
        
        items_to_salvage = filter_salvage_array()
        if log_to_console:
            ConsoleLog(MODULE_NAME, f"Salvaging {items_to_salvage} items.", Py4GW.Console.MessageType.Info, log=log_to_console)
        yield from Routines.Yield.Items.SalvageItems(items_to_salvage, log_to_console)
        
        if log_to_console:
            ConsoleLog(MODULE_NAME, "Selling items.", Py4GW.Console.MessageType.Info, log=log_to_console)
        if bot_variables.sell_config.sell_materials:
            items_to_sell = get_filtered_materials_to_sell()
            yield from Routines.Yield.Merchant.SellItems(items_to_sell, log_to_console)
            
        if log_to_console:
            ConsoleLog(MODULE_NAME, "Depositing items.", Py4GW.Console.MessageType.Info, log=log_to_console)  
        items_to_deposit = filter_items_to_deposit()
        yield from Routines.Yield.Items.DepositItems(items_to_deposit,log_to_console)
        if log_to_console:
            ConsoleLog(MODULE_NAME, "Depositing gold.", Py4GW.Console.MessageType.Info, log=log_to_console)
        yield from Routines.Yield.Items.DepositGold(bot_variables.inventory_config.keep_gold_amount, log_to_console)
        
    yield
    
#endregion
  

#region stuck

def Handle_Stuck():
    """
    Detect and recover the player when stuck. Uses timers and movement logic.
    """
    global bot_variables
    
    longeyes_ledge = GLOBAL_CACHE.Map.GetMapIDByName("Longeyes Ledge")
    bjora_marches = GLOBAL_CACHE.Map.GetMapIDByName("Bjora Marches")
    jaga_moraine = GLOBAL_CACHE.Map.GetMapIDByName("Jaga Moraine")

    if GLOBAL_CACHE.Map.IsMapLoading():
        bot_variables.config.auto_stuck_command_timer.Reset()
        bot_variables.config.stuck_count = 0
        return
    
    if GLOBAL_CACHE.Map.GetMapID() == longeyes_ledge:
        bot_variables.config.auto_stuck_command_timer.Reset()
        bot_variables.config.non_movement_timer.Reset()
        bot_variables.config.stuck_count = 0
        return
    
    if bot_variables.config.pause_stuck_routine:
        bot_variables.config.auto_stuck_command_timer.Reset()
        bot_variables.config.non_movement_timer.Reset()
        bot_variables.config.stuck_count = 0
        return
    
    if bot_variables.config.in_killing_routine:
        bot_variables.config.auto_stuck_command_timer.Reset()
        bot_variables.config.non_movement_timer.Reset()
        bot_variables.config.stuck_count = 0
        return
    
    if bot_variables.config.finished_routine:
        bot_variables.config.auto_stuck_command_timer.Reset()
        bot_variables.config.non_movement_timer.Reset()
        bot_variables.config.stuck_count = 0
        return
    
    
    # Check for periodic "stuck" chat command
    if bot_variables.config.auto_stuck_command_timer.HasElapsed(5000):
        GLOBAL_CACHE.Player.SendChatCommand("stuck")
        bot_variables.config.auto_stuck_command_timer.Reset()

    # Handle severe stuck situations
    if bot_variables.config.stuck_count > 10:
        restart_due_to_stuck()

    # Detect and handle non-movement
    if not GLOBAL_CACHE.Agent.IsMoving(GLOBAL_CACHE.Player.GetAgentID()):
        handle_non_movement()
    else:
        handle_player_movement()


def restart_due_to_stuck():
    """Logs and restarts the bot when recovery fails repeatedly."""
    global bot_variables
    ConsoleLog(MODULE_NAME, "Player is stuck, cannot recover, restarting.", Py4GW.Console.MessageType.Error)
    bot_variables.config.stuck_count = 0
    reset_environment()

def handle_non_movement():
    """Attempts to recover from non-movement situations."""
    global bot_variables

    if not bot_variables.config.non_movement_timer.IsRunning():
        bot_variables.config.non_movement_timer.Reset()

    if bot_variables.config.non_movement_timer.HasElapsed(3000):
        bot_variables.config.non_movement_timer.Reset()
        GLOBAL_CACHE.Player.SendChatCommand("stuck")
        escape_location = get_escape_location()
        GLOBAL_CACHE.Player.Move(escape_location[0], escape_location[1])
        bot_variables.config.stuck_count += 1
        log_stuck_attempt(escape_location)

def handle_player_movement():
    """Tracks player movement and resets relevant timers if moving."""
    new_player_x, new_player_y = GLOBAL_CACHE.Player.GetXY()
    if bot_variables.config.old_player_x != new_player_x or bot_variables.config.old_player_y != new_player_y:
        bot_variables.config.non_movement_timer.Reset()
        bot_variables.config.old_player_x = new_player_x
        bot_variables.config.old_player_y = new_player_y
        bot_variables.config.stuck_count = 0

def log_stuck_attempt(escape_location):
    """Logs details of a recovery attempt."""
    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
    distance = Utils.Distance((player_x, player_y), escape_location)
    ConsoleLog("StuckHandler", f"Player is stuck, attempting to recover to {escape_location} (distance: {distance:.2f})", Py4GW.Console.MessageType.Warning)

#endregion

#region Sequential coding
def RunBotSequentialLogic():
    """function that manages the logic of the bot"""
    global bot_variables


    bot_variables.config.reset_from_jaga_moraine = False
    yield from Routines.Yield.wait(1000)
    while True:
        if not bot_variables.config.is_script_running:
            yield from Routines.Yield.wait(1000)
            continue
    
        log_to_console = bot_variables.config.log_to_console
        
        longeyes_ledge = GLOBAL_CACHE.Map.GetMapIDByName("Longeyes Ledge")
        bjora_marches = GLOBAL_CACHE.Map.GetMapIDByName("Bjora Marches")
        jaga_moraine = GLOBAL_CACHE.Map.GetMapIDByName("Jaga Moraine")
        
        primary_profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        
        if not bot_variables.config.reset_from_jaga_moraine:
            ConsoleLog(MODULE_NAME, "Entering Longeyes Ledge", Py4GW.Console.MessageType.Info, log=log_to_console)
            yield from Routines.Yield.Map.TravelToOutpost(longeyes_ledge, log_to_console)
            

            ConsoleLog(MODULE_NAME, "Loading Skillbar", Py4GW.Console.MessageType.Info, log=log_to_console)
            if primary_profession == "Assassin":
                yield from Routines.Yield.Skills.LoadSkillbar("OwVUI2h5lPP8Id2BkAiAvpLBTAA", log_to_console)
            elif primary_profession == "Dervish":
                yield from Routines.Yield.Skills.LoadSkillbar("Ogej8xpDLT8I6MHQEQIQjbjXihA", log_to_console)
            
            if not IsSkillBarLoaded():
                reset_environment()
                ConsoleLog(MODULE_NAME, "You need the following build: OwVUI2h5lPP8Id2BkAiAvpLBTAA", Py4GW.Console.MessageType.Error, log=True)
                break
            
            ConsoleLog(MODULE_NAME, "Setting Hard Mode", Py4GW.Console.MessageType.Info, log=log_to_console)
            yield from Routines.Yield.Map.SetHardMode(log_to_console)
            ConsoleLog(MODULE_NAME, "Setting Title", Py4GW.Console.MessageType.Info, log=log_to_console)
            yield from Routines.Yield.Player.SetTitle(TitleID.Norn.value, log_to_console)       
            #inventory management  
            ConsoleLog(MODULE_NAME, "Handling Inventory", Py4GW.Console.MessageType.Info, log=log_to_console)
            yield from InventoryHandler(log_to_console)
            #exit outpost
            ConsoleLog(MODULE_NAME, "Leaving Outpost", Py4GW.Console.MessageType.Info, log=log_to_console)
            yield from Routines.Yield.Movement.FollowPath(path_points= path_points_to_leave_outpost, custom_exit_condition=lambda: GLOBAL_CACHE.Map.IsMapLoading() or not bot_variables.config.is_script_running, log=False)
            ConsoleLog(MODULE_NAME, "Waiting for map load", Py4GW.Console.MessageType.Info, log=log_to_console)
            yield from Routines.Yield.Map.WaitforMapLoad(bjora_marches,log_to_console)
            bot_variables.config.pause_stuck_routine = False
            #traverse bjora marches
            ConsoleLog(MODULE_NAME, "traversing bjora marches", Py4GW.Console.MessageType.Info, log=log_to_console)
            yield from Routines.Yield.Movement.FollowPath(path_points_to_traverse_bjora_marches, custom_exit_condition=lambda: player_is_dead_or_map_loading(jaga_moraine) or not bot_variables.config.is_script_running)
            ConsoleLog(MODULE_NAME,"Finished traversing bjora marches", Py4GW.Console.MessageType.Info, log=log_to_console)
            bot_variables.config.pause_stuck_routine = True
            
            if Routines.Checks.Map.MapValid():
                if handle_death():
                    ConsoleLog(MODULE_NAME, "Player is dead while traversing bjora marches. Reseting Environment.", Py4GW.Console.MessageType.Error, log=log_to_console)
                    bot_variables.config.reset_from_jaga_moraine = False
                    continue
            ConsoleLog(MODULE_NAME,"Entering Waiting for map load", Py4GW.Console.MessageType.Info, log=log_to_console)
            yield from Routines.Yield.Map.WaitforMapLoad(jaga_moraine, log_to_console)
            bot_variables.config.reset_from_jaga_moraine = True
            
        ConsoleLog(MODULE_NAME, "following npc path", Py4GW.Console.MessageType.Info, log=log_to_console)   
        
        yield from Routines.Yield.Movement.FollowPath(path_points_to_npc, custom_exit_condition=lambda: player_is_dead() or not bot_variables.config.is_script_running)
        #take bounty
        yield from Routines.Yield.Agents.InteractWithAgentXY(13367, -20771)
        yield from Routines.Yield.Player.SendDialog("0x84")
        bot_variables.config.pause_stuck_routine = False
        yield from Routines.Yield.Movement.FollowPath(path_points_to_farming_route1,custom_exit_condition=lambda: player_is_dead() or not bot_variables.config.is_script_running)
        if handle_death():
            ConsoleLog(MODULE_NAME, "Player is dead while tont farming Route 1. Reseting Environment.", Py4GW.Console.MessageType.Error, log=log_to_console)
            bot_variables.config.reset_from_jaga_moraine = False
            continue
        
        #wait for aggro ball'
        ConsoleLog(MODULE_NAME, "Waiting for left aggro ball", Py4GW.Console.MessageType.Info, log=log_to_console)
        bot_variables.config.pause_stuck_routine = True
        yield from Routines.Yield.wait(15000)
        ConsoleLog(MODULE_NAME,"Finished waiting for left aggro ball", Py4GW.Console.MessageType.Info, log=log_to_console)
        bot_variables.config.pause_stuck_routine = False
        
        yield from Routines.Yield.Movement.FollowPath(path_points_to_farming_route2,custom_exit_condition=lambda: player_is_dead() or not bot_variables.config.is_script_running)
        if handle_death():
            ConsoleLog(MODULE_NAME, "Player is dead while to farming Route 2. Reseting Environment.", Py4GW.Console.MessageType.Error, log=log_to_console)
            bot_variables.config.reset_from_jaga_moraine = False
            continue
        
        ConsoleLog(MODULE_NAME, "Waiting for right aggro ball", Py4GW.Console.MessageType.Info, log=log_to_console)
        bot_variables.config.pause_stuck_routine = True
        yield from Routines.Yield.wait(15000)
        ConsoleLog(MODULE_NAME,"Finished waiting for right aggro ball", Py4GW.Console.MessageType.Info, log=log_to_console)
        bot_variables.config.pause_stuck_routine = False
        
        yield from Routines.Yield.Movement.FollowPath(path_points_to_killing_spot,custom_exit_condition=lambda: player_is_dead() or not bot_variables.config.is_script_running)
        if handle_death():
            ConsoleLog(MODULE_NAME, "Player is dead while to killing spot. Reseting Environment.", Py4GW.Console.MessageType.Error, log=log_to_console)
            bot_variables.config.reset_from_jaga_moraine = False
            continue
            
        ConsoleLog(MODULE_NAME, "Killing enemies", Py4GW.Console.MessageType.Info, log=log_to_console)
        bot_variables.config.in_killing_routine = True
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
        while len(enemy_array) > 0: #sometimes not all enemies are killed
            if handle_death():
                ConsoleLog(MODULE_NAME, "Player is dead while killing enemies. Reseting Environment.", Py4GW.Console.MessageType.Error, log=log_to_console)
                bot_variables.config.reset_from_jaga_moraine = False
                continue
            yield from Routines.Yield.wait(1000)
            enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
        
        bot_variables.config.in_killing_routine = False
        bot_variables.config.finished_routine = True
                
        filtered_agent_ids = LootConfig().GetfilteredLootArray(Range.Earshot.value)
        
        if handle_death():
            ConsoleLog(MODULE_NAME, "Player is dead before looting. Reseting Environment.", Py4GW.Console.MessageType.Error, log=log_to_console)
            bot_variables.config.reset_from_jaga_moraine = False
            continue
        
        yield from Routines.Yield.wait(500)
        yield from Routines.Yield.Items.LootItems(filtered_agent_ids, log_to_console)
        if handle_death():
            ConsoleLog(MODULE_NAME, "Player is dead while looting. Reseting Environment.", Py4GW.Console.MessageType.Error, log=log_to_console)
            bot_variables.config.reset_from_jaga_moraine = False
            continue
            
        ConsoleLog(MODULE_NAME, "ID Items", Py4GW.Console.MessageType.Info, log=log_to_console)
        items_to_idenfity = filter_identify_array()
        yield from Routines.Yield.Items.IdentifyItems(items_to_idenfity, log_to_console)
        
        ConsoleLog(MODULE_NAME, "Salvaging Items", Py4GW.Console.MessageType.Info, log=log_to_console)
        items_to_salvage = filter_salvage_array()
        yield from Routines.Yield.Items.SalvageItems(items_to_salvage, log_to_console)
        
        if handle_return_inventory_check():
            ConsoleLog(MODULE_NAME, "Inventory handling needed, Reseting Environment.", Py4GW.Console.MessageType.Info, log=log_to_console)
            bot_variables.config.reset_from_jaga_moraine = False
            continue
        
        if handle_death():
            ConsoleLog(MODULE_NAME, "Player is dead while looting. Reseting Environment.", Py4GW.Console.MessageType.Error, log=log_to_console)
            bot_variables.config.reset_from_jaga_moraine = False
            continue
        
        ConsoleLog(MODULE_NAME, "Exiting to Bjora Marches", Py4GW.Console.MessageType.Info, log=log_to_console)
        yield from Routines.Yield.Movement.FollowPath(path_points_to_exit_jaga_moraine, custom_exit_condition=lambda: player_is_dead_or_map_loading(bjora_marches) or not bot_variables.config.is_script_running)
        yield from Routines.Yield.Map.WaitforMapLoad(bjora_marches, log_to_console)
        bot_variables.config.finished_routine = False
        
        yield from Routines.Yield.Movement.FollowPath(path_points_to_return_to_jaga_moraine, custom_exit_condition=lambda: player_is_dead_or_map_loading(jaga_moraine) or not bot_variables.config.is_script_running)
        yield from Routines.Yield.Map.WaitforMapLoad(jaga_moraine, log_to_console)          


        bot_variables.config.reset_from_jaga_moraine = True
        bot_variables.config.pause_stuck_routine = True
        #bot_variables.is_script_running = False
        ConsoleLog(MODULE_NAME, "Script finished.", Py4GW.Console.MessageType.Info, log=log_to_console)
        yield from Routines.Yield.wait(100)
#endregion

#region SkillCasting
def BjoraMarchesSkillCasting():
    global bot_variables

    #we only need to cast skills in bjora marches if we are in danger
    if not Routines.Checks.Agents.InDanger(Range.Spellcast):
        yield from Routines.Yield.wait(100)
        return

    player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
    deadly_paradox = bot_variables.skillbar.deadly_paradox
    shadow_form = bot_variables.skillbar.shadow_form
    shroud_of_distress = bot_variables.skillbar.shroud_of_distress
    heart_of_shadow = bot_variables.skillbar.heart_of_shadow

    log_to_console = False #bot_variables.config.log_to_console
    

    #we need to cast deadly paradox and shadow form and mantain it
    has_shadow_form = Routines.Checks.Effects.HasBuff(player_agent_id,shadow_form)
    shadow_form_buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id,shadow_form) if has_shadow_form else 0

    has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id,deadly_paradox)
    if shadow_form_buff_time_remaining <= 3500: #about to expire, recast
        #** Cast Deadly Paradox **
        if Routines.Yield.Skills.CastSkillID(deadly_paradox,extra_condition=(not has_deadly_paradox), log=log_to_console, aftercast_delay=100):           
            yield from Routines.Yield.wait(100)   
        # ** Cast Shadow Form **
        if Routines.Yield.Skills.CastSkillID(shadow_form, log=log_to_console, aftercast_delay=1250):
            yield from Routines.Yield.wait(1250)
        return 
        
    #if were hurt, we need to cast shroud of distress 
    if GLOBAL_CACHE.Agent.GetHealth(player_agent_id) < 0.45:
        # ** Cast Shroud of Distress **
        if Routines.Yield.Skills.CastSkillID(shroud_of_distress, log=log_to_console, aftercast_delay=1250):
            yield from Routines.Yield.wait(1250)
            return

    #if we have an enemy behind us, we can escape with Heart of Shadow
    nearest_enemy = Routines.Agents.GetNearestEnemy(Range.Earshot.value)
    if nearest_enemy:
        # ** Cast Heart of Shadow **
        is_enemy_behind = Routines.Checks.Agents.IsEnemyBehind(player_agent_id)
        if Routines.Yield.Skills.CastSkillID(heart_of_shadow, extra_condition=is_enemy_behind, log=log_to_console, aftercast_delay=350):
            yield from Routines.Yield.wait(350)
            return     
    yield
            

def JagaMoraineSkillCasting():
    player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
    deadly_paradox = bot_variables.skillbar.deadly_paradox
    shadow_form = bot_variables.skillbar.shadow_form
    shroud_of_distress = bot_variables.skillbar.shroud_of_distress
    way_of_perfection = bot_variables.skillbar.way_of_perfection
    heart_of_shadow = bot_variables.skillbar.heart_of_shadow
    wastrels_demise = bot_variables.skillbar.wastrels_demise
    arcane_echo = bot_variables.skillbar.arcane_echo
    channeling = bot_variables.skillbar.channeling
    
    log_to_console = False #bot_variables.config.log_to_console
    
    if not bot_variables.config.reset_from_jaga_moraine:
        yield from Routines.Yield.wait(1000)
        return
    
    if Routines.Checks.Agents.InDanger(Range.Spellcast):
        ConsoleLog(MODULE_NAME, "In danger, casting skills.", Py4GW.Console.MessageType.Info, log=log_to_console)
        #we need to cast deadly paradox and shadow form and mantain it
        has_shadow_form = Routines.Checks.Effects.HasBuff(player_agent_id,shadow_form)
        shadow_form_buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id,shadow_form) if has_shadow_form else 0

        has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id,deadly_paradox)
        if shadow_form_buff_time_remaining <= 3500: #about to expire, recast
            #** Cast Deadly Paradox **
            if Routines.Yield.Skills.CastSkillID(deadly_paradox,extra_condition=(not has_deadly_paradox), log=log_to_console, aftercast_delay=100):
                ConsoleLog(MODULE_NAME, "Casting Deadly Paradox.", Py4GW.Console.MessageType.Info, log=log_to_console)
                yield from Routines.Yield.wait(100)
            
            # ** Cast Shadow Form **
            if Routines.Yield.Skills.CastSkillID(shadow_form, log=log_to_console, aftercast_delay=1250):
                ConsoleLog(MODULE_NAME, "Casting Shadow Form.", Py4GW.Console.MessageType.Info, log=log_to_console)
                yield from Routines.Yield.wait(1250)
            return
                
    #if were hurt, we need to cast shroud of distress 
    if GLOBAL_CACHE.Agent.GetHealth(player_agent_id) < 0.45:
        ConsoleLog(MODULE_NAME, "Casting Shroud of Distress.", Py4GW.Console.MessageType.Info, log=log_to_console)
        # ** Cast Shroud of Distress **
        if Routines.Yield.Skills.CastSkillID(shroud_of_distress, log =log_to_console, aftercast_delay=1250):
            yield from Routines.Yield.wait(1250)
            return
         
    #need to keep Channeling up
    has_channeling = Routines.Checks.Effects.HasBuff(player_agent_id,bot_variables.skillbar.channeling)
    if not has_channeling:
        ConsoleLog(MODULE_NAME, "Casting Channeling.", Py4GW.Console.MessageType.Info, log=log_to_console)
        # ** Cast Channeling **
        if Routines.Yield.Skills.CastSkillID(channeling, log =log_to_console, aftercast_delay=1250):
            yield from Routines.Yield.wait(1250)
            return
            
    #Keep way of perfection up on recharge
    # ** Cast Way of Perfection **
    if Routines.Yield.Skills.CastSkillID(way_of_perfection, log=log_to_console, aftercast_delay=350):
        ConsoleLog(MODULE_NAME, "Casting Way of Perfection.", Py4GW.Console.MessageType.Info, log=log_to_console)
        yield from Routines.Yield.wait(350)
        return
        
    # ** Heart of Shadow to Stay Alive or to get out of stuck**
    if not bot_variables.config.in_killing_routine:
        if GLOBAL_CACHE.Agent.GetHealth(player_agent_id) < 0.35 or bot_variables.config.stuck_count > 0:
            if bot_variables.config.pause_stuck_routine:
                yield from Routines.Yield.Agents.ChangeTarget(player_agent_id)
            else:
                yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Earshot.value)

            if Routines.Yield.Skills.CastSkillID(heart_of_shadow, log=log_to_console, aftercast_delay=350):
                yield from Routines.Yield.wait(350)
                return
                
    # ** Killing Routine **
    if bot_variables.config.in_killing_routine:
        arcane_echo_slot = 7
        wastrels_demise_slot = 6
        both_ready = Routines.Checks.Skills.IsSkillSlotReady(wastrels_demise_slot) and Routines.Checks.Skills.IsSkillSlotReady(arcane_echo_slot)
        target = GetNotHexedEnemy()  
        if target:
            Routines.Yield.Agents.ChangeTarget(target)
            if Routines.Yield.Skills.CastSkillSlot(arcane_echo_slot, extra_condition=both_ready, log=log_to_console, aftercast_delay=2000):
                ConsoleLog(MODULE_NAME, "Casting Arcane Echo.", Py4GW.Console.MessageType.Info, log=log_to_console)
                yield from Routines.Yield.wait(2000)
            else:
                if Routines.Yield.Skills.CastSkillSlot(arcane_echo_slot, log=log_to_console, aftercast_delay=350):
                    ConsoleLog(MODULE_NAME, "Casting Echoed Wastrel.", Py4GW.Console.MessageType.Info, log=log_to_console)
                    yield from Routines.Yield.wait(350)
                    return
        target = GetNotHexedEnemy()  
        if target: 
            Routines.Yield.Agents.ChangeTarget(target)
            if Routines.Yield.Skills.CastSkillSlot(wastrels_demise_slot, log=log_to_console, aftercast_delay=350):
                yield from Routines.Yield.wait(350)
                return
    yield

#endregion

def SkillHandler():
    """function that manages skills and timings."""
    global bot_variables

    while True:
        longeyes_ledge = GLOBAL_CACHE.Map.GetMapIDByName("Longeyes Ledge")
        bjora_marches = GLOBAL_CACHE.Map.GetMapIDByName("Bjora Marches")
        jaga_moraine = GLOBAL_CACHE.Map.GetMapIDByName("Jaga Moraine")
        
        
        if not Routines.Checks.Map.MapValid():
            yield from Routines.Yield.wait(1000)
            continue
        
        if not GLOBAL_CACHE.Map.IsExplorable():
            yield from Routines.Yield.wait(1000)
            continue
        
        #if we are occupied with something else, skip this iteration
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            continue
        
        if bot_variables.config.finished_routine:
            yield from Routines.Yield.wait(1000)  
            continue
        
        if GLOBAL_CACHE.Map.GetMapID() == bjora_marches:
            yield from BjoraMarchesSkillCasting()
        elif GLOBAL_CACHE.Map.GetMapID() == jaga_moraine:  
            yield from JagaMoraineSkillCasting()
        
        yield

        
#region ImGui

def DrawWindow():
    global bot_variables

    try:
        # First run: set window size and position
        if bot_variables.config.window_module.first_run:
            PyImGui.set_next_window_size(*bot_variables.config.window_module.window_size)     
            PyImGui.set_next_window_pos(*bot_variables.config.window_module.window_pos)
            bot_variables.config.window_module.first_run = False

        if PyImGui.begin(bot_variables.config.window_module.window_name, bot_variables.config.window_module.window_flags):
            PyImGui.text_colored("Apo's YAVB 1.0", Color(255,255,0,255).to_tuple())
            PyImGui.text_colored("Yet Another Vaettir Bot", Color(255,255,0,255).to_tuple())
            PyImGui.separator()
            
            PyImGui.text_colored("Status:IDLE", Color(255,0,0,255).to_tuple())
            

            # Control Table
            if PyImGui.begin_table("ControlTable", 2):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Control")
                PyImGui.table_next_column()

                # Start/Stop Button
                button_text = "Start script" if not bot_variables.config.is_script_running else "Stop script"
                if PyImGui.button(button_text):
                    bot_variables.config.is_script_running = not bot_variables.config.is_script_running
                    if bot_variables.config.is_script_running:
                        GLOBAL_CACHE.Coroutines.clear()
                        GLOBAL_CACHE.Coroutines.append(RunBotSequentialLogic())
                        GLOBAL_CACHE.Coroutines.append(SkillHandler())
                    else:
                        reset_environment()


                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.end_table()
                
            # --- Config Section ---
            if PyImGui.collapsing_header("Config"):
                bot_variables.config.log_to_console = PyImGui.checkbox("Log to Console", bot_variables.config.log_to_console)

                # Salvage Section
                if PyImGui.tree_node("Salvage"):
                    if PyImGui.tree_node("White Salvaging"):
                        setattr(bot_variables.salvage_config, "salvage_whites",
                                PyImGui.checkbox("Items", bot_variables.salvage_config.salvage_whites))
                        setattr(bot_variables.salvage_config, "salvage_glacial_stones",
                                PyImGui.checkbox("Glacial Stones", bot_variables.salvage_config.salvage_glacial_stones))
                        PyImGui.tree_pop()

                    for label, attr in [
                        ("Salvage Blues", "salvage_blues"),
                        ("Salvage Purples", "salvage_purples"),
                        ("Salvage Golds", "salvage_golds")
                    ]:
                        setattr(bot_variables.salvage_config, attr,
                                PyImGui.checkbox(label, getattr(bot_variables.salvage_config, attr)))

                    PyImGui.tree_pop()

                # Sell Section
                if PyImGui.tree_node("Sell"):
                    for label, attr in [
                        ("Materials", "sell_materials"),
                        ("Granite", "sell_granite"),
                        ("Wood", "sell_wood"),
                        ("Iron", "sell_iron"),
                        ("Dust", "sell_dust"),
                        ("Cloth", "sell_cloth"),
                        ("Bones", "sell_bones")
                    ]:
                        setattr(bot_variables.sell_config, attr,
                                PyImGui.checkbox(label, getattr(bot_variables.sell_config, attr)))
                    PyImGui.tree_pop()

                # Misc Section
                if PyImGui.tree_node("Misc"):
                    for label, attr in [
                        ("Keep ID Kits", "keep_id_kit"),
                        ("Keep Salvage Kits", "keep_salvage_kit"),
                        ("Keep Gold", "keep_gold_amount"),
                        ("Leave Empty Inventory Slots", "leave_free_slots")
                    ]:
                        setattr(bot_variables.inventory_config, attr,
                                PyImGui.input_int(label, getattr(bot_variables.inventory_config, attr)))
                    PyImGui.tree_pop()

            # --- Debug Section ---
            if PyImGui.collapsing_header("Debug"):
                identify_array = filter_identify_array()
                salvage_array = filter_salvage_array()
                deposit_array = filter_items_to_deposit()
                loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value)

                PyImGui.text(f"Identify Array: {len(identify_array)}")
                PyImGui.text(f"Salvage Array: {len(salvage_array)}")
                PyImGui.text(f"Deposit Array: {len(deposit_array)}")
                PyImGui.text(f"Loot Array: {len(loot_array)}")
                
                PyImGui.text(f"Agent ID: ")
                PyImGui.same_line(0,-1)
                for agent_id in loot_array:
                    PyImGui.text(f",{agent_id}")
                    PyImGui.same_line(0,-1)
                

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

#endregion


def main():
    global bot_variables
    try:   
        if bot_variables.config.is_script_running:
            Handle_Stuck()

        DrawWindow()
        
        if GLOBAL_CACHE.Map.IsMapLoading():
            GLOBAL_CACHE._ActionQueueManager.ResetAllQueues()
            bot_variables.config.auto_stuck_command_timer.Reset()
            bot_variables.config.stuck_count = 0
            return
            
        if not Routines.Checks.Skills.InCastingProcess() and not GLOBAL_CACHE.Agent.IsKnockedDown(GLOBAL_CACHE.Player.GetAgentID()):  
            if bot_variables.config.is_script_running:
                for coro in GLOBAL_CACHE.Coroutines[:]:
                    try:
                        next(coro)
                    except StopIteration:
                        GLOBAL_CACHE.Coroutines.remove(coro)
                        

    except Exception as e:
        ConsoleLog(MODULE_NAME,f"Error: {str(e)}",Py4GW.Console.MessageType.Error,log=True)

if __name__ == "__main__":
    main()
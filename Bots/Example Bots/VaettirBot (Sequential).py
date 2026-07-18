from Py4GWCoreLib import *
import time
from time import sleep

MODULE_NAME = "VaettirBot 3.0"
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

"""(13070, -16911), (12938, -17081), (12790, -17201), (12747, -17220),
    (12703, -17239), (12684, -17184), (12526, -17275),"""

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

# Instantiate MultiThreading manager
thread_manager = MultiThreading(5, log_actions=True)

#region helpers

def IsSkillBarLoaded():
    global bot_variables
    global skillbar

    primary_profession, secondary_profession = Agent.GetProfessionNames(Player.GetAgentID())
    if ((primary_profession == "Assassin" and secondary_profession != "Mesmer") or 
        (primary_profession == "Dervish" and secondary_profession != "Assassin")):
        frame = inspect.currentframe()
        current_function = frame.f_code.co_name if frame else "Unknown"
        ConsoleLog(MODULE_NAME, f"{current_function} - This bot requires A/Me to work, halting.", Py4GW.Console.MessageType.Error, log=True)
        return False

    bot_variables.skillbar.deadly_paradox = Skill.GetID("Deadly_Paradox")
    bot_variables.skillbar.shadow_form = Skill.GetID("Shadow_Form")
    bot_variables.skillbar.shroud_of_distress = Skill.GetID("Shroud_of_Distress")
    bot_variables.skillbar.way_of_perfection = Skill.GetID("Way_of_Perfection")
    bot_variables.skillbar.heart_of_shadow = Skill.GetID("Heart_of_Shadow")
    bot_variables.skillbar.wastrels_demise = Skill.GetID("Wastrel's_Demise")
    bot_variables.skillbar.arcane_echo = Skill.GetID("Arcane_Echo")
    bot_variables.skillbar.channeling = Skill.GetID("Channeling")
    #added for allowing more classes
    bot_variables.skillbar.zealous_renewal = Skill.GetID("Zealous_Renewal")
    bot_variables.skillbar.heart_of_holy_flame = Skill.GetID("Heart_of_Holy_Flame")
    bot_variables.skillbar.pious_fury = Skill.GetID("Pious_Fury")
    
    ConsoleLog(MODULE_NAME, f"SkillBar Loaded.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)       
    return True

def SetHardMode():
    global bot_variables
    ActionQueueManager().AddAction("ACTION",Party.SetHardMode)
    ConsoleLog(MODULE_NAME, "Hard mode set.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
    
def reset_environment():
    global bot_variables
    bot_variables.config.is_script_running = False
    bot_variables.config.reset_from_jaga_moraine = False
    bot_variables.config.in_killing_routine = False
    bot_variables.config.stuck_count = 0
    ActionQueueManager().ResetAllQueues()
    
    thread_manager.stop_all_threads()
    thread_manager.add_thread(MAIN_THREAD_NAME, RunBotSequentialLogic)
    thread_manager.add_thread("SkillHandler", SkillHandler)
    thread_manager.start_watchdog(MAIN_THREAD_NAME)
    

def NeedsToHandleInventory():
    global bot_variables
    free_slots_in_inventory = Inventory.GetFreeSlotCount()
    count_of_id_kits = Inventory.GetModelCount(5899) #5899 model for ID kit
    count_of_salvage_kits = Inventory.GetModelCount(2992) #2992 model for salvage kit
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
    count_of_id_kits = Inventory.GetModelCount(5899) #5899 model for ID kit
    id_kits_to_buy = bot_variables.inventory_config.keep_id_kit - count_of_id_kits
    return id_kits_to_buy

def GetSalvageKitsToBuy():
    global bot_variables
    count_of_salvage_kits = Inventory.GetModelCount(2992) #2992 model for salvage kit
    salvage_kits_to_buy = bot_variables.inventory_config.keep_salvage_kit - count_of_salvage_kits
    return salvage_kits_to_buy

def IsMaterial(item_id):
    material_model_ids = {946, 948, 929, 921, 925, 955}  # Add all known material IDs
    return Item.GetModelID(item_id) in material_model_ids
	
def IsGranite(item_id):
    """Check if the item is granite."""
    granite_model_ids = {955}  # Granite ID
    return Item.GetModelID(item_id) in granite_model_ids
	
def IsWood(item_id):
    """Check if the item is wood."""
    wood_model_ids = {946}  # Replace with the correct IDs for wood
    return Item.GetModelID(item_id) in wood_model_ids

def IsIron(item_id):
    """Check if the item is iron."""
    iron_model_ids = {948}  # Replace with the correct IDs for iron
    return Item.GetModelID(item_id) in iron_model_ids

def IsDust(item_id):
    """Check if the item is glittering dust."""
    dust_model_ids = {929}  # Replace with the correct IDs for dust
    return Item.GetModelID(item_id) in dust_model_ids

def IsBones(item_id):
    """Check if the item is bones."""
    bone_model_ids = {921}  # Replace with the correct IDs for bones
    return Item.GetModelID(item_id) in bone_model_ids

def IsCloth(item_id):
    """Check if the item is cloth."""
    cloth_model_ids = {925}  # Replace with the correct IDs for cloth
    return Item.GetModelID(item_id) in cloth_model_ids


def get_filtered_materials_to_sell():
    global bot_variables
    # Get items from the specified bags
    bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    items_to_sell = ItemArray.GetItemArray(bags_to_check)

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
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    unidentified_items = ItemArray.GetItemArray(bags_to_check)
    unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsWhite(item_id))
    unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Usage.IsIdentified(item_id))

    """
    if not bot_variables.id_config.id_blues:
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsBlue(item_id))
    if not bot_variables.id_config.id_purples:
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsPurple(item_id))
    if not bot_variables.id_config.id_golds:
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsGold(item_id))  
    """   
         
    return unidentified_items

def filter_salvage_array():
    global bot_variables
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    salvageable_items = ItemArray.GetItemArray(bags_to_check)

    salvageable_items = ItemArray.Filter.ByCondition(salvageable_items,lambda item_id: Item.Usage.IsIdentified(item_id) or Item.Rarity.IsWhite(item_id))

    salvageable_items = ItemArray.Filter.ByCondition(salvageable_items,lambda item_id: Item.Usage.IsSalvageable(item_id))

    """
    if not bot_variables.salvage_config.salvage_blues:
        salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: not Item.Rarity.IsBlue(item_id))
  
    if not bot_variables.salvage_config.salvage_purples:
        salvageable_items = ItemArray.Filter.ByCondition(salvageable_items,lambda item_id: not Item.Rarity.IsPurple(item_id))

    if not bot_variables.salvage_config.salvage_golds:
        salvageable_items = ItemArray.Filter.ByCondition(salvageable_items,lambda item_id: not Item.Rarity.IsGold(item_id))
    """

    return salvageable_items
    

def print_filter_salvage_array():
    global bot_variables
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    salvageable_items = ItemArray.GetItemArray(bags_to_check)
    print(f"Initial items: {[ (item_id, Item.Rarity.GetRarity(item_id)[1]) for item_id in salvageable_items ]}")

    salvageable_items = ItemArray.Filter.ByCondition(
        salvageable_items,
        lambda item_id: Item.Usage.IsIdentified(item_id) or Item.Rarity.IsWhite(item_id)
    )
    print(f"After identified/white filter: {[ (item_id, Item.Rarity.GetRarity(item_id)[1]) for item_id in salvageable_items ]}")

    salvageable_items = ItemArray.Filter.ByCondition(
        salvageable_items,
        lambda item_id: Item.Usage.IsSalvageable(item_id)
    )
    print(f"After salvageable filter: {[ (item_id, Item.Rarity.GetRarity(item_id)[1]) for item_id in salvageable_items ]}")

    if not bot_variables.salvage_config.salvage_blues:
        print("Filtering out blues")
        salvageable_items = ItemArray.Filter.ByCondition(
            salvageable_items,
            lambda item_id: not Item.Rarity.IsBlue(item_id)
        )
        print(f"After blue filter: {[ (item_id, Item.Rarity.GetRarity(item_id)[1]) for item_id in salvageable_items ]}")

    if not bot_variables.salvage_config.salvage_purples:
        print("Filtering out purples")
        salvageable_items = ItemArray.Filter.ByCondition(
            salvageable_items,
            lambda item_id: not Item.Rarity.IsPurple(item_id)
        )
        print(f"After purple filter: {[ (item_id, Item.Rarity.GetRarity(item_id)[1]) for item_id in salvageable_items ]}")

    if not bot_variables.salvage_config.salvage_golds:
        print("Filtering out golds")
        salvageable_items = ItemArray.Filter.ByCondition(
            salvageable_items,
            lambda item_id: not Item.Rarity.IsGold(item_id)
        )
        print(f"After gold filter: {[ (item_id, Item.Rarity.GetRarity(item_id)[1]) for item_id in salvageable_items ]}")

    return salvageable_items

        
def filter_items_to_deposit():
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    items_to_deposit = ItemArray.GetItemArray(bags_to_check)
    banned_models = {2992,5899}
    items_to_deposit = ItemArray.Filter.ByCondition(items_to_deposit, lambda item_id: Item.GetModelID(item_id) not in banned_models)
    return items_to_deposit

def player_is_dead_or_map_loading():
    if Map.IsMapLoading():
        return True
    return Agent.IsDead(Player.GetAgentID())

    
def player_is_dead():
    return Agent.IsDead(Player.GetAgentID())

def handle_death():
    if Agent.IsDead(Player.GetAgentID()):
        ConsoleLog(MODULE_NAME, f"Player is dead while traversing {Map.GetMapName(Map.GetMapID())} . Reseting Environment.", Py4GW.Console.MessageType.Error, log=bot_variables.config.log_to_console)
        return True
    return False

def handle_inventory_check():
    global bot_variables
    if Inventory.GetFreeSlotCount() < bot_variables.inventory_config.leave_free_slots:
        ConsoleLog(MODULE_NAME, f"Inventory is full, going to merchant.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
        return True
    
    if GetIDKitsToBuy() >= bot_variables.inventory_config.keep_id_kit:
        ConsoleLog(MODULE_NAME, f"Need to buy ID kits, going to merchant.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
        return True
    
    if GetSalvageKitsToBuy() >= bot_variables.inventory_config.keep_salvage_kit:
        ConsoleLog(MODULE_NAME, f"Need to buy Salvage kits, going to merchant.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
        return True
    
    return False
    
def handle_return_inventory_check():
    global bot_variables
    if Inventory.GetFreeSlotCount() < bot_variables.inventory_config.leave_free_slots:
        ConsoleLog(MODULE_NAME, f"Inventory is full, going to merchant.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
        return True
    
    count_of_id_kits = Inventory.GetModelCount(5899) #5899 model for ID kit
    if count_of_id_kits <=0:
        ConsoleLog(MODULE_NAME, f"Need to buy ID kits, going to merchant.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
        return True
    
    count_of_salvage_kits = Inventory.GetModelCount(2992) #2992 model for salvage kit
    if count_of_salvage_kits <=0:
        ConsoleLog(MODULE_NAME, f"Need to buy Salvage kits, going to merchant.", Py4GW.Console.MessageType.Info, log=bot_variables.config.log_to_console)
        return True
    
    return False

def GetNotHexedEnemy():
    player_pos = Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id:not Agent.IsHexed(agent_id))
    if len(enemy_array) == 0:
        return 0
    
    return enemy_array[0]

def IsValidItem(item_id):
    item_agent = Agent.GetItemAgentByID(item_id)
    if item_agent is None:
        return False
    
    owner = item_agent.owner
    return owner == Player.GetAgentID() or owner == 0

def get_filtered_loot_array():
    global bot_variables
    
    loot_config = LootConfig()
    
    loot_config.SetProperties(
        loot_whites=bot_variables.loot_config.loot_whites,
        loot_blues=bot_variables.loot_config.loot_blues,
        loot_purples=bot_variables.loot_config.loot_purples,
        loot_golds=bot_variables.loot_config.loot_golds,
        loot_greens=True,
    )
    
    loot_preferences = {
        "loot_event_items": {28435, 28436},
        "loot_map_pieces": {24629, 24630, 24631, 24632},
        "loot_glacial_stones": {27047},
        "loot_lockpicks": {22751},
        "loot_black_dyes": {10},
        "loot_white_dyes": {12},
        "loot_tomes": {21797},
        "loot_dyes": {146}
    }
    
    for loot_var, model_ids in loot_preferences.items():
        loot_enabled = getattr(bot_variables.loot_config, loot_var, True)  # Default to True if attribute missing
        if loot_enabled:
            for model_id in model_ids:
                loot_config.AddToWhitelist(model_id)
        else:
            for model_id in model_ids:
                loot_config.AddToBlacklist(model_id)
    
    filtered_agent_ids = loot_config.GetfilteredLootArray(distance=Range.Spellcast.value)

    return filtered_agent_ids


def get_escape_location(scaling_factor=50):
    from Py4GWCoreLib import VectorFields
    """
    Moves the player to a calculated escape location based on enemy repulsion.
    
    Args:
        scaling_factor (float): Factor to scale the escape vector magnitude. Default is 5.
    
    Returns:
        tuple: The escape destination (x, y).
    """
    # Get the player's current position
    player_x, player_y = Player.GetXY()
    
    # Initialize VectorFields with the player's position
    vector_fields = VectorFields(probe_position=(player_x, player_y))

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
        Routines.Sequential.Agents.InteractWithAgentByName("[Merchant]")
        
        if bot_variables.sell_config.sell_materials:
            items_to_sell = get_filtered_materials_to_sell()
            #sell materials to make space
            if log_to_console:
                ConsoleLog(MODULE_NAME, "Selling materials.", Py4GW.Console.MessageType.Info, log=log_to_console)
            Routines.Sequential.Merchant.SellItems(items_to_sell, log_to_console)
        if log_to_console:
            ConsoleLog(MODULE_NAME, "Buying ID and Salvage kits.", Py4GW.Console.MessageType.Info, log=log_to_console)
        Routines.Sequential.Merchant.BuyIDKits(GetIDKitsToBuy(),log_to_console)
        Routines.Sequential.Merchant.BuySalvageKits(GetSalvageKitsToBuy(),log_to_console)
        
        items_to_idenfity = filter_identify_array()
        if log_to_console:
            ConsoleLog(MODULE_NAME,f"IDing {len(items_to_idenfity)} items.", Py4GW.Console.MessageType.Info, log=log_to_console)
        Routines.Sequential.Items.IdentifyItems(items_to_idenfity, log_to_console)
        
        items_to_salvage = filter_salvage_array()
        if log_to_console:
            ConsoleLog(MODULE_NAME, f"Salvaging {items_to_salvage} items.", Py4GW.Console.MessageType.Info, log=log_to_console)
        Routines.Sequential.Items.SalvageItems(items_to_salvage, log_to_console)
        
        if log_to_console:
            ConsoleLog(MODULE_NAME, "Selling items.", Py4GW.Console.MessageType.Info, log=log_to_console)
        if bot_variables.sell_config.sell_materials:
            items_to_sell = get_filtered_materials_to_sell()
            Routines.Sequential.Merchant.SellItems(items_to_sell, log_to_console)
            
        if log_to_console:
            ConsoleLog(MODULE_NAME, "Depositing items.", Py4GW.Console.MessageType.Info, log=log_to_console)  
        items_to_deposit = filter_items_to_deposit()
        Routines.Sequential.Items.DepositItems(items_to_deposit,log_to_console)
        if log_to_console:
            ConsoleLog(MODULE_NAME, "Depositing gold.", Py4GW.Console.MessageType.Info, log=log_to_console)
        Routines.Sequential.Items.DepositGold(bot_variables.inventory_config.keep_gold_amount, log_to_console)
    
#endregion
  

#region stuck

def Handle_Stuck():
    """
    Detect and recover the player when stuck. Uses timers and movement logic.
    """
    global bot_variables
    
    longeyes_ledge = 650 #Longeyes Ledge
    bjora_marches = 482 #Bjora Marches
    jaga_moraine = 546 #Jaga Moraine

    if Map.IsMapLoading():
        bot_variables.config.auto_stuck_command_timer.Reset()
        bot_variables.config.stuck_count = 0
        return
    
    if Map.GetMapID() == longeyes_ledge:
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
        Player.SendChatCommand("stuck")
        bot_variables.config.auto_stuck_command_timer.Reset()

    # Handle severe stuck situations
    if bot_variables.config.stuck_count > 10:
        restart_due_to_stuck()

    # Detect and handle non-movement
    if not Agent.IsMoving(Player.GetAgentID()):
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
        Player.SendChatCommand("stuck")
        escape_location = get_escape_location()
        ActionQueueManager().AddAction("ACTION",Player.Move, escape_location[0], escape_location[1]) 
        bot_variables.config.stuck_count += 1
        log_stuck_attempt(escape_location)

def handle_player_movement():
    """Tracks player movement and resets relevant timers if moving."""
    global FSM_vars
    new_player_x, new_player_y = Player.GetXY()
    if bot_variables.config.old_player_x != new_player_x or bot_variables.config.old_player_y != new_player_y:
        bot_variables.config.non_movement_timer.Reset()
        bot_variables.config.old_player_x = new_player_x
        bot_variables.config.old_player_y = new_player_y
        bot_variables.config.stuck_count = 0

def log_stuck_attempt(escape_location):
    """Logs details of a recovery attempt."""
    global bot_vars
    player_x, player_y = Player.GetXY()
    distance = Utils.Distance((player_x, player_y), escape_location)
    ConsoleLog("StuckHandler", f"Player is stuck, attempting to recover to {escape_location} (distance: {distance:.2f})", Py4GW.Console.MessageType.Warning)

#endregion

#region Sequential coding
def RunBotSequentialLogic():
    """Thread function that manages counting based on ImGui button presses."""
    global MAIN_THREAD_NAME, bot_variables

    reset_from_jaga_moraine = False
    sleep(1)
    while True:
        if not bot_variables.config.is_script_running:
            sleep(1)
            continue

        #movement and follow objects
        log_to_console = bot_variables.config.log_to_console
        
        longeyes_ledge = 650 #Longeyes Ledge
        bjora_marches = 482 #Bjora Marches
        jaga_moraine = 546 #Jaga Moraine
        
        primary_profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
        
        if not reset_from_jaga_moraine:
            Routines.Sequential.Map.TravelToOutpost(longeyes_ledge, log_to_console)
            
            if primary_profession == "Assassin":
                Routines.Sequential.Skills.LoadSkillbar("OwVUI2h5lPP8Id2BkAiAvpLBTAA", log_to_console)
            elif primary_profession == "Dervish":
                Routines.Sequential.Skills.LoadSkillbar("Ogej8xpDLT8I6MHQEQIQjbjXihA", log_to_console)
            
            if not IsSkillBarLoaded():
                reset_environment()
                ConsoleLog(MODULE_NAME, "You need the following build: OwVUI2h5lPP8Id2BkAiAvpLBTAA", Py4GW.Console.MessageType.Error, log=True)
                break
            
            Routines.Sequential.Map.SetHardMode(log_to_console)
            Routines.Sequential.Player.SetTitle(TitleID.Norn.value, log_to_console)       
            #inventory management  
            InventoryHandler(log_to_console)
            #exit outpost
            Routines.Sequential.Movement.FollowPath(path_points= path_points_to_leave_outpost, custom_exit_condition=lambda: Map.IsMapLoading())
            Routines.Sequential.Map.WaitforMapLoad(bjora_marches,log_to_console)
            bot_variables.config.pause_stuck_routine = False
            #traverse bjora marches
            Routines.Sequential.Movement.FollowPath(path_points_to_traverse_bjora_marches, custom_exit_condition=lambda: player_is_dead_or_map_loading())
            bot_variables.config.pause_stuck_routine = True
            
            if not Map.IsMapLoading() and handle_death():
                reset_from_jaga_moraine = False
                continue

            Routines.Sequential.Map.WaitforMapLoad(jaga_moraine, log_to_console)
            reset_from_jaga_moraine = True  
            
        Routines.Sequential.Movement.FollowPath(path_points_to_npc, custom_exit_condition=lambda: player_is_dead_or_map_loading()) 
        #take bounty
        Routines.Sequential.Agents.InteractWithAgentXY(13367, -20771)
        Routines.Sequential.Player.SendDialog("0x84")
        bot_variables.config.pause_stuck_routine = False
        Routines.Sequential.Movement.FollowPath(path_points_to_farming_route1,custom_exit_condition=lambda: player_is_dead())
        if handle_death():
            reset_from_jaga_moraine = False
            continue
        
        #wait for aggro ball'
        ConsoleLog(MODULE_NAME, "Waiting for left aggro ball", Py4GW.Console.MessageType.Info, log=log_to_console)
        bot_variables.config.pause_stuck_routine = True
        sleep (15)
        bot_variables.config.pause_stuck_routine = False
        
        Routines.Sequential.Movement.FollowPath(path_points_to_farming_route2,custom_exit_condition=lambda: player_is_dead())
        if handle_death():
            reset_from_jaga_moraine = False
            continue
        
        ConsoleLog(MODULE_NAME, "Waiting for right aggro ball", Py4GW.Console.MessageType.Info, log=log_to_console)
        bot_variables.config.pause_stuck_routine = True
        sleep (15)
        bot_variables.config.pause_stuck_routine = False
        
        Routines.Sequential.Movement.FollowPath(path_points_to_killing_spot,custom_exit_condition=lambda: player_is_dead())
        if handle_death():
            reset_from_jaga_moraine = False
            continue
            
        bot_variables.config.in_killing_routine = True
        player_pos = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
        while len(enemy_array) > 0: #sometimes not all enemies are killed
            if handle_death():
                reset_from_jaga_moraine = False
                continue
            sleep(1)
            enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
        
        bot_variables.config.in_killing_routine = False
        bot_variables.config.finished_routine = True
                
        filtered_agent_ids = get_filtered_loot_array()
        
        if handle_death():
            reset_from_jaga_moraine = False
            continue
        
        Routines.Sequential.Items.LootItems(filtered_agent_ids, log_to_console)
        if handle_death():
            reset_from_jaga_moraine = False
            continue
            
        items_to_idenfity = filter_identify_array()
        Routines.Sequential.Items.IdentifyItems(items_to_idenfity, log_to_console)
        
        items_to_salvage = filter_salvage_array()
        Routines.Sequential.Items.SalvageItems(items_to_salvage, log_to_console)
        
        if handle_return_inventory_check():
            reset_from_jaga_moraine = False
            continue
        
        if handle_death():
            reset_from_jaga_moraine = False
            continue
        
        Routines.Sequential.Movement.FollowPath(path_points_to_exit_jaga_moraine, custom_exit_condition=lambda: player_is_dead_or_map_loading())
        Routines.Sequential.Map.WaitforMapLoad(bjora_marches, log_to_console)
        bot_variables.config.finished_routine = False
        
        Routines.Sequential.Movement.FollowPath(path_points_to_return_to_jaga_moraine, custom_exit_condition=lambda: player_is_dead_or_map_loading())
        Routines.Sequential.Map.WaitforMapLoad(jaga_moraine, log_to_console)

        reset_from_jaga_moraine = True
        bot_variables.config.pause_stuck_routine = True
        #bot_variables.is_script_running = False
        ConsoleLog(MODULE_NAME, "Script finished.", Py4GW.Console.MessageType.Info, log=log_to_console)
        time.sleep(0.1)
#endregion

#region SkillCasting
def BjoraMarchesSkillCasting():
    global bot_variables
    #we only need to cast skills in bjora marches if we are in danger
    if not Routines.Checks.Agents.InDanger(Range.Spellcast):
        sleep(0.1)
        return
    
    player_agent_id = Player.GetAgentID()
    deadly_paradox = bot_variables.skillbar.deadly_paradox
    shadow_form = bot_variables.skillbar.shadow_form
    shroud_of_distress = bot_variables.skillbar.shroud_of_distress
    heart_of_shadow = bot_variables.skillbar.heart_of_shadow

    log_to_console = False #bot_variables.config.log_to_console
    

    #we need to cast deadly paradox and shadow form and mantain it
    has_shadow_form = Routines.Checks.Effects.HasBuff(player_agent_id,shadow_form)
    shadow_form_buff_time_remaining = Effects.GetEffectTimeRemaining(player_agent_id,shadow_form) if has_shadow_form else 0

    has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id,deadly_paradox)
    if shadow_form_buff_time_remaining <= 3500: #about to expire, recast
        #** Cast Deadly Paradox **
        if Routines.Sequential.Skills.CastSkillID(deadly_paradox,extra_condition=(not has_deadly_paradox), log=log_to_console):             
            sleep(0.1)   
        # ** Cast Shadow Form **
        if Routines.Sequential.Skills.CastSkillID(shadow_form, log=log_to_console):
            sleep(1.25)
        return 
        
    #if were hurt, we need to cast shroud of distress 
    if Agent.GetHealth(player_agent_id) < 0.45:
        # ** Cast Shroud of Distress **
        if Routines.Sequential.Skills.CastSkillID(shroud_of_distress, log=log_to_console):
            sleep(1.25)
            return

    #if we have an enemy behind us, we can escape with Heart of Shadow
    nearest_enemy = Routines.Agents.GetNearestEnemy(Range.Earshot.value)
    if nearest_enemy:
        # ** Cast Heart of Shadow **
        is_enemy_behind = Routines.Checks.Agents.IsEnemyBehind(player_agent_id)
        if Routines.Sequential.Skills.CastSkillID(heart_of_shadow, extra_condition=is_enemy_behind, log=log_to_console):
            sleep(0.350)
            return
            

def JagaMoraineSkillCasting():
    player_agent_id = Player.GetAgentID()
    deadly_paradox = bot_variables.skillbar.deadly_paradox
    shadow_form = bot_variables.skillbar.shadow_form
    shroud_of_distress = bot_variables.skillbar.shroud_of_distress
    way_of_perfection = bot_variables.skillbar.way_of_perfection
    heart_of_shadow = bot_variables.skillbar.heart_of_shadow
    wastrels_demise = bot_variables.skillbar.wastrels_demise
    arcane_echo = bot_variables.skillbar.arcane_echo
    channeling = bot_variables.skillbar.channeling
    
    log_to_console = False #bot_variables.config.log_to_console
    
    if Routines.Checks.Agents.InDanger(Range.Spellcast):
        ConsoleLog(MODULE_NAME, "In danger, casting skills.", Py4GW.Console.MessageType.Info, log=log_to_console)
        #we need to cast deadly paradox and shadow form and mantain it
        has_shadow_form = Routines.Checks.Effects.HasBuff(player_agent_id,shadow_form)
        shadow_form_buff_time_remaining = Effects.GetEffectTimeRemaining(player_agent_id,shadow_form) if has_shadow_form else 0

        has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id,deadly_paradox)
        if shadow_form_buff_time_remaining <= 3500: #about to expire, recast
            #** Cast Deadly Paradox **
            if Routines.Sequential.Skills.CastSkillID(deadly_paradox,extra_condition=(not has_deadly_paradox), log=log_to_console):
                ConsoleLog(MODULE_NAME, "Casting Deadly Paradox.", Py4GW.Console.MessageType.Info, log=log_to_console)
                sleep(0.1)
            
            # ** Cast Shadow Form **
            if Routines.Sequential.Skills.CastSkillID(shadow_form, log=log_to_console):
                ConsoleLog(MODULE_NAME, "Casting Shadow Form.", Py4GW.Console.MessageType.Info, log=log_to_console)
                sleep(1.25)
            return
                
    #if were hurt, we need to cast shroud of distress 
    if Agent.GetHealth(player_agent_id) < 0.45:
        ConsoleLog(MODULE_NAME, "Casting Shroud of Distress.", Py4GW.Console.MessageType.Info, log=log_to_console)
        # ** Cast Shroud of Distress **
        if Routines.Sequential.Skills.CastSkillID(shroud_of_distress, log =log_to_console):
            sleep(1.25)
            return
         
    #need to keep Channeling up
    has_channeling = Routines.Checks.Effects.HasBuff(player_agent_id,bot_variables.skillbar.channeling)
    if not has_channeling:
        ConsoleLog(MODULE_NAME, "Casting Channeling.", Py4GW.Console.MessageType.Info, log=log_to_console)
        # ** Cast Channeling **
        if Routines.Sequential.Skills.CastSkillID(channeling, log =log_to_console):
            sleep(1.25)
            return
            
    #Keep way of perfection up on recharge
    # ** Cast Way of Perfection **
    if Routines.Sequential.Skills.CastSkillID(way_of_perfection, log=log_to_console):
        ConsoleLog(MODULE_NAME, "Casting Way of Perfection.", Py4GW.Console.MessageType.Info, log=log_to_console)
        sleep(0.350)
        return
        
    # ** Heart of Shadow to Stay Alive or to get out of stuck**
    if not bot_variables.config.in_killing_routine:
        if Agent.GetHealth(player_agent_id) < 0.35 or bot_variables.config.stuck_count > 0:
            if bot_variables.config.pause_stuck_routine:
                Routines.Sequential.Agents.ChangeTarget(player_agent_id)
            else:
                Routines.Sequential.Agents.TargetNearestEnemy(Range.Earshot.value)

            if Routines.Sequential.Skills.CastSkillID(heart_of_shadow, log=log_to_console):
                sleep(0.350)
                return
                
    # ** Killing Routine **
    if bot_variables.config.in_killing_routine:
        arcane_echo_slot = 7
        wastrels_demise_slot = 6
        both_ready = Routines.Checks.Skills.IsSkillSlotReady(wastrels_demise_slot) and Routines.Checks.Skills.IsSkillSlotReady(arcane_echo_slot)
        target = GetNotHexedEnemy()  
        if target:
            Routines.Sequential.Agents.ChangeTarget(target)
            if Routines.Sequential.Skills.CastSkillSlot(arcane_echo_slot, extra_condition=both_ready, log=log_to_console):
                ConsoleLog(MODULE_NAME, "Casting Arcane Echo.", Py4GW.Console.MessageType.Info, log=log_to_console)
                sleep(2)
            else:
                if Routines.Sequential.Skills.CastSkillSlot(arcane_echo_slot, log=log_to_console):
                    ConsoleLog(MODULE_NAME, "Casting Echoed Wastrel.", Py4GW.Console.MessageType.Info, log=log_to_console)
                    sleep(0.350)
                    return
        target = GetNotHexedEnemy()  
        if target: 
            Routines.Sequential.Agents.ChangeTarget(target)
            if Routines.Sequential.Skills.CastSkillSlot(wastrels_demise_slot, log=log_to_console):
                sleep(0.350)
                return

#endregion

def SkillHandler():
    """Thread function that manages counting based on ImGui button presses."""
    global MAIN_THREAD_NAME, bot_variables
    while True:
        bjora_marches = 482 #Bjora Marches
        jaga_moraine = 546 #Jaga Moraine
        
        if not Routines.Checks.Map.MapValid():
            sleep(1)
            continue
        
        #if we are occupied with something else, skip this iteration
        if not Routines.Checks.Skills.CanCast():
            sleep(0.1)
            continue
        
        if bot_variables.config.finished_routine:
            sleep(1)  
            continue
        
        if Map.GetMapID() == bjora_marches:
            BjoraMarchesSkillCasting()
        elif Map.GetMapID() == jaga_moraine:    
            JagaMoraineSkillCasting()

        



MAIN_THREAD_NAME = "RunBotSequentialLogic"

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
                        thread_manager.stop_all_threads()
                        thread_manager.add_thread(MAIN_THREAD_NAME, RunBotSequentialLogic)
                        thread_manager.add_thread("SkillHandler", SkillHandler)
                        thread_manager.start_watchdog(MAIN_THREAD_NAME)
                    else:
                        reset_environment()
                        thread_manager.stop_all_threads()

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.end_table()
                
            # --- Config Section ---
            if PyImGui.collapsing_header("Config"):
                bot_variables.config.log_to_console = PyImGui.checkbox("Log to Console", bot_variables.config.log_to_console)

                # Loot Section
                if PyImGui.tree_node("Loot"):
                    for label, attr in [
                        ("Lockpicks", "loot_lockpicks"),
                        ("White Dyes", "loot_white_dyes"),
                        ("Black Dyes", "loot_black_dyes"),
                        ("Map Pieces", "loot_map_pieces")
                    ]:
                        setattr(bot_variables.loot_config, attr,
                                PyImGui.checkbox(label, getattr(bot_variables.loot_config, attr)))

                    if PyImGui.tree_node("White Looting"):
                        for label, attr in [
                            ("Items", "loot_whites"),
                            ("Glacial Stones", "loot_glacial_stones"),
                            ("Tomes", "loot_tomes"),
                            ("Dyes", "loot_dyes"),
                            ("Event Items", "loot_event_items")
                        ]:
                            setattr(bot_variables.loot_config, attr,
                                    PyImGui.checkbox(label, getattr(bot_variables.loot_config, attr)))
                        PyImGui.tree_pop()

                    for label, attr in [
                        ("Loot Blues", "loot_blues"),
                        ("Loot Purples", "loot_purples"),
                        ("Loot Golds", "loot_golds")
                    ]:
                        setattr(bot_variables.loot_config, attr,
                                PyImGui.checkbox(label, getattr(bot_variables.loot_config, attr)))

                    PyImGui.tree_pop()

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
                if PyImGui.button("Print Filtered Arrays"):
                    print_filter_salvage_array()
                identify_array = filter_identify_array()
                salvage_array = filter_salvage_array()
                deposit_array = filter_items_to_deposit()
                loot_array = get_filtered_loot_array()
                #loot_array = get_filtered_loot_array()
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
        frame = inspect.currentframe()
        current_function = frame.f_code.co_name if frame else "Unknown"
        Py4GW.Console.Log(MODULE_NAME, f"Error in {current_function}: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

#endregion


def main():
    global MAIN_THREAD_NAME
    global bot_variables
    try:   
        if bot_variables.config.is_script_running:
            thread_manager.update_all_keepalives()
            Handle_Stuck()

        DrawWindow()
        
        if Map.IsMapLoading():
            ActionQueueManager().ResetAllQueues()
            bot_variables.config.auto_stuck_command_timer.Reset()
            bot_variables.config.stuck_count = 0
            return
            
        if not Routines.Checks.Skills.InCastingProcess() and not Agent.IsKnockedDown(Player.GetAgentID()):
            ActionQueueManager().ProcessQueue("ACTION")
        ActionQueueManager().ProcessQueue("SALVAGE")   
        ActionQueueManager().ProcessQueue("IDENTIFY")             
        ActionQueueManager().ProcessQueue("MERCHANT")       
        ActionQueueManager().ProcessQueue("LOOT")


        
    except Exception as e:
        ConsoleLog(MODULE_NAME,f"Error: {str(e)}",Py4GW.Console.MessageType.Error,log=True)

if __name__ == "__main__":
    main()
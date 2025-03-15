from Py4GWCoreLib import *
import time
from time import sleep

MODULE_NAME = "VaettirBot 3.0"
#region paths

path_points_to_merchant = [(-23041, 14939)]
path_points_to_leave_outpost = [(-24380, 15074), (-26375, 16180)]
path_points_to_traverse_bjora_marches = [
    (17810, -17649), (16582, -17136), (15257, -16568), (14084, -15748), (12940, -14873),
    (11790, -14004), (10640, -13136), (9404 , -12411), (8677 , -11176), (8581 , -9742 ),
    (7892 , -8494 ), (6989 , -7377 ), (6184 , -6180 ), (5384 , -4980 ), (4549 , -3809 ),
    (3622 , -2710 ), (2601 , -1694 ), (1185 , -1535 ), (-251 , -1514 ), (-1690, -1626 ),
    (-3122, -1771 ), (-4556, -1752 ), (-5809, -1109 ), (-6966,  -291 ), (-8390,  -142 ),
    (-9831,  -138 ), (-11272, -156 ), (-12685, -198 ), (-13933,  267 ), (-14914, 1325 ),
    (-15822, 2441 ), (-16917, 3375 ), (-18048, 4223 ), (-19196, 4986 ), (-20000, 5595 ),
    (-20300, 5600 )
]

#endregion

#region globals
class build:
    deadly_paradox:int = 0
    shadow_form:int = 0
    shroud_of_distress:int = 0
    way_of_perfection:int = 0
    heart_of_shadow:int = 0
    wastrels_worry:int = 0
    arcane_echo:int = 0
    channeling:int = 0

skillbar = build()


class InventoryConfig:
    def __init__(self):
        self.leave_free_slots = 4
        self.keep_id_kit = 2
        self.keep_salvage_kit = 2
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
        

class BOTVARIABLES:
    def __init__(self):
        self.is_script_running = False
        self.log_to_console = True # Controls whether to print to console
        self.action_queue = ActionQueueNode(75)
        self.merchant_queue = ActionQueueNode(750)
        self.salvage_queue = ActionQueueNode(350)
        self.inventory_config = InventoryConfig()
        self.sell_config = SellConfig()
        self.id_config = IDConfig()
        self.salvage_config = SalvageConfig()
        
bot_variables = BOTVARIABLES()
#endregion

# Instantiate MultiThreading manager
thread_manager = MultiThreading(0.3)

#region helpers

def IsSkillBarLoaded():
    global bot_variables
    global skillbar

    primary_profession, secondary_profession = Agent.GetProfessionNames(Player.GetAgentID())
    if primary_profession != "Assassin" and secondary_profession != "Mesmer":
        frame = inspect.currentframe()
        current_function = frame.f_code.co_name if frame else "Unknown"
        ConsoleLog(MODULE_NAME, f"{current_function} - This bot requires A/Me to work, halting.", Py4GW.Console.MessageType.Error, log=True)
        return False

    skillbar.deadly_paradox = SkillBar.GetSkillIDBySlot(1)
    skillbar.shadow_form = SkillBar.GetSkillIDBySlot(2)
    skillbar.shroud_of_distress = SkillBar.GetSkillIDBySlot(3)
    skillbar.way_of_perfection = SkillBar.GetSkillIDBySlot(4)
    skillbar.heart_of_shadow = SkillBar.GetSkillIDBySlot(5)
    skillbar.wastrels_worry = SkillBar.GetSkillIDBySlot(6)
    skillbar.arcane_echo = SkillBar.GetSkillIDBySlot(7)
    skillbar.channeling = SkillBar.GetSkillIDBySlot(8)
    
    ConsoleLog(MODULE_NAME, f"SkillBar Loaded.", Py4GW.Console.MessageType.Info, log=bot_variables.log_to_console)       
    return True

def SetHardMode():
    global bot_variables
    bot_variables.action_queue.add_action(Party.SetHardMode)
    ConsoleLog(MODULE_NAME, "Hard mode set.", Py4GW.Console.MessageType.Info, log=bot_variables.log_to_console)
    
def reset_environment():
    global bot_variables
    bot_variables.is_script_running = False
    bot_variables.action_queue.clear()
    bot_variables.merchant_queue.clear()
    

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

    if not bot_variables.id_config.id_blues:
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsBlue(item_id))
    if not bot_variables.id_config.id_purples:
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsPurple(item_id))
    if not bot_variables.id_config.id_golds:
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsGold(item_id))          
    return unidentified_items

def filter_salvage_array():
    global bot_variables
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    salvageable_items = ItemArray.GetItemArray(bags_to_check)
    salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: Item.Usage.IsIdentified(item_id))
    salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: Item.Usage.IsSalvageable(item_id))

    if not bot_variables.salvage_config.salvage_blues:
        salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: not Item.Rarity.IsBlue(item_id))
    if not bot_variables.salvage_config.salvage_purples:
        salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: not Item.Rarity.IsPurple(item_id))
    if not bot_variables.salvage_config.salvage_golds:
        salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: not Item.Rarity.IsGold(item_id))
    return salvageable_items
        
def filter_items_to_deposit():
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    items_to_deposit = ItemArray.GetItemArray(bags_to_check)
    banned_models = {2992,5899}
    items_to_deposit = ItemArray.Filter.ByCondition(items_to_deposit, lambda item_id: Item.GetModelID(item_id) not in banned_models)
    return items_to_deposit
    
#endregion

#region ImGui
def DrawWindow():
    """ImGui draw function that runs every frame."""
    global bot_variables
    
    flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize
    if PyImGui.begin("Py4GW", flags):
        PyImGui.text("This is a template for sequential coding.")
        
        button_text = "Start script" if not bot_variables.is_script_running else "Stop script"
        if PyImGui.button(button_text):
            bot_variables.is_script_running = not bot_variables.is_script_running                

    PyImGui.end()
#endregion
    

#region Sequential coding
def RunBotSequentialLogic():
    """Thread function that manages counting based on ImGui button presses."""
    global MAIN_THREAD_NAME, bot_variables

    while True:
        if thread_manager.should_stop(MAIN_THREAD_NAME):
            ConsoleLog(MODULE_NAME,"thread stopping.",log= bot_variables.log_to_console)
            break  

        if not bot_variables.is_script_running:
            sleep(1)
            continue
        
        #movement and follow objects
        path_to_merchant = Routines.Movement.PathHandler(path_points_to_merchant)
        path_to_leave_outpost = Routines.Movement.PathHandler(path_points_to_leave_outpost)
        path_to_traverse_bjora_marches = Routines.Movement.PathHandler(path_points_to_traverse_bjora_marches)
        follow_object = Routines.Movement.FollowXY()
        
        
        longeyes_ledge = 650 #Longeyes Ledge
        Routines.Sequential.Map.TravelToOutpost(longeyes_ledge, 
                                                bot_variables.action_queue, 
                                                bot_variables.log_to_console)
        Routines.Sequential.Skills.LoadSkillbar("OwVUI2h5lPP8Id2BkAiAvpLBTAA", 
                                                bot_variables.action_queue, 
                                                bot_variables.log_to_console)
        
        if not IsSkillBarLoaded():
            reset_environment()
            ConsoleLog(MODULE_NAME, "You need the following build: OwVUI2h5lPP8Id2BkAiAvpLBTAA", Py4GW.Console.MessageType.Error, log=True)
            break
        
        Routines.Sequential.Map.SetHardMode(bot_variables.action_queue, bot_variables.log_to_console)
                
        #inventory management  
        if NeedsToHandleInventory():
            #going to merchant
            Routines.Sequential.Movement.FollowPath(path_to_merchant, 
                                                    follow_object, 
                                                    bot_variables.action_queue)        
            Routines.Sequential.Targeting.TargetNearestNPC(bot_variables.action_queue)
            Routines.Sequential.Player.InteractTarget(bot_variables.action_queue)
            
            if bot_variables.sell_config.sell_materials:
                items_to_sell = get_filtered_materials_to_sell()
                #sell materials to make space
                Routines.Sequential.Merchant.SellItems(items_to_sell, 
                                                       bot_variables.merchant_queue, 
                                                       bot_variables.log_to_console)
            Routines.Sequential.Merchant.BuyIDKits(GetIDKitsToBuy(), 
                                                   bot_variables.merchant_queue, 
                                                   bot_variables.log_to_console)
            Routines.Sequential.Merchant.BuySalvageKits(GetSalvageKitsToBuy(), 
                                                        bot_variables.merchant_queue, 
                                                        bot_variables.log_to_console)
            
            items_to_idenfity = filter_identify_array()
            Routines.Sequential.Items.IdentifyItems(items_to_idenfity, 
                                                    bot_variables.salvage_queue, 
                                                    bot_variables.log_to_console)
            items_to_salvage = filter_salvage_array()
            Routines.Sequential.Items.SalvageItems(items_to_salvage, 
                                                   bot_variables.salvage_queue, 
                                                   bot_variables.log_to_console)
            if bot_variables.sell_config.sell_materials:
                items_to_sell = get_filtered_materials_to_sell()
                Routines.Sequential.Merchant.SellItems(items_to_sell, 
                                                       bot_variables.merchant_queue, 
                                                       bot_variables.log_to_console)
            items_to_deposit = filter_items_to_deposit()
            Routines.Sequential.Items.DepositItems(items_to_deposit, 
                                                   bot_variables.salvage_queue, 
                                                   bot_variables.log_to_console)
            Routines.Sequential.Items.DepositGold(bot_variables.inventory_config.keep_gold_amount, 
                                                  bot_variables.salvage_queue, 
                                                  bot_variables.log_to_console)
        
        #exit outpost
        Routines.Sequential.Movement.FollowPath(path_handler= path_to_leave_outpost, 
                                                movement_object = follow_object, 
                                                action_queue = bot_variables.action_queue,
                                                custom_exit_condition=lambda: Map.IsMapLoading())
        bjora_marches = 482 #Bjora Marches
        Routines.Sequential.Map.WaitforMapLoad(bjora_marches, bot_variables.log_to_console)
        #traverse bjora marches
        Routines.Sequential.Movement.FollowPath(path_to_traverse_bjora_marches, 
                                                follow_object, 
                                                bot_variables.action_queue,
                                                custom_exit_condition=lambda: Agent.IsDead(Player.GetAgentID()))
        if Agent.IsDead(Player.GetAgentID()):
            ConsoleLog(MODULE_NAME, "Player is dead. Stopping script.", Py4GW.Console.MessageType.Error, log=bot_variables.log_to_console)
            reset_environment()
            break
        
        
        
        
        
        
        
        
        
        bot_variables.is_script_running = False
        ConsoleLog(MODULE_NAME, "Script finished.", Py4GW.Console.MessageType.Info, log=bot_variables.log_to_console)
        time.sleep(0.1)
#endregion

#region SkillHandler

#region Sequential coding
def SkillHandler():
    """Thread function that manages counting based on ImGui button presses."""
    global MAIN_THREAD_NAME, bot_variables
    while True:
        sleep(1)
        #skill handling goes here


#region Watchdog
def watchdog_fn():
    """Daemon thread that monitors all active threads and shuts down unresponsive ones."""
    global MAIN_THREAD_NAME

    while True:
        active_threads = list(thread_manager.threads.keys())

        #Check for timeouts and stop unresponsive threads
        for name in active_threads:
            if name != "watchdog" and thread_manager.should_stop(name):  # Don't stop itself
                ConsoleLog(f"Watchdog",f"Thread: {name}' timed out. Stopping it.",Console.MessageType.Notice,log=True)
                thread_manager.stop_thread(name)

        #If the main thread itself has timed out, shut everything down
        if MAIN_THREAD_NAME not in thread_manager.threads or thread_manager.should_stop(MAIN_THREAD_NAME):
            
            print("[Watchdog] Main thread has timed out. Stopping all threads.")
            thread_manager.stop_all_threads()
            break  # Watchdog exits naturally, no `join()` needed

        time.sleep(1)  #Adjust checking interval as needed


#endregion

MAIN_THREAD_NAME = "RunBotSequentialLogic"
thread_manager.add_thread(MAIN_THREAD_NAME, RunBotSequentialLogic)
thread_manager.start_thread(MAIN_THREAD_NAME)

thread_manager.add_thread("SkillHandler", SkillHandler)
thread_manager.start_thread("SkillHandler")

thread_manager.add_thread("watchdog", watchdog_fn)
thread_manager.start_thread("watchdog")


def main():
    global MAIN_THREAD_NAME
    try:
        thread_manager.update_keepalive(MAIN_THREAD_NAME)
        thread_manager.update_keepalive("SkillHandler")

        DrawWindow()
        
        if bot_variables.action_queue.action_queue_timer.HasElapsed(bot_variables.action_queue.action_queue_time):
            bot_variables.action_queue.execute_next()
        
        if bot_variables.salvage_queue.action_queue_timer.HasElapsed(bot_variables.salvage_queue.action_queue_time):
            if not bot_variables.salvage_queue.is_empty():
                bot_variables.salvage_queue.execute_next()
        
        if bot_variables.merchant_queue.action_queue_timer.HasElapsed(bot_variables.merchant_queue.action_queue_time):
            if not bot_variables.merchant_queue.is_empty():
                bot_variables.merchant_queue.execute_next()
                ConsoleLog(MODULE_NAME, "Item sold.", Py4GW.Console.MessageType.Info, log=bot_variables.log_to_console)
            
    except Exception as e:
        ConsoleLog(MODULE_NAME,f"Error: {str(e)}",Py4GW.Console.MessageType.Error,log=True)

if __name__ == "__main__":
    main()
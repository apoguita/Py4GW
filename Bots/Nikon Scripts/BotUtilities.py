from Py4GWCoreLib import *
from WindowUtilites import *

import Mapping
import Items

pyParty = PyParty.PyParty()

class Heroes:
    Norgu = 1
    Goren = 2
    Tahlkora = 3
    MasterOfWhispers = 4
    AcolyteJin = 5
    Koss = 6
    Dunkoro = 7
    AcolyteSousuke = 8
    Melonni = 9
    ZhedShadowhoof = 10
    GeneralMorgahn = 11
    MagridTheSly = 12
    Zenmai = 13
    Olias = 14
    Razah = 15
    MOX = 16
    KeiranThackeray = 17
    Jora = 18
    PyreFierceshot = 19
    Anton = 20
    Livia = 21
    Hayda = 22
    Kahmu = 23
    Gwen = 24
    Xandra = 25
    Vekk = 26
    Ogden = 27
    MercenaryHero1 = 28
    MercenaryHero2 = 29
    MercenaryHero3 = 30
    MercenaryHero4 = 31
    MercenaryHero5 = 32
    MercenaryHero6 = 33
    MercenaryHero7 = 34
    MercenaryHero8 = 35
    Miku = 36
    ZeiRi = 37

    @staticmethod
    def Exists(value):
        return any(value == getattr(Heroes, attr) for attr in vars(Heroes))

class GameAreas:
    Touch = 144
    Adjacent = 166
    Nearby = 252
    Area = 322
    Lesser_Earshot = 900
    Earshot = 1012 
    Spellcast = 1248
    Spirit = 2500
    Compass = 5000
    
    @staticmethod
    def Exists(value):
        return any(value == getattr(GameAreas, attr) for attr in vars(GameAreas))

################## SKILL HANDLING ROUTINES ##################

class aftercast_class:
    in_aftercast = False
    aftercast_time = 0
    aftercast_timer = Timer()
    aftercast_timer.Start()

    def update(self):
        if self.aftercast_timer.HasElapsed(self.aftercast_time):
            self.in_aftercast = False
            self.aftercast_time = 0
            self.aftercast_timer.Stop()

    def set_aftercast(self, skill_id):
        self.in_aftercast = True
        self.aftercast_time = Skill.Data.GetActivation(skill_id) + Skill.Data.GetAftercast(skill_id)
        self.aftercast_timer.Reset()


aftercast = aftercast_class()

def TargetNearestItem():
    items = AgentArray.GetItemArray()
    items = AgentArray.Filter.ByDistance(items,Player.GetXY(), 200)
    items = AgentArray.Sort.ByDistance(items, Player.GetXY())
    if len(items) > 0:        
        Player.ChangeTarget(items[0])

### --- CHECK BUFF EXISTS --- ###
def HasBuff(agent_id, skill_id):
    if Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id):
        return True
    return False

def BuffTimeRemaining(agent_id, skill_id):
    if HasBuff(agent_id, skill_id):
        buffs = Effects.GetBuffs(agent_id)

        if buffs:
            for buff in buffs:
                if buff.skill_id == skill_id:
                    return True
        
        effects = Effects.GetEffects(agent_id)

        if effects:
            for effect in effects:
                if effect.skill_id == skill_id:
                    return effect.time_remaining

def GetAllEffectsTimeRemaining(agent_id):
    effects = Effects.GetEffects(agent_id)

    effects_time = []

    for effect in effects: 
        combo = (effect.skill_id, effect.time_remaining)
        effects_time = combo

    return effects_time


def CheckSurrounded(number_foes, area=GameAreas.Lesser_Earshot):
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, Player.GetXY(), area)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    return len(enemy_array) > number_foes

### --- CHECK SKILLS --- ###
def IsSkillReadyById(skill_id):
    return IsSkillReadyBySlot(SkillBar.GetSlotBySkillID(skill_id))

def IsSkillReadyBySlot(skill_slot):
    skill = SkillBar.GetSkillData(skill_slot)
    return skill.recharge == 0

def HasEnoughEnergy(skill_id):
    player_agent_id = Player.GetAgentID()
    energy = Agent.GetEnergy(player_agent_id)
    max_energy = Agent.GetMaxEnergy(player_agent_id)
    energy_points = int(energy * max_energy)

    return Skill.Data.GetEnergyCost(skill_id) <= energy_points

def CanCast(player_id) -> bool:
    if not player_id:
        player_id = Player.GetAgentID()
    
    global aftercast
    aftercast.update()

    if (Agent.IsCasting(player_id) 
        or Agent.IsKnockedDown(player_id)
        or Agent.IsDead(player_id)
        or aftercast.in_aftercast):
        return False
    return True

def CastSkillById(skill_id):
    global aftercast
    SkillBar.UseSkill(SkillBar.GetSlotBySkillID(skill_id))
    aftercast.set_aftercast(skill_id)
 
def CastSkillBySlot(skill_slot):
    global aftercast
    SkillBar.UseSkill(skill_slot)
    aftercast.set_aftercast(SkillBar.GetSkillIDBySlot(skill_slot))

### --- CHECK ENEMY POSITION --- ###
def IsEnemyInFront (agent_id) -> bool:  # code originally taken from vaettir bot but was IsEnemyBehind which incorrectly checked if enemy was in front. I just renamed and adjusted the angles a bit to be more in front
    player_agent_id = Player.GetAgentID()
    player_x, player_y = Agent.GetXY(player_agent_id)
    player_angle = Agent.GetRotationAngle(player_agent_id)  # Player's facing direction
    nearest_enemy = agent_id
    #if target is None:
    Player.ChangeTarget(nearest_enemy)
    #target = nearest_enemy
    nearest_enemy_x, nearest_enemy_y = Agent.GetXY(nearest_enemy)                

    # Calculate the angle between the player and the enemy
    dx = nearest_enemy_x - player_x
    dy = nearest_enemy_y - player_y
    angle_to_enemy = math.atan2(dy, dx)  # Angle in radians
    angle_to_enemy = math.degrees(angle_to_enemy)  # Convert to degrees
    angle_to_enemy = (angle_to_enemy + 360) % 360  # Normalize to [0, 360]

    # Calculate the relative angle to the enemy
    angle_diff = (angle_to_enemy - player_angle + 360) % 360

    if angle_diff < 45 or angle_diff > 315:
        return True
    return False

### --- HEROES --- ###
# Check if hero in party
def IsHeroInParty(id: int) -> bool:
    # Ensure the hero id is in deed a hero.
    if not Heroes.Exists(id):
        return False
    
    if Party.GetHeroCount() == 0:
        return False
    
    for _, hero in enumerate(Party.GetHeroes()):
        if hero.hero_id == id:
            return True
        
    return False

### --- HEROES --- ###

### --- REPORTS PROGRESS --- ###
class ReportsProgress():
    window = BasicWindow()    
    step_transition_threshold_timer = Timer()
    
    main_item_collect = 0
    idItems = True
    sellItems = True
    sellWhites = True
    sellBlues = True
    sellGrapes = True
    sellGolds = True
    sellGreens = True
    sellMaterials = False
    salvageItems = False
    salvWhites = False
    salvBlues = False
    salvGrapes = False
    salvGold = False
    collect_white_items = True
    collect_blue_items = True
    collect_grape_items = True
    collect_gold_items = True
    collect_green_items = True
    collect_gold_coins = True
    collect_dye_white_black = True
    collect_event_items = True
    
    default_min_slots = 3

    def __init__(self, window):
        if issubclass(type(window), BasicWindow):
            self.window = window
            
    def UpdateState(self, state):
        if issubclass(type(self.window), BasicWindow):
            self.window.UpdateState(state)

    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if issubclass(type(self.window), BasicWindow):
            self.window.Log(text, msgType)

    def CanPickUp(self, agentId):
        # Need to make sure that if inventory is full, check if the item is stackable and there is a stack in inventory with space.
        agent = Agent.GetAgentByID(agentId)

        if agent:
            item = Agent.GetItemAgent(agentId)

            if item:     
                model = Item.GetModelID(item.item_id)

                if model == Items.Gold_Coin and self.collect_gold_coins:
                    # Check should collect gold coins and this is gold coins
                    onHand = Inventory.GetGoldOnCharacter()
                    return onHand <= 99500                        
                elif model == Items.Dye.Dye_ModelId:
                    # Check should collect dye and this is dye
                    return self.collect_dye_white_black and (item.extra_type == Items.Dye.Black_Dye or item.extra_type == Items.Dye.White_Dye)           
                elif self.collect_event_items and model in Items.EventItems_Array:
                    # Check should collect event items and this is event item
                    return True
                else:
                    # Check should collect color items and this is color item
                    return (Item.Rarity.IsWhite(item.item_id) and self.collect_white_items) or \
                            (Item.Rarity.IsBlue(item.item_id) and self.collect_blue_items) or \
                            (Item.Rarity.IsPurple(item.item_id) and self.collect_grape_items) or \
                            (Item.Rarity.IsGold(item.item_id) and self.collect_gold_items) or \
                            (Item.Rarity.IsGreen(item.item_id) and self.collect_green_items)
            
        return False

    def GetNearestPickupItem(self):
        try:            
            items = AgentArray.GetItemArray()
            items = AgentArray.Filter.ByDistance(items, Player.GetXY(), GameAreas.Lesser_Earshot)
            items = AgentArray.Sort.ByDistance(items, Player.GetXY())

            if items != None and len(items) > 0:
                for item in items:
                    if self.CanPickUp(item):
                        return item
            
            return 0
        except Exception as e:
            Py4GW.Console.Log("Utilities", f"GetNearestPickupItem error {str(e)}")

    def ExecuteTimedStep(self, state, function):
        if not self.step_transition_threshold_timer.IsRunning():
            self.step_transition_threshold_timer.Start()

        self.ExecuteStep(state, function)

    def ExecuteStep(self, state, function):
        self.UpdateState(state)

        # Try to execute the function if present.        
        try:
            if callable(function):
                function()
        except:
            self.Log(f"Calling function {function.__name__} failed", Py4GW.Console.MessageType.Error)
    
    def ShouldForceTransitionStep(self, custom_threshold=300000):        
        if not self.step_transition_threshold_timer.IsRunning():
            self.step_transition_threshold_timer.Start()
            return False

        elapsed = self.step_transition_threshold_timer.HasElapsed(custom_threshold)

        if elapsed:
            self.Log("Forced Step Transition", Py4GW.Console.MessageType.Warning)
            self.step_transition_threshold_timer.Reset()
        return elapsed
    
    def ApplySelections(self, main_item_collect_count, id_items, collect_coins, collect_events, collect_items_white, collect_items_blue, \
                collect_items_grape, collect_items_gold, collect_dye, sell_items, sell_items_white, \
                sell_items_blue, sell_items_grape, sell_items_gold, sell_items_green, sell_materials, salvage_items, salvage_items_white, \
                salvage_items_blue, salvage_items_grape, salvage_items_gold):        
        self.main_item_collect = main_item_collect_count
        self.idItems = id_items
        self.sellItems = sell_items
        self.sellWhites = sell_items_white
        self.sellBlues = sell_items_blue
        self.sellGrapes = sell_items_grape
        self.sellGolds = sell_items_gold
        self.sellGreens = sell_items_green
        self.sellMaterials = sell_materials
        self.salvageItems = salvage_items
        self.salvWhites = salvage_items_white
        self.salvBlues = salvage_items_blue
        self.salvGrapes = salvage_items_grape
        self.salvGold = salvage_items_gold
        self.collect_white_items = collect_items_white
        self.collect_blue_items = collect_items_blue
        self.collect_grape_items = collect_items_grape
        self.collect_gold_items = collect_items_gold
        self.collect_gold_coins = collect_coins
        self.collect_dye_white_black = collect_dye
        self.collect_event_items = collect_events

    
    def ApplyConfigSettings(self, min_slots) -> None:
        self.default_min_slots = min_slots

### --- REPORTS PROGRESS --- ###

### --- SALVAGE ROUTINE --- ###
class SalvageFsm(FSM):
    inventoryHandler = PyInventory.PyInventory()   
    logFunc = None
    window = BasicWindow()
    salvage_Items = []
    current_salvage = 0
    current_quantity = 0
    confirmed = False
    pending_stop = False
    salvage_kit = False

    salvager_start = "Start Salvage"
    salvager_continue = "Continue Salvage"
    salvager_finish = "Finish Salvage"
    salvager_check_done = "Salvaging Done?"

    def __init__(self, window=BasicWindow(), name="SalvageFsm", logFunc=None):
        super().__init__(name)

        self.window = window
        self.name = name
        self.logFunc = logFunc

        self.AddState(self.salvager_start,
                        execute_fn=lambda: self.ExecuteStep(self.salvager_start, self.StartSalvage()),
                        transition_delay_ms=100)
        self.AddState(self.salvager_continue,
                        execute_fn=lambda: self.ExecuteStep(self.salvager_continue, self.ContinueSalvage()),
                        transition_delay_ms=100)
        self.AddState(self.salvager_finish,
                        execute_fn=lambda: self.ExecuteStep(self.salvager_finish, self.FinishSalvage()),
                        transition_delay_ms=100)
        self.AddState(self.salvager_check_done,
                        execute_fn=lambda: self.EndSalvageLoop(),
                        transition_delay_ms=100)
    
    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if issubclass(type(self.window), BasicWindow):            
            self.window.Log(text, msgType)

    def ExecuteStep(self, state, function):
        self.UpdateState(state)

        # Try to execute the function if present.        
        try:
            if callable(function):
                function()
        except Exception as e:
            self.Log(f"Calling function {function.__name__} failed. {str(e)}", Py4GW.Console.MessageType.Error)

    def UpdateState(self, state):
        if issubclass(type(self.window), BasicWindow):
            self.window.UpdateState(state)

    def IsExecuting(self):
        return self.is_started() and not self.is_finished()
    
    def SetSalvageItems(self, salvageItems):
        self.salvage_Items = salvageItems

    def StartSalvage(self):
        salvage_kit = Inventory.GetFirstSalvageKit()
        
        if salvage_kit == 0:
            self.Log("No Salvage Kit")
            self.salvage_kit = False
            self.confirmed = False
            return
        
        self.salvage_kit = True

        if self.current_salvage == 0 and self.salvage_Items and isinstance(self.salvage_Items, list) and len(self.salvage_Items) > 0:            
            self.current_salvage = self.salvage_Items.pop(0)
            self.current_quantity = Item.Properties.GetQuantity(self.current_salvage)

        if self.current_salvage == 0:
            return False        

        self.inventoryHandler.StartSalvage(salvage_kit, self.current_salvage)

    def ContinueSalvage(self):
        if not self.salvage_kit:
            return
        
        if not Item.Rarity.IsWhite(self.current_salvage):  
            self.confirmed = True
            Keystroke.PressAndRelease(Key.Y.value)
        #this is a fix for salvaging with a lesser kit, it will press Y to confirm the salvage
        #this produces the default key for minions to open, need to implenet an IF statement 
        #to check wich type os salvaging youre performing
        #the game itself wont salvage an unidentified item, so be aware of that   
        self.inventoryHandler.HandleSalvageUI()
        pass

    def FinishSalvage(self):
        if not self.salvage_kit:
            return
        
        self.inventoryHandler.FinishSalvage()
        pass

    def EndSalvageLoop(self):
        if not self.salvage_kit or self.pending_stop:
            try:
                if self.window:
                    self.window.DoneSalvaging(False)
            except:
                pass  

            return
        
        if not self.IsFinishedSalvage():
            if self.confirmed:  
                Keystroke.PressAndRelease(Key.Y.value)

            self.confirmed = False            
            self.jump_to_state_by_name(self.salvager_start)
        else:
            self.finished = True   
            try:
                if self.window:
                    self.window.DoneSalvaging(True)
            except:
                pass     
        
        return
    
    def IsFinishedSalvage(self): 
        salvage_kit = Inventory.GetFirstSalvageKit()
        
        if self.current_salvage != 0:
            self.current_quantity -= 1

            if self.current_quantity == 0:
                self.current_salvage = 0

        if self.current_salvage == 0:
            return True
        
        if salvage_kit == 0:
            self.Log("No Salvage Kit")
            return True

        return False
        
    def start(self):
        self.pending_stop = False
        super().start()
    def stop(self):
        self.current_salvage = 0
        self.pending_stop = True
### --- SALVAGE ROUTINE --- ###
    
### --- IDENTIFY ROUTINE --- ###
class IdentifyFsm(FSM):
    logFunc = None
    window = BasicWindow()

    inventory_id_items = "ID Items"
    inventory_id_check = "ID Items Check"

    identifyItems = []
    has_id_kit = True

    def __init__(self, window=BasicWindow(), name="IdentifyFsm", logFunc=None):
        super().__init__(name)

        self.window = window
        self.logFunc = logFunc
        
        self.AddState(name=self.inventory_id_items,
            execute_fn=lambda: self.ExecuteStep(self.inventory_id_items, self.IdentifyItems()),
            transition_delay_ms=150)
        
        self.AddState(name=self.inventory_id_check,
            execute_fn=lambda: self.ExecuteStep(self.inventory_id_items, self.EndIdentifyLoop()),
            transition_delay_ms=150)
        
    def IsExecuting(self):
        return self.is_started() and not self.is_finished()
    
    def ExecuteStep(self, state, function):
        self.UpdateState(state)

        # Try to execute the function if present.        
        try:
            if callable(function):
                function()
        except Exception as e:
            self.window.Log(f"Calling function {function.__name__} failed. {str(e)}", Py4GW.Console.MessageType.Error)

    def UpdateState(self, state):
        if issubclass(type(self.window), BasicWindow):
            self.window.UpdateState(state)

    def SetIdentifyItems(self, identifyItems):
        self.identifyItems = identifyItems

    def IdentifyItems(self): 
        if not self.identifyItems or len(self.identifyItems) == 0:
            return

        id_kit = Inventory.GetFirstIDKit()

        if id_kit == 0:
            self.has_id_kit = False
            return

        idItem = self.identifyItems.pop(0)
        
        if idItem > 0:
            Inventory.IdentifyItem(idItem, id_kit)

    def EndIdentifyLoop(self):
        if not self.has_id_kit:
            if self.window:
                self.window.DoneIdentifying(False)
            
            return
        
        if len(self.identifyItems) == 0:
            if self.window:
                self.window.DoneIdentifying(True)
            
            return            
        
        self.jump_to_state_by_name(self.inventory_id_items)
### --- IDENTIFY ROUTINE --- ###

class InventoryFsm(FSM):
    idItems = False
    sellItems = True
    sellWhites = True
    sellBlues = True
    sellGrapes = True
    sellGolds = True
    sellGreens = True
    sellMaterials = True
    salvageItems = False
    salvWhites = False
    salvBlues = False
    salvGrapes = False
    salvGold = False

    gold_to_keep = 5000
    gold_to_store = 0
    gold_stored = 0
    gold_char_snapshot = 0
    gold_storage_snapshot = 0
    sell_item_count = -1

    inventory_setup_salv = "Update Salvage List"
    inventory_handle_gold = "Manage Money"
    inventory_buy_id_kits = "Buy ID Kits"
    inventory_sell_items = "Sell Items"
    inventory_go_merchant = "Go To Merchant"
    inventory_target_merchant = "Target Merchant"
    inventory_interact_merchant = "Interact Merchant"
    inventory_sell_materials_1 = "Sell Materials#MakeRoom"
    inventory_sell_materials_2 = "Sell Materials#FullSell"
    inventory_buy_salve_kits = "Buy Salvage Kits"
    inventory_id_items = "Id Items"
    inventory_salv_items = "Salvage Items"
    inventory_deposit_items = "Deposit Items"

    action_timer = Timer()
    stop_action_timer = Timer()
    
    merchant_path = None
    merchant_map_id = Mapping.Kamadan
    movement_handler = Routines.Movement.FollowXY(50)

    salvager = SalvageFsm()
    salvager_name = "SalvageFsm"

    # keeps list of inventory at time of creation, ensuring not to sell those items.
    current_Inventory = []

    # keeps the listed model ids in inventory, ensuring not to sell those items
    keep_items = []
    logFunc = None
    window = BasicWindow()

    def __init__(self, window, name, merchantMapId, pathToMerchant, currentInventory=None, modelIdsToKeep=None, 
                 idItems = True, sellItems=True, sellWhites=True, sellBlues=True, 
                 sellGrapes=True, sellGolds=True, sellGreens=True, sellMaterials=False, 
                 salvageItems = False, salvWhites=False, salvBlue=False, salvGrapes=False,
                 salvGolds=False, goldToKeep=5000,
                 logFunc=None):
        super().__init__(name)

        self.window = window
        self.merchant_map_id = merchantMapId
        self.merchant_path = Routines.Movement.PathHandler(pathToMerchant)
        self.current_Inventory = currentInventory
        self.keep_items = modelIdsToKeep
        self.idItems = idItems
        self.sellItems = sellItems
        self.sellWhites = sellWhites
        self.sellBlues = sellBlues
        self.sellGrapes = sellGrapes
        self.sellGolds = sellGolds
        self.sellGreens = sellGreens
        self.sellMaterials = sellMaterials
        self.salvageItems = salvageItems
        self.salvWhites = salvWhites
        self.salvBlues = salvBlue
        self.salvGrapes = salvGrapes
        self.salvGold = salvGolds
        self.gold_to_keep = goldToKeep
        self.logFunc = logFunc
        
        self.salvager = SalvageFsm(self.window, self.salvager_name, self.logFunc)

        self.AddState(name=self.inventory_setup_salv,
            execute_fn=lambda: self.ExecuteStep(self.inventory_handle_gold, self.SetupSalvageRoutine()),
            transition_delay_ms=2000)
                
        self.AddState(name=self.inventory_handle_gold,
            execute_fn=lambda: self.ExecuteStep(self.inventory_handle_gold, self.CheckGold()),
            exit_condition=lambda: Inventory.GetGoldOnCharacter() == self.gold_to_keep or Inventory.GetGoldInStorage() == 0 or Inventory.GetGoldInStorage() == 1000000,
            transition_delay_ms=2000)
        
        self.AddState(name=self.inventory_go_merchant,
            execute_fn=lambda: Routines.Movement.FollowPath(self.merchant_path, self.movement_handler),
            exit_condition=lambda: Routines.Movement.IsFollowPathFinished(self.merchant_path, self.movement_handler),
            run_once=False)
        
        self.AddState(name=self.inventory_target_merchant,
            execute_fn=lambda: self.ExecuteStep(self.inventory_target_merchant, TargetNearestNpc()),
            transition_delay_ms=1000)
        
        self.AddState(name=self.inventory_interact_merchant,
            execute_fn=lambda: self.ExecuteStep(self.inventory_interact_merchant, Routines.Targeting.InteractTarget()),
            exit_condition=lambda: Routines.Targeting.HasArrivedToTarget())
        
        self.AddState(name=self.inventory_sell_materials_1,
            execute_fn=lambda: self.ExecuteStep(self.inventory_sell_materials_1, self.SellMaterials()),
            run_once=False,
            exit_condition=lambda: self.SellingMaterialsComplete())
        
        self.AddState(name=self.inventory_buy_id_kits,
            execute_fn=lambda: self.ExecuteStep(self.inventory_buy_id_kits, self.BuyIdKits()),
            run_once=False,
            exit_condition=lambda: self.BuyIdKitsComplete())
        
        self.AddState(name=self.inventory_id_items,
            execute_fn=lambda: self.ExecuteStep(self.inventory_id_items, self.IdentifyItems()),
            run_once=False,
            exit_condition=lambda: self.IdentifyItemsComplete())
    
        self.AddSubroutine(name=self.inventory_salv_items,
            sub_fsm = self.salvager,
            condition_fn=lambda: not self.salvager.IsFinishedSalvage())
        
        self.AddState(name=self.inventory_buy_salve_kits,
            execute_fn=lambda: self.ExecuteStep(self.inventory_buy_salve_kits, self.BuySalvageKits()),
            run_once=False,
            exit_condition=lambda: self.BuySalvageKitsComplete())       
        
        self.AddState(name=self.inventory_sell_items,
            execute_fn=lambda: self.ExecuteStep(self.inventory_sell_items, self.SellItems()),
            run_once=False,
            exit_condition=lambda: self.SellItemsComplete())
                
        self.AddState(name=self.inventory_sell_materials_2,
            execute_fn=lambda: self.ExecuteStep(self.inventory_sell_materials_2, self.SellMaterials()),
            run_once=False,
            exit_condition=lambda: self.SellingMaterialsComplete())
        
        # self.AddState(name=self.inventory_deposit_items,
        #     execute_fn=lambda: self.ExecuteStep(self.inventory_deposit_items, self.DepositItems()),
        #     run_once=False,
        #     exit_condition=lambda: self.DepositItemsComplete())
        
    def ApplySelections(self, idItems = True, sellItems=True, sellWhites=True, sellBlues=True, 
                 sellGrapes=True, sellGolds=True, sellGreens=True, sellMaterials=False, 
                 salvageItems = False, salvWhites=False, salvBlue=False, salvGrapes=False,
                 salvGolds=False):
        self.idItems = idItems
        self.sellItems = sellItems
        self.sellWhites = sellWhites
        self.sellBlues = sellBlues
        self.sellGrapes = sellGrapes
        self.sellGolds = sellGolds
        self.sellGreens = sellGreens
        self.sellMaterials = sellMaterials
        self.salvageItems = salvageItems
        self.salvWhites = salvWhites
        self.salvBlues = salvBlue
        self.salvGrapes = salvGrapes
        self.salvGold = salvGolds
        
    def GetMinimumSlots(self) -> int:
        return self.default_min_slots
    
    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if not self.logFunc:
            return
        self.logFunc(text, msgType)

    def UpdateState(self, state):
        if issubclass(type(self.window), BasicWindow):
            self.window.UpdateState(state)

    def ExecuteStep(self, state, function):
        self.UpdateState(state)

        # Try to execute the function if present.        
        try:
            if callable(function):
                function()
        except:
            self.Log(f"Calling function {function.__name__} failed", Py4GW.Console.MessageType.Error)

    def SetupSalvageRoutine(self):
        if self.salvager and isinstance(self.salvager, SalvageFsm):
            self.salvager.SetSalvageItems(self.GetInventorySalvageItems())

    def GetInventorySalvageItems(self):    
        # Get items from inventory
        # current inventory is [bagNum, slotsFilled]
        items_to_salvage = GetInventoryNonKeepItemsByBagSlot(self.current_Inventory)
        items_to_salvage = GetInventoryNonKeepItemsByModelId(self.keep_items, items_to_salvage)
        items_to_salvage = GetItemIdList(items_to_salvage)
        items_to_salvage = ItemArray.Filter.ByCondition(items_to_salvage, lambda item_id: Item.Usage.IsSalvageable(item_id))
   
        white_items = []
        blue_items = []
        grape_items = []
        gold_items = []
        
        # Filter salvaging items
        if self.salvWhites:
            white_items = ItemArray.Filter.ByCondition(items_to_salvage, Item.Rarity.IsWhite)
            
        if self.salvBlues:
            blue_items = ItemArray.Filter.ByCondition(items_to_salvage, Item.Rarity.IsBlue)
            
        if self.salvGrapes:
            grape_items = ItemArray.Filter.ByCondition(items_to_salvage, Item.Rarity.IsPurple)
            
        if self.salvGold:
            gold_items = ItemArray.Filter.ByCondition(items_to_salvage, Item.Rarity.IsGold)

        items_to_salvage.clear()
        items_to_salvage.extend(white_items)
        items_to_salvage.extend(blue_items)
        items_to_salvage.extend(grape_items)
        items_to_salvage.extend(gold_items)

        return items_to_salvage
    
    def SellItems(self):
        if not self.sellItems:
            return
        
        if not self.action_timer.IsRunning():
            self.action_timer.Start()
        
        if not self.action_timer.HasElapsed(250):
            return
            
        self.action_timer.Reset()
        
        # Get items from inventory
        # current inventory is [bagNum, slotsFilled]
        items_to_sell = GetInventoryNonKeepItemsByBagSlot(self.current_Inventory)
        items_to_sell = GetInventoryNonKeepItemsByModelId(self.keep_items, items_to_sell)
        items_to_sell = GetItemIdList(items_to_sell)
        items_to_sell = ItemArray.Filter.ByCondition(items_to_sell, lambda item_id: not Item.Type.IsMaterial(item_id))
        items_to_sell = ItemArray.Filter.ByCondition(items_to_sell, lambda item_id: not Item.Type.IsRareMaterial(item_id))
            
        white_items = []
        blue_items = []
        grape_items = []
        gold_items = []
        green_items = []
        
        # Filter gold items
        
        if self.sellWhites:
            white_items = ItemArray.Filter.ByCondition(items_to_sell, Item.Rarity.IsWhite)
            
        if self.sellBlues:
            blue_items = ItemArray.Filter.ByCondition(items_to_sell, Item.Rarity.IsBlue)
            
        if self.sellGrapes:
            grape_items = ItemArray.Filter.ByCondition(items_to_sell, Item.Rarity.IsPurple)
            
        if self.sellGolds:
            gold_items = ItemArray.Filter.ByCondition(items_to_sell, Item.Rarity.IsGold)

        if self.sellGreens:
            green_items = ItemArray.Filter.ByCondition(items_to_sell, Item.Rarity.IsGreen)

        items_to_sell.clear()
        items_to_sell.extend(white_items)
        items_to_sell.extend(blue_items)
        items_to_sell.extend(grape_items)
        items_to_sell.extend(gold_items)
        items_to_sell.extend(green_items)
        
        self.sell_item_count = len(items_to_sell)

        # Sell the gold items if available and timer allows
        if self.sell_item_count > 0: 
            item_id = items_to_sell[0]
            quantity = Item.Properties.GetQuantity(item_id)
            value = Item.Properties.GetValue(item_id)
            cost = quantity * value

            Trading.Merchant.SellItem(item_id, cost)

    def SellItemsComplete(self):
        # Check if there are no remaining items
        if not self.sellItems or self.sell_item_count == 0:
            self.sell_item_count = -1       
            return True

        return False
    
    def SellMaterials(self):
        if not self.sellMaterials:
            return
        
        if not self.action_timer.IsRunning():
            self.action_timer.Start()

        if not self.action_timer.HasElapsed(250):
            return
        
        self.action_timer.Reset()

        items_to_sell = GetInventoryNonKeepItemsByBagSlot(self.current_Inventory)
        items_to_sell = GetInventoryNonKeepItemsByModelId(self.keep_items, items_to_sell)
        items_to_sell = (item for item in items_to_sell if Item.Type.IsMaterial(item.item_id))
        items_to_sell = GetItemIdList(items_to_sell)

        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        items_to_sell = ItemArray.GetItemArray(bags_to_check)
        items_to_sell = ItemArray.Filter.ByCondition(items_to_sell, lambda item_id: Item.Type.IsMaterial(item_id))

        self.sell_item_count = len(items_to_sell)

        if self.sell_item_count > 0:
            item_id = items_to_sell[0]
            quantity = Item.Properties.GetQuantity(item_id)
            value = Item.Properties.GetValue(item_id)
            cost = quantity * value
            Trading.Merchant.SellItem(item_id, cost)

    def SellingMaterialsComplete(self):
        # Check if there are no remaining materials
        if not self.sellMaterials or self.sell_item_count == 0:
            self.sell_item_count = -1
            return True

        return False

    def BuyIdKits(self):
        if not self.idItems:
            return
        
        if not self.action_timer.IsRunning():
            self.action_timer.Start()

        if not self.action_timer.HasElapsed(250):
            return
        
        self.action_timer.Reset()

        kits_in_inv = Inventory.GetModelCount(Items.Id_Kit_Superior)

        if kits_in_inv == 0:
            merchant_item_list = Trading.Merchant.GetOfferedItems()
            merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: Item.GetModelID(item_id) == Items.Id_Kit_Superior)

            if len(merchant_item_list) > 0:
                item_id = merchant_item_list[0]
                value = Item.Properties.GetValue(item_id) * 2 # value is reported is sell value not buy value
                Trading.Merchant.BuyItem(item_id, value)
            else:
                Py4GW.Console.Log("Buy ID Kits", f"No ID kits available from merchant.",Py4GW.Console.MessageType.Info)        

    def BuyIdKitsComplete(self):
        if not self.idItems:
            return True
        
        kits_in_inv = Inventory.GetModelCount(Items.Id_Kit_Superior)

        if kits_in_inv >= 1:
            self.action_timer.Stop()
            return True

        return False

    def BuySalvageKits(self):
        if not self.salvageItems:
            return
        
        if not self.action_timer.IsRunning():
            self.action_timer.Start()

        if not self.action_timer.HasElapsed(250):
            return
        
        self.action_timer.Reset()
        
        kits_in_inv = Inventory.GetModelCount(Items.Salve_Kit_Basic)

        if kits_in_inv <= 1:
            merchant_item_list = Trading.Merchant.GetOfferedItems()
            merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: Item.GetModelID(item_id) == Items.Salve_Kit_Basic)

            item_id = merchant_item_list[0]
            quantity = Item.Properties.GetQuantity(item_id)
            value = Item.Properties.GetValue(item_id) *2 # value is reported is sell value not buy value
            Trading.Merchant.BuyItem(item_id, value)

    def BuySalvageKitsComplete(self):
        if not self.salvageItems:
            return True
        
        kits_in_inv = Inventory.GetModelCount(Items.Salve_Kit_Basic)

        if kits_in_inv >= 1:
            self.action_timer.Stop()
            return True

        return False

    def CheckGold(self):
        charGold = Inventory.GetGoldOnCharacter()

        if charGold < self.gold_to_keep:
            Inventory.WithdrawGold(self.gold_to_keep - charGold)
        else:
            Inventory.DepositGold(charGold - self.gold_to_keep)        

    def DepositItems(self):
        # selling so no deposit
        if self.sellItems:
            return
        
        if not self.action_timer.IsRunning():
            self.action_timer.Start()

        if not self.action_timer.HasElapsed(250):
            return
        
        self.action_timer.Reset()

        items, space = Inventory.GetStorageSpace()

        if items == space:
            return True

        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        items_to_deposit = ItemArray.GetItemArray(bags_to_check)

        banned_models = {Items.Id_Kit_Basic,Items.Salve_Kit_Basic}
        items_to_deposit = ItemArray.Filter.ByCondition(items_to_deposit, lambda item_id: Item.GetModelID(item_id) not in banned_models)

        if len(items_to_deposit) > 0:
            Inventory.DepositItemToStorage(items_to_deposit[0])

    def DepositItemsComplete(self):
        # selling so no deposit
        if self.sellItems:
            return True        
        
        if not self.stop_action_timer.IsRunning():
            self.stop_action_timer.Start()

        if not self.stop_action_timer.HasElapsed(250):
            return
                
        self.stop_action_timer.Reset()

        items, space = Inventory.GetStorageSpace()

        if items == space:
            return True

        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        items_to_deposit = ItemArray.GetItemArray(bags_to_check)

        banned_models = {Items.Id_Kit_Basic,Items.Salve_Kit_Basic}
        items_to_deposit = ItemArray.Filter.ByCondition(items_to_deposit, lambda item_id: Item.GetModelID(item_id) not in banned_models)

        if len(items_to_deposit) == 0:
            self.stop_action_timer.Stop()
            return True

        return False

    def IdentifyItems(self): 
        if not self.idItems:
            return True
        
        if not self.action_timer.IsRunning():
            self.action_timer.Start()

        if not self.action_timer.HasElapsed(250):
            return
                
        self.action_timer.Reset()

        id_kit = Inventory.GetFirstIDKit()

        if id_kit == 0:
            self.jump_to_state_by_name(self.inventory_buy_id_kits)
            return

        unidentified_items = self.FilterItemsToId()
        
        if len(unidentified_items) > 0:
            Inventory.IdentifyItem(unidentified_items[0], id_kit)

    def IdentifyItemsComplete(self):                    
        if not self.idItems:
            return True
        
        if not self.stop_action_timer.IsRunning():
            self.stop_action_timer.Start()

        if self.stop_action_timer.HasElapsed(250):
            self.stop_action_timer.Reset()

            unidentified_items = self.FilterItemsToId()

            if len(unidentified_items) == 0:
                self.stop_action_timer.Stop()
                return True
            
        return False
    
    def FilterItemsToId(self):
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        unidentified_items = ItemArray.GetItemArray(bags_to_check)
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: Item.Usage.IsIdentified(item_id) == False)
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: Item.Rarity.IsWhite(item_id) == False)

        return unidentified_items

    def Reset(self):
        if self.get_state_count() > 0:
            self.reset()
        
        self.action_timer.Stop()

        # resetting to 1 to prev
        self.sell_item_count = -1

        if self.merchant_path:
            self.merchant_path.reset()

        if self.movement_handler:
            self.movement_handler.reset()

def ChangeWeaponSet(set):
    if set == 1:
        Keystroke.PressAndRelease(Key.F1.value)
    elif set == 2:
        Keystroke.PressAndRelease(Key.F2.value)
    elif set == 3:
        Keystroke.PressAndRelease(Key.F3.value)
    elif set == 4:
        Keystroke.PressAndRelease(Key.F4.value)

def CheckWeaponEquipped(weapon, logFunc=None):
    equipped = Agent.GetWeaponType(Player.GetAgentID())

    #if logFunc:
        #logFunc(f"Equipped: Int{equipped[0]}, Name{equipped[1]}")
    return equipped == weapon

def TargetNearestNpc():
    npc_array = AgentArray.GetNPCMinipetArray()
    npc_array = AgentArray.Filter.ByDistance(npc_array,Player.GetXY(), 200)
    npc_array = AgentArray.Sort.ByDistance(npc_array, Player.GetXY())

    if len(npc_array) > 0:
        Player.ChangeTarget(npc_array[0])

        
def CheckIfInventoryHasItem(itemModelId):
    bags = ItemArray.CreateBagList(1,2,3,4)

    for bag_enum in bags:
        try:
            # Create a Bag instance
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            # Get all items in the bag
            items_in_bag = bag_instance.GetItems()

            for item in items_in_bag:
                if item.model_id == itemModelId:
                    return True
        except Exception as e:
            Py4GW.Console.Log("Utilities", f"GetInventoryHasItem: {str(e)}", Py4GW.Console.MessageType.Error)

    return False

def GetItemIdFromModelId(itemModelId):
    bags = ItemArray.CreateBagList(1,2,3,4)

    for bag_enum in bags:
        try:
            # Create a Bag instance
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            # Get all items in the bag
            items_in_bag = bag_instance.GetItems()

            for item in items_in_bag:
                if item.model_id == itemModelId:
                    return item.item_id
        except Exception as e:
            Py4GW.Console.Log("Utilities", f"GetItemIdFromModelId: {str(e)}", Py4GW.Console.MessageType.Error)

    return 0

'''
    keepItems should be [modelId] regardless of slot
'''
def GetInventoryNonKeepItemsByModelId(keepItems = [], input = None):
    if isinstance(input, list):
        items = input
    else:
        items = GetItems(ItemArray.CreateBagList(1, 2, 3, 4))

    sell_items = []

    for item in items:
        model = Item.GetModelID(item.item_id)

        if model in keepItems:
            if model != Items.Dye:
                continue
            else:
                itemAgent = Agent.GetItemAgent(item.agent_id)

                if itemAgent:
                    if itemAgent.extra_type == Items.Dye.Black_Dye or itemAgent.extra_type == Items.Dye.White_Dye:
                        continue
            
        sell_items.append(item)

    return sell_items

'''
    keepSlots should be [bagNum, slots].
'''
def GetInventoryNonKeepItemsByBagSlot(keepSlots = [], logFunc = None):    
    all_item_ids = []  # To store item IDs from all bags

    bags = ItemArray.CreateBagList(1, 2, 3, 4)

    if logFunc != None:
        logFunc(f"{type(keepSlots)}")

    try:
        for bag_enum in bags:
            # Create a Bag instance
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            # Get all items in the bag
            items_in_bag = bag_instance.GetItems()

            for (keepBag, keeps) in keepSlots:
                if keepBag == bag_enum.value:
                    if isinstance(keeps, list):
                    # this is a slot in the bag
                        for item in items_in_bag:
                            # this item slot not in the keeps pile, so mark it for sale
                            if item.slot not in keeps:
                                all_item_ids.append(item)

    except Exception as e:
        Py4GW.Console.Log("GetInventoryItemsToSellByBagSlot", f"error in function: {str(e)}", Py4GW.Console.MessageType.Error)

    return all_item_ids

def GetItemIdList(input):
    if not isinstance(input, list):
        return

    item_id_list = []

    for item in input:
        item_id_list.append(item.item_id)
        
    return item_id_list

def GetItems(bags):
    all_item_ids = []  # To store item IDs from all bags

    for bag_enum in bags:
        try:
            # Create a Bag instance
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            # Get all items in the bag
            items_in_bag = bag_instance.GetItems()
        
            all_item_ids.extend(items_in_bag)
        
        except Exception as e:
            Py4GW.Console.Log("Utilities", f"GetItems: {str(e)}", Py4GW.Console.MessageType.Error)

    return all_item_ids

def GetItemBagSlotList(bags):
    all_item_ids = []  # To store item IDs from all bags

    for bag_enum in bags:
        try:
            # Create a Bag instance
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            # Get all items in the bag
            items_in_bag = bag_instance.GetItems()
            
            slots = []

            for item in items_in_bag:
                slots.append(item.slot)

            # output should be [int, list]
            all_item_ids.append((bag_enum.value, slots))
                
        except Exception as e:
            Py4GW.Console.Log("Utilities", f"GetItemBagSlotList: {str(e)}", Py4GW.Console.MessageType.Error)

    return all_item_ids

def CheckIfKeepItemsInInventory(keepItems = [], bagSlots = []):
    if bagSlots == None:
        bagSlots = GetItemBagSlotList(ItemArray.CreateBagList(1,2,3,4))

    for bag, items in bagSlots:
        pass


def GetInventoryItemSlots(bags=None):
    if bags == None:
        bags = ItemArray.CreateBagList(1, 2, 3, 4)

    all_item_ids = []  # To store item IDs from all bags [bagNum, slotNum]

    for bag_enum in bags:
        try:
            # Create a Bag instance
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            # Get all items in the bag
            items_in_bag = bag_instance.GetItems()

            slots = []

            for item in items_in_bag:
                slots.append(item.slot)

            # output should be [int, list]
            all_item_ids.append((bag_enum.value, slots))
        
        except Exception as e:
            Py4GW.Console.Log("Utilities", f"GetInventoryItemSlots: {str(e)}", Py4GW.Console.MessageType.Error)

    return all_item_ids

from Py4GWCoreLib import *
from WindowUtilites import *

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

class Professions:
    class Name:
        Assassin = "Assassin"
        Dervish = "Dervish"
        Elementalist = "Elementalist"
        Mesmer = "Mesmer"
        Monk = "Monk"
        Necromancer = "Necromancer"
        Paragon = "Paragon"
        Ranger = "Ranger"
        Ritualist = "Ritualist"
        Warrior = "Warrior"

    class Id:        
        NoProfession: int = 0
        Warrior: int = 1
        Ranger: int = 2
        Monk: int = 3
        Necromancer: int = 4
        Mesmer: int = 5
        Elementalist: int = 6
        Assassin: int = 7
        Ritualist: int = 8
        Paragon: int = 9
        Dervish: int = 10

class GameAreas:
    Touch = 144
    Adjacent = 166
    Nearby = 252
    Area = 322
    Far_Area = 650
    Lesser_Earshot = 900
    Earshot = 1012 
    Spellcast = 1248
    Great_Spellcast = 1450
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

"""
Queue that is synchronized with game by connection ping.

Actions are executed in FIFO only when last recorded maximum ping has elapsed (tests every call)
"""
class SynchronizedActionQueue:
    def __init__(self, logFunc):
        """Initialize the action queue."""
        self.queue = deque() # Use deque for efficient FIFO operations        
        self.action_queue_timer = Timer()
        self.action_queue_timer.Start()
        self.ping_handler = Py4GW.PingHandler() # Use pinghandler to sync with game
        self.logFunc = logFunc

    def add_action(self, action, *args, **kwargs):
        """
        Add an action to the queue.

        :param action: Function to execute.
        :param args: Positional arguments for the function.
        :param kwargs: Keyword arguments for the function.
        """
        self.queue.append((action, args, kwargs))
        
    def execute_next(self):
        """Execute the next action in the queue."""
        if self.queue:
            action, args, kwargs = self.queue.popleft()
            action(*args, **kwargs)
            
    def is_empty(self):
        """Check if the action queue is empty."""
        return not bool(self.queue)
    
    def clear(self):
        """Clear all actions from the queue."""
        self.queue.clear()

    def count(self):
        return self.queue.count
    
    def log(self, text):
        if self.logFunc:
            self.logFunc(text)

aftercast = aftercast_class()

### --- ITEMS --- ###
EventItems_Array = [(ModelID.Champagne_Popper), (ModelID.Krytan_Brandy), (ModelID.Hunters_Ale), 
                    (ModelID.Bottle_Rocket), (ModelID.Hard_Apple_Cider), (ModelID.Birthday_Cupcake), (ModelID.Shamrock_Ale), 
                    (ModelID.Four_Leaf_Clover), (ModelID.Bottle_Of_Grog),  (ModelID.Sugary_Blue_Drink), (ModelID.Wintergreen_Candy_Cane),
                    (ModelID.Victory_Token), (ModelID.Snowman_Summoner), (ModelID.Ghost_In_The_Box), 
                    (ModelID.Vial_Of_Absinthe), (ModelID.Squash_Serum), (ModelID.Eggnog), (ModelID.Spiked_Eggnog), 
                    (ModelID.Candy_Corn), (ModelID.Candy_Apple),  (ModelID.Pumpkin_Cookie), (ModelID.Trick_Or_Treat_Bag), 
                    (ModelID.Fruitcake), (ModelID.Peppermint_Candy_Cane), (ModelID.Rainbow_Candy_Cane), (ModelID.Honeycomb), 
                    (ModelID.Wintersday_Gift), (ModelID.Yuletide_Tonic), (ModelID.Lunar_Token), (ModelID.Candy_Cane_Shard), 
                    (ModelID.Golden_Egg), (ModelID.Slice_Of_Pumpkin_Pie), (ModelID.Lunar_Fortune_2007_Pig), 
                    (ModelID.Lunar_Fortune_2008_Rat), (ModelID.Lunar_Fortune_2009_Ox), (ModelID.Lunar_Fortune_2010_Tiger), 
                    (ModelID.Lunar_Fortune_2011_Rabbit), (ModelID.Lunar_Fortune_2012_Dragon), (ModelID.Lunar_Fortune_2013_Snake), 
                    (ModelID.Lunar_Fortune_2014_Horse), (ModelID.Lunar_Fortune_2015_Sheep), (ModelID.Lunar_Fortune_2016_Monkey), 
                    (ModelID.Lunar_Fortune_2017_Rooster), (ModelID.Lunar_Fortune_2018_Dog)]

IdKits = [ModelID.Identification_Kit, ModelID.Superior_Identification_Kit]
SalveKits = [ModelID.Salvage_Kit, ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit]
IdSalveItems_Array = []
IdSalveItems_Array.extend(IdKits)
IdSalveItems_Array.extend(SalveKits)

def TargetNearestItem():
    items = AgentArray.GetItemArray()
    items = AgentArray.Filter.ByDistance(items,Player.GetXY(), 200)
    items = AgentArray.Sort.ByDistance(items, Player.GetXY())
    if len(items) > 0:        
        Player.ChangeTarget(items[0])

def TargetNearestEnemy(area:int=GameAreas.Lesser_Earshot)->None:
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')
    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), area)
    enemies = AgentArray.Sort.ByDistance(enemies, Player.GetXY())

    if len(enemies) > 0:
        Player.ChangeTarget(enemies[0])

def GetNearestEnemy(area: int = GameAreas.Area) -> int:
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')
    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), area)
    enemies = AgentArray.Sort.ByDistance(enemies, Player.GetXY())

    if len(enemies) > 0:
        return enemies[0]
    
    # No enemies matching criteria
    return 0

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

# def HasEnoughAdrenaline(skill_id):
#     player_agent_id = Player.GetAgentID()
#     adrenaline = Skill.Data.GetAdrenaline(skill_id)
#     max_adrenaline = Player.GetAdrenaline(player_agent_id)
#     return adrenaline <= max_adrenaline

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

def CastSkillByIdAndSlot(skill_id: int, slot: int) -> None:
    global aftercast
    SkillBar.UseSkill(slot)
    aftercast.set_aftercast(skill_id)

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

def IsEnemyBehind(agent_id) -> bool:
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

    if angle_diff > 90 and angle_diff < 270:
        return True
    return False

def CheckSurrounded(number_foes, area=GameAreas.Lesser_Earshot):
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, Player.GetXY(), area)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    return len(enemy_array) > number_foes

def IsEnemyModelInRange(model_id: int, range: int=GameAreas.Earshot) -> bool:
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), range)
    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')
    enemies = AgentArray.Sort.ByDistance(enemies, Player.GetXY())

    for enemy in enemies:
        if Agent.GetModelID(enemy) == model_id:
            return True
    return False

def IsEnemyModelListInRange(model_ids: list, range: int=GameAreas.Earshot) -> bool:
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), range)
    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')
    enemies = AgentArray.Sort.ByDistance(enemies, Player.GetXY())

    for enemy in enemies:
        if Agent.GetModelID(enemy) in model_ids:
            return True
    return False

def GetNearestEnemyByModelId(model_id: int, range: int=GameAreas.Earshot) -> int:
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), range)
    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')
    enemies = AgentArray.Sort.ByDistance(enemies, Player.GetXY())

    for enemy in enemies:
        if Agent.GetModelID(enemy) == model_id:
            return enemy
    return 0

def GetNearestEnemyByModelIdList(model_ids: list, range: int=GameAreas.Earshot) -> int:
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), range)
    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')
    enemies = AgentArray.Sort.ByDistance(enemies, Player.GetXY())

    for enemy in enemies:
        if Agent.GetModelID(enemy) in model_ids:
            return enemy
    return 0

def TargetNearestEnemyByModelId(model_id: int, range: int=GameAreas.Earshot):
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), range)
    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')
    enemies = AgentArray.Sort.ByDistance(enemies, Player.GetXY())

    for enemy in enemies:
        if Agent.GetModelID(enemy) == model_id:
            Player.ChangeTarget(enemy)
            break

def GetTargetNearestEnemyByModelId(model_id: int, range: int=GameAreas.Earshot) -> int:
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), range)
    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')
    enemies = AgentArray.Sort.ByDistance(enemies, Player.GetXY())

    for enemy in enemies:
        if Agent.GetModelID(enemy) == model_id:
            Player.ChangeTarget(enemy)
            return enemy
    return 0

def GetTargetNearestEnemyByModelIdList(model_ids: list, range: int=GameAreas.Earshot) -> int:
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), range)
    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')
    enemies = AgentArray.Sort.ByDistance(enemies, Player.GetXY())

    for enemy in enemies:
        if Agent.GetModelID(enemy) in model_ids:
            Player.ChangeTarget(enemy)
            return enemy
    return 0

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
    leave_party = True
    
    default_min_slots = 3
    player_stuck = False

    def __init__(self, window, inventory_map, inventory_merchant_position, keep_slots, keep_models):
        if issubclass(type(window), BasicWindow):
            self.window = window

        self.keep_slots = keep_slots
        self.keep_models = keep_models
        self.inventoryRoutine = InventoryFsm(window, "Basic_Inventory_Routine", inventory_map, 
                                        inventory_merchant_position, keep_slots, 
                                        keep_models, logFunc=self.Log)
            
    def UpdateState(self, state):
        if issubclass(type(self.window), BasicWindow):
            self.window.UpdateState(state)

    def PrintData(self):
        if self.keep_slots != None:
            totalSlotsFull = 0
            for (bag, slots) in self.keep_slots:
                if isinstance(slots, list):
                    totalSlotsFull += len(slots)
                    for slot in slots:
                        self.Log(f"Bag: {bag}, Slot: {slot}")
            self.Log(f"Total Slots Full: {totalSlotsFull}")

    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if issubclass(type(self.window), BasicWindow):
            self.window.Log(text, msgType)

    def CanPickUp(self, agentId, player_id):
        # Need to make sure that if inventory is full, check if the item is stackable and there is a stack in inventory with space.
        agent = Agent.GetAgentByID(agentId)

        if agent:

            item_id = Agent.GetItemAgentItemID(agentId)
            if Agent.GetItemAgentOwnerID(agentId) != 0 and player_id != 0 and Agent.GetItemAgentOwnerID(agentId) != player_id:
                return False
            
            model = Item.GetModelID(item_id)

            if model == ModelID.Gold_Coins and self.collect_gold_coins:
                # Check should collect gold coins and this is gold coins
                onHand = Inventory.GetGoldOnCharacter()
                return onHand <= 99500
            elif model == ModelID.Lockpick: # Just always pick these up for now
                return True
            elif model == ModelID.Vial_Of_Dye and self.collect_dye_white_black:
                dye = Item.GetDyeColor(item_id)
                return dye == DyeColor.Black or dye == DyeColor.White
            elif self.collect_event_items and model in EventItems_Array:
                # Check should collect event items and this is event item
                return True
            else:
                # Check should collect color items and this is color item
                return (Item.Rarity.IsWhite(item_id) and self.collect_white_items) or \
                        (Item.Rarity.IsBlue(item_id) and self.collect_blue_items) or \
                        (Item.Rarity.IsPurple(item_id) and self.collect_grape_items) or \
                        (Item.Rarity.IsGold(item_id) and self.collect_gold_items) or \
                        (Item.Rarity.IsGreen(item_id) and self.collect_green_items)
            
        return False

    def GetNearestPickupItem(self, player_id):
        try:            
            items = AgentArray.GetItemArray()
            items = AgentArray.Filter.ByDistance(items, Player.GetXY(), GameAreas.Lesser_Earshot)
            items = AgentArray.Sort.ByDistance(items, Player.GetXY())

            if items != None and len(items) > 0:
                for item in items:
                    if self.CanPickUp(item, player_id):
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
            self.step_transition_threshold_timer.Stop()
        return elapsed
    
    def ApplyConfigSettings(self, leave_party, collect_input) -> None:
        self.leave_party = leave_party
        self.main_item_collect = collect_input

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
    
    def ApplyInventorySettings(self, min_slots, min_gold, depo_items, depo_mats):
        self.default_min_slots = min_slots

        self.inventoryRoutine.ApplyInventorySettings(min_gold, depo_items, depo_mats)
        self.default_min_gold = min_gold
        self.deposit_items = depo_items
        self.deposit_mats = depo_mats

    def GetMinimumSlots(self) -> int:
        return self.default_min_slots    
    
### --- REPORTS PROGRESS --- ###

### --- SALVAGE ROUTINE --- ###
class SalvageFsm(FSM):
    inventoryHandler = PyInventory.PyInventory()   
    salvage_Items = []
    current_salvage = 0
    current_quantity = 0
    current_ping = 0
    default_base_ping = 100
    default_base_wait_no_ping = 350
    pending_stop = False
    salvage_kit = False
    needs_confirm = False

    salvager_start = "Start Salvage"
    salvager_continue = "Using Salvage Kit"
    salvager_ping_check_1 = "Salvaging"
    salvager_finish = "Finish Salvage"

    def __init__(self, window=BasicWindow(), name="SalvageFsm", logFunc=None, pingHandler=Py4GW.PingHandler()):
        super().__init__(name)

        self.window = window
        self.name = name
        self.logFunc = logFunc
        self.pingHandler = pingHandler        
        self.ping_timer = Timer()
        
        self.AddState(self.salvager_start,
                      execute_fn=lambda: self.ExecuteStep(self.salvager_start, self.SetMaxPing()),
                      transition_delay_ms=150)
        self.AddState(self.salvager_continue,
                        execute_fn=lambda: self.ExecuteStep(self.salvager_continue, self.StartSalvage()),
                        transition_delay_ms=150)
        self.AddState(self.salvager_ping_check_1,
                        execute_fn=lambda: self.ExecuteStep(self.salvager_ping_check_1, None),
                        exit_condition=lambda: self.CheckPingContinue(),
                        run_once=False)
        self.AddState(self.salvager_finish,
                        execute_fn=lambda: self.EndSalvageLoop(),
                        transition_delay_ms=150)
    
    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if isinstance(self.window, BasicWindow):            
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
        if isinstance(self.window, BasicWindow):
            self.window.UpdateState(state)

    def IsExecuting(self):
        return self.is_started() and not self.is_finished()
    
    def SetMaxPing(self):        
        if self.pingHandler:
            self.current_ping = self.pingHandler.GetMaxPing()

    def CheckPingContinue(self):
        if self.ping_timer:
            if not self.ping_timer.IsRunning():
                self.ping_timer.Start()

            if not self.ping_timer.HasElapsed(self.current_ping*2):
                return False
            
            self.ping_timer.Stop()
        return True

    def SetSalvageItems(self, salvageItems):
        self.salvage_Items = salvageItems
        
    def GetSalvageItemCount(self) -> int:
        return len(self.salvage_Items)

    def StartSalvage(self):
        kitId = Inventory.GetFirstSalvageKit()
        
        if kitId == 0:
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

        Inventory.SalvageItem(self.current_salvage, kitId)
        
    def EndSalvageLoop(self):
        Inventory.AcceptSalvageMaterialsWindow()

        if not self.salvage_kit or self.pending_stop:
            try:
                if self.window:
                    self.window.DoneSalvaging(False)
            except:
                pass  

            return
        
        if not self.IsFinishedSalvage():   
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
        if self.current_salvage != 0:
            self.current_quantity -= 1

            if self.current_quantity <= 0:
                self.current_salvage = 0
        
        kitId = Inventory.GetFirstSalvageKit()
        
        if kitId == 0:
            self.Log("No Salvage Kit")
            self.salvage_kit = False
            return True

        return len(self.salvage_Items) == 0
        
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
    default_wait_no_ping = 500
    default_wait_ping = 100
    deposit_mats = False
    deposit_items = False

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
    inventory_check_salve_more = "More to Salvage?"
    inventory_deposit_items = "Deposit Items"

    action_timer = Timer()
    stop_action_timer = Timer()    
    movement_handler = Routines.Movement.FollowXY(50)

    salvager_name = "SalvageFsm"

    # keeps list of inventory at time of creation, ensuring not to sell those items.
    current_Inventory = []

    # keeps the listed model ids in inventory, ensuring not to sell those items
    keep_items = []

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
        
        self.ping_handler = Py4GW.PingHandler()
        self.salvager = SalvageFsm(self.window, self.salvager_name, self.logFunc, self.ping_handler)

        self.AddState(name=self.inventory_setup_salv,
            execute_fn=lambda: self.ExecuteStep(self.inventory_setup_salv, self.SetupSalvageRoutine()),
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
        
        self.AddState(name=self.inventory_buy_salve_kits,
            execute_fn=lambda: self.ExecuteStep(self.inventory_buy_salve_kits, self.BuySalvageKits()),
            run_once=False,
            exit_condition=lambda: self.BuySalvageKitsComplete())    
    
        self.AddSubroutine(name=self.inventory_salv_items,
            sub_fsm = self.salvager,
            condition_fn=lambda: self.salvageItems and self.salvager.GetSalvageItemCount() > 0)
        
        self.AddState(name=self.inventory_check_salve_more,
            execute_fn=lambda: self.ExecuteStep(self.inventory_check_salve_more, self.CheckMoreSalvageItems()))
                
        self.AddState(name=self.inventory_sell_items,
            execute_fn=lambda: self.ExecuteStep(self.inventory_sell_items, self.SellItems()),
            run_once=False,
            exit_condition=lambda: self.SellItemsComplete())
                
        self.AddState(name=self.inventory_sell_materials_2,
            execute_fn=lambda: self.ExecuteStep(self.inventory_sell_materials_2, self.SellMaterials()),
            run_once=False,
            exit_condition=lambda: self.SellingMaterialsComplete())
        
        self.AddState(name=self.inventory_deposit_items,
            execute_fn=lambda: self.ExecuteStep(self.inventory_deposit_items, self.DepositItems()),
            run_once=False,
            exit_condition=lambda: self.DepositItemsComplete())
        
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

    def ApplyInventorySettings(self, min_gold, depo_items, depo_mats):
        self.gold_to_keep = min_gold
        self.deposit_items = depo_items
        self.deposit_mats = depo_mats
            
    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if not self.logFunc:
            return
        self.logFunc(text, msgType)

    def UpdateState(self, state):
        if isinstance(self.window, BasicWindow):
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
    
    def CheckMoreSalvageItems(self):
        items = self.GetInventorySalvageItems()

        if len(items) > 0:
            # Either out of space or out of salvage kits
            if Inventory.GetFreeSlotCount() == 0:
                return
            else:
                salv = Inventory.GetFirstSalvageKit()

                if salv == 0:
                    self.jump_to_state_by_name(self.inventory_buy_salve_kits)
                else:
                    self.jump_to_state_by_name(self.inventory_salv_items)

    def SellItems(self):
        if not self.sellItems:
            return
        
        if not self.action_timer.IsRunning():
            self.action_timer.Start()
        
        if not self.action_timer.HasElapsed(self.GetCurrentPing()):
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

        if not self.action_timer.HasElapsed(self.GetCurrentPing()):
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

        if not self.action_timer.HasElapsed(self.GetCurrentPing()):
            return
        
        self.action_timer.Reset()

        kits_in_inv = Inventory.GetFirstIDKit()

        if kits_in_inv == 0:
            merchant_item_list = Trading.Merchant.GetOfferedItems()
            merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: Item.GetModelID(item_id) == ModelID.Superior_Identification_Kit)

            # if no superior, just go with basic since merchant will have that.
            if len(merchant_item_list) == 0:
                merchant_item_list = Trading.Merchant.GetOfferedItems()
                merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: Item.GetModelID(item_id) == ModelID.Identification_Kit)

            if len(merchant_item_list) > 0:
                item_id = merchant_item_list[0]
                value = Item.Properties.GetValue(item_id) * 2 # value is reported is sell value not buy value
                Trading.Merchant.BuyItem(item_id, value)
            else:
                Py4GW.Console.Log("Buy ID Kits", f"No ID kits available from merchant.",Py4GW.Console.MessageType.Info)        

    def BuyIdKitsComplete(self):
        if not self.idItems:
            return True
        
        kits_in_inv = Inventory.GetFirstIDKit()

        if kits_in_inv >= 1:
            self.action_timer.Stop()
            return True

        return False

    def BuySalvageKits(self):
        if not self.salvageItems:
            return
        
        if not self.action_timer.IsRunning():
            self.action_timer.Start()

        if not self.action_timer.HasElapsed(self.GetCurrentPing()):
            return
        
        self.action_timer.Reset()
        
        kits_in_inv = Inventory.GetModelCount(ModelID.Salvage_Kit)

        if kits_in_inv <= 1:
            merchant_item_list = Trading.Merchant.GetOfferedItems()
            merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: Item.GetModelID(item_id) == ModelID.Salvage_Kit)

            item_id = merchant_item_list[0]
            quantity = Item.Properties.GetQuantity(item_id)
            value = Item.Properties.GetValue(item_id) *2 # value is reported is sell value not buy value
            Trading.Merchant.BuyItem(item_id, value)

    def BuySalvageKitsComplete(self):
        if not self.salvageItems:
            return True
        
        kits_in_inv = Inventory.GetModelCount(ModelID.Salvage_Kit)

        if kits_in_inv >= 1:
            self.action_timer.Stop()
            return True

        return False

    def CheckGold(self):
        charGold = Inventory.GetGoldOnCharacter()

        dif = self.gold_to_keep - charGold
        
        if dif > 0:
            Inventory.WithdrawGold(dif)
        elif dif < 0:
            Inventory.DepositGold(-dif)

    def DepositItems(self):
        # selling so no deposit
        if self.sellItems:
            return
        
        if not self.action_timer.IsRunning():
            self.action_timer.Start()

        if not self.action_timer.HasElapsed(self.GetCurrentPing()):
            return
        
        self.action_timer.Reset()

        items, space = Inventory.GetStorageSpace()

        if items == space:
            return True

        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        items_to_deposit = ItemArray.GetItemArray(bags_to_check)

        items_to_deposit = ItemArray.Filter.ByCondition(items_to_deposit, lambda item_id: Item.GetModelID(item_id) not in IdSalveItems_Array)

        if len(items_to_deposit) > 0:
            Inventory.DepositItemToStorage(items_to_deposit[0])

    def DepositItemsComplete(self):
        # selling so no deposit
        if self.sellItems:
            return True        
        
        if not self.stop_action_timer.IsRunning():
            self.stop_action_timer.Start()

        if not self.stop_action_timer.HasElapsed(self.GetCurrentPing()):
            return
                
        self.stop_action_timer.Reset()

        items, space = Inventory.GetStorageSpace()

        if items == space:
            return True

        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        items_to_deposit = ItemArray.GetItemArray(bags_to_check)

        items_to_deposit = ItemArray.Filter.ByCondition(items_to_deposit, lambda item_id: Item.GetModelID(item_id) not in IdSalveItems_Array)

        if len(items_to_deposit) == 0:
            self.stop_action_timer.Stop()
            return True

        return False

    def IdentifyItems(self): 
        if not self.idItems:
            return True
        
        if not self.action_timer.IsRunning():
            self.action_timer.Start()

        if not self.action_timer.HasElapsed(self.GetCurrentPing()):
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

        if self.stop_action_timer.HasElapsed(self.GetCurrentPing()):
            self.stop_action_timer.Reset()

            unidentified_items = self.FilterItemsToId()

            if len(unidentified_items) == 0:
                self.stop_action_timer.Stop()
                self.current_ping = 0
                return True
            
        return False
    
    def FilterItemsToId(self):
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        unidentified_items = ItemArray.GetItemArray(bags_to_check)
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: Item.Usage.IsIdentified(item_id) == False)
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: Item.Rarity.IsWhite(item_id) == False)

        return unidentified_items

    def GetCurrentPing(self):
            if self.ping_handler:
                return self.default_wait_ping + self.ping_handler.GetMaxPing() * 2
            else:
                return self.default_wait_no_ping

    def Reset(self):
        if self.get_state_count() > 0:
            self.reset()
        self.salvager.reset()
        self.action_timer.Stop()

        # resetting to 1 to prev
        self.sell_item_count = -1

        if self.merchant_path:
            self.merchant_path.reset()

        if self.movement_handler:
            self.movement_handler.reset()

def GetDistance(agent_1, agent_2):
    agent_1_x, agent_1_y = Agent.GetXY(agent_1)
    agent_2_x, agent_2_y = Agent.GetXY(agent_2)
    distance = Utils.Distance((agent_1_x, agent_1_y), (agent_2_x, agent_2_y))
    return distance

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

def CheckIfInventoryHasItem(itemModelId, count=1):
    bags = ItemArray.CreateBagList(1,2,3,4)

    testCount = 0
    for bag_enum in bags:
        try:
            # Create a Bag instance
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            # Get all items in the bag
            items_in_bag = bag_instance.GetItems()

            for item in items_in_bag:
                if item.model_id == itemModelId:
                    testCount += item.quantity

                    if testCount >= count:
                        return True
        except Exception as e:
            Py4GW.Console.Log("Utilities", f"GetInventoryHasItem: {str(e)}", Py4GW.Console.MessageType.Error)

    return False

def GetItemIdFromModelId(itemModelId, min_count = 1):
    bags = ItemArray.CreateBagList(1,2,3,4)

    count = 0
    itemIds = []

    for bag_enum in bags:
        try:
            # Create a Bag instance
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            # Get all items in the bag
            items_in_bag = bag_instance.GetItems()

            for item in items_in_bag:
                if item.model_id == itemModelId:
                    if item.quantity >= min_count:
                        itemIds.append(item.item_id)
                        return itemIds
                    else:
                        count += item.quantity
                        itemIds.append(item.item_id)

                        if count >= min_count:
                            return itemIds
        except Exception as e:
            Py4GW.Console.Log("Utilities", f"GetItemIdFromModelId: {str(e)}", Py4GW.Console.MessageType.Error)

    return 0

def GetModelIdCount(model_id):
    bags = ItemArray.CreateBagList(1,2,3,4)

    count = 0
    for bag_enum in bags:
        try:
            # Create a Bag instance
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            # Get all items in the bag
            items_in_bag = bag_instance.GetItems()
                        
            for item in items_in_bag:
                if item.model_id == model_id:
                    count += item.quantity
        except Exception as e:
            Py4GW.Console.Log("Utilities", f"GetItemIdFromModelId: {str(e)}", Py4GW.Console.MessageType.Error)

    return count
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
            if model != ModelID.Vial_Of_Dye:
                continue
            else:
                extra_type = Agent.GetItemAgentExtraType(item.agent_id)

                if extra_type:
                    if extra_type == DyeColor.Black or extra_type == DyeColor.White:
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

def GetInventorySalvageKitCount(bags=None) -> int:
    if bags == None:
        bags = ItemArray.CreateBagList(1,2,3,4)

    quantity = 0

    for bag_enum in bags:
        try:
            # Create a Bag instance
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            # Get all items in the bag
            items_in_bag = bag_instance.GetItems()

            for item in items_in_bag:
                if item.model_id in SalveKits:
                    quantity += item.quantity
        
        except Exception as e:
            Py4GW.Console.Log("Utilities", f"GetInventoryItemSlots: {str(e)}", Py4GW.Console.MessageType.Error)

    return quantity

# def GetDyeColorIdFromItem(item_id: int) -> int:
#     modifiers = Item.Customization.Modifiers.GetModifiers(item_id)
#     Item.GetItemType(item_id)
#     for mod in modifiers:
#         modColor = mod.GetArg1()
        
#         if modColor != 0:
#             return modColor
        
#     return 0

    
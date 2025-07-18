# region imports
from Py4GWCoreLib import *
from random import randint
from datetime import datetime
# endregion

# region classes
class Path:
    npc    = [(-19085, 17960)]
    rezone = [(-19665, -8045)]
    prep   = [(-16623, -8989)]
    kill   = [(-15525, -8923), (-15737,-9093)]

class BotVariables:
    bot_started: bool  = False
    do_setup: bool     = True
    action_queue       = ActionQueue()
    fsm                = FSM('Bone Farmer')
    fsm_setup          = FSM('Setup')
    fsm_inv            = FSM('Inventory')
    move               = Routines.Movement.FollowXY()
    exact_move         = Routines.Movement.FollowXY(tolerance=5)
    
    class Maps:
        starting: int = 648
        dungeon: int  = 560

    class Path:
        npc    = Routines.Movement.PathHandler(Path.npc)
        rezone = Routines.Movement.PathHandler(Path.rezone)
        prep   = Routines.Movement.PathHandler(Path.prep)
        kill   = Routines.Movement.PathHandler(Path.kill)

        def reset(self):
            self.npc.reset()
            self.rezone.reset()
            self.prep.reset()
            self.kill.reset()

    class Timers:
        throttle: Timer = Timer()
        total: Timer    = Timer()
        lap: Timer      = Timer()
        action: Timer   = Timer()
        settle: Timer   = Timer()
        stuck: Timer    = Timer()

        lap_times: list = []
        throttle.Start()

        class Checks:
            throttle: float = 200
            action: float   = 0
            stuck: float    = 2000

        checks = Checks()

    class Inv:
        empty_slots   = 5
        item_id       = 0
        item_quantity = 0
        log           = {}
        process       = False
        sort_position = 0
        sort_list     = []

    class Opts:
        debug: bool             = True
        build_type: str         = 'mb'

    class Loot:
        salvageables: bool = True
        coins: bool        = True
        picks: bool        = True
        dust: bool         = True
        chalices: bool     = True
        relics: bool       = True

    class Gui:
        window_module = ImGui.WindowModule('Bone Farmer',window_name='CoF Bone Farm',window_pos=(234,802),
                                           window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
        window_pos: tuple[float,float]    = (0,0)
        window_size: tuple[float,float]   = (0,0)
        settings_pos: tuple[int,int]  = (0,0)
        settings_size: tuple[int,int] = (0,0)

        class Stats:
            time: str          = datetime.now().strftime('%H:%M:%S')
            status: str        = 'waiting for input'
            runs: int          = 0
            fails: int         = 0
            avg_time: float    = 0
            bone: int          = 0
            bone_per_hour: int = 0
            starting_bone: int = Inventory.GetModelCount(921)
            total_bone: int    = Inventory.GetModelCount(921)
            gold_coins: int    = 0
            lockpicks: int     = 0
            dust: int          = 0
            iron: int          = 0
            chalices: int      = 0
            relics: int        = 0

        class Opts:
            show_settings: bool        = False
            condense_tables: bool      = False
            color_rows: bool           = True
            show_all: bool             = False

            class Rows:
                runs: bool        = True
                fails: bool       = True
                pace: bool        = True
                lap_time: bool    = False
                total_time: bool  = True
                bones: bool       = True
                bones_hr: bool    = False
                start_bones: bool = False
                total_bones: bool = False
                coins: bool       = False
                picks: bool       = False
                dust: bool        = False
                iron: bool        = False
                chalices: bool    = False
                relics: bool      = False

                def GetRows(self) -> list:
                    return [
                        self.runs,
                        self.fails,
                        self.pace,
                        self.lap_time,
                        self.total_time,
                        self.bones,
                        self.bones_hr,
                        self.start_bones,
                        self.total_bones,
                        self.coins,
                        self.picks,
                        self.dust,
                        self.iron,
                        self.chalices,
                        self.relics
                    ]
            
            rows = Rows()
        
        stats = Stats()
        opts = Opts()
                
    map    = Maps()
    path   = Path()
    timers = Timers()
    inv    = Inv()
    opts   = Opts()
    loot   = Loot()
    gui    = Gui()
    
class Build:
    # template
    def GetTemplate(self,type):
        if type == 'iau':
            return 'OgCjwqpq6SYiihdftXjhOXhX0k'
        elif type == 'mb':
            return 'OgCjkqqLrSYiihdftXjhOXhXxlA'
    # weapon slots
    scythe   = 1
    staff    = 2
    # skills
    soms     = 1
    pf       = 2
    ga       = 3
    vos      = 4
    cv       = 5
    ri       = 6
    vop      = 7
    iau      = 8
    mb       = 8

class Combat:
    def LoadSkillBar(self,template):
        SkillBar.LoadSkillTemplate(template)

    def ChangeWeaponSet(self,set):
        global bot_vars

        if ActionIsPending(): return

        if bot_vars.opts.debug:
            Debug(f'Equipping weapon set [{set}].')

        if   set == 1: Keystroke.PressAndRelease(Key.F1.value)
        elif set == 2: Keystroke.PressAndRelease(Key.F2.value)
        elif set == 3: Keystroke.PressAndRelease(Key.F3.value)
        elif set == 4: Keystroke.PressAndRelease(Key.F4.value)

        SetPendingAction(300)

    def CastSkill(self,skill_slot):
        global bot_vars

        if bot_vars.opts.debug:
            name = Skill.GetName(SkillBar.GetSkillIDBySlot(skill_slot)).replace('_',' ')
            Debug(f'Casting "{name}" in slot [{skill_slot}].')
        key = None
        if   skill_slot == 1: key = Key.One.value
        elif skill_slot == 2: key = Key.Two.value
        elif skill_slot == 3: key = Key.Three.value
        elif skill_slot == 4: key = Key.Four.value
        elif skill_slot == 5: key = Key.Five.value
        elif skill_slot == 6: key = Key.Six.value
        elif skill_slot == 7: key = Key.Seven.value
        elif skill_slot == 8: key = Key.Eight.value

        Keystroke.PressAndRelease(key)

    def CanCast(self):
        player_agent_id = Player.GetAgentID()

        if (Agent.IsCasting(player_agent_id) 
            or Agent.GetCastingSkill(player_agent_id) != 0
            or Agent.IsKnockedDown(player_agent_id)
            or Agent.IsDead(player_agent_id)
            or SkillBar.GetCasting() != 0):
            return False
        return True

    def GetEnergyAgentCost(self,skill_slot):
        skill_id = SkillBar.GetSkillIDBySlot(skill_slot)
        cost = Skill.skill_instance(skill_id).energy_cost

        if cost == 11:
            cost = 15    # True cost is 15
        elif cost == 12:
            cost = 25    # True cost is 25

        cost = max(0, cost)
        return cost

    def HasEnoughAdrenaline(self,skill_slot):
        skill_id = SkillBar.GetSkillIDBySlot(skill_slot)

        return SkillBar.GetSkillData(skill_slot).adrenaline_a >= Skill.Data.GetAdrenaline(skill_id)

    def GetEnergy(self):
        player_agent_id = Player.GetAgentID()
        energy = Agent.GetEnergy(player_agent_id)
        max_energy = Agent.GetMaxEnergy(player_agent_id)
        energy_points = int(energy * max_energy)

        return energy_points

    def HasEnoughEnergy(self,skill_slot):
        player_agent_id = Player.GetAgentID()
        energy = Agent.GetEnergy(player_agent_id)
        max_energy = Agent.GetMaxEnergy(player_agent_id)
        energy_points = int(energy * max_energy)

        return self.GetEnergyAgentCost(skill_slot) <= energy_points
    
    def IsRecharged(self,skill_slot):
        skill = SkillBar.GetSkillData(skill_slot)
        recharge = skill.recharge
        return recharge == 0
    
    def HasBuff(self,agent_id, skill_slot):
        skill_id = SkillBar.GetSkillIDBySlot(skill_slot)

        if Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id):
            return True
        return False
    
    def CheckBuffs(self,buff_list):
        for buff in buff_list:
            if not self.HasBuff(Player.GetAgentID(),buff):
                return False
        return True
    
    def EffectTimeRemaining(self,skill_id):
        for effect in Effects.GetEffects(Player.GetAgentID()):
            if effect.skill_id == skill_id:
                return effect.time_remaining
        return 0
    
    def GetAftercast(self,skill_slot):
        skill_id = SkillBar.GetSkillIDBySlot(skill_slot)

        activation = Skill.Data.GetActivation(skill_id)
        aftercast = Skill.Data.GetAftercast(skill_id)    
        return max(activation*1000 + aftercast*750 + Py4GW.PingHandler().GetCurrentPing() + 50,500)

class ProcessInventory:
    def CheckSlots(self):
        global bot_vars

        if Inventory.GetFreeSlotCount() > bot_vars.inv.empty_slots:
            return False
        else:
            if not bot_vars.inv.log:
                bot_vars.inv.log = Loot().LogInventory([921,929,948])

            return True

    def BuyItem(self,model_id):
        item_array = Trading.Merchant.GetOfferedItems()
        for item in item_array:
            if Item.GetModelID(item) == model_id:
                value = Item.Properties.GetValue(item) * 2

                if bot_vars.opts.debug:
                    Debug(f'Buying ItemID [{item}] for [{value}] gold.')

                Trading.Merchant.BuyItem(item,value)
                break

    def IDInventory(self):
        global bot_vars

        if ActionIsPending():
            return

        kit_id = Inventory.GetFirstIDKit()
        if not kit_id:
            self.BuyItem(2989)
            SetPendingAction(150)
            return False
    
        item_id = Inventory.GetFirstUnidentifiedItem()
        if not item_id:
            if bot_vars.opts.debug:
                Debug(f'Idenfity loop complete.')
            bot_vars.inv.item_id = 0
            return True
        
        if item_id == bot_vars.inv.item_id:
            return False
        
        bot_vars.inv.item_id = item_id
        if bot_vars.opts.debug:
            bag, slot = Inventory.FindItemBagAndSlot(bot_vars.inv.item_id)
            Debug(f'Idenfiying "{Item.GetName(bot_vars.inv.item_id)}" - ItemID [{bot_vars.inv.item_id}] in slot [{bag},{slot}].')
        PyInventory.PyInventory().IdentifyItem(kit_id, bot_vars.inv.item_id)

        return False

    def SalvageInventory(self):
        global bot_vars

        if ActionIsPending():
            return

        kit_id = Inventory.GetFirstSalvageKit()
        if kit_id == 0:
            self.BuyItem(2992)
            SetPendingAction(150)
            return
        
        item_id = Inventory.GetFirstSalvageableItem()
        if item_id == 0:
            if bot_vars.opts.debug:
                Debug(f'Salvage loop complete.')
            bot_vars.inv.item_id = 0
            return True
        
        if item_id == bot_vars.inv.item_id:
            if Item.Rarity.IsPurple(bot_vars.inv.item_id) or Item.Rarity.IsGold(bot_vars.inv.item_id):
                Inventory.AcceptSalvageMaterialsWindow()
            return False
        
        bot_vars.inv.item_id = item_id
        if bot_vars.opts.debug:
           bag, slot = Inventory.FindItemBagAndSlot(bot_vars.inv.item_id)
           Debug(f'Salvaging "{Item.GetName(bot_vars.inv.item_id)}" - ItemID [{bot_vars.inv.item_id}] in slot [{bag},{slot}].')
        PyInventory.PyInventory().Salvage(kit_id, bot_vars.inv.item_id)

        return False

    def GetSellList(self):
        banned_ids = [921,929,933,948,2989,2992,22751]
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)
        item_array = ItemArray.Filter.ByCondition(item_array, lambda item_id: Item.GetModelID(item_id) not in banned_ids)
        item_array = ItemArray.Filter.ByCondition(item_array, lambda item_id: Item.Properties.GetValue(item_id) > 0)
        return item_array

    def SellItem(self):
        global bot_vars

        items_to_sell = self.GetSellList()
        if not items_to_sell:
            return

        bot_vars.inv.item_id = items_to_sell[0]

        if bot_vars.opts.debug:
            bag, slot = Inventory.FindItemBagAndSlot(bot_vars.inv.item_id)
            Debug(f'Selling ItemID [{bot_vars.inv.item_id}] in slot [{bag},{slot}].')

        quantity = Item.Properties.GetQuantity(bot_vars.inv.item_id)
        value = Item.Properties.GetValue(bot_vars.inv.item_id)
        cost = quantity * value
        Trading.Merchant.SellItem(bot_vars.inv.item_id, cost)
        SetPendingAction(randint(300,600))

    def SellLoop(self):
        global bot_vars

        items_to_sell = self.GetSellList()

        if items_to_sell:
            if Inventory.GetItemCount(bot_vars.inv.item_id) == 0:
                bot_vars.fsm_inv.jump_to_state_by_name('selling items')
        else:
            current_inventory = Loot().LogInventory([921,929,948])
            new_inventory = {key: current_inventory[key] - bot_vars.inv.log[key] for key in set(bot_vars.inv.log) & set(current_inventory)}

            bot_vars.gui.stats.gold_coins += new_inventory['gold']
            bot_vars.gui.stats.bone       += new_inventory[921]
            bot_vars.gui.stats.dust       += new_inventory[929]
            bot_vars.gui.stats.iron       += new_inventory[948]

            if bot_vars.timers.total.GetElapsedTime() == 0:
                bot_vars.gui.stats.bone_per_hour = 0
            else:
                bot_vars.gui.stats.bone_per_hour = int(bot_vars.gui.stats.bone*3600000/bot_vars.timers.total.GetElapsedTime())
            bot_vars.gui.stats.total_bone = Inventory.GetModelCount(921)
            bot_vars.inv.log = {}

            if bot_vars.opts.debug:
                Debug('Sell loop complete.')

                Debug('Loot from inventory processing:',            msg_type = 'Notice')
                Debug(f'      Gold coins: {new_inventory['gold']}', msg_type = 'Notice')
                Debug(f'      Bone: {new_inventory[921]}',          msg_type = 'Notice')
                Debug(f'      Dust: {new_inventory[929]}',          msg_type = 'Notice')
                Debug(f'      Iron: {new_inventory[948]}',          msg_type = 'Notice')

            return True
    
        return False
                
    def SortCalculate(self):
        global bot_vars
        sort_algo = [('type_id'  , 29),  # kits
                     ('type_id'  , 18),  # 
                     ('type_id'  , 9),   # 
                     ('type_id'  , 30),  # 
                     ('model_id' , 921), #
                     ('model_id' , 929), #
                     ('model_id' , 933), #
                     ('model_id' , 948)] # iron

        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)
        bot_vars.inv.sort_list = []
        for sorting_type in sort_algo:
            if sorting_type[0] == 'type_id':
                items = ItemArray.Filter.ByCondition(item_array, lambda item_id: Item.GetItemType(item_id)[0] == sorting_type[1])
                bot_vars.inv.sort_list.extend(items)
            elif sorting_type[0] == 'model_id':
                items = ItemArray.Filter.ByCondition(item_array, lambda item_id: Item.GetModelID(item_id) == sorting_type[1])
                bot_vars.inv.sort_list.extend(items)
        bot_vars.inv.sort_position = 0
            
    def SortItem(self):
        global bot_vars

        if ActionIsPending(): return False

        if not bot_vars.inv.sort_list:
            return
        item_id = bot_vars.inv.sort_list[0]

        if bot_vars.inv.sort_position > 34:
            sort_bag = 4
            sort_slot = bot_vars.inv.sort_position - 30
        elif bot_vars.inv.sort_position > 24:
            sort_bag = 3
            sort_slot = bot_vars.inv.sort_position - 25
        elif bot_vars.inv.sort_position > 19:
            sort_bag = 2
            sort_slot = bot_vars.inv.sort_position - 20
        else:
            sort_bag = 1
            sort_slot = bot_vars.inv.sort_position

        item_bag, item_slot = Inventory.FindItemBagAndSlot(item_id)
        if item_bag != sort_bag or item_slot != sort_slot:
            if bot_vars.opts.debug:
                Debug(f'Sorting "{Item.GetName(bot_vars.inv.item_id)}" - ItemID [{item_id}] in slot [{item_bag},{item_slot}] to slot [{sort_bag},{sort_slot}].')

            Inventory.MoveItem(item_id, sort_bag, sort_slot, Item.Properties.GetQuantity(item_id))
            SetPendingAction(randint(300,500))

        bot_vars.inv.sort_list = bot_vars.inv.sort_list[1:]
        bot_vars.inv.sort_position += 1
        
        return

    def SortLoop(self):
        global bot_vars

        if bot_vars.inv.sort_list:
            bot_vars.fsm_inv.jump_to_state_by_name('sorting items')
        else:
            if bot_vars.opts.debug:
                Debug(f'Sort loop complete.')

            if bot_vars.inv.process:
                ResetVariables()
                bot_vars.gui.stats.status = 'waiting for input'

            if bot_vars.inv.process:
                bot_vars.inv.process = False

            return True
        
        return False

class Loot:
    def LogInventory(self,item_ids):
        counts = {}
        counts['gold'] = Inventory.GetGoldOnCharacter()
        salvageables = ItemArray.GetItemArray(ItemArray.CreateBagList(1,2,3,4))
        salvageables = ItemArray.Filter.ByCondition(salvageables, lambda item_id: Item.Usage.IsSalvageable(item_id))
        counts['salv'] = len(salvageables)
        for item_id in item_ids:
            counts[item_id] = Inventory.GetModelCount(item_id)

        return counts
    
    def LogLoot(self):
        curr_inv = self.LogInventory([921,929,22751,24353,24354])
        new_inv  = {key: curr_inv[key] - bot_vars.inv.log[key] for key in set(bot_vars.inv.log) & set(curr_inv)}

        bot_vars.gui.stats.bone       += new_inv[921]
        bot_vars.gui.stats.gold_coins += new_inv['gold']
        bot_vars.gui.stats.lockpicks  += new_inv[22751]
        bot_vars.gui.stats.dust       += new_inv[929]
        bot_vars.gui.stats.chalices   += new_inv[24353]
        bot_vars.gui.stats.relics     += new_inv[24354]

        bot_vars.gui.stats.bone_per_hour = int(bot_vars.gui.stats.bone*3600000/bot_vars.timers.total.GetElapsedTime())
        bot_vars.gui.stats.total_bone = Inventory.GetModelCount(921)
        bot_vars.inv.log = {}
        bot_vars.inv.item_id = 0

        if bot_vars.opts.debug:
            Debug('Loot loop complete.')

            Debug('Loot from current lap:',                   msg_type = 'Notice')
            Debug(f'      Gold coins: {new_inv['gold']}',       msg_type = 'Notice')
            Debug(f'      Lockpicks: {new_inv[22751]}',         msg_type = 'Notice')
            Debug(f'      Diessa Chalices: {new_inv[24353]}',   msg_type = 'Notice')
            Debug(f'      Golden Rin Relics: {new_inv[24354]}', msg_type = 'Notice')
            Debug(f'      Salvageables: {new_inv['salv']}',     msg_type = 'Notice')
            Debug(f'      Bone: {new_inv[921]}',                msg_type = 'Notice')
            Debug(f'      Dust: {new_inv[929]}',                msg_type = 'Notice')

    def GetLootList(self):
        agent_array = AgentArray.GetItemArray()

        valid_model_ids = [921] # bones
        if bot_vars.loot.coins:    valid_model_ids.append(2511)
        if bot_vars.loot.picks:    valid_model_ids.append(22751)
        if bot_vars.loot.dust:     valid_model_ids.append(929)
        if bot_vars.loot.chalices: valid_model_ids.append(24353)
        if bot_vars.loot.relics:   valid_model_ids.append(24354)

        item_array_model = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: Item.GetModelID(Agent.GetItemAgent(agent_id).item_id) in valid_model_ids)

        item_array_salv = []
        if bot_vars.loot.salvageables:
            item_array_salv = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: Item.Usage.IsSalvageable(Agent.GetItemAgent(agent_id).item_id))

        item_array = list(set(item_array_model + item_array_salv))  
        item_array = AgentArray.Sort.ByDistance(item_array,Player.GetXY())

        return item_array

    def Loot(self):
        global bot_vars

        if ActionIsPending():
            return False

        if Agent.IsDead(Player.GetAgentID()):
            return True
        
        if not bot_vars.inv.log:
            bot_vars.inv.log = self.LogInventory([921,929,22751,24353,24354])

        item_array = self.GetLootList()
        if not item_array:
            self.LogLoot()
            return True

        item_id = item_array[0]
        if not item_id:
            self.LogLoot()
            return True

        bot_vars.inv.item_id = item_id
        current_target = Player.GetTargetID()
        if current_target != bot_vars.inv.item_id:
            if bot_vars.opts.debug:
                if Agent.IsNameReady(bot_vars.inv.item_id):
                    name = f'"{Agent.GetName(bot_vars.inv.item_id)}" - '
                else:
                    name = ''
                Debug(f'Changing target to {name}AgentID [{bot_vars.inv.item_id}].')

            Player.ChangeTarget(bot_vars.inv.item_id)
            SetPendingAction(randint(100,150))

            return False
        
        if bot_vars.opts.debug:
            if Agent.IsNameReady(bot_vars.inv.item_id):
                name = f'"{Agent.GetName(bot_vars.inv.item_id)}" - '
            else:
                name = ''
            Debug(f'Picking up {name}AgentID [{bot_vars.inv.item_id}].')

        Keystroke.PressAndRelease(Key.Space.value)
        SetPendingAction(randint(400,700))

        return False
# endregion

# region globals
bot_vars  = BotVariables()
build     = Build()
combat    = Combat()
inventory = ProcessInventory()
loot      = Loot()
# endregion

# region helper functions
def Debug(message, title = 'Log', msg_type = 'Debug'):
    py4gw_msg_type = Py4GW.Console.MessageType.Debug
    if msg_type == 'Debug':         py4gw_msg_type = Py4GW.Console.MessageType.Debug
    elif msg_type == 'Error':       py4gw_msg_type = Py4GW.Console.MessageType.Error
    elif msg_type == 'Info':        py4gw_msg_type = Py4GW.Console.MessageType.Info
    elif msg_type == 'Notice':      py4gw_msg_type = Py4GW.Console.MessageType.Notice
    elif msg_type == 'Performance': py4gw_msg_type = Py4GW.Console.MessageType.Performance
    elif msg_type == 'Success':     py4gw_msg_type = Py4GW.Console.MessageType.Success
    elif msg_type == 'Warning':     py4gw_msg_type = Py4GW.Console.MessageType.Warning
    Py4GW.Console.Log(title, str(message), py4gw_msg_type)

def StartBot():
    global bot_vars
    bot_vars.bot_started = True
    bot_vars.timers.total.Start()
    ResetVariables()

    if bot_vars.opts.debug:
        Debug('Starting script.')

def StopBot():
    global bot_vars
    bot_vars.bot_started = False
    bot_vars.timers.total.Pause()
    bot_vars.timers.lap.Stop()

    if bot_vars.opts.debug:
        Debug('Stopping script.')

def StartLapTimer():
    global bot_vars
    bot_vars.timers.lap.Start()

    if bot_vars.opts.debug:
        Debug('Starting lap timer.')

def ActionIsPending():
    global bot_vars
    if bot_vars.timers.checks.action != 0 and bot_vars.timers.action.GetElapsedTime() > 0:
        if bot_vars.timers.action.HasElapsed(bot_vars.timers.checks.action):
            bot_vars.timers.checks.action = 0
            bot_vars.timers.action.Stop()
            return False
    if bot_vars.timers.checks.action == 0 and bot_vars.timers.action.GetElapsedTime() == 0:
        return False
    return True

def SetPendingAction(time: float = 1000):
    global bot_vars
    bot_vars.timers.checks.action = time
    bot_vars.timers.action.Reset()

def Travel(outpost_id):
    global bot_vars

    if bot_vars.opts.debug:
        Debug(f'Travelling to outpost ID [{outpost_id}].')

    if Map.IsMapReady():
        if not Map.IsOutpost() or (Map.GetMapID() != outpost_id):
            Map.Travel(outpost_id)
            return

def ArrivedOutpost(map_id):
    if Map.IsMapReady() and Map.GetMapID() == map_id and Map.IsOutpost() and Party.IsPartyLoaded():
        return True
    return False

def ArrivedExplorable(map_id):
    if Map.IsMapReady() and Map.GetMapID() == map_id and Map.IsExplorable() and Party.IsPartyLoaded():
        return True
    return False

def FollowPath(path_handler,follow_handler):
    return Routines.Movement.FollowPath(path_handler,follow_handler)

# def FollowPath(path_handler,follow_handler,run_func=None):
#     if run_func(): return
#     return Routines.Movement.FollowPath(path_handler,follow_handler)  

def PathFinished(path_handler,follow_handler):
    return Routines.Movement.IsFollowPathFinished(path_handler, follow_handler)

def RequestEnemyNames():
    enemy_array = AgentArray.GetEnemyArray()
    for enemy in enemy_array:
        Agent.RequestName(enemy)

def RequestItemNames():
    item_array = AgentArray.GetItemArray()
    for item in item_array:
        Agent.RequestName(item)

def RequestInventoryNames():
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    for item in ItemArray.GetItemArray(bags_to_check):
        Item.RequestName(item)

def ResetVariables():
    global bot_vars

    bot_vars.path.reset()
    bot_vars.move.reset()
    bot_vars.exact_move.reset()
    bot_vars.fsm.reset()
    bot_vars.timers.stuck.Stop()
    bot_vars.timers.checks.action = 0
    bot_vars.timers.action.Stop()
    bot_vars.timers.settle.Stop()

    if bot_vars.opts.debug:
        Debug('Resetting script variables.')
# endregion

# region farming functions
def DoSetup():
    global bot_vars

    if bot_vars.do_setup:
        bot_vars.do_setup = False

        if bot_vars.opts.debug:
            Debug('Starting setup.')

        return True
    
    return False

def CheckRequirements():
    global bot_vars

    error = False
    error_msgs = []

    # check attributes (for runes)
    attribute_checks = {'Scythe Mastery' : 11,
                        'Wind Prayers'   : 15,
                        'Mysticism'      : 11}
    for attribute in Agent.GetAttributes(Player.GetAgentID()):
        if attribute.GetName() in attribute_checks:
            if attribute_checks[attribute.GetName()] != attribute.level:
                error_msgs.append(f'\tAttribute "{attribute.GetName()}" differs from requirement of {attribute_checks[attribute.GetName()]}.')
                error = True

    # check skills
    for i in range(1,9):
        skill_instance = PySkill.Skill(SkillBar.GetSkillIDBySlot(i))
        if skill_instance.id.id == 0:
            error_msgs.append(f'\tSkill slot [{i}] is empty.')
            error = True

    # display errors
    if error:
        Debug('Requirments check failed.', msg_type = 'Error')
        for msg in error_msgs:
            Debug(msg, msg_type = 'Error')
    else:
        if bot_vars.opts.debug:
            Debug('Requirments check passed.', msg_type = 'Success')

def InteractNPC():
    if not Agent.IsMoving(Player.GetAgentID()):
        Keystroke.PressAndRelease(Key.Space.value)

    if UIManager.IsNPCDialogVisible():
        return True
    
    return False

def PrepSkills():
    global bot_vars
    if not combat.CanCast(): return
    if ActionIsPending():    return
    
    spells = []
    if bot_vars.opts.build_type == 'iau':
        spells = [build.vop, build.ga, build.vos]
    elif bot_vars.opts.build_type == 'mb':
        spells = [build.vop, build.mb, build.ga, build.vos]

    for spell in spells:
        if combat.IsRecharged(spell):
            combat.CastSkill(spell)
            SetPendingAction(combat.GetAftercast(spell))
            return False
        
    if combat.CheckBuffs(spells):
        return True

def UseVoS():
    global bot_vars 
    
    if (combat.IsRecharged(Build.pf) and combat.IsRecharged(Build.ga) and combat.IsRecharged(Build.vos) and combat.GetEnergy() >= 15):
        if bot_vars.opts.debug:
            Debug('Queuing VoS cast.')

        bot_vars.action_queue.add_action(combat.CastSkill, Build.pf)
        bot_vars.action_queue.add_action(combat.CastSkill, Build.ga)
        bot_vars.action_queue.add_action(combat.CastSkill, Build.vos)
        SetPendingAction(1000)
        return True
    return False

def CheckVos():
    global bot_vars 

    if not combat.CheckBuffs([Build.vos]) and bot_vars.action_queue.is_empty():
        if combat.IsRecharged(Build.pf):
            bot_vars.action_queue.add_action(combat.CastSkill, Build.pf)
        if combat.IsRecharged(Build.ga):
            bot_vars.action_queue.add_action(combat.CastSkill, Build.ga)
        if combat.IsRecharged(Build.vos):
            bot_vars.action_queue.add_action(combat.CastSkill, Build.vos)
        SetPendingAction(1000)
        return True
    return False

def WaitRotation():
    if ActionIsPending(): return
    if UseVoS():          return

    if combat.IsRecharged(build.soms):
        combat.CastSkill(build.soms)
        SetPendingAction(combat.GetAftercast(build.soms))
        return

def KillRotation():
    global bot_vars
    if ActionIsPending():                       return
    if UseVoS():                                return
    if CheckVos():                              return
    if combat.EffectTimeRemaining(1517) < 1500: return
    if not combat.CanCast():                    return

    # maintain signet of mystic speed
    if not combat.CheckBuffs([build.soms]) and combat.IsRecharged(build.soms):
        combat.CastSkill(build.soms)
        SetPendingAction(combat.GetAftercast(build.soms))
        return
    
    # maintain iau (if equipped)
    if bot_vars.opts.build_type == 'iau' and combat.IsRecharged(build.iau):
        combat.CastSkill(build.iau)
        return

    # target
    target_id = Player.GetTargetID()
    if target_id == 0 or Agent.GetAllegiance(target_id)[0] != 3 or Agent.IsDead(target_id):

        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByAttribute(enemy_array,'IsAlive')
        enemy_array = AgentArray.Sort.ByDistance(enemy_array,(-15706,-9035))

        enemy_array = AgentArray.Filter.ByDistance(enemy_array,(-15706,-9035), 600)
        close_array = AgentArray.Filter.ByDistance(enemy_array,(-15706,-9035), 100)
        new_target = 0

        if Utils.Distance(Agent.GetXY(target_id),(-15706,-9035)) > 100 and close_array and close_array[0]:
            new_target = close_array[0]
        elif enemy_array and enemy_array[0]:
            new_target = enemy_array[0]

        if new_target:
            if bot_vars.opts.debug:
                if Agent.IsNameReady(Player.GetTargetID()):
                    name = f'"{Agent.GetName(Player.GetTargetID())}" - '
                else:
                    name = ''
                Debug(f'Changing target to {name}AgentID [{new_target}].')

            Player.ChangeTarget(new_target)
            SetPendingAction(200)
            return

    # attack
    if not Agent.IsAttacking(Player.GetAgentID()):
        if bot_vars.opts.debug:
            if Agent.IsNameReady(Player.GetTargetID()):
                name = f'"{Agent.GetName(Player.GetTargetID())}" - '
            else:
                name = ''
            Debug(f'Attacking {name}AgentID [{Player.GetTargetID()}].')

        Keystroke.PressAndRelease(Key.Space.value)
        SetPendingAction(400)
        return
    
    # cast crippling victory and reap impurities
    for spell in [build.cv, build.ri]:
        if combat.HasEnoughAdrenaline(spell):
            combat.CastSkill(spell)
            SetPendingAction(400)
            return

def HandleSkillbar():
    global bot_vars
    if Map.IsMapReady() and not Map.IsMapLoading() and Map.IsExplorable() and Party.IsPartyLoaded():
        if bot_vars.fsm.get_current_step_name() == 'waiting for enemies':
            WaitRotation()
        elif bot_vars.fsm.get_current_step_name() == 'killing enemies':
            KillRotation()

def HandleStuck():
    global bot_vars
    if Map.IsMapReady() and not Map.IsMapLoading() and Map.IsExplorable() and Party.IsPartyLoaded():
        if bot_vars.fsm.get_current_step_name() == 'going to kill spot':
            if not Agent.IsMoving(Player.GetAgentID()):
                if not bot_vars.timers.stuck.IsRunning():
                    bot_vars.timers.stuck.Start()
                    return
                if bot_vars.timers.stuck.IsRunning() and bot_vars.timers.stuck.HasElapsed(bot_vars.timers.checks.stuck):
                    if bot_vars.opts.debug:
                        Debug('Player is stuck, moving to next state.')

                    bot_vars.fsm.jump_to_state_by_name('waiting for enemies') 
            else:
                if bot_vars.timers.stuck.IsRunning():
                    bot_vars.timers.stuck.Stop()

def WaitForSettle(range,count,timeout = 6000):
    global bot_vars 

    if Agent.IsDead(Player.GetAgentID()):
        return True
    
    if Agent.GetHealth(Player.GetAgentID()) < 0.5:
        return True
    
    if not bot_vars.timers.settle.IsRunning():
        bot_vars.timers.settle.Start()

    if bot_vars.timers.settle.HasElapsed(timeout):
        return True

    player_x, player_y = Player.GetXY()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), range)

    if len(enemy_array) >= count:
        bot_vars.timers.settle.Reset()
        bot_vars.timers.settle.Stop()
        return True

    return False

def WaitForKill():
    global bot_vars

    if Agent.IsDead(Player.GetAgentID()):
        bot_vars.gui.stats.fails += 1
        return True

    player_x, player_y = Player.GetXY()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), 600)

    if not enemy_array or (len(enemy_array) < 2 and enemy_array[0] and Agent.GetHealth(enemy_array[0]) > 0.4):
        bot_vars.gui.stats.runs += 1
        lap_time = bot_vars.timers.lap.GetElapsedTime()
        bot_vars.timers.lap_times.append(lap_time)
        bot_vars.timers.lap.Stop()
        bot_vars.gui.stats.avg_time = sum(bot_vars.timers.lap_times)/bot_vars.gui.stats.runs
        return True

    return False
# endregion

# region fsm config
fsm_setup_states = [
    ('mapping to outpost'    , dict(execute_fn=lambda:Travel(bot_vars.map.starting),exit_condition=lambda:ArrivedOutpost(bot_vars.map.starting),transition_delay_ms=1000)),
    ('loading skillbar'      , dict(execute_fn=lambda:combat.LoadSkillBar(build.GetTemplate(bot_vars.opts.build_type)),transition_delay_ms=1000)),
    ('checking requirements' , dict(execute_fn=lambda:CheckRequirements())),
    ('setting nm'            , dict(execute_fn=lambda:Party.SetNormalMode(),transition_delay_ms=1000)),
    ('going to npc'          , dict(execute_fn=lambda:FollowPath(bot_vars.path.npc,bot_vars.move),exit_condition=lambda:PathFinished(bot_vars.path.npc,bot_vars.move),run_once=False)),
    ('targetting npc'        , dict(execute_fn=lambda:Keystroke.PressAndRelease(Key.V.value),transition_delay_ms=200)),
    ('talking to npc'        , dict(run_once=False,exit_condition=lambda:InteractNPC())),
    ('talking more'          , dict(execute_fn=lambda:Player.SendDialog(0x832105),transition_delay_ms=1000)),
    ('entering dungeon'      , dict(execute_fn=lambda:Player.SendDialog(0x88),exit_condition=lambda:ArrivedExplorable(bot_vars.map.dungeon))),
    ('setting up resign'     , dict(execute_fn=lambda:Player.Move(*Path.rezone[0]),exit_condition=lambda:ArrivedOutpost(bot_vars.map.starting),transition_delay_ms=200)),
    ('resetting npc path'    , dict(execute_fn=lambda:bot_vars.path.npc.reset()))
]

fsm_inventory_states = [
    ('requesting names'      , dict(execute_fn=lambda:RequestInventoryNames())),
    ('targetting merchant'   , dict(execute_fn=lambda:Keystroke.PressAndRelease(Key.V.value),transition_delay_ms=200)),
    ('talking to merchant'   , dict(run_once=False,exit_condition=lambda:InteractNPC())),
    ('trading'               , dict(execute_fn=lambda:Player.SendDialog(0x7F),transition_delay_ms=1000)),
    ('IDing items'           , dict(exit_condition=lambda:inventory.IDInventory())),
    ('salvaging items'       , dict(exit_condition=lambda:inventory.SalvageInventory())),
    ('selling items'         , dict(execute_fn=lambda:inventory.SellItem(),run_once=False,exit_condition=lambda:inventory.SellLoop())),
    ('calculating item sort' , dict(execute_fn=lambda:inventory.SortCalculate())),
    ('sorting items'         , dict(execute_fn=lambda:inventory.SortItem(),run_once=False,exit_condition=lambda:inventory.SortLoop())),
]

fsm_farm_states = [
    ('lapping'               , dict(execute_fn=lambda:StartLapTimer())),
    ('equipping staff'       , dict(execute_fn=lambda:combat.ChangeWeaponSet(Build.staff),transition_delay_ms=1000)),
    ('targetting npc'        , dict(execute_fn=lambda:Keystroke.PressAndRelease(Key.V.value),transition_delay_ms=200)),
    ('talking to npc'        , dict(run_once=False,exit_condition=lambda:InteractNPC())),
    ('talking more'          , dict(execute_fn=lambda:Player.SendDialog(0x832105),transition_delay_ms=1000)),
    ('entering dungeon'      , dict(execute_fn=lambda:Player.SendDialog(0x88),exit_condition=lambda:ArrivedExplorable(560))),
    ('going to prep spot'    , dict(execute_fn=lambda:FollowPath(bot_vars.path.prep,bot_vars.move),exit_condition=lambda:PathFinished(bot_vars.path.prep,bot_vars.move),run_once=False)),
    ('waiting...'            , dict(transition_delay_ms=3000)),
    ('prepping skills'       , dict(execute_fn=lambda:PrepSkills(),exit_condition=lambda:PrepSkills(),run_once=False)),
    ('going to kill spot'    , dict(execute_fn=lambda:FollowPath(bot_vars.path.kill,bot_vars.exact_move),exit_condition=lambda:PathFinished(bot_vars.path.kill,bot_vars.exact_move),run_once=False)),
    ('waiting for enemies'   , dict(exit_condition=lambda:WaitForSettle(200,3))),
    ('equipping scythe'      , dict(execute_fn=lambda:combat.ChangeWeaponSet(build.scythe),exit_condition=lambda:Agent.GetWeaponType(Player.GetAgentID())[1]=='Scythe',run_once=False)),
    ('killing enemies'       , dict(exit_condition=lambda:WaitForKill())),
    ('looting items'         , dict(exit_condition=lambda:loot.Loot())),
    ('resigning'             , dict(execute_fn=lambda:Player.SendChatCommand('resign'),exit_condition=lambda:Party.IsPartyDefeated(),transition_delay_ms=1000)),
    ('returning'             , dict(execute_fn=lambda:Party.ReturnToOutpost(),exit_condition=lambda:ArrivedOutpost(bot_vars.map.starting),transition_delay_ms=200)),
    ('resetting loop'        , dict(execute_fn=lambda:ResetVariables()))
]

for (state, kwargs) in fsm_setup_states:
    bot_vars.fsm_setup.AddState(state,**kwargs)

for (state, kwargs) in fsm_inventory_states:
    bot_vars.fsm_inv.AddState(state,**kwargs)

bot_vars.fsm.AddSubroutine(name='setting up',           sub_fsm=bot_vars.fsm_setup, condition_fn=lambda:DoSetup())
bot_vars.fsm.AddSubroutine(name='processing inventory', sub_fsm=bot_vars.fsm_inv,   condition_fn=lambda:inventory.CheckSlots())

for (state, kwargs) in fsm_farm_states:
    bot_vars.fsm.AddState(state,**kwargs)
# endregion

# region draw
class Draw:
    global bot_vars

    def SetButtonStyle(self,active):
        if active:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (.15,.15,.15,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (.20,.20,.20,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (.25,.25,.25,1))
        else:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (.13,.13,.13,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (.3,.3,.3,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (.4,.4,.4,1))

    def PopButtonStyle(self):
        PyImGui.pop_style_color(3)

    def MakeTable(self,*columns, colors = None):
        num_cols = len(columns)
        num_rows = len(columns[0])

        if PyImGui.begin_table('Info', num_cols,   PyImGui.TableFlags.Borders |
                                                   PyImGui.TableFlags.RowBg   |
                                                   PyImGui.TableFlags.SizingStretchSame):
            for row in range(num_rows):
                PyImGui.table_next_row()
                for col in range(num_cols):
                    PyImGui.table_next_column()
                    if colors:
                        PyImGui.text_colored(str(columns[col][row]), colors[row])
                    else:
                        PyImGui.text(str(columns[col][row]))
            PyImGui.end_table()

    def FormatItemStack(self,count):
        return f'{count} ({round(count/250,1)})'

    def DebugFn(self):
        global bot_vars, mods
        Debug('running debug function', msg_type='Info')
        "NPC Bounty Dialog.Option1.Icon"
        frame_id = UIManager.GetFrameIDByCustomLabel(frame_label = "NPC Bounty Dialog.Option2.Icon") or 0
        if frame_id:
            Debug(dir(PyUIManager.UIFrame(frame_id)))
            UIManager.FrameClick(frame_id)
        else:
            Debug('none')
        
    def CreateRunButton(self):
        window_width = 240
        button_width = (window_width-20)

        self.SetButtonStyle(1)
        if bot_vars.bot_started:
            if PyImGui.button('\uf04d', button_width, 25):
                ResetVariables()
                StopBot()
        else:
            if PyImGui.button('\uf04b', button_width, 25):
                ResetVariables()
                StartBot()
        self.PopButtonStyle()

    def CreateStateLog(self):
        state = ''
        if bot_vars.fsm.get_current_step_name() == 'setting up':
            state = bot_vars.fsm_setup.get_current_step_name()
        elif bot_vars.fsm.get_current_step_name() == 'processing inventory':
            state = bot_vars.fsm_inv.get_current_step_name()
        else:
            state = bot_vars.fsm.get_current_step_name()

        if bot_vars.gui.stats.status != state:
            if "FSM not started or finished" not in state:
                bot_vars.gui.stats.time = datetime.now().strftime('%H:%M:%S')
                bot_vars.gui.stats.status = state

                if bot_vars.opts.debug:
                    Debug(f'Transitioning to state "{bot_vars.gui.stats.status}".')

        PyImGui.text_colored(f'[{bot_vars.gui.stats.time}]', (.48, .68, 1, 1))
        PyImGui.same_line(0.0,-1.0)
        PyImGui.text(f'{bot_vars.gui.stats.status}')

    def CreateTables(self):
        colors = {
            'runs'     : [   0,   .7,    0, 1],
            'fails'    : [   1,  .25,  .23, 1],
            'time'     : [  .9,   .9,   .9, 1],
            'bones'    : [ .89,  .85,  .79, 1],
            'coins'    : [   1,  .75,    0, 1],
            'picks'    : [  .6,   .6,   .6, 1],
            'dust'     : [.737, .463, .455, 1],
            'iron'     : [.631, .616, .580, 1],
            'chalices' : [.737, .514, .365, 1],
            'relics'   : [.839, .737, .424, 1]
        }

        columns = [
            'Runs',
            'Fails',
            'Average Pace',
            'Lap Time',
            'Total Time',
            'Bones',
            'Bones/Hour',
            'Starting Bones',
            'Total Bones',
            'Gold Coins',
            'Lock Picks',
            'Dust',
            'Iron',
            'Chalices',
            'Relics'
        ]

        values = [
            bot_vars.gui.stats.runs,
            bot_vars.gui.stats.fails,
            FormatTime(bot_vars.gui.stats.avg_time,mask='mm:ss'),
            bot_vars.timers.lap.FormatElapsedTime("hh:mm:ss"),
            bot_vars.timers.total.FormatElapsedTime("hh:mm:ss"),
            self.FormatItemStack(bot_vars.gui.stats.bone),
            self.FormatItemStack(round(bot_vars.gui.stats.bone_per_hour)),
            self.FormatItemStack(bot_vars.gui.stats.starting_bone),
            self.FormatItemStack(bot_vars.gui.stats.total_bone),
            bot_vars.gui.stats.gold_coins,
            bot_vars.gui.stats.lockpicks,
            self.FormatItemStack(bot_vars.gui.stats.dust),
            self.FormatItemStack(bot_vars.gui.stats.iron),
            bot_vars.gui.stats.chalices,
            bot_vars.gui.stats.relics
        ]

        colors = [
            colors['runs'],
            colors['fails'],
            colors['time'],
            colors['time'],
            colors['time'],
            colors['bones'],
            colors['bones'],
            colors['bones'],
            colors['bones'],
            colors['coins'],
            colors['picks'],
            colors['dust'],
            colors['iron'],
            colors['chalices'],
            colors['relics']
        ]

        table_nums = [1,1,2,2,2,3,3,3,3,4,4,4,4,4,4]

        filter = bot_vars.gui.opts.rows.GetRows()

        columns    = [item for i, item in enumerate(columns)    if filter[i]] if not bot_vars.gui.opts.show_all else columns
        values     = [item for i, item in enumerate(values)     if filter[i]] if not bot_vars.gui.opts.show_all else values
        colors     = [item for i, item in enumerate(colors)     if filter[i]] if not bot_vars.gui.opts.show_all else colors
        table_nums = [item for i, item in enumerate(table_nums) if filter[i]] if not bot_vars.gui.opts.show_all else table_nums

        if bot_vars.gui.opts.condense_tables:
            self.MakeTable(columns,values,colors=colors if bot_vars.gui.opts.color_rows else None)
        else:
            tables = []
            for num in list(set(table_nums)):
                table = {'columns':[],'values':[],'colors':[]}
                for i,table_num in enumerate(table_nums):
                    if table_num == num:
                        table['columns'].append(columns[i])
                        table['values'].append(values[i])
                        table['colors'].append(colors[i])
                tables.append(table)

            for table in tables:
                self.MakeTable(table['columns'],table['values'],colors = table['colors'] if bot_vars.gui.opts.color_rows else None)

    def CreateSettings(self):
        # general
        if PyImGui.tree_node('General'):
            bot_vars.opts.debug               = PyImGui.checkbox('Debug Mode',           bot_vars.opts.debug)

            self.SetButtonStyle(1)

            if PyImGui.button('Process Inventory',PyImGui.get_window_size()[0]-60):
                bot_vars.inv.process = True

            if PyImGui.button('Open Storage', PyImGui.get_window_size()[0]-60):
                if not Inventory.IsStorageOpen():
                    Inventory.OpenXunlaiWindow()

            if bot_vars.opts.debug:
                if PyImGui.button('Run Debug Function', PyImGui.get_window_size()[0]-60):
                    self.DebugFn()

            PyImGui.pop_style_color(3)
            
            PyImGui.tree_pop()

        # build
        if PyImGui.tree_node('Build'):
            items = ['iau','mb']
            bot_vars.opts.build_type = items[PyImGui.radio_button("IaU", items.index(bot_vars.opts.build_type), 0)]
            PyImGui.same_line(0.0,-1.0)
            bot_vars.opts.build_type = items[PyImGui.radio_button("Mental Block", items.index(bot_vars.opts.build_type), 1)]
            PyImGui.tree_pop()

        # loot
        if PyImGui.tree_node('Loot'):
            bot_vars.loot.salvageables = PyImGui.checkbox('Salvageables',      bot_vars.loot.salvageables)
            bot_vars.loot.coins        = PyImGui.checkbox('Gold Coins',        bot_vars.loot.coins)
            bot_vars.loot.picks        = PyImGui.checkbox('Lockpicks',         bot_vars.loot.picks)
            bot_vars.loot.dust         = PyImGui.checkbox('Glittering Dust',   bot_vars.loot.dust)
            bot_vars.loot.chalices     = PyImGui.checkbox('Diessa Chalices',   bot_vars.loot.chalices)
            bot_vars.loot.relics       = PyImGui.checkbox('Golden Rin Relics', bot_vars.loot.relics)
            PyImGui.tree_pop()

        # gui
        if PyImGui.tree_node('User Interface  '):
            bot_vars.gui.opts.condense_tables  = PyImGui.checkbox('Condense Tables',    bot_vars.gui.opts.condense_tables)
            bot_vars.gui.opts.color_rows       = PyImGui.checkbox('Color Rows',         bot_vars.gui.opts.color_rows)
            bot_vars.gui.opts.show_all         = PyImGui.checkbox('Show All',           bot_vars.gui.opts.show_all)
            PyImGui.separator()
            bot_vars.gui.opts.rows.lap_time    = PyImGui.checkbox('Lap Time',           bot_vars.gui.opts.rows.lap_time)
            bot_vars.gui.opts.rows.bones_hr    = PyImGui.checkbox('Bones per Hour',     bot_vars.gui.opts.rows.bones_hr)
            bot_vars.gui.opts.rows.start_bones = PyImGui.checkbox('Starting Bones',     bot_vars.gui.opts.rows.start_bones)
            bot_vars.gui.opts.rows.total_bones = PyImGui.checkbox('Total Bones',        bot_vars.gui.opts.rows.total_bones)
            bot_vars.gui.opts.rows.coins       = PyImGui.checkbox('Gold Coins ',        bot_vars.gui.opts.rows.coins)
            bot_vars.gui.opts.rows.picks       = PyImGui.checkbox('Lockpicks ',         bot_vars.gui.opts.rows.picks)
            bot_vars.gui.opts.rows.dust        = PyImGui.checkbox('Glittering Dust ',   bot_vars.gui.opts.rows.dust)
            bot_vars.gui.opts.rows.iron        = PyImGui.checkbox('Iron',               bot_vars.gui.opts.rows.iron)
            bot_vars.gui.opts.rows.chalices    = PyImGui.checkbox('Diessa Chalices ',   bot_vars.gui.opts.rows.chalices)
            bot_vars.gui.opts.rows.relics      = PyImGui.checkbox('Golden Rin Relics ', bot_vars.gui.opts.rows.relics)
            PyImGui.tree_pop()

        # general
        if PyImGui.tree_node('Description'):
            PyImGui.text('This bot uses a Dervish to farm bones at the entrance of')
            PyImGui.text('the Cathedral of Flames dungeon. It will loot bone, dust,')
            PyImGui.text('salvageables, coins, lockpicks, Diessa Chalices, and Golden')
            PyImGui.text('Rin Relics. When the inventory has 5 or lessslots remaining,')
            PyImGui.text('it will ID, salvage, and sell everything besides materials.')
            PyImGui.text('Development was done using the requirements below.')
            PyImGui.tree_pop()

        # build
        if PyImGui.tree_node('Requirements  '):
            PyImGui.text('Map:')
            PyImGui.text('     Doolmore Shrine')
            PyImGui.text('Build:')
            PyImGui.text('     Signet of Mystic Speed')
            PyImGui.text('     Pious Fury')
            PyImGui.text('     Grenth\'s Aura')
            PyImGui.text('     Vow of Silence')
            PyImGui.text('     Crippling Victory')
            PyImGui.text('     Reap Impurities')
            PyImGui.text('     Vow of Piety')
            PyImGui.text('     "I Am Unstoppable!" / Mental Block')
            PyImGui.text('Weapons:')
            PyImGui.text('     Slot 1 - Zealous +15%^Ench Scythe of Enchanting')
            PyImGui.text('     Slot 1 - Any Staff of Enchanting')
            PyImGui.text('Armor:')
            PyImGui.text('     x5 Windwalker Insignias')
            PyImGui.text('     +4 Wind Prayers')
            PyImGui.text('     +1 Scythe Mastery')
            PyImGui.text('     +1 Mysticism')
            PyImGui.text('     x2 Runes of Attunement')
            PyImGui.tree_pop()

    def Run(self):
        if bot_vars.gui.window_module.first_run:
            PyImGui.set_next_window_size(bot_vars.gui.window_module.window_size[0], bot_vars.gui.window_module.window_size[1])     
            PyImGui.set_next_window_pos(bot_vars.gui.window_module.window_pos[0], bot_vars.gui.window_module.window_pos[1])
            bot_vars.gui.window_module.first_run = False

        try:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowBorderSize,0.0)
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameRounding,0.0)
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg,        (0.15, 0.15, 0.15, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0.20, 0.20, 0.20, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive,  (0.25, 0.25, 0.25, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.CheckMark,      (1.0, 1.0, 1.0, 1.0))

            PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg,         (0.0, 0.0, 0.0, 0.7))
            PyImGui.push_style_color(PyImGui.ImGuiCol.TitleBg,          (0.0, 0.0, 0.0, 0.7))
            PyImGui.push_style_color(PyImGui.ImGuiCol.TitleBgActive,    (0.0, 0.0, 0.0, 0.7))
            PyImGui.push_style_color(PyImGui.ImGuiCol.TitleBgCollapsed, (0.0, 0.0, 0.0, 0.7))

            if PyImGui.begin(bot_vars.gui.window_module.window_name, bot_vars.gui.window_module.window_flags):
                bot_vars.gui.window_pos  = PyImGui.get_window_pos()
                bot_vars.gui.window_size = PyImGui.get_window_size()

                self.CreateRunButton()
                self.CreateStateLog()
                self.CreateTables()
                if PyImGui.tree_node('Settings'):
                    self.CreateSettings()
                    PyImGui.tree_pop()
            PyImGui.end()

            PyImGui.pop_style_var(3)
            PyImGui.pop_style_color(8)
        except Exception as e:
            current_function = inspect.currentframe().f_code.co_name # type: ignore
            Py4GW.Console.Log('BOT', f'Error in {current_function}: {str(e)}', Py4GW.Console.MessageType.Error)
            raise
# endregion

# region main
def main():
    global bot_vars

    try:
        # only run when everything is loaded
        if not Map.IsMapReady() or not Party.IsPartyLoaded(): return

        # draw gui
        Draw().Run()

        # throttle script calls
        ping = Py4GW.PingHandler().GetCurrentPing() + 50
        if bot_vars.timers.throttle.HasElapsed(max(ping,bot_vars.timers.checks.throttle)):
            bot_vars.timers.throttle.Reset()
            # execute script
            if bot_vars.bot_started:
                if bot_vars.fsm.is_finished():
                    ResetVariables()
                else:
                    if not bot_vars.action_queue.is_empty():
                        bot_vars.action_queue.execute_next()
                    else:
                        bot_vars.fsm.update()
                        HandleSkillbar()
                        HandleStuck()

            # handle inventory button
            if bot_vars.inv.process:
                if not bot_vars.fsm_inv.is_finished():
                    bot_vars.fsm_inv.update()

    except ImportError as e:
        Py4GW.Console.Log('BOT', f'ImportError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('BOT', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log('BOT', f'ValueError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('BOT', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log('BOT', f'TypeError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('BOT', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log('BOT', f'Unexpected error encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('BOT', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == '__main__':
    main()
# endregion
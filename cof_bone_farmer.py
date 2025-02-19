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
    window_module = ImGui.WindowModule('Bone Farmer', window_name='CoF Bone Farm', window_size=(230, 310),
                                       window_pos=(300,600), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
    # misc
    starting_map   = 648
    dungeon_map    = 560
    bot_started    = False
    action_queue   = ActionQueue()
    # timers
    total_timer    = Timer()
    lap_timer      = Timer()
    lap_times      = []
    action_check   = 0
    action_timer   = Timer()
    settle_timer   = Timer()
    throttle_time  = 100
    throttle_timer = Timer()
    throttle_timer.Start()
    # gui
    show_extras    = False
    time           = datetime.now().strftime('%H:%M:%S')
    status         = 'waiting for input'
    runs           = 0
    avg_time       = 0
    fails          = 0
    bone           = 0
    starting_bone  = 0
    current_bone   = 0
    bone_per_hour  = 0
    # inventory
    item_id        = 0
    empty_slots    = 3

class FSMVariables:
    fsm        = FSM('Bone Farmer')
    path       = {'npc'    : Routines.Movement.PathHandler(Path.npc),
                  'rezone' : Routines.Movement.PathHandler(Path.rezone),
                  'prep'   : Routines.Movement.PathHandler(Path.prep),
                  'kill'   : Routines.Movement.PathHandler(Path.kill)}
    move       = Routines.Movement.FollowXY()
    exact_move = Routines.Movement.FollowXY(tolerance=5)
    do_setup   = True
    
class Build:
    # template
    template = 'OgCjkqqLrSYiihdftXjhOXhXxlA'
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
    mb       = 8

class Combat:
    def LoadSkillBar(template):
        SkillBar.LoadSkillTemplate(template)

    def ChangeWeaponSet(set):
        if set == 1:
            Keystroke.PressAndRelease(Key.F1.value)
        elif set == 2:
            Keystroke.PressAndRelease(Key.F2.value)
        elif set == 3:
            Keystroke.PressAndRelease(Key.F3.value)
        elif set == 4:
            Keystroke.PressAndRelease(Key.F4.value)

    def CastSkill(skill_slot, target_agent_id=0):
        SkillBar.UseSkill(skill_slot, target_agent_id)

    def CanCast():
        player_agent_id = Player.GetAgentID()

        if (Agent.IsCasting(player_agent_id) 
            or Agent.GetCastingSkill(player_agent_id) != 0
            or Agent.IsKnockedDown(player_agent_id)
            or Agent.IsDead(player_agent_id)
            or SkillBar.GetCasting() != 0):
            return False
        return True

    def GetEnergyAgentCost(skill_slot):
        skill_id = SkillBar.GetSkillIDBySlot(skill_slot)
        cost = Skill.skill_instance(skill_id).energy_cost

        if cost == 11:
            cost = 15    # True cost is 15
        elif cost == 12:
            cost = 25    # True cost is 25

        cost = max(0, cost)
        return cost

    def HasEnoughAdrenaline(skill_slot):
        skill_id = SkillBar.GetSkillIDBySlot(skill_slot)

        return SkillBar.GetSkillData(skill_slot).adrenaline_a >= Skill.Data.GetAdrenaline(skill_id)

    def GetEnergy():
        player_agent_id = Player.GetAgentID()
        energy = Agent.GetEnergy(player_agent_id)
        max_energy = Agent.GetMaxEnergy(player_agent_id)
        energy_points = int(energy * max_energy)

        return energy_points

    def HasEnoughEnergy(skill_slot):
        player_agent_id = Player.GetAgentID()
        energy = Agent.GetEnergy(player_agent_id)
        max_energy = Agent.GetMaxEnergy(player_agent_id)
        energy_points = int(energy * max_energy)

        return Combat.GetEnergyAgentCost(skill_slot, player_agent_id) <= energy_points
    
    def IsRecharged(skill_slot):
        skill = SkillBar.GetSkillData(skill_slot)
        recharge = skill.recharge
        return recharge == 0
    
    def HasBuff(agent_id, skill_slot):
        skill_id = SkillBar.GetSkillIDBySlot(skill_slot)

        if Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id):
            return True
        return False
    
    def CheckBuffs(buff_list):
        for buff in buff_list:
            if not Combat.HasBuff(Player.GetAgentID(),buff):
                return False
        return True
    
    def EffectTimeRemaining(skill_id):
        for effect in Effects.GetEffects(Player.GetAgentID()):
            if effect.skill_id == skill_id:
                return effect.time_remaining
        return 0
    
    def GetAftercast(skill_slot):
        skill_id = SkillBar.GetSkillIDBySlot(skill_slot)

        activation = Skill.Data.GetActivation(skill_id)
        aftercast = Skill.Data.GetAftercast(skill_id)    
        return max(activation*1000 + aftercast*1000 + Py4GW.PingHandler().GetCurrentPing() + 50,500)

class Loot:
    debug = False

    def GetLootList():
        agent_array = AgentArray.GetItemArray()
        valid_types = [9,11,18,20,30]
        item_array = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: Item.GetItemType(Agent.GetItemAgent(agent_id).item_id)[0] in valid_types)
        return item_array

    def PickUp():
        global bot_vars
        
        if ActionIsPending(): return

        item_array = Loot.GetLootList()
        if len(item_array) == 0:
            return

        item = item_array[0]

        if bot_vars.item_id != item:
            bot_vars.item_id = item
        
        current_target = Player.GetTargetID()
        
        if current_target != bot_vars.item_id:
            Player.ChangeTarget(bot_vars.item_id)
            SetPendingAction(randint(100,150))
            if Loot.debug:
                Debug(f'Changing target to item ID [{bot_vars.item_id}]')
            return
        
        Keystroke.PressAndRelease(Key.Space.value)
        SetPendingAction(randint(400,700))
        if Loot.debug:
            Debug(f'Picking up item ID [{bot_vars.item_id}]')

    def Loop():
        global bot_vars

        if Agent.IsDead(Player.GetAgentID()):
            return True

        item_array = Loot.GetLootList()

        if (len(item_array) == 0):
            bot_vars.current_bone = Inventory.GetModelCount(921)
            bot_vars.bone = bot_vars.current_bone - bot_vars.starting_bone
            bot_vars.bone_per_hour = bot_vars.bone*3600000/bot_vars.total_timer.GetElapsedTime()
            if Loot.debug:
                Debug('Loot loop complete')
            return True
        return False
# endregion

# region globals
bot_vars = BotVariables()
fsm_vars = FSMVariables()
# endregion

# region helper functions
def Debug(message = ''):
    Py4GW.Console.Log('DEBUG', str(message), Py4GW.Console.MessageType.Info)

def StartBot():
    global bot_vars
    bot_vars.bot_started = True
    bot_vars.total_timer.Start()
    ResetVariables()

def StopBot():
    global bot_vars
    bot_vars.bot_started = False
    bot_vars.total_timer.Pause()
    bot_vars.lap_timer.Stop()

def StartLapTimer():
    global bot_vars
    bot_vars.lap_timer.Start()

def ActionIsPending():
    global bot_vars
    if bot_vars.action_check != 0 and bot_vars.action_timer.GetElapsedTime() > 0:
        if bot_vars.action_timer.HasElapsed(bot_vars.action_check):
            bot_vars.action_check = 0
            bot_vars.action_timer.Stop()
            return False
    if bot_vars.action_check == 0 and bot_vars.action_timer.GetElapsedTime() == 0:
        return False
    return True

def SetPendingAction(time=1000):
    global bot_vars
    bot_vars.action_check = time
    bot_vars.action_timer.Reset()

def Travel(outpost_id):
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

def PathFinished(path_handler,follow_handler):
    return Routines.Movement.IsFollowPathFinished(path_handler, follow_handler)

def ResetVariables():
    global bot_vars, fsm_vars

    fsm_vars.path['npc'].reset()
    fsm_vars.path['rezone'].reset()
    fsm_vars.path['prep'].reset()
    fsm_vars.path['kill'].reset()
    fsm_vars.move.reset()
    fsm_vars.exact_move.reset()
    fsm_vars.fsm.reset()
    bot_vars.action_check = 0
    bot_vars.action_timer.Stop()
    bot_vars.settle_timer.Stop()
# endregion

# region farming functions
def DoSetup():
    global bot_vars, fsm_vars
    if fsm_vars.do_setup:
        fsm_vars.do_setup = False
        bot_vars.starting_bone = Inventory.GetModelCount(921)
        bot_vars.current_bone = bot_vars.starting_bone
    else:
        fsm_vars.fsm.jump_to_state_by_name('equipping staff')

def PrepSkills():
    if not Combat.CanCast(): return
    if ActionIsPending():    return
    
    for spell in [Build.vop, Build.mb, Build.ga, Build.vos]:
        if Combat.IsRecharged(spell):
            Combat.CastSkill(spell)
            SetPendingAction(Combat.GetAftercast(spell))
            return

def UseVoS():
    global bot_vars, fsm_vars 
    
    if (Combat.IsRecharged(Build.pf) and Combat.IsRecharged(Build.ga) and Combat.IsRecharged(Build.vos) and Combat.GetEnergy() >= 15):
        bot_vars.action_queue.add_action(Keystroke.PressAndRelease, Key.V.value)
        bot_vars.action_queue.add_action(Combat.CastSkill, Build.pf)
        bot_vars.action_queue.add_action(Combat.CastSkill, Build.ga)
        bot_vars.action_queue.add_action(Combat.CastSkill, Build.vos)
        SetPendingAction(1000)
        return True

def WaitRotation():
    if ActionIsPending(): return
    if UseVoS():          return

    if Combat.IsRecharged(Build.soms):
        Combat.CastSkill(Build.soms)
        SetPendingAction(Combat.GetAftercast(Build.soms))
        return

def KillRotation():
    global fsm_vars
    if ActionIsPending():                       return
    if UseVoS():                                return
    if Combat.EffectTimeRemaining(1517) < 1500: return

    debug = False

    if Combat.CanCast():
        # maintain signet of mystic speed
        if not Combat.CheckBuffs([Build.soms]) and Combat.IsRecharged(Build.soms):
            Combat.CastSkill(Build.soms)
            SetPendingAction(Combat.GetAftercast(Build.soms))
            if debug:
                Debug(f'Casting skill [{Build.soms}]')
            return
  
        # target
        target_id = Player.GetTargetID()
        if target_id == 0 or Agent.GetAllegiance(target_id)[0] != 3 or Agent.IsDead(target_id) or Utils.Distance(Agent.GetXY(target_id),Player.GetXY()) > 200:
            enemy_array = AgentArray.GetEnemyArray()
            enemy_array = AgentArray.Filter.ByAttribute(enemy_array,'IsAlive')
            enemy_array = AgentArray.Sort.ByDistance(enemy_array,(-15706,-9035))

            if enemy_array:
                Player.ChangeTarget(enemy_array[0])
                if debug:
                    Debug(f'changing to target ID [{enemy_array[0]}]')
                SetPendingAction(100)
                return

        # attack
        if not Agent.IsAttacking(Player.GetAgentID()):
            Player.Interact(Player.GetTargetID())
            if debug:
                Debug(f'attacking target ID [{Player.GetTargetID()}]')
            SetPendingAction(400)
            return
        
        # cast crippling victory and reap impurities
        for spell in [Build.cv, Build.ri]:
            if Combat.HasEnoughAdrenaline(spell):
                Combat.CastSkill(spell)
                SetPendingAction(400)
                if debug:
                    Debug(f'Casting skill [{Build.soms}]')
                return

def HandleSkillbar():
    if Map.IsMapReady() and not Map.IsMapLoading() and Map.IsExplorable() and Party.IsPartyLoaded():
        if fsm_vars.fsm.get_current_step_name() == 'waiting for enemies':
            WaitRotation()
        elif fsm_vars.fsm.get_current_step_name() == 'killing enemies':
            KillRotation()

def WaitForSettle(range,count,timeout = 6000):
    global bot_vars 

    if Agent.IsDead(Player.GetAgentID()):
        return True
    
    if Agent.GetHealth(Player.GetAgentID()) < 0.5:
        return True
    
    if not bot_vars.settle_timer.IsRunning():
        bot_vars.settle_timer.Start()

    if bot_vars.settle_timer.HasElapsed(timeout):
        return True

    player_x, player_y = Player.GetXY()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), range)

    if len(enemy_array) >= count:
        bot_vars.settle_timer.Reset()
        bot_vars.settle_timer.Stop()
        return True

    return False

def WaitForKill():
    global bot_vars

    if Agent.IsDead(Player.GetAgentID()):
        bot_vars.fails += 1
        return True

    player_x, player_y = Player.GetXY()

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), 600)

    if not enemy_array or (len(enemy_array) < 2 and enemy_array[0] and Agent.GetHealth(enemy_array[0]) > 0.4):
        bot_vars.runs += 1
        lap_time = bot_vars.lap_timer.GetElapsedTime()
        bot_vars.lap_times.append(lap_time)
        bot_vars.lap_timer.Stop()
        bot_vars.avg_time = sum(bot_vars.lap_times)/bot_vars.runs
        return True

    return False
# endregion

# region fsm config
fsm_main_states = [
    # setup
    ('mapping to outpost'  , dict(execute_fn=lambda:Travel(bot_vars.starting_map),transition_delay_ms=1000,exit_condition=lambda:ArrivedOutpost(bot_vars.starting_map))),
    ('setting up'          , dict(execute_fn=lambda:DoSetup(),transition_delay_ms=100)),
    ('loading skillbar'    , dict(execute_fn=lambda:Combat.LoadSkillBar(Build.template),transition_delay_ms=1000)), 
    ('setting normal mode' , dict(execute_fn=lambda:Party.SetNormalMode(),transition_delay_ms=1000)),
    ('going to npc'        , dict(execute_fn=lambda:FollowPath(fsm_vars.path['npc'],fsm_vars.move),exit_condition=lambda:PathFinished(fsm_vars.path['npc'],fsm_vars.move),run_once=False)),
    ('targetting npc'      , dict(execute_fn=lambda:Keystroke.PressAndRelease(Key.V.value),transition_delay_ms=200)),
    ('talking to npc'      , dict(execute_fn=lambda:Keystroke.PressAndRelease(Key.Space.value),transition_delay_ms=700)),
    ('talking more'        , dict(execute_fn=lambda:Player.SendDialog(0x832105),transition_delay_ms=1000)),
    ('entering dungeon'    , dict(execute_fn=lambda:Player.SendDialog(0x88),exit_condition=lambda:ArrivedExplorable(bot_vars.dungeon_map))),
    ('setting up resign'   , dict(execute_fn=lambda:Player.Move(Path.rezone[0][0],Path.rezone[0][1]),exit_condition=lambda: Map.IsMapLoading())),
    ('loading Doolmore'    , dict(exit_condition=lambda:ArrivedOutpost(bot_vars.starting_map))),
    ('equipping staff'     , dict(execute_fn=lambda:Combat.ChangeWeaponSet(Build.staff),transition_delay_ms=1000)),
    ('starting lap timer'  , dict(execute_fn=lambda:StartLapTimer())),
    # farm loop
    ('targetting npc'      , dict(execute_fn=lambda:Keystroke.PressAndRelease(Key.V.value),transition_delay_ms=200)),
    ('talking to npc'      , dict(execute_fn=lambda:Keystroke.PressAndRelease(Key.Space.value),transition_delay_ms=1300)),
    ('talking more'        , dict(execute_fn=lambda:Player.SendDialog(0x832105),transition_delay_ms=1000)),
    ('entering dungeon'    , dict(execute_fn=lambda:Player.SendDialog(0x88),exit_condition=lambda:ArrivedExplorable(560))),
    ('going to prep loc'   , dict(execute_fn=lambda:FollowPath(fsm_vars.path['prep'],fsm_vars.move),exit_condition=lambda:PathFinished(fsm_vars.path['prep'],fsm_vars.move),run_once=False)),
    ('waiting...'          , dict(transition_delay_ms=3000)),
    ('prepping skills'     , dict(execute_fn=lambda:PrepSkills(),exit_condition=lambda:Combat.CheckBuffs([Build.vop, Build.mb, Build.ga, Build.vos]),run_once=False)),
    ('going to kill spot'  , dict(execute_fn=lambda:FollowPath(fsm_vars.path['kill'],fsm_vars.exact_move),exit_condition=lambda:PathFinished(fsm_vars.path['kill'],fsm_vars.exact_move),run_once=False)),
    ('waiting for enemies' , dict(exit_condition=lambda:WaitForSettle(200,3))),
    ('equipping scythe'    , dict(execute_fn=lambda:Combat.ChangeWeaponSet(Build.scythe),exit_condition=lambda:Agent.GetWeaponType(Player.GetAgentID())[1]=='Scythe')),
    ('killing enemies'     , dict(exit_condition=lambda:WaitForKill())),
    ('looting items'       , dict(execute_fn=lambda: Loot.PickUp(),run_once=False,exit_condition=lambda:Loot.Loop())),
    ('resigning'           , dict(execute_fn=lambda:Player.SendChatCommand("resign"),exit_condition=lambda:Party.IsPartyDefeated(),transition_delay_ms=1000)),
    ('returning'           , dict(execute_fn=lambda:Party.ReturnToOutpost(),exit_condition=lambda:ArrivedOutpost(bot_vars.starting_map))),
    # reset
    ('resetting farm loop' , dict(execute_fn=lambda:ResetVariables()))
]
for (state, kwargs) in fsm_main_states:
    fsm_vars.fsm.AddState(state,**kwargs)
# endregion

# region draw
def DrawWindow():
    global bot_vars, fsm_vars

    def log_state():
        if bot_vars.status != fsm_vars.fsm.get_current_step_name():
            if "FSM not started or finished" not in fsm_vars.fsm.get_current_step_name():
                bot_vars.time = datetime.now().strftime('%H:%M:%S')
                bot_vars.status = fsm_vars.fsm.get_current_step_name()

        PyImGui.text_colored(f'[{bot_vars.time}]', [.48, .68, 1, 1])
        PyImGui.same_line(0.0,-1.0)
        PyImGui.text(f'{bot_vars.status}')

    def make_table(*columns, colors = None):
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

    def format_item_stack(count):
        return f'{count} ({round(count/250,1)})'

    try:
        if bot_vars.window_module.first_run:
            PyImGui.set_next_window_size(bot_vars.window_module.window_size[0], bot_vars.window_module.window_size[1])     
            PyImGui.set_next_window_pos(bot_vars.window_module.window_pos[0], bot_vars.window_module.window_pos[1])
            bot_vars.window_module.first_run = False

        if PyImGui.begin(bot_vars.window_module.window_name, bot_vars.window_module.window_flags):

            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (.2,.2,.2,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (.3,.3,.3,1))
            if bot_vars.bot_started:
                if PyImGui.button('Stop', 220):
                    ResetVariables()
                    StopBot()
            else:
                if PyImGui.button('Start', 220):
                    ResetVariables()
                    StartBot()
            PyImGui.pop_style_color(2)

            log_state()

            tables = [
                {
                    'stats'  : ['Runs','Fails'],
                    'values' : [bot_vars.runs,
                                bot_vars.fails],
                    'colors' : [[0, .7, 0, 1],[1, .25, .23, 1]]
                },
                {
                    'stats'  : ['Average Pace','Total Time'],
                    'values' : [FormatTime(bot_vars.avg_time,mask='mm:ss'),
                                bot_vars.total_timer.FormatElapsedTime("hh:mm:ss")],
                    'colors' : [[.9,.9,.9,1]]*2
                },
                {
                    'stats'  : ['Bones','Bones/Hour'],
                    'values' : [format_item_stack(bot_vars.bone),
                                format_item_stack(round(bot_vars.bone_per_hour))],
                    'colors' : [[.89, .85, .79, 1]]*2
                }
            ]
            
            if bot_vars.show_extras:
                tables = [
                    {
                        'stats'  : ['Runs','Fails'],
                        'values' : [bot_vars.runs,
                                    bot_vars.fails],
                        'colors' : [[0, .7, 0, 1],[1, .25, .23, 1]]
                    },
                    {
                        'stats'  : ['Average Pace','Lap Time','Total Time'],
                        'values' : [FormatTime(bot_vars.avg_time,mask='mm:ss'),
                                    bot_vars.lap_timer.FormatElapsedTime("hh:mm:ss"),
                                    bot_vars.total_timer.FormatElapsedTime("hh:mm:ss")],
                        'colors' : [[.9,.9,.9,1]]*3
                    },
                    {
                        'stats'  : ['Bones','Starting Bones','Current Bones','Bones/Hour'],
                        'values' : [format_item_stack(bot_vars.bone),
                                    format_item_stack(bot_vars.starting_bone),
                                    format_item_stack(bot_vars.current_bone),
                                    format_item_stack(round(bot_vars.bone_per_hour))],
                        'colors' : [[.89, .85, .79, 1]]*4
                    }
                ]

            for table in tables:
                make_table(table['stats'],table['values'],colors = table['colors'])
        PyImGui.end()

    except Exception as e:
        current_function = inspect.currentframe().f_code.co_name
        Py4GW.Console.Log('BOT', f'Error in {current_function}: {str(e)}', Py4GW.Console.MessageType.Error)
        raise
# endregion

# region main
def main():
    global bot_vars, fsm_vars

    try:
        # draw gui
        if Party.IsPartyLoaded():
            DrawWindow()

        # throttle script calls
        if bot_vars.throttle_timer.GetElapsedTime() >= bot_vars.throttle_time:
            bot_vars.throttle_timer.Reset()
            # execute script
            if bot_vars.bot_started:
                if fsm_vars.fsm.is_finished():
                    ResetVariables()
                else:
                    if not bot_vars.action_queue.is_empty():
                        bot_vars.action_queue.execute_next()
                    fsm_vars.fsm.update()
                    HandleSkillbar()

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
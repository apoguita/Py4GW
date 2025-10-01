from Py4GWCoreLib import *
import math
import random

module_name = "Chahbek Village ZM farm"

#region coordinate lists
start_area_coordinate_list      = [
    (7696, 5279), (5626, 1542), (3088, 660)]
start_area_coordinate_list2     = [ 
    (3346, 69), (4550, -722), (4770, -1779)]

chahbek_village_coordinate      = [(4722, -6099)]

chahbek_village_zaishen_scout = [(4554, -9561)]
embark_beach_nf_area = [(2243, 3151), (2616, 3324)]
embark_beach_nf_area2 = [(2261, -1497), (2243, 3151), (2616, 3324)]
embark_beach_nf_goback = [(2195, 4140)]

embark_sand_near_rock = [(366,-2600)]
embark_sand_no_rock = [(1068,-3127)]

embark_beach_str = [(1685, -2352), (1956, -2250)]
embark_beach_handin = [(-627, -3204)]

chahbek_mission_coordinate_list = [
    (3003, -3550), (1785, -3549), (-175, -5908), (-2404, -6115),  
    (-3968, -6531), (-4391, -2261),  (-1955, 209), (-1621, 1145), 
    (-1353, -242), (-544, -1082), (-685, -3269), (-1981, -3805), 
    (-1982, -2814), (-4337, -1998)]
chahbek_mission_cata_one = [(-2998, -2775),(-1720, -2520)]
chahbek_mission_oil = [(-4337, -1998)]
chahbek_mission_cata_two = [(-2998, -2775),(-1731, -4138)]
#endregion

#region fsm states/flags
PREGAME_FSM_STATES = {
    "SYS: Logout for Reroll",
    "SYS: Delete Character",
    "SYS: Create New Character"
}

PROGRESS_FLAGS_ORDER = [
    "has_intro_run",
    "first_time_chahbek_village",
    "first_mission_run",
    "has_post_mission_run",
    "first_time_kamadan",
    "first_time_plains",
    "first_time_ssgh",
    "second_time_plains",
    "second_time_kamadan",
    "second_time_chahbek_village",
    "second_mission_run",
    "farmed_the_proof",
    "logged_out",
    "character_delete_confirmed",
    "character_created_successfully",
]

STATE_ENTRANCE_FLAG_MAP = {
    "EX: Nightfall Introduction": None,
    "OP: Village Part 1": "has_intro_run",
    "MS: Mission Run 1": "first_time_chahbek_village",
    "EX: Post-Mission": "first_mission_run",
    "OP: Kamadan, Jewel of Istan Part 1": "has_post_mission_run",
    "EX: Plains of Jarin Part 1": "first_time_kamadan",
    "OP: Sunspear Great Hall": "first_time_plains",
    "EX: Plains of Jarin Part 2": "first_time_ssgh",
    "OP: Kamadan, Jewel of Istan Part 2": "second_time_plains",
    "OP: Chahbek Village Part 2": "second_time_kamadan",
    "MS: Chahbek Village Run 2": "second_time_chahbek_village",
    "EX: Move to Kamadan": "second_mission_run",
    "OP: Depositing Proof of Triumph": "second_mission_run",
    "SYS: Logout for Reroll": "farmed_the_proof",
    "SYS: Delete Character": "logged_out",
    "SYS: Create New Character": "character_delete_confirmed",
}
#endregion

#region replace .movement.followXY with a unstuck version
class CustomFollowXYWithNudge(Routines.Movement.FollowXY):
    def __init__(self, tolerance=100, stuck_threshold_ms=10000, unstuck_distance=400, log_actions=False):
        super().__init__(tolerance)
        ConsoleLog("CustomFollowXY", "[INIT] Initialized custom FollowXY handler with nudge!", Console.MessageType.Info)

        self.stuck_threshold_ms: int = stuck_threshold_ms
        self.unstuck_distance: int = unstuck_distance
        self._last_player_pos: Tuple[float, float] = (0.0, 0.0)
        self._stuck_check_timer: Timer = Timer()
        self._stuck_cooldown_timer: Timer = Timer()
        self._stuck_check_interval_ms: int = 500 
        self._stuck_cooldown_ms: int = 4000
        self._min_pos_delta_for_not_stuck: float = 15.0
        self.in_unstuck_mode: bool = False
        self._unstuck_timeout_timer: Timer = Timer()
        self._UNSTUCK_TIMEOUT_MS: int = 10000
        self.unstuck_target: Optional[Tuple[float, float]] = None

    def move_to_waypoint(self, x: int = 0, y: int = 0, tolerance: Optional[int] = None, use_action_queue: bool = False):
        super().move_to_waypoint(x, y, tolerance, use_action_queue)

        if self.following:
            self._stuck_check_timer.Reset()
            self._stuck_cooldown_timer.Stop()
            self._last_player_pos = Player.GetXY()

    def reset(self):
        super().reset()
        self._stuck_check_timer.Stop()
        self._stuck_cooldown_timer.Stop()
        self._last_player_pos = (0.0, 0.0)

    def pause(self):
        super().pause()
        for timer in (self.timer, self.wait_timer, self._stuck_check_timer, self._stuck_cooldown_timer):
            timer.Pause()

    def resume(self):
        super().resume()
        for timer in (self.timer, self.wait_timer, self._stuck_check_timer, self._stuck_cooldown_timer):
            timer.Resume()
        self._last_player_pos = Player.GetXY()

    def _is_potentially_stuck(self, player_agent_id: int) -> bool:
        stuck = (self.following and
                not self.arrived and
                not Agent.IsMoving(player_agent_id) and
                not Agent.IsCasting(player_agent_id) and
                not Agent.IsKnockedDown(player_agent_id) and
                not Agent.IsDead(player_agent_id) and
                self.timer.HasElapsed(self.stuck_threshold_ms))
        return stuck

    def _attempt_unstuck_move(self, player_pos: Tuple[float, float], log_actions: bool = True):
        px, py = player_pos
        wx, wy = self.waypoint
        dx, dy = wx - px, wy - py
        dist_to_wp = math.hypot(dx, dy)

        if dist_to_wp < 25:
            return

        try:
            ndx, ndy = dx / dist_to_wp, dy / dist_to_wp
        except ZeroDivisionError:
            if log_actions:
                ConsoleLog("CustomFollowXY", "[UNSTUCK] Zero division error calculating direction, skipping.", Console.MessageType.Warning)
            return

        blockers = self._get_blocking_npcs(player_pos)

        if blockers:
            avg_bx, avg_by = (sum(coords[i] for coords in (Agent.GetXY(aid) for aid in blockers)) / len(blockers) for i in (0, 1))

            away_dx = px - avg_bx
            away_dy = py - avg_by
            away_dist = math.hypot(away_dx, away_dy)

            if away_dist == 0:
                away_dx, away_dy = -ndy, ndx
                away_dist = 1.0

            away_dx /= away_dist
            away_dy /= away_dist

            diag_dx = (away_dx - ndy) / math.sqrt(2)
            diag_dy = (away_dy + ndx) / math.sqrt(2)
            if log_actions:
                ConsoleLog("CustomFollowXY", "[UNSTUCK] Using NPC-aware diagonal escape.", Console.MessageType.Warning)
        else:
            flip = 1 if random.getrandbits(1) else -1
            diag_dx = -ndy * flip
            diag_dy = ndx * flip
            if log_actions:
                ConsoleLog("CustomFollowXY", "[UNSTUCK] No blockers found, using generic dodge.", Console.MessageType.Warning)

        move_dist = self.unstuck_distance
        temp_x = px + diag_dx * move_dist
        temp_y = py + diag_dy * move_dist
        if log_actions:
            ConsoleLog("CustomFollowXY", f"[UNSTUCK] Moving to ({temp_x:.0f}, {temp_y:.0f})", Console.MessageType.Warning)

        self._execute_unstuck_move(temp_x, temp_y)
        
    def _get_blocking_npcs(self, player_pos: Tuple[float, float]) -> List[int]:
        block_radius = Range.Touch.value + Range.Touch.value
        npcs = AgentArray.GetNPCMinipetArray()
        return [
            aid for aid in npcs
            if Agent.IsAlive(aid)
            and Agent.GetModelID(aid) in (4818, 4778, 4811)
            and Utils.Distance(player_pos, Agent.GetXY(aid)) <= block_radius
        ]

    def _execute_unstuck_move(self, temp_x: float, temp_y: float):
        self.unstuck_target = (temp_x, temp_y)
        Player.Move(0, 0)
        Player.Move(temp_x, temp_y)
        self.in_unstuck_mode = True
        self.following = True
        self.arrived = False
        self.timer.Start()
        self._unstuck_timeout_timer.Start()
        self._stuck_cooldown_timer.Start()
        self.wait_timer.Reset()
        self.wait_timer_run_once = True
    
    def _reset_unstuck_mode(self):
        self.in_unstuck_mode = False
        self._unstuck_timeout_timer.Stop()
        self.unstuck_target = None
        return
    
    def _arrive(self):
        self.arrived = True
        self.following = False
        self.timer.Stop()
        self.wait_timer.Stop()
        self._stuck_check_timer.Stop()
        self._stuck_cooldown_timer.Stop()
        return

    def _is_acting_or_moving(self, player_agent_id: int) -> bool:
        return (
            Agent.IsMoving(player_agent_id) or
            Agent.IsCasting(player_agent_id) or
            Agent.IsKnockedDown(player_agent_id) or
            Agent.IsDead(player_agent_id)
        )
    
    def _reissue_move(self, use_action_queue: bool):
        if not use_action_queue:
            Player.Move(0, 0)
            Player.Move(self.waypoint[0], self.waypoint[1])
        else:
            ActionQueueManager().AddAction("ACTION", Player.Move, 0, 0)
            ActionQueueManager().AddAction("ACTION", Player.Move, self.waypoint[0], self.waypoint[1])
    
    def update(self, log_actions: bool = False, use_action_queue: bool = False):
        if self._paused or not self.following:
            return

        current_position = Player.GetXY()
        player_agent_id = Player.GetAgentID()
        if player_agent_id == 0:
            if log_actions:
                ConsoleLog("CustomFollowXY", "[UPDATE_START] Skipping update: Player Agent ID is 0.", Console.MessageType.Warning)
            return

        if self.in_unstuck_mode:
            if self.calculate_distance(current_position, self.unstuck_target) <= self.tolerance:
                if log_actions:    
                    ConsoleLog("CustomFollowXY", "[UNSTUCK] Arrived at target during unstuck, resetting unstuck mode.", Console.MessageType.Info)
                self._reset_unstuck_mode()
                
            if self._unstuck_timeout_timer.HasElapsed(self._UNSTUCK_TIMEOUT_MS):
                if log_actions:
                    ConsoleLog("CustomFollowXY", "[UNSTUCK] Timeout, resetting unstuck mode.", Console.MessageType.Warning)
                self._reset_unstuck_mode()

        if self.calculate_distance(current_position, self.waypoint) <= self.tolerance:
            if log_actions:
                ConsoleLog("CustomFollowXY", f"[ARRIVAL] Arrived at waypoint ({self.waypoint[0]:.0f}, {self.waypoint[1]:.0f}).", Console.MessageType.Info)
            self._arrive()
            
        if self._is_acting_or_moving(player_agent_id):
            self._last_player_pos = current_position
            self._stuck_check_timer.Reset()
            self.wait_timer.Reset()
            self.wait_timer_run_once = True
            return

        if self._is_potentially_stuck(player_agent_id) and not self._stuck_cooldown_timer.IsRunning():
            if self._stuck_check_timer.HasElapsed(self._stuck_check_interval_ms):
                self._stuck_check_timer.Reset()
                if self.calculate_distance(current_position, self._last_player_pos) < self._min_pos_delta_for_not_stuck:
                    ConsoleLog("CustomFollowXY", "[UNSTUCK] AM I STUCK?.", Console.MessageType.Warning)
                    self._attempt_unstuck_move(current_position)
                    self._last_player_pos = current_position
                    return
                self._last_player_pos = current_position

        if not self.wait_timer_run_once and self.wait_timer.HasElapsed(1000):
            self.wait_timer.Reset()
            self.wait_timer_run_once = True

        if self.wait_timer_run_once and (not self._stuck_cooldown_timer.IsRunning() or self._stuck_cooldown_timer.HasElapsed(self._stuck_cooldown_ms)):
            self._reissue_move(use_action_queue)
            self.wait_timer_run_once = False

        if not self._stuck_cooldown_timer.IsRunning():
            self._last_player_pos = current_position
#endregion

class BotVars:  
    def __init__(self):
        self.bot_started = False
        self.combat_started = False
        self.pause_combat_fsm = False
        # --- Run Statistics ---
        self.global_timer = Timer()
        self.lap_timer = Timer()
        self.lap_history = []
        self.min_time = 0
        self.max_time = 0
        self.avg_time = 0.0
        self.runs_attempted = 0
        self.success_rate = 0.0
        self.proofs_deposited = 0
        #Map_IDs
        self.island_of_shehkah = 490
        self.chahbek_village = 544
        self.embark_beach = 857
        self.chahbek_mission = 544
        self.churrhir_fields = 456
        self.kamadan = 449
        self.plains_of_jarin = 430
        self.sunspear_great_hall = 431
        #Check_Variables
        self.summoned_imp: bool = False
        self.has_intro_run: bool = False
        self.pre_chahbek_village: bool = False
        self.first_embark: bool = False
        self.first_time_chahbek_village: bool = False
        self.first_mission_run: bool = False
        self.second_embark: bool = False
        self.has_post_mission_run: bool = False
        self.first_time_kamadan: bool = False
        self.first_time_plains: bool = False
        self.first_time_ssgh: bool = False
        self.second_time_plains: bool = False
        self.second_time_kamadan: bool = False
        self.second_time_chahbek_village: bool = False
        self.second_mission_run: bool = False
        self.farmed_the_proof: bool = False
        self.logged_out: bool = False
        #trainer data
        self.trainer_location: Tuple[int, int] = (0, 0)
        #Item_Model_IDs
        self.igneous_summoning_stone = 30847
        self.proof_of_legend = 37841
        self.copper_coin = 31202
        #logout stuff
        self.oldclipboard = ""
        self.character_index: int = -1
        self.char_select_current_index: int = -99
        self.character_names: List[str] = []
        self.new_char_name_input: str = ""
        self.next_create_index: int = 0
        self.character_to_delete_name: str = ""
        self.character_delete_confirmed: bool = False
        self.character_created_successfully: bool = False
        self.press_key_aq = ActionQueueNode(120)
        #Debug
        self.test = False
        #dialog frame
        self._last_dialog_frame_ids: Dict[str, Optional[int]] = {}
        self.frame_paths = {
            "char_select_delete_button": 3379687503,
            "char_select_delete_confirm_text": (140452905, [5, 1, 15,0]),
            "char_select_delete_name_input": (140452905, [5, 1, 15, 1]),
            "char_select_delete_final_button": (140452905, [5, 1, 15, 2]),
            "char_select_create_button": 3372446797,
            "char_select_create_button2": 3973689736,
            "char_select_sort_dropdown": 2232987037,
            "char_create_type_next_button": 3110341991,
            "char_create_bottom_frame": 921917835,
            "char_create_generic_next_button": 1102119410,
            "char_create_profession_tab_text": (921917835, [1, 1]),
            "char_create_sex_tab_text": (921917835, [2, 1]),
            "char_create_campaign_tab_text": (921917835, [0, 1]),
            "char_create_appearance_tab_text": (921917835, [3, 1]),
            "char_create_body_tab_text": (921917835, [4, 1]),
            "char_create_name_tab_text": 2029278512,
            "char_create_name_input": (408279500, [1, 1]),
            "char_create_final_button": 3856299307,
            "drop_bundle_button":(5040781, [0,0]),
        }
        self.character_name_logged = False
        self.request_name = False
        self.window_module = ImGui.WindowModule()

bot_vars = BotVars()
bot_vars.window_module = ImGui.WindowModule(module_name, window_name=module_name, window_size=(300, 300), 
                                            window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
combat_handler:SkillManager.Autocombat = SkillManager.Autocombat()

class StateMachineVars:
    def __init__(self):
        self.state_machine                  = FSM("Proof of Triumph Farm")
        self.global_combat_fsm              = FSM("Global Combat Monitor")
        self.global_combat_handler          = FSM("Interruptible Combat")
        #Movement Handler
        # self.movement_handler               = Routines.Movement.FollowXY()
        self.movement_handler               = CustomFollowXYWithNudge(unstuck_distance=500, log_actions=True)
        
        #Start check:has_intro_run
        self.nightfall_intro                = FSM("Nightfall Intro")
        self.nightfall_intro_pathing        = Routines.Movement.PathHandler(start_area_coordinate_list)
        self.nightfall_intro_pathing2       = Routines.Movement.PathHandler(start_area_coordinate_list2)
        #first_chahbek_village  check:first_time_chahbek_village
        self.pre_chahbek_village            = FSM("pre Chah Village")
        self.pre_chahbek_village_pathing    = Routines.Movement.PathHandler(chahbek_village_zaishen_scout)
        
        self.first_embark_beach            = FSM("First Embark Beach")
        self.first_eb_flag_pathing          = Routines.Movement.PathHandler(embark_beach_nf_area)
        self.first_eb_flag_pathing_alt      = Routines.Movement.PathHandler(embark_beach_nf_area2)
        self.first_eb_exit_pathing          = Routines.Movement.PathHandler(embark_beach_nf_goback)
        self.eb_path:                         Optional[Routines.Movement.PathHandler] = None
        
        self.first_chahbek_village          = FSM("Chahbek Village")
        self.first_chahbek_village_pathing  = Routines.Movement.PathHandler(chahbek_village_coordinate)
        #chahbek_mission
        self.chahbek_mission                = FSM("Chahbek Village Mission")
        self.chahbek_mission_pathing        = Routines.Movement.PathHandler(chahbek_mission_coordinate_list)
        self.chahbek_mission_cata_one       = Routines.Movement.PathHandler(chahbek_mission_cata_one)
        self.chahbek_mission_oil            = Routines.Movement.PathHandler(chahbek_mission_oil)
        self.chahbek_mission_cata_two       = Routines.Movement.PathHandler(chahbek_mission_cata_two)
        
        self.port_to_embark                 = FSM("GOING TO EB")

        self.second_embark                  = FSM("Second Embark Beach")
        self.embark_beach_str               = Routines.Movement.PathHandler(embark_beach_str)
        self.embark_beach_hand              = Routines.Movement.PathHandler(embark_beach_handin)
        
        self.finish_up_deposit              = FSM("Deposit Proof and Logout")
        
        self.logout_character               = FSM("Logout Character")
        self.delete_character               = FSM("Delete Character")   
        self.create_character               = FSM("Create Character")   
        
fsm_vars = StateMachineVars()

#region functions  
def reset_variables():
    flags = [
        "summoned_imp", "has_intro_run", "first_time_chahbek_village", "first_mission_run",
        "has_post_mission_run", "first_time_kamadan", "first_time_plains", "first_time_ssgh",
        "second_time_plains", "second_time_kamadan", "second_time_chahbek_village",
        "second_mission_run", "farmed_the_proof", "logged_out", 
        "character_delete_confirmed", "character_created_successfully", "pre_chahbek_village",
        "first_embark", "second_embark"
    ]
    for flag in flags:
        setattr(bot_vars, flag, False)
    reset_state_variables()
    clear_frame_click_retry_cache()

def start_bot():
    bot_vars.bot_started = True
    bot_vars.global_timer.Start()
    bot_vars.lap_timer.Start()
    if not bot_vars.character_to_delete_name and not bot_vars.character_names:
        if (Agent.GetProfessionNames(Player.GetAgentID())[0] == "Dervish" or
            Agent.GetProfessionNames(Player.GetAgentID())[0] == "Warrior"):
            ConsoleLog("Character", f"Setting Name to Current Character {get_player_name()}", Console.MessageType.Warning)
        else:
            ConsoleLog("Character", "Player is not a Class this was designed for!", Console.MessageType.Error)
            stop_bot()
            return
    fsm_vars.state_machine.start()
    fsm_vars.global_combat_fsm.start()

def stop_bot(): 
    bot_vars.bot_started = False
    bot_vars.combat_started = False
    bot_vars.global_timer.Stop()
    bot_vars.lap_timer.Stop()

def start_new_run():
    bot_vars.lap_timer.Reset()
    bot_vars.lap_timer.Start()
    bot_vars.runs_attempted += 1

def complete_run(success: bool):
    duration = bot_vars.lap_timer.GetElapsedTime()
    bot_vars.lap_timer.Stop()
    if not success:
        return
    bot_vars.lap_history.append(duration)
    bot_vars.proofs_deposited += 1
    bot_vars.min_time = min(bot_vars.lap_history)
    bot_vars.max_time = max(bot_vars.lap_history)
    bot_vars.avg_time = int(sum(bot_vars.lap_history) / len(bot_vars.lap_history))
    bot_vars.success_rate = (bot_vars.proofs_deposited / bot_vars.runs_attempted)
    ConsoleLog("Stats", f"Run Completed! Time: {FormatTime(duration, 'mm:ss:ms')}", Console.MessageType.Success)

def is_bot_started(): 
    return bot_vars.bot_started

def check_combat():
    return Routines.Checks.Agents.InDanger()

def start_combat(): bot_vars.combat_started = True

def stop_combat(): bot_vars.combat_started = False

def set_pathing_paused(paused: bool = True):
    for name, attr in vars(fsm_vars).items():
        if attr.__class__.__name__ in ("FSM", "ConditionState"):
            continue
        if hasattr(attr, "pause") and hasattr(attr, "resume"):
            (attr.pause if paused else attr.resume)()

def pause_all(debug: bool = False):
    if not check_combat():
        return
    if not fsm_vars.state_machine.is_paused():
        if debug: ConsoleLog("FSM", "[DEBUG] Pausing Main FSM", Py4GW.Console.MessageType.Warning)
        fsm_vars.state_machine.pause()
    if debug: ConsoleLog("FSM", "[DEBUG] Pausing Movement", Py4GW.Console.MessageType.Warning)
    set_pathing_paused(True)

def resume_all(debug: bool = False):
    if check_combat():
        return
    if fsm_vars.state_machine.is_paused():
        if debug: ConsoleLog("FSM", "[DEBUG] Resuming Main FSM", Py4GW.Console.MessageType.Warning)
        fsm_vars.state_machine.resume()
    if debug: ConsoleLog("FSM", "[DEBUG] Resuming Movement", Py4GW.Console.MessageType.Warning)
    set_pathing_paused(False)
    
def mark_flag(flag_name: str, value, debug: bool = False):
    return lambda: (setattr(bot_vars, flag_name, value), print(f"[FSM] Marked {flag_name} = {value}") if debug else None)

def get_player_name():
    target = Player.GetAgentID()
    if not bot_vars.request_name:
        Agent.RequestName(target)
        bot_vars.request_name = True
        return ""

    if Agent.IsNameReady(target):
        return Agent.GetName(target)
    return ""

def add_player_name_if_new(log_actions=False):
    name = get_player_name()
    if name and name not in bot_vars.character_names:
        bot_vars.character_names.append(name)
        delete_index = (bot_vars.next_create_index - 1 + len(bot_vars.character_names)) % len(bot_vars.character_names)
        bot_vars.character_to_delete_name = bot_vars.character_names[delete_index]
        if log_actions:
            ConsoleLog("Character", f"Initial delete target set to: {bot_vars.character_to_delete_name}", Console.MessageType.Info)
        return True
    return False

def check_character_name_added():
    if add_player_name_if_new(log_actions=True) and not bot_vars.character_name_logged:
        ConsoleLog("Character", "CHARACTER NAME ADDED", Console.MessageType.Info)
        bot_vars.character_name_logged = True
        
def reset_character_name_logged():
    bot_vars.character_name_logged = False

def equip_item(model_id):
    item = Item.GetItemIdFromModelID(model_id)
    agent_id = Player.GetAgentID() 
    Inventory.EquipItem(item, agent_id)

def equip_starter():
    if Agent.GetProfessionNames(Player.GetAgentID())[0] == "Dervish":
        equip_item(15591)
    if Agent.GetProfessionNames(Player.GetAgentID())[0] == "Warrior":
        equip_item(2982)
  
def equip_weapon():
    if Agent.GetProfessionNames(Player.GetAgentID())[0] == "Dervish":
        return
    if Agent.GetProfessionNames(Player.GetAgentID())[0] == "Warrior":
        equip_item(6060)
  
def deposit_proof():
    ActionQueueManager().AddAction("ACTION", Inventory.DepositItemToStorage, Item.GetItemIdFromModelID(bot_vars.proof_of_legend))
    
def deposit_coin():
    mark_flag("farmed_the_proof", True)()
    ActionQueueManager().AddAction("ACTION", Inventory.DepositItemToStorage, Item.GetItemIdFromModelID(bot_vars.copper_coin))

def summon_imp_if_needed():
    if bot_vars.summoned_imp:
        return
    Inventory.UseItem(Item.GetItemIdFromModelID(bot_vars.igneous_summoning_stone))
    bot_vars.summoned_imp = True

def nearest_henchman_xy(x,y, distance):
    scan_pos = (x, y)
    ally_array = AgentArray.Sort.ByDistance(
        AgentArray.Filter.ByDistance(AgentArray.GetAllyArray(), scan_pos, distance),
        scan_pos
    )
    return ally_array[0] if ally_array else 0

def nearest_gadget_xy(x,y, distance):
    scan_pos = (x, y)
    gadget_array = AgentArray.Sort.ByDistance(
        AgentArray.Filter.ByDistance(AgentArray.GetGadgetArray(), scan_pos, distance),
        scan_pos
    )
    return gadget_array[0] if gadget_array else 0

def load_skill_bar():
    if Agent.GetProfessionNames(Player.GetAgentID())[0] == "Dervish":
        if not bot_vars.first_mission_run:
            SkillBar.LoadSkillTemplate("OgCikKsxIeluAAAAAAAAAAAA")
            SkillBar.LoadHeroSkillTemplate(1, "OQASEDqEC1vcNABWAAAA")
    elif Agent.GetProfessionNames(Player.GetAgentID())[0] == "Warrior":
        if not bot_vars.first_mission_run:
            SkillBar.LoadSkillTemplate("OQATEjpUjIACVAAAAAAAAAA")
            SkillBar.LoadHeroSkillTemplate(1, "OQASEDqEC1vcNABWAAAA")
    else:
        return

def has_arrived():
    return lambda: Routines.Targeting.HasArrivedToTarget()

def locate_embark_spawm():
    player_pos = Player.GetXY()
    # x,y = Player.GetXY()
    # dx, dy = x - 232, y - (-2647)
    dist = Utils.Distance(player_pos, (1068,-3127))
    # dist = math.hypot(dx, dy)
    if dist < 600:  # adjust radius as needed
        print("alt spawn")
        fsm_vars.eb_path = fsm_vars.first_eb_flag_pathing_alt
    else:
        print("normal spawn")
        fsm_vars.eb_path = fsm_vars.first_eb_flag_pathing

_target_interact_throttle = {}
def target_and_interact(*args, dist: int = 20, cooldown: float = 1.0, target_type: str ="npc"):
    if len(args) == 1 and isinstance(args[0], tuple):
        x, y = args[0]
    elif len(args) == 2:
        x, y = args
    else:
        raise ValueError("target_and_interact expects (x, y) or (x, y, dist)")

    fn_id = f"target_interact_{x}_{y}_{target_type}"

    def throttled():
        now = time.time()
        if now - _target_interact_throttle.get(fn_id, 0) < cooldown:
            return

        _target_interact_throttle[fn_id] = now
        agent = nearest_gadget_xy(x, y, dist) if target_type == "gadget" else Routines.Agents.GetNearestNPCXY(x, y, dist)

        ActionQueueManager().AddAction("ACTION", Player.ChangeTarget, agent)
        ActionQueueManager().AddAction("ACTION", Routines.Targeting.InteractTarget)

    return throttled

def check_active_quest(quest_id: int):
    return quest_id == Quest.GetActiveQuest()

def check_quest_completed(quest_id: int):
    return Quest.IsQuestCompleted(quest_id)

def check_dialog_buttons(buttons: int, size: Optional[str] = None, state_key: Optional[str] = None, debug: bool = False):
    npc_dialog_hash = 3856160816
    npc_dialog_offset = [2, 0, 0, 1]
    frame_id = UIManager.GetFrameIDByHash(npc_dialog_hash)

    if frame_id == 0 or not UIManager.IsVisible(frame_id):
        if debug:
            print("[DEBUG] Dialog frame not found or not visible.")
        return False

    if state_key:
        frame_ids = bot_vars.__dict__.setdefault("_last_dialog_frame_ids", {})
        last_id = frame_ids.get(state_key)
        if last_id == frame_id:
            if debug:
                print(f"[DEBUG] State '{state_key}': Same dialog frame ID {frame_id}, skipping.")
            return False
        if debug:
            print(f"[DEBUG] State '{state_key}': Dialog frame changed from {last_id} → {frame_id}")
        frame_ids[state_key] = frame_id

    button_ids = UIManager.GetAllChildFrameIDs(npc_dialog_hash, npc_dialog_offset)

    if size:
        def size_filter(fid):
            height = PyUIManager.UIFrame(fid).position.height_on_screen
            return (size == "big" and height > 37) or \
                   (size == "medium" and 30 <= height <= 37) or \
                   (size == "small" and height < 30)
        button_ids = [fid for fid in button_ids if size_filter(fid)]

    if debug:
        print(f"[DEBUG] Button size = {size}")
        for fid in button_ids:
            h = PyUIManager.UIFrame(fid).position.height_on_screen
            print(f"[DEBUG] - Frame ID {fid} → height: {h}")
        print(f"[DEBUG] Total Buttons (size={size}): {len(button_ids)}, Required: {buttons}")

    return len(button_ids) == buttons

def clear_dialog_tracking(state_key: Optional[str] = None):
    if not hasattr(bot_vars, "_last_dialog_frame_ids"):
        return
    if state_key:
        bot_vars._last_dialog_frame_ids.pop(state_key, None)
    else:
        bot_vars._last_dialog_frame_ids.clear()

def is_npc_dialog_hidden(debug: bool = False):
    frame_id = UIManager.GetFrameIDByHash(3856160816)
    if debug:
        print(f"[Debug] Dialog frame ID: {frame_id}")
        print(f"[Debug] IsVisible: {UIManager.IsVisible(frame_id) if frame_id else 'N/A'}")
    return frame_id == 0 or not UIManager.IsVisible(frame_id)

def click_dialog_button(button: int, size: Optional[str] = None, backup: Optional[str] = None, debug: bool = False):
    npc_dialog_hash = 3856160816
    frame_id = UIManager.GetFrameIDByHash(npc_dialog_hash) 

    if frame_id == 0 or not UIManager.IsVisible(frame_id):
        if debug: print(f"Parent frame not found or not visible: {npc_dialog_hash}")
        return False

    all_ids = UIManager.GetAllChildFrameIDs(npc_dialog_hash, [2, 0, 0, 1])

    if size:
        def size_filter(fid):
            height = PyUIManager.UIFrame(fid).position.height_on_screen
            return (size == "big" and height > 37) or \
                   (size == "medium" and 30 <= height <= 37) or \
                   (size == "small" and height < 30)
        all_ids = [fid for fid in all_ids if size_filter(fid)]

    sorted_frames = UIManager.SortFramesByVerticalPosition(all_ids)
    index = button - 1  # 1-based to 0-based

    if debug:
        print(f"Requested button: {button} (size={size})")
        for fid, y in sorted_frames:
            h = PyUIManager.UIFrame(fid).position.height_on_screen
            print(f" - Frame ID {fid} at Y={y} → height: {h}")
        print(f"Sorted frame IDs (top to bottom): {[fid for fid, _ in sorted_frames]}")

    if not (0 <= index < len(sorted_frames)):
        if debug:
            print(f"Button index {button} out of range (found {len(sorted_frames)} frames)")
        return False

    target_id = sorted_frames[index][0]
    scroll_id = UIManager.IsVisible(UIManager.GetChildFrameID(npc_dialog_hash, [2, 3]))
    
    if scroll_id and backup:
        ActionQueueManager().AddAction("ACTION", Player.SendDialog, int(backup, 16))
        return True

    ActionQueueManager().AddAction("ACTION", UIManager.FrameClick, target_id)
    return True

click_retry_tracker = {}
def click_dialog_button_retry(button: int, retry_delay: float = 1.0, size: Optional[str] = None, backup: Optional[str] = None, debug: bool = False):
    fn_id = f"click_retry_btn_{button}_{size or 'any'}"
    now = time.time()
    if now - click_retry_tracker.get(fn_id, 0) < retry_delay:
        return False
    click_retry_tracker[fn_id] = now
    return click_dialog_button(button, size=size, backup=backup, debug=debug)

def clear_click_retry_cache():
    click_retry_tracker.clear()

LEVEL_THRESHOLDS = {
    2: 	2000,	
    3: 	4600,	
    4: 	7800, 	
    5: 	11600, 	
    6: 	16000,	
    7: 	21000,	
    8: 	26600,	
    9: 	32800,	
    10: 39600,	
    11: 47000,	
    12: 55000,	
    13: 63600,	
    14: 72800,	
    15: 82600,
    16: 93000,
    17: 104000,
    18: 115600,
    19: 127800,
    20: 140600
}
def check_level_threshold(threshold: int):
    xp = Player.GetExperience()
    return xp >= threshold

def is_level(level: int):
    return (xp := LEVEL_THRESHOLDS.get(level)) is not None and Player.GetExperience() >= xp

def is_within_xp_gap(target_level: int, gap: int):
    return (xp := LEVEL_THRESHOLDS.get(target_level)) is not None and Player.GetExperience() >= xp - gap

def reset_paths_and_handler(*paths):
    return lambda: ([(p.reset()) for p in paths], fsm_vars.movement_handler.reset())

def reset_state_variables(state: Optional[str] = None):
    if state:
        print(state)
    [attr.reset() for attr in vars(fsm_vars).values() if isinstance(attr, Routines.Movement.PathHandler)]
    fsm_vars.movement_handler.reset()
    clear_click_retry_cache()
    clear_dialog_tracking()

def is_in_character_select():
    if Party.IsPartyLoaded():
        return False
    
    cs_base = UIManager.GetFrameIDByHash(2232987037)
    cs_c0 = UIManager.GetChildFrameID(2232987037, [0])
    cs_c1 = UIManager.GetChildFrameID(2232987037, [1])
    ig_menu = UIManager.GetFrameIDByHash(1144678641)
    
    frames = {
        "cs_base": cs_base,
        "cs_c0": cs_c0,
        "cs_c1": cs_c1,
        "ig_menu": ig_menu,
    }
    
    in_load_screen = all(isinstance(f, int) and f == 0 for f in frames.values())
    in_char_select = (
        not in_load_screen and
        any(isinstance(f, int) and f > 0 for f in (cs_base, cs_c0, cs_c1)) and 
        not Party.IsPartyLoaded()
    )
    
    return in_char_select

def is_in_load_screen():
    if Party.IsPartyLoaded():
        return False
    
    cs_base = UIManager.GetFrameIDByHash(2232987037)
    cs_c0 = UIManager.GetChildFrameID(2232987037, [0])
    cs_c1 = UIManager.GetChildFrameID(2232987037, [1])
    ig_menu = UIManager.GetFrameIDByHash(1144678641)
    
    frames = {
        "cs_base": cs_base,
        "cs_c0": cs_c0,
        "cs_c1": cs_c1,
        "ig_menu": ig_menu,
    }
    
    in_load_screen = all(isinstance(f, int) and f == 0 for f in frames.values())

    return in_load_screen

def in_character_select():
    return is_in_character_select()

def is_char_select_context_ready():
    return in_character_select() and (pregame := Player.GetPreGameContext()) and pregame.chars is not None
     
def is_char_select_ready():
    return is_char_select_context_ready()

def is_target_selected():
    return is_char_select_context_ready() and Player.GetPreGameContext().index_1 == bot_vars.character_index

def initiate_logout(debug: bool = False):
    if not bot_vars.character_to_delete_name:
        if debug:
            ConsoleLog("initiate_logout", "Target character name (for deletion) not set!", Console.MessageType.Error)
        fsm_vars.logout_character.stop()
        return
    if debug:
        ConsoleLog("initiate_logout", f"Initiating logout to select '{bot_vars.character_to_delete_name}' for deletion...", Console.MessageType.Info)
    Player.LogoutToCharacterSelect()
    bot_vars.character_index = bot_vars.char_select_current_index = -99

def find_target_character(debug: bool = False):
    if not is_char_select_context_ready():
        if debug:
            ConsoleLog("find_target_character", "Char select context not ready during find action.", Console.MessageType.Warning)
        return

    pregame = Player.GetPreGameContext()
    target_name = bot_vars.character_to_delete_name
    
    try:
        if not pregame.chars:
            if debug:
                ConsoleLog("find_target_character", "Character list (pregame.chars) is None or empty.", Console.MessageType.Warning)
            return
        
        target_lower = target_name.lower()
        for i, char_name in enumerate(pregame.chars):
            if target_lower == char_name.lower():
                bot_vars.character_index = i
                bot_vars.char_select_current_index = pregame.index_1
                if debug:
                    ConsoleLog("find_target_character", f"Found deletion target '{target_name}' at index {i}. Current selection: {bot_vars.char_select_current_index}", Console.MessageType.Info)
                return

    except Exception as e:
        ConsoleLog("find_target_character", f"Error accessing character list: {e}", Console.MessageType.Error)
        fsm_vars.logout_character.stop()

def navigate_char_select(debug: bool = False):
    if not is_char_select_context_ready():
        if debug:
            ConsoleLog("navigate_char_select", "Char select context not ready during navigate action.", Console.MessageType.Warning)
        return

    pregame = Player.GetPreGameContext()
    current_index = pregame.index_1

    if current_index == bot_vars.character_index:
        if debug:
            ConsoleLog("navigate_char_select", "Target already selected, skipping navigation.", Console.MessageType.Debug)
        return

    bot_vars.char_select_current_index = current_index
    distance = bot_vars.character_index - current_index

    if debug:
        direction = "Right" if distance > 0 else "Left"
        ConsoleLog("navigate_char_select", f"Navigating {direction} (Current: {current_index}, Target: {bot_vars.character_index})", Console.MessageType.Debug)
    
    if distance > 0:
        Keystroke.PressAndRelease(Key.RightArrow.value)
    elif distance < 0:
        Keystroke.PressAndRelease(Key.LeftArrow.value)

_frame_click_retry_tracker = {}
def click_frame_retry(frame_id_or_path, retry_delay: float = 1.5, debug: bool = False):
    if isinstance(frame_id_or_path, int):
        frame_id = UIManager.GetFrameIDByHash(frame_id_or_path)
        frame_key = str(frame_id_or_path)
    elif isinstance(frame_id_or_path, tuple) and len(frame_id_or_path) == 2:
        parent_hash, offsets = frame_id_or_path
        all_ids = UIManager.GetAllChildFrameIDs(parent_hash, offsets)
        frame_id = all_ids[0] if all_ids else 0
        frame_key = f"{parent_hash}_{'_'.join(map(str, offsets))}"
    else:
        if debug:
            ConsoleLog("click_frame_retry", f"Invalid frame identifier: {frame_id_or_path}", Console.MessageType.Error)
        return False

    fn_id = f"click_retry_{frame_key}"
    now = time.time()

    if now - _frame_click_retry_tracker.get(fn_id, 0) < retry_delay:
        if debug:
            ConsoleLog("click_frame_retry", f"Throttled: {fn_id}", Console.MessageType.Debug)
        return False

    _frame_click_retry_tracker[fn_id] = now

    if frame_id != 0 and UIManager.FrameExists(frame_id):
        if debug:
            ConsoleLog("click_frame_retry", f"Clicking Frame ID: {frame_id} (Key: {frame_key})", Console.MessageType.Debug)
        ActionQueueManager().AddAction("ACTION", UIManager.FrameClick, frame_id)
        return True

    if debug:
        ConsoleLog("click_frame_retry", f"Frame not found or not visible: {frame_id} (Key: {frame_key})", Console.MessageType.Warning)
    return False

def click_frame_once(frame_id_or_path, debug: bool = False):
    if isinstance(frame_id_or_path, int):
        frame_id = UIManager.GetFrameIDByHash(frame_id_or_path)
        frame_key = str(frame_id_or_path)
    elif isinstance(frame_id_or_path, tuple) and len(frame_id_or_path) == 2:
        parent_hash, offsets = frame_id_or_path
        all_ids = UIManager.GetAllChildFrameIDs(parent_hash, offsets)
        frame_id = all_ids[0] if all_ids else 0
        frame_key = f"{parent_hash}_{'_'.join(map(str, offsets))}"
    else:
        if debug:
            ConsoleLog("click_frame_once", f"Invalid frame identifier: {frame_id_or_path}", Console.MessageType.Error)
        return False

    if frame_id != 0 and UIManager.FrameExists(frame_id):
        if debug:
            ConsoleLog("click_frame_once", f"Clicking Frame ID: {frame_id} (Key: {frame_key})", Console.MessageType.Debug)
        return UIManager.FrameClick(frame_id)

    if debug:
        ConsoleLog("click_frame_once", f"Frame not found or not visible: {frame_id} (Key: {frame_key})", Console.MessageType.Warning)
    return False

def clear_frame_click_retry_cache(debug: bool = False):
    _frame_click_retry_tracker.clear()
    if debug:
        ConsoleLog("Helpers", "Cleared frame click retry cache.", Console.MessageType.Info)

def check_frame_visible(frame_id_or_path, debug: bool = False):
    if frame_id_or_path is None:
        if debug:
            ConsoleLog("check_frame_visible", "Frame path is None.", Console.MessageType.Warning)
        return False

    try:
        if isinstance(frame_id_or_path, int):
            frame_id = UIManager.GetFrameIDByHash(frame_id_or_path)
        elif isinstance(frame_id_or_path, tuple) and len(frame_id_or_path) == 2:
            parent_hash, offsets = frame_id_or_path
            all_ids = UIManager.GetAllChildFrameIDs(parent_hash, offsets) or []
            frame_id = next((fid for fid in all_ids if UIManager.FrameExists(fid)), 0)
        else:
            if debug:
                ConsoleLog("check_frame_visible", f"Invalid frame identifier: {frame_id_or_path}", Console.MessageType.Error)
            return False

        exists = frame_id != 0 and UIManager.FrameExists(frame_id)
        if debug:
            ConsoleLog("check_frame_visible", f"Checking visibility for {frame_id_or_path} -> ID: {frame_id}, Exists: {exists}", Console.MessageType.Debug)
        return exists

    except Exception as e:
        if debug:
            ConsoleLog("check_frame_visible", f"Exception checking frame visibility: {e}", Console.MessageType.Error)
        return False

def press_key_repeat(key_value: int, times: int, debug: bool = False):
    if debug:
        ConsoleLog("press_key_repeat", f"Queueing key {key_value} press {times} times.", Console.MessageType.Debug)
    for _ in range(times):
        bot_vars.press_key_aq.add_action(Keystroke.PressAndRelease, key_value)

def is_char_name_gone(name: str, debug: bool = False):
    if not is_in_character_select():
        if debug:
            ConsoleLog("is_char_name_gone", "Not in char select screen.", Console.MessageType.Debug)
        return False
    
    try:
        characters = Player.GetLoginCharacters()
        if not characters:
            if debug:
                ConsoleLog("is_char_name_gone", "Character list is None.", Console.MessageType.Warning)
            return False

        is_gone = name not in [char.player_name for char in characters]
        if debug:
            ConsoleLog("is_char_name_gone", f"Checking if '{name}' is gone. Found: {[c.player_name for c in characters]}. Is gone: {is_gone}", Console.MessageType.Debug)
        return is_gone

    except Exception as e:
        ConsoleLog("is_char_name_gone", f"Error checking character list: {e}", Console.MessageType.Error)
        return False

def _stop_fsm_on_timeout(fsm_name: str, state_name: str):
    ConsoleLog(fsm_name, f"Timeout occurred in state: {state_name}", Console.MessageType.Error)
    fsm_attr = fsm_name.lower().replace(" ", "_")
    fsm_to_stop = getattr(fsm_vars, fsm_attr, None)

    if not (fsm_to_stop and isinstance(fsm_to_stop, FSM)):
        ConsoleLog(fsm_name, f"Could not find FSM attribute '{fsm_attr}' to stop on timeout.", Console.MessageType.Error)
        return

    if not fsm_to_stop.is_finished():
        ConsoleLog(fsm_name, "Stopping FSM due to timeout.", Console.MessageType.Warning)
        fsm_to_stop.stop()
         
def _is_target_character_selected(target_name: str, debug: bool = False):
    if not is_char_select_context_ready():
        if debug:
            ConsoleLog("_is_target_character_selected", "Context not ready.", Console.MessageType.Debug)
        return False

    pregame = Player.GetPreGameContext()
    current_index = pregame.index_1

    if not (pregame.chars and 0 <= current_index < len(pregame.chars)):
        if debug:
            ConsoleLog("_is_target_character_selected", f"Current index {current_index} out of bounds or chars list empty/None.", Console.MessageType.Warning)
        return False

    selected_name = pregame.chars[current_index].lower()
    is_correct = selected_name == target_name.lower()

    if debug:
        if is_correct:
            ConsoleLog("_is_target_character_selected", f"Correct character selected: Index {current_index} -> '{selected_name}'", Console.MessageType.Debug)
        else:
            ConsoleLog("_is_target_character_selected", f"WRONG character selected: Index {current_index} -> '{selected_name}', expected '{target_name}'", Console.MessageType.Warning)

    return is_correct

def check_button_enabled_and_click(frame_id_or_path, enabled_field_value=18692, field_name="field91_0x184", retry_delay=1.5, debug=False):
    if frame_id_or_path is None:
        if debug:
            ConsoleLog("check_frame_visible", "Frame path is None.", Console.MessageType.Warning)
        return False
    
    try:
        if isinstance(frame_id_or_path, int):
            frame_id = UIManager.GetFrameIDByHash(frame_id_or_path)
            frame_key = str(frame_id_or_path)
        elif isinstance(frame_id_or_path, tuple) and len(frame_id_or_path) == 2:
            parent_hash, offsets = frame_id_or_path
            all_ids = UIManager.GetAllChildFrameIDs(parent_hash, offsets)
            frame_id = all_ids[0] if all_ids else 0
            frame_key = f"{parent_hash}_{'_'.join(map(str, offsets))}"
        else:
            if debug:
                ConsoleLog("check_button_enabled", f"Invalid frame identifier: {frame_id_or_path}", Console.MessageType.Error)
            return False

        if frame_id == 0 or not UIManager.FrameExists(frame_id):
            if debug:
                ConsoleLog("check_button_enabled", f"Frame not found for check: {frame_id_or_path} -> ID {frame_id}", Console.MessageType.Warning)
            _frame_click_retry_tracker[f"click_retry_{frame_key}"] = time.time()
            return False
    except Exception as e:
        if debug:
            ConsoleLog("check_frame_visible", f"Exception checking frame visibility: {e}", Console.MessageType.Error)
        return False

    try:
        frame_obj = PyUIManager.UIFrame(frame_id)
        frame_obj.get_context()
        current_value = getattr(frame_obj, field_name, None)

        if debug:
            status = "ENABLED" if current_value == enabled_field_value else "DISABLED"
            ConsoleLog("check_button_enabled", f"Button {frame_id} is {status} ({field_name}={current_value}).", Console.MessageType.Debug)

        if current_value == enabled_field_value:
            return click_frame_retry(frame_id_or_path, retry_delay=retry_delay, debug=debug)

    except AttributeError:
        if debug:
            ConsoleLog("check_button_enabled", f"Field '{field_name}' not found on frame {frame_id}.", Console.MessageType.Warning)
    except Exception as e:
        ConsoleLog("check_button_enabled", f"Error reading field '{field_name}' for frame {frame_id}: {e}", Console.MessageType.Error)

    now = time.time()
    last_time = _frame_click_retry_tracker.get(f"click_retry_{frame_key}", 0)
    if now - last_time >= retry_delay:
        _frame_click_retry_tracker[f"click_retry_{frame_key}"] = now

    return False

def check_button_field_and_click(frame_id_or_path, field_value=18692, field_name="field91_0x184", debug=False):
    if frame_id_or_path is None:
        if debug:
            ConsoleLog("check_field_click", "Frame path is None.", Console.MessageType.Warning)
        return False
    try:
        if isinstance(frame_id_or_path, int):
            frame_id = UIManager.GetFrameIDByHash(frame_id_or_path)
        elif isinstance(frame_id_or_path, tuple) and len(frame_id_or_path) == 2:
            parent_hash, offsets = frame_id_or_path
            all_ids = UIManager.GetAllChildFrameIDs(parent_hash, offsets)
            frame_id = all_ids[0] if all_ids else 0
        else:
            return False

        if frame_id == 0 or not UIManager.FrameExists(frame_id):
            return False
    except Exception as e:
        return False
    try:
        frame_obj = PyUIManager.UIFrame(frame_id)
        frame_obj.get_context()
        current_value = getattr(frame_obj, field_name, None)

        if current_value == field_value:
            return ActionQueueManager().AddAction("ACTION", UIManager.FrameClick, frame_id)

    except Exception as e:
        ConsoleLog("check_field_click", f"Error reading field '{field_name}' for frame {frame_id}: {e}", Console.MessageType.Error)
    return False

def copy_text_with_imgui(text_to_copy: str):
    PyImGui.set_clipboard_text(text_to_copy)

def _set_flags_for_reroll_jump(target_state_name: str):
    ConsoleLog("Debug Jump", f"Setting flags for jump to: {target_state_name}", Console.MessageType.Debug)

    base_flags = {
        "second_mission_run": True,
        "farmed_the_proof": True,
        "logged_out": False,
        "character_delete_confirmed": False,
        "character_created_successfully": False
    }
    for flag, value in base_flags.items():
        setattr(bot_vars, flag, value)

    if target_state_name == "SYS: Logout for Reroll":
        ConsoleLog("Debug Jump", "  Flags set for Logout state.", Console.MessageType.Debug)

    elif target_state_name == "SYS: Delete Character":
        bot_vars.logged_out = True
        if bot_vars.character_names and 0 <= bot_vars.next_create_index < len(bot_vars.character_names):
            name = bot_vars.character_names[bot_vars.next_create_index]
            bot_vars.character_to_delete_name = name
            ConsoleLog("Debug Jump", f"  Set delete target to '{name}' (simulating post-create).", Console.MessageType.Debug)
        else:
            ConsoleLog("Debug Jump", "  Warning: Cannot set delete target - character names list or index invalid.", Console.MessageType.Warning)
        ConsoleLog("Debug Jump", "  Flags set for Delete state (logged_out=True).", Console.MessageType.Debug)

    elif target_state_name == "SYS: Create New Character":
        bot_vars.logged_out = True
        bot_vars.character_delete_confirmed = True
        ConsoleLog("Debug Jump", "  Flags set for Create state (logged_out=True, delete_confirmed=True).", Console.MessageType.Debug)

    else:
        ConsoleLog("Debug Jump", f"Warning: Unknown reroll target state '{target_state_name}' for flag setting.", Console.MessageType.Warning)

    flags_to_clear = [
        "has_intro_run", "first_time_chahbek_village", "first_mission_run",
        "has_post_mission_run", "first_time_kamadan", "first_time_plains",
        "first_time_ssgh", "second_time_plains", "second_time_kamadan",
        "second_time_chahbek_village"
    ]
    for flag in flags_to_clear:
        if hasattr(bot_vars, flag):
            setattr(bot_vars, flag, False)

def check_morale(target_percent: int) -> bool:
    return Player.GetMorale() == 100 + target_percent

def safe_add_state(fsm, state_tuple):
    name = state_tuple[0]
    execute_fn = state_tuple[1] if len(state_tuple) > 1 else None
    exit_condition = state_tuple[2] if len(state_tuple) > 2 else None
    transition_delay_ms = state_tuple[3] if len(state_tuple) > 3 else 0
    run_once = state_tuple[4] if len(state_tuple) > 4 else True
    on_enter = state_tuple[5] if len(state_tuple) > 5 else None
    on_exit = state_tuple[6] if len(state_tuple) > 6 else None

    fsm.AddState(
        name=name,
        execute_fn=execute_fn or (lambda: None),
        exit_condition=exit_condition or (lambda: True),
        transition_delay_ms=transition_delay_ms,
        run_once=run_once,
        on_enter=on_enter or (lambda: None),
        on_exit=on_exit or (lambda: None)
    )
    
def copy_text_with_ctypes(text: str, debug: bool = False):
    CF_TEXT = 1
    kernel32, user32 = ctypes.windll.kernel32, ctypes.windll.user32
    buffer_ptr = None

    try:
        encoded = text.encode('utf-8') + b'\0'
        mem = ctypes.c_buffer(encoded)
        buffer_ptr = kernel32.GlobalAlloc(0x0002, len(mem))
        if not buffer_ptr:
            return ConsoleLog(module_name, "GlobalAlloc failed.", Console.MessageType.Error)

        lock = kernel32.GlobalLock(buffer_ptr)
        if not lock:
            kernel32.GlobalFree(buffer_ptr)
            return ConsoleLog(module_name, "GlobalLock failed.", Console.MessageType.Error)

        ctypes.memmove(lock, mem, len(mem))
        kernel32.GlobalUnlock(buffer_ptr)

        if not user32.OpenClipboard(0):
            kernel32.GlobalFree(buffer_ptr)
            return ConsoleLog(module_name, f"OpenClipboard failed. Error: {kernel32.GetLastError()}", Console.MessageType.Error)

        user32.EmptyClipboard()
        if user32.SetClipboardData(CF_TEXT, buffer_ptr):
            user32.CloseClipboard()
            if debug:
                ConsoleLog(module_name, f"Copied '{text}' to clipboard.", Console.MessageType.Success)
            return

        user32.CloseClipboard()
        kernel32.GlobalFree(buffer_ptr)
        ConsoleLog(module_name, f"SetClipboardData failed. Error: {kernel32.GetLastError()}", Console.MessageType.Error)

    except Exception as e:
        ConsoleLog(module_name, f"Exception: {e}", Console.MessageType.Error)
        if buffer_ptr:
            try:
                kernel32.GlobalFree(buffer_ptr)
            except Exception as e2:
                if debug:
                    ConsoleLog(module_name, f"Cleanup GlobalFree failed: {e2}", Console.MessageType.Warning)

#endregion (End of functions/variables)

#region FSM for Combat
fsm_vars.global_combat_fsm.SetLogBehavior(False)
fsm_vars.global_combat_fsm.AddState(
    name="Check: In Danger",
    execute_fn=lambda: pause_all(),
    exit_condition=check_combat,
    run_once=False)
fsm_vars.global_combat_fsm.AddSubroutine(
    name="Combat: Execute Global",
    condition_fn=lambda: check_combat(),
    sub_fsm=fsm_vars.global_combat_handler)
fsm_vars.global_combat_fsm.AddState(
    name="Resume: Main FSM",
    execute_fn=lambda: resume_all(),
    exit_condition=lambda: not check_combat(),
    run_once=False)

fsm_vars.global_combat_handler.SetLogBehavior(False)
fsm_vars.global_combat_handler.AddState(
    name="Combat: Start",
    execute_fn=lambda: start_combat(),
    exit_condition=lambda: True)
fsm_vars.global_combat_handler.AddState(
    name="Combat: Wait Safe",
    execute_fn=lambda: None,
    exit_condition=lambda: not check_combat(),
    run_once=False)
fsm_vars.global_combat_handler.AddState(
    name="Combat: Stop",
    execute_fn=lambda: stop_combat(),
    exit_condition=lambda: True)
#endregion

#region FSM Nightfall Fresh Character
fsm_vars.nightfall_intro.SetLogBehavior(False)
fsm_vars.nightfall_intro.AddState(
    name="Target: Kormir",
    execute_fn=lambda: target_and_interact(10331,6387)(),
    exit_condition=lambda: check_dialog_buttons(buttons=2, state_key="kormir1"),
    transition_delay_ms=500,
    run_once=False,
    on_exit=lambda: start_new_run())
fsm_vars.nightfall_intro.AddState(
    name="Click: Skip",
    execute_fn=lambda: click_dialog_button_retry(button=2),
    exit_condition=lambda: check_dialog_buttons(buttons=2, state_key="Kormir2"),
    transition_delay_ms=200,
    run_once=False,
    on_exit=mark_flag("pause_combat_fsm", False))
fsm_vars.nightfall_intro.AddState(
    name="Click: Confident",
    execute_fn=lambda: click_dialog_button_retry(button=1),
    exit_condition=lambda: is_npc_dialog_hidden(),
        #check_active_quest(677)),
    transition_delay_ms=200,
    run_once=False)
fsm_vars.nightfall_intro.AddState(
    name="Equip: Weapon",
    execute_fn=lambda: equip_starter(),
    transition_delay_ms=1000,
    run_once=True)
fsm_vars.nightfall_intro.AddState(
    name="Move: to Enemies",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.nightfall_intro_pathing, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.nightfall_intro_pathing, fsm_vars.movement_handler),
    run_once=False)
fsm_vars.nightfall_intro.AddState(
    name="Move: to Jahdugar",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.nightfall_intro_pathing2, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.nightfall_intro_pathing2, fsm_vars.movement_handler),
    run_once=False,
    on_exit=mark_flag("pause_combat_fsm", True))
fsm_vars.nightfall_intro.AddState(
    name="Target: Jahdugar",
    execute_fn=lambda: target_and_interact(4784,-1881)(),
    exit_condition=lambda: (
        check_dialog_buttons(buttons=1) and
        has_arrived()),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.nightfall_intro.AddState(
    name="Click: Shortcut",
    execute_fn=lambda: click_dialog_button_retry(button=1),
    exit_condition=lambda: (check_dialog_buttons(buttons=1, state_key="click_shortcut")),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.nightfall_intro.AddState(
    name="Click: Let me know",
    execute_fn=lambda: click_dialog_button_retry(button=1),
    exit_condition=lambda: (check_dialog_buttons(buttons=1, state_key="click_me_know")),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.nightfall_intro.AddState(
    name="Click: Ready",
    execute_fn=lambda: click_dialog_button_retry(button=1),
    exit_condition=lambda: (is_npc_dialog_hidden()),
    transition_delay_ms=500,
    run_once=False,
    on_exit=mark_flag("has_intro_run", True))
fsm_vars.nightfall_intro.AddState(
    name="Wait: Village",
    exit_condition=lambda: (Routines.Transition.IsOutpostLoaded(log_actions=False) and Party.IsPartyLoaded() and bot_vars.has_intro_run) or Map.IsMapLoading(),
    transition_delay_ms=2000,
    on_exit=lambda: reset_state_variables())
#endregion

#region FSM Chahbek Pre
fsm_vars.pre_chahbek_village.SetLogBehavior(False)
fsm_vars.pre_chahbek_village.AddState(
    name="Move: To Scout",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.pre_chahbek_village_pathing, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.pre_chahbek_village_pathing, fsm_vars.movement_handler),
    run_once=False)
fsm_vars.pre_chahbek_village.AddState(
    name="Target: Zaishen Scout",
    execute_fn=lambda: target_and_interact(4626, -9617)(),
    exit_condition=lambda: check_dialog_buttons(buttons=2, state_key="check1"),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.pre_chahbek_village.AddState(
    name="Click: Take me to Embark",
    execute_fn=lambda: click_dialog_button_retry(button=1),
    exit_condition=lambda: is_npc_dialog_hidden(),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.pre_chahbek_village.AddState(
    name="Wait: Embark",
    execute_fn=mark_flag("pre_chahbek_village", True),
    exit_condition=lambda: Routines.Transition.IsOutpostLoaded(log_actions=False) and Party.IsPartyLoaded() and bot_vars.pre_chahbek_village,
    transition_delay_ms=2000,
    on_exit=lambda: reset_state_variables())
#endregion

#region FSM Embark 1
fsm_vars.first_embark_beach.SetLogBehavior(False)

fsm_vars.first_embark_beach.AddState(
    name="Wait: check spawn Embark",
    execute_fn=lambda: locate_embark_spawm(),
    exit_condition=lambda: Routines.Transition.IsOutpostLoaded(log_actions=False) and Party.IsPartyLoaded(),
    transition_delay_ms=2000)

fsm_vars.first_embark_beach.AddState(
    name="Move: NE area",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.eb_path, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.eb_path, fsm_vars.movement_handler),
    run_once=False)
fsm_vars.first_embark_beach.AddState(
    name="Target: Zaishen Mission Flag",
    execute_fn=lambda: target_and_interact(2700, 3278)(),
    exit_condition=lambda: check_dialog_buttons(buttons=2, state_key="check1"),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.first_embark_beach.AddState(
    name="Click: I can",
    execute_fn=lambda: click_dialog_button_retry(button=1),
    exit_condition=lambda: is_npc_dialog_hidden(),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.first_embark_beach.AddState(
    name="Move: Exit Guy",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.first_eb_exit_pathing, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.first_eb_exit_pathing, fsm_vars.movement_handler),
    run_once=False)
fsm_vars.first_embark_beach.AddState(
    name="Target: Zinshao",
    execute_fn=lambda: target_and_interact(2197, 4223)(),
    exit_condition=lambda: check_dialog_buttons(buttons=5, state_key="check2"),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.first_embark_beach.AddState(
    name="Click: Istan",
    execute_fn=lambda: click_dialog_button_retry(button=1),
    exit_condition=lambda: check_dialog_buttons(buttons=4, state_key="check3"),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.first_embark_beach.AddState(
    name="Click: Chahbek",
    execute_fn=lambda: click_dialog_button_retry(button=1),
    exit_condition=lambda: is_npc_dialog_hidden(),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.first_embark_beach.AddState(
    name="Wait: Chahbek Village",
    execute_fn=mark_flag("first_embark", True),
    exit_condition=lambda: Routines.Transition.IsOutpostLoaded(log_actions=False) and Party.IsPartyLoaded() and bot_vars.first_embark,
    transition_delay_ms=2000,
    on_exit=lambda: reset_state_variables())
#endregion

#region FSM First Chahbek Village
def setup_first_chahbek_village(fsm, random_insert_chance=0.5):
    fsm.SetLogBehavior(False)

    early_steps = [
        ("Target: Jahdugar #1", lambda: target_and_interact(3482, -5167)(), lambda: check_dialog_buttons(buttons=1) or check_dialog_buttons(buttons=2), 500, False, None, None),
        ("Click: Accept #1", lambda: click_dialog_button_retry(button=1), lambda: check_dialog_buttons(buttons=2, state_key="accept"), 500, False, None, None),
        ("Click: count on me.", lambda: click_dialog_button_retry(button=1), lambda: is_npc_dialog_hidden() and check_active_quest(709), 500, False, None, lambda: Keystroke.PressAndRelease(Key.Escape.value)),
    ]

    recruit_steps = [
        ("Type: /bonus", lambda: ActionQueueManager().AddAction("ACTION", Player.SendChatCommand, "bonus"), None, 500, True, None, None),
        ("Type: delete bow", lambda: ActionQueueManager().AddAction("ACTION", Inventory.DestroyItem, Item.GetItemIdFromModelID(5831)), None, 100, True, None, None),
        ("Type: delete roar", lambda: ActionQueueManager().AddAction("ACTION", Inventory.DestroyItem, Item.GetItemIdFromModelID(6036)), None, 100, True, None, None),
        ("Type: delete favor", lambda: ActionQueueManager().AddAction("ACTION", Inventory.DestroyItem, Item.GetItemIdFromModelID(6058)), None, 100, True, None, None),
        ("Equip Sundering Charge", lambda: ActionQueueManager().AddAction("ACTION", equip_weapon), None, 100, True, None, None),
        ("Type: delete shriek", lambda: ActionQueueManager().AddAction("ACTION", Inventory.DestroyItem, Item.GetItemIdFromModelID(6515)), None, 100, True, None, None),

    ]

    party_steps = [
        ("Party: Koss.", lambda: Party.Heroes.AddHero(6), None, 500, True, None, None),
        ("Party: Sogolon.", lambda: Party.Henchmen.AddHenchman(1), None, 500, True, None, None),
        ("Party: Kihm.", lambda: Party.Henchmen.AddHenchman(2), None, 500, True, None, None),
    ]

    post_recruit_steps = [
        ("Load: skill bar", lambda: load_skill_bar(), None, 1000, True, None, None),
        ("Target: Jahdugar #3", lambda: target_and_interact(3482, -5167)(), lambda: check_dialog_buttons(buttons=2, state_key="#3"), 500, False, None, None),
        ("Click: We must hurry", lambda: click_dialog_button_retry(button=2), lambda: check_dialog_buttons(buttons=2, state_key="hurry"), 500, False, None, None),
        ("Click: Ready.", lambda: click_dialog_button_retry(button=1), lambda: is_npc_dialog_hidden(), 500, False, None, lambda: mark_flag("first_time_chahbek_village", True)()),
        ("Wait: Mission", mark_flag("pause_combat_fsm", False), lambda: (Routines.Transition.IsExplorableLoaded(log_actions=True) and Party.IsPartyLoaded() and bot_vars.first_time_chahbek_village) or Map.IsMapLoading(), 2000, True, None, lambda: reset_state_variables())
    ]

    for step in early_steps:
        safe_add_state(fsm, step)

    pending_party_steps = party_steps.copy()
    random.shuffle(pending_party_steps)

    for step in recruit_steps:
        safe_add_state(fsm, step)
        if pending_party_steps and random.random() < random_insert_chance:
            party_step = pending_party_steps.pop()
            safe_add_state(fsm, party_step)

    for party_step in pending_party_steps:
        safe_add_state(fsm, party_step)

    for step in post_recruit_steps:
        safe_add_state(fsm, step)

setup_first_chahbek_village(fsm_vars.first_chahbek_village)
#endregion

#region FSM Chahbek Village Mission
fsm_vars.chahbek_mission.SetLogBehavior(False)
fsm_vars.chahbek_mission.AddState(
    name="Item: summon Imp", 
    execute_fn=lambda: summon_imp_if_needed(),
    on_enter=mark_flag("pause_combat_fsm", False), 
    run_once=True)
fsm_vars.chahbek_mission.AddState(
    name="Move: Clear map",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.chahbek_mission_pathing, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.chahbek_mission_pathing, fsm_vars.movement_handler),
    run_once=False)

fsm_vars.chahbek_mission.AddState(
    name="Target: Grab Oil #1",
    execute_fn=lambda: target_and_interact(-4781,-1776, target_type="gadget")(),
    exit_condition=lambda: check_frame_visible(bot_vars.frame_paths["drop_bundle_button"]),
    transition_delay_ms=500,
    run_once=False)

fsm_vars.chahbek_mission.AddState(
    name="Move: Catapult #1",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.chahbek_mission_cata_one, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.chahbek_mission_cata_one, fsm_vars.movement_handler),
    run_once=False)

fsm_vars.chahbek_mission.AddState(
    name="Target: Catapult",
    execute_fn=lambda: target_and_interact(-1691,-2515, target_type="gadget")(),
    exit_condition=lambda:  has_arrived() and not check_frame_visible(bot_vars.frame_paths["drop_bundle_button"]),
    transition_delay_ms=2500,
    run_once=False)
fsm_vars.chahbek_mission.AddState(
    name="Target: Fire Catapult",
    execute_fn=lambda: target_and_interact(-1691,-2515, target_type="gadget")(),
    exit_condition=lambda: check_morale(4),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.chahbek_mission.AddState(
    name="Move: Oil #2",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.chahbek_mission_oil, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.chahbek_mission_oil, fsm_vars.movement_handler),
    run_once=False)
fsm_vars.chahbek_mission.AddState(
    name="Target: Grab Oil #2",
    execute_fn=lambda: target_and_interact(-4781,-1776, target_type="gadget")(),
    exit_condition=lambda: has_arrived() and check_frame_visible(bot_vars.frame_paths["drop_bundle_button"]),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.chahbek_mission.AddState(
    name="Move: Cata #2",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.chahbek_mission_cata_two, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.chahbek_mission_cata_two, fsm_vars.movement_handler),
    run_once=False)
fsm_vars.chahbek_mission.AddState(
    name="Target: Catapult #2",
    execute_fn=lambda: target_and_interact(-1733,-4172, target_type="gadget")(),
    exit_condition=lambda: has_arrived() and not check_frame_visible(bot_vars.frame_paths["drop_bundle_button"]),
    transition_delay_ms=2500,
    run_once=False)
fsm_vars.chahbek_mission.AddState(
    name="Target: Fire Catapult #2",
    execute_fn=lambda: target_and_interact(-1733,-4172, target_type="gadget")(),
    exit_condition=lambda: check_morale(6),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.chahbek_mission.AddState(
    name="Wait: Map",
    execute_fn=mark_flag("second_mission_run", True),
    exit_condition=lambda: Routines.Transition.IsExplorableLoaded(log_actions=False) and Party.IsPartyLoaded() and bot_vars.second_mission_run and Map.GetMapID() == bot_vars.churrhir_fields,
    transition_delay_ms=2000,
    on_exit=lambda: [
        reset_state_variables(),
        mark_flag("summoned_imp", False)(),
        mark_flag("pause_combat_fsm", True)(),
        mark_flag("first_mission_run", True)(),
        reset_paths_and_handler()
    ])
#endregion

#region FSM port to embark
fsm_vars.port_to_embark.SetLogBehavior(False)
fsm_vars.port_to_embark.AddState(
    name="Wait: For Map",
    exit_condition=lambda: Routines.Transition.IsExplorableLoaded(log_actions=False) and Party.IsPartyLoaded(),
    transition_delay_ms=500)
fsm_vars.port_to_embark.AddState(
    name="Move: EB",
    execute_fn=lambda: Routines.Transition.TravelToOutpost(outpost_id=bot_vars.embark_beach, log_actions=False),
    exit_condition=lambda: Routines.Transition.HasArrivedToOutpost(outpost_id=bot_vars.embark_beach, log_actions=False),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.port_to_embark.AddState(
    name="Wait: Embark Beach",
    exit_condition=lambda: Routines.Transition.IsOutpostLoaded(log_actions=False) and Party.IsPartyLoaded(),
    transition_delay_ms=500,
    on_exit=lambda: reset_state_variables())
#endregion

#region FSM Second Embark
fsm_vars.second_embark.SetLogBehavior(False)
fsm_vars.second_embark.AddState(
    name="Move: Storage",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.embark_beach_str, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.embark_beach_str, fsm_vars.movement_handler),
    run_once=False)
fsm_vars.second_embark.AddState(
    name="Target: Storage person",
    execute_fn=lambda: target_and_interact(2060, -2205)(),
    exit_condition=lambda: check_dialog_buttons(buttons=2, state_key="check1"),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.second_embark.AddState(
    name="Click: Buy Storage",
    execute_fn=lambda: click_dialog_button_retry(button=1),
    exit_condition=lambda: check_dialog_buttons(buttons=3, state_key="check2"),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.second_embark.AddState(
    name="Move: ZM handin",
    execute_fn=lambda: Routines.Movement.FollowPath(fsm_vars.embark_beach_hand, fsm_vars.movement_handler),
    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(fsm_vars.embark_beach_hand, fsm_vars.movement_handler),
    run_once=False)
fsm_vars.second_embark.AddState(
    name="Target: Zehnchu",
    execute_fn=lambda: target_and_interact(-749, -3262)(),
    exit_condition=lambda: check_dialog_buttons(buttons=1, state_key="check3"),
    transition_delay_ms=500,
    run_once=False)
fsm_vars.second_embark.AddState(
    name="Click: Accept",
    execute_fn=lambda: click_dialog_button_retry(button=1),
    exit_condition=lambda: is_npc_dialog_hidden(),
    # exit_condition=lambda: check_dialog_buttons(buttons=4, state_key="check3"),
    transition_delay_ms=500,
    run_once=False)
# fsm_vars.second_embark.AddState(
#     name="Click: Chahbek",
#     execute_fn=lambda: click_dialog_button_retry(button=1),
#     exit_condition=lambda: is_npc_dialog_hidden(),
#     transition_delay_ms=500,
#     run_once=False)
fsm_vars.second_embark.AddState(
    name="Wait: Set Flag",
    execute_fn=mark_flag("second_embark", True),
    exit_condition=lambda: True,
    transition_delay_ms=2000,
    on_exit=lambda: reset_state_variables())
#endregion

#region FSM deposit copper
fsm_vars.finish_up_deposit.AddState(
    name="Item: Deposit COIN",
    # execute_fn=lambda: print("ITS WORKING, WE DEPOSITING"),
    execute_fn=lambda: deposit_coin(),
    exit_condition=lambda: Item.GetItemIdFromModelID(bot_vars.copper_coin) == 0 and ActionQueueManager().IsEmpty("ACTION"),
    transition_delay_ms=2000,
    on_exit=lambda: complete_run(True))
#endregion

#region --- FSM Character Logout ---
fsm_vars.logout_character.SetLogBehavior(False)
fsm_vars.logout_character.AddState(
    name="Action: Initiate Logout",
    execute_fn=initiate_logout,
    exit_condition=is_char_select_ready,
    transition_delay_ms=2000,
    run_once=True)
fsm_vars.logout_character.AddState(
    name="Action: Find Target Character",
    execute_fn=find_target_character,
    exit_condition=lambda: bot_vars.character_index != -99,
    run_once=False)
fsm_vars.logout_character.AddState(
    name="Action: Navigate Character Select",
    execute_fn=navigate_char_select,
    exit_condition=is_target_selected,
    run_once=False,
    on_exit=lambda: clear_frame_click_retry_cache(True))
fsm_vars.logout_character.AddWaitState(
    name="Wait: Target Character Selected",
    condition_fn=is_target_selected,
    timeout_ms=15000,
    on_timeout=lambda:  _stop_fsm_on_timeout("logout_character", "Wait: Target Character Selected"),
    on_exit=lambda: [
        mark_flag("logged_out", True)(),
        ConsoleLog("logout_character", "Logout and character selection complete.", Console.MessageType.Success)
    ])
#endregion

#region --- FSM Delete Character ---
fsm_vars.delete_character.SetLogBehavior(False)
fsm_vars.delete_character.AddState(
    name="Check: In Char Select",
    execute_fn=lambda: None,
    exit_condition=lambda: is_in_character_select(),
    run_once=True,
    transition_delay_ms=1000)
fsm_vars.delete_character.AddState(
    name="Check: Target Name Set",
    execute_fn=lambda: None,
    exit_condition=lambda: bot_vars.character_to_delete_name != "" and check_frame_visible(bot_vars.frame_paths["char_select_delete_button"]),
    run_once=True,
    transition_delay_ms=1500)
fsm_vars.delete_character.AddState(
    name="Wait: Delete Button Loaded",
    exit_condition=lambda: check_frame_visible(bot_vars.frame_paths["char_select_delete_button"]),
    transition_delay_ms=1000)
fsm_vars.delete_character.AddState(
    name="Click: Delete Button",
    execute_fn=lambda: bot_vars.press_key_aq.add_action(Keystroke.PressAndRelease, Key.D.value),
    exit_condition=lambda: check_frame_visible(bot_vars.frame_paths["char_select_delete_confirm_text"]),
    run_once=True,
    transition_delay_ms=1500)
fsm_vars.delete_character.AddState(
    name="Copy Name to Clipboard",
    execute_fn=lambda: copy_text_with_ctypes(bot_vars.character_to_delete_name),
    exit_condition=lambda: True,
    run_once=True,
    transition_delay_ms=200)
fsm_vars.delete_character.AddState(
    name="Paste Name (Ctrl+V)",
    execute_fn=lambda: bot_vars.press_key_aq.add_action(Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.V.value]),
    exit_condition=lambda: bot_vars.press_key_aq.is_empty(),
    run_once=True,
    transition_delay_ms=200)
fsm_vars.delete_character.AddState(
    name="Click: Final Delete Button",
    execute_fn=lambda:  bot_vars.press_key_aq.add_action(Keystroke.PressAndRelease, Key.Enter.value),
    exit_condition=lambda: (
        not check_frame_visible(bot_vars.frame_paths["char_select_delete_confirm_text"]) or
        is_char_name_gone(bot_vars.character_to_delete_name)),
    run_once=True,
    transition_delay_ms=1000,
    on_exit=lambda: [
        ConsoleLog("delete_character", f"Character '{bot_vars.character_to_delete_name}' deleted successfully.", Console.MessageType.Success),
        mark_flag("character_delete_confirmed", True)()
    ])
#endregion --- FSM Delete Character ---

#region --- FSM Create Character ---
fsm_vars.create_character.SetLogBehavior(False)
fsm_vars.create_character.AddState(
    name="Check: In Char Select",
    execute_fn=lambda: None,
    exit_condition=lambda: is_in_character_select(),
    transition_delay_ms=1000,
    run_once=False)
fsm_vars.create_character.AddState(
    name="Click: Create Button",
    execute_fn=lambda: (
        click_frame_once(bot_vars.frame_paths["char_select_create_button2"]) 
        or click_frame_once(bot_vars.frame_paths["char_select_create_button"])
    ),
    exit_condition=lambda: (
        check_frame_visible(bot_vars.frame_paths["char_create_type_next_button"]) or 
        not check_frame_visible(bot_vars.frame_paths["char_select_sort_dropdown"])),
    run_once=True,
    transition_delay_ms=1000)
fsm_vars.create_character.AddState(
    name="Click: Next (Type)",
    execute_fn=lambda: click_frame_once(bot_vars.frame_paths["char_create_type_next_button"]),
    exit_condition=lambda: check_frame_visible(bot_vars.frame_paths["char_create_bottom_frame"]),
    run_once=True,
    transition_delay_ms=1500)
fsm_vars.create_character.AddState(
    name="Select: Campaign (Nightfall)",
    execute_fn=lambda: press_key_repeat(Key.RightArrow.value, 3),
    exit_condition=lambda: bot_vars.press_key_aq.is_empty(),
    run_once=True,
    transition_delay_ms=1500)
fsm_vars.create_character.AddState(
    name="Click: Next (Campaign)",
    execute_fn=lambda: click_frame_once(bot_vars.frame_paths["char_create_generic_next_button"]),
    exit_condition=lambda: check_frame_visible(bot_vars.frame_paths["char_create_profession_tab_text"]),
    run_once=True,
    transition_delay_ms=1500)
# fsm_vars.create_character.AddState(
#     name="Select: Profession (Dervish)",
#     execute_fn=lambda: press_key_repeat(Key.RightArrow.value, 7),
#     exit_condition=lambda: bot_vars.press_key_aq.is_empty(),
#     run_once=True,
#     transition_delay_ms=2000)
fsm_vars.create_character.AddState(
    name="Click: Next (Profession)",
    execute_fn=lambda: click_frame_once(bot_vars.frame_paths["char_create_generic_next_button"]),
    exit_condition=lambda: check_frame_visible(bot_vars.frame_paths["char_create_sex_tab_text"]),
    run_once=True,
    transition_delay_ms=1500,
    on_exit=clear_frame_click_retry_cache(True))
fsm_vars.create_character.AddState(
    name="Click: Next (Sex)",
    execute_fn=lambda: click_frame_once(bot_vars.frame_paths["char_create_generic_next_button"]),
    exit_condition=lambda: check_frame_visible(bot_vars.frame_paths["char_create_appearance_tab_text"]),
    run_once=True,
    transition_delay_ms=1500,
    on_exit=clear_frame_click_retry_cache(True))
fsm_vars.create_character.AddState(
    name="Click: Next (Appearance)",
    execute_fn=lambda: click_frame_once(bot_vars.frame_paths["char_create_generic_next_button"]),
    exit_condition=lambda: check_frame_visible(bot_vars.frame_paths["char_create_body_tab_text"]),
    run_once=True,
    transition_delay_ms=1500,
    on_exit=clear_frame_click_retry_cache(True))
fsm_vars.create_character.AddState(
    name="Click: Next (Body)",
    execute_fn=lambda: click_frame_once(bot_vars.frame_paths["char_create_generic_next_button"]),
    exit_condition=lambda: (check_frame_visible(bot_vars.frame_paths["char_create_name_tab_text"])),
    run_once=True,
    transition_delay_ms=1500,
    on_exit=clear_frame_click_retry_cache(True))
fsm_vars.create_character.AddState(
    name="Copy Name to Clipboard",
    execute_fn=lambda: copy_text_with_ctypes(bot_vars.character_names[bot_vars.next_create_index]),
    exit_condition=lambda: True,
    run_once=True,
    transition_delay_ms=800)
fsm_vars.create_character.AddState(
    name="Paste Name (Ctrl+V)",
    execute_fn=lambda: bot_vars.press_key_aq.add_action(Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.V.value]),
    exit_condition=lambda: bot_vars.press_key_aq.is_empty(),
    run_once=True,
    transition_delay_ms=500)
fsm_vars.create_character.AddState(
    name="Click: Final Create Button",
    execute_fn=lambda: bot_vars.press_key_aq.add_action(Keystroke.PressAndRelease, Key.Enter.value),
    exit_condition=lambda: is_in_load_screen(),
    run_once=True,
    transition_delay_ms=2000)

fsm_vars.create_character.AddState(
    name="Wait: Loading",
    exit_condition=lambda: Map.IsInCinematic() or is_in_load_screen() or (not is_in_load_screen() and Party.IsPartyLoaded()), #Map.IsInCinematic() or Map.IsMapLoading() or
    run_once=True,
    transition_delay_ms=1000)

fsm_vars.create_character.AddState(
    name="dumb wait?",
    exit_condition=lambda: (not is_in_load_screen() and Party.IsPartyLoaded()),
    run_once=True,
    transition_delay_ms=1000)

fsm_vars.create_character.AddState(
    name="Final wait",
    exit_condition=lambda: (not is_in_load_screen() and Map.GetMapID() == bot_vars.island_of_shehkah and Party.IsPartyLoaded() and Map.IsMapReady()), #Map.IsInCinematic() or Map.IsMapLoading() or
    run_once=True,
    transition_delay_ms=4000,
    on_exit=lambda: [
        (name_created := bot_vars.character_names[bot_vars.next_create_index]),
        ConsoleLog("create_character", f"Character '{name_created}' created successfully.", Console.MessageType.Success),
        mark_flag("character_created_successfully", True)(),
        mark_flag("character_to_delete_name", name_created)(),
        mark_flag("next_create_index", (bot_vars.next_create_index + 1) % len(bot_vars.character_names))(),
        ConsoleLog("create_character", f"Next character to create: {bot_vars.character_names[bot_vars.next_create_index]} (Index: {bot_vars.next_create_index})", Console.MessageType.Info),
        ConsoleLog("create_character", f"Next character to delete: {bot_vars.character_to_delete_name}", Console.MessageType.Info),
        clear_frame_click_retry_cache(True)
    ])
#endregion --- FSM Create Character ---

#region --- Main FSM Orchestration ---
fsm_vars.state_machine.AddSubroutine(
    name="EX: Nightfall Introduction",
    sub_fsm=fsm_vars.nightfall_intro,
    condition_fn=lambda: 
        (Map.GetMapID() == bot_vars.island_of_shehkah and 
         Map.IsExplorable() and 
         not bot_vars.has_intro_run))

fsm_vars.state_machine.AddSubroutine(
    name="OP: Village Part 1",
    sub_fsm=fsm_vars.pre_chahbek_village,
    condition_fn=lambda: 
        (Map.GetMapID() == bot_vars.chahbek_village and 
         Map.IsOutpost() and 
         not bot_vars.pre_chahbek_village))

fsm_vars.state_machine.AddSubroutine(
    name="OP: Emabrk Part 1",
    sub_fsm=fsm_vars.first_embark_beach,
    condition_fn=lambda: 
        (Map.GetMapID() == bot_vars.embark_beach and 
         Map.IsOutpost() and 
         bot_vars.pre_chahbek_village and
         not bot_vars.first_embark))

fsm_vars.state_machine.AddSubroutine(
    name="OP: Village Part 2",
    sub_fsm=fsm_vars.first_chahbek_village,
    condition_fn=lambda: 
        (Map.GetMapID() == bot_vars.chahbek_village and 
         Map.IsOutpost() and 
         bot_vars.pre_chahbek_village and
         bot_vars.first_embark and
         not bot_vars.first_time_chahbek_village))

fsm_vars.state_machine.AddSubroutine(
    name="MS: Mission Run 1",
    sub_fsm=fsm_vars.chahbek_mission,
    condition_fn=lambda: 
        (Map.GetMapID() == bot_vars.chahbek_mission and 
         Map.IsExplorable() and 
         not bot_vars.first_mission_run))

fsm_vars.state_machine.AddSubroutine(
    name="EX: To EB",
    sub_fsm=fsm_vars.port_to_embark,
    condition_fn=lambda: 
        (Map.GetMapID() == bot_vars.churrhir_fields and 
         Map.IsExplorable() and 
         bot_vars.second_mission_run and 
         not bot_vars.farmed_the_proof))

fsm_vars.state_machine.AddSubroutine(
    name="OP: Emabrk Part 2",
    sub_fsm=fsm_vars.second_embark,
    condition_fn=lambda: 
        (Map.GetMapID() == bot_vars.embark_beach and 
         Map.IsOutpost() and 
         bot_vars.second_mission_run and
         not bot_vars.second_embark))

fsm_vars.state_machine.AddSubroutine(
    name="OP: Depositing Proof of Triumph",
    sub_fsm=fsm_vars.finish_up_deposit,
    condition_fn=lambda:
        (Map.GetMapID() == bot_vars.embark_beach and
         Map.IsOutpost() and
         bot_vars.second_embark and
         not bot_vars.farmed_the_proof))

fsm_vars.state_machine.AddSubroutine(
    name="SYS: Logout for Reroll",
    sub_fsm=fsm_vars.logout_character,
    condition_fn=lambda: [
        bot_vars.second_mission_run and
        bot_vars.farmed_the_proof and
        not bot_vars.logged_out and
        bot_vars.character_to_delete_name != ""
    ],
    on_exit=lambda: [
        clear_frame_click_retry_cache()
    ])
fsm_vars.state_machine.AddSubroutine(
    name="SYS: Delete Character",
    sub_fsm=fsm_vars.delete_character,
    condition_fn=lambda: [
        bot_vars.second_mission_run and
        bot_vars.logged_out and
        bot_vars.farmed_the_proof and
        not bot_vars.character_delete_confirmed
    ],
     on_exit=lambda: [
        clear_frame_click_retry_cache()
     ])
fsm_vars.state_machine.AddSubroutine(
    name="SYS: Create New Character",
    sub_fsm=fsm_vars.create_character,
    condition_fn=lambda: [
        bot_vars.character_delete_confirmed and
        not bot_vars.character_created_successfully
    ],
    on_exit=lambda: [
        ConsoleLog("Main FSM", "Character creation subroutine finished. Resetting environment.", Console.MessageType.Info),
        reset_variables(),
        ConsoleLog("Stats", "Starting new run timer.", Console.MessageType.Notice),
        bot_vars.lap_timer.Reset()
    ])
#endregion

#region Draw Window
def draw_window():

    if bot_vars.window_module.first_run:
        PyImGui.set_next_window_size(*bot_vars.window_module.window_size)
        PyImGui.set_next_window_pos(*bot_vars.window_module.window_pos)
        bot_vars.window_module.first_run = False

    if not PyImGui.begin(bot_vars.window_module.window_name, bot_vars.window_module.window_flags):
        return
    
    PyImGui.begin_group()
    PyImGui.dummy(0, 0)
    PyImGui.text("Start/Stop")
    PyImGui.end_group()
    PyImGui.same_line(0,-1)
    if PyImGui.button("Stop FSM") if is_bot_started() else PyImGui.button("Start FSM"):
        stop_bot() if is_bot_started() else start_bot()
    PyImGui.separator()
    def draw_fsm_info(label, fsm, use_collapsing_header=True):
        if use_collapsing_header:
            if not PyImGui.collapsing_header(label):
                return
        else:
            PyImGui.text(label)

        ImGui.table(label, ["Value", "Data"], [
            ("Previous Step:", fsm.get_previous_step_name()),
            ("Current Step:", fsm.get_current_step_name()),
            ("Next Step:", fsm.get_next_step_name()),
            ("Is Started:", fsm.is_started()),
            ("Is Finished:", fsm.is_finished()),
        ])
        PyImGui.separator()
    def get_current_sub_fsm(fsm):
        state = fsm.current_state
        if isinstance(state, FSM.ConditionState) and state.sub_fsm and not state.sub_fsm.is_finished():
            return state.sub_fsm
        return None
    sub_fsm = get_current_sub_fsm(fsm_vars.state_machine)
    if PyImGui.begin_tab_bar("TopTabBar"):
        if PyImGui.begin_tab_item("Statistics"):
            headers = ["Statistic", "Value"]
            data = [
                ("Current Main Step", fsm_vars.state_machine.get_current_step_name()),
                ("Current Sub Step", sub_fsm.get_current_step_name() if sub_fsm else "-"),
                ("Total Bot Runtime", bot_vars.global_timer.FormatElapsedTime("hh:mm:ss")),
                ("Current Run Time", bot_vars.lap_timer.FormatElapsedTime("mm:ss")),
                ("Minimum Run Time", FormatTime(bot_vars.min_time, "mm:ss") if bot_vars.min_time > 0 else "N/A"),
                ("Maximum Run Time", FormatTime(bot_vars.max_time, "mm:ss") if bot_vars.max_time > 0 else "N/A"),
                ("Average Run Time", FormatTime(bot_vars.avg_time, "mm:ss") if bot_vars.avg_time > 0 else "N/A"),
                ("Current Run", bot_vars.runs_attempted),
                ("37 Copper Deposited x", bot_vars.proofs_deposited),
                ("Success Rate", f"{bot_vars.success_rate * 100:.1f}%" if bot_vars.runs_attempted > 0 else "N/A"),
            ]
            ImGui.table("Run Statistics", headers, data)
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Character List"):
            PyImGui.text("Manage Character Rotation List:")
            PyImGui.separator()
            PyImGui.text("Add New Name:")
            avail_width = int(PyImGui.get_content_region_avail()[0])
            PyImGui.push_item_width(avail_width * 0.7) # Adjust width as needed
            bot_vars.new_char_name_input = PyImGui.input_text("##add_char_name", bot_vars.new_char_name_input)
            PyImGui.pop_item_width()
            PyImGui.same_line(0,1)
            if PyImGui.button("Add"):
                name_to_add = bot_vars.new_char_name_input.strip()
                if name_to_add:
                    if name_to_add not in bot_vars.character_names:
                        bot_vars.character_names.append(name_to_add)
                        bot_vars.new_char_name_input = ""
                        ConsoleLog("CharacterList", f"Added '{name_to_add}' to rotation.", Console.MessageType.Info)
                        if len(bot_vars.character_names) == 1:
                             bot_vars.character_to_delete_name = name_to_add
                             bot_vars.next_create_index = 0
                    else:
                        ConsoleLog("CharacterList", f"Name '{name_to_add}' already exists in the list.", Console.MessageType.Warning)
                else:
                    ConsoleLog("CharacterList", "Cannot add an empty name.", Console.MessageType.Warning)

            PyImGui.separator()
            PyImGui.text("Current Names:")
            name_to_remove_index = -1
            if not bot_vars.character_names:
                PyImGui.text_colored("List is empty!", Utils.RGBToNormal(255, 100, 100, 255))
            else:
                PyImGui.dummy(0,0)
                for i, name in enumerate(bot_vars.character_names):
                    PyImGui.text(f"{i+1}. {name}")
                    PyImGui.same_line(0,-1)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Utils.RGBToNormal(200, 50, 50, 255)) # Red button
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Utils.RGBToNormal(230, 70, 70, 255))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, Utils.RGBToNormal(255, 90, 90, 255))
                    if PyImGui.button(f"@##remove_{i}", width=10, height=10):
                        if len(bot_vars.character_names) > 1:
                            name_to_remove_index = i
                        else:
                            ConsoleLog("CharacterList", "Cannot remove the last character name.", Console.MessageType.Warning)

                    PyImGui.pop_style_color(3)
                    ImGui.show_tooltip(f"Remove '{name}'")
            if name_to_remove_index != -1:
                removed_name = bot_vars.character_names.pop(name_to_remove_index)
                ConsoleLog("CharacterList", f"Removed '{removed_name}' from rotation.", Console.MessageType.Info)
                list_len = len(bot_vars.character_names)
                if list_len > 0:
                    if bot_vars.next_create_index >= list_len:
                        bot_vars.next_create_index = 0
                    delete_index = (bot_vars.next_create_index - 1 + list_len) % list_len
                    bot_vars.character_to_delete_name = bot_vars.character_names[delete_index]
                    ConsoleLog("CharacterList", f"Adjusted delete target to: {bot_vars.character_to_delete_name}", Console.MessageType.Info)
                else:
                    bot_vars.next_create_index = 0
                    bot_vars.character_to_delete_name = ""
                    ConsoleLog("CharacterList", "Character list is now empty.", Console.MessageType.Warning)
            PyImGui.separator()
            PyImGui.text_disabled("Current Rotation State:")
            PyImGui.text(f"  Next Create Index: {bot_vars.next_create_index}")
            if bot_vars.character_names:
                 PyImGui.text(f"  Next Create Name: '{bot_vars.character_names[bot_vars.next_create_index]}'")
            PyImGui.text(f"  Target Delete Name: {bot_vars.character_to_delete_name}")
            PyImGui.end_tab_item()
        PyImGui.end_tab_bar()
    PyImGui.separator()   
       
    if PyImGui.collapsing_header("FSM Info"):
        draw_fsm_info("Main FSM", fsm_vars.state_machine)
        
        if sub_fsm:
            draw_fsm_info("Sub FSM", sub_fsm)
            
    if PyImGui.collapsing_header("Debug Items"):
        if bot_vars.test:
            if PyImGui.collapsing_header("Manual FSM Jumps"):
                if len(bot_vars.character_names) > 0:
                    PyImGui.text("Character Name Rotation:")
                    PyImGui.text(f"  List: {', '.join(bot_vars.character_names)}")
                    PyImGui.text(f"  Next Create Index: {bot_vars.next_create_index} -> '{bot_vars.character_names[bot_vars.next_create_index]}'")
                    PyImGui.text_colored(f"  Target Delete Name: {bot_vars.character_to_delete_name}",
                                        Utils.TrueFalseColor(bot_vars.character_to_delete_name != ""))
                    PyImGui.separator()
                    
                    if PyImGui.button(f"Pause Combat:{bot_vars.pause_combat_fsm}"):
                        bot_vars.pause_combat_fsm = not bot_vars.pause_combat_fsm
                    PyImGui.separator()
                    PyImGui.text("Reroll Testing Jumps:")

                    # Check if delete name is set - crucial for reroll testing
                    delete_name_set = bot_vars.character_to_delete_name != ""
                    if not delete_name_set:
                        PyImGui.text_wrapped("Set 'Target Delete Name' via normal run or start_bot() before using reroll jumps.")

                    # Define the reroll jump targets
                    reroll_jumps = {
                        "Jump to Logout": "SYS: Logout for Reroll",
                        "Jump to Delete": "SYS: Delete Character",
                        "Jump to Create": "SYS: Create New Character",
                    }

                    # Create buttons for each reroll jump
                    for label, target_state_name in reroll_jumps.items():
                        if PyImGui.button(label):
                            try:
                                if not fsm_vars.state_machine.is_started():
                                    ConsoleLog("Debug Jump", "Main FSM not started, starting it first.", Console.MessageType.Warning)
                                    start_bot() # Ensure FSM is running

                                if fsm_vars.state_machine.has_state(target_state_name):
                                    ConsoleLog("Debug Jump", f"Attempting jump to: {target_state_name}", Console.MessageType.Notice)
                                    # Set prerequisite flags using the helper function
                                    _set_flags_for_reroll_jump(target_state_name)
                                    # Perform the jump
                                    fsm_vars.state_machine.jump_to_state_by_name(target_state_name)
                                    if not bot_vars.bot_started: bot_vars.bot_started = True # Ensure bot is marked as started
                                    ConsoleLog("Debug Jump", f"Jump successful. Current state: {fsm_vars.state_machine.get_current_step_name()}", Console.MessageType.Success)
                                else:
                                    ConsoleLog("Debug Jump", f"Error: State '{target_state_name}' not found!", Console.MessageType.Error)
                            except Exception as e:
                                ConsoleLog("Debug Jump", f"Error during jump to {target_state_name}: {e}\n{traceback.format_exc()}", Console.MessageType.Error)

                    PyImGui.separator()
                    
                    PyImGui.text("General Progression Jumps:")
                    all_state_names = fsm_vars.state_machine.get_state_names()
                    for state_name in all_state_names:
                        if state_name in PREGAME_FSM_STATES: # Skip reroll states here
                            continue

                        if PyImGui.button(f"Jump to: {state_name}##jump_{state_name}"):
                            target_state_name = state_name
                            try:
                                if not fsm_vars.state_machine.is_started():
                                    ConsoleLog("Debug Jump", "Main FSM not started, starting it first.", Console.MessageType.Warning)
                                    start_bot()

                                if fsm_vars.state_machine.has_state(target_state_name):
                                    ConsoleLog("Debug Jump", f"Attempting to jump main FSM to: {target_state_name}", Console.MessageType.Notice)

                                    last_required_flag = STATE_ENTRANCE_FLAG_MAP.get(target_state_name)
                                    target_flag_index = -1
                                    if last_required_flag:
                                        try:
                                            target_flag_index = PROGRESS_FLAGS_ORDER.index(last_required_flag)
                                        except ValueError:
                                            ConsoleLog("Debug Jump", f"Warning: Flag '{last_required_flag}' for state '{target_state_name}' not found in PROGRESS_FLAGS_ORDER.", Console.MessageType.Warning)

                                    ConsoleLog("Debug Jump", f"Setting flags up to index {target_flag_index} ({last_required_flag or 'None'}) to True, others to False.", Console.MessageType.Debug)
                                    for i, flag in enumerate(PROGRESS_FLAGS_ORDER):
                                        if flag in ["logged_out", "character_delete_confirmed", "character_created_successfully"]:
                                            continue

                                        should_be_true = (i <= target_flag_index)
                                        setattr(bot_vars, flag, should_be_true)

                                    if target_state_name == "OP: Depositing Proof of Triumph":
                                        bot_vars.farmed_the_proof = True
                                        ConsoleLog("Debug Jump", "  Set bot_vars.farmed_the_proof = True (special case for deposit jump)", Console.MessageType.Debug)

                                    fsm_vars.state_machine.jump_to_state_by_name(target_state_name)
                                    if not bot_vars.bot_started:
                                        bot_vars.bot_started = True
                                    ConsoleLog("Debug Jump", f"Jump successful. Current state: {fsm_vars.state_machine.get_current_step_name()}", Console.MessageType.Success)
                                else:
                                    ConsoleLog("Debug Jump", f"Error: State '{target_state_name}' not found in main FSM!", Console.MessageType.Error)

                            except Exception as e:
                                ConsoleLog("Debug Jump", f"Error during jump to {target_state_name}: {e}", Console.MessageType.Error)
                                ConsoleLog("Debug Jump", f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)       

        if PyImGui.collapsing_header("Other FSM and Variable Debug"):
            if PyImGui.begin_tab_bar("MyTabBar"):
                if bot_vars.test:
                    if PyImGui.begin_tab_item("Debug: Test buttons"):
                        if PyImGui.button("Get Target Name"):
                            target = Player.GetTargetID()
                            Agent.RequestName(target)
                            agent_name_recieved = False
                            agent_name =""
                            
                            if not agent_name_recieved and Agent.IsNameReady(target):
                                agent_name_recieved = True
                                agent_name = Agent.GetName(target)
                            
                            print(f"Target Name: {agent_name}")
                        PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Debug: Variables"):
                    ImGui.table("Variable Info", ["Value", "Data"], [
                            ("pause_combat_fsm:", bot_vars.pause_combat_fsm),
                            ("movement_handler.is_paused", fsm_vars.movement_handler.is_paused()),
                            ("global_combat_fsm.is_paused", fsm_vars.global_combat_fsm.is_paused()),
                            ("state_machine.is_paused", fsm_vars.state_machine.is_paused()),
                            ("has_intro_run:", bot_vars.has_intro_run),
                            ("first_time_chahbek_village:", bot_vars.first_time_chahbek_village),
                            ("first_mission_run:", bot_vars.first_mission_run),
                            ("has_post_mission_run:", bot_vars.has_post_mission_run),
                            ("first_time_kamadan:", bot_vars.first_time_kamadan),
                            ("first_time_plains:", bot_vars.first_time_plains),
                            ("first_time_ssgh:", bot_vars.first_time_ssgh),
                            ("second_time_plains:", bot_vars.second_time_plains),
                            ("second_time_kamadan:", bot_vars.second_time_kamadan),
                            ("second_time_chahbek_village:", bot_vars.second_time_chahbek_village),
                            ("second_mission_run:", bot_vars.second_mission_run),
                            ("farmed_the_proof:", bot_vars.farmed_the_proof),
                            ("logged_out:", bot_vars.logged_out),
                            ("character_delete_confirmed:", bot_vars.character_delete_confirmed),
                            ("character_created_successfully:", bot_vars.character_created_successfully),
                            ("next_create_index:", bot_vars.next_create_index),
                            ("character_to_delete_name:", bot_vars.character_to_delete_name),
                        ])
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Debug: Combat"):
                    draw_fsm_info("Global Combat FSM", fsm_vars.global_combat_fsm, False)
                    draw_fsm_info("Combat Handler FSM", fsm_vars.global_combat_handler, False)
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Debug: FollowXY"):
                    ImGui.table("follow info", ["Value", "Data"], [
                        ("Waypoint:", fsm_vars.movement_handler.waypoint),
                        ("Following:", fsm_vars.movement_handler.is_following()),
                        ("Has Arrived:", fsm_vars.movement_handler.has_arrived()),
                        ("Distance to Waypoint:", fsm_vars.movement_handler.get_distance_to_waypoint()),
                        ("Time Elapsed:", fsm_vars.movement_handler.get_time_elapsed()),
                        ("wait Timer:", fsm_vars.movement_handler.wait_timer.GetElapsedTime()),
                        ("wait timer run once", fsm_vars.movement_handler.wait_timer_run_once),
                        ("is casting", Agent.IsCasting(Player.GetAgentID())),
                        ("is moving", Agent.IsMoving(Player.GetAgentID())),
                    ])
                    PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
        if PyImGui.collapsing_header("All FSM"):
            for name, fsm in vars(fsm_vars).items():
                if isinstance(fsm, FSM):
                    draw_fsm_info(f"Sub-FSM: {name.replace('_', ' ').title()}", fsm)
    PyImGui.end()
#endregion

#region --- Main Loop ---
def main():
    try:
        
        if ((Map.GetDescriptionID() == 39684 and Map.GetMapID() == 514) or Map.IsInCinematic()):
            return
        
        draw_window()

        is_in_pregame_fsm_state = False
        if fsm_vars.state_machine.current_state:
            current_main_state_name = fsm_vars.state_machine.get_current_step_name()
            if current_main_state_name in PREGAME_FSM_STATES:
                is_in_pregame_fsm_state = True

        if (is_in_load_screen() or not Map.IsMapReady() or not Party.IsPartyLoaded()) and not is_in_pregame_fsm_state:
            return
        
        if not is_bot_started():
            return
        
        no_valid_names = not bot_vars.character_names or not any(bot_vars.character_names)
        if no_valid_names and not bot_vars.character_name_logged:
            print(f"no valid names {no_valid_names}")
            check_character_name_added()
            
        if fsm_vars.global_combat_fsm.is_finished():
            fsm_vars.global_combat_fsm.reset()
            return
        
        if fsm_vars.state_machine.is_finished():
            fsm_vars.state_machine.reset()
            print("[FSM] Warning: Main FSM finished unexpectedly. Possible missing condition_fn trigger.")
            return

        if Map.IsExplorable() and not is_in_load_screen():
            if bot_vars.combat_started:
                combat_handler.HandleCombat()
                
        bot_vars.press_key_aq.ProcessQueue()
        ActionQueueManager().ProcessAll()
        
        if not bot_vars.pause_combat_fsm:
            fsm_vars.global_combat_fsm.update()
        fsm_vars.state_machine.update()
        
    except ImportError as e:
        ConsoleLog(bot_vars.window_module.module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        ConsoleLog(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        ConsoleLog(bot_vars.window_module.module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        ConsoleLog(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        ConsoleLog(bot_vars.window_module.module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        ConsoleLog(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        ConsoleLog(bot_vars.window_module.module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        ConsoleLog(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass
#endregion

if __name__ == "__main__":
    main()
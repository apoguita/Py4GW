
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, AutoPathing, Py4GW, FSM, ConsoleLog, Color, DXOverlay,
                          UIManager,ModelID, Utils
                         )
from typing import List, Tuple, Any, Generator, Callable
import PyImGui

MODULE_NAME = "sequential bot test"

class GeneralHelpers:
    @staticmethod
    def is_party_member_dead():
        is_someone_dead = False
        players = GLOBAL_CACHE.Party.GetPlayers()
        henchmen = GLOBAL_CACHE.Party.GetHenchmen()
        heroes = GLOBAL_CACHE.Party.GetHeroes()
 
        for player in players:
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            if GLOBAL_CACHE.Agent.IsDead(agent_id):
                is_someone_dead = True
                break
        for henchman in henchmen:
            if GLOBAL_CACHE.Agent.IsDead(henchman.agent_id):
                is_someone_dead = True
                break
            
        for hero in heroes:
            if GLOBAL_CACHE.Agent.IsDead(hero.agent_id):
                is_someone_dead = True
                break

        return is_someone_dead
    
    @staticmethod
    def is_map_loading():
        if GLOBAL_CACHE.Map.IsMapLoading():
            return True
        return False
    
    @staticmethod
    def is_player_dead():
        return GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID())

class BotConfig:
    def __init__(self, parent: "Botting",  bot_name: str):
        self.parent = parent
        self.bot_name = bot_name
        self.pause_on_danger = False
        self.pause_on_danger_counter = 0
        self.pause_combat_fn: Callable[[], bool] = lambda: False
        self.pause_combat_fn_counter = 0
        self._reset_pause_on_combat_fn()
        self.movement_timeout = 15000
        self.movement_timeout_counter = 0
        self.movement_tolerance = 150
        self.movement_tolerance_counter = 0

        self.path = []
        self.path_to_draw = []
        self.draw_path = True

        self.get_path_to_counter = 0
        self.set_path_to_counter = 0
        self.move_to_counter = 0
        self.follow_path_counter = 0
        self.follow_path_succeeded = False
        self.on_follow_path_failed_counter = 0
        self.on_follow_path_failed: Callable[[], bool] = lambda: False

        self.halt_on_death = True
        self.halt_on_death_counter = 0
        self.running = False
        self.initialized = False
        self.FSM = FSM(bot_name)
        
        self.log_actions = False

        self.dialog_at_counter = 0
        self.dialog_at_succeeded = False

        self.wait_for_map_load_counter = 0
        
        self.player_profession_primary = "None"
        self.player_profession_secondary = "None"

        self.update_player_data_counter = 0

        self.waste_time_counter = 0

    def _set_log_actions(self, log_actions: bool) -> None:
        self.log_actions = log_actions
        if self.log_actions:
            ConsoleLog(MODULE_NAME, f"Set LogActions to {log_actions}", Py4GW.Console.MessageType.Info)

    def _set_pause_on_danger(self, pause_on_danger: bool) -> None:
        self.pause_on_danger = pause_on_danger
        if self.log_actions:
            ConsoleLog(MODULE_NAME, f"Set PauseOnDanger to {pause_on_danger}", Py4GW.Console.MessageType.Info)
     
    def _set_pause_on_combat_fn(self, executable_fn: Callable[[], bool]) -> None:
        self.pause_combat_fn = executable_fn
               
    def _reset_pause_on_combat_fn(self) -> None:
        self._set_pause_on_combat_fn(lambda: Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot) or GeneralHelpers.is_party_member_dead())

    def _set_halt_on_death(self, halt_on_death: bool) -> None:
        self.halt_on_death = halt_on_death
        if self.log_actions:
            ConsoleLog(MODULE_NAME, f"Set HaltOnDeath to {halt_on_death}", Py4GW.Console.MessageType.Info)

    def _set_movement_timeout(self, movement_timeout: int) -> None:
        self.movement_timeout = movement_timeout
        if self.log_actions:
            ConsoleLog(MODULE_NAME, f"Set MovementTimeout to {movement_timeout}", Py4GW.Console.MessageType.Info)

    def _set_movement_tolerance(self, movement_tolerance: int) -> None:
        self.movement_tolerance = movement_tolerance
        if self.log_actions:
            ConsoleLog(MODULE_NAME, f"Set MovementTolerance to {movement_tolerance}", Py4GW.Console.MessageType.Info)

    def _set_on_follow_path_failed(self, on_follow_path_failed: Callable[[], bool]) -> None:
        self.on_follow_path_failed = on_follow_path_failed
        if self.log_actions:
            ConsoleLog(MODULE_NAME, f"Set OnFollowPathFailed to {on_follow_path_failed}", Py4GW.Console.MessageType.Info)

    def _update_player_data(self) -> None:
        primary, secondary = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        self.player_profession_primary = primary
        self.player_profession_secondary = secondary

    #FSM HELPERS
    def set_log_actions(self, log_actions: bool) -> None:
        self.log_actions_counter += 1
        self.FSM.AddState(name=f"LogActions_{self.log_actions_counter}", 
                          execute_fn=lambda:self._set_log_actions(log_actions),)

    def set_pause_on_danger(self, pause_on_danger: bool) -> None:
        self.pause_on_danger_counter += 1
        self.FSM.AddState(name=f"PauseOnDanger_{self.pause_on_danger_counter}", 
                          execute_fn=lambda:self._set_pause_on_danger(pause_on_danger),)

    def set_pause_on_combat_fn(self, pause_on_combat_fn: Callable[[], bool]) -> None:
        self.pause_combat_fn_counter += 1
        self.FSM.AddState(name=f"PauseOnCombatFn_{self.pause_combat_fn_counter}",
                          execute_fn=lambda:self._set_pause_on_combat_fn(pause_on_combat_fn),)

    def reset_pause_on_combat_fn(self) -> None:
        self._reset_pause_on_combat_fn()
        self.FSM.AddState(name=f"ResetPauseOnCombatFn_{self.pause_combat_fn_counter}",
                          execute_fn=lambda:self._reset_pause_on_combat_fn(),)

    def set_halt_on_death(self, halt_on_death: bool) -> None:
        self.halt_on_death_counter += 1
        self.FSM.AddState(name=f"HaltOnDeath_{self.halt_on_death_counter}", 
                          execute_fn=lambda:self._set_halt_on_death(halt_on_death),)

    def set_movement_timeout(self, movement_timeout: int) -> None:
        self.movement_timeout_counter += 1
        self.FSM.AddState(name=f"MovementTimeout_{self.movement_timeout_counter}",
                          execute_fn=lambda:self._set_movement_timeout(movement_timeout),)

    def set_movement_tolerance(self, movement_tolerance: int) -> None:
        self.movement_tolerance_counter += 1
        self.FSM.AddState(name=f"MovementTolerance_{self.movement_tolerance_counter}",
                          execute_fn=lambda:self._set_movement_tolerance(movement_tolerance),)

    def set_on_follow_path_failed(self, on_follow_path_failed: Callable[[], bool]):
        self.on_follow_path_failed_counter += 1
        self.FSM.AddState(name=f"OnFollowPathFailed_{self.on_follow_path_failed_counter}",
                          execute_fn=lambda:self._set_on_follow_path_failed(on_follow_path_failed),)

    def reset_on_follow_path_failed(self) -> None:
        self.on_follow_path_failed_counter += 1
        self.set_on_follow_path_failed(lambda: self.parent.helpers.default_on_unmanaged_fail())

    def update_player_data(self) -> None:
        self.update_player_data_counter += 1
        self.FSM.AddState(name=f"UpdatePlayerData_{self.update_player_data_counter}",
                          execute_fn=lambda:self._update_player_data(),)

class BottingHelpers:
    def __init__(self, parent: "Botting"):
        self.parent = parent

    def is_map_loading(self):
        if GeneralHelpers.is_map_loading():
            return True
        if not self.parent.config.running:
            return True
        return False

    def _waste_time(self, duration: int=100):
        yield from Routines.Yield.wait(duration)

    def waste_time(self, duration: int=100) -> None:
        self.parent.config.waste_time_counter += 1
        step_name = f"WasteTime_{self.parent.config.waste_time_counter}"
        self.parent.config.FSM.AddYieldRoutineStep(
            name=step_name,
            coroutine_fn=lambda: self._waste_time(duration)
        )

    def insert_header_step(self, step_name: str) -> None:
        self.parent.config.FSM.AddYieldRoutineStep(
            name=step_name,
            coroutine_fn=lambda: self._waste_time()
        )

    def on_unmanaged_fail(self) -> bool:
        ConsoleLog(MODULE_NAME, "Follow path failed for an unmanaged reason, stopping bot.", Py4GW.Console.MessageType.Warning)
        self.parent.Stop()
        return True
        
    def default_on_unmanaged_fail(self) -> bool:
        ConsoleLog(MODULE_NAME, "Follow path failed for an unmanaged reason, stopping bot.", Py4GW.Console.MessageType.Warning)
        self.parent.Stop()
        return True

    def _follow_path(
        self,
        path: List[Tuple[float, float]],
    ) -> Generator[Any, Any, bool]:
        
        exit_condition = lambda: GeneralHelpers.is_player_dead() or self.is_map_loading() if self.parent.config.halt_on_death else self.is_map_loading()
        pause_condition = self.parent.config.pause_combat_fn if self.parent.config.pause_on_danger else None

        #ConsoleLog(MODULE_NAME, f"Following path with {len(path)} points.", Py4GW.Console.MessageType.Info)
        #for point in path:
        #    ConsoleLog(MODULE_NAME, f" - {point}", Py4GW.Console.MessageType.Info)

        success_movement = yield from Routines.Yield.Movement.FollowPath(
            path_points=path,
            custom_exit_condition=exit_condition,
            log=self.parent.config.log_actions,
            custom_pause_fn=pause_condition,
            timeout=self.parent.config.movement_timeout,
            tolerance=self.parent.config.movement_tolerance,
        )
        
        self.parent.config.follow_path_succeeded = success_movement
        if not success_movement:
            if exit_condition:
                return True
            #self.on_follow_path_failed()
            return False
        
        return True

    def follow_path(self, step_name: str="") -> None:
        self.parent.config.follow_path_counter += 1
        if step_name == "":
            step_name = f"FollowPath_{self.parent.config.follow_path_counter}"

        self.parent.config.FSM.AddYieldRoutineStep(
            name=step_name,
            coroutine_fn=lambda: self._follow_path(self.parent.config.path)
        )

    def _get_path_to(self, x: float, y: float):
        path = yield from AutoPathing().get_path_to(x, y)
        self.parent.config.path = path.copy()
        current_pos = GLOBAL_CACHE.Player.GetXY()
        self.parent.config.path_to_draw.clear()
        self.parent.config.path_to_draw.append((current_pos[0], current_pos[1]))
        self.parent.config.path_to_draw.extend(path.copy())

    def get_path_to(self, x: float, y: float, step_name: str="") -> None:
        self.parent.config.get_path_to_counter += 11
        if step_name == "":
            step_name = f"GetPathTo_{self.parent.config.get_path_to_counter}"

        self.parent.config.FSM.AddYieldRoutineStep(
            name=step_name,
            coroutine_fn=lambda: self._get_path_to(x, y)
        )

    def _set_path_to(self, path: List[Tuple[float, float]]):
        self.parent.config.path = path.copy()
        self.parent.config.path_to_draw = path.copy()
        
    def set_path_to(self, path: List[Tuple[float, float]], step_name: str="") -> None:
        self.parent.config.set_path_to_counter += 1
        if step_name == "":
            step_name = f"SetPathTo_{self.parent.config.set_path_to_counter}"

        self.parent.config.FSM.AddYieldRoutineStep(
            name=step_name,
            coroutine_fn=lambda: self._set_path_to(path)
        )
        
    def draw_path(self, color:Color=Color(255, 255, 0, 255)) -> None:
        overlay = DXOverlay()

        path = self.parent.config.path_to_draw

        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            z1 = DXOverlay.FindZ(x1, y1) - 125
            z2 = DXOverlay.FindZ(x2, y2) - 125
            overlay.DrawLine3D(x1, y1, z1, x2, y2, z2, color.to_color(), False)


    def _interact_with_agent(self,coords: Tuple[float, float],dialog_id: int=0) -> Generator[Any, Any, bool]:
        result = yield from Routines.Yield.Agents.InteractWithAgentXY(*coords)
        if not result:
            self.on_unmanaged_fail()
            self.parent.config.dialog_at_succeeded = False
            return False

        if not self.parent.config.running:
            yield from Routines.Yield.wait(100)
            self.parent.config.dialog_at_succeeded = False
            return False

        if dialog_id != 0:
            GLOBAL_CACHE.Player.SendDialog(dialog_id)
            yield from Routines.Yield.wait(500)

        self.parent.config.dialog_at_succeeded = True
        return True

    def interact_with_agent(self, coords: Tuple[float, float], dialog_id: int=0, step_name: str="") -> None:
        self.parent.config.dialog_at_counter += 1
        if step_name == "":
            step_name = f"InteractWithAgent_{self.parent.config.dialog_at_counter}"

        self.parent.config.FSM.AddYieldRoutineStep(
            name=step_name,
            coroutine_fn=lambda: self._interact_with_agent(coords, dialog_id)
        )
        
    def _wait_for_map_load(self, target_map_id):
        wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(target_map_id)
        if not wait_of_map_load:
            Py4GW.Console.Log(MODULE_NAME, "Map load failed.", Py4GW.Console.MessageType.Error)
            self.on_unmanaged_fail()
        yield from Routines.Yield.wait(1000)
        
    def wait_for_map_load(self, target_map_id: int) -> None:
        self.parent.config.wait_for_map_load_counter += 1
        map_name = GLOBAL_CACHE.Map.GetMapName(target_map_id)
        self.parent.config.FSM.AddYieldRoutineStep(
            name=f"WaitForMapLoad_{target_map_id}_{self.parent.config.wait_for_map_load_counter}_{map_name}",
            coroutine_fn=lambda: self._wait_for_map_load(target_map_id)
        )

class Botting:
    def __init__(self, bot_name="DefaultBot"):
        self.bot_name = bot_name
        self.helpers = BottingHelpers(self)
        self.config = BotConfig(self, bot_name)
        
        
    def Routine(self):
        pass

    def Start(self):
        self.config.FSM.start()
        self.config.running = True

    def Stop(self):
        self.config.running = False
        self.config.FSM.stop()

    def Update(self):
        if not self.config.initialized:
            self.Routine()
            self.config.initialized = True
            
        if self.config.running:
            self.config.FSM.update()

    def WasteTime(self, duration: int= 100) -> None:
        self.helpers.waste_time(duration)

    def AddFSMCustomYieldState(self, execute_fn, name: str) -> None:
        self.config.FSM.AddYieldRoutineStep(name=name, coroutine_fn=execute_fn)

    def MoveTo(self, x:float, y:float, step_name: str=""):
        self.config.move_to_counter += 1
        if step_name == "":
            step_name = f"MoveTo_{self.config.move_to_counter}"
            
        self.helpers.insert_header_step(step_name)  
        self.helpers.get_path_to(x, y, step_name=step_name+"gpt")
        self.helpers.follow_path(step_name=step_name+"fp")

    def FollowPath(self, path: List[Tuple[float, float]], step_name: str="") -> None:
        self.config.follow_path_counter += 1
        if step_name == "":
            step_name = f"FollowPath_{self.config.follow_path_counter}"

        self.helpers.insert_header_step(step_name)
        self.helpers.set_path_to(path, step_name=step_name+"spt")
        self.helpers.follow_path(step_name=step_name+"fp")
        
    def DrawPath(self, color:Color=Color(255, 255, 0, 255)) -> None:
        if self.config.draw_path:
            self.helpers.draw_path(color)

    def DialogAt(self, x: float, y: float, dialog:int, step_name: str="") -> None:
        self.config.dialog_at_counter += 1
        if step_name == "":
            step_name = f"DialogAt_{self.config.dialog_at_counter}"

        self.helpers.insert_header_step(step_name)
        self.helpers.interact_with_agent((x, y), dialog_id=dialog, step_name=step_name+"ia")

    def InteractAt(self, x: float, y: float, step_name: str="") -> None:
        self.helpers.insert_header_step(step_name)
        self.helpers.interact_with_agent((x, y), step_name=step_name+"ia")

    def WaitForMapLoad(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        if target_map_name:
            target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)
            
        self.helpers.wait_for_map_load(target_map_id)

# ----------------------- BOT CONFIGURATION --------------------------------------------

LUDO_I_AM_SURE = 0x85
UNLOCK_SECONDARY = 0x813D08
TAKE_SECONDARY_REWARD = 0x813D07
TAKE_MINISTER_CHO_QUEST = 0x813E01
UNLOCK_STORAGE = 0x84
GUARDMAN_ZUI_DLG4 = 0x80000B

bot = Botting("Factions Leveler")

#region bot_helpers
def assign_profession_unlocker_dialog():
    global UNLOCK_SECONDARY, bot
    UNLOCK_SECONDARY = 0x813D08 if bot.config.player_profession_primary != "Assassin" else 0x813D0E
    yield from bot.helpers._waste_time()

def cancel_skill_reward_window():
    global bot
    cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)  # Cancel button frame ID
    if not cancel_button_frame_id:
        Py4GW.Console.Log(MODULE_NAME, "Cancel button frame ID not found.", Py4GW.Console.MessageType.Error)
        bot.helpers.on_unmanaged_fail()
        return
    
    while not UIManager.FrameExists(cancel_button_frame_id):
        yield from bot.helpers._waste_time(1000)
        return
    
    UIManager.FrameClick(cancel_button_frame_id)
    yield from bot.helpers._waste_time(1000)
    
class BotLocals:
    def __init__(self):
        self.target_cupcake_count = 50
        self.target_honeycomb_count = 100
        self.use_cupcakes = True
        self.use_honeycombs = True

bot_locals = BotLocals()

def prepare_for_battle(): 
    global bot, bot_locals
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if profession == "Warrior":
        yield from Routines.Yield.Skills.LoadSkillbar("OQcUEvq0jvIClLHAAAAAAAAAAA",log=False)
    elif profession == "Ranger":
        yield from Routines.Yield.Skills.LoadSkillbar("OgcUcLs1jvIPsv5yAAAAAAAAAA",log=False)
    elif profession == "Monk":
        yield from Routines.Yield.Skills.LoadSkillbar("OwcB0lkRuMAAAAAAAAAA",log=False)
    elif profession == "Necromancer":
        yield from Routines.Yield.Skills.LoadSkillbar("OAdTUOj8FxlTDAAAAAAAAAAA",log=False)
    elif profession == "Mesmer":
        yield from Routines.Yield.Skills.LoadSkillbar("OQdTAEx9FRDcZAAAAAAAAAAA",log=False)
    elif profession == "Elementalist":
        yield from Routines.Yield.Skills.LoadSkillbar("OgdToO28FRYcZAAAAAAAAAAA",log=False)
    elif profession == "Ritualist":
        yield from Routines.Yield.Skills.LoadSkillbar("OAej8JgHpMusvJAAAAAAAAAAAA",log=False)
    elif profession == "Assassin":
        yield from Routines.Yield.Skills.LoadSkillbar("OwBj0NfyoJPsLDAAAAAAAAAA",log=False)
     
    yield from Routines.Yield.wait(500)   
    GLOBAL_CACHE.Party.LeaveParty()
    yield from Routines.Yield.wait(500)
    
    party_size = GLOBAL_CACHE.Map.GetMaxPartySize()
    
    zen_daijun_map_id = 213
    
    if party_size <= 4:
        HEALER_ID = 1
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
        yield from Routines.Yield.wait(250)
        SPIRITS_ID = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRITS_ID)
        yield from Routines.Yield.wait(250)
        GUARDIAN_ID = 2
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(GUARDIAN_ID)
        yield from Routines.Yield.wait(250)
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor"):
        GUARDIAN_ID = 2
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(GUARDIAN_ID)
        yield from Routines.Yield.wait(250)
        DEADLY_ID = 3
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(DEADLY_ID)
        yield from Routines.Yield.wait(250)
        SHOCK_ID = 1
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SHOCK_ID)
        yield from Routines.Yield.wait(250)
        SPIRITS_ID = 4
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRITS_ID)
        yield from Routines.Yield.wait(250)
        HEALER_ID = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
        yield from Routines.Yield.wait(250)
    elif GLOBAL_CACHE.Map.GetMapID() == zen_daijun_map_id:
        FIGHTER_ID = 3
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(FIGHTER_ID)
        yield from Routines.Yield.wait(250)
        CUTTHROAT_ID = 2
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(CUTTHROAT_ID)
        yield from Routines.Yield.wait(250)
        EARTH_ID = 1
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(EARTH_ID)
        yield from Routines.Yield.wait(250)
        SPIRIT_ID = 8
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRIT_ID)
        yield from Routines.Yield.wait(250)
        HEALER_ID = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
        yield from Routines.Yield.wait(250)

    summoning_stone_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Igneous_Summoning_Stone.value)
    if summoning_stone_in_bags < 1:
        GLOBAL_CACHE.Player.SendChatCommand("bonus")
        yield from Routines.Yield.wait(250)
        
    target_cupcake_count = bot_locals.target_cupcake_count
    if bot_locals.use_cupcakes:
        model_id = ModelID.Birthday_Cupcake.value
        cupcake_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        cupcake_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)

        cupcakes_needed = target_cupcake_count - cupcake_in_bags
        if cupcakes_needed > 0 and cupcake_in_storage > 0:
            # First, try to withdraw exactly what we need
            items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, cupcakes_needed)
            yield from Routines.Yield.wait(250)

            if not items_withdrawn:
                # Try withdrawing as much as possible instead
                fallback_amount = min(cupcakes_needed, cupcake_in_storage)
                items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, fallback_amount)
                yield from Routines.Yield.wait(250)

                if not items_withdrawn:
                    Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw cupcakes from storage.", Py4GW.Console.MessageType.Error)

    yield from Routines.Yield.wait(250)

    target_honeycomb_count = bot_locals.target_honeycomb_count
    if bot_locals.use_honeycombs:
        model_id = ModelID.Honeycomb.value
        honey_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        honey_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)

        honey_needed = target_honeycomb_count - honey_in_bags
        if honey_needed > 0 and honey_in_storage > 0:
            # Try withdrawing the full amount first
            items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, honey_needed)
            yield from Routines.Yield.wait(250)

            if not items_withdrawn:
                # Fallback to withdraw whatever is available
                fallback_amount = min(honey_needed, honey_in_storage)
                items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, fallback_amount)
                yield from Routines.Yield.wait(250)

                if not items_withdrawn:
                    Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw honeycombs from storage.", Py4GW.Console.MessageType.Error)

    
def craft_weapons():
    global bot
    
    MELEE_CLASSES = ["Warrior", "Ranger", "Assassin"]
    if bot.config.player_profession_primary in MELEE_CLASSES:
        yield from bot.helpers._interact_with_agent((-6519, 12335))
        iron_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(ModelID.Iron_Ingot.value)
        if iron_in_storage < 5:
            Py4GW.Console.Log(MODULE_NAME, "Not enough Iron Ingots (5) to craft weapons.", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return
        
        items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(ModelID.Iron_Ingot.value, 5)
        yield from bot.helpers._waste_time(500)
        if not items_withdrawn:
            Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw (5) Iron Ingots from storage.", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return
        
        SAI_MODEL_ID = 11643
        merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
        for item_id in merchant_item_list:    
            if GLOBAL_CACHE.Item.GetModelID(item_id) == SAI_MODEL_ID:
                iron_ingots = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Iron_Ingot.value)
                if iron_ingots:
                    trade_item_list = [iron_ingots]
                    quantity_list = [5]
                
                    GLOBAL_CACHE.Trading.Crafter.CraftItem(item_id, 100, trade_item_list, quantity_list)
                    yield from bot.helpers._waste_time(500)
                    break
                
        #equip crafted weapon
        crafted_weapon = GLOBAL_CACHE.Inventory.GetFirstModelID(SAI_MODEL_ID)
        if crafted_weapon:
            GLOBAL_CACHE.Inventory.EquipItem(crafted_weapon, GLOBAL_CACHE.Player.GetAgentID())
            yield from Routines.Yield.wait(500)
        else:
            Py4GW.Console.Log(MODULE_NAME, "Crafted weapon not found in inventory.", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return
    else:
        yield from prepare_for_battle()
        wand = GLOBAL_CACHE.Inventory.GetFirstModelID(6508) #wand
        GLOBAL_CACHE.Inventory.EquipItem(wand, GLOBAL_CACHE.Player.GetAgentID())
        yield from Routines.Yield.wait(250)
        shield = GLOBAL_CACHE.Inventory.GetFirstModelID(6514) #shield
        GLOBAL_CACHE.Inventory.EquipItem(shield, GLOBAL_CACHE.Player.GetAgentID())
        yield from Routines.Yield.wait(250)


def create_bot_routine(bot: Botting) -> None:
    bot.helpers.insert_header_step("StartStep")
    bot.config.set_pause_on_danger(False)
    bot.config.set_halt_on_death(False)
    bot.config.update_player_data()
    #ExitMonasteryOverlook
    bot.MoveTo(-7011, 5750,"Move to Ludo")
    bot.DialogAt(-7048,5817,LUDO_I_AM_SURE, step_name="Talk to Ludo")
    bot.WaitForMapLoad(target_map_name="Shing Jea Monastery")
    #ExitToCourtyard
    bot.MoveTo(-3480, 9460, "ExitToCourtyard001")
    bot.WaitForMapLoad(target_map_name="Linnok Courtyard")
    #Unlock Secondary
    bot.MoveTo(-159, 9174, "Move to Togo 001")
    bot.AddFSMCustomYieldState(assign_profession_unlocker_dialog, "Update Secondary Profession Dialog")
    bot.DialogAt(-92, 9217, UNLOCK_SECONDARY, step_name="Unlock Secondary Profession")
    bot.AddFSMCustomYieldState(cancel_skill_reward_window, "Cancel Skill Reward Window 001")
    bot.AddFSMCustomYieldState(cancel_skill_reward_window, "Cancel Skill Reward Window 002")
    bot.DialogAt(-92, 9217, TAKE_SECONDARY_REWARD, step_name="Take Secondary Reward")
    bot.DialogAt(-92, 9217, TAKE_MINISTER_CHO_QUEST, step_name="Take Minister Cho Quest")
    #ExitCourtyard
    bot.MoveTo(-3762, 9471, "Exit Courtyard 001")
    bot.WaitForMapLoad(target_map_name="Shing Jea Monastery")
    #UnlockXunlaiStorage
    path_to_xunlai: List[Tuple[float, float]] = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3869, 10346),]
    bot.FollowPath(path_to_xunlai,"Follow Path to Xunlai")
    bot.DialogAt(-3749, 10367, UNLOCK_STORAGE, step_name="Unlock Xunlai Storage")
    #Craft Weapons
    bot.MoveTo(-6423, 12183, "Move to Weapon Crafter")
    bot.AddFSMCustomYieldState(craft_weapons, "Craft & Equip Weapons")
    #Exit to Sunqua Vale
    bot.MoveTo(-14961,11453, "Exit to Sunqua Vale")
    bot.WaitForMapLoad(target_map_name="Sunqua Vale")
    #Travel to Minister Cho
    bot.MoveTo(6698, 16095, "Move to Minister Cho")
    bot.DialogAt(6637, 16147, GUARDMAN_ZUI_DLG4, step_name="Talk to Guardman Zui")
    bot.WasteTime(5000)
    minister_cho_map_id = 214
    bot.WaitForMapLoad(target_map_id=minister_cho_map_id)
    #Prepare for Minister Cho Mission
    

bot.Routine = create_bot_routine.__get__(bot)



selected_step = 0
def main():
    global selected_step
    try:
        bot.Update()
        
        if PyImGui.begin("PathPlanner Test", PyImGui.WindowFlags.AlwaysAutoResize):
            
            if PyImGui.button("Start Botting"):
                bot.Start()

            if PyImGui.button("Stop Botting"):
                bot.Stop()
                
            PyImGui.separator()
            
            fsm_steps = bot.config.FSM.get_state_names()
            selected_step = PyImGui.combo("FSM Steps",selected_step,  fsm_steps)
            if PyImGui.button("start at Step"):
                if selected_step < len(fsm_steps):
                    bot.config.running = True
                    bot.config.FSM.reset()
                    bot.config.FSM.jump_to_state_by_name(fsm_steps[selected_step])
                
            PyImGui.separator()

            bot.config.draw_path = PyImGui.checkbox("Draw Path", bot.config.draw_path)
            
            # Segment-by-segment distances
            if bot.config.path and len(bot.config.path) >= 2:
                if PyImGui.collapsing_header("Path Segments"):
                    total = 0.0
                    for i in range(len(bot.config.path) - 1):
                        p0 = bot.config.path[i][:2]
                        p1 = bot.config.path[i + 1][:2]
                        d = Utils.Distance(p0, p1)
                        total += d
                        PyImGui.text(f"{i:02d} {bot.config.path[i]} -> {i+1:02d} {bot.config.path[i+1]}  |  d={d:.1f}")
                    PyImGui.separator()
                    PyImGui.text(f"Total: {total:.1f}")


        PyImGui.end()

        bot.DrawPath()

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()

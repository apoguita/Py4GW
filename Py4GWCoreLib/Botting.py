  
from typing import Any, Tuple, Callable, List

from .botting_src.helpers import BottingHelpers
from .botting_src.botconfig import BotConfig
from .botting_src.property import Property
from .Py4GWcorelib import Color


class BottingClass:
    def __init__(self, bot_name="DefaultBot"):
        self.bot_name = bot_name
        self.helpers = BottingHelpers(self)
        self.config = BotConfig(self, bot_name)
    
    def AddHeaderStep(self, step_name: str) -> None:
        self.helpers.insert_header_step(step_name)

    def Routine(self):
        print("This method should be overridden in the subclass.")
        pass
    
    def _start_coroutines(self):
        # add all upkeep coroutines once
        H = self.helpers

        self.config.FSM.AddManagedCoroutine("keep_alcohol",        H.upkeep_alcohol())
        self.config.FSM.AddManagedCoroutine("keep_city_speed",     H.upkeep_city_speed())
        self.config.FSM.AddManagedCoroutine("keep_morale",         H.upkeep_morale())
        self.config.FSM.AddManagedCoroutine("keep_armor_salv",     H.upkeep_armor_of_salvation())
        self.config.FSM.AddManagedCoroutine("keep_celerity",       H.upkeep_essence_of_celerity())
        self.config.FSM.AddManagedCoroutine("keep_grail",          H.upkeep_grail_of_might())
        self.config.FSM.AddManagedCoroutine("keep_blue_candy",     H.upkeep_blue_rock_candy())
        self.config.FSM.AddManagedCoroutine("keep_green_candy",    H.upkeep_green_rock_candy())
        self.config.FSM.AddManagedCoroutine("keep_red_candy",      H.upkeep_red_rock_candy())
        self.config.FSM.AddManagedCoroutine("keep_cupcake",        H.upkeep_birthday_cupcake())
        self.config.FSM.AddManagedCoroutine("keep_pumpkin_pie",    H.upkeep_slice_of_pumpkin_pie())
        self.config.FSM.AddManagedCoroutine("keep_soup",           H.upkeep_bowl_of_skalefin_soup())
        self.config.FSM.AddManagedCoroutine("keep_candy_apple",    H.upkeep_candy_apple())
        self.config.FSM.AddManagedCoroutine("keep_candy_corn",     H.upkeep_candy_corn())
        self.config.FSM.AddManagedCoroutine("keep_drake_kabob",    H.upkeep_drake_kabob())
        self.config.FSM.AddManagedCoroutine("keep_golden_egg",     H.upkeep_golden_egg())
        self.config.FSM.AddManagedCoroutine("keep_pahnai_salad",   H.upkeep_pahnai_salad())
        self.config.FSM.AddManagedCoroutine("keep_war_supplies",   H.upkeep_war_supplies())
        self.config.FSM.AddManagedCoroutine("keep_imp",           H.upkeep_imp())
        self.config.FSM.AddManagedCoroutine("keep_auto_combat",    H.upkeep_auto_combat())
        self.config.events.start()


    def Start(self):
        self.config.FSM.start()
        self.config.fsm_running = True
        self._start_coroutines()

    def Stop(self):
        self.config.FSM.RemoveAllManagedCoroutines()
        self.config.FSM.stop()
        self.config.fsm_running = False

    def StartAtStep(self, step_name: str) -> None:
        self.Stop()
        self.config.fsm_running = True
        self.config.FSM.reset()
        self.config.FSM.jump_to_state_by_name(step_name)
        self._start_coroutines()

    def Update(self):
        if not self.config.initialized:
            self.Routine()
            self.config.initialized = True
        if self.config.fsm_running:
            self.config.FSM.update()
            

    def WasteTime(self, duration: int= 100) -> None:
        self.helpers.waste_time(duration)

    def WasteTimeUntilConditionMet(self, condition: Callable[[], bool], duration: int=1000) -> None:
        self.helpers.waste_time_until_condition_met(condition, duration)
        
    def WasteTimeUntilOOC(self) -> None:
        from .Routines import Routines
        from .Py4GWcorelib import Range
        wait_condition = lambda: not(Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot))
        self.helpers.waste_time_until_condition_met(wait_condition)

    def AddFSMCustomYieldState(self, execute_fn, name: str) -> None:
        self.config.FSM.AddYieldRoutineStep(name=name, coroutine_fn=execute_fn)

    def Travel(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        from .GlobalCache import GLOBAL_CACHE
        if target_map_name:
            target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)

        self.helpers.travel(target_map_id)

    def MoveTo(self, x:float, y:float, step_name: str=""):
        if step_name == "":
            step_name = f"MoveTo_{self.config.get_counter('MOVE_TO')}"

        self.helpers.get_path_to(x, y)
        self.helpers.follow_path()

    def FollowPath(self, path: List[Tuple[float, float]], step_name: str="") -> None:
        if step_name == "":
            step_name = f"FollowPath_{self.config.get_counter('FOLLOW_PATH')}"

        self.helpers.set_path_to(path)
        self.helpers.follow_path()
        
    def DrawPath(self, color:Color=Color(255, 255, 0, 255)) -> None:
        if self.config.config_properties.draw_path.is_active():
            self.helpers.draw_path(color)

    def DialogAt(self, x: float, y: float, dialog:int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"DialogAt_{self.config.get_counter('DIALOG_AT')}"

        self.helpers.interact_with_agent((x, y), dialog_id=dialog)
        
    def DialogWithModel(self, model_id: int, dialog:int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"DialogWithModel_{self.config.get_counter('DIALOG_AT')}"

        self.helpers.interact_with_model(model_id=model_id, dialog_id=dialog)

    def InteractNPCAt(self, x: float, y: float, step_name: str="") -> None:
        if step_name == "":
            step_name = f"InteractAt_{self.config.get_counter('INTERACT_AT')}"

        self.helpers.interact_with_agent((x, y))

    def InteractGadgetAt(self, x: float, y: float, step_name: str="") -> None:
        if step_name == "":
            step_name = f"InteractGadgetAt_{self.config.get_counter('INTERACT_GADGET_AT')}"

        self.helpers.interact_with_gadget((x, y))

    def InteractWithModel(self, model_id: int) -> None:
        self.helpers.interact_with_model(model_id=model_id)

    def WaitForMapLoad(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        from Py4GWCoreLib import GLOBAL_CACHE
        if target_map_name:
            target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)
            
        self.helpers.wait_for_map_load(target_map_id)

    def EnterChallenge(self, wait_for:int= 4500):
        self.helpers.enter_challenge(wait_for=wait_for)
        
    def CancelSkillRewardWindow(self):
        self.helpers.cancel_skill_reward_window()
        
    def WithdrawItems(self, model_id:int, quantity:int):
        self.helpers.withdraw_items(model_id, quantity)

    def CraftItem(self, model_id: int, value: int, trade_items_models: list[int], quantity_list: list[int]):
        self.helpers.craft_item(model_id, value, trade_items_models, quantity_list)

    def EquipItem(self, model_id: int):
        self.helpers.equip_item(model_id)
        
    def LeaveParty(self):
        self.helpers.leave_party()
        
    def SpawnBonusItems(self):
        self.helpers.spawn_bonus_items()
        
    def FlagAllHeroes(self, x: float, y: float):
        self.helpers.flag_all_heroes(x, y)

    def UnflagAllHeroes(self):
        self.helpers.unflag_all_heroes()
        
    def Resign(self):
        self.helpers.resign()
        
    def SendChatMessage(self, channel: str, message: str):
        self.helpers.send_chat_message(channel, message)
        
    def PrintMessageToConsole(self, source: str, message: str):
        self.helpers.print_message_to_console(source, message)

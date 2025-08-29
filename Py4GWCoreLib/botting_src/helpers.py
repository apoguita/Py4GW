from __future__ import annotations
from typing import Tuple, Any


from typing import Any, Generator, TYPE_CHECKING, List, Callable

if TYPE_CHECKING:
    from .helpers import BottingHelpers  # for type checkers only
    from ..Botting import BottingClass  # for type checkers only

from functools import wraps
from ..Py4GWcorelib import ModelID

# Internal decorator factory (class-scope function)
def _yield_step(label: str,counter_key: str):
    def deco(coro_method):
        @wraps(coro_method)
        def wrapper(self:"BottingHelpers", *args, **kwargs):
            step_name = f"{label}_{self.parent.config.get_counter(counter_key)}"
            self.parent.config.FSM.AddSelfManagedYieldStep(
                name=step_name,
                coroutine_fn=lambda: coro_method(self, *args, **kwargs)
            )
            # Return immediately; FSM will run the coroutine later
        return wrapper
    return deco

yield_step = staticmethod(_yield_step)

def _fsm_step(label: str,counter_key: str):
    def deco(fn):
        @wraps(fn)
        def wrapper(self:"BottingHelpers", *args, **kwargs) -> None:
            step_name = f"{label}_{self.parent.config.get_counter(counter_key)}"
            # Schedule a NORMAL FSM state (non-yield)
            self.parent.config.FSM.AddState(
                name=step_name,
                execute_fn=lambda: fn(self, *args, **kwargs)
            )
        return wrapper
    return deco

fsm_step = staticmethod(_fsm_step)

class BottingHelpers:
    from ..Py4GWcorelib import Color
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        
    def is_map_loading(self):
        from ..GlobalCache import GLOBAL_CACHE
        if GLOBAL_CACHE.Map.IsMapLoading():
            return True
        if not self.parent.config.fsm_running:
            return True
        return False
    
    def on_unmanaged_fail(self) -> bool:
        from ..Py4GWcorelib import ConsoleLog, Console
        ConsoleLog("On Unmanaged Fail", "there was an unmanaged failure, stopping bot.", Console.MessageType.Error)
        self.parent.Stop()
        return True
        
    def default_on_unmanaged_fail(self) -> bool:
        from ..Py4GWcorelib import ConsoleLog, Console
        ConsoleLog("On Unmanaged Fail", "there was an unmanaged failure, stopping bot.", Console.MessageType.Error)
        self.parent.Stop()
        return True

    def insert_header_step(self, step_name: str) -> None:
        from ..Routines import Routines
        header_name = f"[H]{step_name}_{self.parent.config.get_counter("HEADER_COUNTER")}"
        self.parent.config.FSM.AddYieldRoutineStep(
            name=header_name,
            coroutine_fn=lambda: Routines.Yield.wait(100)
        )
        
    def _interact_with_agent(self, coords: Tuple[float, float], dialog_id: int = 0):
        from ..Routines import Routines
        from ..GlobalCache import GLOBAL_CACHE
        #ConsoleLog(MODULE_NAME, f"Interacting with agent at {coords} with dialog_id {dialog_id}", Py4GW.Console.MessageType.Info)
        while True:
            if GLOBAL_CACHE.Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(500)
                break
            else:
                break

        result = yield from Routines.Yield.Agents.InteractWithAgentXY(*coords)
        #ConsoleLog(MODULE_NAME, f"Interaction result: {result}", Py4GW.Console.MessageType.Info)
        if not result:
            self.on_unmanaged_fail()
            self.parent.config.config_properties.dialog_at_succeeded.set_now("value", False)
            return False

        if not self.parent.config.fsm_running:
            yield from Routines.Yield.wait(100)
            self.parent.config.config_properties.dialog_at_succeeded.set_now("value", False)
            return False

        if dialog_id != 0:
            GLOBAL_CACHE.Player.SendDialog(dialog_id)
            yield from Routines.Yield.wait(500)

        self.parent.config.config_properties.dialog_at_succeeded.set_now("value", True)
        return True
    
    def _interact_with_gadget(self, coords: Tuple[float, float]):
        from ..Routines import Routines
        from ..GlobalCache import GLOBAL_CACHE
        #ConsoleLog(MODULE_NAME, f"Interacting with gadget at {coords}", Py4GW.Console.MessageType.Info)
        while True:
            if GLOBAL_CACHE.Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(500)
                break
            else:
                break
        result = yield from Routines.Yield.Agents.InteractWithGadgetXY(*coords)
        #ConsoleLog(MODULE_NAME, f"Interaction result: {result}", Py4GW.Console.MessageType.Info)
        if not result:
            self.on_unmanaged_fail()
            self.parent.config.config_properties.dialog_at_succeeded._apply("value", False)
            return False

        if not self.parent.config.fsm_running:
            yield from Routines.Yield.wait(100)
            self.parent.config.config_properties.dialog_at_succeeded._apply("value", False)
            return False

        return True
    
    def _interact_with_item(self, coords: Tuple[float, float]):
        from ..Routines import Routines
        from ..GlobalCache import GLOBAL_CACHE
        while True:
            if GLOBAL_CACHE.Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(500)
                break
            else:
                break
        result = yield from Routines.Yield.Agents.InteractWithItemXY(*coords)
        if not result:
            self.on_unmanaged_fail()
            self.parent.config.config_properties.dialog_at_succeeded._apply("value", False)
            return False

        if not self.parent.config.fsm_running:
            yield from Routines.Yield.wait(100)
            self.parent.config.config_properties.dialog_at_succeeded._apply("value", False)
            return False

        return True

    def draw_path(self, color:Color=Color(255, 255, 0, 255), use_occlusion: bool = False, snap_to_ground_segments: int = 1, floor_offset: float = 0) -> None:
        from ..DXOverlay import DXOverlay
        from ..GlobalCache import GLOBAL_CACHE
        from ..Pathing import AutoPathing
        overlay = DXOverlay()

        path = self.parent.config.path_to_draw

        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            z1 = DXOverlay.FindZ(x1, y1)
            z2 = DXOverlay.FindZ(x2, y2)
            DXOverlay().DrawLine3D(x1, y1, z1, x2, y2, z2, color.to_color(), use_occlusion, snap_to_ground_segments, floor_offset)

    def auto_combat(self):
        from ..Routines import Routines
        from ..GlobalCache import GLOBAL_CACHE
        global auto_attack_timer, auto_attack_threshold, is_expired
        self.parent.config.auto_combat_handler.SetWeaponAttackAftercast()

        if not (Routines.Checks.Map.MapValid() and 
                Routines.Checks.Player.CanAct() and
                GLOBAL_CACHE.Map.IsExplorable() and
                not self.parent.config.auto_combat_handler.InCastingRoutine()):
            yield from Routines.Yield.wait(100)
        else:
            self.parent.config.auto_combat_handler.HandleCombat()
            #control vars
            auto_attack_timer = self.parent.config.auto_combat_handler.auto_attack_timer.GetTimeElapsed()
            auto_attack_threshold = self.parent.config.auto_combat_handler.auto_attack_timer.throttle_time
            is_expired = self.parent.config.auto_combat_handler.auto_attack_timer.IsExpired()
        yield

    def upkeep_auto_combat(self):
        from ..Routines import Routines
        while True:
            #print (f"autocombat is: {self.parent.config.upkeep.auto_combat.is_active()}")
            if self.parent.config.upkeep.auto_combat.is_active():
                yield from self.auto_combat()
            else:
                yield from Routines.Yield.wait(500)
                
    def restock_item(self, model_id: int, desired_quantity: int) -> Generator[Any, Any, bool]:
        from ..Routines import Routines
        from ..Py4GWcorelib import ConsoleLog
        result = yield from Routines.Yield.Items.RestockItems(model_id, desired_quantity)
        if not result:
            yield
            return False
        yield
        return True

    def upkeep_armor_of_salvation(self):    
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.armor_of_salvation.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_ArmorOfSalvation()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_essence_of_celerity(self):
        from ..Routines import Routines
        while True: 
            if self.parent.config.upkeep.essence_of_celerity.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_EssenceOfCelerity()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_grail_of_might(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.grail_of_might.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GrailOfMight()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_green_rock_candy(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.green_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GreenRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_red_rock_candy(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.red_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_RedRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_blue_rock_candy(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.blue_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BlueRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_birthday_cupcake(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.birthday_cupcake.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BirthdayCupcake()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_slice_of_pumpkin_pie(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.slice_of_pumpkin_pie.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_SliceOfPumpkinPie()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_bowl_of_skalefin_soup(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.bowl_of_skalefin_soup.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BowlOfSkalefinSoup()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_candy_apple(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.candy_apple.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_CandyApple()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_candy_corn(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.candy_corn.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_CandyCorn()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_drake_kabob(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.drake_kabob.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_DrakeKabob()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_golden_egg(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.golden_egg.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GoldenEgg()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_pahnai_salad(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.pahnai_salad.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_PahnaiSalad()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_war_supplies(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.war_supplies.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_WarSupplies()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_alcohol(self):
        import PyEffects
        from ..Routines import Routines
        target_alc_level = 2
        disable_drunk_effects = False
        if disable_drunk_effects:
            PyEffects.PyEffects.ApplyDrunkEffect(0, 0)
        while True:
            if self.parent.config.upkeep.alcohol.is_active():
                
                yield from Routines.Yield.Upkeepers.Upkeep_Alcohol(target_alc_level, disable_drunk_effects)
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_city_speed(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.city_speed.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_City_Speed()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_morale(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.honeycomb.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(110)
            elif (self.parent.config.upkeep.four_leaf_clover.is_active()):
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(100)
            elif self.parent.config.upkeep.morale.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(110)
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_imp(self):
        from ..Routines import Routines
        while True:
            if self.parent.config.upkeep.imp.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_Imp()
            else:
                yield from Routines.Yield.wait(500)
                
    #region yield steps

    @_yield_step(label="WasteTime", counter_key="WASTE_TIME")
    def waste_time(self, duration: int = 100):
        from ..Routines import Routines
        yield from Routines.Yield.wait(duration)

    @_yield_step(label="WasteTimeUntilConditionMet", counter_key="WASTE_TIME")
    def waste_time_until_condition_met(self, condition: Callable[[], bool], duration: int=1000):
        from ..Routines import Routines
        while True:
            yield from Routines.Yield.wait(duration)
            if condition():
                break

    @_yield_step(label="Travel", counter_key="TRAVEL")
    def travel(self, target_map_id):
        from ..Routines import Routines
        from ..GlobalCache import GLOBAL_CACHE
        GLOBAL_CACHE.Map.Travel(target_map_id)
        yield from Routines.Yield.wait(1000)

    @_yield_step(label="FollowPath", counter_key="FOLLOW_PATH")
    def follow_path(self) -> Generator[Any, Any, bool]:
        from ..Routines import Routines
        path = self.parent.config.path
        exit_condition = lambda: Routines.Checks.Player.IsDead() or self.is_map_loading() if self.parent.config.config_properties.halt_on_death.is_active() else self.is_map_loading()
        pause_condition = self.parent.config.pause_on_danger_fn if self.parent.config.config_properties.pause_on_danger.is_active() else None

        success_movement = yield from Routines.Yield.Movement.FollowPath(
            path_points=path,
            custom_exit_condition=exit_condition,
            log=self.parent.config.config_properties.log_actions.is_active(),
            custom_pause_fn=pause_condition,
            timeout=self.parent.config.config_properties.movement_timeout.get('value'),
            tolerance=self.parent.config.config_properties.movement_tolerance.get('value')
        )

        self.parent.config.config_properties.follow_path_succeeded.set_now("value",success_movement)
        if not success_movement:
            if exit_condition:
                return True
            self.on_unmanaged_fail()
            return False
        
        return True

    @_yield_step(label="GetPathTo", counter_key="GET_PATH_TO")
    def get_path_to(self, x: float, y: float):
        from ..Pathing import AutoPathing
        from ..GlobalCache import GLOBAL_CACHE
        path = yield from AutoPathing().get_path_to(x, y)
        self.parent.config.path = path.copy()
        current_pos = GLOBAL_CACHE.Player.GetXY()
        self.parent.config.path_to_draw.clear()
        self.parent.config.path_to_draw.append((current_pos[0], current_pos[1]))
        self.parent.config.path_to_draw.extend(path.copy())

    @_yield_step(label="SetPathTo", counter_key="SET_PATH_TO")
    def set_path_to(self, path: List[Tuple[float, float]]):
        self.parent.config.path = path.copy()
        self.parent.config.path_to_draw = path.copy()

    @_yield_step(label="InteractWithAgent", counter_key="DIALOG_AT")
    def interact_with_agent(self,coords: Tuple[float, float],dialog_id: int=0) -> Generator[Any, Any, bool]:
        return (yield from self._interact_with_agent(coords, dialog_id))
    
    @_yield_step(label="InteractWithGadget", counter_key="DIALOG_AT")
    def interact_with_gadget(self, coords: Tuple[float, float]) -> Generator[Any, Any, bool]:
        return (yield from self._interact_with_gadget(coords))

    @_yield_step(label="InteractWithItem", counter_key="DIALOG_AT")
    def interact_with_item(self, coords: Tuple[float, float]) -> Generator[Any, Any, bool]:
        return (yield from self._interact_with_item(coords))

    @_yield_step(label="InteractWithModel", counter_key="DIALOG_AT")
    def interact_with_model(self, model_id: int, dialog_id: int=0) -> Generator[Any, Any, bool]:
        from ..Routines import Routines
        from ..GlobalCache import GLOBAL_CACHE
        agent_id = Routines.Agents.GetAgentIDByModelID(model_id)
        x,y = GLOBAL_CACHE.Agent.GetXY(agent_id)
        return (yield from self._interact_with_agent((x, y), dialog_id))

    @_yield_step(label="WaitForMapLoad", counter_key="WAIT_FOR_MAP_LOAD")
    def wait_for_map_load(self, target_map_id):
        from ..Routines import Routines
        import Py4GW
        wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(target_map_id)
        if not wait_of_map_load:
            Py4GW.Console.Log("Wait for map load", "Map load failed.", Py4GW.Console.MessageType.Error)
            self.on_unmanaged_fail()
        yield from Routines.Yield.wait(1000)

    @_yield_step(label="EnterChallenge", counter_key="ENTER_CHALLENGE")
    def enter_challenge(self, wait_for:int= 3000):
        from ..GlobalCache import GLOBAL_CACHE
        from ..Routines import Routines
        GLOBAL_CACHE.Map.EnterChallenge()
        yield from Routines.Yield.wait(wait_for)
        
    @_yield_step(label="CancelSkillRewardWindow", counter_key="CANCEL_SKILL_REWARD_WINDOW")
    def cancel_skill_reward_window(self):
        from ..Routines import Routines
        import Py4GW
        from ..UIManager import UIManager
        global bot  
        yield from Routines.Yield.wait(500)
        cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)  # Cancel button frame ID
        if not cancel_button_frame_id:
            Py4GW.Console.Log("CancelSkillRewardWindow", "Cancel button frame ID not found.", Py4GW.Console.MessageType.Error)
            self.parent.helpers.on_unmanaged_fail()
            return
        
        while not UIManager.FrameExists(cancel_button_frame_id):
            yield from Routines.Yield.wait(1000)
            return
        
        UIManager.FrameClick(cancel_button_frame_id)
        yield from Routines.Yield.wait(1000)
            
            
    @_yield_step(label="WithdrawItems", counter_key="WITHDRAW_ITEMS")
    def withdraw_items(self, model_id:int, quantity:int) -> Generator[Any, Any, bool]:
        from ..Routines import Routines
        from ..Py4GWcorelib import ConsoleLog
        import Py4GW
        result = yield from Routines.Yield.Items.WithdrawItems(model_id, quantity)
        if not result:
            ConsoleLog("WithdrawItems", f"Failed to withdraw ({quantity}) items from storage.", Py4GW.Console.MessageType.Error)
            self.parent.helpers.on_unmanaged_fail()
            return False

        return True

    @_yield_step(label="CraftItem", counter_key="CRAFT_ITEM")
    def craft_item(self, output_model_id: int, count: int,
                trade_model_ids: list[int], quantity_list: list[int]):
        from ..Routines import Routines
        from ..Py4GWcorelib import ConsoleLog
        import Py4GW
        result = yield from Routines.Yield.Items.CraftItem(output_model_id=output_model_id,
                                                            count=count,
                                                            trade_model_ids=trade_model_ids,
                                                            quantity_list=quantity_list)
        if not result:
            ConsoleLog("CraftItem", f"Failed to craft item ({output_model_id}).", Py4GW.Console.MessageType.Error)
            self.parent.helpers.on_unmanaged_fail()
            return False

        return True


    @_yield_step(label="EquipItem", counter_key="EQUIP_ITEM")
    def equip_item(self, model_id: int):
        from ..Routines import Routines
        import Py4GW
        from ..Py4GWcorelib import ConsoleLog
        result = yield from Routines.Yield.Items.EquipItem(model_id)
        if not result:
            ConsoleLog("EquipItem", f"Failed to equip item ({model_id}).", Py4GW.Console.MessageType.Error)
            self.parent.helpers.on_unmanaged_fail()
            return False

        return True

    @_yield_step(label="LeaveParty", counter_key="LEAVE_PARTY")
    def leave_party(self):
        from ..GlobalCache import GLOBAL_CACHE
        from ..Routines import Routines
        GLOBAL_CACHE.Party.LeaveParty()
        yield from Routines.Yield.wait(250)

    @_yield_step(label="SpawnBonusItems", counter_key="SPAWN_BONUS")
    def spawn_bonus_items(self):
        from ..Routines import Routines
        yield from Routines.Yield.Items.SpawnBonusItems()

    @_yield_step(label="FlagAllHeroes", counter_key="FLAG_ALL_HEROES")
    def flag_all_heroes(self, x, y):
        from ..GlobalCache import GLOBAL_CACHE
        from ..Routines import Routines
        GLOBAL_CACHE.Party.Heroes.FlagAllHeroes(x,y)
        yield from Routines.Yield.wait(500)

    @_yield_step(label="UnflagAllHeroes", counter_key="FLAG_ALL_HEROES")
    def unflag_all_heroes(self):
        from ..Routines import Routines
        from ..GlobalCache import GLOBAL_CACHE
        GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()
        yield from Routines.Yield.wait(500)

    @_yield_step(label="Resign", counter_key="SEND_CHAT_MESSAGE")
    def resign(self):
        from ..Routines import Routines
        yield from Routines.Yield.Player.Resign()
        yield from Routines.Yield.wait(500)

    @_yield_step(label="SendChatMessage", counter_key="SEND_CHAT_MESSAGE")
    def send_chat_message(self, channel: str, message: str):
        from ..Routines import Routines
        yield from Routines.Yield.Player.SendChatMessage(channel, message)

    @_yield_step(label="PrintMessageToConsole", counter_key="SEND_CHAT_MESSAGE")
    def print_message_to_console(self, source:str, message: str):
        from ..Routines import Routines
        yield from Routines.Yield.Player.PrintMessageToConsole(source, message)
     
    @_yield_step(label="RestockBirthdayCupcake", counter_key="RESTOCK_BIRTHDAY_CUPCAKE")   
    def restock_birthday_cupcake (self):
        if self.parent.config.upkeep.birthday_cupcake.is_active():
            qty = self.parent.config.upkeep.birthday_cupcake.get("restock_quantity")
            yield from self.parent.helpers.restock_item(ModelID.Birthday_Cupcake.value, qty)

    @_yield_step(label="RestockHoneycomb", counter_key="RESTOCK_HONEYCOMB")
    def restock_honeycomb(self):
        if (self.parent.config.upkeep.honeycomb.is_active() or
            self.parent.config.upkeep.morale.is_active()):
            qty = self.parent.config.upkeep.honeycomb.get("restock_quantity")
            yield from self.parent.helpers.restock_item(ModelID.Honeycomb.value, qty)
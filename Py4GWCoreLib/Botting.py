  
from email.mime import message
from typing import Any, Tuple, Callable, List, Iterable, Dict, Optional

from .botting_src.helpers import BottingHelpers
from .botting_src.botconfig import BotConfig
from .botting_src.property import Property
from .Py4GWcorelib import Color, ActionQueueManager
from functools import wraps

def _yield_step(label: str, counter_key: str):
    def deco(coro_method):
        @wraps(coro_method)
        def wrapper(self, *args, **kwargs):
            # Resolve the owner that actually has .config/.FSM
            owner = self
            if not hasattr(owner, "config"):
                owner = getattr(self, "parent", None)
            if owner is None or not hasattr(owner, "config"):
                raise RuntimeError(
                    f"{coro_method.__qualname__}: cannot resolve bot owner with .config"
                )

            step_name = f"{label}_{owner.config.get_counter(counter_key)}"
            owner.config.FSM.AddSelfManagedYieldStep(
                name=step_name,
                coroutine_fn=lambda: coro_method(self, *args, **kwargs)
            )
            # Return immediately; FSM runs the coroutine later
        return wrapper
    return deco

class BottingClass:
    def __init__(self, bot_name="DefaultBot",
                 config_log_actions: bool = False,
                 config_halt_on_death: bool = True,
                 config_pause_on_danger: bool = False,
                 config_movement_timeout: int = 15000,
                 config_movement_tolerance: int = 150,
                 config_draw_path: bool = True,
                 config_use_occlusion: bool = True,
                 config_snap_to_ground: bool = True,
                 config_snap_to_ground_segments: int = 8,
                 config_floor_offset: int = 20,
                 config_follow_path_color: Any = None,
                 #UPKEEP
                 upkeep_alcohol_active: bool = False,
                 upkeep_alcohol_target_drunk_level: int = 2,
                 upkeep_alcohol_disable_visual: bool = True,
                 upkeep_armor_of_salvation_active: bool = False,
                 upkeep_armor_of_salvation_restock: int = 0,
                 upkeep_auto_combat_active: bool = False,
                 upkeep_birthday_cupcake_active: bool = False,
                 upkeep_birthday_cupcake_restock: int = 0,
                 upkeep_blue_rock_candy_active: bool = False,
                 upkeep_blue_rock_candy_restock: int = 0,
                 upkeep_bowl_of_skalefin_soup_active: bool = False,
                 upkeep_bowl_of_skalefin_soup_restock: int = 0,
                 upkeep_candy_apple_active: bool = False,
                 upkeep_candy_apple_restock: int = 0,
                 upkeep_candy_corn_active: bool = False,
                 upkeep_candy_corn_restock: int = 0,
                 upkeep_city_speed_active: bool = False,
                 upkeep_drake_kabob_active: bool = False,
                 upkeep_drake_kabob_restock: int = 0,
                 upkeep_essence_of_celerity_active: bool = False,
                 upkeep_essence_of_celerity_restock: int = 0,
                 upkeep_four_leaf_clover_active: bool = False,
                 upkeep_four_leaf_clover_restock: int = 0,
                 upkeep_golden_egg_active: bool = False,
                 upkeep_golden_egg_restock: int = 0,
                 upkeep_grail_of_might_active: bool = False,
                 upkeep_grail_of_might_restock: int = 0,
                 upkeep_green_rock_candy_active: bool = False,
                 upkeep_green_rock_candy_restock: int = 0,
                 upkeep_honeycomb_active: bool = False,
                 upkeep_honeycomb_restock: int = 0,
                 upkeep_imp_active: bool = False,
                 upkeep_morale_active:bool = False,
                 upkeep_morale_target_level: int = 110,
                 upkeep_pahnai_salad_active: bool = False,
                 upkeep_pahnai_salad_restock: int = 0,
                 upkeep_red_rock_candy_active: bool = False,
                 upkeep_red_rock_candy_restock: int = 0,
                 upkeep_slice_of_pumpkin_pie_active: bool = False,
                 upkeep_slice_of_pumpkin_pie_restock: int = 0,
                 upkeep_war_supplies_active: bool = False,
                 upkeep_war_supplies_restock: int = 0):
        #internal configuration
        self.bot_name = bot_name
        self.helpers = BottingHelpers(self)
        self.config = BotConfig(self, bot_name,
                                config_log_actions=config_log_actions,
                                config_halt_on_death=config_halt_on_death,
                                config_pause_on_danger=config_pause_on_danger,
                                config_movement_timeout=config_movement_timeout,
                                config_movement_tolerance=config_movement_tolerance,
                                config_draw_path=config_draw_path,
                                config_use_occlusion=config_use_occlusion,
                                config_snap_to_ground=config_snap_to_ground,
                                config_snap_to_ground_segments=config_snap_to_ground_segments,
                                config_floor_offset=config_floor_offset,
                                config_follow_path_color=config_follow_path_color,
                                #UPKEEP
                                upkeep_alcohol_active=upkeep_alcohol_active,
                                upkeep_alcohol_target_drunk_level=upkeep_alcohol_target_drunk_level,
                                upkeep_alcohol_disable_visual=upkeep_alcohol_disable_visual,
                                upkeep_armor_of_salvation_active=upkeep_armor_of_salvation_active,
                                upkeep_armor_of_salvation_restock=upkeep_armor_of_salvation_restock,
                                upkeep_auto_combat_active=upkeep_auto_combat_active,
                                upkeep_birthday_cupcake_active=upkeep_birthday_cupcake_active,
                                upkeep_birthday_cupcake_restock=upkeep_birthday_cupcake_restock,
                                upkeep_blue_rock_candy_active=upkeep_blue_rock_candy_active,
                                upkeep_blue_rock_candy_restock=upkeep_blue_rock_candy_restock,
                                upkeep_bowl_of_skalefin_soup_active=upkeep_bowl_of_skalefin_soup_active,
                                upkeep_bowl_of_skalefin_soup_restock=upkeep_bowl_of_skalefin_soup_restock,
                                upkeep_candy_apple_active=upkeep_candy_apple_active,
                                upkeep_candy_apple_restock=upkeep_candy_apple_restock,
                                upkeep_candy_corn_active=upkeep_candy_corn_active,
                                upkeep_candy_corn_restock=upkeep_candy_corn_restock,
                                upkeep_city_speed_active=upkeep_city_speed_active,
                                upkeep_drake_kabob_active=upkeep_drake_kabob_active,
                                upkeep_drake_kabob_restock=upkeep_drake_kabob_restock,
                                upkeep_essence_of_celerity_active=upkeep_essence_of_celerity_active,
                                upkeep_essence_of_celerity_restock=upkeep_essence_of_celerity_restock,
                                upkeep_four_leaf_clover_active=upkeep_four_leaf_clover_active,
                                upkeep_four_leaf_clover_restock=upkeep_four_leaf_clover_restock,
                                upkeep_golden_egg_active=upkeep_golden_egg_active,
                                upkeep_golden_egg_restock=upkeep_golden_egg_restock,
                                upkeep_grail_of_might_active=upkeep_grail_of_might_active,
                                upkeep_grail_of_might_restock=upkeep_grail_of_might_restock,
                                upkeep_green_rock_candy_active=upkeep_green_rock_candy_active,
                                upkeep_green_rock_candy_restock=upkeep_green_rock_candy_restock,
                                upkeep_honeycomb_active=upkeep_honeycomb_active,
                                upkeep_honeycomb_restock=upkeep_honeycomb_restock,
                                upkeep_imp_active=upkeep_imp_active,
                                upkeep_morale_active=upkeep_morale_active,
                                upkeep_morale_target_level=upkeep_morale_target_level,
                                upkeep_pahnai_salad_active=upkeep_pahnai_salad_active,
                                upkeep_pahnai_salad_restock=upkeep_pahnai_salad_restock,
                                upkeep_red_rock_candy_active=upkeep_red_rock_candy_active,
                                upkeep_red_rock_candy_restock=upkeep_red_rock_candy_restock,
                                upkeep_slice_of_pumpkin_pie_active=upkeep_slice_of_pumpkin_pie_active,
                                upkeep_slice_of_pumpkin_pie_restock=upkeep_slice_of_pumpkin_pie_restock,
                                upkeep_war_supplies_active=upkeep_war_supplies_active,
                                upkeep_war_supplies_restock=upkeep_war_supplies_restock)

        #exposed Helpers
        self.States = BottingClass._STATES(self)
        self.UI = BottingClass._UI(self)
        self.Items = BottingClass._ITEMS(self)
        self.Dialogs = BottingClass._DIALOGS(self)
        self.Wait = BottingClass._WAIT(self)
        self.Movement = BottingClass._MOVEMENT(self)
        self.Map = BottingClass._MAP(self)
        self.Interact = BottingClass._INTERACT(self)
        self.Party = BottingClass._PARTY(self)
        self.Events = BottingClass._EVENTS(self)
        self.Properties = BottingClass._PROPERTIES(self)

    #region internal Helpers
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
        self.config.FSM.AddManagedCoroutine("keep_imp",            H.upkeep_imp())
        self.config.FSM.AddManagedCoroutine("keep_auto_combat",    H.upkeep_auto_combat())
        self.config.events.start()
      
    #region Routines  
    def Routine(self):
        print("This method should be overridden in the subclass.")
        pass
    
    def SetMainRoutine(self, routine: Callable) -> None:
        """
        This method Overrides the main routine for the bot.
        """
        try:
            self.Routine = routine.__get__(self, self.__class__)
        except AttributeError:
            self.Routine = routine
    
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
        if self.config.fsm_paused and self.config.fsm_running:
            self.config.state_description = "Paused"
        else:
            self.config.state_description = "Running" if self.config.fsm_running else "Stopped"

        if not self.config.initialized:
            self.Routine()
            self.config.initialized = True
        if self.config.fsm_running:
            self.config.FSM.update()
  
    #region DIALOGS
    class _DIALOGS:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self.combat_status = False

        @_yield_step("DisableAutoCombat","AUTO_DISABLE_AUTO_COMBAT")
        def _disable_auto_combat(self):
            self.combat_status = self.parent.config.upkeep.auto_combat.is_active()
            self.parent.config.upkeep.auto_combat.set_now("active", False)
            ActionQueueManager().ResetAllQueues()
            yield

        @_yield_step("RestoreAutoCombat","AUTO_RESTORE_AUTO_COMBAT")
        def _restore_auto_combat(self):
            self.parent.config.upkeep.auto_combat.set_now("active", self.combat_status)
            yield


        def DialogAt(self, x: float, y: float, dialog:int, step_name: str="") -> None:
            if step_name == "":
                step_name = f"DialogAt_{self.parent.config.get_counter('DIALOG_AT')}"

            #disable combat to prevent interference
            self._disable_auto_combat()

            self.parent.helpers.interact_with_agent((x, y), dialog_id=dialog)

            #re-enable combat
            self._restore_auto_combat()

        def DialogWithModel(self, model_id: int, dialog:int, step_name: str="") -> None:
            if step_name == "":
                step_name = f"DialogWithModel_{self.parent.config.get_counter('DIALOG_AT')}"

            #disable combat to prevent interference
            self._disable_auto_combat()

            self.parent.helpers.interact_with_model(model_id=model_id, dialog_id=dialog)

            #re-enable combat
            self._restore_auto_combat()

    #region EVENTS
    class _EVENTS:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent

        def OnDeathCallback(self, callback: Callable[[], None]) -> None:
            self.parent.config.events.on_death.set_callback(callback)

        def OnPartyWipeCallback(self, callback: Callable[[], None]) -> None:
            self.parent.config.events.on_party_wipe.set_callback(callback)

        def OnPartyDefeatedCallback(self, callback: Callable[[], None]) -> None:
            self.parent.config.events.on_party_defeated.set_callback(callback)

    #region INTERACT
    class _INTERACT:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self.combat_status = False

        @_yield_step("DisableAutoCombat","AUTO_DISABLE_AUTO_COMBAT")
        def _disable_auto_combat(self):
            self.combat_status = self.parent.config.upkeep.auto_combat.is_active()
            self.parent.config.upkeep.auto_combat.set_now("active", False)
            ActionQueueManager().ResetAllQueues()
            yield

        @_yield_step("RestoreAutoCombat","AUTO_RESTORE_AUTO_COMBAT")
        def _restore_auto_combat(self):
            self.parent.config.upkeep.auto_combat.set_now("active", self.combat_status)
            yield

        def InteractNPCAt(self, x: float, y: float, step_name: str="") -> None:
            if step_name == "":
                step_name = f"InteractAt_{self.parent.config.get_counter('INTERACT_AT')}"

            #disable combat to prevent interference
            self._disable_auto_combat()
            
            self.parent.helpers.interact_with_agent((x, y))
            #re-enable combat
            self._restore_auto_combat()

        def InteractGadgetAt(self, x: float, y: float, step_name: str="") -> None:
            if step_name == "":
                step_name = f"InteractGadgetAt_{self.parent.config.get_counter('INTERACT_GADGET_AT')}"

            #disable combat to prevent interference
            self._disable_auto_combat()

            self.parent.helpers.interact_with_gadget((x, y))

            #re-enable combat
            self._restore_auto_combat()

        def InteractItemAt(self, x: float, y: float, step_name: str="") -> None:
            if step_name == "":
                step_name = f"InteractWithItem_{self.parent.config.get_counter('INTERACT_WITH_ITEM')}"

            
            #disable combat to prevent interference
            self._disable_auto_combat()

            self.parent.helpers.interact_with_item((x, y))
            #re-enable combat
            self._restore_auto_combat()

        def InteractWithModel(self, model_id: int, step_name: str="") -> None:
            if step_name == "":
                step_name = f"InteractWithModel_{self.parent.config.get_counter('INTERACT_WITH_MODEL')}"

            #disable combat to prevent interference
            self._disable_auto_combat()

            self.parent.helpers.interact_with_model(model_id=model_id)

            #re-enable combat
            self._restore_auto_combat()

    #region ITEMS
    class _ITEMS:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self.Restock = BottingClass._ITEMS._RESTOCK(parent)

        def Craft(self, model_id: int, value: int, trade_items_models: list[int], quantity_list: list[int]):
            self.parent.helpers.craft_item(model_id, value, trade_items_models, quantity_list)
            
        def Withdraw(self, model_id:int, quantity:int):
            self.parent.helpers.withdraw_items(model_id, quantity)

        def Equip(self, model_id: int):
            self.parent.helpers.equip_item(model_id)
            
        def SpawnBonusItems(self):
            self.parent.helpers.spawn_bonus_items()
        
        class _RESTOCK:
            def __init__(self, parent: "BottingClass"):
                self.parent = parent

            def BirthdayCupcake(self):
                self.parent.helpers.restock_birthday_cupcake()

            def Honeycomb(self):
                self.parent.helpers.restock_honeycomb()


    #region MAP
    class _MAP:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent

        def Travel(self, target_map_id: int = 0, target_map_name: str = "") -> None:
            from .GlobalCache import GLOBAL_CACHE
            if target_map_name:
                target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)

            self.parent.helpers.travel(target_map_id)
            self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)
            
        def EnterChallenge(self, delay:int= 4500, target_map_id: int = 0, target_map_name: str = "") -> None:
            self.parent.helpers.enter_challenge(wait_for=delay)
            self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)

        def TravelGH(self):
            from .GlobalCache import GLOBAL_CACHE
            self.parent.helpers.travel_to_gh()
            self.parent.Wait.WasteTime(8000)
            
        def LeaveGH(self):
            self.parent.helpers.leave_gh()
            self.parent.Wait.WasteTime(8000)


    #region MOVEMENT
    class _MOVEMENT:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            
        def MoveTo(self, x:float, y:float, step_name: str=""):
            if step_name == "":
                step_name = f"MoveTo_{self.parent.config.get_counter('MOVE_TO')}"

            self.parent.helpers.get_path_to(x, y)
            self.parent.helpers.follow_path()

        def FollowPath(self, path: List[Tuple[float, float]], step_name: str="") -> None:
            if step_name == "":
                step_name = f"FollowPath_{self.parent.config.get_counter('FOLLOW_PATH')}"

            self.parent.helpers.set_path_to(path)
            self.parent.helpers.follow_path()
            
        def FollowAutoPath(self, points: List[Tuple[float, float]], step_name: str = "") -> None:
            """
            For each (x, y) target point, compute an autopath and follow it.
            Input format matches FollowPath, but each point is autpathed independently.
            """
            if step_name == "":
                step_name = f"FollowAutoPath_{self.parent.config.get_counter('FOLLOW_AUTOPATH')}"

            for x, y in points:
                self.parent.helpers.get_path_to(x, y)   # autopath to this target
                self.parent.helpers.follow_path()       # then execute the path



        def FollowModelID(self, model_id: int, follow_range: float, exit_condition: Optional[Callable[[], bool]] = lambda:False) -> None:
            self.parent.helpers.follow_model_id(model_id, follow_range, exit_condition)

        def FollowPathAndDialog(self, path: List[Tuple[float, float]], dialog_id: int, step_name: str="") -> None:
            self.FollowPath(path, step_name=step_name)
            last_point = path[-1]
            self.parent.Dialogs.DialogAt(*last_point, dialog_id, step_name=step_name+"_DIALOGAT")

        def MoveAndDialog(self, x: float, y: float, dialog_id: int, step_name: str="") -> None:
            self.MoveTo(x, y, step_name=step_name)
            self.parent.Dialogs.DialogAt(x, y, dialog_id, step_name=step_name+"_DIALOGAT")

        def MoveAndInteractNPC(self, x: float, y: float, step_name: str="") -> None:
            self.MoveTo(x, y, step_name=step_name)
            self.parent.Interact.InteractNPCAt(x, y, step_name=step_name+"_INTERACT")

        def MoveAndInteractGadget(self, x: float, y: float, step_name: str="") -> None:
            self.MoveTo(x, y, step_name=step_name)
            self.parent.Interact.InteractGadgetAt(x, y, step_name=step_name+"_INTERACT")
            
        def MoveAndInteractItem(self, x: float, y: float, step_name: str="") -> None:
            self.MoveTo(x, y, step_name=step_name)
            self.parent.Interact.InteractItemAt(x, y, step_name=step_name+"_INTERACT")

        def MoveAndExitMap(self, x: float, y: float, target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> None:
            self.MoveTo(x, y, step_name=step_name)
            self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)

        def FollowPathAndExitMap(self, path: List[Tuple[float, float]], target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> None:
            self.FollowPath(path, step_name=step_name)
            self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)

    #region PROPERTIES
    class _PROPERTIES:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent

        def get(self, name: str, field: str = "active") -> Any:
            return self._resolve(name).get(field)

        def set(self, name: str, value: Any, field: str = "value") -> None:
            self._resolve(name).set(field, value)

        def is_active(self, name: str) -> bool:
            return self._resolve(name).is_active()

        def enable(self, name: str) -> None:
            self._resolve(name).enable()

        def disable(self, name: str) -> None:
            self._resolve(name).disable()

        def set_active(self, name: str, active: bool) -> None:
            self._resolve(name).set_active(active)

        def reset(self, name: str, field: str = "active") -> None:
            self._resolve(name).reset(field)

        def reset_all(self, name: str) -> None:
            self._resolve(name).reset_all()
            
        def direct_apply(self, name: str, field: str, value: Any) -> None:
            """
            Immediate, no-FSM write.
            Directly calls Property._apply(field, value).
            Use with care: this bypasses FSM AddState.
            """
            self._resolve(name)._apply(field, value)

        # --- Internal resolver ---
        def _resolve(self, name: str):
            # Check config_properties first
            if hasattr(self.parent.config.config_properties, name):
                return getattr(self.parent.config.config_properties, name)
            # Then upkeep
            if hasattr(self.parent.config.upkeep, name):
                return getattr(self.parent.config.upkeep, name)
            raise AttributeError(f"No property named {name!r}")
        
        def exists(self, name: str) -> bool:
            try:
                self._resolve(name)
                return True
            except AttributeError:
                return False

        # Introspection (useful for tooling/validation)
        def fields(self, name: str) -> Iterable[str]:
            prop = self._resolve(name)
            return list(prop._values.keys())  # read-only exposure

        def values(self, name: str) -> Dict[str, Any]:
            prop = self._resolve(name)
            return dict(prop._values)  # snapshot

        def defaults(self, name: str) -> Dict[str, Any]:
            prop = self._resolve(name)
            return dict(prop._defaults)  # snapshot

    #region PARTY
    class _PARTY:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent

        def LeaveParty(self):
            self.parent.helpers.leave_party()

        def FlagAllHeroes(self, x: float, y: float):
            self.parent.helpers.flag_all_heroes(x, y)

        def UnflagAllHeroes(self):
            self.parent.helpers.unflag_all_heroes()
            
        def Resign(self):
            self.parent.helpers.resign()


    #region STATES
    class _STATES:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent

        def AddFSMCustomYieldState(self, execute_fn, name: str) -> None:
            self.parent.config.FSM.AddYieldRoutineStep(name=name, coroutine_fn=execute_fn)

        def AddHeaderStep(self, step_name: str) -> None:
            self.parent.helpers.insert_header_step(step_name)
            
    #region UI
    class _UI:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent

        def CancelSkillRewardWindow(self):
            self.parent.helpers.cancel_skill_reward_window()
            
        def DrawPath(self, color:Color=Color(255, 255, 0, 255), use_occlusion: bool = False, snap_to_ground_segments: int = 1, floor_offset: float = 0) -> None:
            if self.parent.config.config_properties.draw_path.is_active():
                self.parent.helpers.draw_path(color, use_occlusion, snap_to_ground_segments, floor_offset)
                
        def SendChatMessage(self, channel: str, message: str):
            self.parent.helpers.send_chat_message(channel, message)

        def PrintMessageToConsole(self, source: str, message: str):
            self.parent.helpers.print_message_to_console(source, message)

    #region WAIT
    class _WAIT:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent

        def WasteTime(self, duration: int= 100) -> None:
            self.parent.helpers.waste_time(duration)

        def WasteTimeUntilConditionMet(self, condition: Callable[[], bool], duration: int=1000) -> None:
            self.parent.helpers.waste_time_until_condition_met(condition, duration)
            
        def WasteTimeUntilOOC(self) -> None:
            from .Routines import Routines
            from .Py4GWcorelib import Range
            wait_condition = lambda: not(Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot))
            self.parent.helpers.waste_time_until_condition_met(wait_condition)
            
        def ForMapLoad(self, target_map_id: int = 0, target_map_name: str = "") -> None:
            from Py4GWCoreLib import GLOBAL_CACHE
            if target_map_name:
                target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)

            self.parent.helpers.wait_for_map_load(target_map_id)
            
        def ForMapTransition(self, target_map_id: int = 0, target_map_name: str = "") -> None:
            """Waits until all action finishes in current map and game sends you to a new one"""
            from .Routines import Routines
            from .GlobalCache import GLOBAL_CACHE
            if target_map_name:
                target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)
                
            wait_condition = lambda: (
                Routines.Checks.Map.MapValid() and 
                GLOBAL_CACHE.Map.GetMapID() == target_map_id
            )
    
            self.WasteTimeUntilConditionMet(wait_condition, duration=3000)
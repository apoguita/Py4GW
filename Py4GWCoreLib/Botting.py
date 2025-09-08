  
from email.mime import message
from typing import Any, Tuple, Callable, List, Iterable, Dict, Optional


from .botting_src.helpers import BottingHelpers
from .botting_src.botconfig import BotConfig
from .botting_src.property import Property
from .Py4GWcorelib import Color, ActionQueueManager
from functools import wraps
import PyImGui

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

        self.helpers = BottingHelpers(self)
        #exposed Helpers
        self.States = BottingClass._STATES(self)
        self.UI = BottingClass._UI(self)
        self.Items = BottingClass._ITEMS(self)
        self.Dialogs = BottingClass._DIALOGS(self)
        self.Wait = BottingClass._WAIT(self)
        self.Move = BottingClass._MOVE(self)
        self.Map = BottingClass._MAP(self)
        self.Interact = BottingClass._INTERACT(self)
        self.Party = BottingClass._PARTY(self)
        self.Events = BottingClass._EVENTS(self)
        self.Properties = BottingClass._PROPERTIES(self)
        self.Target = BottingClass._TARGET(self)
        self.SkillBar = BottingClass._SKILLBAR(self)

    #region internal Helpers
    def _start_coroutines(self):
        # add all upkeep coroutines once
        H = self.helpers.Upkeepers

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

    def Stop(self):
        self.config.FSM.RemoveAllManagedCoroutines()
        self.config.FSM.stop()
        self.config.fsm_running = False

    def StartAtStep(self, step_name: str) -> None:
        self.Stop()
        self.config.fsm_running = True
        self.config.FSM.reset()
        self.config.FSM.jump_to_state_by_name(step_name)

    def Update(self):
        if self.config.fsm_running:
            self.config.state_description = "Running" if self.config.fsm_running else "Stopped"

        if not self.config.initialized:
            self.Routine()
            self.config.initialized = True
        if self.config.fsm_running:
            self._start_coroutines()
            self.config.FSM.update()
  
    #region DIALOGS
    class _DIALOGS:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers
            self.combat_status = False

        @_yield_step("DisableAutoCombat","AUTO_DISABLE_AUTO_COMBAT")
        def _disable_auto_combat(self):
            self.combat_status = self._config.upkeep.auto_combat.is_active()
            self._config.upkeep.auto_combat.set_now("active", False)
            ActionQueueManager().ResetAllQueues()
            yield

        @_yield_step("RestoreAutoCombat","AUTO_RESTORE_AUTO_COMBAT")
        def _restore_auto_combat(self):
            self._config.upkeep.auto_combat.set_now("active", self.combat_status)
            yield


        def AtXY(self, x: float, y: float, dialog:int, step_name: str="") -> None:
            if step_name == "":
                step_name = f"DialogAt_{self._config.get_counter('DIALOG_AT')}"

            #disable combat to prevent interference
            self._disable_auto_combat()

            self._helpers.Interact.with_npc_at_xy((x, y), dialog_id=dialog)

            #re-enable combat
            self._restore_auto_combat()

        def WithModel(self, model_id: int, dialog:int, step_name: str="") -> None:
            if step_name == "":
                step_name = f"DialogWithModel_{self._config.get_counter('DIALOG_AT')}"

            #disable combat to prevent interference
            self._disable_auto_combat()

            self._helpers.Interact.with_model(model_id=model_id, dialog_id=dialog)

            #re-enable combat
            self._restore_auto_combat()

    #region EVENTS
    class _EVENTS:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers

        def OnDeathCallback(self, callback: Callable[[], None]) -> None:
            self._config.events.on_death.set_callback(callback)

        def OnPartyWipeCallback(self, callback: Callable[[], None]) -> None:
            self._config.events.on_party_wipe.set_callback(callback)

        def OnPartyDefeatedCallback(self, callback: Callable[[], None]) -> None:
            self._config.events.on_party_defeated.set_callback(callback)

    #region INTERACT
    class _INTERACT:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers
            self.combat_status = False

        @_yield_step("DisableAutoCombat","AUTO_DISABLE_AUTO_COMBAT")
        def _disable_auto_combat(self):
            self.combat_status = self._config.upkeep.auto_combat.is_active()
            self._config.upkeep.auto_combat.set_now("active", False)
            ActionQueueManager().ResetAllQueues()
            yield

        @_yield_step("RestoreAutoCombat","AUTO_RESTORE_AUTO_COMBAT")
        def _restore_auto_combat(self):
            self._config.upkeep.auto_combat.set_now("active", self.combat_status)
            yield

        def WithNpcAtXY(self, x: float, y: float, step_name: str="") -> None:
            if step_name == "":
                step_name = f"InteractAt_{self._config.get_counter('INTERACT_AT')}"

            #disable combat to prevent interference
            self._disable_auto_combat()
            
            self._helpers.Interact.with_npc_at_xy((x, y))
            #re-enable combat
            self._restore_auto_combat()

        def WithGadgetAtXY(self, x: float, y: float, step_name: str="") -> None:
            if step_name == "":
                step_name = f"InteractGadgetAt_{self._config.get_counter('INTERACT_GADGET_AT')}"

            #disable combat to prevent interference
            self._disable_auto_combat()

            self._helpers.Interact.with_gadget_at_xy((x, y))

            #re-enable combat
            self._restore_auto_combat()

        def WithItemAtXY(self, x: float, y: float, step_name: str="") -> None:
            if step_name == "":
                step_name = f"InteractWithItem_{self._config.get_counter('INTERACT_WITH_ITEM')}"

            
            #disable combat to prevent interference
            self._disable_auto_combat()

            self._helpers.Interact.with_item_at_xy((x, y))
            #re-enable combat
            self._restore_auto_combat()

        def WithModel(self, model_id: int, step_name: str="") -> None:
            if step_name == "":
                step_name = f"InteractWithModel_{self._config.get_counter('INTERACT_WITH_MODEL')}"

            #disable combat to prevent interference
            self._disable_auto_combat()

            self._helpers.Interact.with_model(model_id=model_id)

            #re-enable combat
            self._restore_auto_combat()

    #region ITEMS
    class _ITEMS:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers
            self.Restock = BottingClass._ITEMS._RESTOCK(parent)

        def Craft(self, model_id: int, value: int, trade_items_models: list[int], quantity_list: list[int]):
            self._helpers.Items.craft(model_id, value, trade_items_models, quantity_list)
            
        def Withdraw(self, model_id:int, quantity:int):
            self._helpers.Items.withdraw(model_id, quantity)

        def Equip(self, model_id: int):
            self._helpers.Items.equip(model_id)

        def SpawnBonusItems(self):
            self._helpers.Items.spawn_bonus_items()
        
        class _RESTOCK:
            def __init__(self, parent: "BottingClass"):
                self.parent = parent
                self._config = parent.config
                self._helpers = parent.helpers

            def BirthdayCupcake(self):
                self._helpers.Restock.restock_birthday_cupcake()

            def Honeycomb(self):
                self._helpers.Restock.restock_honeycomb()


    #region MAP
    class _MAP:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers

        def Travel(self, target_map_id: int = 0, target_map_name: str = "") -> None:
            from .GlobalCache import GLOBAL_CACHE
            if target_map_name:
                target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)
                
            current_map_id = GLOBAL_CACHE.Map.GetMapID()
            if current_map_id == target_map_id:
                return

            self._helpers.Map.travel(target_map_id)
            self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)
            
        def EnterChallenge(self, delay:int= 4500, target_map_id: int = 0, target_map_name: str = "") -> None:
            self._helpers.Map.enter_challenge(wait_for=delay)
            self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)

        def TravelGH(self):
            self._helpers.Map.travel_to_gh(wait_time=8000)
            
        def LeaveGH(self):
            self._helpers.Map.leave_gh(wait_time=8000)


    #region MOVE
    class _MOVE:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers
            
        def XY(self, x:float, y:float, step_name: str=""):
            """Uses autopath to move to (x, y)"""
            if step_name == "":
                step_name = f"MoveTo_{self._config.get_counter('MOVE_TO')}"

            self._helpers.Move.get_path_to(x, y)
            self._helpers.Move.follow_path()
            
        def XYAndDialog(self, x: float, y: float, dialog_id: int, step_name: str="") -> None:
            self.XY(x, y, step_name=step_name)
            self.parent.Dialogs.AtXY(x, y, dialog_id, step_name=step_name+"_DIALOGAT")

        def XYAndInteractNPC(self, x: float, y: float, step_name: str="") -> None:
            self.XY(x, y, step_name=step_name)
            self.parent.Interact.WithNpcAtXY(x, y, step_name=step_name+"_INTERACT")

        def XYAndInteractGadget(self, x: float, y: float, step_name: str="") -> None:
            self.XY(x, y, step_name=step_name)
            self.parent.Interact.WithGadgetAtXY(x, y, step_name=step_name+"_INTERACT")
            
        def XYAndInteractItem(self, x: float, y: float, step_name: str="") -> None:
            self.XY(x, y, step_name=step_name)
            self.parent.Interact.WithItemAtXY(x, y, step_name=step_name+"_INTERACT")

        def XYAndExitMap(self, x: float, y: float, target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> None:
            self.XY(x, y, step_name=step_name)
            self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)


        def FollowPath(self, path: List[Tuple[float, float]], step_name: str="") -> None:
            """ follow a predefined path of (x, y) points.
            """
            if step_name == "":
                step_name = f"FollowPath_{self._config.get_counter('FOLLOW_PATH')}"

            self._helpers.Move.set_path_to(path)
            self._helpers.Move.follow_path()
            
        def FollowPathAndDialog(self, path: List[Tuple[float, float]], dialog_id: int, step_name: str="") -> None:
            self.FollowPath(path, step_name=step_name)
            last_point = path[-1]
            self.parent.Dialogs.AtXY(*last_point, dialog_id, step_name=step_name+"_DIALOGAT")
            
        def FollowPathAndExitMap(self, path: List[Tuple[float, float]], target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> None:
            self.FollowPath(path, step_name=step_name)
            self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)

        def FollowAutoPath(self, points: List[Tuple[float, float]], step_name: str = "") -> None:
            """
            For each (x, y) target point, compute an autopath and follow it.
            Input format matches FollowPath, but each point is autpathed independently.
            """
            if step_name == "":
                step_name = f"FollowAutoPath_{self._config.get_counter('FOLLOW_AUTOPATH')}"

            for x, y in points:
                self._helpers.Move.get_path_to(x, y)   # autopath to this target
                self._helpers.Move.follow_path()       # then execute the path

        def FollowModel(self, model_id: int, follow_range: float, exit_condition: Optional[Callable[[], bool]] = lambda:False) -> None:
            self._helpers.Move.follow_model(model_id, follow_range, exit_condition)

        

    #region PROPERTIES
    class _PROPERTIES:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers

        def Get(self, name: str, field: str = "active") -> Any:
            return self._resolve(name).get(field)

        def Set(self, name: str, value: Any, field: str = "value") -> None:
            self._resolve(name).set(field, value)

        def IsActive(self, name: str) -> bool:
            return self._resolve(name).is_active()

        def Enable(self, name: str) -> None:
            self._resolve(name).enable()

        def Disable(self, name: str) -> None:
            self._resolve(name).disable()

        def SetActive(self, name: str, active: bool) -> None:
            self._resolve(name).set_active(active)

        def ResetTodefault(self, name: str, field: str = "active") -> None:
            self._resolve(name).reset(field)

        def ResetAll(self, name: str) -> None:
            self._resolve(name).reset_all()
            
        def ApplyNow(self, name: str, field: str, value: Any) -> None:
            """
            Immediate, no-FSM write.
            Directly calls Property._apply(field, value).
            Use with care: this bypasses FSM AddState.
            """
            self._resolve(name)._apply(field, value)

        # --- Internal resolver ---
        def _resolve(self, name: str):
            # Check config_properties first
            if hasattr(self._config.config_properties, name):
                return getattr(self._config.config_properties, name)
            # Then upkeep
            if hasattr(self._config.upkeep, name):
                return getattr(self._config.upkeep, name)
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
            self._config = parent.config
            self._helpers = parent.helpers

        def LeaveParty(self):
            self._helpers.Party.leave_party()

        def FlagAllHeroes(self, x: float, y: float):
            self._helpers.Party.flag_all_heroes(x, y)

        def UnflagAllHeroes(self):
            self._helpers.Party.unflag_all_heroes()

        def Resign(self):
            self._helpers.Party.resign()

        def AddHenchman(self, henchman_id: int):
            self._helpers.Party.add_henchman(henchman_id)
            
        def AddHero(self, hero_id: int):
            self._helpers.Party.add_hero(hero_id)

        def InvitePlayer(self, player_name: str):
            self._helpers.Party.invite_player(player_name)

        def KickHenchman(self, henchman_id: int):
            self._helpers.Party.kick_henchman(henchman_id)

        def KickHero(self, hero_id: int):
            self._helpers.Party.kick_hero(hero_id)

        def KickPlayer(self, player_name: str):
            self._helpers.Party.kick_player(player_name)
    #region SKILLBAR
    class _SKILLBAR:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers
            
        def LoadSkillBar(self, skill_template: str):
            self._helpers.Skills.load_skillbar(skill_template)

        def UseSkill(self, skill_id:int):
            self._helpers.Skills.cast_skill_id(skill_id)

        def UseSkillSlot(self, slot_index:int):
            self._helpers.Skills.cast_skill_slot(slot_index)

    #region STATES
    class _STATES:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers

        def AddCustomState(self, execute_fn, name: str) -> None:
            self._config.FSM.AddYieldRoutineStep(name=name, coroutine_fn=execute_fn)

        def AddHeader(self, step_name: str) -> None:
            self._helpers.States.insert_header_step(step_name)
            
    #region TARGET
    class _TARGET:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers
            
        def Model(self, model_id:int):
            self._helpers.Target.model(model_id)

    #region WAIT
    class _WAIT:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers

        def ForTime(self, duration: int= 100) -> None:
            self._helpers.Wait.for_time(duration)

        def UntilCondition(self, condition: Callable[[], bool], duration: int=1000) -> None:
            self._helpers.Wait.until_condition(condition, duration)

        def UntilOutOfCombat(self) -> None:
            from .Routines import Routines
            from .Py4GWcorelib import Range
            wait_condition = lambda: not(Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot))
            self._helpers.Wait.until_condition(wait_condition)
            
        def ForMapLoad(self, target_map_id: int = 0, target_map_name: str = "") -> None:
            from Py4GWCoreLib import GLOBAL_CACHE
            if target_map_name:
                target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)

            self._helpers.Wait.for_map_load(target_map_id)
            
        def ForMapToChange(self, target_map_id: int = 0, target_map_name: str = "") -> None:
            """Waits until all action finishes in current map and game sends you to a new one"""
            from .Routines import Routines
            from .GlobalCache import GLOBAL_CACHE
            if target_map_name:
                target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)
                
            wait_condition = lambda: (
                Routines.Checks.Map.MapValid() and 
                GLOBAL_CACHE.Map.GetMapID() == target_map_id
            )
    
            self.UntilCondition(wait_condition, duration=3000)
            
    #region UI
    class _UI:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers
            self.draw_texture_fn: Optional[Callable[[], None]] = None
            self.draw_config_fn: Optional[Callable[[], None]] = None
            self.draw_help_fn: Optional[Callable[[], None]] = None
            
            self._FSM_SELECTED_NAME_ORIG: str | None = None   # selection persists across frames
            self._FSM_FILTER_START: int = 0
            self._FSM_FILTER_END: int = 0

        def CancelSkillRewardWindow(self):
            self._helpers.UI.cancel_skill_reward_window()
            
        def _draw_path(self, color:Color=Color(255, 255, 0, 255), use_occlusion: bool = False, snap_to_ground_segments: int = 1, floor_offset: float = 0) -> None:
            from .DXOverlay import DXOverlay
            path = self._config.path_to_draw

            for i in range(len(path) - 1):
                x1, y1 = path[i]
                x2, y2 = path[i + 1]
                z1 = DXOverlay.FindZ(x1, y1)
                z2 = DXOverlay.FindZ(x2, y2)
                DXOverlay().DrawLine3D(x1, y1, z1, x2, y2, z2, color.to_color(), use_occlusion, snap_to_ground_segments, floor_offset)

            
        def DrawPath(self, color:Color=Color(255, 255, 0, 255), use_occlusion: bool = False, snap_to_ground_segments: int = 1, floor_offset: float = 0) -> None:
            if self._config.config_properties.draw_path.is_active():
                self._draw_path(color, use_occlusion, snap_to_ground_segments, floor_offset)

        def SendChatMessage(self, channel: str, message: str):
            self._helpers.UI.send_chat_message(channel, message)

        def PrintMessageToConsole(self, source: str, message: str):
            self._helpers.UI.print_message_to_console(source, message)
            
        def _find_current_header_step(self):
            import re

            steps = self._config.FSM.get_state_names()
            total_steps = len(steps)

            # Raw current index as reported by the FSM (may be None or out-of-bounds at "end")
            raw_current = self._config.FSM.get_current_state_number()

            # Normalize and detect "finished"
            if total_steps == 0:
                # No steps at all
                current_idx = -1
                finished = True
                step_name = None
                search_from = -1
            else:
                if raw_current is None:
                    finished = True
                    current_idx = total_steps - 1           # clamp to last valid index for display
                elif raw_current < 0:
                    finished = False
                    current_idx = 0                         # clamp up
                elif raw_current >= total_steps:
                    finished = True
                    current_idx = total_steps - 1           # clamp down
                else:
                    finished = False
                    current_idx = raw_current

                step_name = None if finished else self._config.FSM.get_state_name_by_number(current_idx)
                search_from = current_idx if current_idx >= 0 else -1

            # Find nearest preceding [H] header up to the display index (or last if empty/finished)
            header_for_current = None
            current_header_step = -1
            if total_steps > 0 and search_from >= 0:
                for i in range(search_from, -1, -1):
                    name = steps[i]
                    if name.startswith("[H]"):
                        # strip "[H]" and trailing index suffixes "_[n]" or "_n"
                        name_clean = re.sub(r'^\[H\]\s*', '', name)
                        name_clean = re.sub(r'_(?:\[\d+\]|\d+)$', '', name_clean)
                        header_for_current = name_clean
                        current_header_step = i
                        break

            return current_header_step, header_for_current, current_idx, total_steps, step_name, finished

        
        def _draw_texture(self, texture_path:str, size:Tuple[float,float]=(96.0,96.0), tint:Color=Color(255,255,255,255), border_col:Color=Color(0,0,0,0)):
            from .ImGui import ImGui
            from .enums import ItemModelTextureMap
            if self.draw_texture_fn is not None:
                self.draw_texture_fn()
                return
            
            if not texture_path:
                texture_path = ItemModelTextureMap.get(0, "")
            
            ImGui.DrawTextureExtended(texture_path=texture_path, size=size,
                                  uv0=(0.0, 0.0),   uv1=(1.0, 1.0),
                                  tint=tint.to_tuple(), border_color=border_col.to_tuple())
            
        def override_draw_texture(self, draw_fn: Optional[Callable[[], None]] = None) -> None:
            """
            Override the texture drawing function.
            If draw_fn is None, resets to default drawing behavior.
            """
            self.draw_texture_fn = draw_fn
            
        def override_draw_config(self, draw_fn: Optional[Callable[[], None]] = None) -> None:
            """
            Override the config drawing function.
            If draw_fn is None, resets to default drawing behavior.
            """
            self.draw_config_fn = draw_fn
            
        def override_draw_help(self, draw_fn: Optional[Callable[[], None]] = None) -> None:
            """
            Override the help drawing function.
            If draw_fn is None, resets to default drawing behavior.
            """
            self.draw_help_fn = draw_fn
            
        def _draw_fsm_jump_button(self) -> None:
            if self._FSM_SELECTED_NAME_ORIG:
                sel_num = self._config.FSM.get_state_number_by_name(self._FSM_SELECTED_NAME_ORIG)
                sel_str = f"{sel_num-1}" if isinstance(sel_num, int) else "N/A"
                PyImGui.text(f"Selected: {self._FSM_SELECTED_NAME_ORIG}  (#{sel_str})")
            else:
                PyImGui.text("Selected: (none)")

            if PyImGui.button("Jump to Selected") and self._FSM_SELECTED_NAME_ORIG:
                self._config.fsm_running = True
                self._config.FSM.reset()
                self._config.FSM.jump_to_state_by_name(self._FSM_SELECTED_NAME_ORIG)

                
        def _draw_step_range_inputs(self):
            steps = self._config.FSM.get_state_names()
            if not steps:
                self._FSM_FILTER_START = 0
                self._FSM_FILTER_END = 0
                PyImGui.text("No steps.")
                return

            last_index = len(steps) - 1
            if self._FSM_FILTER_END == 0 and last_index > 0:
                self._FSM_FILTER_END = last_index

            self._FSM_FILTER_START = PyImGui.input_int("Start Step", self._FSM_FILTER_START)
            self._FSM_FILTER_END   = PyImGui.input_int("End Step",   self._FSM_FILTER_END)

            self._FSM_FILTER_START = max(0, min(self._FSM_FILTER_START, last_index))
            self._FSM_FILTER_END   = max(0, min(self._FSM_FILTER_END,   last_index))
            if self._FSM_FILTER_START > self._FSM_FILTER_END:
                self._FSM_FILTER_START, self._FSM_FILTER_END = self._FSM_FILTER_END, self._FSM_FILTER_START

            PyImGui.same_line(0,-1)
            if PyImGui.button("Reset Range"):
                self._FSM_FILTER_START = 0
                self._FSM_FILTER_END   = last_index

            PyImGui.text(f"Showing steps [{self._FSM_FILTER_START} … {self._FSM_FILTER_END}] of 0…{last_index}")



        def _get_fsm_sections(self):
            """
            -> List[dict] with:
            header_idx:int, header_name_orig:str, header_name_clean:str,
            children: List[Tuple[int, str]]  # (step_index, original_name)
            Groups steps under the nearest preceding [H] header.
            """
            def _clean_header(name: str) -> str:
                import re
                if name.startswith("[H]"):
                    name = re.sub(r'^\[H\]\s*', '', name)
                    name = re.sub(r'_(?:\[\d+\]|\d+)$', '', name)
                return name

            steps = self._config.FSM.get_state_names()
            sections = []
            current = None

            for i, name in enumerate(steps):
                if name.startswith("[H]"):
                    if current is not None:
                        sections.append(current)
                    current = {
                        "header_idx": i,
                        "header_name_orig": name,
                        "header_name_clean": _clean_header(name),
                        "children": []
                    }
                else:
                    if current is None:
                        current = {
                            "header_idx": -1,
                            "header_name_orig": "[H] (No Header)",
                            "header_name_clean": "(No Header)",
                            "children": []
                        }
                    current["children"].append((i, name))

            if current is not None:
                sections.append(current)
            return sections
        
        def draw_fsm_tree_selector_ranged(self, child_size: Tuple[float, float]=(350, 250)) -> str | None:
            """
            Scrollable child window with a header-grouped tree,
            filtered to only show steps in [_FSM_FILTER_START, _FSM_FILTER_END].
            Returns selected ORIGINAL name or None.
            """

            # filter inputs
            self._draw_step_range_inputs()
            PyImGui.separator()

            sections = self._get_fsm_sections()
            NOFLAG = PyImGui.SelectableFlags.NoFlag
            SIZE: Tuple[float, float] = (0.0, 0.0)

            PyImGui.begin_child("fsm_tree_ranged_child", child_size, True, 0)

            any_drawn = False
            for sec in sections:
                # header/children within range?
                header_in_range = (sec["header_idx"] >= 0 and self._FSM_FILTER_START <= sec["header_idx"] <= self._FSM_FILTER_END)
                children_in_range = [(idx, nm) for (idx, nm) in sec["children"] if self._FSM_FILTER_START <= idx <= self._FSM_FILTER_END]

                if not header_in_range and not children_in_range:
                    continue

                any_drawn = True
                header_idx_label = sec["header_idx"] if sec["header_idx"] >= 0 else "—"
                parent_label = f"[{header_idx_label}] {sec['header_name_clean']}##hdr_{header_idx_label}"

                if PyImGui.tree_node(parent_label):
                    # header selectable
                    header_label = f"(Header) {sec['header_name_clean']}##sel_hdr_{header_idx_label}"
                    is_header_sel = (self._FSM_SELECTED_NAME_ORIG == sec["header_name_orig"])
                    if PyImGui.selectable(header_label, is_header_sel, NOFLAG, SIZE):
                        self._FSM_SELECTED_NAME_ORIG = sec["header_name_orig"]

                    # children (in range)
                    for idx, name_orig in children_in_range:
                        label = f"[{idx}] {name_orig}##sel_step_{idx}"
                        is_sel = (self._FSM_SELECTED_NAME_ORIG == name_orig)
                        if PyImGui.selectable(label, is_sel, NOFLAG, SIZE):
                            self._FSM_SELECTED_NAME_ORIG = name_orig

                    PyImGui.tree_pop()

            if not any_drawn:
                PyImGui.text("No steps in selected range.")

            PyImGui.end_child()
            return self._FSM_SELECTED_NAME_ORIG

        def _draw_main_child (self, main_child_dimensions: Tuple[int, int]  = (350, 275), 
                              icon_path:str = "",
                              iconwidth: int = 96) -> None:
            from .ImGui import ImGui
            from .IconsFontAwesome5 import IconsFontAwesome5
            from .Py4GWcorelib import ConsoleLog, Console
            from .GlobalCache import GLOBAL_CACHE
            
            current_header_step, header_for_current , current_step, total_steps, step_name, finished = self._find_current_header_step()
            if PyImGui.begin_table("bot_header_table", 2, PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersOuterH):
                PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, iconwidth)
                PyImGui.table_setup_column("titles", PyImGui.TableColumnFlags.WidthFixed, main_child_dimensions[0] - iconwidth)
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                self._draw_texture(texture_path=icon_path, size=(iconwidth, iconwidth))
                PyImGui.table_set_column_index(1)
                
                PyImGui.dummy(0,3)
                ImGui.push_font("Regular", 22)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Color(255, 255, 0, 255).to_tuple_normalized())
                PyImGui.text(f"{self._config.bot_name}")
                PyImGui.pop_style_color(1)
                ImGui.pop_font()
        
                ImGui.push_font("Bold", 18)
                PyImGui.text(f"[{max(current_header_step, 0)}] {header_for_current or 'Not started'}")
                ImGui.pop_font()
                if total_steps <= 0:
                    PyImGui.text("Step: —/— - (No steps)")
                else:
                    # When finished we show the last index and mark it as Finished
                    if finished:
                        PyImGui.text(f"Step: {total_steps-1}/{total_steps-1} - (Finished)")
                    else:
                        PyImGui.text(f"Step: {current_step}/{max(total_steps-1, 0)} - {step_name or '(…?)'}")

                # Status line
                if not self._config.fsm_running and finished:
                    self._config.state_description = "Finished"
                PyImGui.text(f"Status: {self._config.state_description}")

                PyImGui.end_table()

            
            # --- Single toggle button: Play ↔ Stop ---
            icon = IconsFontAwesome5.ICON_STOP_CIRCLE if self._config.fsm_running else IconsFontAwesome5.ICON_PLAY_CIRCLE
            legend = "  Stop" if self._config.fsm_running else "  Start"
            if PyImGui.button(icon + legend + "##BotToggle"):
                if self._config.fsm_running:
                    # Stop
                    self._config.fsm_running = False
                    ConsoleLog(self._config.bot_name, "Script stopped", Console.MessageType.Info)
                    self._config.state_description = "Idle"
                    self._config.FSM.stop()
                    GLOBAL_CACHE.Coroutines.clear()
                else:
                    # Start
                    self._config.fsm_running = True
                    ConsoleLog(self._config.bot_name, "Script started", Console.MessageType.Info)
                    self._config.state_description = "Running"
                    self._config.FSM.restart()


                
            if total_steps > 1:
                fraction = (total_steps - 1) and (current_step / float(total_steps - 1)) or 0.0
            else:
                fraction = 1.0 if finished and total_steps == 1 else 0.0
            if finished and total_steps > 0:
                fraction = 1.0
            fraction = max(0.0, min(1.0, fraction))

                
            PyImGui.text("Overall Progress")
            PyImGui.push_item_width(main_child_dimensions[0] - 10)
            PyImGui.progress_bar(fraction, (main_child_dimensions[0] - 10), 0, f"{fraction * 100:.2f}%")
            PyImGui.pop_item_width()
            
            PyImGui.separator()
            PyImGui.text("Step Progress")
            PyImGui.push_item_width(main_child_dimensions[0] - 10)
            PyImGui.progress_bar(self._config.state_percentage, (main_child_dimensions[0] - 10), 0, f"{self._config.state_percentage * 100:.2f}%")
            PyImGui.pop_item_width()

        def _draw_settings_child(self):
            if self.draw_config_fn:
                self.draw_config_fn()
                return 
            
            PyImGui.text("Bot Settings")
            PyImGui.separator()
            PyImGui.text("override this function to provide custom settings")
            PyImGui.text("use bot.Override_settings to set a custom settings function")
            PyImGui.separator()

        def _draw_help_child(self):
            if self.draw_help_fn:
                self.draw_help_fn()
                return
            
            PyImGui.text("Bot Help")
            PyImGui.separator()
            PyImGui.text("override this function to provide custom help info")
            PyImGui.text("use bot.Override_help to set a custom help function")
            PyImGui.separator()
          
        def draw_configure_window(self):
            from .ImGui import ImGui
            from .IconsFontAwesome5 import IconsFontAwesome5

            if PyImGui.begin("Bot Configuration", PyImGui.WindowFlags.AlwaysAutoResize):
                self._draw_settings_child()    
                PyImGui.end()  
            
        def draw_window(self, main_child_dimensions: Tuple[int, int]  = (350, 275), icon_path:str = "",iconwidth: int = 96):

            if PyImGui.begin(self._config.bot_name, PyImGui.WindowFlags.AlwaysAutoResize):
                if PyImGui.begin_tab_bar(self._config.bot_name + "_tabs"):
                    if PyImGui.begin_tab_item("Main"):
                        if PyImGui.begin_child(f"{self._config.bot_name} - Main", main_child_dimensions, True, PyImGui.WindowFlags.NoFlag):
                            self._draw_main_child(main_child_dimensions, icon_path, iconwidth)
                            PyImGui.end_child()
                        PyImGui.end_tab_item()
                    
                    if PyImGui.begin_tab_item("Navigation"):        
                        PyImGui.text("Jump to step (filtered by step index):")
                        self._draw_fsm_jump_button()
                        PyImGui.separator()
                        selected_name = self.draw_fsm_tree_selector_ranged(child_size=main_child_dimensions)
                        PyImGui.end_tab_item()

                    if PyImGui.begin_tab_item("Settings"):
                        self._draw_settings_child()
                        PyImGui.end_tab_item()
                        
                    if PyImGui.begin_tab_item("Help"):
                        self._draw_help_child()
                        PyImGui.end_tab_item()

                    if PyImGui.begin_tab_item("Debug"):
                        if PyImGui.collapsing_header("Map Navigation"):
                            self._config.config_properties.draw_path.set_now("active",PyImGui.checkbox("Draw Path", self._config.config_properties.draw_path.is_active()))
                            self._config.config_properties.use_occlusion.set_now("active",PyImGui.checkbox("Use Occlusion", self._config.config_properties.use_occlusion.is_active()))
                            self._config.config_properties.snap_to_ground_segments.set_now("value", PyImGui.slider_int("Snap to Ground Segments", self._config.config_properties.snap_to_ground_segments.get("value"), 1, 32))
                            self._config.config_properties.floor_offset.set_now("value", PyImGui.slider_float("Floor Offset", self._config.config_properties.floor_offset.get("value"), -10.0, 50.0))

                        if PyImGui.collapsing_header("Properties"):
                            def debug_text(self, prop_name:str, key:str):
                                from .Py4GWcorelib import Utils
                                value = self.parent.Properties.get(prop_name, key)
                                if isinstance(value, bool):
                                    color = Utils.TrueFalseColor(value)
                                else:
                                    color = (255, 255, 255, 255)
                                PyImGui.text_colored(f"{prop_name} - {key}: {value}", color)

                            debug_text(self, "log_actions", "active")
                            debug_text(self, "halt_on_death", "active")
                            debug_text(self, "pause_on_danger", "active")
                            debug_text(self, "movement_timeout", "value")
                            debug_text(self, "movement_tolerance", "value")
                            debug_text(self, "draw_path", "active")
                            debug_text(self, "use_occlusion", "active")
                            debug_text(self, "snap_to_ground", "active")
                            debug_text(self, "snap_to_ground_segments", "value")
                            debug_text(self, "floor_offset", "value")
                            debug_text(self, "follow_path_color", "value")
                            PyImGui.separator()
                            debug_text(self, "follow_path_succeeded", "value")
                            debug_text(self, "dialog_at_succeeded", "value")

                        
                        if PyImGui.collapsing_header("UpkeepData"):
                            def render_upkeep_data(parent):
                                # ---- your exact accessor, unchanged ----
                                def debug_text(self, prop_name: str, key: str):
                                    from .Py4GWcorelib import Utils
                                    value = self.parent.Properties.get(prop_name, key)
                                    if isinstance(value, bool):
                                        color = Utils.TrueFalseColor(value)
                                    else:
                                        color = (255, 255, 255, 255)
                                    PyImGui.text_colored(f"{prop_name} - {key}: {value}", color)

                                # Most items: ("active", "restock_quantity")
                                DEFAULT_KEYS = ("active", "restock_quantity")

                                # Compact spec: either "prop" (uses DEFAULT_KEYS) or ("prop", (<custom keys>))
                                ITEMS = [
                                    ("alcohol", ("active", "target_drunk_level", "disable_visual")),
                                    "armor_of_salvation",
                                    ("auto_combat", ("active",)),
                                    "birthday_cupcake",
                                    "blue_rock_candy",
                                    "bowl_of_skalefin_soup",
                                    "candy_apple",
                                    "candy_corn",
                                    ("city_speed", ("active",)),
                                    "drake_kabob",
                                    "essence_of_celerity",
                                    "four_leaf_clover",
                                    "golden_egg",
                                    "grail_of_might",
                                    "green_rock_candy",
                                    "honeycomb",
                                    ("imp", ("active",)),
                                    ("morale", ("active", "target_morale")),
                                    "pahnai_salad",
                                    "red_rock_candy",
                                    "slice_of_pumpkin_pie",
                                    "war_supplies",
                                ]

                                if not PyImGui.collapsing_header("UpkeepData"):
                                    return

                                for item in ITEMS:
                                    if isinstance(item, str):
                                        prop, keys = item, DEFAULT_KEYS
                                    else:
                                        prop, keys = item

                                    if PyImGui.tree_node(prop):
                                        PyImGui.push_id(prop)  # avoid ID collisions for the same key labels
                                        for key in keys:
                                            debug_text(parent, prop, key)
                                        PyImGui.pop_id()
                                        PyImGui.tree_pop()

                            render_upkeep_data(self)

                        PyImGui.end_tab_item()
                    PyImGui.end_tab_bar()

            PyImGui.end()
            self.parent.UI.DrawPath(
                self._config.config_properties.follow_path_color.get("value"), 
                self._config.config_properties.use_occlusion.is_active(), 
                self._config.config_properties.snap_to_ground_segments.get("value"), 
                self._config.config_properties.floor_offset.get("value"))




from PyEffects import PyEffects
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, AutoPathing, Py4GW, FSM, ConsoleLog, Color, DXOverlay,
                          UIManager,ModelID, Utils, SkillManager, Map, ConsoleLog
                         )
from typing import List, Tuple, Any, Generator, Callable
import PyImGui

#from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
from functools import wraps
import time
import re

MODULE_NAME = "sequential bot test"


from collections import defaultdict
from typing import Dict, Iterable, Optional, Final

STEP_NAMES: Final[tuple[str, ...]] = (
    "ALCOHOL_COUNTER",
    "AUTO_COMBAT",
    "CANCEL_SKILL_REWARD_WINDOW",
    "CELERITY_COUNTER",
    "CITY_SPEED_COUNTER",
    "CONSETS_COUNTER",
    "CRAFT_ITEM",
    "CUPCAKES_COUNTER",
    "CUSTOM_STEP",
    "DIALOG_AT",
    "DP_REMOVAL_COUNTER",
    "ENTER_CHALLENGE",
    "EQUIP_ITEM",
    "FLAG_ALL_HEROES",
    "FOLLOW_PATH",
    "GET_PATH_TO",
    "GRAIL_COUNTER",
    "HALT_ON_DEATH",
    "HEADER_COUNTER",
    "HONEYCOMBS_COUNTER",
    "IMP_COUNTER",
    "LEAVE_PARTY",
    "LOG_ACTIONS",
    "MORALE_COUNTER",
    "MOVE_TO",
    "MOVEMENT_TIMEOUT",
    "MOVEMENT_TOLERANCE",
    "ON_FOLLOW_PATH_FAILED",
    "PAUSE_ON_DANGER",
    "PROPERTY",
    "SALVATION_COUNTER",
    "SET_PATH_TO",
    "SPAWN_BONUS",
    "TRAVEL",
    "UPDATE_PLAYER_DATA",
    "WAIT_FOR_MAP_LOAD",
    "WASTE_TIME",
    "WITHDRAW_ITEMS",
    "UNKNOWN"
)
ALLOWED_STEPS: Final[frozenset[str]] = frozenset(STEP_NAMES)

class StepNameCounters:
    def __init__(self, seed: Dict[str, int] | None = None,
                 allowed: Iterable[str] = ALLOWED_STEPS) -> None:
        self._allowed = frozenset(s.upper() for s in allowed)
        self._counts: defaultdict[str, int] = defaultdict(int)
        if seed:
            for k, v in seed.items():
                ku = k.upper()
                if ku in self._allowed:
                    self._counts[ku] = int(v)

    def _canon(self, name: str) -> str:
        return name.upper()

    def _key_or_none(self, name: str) -> str:
        k = self._canon(name)
        return k if k in self._allowed else "UNKNOWN"

    def next_index(self, name: str) -> int:
        key = self._key_or_none(name)
        self._counts[key] += 1
        return self._counts[key]

    def get_index(self, name: str) -> int:
        return self._counts[self._key_or_none(name)]

    def reset_index(self, name: str, to: int = 0) -> None:
        self._counts[self._key_or_none(name)] = to

    def set_index(self, name: str, to: int) -> None:
        self._counts[self._key_or_none(name)] = to

    def clear_all(self) -> None:
        self._counts.clear()


class Property:
    """
    A flexible property system for BotConfig.
    - Always has an `active` flag.
    - Can have any number of extra fields (with defaults).
    - Changes are scheduled through the FSM of the parent BotConfig.
    """

    def __init__(self, parent: "BotConfig", name: str,
                 active: bool = True,
                 extra_fields: Optional[Dict[str, Any]] = None):
        self.parent = parent
        self.name = name

        # store defaults and current values
        self._defaults: Dict[str, Any] = {"active": active}
        self._values: Dict[str, Any] = {"active": active}

        if extra_fields:
            for k, v in extra_fields.items():
                self._defaults[k] = v
                self._values[k] = v

    # ---- getters ----
    def is_active(self) -> bool:
        return bool(self._values["active"])

    def get(self, field: str = "active") -> Any:
        return self._values[field]

    # ---- apply immediately (internal) ----
    def _apply(self, field: str, value: Any) -> None:
        self._values[field] = value

    # ---- schedule changes through FSM ----
    def set(self, field: str, value: Any) -> None:
        step_name = f"{self.name}_{field}_{self.parent.get_counter('PROPERTY')}"
        self.parent.FSM.AddState(
            name=step_name,
            execute_fn=lambda f=field, v=value: self._apply(f, v),
        )

    def enable(self) -> None:
        self.set("active", True)

    def disable(self) -> None:
        self.set("active", False)

    def toggle(self) -> None:
        self.set("active", not self.is_active())

    def set_active(self, value: bool) -> None:
        self._apply("active", value)

    # ---- reset ----
    def reset(self, field: str = "active") -> None:
        step_name = f"{self.name}_{field}_RESET_{self.parent.get_counter('PROPERTY')}"
        default_value = self._defaults[field]
        self.parent.FSM.AddState(
            name=step_name,
            execute_fn=lambda f=field, v=default_value: self._apply(f, v),
        )

    def reset_all(self) -> None:
        for f in self._values.keys():
            self.reset(f)

    # ---- immediate init (bypass FSM, e.g., bootstrapping) ----
    def init_now(self, **kwargs: Any) -> None:
        for f, v in kwargs.items():
            if f not in self._values:
                raise KeyError(f"Unknown field '{f}' in Property {self.name}")
            self._apply(f, v)

    # ---- representation ----
    def __repr__(self) -> str:
        return f"Property({self.name}, {self._values})"
    

class LiveData:
    def __init__(self, parent: "BotConfig"):
        self.parent = parent

        # Player-related live data
        self.Player = Property(parent, "player",
                               extra_fields={
                                   "primary_profession": "None",
                                   "secondary_profession": "None",
                                   "level": 1,
                               })

        # Map-related live data
        self.Map = Property(parent, "map",
                            extra_fields={
                                "current_map_id": 0,
                                "max_party_size": 0
                            })

    def update(self):
        # update values directly (bypasses FSM scheduling)
        primary, secondary = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        self.Player._apply("primary_profession", primary)
        self.Player._apply("secondary_profession", secondary)
        self.Player._apply("level", GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID()))

        self.Map._apply("current_map_id", GLOBAL_CACHE.Map.GetMapID())
        self.Map._apply("max_party_size", GLOBAL_CACHE.Map.GetMaxPartySize())


class ConfigProperties:
    def __init__(self, parent: "BotConfig"):
        self.parent = parent

        # simple properties with only one field
        self.log_actions = Property(parent, "log_actions", active=False)
        self.halt_on_death = Property(parent, "halt_on_death", active=True)
        self.pause_on_danger = Property(parent, "pause_on_danger", active=False)
        self.movement_timeout = Property(parent, "movement_timeout", extra_fields={"value": 15000})
        self.movement_tolerance = Property(parent, "movement_tolerance", extra_fields={"value": 150})
        self.draw_path = Property(parent, "draw_path", active=True)
        self.follow_path_succeeded = Property(parent, "follow_path_succeeded", extra_fields={"value": False})   
        self.dialog_at_succeeded = Property(parent, "dialog_at_succeeded", extra_fields={"value": False})

        # more properties can be added here

class UpkeepData:
    def __init__(self, parent: "BotConfig"):
        self.parent = parent

        self.alcohol = Property(parent,"alcohol", active=False,
            extra_fields={
                "target_drunk_level": 2,        # Drunk level to maintain
                "disable_visual": True         # hide drunk visual effect
            }
        )

        self.city_speed = Property(parent,"city_speed", active=False)

        self.morale = Property(parent, "morale",
            active=False,
            extra_fields={"target_morale": 110,}
        )

        self.armor_of_salvation = Property(parent, "armor_of_salvation", active=False)
        self.essence_of_celerity = Property(parent, "essence_of_celerity", active=False)
        self.grail_of_might = Property(parent, "grail_of_might", active=False)
        self.blue_rock_candy = Property(parent, "blue_rock_candy", active=False)
        self.green_rock_candy = Property(parent, "green_rock_candy", active=False)
        self.red_rock_candy = Property(parent, "red_rock_candy", active=False)
        self.birthday_cupcake = Property(parent, "birthday_cupcake", active=False)
        self.slice_of_pumpkin_pie = Property(parent, "slice_of_pumpkin_pie", active=False)
        self.bowl_of_skalefin_soup = Property(parent, "bowl_of_skalefin_soup", active=False)
        self.candy_apple = Property(parent, "candy_apple", active=False)
        self.candy_corn = Property(parent, "candy_corn", active=False)
        self.drake_kabob = Property(parent, "drake_kabob", active=False)
        self.golden_egg = Property(parent, "golden_egg", active=False)
        self.pahnai_salad = Property(parent, "pahnai_salad", active=False)
        self.war_supplies = Property(parent, "war_supplies", active=False)
        self.imp = Property(parent, "imp", active=False)
        self.auto_combat = Property(parent, "auto_combat", active=False)

    def __repr__(self) -> str:
        return (
            f"UpkeepData("
            f"alcohol={self.alcohol}, "
            f"city_speed={self.city_speed}, "
            f"morale={self.morale}, "
            f"armor_of_salvation={self.armor_of_salvation}, "
            f"essence_of_celerity={self.essence_of_celerity}, "
            f"grail_of_might={self.grail_of_might}, "
            f"blue_rock_candy={self.blue_rock_candy}, "
            f"green_rock_candy={self.green_rock_candy}, "
            f"red_rock_candy={self.red_rock_candy}, "
            f"birthday_cupcake={self.birthday_cupcake}, "
            f"slice_of_pumpkin_pie={self.slice_of_pumpkin_pie}, "
            f"bowl_of_skalefin_soup={self.bowl_of_skalefin_soup}, "
            f"candy_apple={self.candy_apple}, "
            f"candy_corn={self.candy_corn}, "
            f"drake_kabob={self.drake_kabob}, "
            f"golden_egg={self.golden_egg}, "
            f"pahnai_salad={self.pahnai_salad}, "
            f"war_supplies={self.war_supplies}, "
        )


class BotConfig:
    def __init__(self, parent: "Botting",  bot_name: str):
        self.parent:"Botting" = parent
        self.bot_name:str = bot_name
        self.initialized:bool = False
        self.FSM = FSM(bot_name)
        self.fsm_running:bool = False
        self.auto_combat_handler:SkillManager.Autocombat = SkillManager.Autocombat()

        self.counters = StepNameCounters()
        
        self.path:List[Tuple[float, float]] = []
        self.path_to_draw:List[Tuple[float, float]] = []
        
        #Overridable functions
        self.pause_on_danger_fn: Callable[[], bool] = lambda: False
        self._reset_pause_on_danger_fn()
        self.on_follow_path_failed: Callable[[], bool] = lambda: False
        
        #Properties
        self.config_properties = ConfigProperties(self)
        self.live_data = LiveData(self)
        
        # Consumable maintainers (default: disabled) - by aC
        self.upkeep = UpkeepData(self)



    def get_counter(self, name: str) -> Optional[int]:
        return self.counters.next_index(name)
   
    def _set_pause_on_danger_fn(self, executable_fn: Callable[[], bool]) -> None:
        self.pause_on_danger_fn = executable_fn
               
    def _reset_pause_on_danger_fn(self) -> None:
        self._set_pause_on_danger_fn(lambda: Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot) or Routines.Checks.Party.IsPartyMemberDead())

    def _set_on_follow_path_failed(self, on_follow_path_failed: Callable[[], bool]) -> None:
        self.on_follow_path_failed = on_follow_path_failed
        if self.config_properties.log_actions.is_active():
            ConsoleLog(MODULE_NAME, f"Set OnFollowPathFailed to {on_follow_path_failed}", Py4GW.Console.MessageType.Info)

    def _update_live_data(self) -> None:
        self.live_data.update()

    #FSM HELPERS
    def set_pause_on_danger_fn(self, pause_on_combat_fn: Callable[[], bool]) -> None:
        self.FSM.AddState(name=f"PauseOnDangerFn_{self.get_counter("PAUSE_ON_DANGER")}",
                          execute_fn=lambda:self._set_pause_on_danger_fn(pause_on_combat_fn),)

    def reset_pause_on_danger_fn(self) -> None:
        self._reset_pause_on_danger_fn()
        self.FSM.AddState(name=f"ResetPauseOnDangerFn_{self.get_counter("PAUSE_ON_DANGER")}",
                          execute_fn=lambda:self._reset_pause_on_danger_fn(),)

    def set_on_follow_path_failed(self, on_follow_path_failed: Callable[[], bool]):
        self.FSM.AddState(name=f"OnFollowPathFailed_{self.get_counter("ON_FOLLOW_PATH_FAILED")}",
                          execute_fn=lambda:self._set_on_follow_path_failed(on_follow_path_failed),)

    def reset_on_follow_path_failed(self) -> None:
        self.set_on_follow_path_failed(lambda: self.parent.helpers.default_on_unmanaged_fail())

    def update_live_data(self) -> None:
        self.FSM.AddState(name=f"UpdatePlayerData_{self.get_counter("UPDATE_PLAYER_DATA")}",
                          execute_fn=lambda:self._update_live_data(),)

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
    def __init__(self, parent: "Botting"):
        self.parent = parent
        
    def is_map_loading(self):
        if GLOBAL_CACHE.Map.IsMapLoading():
            return True
        if not self.parent.config.fsm_running:
            return True
        return False
    
    def on_unmanaged_fail(self) -> bool:
        ConsoleLog(MODULE_NAME, "there was an unmanaged failure, stopping bot.", Py4GW.Console.MessageType.Warning)
        self.parent.Stop()
        return True
        
    def default_on_unmanaged_fail(self) -> bool:
        ConsoleLog(MODULE_NAME, "there was an unmanaged failure, stopping bot.", Py4GW.Console.MessageType.Warning)
        self.parent.Stop()
        return True

    def insert_header_step(self, step_name: str) -> None:
        header_name = f"[H]{step_name}_{self.parent.config.get_counter("HEADER_COUNTER")}"
        self.parent.config.FSM.AddYieldRoutineStep(
            name=header_name,
            coroutine_fn=lambda: Routines.Yield.wait(100)
        )
        
    def _interact_with_agent(self, coords: Tuple[float, float], dialog_id: int = 0):
        #ConsoleLog(MODULE_NAME, f"Interacting with agent at {coords} with dialog_id {dialog_id}", Py4GW.Console.MessageType.Info)
        result = yield from Routines.Yield.Agents.InteractWithAgentXY(*coords)
        #ConsoleLog(MODULE_NAME, f"Interaction result: {result}", Py4GW.Console.MessageType.Info)
        if not result:
            self.on_unmanaged_fail()
            self.parent.config.config_properties.dialog_at_succeeded._apply("value", False)
            return False

        if not self.parent.config.fsm_running:
            yield from Routines.Yield.wait(100)
            self.parent.config.config_properties.dialog_at_succeeded._apply("value", False)
            return False

        if dialog_id != 0:
            GLOBAL_CACHE.Player.SendDialog(dialog_id)
            yield from Routines.Yield.wait(500)

        self.parent.config.config_properties.dialog_at_succeeded._apply("value", True)
        return True
    
    def _interact_with_gadget(self, coords: Tuple[float, float]):
        #ConsoleLog(MODULE_NAME, f"Interacting with gadget at {coords}", Py4GW.Console.MessageType.Info)
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
    
    def draw_path(self, color:Color=Color(255, 255, 0, 255)) -> None:
        overlay = DXOverlay()

        path = self.parent.config.path_to_draw

        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            z1 = DXOverlay.FindZ(x1, y1) - 125
            z2 = DXOverlay.FindZ(x2, y2) - 125
            overlay.DrawLine3D(x1, y1, z1, x2, y2, z2, color.to_color(), False)
            
    def auto_combat(self):
        self.parent.config.auto_combat_handler.SetWeaponAttackAftercast()

        if not (Routines.Checks.Map.MapValid() and 
                Routines.Checks.Player.CanAct() and
                Map.IsExplorable() and
                not self.parent.config.auto_combat_handler.InCastingRoutine()):
            yield from Routines.Yield.wait(100)
        else:
            self.parent.config.auto_combat_handler.HandleCombat()
        yield

    def upkeep_auto_combat(self):
        while True:
            if self.parent.config.upkeep.auto_combat.is_active():
                yield from self.auto_combat()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_armor_of_salvation(self):
        while True:
            if self.parent.config.upkeep.armor_of_salvation.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_ArmorOfSalvation()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_essence_of_celerity(self):
        while True: 
            if self.parent.config.upkeep.essence_of_celerity.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_EssenceOfCelerity()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_grail_of_might(self):
        while True:
            if self.parent.config.upkeep.grail_of_might.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GrailOfMight()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_green_rock_candy(self):
        while True:
            if self.parent.config.upkeep.green_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GreenRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_red_rock_candy(self):
        while True:
            if self.parent.config.upkeep.red_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_RedRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_blue_rock_candy(self):
        while True:
            if self.parent.config.upkeep.blue_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BlueRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_birthday_cupcake(self):
        while True:
            if self.parent.config.upkeep.birthday_cupcake.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BirthdayCupcake()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_slice_of_pumpkin_pie(self):
        while True:
            if self.parent.config.upkeep.slice_of_pumpkin_pie.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_SliceOfPumpkinPie()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_bowl_of_skalefin_soup(self):
        while True:
            if self.parent.config.upkeep.bowl_of_skalefin_soup.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BowlOfSkalefinSoup()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_candy_apple(self):
        while True:
            if self.parent.config.upkeep.candy_apple.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_CandyApple()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_candy_corn(self):
        while True:
            if self.parent.config.upkeep.candy_corn.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_CandyCorn()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_drake_kabob(self):
        while True:
            if self.parent.config.upkeep.drake_kabob.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_DrakeKabob()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_golden_egg(self):
        while True:
            if self.parent.config.upkeep.golden_egg.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GoldenEgg()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_pahnai_salad(self):
        while True:
            if self.parent.config.upkeep.pahnai_salad.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_PahnaiSalad()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_war_supplies(self):
        while True:
            if self.parent.config.upkeep.war_supplies.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_WarSupplies()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_alcohol(self):
        import PyEffects
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
        while True:
            if self.parent.config.upkeep.city_speed.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_City_Speed()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_morale(self):
        while True:
            if self.parent.config.upkeep.morale.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(110)
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_imp(self):
        while True:
            if self.parent.config.upkeep.imp.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_Imp()
            else:
                yield from Routines.Yield.wait(500)

    #region yield steps

    @_yield_step(label="WasteTime", counter_key="WASTE_TIME")
    def waste_time(self, duration: int = 100):
        yield from Routines.Yield.wait(duration)

    @_yield_step(label="WasteTimeUntilConditionMet", counter_key="WASTE_TIME")
    def waste_time_until_condition_met(self, condition: Callable[[], bool], duration: int=1000):
        while True:
            yield from Routines.Yield.wait(duration)
            if condition():
                break

    @_yield_step(label="Travel", counter_key="TRAVEL")
    def travel(self, target_map_id):
        GLOBAL_CACHE.Map.Travel(target_map_id)
        yield from Routines.Yield.wait(1000)

    @_yield_step(label="FollowPath", counter_key="FOLLOW_PATH")
    def follow_path(self) -> Generator[Any, Any, bool]:
        
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

        self.parent.config.config_properties.follow_path_succeeded._apply("value",success_movement)
        if not success_movement:
            if exit_condition:
                return True
            self.on_unmanaged_fail()
            return False
        
        return True

    @_yield_step(label="GetPathTo", counter_key="GET_PATH_TO")
    def get_path_to(self, x: float, y: float):
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

    @_yield_step(label="InteractWithModel", counter_key="DIALOG_AT")
    def interact_with_model(self, model_id: int, dialog_id: int=0) -> Generator[Any, Any, bool]:
        agent_id = Routines.Agents.GetAgentIDByModelID(model_id)
        x,y = GLOBAL_CACHE.Agent.GetXY(agent_id)
        return (yield from self._interact_with_agent((x, y), dialog_id))

    @_yield_step(label="WaitForMapLoad", counter_key="WAIT_FOR_MAP_LOAD")
    def wait_for_map_load(self, target_map_id):
        wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(target_map_id)
        if not wait_of_map_load:
            Py4GW.Console.Log(MODULE_NAME, "Map load failed.", Py4GW.Console.MessageType.Error)
            self.on_unmanaged_fail()
        yield from Routines.Yield.wait(1000)

    @_yield_step(label="EnterChallenge", counter_key="ENTER_CHALLENGE")
    def enter_challenge(self, wait_for:int= 3000):
        GLOBAL_CACHE.Map.EnterChallenge()
        yield from Routines.Yield.wait(wait_for)
        
    @_yield_step(label="CancelSkillRewardWindow", counter_key="CANCEL_SKILL_REWARD_WINDOW")
    def cancel_skill_reward_window(self):
        global bot  
        yield from Routines.Yield.wait(500)
        cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)  # Cancel button frame ID
        if not cancel_button_frame_id:
            Py4GW.Console.Log(MODULE_NAME, "Cancel button frame ID not found.", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return
        
        while not UIManager.FrameExists(cancel_button_frame_id):
            yield from Routines.Yield.wait(1000)
            return
        
        UIManager.FrameClick(cancel_button_frame_id)
        yield from Routines.Yield.wait(1000)
            
            
    @_yield_step(label="WithdrawItems", counter_key="WITHDRAW_ITEMS")
    def withdraw_items(self, model_id:int, quantity:int) -> Generator[Any, Any, bool]:
        result = yield from Routines.Yield.Items.WithdrawItems(model_id, quantity)
        if not result:
            ConsoleLog("WithdrawItems", f"Failed to withdraw ({quantity}) items from storage.", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return False

        return True

    @_yield_step(label="CraftItem", counter_key="CRAFT_ITEM")
    def craft_item(self, output_model_id: int, count: int,
                trade_model_ids: list[int], quantity_list: list[int]):
        result = yield from Routines.Yield.Items.CraftItem(output_model_id=output_model_id,
                                                            count=count,
                                                            trade_model_ids=trade_model_ids,
                                                            quantity_list=quantity_list)
        if not result:
            ConsoleLog("CraftItem", f"Failed to craft item ({output_model_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return False

        return True

    @_yield_step(label="EquipItem", counter_key="EQUIP_ITEM")
    def equip_item(self, model_id: int):
        result = yield from Routines.Yield.Items.EquipItem(model_id)
        if not result:
            ConsoleLog("EquipItem", f"Failed to equip item ({model_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return False

        return True

    @_yield_step(label="LeaveParty", counter_key="LEAVE_PARTY")
    def leave_party(self):
        GLOBAL_CACHE.Party.LeaveParty()
        yield from Routines.Yield.wait(250)

    @_yield_step(label="SpawnBonusItems", counter_key="SPAWN_BONUS")
    def spawn_bonus_items(self):
        yield from Routines.Yield.Items.SpawnBonusItems()

    @_yield_step(label="FlagAllHeroes", counter_key="FLAG_ALL_HEROES")
    def flag_all_heroes(self, x, y):
        GLOBAL_CACHE.Party.Heroes.FlagAllHeroes(x,y)
        yield from Routines.Yield.wait(500)

    @_yield_step(label="UnflagAllHeroes", counter_key="FLAG_ALL_HEROES")
    def unflag_all_heroes(self):
        GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()
        yield from Routines.Yield.wait(500)

    def resign(self):
        yield from Routines.Yield.Player.Resign()

class Botting:
    def __init__(self, bot_name="DefaultBot"):
        self.bot_name = bot_name
        self.helpers = BottingHelpers(self)
        self.config = BotConfig(self, bot_name)

    # ---------- internal path resolver ----------

    def _resolve_property_path(self, name: str) -> Tuple["Property", str]:
        """
        Resolve a dotted name like:
          - "config.log_actions.value"
          - "upkeep.alcohol.active"
          - "live.Player.level"
          - "config.movement_timeout"   (defaults to 'value' if present)
        Returns: (Property_instance, field_name)
        Raises: AttributeError / KeyError if not found or not a Property.
        """
        if not isinstance(name, str) or not name:
            raise AttributeError("Empty property path")

        parts = name.split(".")
        # map first segment to the correct container on BotConfig
        roots = {
            "upkeep": self.config.upkeep,
            "live_data": self.config.live_data,
            "config_properties": self.config.config_properties,
        }

        # choose root
        root_key = parts[0]
        if root_key in roots:
            obj = roots[root_key]
            parts = parts[1:]
        else:
            # fallback: try direct attr on BotConfig (advanced users)
            obj = self.config

        # walk attributes until we hit a Property
        prop = None
        for i, seg in enumerate(parts):
            nxt = getattr(obj, seg, None)
            if nxt is None:
                raise AttributeError(f"Path segment '{seg}' not found in '{obj}' for '{name}'")

            # if we reach a Property, remaining segment (if any) is the field
            if isinstance(nxt, Property):
                prop = nxt
                remaining = parts[i+1:]
                if remaining:
                    field = remaining[0]
                else:
                    # choose sensible default field
                    # prefer 'value' if present, else 'active'
                    field = "value" if "value" in prop._values else "active"
                return prop, field

            obj = nxt  # go deeper

        # If we finished the loop with no Property yet, maybe the last obj is a Property
        if isinstance(obj, Property):
            prop = obj
            field = "value" if "value" in prop._values else "active"
            return prop, field

        raise AttributeError(f"'{name}' did not resolve to a Property")

    # ---------- public API ----------

    def SetProperty(self, name: str, value: Any) -> bool:
        """
        Schedule a change via the FSM on the targeted Property field.
        """
        try:
            prop, field = self._resolve_property_path(name)
            prop.set(field, value)  # schedule
            return True
        except Exception:
            return False

    def GetProperty(self, name: str) -> Any | None:
        """
        Read the committed value of a Property field.
        """
        try:
            prop, field = self._resolve_property_path(name)
            return prop.get(field)
        except Exception:
            return None

    
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


    def Start(self):
        self.config.FSM.start()
        self.config.fsm_running = True
        self._start_coroutines()

    def Stop(self):
        self.config.fsm_running = False
        self.config.FSM.RemoveAllManagedCoroutines()
        self.config.FSM.stop()

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
            self.config._update_live_data()
            self.config.FSM.update()
            

    def WasteTime(self, duration: int= 100) -> None:
        self.helpers.waste_time(duration)

    def WasteTimeUntilConditionMet(self, condition: Callable[[], bool], duration: int=1000) -> None:
        self.helpers.waste_time_until_condition_met(condition, duration)
        
    def WasteTimeUntilOOC(self) -> None:
        wait_condition = lambda: not(Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot))
        self.helpers.waste_time_until_condition_met(wait_condition)

    def AddFSMCustomYieldState(self, execute_fn, name: str) -> None:
        self.config.FSM.AddYieldRoutineStep(name=name, coroutine_fn=execute_fn)

    def Travel(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        if target_map_name:
            target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)

        self.helpers.travel(target_map_id)

    def MoveTo(self, x:float, y:float, step_name: str=""):
        if step_name == "":
            step_name = f"MoveTo_{self.config.get_counter("MOVE_TO")}"

        self.helpers.get_path_to(x, y)
        self.helpers.follow_path()

    def FollowPath(self, path: List[Tuple[float, float]], step_name: str="") -> None:
        if step_name == "":
            step_name = f"FollowPath_{self.config.get_counter("FOLLOW_PATH")}"

        self.helpers.set_path_to(path)
        self.helpers.follow_path()
        
    def DrawPath(self, color:Color=Color(255, 255, 0, 255)) -> None:
        if self.config.config_properties.draw_path.is_active():
            self.helpers.draw_path(color)

    def DialogAt(self, x: float, y: float, dialog:int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"DialogAt_{self.config.get_counter("DIALOG_AT")}"

        self.helpers.interact_with_agent((x, y), dialog_id=dialog)
        
    def DialogWithModel(self, model_id: int, dialog:int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"DialogWithModel_{self.config.get_counter("DIALOG_AT")}"

        self.helpers.interact_with_model(model_id=model_id, dialog_id=dialog)

    def InteractNPCAt(self, x: float, y: float, step_name: str="") -> None:
        if step_name == "":
            step_name = f"InteractAt_{self.config.get_counter("INTERACT_AT")}"
            
        self.helpers.interact_with_agent((x, y))

    def InteractGadgetAt(self, x: float, y: float, step_name: str="") -> None:
        if step_name == "":
            step_name = f"InteractGadgetAt_{self.config.get_counter("INTERACT_GADGET_AT")}"

        self.helpers.interact_with_gadget((x, y))

    def InteractWithModel(self, model_id: int) -> None:
        self.helpers.interact_with_model(model_id=model_id)

    def WaitForMapLoad(self, target_map_id: int = 0, target_map_name: str = "") -> None:
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



# ----------------------- BOT CONFIGURATION --------------------------------------------

UNLOCK_SECONDARY = 0x813D08
UNLOCK_STORAGE = 0x84
ACCEPT_THE_THREAT_GROWS_REWARD = 0x815407
TAKE_GO_TO_TOGO_QUEST = 0x815501

bot = Botting("Factions Leveler")

#region bot_helpers
class BotLocals:
    def __init__(self):
        self.target_cupcake_count = 50
        self.target_honeycomb_count = 100

bot_locals = BotLocals()

#Helpers
def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.config.config_properties.pause_on_danger.disable()
    bot.config.config_properties.halt_on_death.enable()
    bot.config.config_properties.movement_timeout.set("value", 15000)
    bot.SpawnBonusItems()
    bot.config.upkeep.auto_combat.disable()
    bot.config.upkeep.imp.disable()
    bot.config.upkeep.birthday_cupcake.enable()
    bot.config.upkeep.morale.disable()
    bot.AddFSMCustomYieldState(withdraw_cupcakes, "Withdraw Cupcakes")

def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.config.config_properties.pause_on_danger.enable()
    bot.config.config_properties.halt_on_death.disable()
    bot.config.config_properties.movement_timeout.set("value",-1)
    bot.SpawnBonusItems()
    bot.config.upkeep.auto_combat.enable()
    bot.config.upkeep.imp.enable()
    bot.config.upkeep.birthday_cupcake.enable()
    bot.config.upkeep.morale.enable()

def EquipSkillBar(): 
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
    
def AddHenchmen():
    party_size = bot.GetProperty("live_data.Map.max_party_size") or 0
    zen_daijun_map_id = 213
    
    if party_size <= 4:
        HEALER_ID = 1
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
        ConsoleLog("addhenchman",f"Added Henchman: {HEALER_ID}")
        yield from Routines.Yield.wait(250)
        SPIRITS_ID = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRITS_ID)
        ConsoleLog("addhenchman",f"Added Henchman: {SPIRITS_ID}")
        yield from Routines.Yield.wait(250)
        GUARDIAN_ID = 2
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(GUARDIAN_ID)
        ConsoleLog("addhenchman",f"Added Henchman: {GUARDIAN_ID}")
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
    elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("The Marketplace"):
        HEALER_ID = 6
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
        yield from Routines.Yield.wait(250)
        SPIRIT_ID = 9
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRIT_ID)
        yield from Routines.Yield.wait(250)
        EARTH_ID = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(EARTH_ID)
        yield from Routines.Yield.wait(250)
        SHOCK_ID = 1
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SHOCK_ID)
        yield from Routines.Yield.wait(250)
        GRAVE_ID = 4
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(GRAVE_ID)
        yield from Routines.Yield.wait(250)
        FIGHTER_ID = 7
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(FIGHTER_ID)
        yield from Routines.Yield.wait(250)
        ILLUSION_ID = 3
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(ILLUSION_ID)
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
    else:
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(1)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(2)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(3)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(4)
        yield from Routines.Yield.wait(250)
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(5)
        yield from Routines.Yield.wait(250)

def ExitMonasteryOverlook(bot: Botting) -> None:
    bot.AddHeaderStep("Exit Monastery Overlook")
    bot.MoveTo(-7011, 5750,"Move to Ludo")
    LUDO_I_AM_SURE = 0x85
    bot.DialogAt(-7048,5817,LUDO_I_AM_SURE)
    bot.WaitForMapLoad(target_map_name="Shing Jea Monastery")
    
def ExitToCourtyard(bot: Botting) -> None:
    bot.AddHeaderStep("Exit To Courtyard")
    PrepareForBattle(bot)
    bot.MoveTo(-3480, 9460)
    bot.WaitForMapLoad(target_map_name="Linnok Courtyard")
    
def UnlockSecondaryProfession(bot: Botting) -> None:
    def assign_profession_unlocker_dialog():
        global bot
        if bot.GetProperty("live_data.Player.primary_profession") == "Assassin":
            yield from bot.helpers._interact_with_agent((-92, 9217),0x813D0E)
        else:
            yield from bot.helpers._interact_with_agent((-92, 9217),0x813D08)
        yield from Routines.Yield.wait(250)


    bot.AddHeaderStep("Unlock Secondary Profession")
    bot.MoveTo(-159, 9174)
    bot.AddFSMCustomYieldState(assign_profession_unlocker_dialog, "Update Secondary Profession Dialog")
    bot.CancelSkillRewardWindow()
    bot.CancelSkillRewardWindow()
    TAKE_SECONDARY_REWARD = 0x813D07
    bot.DialogAt(-92, 9217, TAKE_SECONDARY_REWARD)
    TAKE_MINISTER_CHO_QUEST = 0x813E01
    bot.DialogAt(-92, 9217, TAKE_MINISTER_CHO_QUEST)
    #ExitCourtyard
    bot.MoveTo(-3762, 9471)
    bot.WaitForMapLoad(target_map_name="Shing Jea Monastery")

def UnlockXunlaiStorage(bot: Botting) -> None:
    bot.AddHeaderStep("Unlock Xunlai Storage")
    path_to_xunlai: List[Tuple[float, float]] = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3869, 10346),]
    bot.FollowPath(path_to_xunlai,"Follow Path to Xunlai")
    bot.DialogAt(-3749, 10367, UNLOCK_STORAGE, step_name="Unlock Xunlai Storage")
    
def CraftWeapons(bot: Botting) -> None:
    def craft_and_equip_items():
        MELEE_CLASSES = ["Warrior", "Ranger", "Assassin","None"]
        if bot.GetProperty("live_data.Player.primary_profession") in MELEE_CLASSES:
            yield from bot.helpers._interact_with_agent((-6519, 12335))
            result = yield from Routines.Yield.Items.WithdrawItems(ModelID.Iron_Ingot.value, 5)
            if not result:
                ConsoleLog("CraftWeapons", "Failed to withdraw Iron Ingots.", Py4GW.Console.MessageType.Error)
                bot.helpers.on_unmanaged_fail()
                return

            SAI_MODEL_ID = 11643
            result = yield from Routines.Yield.Items.CraftItem(SAI_MODEL_ID, 100,[ModelID.Iron_Ingot.value],[5])
            if not result:
                ConsoleLog("CraftWeapons", "Failed to craft SAI_MODEL_ID.", Py4GW.Console.MessageType.Error)
                bot.helpers.on_unmanaged_fail()
                return

            result = yield from Routines.Yield.Items.EquipItem(SAI_MODEL_ID)
            if not result:
                ConsoleLog("CraftWeapons", f"Failed to equip item ({SAI_MODEL_ID}).", Py4GW.Console.MessageType.Error)
                bot.helpers.on_unmanaged_fail()
                return False

            return True
        
        else:
            yield from Routines.Yield.Items.SpawnBonusItems()
            WAND_MODEL_ID = 6508
            yield from Routines.Yield.Items.EquipItem(WAND_MODEL_ID)
            SHIELD_MODEL_ID = 6514
            yield from Routines.Yield.Items.EquipItem(SHIELD_MODEL_ID)

    bot.AddHeaderStep("Craft Weapons")

    bot.MoveTo(-6423, 12183, "Move to Weapon Crafter")
    bot.AddFSMCustomYieldState(craft_and_equip_items, "Craft and Equip Items")


def ExitToSunquaVale(bot: Botting) -> None:
    bot.AddHeaderStep("Exit To Sunqua Vale")
    ConfigurePacifistEnv(bot)
    bot.MoveTo(-14961,11453)
    bot.WaitForMapLoad(target_map_name="Sunqua Vale")

def TravelToMinisterCho(bot: Botting) -> None:
    bot.AddHeaderStep("Travel To Minister Cho")
    ConfigurePacifistEnv(bot)
    bot.MoveTo(6698, 16095, "Move to Minister Cho")
    GUARDMAN_ZUI_DLG4 = 0x80000B
    bot.DialogAt(6637, 16147, GUARDMAN_ZUI_DLG4, step_name="Talk to Guardman Zui")
    bot.WasteTime(5000)
    minister_cho_map_id = 214
    bot.WaitForMapLoad(target_map_id=minister_cho_map_id)
    ACCEPT_MINISTER_CHO_REWARD = 0x813E07
    bot.DialogAt(7884, -10029, ACCEPT_MINISTER_CHO_REWARD, step_name="Accept Minister Cho Reward")
    

def withdraw_cupcakes():
    global bot_locals
    target_cupcake_count = bot_locals.target_cupcake_count
    if bot.GetProperty("upkeep.birthday_cupcake.active"):
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

def withdraw_honeycombs():
    target_honeycomb_count = bot_locals.target_honeycomb_count
    if bot.GetProperty("upkeep.morale.active"):
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
    yield from Routines.Yield.wait(250)

def PrepareForBattle(bot: Botting):
    ConfigureAggressiveEnv(bot)
    bot.AddFSMCustomYieldState(EquipSkillBar, "Equip Skill Bar")
    bot.LeaveParty()
    bot.AddFSMCustomYieldState(AddHenchmen, "Add Henchmen")
    bot.AddFSMCustomYieldState(withdraw_cupcakes, "Withdraw Cupcakes")
    bot.AddFSMCustomYieldState(withdraw_honeycombs, "Withdraw Honeycombs")

def EnterMinisterChoMission(bot: Botting):
    bot.AddHeaderStep("Enter Minister Cho Mission")
    PrepareForBattle(bot)
    bot.EnterChallenge(wait_for=4500)
    minister_cho_map_id = 214
    bot.WaitForMapLoad(target_map_id=minister_cho_map_id)
    
def MinisterChoMission(bot: Botting) -> None:
    bot.AddHeaderStep("Minister Cho Mission")
    bot.MoveTo(6358, -7348, "Move to Activate Mission")
    bot.MoveTo(507, -8910, "Move to First Door")
    bot.MoveTo(4889, -5043, "Move to Map Tutorial")
    bot.MoveTo(6216, -1108, "Move to Bridge Corner")
    bot.MoveTo(2617, 642, "Move to Past Bridge")
    bot.MoveTo(0, 1137, "Move to Fight Area")
    bot.MoveTo(-7454, -7384, "Move to Zoo Entrance")
    bot.MoveTo(-9138, -4191, "Move to First Zoo Fight")
    bot.MoveTo(-7109, -25, "Move to Bridge Waypoint")
    bot.MoveTo(-7443, 2243, "Move to Zoo Exit")
    bot.MoveTo(-16924, 2445, "Move to Final Destination")
    bot.InteractNPCAt(-17031, 2448) #"Interact with Minister Cho"
    wait_condition = lambda: (Routines.Checks.Map.MapValid() and (GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Ran Musu Gardens")))
    bot.WasteTimeUntilConditionMet(wait_condition)

def TakeWarningTheTenguQuest(bot: Botting):
    bot.AddHeaderStep("Take Warning the Tengu Quest")
    TAKE_WARNING_THE_TENGU = 0x815301
    bot.DialogAt(15846, 19013, TAKE_WARNING_THE_TENGU, step_name="Take Warning the Tengu Quest")
    PrepareForBattle(bot)
    ConfigurePacifistEnv(bot)
    bot.MoveTo(14730,15176)
    bot.WaitForMapLoad(target_map_name="Kinya Province")

def WarningTheTenguQuest(bot: Botting):
    bot.AddHeaderStep("Warning The Tengu Quest")
    bot.MoveTo(1429, 12768, "Move to Tengu Part2")
    #part 2
    ConfigureAggressiveEnv(bot)
    bot.MoveTo(-983, 4931, "Move to Tengu NPC")
    CONTINUE_WARNING_THE_TENGU_QUEST = 0x815304
    bot.DialogAt(-1023, 4844, CONTINUE_WARNING_THE_TENGU_QUEST, step_name="Continue Warning the Tengu Quest")
    bot.MoveTo(-5011, 732, "Move to Tengu Killspot")
    bot.WasteTimeUntilOOC()
    bot.MoveTo(-983, 4931, "Move back to Tengu NPC")
    TAKE_WARNING_THE_TENGU_REWARD = 0x815307
    bot.DialogAt(-1023, 4844, TAKE_WARNING_THE_TENGU_REWARD, step_name="Take Warning the Tengu Reward")
    TAKE_THE_THREAT_GROWS = 0x815401
    bot.DialogAt(-1023, 4844, TAKE_THE_THREAT_GROWS, step_name="Take The Threat Grows Quest")
    bot.Travel(target_map_name="Shing Jea Monastery")
    bot.WaitForMapLoad(target_map_name="Shing Jea Monastery")

def ExitToTsumeiVillage(bot: Botting):
    bot.AddHeaderStep("Exit To Tsumei Village")
    bot.MoveTo(-4900, -13900, "Move to Tsumei Village")
    bot.WaitForMapLoad(target_map_name="Tsumei Village")

def ExitToPanjiangPeninsula(bot: Botting):
    bot.AddHeaderStep("Exit To Panjiang Peninsula")
    PrepareForBattle(bot)
    bot.MoveTo(-11600,-17400, "Move to Panjiang Peninsula")
    bot.WaitForMapLoad(target_map_name="Panjiang Peninsula")

def TheThreatGrows(bot: Botting):
    bot.AddHeaderStep("The Threat Grows")
    bot.MoveTo(9700, 7250, "Move to The Threat Grows Killspot")
    SISTER_TAI_MODEL_ID = 3316
    wait_function = lambda: (not Routines.Checks.Agents.InDanger(aggro_area=Range.Spellcast)) and GLOBAL_CACHE.Agent.HasQuest(Routines.Agents.GetAgentIDByModelID(SISTER_TAI_MODEL_ID))
    bot.WasteTimeUntilConditionMet(wait_function)
    ConfigurePacifistEnv(bot)
    ACCEPT_REWARD = 0x815407
    bot.DialogWithModel(SISTER_TAI_MODEL_ID, ACCEPT_REWARD, step_name="Accept The Threat Grows Reward")
    TAKE_QUEST = 0x815501
    bot.DialogWithModel(SISTER_TAI_MODEL_ID, TAKE_QUEST, step_name="Take Go to Togo Quest")
    bot.Travel(target_map_name="Shing Jea Monastery")
    bot.WaitForMapLoad(target_map_name="Shing Jea Monastery")

def AdvanceToSaoshangTrail(bot: Botting):
    bot.AddHeaderStep("Advance To Saoshang Trail")
    bot.MoveTo(-159, 9174, "Move to Togo 002")
    ACCEPT_TOGO_QUEST = 0x815507
    bot.DialogAt(-92, 9217, ACCEPT_TOGO_QUEST, step_name="Accept Togo Quest")
    TAKE_EXIT_QUEST = 0x815601
    bot.DialogAt(-92, 9217, TAKE_EXIT_QUEST, step_name="Take Exit Quest")
    CONTINUE = 0x80000B
    bot.DialogAt(538, 10125, CONTINUE, step_name="Continue")
    saoshang_trail_map_id = 313
    bot.WaitForMapLoad(target_map_id=saoshang_trail_map_id)

def TraverseSaoshangTrail(bot: Botting):
    bot.AddHeaderStep("Traverse Saoshang Trail")
    CONTINUE = 0x815604
    bot.DialogAt(1254, 10875, CONTINUE)
    bot.MoveTo(16600, 13150)
    bot.WaitForMapLoad(target_map_name="Seitung Harbor")

def TakeRewardAndExitSeitungHarbor(bot: Botting):
    bot.AddHeaderStep("Take Reward And Exit Seitung Harbor")
    TAKE_REWARD = 0x815607
    bot.DialogAt(16368, 12011, TAKE_REWARD)
    PrepareForBattle(bot)
    bot.MoveTo(16777,17540)
    bot.WaitForMapLoad(target_map_name="Jaya Bluffs")

def GoToZenDaijun(bot: Botting):
    bot.AddHeaderStep("Go To Zen Daijun")
    bot.MoveTo(23616, 1587)
    bot.WaitForMapLoad(target_map_name="Haiju Lagoon")
    bot.MoveTo(16571, -22196)
    CONTINUE = 0x80000B
    bot.DialogAt(16489, -22213, CONTINUE)
    bot.WasteTime(6000)
    zen_daijun_map_id = 213
    bot.WaitForMapLoad(target_map_id=zen_daijun_map_id)
    
def PrepareForZenDaijunMission(bot:Botting):
    bot.AddHeaderStep("Prepare for Zen Daijun Mission")
    PrepareForBattle(bot)
    bot.EnterChallenge(6000)
    

def ZenDaijunMission(bot: Botting):
    bot.AddHeaderStep("Zen Daijun Mission")
    bot.MoveTo(11903, 11235)
    bot.InteractGadgetAt(11665, 11386)
    bot.MoveTo(10549,8070)
    bot.MoveTo(10945,3436)
    bot.MoveTo(7551,3810)
    bot.MoveTo(5538,1993)
    bot.InteractGadgetAt(4754,1451)
    bot.MoveTo(4508, -1084)
    bot.MoveTo(528, 6271)
    bot.MoveTo(-9833, 7579)
    bot.MoveTo(-12983, 2191)
    bot.MoveTo(-12362, -263)
    bot.MoveTo(-9813, -114)
    bot.FlagAllHeroes(-8656, -771)
    bot.MoveTo(-7851, -1458)
    wait_condition = lambda: (Routines.Checks.Map.MapValid() and (GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor")))
    bot.WasteTimeUntilConditionMet(wait_condition)

def AdvanceToMarketplace(bot: Botting):
    bot.AddHeaderStep("Advance To Marketplace")
    bot.MoveTo(17470, 9029)
    bot.DialogAt(16927, 9004, 0x815D01)  # "I Will Set Sail Immediately"
    bot.DialogAt(16927, 9004, 0x815D05)  # "a Master burden"
    #bot.DialogAt(16927, 9004, 0x81)  # book a passage to kaineng
    bot.DialogAt(16927, 9004, 0x84)  # i am sure
    bot.WaitForMapLoad(target_map_name="Kaineng Docks")
    bot.MoveTo(9866, 20041) #headmaster Greico
    bot.DialogAt(9955, 20033, 0x815D04)  # a masters burden
    bot.MoveTo(12003, 18529) 
    bot.WaitForMapLoad(target_map_name="The Marketplace")

def FarmUntilLevel10(bot: Botting):
    bot.AddHeaderStep("Farm Until Level 10")
    PrepareForBattle(bot)
    bot.MoveTo(11360, 15174)
    bot.WaitForMapLoad(target_map_name="Wajjun Bazaar")
    bot.MoveTo(6451, 14474)
    bot.MoveTo(4122, 9766)
    bot.MoveTo(385, 11297)
    bot.MoveTo(2251, 15280)
    bot.MoveTo(1352, 17728)
    bot.WasteTimeUntilOOC()
    if bot.config.live_data.Player.get("level") >= 10:
        bot.config.FSM.jump_to_state_by_name("[H]Farm Until Level 10_25")

def create_bot_routine(bot: Botting) -> None:
    bot.AddHeaderStep("Initial Step")
    ExitMonasteryOverlook(bot)
    ExitToCourtyard(bot)
    UnlockSecondaryProfession(bot)
    UnlockXunlaiStorage(bot)
    CraftWeapons(bot)
    ExitToSunquaVale(bot)
    TravelToMinisterCho(bot)
    EnterMinisterChoMission(bot)
    MinisterChoMission(bot)
    ConfigurePacifistEnv(bot)
    TakeWarningTheTenguQuest(bot)
    WarningTheTenguQuest(bot)
    ExitToSunquaVale(bot)
    ExitToTsumeiVillage(bot)
    ExitToPanjiangPeninsula(bot)
    TheThreatGrows(bot)
    ExitToCourtyard(bot)
    AdvanceToSaoshangTrail(bot)
    TraverseSaoshangTrail(bot)
    TakeRewardAndExitSeitungHarbor(bot)
    GoToZenDaijun(bot)
    PrepareForZenDaijunMission(bot)
    ZenDaijunMission(bot)
    AdvanceToMarketplace(bot)
    FarmUntilLevel10(bot)
    bot.AddHeaderStep("Final Step")
    bot.Stop()


bot.Routine = create_bot_routine.__get__(bot)



selected_step = 0
filter_header_steps = True
def main():
    global selected_step, filter_header_steps
    try:
        bot.Update()
        
        if PyImGui.begin("PathPlanner Test", PyImGui.WindowFlags.AlwaysAutoResize):
            
            if PyImGui.button("Start Botting"):
                bot.Start()

            if PyImGui.button("Stop Botting"):
                bot.Stop()
                
            PyImGui.separator()
            
            filter_header_steps = PyImGui.checkbox("Show only Header Steps", filter_header_steps)

            fsm_steps_all = bot.config.FSM.get_state_names()
            

            # choose source list (original names) based on filter
            if filter_header_steps:
                fsm_steps_original = [s for s in fsm_steps_all if s.startswith("[H]")]
            else:
                fsm_steps_original = fsm_steps_all

            # display list: clean headers; leave non-headers as-is
            def _clean_header(name: str) -> str:
                #return name
                if name.startswith("[H]"):
                    name = re.sub(r'^\[H\]\s*', '', name)              # remove [H] (and optional space)
                    name = re.sub(r'_(?:\[\d+\]|\d+)$', '', name)       # remove _123 or _[123] at end
                return name

            fsm_steps = [_clean_header(s) for s in fsm_steps_original]
            

            if not fsm_steps:
                PyImGui.text("No steps to show (filter active).")
            else:
                if selected_step >= len(fsm_steps):
                    selected_step = max(0, len(fsm_steps) - 1)

                selected_step = PyImGui.combo("FSM Steps", selected_step, fsm_steps)
                
                sel_orig = fsm_steps_original[selected_step]
                state_num = bot.config.FSM.get_state_number_by_name(sel_orig)

                # display it (handle not-found defensively)
                if state_num is None or state_num == -1:
                    PyImGui.text(f"Selected step: {sel_orig}  (step #: N/A)")
                else:
                    PyImGui.text(f"Selected step: {sel_orig}  (step #: {state_num})")

                if PyImGui.button("start at Step"):
                    bot.config.fsm_running = True
                    bot.config.FSM.reset()
                    # jump with ORIGINAL name
                    bot.config.FSM.jump_to_state_by_name(fsm_steps_original[selected_step])
                    bot._start_coroutines()


                            
            PyImGui.separator()

            bot.config.config_properties.draw_path.set_active(PyImGui.checkbox("Draw Path", bot.config.config_properties.draw_path.is_active()))

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

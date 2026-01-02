
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, AutoPathing, Py4GW, FSM, ConsoleLog, Color, DXOverlay,
                          UIManager,ModelID, Utils, SkillManager, Map
                         )
from typing import List, Tuple, Any, Generator, Callable
import PyImGui
import time

from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
from functools import wraps

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
    def is_player_dead():
        return GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID())


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


class BotProperty:
    def __init__(self, parent: "BotConfig", name: str, default_value: Any):
        self.parent = parent            # has FSM and get_counter(name: str) -> int
        self.name = name                # string key (e.g., "movement_timeout")
        self._default = default_value
        self._value = default_value     # committed value

    # Read current committed value (no FSM)
    def get(self) -> Any:
        return self._value

    # Internal apply used by scheduled steps
    def _apply(self, new_value: Any) -> None:
        self._value = new_value

    # Schedule a change; actual write happens when FSM runs the step
    def set(self, value: Any) -> None:
        step_name = f"{self.name}_{self.parent.get_counter("PROPERTY")}"
        self.parent.FSM.AddState(
            name=step_name,
            execute_fn=lambda v=value: self._apply(v),
        )

    # Schedule reset to default
    def reset(self) -> None:
        step_name = f"{self.name}_RESET_{self.parent.get_counter("PROPERTY")}"
        self.parent.FSM.AddState(
            name=step_name,
            execute_fn=lambda: self._apply(self._default),
        )

class LiveData:
    def __init__(self):
        self.player_profession_primary = "None"
        self.player_profession_secondary = "None"
        self.level = 1
        self.map_current_map_id = 0
        self.map_max_party_size = 0

    def update(self):
        primary, secondary = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        self.player_profession_primary = primary
        self.player_profession_secondary = secondary
        self.level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())
        self.current_map_id = Map.GetMapID()
        self.map_max_party_size = Map.GetMaxPartySize()
        
#region BotConfig
class BotConfig:
    def __init__(self, parent: "Botting",  bot_name: str):
        self.parent:"Botting" = parent
        self.bot_name:str = bot_name
        self.initialized:bool = False
        self.FSM = FSM(bot_name)
        self.fsm_running:bool = False
        self.auto_combat_handler:SkillManager.Autocombat = SkillManager.Autocombat()

        self.counters = StepNameCounters()

        self.pause_on_danger_fn: Callable[[], bool] = lambda: False
        self._reset_pause_on_danger_fn()
        
        self.path:List[Tuple[float, float]] = []
        self.path_to_draw:List[Tuple[float, float]] = []
        
        self.on_follow_path_failed: Callable[[], bool] = lambda: False
        
        #Properties
        self.halt_on_death = BotProperty(self, "halt_on_death", True)
        self.pause_on_danger = BotProperty(self, "pause_on_danger", False)
        self.movement_timeout = BotProperty(self, "movement_timeout", 15000)
        self.movement_tolerance = BotProperty(self, "movement_tolerance", 150)
        self.draw_path = BotProperty(self, "draw_path", True)
        self.follow_path_succeeded = BotProperty(self, "follow_path_succeeded", False)
        self.log_actions = BotProperty(self, "log_actions", False)
        self.dialog_at_succeeded = BotProperty(self, "dialog_at_succeeded", False)
        # Consumable maintainers (default: disabled) - by aC
        self.use_alcohol        = BotProperty(self, "use_alcohol", False)
        self.use_city_speed     = BotProperty(self, "use_city_speed", False)
        self.use_morale         = BotProperty(self, "use_morale", False)
        self.use_dp_removal     = BotProperty(self, "use_dp_removal", False)
        self.use_consets        = BotProperty(self, "use_consets", False)
        self.use_grail          = BotProperty(self, "use_grail_of_might", False)
        self.use_salvation      = BotProperty(self, "use_armor_of_salvation", False)
        self.use_celerity       = BotProperty(self, "use_essence_of_celerity", False)

        self.live_data = LiveData()


    def get_counter(self, name: str) -> Optional[int]:
        return self.counters.next_index(name)

     
    def _set_pause_on_danger_fn(self, executable_fn: Callable[[], bool]) -> None:
        self.pause_on_danger_fn = executable_fn
               
    def _reset_pause_on_danger_fn(self) -> None:
        self._set_pause_on_danger_fn(lambda: Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot) or GeneralHelpers.is_party_member_dead())


    def _set_on_follow_path_failed(self, on_follow_path_failed: Callable[[], bool]) -> None:
        self.on_follow_path_failed = on_follow_path_failed
        if self.log_actions:
            ConsoleLog(MODULE_NAME, f"Set OnFollowPathFailed to {on_follow_path_failed}", Py4GW.Console.MessageType.Info)

    def _update_player_data(self) -> None:
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

    def update_player_data(self) -> None:
        self.FSM.AddState(name=f"UpdatePlayerData_{self.get_counter("UPDATE_PLAYER_DATA")}",
                          execute_fn=lambda:self._update_player_data(),)

# Internal decorator factory (class-scope function)
def _yield_step(label: str,counter_key: str):
    def deco(coro_method):
        @wraps(coro_method)
        def wrapper(self:"BottingHelpers", *args, **kwargs):
            step_name = f"{label}_{self.parent.config.get_counter(counter_key)}"
            self.parent.config.FSM.AddYieldRoutineStep(
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

  #region BottingHelpers
class BottingHelpers:
    def __init__(self, parent: "Botting"):
        self.parent = parent
        
    def is_map_loading(self):
        if Map.IsMapLoading():
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
        counter = self.parent.config.get_counter("HEADER_COUNTER")
        self.parent.config.FSM.AddYieldRoutineStep(
            name="[H] " + step_name + f"_[{counter}]",
            coroutine_fn=lambda: Routines.Yield.wait(100)
        )
        
    def _interact_with_agent(self, coords: Tuple[float, float], dialog_id: int = 0):
        result = yield from Routines.Yield.Agents.InteractWithAgentXY(*coords)
        if not result:
            self.on_unmanaged_fail()
            self.parent.config.dialog_at_succeeded._apply(False)
            return False

        if not self.parent.config.fsm_running:
            yield from Routines.Yield.wait(100)
            self.parent.config.dialog_at_succeeded._apply(False)
            return False

        if dialog_id != 0:
            GLOBAL_CACHE.Player.SendDialog(dialog_id)
            yield from Routines.Yield.wait(500)

        self.parent.config.dialog_at_succeeded._apply(True)
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
        while True:
            if not (Routines.Checks.Map.MapValid() and 
                    Routines.Checks.Player.CanAct() and
                    Map.IsExplorable() and
                    not self.parent.config.auto_combat_handler.InCastingRoutine()):
                ActionQueueManager().ResetQueue("ACTION")
                yield from Routines.Yield.wait(100)
            else:
                self.parent.config.auto_combat_handler.HandleCombat()
            yield
            
    # --- minimal helpers ---
    def _alive_explorable(self) -> bool:
        return (Routines.Checks.Map.MapValid()
                and Map.IsExplorable()
                and not GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()))

    def _use_first(self, model_list) -> bool:
        for m in model_list:
            iid = GLOBAL_CACHE.Inventory.GetFirstModelID(m.value)
            if iid:
                GLOBAL_CACHE.Inventory.UseItem(iid)
                return True
        return False

    # --- item lists ---
    ALC_3P = [
        ModelID.Aged_Dwarven_Ale, ModelID.Aged_Hunters_Ale, ModelID.Bottle_Of_Grog,
        ModelID.Flask_Of_Firewater, ModelID.Keg_Of_Aged_Hunters_Ale,
        ModelID.Krytan_Brandy, ModelID.Spiked_Eggnog,
    ]
    ALC_1P = [
        ModelID.Bottle_Of_Rice_Wine, ModelID.Eggnog, ModelID.Dwarven_Ale,
        ModelID.Hard_Apple_Cider, ModelID.Hunters_Ale, ModelID.Bottle_Of_Juniberry_Gin,
        ModelID.Shamrock_Ale, ModelID.Bottle_Of_Vabbian_Wine, ModelID.Vial_Of_Absinthe,
        ModelID.Witchs_Brew, ModelID.Zehtukas_Jug,
    ]

    CITY_10M = [ModelID.Creme_Brulee, ModelID.Jar_Of_Honey, ModelID.Krytan_Lokum]
    CITY_5M  = [ModelID.Chocolate_Bunny, ModelID.Fruitcake, ModelID.Red_Bean_Cake]
    CITY_3M  = [ModelID.Mandragor_Root_Cake]
    CITY_2M  = [ModelID.Delicious_Cake, ModelID.Minitreat_Of_Purity, ModelID.Sugary_Blue_Drink]

    CON_SET = [ModelID.Grail_Of_Might, ModelID.Armor_Of_Salvation, ModelID.Essence_Of_Celerity]

    MORALE_ITEMS = [
        ModelID.Honeycomb, ModelID.Rainbow_Candy_Cane, ModelID.Elixir_Of_Valor,
        ModelID.Pumpkin_Cookie, ModelID.Powerstone_Of_Courage, ModelID.Seal_Of_The_Dragon_Empire,
    ]
    DP_REMOVAL = [
        ModelID.Four_Leaf_Clover, ModelID.Oath_Of_Purity, ModelID.Peppermint_Candy_Cane,
        ModelID.Refined_Jelly, ModelID.Shining_Blade_Ration, ModelID.Wintergreen_Candy_Cane,
    ]
            
    def pop_imp(self):
        while True:
            if ((not Routines.Checks.Map.MapValid()) and (not Map.IsExplorable())):
                return

            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                return

            level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())

            if level >= 20:
                return

            summoning_stone = ModelID.Igneous_Summoning_Stone.value
            stone_id = GLOBAL_CACHE.Inventory.GetFirstModelID(summoning_stone)
            imp_effect_id = 2886
            has_effect = GLOBAL_CACHE.Effects.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), imp_effect_id)

            imp_model_id = 513
            others = GLOBAL_CACHE.Party.GetOthers()
            cast_imp = True  # Assume we should cast

            for other in others:
                if GLOBAL_CACHE.Agent.GetModelID(other) == imp_model_id:
                    if not GLOBAL_CACHE.Agent.IsDead(other):
                        # Imp is alive — no need to cast
                        cast_imp = False
                    break  # Found the imp, no need to keep checking

            if stone_id and not has_effect and cast_imp:
                GLOBAL_CACHE.Inventory.UseItem(stone_id)
                yield from Routines.Yield.wait(500)

    def maintain_cupcake(self):
        while True:
            if ((not Routines.Checks.Map.MapValid()) and (not Map.IsExplorable())):
                yield from Routines.Yield.wait(500)
                continue
            
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(500)
                continue

            cupcake__id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Birthday_Cupcake.value)
            cupcake_effect = GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill")
            
            if not GLOBAL_CACHE.Effects.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), cupcake_effect) and cupcake__id:
                GLOBAL_CACHE.Inventory.UseItem(cupcake__id)
                yield from Routines.Yield.wait(500)
            
    def maintain_honeycomb(self):
        while True:
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(500)
                continue
            
            target_morale = 110
            
            while True:
                morale = GLOBAL_CACHE.Player.GetMorale()
                if morale >= target_morale:
                    yield from Routines.Yield.wait(500)
                    break

                honeycomb_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Honeycomb.value)
                if not honeycomb_id:
                    yield from Routines.Yield.wait(500)
                    break

                GLOBAL_CACHE.Inventory.UseItem(honeycomb_id)
                yield from Routines.Yield.wait(500)
            
    def _maintain_grail(self):
        while True:
            if self.parent.config.use_grail.get():
                if ((not Routines.Checks.Map.MapValid()) and (not Map.IsExplorable())):
                    yield; continue
                if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    yield; continue

                grail_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Grail_Of_Might.value)
                grail_effect = GLOBAL_CACHE.Skill.GetID("Grail_Of_Might_skill")  # correct skill name
                if grail_id and not GLOBAL_CACHE.Effects.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), grail_effect):
                    GLOBAL_CACHE.Inventory.UseItem(grail_id)
                    yield from Routines.Yield.wait(500)
            yield from Routines.Yield.wait(500)


    def _maintain_salvation(self):
        while True:
            if self.parent.config.use_salvation.get():
                if ((not Routines.Checks.Map.MapValid()) and (not Map.IsExplorable())):
                    yield; continue
                if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    yield; continue

                salvation_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Armor_Of_Salvation.value)
                salvation_effect = GLOBAL_CACHE.Skill.GetID("Armor_Of_Salvation_skill")  # correct skill name
                if salvation_id and not GLOBAL_CACHE.Effects.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), salvation_effect):
                    GLOBAL_CACHE.Inventory.UseItem(salvation_id)
                    yield from Routines.Yield.wait(500)
            yield from Routines.Yield.wait(500)


    def _maintain_celerity(self):
        while True:
            if self.parent.config.use_celerity.get():
                if ((not Routines.Checks.Map.MapValid()) and (not Map.IsExplorable())):
                    yield; continue
                if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    yield; continue

                celerity_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Essence_Of_Celerity.value)
                celerity_effect = GLOBAL_CACHE.Skill.GetID("Essence_Of_Celerity_skill")  # correct skill name
                if celerity_id and not GLOBAL_CACHE.Effects.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), celerity_effect):
                    GLOBAL_CACHE.Inventory.UseItem(celerity_id)
                    yield from Routines.Yield.wait(500)
            yield from Routines.Yield.wait(500)

    def _maintain_alcohol(self):
        next_ts = 0.0
        while True:
            # flag gate
            if not self.parent.config.use_alcohol.get():
                yield from Routines.Yield.wait(250); continue

            if not self._alive_explorable():
                next_ts = 0.0; yield; continue

            now = time.time()
            if now < next_ts: yield; continue

            if self._use_first(self.ALC_3P):
                next_ts = now + 180  # 3 minutes
                yield from Routines.Yield.wait(300); continue
            if self._use_first(self.ALC_1P):
                next_ts = now + 60   # 1 minute
                yield from Routines.Yield.wait(300); continue

            yield from Routines.Yield.wait(750)

    def _maintain_city_speed(self):
        next_ts = 0.0
        options = [(self.CITY_10M, 600), (self.CITY_5M, 300), (self.CITY_3M, 180), (self.CITY_2M, 120)]
        while True:
            if not self.parent.config.use_city_speed.get():
                yield from Routines.Yield.wait(250); continue

            # towns/outposts only
            if not Routines.Checks.Map.MapValid() or Map.IsExplorable():
                next_ts = 0.0; yield; continue

            now = time.time()
            if now < next_ts: yield; continue

            used = False
            for group, cd in options:
                if self._use_first(group):
                    next_ts = now + cd
                    used = True
                    break

            yield from Routines.Yield.wait(300 if used else 750)

    def _maintain_consets(self):
        next_ts = 0.0
        while True:
            if not self.parent.config.use_consets.get():
                yield from Routines.Yield.wait(250); continue

            if not self._alive_explorable():
                next_ts = 0.0; yield; continue

            now = time.time()
            if now < next_ts: yield; continue

            if self._use_first(self.CON_SET):
                next_ts = now + 1800  # 30 minutes
                yield from Routines.Yield.wait(300); continue

            yield from Routines.Yield.wait(750)

    def _maintain_morale(self, target=110):
        while True:
            if not self.parent.config.use_morale.get():
                yield from Routines.Yield.wait(250); continue

            if not self._alive_explorable():
                yield; continue

            if GLOBAL_CACHE.Player.GetMorale() >= target:
                yield; continue

            if self._use_first(self.MORALE_ITEMS):
                yield from Routines.Yield.wait(500); continue

            yield from Routines.Yield.wait(750)

    def _maintain_dp_removal(self, target=100):
        while True:
            if not self.parent.config.use_dp_removal.get():
                yield from Routines.Yield.wait(250); continue

            if not self._alive_explorable():
                yield; continue

            if GLOBAL_CACHE.Player.GetMorale() >= target:
                yield; continue

            if self._use_first(self.DP_REMOVAL):
                yield from Routines.Yield.wait(500); continue

            yield from Routines.Yield.wait(750)         

            
    #FSM Maintained Steps

    @_fsm_step("PopImp","IMP_COUNTER")
    def add_pop_imp(self):
        pop_imp = self.pop_imp()
        if pop_imp not in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.append(pop_imp)

    @_fsm_step("RemovePopImp","IMP_COUNTER")
    def remove_pop_imp(self):
        pop_imp = self.pop_imp()
        if pop_imp in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(pop_imp)

    @_fsm_step("MaintainCupcake","CUPCAKES_COUNTER")
    def add_maintain_cupcake(self):
        maintain_cupcake = self.maintain_cupcake()
        if maintain_cupcake not in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.append(maintain_cupcake)

    @_fsm_step("RemoveMaintainCupcake", "CUPCAKES_COUNTER")
    def remove_maintain_cupcake(self):
        maintain_cupcake = self.maintain_cupcake()
        if maintain_cupcake in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(maintain_cupcake)

    @_fsm_step("MaintainHoneycomb","HONEYCOMBS_COUNTER")
    def add_maintain_honeycomb(self):
        maintain_honeycomb = self.maintain_honeycomb()
        if maintain_honeycomb not in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.append(maintain_honeycomb)

    @_fsm_step("RemoveMaintainHoneycomb", "HONEYCOMBS_COUNTER")
    def remove_maintain_honeycomb(self):
        maintain_honeycomb = self.maintain_honeycomb()
        if maintain_honeycomb in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(maintain_honeycomb)
            
    @_fsm_step("StartAutoCombat", "AUTO_COMBAT")
    def start_auto_combat(self):
        autocombat = self.auto_combat()                 # generator
        if autocombat not in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.append(autocombat)      # register it
    
    @_fsm_step("StopAutoCombat", "AUTO_COMBAT")
    def stop_auto_combat(self):
        autocombat = self.auto_combat()
        if autocombat in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(autocombat)
            
    @fsm_step("MaintainAlcohol", "ALCOHOL_COUNTER")  # counter key can be new; reused for brevity
    def add_maintain_alcohol(self):
        gen = self._maintain_alcohol()
        GLOBAL_CACHE.Coroutines.append(gen)

    @fsm_step("RemoveMaintainAlcohol", "ALCOHOL_COUNTER")
    def remove_maintain_alcohol(self):
        gen = self._maintain_alcohol()
        if gen in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(gen)

    @fsm_step("MaintainCitySpeed", "CITY_SPEED_COUNTER")
    def add_maintain_city_speed(self):
        gen = self._maintain_city_speed()
        GLOBAL_CACHE.Coroutines.append(gen)

    @fsm_step("RemoveMaintainCitySpeed", "CITY_SPEED_COUNTER")
    def remove_maintain_city_speed(self):
        gen = self._maintain_city_speed()
        if gen in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(gen)

    @fsm_step("MaintainConSets", "CONSETS_COUNTER")
    def add_maintain_consets(self):
        gen = self._maintain_consets()
        GLOBAL_CACHE.Coroutines.append(gen)

    @fsm_step("RemoveMaintainConSets", "CONSETS_COUNTER")
    def remove_maintain_consets(self):
        gen = self._maintain_consets()
        if gen in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(gen)

    @fsm_step("MaintainGrail", "GRAIL_COUNTER")
    def add_maintain_grail(self):
        GLOBAL_CACHE.Coroutines.append(self._maintain_grail())

    @fsm_step("RemoveMaintainGrail", "GRAIL_COUNTER")
    def remove_maintain_grail(self):
        gen = self._maintain_grail()
        if gen in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(gen)


    @fsm_step("MaintainSalvation", "SALVATION_COUNTER")
    def add_maintain_salvation(self):
        if self.parent.config.use_salvation.get():
            GLOBAL_CACHE.Coroutines.append(self._maintain_salvation())

    @fsm_step("RemoveMaintainSalvation", "SALVATION_COUNTER")
    def remove_maintain_salvation(self):
        gen = self._maintain_salvation()
        if gen in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(gen)


    @fsm_step("MaintainCelerity", "CELERITY_COUNTER")
    def add_maintain_celerity(self):
        if self.parent.config.use_celerity.get():
            GLOBAL_CACHE.Coroutines.append(self._maintain_celerity())

    @fsm_step("RemoveMaintainCelerity", "CELERITY_COUNTER")
    def remove_maintain_celerity(self):
        gen = self._maintain_celerity()
        if gen in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(gen)


    @fsm_step("MaintainMorale", "MORALE_COUNTER")
    def add_maintain_morale(self):
        if self.parent.config.use_morale.get():  # Assuming you added a morale flag
            GLOBAL_CACHE.Coroutines.append(self._maintain_morale())

    @fsm_step("RemoveMaintainMorale", "MORALE_COUNTER")
    def remove_maintain_morale(self):
        gen = self._maintain_morale()
        if gen in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(gen)

    @fsm_step("MaintainDPRemoval", "DP_REMOVAL_COUNTER")
    def add_maintain_dp_removal(self):
        gen = self._maintain_dp_removal()
        GLOBAL_CACHE.Coroutines.append(gen)

    @fsm_step("RemoveMaintainDPRemoval", "DP_REMOVAL_COUNTER")
    def remove_maintain_dp_removal(self):
        gen = self._maintain_dp_removal()
        if gen in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(gen)


    #Yield Steps

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
        Map.Travel(target_map_id)
        yield from Routines.Yield.wait(1000)

    @_yield_step(label="FollowPath", counter_key="FOLLOW_PATH")
    def follow_path(self) -> Generator[Any, Any, bool]:
        
        path = self.parent.config.path
        exit_condition = lambda: GeneralHelpers.is_player_dead() or self.is_map_loading() if self.parent.config.halt_on_death.get() else self.is_map_loading()
        pause_condition = self.parent.config.pause_on_danger_fn if self.parent.config.pause_on_danger.get() else None

        success_movement = yield from Routines.Yield.Movement.FollowPath(
            path_points=path,
            custom_exit_condition=exit_condition,
            log=self.parent.config.log_actions.get(),
            custom_pause_fn=pause_condition,
            timeout=self.parent.config.movement_timeout.get(),
            tolerance=self.parent.config.movement_tolerance.get(),
        )

        self.parent.config.follow_path_succeeded._apply(success_movement)
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
        Map.EnterChallenge()
        yield from Routines.Yield.wait(wait_for)

    @_yield_step(label="CancelSkillRewardWindow", counter_key="CANCEL_SKILL_REWARD_WINDOW")
    def cancel_skill_reward_window(self):
        global bot  
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

        item_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
        if item_in_storage < quantity:
            Py4GW.Console.Log(MODULE_NAME, f"Not enough items ({quantity}) to withdraw.", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return False

        items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, quantity)
        yield from Routines.Yield.wait(500)
        if not items_withdrawn:
            Py4GW.Console.Log(MODULE_NAME, f"Failed to withdraw ({quantity}) items from storage.", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return False

        return True

    @_yield_step(label="CraftItem", counter_key="CRAFT_ITEM")
    def craft_item(self, output_model_id: int, count: int,
                trade_model_ids: list[int], quantity_list: list[int]):
        # Align lists (no exceptions; clamp to shortest)
        k = min(len(trade_model_ids), len(quantity_list))
        if k == 0:
            return
        trade_model_ids = trade_model_ids[:k]
        quantity_list   = quantity_list[:k]

        # Resolve each model -> first matching item in inventory
        trade_item_ids: list[int] = []
        for m in trade_model_ids:
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(m)
            trade_item_ids.append(item_id or 0)

        # Bail if any required item is missing
        if any(i == 0 for i in trade_item_ids):
            return

        # Find the crafter’s offered item that matches the desired output model
        target_item_id = 0
        for offered_item_id in GLOBAL_CACHE.Trading.Merchant.GetOfferedItems():
            if GLOBAL_CACHE.Item.GetModelID(offered_item_id) == output_model_id:
                target_item_id = offered_item_id
                break
        if target_item_id == 0:
            return

        # Craft, then give a short yield
        GLOBAL_CACHE.Trading.Crafter.CraftItem(target_item_id, count, trade_item_ids, quantity_list)
        yield from Routines.Yield.wait(500)

    @_yield_step(label="EquipItem", counter_key="EQUIP_ITEM")
    def equip_item(self, model_id: int):
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if item_id:
            GLOBAL_CACHE.Inventory.EquipItem(item_id, GLOBAL_CACHE.Player.GetAgentID())
            yield from Routines.Yield.wait(500)
        else:
            Py4GW.Console.Log(MODULE_NAME, "Crafted weapon not found in inventory.", Py4GW.Console.MessageType.Error)
            bot.helpers.on_unmanaged_fail()
            return

    @_yield_step(label="LeaveParty", counter_key="LEAVE_PARTY")
    def leave_party(self):
        GLOBAL_CACHE.Party.LeaveParty()
        yield from Routines.Yield.wait(500)

    @_yield_step(label="SpawnBonusItems", counter_key="SPAWN_BONUS")
    def spawn_bonus_items(self):
        summoning_stone_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Igneous_Summoning_Stone.value)
        if summoning_stone_in_bags < 1:
            GLOBAL_CACHE.Player.SendChatCommand("bonus")
            yield from Routines.Yield.wait(250)


#region Botting
class Botting:
    def __init__(self, bot_name="DefaultBot"):
        self.bot_name = bot_name
        self.helpers = BottingHelpers(self)
        self.config = BotConfig(self, bot_name)
        
    def SetProperty(self, name: str, value: Any) -> bool:
        prop = getattr(self.config, name, None)
        if not isinstance(prop, BotProperty):
            return False
        prop.set(value)  # schedules FSM step; no direct mutation
        return True

    def GetProperty(self, name: str) -> Any | None:
        prop = getattr(self.config, name, None)
        if not isinstance(prop, BotProperty):
            return None
        return prop.get()

    def AddHeaderStep(self, step_name: str) -> None:
        self.helpers.insert_header_step(step_name)

    def Routine(self):
        pass

    def Start(self):
        self.config.FSM.start()
        self.config.fsm_running = True

    def Stop(self):
        self.config.fsm_running = False
        self.config.FSM.stop()

    def Update(self):
        if not self.config.initialized:
            self.Routine()
            self.config.initialized = True

        if self.config.fsm_running:
            self.config.FSM.update()
            self.config.live_data.update()

    def WasteTime(self, duration: int= 100) -> None:
        self.helpers.waste_time(duration)

    def WasteTimeUntilConditionMet(self, condition: Callable[[], bool], duration: int=1000) -> None:
        self.helpers.waste_time_until_condition_met(condition, duration)

    def AddFSMCustomYieldState(self, execute_fn, name: str) -> None:
        step_name = f"{name}_{self.config.get_counter("CUSTOM_STEP")}"
        self.config.FSM.AddYieldRoutineStep(name=step_name, coroutine_fn=execute_fn)

    def Travel(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        if target_map_name:
            target_map_id = Map.GetMapIDByName(target_map_name)

        self.helpers.travel(target_map_id)

    def MoveTo(self, x:float, y:float, step_name: str=""):
        if step_name == "":
            step_name = f"MoveTo_{self.config.get_counter("MOVE_TO")}"

        self.helpers.insert_header_step(step_name)
        self.helpers.get_path_to(x, y)
        self.helpers.follow_path()

    def FollowPath(self, path: List[Tuple[float, float]], step_name: str="") -> None:
        if step_name == "":
            step_name = f"FollowPath_{self.config.get_counter("FOLLOW_PATH")}"

        self.helpers.insert_header_step(step_name)
        self.helpers.set_path_to(path)
        self.helpers.follow_path()
        
    def DrawPath(self, color:Color=Color(255, 255, 0, 255)) -> None:
        if self.config.draw_path:
            self.helpers.draw_path(color)

    def DialogAt(self, x: float, y: float, dialog:int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"DialogAt_{self.config.get_counter("DIALOG_AT")}"

        self.helpers.insert_header_step(step_name)
        self.helpers.interact_with_agent((x, y), dialog_id=dialog)
        
    def DialogWithModel(self, model_id: int, dialog:int, step_name: str="") -> None:
        if step_name == "":
            step_name = f"DialogWithModel_{self.config.get_counter("DIALOG_AT")}"

        self.helpers.insert_header_step(step_name)
        self.helpers.interact_with_model(model_id=model_id, dialog_id=dialog)

    def InteractAt(self, x: float, y: float, step_name: str="") -> None:
        self.helpers.insert_header_step(step_name)
        self.helpers.interact_with_agent((x, y))
        
    def InteractWithModel(self, model_id: int, step_name: str="") -> None:
        self.helpers.insert_header_step(step_name)
        self.helpers.interact_with_model(model_id=model_id)

    def WaitForMapLoad(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        if target_map_name:
            target_map_id = Map.GetMapIDByName(target_map_name)
            
        self.helpers.wait_for_map_load(target_map_id)

    def EnterChallenge(self, wait_for:int= 4500):
        self.helpers.enter_challenge(wait_for=wait_for)
        
    def StartAutoCombat(self):
        self.helpers.start_auto_combat()

    def StopAutoCombat(self):
        self.helpers.stop_auto_combat()

    def AddPopImpRoutine(self):
        self.helpers.add_pop_imp()

    def RemovePopImpRoutine(self):
        self.helpers.remove_pop_imp()
        
    def AddMaintainCupcakeRoutine(self):
        self.helpers.add_maintain_cupcake()

    def RemoveMaintainCupcakeRoutine(self):
        self.helpers.remove_maintain_cupcake()

    def AddMaintainHoneycombRoutine(self):
        self.helpers.add_maintain_honeycomb()

    def RemoveMaintainHoneycombRoutine(self):
        self.helpers.remove_maintain_honeycomb()
        
    def AddMaintainAlcoholRoutine(self):        
        self.helpers.add_maintain_alcohol()

    def RemoveMaintainAlcoholRoutine(self):     
        self.helpers.remove_maintain_alcohol()

    def AddMaintainCitySpeedRoutine(self):      
        self.helpers.add_maintain_city_speed()

    def RemoveMaintainCitySpeedRoutine(self):   
        self.helpers.remove_maintain_city_speed()

    def AddMaintainConSetsRoutine(self):        
        self.helpers.add_maintain_consets()

    def RemoveMaintainConSetsRoutine(self):     
        self.helpers.remove_maintain_consets()

    def AddMaintainMoraleRoutine(self):         
        self.helpers.add_maintain_morale()

    def RemoveMaintainMoraleRoutine(self):      
        self.helpers.remove_maintain_morale()

    def AddMaintainDPRemovalRoutine(self):      
        self.helpers.add_maintain_dp_removal()

    def RemoveMaintainDPRemovalRoutine(self):   
        self.helpers.remove_maintain_dp_removal()

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
        
        
# ----------------------- BOT CONFIGURATION --------------------------------------------
#region BotConfig

bot = Botting("cupcake_bot")

#region bot_helpers

SCRIPT_RUNNING = False

def create_bot_routine(bot: Botting) -> None:
    global SCRIPT_RUNNING
    bot.AddMaintainCupcakeRoutine()
    exit_fn = lambda: (SCRIPT_RUNNING == False)
    bot.WasteTimeUntilConditionMet(exit_fn)
    bot.RemoveMaintainCupcakeRoutine()

bot.Routine = create_bot_routine.__get__(bot)
    

selected_step = 0
def main():
    global SCRIPT_RUNNING, selected_step
    try:
        bot.Update()
        
        if PyImGui.begin("Cupcake test", PyImGui.WindowFlags.AlwaysAutoResize):
            
            if PyImGui.button("Start Botting"):
                SCRIPT_RUNNING = True
                bot.Start()

            if PyImGui.button("Stop Botting"):
                SCRIPT_RUNNING = False
                bot.Stop()
                
            PyImGui.separator()
            
            fsm_steps = bot.config.FSM.get_state_names()
            selected_step = PyImGui.combo("FSM Steps",selected_step,  fsm_steps)
            if PyImGui.button("start at Step"):
                if selected_step < len(fsm_steps):
                    bot.config.fsm_running = True
                    bot.config.FSM.reset()
                    bot.config.FSM.jump_to_state_by_name(fsm_steps[selected_step])
                
            PyImGui.separator()
        PyImGui.end()


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()

from __future__ import annotations
from typing import Callable, Optional, List, Tuple, Any


from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..Botting import BottingClass  # for type checkers only
    
from ..SkillManager import SkillManager
from ..Py4GWcorelib import FSM
from ..BuildMgr import BuildMgr
from ..Builds import AutoCombat
from .property import StepNameCounters, UpkeepData, ConfigProperties
from .event import Events
    

class BotConfig:
    def __init__(self, parent: "BottingClass",  bot_name: str,
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
                 #A
                 alcohol_active: bool = False,
                 alcohol_target_drunk_level: int = 2,
                 alcohol_disable_visual: bool = True,
                 armor_of_salvation_active: bool = False,
                 armor_of_salvation_restock: int = 0,
                 auto_combat_active: bool = False,
                 auto_inventory_management_active: bool = False,
                 auto_loot_active: bool = False,
                 #B
                 birthday_cupcake_active: bool = False,
                 birthday_cupcake_restock: int = 0,
                 blue_rock_candy_active: bool = False,
                 blue_rock_candy_restock: int = 0,
                 bowl_of_skalefin_soup_active: bool = False,
                 bowl_of_skalefin_soup_restock: int = 0,
                 #C
                 candy_apple_active: bool = False,
                 candy_apple_restock: int = 0,
                 candy_corn_active: bool = False,
                 candy_corn_restock: int = 0,
                 city_speed_active: bool = False,
                 #D
                 drake_kabob_active: bool = False,
                 drake_kabob_restock: int = 0,
                 #E
                 essence_of_celerity_active: bool = False,
                 essence_of_celerity_restock: int = 0,
                 #F
                 four_leaf_clover_active: bool = False,
                 four_leaf_clover_restock: int = 0,
                 #G
                 golden_egg_active: bool = False,
                 golden_egg_restock: int = 0,
                 grail_of_might_active: bool = False,
                 grail_of_might_restock: int = 0,
                 green_rock_candy_active: bool = False,
                 green_rock_candy_restock: int = 0,
                 #H
                 hero_ai_active: bool = False,
                 honeycomb_active: bool = False,
                 honeycomb_restock: int = 0,
                 #I
                 imp_active: bool = False,
                 #L
                 leave_empty_inventory_slots: int = 0,
                 #M
                 morale_active:bool = False,
                 morale_target_level: int = 110,
                 #P
                 pahnai_salad_active: bool = False,
                 pahnai_salad_restock: int = 0,
                 #R
                 red_rock_candy_active: bool = False,
                 red_rock_candy_restock: int = 0,
                 #S
                 slice_of_pumpkin_pie_active: bool = False,
                 slice_of_pumpkin_pie_restock: int = 0,
                 #W
                 war_supplies_active: bool = False,
                 war_supplies_restock: int = 0,
                 #merchants
                 identify_kits_active: bool = False,
                 identify_kits_restock: int = 2,
                 salvage_kits_active: bool = False,
                 salvage_kits_restock: int = 4,
                 
                 
                 custom_build: Optional[BuildMgr] = None
                 ):
        self.parent:"BottingClass" = parent
        self.bot_name:str = bot_name
        self.initialized:bool = False
        self.FSM = FSM(bot_name)
        self.fsm_running:bool = False
        self.state_description: str = "Idle"
        self.state_percentage: float = 0.0
        #self.build_handler:SkillManager.Autocombat = SkillManager.Autocombat()
        if custom_build is not None:
            self.build_handler:BuildMgr = custom_build
        else:
            self.build_handler:BuildMgr = AutoCombat()

        self.counters = StepNameCounters()
        
        self.path:List[Tuple[float, float]] = []
        self.path_to_draw:List[Tuple[float, float]] = []
        
        #Overridable functions
        self.pause_on_danger_fn: Callable[[], bool] = lambda: False
        self._reset_pause_on_danger_fn()
        self.on_follow_path_failed: Callable[[], bool] = lambda: False
        
        #Properties
        self.config_properties = ConfigProperties(self,
                                                  log_actions=config_log_actions,
                                                  halt_on_death=config_halt_on_death,
                                                  pause_on_danger=config_pause_on_danger,
                                                  movement_timeout=config_movement_timeout,
                                                  movement_tolerance=config_movement_tolerance,
                                                  draw_path=config_draw_path,
                                                  use_occlusion=config_use_occlusion,
                                                  snap_to_ground=config_snap_to_ground,
                                                  snap_to_ground_segments=config_snap_to_ground_segments,
                                                  floor_offset=config_floor_offset,
                                                  follow_path_color=config_follow_path_color
                                                  )

        self.upkeep = UpkeepData(self, 
                #A
                 alcohol_active=alcohol_active,
                 alcohol_target_drunk_level=alcohol_target_drunk_level,
                 alcohol_disable_visual=alcohol_disable_visual,
                 armor_of_salvation_active=armor_of_salvation_active,
                 armor_of_salvation_restock=armor_of_salvation_restock,
                 auto_combat_active=auto_combat_active,
                 auto_inventory_management_active=auto_inventory_management_active,
                 auto_loot_active=auto_loot_active,
                #B
                 birthday_cupcake_active=birthday_cupcake_active,
                 birthday_cupcake_restock=birthday_cupcake_restock,
                 blue_rock_candy_active=blue_rock_candy_active,
                 blue_rock_candy_restock=blue_rock_candy_restock,
                 bowl_of_skalefin_soup_active=bowl_of_skalefin_soup_active,
                 bowl_of_skalefin_soup_restock=bowl_of_skalefin_soup_restock,
                    #C
                 candy_apple_active=candy_apple_active,
                 candy_apple_restock=candy_apple_restock,
                 candy_corn_active=candy_corn_active,
                 candy_corn_restock=candy_corn_restock,
                 city_speed_active=city_speed_active,
                    #D
                 drake_kabob_active=drake_kabob_active,
                 drake_kabob_restock=drake_kabob_restock,
                    #E
                 essence_of_celerity_active=essence_of_celerity_active,
                 essence_of_celerity_restock=essence_of_celerity_restock,
                    #F
                 four_leaf_clover_active=four_leaf_clover_active,
                 four_leaf_clover_restock=four_leaf_clover_restock,
                    #G
                 golden_egg_active=golden_egg_active,
                 golden_egg_restock=golden_egg_restock,
                 grail_of_might_active=grail_of_might_active,
                 grail_of_might_restock=grail_of_might_restock,
                 green_rock_candy_active=green_rock_candy_active,
                 green_rock_candy_restock=green_rock_candy_restock,
                    #H
                 hero_ai_active=hero_ai_active,
                 honeycomb_active=honeycomb_active,
                 honeycomb_restock=honeycomb_restock,
                    #I
                 imp_active=imp_active,
                    #L
                 leave_empty_inventory_slots=leave_empty_inventory_slots,
                    #M
                 morale_active=morale_active,
                 morale_target_level=morale_target_level,
                    #P
                 pahnai_salad_active=pahnai_salad_active,
                 pahnai_salad_restock=pahnai_salad_restock,
                    #R
                 red_rock_candy_active=red_rock_candy_active,
                 red_rock_candy_restock=red_rock_candy_restock,
                    #S
                 slice_of_pumpkin_pie_active=slice_of_pumpkin_pie_active,
                 slice_of_pumpkin_pie_restock=slice_of_pumpkin_pie_restock,
                    #W
                 war_supplies_active=war_supplies_active,
                 war_supplies_restock=war_supplies_restock,
                    #merchants
                 identify_kits_active=identify_kits_active,
                 identify_kits_restock=identify_kits_restock,
                 salvage_kits_active=salvage_kits_active,
                 salvage_kits_restock=salvage_kits_restock,
                    )
        self.events = Events(self)



    def get_counter(self, name: str) -> Optional[int]:
        return self.counters.next_index(name)
   
    def _set_pause_on_danger_fn(self, executable_fn: Callable[[], bool]) -> None:
        self.pause_on_danger_fn = executable_fn
               
    def _reset_pause_on_danger_fn(self) -> None:
        from ..Routines import Checks  # local import to avoid cycles
        from ..enums_src.GameData_enums import Range

        self._set_pause_on_danger_fn(lambda: Checks.Agents.InDanger(aggro_area=Range.Earshot) or Checks.Party.IsPartyMemberDead() or Checks.Skills.InCastingProcess())

    def _set_on_follow_path_failed(self, on_follow_path_failed: Callable[[], bool]) -> None:
        from ..Py4GWcorelib import ConsoleLog
        import Py4GW
        self.on_follow_path_failed = on_follow_path_failed
        if self.config_properties.log_actions.is_active():
            ConsoleLog("OnFollowPathFailed", f"Set OnFollowPathFailed to {on_follow_path_failed}", Py4GW.Console.MessageType.Info)


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
        self.set_on_follow_path_failed(lambda: self.parent.helpers.Events.default_on_unmanaged_fail())


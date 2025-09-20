
from typing import Any,Callable,Optional

from .botting_src.helpers import BottingHelpers
from .botting_src.config import BotConfig
from .BuildMgr import BuildMgr

from .botting_src.subclases_src.STATES_src import _STATES
from .botting_src.subclases_src.DIALOGS_src import _DIALOGS
from .botting_src.subclases_src.EVENTS_src import _EVENTS
from .botting_src.subclases_src.INTERACT_src import _INTERACT
from .botting_src.subclases_src.ITEMS_src import _ITEMS
from .botting_src.subclases_src.MAP_src import _MAP
from .botting_src.subclases_src.MOVE_src import _MOVE
from .botting_src.subclases_src.PROPERTIES_src import _PROPERTIES
from .botting_src.subclases_src.PARTY_src import _PARTY
from .botting_src.subclases_src.SKILLBAR_src import _SKILLBAR
from .botting_src.subclases_src.TARGET_src import _TARGET
from .botting_src.subclases_src.WAIT_src import _WAIT
from .botting_src.subclases_src.UI_src import _UI
from .botting_src.subclases_src.MULTIBOX_src import _MULTIBOX
from .botting_src.subclases_src.MERCHANT_src import _MERCHANTS
from .botting_src.subclases_src.PLAYER_src import _PLAYER
from .botting_src.subclases_src.CONFIG_TEMPLATES_src import _CONFIG_TEMPLATES


class BottingClass:
    def __init__(self, bot_name="DefaultBot",
                 #CONFIG
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
                 custom_build: Optional[BuildMgr] = None,
                 #UPKEEP
                 #A
                 upkeep_alcohol_active: bool = False,
                 upkeep_alcohol_target_drunk_level: int = 2,
                 upkeep_alcohol_disable_visual: bool = True,
                 upkeep_armor_of_salvation_active: bool = False,
                 upkeep_armor_of_salvation_restock: int = 0,
                 upkeep_auto_combat_active: bool = False,
                 upkeep_auto_inventory_management_active = False,
                 upkeep_auto_loot_active = False,
                 #B
                 upkeep_birthday_cupcake_active: bool = False,
                 upkeep_birthday_cupcake_restock: int = 0,
                 upkeep_blue_rock_candy_active: bool = False,
                 upkeep_blue_rock_candy_restock: int = 0,
                 upkeep_bowl_of_skalefin_soup_active: bool = False,
                 upkeep_bowl_of_skalefin_soup_restock: int = 0,
                 #C
                 upkeep_candy_apple_active: bool = False,
                 upkeep_candy_apple_restock: int = 0,
                 upkeep_candy_corn_active: bool = False,
                 upkeep_candy_corn_restock: int = 0,
                 upkeep_city_speed_active: bool = False,
                 #D
                 upkeep_drake_kabob_active: bool = False,
                 upkeep_drake_kabob_restock: int = 0,
                 #E
                 upkeep_essence_of_celerity_active: bool = False,
                 upkeep_essence_of_celerity_restock: int = 0,
                 #F
                 upkeep_four_leaf_clover_active: bool = False,
                 upkeep_four_leaf_clover_restock: int = 0,
                 #G
                 upkeep_golden_egg_active: bool = False,
                 upkeep_golden_egg_restock: int = 0,
                 upkeep_grail_of_might_active: bool = False,
                 upkeep_grail_of_might_restock: int = 0,
                 upkeep_green_rock_candy_active: bool = False,
                 upkeep_green_rock_candy_restock: int = 0,
                 #H
                 upkeep_hero_ai_active: bool = False,
                 upkeep_honeycomb_active: bool = False,
                 upkeep_honeycomb_restock: int = 0,
                 #I
                 upkeep_imp_active: bool = False,
                 #L
                 leave_empty_inventory_slots: int = 0,
                 #M
                 upkeep_morale_active:bool = False,
                 upkeep_morale_target_level: int = 110,
                 #P
                 upkeep_pahnai_salad_active: bool = False,
                 upkeep_pahnai_salad_restock: int = 0,
                 #R
                 upkeep_red_rock_candy_active: bool = False,
                 upkeep_red_rock_candy_restock: int = 0,
                 #S
                 upkeep_slice_of_pumpkin_pie_active: bool = False,
                 upkeep_slice_of_pumpkin_pie_restock: int = 0,
                 #W
                 upkeep_war_supplies_active: bool = False,
                 upkeep_war_supplies_restock: int = 0,
                    #merchants
                 upkeep_identify_kits_active: bool = False,
                 upkeep_identify_kits_restock: int = 2,
                 upkeep_salvage_kits_active: bool = False,
                 upkeep_salvage_kits_restock: int = 4,
                 ):
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
                                custom_build=custom_build,
                                #UPKEEP
                                #A
                                alcohol_active=upkeep_alcohol_active,
                                alcohol_target_drunk_level=upkeep_alcohol_target_drunk_level,
                                alcohol_disable_visual=upkeep_alcohol_disable_visual,
                                armor_of_salvation_active=upkeep_armor_of_salvation_active,
                                armor_of_salvation_restock=upkeep_armor_of_salvation_restock,
                                auto_combat_active=upkeep_auto_combat_active,
                                auto_inventory_management_active=upkeep_auto_inventory_management_active,
                                auto_loot_active=upkeep_auto_loot_active,
                                #B
                                birthday_cupcake_active=upkeep_birthday_cupcake_active,
                                birthday_cupcake_restock=upkeep_birthday_cupcake_restock,
                                blue_rock_candy_active=upkeep_blue_rock_candy_active,
                                blue_rock_candy_restock=upkeep_blue_rock_candy_restock,
                                bowl_of_skalefin_soup_active=upkeep_bowl_of_skalefin_soup_active,
                                bowl_of_skalefin_soup_restock=upkeep_bowl_of_skalefin_soup_restock,
                                #C
                                candy_apple_active=upkeep_candy_apple_active,
                                candy_apple_restock=upkeep_candy_apple_restock,
                                candy_corn_active=upkeep_candy_corn_active,
                                candy_corn_restock=upkeep_candy_corn_restock,
                                city_speed_active=upkeep_city_speed_active,
                                #D
                                drake_kabob_active=upkeep_drake_kabob_active,
                                drake_kabob_restock=upkeep_drake_kabob_restock,
                                #E
                                essence_of_celerity_active=upkeep_essence_of_celerity_active,
                                essence_of_celerity_restock=upkeep_essence_of_celerity_restock,
                                #F
                                four_leaf_clover_active=upkeep_four_leaf_clover_active,
                                four_leaf_clover_restock=upkeep_four_leaf_clover_restock,
                                #G
                                golden_egg_active=upkeep_golden_egg_active,
                                golden_egg_restock=upkeep_golden_egg_restock,
                                grail_of_might_active=upkeep_grail_of_might_active,
                                grail_of_might_restock=upkeep_grail_of_might_restock,
                                green_rock_candy_active=upkeep_green_rock_candy_active,
                                green_rock_candy_restock=upkeep_green_rock_candy_restock,
                                #H
                                hero_ai_active=upkeep_hero_ai_active,
                                honeycomb_active=upkeep_honeycomb_active,
                                honeycomb_restock=upkeep_honeycomb_restock,
                                #I
                                imp_active=upkeep_imp_active,
                                #L
                                leave_empty_inventory_slots=leave_empty_inventory_slots,
                                #M
                                morale_active=upkeep_morale_active,
                                morale_target_level=upkeep_morale_target_level,
                                #P
                                pahnai_salad_active=upkeep_pahnai_salad_active,
                                pahnai_salad_restock=upkeep_pahnai_salad_restock,
                                #R
                                red_rock_candy_active=upkeep_red_rock_candy_active,
                                red_rock_candy_restock=upkeep_red_rock_candy_restock,
                                #S
                                slice_of_pumpkin_pie_active=upkeep_slice_of_pumpkin_pie_active,
                                slice_of_pumpkin_pie_restock=upkeep_slice_of_pumpkin_pie_restock,
                                #W
                                war_supplies_active=upkeep_war_supplies_active,
                                war_supplies_restock=upkeep_war_supplies_restock,
                                #merchants
                                identify_kits_active=upkeep_identify_kits_active,
                                identify_kits_restock=upkeep_identify_kits_restock,
                                salvage_kits_active=upkeep_salvage_kits_active,
                                salvage_kits_restock=upkeep_salvage_kits_restock
                                )

        self.helpers = BottingHelpers(self)
        #region SubClasses
        self.States = _STATES(self)
        self.Properties = _PROPERTIES(self)
        self.UI = _UI(self)
        self.Items = _ITEMS(self)
        self.Merchant = _MERCHANTS(self)
        self.Dialogs = _DIALOGS(self)
        self.Wait = _WAIT(self)
        self.Move = _MOVE(self)
        self.Map = _MAP(self)
        self.Interact = _INTERACT(self)
        self.Party = _PARTY(self)
        self.Player = _PLAYER(self)
        self.Events = _EVENTS(self)
        self.Target = _TARGET(self)
        self.SkillBar = _SKILLBAR(self)
        self.Multibox = _MULTIBOX(self)
        self.ConfigTemplates = _CONFIG_TEMPLATES(self)

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
        self.config.FSM.AddManagedCoroutine("keep_hero_ai",        H.upkeep_hero_ai())
        self.config.FSM.AddManagedCoroutine("keep_auto_inventory_management", H.upkeep_auto_inventory_management())
        #self.config.FSM.AddManagedCoroutine("keep_auto_loot",      H.upkeep_auto_loot())
        self.config.events.start()

        """if self.States.coroutines:
            for name, routine_or_fn in list(self.States.coroutines.items()):
                self.config.FSM.AddManagedCoroutine(name, routine_or_fn)"""

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

    def OverrideBuild(self, build: BuildMgr) -> None:
        self.config.build_handler = build


    

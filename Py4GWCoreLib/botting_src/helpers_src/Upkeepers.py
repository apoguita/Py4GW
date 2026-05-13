from functools import wraps
from typing import TYPE_CHECKING

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib import ConsoleLog, Console, Agent, Player
from Py4GWCoreLib.Item import (
    has_active_party_summon,
    has_summoning_sickness,
)

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable

#region UPKEEPERS
class _Upkeepers:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
        self.cancel_movement_triggered = False
        self._hero_ai_pause_applied = False
        self._hero_ai_pause_snapshot = None
        self._hero_ai_legacy_range_override_applied = False
        
    
    def upkeep_hero_ai(self):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        from HeroAI.settings import Settings
        from Py4GW_widget_manager import get_widget_handler
        handler = get_widget_handler()

        def set_botting_range_mode(active: bool) -> None:
            if active:
                if not self._hero_ai_legacy_range_override_applied:
                    Settings().set_runtime_combat_range_mode_override(Settings.COMBAT_RANGE_MODE_LEGACY)
                    self._hero_ai_legacy_range_override_applied = True
            elif self._hero_ai_legacy_range_override_applied:
                Settings().set_runtime_combat_range_mode_override(None)
                self._hero_ai_legacy_range_override_applied = False

        while True:   
            pause_requested = bool(getattr(self._config.upkeep, "hero_ai_paused", None) and self._config.upkeep.hero_ai_paused.is_active())

            if pause_requested:
                account_email = Player.GetAccountEmail()
                current_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email) if account_email else None
                if current_options and not self._hero_ai_pause_applied:
                    self._hero_ai_pause_snapshot = (
                        current_options.Following,
                        current_options.Targeting,
                        current_options.Combat,
                    )
                    current_options.Following = False
                    current_options.Targeting = False
                    current_options.Combat = False
                    GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, current_options)
                    self._hero_ai_pause_applied = True

                # If an interaction started while moving, stop once and let it settle.
                if Agent.IsMoving(Player.GetAgentID()) and not self.cancel_movement_triggered:
                    yield from Routines.Yield.Movement.StopMovement()
                    self.cancel_movement_triggered = True

                yield from Routines.Yield.wait(200)
                continue
            elif self._hero_ai_pause_applied:
                account_email = Player.GetAccountEmail()
                current_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email) if account_email else None
                if current_options and self._hero_ai_pause_snapshot is not None:
                    current_options.Following = bool(self._hero_ai_pause_snapshot[0])
                    current_options.Targeting = bool(self._hero_ai_pause_snapshot[1])
                    current_options.Combat = bool(self._hero_ai_pause_snapshot[2])
                    GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, current_options)
                self._hero_ai_pause_applied = False
                self._hero_ai_pause_snapshot = None
                self.cancel_movement_triggered = False

            if not self._config.upkeep.hero_ai.is_active():
                set_botting_range_mode(False)
                if handler.is_widget_enabled("HeroAI"):
                    handler.disable_widget("HeroAI")
                yield from Routines.Yield.wait(500)
                continue

            set_botting_range_mode(True)
              
            if not (self.parent.config.pause_on_danger_fn()):
                self.cancel_movement_triggered = False
            
            if (self.parent.config.pause_on_danger_fn() and 
                Agent.IsMoving(Player.GetAgentID()) and
                not self.cancel_movement_triggered):
                yield from Routines.Yield.Movement.StopMovement()
                self.cancel_movement_triggered = True
                    
            if self._config.upkeep.hero_ai.is_active() and not handler.is_widget_enabled("HeroAI"):
                handler.enable_widget("HeroAI")
            elif not self._config.upkeep.hero_ai.is_active() and handler.is_widget_enabled("HeroAI"):
                handler.disable_widget("HeroAI")
            yield from Routines.Yield.wait(500)

    def upkeep_build_ticker(self):
        from ...BuildMgr import BuildMgr
        from ...Routines import Routines

        while True:
            if not self._config.upkeep.build_ticker.is_active():
                yield from Routines.Yield.wait(250)
                continue

            build = self._config.build_handler
            if build is None or type(build) is BuildMgr:
                yield from Routines.Yield.wait(250)
                continue

            try:
                yield from build.ProcessSkillCasting()
            except NotImplementedError:
                yield from Routines.Yield.wait(250)
        
    def upkeep_auto_inventory_management(self):
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        from ...Routines import Routines
        inventory_handler = AutoInventoryHandler()
        while True:
            if self._config.upkeep.auto_inventory_management.is_active() and not inventory_handler.module_active:
                inventory_handler.module_active = True
            elif not self._config.upkeep.auto_inventory_management.is_active() and inventory_handler.module_active:
                inventory_handler.module_active = False
                
            yield from Routines.Yield.wait(500)
        
    def upkeep_auto_loot(self):
        from ...Routines import Routines
        from ...Py4GWcorelib import LootConfig
        from ...enums import Range, SharedCommandType
        from Py4GW_widget_manager import get_widget_handler
        def LootingRoutineActive():
            account_email = Player.GetAccountEmail()
            index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)

            if index == -1 or message is None:
                return False

            if message.Command != SharedCommandType.PickUpLoot:
                return False
            return True

        handler = get_widget_handler()

        while True:
            if not self._config.upkeep.auto_loot.is_active():
                yield from Routines.Yield.wait(500)
                continue

            # Enforce strict priority when combat is enabled:
            # combat > loot > movement.
            if handler.is_widget_enabled("HeroAI"):
                player_id = Player.GetAgentID()
                if (
                    self.parent.config.pause_on_danger_fn()
                    or Agent.IsInCombatStance(player_id)
                    or Routines.Checks.Agents.InAggro()
                    or Routines.Checks.Agents.IsCloseToAggro()
                    or Routines.Checks.Party.IsPartyMemberInDanger()
                ):
                    yield from Routines.Yield.wait(500)
                    continue
             
            if self.parent.config.pause_on_danger_fn():
                yield from Routines.Yield.wait(500)
                continue
            
            loot_singleton = LootConfig()
            loot_array = loot_singleton.GetfilteredLootArray(distance=Range.Earshot.value, multibox_loot=True, allow_unasigned_loot=False)
            if len(loot_array) == 0:
                yield from Routines.Yield.wait(500)
                continue
            player_email = Player.GetAccountEmail()
            GLOBAL_CACHE.ShMem.SendMessage(
                player_email,
                player_email,
                SharedCommandType.PickUpLoot,
                (0, 0, 0, 0),
            )
            yield from Routines.Yield.wait(500)
            while LootingRoutineActive():
                yield from Routines.Yield.wait(100)
            


    def upkeep_armor_of_salvation(self):    
        from ...Routines import Routines
        while True:
            if self._config.upkeep.armor_of_salvation.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_ArmorOfSalvation()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_essence_of_celerity(self):
        from ...Routines import Routines
        while True: 
            if self._config.upkeep.essence_of_celerity.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_EssenceOfCelerity()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_grail_of_might(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.grail_of_might.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GrailOfMight()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_green_rock_candy(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.green_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GreenRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_red_rock_candy(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.red_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_RedRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_blue_rock_candy(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.blue_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BlueRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_birthday_cupcake(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.birthday_cupcake.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BirthdayCupcake()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_slice_of_pumpkin_pie(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.slice_of_pumpkin_pie.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_SliceOfPumpkinPie()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_bowl_of_skalefin_soup(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.bowl_of_skalefin_soup.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BowlOfSkalefinSoup()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_candy_apple(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.candy_apple.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_CandyApple()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_candy_corn(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.candy_corn.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_CandyCorn()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_drake_kabob(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.drake_kabob.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_DrakeKabob()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_golden_egg(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.golden_egg.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GoldenEgg()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_pahnai_salad(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.pahnai_salad.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_PahnaiSalad()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_war_supplies(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.war_supplies.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_WarSupplies()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_alcohol(self):
        import PyEffects
        from ...Routines import Routines
        target_alc_level = 2
        disable_drunk_effects = False
        if disable_drunk_effects:
            PyEffects.PyEffects.ApplyDrunkEffect(0, 0)
        while True:
            if self._config.upkeep.alcohol.is_active():
                
                yield from Routines.Yield.Upkeepers.Upkeep_Alcohol(target_alc_level, disable_drunk_effects)
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_city_speed(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.city_speed.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_City_Speed()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_morale(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.honeycomb.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(110)
            elif (self._config.upkeep.four_leaf_clover.is_active()):
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(100)
            elif self._config.upkeep.morale.is_active():
                target_morale = int(self._config.upkeep.morale.get("target_morale"))
                target_morale = max(0, min(110, target_morale))
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(target_morale)
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_summoning_stone(self):
        from ...Routines import Routines
        from ...Agent import Agent
        from ...Player import Player
        from ...GlobalCache import GLOBAL_CACHE
        from ...enums import ModelID
        from ...Map import Map
        
        # Priority list for summoning stones (items)
        priority_stones = [
            ModelID.Legionnaire_Summoning_Crystal.value,  # Priority 1: Legionnaire
            ModelID.Igneous_Summoning_Stone.value,  # Priority 2: Igneous (if level < 20)
        ]
        
        # Other stones (items)
        other_stones = [
            ModelID.Amber_Summon.value,
            ModelID.Arctic_Summon.value,
            ModelID.Automaton_Summon.value,
            ModelID.Celestial_Summon.value,
            ModelID.Chitinous_Summon.value,
            ModelID.Demonic_Summon.value,
            ModelID.Fossilized_Summon.value,
            ModelID.Frosty_Summon.value,
            ModelID.Gelatinous_Summon.value,
            ModelID.Ghastly_Summon.value,
            ModelID.Imperial_Guard_Summon.value,
            ModelID.Jadeite_Summon.value,
            ModelID.Merchant_Summon.value,
            ModelID.Mischievous_Summon.value,
            ModelID.Mysterious_Summon.value,
            ModelID.Mystical_Summon.value,
            ModelID.Shining_Blade_Summon.value,
            ModelID.Tengu_Summon.value,
            ModelID.Zaishen_Summon.value,
        ]

        while True:
            if self._config.upkeep.summoning_stone.is_active():
                # Check if we're in an explorable area
                if not Map.IsExplorable():
                    yield from Routines.Yield.wait(1000)
                    continue
                
                # Check if player is alive
                if Agent.IsDead(Player.GetAgentID()):
                    yield from Routines.Yield.wait(1000)
                    continue
                
                # Check if player has skill points (required to use summoning stones)
                current_sp, _ = Player.GetSkillPointData()
                if current_sp <= 0:
                    yield from Routines.Yield.wait(1000)
                    continue

                # Check if player has Summoning Sickness effect
                has_summoning_sickness_active = has_summoning_sickness(Player.GetAgentID())
                has_alive_summon = has_active_party_summon(GLOBAL_CACHE.Party.GetOthers())
                
                # Only use stone if no summoning sickness AND no alive summon exists
                if not has_summoning_sickness_active and not has_alive_summon:
                    # Try Legionnaire first
                    stone_id = GLOBAL_CACHE.Inventory.GetFirstModelID(priority_stones[0])
                    if stone_id:
                        GLOBAL_CACHE.Inventory.UseItem(stone_id)
                    else:
                        # Try Igneous if level < 20
                        level = Agent.GetLevel(Player.GetAgentID())
                        if level < 20:
                            stone_id = GLOBAL_CACHE.Inventory.GetFirstModelID(priority_stones[1])
                            if stone_id:
                                GLOBAL_CACHE.Inventory.UseItem(stone_id)
                        
                        # Try other stones if Legionnaire and Igneous not available
                        if not stone_id:
                            for stone_model_id in other_stones:
                                stone_id = GLOBAL_CACHE.Inventory.GetFirstModelID(stone_model_id)
                                if stone_id:
                                    GLOBAL_CACHE.Inventory.UseItem(stone_id)
                                    break
                
                yield from Routines.Yield.wait(1000)
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_imp(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.imp.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_Imp()
            else:
                yield from Routines.Yield.wait(500)
    

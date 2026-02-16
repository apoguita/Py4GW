from functools import wraps
from typing import TYPE_CHECKING

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib import ConsoleLog, Console, Agent, Player

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
        
    
    def upkeep_auto_combat(self):
        from ...Routines import Routines
        while True:
            #print (f"autocombat is: {self._config.upkeep.auto_combat.is_active()}")
            if self._config.upkeep.auto_combat.is_active():
                yield from self._config.build_handler.ProcessSkillCasting()
            else:
                yield from Routines.Yield.wait(250)       
           
    def upkeep_hero_ai(self):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        from Py4GW_widget_manager import get_widget_handler
        handler = get_widget_handler()
        while True:   
            if not self._config.upkeep.hero_ai.is_active():
                if handler.is_widget_enabled("HeroAI"):
                    handler.disable_widget("HeroAI")
                yield from Routines.Yield.wait(500)
                continue
            
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
            
            if self.parent.config.pause_on_danger_fn():
                yield from Routines.Yield.wait(500)
                continue
            
            if handler.is_widget_enabled("HeroAI"):
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
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(100)
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_summoning_stone(self):
        from ...Routines import Routines
        from ...Agent import Agent
        from ...Player import Player
        from ...GlobalCache import GLOBAL_CACHE
        from ...enums import ModelID
        from ...Map import Map
        from ...Quest import Quest
        
        # Quest IDs where summoning stones should NOT be used
        excluded_quest_ids = [
            490,  # The Council is Called
            503,  # All's Well That Ends Well
            504,  # Warning Kehanni
            505,  # Calling the Order
            730,  # Gain Goren
        ]
        
        # Map IDs where summoning stones should NOT be used
        excluded_map_ids = [
            503,  # Throne of Secrets
        ]
        
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
        
        # Known summon creature model IDs (the actual spawned allies, not the items)
        summon_creature_model_ids = [
            513,   # Fire Imp
            8028,  # Legionnaire
            9055,  # Tengu Support Flare - Warrior
            9056,  # Tengu Support Flare - Ranger
            9058,  # Tengu Support Flare - Monk
            9060,  # Tengu Support Flare - Mesmer
            9062,  # Tengu Support Flare - Ritualist
            9065,  # Tengu Support Flare - Assassin
            9067,  # Tengu Support Flare - Elementalist
            9069,  # Tengu Support Flare - Necromancer
            # Add more as discovered via summon_model_id_detector.py
        ]
        
        # Summoning Sickness effect ID - applies to all summons
        summoning_sickness_effect_id = 2886
        
        while True:
            if self._config.upkeep.summoning_stone.is_active():
                # Check if we're in an explorable area
                if not Map.IsExplorable():
                    yield from Routines.Yield.wait(1000)
                    continue
                
                # Skip if an excluded quest is in the quest log
                active_quests = Quest.GetQuestLogIds()
                if any(qid in excluded_quest_ids for qid in active_quests):
                    yield from Routines.Yield.wait(1000)
                    continue
                
                # Skip if in an excluded map
                if Map.GetMapID() in excluded_map_ids:
                    yield from Routines.Yield.wait(1000)
                    continue
                
                # Check if player is alive
                if Agent.IsDead(Player.GetAgentID()):
                    yield from Routines.Yield.wait(1000)
                    continue
                
                # Check if player has Summoning Sickness effect
                has_summoning_sickness = GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), summoning_sickness_effect_id)
                
                # Check if there's already a summon alive in party by checking model IDs
                has_alive_summon = False
                others = GLOBAL_CACHE.Party.GetOthers()
                for other in others:
                    if Agent.IsAlive(other):
                        model_id = Agent.GetModelID(other)
                        if model_id in summon_creature_model_ids:
                            has_alive_summon = True
                            break
                
                # Only use stone if no summoning sickness AND no alive summon exists
                if not has_summoning_sickness and not has_alive_summon:
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
    
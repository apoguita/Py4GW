from typing import List, Tuple, Callable, Optional, Generator, Any

from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.py4gwcorelib_src.Keystroke import Keystroke
from Py4GWCoreLib.py4gwcorelib_src.Timer import Timer, ThrottledTimer
from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.py4gwcorelib_src.Keystroke import Keystroke
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.routines_src import Checks
from ..Map import Map

from ..GlobalCache import GLOBAL_CACHE
from ..Py4GWcorelib import ConsoleLog, Console, Utils, ActionQueueManager
from ..py4gwcorelib_src.BehaviorTree import BehaviorTree

from ..enums_src.Model_enums import ModelID
from ..enums_src.UI_enums import ControlAction
from .BehaviourTrees import BT
from .yield_src.helpers import _run_bt_tree, wait as _yield_wait
from .yield_src.keybinds import Keybinds as YieldKeybinds
from .yield_src.player import Player as YieldPlayer
from .yield_src.skills import Skills as YieldSkills
from .yield_src.map import Map as YieldMap
from .yield_src.movement import Movement as YieldMovement
from .yield_src.agents import Agents as YieldAgents
from .yield_src.merchant import Merchant as YieldMerchant
from .yield_src.items import Items as YieldItems

import functools
import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()

class Yield:
    @staticmethod
    def wait(ms: int, break_on_map_transition: bool = False):
        yield from _yield_wait(ms, break_on_map_transition=break_on_map_transition)

    Player = YieldPlayer
    Skills = YieldSkills
    Map = YieldMap
    Keybinds = YieldKeybinds
    Movement = YieldMovement
    Agents = YieldAgents
    Merchant = YieldMerchant
    Items = YieldItems

#region Upkeepers
    class Upkeepers:

        ALCOHOL_ITEMS = [
            ModelID.Aged_Dwarven_Ale, ModelID.Aged_Hunters_Ale, ModelID.Bottle_Of_Grog,
            ModelID.Flask_Of_Firewater, ModelID.Keg_Of_Aged_Hunters_Ale,
            ModelID.Krytan_Brandy, ModelID.Spiked_Eggnog,
            ModelID.Bottle_Of_Rice_Wine, ModelID.Eggnog, ModelID.Dwarven_Ale,
            ModelID.Hard_Apple_Cider, ModelID.Hunters_Ale, ModelID.Bottle_Of_Juniberry_Gin,
            ModelID.Shamrock_Ale, ModelID.Bottle_Of_Vabbian_Wine, ModelID.Vial_Of_Absinthe,
            ModelID.Witchs_Brew, ModelID.Zehtukas_Jug,
        ]

        CITY_SPEED_ITEMS = [ModelID.Creme_Brulee, ModelID.Jar_Of_Honey, ModelID.Krytan_Lokum,
                            ModelID.Chocolate_Bunny, ModelID.Fruitcake, ModelID.Red_Bean_Cake,
                            ModelID.Mandragor_Root_Cake,
                            ModelID.Delicious_Cake, ModelID.Minitreat_Of_Purity,
                            ModelID.Sugary_Blue_Drink]
        
        CITY_SPEED_EFFECTS = [1860, #Sugar_Rush_short, // 1 minute
                              1323, #Sugar_Rush_medium, // 3 minute
                              1612, #Sugar_Rush_long, // 5 minute
                              3070, #Sugar_Rush_Agent_of_the_Mad_King
                              1916, #Sugar_Jolt_short, // 2 minute
                              1933, #Sugar_Jolt_long, // 5 minute
        ]

        MORALE_ITEMS = [
            ModelID.Honeycomb, ModelID.Rainbow_Candy_Cane, ModelID.Elixir_Of_Valor,
            ModelID.Pumpkin_Cookie, ModelID.Powerstone_Of_Courage, ModelID.Seal_Of_The_Dragon_Empire,
            ModelID.Four_Leaf_Clover, ModelID.Oath_Of_Purity, ModelID.Peppermint_Candy_Cane,
            ModelID.Refined_Jelly, ModelID.Shining_Blade_Ration, ModelID.Wintergreen_Candy_Cane,
        ]
        
        @staticmethod
        def Upkeep_Imp():
            from .Checks import Checks
            
            if ((not Checks.Map.MapValid())):
                yield from Yield.wait(500)
                return

            if (not Map.IsExplorable()):
                yield from Yield.wait(500)
                return

            if Agent.IsDead(Player.GetAgentID()):
                yield from Yield.wait(500)
                return

            level = Agent.GetLevel(Player.GetAgentID())

            if level >= 20:
                yield from Yield.wait(500)
                return

            summoning_stone = ModelID.Igneous_Summoning_Stone.value
            stone_id = GLOBAL_CACHE.Inventory.GetFirstModelID(summoning_stone)
            imp_effect_id = 2886
            has_effect = GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), imp_effect_id)

            imp_model_id = 513
            others = GLOBAL_CACHE.Party.GetOthers()
            cast_imp = True  # Assume we should cast

            for other in others:
                if Agent.GetModelID(other) == imp_model_id:
                    if not Agent.IsDead(other):
                        # Imp is alive — no need to cast
                        cast_imp = False
                    break  # Found the imp, no need to keep checking

            if stone_id and not has_effect and cast_imp:
                GLOBAL_CACHE.Inventory.UseItem(stone_id)
                yield from Yield.wait(500)

            yield from Yield.wait(500)
        
        @staticmethod
        def _upkeep_consumable(model_id:int, effect_name:str):
            from .Checks import Checks

            if ((not Checks.Map.MapValid())):
                yield from Yield.wait(500)
                return

            if (not Map.IsExplorable()):
                yield from Yield.wait(500)
                return

            if Agent.IsDead(Player.GetAgentID()):
                yield from Yield.wait(500)
                return

            effect_id = GLOBAL_CACHE.Skill.GetID(effect_name)
            if not GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), effect_id):
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                if item_id:
                    GLOBAL_CACHE.Inventory.UseItem(item_id)
                    yield from Yield.wait(500)

            yield from Yield.wait(500)
     
        @staticmethod
        def Upkeep_ArmorOfSalvation():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Armor_Of_Salvation, "Armor_of_Salvation_item_effect")  
        
        @staticmethod
        def Upkeep_EssenceOfCelerity():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Essence_Of_Celerity, "Essence_of_Celerity_item_effect")
            
        @staticmethod
        def Upkeep_GrailOfMight():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Grail_Of_Might, "Grail_of_Might_item_effect")
            
        @staticmethod
        def Upkeep_BlueRockCandy():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Blue_Rock_Candy, "Blue_Rock_Candy_Rush")

        @staticmethod
        def Upkeep_GreenRockCandy():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Green_Rock_Candy, "Green_Rock_Candy_Rush")
        
        @staticmethod
        def Upkeep_RedRockCandy():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Red_Rock_Candy, "Red_Rock_Candy_Rush")
            
        @staticmethod
        def Upkeep_BirthdayCupcake():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Birthday_Cupcake, "Birthday_Cupcake_skill")
      
        @staticmethod
        def Upkeep_SliceOfPumpkinPie():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Slice_Of_Pumpkin_Pie, "Pie_Induced_Ecstasy")
            
        @staticmethod
        def Upkeep_BowlOfSkalefinSoup():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Bowl_Of_Skalefin_Soup, "Skale_Vigor")
            
        @staticmethod
        def Upkeep_CandyApple():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Candy_Apple, "Candy_Apple_skill")
            
        @staticmethod
        def Upkeep_CandyCorn():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Candy_Corn, "Candy_Corn_skill")
        
        @staticmethod
        def Upkeep_DrakeKabob():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Drake_Kabob, "Drake_Skin")
            
        @staticmethod
        def Upkeep_GoldenEgg():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Golden_Egg, "Golden_Egg_skill")
            
        @staticmethod
        def Upkeep_PahnaiSalad():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Pahnai_Salad, "Pahnai_Salad_item_effect")
            
        @staticmethod
        def Upkeep_WarSupplies():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.War_Supplies, "Well_Supplied")

        @staticmethod
        def Upkeep_Morale(target_morale=110):
            from .Checks import Checks

            # Party-wide morale items: affect all members, so check party morale too.
            # Player-only items must not be spent trying to raise party morale.
            PARTY_MORALE_MODELS = frozenset(
                m.value if hasattr(m, "value") else int(m)
                for m in (
                    ModelID.Honeycomb, ModelID.Rainbow_Candy_Cane,
                    ModelID.Elixir_Of_Valor, ModelID.Powerstone_Of_Courage,
                )
            )

            morale_models = [
                (m.value if hasattr(m, "value") else int(m))
                for m in Yield.Upkeepers.MORALE_ITEMS
            ]

            if not (Checks.Map.MapValid() and Map.IsExplorable()):
                yield from Yield.wait(500)
                return

            if Agent.IsDead(Player.GetAgentID()):
                yield from Yield.wait(500)
                return

            def _min_party_morale():
                try:
                    entries = GLOBAL_CACHE.Party.GetPartyMorale() or []
                    if not entries:
                        return Player.GetMorale()
                    return min(int(m) for _, m in entries)
                except Exception:
                    return Player.GetMorale()

            player_morale = Player.GetMorale()
            min_party = _min_party_morale()

            while player_morale < target_morale or min_party < target_morale:
                item_id = 0
                need_player_morale = player_morale < target_morale
                need_party_morale = min_party < target_morale

                # If any party member is below target, only party-wide morale items can help.
                if need_party_morale:
                    for model_id in morale_models:
                        if model_id in PARTY_MORALE_MODELS:
                            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                            if item_id:
                                break

                # Only use player-only morale items when the player still needs morale.
                if not item_id and need_player_morale:
                    for model_id in morale_models:
                        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                        if item_id:
                            break

                if not item_id:
                    # nothing to use right now
                    yield from Yield.wait(500)
                    break

                GLOBAL_CACHE.Inventory.UseItem(item_id)
                yield from Yield.wait(750)

                # Recalculate after use
                player_morale = Player.GetMorale()
                min_party = _min_party_morale()

            yield from Yield.wait(500)

        @staticmethod
        def Upkeep_Alcohol(target_alc_level=2, disable_drunk_effects=False):
            import PyEffects
            from .Checks import Checks
            alcohol_models = [
                (m.value if hasattr(m, "value") else int(m))
                for m in Yield.Upkeepers.ALCOHOL_ITEMS
            ]

            #if disable_drunk_effects:
            #    PyEffects.PyEffects.ApplyDrunkEffect(0, 0)

            
            if not (Checks.Map.MapValid() and Map.IsExplorable()):
                yield from Yield.wait(500)
                return

            if Agent.IsDead(Player.GetAgentID()):
                yield from Yield.wait(500)
                return

            while True:
                drunk_level = PyEffects.PyEffects.GetAlcoholLevel()
                if drunk_level >= target_alc_level:
                    yield from Yield.wait(500)
                    break

                item_id = 0
                for model_id in alcohol_models:
                    item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                    if item_id:
                        break
                    
                if not item_id:
                    # nothing to use right now
                    yield from Yield.wait(500)
                    break

                GLOBAL_CACHE.Inventory.UseItem(item_id)
                yield from Yield.wait(500)
                
            yield from Yield.wait(500)
                
        @staticmethod
        def Upkeep_City_Speed():
            from .Checks import Checks

            # resolve enum -> int once
            item_models = [(m.value if hasattr(m, "value") else int(m)) for m in Yield.Upkeepers.CITY_SPEED_ITEMS]
            effect_ids = list(Yield.Upkeepers.CITY_SPEED_EFFECTS)
            player_id = lambda: Player.GetAgentID()
            period_ms: int = 1000


            # basic guards
            if not Checks.Map.MapValid():
                yield from Yield.wait(period_ms)
                return
            # City speed is for towns/outposts, so skip if explorable
            if not Map.IsOutpost():
                yield from Yield.wait(period_ms)
                return
            if Agent.IsDead(player_id()):
                yield from Yield.wait(period_ms)
                return

            # already have ANY acceptable city-speed effect?
            if any(GLOBAL_CACHE.Effects.HasEffect(player_id(), eid) for eid in effect_ids):
                yield from Yield.wait(period_ms)
                return

            # use first available item by priority
            used = False
            for mid in item_models:
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(mid)
                if item_id:
                    GLOBAL_CACHE.Inventory.UseItem(item_id)
                    yield from Yield.wait(period_ms)
                    used = True
                    break

            # short cooldown either way
            yield from Yield.wait(period_ms)

#endregion

#region Keybinds
#region Character Reroll
    class RerollCharacter:
        @staticmethod
        def DeleteCharacter(character_name_to_delete: str, timeout_ms: int = 10000, log: bool = False) -> Generator[Any, Any, bool]:
            import PyImGui
            from ..UIManager import WindowFrames
            from ..Context import GWContext
            def _failed() -> bool:
                return timeout_timer.IsExpired() or not Map.Pregame.InCharacterSelectScreen()
            
            def _timeout_reached() -> bool:
                return timeout_timer.IsExpired()
            
            #A new character is not reported here until next login, so we skip this check
            """
            character_names = [char.player_name for char in Player.GetLoginCharacters()]
            if character_name_to_delete not in character_names:
                ConsoleLog("Reroll", f"Character '{character_name_to_delete}' not found among login characters.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return False
            """
            
            timeout_timer = ThrottledTimer(timeout_ms)
            ActionQueueManager().ResetAllQueues()

            if not Map.Pregame.InCharacterSelectScreen():
                ConsoleLog("Reroll", "Logging out to character select screen...", Console.MessageType.Info, log)
                Map.Pregame.LogoutToCharacterSelect() 
                while not Map.Pregame.InCharacterSelectScreen() and not timeout_timer.IsExpired():
                    yield from Yield.wait(250)
                    
            if _timeout_reached():
                ConsoleLog("Reroll", "Timeout while waiting to reach character select screen.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return False
                
            yield from Yield.wait(1000)
            pregame = GWContext.PreGame.GetContext()
            if pregame is None:
                ConsoleLog("Reroll", "Failed to retrieve pregame context.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return False
            
            character_index = pregame.chars_list.index(character_name_to_delete) if character_name_to_delete in pregame.chars_list else -1
            last_known_index = pregame.chosen_character_index
            
            """if character_index == -1:
                ConsoleLog("Reroll", f"Character '{character_name_to_delete}' not found in character list.", Console.MessageType.Error)
                yield from Yield.wait(100)
                return False
            
            while last_known_index != character_index and not _failed(): 
                distance = character_index - last_known_index
                
                if distance != 0:
                    key = Key.RightArrow.value if distance > 0 else Key.LeftArrow.value
                    ConsoleLog("Reroll", f"Navigating {'Right' if distance > 0 else 'Left'} (Current: {last_known_index}, Target: {character_index})", Console.MessageType.Debug, log)
                    Keystroke.PressAndRelease(key)
                    yield from Yield.wait(250)
                    pregame = Player.GetPreGameContext()
                    last_known_index = pregame.index_1
                    
            if _failed():
                ConsoleLog("Reroll", "Timeout while navigating to target character.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return False"""
            
            WindowFrames["DeleteCharacterButton"].FrameClick()
            yield from Yield.wait(750)
            PyImGui.set_clipboard_text(character_name_to_delete)
            Keystroke.PressAndReleaseCombo([Key.Ctrl.value, Key.V.value])
            yield from Yield.wait(750)
            WindowFrames["FinalDeleteCharacterButton"].FrameClick()
            yield from Yield.wait(750)
            
            return True
        
        @staticmethod
        def CreateCharacter(character_name: str,campaign_name: str, profession_name: str, timeout_ms: int = 15000, log: bool = False) -> Generator[Any, Any, None]:
            import PyImGui
            from ..UIManager import WindowFrames
            def _failed() -> bool:
                return timeout_timer.IsExpired() or not Map.Pregame.InCharacterSelectScreen()
            
            def _timeout_reached() -> bool:
                return timeout_timer.IsExpired()
            
            def _select_character_type(character_type: str) -> Generator[Any, Any, None]:
                if character_type == "PvE":
                    # Default, do nothing
                    yield from Yield.wait(100)
                    return
                
                Keystroke.PressAndRelease(Key.RightArrow.value)
                yield from Yield.wait(100)
            
            def _select_campaign(campaign_name: str) -> Generator[Any, Any, None]:
                repeats = 0
                if campaign_name == "Prophecies":
                    repeats = 1
                elif campaign_name == "Factions":
                    repeats = 2
                elif campaign_name == "Nightfall":
                    repeats = 0
                
                for _ in range(repeats):
                    Keystroke.PressAndRelease(Key.RightArrow.value)
                    yield from Yield.wait(100)
                yield from Yield.wait(100)
                
            def _select_profession(profession_name: str) -> Generator[Any, Any, None]:
                profession_map = {
                    "Warrior": 0,
                    "Ranger": 1,
                    "Monk": 2,
                    "Necromancer": 3,
                    "Mesmer": 4,
                    "Elementalist": 5,
                    "Assassin": 6,
                    "Ritualist": 7,
                    "Paragon": 6,
                    "Dervish": 7
                }
                
                target_index = profession_map.get(profession_name, -1)
                if target_index == -1:
                    ConsoleLog("Reroll", f"Unknown profession '{profession_name}'.", Console.MessageType.Error, log)
                    yield from Yield.wait(100)
                    return
                
                for _ in range(target_index):
                    Keystroke.PressAndRelease(Key.RightArrow.value)
                    yield from Yield.wait(100)
                yield from Yield.wait(100)
            
            """character_names = [char.player_name for char in Player.GetLoginCharacters()]
            if character_name in character_names:
                ConsoleLog("Reroll", f"Character '{character_name}' already exists among login characters.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return  """
            
            yield from Yield.wait(1000)
            timeout_timer = ThrottledTimer(timeout_ms)
            ActionQueueManager().ResetAllQueues()

            if not Map.Pregame.InCharacterSelectScreen():
                ConsoleLog("Reroll", "Logging out to character select screen...", Console.MessageType.Info, log)
                Map.Pregame.LogoutToCharacterSelect() 
                while not Map.Pregame.InCharacterSelectScreen() and not timeout_timer.IsExpired():
                    yield from Yield.wait(250)
                    
            if _timeout_reached():
                ConsoleLog("Reroll", "Timeout while waiting to reach character select screen.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return
                
            ConsoleLog("Reroll", "Creating new character...", Console.MessageType.Info, log)
            WindowFrames["CreateCharacterButton1"].FrameClick()
            yield from Yield.wait(500)
            WindowFrames["CreateCharacterButton2"].FrameClick()
            yield from Yield.wait(1000)
            # Select character type
            yield from _select_character_type("PvE")
            yield from Yield.wait(500)
            WindowFrames["CreateCharacterTypeNextButton"].FrameClick()
            yield from Yield.wait(1000)
            # Select campaign
            yield from _select_campaign(campaign_name)
            yield from Yield.wait(500)

            WindowFrames["CreateCharacterNextButtonGeneric"].FrameClick()
            yield from Yield.wait(1000)
            # Select profession
            yield from _select_profession(profession_name)
            yield from Yield.wait(500)
            WindowFrames["CreateCharacterNextButtonGeneric"].FrameClick()
            yield from Yield.wait(1000)
            #Selct Gender (default)
            WindowFrames["CreateCharacterNextButtonGeneric"].FrameClick()
            yield from Yield.wait(1000)
            #select Appearance (default)
            WindowFrames["CreateCharacterNextButtonGeneric"].FrameClick()
            yield from Yield.wait(1000)
            #sxelect Body (default)
            WindowFrames["CreateCharacterNextButtonGeneric"].FrameClick()
            yield from Yield.wait(1000)
            # Enter name and finalize     
            PyImGui.set_clipboard_text(character_name)
            Keystroke.PressAndReleaseCombo([Key.Ctrl.value, Key.V.value])    
            yield from Yield.wait(1000)
            WindowFrames["FinalCreateCharacterButton"].FrameClick()
            yield from Yield.wait(3000)
            
        @staticmethod
        def DeleteAndCreateCharacter(character_name_to_delete: str, new_character_name: str,
                             campaign_name: str, profession_name: str,
                             timeout_ms: int = 25000, log: bool = False) -> Generator[Any, Any, None]:
            result = yield from Yield.RerollCharacter.DeleteCharacter(character_name_to_delete, timeout_ms=timeout_ms//2, log=log)
            if not result:
                return
            yield from Yield.wait(1000)  # brief wait before creating new character
            yield from Yield.RerollCharacter.CreateCharacter(new_character_name, campaign_name, profession_name, timeout_ms=timeout_ms//2, log=log)    


                    
        @staticmethod
        def Reroll(target_character_name: str, timeout_ms: int = 10000, log: bool = False) -> Generator[Any, Any, None]:
            from ..Context import GWContext
            def _failed() -> bool:
                return timeout_timer.IsExpired() or not Map.Pregame.InCharacterSelectScreen()
            
            def _timeout_reached() -> bool:
                return timeout_timer.IsExpired()
            
            character_names = [char.player_name for char in Map.Pregame.GetAvailableCharacterList()]
            if target_character_name not in character_names:
                ConsoleLog("Reroll", f"Character '{target_character_name}' not found among login characters.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return  
            
            if Player.GetName() == target_character_name and not Map.Pregame.InCharacterSelectScreen():
                ConsoleLog("Reroll", f"Already logged in as '{target_character_name}'. No reroll needed.", Console.MessageType.Info, log)
                yield from Yield.wait(100)
                return
            
            timeout_timer = ThrottledTimer(timeout_ms)
            ActionQueueManager().ResetAllQueues()

            if not Map.Pregame.InCharacterSelectScreen():
                ConsoleLog("Reroll", "Logging out to character select screen...", Console.MessageType.Info, log)
                Map.Pregame.LogoutToCharacterSelect() 
                while not Map.Pregame.InCharacterSelectScreen() and not timeout_timer.IsExpired():
                    yield from Yield.wait(250)
                    
            if _timeout_reached():
                ConsoleLog("Reroll", "Timeout while waiting to reach character select screen.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return
                
            pregame = GWContext.PreGame.GetContext()
            if pregame is None:
                ConsoleLog("Reroll", "Failed to retrieve pregame context.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return
            character_index = pregame.chars_list.index(target_character_name) if target_character_name in pregame.chars_list else -1
            last_known_index = pregame.chosen_character_index
            
            if character_index == -1:
                ConsoleLog("Reroll", f"Character '{target_character_name}' not found in character list.", Console.MessageType.Error)
                yield from Yield.wait(100)
                return
            
            while last_known_index != character_index and not _failed(): 
                distance = character_index - last_known_index
                
                if distance != 0:
                    key = Key.RightArrow.value if distance > 0 else Key.LeftArrow.value
                    ConsoleLog("Reroll", f"Navigating {'Right' if distance > 0 else 'Left'} (Current: {last_known_index}, Target: {character_index})", Console.MessageType.Debug, log)
                    Keystroke.PressAndRelease(key)
                    yield from Yield.wait(250)
                    pregame = GWContext.PreGame.GetContext()
                    if pregame is None:
                        ConsoleLog("Reroll", "Failed to retrieve pregame context.", Console.MessageType.Error, log)
                        yield from Yield.wait(100)
                        return
                    
                    last_known_index = pregame.chosen_character_index
                    
            if _failed():
                ConsoleLog("Reroll", "Timeout while navigating to target character.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return
            
            ConsoleLog("Reroll", f"Selecting character '{target_character_name}'.", Console.MessageType.Info, log)
            Keystroke.PressAndRelease(Key.P.value)
            yield from Yield.wait(50)
            
            while not Map.IsMapReady() and not _timeout_reached():
                yield from Yield.wait(250)
                
            if _timeout_reached():
                ConsoleLog("Reroll", "Timeout reached while waiting for map to load.", Console.MessageType.Error)
                return
            
            ConsoleLog("Reroll", f"Successfully logged in as '{target_character_name}'.", Console.MessageType.Info, log)
            yield                  

from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable


#region UI
class _UI:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._helpers = parent
        self._Events = parent.Events  
        self.Keybinds = self._Keybinds(self) 
    
    def _cancel_skill_reward_window(self):
        from ...Routines import Routines
        import Py4GW
        from ...UIManager import UIManager
        global bot  
        yield from Routines.Yield.wait(500)
        cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)  # Cancel button frame ID
        if not cancel_button_frame_id:
            Py4GW.Console.Log("CancelSkillRewardWindow", "Cancel button frame ID not found.", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return
        
        while not UIManager.FrameExists(cancel_button_frame_id):
            yield from Routines.Yield.wait(1000)
            return
        
        UIManager.FrameClick(cancel_button_frame_id)
        yield from Routines.Yield.wait(1000)
    
    @_yield_step(label="CancelSkillRewardWindow", counter_key="CANCEL_SKILL_REWARD_WINDOW")
    def cancel_skill_reward_window(self):
        yield from self._cancel_skill_reward_window()
            
            
    @_yield_step(label="SendChatMessage", counter_key="SEND_CHAT_MESSAGE")
    def send_chat_message(self, channel: str, message: str):
        from ...Routines import Routines
        yield from Routines.Yield.Player.SendChatMessage(channel, message)

    @_yield_step(label="PrintMessageToConsole", counter_key="SEND_CHAT_MESSAGE")
    def print_message_to_console(self, source:str, message: str):
        from ...Routines import Routines
        yield from Routines.Yield.Player.PrintMessageToConsole(source, message)
        
    @_yield_step(label="OpenSkillsAndAttributes", counter_key="OPEN_SKILLS_AND_ATTRIBUTES")
    def open_skills_and_attributes(self):
        from ...Routines import Routines
        yield from Routines.Yield.Keybinds.OpenSkillsAndAttributes()
        
    class _Keybinds:
        def __init__(self, parent: "_UI"):
            self.parent = parent
            self._helpers = self.parent._helpers
            self._config = self.parent._config

        @_yield_step(label="DropBundle", counter_key="DROP_BUNDLE")
        def drop_bundle(self):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.DropBundle()
        
        @_yield_step(label="CloseAllPanels", counter_key="CLOSE_ALL_PANELS")
        def close_all_panels(self):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.CloseAllPanels()
            
        @_yield_step(label="toggle_inventory", counter_key="TOGGLE_INVENTORY")
        def toggle_inventory(self):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.ToggleInventory()
            
        @_yield_step(label="toggle_all_bags", counter_key="TOGGLE_ALL_BAGS")
        def toggle_all_bags(self):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.ToggleAllBags()
            
        @_yield_step(label="open_mission_map", counter_key="OPEN_MISSION_MAP")
        def open_mission_map(self):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.OpenMissionMap()
            
        @_yield_step(label="cycle_equipment_set", counter_key="CYCLE_EQUIPMENT_SET")
        def cycle_equipment_set(self):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.CycleEquipment()

        @_yield_step(label="activate_weapon_set", counter_key="ACTIVATE_WEAPON_SET")
        def activate_weapon_set(self, set_number:int=1):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.ActivateWeaponSet(set_number)
            
        @_yield_step(label="move_fordward", counter_key="MOVE_FORWARD")
        def move_forward(self, duration_ms:int=500):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.MoveForwards(duration_ms)
            
        @_yield_step(label="move_backward", counter_key="MOVE_BACKWARD")
        def move_backward(self, duration_ms:int=500):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.MoveBackwards(duration_ms)
            
        @_yield_step(label="turn_left", counter_key="TURN_LEFT")
        def turn_left(self, duration_ms:int=500):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.TurnLeft(duration_ms)
            
        @_yield_step(label="turn_right", counter_key="TURN_RIGHT")
        def turn_right(self, duration_ms:int=500):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.TurnRight(duration_ms)
            
        @_yield_step(label="strafe_left", counter_key="STRAFE_LEFT")
        def strafe_left(self, duration_ms:int=500):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.StrafeLeft(duration_ms)
            
        @_yield_step(label="strafe_right", counter_key="STRAFE_RIGHT")
        def strafe_right(self, duration_ms:int=500):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.StrafeRight(duration_ms)
            
        @_yield_step(label="cancel_action", counter_key="CANCEL_ACTION")
        def cancel_action(self):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.CancelAction()
            
        @_yield_step(label="clear_party_commands", counter_key="CLEAR_PARTY_COMMANDS")
        def clear_party_commands(self): 
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.ClearPartyCommands()
            
        @_yield_step(label="use_skill", counter_key="USE_SKILL")
        def use_skill(self, slot_number:int):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.UseSkill(slot_number)
            
        @_yield_step(label="use_hero_skill", counter_key="USE_HERO_SKILL")
        def use_hero_skill(self, hero_index:int, slot_number:int):
            from ...Routines import Routines
            yield from Routines.Yield.Keybinds.HeroSkill(hero_index, slot_number)

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
        self._Events = parent.Events   
    
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
        
    @_yield_step(label="CloseAllDialogs", counter_key="CLOSE_ALL_DIALOGS")
    def drop_bundle(self):
        from ...Routines import Routines
        yield from Routines.Yield.Keybinds.DropBundle()
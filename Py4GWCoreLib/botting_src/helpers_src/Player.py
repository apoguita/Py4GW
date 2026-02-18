from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple

#region TARGET
class _Player:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
    
    @_yield_step(label="SetTitle", counter_key="SET_TITLE")
    def set_title(self, title: int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        yield from Routines.Yield.Player.SetTitle(title, False)
        
    @_yield_step(label="CallTarget", counter_key="CALL_TARGET")
    def call_target(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        yield from Routines.Yield.Keybinds.CallTarget(False)
        
    @_yield_step(label="DeleteCharacter", counter_key="DELETE_CHARACTER")
    def delete_character(self, character_name: str, timeout_ms: int = 15000, log: bool = True) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        yield from Routines.Yield.RerollCharacter.DeleteCharacter(character_name, timeout_ms, log)
    
    @_yield_step(label="CreateCharacter", counter_key="CREATE_CHARACTER")
    def create_character(self, character_name: str, faction: str, class_name: str, timeout_ms: int = 15000, log: bool = True) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        yield from Routines.Yield.RerollCharacter.CreateCharacter(character_name, faction, class_name, timeout_ms, log)
        
    @_yield_step(label="DeleteAndCreateCharacter", counter_key="DELETE_CREATE_CHARACTER")
    def delete_and_create_character(self, character_name: str, target_character_name: str, faction: str, class_name: str, timeout_ms: int = 15000, log: bool = True) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        yield from Routines.Yield.RerollCharacter.DeleteAndCreateCharacter(character_name, target_character_name, faction, class_name, timeout_ms, log)
        
    @_yield_step(label="RerollCharacter", counter_key="REROLL_CHARACTER")
    def reroll_character(self,target_character_name: str, timeout_ms: int = 15000, log: bool = True) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        yield from Routines.Yield.RerollCharacter.Reroll(target_character_name, timeout_ms, log)

    @_yield_step(label="BuySkill", counter_key="BUY_SKILL")
    def buy_skill(self, skill_id: int, log: bool = False) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        yield from Routines.Yield.Player.BuySkill(skill_id, log)

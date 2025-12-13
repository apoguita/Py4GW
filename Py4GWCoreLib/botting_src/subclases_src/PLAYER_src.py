#region STATES
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

#region PARTY
class _PLAYER:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers

    def SetTitle(self, title_id: int):
        self._helpers.Player.set_title(title_id)
        
    def CallTarget(self):
        self._helpers.Player.call_target()
        
    def DeleteCharacter(self, character_name: str, timeout_ms: int = 15000, log: bool = True):
        self._helpers.Player.delete_character(character_name, timeout_ms, log)
        
    def CreateCharacter(self, character_name: str, faction: str, class_name: str, timeout_ms: int = 15000, log: bool = True):
        self._helpers.Player.create_character(character_name, faction, class_name, timeout_ms, log)
        
    def DeleteAndCreateCharacter(self, character_name: str, target_character_name: str, faction: str, class_name: str, timeout_ms: int = 15000, log: bool = True):
        self._helpers.Player.delete_and_create_character(character_name, target_character_name, faction, class_name, timeout_ms, log)
        
    def RerollCharacter(self,target_character_name: str, timeout_ms: int = 15000, log: bool = True):
        self._helpers.Player.reroll_character(target_character_name, timeout_ms, log)
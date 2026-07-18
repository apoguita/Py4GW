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

    def BuySkill(self, skill_id: int, log: bool = False):
        self._helpers.Player.buy_skill(skill_id, log)

    def UnlockBalthazarSkill(self, skill_id: int, use_pvp_remap: bool = True, log: bool = False):
        self._helpers.Player.unlock_balthazar_skill(skill_id, use_pvp_remap, log)

    def HasSkillPoints(self) -> bool:
        # Returns True if the player has at least one skill point available. Use for gating skill purchases.
        from ...Player import Player
        current, _ = Player.GetSkillPointData()
        return current > 0

    def GetSkillPoints(self) -> int:
        # Returns the exact number of skill points available. Use when you need the count (e.g. logging, buying multiple skills).
        from ...Player import Player
        current, _ = Player.GetSkillPointData()
        return current

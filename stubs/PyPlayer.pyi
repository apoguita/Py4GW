# PyPlayer.pyi - Auto-generated .pyi file for PyPlayer module

from typing import Any, List, overload
from PyAgent import PyAgent

    
# Class PyPlayer
class PyPlayer:
    id: int
    agent: PyAgent
    target_id: int
    mouse_over_id: int
    observing_id: int
    account_name: str
    account_email: str
    player_uuid: tuple[int,int,int,int]
    wins: int
    losses: int
    rating: int
    qualifier_points: int
    rank: int
    tournament_reward_points: int
    morale: int
    party_morale: list[tuple[int, int]]
    experience: int
    level : int
    current_kurzick: int
    total_earned_kurzick: int
    max_kurzick: int
    current_luxon: int
    total_earned_luxon: int
    max_luxon: int
    current_imperial: int
    total_earned_imperial: int
    max_imperial: int
    current_balth: int
    total_earned_balth: int
    max_balth: int
    current_skill_points: int
    total_earned_skill_points: int
    missions_completed: list[int]
    missions_bonus: list[int]
    missions_completed_hm: list[int]
    missions_bonus_hm: list[int]
    controlled_minions: list[tuple[int, int]] #agent_id, minion count
    learnable_character_skills: list[int] #populated at skill trainer and when using signet of capture
    unlocked_character_skills: list[int]

    def __init__(self) -> None: ...
    def GetContext(self) -> None: ...
    def SendDialog(self, dialog_id: int) -> None: ...
    def IsAgentIDValid(self, agent_id: int) -> bool: ...
    def GetChatHistory(self) -> List[str]: ...
    def RequestChatHistory(self) -> None: ...
    def Istyping(self) -> bool: ...
    def IsChatHistoryReady(self) -> bool: ...
    def SendChatCommand(self, msg: str) -> None: ...
    def SendChat(self, channel: str, msg: str) -> None: ...
    def SendWhisper(self, name: str, msg: str) -> None: ...
    def SendFakeChat(self, channel: int, msg: str) -> None: ...
    def SendFakeChatColored(self, channel: int, msg: str, r: int, g: int, b: int) -> None: ...

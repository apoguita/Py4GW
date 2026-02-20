#region STATES
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

#region PARTY
class _PARTY:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers

    def LeaveParty(self):
        self._helpers.Party.leave_party()

    def FlagHero(self, hero_index: int, x: float, y: float):
        """
        Flag a specific hero to a location by hero index.
        Args:
            hero_index (int): The 0-based index of the hero in the party (0 = first hero, 1 = second hero, etc.)
            x (float): The X coordinate
            y (float): The Y coordinate
        """
        self._helpers.Party.flag_hero(hero_index, x, y)

    def UnflagHero(self, hero_index: int):
        """
        Unflag a specific hero by hero index.
        Args:
            hero_index (int): The 0-based index of the hero in the party (0 = first hero, 1 = second hero, etc.)
        """
        self._helpers.Party.unflag_hero(hero_index)

    def FlagAllHeroes(self, x: float, y: float):
        self._helpers.Party.flag_all_heroes(x, y)

    def UnflagAllHeroes(self):
        self._helpers.Party.unflag_all_heroes()
    
    def SetHeroBehavior(self, hero_position: int, behavior: int):
        self._helpers.Party.set_hero_behavior(hero_position, behavior)
    
    def SetAllHeroesBehavior(self, behavior: int, delay_ms: int = 100):
        self._helpers.Party.set_all_heroes_behavior(behavior, delay_ms)

    def Resign(self):
        self._helpers.Party.resign()

    def SetHardMode(self, hard_mode: bool):
        self._helpers.Party.set_hard_mode(hard_mode)

    def AddHenchman(self, henchman_id: int):
        self._helpers.Party.add_henchman(henchman_id)
        
    def AddHenchmanList(self, henchman_id_list: List[int]):
        for henchman_id in henchman_id_list:
            self._helpers.Party.add_henchman(henchman_id)
    def AddHero(self, hero_id: int):
        self._helpers.Party.add_hero(hero_id)
        
    def AddHeroList(self, hero_id_list: List[int]):
        for hero_id in hero_id_list:
            self._helpers.Party.add_hero(hero_id)

    def InvitePlayer(self, player_name: str):
        self._helpers.Party.invite_player(player_name)

    def KickHenchman(self, henchman_id: int):
        self._helpers.Party.kick_henchman(henchman_id)

    def KickHero(self, hero_id: int):
        self._helpers.Party.kick_hero(hero_id)

    def KickPlayer(self, player_name: str):
        self._helpers.Party.kick_player(player_name)

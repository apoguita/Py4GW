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

    def FlagAllHeroes(self, x: float, y: float):
        self._helpers.Party.flag_all_heroes(x, y)

    def UnflagAllHeroes(self):
        self._helpers.Party.unflag_all_heroes()

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
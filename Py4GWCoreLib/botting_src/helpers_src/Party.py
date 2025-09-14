from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable

#region PARTY
class _Party:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events

    @_yield_step(label="LeaveParty", counter_key="LEAVE_PARTY")
    def leave_party(self):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        GLOBAL_CACHE.Party.LeaveParty()
        yield from Routines.Yield.wait(250)
    
    @_yield_step(label="AddHenchman", counter_key="ADD_HENCHMAN")    
    def add_henchman(self, henchman_id):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(henchman_id)
        yield from Routines.Yield.wait(250)

    @_yield_step(label="AddHero", counter_key="ADD_HERO")
    def add_hero(self, hero_id):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        GLOBAL_CACHE.Party.Heroes.AddHero(hero_id)
        yield from Routines.Yield.wait(250)
    
    @_yield_step(label="InvitePlayer", counter_key="INVITE_PLAYER")    
    def invite_player(self, player_name):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        GLOBAL_CACHE.Party.Players.InvitePlayer(player_name)
        yield from Routines.Yield.wait(250)

    @_yield_step(label="KickHenchman", counter_key="KICK_HENCHMAN")
    def kick_henchman(self, henchman_id):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        GLOBAL_CACHE.Party.Henchmen.KickHenchman(henchman_id)
        yield from Routines.Yield.wait(250)
        
    @_yield_step(label="KickHero", counter_key="KICK_HERO")
    def kick_hero(slef, hero_id):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        GLOBAL_CACHE.Party.Heroes.KickHero(hero_id)
        yield from Routines.Yield.wait(250)
        
    @_yield_step(label="KickPlayer", counter_key="KICK_PLAYER")
    def kick_player(self, player_name):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        GLOBAL_CACHE.Party.Players.KickPlayer(player_name)
        yield from Routines.Yield.wait(250)

    @_yield_step(label="FlagAllHeroes", counter_key="FLAG_ALL_HEROES")
    def flag_all_heroes(self, x, y):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        GLOBAL_CACHE.Party.Heroes.FlagAllHeroes(x,y)
        yield from Routines.Yield.wait(500)

    @_yield_step(label="UnflagAllHeroes", counter_key="FLAG_ALL_HEROES")
    def unflag_all_heroes(self):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()
        yield from Routines.Yield.wait(500)

    @_yield_step(label="Resign", counter_key="SEND_CHAT_MESSAGE")
    def resign(self):
        from ...Routines import Routines
        yield from Routines.Yield.Player.Resign()
        yield from Routines.Yield.wait(500)
        
    @_yield_step(label="SetHardMode", counter_key="SET_HARD_MODE")
    def set_hard_mode(self, is_hard_mode: bool):
        from ...Routines import Routines
        yield from Routines.Yield.Map.SetHardMode(is_hard_mode)

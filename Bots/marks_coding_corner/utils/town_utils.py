from Py4GWCoreLib import GLOBAL_CACHE, Map, Player
from Py4GWCoreLib import Routines


def return_to_outpost():
    if Map.IsOutpost():
        return

    is_explorable = Map.IsExplorable()
    while is_explorable:
        is_map_ready = Map.IsMapReady()
        is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated() or Player.GetMorale() < 100

        if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
            yield from Routines.Yield.Player.Resign()
            yield from Routines.Yield.wait(2000)
            GLOBAL_CACHE.Party.ReturnToOutpost()
        else:
            is_explorable = Map.IsExplorable()
            yield from Routines.Yield.wait(4000)

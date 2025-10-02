from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines


def return_to_outpost():
    if GLOBAL_CACHE.Map.IsOutpost():
        return

    is_explorable = GLOBAL_CACHE.Map.IsExplorable()
    while is_explorable:
        is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
        is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated() or GLOBAL_CACHE.Player.GetMorale() < 100

        if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
            yield from Routines.Yield.Player.Resign()
            yield from Routines.Yield.wait(2000)
            GLOBAL_CACHE.Party.ReturnToOutpost()
        else:
            is_explorable = GLOBAL_CACHE.Map.IsExplorable()
            yield from Routines.Yield.wait(4000)

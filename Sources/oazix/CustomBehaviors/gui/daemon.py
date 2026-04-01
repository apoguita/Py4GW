from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty

loader_throttler = ThrottledTimer(100)
refresh_throttler = ThrottledTimer(1_000)
heroai_fallack_mecanism_throttler = ThrottledTimer(500)

@staticmethod
def daemon():

    cb = CustomBehaviorLoader().custom_combat_behavior
    if loader_throttler.IsExpired(): 
        loader_throttler.Reset()
        loaded = CustomBehaviorLoader().initialize_custom_behavior_candidate()
        if loaded: return

    if refresh_throttler.IsExpired(): 
        refresh_throttler.Reset()
        if cb is not None:
            if not cb.is_custom_behavior_match_in_game_build():
                CustomBehaviorLoader().refresh_custom_behavior_candidate()
                return
            
    if heroai_fallack_mecanism_throttler.IsExpired(): 
        heroai_fallack_mecanism_throttler.Reset()

        from HeroAI.cache_data import CacheData
        cached_data: CacheData = CacheData()
        cached_data.UpdateCombat()

    # main loops
    if cb is not None:
        cb.act()

    CustomBehaviorParty().act()
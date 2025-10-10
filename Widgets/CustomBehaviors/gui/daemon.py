from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig import LootConfig
from Widgets.CustomBehaviors.primitives.auto_mover.auto_mover import AutoMover
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty

loader_throttler = ThrottledTimer(100)
refresh_throttler = ThrottledTimer(1_000)
heroai_fallack_mecanism_throttler = ThrottledTimer(500)

@staticmethod
def daemon():

    # LootConfig().AddToWhitelist(1682) # minotaur_horn
    # LootConfig().AddToWhitelist(1663) # pillaged_goods

    if loader_throttler.IsExpired(): 
        loader_throttler.Reset()
        loaded = CustomBehaviorLoader().initialize_custom_behavior_candidate()
        if loaded: return

    if refresh_throttler.IsExpired(): 
        refresh_throttler.Reset()
        if CustomBehaviorLoader().custom_combat_behavior is not None:
            if not CustomBehaviorLoader().custom_combat_behavior.is_custom_behavior_match_in_game_build():
                CustomBehaviorLoader().refresh_custom_behavior_candidate()
                return
            
    if heroai_fallack_mecanism_throttler.IsExpired(): 
        heroai_fallack_mecanism_throttler.Reset()

        from HeroAI.cache_data import CacheData
        cached_data: CacheData = CacheData()
        
        from HeroAI.players import RegisterHeroes, RegisterPlayer, UpdatePlayers
        RegisterPlayer(cached_data)
        RegisterHeroes(cached_data)
        UpdatePlayers(cached_data)
        cached_data.UdpateCombat()

    # main loops

    if CustomBehaviorLoader().custom_combat_behavior is not None:
        CustomBehaviorLoader().custom_combat_behavior.act()

    CustomBehaviorParty().act()
    
    AutoMover().act()
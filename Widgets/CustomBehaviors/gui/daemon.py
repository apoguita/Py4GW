from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig import LootConfig
from Widgets.CustomBehaviors.primitives.auto_mover.auto_mover import AutoMover
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty

loader_throttler = ThrottledTimer(100)
refresh_throttler = ThrottledTimer(1_000)

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

    # main loops

    if CustomBehaviorLoader().custom_combat_behavior is not None:
        CustomBehaviorLoader().custom_combat_behavior.act()

    CustomBehaviorParty().act()
    
    AutoMover().act()
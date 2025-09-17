from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, LootConfig, ThrottledTimer
from Widgets.CustomBehaviors.primitives.auto_mover.auto_mover import FollowPathExecutor
from Widgets.CustomBehaviors.primitives.auto_mover.auto_mover import AutoMover
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader

loader_throttler = ThrottledTimer(100)
refresh_throttler = ThrottledTimer(1_000)

@staticmethod
def daemon():

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

    # main loop
    if CustomBehaviorLoader().custom_combat_behavior is not None:
        CustomBehaviorLoader().custom_combat_behavior.act()

    AutoMover().act()

    # ActionQueueManager().ProcessQueue("ACTION")



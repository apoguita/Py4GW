from HeroAI.cache_data import CacheData
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader


@staticmethod
def deamon(manual_disable_heroai=True):
    CustomBehaviorLoader().initialize_custom_behavior_candidate()

    if CustomBehaviorLoader().custom_combat_behavior is not None:
        CustomBehaviorLoader().ensure_custom_behavior_match_in_game_build()

    if CustomBehaviorLoader().custom_combat_behavior is not None:
        CustomBehaviorLoader().custom_combat_behavior.act(  # type: ignore
            CacheData(), manual_disable_heroai=manual_disable_heroai
        )

    ActionQueueManager().ProcessQueue("ACTION")

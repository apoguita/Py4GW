from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader


@staticmethod
def deamon():
    CustomBehaviorLoader().initialize_custom_behavior_candidate()

    if CustomBehaviorLoader().custom_combat_behavior is not None:
        if not CustomBehaviorLoader().custom_combat_behavior.is_custom_behavior_match_in_game_build():
            CustomBehaviorLoader().refresh_custom_behavior_candidate()

    if CustomBehaviorLoader().custom_combat_behavior is not None:
        CustomBehaviorLoader().custom_combat_behavior.act()

    ActionQueueManager().ProcessQueue("ACTION")

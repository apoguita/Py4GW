from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, LootConfig
from Widgets.CustomBehaviors.primitives.auto_mover.auto_mover import AutoMover
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader


@staticmethod
def daemon():
    CustomBehaviorLoader().initialize_custom_behavior_candidate()

    if CustomBehaviorLoader().custom_combat_behavior is not None:
        if not CustomBehaviorLoader().custom_combat_behavior.is_custom_behavior_match_in_game_build():
            CustomBehaviorLoader().refresh_custom_behavior_candidate()

    if CustomBehaviorLoader().custom_combat_behavior is not None:
        CustomBehaviorLoader().custom_combat_behavior.act()

    AutoMover().act()

    ActionQueueManager().ProcessQueue("ACTION")



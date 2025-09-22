from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig import LootConfig
from Widgets.CustomBehaviors.primitives.auto_mover.auto_mover import AutoMover
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract
from Widgets.CustomBehaviors.primitives.botting.botting_loader import BottingLoader
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader

loader_throttler = ThrottledTimer(100)
refresh_throttler = ThrottledTimer(1_000)

@staticmethod
def daemon_botting(widget_window_size:tuple[float, float], widget_window_pos:tuple[float, float]):

    is_executing_utility_skills:bool = False

    if CustomBehaviorLoader().custom_combat_behavior is not None:
        is_executing_utility_skills = CustomBehaviorLoader().custom_combat_behavior.is_executing_utility_skills()

    bot:BottingAbstract | None = BottingLoader().get_active_bot()
    if bot is not None:
        bot.render(widget_window_size, widget_window_pos)
        if not is_executing_utility_skills:
            bot.act()
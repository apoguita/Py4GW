from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Sources.oazix.CustomBehaviors.primitives.auto_mover.auto_follow_agent import AutoFollowAgent
from Sources.oazix.CustomBehaviors.primitives.auto_mover.auto_follow_path import AutoFollowPath
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.hero_ai_wrapping.hero_ai_wrapping import HeroAiWrapping
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty

loader_throttler = ThrottledTimer(100)
refresh_throttler = ThrottledTimer(1_000)

@staticmethod
def daemon():
    loader = CustomBehaviorLoader()

    # Ensure botting daemon is registered with FSM (handles re-registration after FSM restart)
    loader.ensure_botting_daemon_running()

    player_behavior = loader.custom_combat_behavior
    if loader_throttler.IsExpired():
        loader_throttler.Reset()
        loaded = loader.initialize_custom_behavior_candidate()
        if loaded: return

    if refresh_throttler.IsExpired():
        refresh_throttler.Reset()
        if player_behavior is not None:
            if not player_behavior.is_custom_behavior_match_in_game_build():
                loader.refresh_custom_behavior_candidate()
                return

    HeroAiWrapping().act()
    # main loops
    if player_behavior is not None:
        player_behavior.act()

    CustomBehaviorParty().act()
    AutoFollowPath().act()
    AutoFollowAgent().act()
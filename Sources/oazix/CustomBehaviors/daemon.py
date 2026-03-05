import importlib
import os
import sys
import time
from copy import deepcopy
from types import ModuleType

from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Sources.oazix.CustomBehaviors.primitives.auto_mover.auto_follow_agent import AutoFollowAgent
from Sources.oazix.CustomBehaviors.primitives.auto_mover.auto_follow_path import AutoFollowPath
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.hero_ai_wrapping.hero_ai_wrapping import HeroAiWrapping
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_utility import DropTrackerSender

loader_throttler = ThrottledTimer(100)
refresh_throttler = ThrottledTimer(1_000)

_DROP_TRACKER_RELOAD_SCAN_INTERVAL_S = 1.0
_DROP_TRACKER_LAST_RELOAD_SCAN_TS = 0.0
_DROP_TRACKER_RELOAD_MTIMES: dict[str, float] = {}
_DROP_TRACKER_RELOAD_IN_PROGRESS = False
_DROP_TRACKER_SENDER_UNSAFE_TYPE_NAMES = {
    "Pattern",
    "ThrottledTimer",
}
_DROP_TRACKER_SENDER_EXCLUDED_FIELDS = {
    "gold_regex",
    "mod_db",
    "runtime_config_path",
    "live_debug_log_path",
}


def _module_file_mtime(path: str) -> float | None:
    try:
        return float(os.path.getmtime(path))
    except OSError:
        return None


def _iter_drop_tracker_reload_targets() -> list[tuple[str, ModuleType, str]]:
    module_targets: list[tuple[str, ModuleType, str]] = []
    for module_name, module in tuple(sys.modules.items()):
        if module is None:
            continue
        include = (
            module_name == "Sources.oazix.CustomBehaviors.skills.monitoring.item_mod_render_utils"
            or module_name == "Sources.oazix.CustomBehaviors.primitives.helpers.map_instance_helper"
            or module_name.startswith("Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_")
        )
        if not include:
            continue
        module_path = getattr(module, "__file__", "")
        if not isinstance(module_path, str) or not module_path.endswith(".py"):
            continue
        module_targets.append((module_name, module, module_path))
    module_targets.sort(key=lambda item: (item[0].endswith("drop_tracker_utility"), item[0]))
    return module_targets


def _capture_drop_tracker_sender_state(sender) -> dict[str, object]:
    state: dict[str, object] = {}
    for key, value in vars(sender).items():
        if key in _DROP_TRACKER_SENDER_EXCLUDED_FIELDS or key.endswith("_timer"):
            continue
        if callable(value):
            continue
        if type(value).__name__ in _DROP_TRACKER_SENDER_UNSAFE_TYPE_NAMES:
            continue
        try:
            state[key] = deepcopy(value)
        except Exception:
            continue
    return state


def _apply_drop_tracker_sender_state(sender, state: dict[str, object] | None) -> None:
    if not isinstance(state, dict):
        return
    for key, value in state.items():
        if key in _DROP_TRACKER_SENDER_EXCLUDED_FIELDS or not hasattr(sender, key):
            continue
        try:
            setattr(sender, key, deepcopy(value))
        except Exception:
            continue
    try:
        sender._load_runtime_config()
    except Exception:
        pass


def _reload_drop_tracker_runtime(module_targets: list[tuple[str, ModuleType, str]]) -> None:
    global DropTrackerSender
    global _DROP_TRACKER_LAST_RELOAD_SCAN_TS
    global _DROP_TRACKER_RELOAD_MTIMES
    global _DROP_TRACKER_RELOAD_IN_PROGRESS

    current_sender = DropTrackerSender()
    sender_state = _capture_drop_tracker_sender_state(current_sender)
    _DROP_TRACKER_RELOAD_IN_PROGRESS = True
    importlib.invalidate_caches()

    try:
        for module_name, module, _module_path in module_targets:
            importlib.reload(module)
        tracker_module = sys.modules["Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_utility"]
        DropTrackerSender = getattr(tracker_module, "DropTrackerSender")
        refreshed_sender = DropTrackerSender()
        _apply_drop_tracker_sender_state(refreshed_sender, sender_state)
        _DROP_TRACKER_RELOAD_MTIMES = {
            module_path: mtime
            for _module_name, _module, module_path in _iter_drop_tracker_reload_targets()
            for mtime in [_module_file_mtime(module_path)]
            if mtime is not None
        }
        _DROP_TRACKER_LAST_RELOAD_SCAN_TS = time.time()
    finally:
        _DROP_TRACKER_RELOAD_IN_PROGRESS = False


def _maybe_refresh_drop_tracker_runtime() -> None:
    global _DROP_TRACKER_LAST_RELOAD_SCAN_TS
    global _DROP_TRACKER_RELOAD_MTIMES

    if _DROP_TRACKER_RELOAD_IN_PROGRESS:
        return

    now = time.time()
    if (now - _DROP_TRACKER_LAST_RELOAD_SCAN_TS) < _DROP_TRACKER_RELOAD_SCAN_INTERVAL_S:
        return

    _DROP_TRACKER_LAST_RELOAD_SCAN_TS = now
    module_targets = _iter_drop_tracker_reload_targets()
    latest_mtimes: dict[str, float] = {}
    changed = False

    for _module_name, _module, module_path in module_targets:
        mtime = _module_file_mtime(module_path)
        if mtime is None:
            continue
        latest_mtimes[module_path] = mtime
        previous_mtime = _DROP_TRACKER_RELOAD_MTIMES.get(module_path)
        if previous_mtime is not None and mtime > previous_mtime:
            changed = True

    if not _DROP_TRACKER_RELOAD_MTIMES:
        _DROP_TRACKER_RELOAD_MTIMES = latest_mtimes
        return

    if not changed:
        _DROP_TRACKER_RELOAD_MTIMES.update(latest_mtimes)
        return

    _reload_drop_tracker_runtime(module_targets)

@staticmethod
def daemon():
    _maybe_refresh_drop_tracker_runtime()
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
    DropTrackerSender().act()
    # main loops
    if player_behavior is not None:
        player_behavior.act()

    CustomBehaviorParty().act()
    AutoFollowPath().act()
    AutoFollowAgent().act()

from __future__ import annotations

from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..BehaviourTrees import BT


def wait(ms: int, break_on_map_transition: bool = False):
    import time
    def _map_transition_detected() -> bool:
        return False

    if break_on_map_transition:
        from ..Checks import Checks
        from ...Map import Map as _Map

        initial_map_id = _Map.GetMapID()
        initial_district = _Map.GetDistrict()
        initial_region_id = _Map.GetRegion()[0]
        initial_language_id = _Map.GetLanguage()[0]
        initial_instance_uptime = _Map.GetInstanceUptime()

        def _map_transition_detected() -> bool:
            if _Map.IsInCinematic():
                return True
            if not Checks.Map.MapValid() or _Map.IsMapLoading():
                return True
            if _Map.GetMapID() != initial_map_id:
                return True
            if _Map.GetDistrict() != initial_district:
                return True
            if _Map.GetRegion()[0] != initial_region_id:
                return True
            if _Map.GetLanguage()[0] != initial_language_id:
                return True

            current_instance_uptime = _Map.GetInstanceUptime()
            if initial_instance_uptime > 0 and current_instance_uptime + 2000 < initial_instance_uptime:
                return True

            return False

    start = time.time()
    while (time.time() - start) * 1000 < ms:
        if break_on_map_transition and _map_transition_detected():
            break
        yield


def _run_bt_tree(tree, return_bool: bool = False, throttle_ms: int = 100):
    """
    Drives a BT tree until SUCCESS / FAILURE, yielding periodically.
    Always yields at least once to guarantee cooperative scheduling.
    If return_bool is True -> returns True/False.
    If return_bool is False -> just exits.
    """
    while True:
        state = BehaviorTree.Node._normalize_state(tree.tick())
        if state is None:
            raise TypeError("Yield runner received a non-NodeState tree result.")

        if state in (BT.NodeState.SUCCESS, BT.NodeState.FAILURE):
            yield
            if return_bool:
                return state == BT.NodeState.SUCCESS
            return

        yield from wait(throttle_ms)

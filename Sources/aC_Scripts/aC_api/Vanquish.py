from Py4GWCoreLib import *

_vanquish_timer = ThrottledTimer(1000)  # 1 second
_cached_vanquish = {"killed": 0, "total": 0, "valid": False}

def draw_vanquish_status(label: str = "Vanquish Status"):
    if not Routines.Checks.Map.MapValid():
        return
    if not Map.IsExplorable():
        return
    """
    Displays vanquish status with kills, total, and percent.
    Updates once per second via cached values.
    """
    global _cached_vanquish

    if _vanquish_timer.IsExpired():
        ready = (
            Map.IsMapReady() and
            GLOBAL_CACHE.Party.IsPartyLoaded() and
            Map.IsExplorable() and
            Map.IsVanquishable() and
            GLOBAL_CACHE.Party.IsHardMode()
        )
        _cached_vanquish["valid"] = ready
        if ready:
            _cached_vanquish["killed"] = Map.GetFoesKilled()
            _cached_vanquish["total"] = Map.GetFoesToKill()
        _vanquish_timer.Reset()

    if _cached_vanquish["valid"]:
        killed = _cached_vanquish["killed"]
        total = _cached_vanquish["total"] + killed
        percent = (killed / total * 100) if total > 0 else 0
        PyImGui.text(f"{label}: {killed:,} / {total:,} ({percent:.1f}%)")
    else:
        PyImGui.text(f"{label}: N/A")

__all__ = ["draw_vanquish_status"]

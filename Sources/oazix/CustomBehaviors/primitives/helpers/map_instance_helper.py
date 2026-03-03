from __future__ import annotations

INSTANCE_UPTIME_ROLLBACK_GRACE_MS = 2000


def read_current_map_instance() -> tuple[int, int]:
    from Py4GWCoreLib import Map

    try:
        current_map_id = max(0, int(Map.GetMapID() or 0))
    except Exception:
        current_map_id = 0
    try:
        current_instance_uptime_ms = max(0, int(Map.GetInstanceUptime() or 0))
    except Exception:
        current_instance_uptime_ms = 0
    return current_map_id, current_instance_uptime_ms


def classify_map_instance_transition(
    previous_map_id: int,
    previous_instance_uptime_ms: int,
    current_map_id: int,
    current_instance_uptime_ms: int,
    uptime_rollback_grace_ms: int = INSTANCE_UPTIME_ROLLBACK_GRACE_MS,
) -> str:
    prev_map_id = max(0, int(previous_map_id or 0))
    prev_uptime_ms = max(0, int(previous_instance_uptime_ms or 0))
    map_id = max(0, int(current_map_id or 0))
    uptime_ms = max(0, int(current_instance_uptime_ms or 0))
    rollback_grace_ms = max(0, int(uptime_rollback_grace_ms or 0))

    if prev_map_id <= 0 or map_id <= 0:
        return ""
    if map_id != prev_map_id:
        return "map_change"
    if prev_uptime_ms > 0 and uptime_ms > 0 and (uptime_ms + rollback_grace_ms) < prev_uptime_ms:
        return "instance_change"
    return ""


def has_new_map_instance(
    previous_map_id: int,
    previous_instance_uptime_ms: int,
    current_map_id: int,
    current_instance_uptime_ms: int,
    uptime_rollback_grace_ms: int = INSTANCE_UPTIME_ROLLBACK_GRACE_MS,
) -> bool:
    return bool(
        classify_map_instance_transition(
            previous_map_id=previous_map_id,
            previous_instance_uptime_ms=previous_instance_uptime_ms,
            current_map_id=current_map_id,
            current_instance_uptime_ms=current_instance_uptime_ms,
            uptime_rollback_grace_ms=uptime_rollback_grace_ms,
        )
    )

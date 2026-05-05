from __future__ import annotations

import Py4GW

from Py4GWCoreLib.enums_src.Whiteboard_enums import (
    WhiteboardClaimStrength,
    WhiteboardLockKind,
    WhiteboardLockMode,
    WhiteboardReentryPolicy,
)

from ..py4gwcorelib_src.FrameCache import frame_cache


MINION_LOCK_KEY = 0
MINION_LOCK_MIN_DURATION_MS = 500
RESURRECTION_LOCK_KEY = 0
RESURRECTION_LOCK_MIN_DURATION_MS = 1000
HEX_REMOVAL_LOCK_KEY = 0
HEX_REMOVAL_LOCK_MIN_DURATION_MS = 750


@frame_cache(category="WhiteboardLocks", source_lib="OwnerContext")
def _owner_context() -> tuple[str, int]:
    from Py4GWCoreLib import GLOBAL_CACHE, Player

    email = Player.GetAccountEmail() or ""
    if not email:
        return "", 0
    try:
        group_id = int(GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(email))
    except Exception:
        group_id = 0
    return email, group_id


def _skill_lock_duration_ms(skill_id: int, aftercast_delay: int = 250, minimum_ms: int = 500) -> int:
    from Py4GWCoreLib import GLOBAL_CACHE
    from Py4GWCoreLib.GlobalCache.shared_memory_src.Globals import (
        SHMEM_INTENT_DEFAULT_PING_BUDGET_MS,
    )

    activation_ms = 0
    aftercast_ms = 0
    try:
        activation_ms = int((GLOBAL_CACHE.Skill.Data.GetActivation(skill_id) or 0) * 1000)
    except Exception:
        pass
    try:
        aftercast_ms = int((GLOBAL_CACHE.Skill.Data.GetAftercast(skill_id) or 0) * 1000)
    except Exception:
        pass
    if aftercast_ms <= 0:
        aftercast_ms = int(aftercast_delay)
    return (
        max(int(minimum_ms), activation_ms + aftercast_ms)
        + int(SHMEM_INTENT_DEFAULT_PING_BUDGET_MS)
    )


def is_minion_lock_blocked(corpse_agent_id: int, now_tick: int | None = None) -> bool:
    """True when another account already reserved this corpse for minion creation."""
    if corpse_agent_id <= 0:
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return False
        if now_tick is None:
            now_tick = int(Py4GW.Game.get_tick_count64())
        return bool(GLOBAL_CACHE.ShMem.IsLockBlocked(
            int(WhiteboardLockKind.MINION_CORPSE),
            MINION_LOCK_KEY,
            int(corpse_agent_id),
            int(group_id),
            email,
            int(now_tick),
            int(WhiteboardLockMode.EXCLUSIVE),
            1,
            int(WhiteboardReentryPolicy.OWNER_REENTRANT),
            int(WhiteboardClaimStrength.HARD),
        ))
    except Exception:
        return False


def filter_unlocked_minion_corpses(corpse_agent_ids: list[int]) -> list[int]:
    """Return corpses not currently held by a Minion Lock."""
    if not corpse_agent_ids:
        return []
    now_tick = int(Py4GW.Game.get_tick_count64())
    return [
        int(corpse_id)
        for corpse_id in corpse_agent_ids
        if corpse_id and not is_minion_lock_blocked(int(corpse_id), now_tick)
    ]


def post_minion_lock(corpse_agent_id: int, skill_id: int = 0, aftercast_delay: int = 250) -> int:
    """Reserve a corpse for minion creation. Returns slot index or -1."""
    if corpse_agent_id <= 0:
        return -1
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return -1
        now = int(Py4GW.Game.get_tick_count64())
        expires_at = now + _skill_lock_duration_ms(
            int(skill_id),
            int(aftercast_delay),
            MINION_LOCK_MIN_DURATION_MS,
        )
        return int(GLOBAL_CACHE.ShMem.PostLock(
            email,
            int(WhiteboardLockKind.MINION_CORPSE),
            MINION_LOCK_KEY,
            int(corpse_agent_id),
            int(expires_at),
            int(group_id),
            int(WhiteboardLockMode.EXCLUSIVE),
            1,
            int(WhiteboardReentryPolicy.OWNER_REENTRANT),
            int(WhiteboardClaimStrength.HARD),
        ))
    except Exception:
        return -1


def is_resurrection_lock_blocked(dead_ally_agent_id: int, now_tick: int | None = None) -> bool:
    """True when another account already reserved this ally for resurrection."""
    if dead_ally_agent_id <= 0:
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return False
        if now_tick is None:
            now_tick = int(Py4GW.Game.get_tick_count64())
        return bool(GLOBAL_CACHE.ShMem.IsLockBlocked(
            int(WhiteboardLockKind.RESURRECT_TARGET),
            RESURRECTION_LOCK_KEY,
            int(dead_ally_agent_id),
            int(group_id),
            email,
            int(now_tick),
            int(WhiteboardLockMode.EXCLUSIVE),
            1,
            int(WhiteboardReentryPolicy.OWNER_REENTRANT),
            int(WhiteboardClaimStrength.HARD),
        ))
    except Exception:
        return False


def filter_unlocked_resurrection_targets(dead_ally_agent_ids: list[int]) -> list[int]:
    """Return dead allies not currently held by a Resurrection Lock."""
    if not dead_ally_agent_ids:
        return []
    now_tick = int(Py4GW.Game.get_tick_count64())
    return [
        int(agent_id)
        for agent_id in dead_ally_agent_ids
        if agent_id and not is_resurrection_lock_blocked(int(agent_id), now_tick)
    ]


def post_resurrection_lock(dead_ally_agent_id: int, skill_id: int = 0, aftercast_delay: int = 250) -> int:
    """Reserve a dead ally for resurrection. Returns slot index or -1."""
    if dead_ally_agent_id <= 0:
        return -1
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return -1
        now = int(Py4GW.Game.get_tick_count64())
        expires_at = now + _skill_lock_duration_ms(
            int(skill_id),
            int(aftercast_delay),
            RESURRECTION_LOCK_MIN_DURATION_MS,
        )
        return int(GLOBAL_CACHE.ShMem.PostLock(
            email,
            int(WhiteboardLockKind.RESURRECT_TARGET),
            RESURRECTION_LOCK_KEY,
            int(dead_ally_agent_id),
            int(expires_at),
            int(group_id),
            int(WhiteboardLockMode.EXCLUSIVE),
            1,
            int(WhiteboardReentryPolicy.OWNER_REENTRANT),
            int(WhiteboardClaimStrength.HARD),
        ))
    except Exception:
        return -1


def is_hex_removal_lock_blocked(hexed_ally_agent_id: int, now_tick: int | None = None) -> bool:
    """True when another account already reserved this ally for hex removal."""
    if hexed_ally_agent_id <= 0:
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return False
        if now_tick is None:
            now_tick = int(Py4GW.Game.get_tick_count64())
        return bool(GLOBAL_CACHE.ShMem.IsLockBlocked(
            int(WhiteboardLockKind.HEX_REMOVAL_TARGET),
            HEX_REMOVAL_LOCK_KEY,
            int(hexed_ally_agent_id),
            int(group_id),
            email,
            int(now_tick),
            int(WhiteboardLockMode.EXCLUSIVE),
            1,
            int(WhiteboardReentryPolicy.OWNER_REENTRANT),
            int(WhiteboardClaimStrength.HARD),
        ))
    except Exception:
        return False


def filter_unlocked_hex_targets(hexed_ally_agent_ids: list[int]) -> list[int]:
    """Return hexed allies not currently held by a Hex Removal Lock."""
    if not hexed_ally_agent_ids:
        return []
    now_tick = int(Py4GW.Game.get_tick_count64())
    return [
        int(agent_id)
        for agent_id in hexed_ally_agent_ids
        if agent_id and not is_hex_removal_lock_blocked(int(agent_id), now_tick)
    ]


def post_hex_removal_lock(hexed_ally_agent_id: int, skill_id: int = 0, aftercast_delay: int = 250) -> int:
    """Reserve a hexed ally for hex removal. Returns slot index or -1.

    Self-lock dedup: if this owner already holds an active lock on this
    target in the same group, returns the existing slot. Without dedup,
    multi-tier rotations (HIGH/MED/LOW) post one lock per tier per tick
    while the previous cast hasn't yet bumped recharge.
    """
    if hexed_ally_agent_id <= 0:
        return -1
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return -1
        now = int(Py4GW.Game.get_tick_count64())

        # Drop expired-but-not-yet-swept entries so a stale lock can't suppress a fresh POST.
        for slot_index, intent in GLOBAL_CACHE.ShMem.GetAllAccounts().GetAllIntents():
            if intent.OwnerEmail != email:
                continue
            if int(intent.KindID) != int(WhiteboardLockKind.HEX_REMOVAL_TARGET):
                continue
            if int(intent.TargetAgentID) != int(hexed_ally_agent_id):
                continue
            if int(intent.IsolationGroupID) != int(group_id):
                continue
            if int(intent.ExpiresAtTick) <= now:
                continue
            return int(slot_index)

        expires_at = now + _skill_lock_duration_ms(
            int(skill_id),
            int(aftercast_delay),
            HEX_REMOVAL_LOCK_MIN_DURATION_MS,
        )
        return int(GLOBAL_CACHE.ShMem.PostLock(
            email,
            int(WhiteboardLockKind.HEX_REMOVAL_TARGET),
            HEX_REMOVAL_LOCK_KEY,
            int(hexed_ally_agent_id),
            int(expires_at),
            int(group_id),
            int(WhiteboardLockMode.EXCLUSIVE),
            1,
            int(WhiteboardReentryPolicy.OWNER_REENTRANT),
            int(WhiteboardClaimStrength.HARD),
        ))
    except Exception:
        return -1


def clear_hex_removal_lock(hexed_ally_agent_id: int) -> bool:
    """Release the local hex-removal lock early after a successful cleanse.

    Returns True if at least one matching lock was cleared.
    """
    if hexed_ally_agent_id <= 0:
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return False
        cleared = int(GLOBAL_CACHE.ShMem.ClearLockByOwnerKindTarget(
            email,
            int(WhiteboardLockKind.HEX_REMOVAL_TARGET),
            int(hexed_ally_agent_id),
            int(group_id),
        ))
        return cleared > 0
    except Exception:
        return False

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
LOOT_LOCK_KEY = 0
LOOT_LOCK_MIN_DURATION_MS = 4000
BUFF_TARGET_LOCK_KEY = 0
BUFF_TARGET_LOCK_MIN_DURATION_MS = 1000
BLOOD_ENERGY_BUFF_LOCK_KEY = 1


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


def get_resurrection_lock_owner(dead_ally_agent_id: int, now_tick: int | None = None) -> tuple[str, int]:
    """Return the effective owner email and slot for a resurrection target lock."""
    if dead_ally_agent_id <= 0:
        return "", -1
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return "", -1
        if now_tick is None:
            now_tick = int(Py4GW.Game.get_tick_count64())

        winner = None
        for slot_index, intent in GLOBAL_CACHE.ShMem.GetAllAccounts().GetAllIntents():
            if int(intent.KindID) != int(WhiteboardLockKind.RESURRECT_TARGET):
                continue
            if int(intent.SkillID) != int(RESURRECTION_LOCK_KEY):
                continue
            if int(intent.TargetAgentID) != int(dead_ally_agent_id):
                continue
            if int(intent.IsolationGroupID) != int(group_id):
                continue
            if int(intent.ExpiresAtTick) <= int(now_tick):
                continue
            candidate = (int(intent.PostedAtTick), int(slot_index), intent.OwnerEmail or "")
            if winner is None or candidate < winner:
                winner = candidate

        if winner is None:
            return "", -1
        return winner[2], winner[1]
    except Exception:
        return "", -1


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

        owner_email, owner_slot = get_resurrection_lock_owner(dead_ally_agent_id, now)
        if owner_email:
            if owner_email == email:
                return int(owner_slot)
            return -1

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


def is_buff_target_lock_blocked(buffed_ally_agent_id: int, key_id: int = BUFF_TARGET_LOCK_KEY, now_tick: int | None = None) -> bool:
    """True when another account already reserved this ally for a shared buff cast."""
    if buffed_ally_agent_id <= 0:
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return False
        if now_tick is None:
            now_tick = int(Py4GW.Game.get_tick_count64())
        return bool(GLOBAL_CACHE.ShMem.IsLockBlocked(
            int(WhiteboardLockKind.BUFF_TARGET),
            int(key_id),
            int(buffed_ally_agent_id),
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


def post_buff_target_lock(
    buffed_ally_agent_id: int,
    *,
    key_id: int = BUFF_TARGET_LOCK_KEY,
    skill_id: int = 0,
    aftercast_delay: int = 250,
) -> int:
    """Reserve an ally for a shared buff cast. Returns slot index or -1."""
    if buffed_ally_agent_id <= 0:
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
            if int(intent.KindID) != int(WhiteboardLockKind.BUFF_TARGET):
                continue
            if int(intent.SkillID) != int(key_id):
                continue
            if int(intent.TargetAgentID) != int(buffed_ally_agent_id):
                continue
            if int(intent.IsolationGroupID) != int(group_id):
                continue
            if int(intent.ExpiresAtTick) <= now:
                continue
            return int(slot_index)

        expires_at = now + _skill_lock_duration_ms(
            int(skill_id),
            int(aftercast_delay),
            BUFF_TARGET_LOCK_MIN_DURATION_MS,
        )
        return int(GLOBAL_CACHE.ShMem.PostLock(
            email,
            int(WhiteboardLockKind.BUFF_TARGET),
            int(key_id),
            int(buffed_ally_agent_id),
            int(expires_at),
            int(group_id),
            int(WhiteboardLockMode.EXCLUSIVE),
            1,
            int(WhiteboardReentryPolicy.OWNER_REENTRANT),
            int(WhiteboardClaimStrength.HARD),
        ))
    except Exception:
        return -1


def claim_resurrection_target(dead_ally_agent_ids: list[int], skill_id: int = 0, aftercast_delay: int = 250) -> int:
    """Claim the first available dead ally through the whiteboard and return its agent id."""
    if not dead_ally_agent_ids:
        return 0
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return 0

        for dead_ally_id in dead_ally_agent_ids:
            now = int(Py4GW.Game.get_tick_count64())
            owner_email, _ = get_resurrection_lock_owner(int(dead_ally_id), now)
            if owner_email:
                if owner_email == email:
                    return int(dead_ally_id)
                continue

            lock_slot = post_resurrection_lock(
                int(dead_ally_id),
                skill_id=skill_id,
                aftercast_delay=aftercast_delay,
            )
            if lock_slot < 0:
                continue

            owner_email, owner_slot = get_resurrection_lock_owner(int(dead_ally_id))
            if owner_email == email and int(owner_slot) == int(lock_slot):
                return int(dead_ally_id)

            GLOBAL_CACHE.ShMem.GetAllAccounts().ClearLockByOwnerKindTarget(
                email,
                int(WhiteboardLockKind.RESURRECT_TARGET),
                int(dead_ally_id),
                int(group_id),
            )
    except Exception:
        return 0
    return 0


def filter_unlocked_buff_targets(ally_agent_ids: list[int], key_id: int = BUFF_TARGET_LOCK_KEY) -> list[int]:
    """Return allies not currently held by a buff-target lock for ``key_id``."""
    if not ally_agent_ids:
        return []
    now_tick = int(Py4GW.Game.get_tick_count64())
    return [
        int(agent_id)
        for agent_id in ally_agent_ids
        if agent_id and not is_buff_target_lock_blocked(int(agent_id), int(key_id), now_tick)
    ]


def is_loot_lock_blocked(item_agent_id: int, now_tick: int | None = None) -> bool:
    """True when another account already reserved this ground item for pickup."""
    if item_agent_id <= 0:
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return False
        if now_tick is None:
            now_tick = int(Py4GW.Game.get_tick_count64())
        return bool(GLOBAL_CACHE.ShMem.IsLockBlocked(
            int(WhiteboardLockKind.LOOT_ITEM),
            LOOT_LOCK_KEY,
            int(item_agent_id),
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


def filter_unlocked_loot_items(item_agent_ids: list[int]) -> list[int]:
    """Return ground items not currently held by a loot lock."""
    if not item_agent_ids:
        return []
    now_tick = int(Py4GW.Game.get_tick_count64())
    return [
        int(agent_id)
        for agent_id in item_agent_ids
        if agent_id and not is_loot_lock_blocked(int(agent_id), now_tick)
    ]


def post_loot_lock(item_agent_id: int, minimum_ms: int = LOOT_LOCK_MIN_DURATION_MS) -> int:
    """Reserve a ground item for loot pickup. Returns slot index or -1."""
    if item_agent_id <= 0:
        return -1
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return -1
        now = int(Py4GW.Game.get_tick_count64())

        for slot_index, intent in GLOBAL_CACHE.ShMem.GetAllAccounts().GetAllIntents():
            if intent.OwnerEmail != email:
                continue
            if int(intent.KindID) != int(WhiteboardLockKind.LOOT_ITEM):
                continue
            if int(intent.TargetAgentID) != int(item_agent_id):
                continue
            if int(intent.IsolationGroupID) != int(group_id):
                continue
            if int(intent.ExpiresAtTick) <= now:
                continue
            return int(slot_index)

        expires_at = now + max(int(minimum_ms), LOOT_LOCK_MIN_DURATION_MS)
        return int(GLOBAL_CACHE.ShMem.PostLock(
            email,
            int(WhiteboardLockKind.LOOT_ITEM),
            LOOT_LOCK_KEY,
            int(item_agent_id),
            int(expires_at),
            int(group_id),
            int(WhiteboardLockMode.EXCLUSIVE),
            1,
            int(WhiteboardReentryPolicy.OWNER_REENTRANT),
            int(WhiteboardClaimStrength.HARD),
        ))
    except Exception:
        return -1


def clear_loot_lock(item_agent_id: int) -> bool:
    """Release the local loot lock early after a successful pickup or skip."""
    if item_agent_id <= 0:
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        email, group_id = _owner_context()
        if not email:
            return False
        cleared = int(GLOBAL_CACHE.ShMem.ClearLockByOwnerKindTarget(
            email,
            int(WhiteboardLockKind.LOOT_ITEM),
            int(item_agent_id),
            int(group_id),
        ))
        return cleared > 0
    except Exception:
        return False

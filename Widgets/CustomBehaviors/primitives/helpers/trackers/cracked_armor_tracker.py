# python
import time
from typing import Optional

# Maps agent_id -> expiration timestamp
_cracked_armor_expiry: dict[int, float] = {}


def record_cracked_armor(agent_id: int, duration: float) -> None:
    """Record that Cracked Armor was applied on agent_id with the given duration in seconds."""
    if agent_id is None:
        return
    now = time.time()
    _cracked_armor_expiry[int(agent_id)] = now + float(duration)
    # Cleanup expired entries
    _cleanup_expired(now)


def has_cracked_armor(agent_id: Optional[int]) -> bool:
    """Return True if agent currently has Cracked Armor (not expired)."""
    if agent_id is None:
        return False
    expiry = _cracked_armor_expiry.get(int(agent_id))
    if expiry is None:
        return False
    return time.time() < expiry


def _cleanup_expired(now: float) -> None:
    """Remove entries that have expired."""
    to_remove = [aid for aid, expiry in _cracked_armor_expiry.items() if now >= expiry]
    for aid in to_remove:
        del _cracked_armor_expiry[aid]


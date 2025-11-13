# python
import time
from typing import Optional

_WINDOW_SECONDS = 10.0
_recent_glimmers: dict[int, float] = {}


def record_glimmer_on(agent_id: int) -> None:
    """Record that Glimmering_Mark was cast on agent_id now."""
    if agent_id is None:
        return
    _recent_glimmers[int(agent_id)] = time.time()


def had_glimmer_recently(agent_id: Optional[int], window_seconds: float = _WINDOW_SECONDS) -> bool:
    """Return True if agent had Glimmering_Mark recorded within the last `window_seconds`."""
    if agent_id is None:
        return False
    ts = _recent_glimmers.get(int(agent_id))
    if ts is None:
        return False
    return (time.time() - ts) < float(window_seconds)


def cleanup_older(threshold: float = _WINDOW_SECONDS) -> None:
    """Optional: remove entries older than threshold seconds."""
    now = time.time()
    to_remove = [aid for aid, ts in _recent_glimmers.items() if (now - ts) >= threshold]
    for aid in to_remove:
        del _recent_glimmers[aid]
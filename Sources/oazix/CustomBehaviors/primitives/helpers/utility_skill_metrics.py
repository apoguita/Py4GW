import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class UtilitySkillMetricsSample:
    """Metrics for one action."""
    skill_id: int = 0
    action_type: str = ""  # "skipped" or "performed"
    timestamp: float = 0.0

class UtilitySkillMetrics:
    """Singleton metrics tracker for utility skill execution.

    Tracks only:
    - ACTION_SKIPPED (execution returned ACTION_SKIPPED)
    - ACTION_PERFORMED (execution returned ACTION_PERFORMED)
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.enabled: bool = True
        self._history: deque[UtilitySkillMetricsSample] = deque(maxlen=5000)
        self.should_reset_when_entering_combat: bool = True
        self._initialized = True

    def record_action_skipped(self, skill_id: int):
        """Record that a skill execution returned ACTION_SKIPPED."""
        if not self.enabled or skill_id == 0:
            return
        sample = UtilitySkillMetricsSample(
            skill_id=skill_id,
            action_type="skipped",
            timestamp=time.perf_counter()
        )
        self._history.append(sample)

    def record_action_performed(self, skill_id: int):
        """Record that a skill execution returned ACTION_PERFORMED."""
        if not self.enabled or skill_id == 0:
            return
        sample = UtilitySkillMetricsSample(
            skill_id=skill_id,
            action_type="performed",
            timestamp=time.perf_counter()
        )
        self._history.append(sample)

    def clear(self):
        """Clear all collected history."""
        self._history.clear()

    @property
    def history(self) -> deque[UtilitySkillMetricsSample]:
        return self._history

class _NullContext:
    """No-op context manager when metrics are disabled."""
    __slots__ = ()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

_NULL_CONTEXT = _NullContext()
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class EvalCycleSample:
    """Timing measurements for one eval cycle."""
    timestamp: float = 0.0
    enemy_targeting_ms: float = 0.0
    enemy_targeting_calls: int = 0
    ally_targeting_ms: float = 0.0
    ally_targeting_calls: int = 0
    enemy_neighbor_counting_ms: float = 0.0
    enemy_neighbor_counting_calls: int = 0
    ally_neighbor_counting_ms: float = 0.0
    ally_neighbor_counting_calls: int = 0
    gravity_center_ms: float = 0.0
    gravity_center_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    skill_timings: dict[str, float] = field(default_factory=dict)
    skill_infra: dict[str, dict[str, float]] = field(default_factory=dict)


class EvalProfiler:
    """Singleton profiler for skill eval cycle operations.

    Usage:
        with EvalProfiler().measure("enemy_targeting"):
            ...  # timed block

        EvalProfiler().record_cache(hit=True)
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
        self.enabled: bool = False
        self.window_seconds: int = 60
        self._current: EvalCycleSample = EvalCycleSample()
        self._history: deque[EvalCycleSample] = deque(maxlen=2000)
        self._initialized = True

    def begin_cycle(self):
        """Call at the start of each eval cycle. Flushes previous sample."""
        if not self.enabled:
            return
        if self._current.enemy_targeting_calls > 0 or self._current.ally_targeting_calls > 0 or self._current.skill_timings:
            self._current.timestamp = time.perf_counter()
            self._history.append(self._current)
        self._current = EvalCycleSample()
        # Trim samples outside the time window
        cutoff = time.perf_counter() - self.window_seconds
        while self._history and self._history[0].timestamp < cutoff:
            self._history.popleft()

    def measure(self, section: str):
        """Context manager for timing a named section."""
        if self.enabled:
            return _TimingContext(self, section)
        return _NULL_CONTEXT

    def record_cache(self, hit: bool):
        """Record a cache hit or miss."""
        if not self.enabled:
            return
        if hit:
            self._current.cache_hits += 1
        else:
            self._current.cache_misses += 1

    def measure_skill(self, skill_name: str):
        """Context manager for timing a specific skill's evaluate() call."""
        if self.enabled:
            return _SkillTimingContext(self, skill_name)
        return _NULL_CONTEXT

    def clear(self):
        """Clear all collected history."""
        self._history.clear()
        self._current = EvalCycleSample()

    @property
    def history(self) -> deque[EvalCycleSample]:
        return self._history


class _TimingContext:
    __slots__ = ('_profiler', '_section', '_start')

    def __init__(self, profiler: EvalProfiler, section: str):
        self._profiler = profiler
        self._section = section

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        elapsed = (time.perf_counter() - self._start) * 1000.0
        s = self._profiler._current
        if self._section == "enemy_targeting":
            s.enemy_targeting_ms += elapsed
            s.enemy_targeting_calls += 1
        elif self._section == "ally_targeting":
            s.ally_targeting_ms += elapsed
            s.ally_targeting_calls += 1
        elif self._section == "enemy_neighbor_counting":
            s.enemy_neighbor_counting_ms += elapsed
            s.enemy_neighbor_counting_calls += 1
        elif self._section == "ally_neighbor_counting":
            s.ally_neighbor_counting_ms += elapsed
            s.ally_neighbor_counting_calls += 1
        elif self._section == "gravity_center":
            s.gravity_center_ms += elapsed
            s.gravity_center_calls += 1


class _SkillTimingContext:
    """Times a single skill's evaluate() call, accumulates into skill_timings dict."""
    __slots__ = ('_profiler', '_name', '_start', '_snap_enemy', '_snap_ally', '_snap_gravity')

    def __init__(self, profiler: EvalProfiler, name: str):
        self._profiler = profiler
        self._name = name

    def __enter__(self):
        self._start = time.perf_counter()
        s = self._profiler._current
        self._snap_enemy = s.enemy_targeting_ms
        self._snap_ally = s.ally_targeting_ms
        self._snap_gravity = s.gravity_center_ms
        return self

    def __exit__(self, *_):
        elapsed = (time.perf_counter() - self._start) * 1000.0
        s = self._profiler._current
        s.skill_timings[self._name] = s.skill_timings.get(self._name, 0.0) + elapsed
        d_enemy = s.enemy_targeting_ms - self._snap_enemy
        d_ally = s.ally_targeting_ms - self._snap_ally
        d_gravity = s.gravity_center_ms - self._snap_gravity
        if d_enemy > 0 or d_ally > 0 or d_gravity > 0:
            infra = s.skill_infra.setdefault(self._name, {})
            if d_enemy > 0:
                infra["enemy_targeting"] = infra.get("enemy_targeting", 0.0) + d_enemy
            if d_ally > 0:
                infra["ally_targeting"] = infra.get("ally_targeting", 0.0) + d_ally
            if d_gravity > 0:
                infra["gravity_center"] = infra.get("gravity_center", 0.0) + d_gravity


class _NullContext:
    """Zero-cost no-op context manager when profiling is disabled."""
    __slots__ = ()
    def __enter__(self): return self
    def __exit__(self, *_): pass

_NULL_CONTEXT = _NullContext()

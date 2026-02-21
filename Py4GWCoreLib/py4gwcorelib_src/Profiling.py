import sys
import time
import cProfile
from typing import Optional


class SimpleProfiler:
    """Minimal sys.setprofile profiler that works with pybind11 and multiple runcall() calls."""

    def __init__(self):
        self.stats: dict[tuple, list] = {}      # {func_key: [call_count, self_ns, cum_ns]}
        self.callers: dict[tuple, dict] = {}    # {func_key: {caller_key: [count, cum_ns]}}
        self._stack: list[list] = []            # [[func_key, enter_ns, children_ns]]
        self.edge_order: dict[tuple, int] = {}  # (caller, callee) -> first-seen sequence
        self._seq: int = 0
        self._trace = self._make_trace()

    def _make_trace(self):
        _clock = time.perf_counter_ns
        _stats = self.stats
        _callers = self.callers
        _stack = self._stack
        _edge_order = self.edge_order
        _seq = [self._seq]

        def trace(frame, event, arg):
            if event == 'call':
                co = frame.f_code
                _stack.append([(co.co_filename, co.co_firstlineno, co.co_name), _clock(), 0])
            elif event == 'return':
                if not _stack:
                    return
                now = _clock()
                key, t0, children = _stack.pop()
                elapsed = now - t0
                s = _stats.get(key)
                if s:
                    s[0] += 1; s[1] += elapsed - children; s[2] += elapsed
                else:
                    _stats[key] = [1, elapsed - children, elapsed]
                if _stack:
                    parent = _stack[-1]
                    caller_key = parent[0]
                    cd = _callers.get(key)
                    if cd is not None:
                        edge = cd.get(caller_key)
                        if edge:
                            edge[0] += 1; edge[1] += elapsed
                        else:
                            cd[caller_key] = [1, elapsed]
                            _edge_order[(caller_key, key)] = _seq[0]
                            _seq[0] += 1
                    else:
                        _callers[key] = {caller_key: [1, elapsed]}
                        _edge_order[(caller_key, key)] = _seq[0]
                        _seq[0] += 1
                    parent[2] += elapsed
            elif event == 'c_call':
                try:
                    name = arg.__qualname__
                except AttributeError:
                    name = str(arg)
                _stack.append([('~', 0, name), _clock(), 0])
            elif event == 'c_return' or event == 'c_exception':
                if not _stack:
                    return
                now = _clock()
                key, t0, children = _stack.pop()
                elapsed = now - t0
                s = _stats.get(key)
                if s:
                    s[0] += 1; s[1] += elapsed - children; s[2] += elapsed
                else:
                    _stats[key] = [1, elapsed - children, elapsed]
                if _stack:
                    parent = _stack[-1]
                    caller_key = parent[0]
                    cd = _callers.get(key)
                    if cd is not None:
                        edge = cd.get(caller_key)
                        if edge:
                            edge[0] += 1; edge[1] += elapsed
                        else:
                            cd[caller_key] = [1, elapsed]
                            _edge_order[(caller_key, key)] = _seq[0]
                            _seq[0] += 1
                    else:
                        _callers[key] = {caller_key: [1, elapsed]}
                        _edge_order[(caller_key, key)] = _seq[0]
                        _seq[0] += 1
                    parent[2] += elapsed

        return trace

    def enable(self):
        self._stack.clear()
        sys.setprofile(self._trace)

    def disable(self):
        sys.setprofile(None)

    def runcall(self, func, *args, **kwargs):
        self.enable()
        try:
            return func(*args, **kwargs)
        finally:
            self.disable()


class ProfileScope:
    __slots__ = ('timings', 'category', 'name', 'cprofiler', 't0')

    def __init__(self, timings: dict, category: str, name: str,
                 cprofiler: Optional[cProfile.Profile] = None):
        self.timings = timings
        self.category = category
        self.name = name
        self.cprofiler = cprofiler

    def __enter__(self):
        self.t0 = time.perf_counter_ns()
        if self.cprofiler:
            try:
                self.cprofiler.enable()
            except ValueError:
                self.cprofiler = None
        return self

    def __exit__(self, *exc):
        if self.cprofiler:
            self.cprofiler.disable()
        cat = self.timings.setdefault(self.category, {})
        cat[self.name] = time.perf_counter_ns() - self.t0
        return False


class ProfilingRegistry:
    _instance: Optional['ProfilingRegistry'] = None

    enabled: bool
    timings: dict[str, dict[str, int]]
    cprofile_targets: dict[str, cProfile.Profile]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.enabled = False
            cls._instance.timings = {}
            cls._instance.cprofile_targets = {}
        return cls._instance

    def scope(self, category: str, name: str) -> ProfileScope:
        return ProfileScope(
            self.timings, category, name,
            self.cprofile_targets.get(name)
        )

    def runcall_scope(self, category: str, name: str, func, *args, **kwargs):
        """Time func and, if a cProfile target is registered, profile it via runcall
        so the function itself appears as the root entry in the stats."""
        t0 = time.perf_counter_ns()
        cprofiler = self.cprofile_targets.get(name)
        if cprofiler:
            try:
                result = cprofiler.runcall(func, *args, **kwargs)
            except ValueError:
                import sys
                sys.setprofile(None)
                result = func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        self.timings.setdefault(category, {})[name] = time.perf_counter_ns() - t0
        return result

    def clear_frame(self):
        for cat in self.timings.values():
            cat.clear()

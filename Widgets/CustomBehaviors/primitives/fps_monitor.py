import time
from collections import deque

class FPSMonitor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FPSMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self, history=100, smoothing=0.9):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.last_time = time.perf_counter()
        self.frame_times = deque(maxlen=history)

        self.smoothing = smoothing
        self.smoothed_fps = None
        self.last_dt = 0.0
        self._initialized = True

    def tick(self):
        """Call once per frame/cycle to record timing."""
        now = time.perf_counter()
        self.last_dt = now - self.last_time
        self.last_time = now

        self.frame_times.append(self.last_dt)

        inst_fps = 1.0 / self.last_dt if self.last_dt > 0 else float("inf")

        if self.smoothed_fps is None:
            self.smoothed_fps = inst_fps
        else:
            self.smoothed_fps = (
                self.smoothed_fps * self.smoothing + inst_fps * (1 - self.smoothing)
            )

        return self.last_dt

    @property
    def dt(self):
        """Duration of the last frame (seconds)."""
        return self.last_dt

    @property
    def raw_fps(self):
        """Average FPS over the history window (no smoothing)."""
        if not self.frame_times:
            return 0.0
        avg_dt = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_dt if avg_dt > 0 else float("inf")

    @property
    def fps(self):
        """Smoothed FPS (EMA)."""
        return self.smoothed_fps if self.smoothed_fps else 0.0

    def frame_stats(self):
        """Return frame timing statistics (ms)."""
        if not self.frame_times:
            return {}, "No data yet"

        stats_dict = {
            "last_dt_ms": self.dt * 1000,
            "avg_dt_ms": (sum(self.frame_times) / len(self.frame_times)) * 1000,
            "min_dt_ms": min(self.frame_times) * 1000,
            "max_dt_ms": max(self.frame_times) * 1000,
        }

        stats_str = (
            f"Frame: {stats_dict['last_dt_ms']:.2f} ms | "
            f"Avg: {stats_dict['avg_dt_ms']:.2f} ms | "
            f"Min: {stats_dict['min_dt_ms']:.2f} ms | "
            f"Max: {stats_dict['max_dt_ms']:.2f} ms"
        )
        return stats_dict, stats_str

    def fps_stats(self):
        """Return FPS statistics (smoothed and raw)."""
        stats_dict = {
            "smoothed_fps": self.fps,
            "raw_fps": self.raw_fps,
        }

        stats_str = (
            f"Smoothed FPS: {stats_dict['smoothed_fps']:.2f} | "
            f"Raw FPS: {stats_dict['raw_fps']:.2f}"
        )
        return stats_dict, stats_str

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Hashable, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


@dataclass(frozen=True)
class FrameCacheKey:
    category: str
    source_lib: str
    function_name: str
    key: Hashable = ""


class FrameCache:
    _instance: "FrameCache | None" = None
    _values: dict[FrameCacheKey, Any]
    _callback_name: str
    _callback_registered: bool

    def __new__(cls) -> "FrameCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_values"):
            self._values = {}
        if not hasattr(self, "_callback_name"):
            self._callback_name = "FrameCache.ResetCache"
        if not hasattr(self, "_callback_registered"):
            self._callback_registered = False

    def get_or_create(
        self,
        category: str,
        function_name: str,
        factory: Callable[[], T],
        source_lib: str = "",
        key: Any = "",
    ) -> T:
        cache_key = FrameCacheKey(
            category=str(category),
            source_lib=str(source_lib),
            function_name=str(function_name),
            key=self._normalize_key(key),
        )
        if cache_key not in self._values:
            self._values[cache_key] = factory()
        return self._values[cache_key]

    def reset_cache(self) -> None:
        self._values.clear()

    def clear(self) -> None:
        self.reset_cache()

    def items(self) -> list[tuple[FrameCacheKey, Any]]:
        return list(self._values.items())

    @staticmethod
    def _normalize_key(key: Any) -> Hashable:
        if key is None:
            return None

        # Fast path: most cache keys are already hashable (int, str, tuple, etc.)
        try:
            hash(key)
            return key
        except TypeError:
            pass

        if isinstance(key, list):
            return tuple(
                part if _is_hashable(part) else FrameCache._normalize_key(part)
                for part in key
            )
        if isinstance(key, set):
            return frozenset(
                part if _is_hashable(part) else FrameCache._normalize_key(part)
                for part in key
            )
        if isinstance(key, dict):
            return tuple(
                (
                    name if _is_hashable(name) else FrameCache._normalize_key(name),
                    value if _is_hashable(value) else FrameCache._normalize_key(value),
                )
                for name, value in key.items()
            )
        return id(key)

    def enable(self) -> None:
        if self._callback_registered:
            return
        import PyCallback

        PyCallback.PyCallback.Register(
            self._callback_name,
            PyCallback.Phase.PreUpdate,
            self.reset_cache,
            priority=7,
        )
        self._callback_registered = True

    def disable(self) -> None:
        if not self._callback_registered:
            return
        import PyCallback

        PyCallback.PyCallback.RemoveByName(self._callback_name)
        self._callback_registered = False


def _is_hashable(value: Any) -> bool:
    try:
        hash(value)
        return True
    except TypeError:
        return False


FRAME_CACHE = FrameCache()
FRAME_CACHE.enable()


def frame_cache(
    category: str,
    source_lib: str = "",
    key: Any = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if callable(key):
                resolved_key = key(*args, **kwargs)
            elif key is not None:
                resolved_key = key
            elif not args and not kwargs:
                resolved_key = "global"
            elif kwargs:
                resolved_key = {"args": args, "kwargs": kwargs}
            else:
                resolved_key = args

            return FRAME_CACHE.get_or_create(
                category=category,
                function_name=func.__name__,
                factory=lambda: func(*args, **kwargs),
                source_lib=source_lib,
                key=resolved_key,
            )

        return wrapper

    return decorator

from typing import TypeVar, Callable

T = TypeVar('T')


class MemoryCacheManager:

    PARTY_LEADER_ID = "party_leader_id"
    
    """
    A singleton per-frame cache that stores values by string keys.
    Call refresh() at the start of each frame/tick to clear all cached data.

    Usage:
        # Get or compute a value (preferred pattern)
        value = MemoryCacheManager.get_or_set("my_key", lambda: expensive_computation())

        # Manual get/set
        cache = MemoryCacheManager()
        cache.set("key", value)
        cached = cache.get("key")
    """
    _instance: "MemoryCacheManager | None" = None
    _cache: dict[str, object]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryCacheManager, cls).__new__(cls)
            cls._instance._cache = {}
        return cls._instance

    @classmethod
    def get_or_set(cls, key: str, factory: Callable[[], T]) -> T:
        """
        Get a cached value by key, or compute and cache it if not found.

        :param key: The cache key
        :param factory: A callable that returns the value to cache if not found
        :return: The cached or newly computed value
        """
        instance = cls()
        if key in instance._cache:
            return instance._cache[key]  # type: ignore
        value = factory()
        instance._cache[key] = value
        return value

    def get(self, key: str) -> object | None:
        """
        Get a cached value by key.

        :param key: The cache key
        :return: The cached value, or None if not found
        """
        return self._cache.get(key)

    def set(self, key: str, value: object) -> None:
        """
        Store a value in the cache.

        :param key: The cache key
        :param value: The value to cache
        """
        self._cache[key] = value

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        :param key: The cache key
        :return: True if the key exists, False otherwise
        """
        return key in self._cache

    def refresh(self) -> None:
        """Clear all cached data. Call this at the start of each frame/tick."""
        self._cache.clear()
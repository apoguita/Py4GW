# YourMainPackage/GlobalCache/__init__.py

from .GlobalCache import GlobalCache

# Optional: ready-to-use singleton
GLOBAL_CACHE = GlobalCache()

__all__ = ["GLOBAL_CACHE"]
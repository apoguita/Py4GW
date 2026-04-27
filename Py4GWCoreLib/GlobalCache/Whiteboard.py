"""General opt-in registry for the cross-hero whiteboard.

The shared-memory plumbing (``IntentStruct`` slot array, slot allocator,
expiry paths) lives in ``GlobalCache/shared_memory_src/``. This module is
the **opt-in registry** that decides which keys participate.

The primitive is intentionally generic. Skills are one consumer; other
plausible consumers include loot pickup ownership, resurrection ownership,
dialog interactions, consumable usage, and any other "one hero in the team
should claim, the others should skip" pattern.

Keys are namespaced by ``kind`` so different consumers cannot collide:

- ``("skill", skill_id)`` — managed via :mod:`Py4GWCoreLib.Builds.Skills._whiteboard`
- ``("loot", item_id)`` — future
- ``("resurrect", agent_id)`` — future
- etc.

Skill-system callers should keep using the thin wrapper at
``Py4GWCoreLib.Builds.Skills._whiteboard`` (which pre-fills ``kind="skill"``)
rather than reaching into this module directly. New consumer kinds should
add their own thin wrapper modeled on the skill one.
"""

from typing import Callable, TypeVar

# kind -> set of registered keys
_registry: dict[str, set[int]] = {}

F = TypeVar("F", bound=Callable[..., object])


def register(kind: str, key: int) -> None:
    """Mark ``(kind, key)`` as participating in cross-hero whiteboard coordination."""
    if not kind or not key or key <= 0:
        return
    _registry.setdefault(str(kind), set()).add(int(key))


def unregister(kind: str, key: int) -> None:
    """Remove ``(kind, key)`` from the registry."""
    if not kind:
        return
    bucket = _registry.get(str(kind))
    if bucket is not None:
        bucket.discard(int(key))


def is_registered(kind: str, key: int) -> bool:
    """True iff ``(kind, key)`` has been opted into whiteboard coordination."""
    if not kind:
        return False
    bucket = _registry.get(str(kind))
    if bucket is None:
        return False
    return int(key) in bucket


def registered_keys(kind: str) -> frozenset[int]:
    """Snapshot of currently registered keys for ``kind`` (read-only)."""
    if not kind:
        return frozenset()
    bucket = _registry.get(str(kind))
    if bucket is None:
        return frozenset()
    return frozenset(bucket)


def all_kinds() -> frozenset[str]:
    """Snapshot of every ``kind`` that currently has at least one registered key."""
    return frozenset(k for k, v in _registry.items() if v)


def coordinates_via_whiteboard(kind: str, key: int) -> Callable[[F], F]:
    """Decorator form that registers ``(kind, key)`` at import time.

    Most callers should use the thin per-kind wrapper (e.g.
    :func:`Py4GWCoreLib.Builds.Skills._whiteboard.coordinates_via_whiteboard`)
    rather than calling this directly.
    """

    def _decorator(fn: F) -> F:
        register(kind, key)
        return fn

    return _decorator

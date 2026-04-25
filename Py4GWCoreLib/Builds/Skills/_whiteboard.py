"""Cross-hero cast-intent whiteboard opt-in registry.

A skill participates in whiteboard coordination when any of:

- its CustomSkill metadata has ``CoordinatesViaWhiteboard = True``, OR
- it is registered here via :func:`register` or ``@coordinates_via_whiteboard``.

The combat loop (BuildMgr._is_whiteboard_skill) unions the two surfaces, so a
skill module under ``Py4GWCoreLib/Builds/Skills/**`` can opt in without
touching HeroAI's custom-skill table.
"""

from typing import Callable, TypeVar

_whiteboard_skill_ids: set[int] = set()

F = TypeVar("F", bound=Callable[..., object])


def register(skill_id: int) -> None:
    """Mark ``skill_id`` as participating in the cross-hero whiteboard."""
    if skill_id and skill_id > 0:
        _whiteboard_skill_ids.add(int(skill_id))


def unregister(skill_id: int) -> None:
    """Remove ``skill_id`` from the whiteboard registry."""
    _whiteboard_skill_ids.discard(int(skill_id))


def is_registered(skill_id: int) -> bool:
    """True if this skill has been opted into whiteboard coordination."""
    return int(skill_id) in _whiteboard_skill_ids


def registered_skill_ids() -> frozenset[int]:
    """Snapshot of currently registered skill IDs (read-only)."""
    return frozenset(_whiteboard_skill_ids)


def coordinates_via_whiteboard(skill_id: int) -> Callable[[F], F]:
    """Decorator form that registers ``skill_id`` at import time.

    Usage on a skill method::

        @coordinates_via_whiteboard(Skill.GetID("Power_Drain"))
        def Power_Drain(self) -> BuildCoroutine:
            ...
    """

    def _decorator(fn: F) -> F:
        register(skill_id)
        return fn

    return _decorator

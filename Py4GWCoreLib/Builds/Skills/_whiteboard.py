"""Skill-scoped wrapper around the general whiteboard registry.

The underlying ``(kind, key)`` registry lives at
:mod:`Py4GWCoreLib.GlobalCache.Whiteboard`. This module pre-fills
``kind="skill"`` so skill-system callers keep their existing API.

A skill participates in whiteboard coordination when any of:

- its CustomSkill metadata has ``CoordinatesViaWhiteboard = True``, OR
- it is registered here via :func:`register` or ``@coordinates_via_whiteboard``.

The combat loop (``BuildMgr._is_whiteboard_skill``) unions the two surfaces,
so a skill module under ``Py4GWCoreLib/Builds/Skills/**`` can opt in
without touching HeroAI's custom-skill table.
"""

from typing import Callable, TypeVar

from Py4GWCoreLib.GlobalCache.Whiteboard import (
    is_registered as _wb_is_registered,
    register as _wb_register,
    registered_keys as _wb_registered_keys,
    unregister as _wb_unregister,
)

KIND = "skill"

F = TypeVar("F", bound=Callable[..., object])


def register(skill_id: int) -> None:
    """Mark ``skill_id`` as participating in the cross-hero whiteboard."""
    _wb_register(KIND, skill_id)


def unregister(skill_id: int) -> None:
    """Remove ``skill_id`` from the whiteboard registry."""
    _wb_unregister(KIND, skill_id)


def is_registered(skill_id: int) -> bool:
    """True if this skill has been opted into whiteboard coordination."""
    return _wb_is_registered(KIND, skill_id)


def registered_skill_ids() -> frozenset[int]:
    """Snapshot of currently registered skill IDs (read-only)."""
    return _wb_registered_keys(KIND)


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

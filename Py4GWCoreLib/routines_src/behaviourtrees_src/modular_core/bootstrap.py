"""
bootstrap module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from .step_registration import register_decorated_step_types

_BOOTSTRAPPED = False


def register_default_action_nodes(*, force: bool = False) -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED and not force:
        return
    register_decorated_step_types(overwrite=force)
    _BOOTSTRAPPED = True


def ensure_action_nodes_bootstrapped() -> None:
    register_default_action_nodes(force=False)

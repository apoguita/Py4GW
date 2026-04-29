"""
step_actions module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from collections.abc import Callable

from .step_context import StepContext

StepActionHandler = Callable[[StepContext], None]

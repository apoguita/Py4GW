from __future__ import annotations

from collections.abc import Callable

from .actions_interaction import HANDLERS as INTERACTION_HANDLERS
from .actions_inventory import HANDLERS as INVENTORY_HANDLERS
from .actions_movement import HANDLERS as MOVEMENT_HANDLERS
from .actions_party import HANDLERS as PARTY_HANDLERS
from .actions_targeting import HANDLERS as TARGETING_HANDLERS
from .step_context import StepContext

StepHandler = Callable[[StepContext], None]

STEP_HANDLERS: dict[str, StepHandler] = {}

for handler_group in (
    MOVEMENT_HANDLERS,
    TARGETING_HANDLERS,
    INTERACTION_HANDLERS,
    PARTY_HANDLERS,
    INVENTORY_HANDLERS,
):
    STEP_HANDLERS.update(handler_group)

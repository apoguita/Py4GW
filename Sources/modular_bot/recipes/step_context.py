from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting


@dataclass(frozen=True)
class StepContext:
    bot: "Botting"
    step: Dict[str, Any]
    step_idx: int
    recipe_name: str
    step_type: str
    step_display: str

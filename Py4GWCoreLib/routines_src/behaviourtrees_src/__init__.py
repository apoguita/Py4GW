"""
Internal package for the BehaviourTrees routine subsystem.

This package is the staging area for code extracted from
`routines_src/BehaviourTrees.py` as the BT routines surface is split into
smaller, easier-to-maintain modules.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .agents import BTAgents
    from .composite import BTComposite, BTCompositeHelpers
    from .items import BTItems
    from .keybinds import BTKeybinds
    from .map import BTMap
    from .movement import BTMovement
    from .party import BTParty
    from .player import BTPlayer
    from .shared import BTShared
    from .skills import BTSkills
    from .upkeepers import BTUpkeepers

__all__ = [
    "BTAgents",
    "BTComposite",
    "BTCompositeHelpers",
    "BTItems",
    "BTKeybinds",
    "BTMap",
    "BTMovement",
    "BTParty",
    "BTPlayer",
    "BTShared",
    "BTSkills",
    "BTUpkeepers",
]


def __getattr__(name: str) -> Any:
    if name == "BTAgents":
        from .agents import BTAgents
        return BTAgents
    if name == "BTComposite":
        from .composite import BTComposite
        return BTComposite
    if name == "BTCompositeHelpers":
        from .composite import BTCompositeHelpers
        return BTCompositeHelpers
    if name == "BTItems":
        from .items import BTItems
        return BTItems
    if name == "BTKeybinds":
        from .keybinds import BTKeybinds
        return BTKeybinds
    if name == "BTMap":
        from .map import BTMap
        return BTMap
    if name == "BTMovement":
        from .movement import BTMovement
        return BTMovement
    if name == "BTParty":
        from .party import BTParty
        return BTParty
    if name == "BTPlayer":
        from .player import BTPlayer
        return BTPlayer
    if name == "BTShared":
        from .shared import BTShared
        return BTShared
    if name == "BTSkills":
        from .skills import BTSkills
        return BTSkills
    if name == "BTUpkeepers":
        from .upkeepers import BTUpkeepers
        return BTUpkeepers
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

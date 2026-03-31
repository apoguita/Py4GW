"""
Internal package for the BehaviourTrees routine subsystem.

This package is the staging area for code extracted from
`routines_src/BehaviourTrees.py` as the BT routines surface is split into
smaller, easier-to-maintain modules.
"""

from .agents import BTAgents
from .composite import BTComposite, BTCompositeHelpers
from .items import BTItems
from .keybinds import BTKeybinds
from .map import BTMap
from .movement import BTMovement
from .player import BTPlayer
from .skills import BTSkills
from .upkeepers import BTUpkeepers

__all__ = ["BTAgents", "BTComposite", "BTCompositeHelpers", "BTItems", "BTKeybinds", "BTMap", "BTMovement", "BTPlayer", "BTSkills", "BTUpkeepers"]

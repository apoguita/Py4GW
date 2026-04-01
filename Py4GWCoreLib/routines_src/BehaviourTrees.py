"""
BehaviourTrees module notes
===========================

This file is both:
- the public BT catalog entry point
- a discovery source for higher-level tooling

Authoring and discovery conventions
-----------------------------------
- Keep existing class names as the system-level grouping surface.
- Treat `BT` as the root public catalog.
- Treat public grouped classes bound on `BT` as the front-facing routine surface.
- Use `PascalCase` for public/front-facing routine methods.
- Use `snake_case` for helper/internal methods.
- Use `_snake_case` for explicitly private helpers.
- Keep helper/internal methods out of the public discovery surface.

Routine docstring template
--------------------------
Each user-facing routine method should use:
- a free human-readable description first
- a structured `Meta:` block after it

Template:

    \"\"\"
    One or more human-readable paragraphs explaining what the routine builds.

    Meta:
      Expose: true
      Audience: beginner
      Display: Target Nearest NPC
      Purpose: Build a tree that targets the nearest NPC within range.
      UserDescription: Use this when you want to find and target a nearby NPC.
      Notes: Keep metadata single-line. Structural truth should stay in code.
    \"\"\"

Docstring parsing rules
-----------------------
- Only the `Meta:` section is intended for machine parsing.
- Keep metadata lines single-line and in `Key: Value` form.
- Unknown keys should be safe for tooling to ignore.
- Prefer adding presentation/help metadata in docstrings instead of duplicating
  structural metadata that already exists in code.
"""

from Py4GWCoreLib.routines_src.Agents import Agents
from ..GlobalCache import GLOBAL_CACHE
from ..Py4GWcorelib import ConsoleLog, Console
from ..Map import Map
from ..Agent import Agent
from ..Player import Player
from ..enums_src.Title_enums import TITLE_NAME
from ..enums_src.Model_enums import ModelID
from ..UIManager import UIManager
from ..enums_src.GameData_enums import Range
from ..enums import SharedCommandType

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from enum import Enum, auto
from typing import Callable

from .behaviourtrees_src import BTAgents, BTComposite, BTCompositeHelpers, BTItems, BTKeybinds, BTMap, BTMovement, BTPlayer, BTSkills, BTUpkeepers
from .Checks import Checks

import importlib
import random

class _RProxy:
    """
    Internal proxy that resolves the `Routines` root package lazily.

    Meta:
      Expose: false
      Audience: advanced
      Display: Internal Routines Proxy
      Purpose: Provide lazy access to the root routines package from the BT helper catalog module.
      UserDescription: Internal support helper class.
      Notes: This proxy exists to avoid eager import wiring and is not part of the BT configurator surface.
    """
    def __getattr__(self, name: str):
        """
        Resolve a routine attribute from the root package on demand.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Routines Proxy Get Attribute
          Purpose: Lazily fetch a named routine attribute from the root package.
          UserDescription: Internal support routine.
          Notes: This keeps BT helper imports lightweight and should never be shown as a front-facing BT routine.
        """
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()


class BT:
    """
    Root BT helper catalog exposed to discovery tooling.

    Meta:
      Expose: true
      Audience: advanced
      Display: BT
      Purpose: Provide the grouped public BT helper surface for discovery and authoring.
      UserDescription: Root catalog for built-in BT helper groups.
      Notes: Discovery should start from this class and then inspect approved grouped surfaces.
    """
    NodeState = BehaviorTree.NodeState

    Composite = BTComposite
    Player = BTPlayer
    Movement = BTMovement
    Skills = BTSkills   
    Map = BTMap
    Upkeepers = BTUpkeepers
    Items = BTItems
    Agents = BTAgents
    Keybinds = BTKeybinds

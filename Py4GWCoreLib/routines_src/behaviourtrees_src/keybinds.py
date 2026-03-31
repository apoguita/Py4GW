"""
BT routines file notes
======================

This file is both:
- part of the public BT grouped routine surface
- a discovery source for higher-level tooling

Authoring and discovery conventions
-----------------------------------
- Keep existing class names as the system-level grouping surface.
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
      Display: Press Keybind
      Purpose: Build a tree that presses a configured keybind for a duration.
      UserDescription: Use this when you want to trigger a keybind from a tree.
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

from __future__ import annotations

from ...Py4GWcorelib import ConsoleLog
from ...UIManager import UIManager
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree


class BTKeybinds:
    """
    Public BT helper group for keybind-trigger routines.

    Meta:
      Expose: true
      Audience: advanced
      Display: Keybinds
      Purpose: Group public BT routines related to pressing configured keybinds.
      UserDescription: Built-in BT helper group for keybind-trigger routines.
      Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
    """
    @staticmethod
    def PressKeybind(keybind_index:int, duration_ms:int=125, log:bool=False):
        """
        Build a tree that presses a configured keybind for a short duration.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Press Keybind
          Purpose: Press and release a UI keybind by index.
          UserDescription: Use this when you want a behavior tree to trigger a configured keybind.
          Notes: Holds the key down for `duration_ms`, then releases it and logs the action when enabled.
        """
        def _keydown():
            """
            Press the configured keybind down.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Key Down Helper
              Purpose: Issue the low-level key-down event for the configured keybind.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after the key-down request.
            """
            UIManager.Keydown(keybind_index,0)
            return BehaviorTree.NodeState.SUCCESS
        
        def _keyup():
            """
            Release the configured keybind.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Key Up Helper
              Purpose: Issue the low-level key-up event for the configured keybind.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after the key-up request.
            """
            UIManager.Keyup(keybind_index,0)
            return BehaviorTree.NodeState.SUCCESS
        
        def _log_action():
            """
            Log the completed keybind press action.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Keybind Log Helper
              Purpose: Emit the optional log message for the enclosing keybind routine.
              UserDescription: Internal support routine.
              Notes: Returns success whether logging is enabled or not.
            """
            ConsoleLog("PressKeybind", f"Pressed keybind index {keybind_index} for {duration_ms}ms.", log=log)
            return BehaviorTree.NodeState.SUCCESS
        
        tree = BehaviorTree.SequenceNode(
                children=[
                    BehaviorTree.ActionNode(name="KeyDown", action_fn=_keydown, aftercast_ms=duration_ms),
                    BehaviorTree.ActionNode(name="KeyUp", action_fn=_keyup, aftercast_ms=50 ),
                    BehaviorTree.ActionNode(name="LogAction", action_fn=_log_action)
                ]
        )
        bt = BehaviorTree(root=tree)
        return bt

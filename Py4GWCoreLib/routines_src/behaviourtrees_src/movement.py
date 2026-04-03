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
      Display: Move And Target
      Purpose: Build a tree that combines movement and a targeting step.
      UserDescription: Use this when you want to move first and then target something.
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

from ...Agent import Agent
from ...enums_src.GameData_enums import Range
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from .composite import BTCompositeHelpers


class BTMovement:
    """
    Public BT helper group for movement-first composite routines.

    Meta:
      Expose: true
      Audience: advanced
      Display: Movement
      Purpose: Group public BT routines that combine movement with targeting, interaction, and dialog flows.
      UserDescription: Built-in BT helper group for movement-driven BT routines.
      Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
    """
    @staticmethod
    def _move_to_model_id(modelID_or_encStr: int | str, log: bool = False) -> BehaviorTree:
        """
        Build an internal support tree that resolves an agent by model id and moves to its coordinates.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Move To Model ID Helper
          Purpose: Resolve an agent by model id and compose the movement subtree used by public movement routines.
          UserDescription: Internal support routine.
          Notes: Stores the resolved agent id and coordinates on the blackboard before delegating to `BTPlayer.Move`.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        def _move_to_resolved_agent(node: BehaviorTree.Node):
            """
            Convert the resolved model-id lookup result into a concrete move subtree.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Move To Resolved Agent Helper
              Purpose: Read the resolved agent id from the blackboard, store coordinates, and build the move subtree.
              UserDescription: Internal support routine.
              Notes: Returns a failing tree when no agent id has been resolved yet.
            """
            agent_id = int(node.blackboard.get("result", 0) or 0)
            if agent_id == 0:
                return BehaviorTree(BehaviorTree.FailerNode(name="MoveToModelIDMissingAgent"))

            agent_x, agent_y = Agent.GetXY(agent_id)
            node.blackboard["resolved_agent_id"] = agent_id
            node.blackboard["resolved_agent_xy"] = (agent_x, agent_y)
            return BTPlayer.Move(x=agent_x, y=agent_y, tolerance=Range.Adjacent.value, log=log)

        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="MoveToModelID",
                children=[
                    BehaviorTree.SubtreeNode(
                        name="GetAgentIDByModelIDSubtree",
                        subtree_fn=lambda node: BTAgents.GetAgentIDByModelID(modelID_or_encStr, log=log),
                    ),
                    BehaviorTree.SubtreeNode(
                        name="MoveToResolvedAgentXYSubtree",
                        subtree_fn=_move_to_resolved_agent,
                    ),
                ],
            )
        )

    @staticmethod
    def MoveAndTarget(
        x: float,
        y: float,
        target_distance: float = Range.Adjacent.value,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that moves to coordinates and then targets the nearest NPC.

        Meta:
          Expose: true
          Audience: beginner
          Display: Move And Target
          Purpose: Move to a location and then target a nearby NPC.
          UserDescription: Use this when you want to walk somewhere first and then acquire a nearby NPC target.
          Notes: Combines the player move routine with the nearest-NPC targeting routine.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        return BTCompositeHelpers.move_and_target(
            move_tree=BTPlayer.Move(x=x, y=y, log=log),
            target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
        )

    @staticmethod
    def MoveTargetAndInteract(
        x: float,
        y: float,
        target_distance: float = Range.Nearby.value,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that moves to coordinates, targets a nearby NPC, and interacts.

        Meta:
          Expose: true
          Audience: beginner
          Display: Move Target And Interact
          Purpose: Move to a location, target a nearby NPC, and interact with it.
          UserDescription: Use this when you want to travel to an area and immediately interact with a nearby NPC.
          Notes: Uses the nearest-NPC target search after movement before calling player interaction.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        return BTCompositeHelpers.move_target_and_interact(
            move_tree=BTPlayer.Move(x=x, y=y, log=log),
            target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
            log=log,
        )

    @staticmethod
    def MoveTargetInteractAndDialog(
        x: float,
        y: float,
        target_distance: float = Range.Nearby.value,
        dialog_id: str | int = 0,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that moves, targets, interacts, and sends a dialog id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Dialog
          Purpose: Move to a location, interact with a nearby NPC, and send a dialog id.
          UserDescription: Use this when an interaction flow needs both travel and a follow-up dialog selection.
          Notes: Sends a manual dialog id after the interaction succeeds.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        return BTCompositeHelpers.move_target_interact_and_dialog(
            move_tree=BTPlayer.Move(x=x, y=y, log=log),
            target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
            dialog_id=dialog_id,
            log=log,
        )

    @staticmethod
    def MoveTargetInteractAndAutomaticDialog(
        x: float,
        y: float,
        target_distance: float = Range.Nearby.value,
        button_number: int = 0,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that moves, targets, interacts, and sends an automatic dialog button.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Automatic Dialog
          Purpose: Move to a location, interact with a nearby NPC, and press an automatic dialog button.
          UserDescription: Use this when an interaction flow requires choosing a visible dialog button after traveling.
          Notes: Waits for the dialog state and then sends the requested button index.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        return BTCompositeHelpers._interact_and_automatic_dialog(
            move_tree=BTPlayer.Move(x=x, y=y, log=log),
            target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
            button_number=button_number,
            log=log,
        )

    @staticmethod
    def MoveAndTargetByModelID(
        modelID_or_encStr: int | str,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, and targets it.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move And Target By Model ID
          Purpose: Resolve an agent by model id, move to its position, and target it.
          UserDescription: Use this when you know the model id of the agent you want to approach and target.
          Notes: Resolves the current agent id dynamically before movement and targeting.
        """
        from .agents import BTAgents

        return BTCompositeHelpers.move_and_target(
            move_tree=BTMovement._move_to_model_id(modelID_or_encStr=modelID_or_encStr, log=log),
            target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
        )

    @staticmethod
    def MoveTargetAndInteractByModelID(
        modelID_or_encStr: int | str,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, and interacts.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target And Interact By Model ID
          Purpose: Resolve an agent by model id, move to it, target it, and interact.
          UserDescription: Use this when you want a direct approach-and-interact flow for a known model id.
          Notes: Uses the shared model-id resolver before running the interaction sequence.
        """
        from .agents import BTAgents

        return BTCompositeHelpers.move_target_and_interact(
            move_tree=BTMovement._move_to_model_id(modelID_or_encStr=modelID_or_encStr, log=log),
            target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
            log=log,
        )

    @staticmethod
    def MoveTargetInteractAndDialogByModelID(
        modelID_or_encStr: int | str,
        dialog_id: str | int = 0,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, interacts, and sends a dialog id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Dialog By Model ID
          Purpose: Resolve an agent by model id, approach it, and send a dialog id after interaction.
          UserDescription: Use this when a known model id requires a move, interaction, and a dialog response.
          Notes: Sends the manual dialog id after the interaction succeeds.
        """
        from .agents import BTAgents

        return BTCompositeHelpers.move_target_interact_and_dialog(
            move_tree=BTMovement._move_to_model_id(modelID_or_encStr=modelID_or_encStr, log=log),
            target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
            dialog_id=dialog_id,
            log=log,
        )

    @staticmethod
    def MoveTargetInteractAndAutomaticDialogByModelID(
        modelID_or_encStr: int | str,
        button_number: int = 0,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, interacts, and presses an automatic dialog button.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Automatic Dialog By Model ID
          Purpose: Resolve an agent by model id, approach it, and send an automatic dialog choice.
          UserDescription: Use this when a known model id requires a move, interaction, and a visible dialog button selection.
          Notes: Uses the automatic dialog routine after the interaction succeeds.
        """
        from .agents import BTAgents

        return BTCompositeHelpers._interact_and_automatic_dialog(
            move_tree=BTMovement._move_to_model_id(modelID_or_encStr=modelID_or_encStr, log=log),
            target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
            button_number=button_number,
            log=log,
        )

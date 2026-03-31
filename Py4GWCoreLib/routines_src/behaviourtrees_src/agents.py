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

from __future__ import annotations

from ...Agent import Agent
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...enums_src.GameData_enums import Range
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..Agents import Agents as RoutinesAgents
from ..Checks import Checks
from .composite import BTCompositeHelpers
from .movement import BTMovement
from .player import BTPlayer


class BTAgents:
    """
    Public BT helper group for targeting, lookup, and agent-driven interaction flows.

    Meta:
      Expose: true
      Audience: advanced
      Display: Agents
      Purpose: Group public BT routines related to agent lookup, targeting, and agent interaction flows.
      UserDescription: Built-in BT helper group for targeting and agent interaction routines.
      Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
    """
    agent_ids = None

    @staticmethod
    def GetAgentIDByName(agent_name: str) -> BehaviorTree:
            """
            Build a tree that resolves an agent id by agent name.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Get Agent ID By Name
              Purpose: Resolve an agent id from an agent name and store it on the blackboard.
              UserDescription: Use this when a later step needs the current agent id for a named agent.
              Notes: Stores the resolved value in `blackboard['result']`.
            """
            def _search_name(node):
                """
                Resolve an agent id by name and store it on the blackboard.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Search Agent Name Helper
                  Purpose: Look up an agent id by name for the enclosing agent-resolution routine.
                  UserDescription: Internal support routine.
                  Notes: Stores the resolved value in `blackboard['result']` and returns failure when no match is found.
                """
                found = Agent.GetAgentIDByName(agent_name)
                node.blackboard["result"] = found
                return (BehaviorTree.NodeState.SUCCESS
                        if found != 0
                        else BehaviorTree.NodeState.FAILURE)

            tree = BehaviorTree.SequenceNode(name="GetAgentIDByNameRoot",
                children=[
                    BehaviorTree.ConditionNode(name="SearchName", condition_fn=_search_name)
                ]
            )
            return BehaviorTree(tree)
        
    @staticmethod
    def GetAgentIDByModelID(model_id:int, log:bool=False) -> BehaviorTree:
            """
            Build a tree that resolves an agent id by model id.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Get Agent ID By Model ID
              Purpose: Resolve an agent id from a model id and store it on the blackboard.
              UserDescription: Use this when a later step needs the current agent id for a known model id.
              Notes: Stores the resolved value in `blackboard['result']` and logs whether a matching agent was found.
            """
            def _search_model_id(node):
                """
                Resolve an agent id by model id and store it on the blackboard.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Search Agent Model ID Helper
                  Purpose: Scan the current agent array for the first agent whose model id matches the request.
                  UserDescription: Internal support routine.
                  Notes: Stores the resolved value in `blackboard['result']` and logs whether a match was found.
                """
                from ...AgentArray import AgentArray
                ids = AgentArray.GetAgentArray()
                found = 0

                for aid in ids:
                    if Agent.GetModelID(aid) == model_id:
                        found = aid
                        break

                node.blackboard["result"] = found
                if found != 0:
                    ConsoleLog("GetAgentIDByModelID", f"Found agent ID {found} for model ID {model_id}.", Console.MessageType.Info, log=log)
                    BehaviorTree.NodeState.SUCCESS
                else:
                    ConsoleLog("GetAgentIDByModelID", f"No agent found for model ID {model_id}.", Console.MessageType.Warning, log=log) 
                    BehaviorTree.NodeState.FAILURE
                
                return (BehaviorTree.NodeState.SUCCESS
                        if found != 0
                        else BehaviorTree.NodeState.FAILURE)

            tree = BehaviorTree.ActionNode(name="GetAgentIDByModelID",
                action_fn=_search_model_id)
            return BehaviorTree(tree)
        
    @staticmethod
    def TargetAgentByName(agent_name:str, log:bool=False):
            """
            Build a tree that resolves and targets an agent by name.

            Meta:
              Expose: true
              Audience: beginner
              Display: Target Agent By Name
              Purpose: Find an agent by name and change target to it.
              UserDescription: Use this when you want to target a known agent name directly.
              Notes: Resolves the agent id first and then forwards to the player target change routine.
            """
            tree = BehaviorTree.SequenceNode(name="TargetAgentByName",
                children=[
                    BehaviorTree.SubtreeNode(name="GetAgentIDByNameSubtree",
                                             subtree_fn=lambda node: BTAgents.GetAgentIDByName(agent_name)),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BTPlayer.ChangeTarget(node.blackboard.get("result", 0),log=log))
                ]
            )
            return BehaviorTree(tree)

    @staticmethod
    def TargetAgentByModelID(model_id: int, log: bool = False):
            """
            Build a tree that resolves and targets an agent by model id.

            Meta:
              Expose: true
              Audience: beginner
              Display: Target Agent By Model ID
              Purpose: Find an agent by model id and change target to it.
              UserDescription: Use this when you want to target a known model id directly.
              Notes: Resolves the agent id first and then forwards to the player target change routine.
            """
            tree = BehaviorTree.SequenceNode(name="TargetAgentByModelID",
                children=[
                    BehaviorTree.SubtreeNode(name="GetAgentIDByModelIDSubtree",
                                             subtree_fn=lambda node: BTAgents.GetAgentIDByModelID(model_id, log=log)),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BTPlayer.ChangeTarget(node.blackboard.get("result", 0), log=log))
                ]
            )
            return BehaviorTree(tree)

    @staticmethod
    def InteractAndDialog(dialog_id: str | int, log: bool = False) -> BehaviorTree:
        """
        Build a tree that interacts with the current target and sends a dialog id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Interact And Dialog
          Purpose: Interact with the current target and send a dialog id.
          UserDescription: Use this when a target interaction needs a manual dialog response.
          Notes: Delegates to the player interaction-and-dialog routine.
        """
        return BTPlayer.InteractAndDialog(dialog_id=dialog_id, log=log)

    @staticmethod
    def InteractAndAutomaticDialog(button_number: int, log: bool = False) -> BehaviorTree:
        """
        Build a tree that interacts with the current target and presses an automatic dialog button.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Interact And Automatic Dialog
          Purpose: Interact with the current target and choose an automatic dialog button.
          UserDescription: Use this when a target interaction needs a visible dialog button selection.
          Notes: Delegates to the player interaction-and-automatic-dialog routine.
        """
        return BTPlayer.InteractAndAutomaticDialog(button_number=button_number, log=log)

    @staticmethod
    def MoveAndTarget(
        x: float,
        y: float,
        target_distance: float = Range.Adjacent.value,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that moves to coordinates and then targets a nearby NPC.

        Meta:
          Expose: true
          Audience: beginner
          Display: Move And Target
          Purpose: Move to a location and then target a nearby NPC.
          UserDescription: Use this when you want an agent-oriented move and target flow from coordinates.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveAndTarget(x=x, y=y, target_distance=target_distance, log=log)

    @staticmethod
    def TargetAndInteract(target_distance: float = 4500.0, log: bool = False) -> BehaviorTree:
            """
            Build a tree that targets the nearest NPC and interacts with it.

            Meta:
              Expose: true
              Audience: beginner
              Display: Target And Interact
              Purpose: Target the nearest NPC within range and interact with it.
              UserDescription: Use this when you want a simple target-and-interact flow for nearby NPCs.
              Notes: Uses the nearest-NPC selector before running the interaction step.
            """
            return BTCompositeHelpers.target_and_interact(
                target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
                log=log,
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
          Purpose: Move to a location, target a nearby NPC, and interact.
          UserDescription: Use this when you want to travel somewhere and immediately interact with a nearby NPC.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveTargetAndInteract(x=x, y=y, target_distance=target_distance, log=log)

    @staticmethod
    def TargetInteractAndDialog(
            target_distance: float = Range.Nearby.value,
            dialog_id: str | int = 0,
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that targets the nearest NPC, interacts, and sends a dialog id.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Target Interact And Dialog
              Purpose: Target the nearest NPC, interact with it, and send a dialog id.
              UserDescription: Use this when a nearby NPC flow requires both interaction and a manual dialog response.
              Notes: Uses nearest-NPC targeting before interaction and dialog dispatch.
            """
            return BTCompositeHelpers.target_interact_and_dialog(
                target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
                dialog_id=dialog_id,
                log=log,
            )

    @staticmethod
    def TargetInteractAndAutomaticDialog(
            target_distance: float = Range.Nearby.value,
            button_number: int = 0,
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that targets the nearest NPC, interacts, and presses an automatic dialog button.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Target Interact And Automatic Dialog
              Purpose: Target the nearest NPC, interact with it, and choose an automatic dialog button.
              UserDescription: Use this when a nearby NPC flow requires a visible dialog button selection.
              Notes: Uses nearest-NPC targeting before interaction and automatic dialog selection.
            """
            return BTCompositeHelpers.target_interact_and_automatic_dialog(
                target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
                button_number=button_number,
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
        Build a tree that moves to coordinates, targets a nearby NPC, interacts, and sends a dialog id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Dialog
          Purpose: Move to a location, interact with a nearby NPC, and send a dialog id.
          UserDescription: Use this when a travel step should end with an NPC interaction and dialog response.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveTargetInteractAndDialog(
            x=x,
            y=y,
            target_distance=target_distance,
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
        Build a tree that moves to coordinates, targets a nearby NPC, interacts, and presses an automatic dialog button.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Automatic Dialog
          Purpose: Move to a location, interact with a nearby NPC, and choose an automatic dialog button.
          UserDescription: Use this when a travel step should end with an NPC interaction and visible dialog button selection.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveTargetInteractAndAutomaticDialog(
            x=x,
            y=y,
            target_distance=target_distance,
            button_number=button_number,
            log=log,
        )

    @staticmethod
    def MoveAndTargetByModelID(
        model_id: int,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, and targets it.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move And Target By Model ID
          Purpose: Resolve an agent by model id, move to it, and target it.
          UserDescription: Use this when you know the model id of the agent you want to approach and target.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveAndTargetByModelID(model_id=model_id, log=log)

    @staticmethod
    def TargetAndInteractByModelID(model_id: int, log: bool = False) -> BehaviorTree:
            """
            Build a tree that targets an agent by model id and interacts with it.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Target And Interact By Model ID
              Purpose: Target an agent by model id and interact with it.
              UserDescription: Use this when you know the model id of the agent you want to interact with directly.
              Notes: Resolves the target from model id before interaction.
            """
            return BTCompositeHelpers.target_and_interact(
                target_tree=BTAgents.TargetAgentByModelID(model_id=model_id, log=log),
                log=log,
            )

    @staticmethod
    def MoveTargetAndInteractByModelID(
        model_id: int,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, and interacts.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target And Interact By Model ID
          Purpose: Resolve an agent by model id, move to it, target it, and interact.
          UserDescription: Use this when you want an approach-and-interact flow for a known model id.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveTargetAndInteractByModelID(model_id=model_id, log=log)

    @staticmethod
    def TargetInteractAndDialogByModelID(
            model_id: int,
            dialog_id: str | int = 0,
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that targets an agent by model id, interacts, and sends a dialog id.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Target Interact And Dialog By Model ID
              Purpose: Target an agent by model id, interact with it, and send a dialog id.
              UserDescription: Use this when a known model id requires interaction plus a manual dialog response.
              Notes: Resolves the target from model id before interaction and dialog dispatch.
            """
            return BTCompositeHelpers.target_interact_and_dialog(
                target_tree=BTAgents.TargetAgentByModelID(model_id=model_id, log=log),
                dialog_id=dialog_id,
                log=log,
            )

    @staticmethod
    def TargetInteractAndAutomaticDialogByModelID(
            model_id: int,
            button_number: int = 0,
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that targets an agent by model id, interacts, and presses an automatic dialog button.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Target Interact And Automatic Dialog By Model ID
              Purpose: Target an agent by model id, interact with it, and choose an automatic dialog button.
              UserDescription: Use this when a known model id requires interaction plus a visible dialog button selection.
              Notes: Resolves the target from model id before interaction and automatic dialog selection.
            """
            return BTCompositeHelpers.target_interact_and_automatic_dialog(
                target_tree=BTAgents.TargetAgentByModelID(model_id=model_id, log=log),
                button_number=button_number,
                log=log,
            )
        
    @staticmethod
    def MoveTargetInteractAndDialogByModelID(
        model_id: int,
        dialog_id: str | int = 0,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, interacts, and sends a dialog id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Dialog By Model ID
          Purpose: Resolve an agent by model id, move to it, interact, and send a dialog id.
          UserDescription: Use this when a known model id requires a full move, interaction, and dialog flow.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveTargetInteractAndDialogByModelID(
            model_id=model_id,
            dialog_id=dialog_id,
            log=log,
        )

    @staticmethod
    def MoveTargetInteractAndAutomaticDialogByModelID(
        model_id: int,
        button_number: int = 0,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, interacts, and presses an automatic dialog button.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Automatic Dialog By Model ID
          Purpose: Resolve an agent by model id, move to it, interact, and choose an automatic dialog button.
          UserDescription: Use this when a known model id requires a full move, interaction, and visible dialog button flow.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveTargetInteractAndAutomaticDialogByModelID(
            model_id=model_id,
            button_number=button_number,
            log=log,
        )

    @staticmethod
    def TargetNearestNPC(distance:float = 4500.0, log:bool=False):
            """
            Build a tree that finds and targets the nearest NPC within range.

            Meta:
              Expose: true
              Audience: beginner
              Display: Target Nearest NPC
              Purpose: Find the nearest NPC within range and change target to it.
              UserDescription: Use this when you want to target the nearest NPC automatically.
              Notes: Stores the resolved NPC id on the blackboard before changing target.
            """
            def _find_nearest_npc(node):
                """
                Resolve the nearest NPC within the requested range.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Find Nearest NPC Helper
                  Purpose: Find the nearest NPC and store its id on the blackboard for the enclosing targeting routine.
                  UserDescription: Internal support routine.
                  Notes: Stores the resolved NPC id in `blackboard['nearest_npc_id']`.
                """
                from ..Agents import Agents as RoutinesAgents
                nearest_npc = RoutinesAgents.GetNearestNPC(distance)
                node.blackboard["nearest_npc_id"] = nearest_npc
                if nearest_npc != 0:
                    ConsoleLog("TargetNearestNPC", f"Found nearest NPC with ID {nearest_npc} within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestNPC", f"No NPC found within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestNPCRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestNPC", action_fn=_find_nearest_npc),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BTPlayer.ChangeTarget(node.blackboard.get("nearest_npc_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
    @staticmethod
    def TargetNearestNPCXY(x,y,distance, log:bool=False):
            """
            Build a tree that finds and targets the nearest NPC near specific coordinates.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Target Nearest NPC XY
              Purpose: Find the nearest NPC around a coordinate pair and change target to it.
              UserDescription: Use this when you want to target an NPC near a specific location rather than near the player.
              Notes: Stores the resolved NPC id on the blackboard before changing target.
            """
            def _find_nearest_npc_xy(node):
                """
                Resolve the nearest NPC around a specific coordinate pair.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Find Nearest NPC XY Helper
                  Purpose: Find the nearest NPC around the provided coordinates and store its id on the blackboard.
                  UserDescription: Internal support routine.
                  Notes: Stores the resolved NPC id in `blackboard['nearest_npc_id']`.
                """
                from ..Agents import Agents as RoutinesAgents
                nearest_npc = RoutinesAgents.GetNearestNPCXY(x,y,distance)
                node.blackboard["nearest_npc_id"] = nearest_npc
                if nearest_npc != 0:
                    ConsoleLog("TargetNearestNPCXY", f"Found nearest NPC with ID {nearest_npc} near ({x}, {y}) within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestNPCXY", f"No NPC found near ({x}, {y}) within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestNPCXYRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestNPCXY", action_fn=_find_nearest_npc_xy),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BTPlayer.ChangeTarget(node.blackboard.get("nearest_npc_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
    @staticmethod
    def TargetNearestGadgetXY(x,y,distance, log:bool=False):
            """
            Build a tree that finds and targets the nearest gadget near specific coordinates.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Target Nearest Gadget XY
              Purpose: Find the nearest gadget around a coordinate pair and change target to it.
              UserDescription: Use this when you want to target a gadget near a specific location.
              Notes: Stores the resolved gadget id on the blackboard before changing target.
            """
            def _find_nearest_gadget_xy(node):
                """
                Resolve the nearest gadget around a specific coordinate pair.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Find Nearest Gadget XY Helper
                  Purpose: Find the nearest gadget around the provided coordinates and store its id on the blackboard.
                  UserDescription: Internal support routine.
                  Notes: Stores the resolved gadget id in `blackboard['nearest_gadget_id']`.
                """
                from ..Agents import Agents as RoutinesAgents
                nearest_gadget = RoutinesAgents.GetNearestGadgetXY(x,y, distance)
                node.blackboard["nearest_gadget_id"] = nearest_gadget
                if nearest_gadget != 0:
                    ConsoleLog("TargetNearestGadgetXY", f"Found nearest gadget with ID {nearest_gadget} near ({x}, {y}) within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestGadgetXY", f"No gadget found near ({x}, {y}) within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestGadgetXYRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestGadgetXY", action_fn=_find_nearest_gadget_xy),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BTPlayer.ChangeTarget(node.blackboard.get("nearest_gadget_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
    @staticmethod
    def TargetNearestItemXY(x,y,distance, log:bool=False):
            """
            Build a tree that finds and targets the nearest item near specific coordinates.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Target Nearest Item XY
              Purpose: Find the nearest item around a coordinate pair and change target to it.
              UserDescription: Use this when you want to target an item near a specific location.
              Notes: Stores the resolved item id on the blackboard before changing target.
            """
            def _find_nearest_item_xy(node):
                """
                Resolve the nearest item around a specific coordinate pair.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Find Nearest Item XY Helper
                  Purpose: Find the nearest item around the provided coordinates and store its id on the blackboard.
                  UserDescription: Internal support routine.
                  Notes: Stores the resolved item id in `blackboard['nearest_item_id']`.
                """
                from ..Agents import Agents as RoutinesAgents
                nearest_item = RoutinesAgents.GetNearestItemXY(x,y, distance)
                node.blackboard["nearest_item_id"] = nearest_item
                if nearest_item != 0:
                    ConsoleLog("TargetNearestItemXY", f"Found nearest item with ID {nearest_item} near ({x}, {y}) within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestItemXY", f"No item found near ({x}, {y}) within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestItemXYRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestItemXY", action_fn=_find_nearest_item_xy),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BTPlayer.ChangeTarget(node.blackboard.get("nearest_item_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
    @staticmethod
    def TargetNearestEnemy(distance, log:bool=False):
            """
            Build a tree that finds and targets the nearest enemy within range.

            Meta:
              Expose: true
              Audience: beginner
              Display: Target Nearest Enemy
              Purpose: Find the nearest enemy within range and change target to it.
              UserDescription: Use this when you want combat targeting to acquire the nearest enemy automatically.
              Notes: Stores the resolved enemy id on the blackboard before changing target.
            """
            def _find_nearest_enemy(node):
                """
                Resolve the nearest enemy within the requested range.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Find Nearest Enemy Helper
                  Purpose: Find the nearest enemy and store its id on the blackboard for the enclosing targeting routine.
                  UserDescription: Internal support routine.
                  Notes: Stores the resolved enemy id in `blackboard['nearest_enemy_id']`.
                """
                from ..Agents import Agents as RoutinesAgents
                nearest_enemy = RoutinesAgents.GetNearestEnemy(distance)
                node.blackboard["nearest_enemy_id"] = nearest_enemy
                if nearest_enemy != 0:
                    ConsoleLog("TargetNearestEnemy", f"Found nearest enemy with ID {nearest_enemy} within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestEnemy", f"No enemy found within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestEnemyRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestEnemy", action_fn=_find_nearest_enemy),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BTPlayer.ChangeTarget(node.blackboard.get("nearest_enemy_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)

    @staticmethod
    def ClearEnemiesInArea(
            x: float,
            y: float,
            radius: float = float(Range.Earshot.value),
            interact_interval_ms: int = 750,
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that repeatedly targets and interacts with enemies inside an area until it is clear.

            Meta:
              Expose: true
              Audience: advanced
              Display: Clear Enemies In Area
              Purpose: Keep interacting with enemies in an area until no alive enemies remain there.
              UserDescription: Use this when you want a service-like combat loop for a specific area center and radius.
              Notes: Returns RUNNING while enemies remain and SUCCESS once the area is clear.
            """
            from ...Py4GWcorelib import Utils

            state = {
                "last_interact_ms": 0,
                "last_target_id": 0,
            }

            def _get_enemies_in_area() -> list[int]:
                """
                Collect alive enemies inside the configured area and sort them by distance.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Get Enemies In Area Helper
                  Purpose: Build the current ordered enemy list for the clear-area service loop.
                  UserDescription: Internal support routine.
                  Notes: Filters dead enemies out before sorting by player distance.
                """
                enemy_array = list(RoutinesAgents.GetFilteredEnemyArray(x, y, radius) or [])
                enemy_array = [agent_id for agent_id in enemy_array if Agent.IsAlive(agent_id)]
                enemy_array.sort(key=lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)))
                return enemy_array

            def _clear_enemies(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                """
                Drive the clear-area enemy interaction loop for the configured area.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Clear Enemies Helper
                  Purpose: Repeatedly target and interact with enemies in the configured area until none remain.
                  UserDescription: Internal support routine.
                  Notes: Stores area and target data on the blackboard and throttles repeated interact attempts.
                """
                now = Utils.GetBaseTimestamp()
                enemies = _get_enemies_in_area()
                node.blackboard["clear_area_enemy_count"] = len(enemies)
                node.blackboard["clear_area_center"] = (x, y)
                node.blackboard["clear_area_radius"] = radius

                if not enemies:
                    if log:
                        ConsoleLog(
                            "ClearEnemiesInArea",
                            f"Area at ({x}, {y}) is clear.",
                            Console.MessageType.Success,
                            log=log,
                        )
                    state["last_target_id"] = 0
                    state["last_interact_ms"] = 0
                    return BehaviorTree.NodeState.SUCCESS

                target_id = enemies[0]
                node.blackboard["clear_area_target_id"] = target_id

                if state["last_target_id"] != target_id or now - state["last_interact_ms"] >= interact_interval_ms:
                    Player.ChangeTarget(target_id)
                    Player.Interact(target_id, False)
                    state["last_target_id"] = target_id
                    state["last_interact_ms"] = now
                    if log:
                        ConsoleLog(
                            "ClearEnemiesInArea",
                            f"Clearing area: interacting enemy {target_id} near ({x}, {y}); remaining enemies={len(enemies)}.",
                            Console.MessageType.Info,
                            log=log,
                        )

                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree(
                BehaviorTree.ConditionNode(
                    name="ClearEnemiesInArea",
                    condition_fn=_clear_enemies,
                )
            )
        
    @staticmethod
    def TargetNearestItem(distance, log:bool=False):
            """
            Build a tree that finds and targets the nearest item within range.

            Meta:
              Expose: true
              Audience: beginner
              Display: Target Nearest Item
              Purpose: Find the nearest item within range and change target to it.
              UserDescription: Use this when you want to target a nearby item automatically.
              Notes: Stores the resolved item id on the blackboard before changing target.
            """
            def _find_nearest_item(node):
                """
                Resolve the nearest item within the requested range.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Find Nearest Item Helper
                  Purpose: Find the nearest item and store its id on the blackboard for the enclosing targeting routine.
                  UserDescription: Internal support routine.
                  Notes: Stores the resolved item id in `blackboard['nearest_item_id']`.
                """
                from ..Agents import Agents as RoutinesAgents
                nearest_item = RoutinesAgents.GetNearestItem(distance)
                node.blackboard["nearest_item_id"] = nearest_item
                if nearest_item != 0:
                    ConsoleLog("TargetNearestItem", f"Found nearest item with ID {nearest_item} within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestItem", f"No item found within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestItemRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestItem", action_fn=_find_nearest_item),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BTPlayer.ChangeTarget(node.blackboard.get("nearest_item_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
    @staticmethod
    def TargetNearestChest(distance, log:bool=False):
            """
            Build a tree that finds and targets the nearest chest within range.

            Meta:
              Expose: true
              Audience: beginner
              Display: Target Nearest Chest
              Purpose: Find the nearest chest within range and change target to it.
              UserDescription: Use this when you want to target a nearby chest automatically.
              Notes: Stores the resolved chest id on the blackboard before changing target.
            """
            def _find_nearest_chest(node):
                """
                Resolve the nearest chest within the requested range.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Find Nearest Chest Helper
                  Purpose: Find the nearest chest and store its id on the blackboard for the enclosing targeting routine.
                  UserDescription: Internal support routine.
                  Notes: Stores the resolved chest id in `blackboard['nearest_chest_id']`.
                """
                from ..Agents import Agents as RoutinesAgents
                nearest_chest = RoutinesAgents.GetNearestChest(distance)
                node.blackboard["nearest_chest_id"] = nearest_chest
                if nearest_chest != 0:
                    ConsoleLog("TargetNearestChest", f"Found nearest chest with ID {nearest_chest} within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestChest", f"No chest found within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestChestRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestChest", action_fn=_find_nearest_chest),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BTPlayer.ChangeTarget(node.blackboard.get("nearest_chest_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
        
        

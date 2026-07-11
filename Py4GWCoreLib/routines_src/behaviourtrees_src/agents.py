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
import time
from typing import Any, TypedDict
import time
from ...native_src.internals.types import PointOrPath, PointPath, Vec2f


def _log(source: str, message: str, *, log: bool = False, message_type=Console.MessageType.Info) -> None:
    ConsoleLog(source, message, message_type, log=log)


def _fail_log(source: str, message: str, message_type=Console.MessageType.Warning) -> None:
    ConsoleLog(source, message, message_type, log=True)


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
    def _resolve_model_id_value(modelID_or_encStr: int | str) -> int:
            if isinstance(modelID_or_encStr, str):
                return Agent.GetModelIDByEncString(modelID_or_encStr)
            return int(modelID_or_encStr)

    @staticmethod
    def _resolve_aggro_area(aggro_area: float | Range) -> Any:
            if isinstance(aggro_area, Range):
                return aggro_area
            return float(aggro_area)

    @staticmethod
    def WaitUntilOutOfCombat(range: float = Range.Earshot.value, timeout_ms: int = 60000, log: bool = False) -> BehaviorTree:
            """
            Build a tree that waits until no danger remains within the requested aggro range.

            Meta:
              Expose: true
              Audience: beginner
              Display: Wait Until Out Of Combat
              Purpose: Wait until nearby combat danger clears.
              UserDescription: Use this when a step should pause until the player is safely out of combat.
              Notes: Uses the standard agent-danger check against the provided aggro radius.
            """
            aggro_area = BTAgents._resolve_aggro_area(range)

            def _wait_until_out_of_combat() -> BehaviorTree.NodeState:
                if not Checks.Agents.InDanger(aggro_area=aggro_area):
                    _log("WaitUntilOutOfCombat", f"No danger remains within range {range}.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree(
                BehaviorTree.WaitUntilNode(
                    name="WaitUntilOutOfCombat",
                    condition_fn=_wait_until_out_of_combat,
                    throttle_interval_ms=1000,
                    timeout_ms=timeout_ms,
                )
            )

    @staticmethod
    def WaitUntilOnCombat(range: float = Range.Earshot.value, timeout_ms: int = 60000, log: bool = False) -> BehaviorTree:
            """
            Build a tree that waits until nearby combat danger is detected.

            Meta:
              Expose: true
              Audience: beginner
              Display: Wait Until On Combat
              Purpose: Wait until nearby combat danger begins.
              UserDescription: Use this when a step should pause until the player enters combat.
              Notes: Uses the standard agent-danger check against the provided aggro radius.
            """
            aggro_area = BTAgents._resolve_aggro_area(range)

            def _wait_until_on_combat() -> BehaviorTree.NodeState:
                if Checks.Agents.InDanger(aggro_area=aggro_area):
                    _log("WaitUntilOnCombat", f"Combat danger detected within range {range}.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree(
                BehaviorTree.WaitUntilNode(
                    name="WaitUntilOnCombat",
                    condition_fn=_wait_until_on_combat,
                    throttle_interval_ms=1000,
                    timeout_ms=timeout_ms,
                )
            )

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
    def GetAgentIDByModelID(modelID_or_encStr: int | str, log: bool = False) -> BehaviorTree:
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
                resolved_model_id = BTAgents._resolve_model_id_value(modelID_or_encStr)

                node.blackboard["resolved_model_id"] = resolved_model_id
                if resolved_model_id == 0:
                    _fail_log("GetAgentIDByModelID", f"Failed to resolve model ID from '{modelID_or_encStr}'.")
                    node.blackboard["result"] = 0
                    return BehaviorTree.NodeState.FAILURE

                for aid in ids:
                    if Agent.GetModelID(aid) == resolved_model_id:
                        found = aid
                        break

                node.blackboard["result"] = found
                if found != 0:
                    _log("GetAgentIDByModelID", f"Found agent ID {found} for model ID {resolved_model_id}.", log=log)
                    BehaviorTree.NodeState.SUCCESS
                else:
                    _fail_log("GetAgentIDByModelID", f"No agent found for model ID {resolved_model_id}.")
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
    def TargetAgentByModelID(modelID_or_encStr: int | str, log: bool = False):
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
                                             subtree_fn=lambda node: BTAgents.GetAgentIDByModelID(modelID_or_encStr, log=log)),
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
        modelID_or_encStr: int | str,
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
        return BTMovement.MoveAndTargetByModelID(modelID_or_encStr=modelID_or_encStr, log=log)

    @staticmethod
    def TargetAndInteractByModelID(modelID_or_encStr: int | str, log: bool = False) -> BehaviorTree:
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
                target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
                log=log,
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
          UserDescription: Use this when you want an approach-and-interact flow for a known model id.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveTargetAndInteractByModelID(modelID_or_encStr=modelID_or_encStr, log=log)

    @staticmethod
    def TargetInteractAndDialogByModelID(
            modelID_or_encStr: int | str,
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
                target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
                dialog_id=dialog_id,
                log=log,
            )

    @staticmethod
    def TargetInteractAndAutomaticDialogByModelID(
            modelID_or_encStr: int | str,
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
                target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
                button_number=button_number,
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
          Purpose: Resolve an agent by model id, move to it, interact, and send a dialog id.
          UserDescription: Use this when a known model id requires a full move, interaction, and dialog flow.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveTargetInteractAndDialogByModelID(
            modelID_or_encStr=modelID_or_encStr,
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
          Purpose: Resolve an agent by model id, move to it, interact, and choose an automatic dialog button.
          UserDescription: Use this when a known model id requires a full move, interaction, and visible dialog button flow.
          Notes: Delegates to the movement group implementation.
        """
        return BTMovement.MoveTargetInteractAndAutomaticDialogByModelID(
            modelID_or_encStr=modelID_or_encStr,
            button_number=button_number,
            log=log,
    )



    @staticmethod
    def MoveAndInteractWithGadget(
        gadget_id: int | None = None,
        pos: PointOrPath | None = None,
        search_distance: float = 5_000.0,
        interaction_distance: float = Range.Nearby.value,
        interaction_count: int = 1,
        interaction_interval_ms: int = 500,
        account_settle_ms: int = 5_000,
        timeout_ms: int = 90_000,
        multi_account: bool = False,
        include_self: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that finds a gadget by its internal gadget id, moves to it,
        and interacts with it.

        When multibox mode is enabled, the local account interacts first. Remote
        accounts in the same map instance are then processed one at a time. The
        node waits for each shared-memory interaction command to finish before
        dispatching the next one.

        Meta:
        Expose: true
        Audience: advanced
        Display: Move And Interact With Gadget By ID
        Purpose: Find a specific gadget, move to it, and interact locally or sequentially across multiple accounts.
        UserDescription: Use this when a chest, lock, lever, or other known gadget must be interacted with by one or several accounts.
        Notes: Remote accounts are filtered by map instance and processed sequentially.
        """
        from ...AgentArray import AgentArray
        from ...GlobalCache import GLOBAL_CACHE
        from ...Py4GWcorelib import Utils
        from ...enums_src.Multiboxing_enums import SharedCommandType

        class GadgetInteractionState(TypedDict):
            phase: str
            started_at: float

            target_agent_id: int
            target_xy: tuple[float, float] | None

            local_interaction_count: int
            next_action_at: float

            account_emails: list[str]
            account_index: int
            account_interaction_count: int

            current_account_email: str
            current_message_index: int
            remote_command_deadline: float

            settle_until: float

        resolved_search_point: Vec2f | None = None

        if pos is not None:
            try:
                resolved_path = PointPath.as_path(pos)
                if resolved_path:
                    resolved_search_point = resolved_path[-1]
            except Exception:
                resolved_search_point = None

        state: GadgetInteractionState = {
            "phase": "find",
            "started_at": 0.0,

            "target_agent_id": 0,
            "target_xy": None,

            "local_interaction_count": 0,
            "next_action_at": 0.0,

            "account_emails": [],
            "account_index": 0,
            "account_interaction_count": 0,

            "current_account_email": "",
            "current_message_index": -1,
            "remote_command_deadline": 0.0,

            "settle_until": 0.0,
        }

        def _reset() -> None:
            state["phase"] = "find"
            state["started_at"] = 0.0

            state["target_agent_id"] = 0
            state["target_xy"] = None

            state["local_interaction_count"] = 0
            state["next_action_at"] = 0.0

            state["account_emails"] = []
            state["account_index"] = 0
            state["account_interaction_count"] = 0

            state["current_account_email"] = ""
            state["current_message_index"] = -1
            state["remote_command_deadline"] = 0.0

            state["settle_until"] = 0.0

        def _stop_local_player() -> None:
            try:
                player_x, player_y = Player.GetXY()
                Player.Move(
                    float(player_x),
                    float(player_y),
                )
            except Exception:
                pass

        def _is_matching_gadget(agent_id: int) -> bool:
            if agent_id <= 0:
                return False

            if gadget_id is None:
                return Agent.IsValid(agent_id)

            try:
                return (
                    int(Agent.GetGadgetID(agent_id) or 0)
                    == int(gadget_id)
                )
            except Exception:
                return False

        def _find_gadget() -> tuple[
            int,
            tuple[float, float] | None,
        ]:
            # Cas 1 : recherche par gadget ID
            if gadget_id is not None:
                if resolved_search_point is None:
                    agent_id = int(
                        RoutinesAgents.GetNearestGadgetByID(
                            gadget_id=int(gadget_id),
                            max_distance=float(search_distance),
                        )
                        or 0
                    )

                    if agent_id <= 0:
                        return 0, None

                    xy = Agent.GetXY(agent_id)

                    return (
                        agent_id,
                        (
                            float(xy[0]),
                            float(xy[1]),
                        ),
                    )

                origin = (
                    float(resolved_search_point.x),
                    float(resolved_search_point.y),
                )

                gadget_agents = AgentArray.GetGadgetArray()
                gadget_agents = AgentArray.Filter.ByDistance(
                    gadget_agents,
                    origin,
                    float(search_distance),
                )
                gadget_agents = AgentArray.Sort.ByDistance(
                    gadget_agents,
                    origin,
                )

                for candidate_id in gadget_agents:
                    agent_id = int(candidate_id)

                    if not _is_matching_gadget(agent_id):
                        continue

                    xy = Agent.GetXY(agent_id)

                    return (
                        agent_id,
                        (
                            float(xy[0]),
                            float(xy[1]),
                        ),
                    )

                return 0, None

            # Cas 2 : aucun ID, recherche du gadget le plus proche de pos
            if resolved_search_point is not None:
                agent_id = int(
                    RoutinesAgents.GetNearestGadgetXY(
                        float(resolved_search_point.x),
                        float(resolved_search_point.y),
                        float(search_distance),
                    )
                    or 0
                )
            else:
                # Cas 3 : aucun ID et aucune position
                agent_id = int(
                    RoutinesAgents.GetNearestGadget(
                        float(search_distance),
                    )
                    or 0
                )

            if agent_id <= 0:
                return 0, None

            xy = Agent.GetXY(agent_id)

            return (
                agent_id,
                (
                    float(xy[0]),
                    float(xy[1]),
                ),
            )

        def _read_party_id(account_data) -> int:
            """
            Read PartyID defensively because its exact nesting can vary between
            shared-memory account-data versions.
            """
            candidates = (
                getattr(account_data, "PartyID", None),
                getattr(
                    getattr(
                        account_data,
                        "AgentData",
                        None,
                    ),
                    "PartyID",
                    None,
                ),
                getattr(
                    getattr(
                        getattr(
                            account_data,
                            "AgentData",
                            None,
                        ),
                        "Party",
                        None,
                    ),
                    "PartyID",
                    None,
                ),
            )

            for value in candidates:
                try:
                    resolved_value = int(value or 0)
                except Exception:
                    continue

                if resolved_value > 0:
                    return resolved_value

            return 0

        def _same_map_instance(
            leader_data,
            account_data,
        ) -> bool:
            try:
                leader_map = leader_data.AgentData.Map
                account_map = account_data.AgentData.Map

                return bool(
                    int(account_map.MapID)
                    == int(leader_map.MapID)
                    and account_map.Region
                    == leader_map.Region
                    and account_map.Language
                    == leader_map.Language
                    and account_map.District
                    == leader_map.District
                )
            except Exception:
                return False

        def _same_party_if_known(
            leader_data,
            account_data,
        ) -> bool:
            leader_party_id = _read_party_id(
                leader_data
            )
            account_party_id = _read_party_id(
                account_data
            )

            # Some shared-memory versions do not expose PartyID.
            # In that case, the map-instance filter remains authoritative.
            if (
                leader_party_id <= 0
                or account_party_id <= 0
            ):
                return True

            return account_party_id == leader_party_id

        def _collect_remote_accounts() -> list[str]:
            sender_email = str(
                Player.GetAccountEmail() or ""
            )

            if not sender_email:
                return []

            try:
                leader_data = (
                    GLOBAL_CACHE.ShMem
                    .GetAccountDataFromEmail(
                        sender_email
                    )
                )
            except Exception:
                leader_data = None

            if leader_data is None:
                _fail_log(
                    "MoveAndInteractWithGadgetByID",
                    (
                        "Could not resolve the local "
                        "shared-memory account data."
                    ),
                )
                return []

            account_emails: list[str] = []

            for account_data in (
                GLOBAL_CACHE.ShMem.GetAllAccountData()
                or []
            ):
                account_email = str(
                    getattr(
                        account_data,
                        "AccountEmail",
                        "",
                    )
                    or ""
                )

                if not account_email:
                    continue

                if account_email == sender_email:
                    continue

                if not bool(
                    getattr(
                        account_data,
                        "IsSlotActive",
                        True,
                    )
                ):
                    continue

                if not _same_map_instance(
                    leader_data,
                    account_data,
                ):
                    continue

                if not _same_party_if_known(
                    leader_data,
                    account_data,
                ):
                    continue

                account_emails.append(
                    account_email
                )

            return account_emails

        def _message_is_active(
            message_index: int,
            sender_email: str,
            receiver_email: str,
        ) -> bool:
            if message_index < 0:
                return False

            try:
                message = GLOBAL_CACHE.ShMem.GetInbox(
                    message_index
                )
            except Exception:
                return False

            if message is None:
                return False

            try:
                return bool(
                    getattr(message, "Active", False)
                    and str(
                        getattr(
                            message,
                            "SenderEmail",
                            "",
                        )
                        or ""
                    )
                    == sender_email
                    and str(
                        getattr(
                            message,
                            "ReceiverEmail",
                            "",
                        )
                        or ""
                    )
                    == receiver_email
                    and int(
                        getattr(
                            message,
                            "Command",
                            -1,
                        )
                    )
                    == int(
                        SharedCommandType
                        .InteractWithTarget
                    )
                )
            except Exception:
                return False

        def _move_and_interact(
            node: BehaviorTree.Node,
        ) -> BehaviorTree.NodeState:
            now = time.monotonic()

            if bool(
                node.blackboard.get(
                    "USER_INTERRUPT_ACTIVE",
                    False,
                )
            ):
                _stop_local_player()
                _reset()
                return BehaviorTree.NodeState.FAILURE

            if state["started_at"] <= 0.0:
                state["started_at"] = now

            elapsed_ms = (
                now - state["started_at"]
            ) * 1000.0

            if elapsed_ms >= max(
                1,
                int(timeout_ms),
            ):
                _fail_log(
                    "MoveAndInteractWithGadgetByID",
                    (
                        f"Timed out while processing "
                        f"gadget id {gadget_id}."
                    ),
                )
                _stop_local_player()
                _reset()
                return BehaviorTree.NodeState.FAILURE

            phase = state["phase"]

            # -------------------------------------------------
            # Resolve the gadget
            # -------------------------------------------------

            if phase == "find":
                (
                    target_agent_id,
                    target_xy,
                ) = _find_gadget()

                if (
                    target_agent_id <= 0
                    or target_xy is None
                ):
                    return BehaviorTree.NodeState.RUNNING

                state["target_agent_id"] = (
                    target_agent_id
                )
                state["target_xy"] = target_xy

                node.blackboard[
                    "gadget_target_agent_id"
                ] = target_agent_id
                node.blackboard[
                    "gadget_target_id"
                ] = int(gadget_id or 0)
                node.blackboard[
                    "gadget_target_xy"
                ] = target_xy

                _log(
                    "MoveAndInteractWithGadgetByID",
                    (
                        f"Found gadget id {gadget_id}: "
                        f"agent_id={target_agent_id}, "
                        f"position={target_xy}."
                    ),
                    log=log,
                )

                state["phase"] = (
                    "local_move"
                    if include_self
                    else "prepare_accounts"
                )

                return BehaviorTree.NodeState.RUNNING

            target_agent_id = (
                state["target_agent_id"]
            )
            target_xy = state["target_xy"]

            if not _is_matching_gadget(
                target_agent_id
            ):
                _fail_log(
                    "MoveAndInteractWithGadgetByID",
                    (
                        f"Gadget id {gadget_id} "
                        "is no longer valid."
                    ),
                )
                _reset()
                return BehaviorTree.NodeState.FAILURE

            if target_xy is None:
                state["phase"] = "find"
                return BehaviorTree.NodeState.RUNNING

            # -------------------------------------------------
            # Local account
            # -------------------------------------------------

            if phase == "local_move":
                distance_to_gadget = float(
                    Utils.Distance(
                        Player.GetXY(),
                        target_xy,
                    )
                )

                node.blackboard[
                    "gadget_target_distance"
                ] = distance_to_gadget

                if (
                    distance_to_gadget
                    > float(interaction_distance)
                ):
                    Player.Move(
                        float(target_xy[0]),
                        float(target_xy[1]),
                    )
                    return BehaviorTree.NodeState.RUNNING

                _stop_local_player()
                Player.ChangeTarget(
                    target_agent_id
                )

                state["phase"] = (
                    "local_interact"
                )
                state["next_action_at"] = 0.0

                return BehaviorTree.NodeState.RUNNING

            if phase == "local_interact":
                if now < state["next_action_at"]:
                    return BehaviorTree.NodeState.RUNNING

                local_count = state[
                    "local_interaction_count"
                ]

                if local_count < max(
                    1,
                    int(interaction_count),
                ):
                    Player.ChangeTarget(
                        target_agent_id
                    )
                    Player.Interact(
                        target_agent_id,
                        False,
                    )

                    state[
                        "local_interaction_count"
                    ] = local_count + 1

                    state["next_action_at"] = (
                        now
                        + max(
                            0,
                            int(
                                interaction_interval_ms
                            ),
                        )
                        / 1000.0
                    )

                    return BehaviorTree.NodeState.RUNNING

                state["phase"] = (
                    "prepare_accounts"
                )
                return BehaviorTree.NodeState.RUNNING

            # -------------------------------------------------
            # Prepare remote account list
            # -------------------------------------------------

            if phase == "prepare_accounts":
                if not multi_account:
                    _reset()
                    return BehaviorTree.NodeState.SUCCESS

                state["account_emails"] = (
                    _collect_remote_accounts()
                )
                state["account_index"] = 0
                state[
                    "account_interaction_count"
                ] = 0

                state[
                    "current_account_email"
                ] = ""
                state[
                    "current_message_index"
                ] = -1

                state["phase"] = (
                    "remote_dispatch"
                )

                _log(
                    "MoveAndInteractWithGadgetByID",
                    (
                        "Remote accounts in the same "
                        "instance to process: "
                        f"{len(state['account_emails'])}."
                    ),
                    log=log,
                )

                return BehaviorTree.NodeState.RUNNING

            # -------------------------------------------------
            # Remote accounts, sequentially
            # -------------------------------------------------

            if phase == "remote_dispatch":
                account_emails = state[
                    "account_emails"
                ]
                account_index = state[
                    "account_index"
                ]

                if account_index >= len(
                    account_emails
                ):
                    _log(
                        "MoveAndInteractWithGadgetByID",
                        (
                            f"Finished interaction with "
                            f"gadget id {gadget_id}."
                        ),
                        log=log,
                        message_type=(
                            Console.MessageType.Success
                        ),
                    )
                    _reset()
                    return BehaviorTree.NodeState.SUCCESS

                interaction_index = state[
                    "account_interaction_count"
                ]

                if interaction_index >= max(
                    1,
                    int(interaction_count),
                ):
                    state["phase"] = (
                        "remote_settle"
                    )
                    state["settle_until"] = (
                        now
                        + max(
                            0,
                            int(account_settle_ms),
                        )
                        / 1000.0
                    )

                    return BehaviorTree.NodeState.RUNNING

                sender_email = str(
                    Player.GetAccountEmail() or ""
                )
                receiver_email = account_emails[
                    account_index
                ]

                message_index = int(
                    GLOBAL_CACHE.ShMem.SendMessage(
                        sender_email,
                        receiver_email,
                        SharedCommandType
                        .InteractWithTarget,
                        (
                            float(target_agent_id),
                            0.0,
                            0.0,
                            0.0,
                        ),
                    )
                )

                if message_index < 0:
                    _fail_log(
                        "MoveAndInteractWithGadgetByID",
                        (
                            "Failed to dispatch "
                            f"InteractWithTarget to "
                            f"{receiver_email}."
                        ),
                    )

                    # Skip this interaction rather than
                    # blocking the entire routine forever.
                    state[
                        "account_interaction_count"
                    ] = interaction_index + 1
                    state["next_action_at"] = (
                        now
                        + max(
                            0,
                            int(
                                interaction_interval_ms
                            ),
                        )
                        / 1000.0
                    )
                    state["phase"] = (
                        "remote_interval"
                    )
                    return BehaviorTree.NodeState.RUNNING

                state[
                    "current_account_email"
                ] = receiver_email
                state[
                    "current_message_index"
                ] = message_index

                state[
                    "remote_command_deadline"
                ] = (
                    now
                    + max(
                        10.0,
                        float(account_settle_ms)
                        / 1000.0,
                    )
                )

                _log(
                    "MoveAndInteractWithGadgetByID",
                    (
                        f"Sent interaction "
                        f"{interaction_index + 1}/"
                        f"{max(1, int(interaction_count))} "
                        f"to account "
                        f"{account_index + 1}/"
                        f"{len(account_emails)} "
                        f"(message={message_index})."
                    ),
                    log=log,
                )

                state["phase"] = (
                    "remote_wait"
                )

                return BehaviorTree.NodeState.RUNNING

            if phase == "remote_wait":
                sender_email = str(
                    Player.GetAccountEmail() or ""
                )
                receiver_email = state[
                    "current_account_email"
                ]
                message_index = state[
                    "current_message_index"
                ]

                if _message_is_active(
                    message_index,
                    sender_email,
                    receiver_email,
                ):
                    if (
                        now
                        < state[
                            "remote_command_deadline"
                        ]
                    ):
                        return BehaviorTree.NodeState.RUNNING

                    _fail_log(
                        "MoveAndInteractWithGadgetByID",
                        (
                            "Remote interaction timed out "
                            f"for {receiver_email}; "
                            "continuing with the next step."
                        ),
                    )

                state[
                    "account_interaction_count"
                ] += 1
                state[
                    "current_account_email"
                ] = ""
                state[
                    "current_message_index"
                ] = -1

                state["next_action_at"] = (
                    now
                    + max(
                        0,
                        int(
                            interaction_interval_ms
                        ),
                    )
                    / 1000.0
                )
                state["phase"] = (
                    "remote_interval"
                )

                return BehaviorTree.NodeState.RUNNING

            if phase == "remote_interval":
                if now < state["next_action_at"]:
                    return BehaviorTree.NodeState.RUNNING

                state["phase"] = (
                    "remote_dispatch"
                )
                return BehaviorTree.NodeState.RUNNING

            if phase == "remote_settle":
                if now < state["settle_until"]:
                    return BehaviorTree.NodeState.RUNNING

                state["account_index"] += 1
                state[
                    "account_interaction_count"
                ] = 0
                state[
                    "current_account_email"
                ] = ""
                state[
                    "current_message_index"
                ] = -1

                state["phase"] = (
                    "remote_dispatch"
                )

                return BehaviorTree.NodeState.RUNNING

            _reset()
            return BehaviorTree.NodeState.FAILURE

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=(
                    "MoveAndInteractWithGadgetByID"
                    f"({gadget_id})"
                ),
                action_fn=_move_and_interact,
            )
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
                    _log("TargetNearestNPC", f"Found nearest NPC with ID {nearest_npc} within distance {distance}.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                _fail_log("TargetNearestNPC", f"No NPC found within distance {distance}.")
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
                    _log("TargetNearestNPCXY", f"Found nearest NPC with ID {nearest_npc} near ({x}, {y}) within distance {distance}.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                _fail_log("TargetNearestNPCXY", f"No NPC found near ({x}, {y}) within distance {distance}.")
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
                    _log("TargetNearestGadgetXY", f"Found nearest gadget with ID {nearest_gadget} near ({x}, {y}) within distance {distance}.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                _fail_log("TargetNearestGadgetXY", f"No gadget found near ({x}, {y}) within distance {distance}.")
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
                    _log("TargetNearestItemXY", f"Found nearest item with ID {nearest_item} near ({x}, {y}) within distance {distance}.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                _fail_log("TargetNearestItemXY", f"No item found near ({x}, {y}) within distance {distance}.")
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
                    _log("TargetNearestEnemy", f"Found nearest enemy with ID {nearest_enemy} within distance {distance}.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                _fail_log("TargetNearestEnemy", f"No enemy found within distance {distance}.")
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
            allowed_alive_enemies: int = 0,
            interact_interval_ms: int = 750,
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that repeatedly targets and interacts with enemies inside an area until it is clear.

            Meta:
              Expose: true
              Audience: advanced
              Display: Clear Enemies In Area
              Purpose: Keep interacting with enemies in an area until the alive-enemy count is at or below an allowed threshold.
              UserDescription: Use this when you want a service-like combat loop for a specific area center and radius.
              Notes: Returns RUNNING while the alive-enemy count exceeds the threshold and SUCCESS once it is at or below it.
            """
            from ...Py4GWcorelib import Utils

            state = {
                "last_interact_ms": 0,
                "last_target_id": 0,
                "paused_for_looting": False,
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
                from typing import Any
                from ...GlobalCache import GLOBAL_CACHE
                from ... import SharedCommandType

                def _get_pause_reason(node: BehaviorTree.Node) -> str:
                    account_email: str = Player.GetAccountEmail()
                    index: int
                    message: Any
                    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
                    if (
                        index != -1
                        and message
                        and message.Command == SharedCommandType.PickUpLoot
                        and bool(getattr(message, "Running", False))
                    ):
                        return "loot_message_active"
                    if Checks.Player.IsDead():
                        return "player_dead"
                    if bool(node.blackboard.get("PAUSE_MOVEMENT", False)):
                        return "external_pause"
                    if Checks.Player.IsCasting():
                        return "casting"
                    return ""
                 
                now = Utils.GetBaseTimestamp()
                enemies = _get_enemies_in_area()
                node.blackboard["clear_area_enemy_count"] = len(enemies)
                node.blackboard["clear_area_center"] = (x, y)
                node.blackboard["clear_area_radius"] = radius
                node.blackboard["clear_area_allowed_alive_enemies"] = allowed_alive_enemies

                pause_reason = _get_pause_reason(node)
                if pause_reason:
                    if log and not state["paused_for_looting"]:
                        _log("ClearEnemiesInArea", f"Pausing clear-area routine near ({x}, {y}) due to {pause_reason}.", log=log)
                    state["paused_for_looting"] = True
                    return BehaviorTree.NodeState.RUNNING

                state["paused_for_looting"] = False

                if len(enemies) <= allowed_alive_enemies:
                    
                    _log(
                        "ClearEnemiesInArea",
                        f"Area at ({x}, {y}) is clear enough: alive_enemies={len(enemies)}, allowed={allowed_alive_enemies}.",
                        log=log,
                        message_type=Console.MessageType.Success,
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
                        _log(
                            "ClearEnemiesInArea",
                            f"Clearing area: interacting enemy {target_id} near ({x}, {y}); remaining enemies={len(enemies)}.",
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
    def WaitForClearEnemiesInArea(
        x: float,
        y: float,
        radius: float = float(Range.Earshot.value),
        allowed_alive_enemies: int = 0,
        interact_interval_ms: int = 750,
        stable_clear_ms: int = 0,
        keep_player_near_center: bool = False,
        center_tolerance: float = 750.0,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that waits until the alive-enemy count in an area is at or
        below an allowed threshold.

        The routine can optionally require the area to remain clear for a stable
        duration before succeeding, and can keep the local player near the area
        center while the routine is active.

        Meta:
        Expose: true
        Audience: advanced
        Display: Wait For Clear Enemies In Area
        Purpose: Wait until an area is clear enough, optionally requiring a stable clear duration and keeping the player near the center.
        UserDescription: Use this when you want to block until enemies in an area are cleared, including encounters with delayed respawns or multiple waves.
        Notes: Returns RUNNING while enemies remain or while the stable-clear timer is active. Returns SUCCESS once the configured clear conditions are met.
        """
        from typing import Any

        from ...GlobalCache import GLOBAL_CACHE
        from ...Py4GWcorelib import Utils
        from ...enums_src.Multiboxing_enums import SharedCommandType

        state = {
            "paused": False,
            "last_interact_ms": 0,
            "last_target_id": 0,
            "clear_since_ms": 0,
        }

        def _reset_state() -> None:
            state["paused"] = False
            state["last_interact_ms"] = 0
            state["last_target_id"] = 0
            state["clear_since_ms"] = 0

        def _get_enemies_in_area() -> list[int]:
            enemy_array = list(
                RoutinesAgents.GetFilteredEnemyArray(
                    float(x),
                    float(y),
                    float(radius),
                )
                or []
            )

            enemy_array = [
                int(agent_id)
                for agent_id in enemy_array
                if int(agent_id) > 0
                and Agent.IsValid(int(agent_id))
                and Agent.IsAlive(int(agent_id))
            ]

            player_xy = Player.GetXY()

            enemy_array.sort(
                key=lambda agent_id: Utils.Distance(
                    player_xy,
                    Agent.GetXY(agent_id),
                )
            )

            return enemy_array

        def _get_pause_reason(
            node: BehaviorTree.Node,
        ) -> str:
            account_email = str(
                Player.GetAccountEmail() or ""
            )

            try:
                index: int
                message: Any
                index, message = (
                    GLOBAL_CACHE.ShMem.PreviewNextMessage(
                        account_email
                    )
                )
            except Exception:
                index = -1
                message = None

            if (
                index != -1
                and message is not None
                and getattr(message, "Command", None)
                == SharedCommandType.PickUpLoot
                and bool(
                    getattr(
                        message,
                        "Running",
                        False,
                    )
                )
            ):
                return "loot_message_active"

            if Checks.Player.IsDead():
                return "player_dead"

            if bool(
                node.blackboard.get(
                    "PAUSE_MOVEMENT",
                    False,
                )
            ):
                return "external_pause"

            if Checks.Player.IsCasting():
                return "casting"

            return ""

        def _keep_player_near_center() -> None:
            if not keep_player_near_center:
                return

            try:
                player_xy = Player.GetXY()
            except Exception:
                return

            if not player_xy:
                return

            if (
                Utils.Distance(
                    player_xy,
                    (float(x), float(y)),
                )
                > float(center_tolerance)
            ):
                Player.Move(
                    float(x),
                    float(y),
                )

        def _wait_for_clear_enemies(
            node: BehaviorTree.Node,
        ) -> BehaviorTree.NodeState:
            now = int(
                Utils.GetBaseTimestamp()
            )

            _keep_player_near_center()

            enemies = _get_enemies_in_area()

            node.blackboard[
                "wait_clear_area_enemy_count"
            ] = len(enemies)
            node.blackboard[
                "wait_clear_area_center"
            ] = (
                float(x),
                float(y),
            )
            node.blackboard[
                "wait_clear_area_radius"
            ] = float(radius)
            node.blackboard[
                "wait_clear_area_allowed_alive_enemies"
            ] = int(
                allowed_alive_enemies
            )
            node.blackboard[
                "wait_clear_area_stable_clear_ms"
            ] = int(
                stable_clear_ms
            )
            node.blackboard[
                "wait_clear_area_clear_since_ms"
            ] = int(
                state["clear_since_ms"]
            )

            pause_reason = _get_pause_reason(
                node
            )

            if pause_reason:
                if log and not state["paused"]:
                    _log(
                        "WaitForClearEnemiesInArea",
                        (
                            f"Pausing clear-area routine near "
                            f"({x}, {y}) due to "
                            f"{pause_reason}."
                        ),
                        log=log,
                    )

                state["paused"] = True
                return BehaviorTree.NodeState.RUNNING

            state["paused"] = False

            if (
                len(enemies)
                <= int(allowed_alive_enemies)
            ):
                state["last_target_id"] = 0
                state["last_interact_ms"] = 0

                if int(stable_clear_ms) <= 0:
                    _log(
                        "WaitForClearEnemiesInArea",
                        (
                            f"Area at ({x}, {y}) is clear "
                            f"enough: alive_enemies="
                            f"{len(enemies)}, allowed="
                            f"{allowed_alive_enemies}."
                        ),
                        log=log,
                        message_type=(
                            Console.MessageType.Success
                        ),
                    )

                    _reset_state()
                    return BehaviorTree.NodeState.SUCCESS

                if state["clear_since_ms"] <= 0:
                    state["clear_since_ms"] = now

                    node.blackboard[
                        "wait_clear_area_clear_since_ms"
                    ] = now

                    _log(
                        "WaitForClearEnemiesInArea",
                        (
                            f"Area near ({x}, {y}) is "
                            f"currently clear. Starting "
                            f"{stable_clear_ms}ms stable "
                            f"clear timer."
                        ),
                        log=log,
                    )

                    return BehaviorTree.NodeState.RUNNING

                clear_elapsed_ms = (
                    now
                    - int(
                        state[
                            "clear_since_ms"
                        ]
                    )
                )

                node.blackboard[
                    "wait_clear_area_clear_elapsed_ms"
                ] = clear_elapsed_ms

                if (
                    clear_elapsed_ms
                    >= int(stable_clear_ms)
                ):
                    _log(
                        "WaitForClearEnemiesInArea",
                        (
                            f"Area near ({x}, {y}) "
                            f"remained clear for "
                            f"{clear_elapsed_ms}ms."
                        ),
                        log=log,
                        message_type=(
                            Console.MessageType.Success
                        ),
                    )

                    _reset_state()
                    return BehaviorTree.NodeState.SUCCESS

                return BehaviorTree.NodeState.RUNNING

            # An enemy reappeared, so any stable-clear timer is cancelled.
            if state["clear_since_ms"] > 0:
                _log(
                    "WaitForClearEnemiesInArea",
                    (
                        f"Enemy activity resumed near "
                        f"({x}, {y}); resetting the "
                        f"stable-clear timer."
                    ),
                    log=log,
                )

            state["clear_since_ms"] = 0

            target_id = int(
                enemies[0]
            )

            node.blackboard[
                "wait_clear_area_target_id"
            ] = target_id

            if (
                state["last_target_id"]
                != target_id
                or now
                - int(
                    state[
                        "last_interact_ms"
                    ]
                )
                >= int(
                    interact_interval_ms
                )
            ):
                Player.ChangeTarget(
                    target_id
                )
                Player.Interact(
                    target_id,
                    False,
                )

                state["last_target_id"] = (
                    target_id
                )
                state["last_interact_ms"] = now

                _log(
                    "WaitForClearEnemiesInArea",
                    (
                        f"Interacting with enemy "
                        f"{target_id} near ({x}, {y}); "
                        f"alive_enemies={len(enemies)}."
                    ),
                    log=log,
                )

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name="WaitForClearEnemiesInArea",
                condition_fn=(
                    _wait_for_clear_enemies
                ),
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
                    _log("TargetNearestItem", f"Found nearest item with ID {nearest_item} within distance {distance}.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                _fail_log("TargetNearestItem", f"No item found within distance {distance}.")
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
                    _log("TargetNearestChest", f"Found nearest chest with ID {nearest_chest} within distance {distance}.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                _fail_log("TargetNearestChest", f"No chest found within distance {distance}.")
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestChestRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestChest", action_fn=_find_nearest_chest),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BTPlayer.ChangeTarget(node.blackboard.get("nearest_chest_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
        
        

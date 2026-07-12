"""
Public Behavior Tree routines related to quest-state conditions.
"""

from __future__ import annotations

from ...Py4GWcorelib import Console, ConsoleLog
from ...Quest import Quest
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree


def _log(
    source: str,
    message: str,
    *,
    log: bool = False,
    message_type=Console.MessageType.Info,
) -> None:
    ConsoleLog(
        source,
        message,
        message_type,
        log=log,
    )


class BTQuest:
    """
    Public BT helper group for quest-state conditions.

    Meta:
      Expose: true
      Audience: advanced
      Display: Quest
      Purpose: Group public BT routines related to quest state and quest-log conditions.
      UserDescription: Built-in BT helper group for checking quest state.
      Notes: Public PascalCase methods marked exposed are discovery candidates.
    """

    @staticmethod
    def IsQuestState(
        quest_id: int,
        state: str,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a condition tree that checks the current state of a quest.

        Supported states are `missing`, `active`, and `complete`.

        Meta:
          Expose: true
          Audience: beginner
          Display: Is Quest State
          Purpose: Check whether a quest is missing, active, or complete.
          UserDescription: Use this when a selector or sequence should run only for a specific quest state.
          Notes: Returns SUCCESS when the requested state matches and FAILURE immediately otherwise.
        """
        normalized_state = str(
            state or ""
        ).strip().lower()

        valid_states = {
            "missing",
            "active",
            "complete",
        }

        if normalized_state not in valid_states:
            raise ValueError(
                "state must be one of: "
                "'missing', 'active', 'complete'."
            )

        resolved_quest_id = int(quest_id)

        def _resolve_quest_state() -> str:
            quest_ids = {
                int(current_quest_id)
                for current_quest_id in (
                    Quest.GetQuestLogIds()
                    or []
                )
            }

            if resolved_quest_id not in quest_ids:
                return "missing"

            try:
                if Quest.IsQuestCompleted(
                    resolved_quest_id
                ):
                    return "complete"
            except Exception:
                pass

            return "active"

        def _is_quest_state(
            node: BehaviorTree.Node,
        ) -> BehaviorTree.NodeState:
            current_state = (
                _resolve_quest_state()
            )

            node.blackboard[
                "quest_state_quest_id"
            ] = resolved_quest_id
            node.blackboard[
                "quest_state_current"
            ] = current_state
            node.blackboard[
                "quest_state_expected"
            ] = normalized_state

            if current_state == normalized_state:
                _log(
                    "IsQuestState",
                    (
                        f"Quest {resolved_quest_id} "
                        f"is in expected state "
                        f"'{normalized_state}'."
                    ),
                    log=log,
                )
                return (
                    BehaviorTree.NodeState.SUCCESS
                )

            _log(
                "IsQuestState",
                (
                    f"Quest {resolved_quest_id} "
                    f"is '{current_state}', expected "
                    f"'{normalized_state}'."
                ),
                log=log,
            )
            return BehaviorTree.NodeState.FAILURE

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name=(
                    f"IsQuestState("
                    f"{resolved_quest_id}, "
                    f"{normalized_state})"
                ),
                condition_fn=_is_quest_state,
            )
        )
    

    
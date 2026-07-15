import time
from typing import Callable

from .. import Py4GW
from ..GlobalCache import GLOBAL_CACHE
from ..Routines import Routines
from ..py4gwcorelib_src.BehaviorTree import BehaviorTree


class BottingTreeServicesMixin:
    @staticmethod
    def PartyWipeRecoveryServiceTree(
        default_step_name: str | Callable[[], str | None] | None = None,
        return_interval_ms: float = 1000.0,
    ) -> BehaviorTree:
        """
        Recover the planner after a party wipe.

        Two distinct recovery scenarios are supported:

        1. Recoverable wipe:
           - the party dies in an explorable area;
           - the player is revived at a shrine;
           - the current named planner step is restarted in the same instance.

        2. Party defeated:
           - the party can no longer revive normally;
           - the game returns, or is instructed to return, to the outpost;
           - the current named planner step is restarted from the outpost.
        """
        state = {
            "active": False,
            "mode": "",
            "step_name": "",
            "last_return_ms": 0.0,
            "player_was_dead": False,
            "player_dead_pos": None,
        }

        def _log(
            message: str,
            message_type=Py4GW.Console.MessageType.Info,
        ) -> None:
            Py4GW.Console.Log(
                "PartyWipeRecoveryService",
                message,
                message_type,
            )

        def _resolve_default_step_name() -> str:
            if callable(default_step_name):
                try:
                    resolved = default_step_name()
                except Exception:
                    resolved = None
            else:
                resolved = default_step_name

            return str(resolved or "")

        def _resolve_recovery_step(
            node: BehaviorTree.Node,
        ) -> str:
            step_name = str(
                node.blackboard.get(
                    "current_step_name",
                    "",
                )
                or ""
            )

            if not step_name:
                step_name = _resolve_default_step_name()

            return step_name

        def _reset_state(
            node: BehaviorTree.Node,
        ) -> None:
            state["active"] = False
            state["mode"] = ""
            state["step_name"] = ""
            state["last_return_ms"] = 0.0
            state["player_was_dead"] = False
            state["player_dead_pos"] = None

            node.blackboard[
                "party_wipe_recovery_active"
            ] = False

            node.blackboard[
                "party_wipe_recovery_mode"
            ] = ""

            node.blackboard[
                "party_wipe_recovery_step_name"
            ] = ""

        def _request_step_restart(
            node: BehaviorTree.Node,
        ) -> bool:
            step_name = str(
                state["step_name"]
                or _resolve_default_step_name()
            )

            if not step_name:
                _log(
                    (
                        "Recovery completed, but no named planner "
                        "step could be resolved."
                    ),
                    Py4GW.Console.MessageType.Warning,
                )
                return False

            node.blackboard[
                "restart_step_name_request"
            ] = step_name

            return True

        def _detect_revive_teleport() -> bool:
            """
            Detect a transition from the death location to a distant shrine.

            It handles both:
            - the dead agent being teleported before becoming alive;
            - the player becoming alive at a position far from the death point.
            """
            from ..Agent import Agent
            from ..Player import Player
            from ..enums_src.GameData_enums import Range
            from ..py4gwcorelib_src.Utils import Utils

            player_id = Player.GetAgentID()

            if not Agent.IsValid(player_id):
                return False

            current_pos = Agent.GetXY(
                player_id
            )
            is_dead = bool(
                Agent.IsDead(player_id)
            )

            if is_dead:
                if not state["player_was_dead"]:
                    state["player_was_dead"] = True
                    state["player_dead_pos"] = current_pos
                    return False

                death_pos = state[
                    "player_dead_pos"
                ]

                if (
                    death_pos
                    and Utils.Distance(
                        death_pos,
                        current_pos,
                    )
                    > Range.Spellcast.value
                ):
                    # Some revive flows teleport the dead agent first.
                    state["player_was_dead"] = False
                    state["player_dead_pos"] = None
                    return True

                return False

            if not state["player_was_dead"]:
                return False

            state["player_was_dead"] = False

            death_pos = state[
                "player_dead_pos"
            ]
            state["player_dead_pos"] = None

            if not death_pos:
                return False

            return (
                Utils.Distance(
                    death_pos,
                    current_pos,
                )
                > Range.Spellcast.value
            )

        def _player_is_alive() -> bool:
            from ..Agent import Agent
            from ..Player import Player

            player_id = Player.GetAgentID()

            return bool(
                Agent.IsValid(player_id)
                and not Agent.IsDead(player_id)
            )

        def _can_resume_in_explorable() -> bool:
            from ..Map import Map

            return bool(
                Map.IsMapReady()
                and Map.IsExplorable()
                and GLOBAL_CACHE.Party.IsPartyLoaded()
                and _player_is_alive()
            )

        def _can_resume_from_outpost() -> bool:
            from ..Map import Map

            return bool(
                Map.IsMapReady()
                and Map.IsOutpost()
                and GLOBAL_CACHE.Party.IsPartyLoaded()
            )

        def _begin_recovery(
            node: BehaviorTree.Node,
            mode: str,
        ) -> None:
            from ..py4gwcorelib_src.ActionQueue import (
                ActionQueueManager,
            )

            step_name = _resolve_recovery_step(
                node
            )

            state["active"] = True
            state["mode"] = mode
            state["step_name"] = step_name
            state["last_return_ms"] = 0.0

            node.blackboard[
                "party_wipe_recovery_active"
            ] = True

            node.blackboard[
                "party_wipe_recovery_mode"
            ] = mode

            node.blackboard[
                "party_wipe_recovery_step_name"
            ] = step_name

            ActionQueueManager().ResetAllQueues()

            if mode == "defeated":
                _log(
                    (
                        "Party defeated. Waiting for the outpost "
                        f"before restarting step '{step_name}'."
                    ),
                    Py4GW.Console.MessageType.Warning,
                )
            else:
                _log(
                    (
                        "Recoverable party wipe detected. "
                        "Waiting for shrine revival before "
                        f"restarting step '{step_name}'."
                    ),
                    Py4GW.Console.MessageType.Warning,
                )

        def _tick_party_wipe_service(
            node: BehaviorTree.Node,
        ) -> BehaviorTree.NodeState:
            from ..Map import Map

            now = time.monotonic() * 1000.0

            if bool(
                node.blackboard.get(
                    "party_wipe_recovery_suppressed",
                    False,
                )
            ):
                _reset_state(node)
                return BehaviorTree.NodeState.RUNNING

            revived_at_shrine = (
                _detect_revive_teleport()
            )

            party_wiped = bool(
                Routines.Checks.Party.IsPartyWiped()
            )

            party_defeated = bool(
                GLOBAL_CACHE.Party.IsPartyDefeated()
            )

            # ---------------------------------------------
            # Start recovery
            # ---------------------------------------------

            if not state["active"]:
                if not (
                    party_wiped
                    or party_defeated
                    or revived_at_shrine
                ):
                    node.blackboard[
                        "party_wipe_recovery_active"
                    ] = False
                    return BehaviorTree.NodeState.RUNNING

                recovery_mode = (
                    "defeated"
                    if party_defeated
                    else "shrine"
                )

                _begin_recovery(
                    node,
                    recovery_mode,
                )

                # The service may first notice the wipe on the same
                # tick as the shrine teleport.
                if (
                    recovery_mode == "shrine"
                    and revived_at_shrine
                    and _can_resume_in_explorable()
                ):
                    restarted = _request_step_restart(
                        node
                    )

                    if restarted:
                        _log(
                            (
                                "Shrine revival detected. "
                                f"Restarting step "
                                f"'{state['step_name']}' "
                                "in the current instance."
                            ),
                            Py4GW.Console.MessageType.Success,
                        )

                    _reset_state(node)

                    return (
                        BehaviorTree.NodeState.SUCCESS
                        if restarted
                        else BehaviorTree.NodeState.FAILURE
                    )

                return BehaviorTree.NodeState.RUNNING

            # ---------------------------------------------
            # Recovery already active
            # ---------------------------------------------

            # A recoverable wipe may later become a true defeat.
            if party_defeated:
                if state["mode"] != "defeated":
                    state["mode"] = "defeated"

                    _log(
                        (
                            "The recoverable wipe became a party "
                            "defeat. Switching to outpost recovery."
                        ),
                        Py4GW.Console.MessageType.Warning,
                    )

            node.blackboard[
                "party_wipe_recovery_active"
            ] = True

            node.blackboard[
                "party_wipe_recovery_mode"
            ] = state["mode"]

            node.blackboard[
                "party_wipe_recovery_step_name"
            ] = state["step_name"]

            # ---------------------------------------------
            # Shrine recovery: stay in the same instance
            # ---------------------------------------------

            if state["mode"] == "shrine":
                # If the game returned to an outpost anyway, fall back
                # to the outpost recovery behavior.
                if _can_resume_from_outpost():
                    state["mode"] = "defeated"

                    node.blackboard[
                        "party_wipe_recovery_mode"
                    ] = "defeated"

                    _log(
                        (
                            "The party returned to an outpost "
                            "during shrine recovery. Switching "
                            "to outpost recovery."
                        ),
                        Py4GW.Console.MessageType.Warning,
                    )

                else:
                    shrine_recovery_complete = bool(
                        revived_at_shrine
                        or (
                            not party_wiped
                            and _can_resume_in_explorable()
                        )
                    )

                    if shrine_recovery_complete:
                        restarted = _request_step_restart(
                            node
                        )

                        if restarted:
                            _log(
                                (
                                    "Shrine revival detected. "
                                    f"Restarting step "
                                    f"'{state['step_name']}' "
                                    "in the current instance."
                                ),
                                Py4GW.Console.MessageType.Success,
                            )

                        _reset_state(node)

                        return (
                            BehaviorTree.NodeState.SUCCESS
                            if restarted
                            else BehaviorTree.NodeState.FAILURE
                        )

                    # Never call ReturnToOutpost for a recoverable wipe.
                    return BehaviorTree.NodeState.RUNNING

            # ---------------------------------------------
            # Defeated recovery: resume from the outpost
            # ---------------------------------------------

            if _can_resume_from_outpost():
                restarted = _request_step_restart(
                    node
                )

                if restarted:
                    _log(
                        (
                            "Outpost loaded after party defeat. "
                            f"Restarting step "
                            f"'{state['step_name']}'."
                        ),
                        Py4GW.Console.MessageType.Success,
                    )

                _reset_state(node)

                return (
                    BehaviorTree.NodeState.SUCCESS
                    if restarted
                    else BehaviorTree.NodeState.FAILURE
                )

            if (
                now
                - float(
                    state["last_return_ms"]
                )
                >= max(
                    100.0,
                    float(return_interval_ms),
                )
            ):
                GLOBAL_CACHE.Party.ReturnToOutpost()
                state["last_return_ms"] = now

                _log(
                    "Requesting return to outpost after party defeat."
                )

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="PartyWipeRecoveryService",
                action_fn=_tick_party_wipe_service,
                aftercast_ms=0,
            )
        )

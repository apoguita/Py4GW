"""
BT routines file notes
======================

This file is both:
- part of the public BT grouped routine surface
- a discovery source for higher-level tooling
"""

from __future__ import annotations

from ...Map import Map
from ...Party import Party
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree


class BTParty:
    """
    Public BT helper group for party-management routines.

    Meta:
      Expose: true
      Audience: advanced
      Display: Party
      Purpose: Group public BT routines related to party composition and party control.
      UserDescription: Built-in BT helper group for party-management actions.
      Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
    """

    @staticmethod
    def IsPartyLeader(log: bool = False) -> BehaviorTree:
        """
        Build a condition tree that succeeds when the local player is party leader.

        Meta:
          Expose: true
          Audience: beginner
          Display: Is Party Leader
          Purpose: Check whether the local player currently leads the party.
          UserDescription: Use this when a step should only run for the party leader.
          Notes: Returns failure when not party leader.
        """

        def _is_party_leader() -> bool:
            result = bool(Party.IsPartyLeader())
            if log:
                ConsoleLog("BTParty.IsPartyLeader", f"is_party_leader={result}", Console.MessageType.Info, log=log)
            return result

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name="IsPartyLeader",
                condition_fn=_is_party_leader,
            )
        )

    @staticmethod
    def LeaveParty(log: bool = False, aftercast_ms: int = 250) -> BehaviorTree:
        """
        Build an action tree that leaves the current party.

        Meta:
          Expose: true
          Audience: beginner
          Display: Leave Party
          Purpose: Leave the current party.
          UserDescription: Use this when you want to leave party immediately.
          Notes: Executes instantly and returns success once dispatched.
        """

        def _leave_party() -> BehaviorTree.NodeState:
            Party.LeaveParty()
            if log:
                ConsoleLog("BTParty.LeaveParty", "LeaveParty dispatched.", Console.MessageType.Info, log=log)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="LeaveParty",
                action_fn=_leave_party,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def FlagAllHeroes(x: float, y: float, log: bool = False, aftercast_ms: int = 125) -> BehaviorTree:
        """
        Build an action tree that flags all heroes at a world coordinate.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Flag All Heroes
          Purpose: Flag all local heroes at a given position.
          UserDescription: Use this when you need to place all heroes at one flag position.
          Notes: Operates on local party heroes only.
        """

        def _flag_all_heroes() -> BehaviorTree.NodeState:
            Party.Heroes.FlagAllHeroes(float(x), float(y))
            if log:
                ConsoleLog("BTParty.FlagAllHeroes", f"FlagAllHeroes x={x:.2f}, y={y:.2f}", Console.MessageType.Info, log=log)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="FlagAllHeroes",
                action_fn=_flag_all_heroes,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def UnflagAllHeroes(log: bool = False, aftercast_ms: int = 125) -> BehaviorTree:
        """
        Build an action tree that clears all local hero flags.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Unflag All Heroes
          Purpose: Remove all local hero flags.
          UserDescription: Use this to clear hero flags and resume default behavior.
          Notes: Operates on local party heroes only.
        """

        def _unflag_all_heroes() -> BehaviorTree.NodeState:
            Party.Heroes.UnflagAllHeroes()
            if log:
                ConsoleLog("BTParty.UnflagAllHeroes", "UnflagAllHeroes dispatched.", Console.MessageType.Info, log=log)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="UnflagAllHeroes",
                action_fn=_unflag_all_heroes,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def LoadParty(
        hero_ids: list[int] | None = None,
        henchman_ids: list[int] | None = None,
        clear_existing: bool = False,
        require_outpost: bool = True,
        log: bool = False,
        aftercast_ms: int = 250,
    ) -> BehaviorTree:
        """
        Build an action tree that loads party heroes/henchmen.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Load Party
          Purpose: Populate the local party with heroes and optional henchmen.
          UserDescription: Use this to set up party composition before leaving outpost.
          Notes: This routine is leader-only and can be restricted to outposts.
        """

        hero_ids = [int(h) for h in (hero_ids or []) if int(h) > 0]
        henchman_ids = [int(h) for h in (henchman_ids or []) if int(h) > 0]

        def _load_party() -> BehaviorTree.NodeState:
            if not Party.IsPartyLeader():
                if log:
                    ConsoleLog("BTParty.LoadParty", "Skipped: local player is not party leader.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            if require_outpost and not Map.IsOutpost():
                if log:
                    ConsoleLog("BTParty.LoadParty", "Skipped: can only add party members in outpost.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            if clear_existing:
                Party.Heroes.KickAllHeroes()

            existing_heroes = set()
            for hero in Party.GetHeroes() or []:
                hid = int(getattr(hero, "hero_id", 0) or 0)
                if hid > 0:
                    existing_heroes.add(hid)

            for hero_id in hero_ids:
                if hero_id in existing_heroes:
                    continue
                Party.Heroes.AddHero(hero_id)
                existing_heroes.add(hero_id)

            for henchman_id in henchman_ids:
                Party.Henchmen.AddHenchman(henchman_id)

            if log:
                ConsoleLog(
                    "BTParty.LoadParty",
                    f"LoadParty dispatched heroes={hero_ids}, henchmen={henchman_ids}, clear_existing={clear_existing}",
                    Console.MessageType.Info,
                    log=log,
                )
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="LoadParty",
                action_fn=_load_party,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def WaitForPartyLoaded(
        expected_heroes: int = 0,
        expected_henchmen: int = 0,
        timeout_ms: int = 10000,
        poll_interval_ms: int = 200,
        require_party_loaded_flag: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a wait tree that blocks until the party reaches expected counts.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait For Party Loaded
          Purpose: Wait until party-load state and expected hero/henchman counts are reached.
          UserDescription: Use this to wait after party composition changes.
          Notes: Returns failure on timeout.
        """

        expected_heroes = max(0, int(expected_heroes))
        expected_henchmen = max(0, int(expected_henchmen))
        timeout_ms = max(0, int(timeout_ms))
        poll_interval_ms = max(10, int(poll_interval_ms))

        def _is_loaded() -> bool:
            heroes = int(Party.GetHeroCount() or 0)
            henchmen = int(Party.GetHenchmanCount() or 0)
            loaded_flag = bool(Party.IsPartyLoaded()) if require_party_loaded_flag else True
            result = loaded_flag and heroes >= expected_heroes and henchmen >= expected_henchmen
            if log and result:
                ConsoleLog(
                    "BTParty.WaitForPartyLoaded",
                    f"Party ready heroes={heroes}/{expected_heroes}, henchmen={henchmen}/{expected_henchmen}",
                    Console.MessageType.Info,
                    log=log,
                )
            return result

        return BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name="WaitForPartyLoaded",
                condition_fn=_is_loaded,
                throttle_interval_ms=poll_interval_ms,
                timeout_ms=timeout_ms,
            )
        )

    @staticmethod
    def Resign(log: bool = False, aftercast_ms: int = 250) -> BehaviorTree:
        """
        Build an action tree that sends resign command.

        Meta:
          Expose: true
          Audience: beginner
          Display: Resign
          Purpose: Trigger resign command for the local player.
          UserDescription: Use this when you want to resign the current run.
          Notes: This routine dispatches the command and returns success.
        """

        def _resign() -> BehaviorTree.NodeState:
            Player.SendChatCommand("resign")
            if log:
                ConsoleLog("BTParty.Resign", "Resign dispatched.", Console.MessageType.Info, log=log)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="Resign",
                action_fn=_resign,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

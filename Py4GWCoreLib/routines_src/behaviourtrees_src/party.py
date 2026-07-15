"""
BT routines file notes
======================

This file is both:
- part of the public BT grouped routine surface
- a discovery source for higher-level tooling
"""

from __future__ import annotations

from collections.abc import Sequence

from ...Agent import Agent
from ...GlobalCache import GLOBAL_CACHE
from ...Map import Map
from ...Party import Party
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...Skillbar import SkillBar
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from .composite import BTComposite
import time

from ...Quest import Quest
from ...enums import SharedCommandType


def _log(source: str, message: str, *, log: bool = False, message_type=Console.MessageType.Info) -> None:
    ConsoleLog(source, message, message_type, log=log)


def _fail_log(source: str, message: str, message_type=Console.MessageType.Warning) -> None:
    ConsoleLog(source, message, message_type, log=True)


def _apply_multibox_all_flag(x: float, y: float) -> None:
    leader_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(0)
    if leader_options is None:
        return
    leader_id = int(GLOBAL_CACHE.Party.GetPartyLeaderID() or 0)
    leader_options.AllFlag.x = float(x)
    leader_options.AllFlag.y = float(y)
    leader_options.IsFlagged = True
    leader_options.FlagFacingAngle = float(Agent.GetRotationAngle(leader_id) if leader_id > 0 else 0.0)


def _clear_multibox_all_flags() -> None:
    party_id = int(GLOBAL_CACHE.Party.GetPartyID() or 0)
    for account, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
        if (
            not account
            or options is None
            or not account.IsSlotActive
            or int(account.AgentPartyData.PartyID or 0) != party_id
        ):
            continue
        options.IsFlagged = False
        options.FlagPos.x = 0.0
        options.FlagPos.y = 0.0
        options.AllFlag.x = 0.0
        options.AllFlag.y = 0.0
        options.FlagFacingAngle = 0.0


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
            _log("BTParty.IsPartyLeader", f"is_party_leader={result}", log=log)
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
            _log("BTParty.LeaveParty", "LeaveParty dispatched.", log=log)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="LeaveParty",
                action_fn=_leave_party,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def FlagHero(hero_position: int, x: float, y: float, log: bool = False, aftercast_ms: int = 125) -> BehaviorTree:
        """
        Build an action tree that flags one hero at a world coordinate.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Flag Hero
          Purpose: Flag a single local hero at a given position.
          UserDescription: Use this when you need to place one hero at a specific flag position.
          Notes: The hero selector uses party position and resolves to the current hero agent id at runtime.
        """

        def _flag_hero() -> BehaviorTree.NodeState:
            resolved_position = int(hero_position)
            if resolved_position <= 0:
                _fail_log(
                    "BTParty.FlagHero",
                    f"Failed to flag hero: invalid party position {resolved_position}.",
                )
                return BehaviorTree.NodeState.FAILURE

            hero_agent_id = int(Party.Heroes.GetHeroAgentIDByPartyPosition(resolved_position) or 0)
            if hero_agent_id <= 0:
                _fail_log(
                    "BTParty.FlagHero",
                    f"Failed to flag hero: no hero found at party position {resolved_position}.",
                )
                return BehaviorTree.NodeState.FAILURE

            Party.Heroes.FlagHero(hero_agent_id, float(x), float(y))
            _log(
                "BTParty.FlagHero",
                f"FlagHero party_position={resolved_position}, agent_id={hero_agent_id}, x={x:.2f}, y={y:.2f}",
                log=log,
            )
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="FlagHero",
                action_fn=_flag_hero,
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
            _apply_multibox_all_flag(float(x), float(y))
            _log("BTParty.FlagAllHeroes", f"FlagAllHeroes x={x:.2f}, y={y:.2f}", log=log)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="FlagAllHeroes",
                action_fn=_flag_all_heroes,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def FlagHeroesFromList(
        hero_positions: Sequence[int | str] | None,
        x: float,
        y: float,
        flag_all: bool = False,
        log: bool = False,
        aftercast_ms: int = 125,
    ) -> BehaviorTree:
        """
        Build a composite tree that flags selected heroes at a world coordinate.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Flag Heroes From List
          Purpose: Flag several local heroes in sequence using party positions, or all heroes with an explicit flag.
          UserDescription: Use this when a step should flag one hero, many heroes, or all heroes through one shared entrypoint.
          Notes: When `flag_all` is true, the composite collapses to the all-heroes flag routine and ignores `hero_positions`.
        """
        normalized_positions: list[int] = []
        if flag_all:
            return BTParty.FlagAllHeroes(x=float(x), y=float(y), log=log, aftercast_ms=aftercast_ms)

        for raw_value in hero_positions or []:
            if isinstance(raw_value, str):
                stripped_value = raw_value.strip()
                if not stripped_value:
                    continue
                try:
                    resolved_position = int(stripped_value)
                except ValueError as exc:
                    raise ValueError(f"Invalid hero position value {raw_value!r}; expected positive integer.") from exc
            else:
                resolved_position = int(raw_value)

            if resolved_position <= 0:
                raise ValueError(f"Invalid hero position value {raw_value!r}; expected positive integer.")
            normalized_positions.append(resolved_position)

        if not normalized_positions:
            raise ValueError("FlagHeroesFromList requires at least one hero position unless flag_all is true.")

        return BTComposite.Sequence(
            *[
                BTParty.FlagHero(
                    hero_position=hero_position,
                    x=float(x),
                    y=float(y),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
                for hero_position in normalized_positions
            ],
            name="FlagHeroesFromList",
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
            _clear_multibox_all_flags()
            _log("BTParty.UnflagAllHeroes", "UnflagAllHeroes dispatched.", log=log)
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
                _fail_log("BTParty.LoadParty", "Failed to load party: local player is not party leader.")
                return BehaviorTree.NodeState.FAILURE

            if require_outpost and not Map.IsOutpost():
                _fail_log("BTParty.LoadParty", "Failed to load party: can only add party members in outpost.")
                return BehaviorTree.NodeState.FAILURE

            if clear_existing:
                Party.Heroes.KickAllHeroes()

            existing_heroes = set()
            for hero in Party.GetHeroes() or []:
                hero_id = getattr(hero, "hero_id", 0)

                if hasattr(hero_id, "GetID"):
                    hid = int(hero.hero_id.GetID() or 0)
                else:
                    hid = int(hero_id or 0)

                if hid > 0:
                    existing_heroes.add(hid)

            for hero_id in hero_ids:
                if hero_id in existing_heroes:
                    continue
                Party.Heroes.AddHero(hero_id)
                existing_heroes.add(hero_id)

            for henchman_id in henchman_ids:
                Party.Henchmen.AddHenchman(henchman_id)

            _log(
                "BTParty.LoadParty",
                f"LoadParty dispatched heroes={hero_ids}, henchmen={henchman_ids}, clear_existing={clear_existing}",
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

        state = {"started": False}

        def _is_loaded() -> bool:
            heroes = int(Party.GetHeroCount() or 0)
            henchmen = int(Party.GetHenchmanCount() or 0)
            loaded_flag = bool(Party.IsPartyLoaded()) if require_party_loaded_flag else True
            result = loaded_flag and heroes >= expected_heroes and henchmen >= expected_henchmen
            if result:
                _log(
                    "BTParty.WaitForPartyLoaded",
                    f"Party ready heroes={heroes}/{expected_heroes}, henchmen={henchmen}/{expected_henchmen}",
                    log=log,
                )
            elif not state["started"]:
                state["started"] = True
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
            _log("BTParty.Resign", "Resign dispatched.", log=log)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="Resign",
                action_fn=_resign,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def SetTitle(title_id: int, log: bool = False, aftercast_ms: int = 250) -> BehaviorTree:
        """
        Build an action tree that sets the local player's active title.

        Meta:
          Expose: true
          Audience: beginner
          Display: Set Title
          Purpose: Set the active player title by title id.
          UserDescription: Use this when a route or setup needs a specific title active.
          Notes: Dispatches the title change and returns success immediately.
        """

        def _set_title() -> BehaviorTree.NodeState:
            Player.SetActiveTitle(int(title_id))
            _log("BTParty.SetTitle", f"Set title id={int(title_id)}.", log=log)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="SetTitle",
                action_fn=_set_title,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def ForceHeroState(behavior: int, log: bool = False, aftercast_ms: int = 125) -> BehaviorTree:
        """
        Build an action tree that sets every current hero to a behavior mode.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Force Hero State
          Purpose: Set all local heroes to fight, guard, or avoid behavior.
          UserDescription: Use this when you want to force the whole hero party into one behavior mode.
          Notes: Behavior values are the native hero behavior ids 0, 1, and 2.
        """

        def _force_hero_state() -> BehaviorTree.NodeState:
            behavior_value = int(behavior)
            if behavior_value not in (0, 1, 2):
                _fail_log("BTParty.ForceHeroState", f"Failed to update hero behavior: invalid behavior value {behavior_value}.")
                return BehaviorTree.NodeState.FAILURE
            used = 0
            for hero in Party.GetHeroes():
                hero_agent_id = getattr(hero, "agent_id", 0)
                if hero_agent_id:
                    Party.Heroes.SetHeroBehavior(hero_agent_id, behavior_value)
                    used += 1
            _log("BTParty.ForceHeroState", f"Updated {used} hero behavior(s).", log=log)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="ForceHeroState",
                action_fn=_force_hero_state,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def SetHeroSkillAI(
        hero_positions: int | Sequence[int],
        skill_ids: int | Sequence[int],
        enabled: bool = False,
        log: bool = False,
        aftercast_ms: int = 125,
    ) -> BehaviorTree:
        """
        Build an action tree that enables or disables native hero AI use for skill ids.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Set Hero Skill AI
          Purpose: Enable or disable native hero AI auto-use for selected skill ids on selected heroes.
          UserDescription: Use this when heroes should keep a skill on their bar but native hero AI must not auto-cast it.
          Notes: Hero positions are 1-7. Resolve skill names before calling, e.g. Skill.GetID("Gaze_of_Fury").
        """

        def _as_positions(value: int | Sequence[int]) -> list[int]:
            if isinstance(value, int):
                return [int(value)]
            return [int(position) for position in value]

        def _as_skill_ids(value: int | Sequence[int]) -> list[int]:
            if isinstance(value, int):
                values = [value]
            else:
                values = list(value)

            return [int(skill_id) for skill_id in values if int(skill_id) > 0]

        def _set_hero_skill_ai() -> BehaviorTree.NodeState:
            positions = _as_positions(hero_positions)
            desired_skill_ids = _as_skill_ids(skill_ids)
            if not positions or not desired_skill_ids:
                return BehaviorTree.NodeState.FAILURE

            desired_enabled = bool(enabled)
            matched = 0
            for hero_position in positions:
                if hero_position < 1 or hero_position > 7:
                    _fail_log("BTParty.SetHeroSkillAI", f"Invalid hero position: {hero_position}.")
                    return BehaviorTree.NodeState.FAILURE

                hero_agent_id = int(Party.Heroes.GetHeroAgentIDByPartyPosition(hero_position) or 0)
                if hero_agent_id <= 0:
                    _fail_log("BTParty.SetHeroSkillAI", f"No hero agent id for position {hero_position}.")
                    return BehaviorTree.NodeState.FAILURE

                hero_skillbar = SkillBar.GetHeroSkillbar(hero_position)
                found_for_hero = False
                for slot, hero_skill in enumerate(hero_skillbar, start=1):
                    hero_skill_id = int(getattr(getattr(hero_skill, "id", None), "id", 0) or 0)
                    if hero_skill_id not in desired_skill_ids:
                        continue
                    if not Party.Heroes.SetSkillAIEnabled(hero_agent_id, slot, desired_enabled):
                        _fail_log(
                            "BTParty.SetHeroSkillAI",
                            f"Failed to update hero {hero_position} skill slot {slot}.",
                        )
                        return BehaviorTree.NodeState.FAILURE
                    found_for_hero = True
                    matched += 1

                if not found_for_hero:
                    ids = ", ".join(str(skill_id) for skill_id in desired_skill_ids)
                    _fail_log("BTParty.SetHeroSkillAI", f"Hero {hero_position} does not have skill id(s): {ids}.")
                    return BehaviorTree.NodeState.FAILURE

            state = "enabled" if desired_enabled else "disabled"
            _log("BTParty.SetHeroSkillAI", f"{state} {matched} hero skill AI flag(s).", log=log)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="SetHeroSkillAI",
                action_fn=_set_hero_skill_ai,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def DropBundle(log: bool = False) -> BehaviorTree:
        """
        Build an action tree that drops the currently held bundle.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Drop Bundle
          Purpose: Press the configured drop-item control action used to drop a held bundle.
          UserDescription: Use this when a route needs to release a bundle before continuing.
          Notes: Uses the native drop-item keybind action instead of raw function keys.
        """
        from ...UIManager import UIManager
        from ...enums_src.UI_enums import ControlAction

        def _keydown() -> BehaviorTree.NodeState:
            UIManager.Keydown(ControlAction.ControlAction_DropItem.value, 0)
            _log("BTParty.DropBundle", "Pressed drop-item control action.", log=log)
            return BehaviorTree.NodeState.SUCCESS

        def _keyup() -> BehaviorTree.NodeState:
            UIManager.Keyup(ControlAction.ControlAction_DropItem.value, 0)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="DropBundle",
                children=[
                    BehaviorTree.ActionNode(
                        name="DropBundleKeyDown",
                        action_fn=_keydown,
                        aftercast_ms=75,
                    ),
                    BehaviorTree.ActionNode(
                        name="DropBundleKeyUp",
                        action_fn=_keyup,
                        aftercast_ms=50,
                    ),
                ],
            )
        )

    
    @staticmethod
    def WaitForActiveQuest(quest_id: int, timeout_ms: int = 10000, throttle_interval_ms: int = 250, log: bool = False) -> BehaviorTree:
        """
        Build a tree that waits until the requested quest becomes the active quest.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait For Active Quest
          Purpose: Wait until a specific quest id is the active quest.
          UserDescription: Use this when a dialog or interaction should be confirmed by checking the active quest id.
          Notes: Succeeds only when the requested quest becomes active before timeout.
        """

        def _wait_for_active_quest() -> BehaviorTree.NodeState:
            from ...Quest import Quest

            if int(Quest.GetActiveQuest() or 0) == int(quest_id):
                _log("BTParty.WaitForActiveQuest", f"Quest {int(quest_id)} is now active.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name=f"WaitForActiveQuest({int(quest_id)})",
                condition_fn=_wait_for_active_quest,
                throttle_interval_ms=max(1, int(throttle_interval_ms)),
                timeout_ms=max(0, int(timeout_ms)),
            )
        )

    @staticmethod
    def WaitForActiveQuestCleared(quest_id: int, timeout_ms: int = 10000, throttle_interval_ms: int = 250, log: bool = False) -> BehaviorTree:
        """
        Build a tree that waits until the requested quest is no longer the active quest.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait For Active Quest Cleared
          Purpose: Wait until a specific quest id is no longer active.
          UserDescription: Use this when quest completion or abandonment should be confirmed by checking that the active quest changed away.
          Notes: Succeeds when the active quest differs from the requested quest before timeout.
        """

        def _wait_for_quest_cleared() -> BehaviorTree.NodeState:
            from ...Quest import Quest

            if int(Quest.GetActiveQuest() or 0) != int(quest_id):
                _log("BTParty.WaitForQuestCleared", f"Quest {int(quest_id)} is no longer active.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name=f"WaitForQuestCleared({int(quest_id)})",
                condition_fn=_wait_for_quest_cleared,
                throttle_interval_ms=max(1, int(throttle_interval_ms)),
                timeout_ms=max(0, int(timeout_ms)),
            )
        )

    @staticmethod
    def WaitForQuestState(
        quest_id: int,
        state: str,
        timeout_ms: int = 10000,
        throttle_interval_ms: int = 250,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that waits until the requested quest reaches the requested state.

        Valid states:
        - "active"
        - "complete"
        - "missing"

        Meta:
        Expose: true
        Audience: intermediate
        Display: Wait For Quest State
        Purpose: Wait until a quest reaches the requested state.
        UserDescription: Use this when a dialog or interaction should be confirmed by waiting for a quest state change.
        Notes: Returns SUCCESS only when the requested state is reached before timeout.
        """

        expected_state = str(state).strip().lower()

        valid_states = {
            "active",
            "complete",
            "missing",
        }

        if expected_state not in valid_states:
            raise ValueError(
                f"Unsupported quest state '{state}'. "
                f"Expected one of {sorted(valid_states)}."
            )

        def _wait_for_quest_state() -> BehaviorTree.NodeState:
            from ...Quest import Quest

            quest_ids = {
                int(qid)
                for qid in (Quest.GetQuestLogIds() or [])
            }

            quest_in_log = int(quest_id) in quest_ids

            try:
                quest_complete = bool(
                    Quest.IsQuestCompleted(
                        int(quest_id)
                    )
                )
            except Exception:
                quest_complete = False

            if expected_state == "missing":
                matched = not quest_in_log

            elif expected_state == "active":
                matched = (
                    quest_in_log
                    and not quest_complete
                )

            else:  # complete
                matched = (
                    quest_in_log
                    and quest_complete
                )

            if matched:
                _log(
                    "BTQuest.WaitForQuestState",
                    (
                        f"Quest {int(quest_id)} "
                        f"reached state '{expected_state}'."
                    ),
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name=(
                    f"WaitForQuestState"
                    f"({int(quest_id)},"
                    f"{expected_state})"
                ),
                condition_fn=_wait_for_quest_state,
                throttle_interval_ms=max(
                    1,
                    int(throttle_interval_ms),
                ),
                timeout_ms=max(
                    0,
                    int(timeout_ms),
                ),
            )
        )


    @staticmethod
    def IsQuestInLog(quest_id: int, log: bool = False) -> BehaviorTree:
        """
        Build a condition tree that succeeds when the requested quest id is present in the quest log.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Is Quest In Log
          Purpose: Check whether a specific quest id is currently present in the quest log.
          UserDescription: Use this when a route needs a direct condition check for whether a quest is currently in the quest log.
          Notes: Returns failure when the quest id is not found in the quest log ids.
        """

        def _is_quest_in_log() -> bool:
            from ...Quest import Quest


            quest_log_ids = [int(qid) for qid in (Quest.GetQuestLogIds() or [])]
            result = int(quest_id) in quest_log_ids
            _log("BTParty.IsQuestInLog", f"quest_id={int(quest_id)} in_log={result}", log=log)
            return result

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name=f"IsQuestInLog({int(quest_id)})",
                condition_fn=_is_quest_in_log,
            )
        )

    @staticmethod
    def IsQuestAbsentFromLog(quest_id: int, log: bool = False) -> BehaviorTree:
        """
        Build a condition tree that succeeds when the requested quest id is absent from the quest log.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Is Quest Absent From Log
          Purpose: Check whether a specific quest id is currently absent from the quest log.
          UserDescription: Use this when a route needs a direct condition check for whether a quest is currently not in the quest log.
          Notes: Returns failure when the quest id is still found in the quest log ids.
        """

        def _is_quest_absent_from_log() -> bool:
            from ...Quest import Quest

            quest_log_ids = [int(qid) for qid in (Quest.GetQuestLogIds() or [])]
            result = int(quest_id) not in quest_log_ids
            _log("BTParty.IsQuestAbsentFromLog", f"quest_id={int(quest_id)} absent_from_log={result}", log=log)
            return result

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name=f"IsQuestAbsentFromLog({int(quest_id)})",
                condition_fn=_is_quest_absent_from_log,
            )
        )


    @staticmethod
    def AbandonQuest(
        quest_id: int,
        multi_account: bool = False,
        include_self: bool = True,
        timeout_ms: int = 10_000,
        aftercast_ms: int = 250,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that abandons a quest locally or across active accounts.

        When multibox mode is enabled, the routine abandons the quest locally
        when requested, sends an AbandonQuest shared command to every other
        active account, then waits until all dispatched messages are processed.

        Meta:
        Expose: true
        Audience: intermediate
        Display: Abandon Quest
        Purpose: Abandon a quest locally or across a multibox party.
        UserDescription: Use this when every account must reset the same quest before continuing.
        Notes: Remote accounts must support SharedCommandType.AbandonQuest.
        """
        import time

        resolved_quest_id = int(quest_id)
        resolved_timeout_ms = max(
            0,
            int(timeout_ms),
        )

        phase = "start"
        started_at = 0.0
        refs: list[tuple[str, int]] = []

        def _reset() -> None:
            nonlocal phase
            nonlocal started_at
            nonlocal refs

            phase = "start"
            started_at = 0.0
            refs = []

        def _trace(
            message: str,
            message_type=Console.MessageType.Info,
        ) -> None:
            _log(
                "BTParty.AbandonQuest",
                message,
                log=log,
                message_type=message_type,
            )

        def _message_is_active(
            sender_email: str,
            receiver_email: str,
            message_index: int,
        ) -> bool:
            if int(message_index) < 0:
                return False

            try:
                message = GLOBAL_CACHE.ShMem.GetInbox(
                    int(message_index)
                )
            except Exception:
                return False

            return (
                bool(
                    getattr(
                        message,
                        "Active",
                        False,
                    )
                )
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
                    SharedCommandType.AbandonQuest
                )
            )

        def _abandon_quest(
            _node: BehaviorTree.Node,
        ) -> BehaviorTree.NodeState:
            nonlocal phase
            nonlocal started_at
            nonlocal refs

            now = time.monotonic()

            if resolved_quest_id <= 0:
                _fail_log(
                    "BTParty.AbandonQuest",
                    (
                        "Invalid quest id: "
                        f"{resolved_quest_id}."
                    ),
                )
                _reset()
                return BehaviorTree.NodeState.FAILURE

            if phase == "start":
                started_at = now
                refs = []

                if include_self:
                    Quest.AbandonQuest(
                        resolved_quest_id
                    )

                    _trace(
                        (
                            f"Abandoned quest "
                            f"{resolved_quest_id} locally."
                        )
                    )

                if not multi_account:
                    _reset()
                    return BehaviorTree.NodeState.SUCCESS

                sender_email = str(
                    Player.GetAccountEmail() or ""
                )

                if not sender_email:
                    _fail_log(
                        "BTParty.AbandonQuest",
                        "Unable to resolve the local account email.",
                    )
                    _reset()
                    return BehaviorTree.NodeState.FAILURE

                for account in (
                    GLOBAL_CACHE.ShMem.GetAllAccountData()
                    or []
                ):
                    receiver_email = str(
                        getattr(
                            account,
                            "AccountEmail",
                            "",
                        )
                        or ""
                    )

                    if (
                        not receiver_email
                        or receiver_email == sender_email
                    ):
                        continue

                    try:
                        message_index = int(
                            GLOBAL_CACHE.ShMem.SendMessage(
                                sender_email,
                                receiver_email,
                                SharedCommandType.AbandonQuest,
                                (
                                    resolved_quest_id,
                                    0,
                                    0,
                                    0,
                                ),
                            )
                        )
                    except Exception as error:
                        _fail_log(
                            "BTParty.AbandonQuest",
                            (
                                "Failed to send AbandonQuest "
                                f"to '{receiver_email}': {error}"
                            ),
                        )
                        continue

                    refs.append(
                        (
                            receiver_email,
                            message_index,
                        )
                    )

                    _trace(
                        (
                            f"Sent quest {resolved_quest_id} "
                            f"abandon command to "
                            f"'{receiver_email}' "
                            f"(message={message_index})."
                        )
                    )

                if not refs:
                    _trace(
                        "No remote accounts required processing."
                    )
                    _reset()
                    return BehaviorTree.NodeState.SUCCESS

                phase = "wait"
                return BehaviorTree.NodeState.RUNNING

            if phase == "wait":
                sender_email = str(
                    Player.GetAccountEmail() or ""
                )

                pending_accounts: list[str] = []

                for receiver_email, message_index in refs:
                    if _message_is_active(
                        sender_email,
                        receiver_email,
                        message_index,
                    ):
                        pending_accounts.append(
                            receiver_email
                        )

                if not pending_accounts:
                    remote_count = len(refs)

                    _trace(
                        (
                            f"Quest {resolved_quest_id} "
                            f"abandoned on the local account "
                            f"and {remote_count} remote account(s)."
                        ),
                        Console.MessageType.Success,
                    )

                    _reset()
                    return BehaviorTree.NodeState.SUCCESS

                elapsed_ms = (
                    now - started_at
                ) * 1000.0

                if (
                    resolved_timeout_ms > 0
                    and elapsed_ms >= resolved_timeout_ms
                ):
                    _fail_log(
                        "BTParty.AbandonQuest",
                        (
                            "Timed out while waiting for "
                            "remote quest abandonment: "
                            + ", ".join(
                                pending_accounts
                            )
                        ),
                    )

                    _reset()
                    return BehaviorTree.NodeState.FAILURE

                return BehaviorTree.NodeState.RUNNING

            _reset()
            return BehaviorTree.NodeState.FAILURE

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="AbandonQuest",
                action_fn=_abandon_quest,
                aftercast_ms=max(
                    0,
                    int(aftercast_ms),
                ),
            )
        )
    

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
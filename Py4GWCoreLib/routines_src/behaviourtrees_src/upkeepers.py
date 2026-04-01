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
      Display: Outpost Imp Service
      Purpose: Build a tree that runs an upkeep or service routine.
      UserDescription: Use this when you want a background upkeep tree beside the main planner.
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
from ...GlobalCache import GLOBAL_CACHE
from ...Map import Map
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...enums_src.Model_enums import ModelID
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..Checks import Checks
from .composite import BTComposite
from .items import BTItems


class BTUpkeepers:
    """
    Public BT helper group for upkeep and background service routines.

    Meta:
      Expose: true
      Audience: advanced
      Display: Upkeepers
      Purpose: Group public BT routines related to upkeep services and background support flows.
      UserDescription: Built-in BT helper group for upkeep and service-style routines.
      Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
    """
    @staticmethod
    def SpawnImp(
        target_bag: int = 1,
        slot: int = 0,
        exclude_list: list[int] | None = None,
        log: bool = False,
        spawn_settle_ms: int = 250,
    ) -> BehaviorTree:
        """
        Build a tree that spawns bonus items, prunes extras, and stores the imp stone in a target bag slot.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Spawn Imp
          Purpose: Prepare an imp summoning stone from the bonus item flow.
          UserDescription: Use this when you want to create and organize the imp stone item before using it.
          Notes: Spawns bonus items, destroys other bonus models except exclusions, and moves the imp stone to the target bag slot.
        """
        imp_model_id = ModelID.Igneous_Summoning_Stone.value
        effective_exclude_list = list(exclude_list or [
            imp_model_id,
        ])

        if imp_model_id not in effective_exclude_list:
            effective_exclude_list.append(imp_model_id)

        return BTComposite.Sequence(
            BTItems.SpawnBonusItems(log=log, aftercast_ms=spawn_settle_ms),
            BTItems.DestroyBonusItems(exclude_list=effective_exclude_list, log=log, aftercast_ms=35),
            BTItems.MoveModelToBagSlot(
                model_id=imp_model_id,
                target_bag=target_bag,
                slot=slot,
                log=log,
                required=True,
                aftercast_ms=spawn_settle_ms,
            ),
            name="SpawnImp",
        )

    @staticmethod
    def OutpostImpService(
        target_bag: int = 1,
        slot: int = 0,
        exclude_list: list[int] | None = None,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a service tree that prepares the imp stone once per outpost map.

        Meta:
          Expose: true
          Audience: advanced
          Display: Outpost Imp Service
          Purpose: Run a background outpost service that prepares the imp stone when needed.
          UserDescription: Use this as a service tree when you want imp preparation to happen automatically in outposts.
          Notes: Runs once per ready outpost map and idles until the next relevant map change.
        """
        state = {
            "outpost_visit_signature": None,
            "map_processed": False,
            "spawn_tree": None,
            "last_stage_log": "",
        }

        imp_model_id = ModelID.Igneous_Summoning_Stone.value
        effective_exclude_list = list(exclude_list or [
            imp_model_id,
        ])
        

        def _reset_cache_data():
            """
            Reset runtime cache state for the outpost imp service.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Reset Imp Service Cache Helper
              Purpose: Clear cached map-processing state and reset any active spawn tree.
            UserDescription: Internal support routine.
            Notes: Resets the cached spawn subtree when map readiness changes.
            """
            state["outpost_visit_signature"] = None
            state["map_processed"] = False
            state["last_stage_log"] = ""
            if state["spawn_tree"] is not None:
                state["spawn_tree"].reset()
                state["spawn_tree"] = None


        def _tick_outpost_imp_service(node: BehaviorTree.Node):
            """
            Drive the outpost imp preparation service loop.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Outpost Imp Service Tick Helper
              Purpose: Manage per-map imp preparation in outposts and reuse the spawn subtree when needed.
            UserDescription: Internal support routine.
            Notes: Resets state on loading changes and keeps running until the next eligible map change.
            """
            if (
                Map.IsMapLoading()
                or not Checks.Map.MapValid()
                or not Map.IsMapReady()
                or Map.IsExplorable()
            ):
                _reset_cache_data()
                return BehaviorTree.NodeState.RUNNING

            if not Map.IsOutpost():
                _reset_cache_data()
                return BehaviorTree.NodeState.RUNNING

            current_map_id = Map.GetMapID()
            if current_map_id == 0:
                _reset_cache_data()
                return BehaviorTree.NodeState.RUNNING

            current_instance_uptime = Map.GetInstanceUptime()
            current_visit_signature = state["outpost_visit_signature"]
            if (
                current_visit_signature is None
                or current_visit_signature[0] != current_map_id
            ):
                state["outpost_visit_signature"] = (current_map_id, current_instance_uptime)
                state["map_processed"] = False
                if state["spawn_tree"] is not None:
                    state["spawn_tree"].reset()
                    state["spawn_tree"] = None

            if state["map_processed"]:
                return BehaviorTree.NodeState.RUNNING

            if state["spawn_tree"] is None:
                if GLOBAL_CACHE.Inventory.GetFirstModelID(imp_model_id) != 0:
                    state["map_processed"] = True
                    if log:
                        ConsoleLog(
                            "OutpostImpService",
                            f"Imp model {imp_model_id} already present in bags for map {current_map_id}.",
                            Console.MessageType.Info,
                            log=log,
                        )
                    return BehaviorTree.NodeState.RUNNING

                state["spawn_tree"] = BTUpkeepers.SpawnImp(
                    target_bag=target_bag,
                    slot=slot,
                    exclude_list=effective_exclude_list,
                    log=log,
                )

            state["spawn_tree"].blackboard = node.blackboard
            spawn_result = BehaviorTree.Node._normalize_state(state["spawn_tree"].tick())
            if spawn_result is None:
                raise TypeError("OutpostImpService spawn tree returned a non-NodeState result.")

            if spawn_result == BehaviorTree.NodeState.SUCCESS:
                if log:
                    ConsoleLog(
                        "OutpostImpService",
                        f"Prepared imp model {imp_model_id} in outpost map {current_map_id}.",
                        Console.MessageType.Success,
                        log=log,
                    )
                state["map_processed"] = True
                state["spawn_tree"].reset()
                state["spawn_tree"] = None
            elif spawn_result == BehaviorTree.NodeState.FAILURE:
                ConsoleLog(
                    "OutpostImpService",
                    f"Failed to prepare imp model {imp_model_id} in outpost map {current_map_id}; idling until next map change.",
                    Console.MessageType.Warning,
                    log=True,
                )
                state["map_processed"] = True
                state["spawn_tree"].reset()
                state["spawn_tree"] = None

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name="OutpostImpService",
                condition_fn=_tick_outpost_imp_service,
            )
        )

    @staticmethod
    def ExplorableImpService(
        imp_model_id: int = ModelID.Igneous_Summoning_Stone.value,
        log: bool = False,
        check_interval_ms: int = 1000,
    ) -> BehaviorTree:
        """
        Build a service tree that uses the imp stone automatically in eligible explorable maps.

        Meta:
          Expose: true
          Audience: advanced
          Display: Explorable Imp Service
          Purpose: Run a background service that summons the imp in explorable areas when conditions allow.
          UserDescription: Use this as a service tree when you want the imp stone to be used automatically during leveling or farming flows.
          Notes: Skips use while loading, in outposts, when dead, at level 20, during summoning sickness, or when an imp is already alive.
        """
        state = {
            "last_attempt_ms": 0,
        }

        summoning_sickness_effect_id = 2886
        summon_creature_model_ids = {
            513,   # Fire Imp
            1726,  # Fire Imp variant
        }

        def _has_alive_imp() -> bool:
            """
            Check whether a summoned imp is already alive in the party.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Has Alive Imp Helper
              Purpose: Detect an existing summoned imp before attempting to use the imp stone again.
              UserDescription: Internal support routine.
              Notes: Looks at other party members and filters out dead summons.
            """
            for other in GLOBAL_CACHE.Party.GetOthers():
                if Agent.GetModelID(other) in summon_creature_model_ids and not Agent.IsDead(other):
                    return True
            return False

        def _tick_explorable_imp_service(node: BehaviorTree.Node):
            """
            Drive the explorable imp-summon service loop.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Explorable Imp Service Tick Helper
              Purpose: Decide when the imp stone can be used in explorable maps and trigger it when allowed.
              UserDescription: Internal support routine.
              Notes: Skips use when the player is dead, level-capped, loading, ineligible, or already protected by an active imp or summoning sickness.
            """
            if Map.IsMapLoading() or not Checks.Map.MapValid() or not Map.IsMapReady():
                return BehaviorTree.NodeState.RUNNING

            if not Map.IsExplorable():
                return BehaviorTree.NodeState.RUNNING

            if Agent.IsDead(Player.GetAgentID()):
                return BehaviorTree.NodeState.RUNNING

            if Player.GetLevel() >= 20:
                return BehaviorTree.NodeState.RUNNING

            if GLOBAL_CACHE.Inventory.GetFirstModelID(imp_model_id) == 0:
                return BehaviorTree.NodeState.RUNNING

            if GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), summoning_sickness_effect_id):
                return BehaviorTree.NodeState.RUNNING

            if _has_alive_imp():
                return BehaviorTree.NodeState.RUNNING

            from ...Py4GWcorelib import Utils
            now = Utils.GetBaseTimestamp()

            if now - int(state["last_attempt_ms"]) < check_interval_ms:
                return BehaviorTree.NodeState.RUNNING

            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(imp_model_id)
            if item_id == 0:
                return BehaviorTree.NodeState.RUNNING

            GLOBAL_CACHE.Inventory.UseItem(item_id)
            state["last_attempt_ms"] = int(now)
            if log:
                ConsoleLog(
                    "ExplorableImpService",
                    f"Used imp stone model {imp_model_id} in explorable map {Map.GetMapID()}.",
                    Console.MessageType.Info,
                    log=log,
                )

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name="ExplorableImpService",
                condition_fn=_tick_explorable_imp_service,
            )
        )

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
      Display: Travel To Outpost
      Purpose: Build a tree that performs a map or travel routine.
      UserDescription: Use this when you want to change or prepare the current map state.
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

from ...GlobalCache import GLOBAL_CACHE
from ...Map import Map
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree


class BTMap:
    """
    Public BT helper group for map travel, mode switching, and map-load waiting routines.

    Meta:
      Expose: true
      Audience: advanced
      Display: Map
      Purpose: Group public BT routines related to map state, travel, and map readiness flows.
      UserDescription: Built-in BT helper group for travel and map-state routines.
      Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
    """
    @staticmethod
    def SetHardMode(hard_mode=True, log=False):
        """
        Build a tree that switches the party difficulty mode and verifies the result.

        Meta:
          Expose: true
          Audience: beginner
          Display: Set Hard Mode
          Purpose: Set the party to hard mode or normal mode.
          UserDescription: Use this when you want to change the current party difficulty setting.
          Notes: Verifies the requested mode after issuing the mode change action.
        """
        def set_mode():
            """
            Issue the party difficulty mode change.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Set Mode Helper
              Purpose: Dispatch the normal-mode or hard-mode request for the enclosing routine.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after sending the mode request.
            """
            if not hard_mode:
                GLOBAL_CACHE.Party.SetNormalMode()
            else:
                GLOBAL_CACHE.Party.SetHardMode()
            return BehaviorTree.NodeState.SUCCESS
        
        def check_mode_and_log():
            """
            Verify that the requested party difficulty mode is active.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Check Mode Helper
              Purpose: Confirm that the requested difficulty mode change succeeded.
              UserDescription: Internal support routine.
              Notes: Returns a boolean result for the enclosing condition node and logs success or failure.
            """
            if GLOBAL_CACHE.Party.IsHardMode() == hard_mode:
                ConsoleLog("SetHardMode", f"Mode set to {'hard_mode' if hard_mode else 'normal_mode'}.", Console.MessageType.Info, log=log)
                return True
            ConsoleLog("SetHardMode", f"Failed to set hard mode to {hard_mode}.", Console.MessageType.Error, log=log)
            return False
        
        tree = BehaviorTree.SequenceNode(children=[
                    BehaviorTree.ActionNode(name="SetMode", action_fn=lambda: set_mode(), aftercast_ms=500),
                    BehaviorTree.ConditionNode(name="CheckMode", condition_fn=lambda: check_mode_and_log()),
                ])
        
        return BehaviorTree(tree)

    @staticmethod
    def TravelToOutpost(outpost_id: int, log: bool = False, timeout: int = 10000) -> BehaviorTree: 
        """
        Build a tree that travels to an outpost and waits for arrival.

        Meta:
          Expose: true
          Audience: beginner
          Display: Travel To Outpost
          Purpose: Travel to a target outpost and wait until the map is ready.
          UserDescription: Use this when you want to move the party to a specific outpost safely.
          Notes: Succeeds immediately if already in the requested outpost and otherwise waits for map readiness and party load.
        """
        def arrived_early(outpost_id) -> bool: 
            """
            Check whether the party is already in the requested outpost.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Travel To Outpost Early Arrival Helper
              Purpose: Short-circuit the outpost travel routine when the destination is already active.
              UserDescription: Internal support routine.
              Notes: Logs the matched outpost when early success is detected.
            """
            if Map.IsMapIDMatch(0, outpost_id): 
                ConsoleLog("TravelToOutpost", f"Already at {Map.GetMapName(outpost_id)}", log=log) 
                return True
            return False

        def travel_action(outpost_id) -> BehaviorTree.NodeState:
            """
            Dispatch the outpost travel request.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Travel To Outpost Action Helper
              Purpose: Send the map-travel request for the requested outpost id.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after dispatching the travel request.
            """
            ConsoleLog("TravelToOutpost", f"Travelling to {Map.GetMapName(outpost_id)}", log=log)
            Map.Travel(outpost_id)
            return BehaviorTree.NodeState.SUCCESS 
        
        def map_arrival (outpost_id: int) -> BehaviorTree.NodeState: 
            """
            Check whether the requested outpost has fully loaded.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Travel To Outpost Arrival Helper
              Purpose: Confirm that the destination outpost is ready and the party has finished loading.
              UserDescription: Internal support routine.
              Notes: Keeps the enclosing wait node running until map readiness and outpost id match both succeed.
            """
            if (Map.IsMapReady() and 
                GLOBAL_CACHE.Party.IsPartyLoaded() and 
                Map.IsMapIDMatch(0, outpost_id)): 
                ConsoleLog("TravelToOutpost", f"Arrived at {Map.GetMapName(outpost_id)}", log=log) 
                return BehaviorTree.NodeState.SUCCESS 
            return BehaviorTree.NodeState.RUNNING 
        
        tree = BehaviorTree.SelectorNode(children=[ 
                    BehaviorTree.ConditionNode(name="ArrivedEarly", condition_fn=lambda: arrived_early(outpost_id)),
                    BehaviorTree.SequenceNode(name="TravelSequence", children=[ 
                        BehaviorTree.ActionNode(name="TravelAction", action_fn=lambda: travel_action(outpost_id), aftercast_ms=3000),
                        BehaviorTree.WaitNode(name="MapArrival", check_fn=lambda: map_arrival(outpost_id), timeout_ms=timeout),
                        BehaviorTree.WaitForTimeNode(name="PostArrivalWait", duration_ms=1000)
                    ]) 
            ]) 
        
        return BehaviorTree(tree)

    @staticmethod
    def TravelToRegion(outpost_id, region, district, language=0, log:bool=False, timeout: int = 10000):
        """
        Build a tree that travels to a specific outpost, region, district, and language combination.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Travel To Region
          Purpose: Travel to a specific outpost instance variant and wait for arrival.
          UserDescription: Use this when you need to travel to a map with a specific region, district, or language.
          Notes: Treats matching map id, region, district, and language as early success.
        """
        # 1. EARLY ARRIVAL CHECK
        def arrived_early() -> bool:
            """
            Check whether the requested region variant is already active.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Travel To Region Early Arrival Helper
              Purpose: Short-circuit regional travel when map id, region, district, and language already match.
              UserDescription: Internal support routine.
              Notes: Logs the destination on early success.
            """
            if (Map.IsMapIDMatch(0, outpost_id) and
                Map.GetRegion() == region and
                Map.GetDistrict() == district and
                Map.GetLanguage() == language):

                ConsoleLog("TravelToRegion",
                        f"Already at {Map.GetMapName(outpost_id)}",
                        log=log)
                return True
            
            return False
        # 2. TRAVEL ACTION
        def travel_action() -> BehaviorTree.NodeState:
            """
            Dispatch the region-aware travel request.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Travel To Region Action Helper
              Purpose: Send the regional travel request for the requested outpost and instance settings.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after dispatching the travel request.
            """
            ConsoleLog("TravelToRegion",
                    f"Travelling to {Map.GetMapName(outpost_id)}",
                    log=log)
            Map.TravelToRegion(outpost_id, region, district, language)
            return BehaviorTree.NodeState.SUCCESS
        # 3. ARRIVAL CHECK
        def map_arrival() -> BehaviorTree.NodeState:
            """
            Check whether the requested regional destination has fully loaded.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Travel To Region Arrival Helper
              Purpose: Confirm that map id, region, district, language, and loading state all match the destination.
              UserDescription: Internal support routine.
              Notes: Keeps the enclosing wait node running until the full destination state matches.
            """
            if (Map.IsMapReady() and
                GLOBAL_CACHE.Party.IsPartyLoaded() and
                Map.IsMapIDMatch(0, outpost_id) and
                Map.GetRegion() == region and
                Map.GetDistrict() == district and
                Map.GetLanguage() == language):

                ConsoleLog("TravelToRegion",
                        f"Arrived at {Map.GetMapName(outpost_id)}",
                        log=log)
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.NodeState.RUNNING
            

        tree = BehaviorTree.SelectorNode(children=[
            BehaviorTree.ConditionNode(name="ArrivedEarly",condition_fn=lambda: arrived_early()),
            BehaviorTree.SequenceNode(name="TravelSequence", children=[
                BehaviorTree.ActionNode(name="TravelToRegionAction", action_fn=lambda: travel_action(), aftercast_ms=2000),
                BehaviorTree.WaitNode(name="WaitForMapArrival", check_fn=lambda: map_arrival(), timeout_ms=timeout),
                BehaviorTree.WaitForTimeNode(name="PostArrivalWait", duration_ms=1000)
            ])
        ])

        return BehaviorTree(tree)

    @staticmethod
    def TravelGH(log: bool = False, wait_time: int = 1000, timeout: int = 15000) -> BehaviorTree:
        """
        Build a tree that travels to the guild hall and waits until it is loaded.

        Meta:
          Expose: true
          Audience: beginner
          Display: Travel Guild Hall
          Purpose: Travel to the guild hall and wait for a ready guild hall outpost.
          UserDescription: Use this when the current route needs to enter the guild hall and continue only after loading is complete.
          Notes: Succeeds early when already in a loaded guild hall.
        """
        def already_in_guild_hall() -> bool:
            if Map.IsMapReady() and Map.IsOutpost() and Map.IsGuildHall() and GLOBAL_CACHE.Party.IsPartyLoaded():
                ConsoleLog("TravelGH", "Already in a loaded guild hall.", Console.MessageType.Info, log=log)
                return True
            return False

        def travel_gh_action() -> BehaviorTree.NodeState:
            """
            Dispatch the travel-to-guild-hall request.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Travel Guild Hall Helper
              Purpose: Send the low-level map travel guild hall request.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after dispatching the request.
            """
            ConsoleLog("TravelGH", "Traveling to guild hall.", Console.MessageType.Info, log=log)
            Map.TravelGH()
            return BehaviorTree.NodeState.SUCCESS

        def guild_hall_loaded() -> BehaviorTree.NodeState:
            if (
                Map.IsMapReady()
                and Map.IsOutpost()
                and Map.IsGuildHall()
                and GLOBAL_CACHE.Party.IsPartyLoaded()
                and Map.GetInstanceUptime() >= 1500
                and Player.GetInstanceUptime() >= 1500
            ):
                ConsoleLog("TravelGH", "Guild hall loaded.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.SelectorNode(
                name="TravelGH",
                children=[
                    BehaviorTree.ConditionNode(
                        name="AlreadyInGuildHall",
                        condition_fn=already_in_guild_hall,
                    ),
                    BehaviorTree.SequenceNode(
                        name="TravelGHSequence",
                        children=[
                            BehaviorTree.ActionNode(
                                name="TravelGHAction",
                                action_fn=travel_gh_action,
                                aftercast_ms=wait_time,
                            ),
                            BehaviorTree.WaitUntilNode(
                                name="WaitForGuildHallLoad",
                                condition_fn=lambda node: guild_hall_loaded(),
                                throttle_interval_ms=500,
                                timeout_ms=timeout,
                            ),
                        ],
                    ),
                ],
            )
        )

    @staticmethod
    def LeaveGH(log: bool = False, wait_time: int = 1000, timeout: int = 15000) -> BehaviorTree:
        """
        Build a tree that leaves the guild hall and waits until a non-guild-hall outpost is loaded.

        Meta:
          Expose: true
          Audience: beginner
          Display: Leave Guild Hall
          Purpose: Leave the guild hall and wait for a ready non-guild-hall outpost.
          UserDescription: Use this when the current route needs to leave the guild hall before continuing in the returned outpost.
          Notes: Succeeds early when already in a loaded non-guild-hall outpost.
        """
        def already_outside_guild_hall() -> bool:
            if Map.IsMapReady() and Map.IsOutpost() and not Map.IsGuildHall() and GLOBAL_CACHE.Party.IsPartyLoaded():
                ConsoleLog("LeaveGH", "Already outside the guild hall in a loaded outpost.", Console.MessageType.Info, log=log)
                return True
            return False

        def leave_gh_action() -> BehaviorTree.NodeState:
            """
            Dispatch the leave-guild-hall request.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Leave Guild Hall Helper
              Purpose: Send the low-level map leave guild hall request.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after dispatching the request.
            """
            ConsoleLog("LeaveGH", "Leaving guild hall.", Console.MessageType.Info, log=log)
            Map.LeaveGH()
            return BehaviorTree.NodeState.SUCCESS

        def returned_outpost_loaded() -> BehaviorTree.NodeState:
            if (
                Map.IsMapReady()
                and Map.IsOutpost()
                and not Map.IsGuildHall()
                and GLOBAL_CACHE.Party.IsPartyLoaded()
                and Map.GetInstanceUptime() >= 1500
                and Player.GetInstanceUptime() >= 1500
            ):
                ConsoleLog("LeaveGH", "Returned outpost loaded.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.SelectorNode(
                name="LeaveGH",
                children=[
                    BehaviorTree.ConditionNode(
                        name="AlreadyOutsideGuildHall",
                        condition_fn=already_outside_guild_hall,
                    ),
                    BehaviorTree.SequenceNode(
                        name="LeaveGHSequence",
                        children=[
                            BehaviorTree.ActionNode(
                                name="LeaveGHAction",
                                action_fn=leave_gh_action,
                                aftercast_ms=wait_time,
                            ),
                            BehaviorTree.WaitUntilNode(
                                name="WaitForReturnedOutpostLoad",
                                condition_fn=lambda node: returned_outpost_loaded(),
                                throttle_interval_ms=500,
                                timeout_ms=timeout,
                            ),
                        ],
                    ),
                ],
            )
        )
    
    @staticmethod
    def WaitforMapLoad(map_id:int=0, log:bool=False, timeout: int = 10000, map_name: str =""):   
        """
        Build a tree that waits for a target map instance to finish loading.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait For Map Load
          Purpose: Wait until the target map is valid, ready, and fully loaded.
          UserDescription: Use this after travel or map transitions when you need to wait for the destination map to become usable.
          Notes: Accepts either `map_id` or `map_name` and also waits for party and player instance uptime checks.
        """
        def _map_arrival_check(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            """
            Check whether the requested map target has finished loading and is ready to use.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Wait For Map Load Helper
              Purpose: Resolve the requested target map and confirm full readiness for the enclosing wait routine.
              UserDescription: Internal support routine.
              Notes: Accepts map id or map name, then waits for map validity, party load, uptime, and map match before succeeding.
            """
            nonlocal map_id, map_name, log
            from ..Checks import Checks
            
            if map_name:
                map_id = Map.GetMapIDByName(map_name)
                
            if map_id == 0:
                return BehaviorTree.NodeState.RUNNING
            
            _map_valid = Checks.Map.MapValid()
            if not _map_valid:
                return BehaviorTree.NodeState.RUNNING
            
            if not GLOBAL_CACHE.Party.IsPartyLoaded():
                return BehaviorTree.NodeState.RUNNING
            
            if not Map.GetInstanceUptime() >= 1500:
                return BehaviorTree.NodeState.RUNNING
            
            if not Player.GetInstanceUptime() >= 1500:
                return BehaviorTree.NodeState.RUNNING

            if Map.IsMapIDMatch(Map.GetMapID(), map_id):
                ConsoleLog("WaitforMapLoad", f"Map {Map.GetMapName(map_id)} loaded successfully.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            return BehaviorTree.NodeState.RUNNING

        tree = BehaviorTree.SequenceNode(name="WaitforMapLoadRoot",
                    children=[
                        BehaviorTree.WaitUntilNode(name="WaitForMapLoadUntil",
                            condition_fn=lambda node: _map_arrival_check(node),
                            throttle_interval_ms=500,
                            timeout_ms=timeout),
                        BehaviorTree.WaitForTimeNode(name="PostArrivalWait", duration_ms=1000)
                    ]
                )
        
        return BehaviorTree(tree)

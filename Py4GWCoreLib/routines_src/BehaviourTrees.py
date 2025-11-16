
from ..GlobalCache import GLOBAL_CACHE
from ..Py4GWcorelib import ConsoleLog

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from enum import Enum, auto


import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()


class BT:
    NodeState = BehaviorTree.NodeState

    #region Map      
    class Map:  
        @staticmethod
        def TravelToOutpost(outpost_id: int, log: bool = False, timeout: int = 10000) -> BehaviorTree.Node: 
            """
            Purpose: Positions yourself safely on the outpost.
            Args:
                outpost_id (int): The ID of the outpost to travel to.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def already_in_map(outpost_id) -> bool: 
                if GLOBAL_CACHE.Map.GetMapID() == outpost_id: 
                    ConsoleLog("TravelToOutpost", f"Already at {GLOBAL_CACHE.Map.GetMapName(outpost_id)}", log=log) 
                    return True
                return False

            def travel_action(outpost_id) -> BehaviorTree.NodeState:
                ConsoleLog("TravelToOutpost", f"Travelling to {GLOBAL_CACHE.Map.GetMapName(outpost_id)}", log=log)
                GLOBAL_CACHE.Map.Travel(outpost_id)
                return BehaviorTree.NodeState.SUCCESS 
            
            def TravelReady (outpost_id: int) -> BehaviorTree.NodeState: 
                if (GLOBAL_CACHE.Map.IsMapReady() and 
                    GLOBAL_CACHE.Party.IsPartyLoaded() and 
                    GLOBAL_CACHE.Map.GetMapID() == outpost_id): 
                    ConsoleLog("TravelToOutpost", f"Arrived at {GLOBAL_CACHE.Map.GetMapName(outpost_id)}", log=log) 
                    return BehaviorTree.NodeState.SUCCESS 
                return BehaviorTree.NodeState.RUNNING 
            
            tree = BehaviorTree.SelectorNode(children=[ 
                        BehaviorTree.ConditionNode(name="AlreadyInMap", condition_fn=lambda: already_in_map(outpost_id)),
                        BehaviorTree.SequenceNode(name="TravelSequence", children=[ 
                            BehaviorTree.ActionNode(name="TravelAction", action_fn=lambda: travel_action(outpost_id)), 
                            BehaviorTree.WaitForTimeNode(name="WaitForTime", duration_ms=3000), 
                            BehaviorTree.WaitNode(name="TravelReady", check_fn=lambda: TravelReady(outpost_id), timeout_ms=timeout) 
                        ]) 
                ]) 
            
            return tree

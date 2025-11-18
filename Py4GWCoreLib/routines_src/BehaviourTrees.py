
from ..GlobalCache import GLOBAL_CACHE
from ..Py4GWcorelib import ConsoleLog, Console
from ..enums_src.Title_enums import TITLE_NAME

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from enum import Enum, auto

from .Checks import Checks

import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()


class BT:
    NodeState = BehaviorTree.NodeState

    #region Player
    class Player:
        @staticmethod
        def InteractAgent(agent_id:int, log:bool=False):
            """
            Purpose: Interact with the specified agent.
            Args:
                agent_id (int): The ID of the agent to interact with.
                log (bool) Optional: Whether to log the action. Default is False.
            """
            def _interact_agent(agent_id:int):
                GLOBAL_CACHE.Player.Interact(agent_id, False)
                ConsoleLog("InteractAgent", f"Interacted with agent {agent_id}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="InteractAgent", action_fn=lambda: _interact_agent(agent_id), aftercast_ms=100)
            return BehaviorTree(tree)
            
        @staticmethod
        def InteractTarget(log:bool=False):
            """
            Purpose: Interact with the currently selected target.
            """
            def _get_target_id(node: BehaviorTree.Node):
                node.blackboard["target_id"] = GLOBAL_CACHE.Player.GetTargetID()
                if node.blackboard["target_id"] == 0:
                    ConsoleLog("InteractTarget", "No target selected.", Console.MessageType.Error, log=True)
                    return BehaviorTree.NodeState.FAILURE

                ConsoleLog("InteractTarget",
                        f"Target ID obtained: {node.blackboard['target_id']}.",
                        Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.SequenceNode(children=[
                BehaviorTree.ActionNode(
                    name="GetTargetID",
                    action_fn=lambda node:_get_target_id(node),
                    aftercast_ms=0
                ),

                #SubtreeNode factory receives *its own node* (with blackboard)
                BehaviorTree.SubtreeNode(
                    name="InteractAgent",
                    subtree_fn=lambda node: BT.Player.InteractAgent(
                        node.blackboard["target_id"],
                        log=log
                    ),
                ),
            ])

            return BehaviorTree(tree)


        
        @staticmethod
        def SendDialog(dialog_id:str | int, log:bool=False):
            """
            Purpose: Send a dialog to the specified dialog ID.
            Args:
                dialog_id (str | int): The ID of the dialog to send.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _send_dialog(dialog_id):
                GLOBAL_CACHE.Player.SendDialog(dialog_id)
                ConsoleLog("SendDialog", f"Sent dialog {dialog_id}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SendDialog", action_fn=lambda: _send_dialog(dialog_id), aftercast_ms=300)
            return BehaviorTree(tree)
        
        @staticmethod   
        def SetTitle(title_id:int, log:bool=False):
            """
            Purpose: Set the player's title to the specified title ID.
            Args:
                title_id (int): The ID of the title to set.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _set_title(title_id:int):
                GLOBAL_CACHE.Player.SetActiveTitle(title_id)
                ConsoleLog("SetTitle", f"Set title to {TITLE_NAME.get(title_id, 'Invalid')}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SetTitle", action_fn=lambda: _set_title(title_id), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def SendChatCommand(command:str, log=False):
            """
            Purpose: Send a chat command.
            Args:
                command (str): The chat command to send.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _send_chat_command(command:str):
                GLOBAL_CACHE.Player.SendChatCommand(command)
                ConsoleLog("SendChatCommand", f"Sent chat command: {command}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SendChatCommand", action_fn=lambda: _send_chat_command(command), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def Resign(log:bool=False):
            """
            Purpose: Resign from the current map.
            Args:
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _resign():
                GLOBAL_CACHE.Player.SendChatCommand("resign")
                ConsoleLog("Resign", "Resigned from party.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="Resign", action_fn=lambda: _resign(), aftercast_ms=250)
            return BehaviorTree(tree)

        @staticmethod
        def SendChatMessage(channel:str, message:str, log=False):
            """
            Purpose: Send a chat message to the specified channel.
            Args:
                channel (str): The channel to send the message to.
                message (str): The message to send.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            def _send_chat_message(channel:str, message:str):
                GLOBAL_CACHE.Player.SendChat(channel, message)
                ConsoleLog("SendChatMessage", f"Sent chat message to {channel}: {message}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SendChatMessage", action_fn=lambda: _send_chat_message(channel, message), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def PrintMessageToConsole(source:str, message: str, message_type: int = Console.MessageType.Info):
            """
            Purpose: Print a message to the console.
            Args:
                message (str): The message to print.
            Returns: None
            """
            def _print_message_to_console(source:str, message: str, message_type: int):
                ConsoleLog(source, message, message_type, log=True)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="PrintMessageToConsole", action_fn=lambda: _print_message_to_console(source, message, message_type), aftercast_ms=100)
            return BehaviorTree(tree)

        @staticmethod
        def Move(x:float, y:float, log=False):
            """
            Purpose: Move the player to the specified coordinates.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _move(x:float, y:float):
                GLOBAL_CACHE.Player.Move(x, y)
                ConsoleLog("Move", f"Moving to ({x}, {y}).", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="Move", action_fn=lambda: _move(x, y), aftercast_ms=100)
            return BehaviorTree(tree)
        
        @staticmethod
        def MoveXYZ(x:float, y:float, zplane:float, log=False):
            """
            Purpose: Move the player to the specified coordinates with z-plane.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                zplane (float): The z-plane coordinate.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _move_xyz(x:float, y:float, zplane:float):
                GLOBAL_CACHE.Player.MoveXYZ(x, y, zplane)
                ConsoleLog("MoveXYZ", f"Moving to ({x}, {y}, {zplane}).", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="MoveXYZ", action_fn=lambda: _move_xyz(x, y, zplane), aftercast_ms=100)
            return BehaviorTree(tree)
        
    #region Skills
    class Skills:
        @staticmethod
        def LoadSkillbar(template:str, log:bool=False):
            """
            Purpose: Load a skillbar template.
            Args:
                template (str): The skillbar template to load.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _load_skillbar(template:str):
                GLOBAL_CACHE.SkillBar.LoadSkillTemplate(template)
                ConsoleLog("LoadSkillbar", f"Loaded skillbar template.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="LoadSkillbar", action_fn=lambda: _load_skillbar(template), aftercast_ms=500)
            return BehaviorTree(tree)
        
        @staticmethod
        def LoadHeroSkillbar(hero_index:int, template:str, log:bool=False):
            """
            Purpose: Load a hero's skillbar template.
            Args:
                hero_index (int): The index of the hero.
                template (str): The skillbar template to load.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _load_hero_skillbar(hero_index:int, template:str):
                GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(hero_index, template)
                ConsoleLog("LoadHeroSkillbar", f"Loaded hero {hero_index} skillbar template.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="LoadHeroSkillbar", action_fn=lambda: _load_hero_skillbar(hero_index, template), aftercast_ms=500)
            return BehaviorTree(tree)
        
        @staticmethod
        def CastSkillID (skill_id:int,target_agent_id:int =0, extra_condition=True, aftercast_delay=0,  log=False):
            """
            Purpose: Cast a skill by its ID using a Behavior Tree.
            Args:
                skill_id (int): The ID of the skill to cast.
                target_agent_id (int) Optional: The ID of the target agent. Default is 0.
                extra_condition (bool) Optional: An extra condition to check before casting. Default is True.
                aftercast_delay (int) Optional: Delay in milliseconds after casting the skill. Default is 0.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: A Behavior Tree that performs the skill cast.
            """
            def _use_skill(slot:int,target_agent_id:int, aftercast_delay:int, log:bool):
                GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=target_agent_id, aftercast_delay=aftercast_delay)
                ConsoleLog("CastSkillID", f"Cast {GLOBAL_CACHE.Skill.GetName(skill_id)}, slot: {GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)}", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.SequenceNode(children=[
                        BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Checks.Map.IsExplorable()),
                        BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Checks.Skills.HasEnoughEnergy(GLOBAL_CACHE.Player.GetAgentID(),skill_id)),
                        BehaviorTree.ConditionNode(name="IsSkillIDReady", condition_fn=lambda:Checks.Skills.IsSkillIDReady(skill_id)),
                        BehaviorTree.ConditionNode(name="IsSkillInSlot", condition_fn=lambda:1 <= GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id) <= 8),
                        BehaviorTree.ConditionNode(name="ExtraCustomCondition", condition_fn=lambda: extra_condition),
                        BehaviorTree.ActionNode(name="CastSkillID", action_fn=lambda:_use_skill(GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id), target_agent_id, aftercast_delay, log), aftercast_ms=aftercast_delay),
                    ])
            bt = BehaviorTree(root=tree)
            return bt
        
        @staticmethod
        def CastSkillSlot(slot:int,target_agent_id: int =0,extra_condition=True, aftercast_delay=0, log=False):
            """
            Purpose: Cast a skill in a specific slot using a Behavior Tree.
            Args:
                slot (int): The slot number of the skill to cast.
                extra_condition (bool) Optional: An extra condition to check before casting. Default is True.
                aftercast_delay (int) Optional: Delay in milliseconds after casting the skill. Default is 0.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: A Behavior Tree that performs the skill cast.
            """
            def _use_skill(slot:int,target_agent_id:int, aftercast_delay:int, log:bool):
                GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=target_agent_id, aftercast_delay=aftercast_delay)
                ConsoleLog("CastSkillSlot", f"Cast {GLOBAL_CACHE.Skill.GetName(GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot))}, slot: {slot}", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.SequenceNode(children=[
                        BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Routines.Checks.Map.IsExplorable()),
                        BehaviorTree.ConditionNode(name="ValidSkillSlot", condition_fn=lambda:1 <= slot <= 8),
                        BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Routines.Checks.Skills.HasEnoughEnergy(GLOBAL_CACHE.Player.GetAgentID(), GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot))),
                        BehaviorTree.ConditionNode(name="IsSkillSlotReady", condition_fn=lambda:Routines.Checks.Skills.IsSkillSlotReady(slot)),
                        BehaviorTree.ConditionNode(name="ExtraCustomCondition", condition_fn=lambda: extra_condition),
                        BehaviorTree.ActionNode(name="CastSkillSlot", action_fn=lambda:_use_skill(slot, target_agent_id, aftercast_delay, log), aftercast_ms=aftercast_delay),
                    ])
            bt = BehaviorTree(root=tree)
            return bt
        
        
        @staticmethod
        def IsSkillIDUsable(skill_id: int):
            """
            Purpose: Check if a skill by its ID is usable using a Behavior Tree.
            Args:
                skill_id (int): The ID of the skill to check.
            Returns: A Behavior Tree that checks if the skill is usable.
            """
            tree = BehaviorTree.SequenceNode(children=[
                BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Checks.Map.IsExplorable()),
                BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Checks.Skills.HasEnoughEnergy(GLOBAL_CACHE.Player.GetAgentID(),skill_id)),
                BehaviorTree.ConditionNode(name="IsSkillIDReady", condition_fn=lambda:Checks.Skills.IsSkillIDReady(skill_id)),
                BehaviorTree.ConditionNode(name="IsSkillInSlot", condition_fn=lambda:1 <= GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id) <= 8),
            ])
            bt = BehaviorTree(root=tree)
            return bt
        
        @staticmethod
        def IsSkillSlotUsable(skill_slot: int):
            """
            Purpose: Check if a skill in a specific slot is usable using a Behavior Tree.
            Args:
                skill_slot (int): The slot number of the skill to check.
            Returns: A Behavior Tree that checks if the skill in the slot is usable.
            """
            def _get_skill_id_from_slot(slot:int):
                return GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot)
            
            tree = BehaviorTree.SequenceNode(children=[
                BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Checks.Map.IsExplorable()),
                BehaviorTree.ConditionNode(name="ValidSkillSlot", condition_fn=lambda:1 <= skill_slot <= 8),
                BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Checks.Skills.HasEnoughEnergy(GLOBAL_CACHE.Player.GetAgentID(), _get_skill_id_from_slot(skill_slot))),
                BehaviorTree.ConditionNode(name="IsSkillIDReady", condition_fn=lambda:Checks.Skills.IsSkillSlotReady(skill_slot)),
            ])
            bt = BehaviorTree(root=tree)
            return bt

    #region Map      
    class Map:  
        @staticmethod
        def SetHardMode(hard_mode=True, log=False):
            """
            Purpose: Set the map to hard mode.
            Args: None
            Returns: None
            """
            def set_mode():
                if not hard_mode:
                    GLOBAL_CACHE.Party.SetNormalMode()
                else:
                    GLOBAL_CACHE.Party.SetHardMode()
                return BehaviorTree.NodeState.SUCCESS
            
            def check_mode_and_log():
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
            Purpose: Positions yourself safely on the outpost.
            Args:
                outpost_id (int): The ID of the outpost to travel to.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def arrived_early(outpost_id) -> bool: 
                if GLOBAL_CACHE.Map.GetMapID() == outpost_id: 
                    ConsoleLog("TravelToOutpost", f"Already at {GLOBAL_CACHE.Map.GetMapName(outpost_id)}", log=log) 
                    return True
                return False

            def travel_action(outpost_id) -> BehaviorTree.NodeState:
                ConsoleLog("TravelToOutpost", f"Travelling to {GLOBAL_CACHE.Map.GetMapName(outpost_id)}", log=log)
                GLOBAL_CACHE.Map.Travel(outpost_id)
                return BehaviorTree.NodeState.SUCCESS 
            
            def map_arrival (outpost_id: int) -> BehaviorTree.NodeState: 
                if (GLOBAL_CACHE.Map.IsMapReady() and 
                    GLOBAL_CACHE.Party.IsPartyLoaded() and 
                    GLOBAL_CACHE.Map.GetMapID() == outpost_id): 
                    ConsoleLog("TravelToOutpost", f"Arrived at {GLOBAL_CACHE.Map.GetMapName(outpost_id)}", log=log) 
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
            # 1. EARLY ARRIVAL CHECK
            def arrived_early() -> bool:
                if (GLOBAL_CACHE.Map.GetMapID() == outpost_id and
                    GLOBAL_CACHE.Map.GetRegion() == region and
                    GLOBAL_CACHE.Map.GetDistrict() == district and
                    GLOBAL_CACHE.Map.GetLanguage() == language):

                    ConsoleLog("TravelToRegion",
                            f"Already at {GLOBAL_CACHE.Map.GetMapName(outpost_id)}",
                            log=log)
                    return True
                
                return False
            # 2. TRAVEL ACTION
            def travel_action() -> BehaviorTree.NodeState:
                ConsoleLog("TravelToRegion",
                        f"Travelling to {GLOBAL_CACHE.Map.GetMapName(outpost_id)}",
                        log=log)
                GLOBAL_CACHE.Map.TravelToRegion(outpost_id, region, district, language)
                return BehaviorTree.NodeState.SUCCESS
            # 3. ARRIVAL CHECK
            def map_arrival() -> BehaviorTree.NodeState:
                if (GLOBAL_CACHE.Map.IsMapReady() and
                    GLOBAL_CACHE.Party.IsPartyLoaded() and
                    GLOBAL_CACHE.Map.GetMapID() == outpost_id and
                    GLOBAL_CACHE.Map.GetRegion() == region and
                    GLOBAL_CACHE.Map.GetDistrict() == district and
                    GLOBAL_CACHE.Map.GetLanguage() == language):

                    ConsoleLog("TravelToRegion",
                            f"Arrived at {GLOBAL_CACHE.Map.GetMapName(outpost_id)}",
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
        def WaitforMapLoad(map_id:int=0, log:bool=False, timeout: int = 10000, map_name: str =""):   
            def _map_arrival_check(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                nonlocal map_id, map_name, log
                
                if map_name:
                    map_id = GLOBAL_CACHE.Map.GetMapIDByName(map_name)
                
                
                if (GLOBAL_CACHE.Map.IsMapReady() and
                    GLOBAL_CACHE.Party.IsPartyLoaded() and
                    GLOBAL_CACHE.Map.GetMapID() == map_id and
                    GLOBAL_CACHE.Map.GetInstanceUptime() >= 2000):
                    ConsoleLog("WaitforMapLoad", f"Map {GLOBAL_CACHE.Map.GetMapName(map_id)} loaded successfully.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="WaitforMapLoadRoot",
                        children=[
                            BehaviorTree.RepeaterUntilSuccessNode(name="WaitForMapLoadLoop",timeout_ms=timeout,
                                child=
                                    BehaviorTree.SelectorNode(name="WaitForMapLoad",
                                        children=[
                                            BehaviorTree.ConditionNode(name="MapArrivalCheck",condition_fn=_map_arrival_check),
                                            BehaviorTree.SequenceNode(name="WaitForThrottle",
                                                children=[
                                                    BehaviorTree.WaitForTimeNode(500), 
                                                    BehaviorTree.FailureNode("FailToRepeat")
                                                ]
                                            )     
                                        ]
                                    )
                                ),
                            BehaviorTree.WaitForTimeNode(name="PostArrivalWait", duration_ms=1000)
                        ]
                    )
            
            return tree

    #region Agents        
    class Agents:
        agent_ids = None
        @staticmethod
        def GetAgentIDByName(agent_name: str) -> BehaviorTree:
            def _request_names(node):
                ids = GLOBAL_CACHE.AgentArray.GetAgentArray()
                node.blackboard["agent_ids"] = ids

                for aid in ids:
                    GLOBAL_CACHE.Agent.RequestName(aid)

                return BehaviorTree.NodeState.SUCCESS

            def _check_names_ready(node):
                for aid in node.blackboard["agent_ids"]:
                    if not GLOBAL_CACHE.Agent.IsNameReady(aid):
                        return BehaviorTree.NodeState.FAILURE
                return BehaviorTree.NodeState.SUCCESS
            
            def _search_name(node):
                search_lower = agent_name.lower()
                found = 0

                for aid in node.blackboard["agent_ids"]:
                    if GLOBAL_CACHE.Agent.IsNameReady(aid):
                        name = GLOBAL_CACHE.Agent.GetName(aid)
                        if search_lower in name.lower():
                            found = aid
                            break

                node.blackboard["result"] = found
                return (BehaviorTree.NodeState.SUCCESS
                        if found != 0
                        else BehaviorTree.NodeState.FAILURE)

            tree = BehaviorTree.SequenceNode(name="GetAgentIDByNameRoot",
                children=[
                    BehaviorTree.ActionNode(name="RequestAllNames",action_fn=_request_names),
                    BehaviorTree.RepeaterUntilSuccessNode(name="WaitUntilAllNamesReadyRepeater",timeout_ms=2000,
                        child=BehaviorTree.SelectorNode(name="WaitUntilAllNamesReadySelector",
                            children=[
                                BehaviorTree.ConditionNode(name="AllNamesReadyCheck",condition_fn=_check_names_ready),
                                BehaviorTree.SequenceNode(name="WaitForThrottle",
                                    children=[
                                        BehaviorTree.WaitForTimeNode(name="Throttle100ms",duration_ms=100),
                                        BehaviorTree.FailureNode(name="FailToRepeat")
                                    ]
                                ),
                            ]
                        )
                    ),
                    BehaviorTree.ActionNode(name="SearchName",action_fn=_search_name)
                ]
            )
            return BehaviorTree(tree)
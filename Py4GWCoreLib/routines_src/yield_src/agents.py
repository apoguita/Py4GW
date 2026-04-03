from __future__ import annotations

from ...Agent import Agent
from ...Player import Player
from ..BehaviourTrees import BT
from .helpers import _run_bt_tree, wait
from .movement import Movement
from .player import Player as YieldPlayer


class Agents:
    @staticmethod
    def GetAgentIDByName(agent_name):
        tree = BT.Agents.GetAgentIDByName(agent_name)
        yield from _run_bt_tree(tree, throttle_ms=100)
        agent = tree.blackboard.get("result", 0)
        return agent

    @staticmethod
    def GetAgentIDByModelID(model_id: int):
        """
        Purpose: Get the agent ID by model ID.
        Args:
            model_id (int): The model ID of the agent.
        Returns: int: The agent ID or 0 if not found.
        """
        tree = BT.Agents.GetAgentIDByModelID(model_id)
        yield from _run_bt_tree(tree, throttle_ms=100)
        agent = tree.blackboard.get("result", 0)
        return agent

    @staticmethod
    def ChangeTarget(agent_id, log=False):
        """
        Purpose: Change the player's target to the specified agent ID.
        Args:
            agent_id (int): The ID of the agent to target.
        Returns: None
        """
        yield from YieldPlayer.ChangeTarget(agent_id, log=log)

    @staticmethod
    def InteractAgent(agent_id: int, log: bool = False):
        """
        Purpose: Interact with the specified agent.
        Args:
            agent_id (int): The ID of the agent to interact with.
            log (bool) Optional: Whether to log the action. Default is False.
        """
        yield from YieldPlayer.InteractAgent(agent_id, log=log)

    @staticmethod
    def TargetAgentByName(agent_name: str, log: bool = False):
        """
        Purpose: Target an agent by name.
        Args:
            agent_name (str): The name of the agent to target.
        Returns: None
        """
        tree = BT.Agents.TargetAgentByName(agent_name, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def TargetNearestNPC(distance: float = 4500.0, log: bool = False):
        """
        Purpose: Target the nearest NPC within a specified distance.
        Args:
            distance (float) Optional: The maximum distance to search for an NPC. Default is 4500.0.
        Returns: None
        """
        tree = BT.Agents.TargetNearestNPC(distance, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def TargetNearestNPCXY(x, y, distance, log: bool = False):
        """
        Purpose: Target the nearest NPC to specified coordinates within a certain distance.
        Args:
            x (float): The x coordinate.
            y (float): The y coordinate.
            distance (float): The maximum distance to search for an NPC.
        Returns: None
        """
        tree = BT.Agents.TargetNearestNPCXY(x, y, distance, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def TargetNearestGadgetXY(x, y, distance, log: bool = False):
        """
        Purpose: Target the nearest gadget to specified coordinates within a certain distance.
        Args:
            x (float): The x coordinate.
            y (float): The y coordinate.
            distance (float): The maximum distance to search for a gadget.
        Returns: None
        """
        tree = BT.Agents.TargetNearestGadgetXY(x, y, distance, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def TargetNearestItemXY(x, y, distance, log: bool = False):
        """
        Purpose: Target the nearest item to specified coordinates within a certain distance.
        Args:
            x (float): The x coordinate.
            y (float): The y coordinate.
            distance (float): The maximum distance to search for an item.
        Returns: None
        """
        tree = BT.Agents.TargetNearestItemXY(x, y, distance, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def TargetNearestEnemy(distance, log: bool = False):
        """
        Purpose: Target the nearest enemy within a specified distance.
        Args:
            distance (float): The maximum distance to search for an enemy.
        Returns: None
        """
        tree = BT.Agents.TargetNearestEnemy(distance, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def TargetNearestItem(distance, log: bool = False):
        """
        Purpose: Target the nearest item within a specified distance.
        Args:
            distance (float): The maximum distance to search for an item.
        Returns: None
        """
        tree = BT.Agents.TargetNearestItem(distance, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def TargetNearestChest(distance, log: bool = False):
        """
        Purpose: Target the nearest chest within a specified distance.
        Args:
            distance (float): The maximum distance to search for a chest.
        Returns: None
        """
        tree = BT.Agents.TargetNearestChest(distance, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def InteractWithNearestChest(max_distance: int = 2500, before_interact_fn=lambda: None, after_interact_fn=lambda: None):
        """Target and interact with chest and items."""
        from ...Py4GWcorelib import LootConfig, Utils
        from ...enums_src.GameData_enums import Range
        from ..Agents import Agents as BaseAgents

        nearest_chest = BaseAgents.GetNearestChest(max_distance)
        chest_x, chest_y = Agent.GetXY(nearest_chest)

        yield from Movement.FollowPath([(chest_x, chest_y)])
        yield from wait(500)

        before_interact_fn()

        yield from YieldPlayer.InteractAgent(nearest_chest)
        yield from wait(500)
        Player.SendDialog(2)
        yield from wait(500)

        yield from Agents.TargetNearestItem(distance=300)
        filtered_loot = LootConfig().GetfilteredLootArray(Range.Area.value, multibox_loot=True)
        item = Utils.GetFirstFromArray(filtered_loot)
        yield from Agents.ChangeTarget(item)
        yield from YieldPlayer.InteractTarget()

        after_interact_fn()

        yield from wait(1000)

    @staticmethod
    def InteractWithAgentByName(agent_name: str):
        yield from Agents.TargetAgentByName(agent_name)
        agent_x, agent_y = Agent.GetXY(Player.GetTargetID())

        yield from Movement.FollowPath([(agent_x, agent_y)])
        yield from wait(500)

        yield from YieldPlayer.InteractTarget()
        yield from wait(1000)

    @staticmethod
    def InteractWithAgentXY(x: float, y: float, timeout_ms: int = 5000, tolerance: float = 200.0):
        from ...Py4GWcorelib import ConsoleLog, Utils
        yield from Agents.TargetNearestNPCXY(x, y, 100)
        target_id = Player.GetTargetID()
        if not target_id:
            ConsoleLog("InteractWithGadgetXY", "No target after targeting.")
            return False

        yield from YieldPlayer.InteractTarget()

        elapsed = 0
        since_reissue = 0
        reissue_interval = 1000
        step = 100
        while elapsed < timeout_ms:
            px, py = Player.GetXY()
            tx, ty = Agent.GetXY(target_id)
            if Utils.Distance((px, py), (tx, ty)) <= tolerance:
                break

            if since_reissue >= reissue_interval:
                yield from Agents.TargetNearestGadgetXY(x, y, 100)
                yield from YieldPlayer.InteractTarget()
                since_reissue = 0

            yield from wait(step)
            elapsed += step
            since_reissue += step

        if elapsed >= timeout_ms:
            ConsoleLog("InteractWithAgentXY", "TIMEOUT waiting to reach target range.")
            return False

        yield from wait(500)
        return True

    @staticmethod
    def InteractWithGadgetXY(x: float, y: float, tolerance: float = 200.0, timeout_ms: int = 15000):
        from ...Py4GWcorelib import ConsoleLog, Utils
        yield from Agents.TargetNearestGadgetXY(x, y, 100)
        target_id = Player.GetTargetID()
        if not target_id:
            ConsoleLog("InteractWithGadgetXY", "No target after targeting.")
            return False

        yield from YieldPlayer.InteractTarget()

        elapsed = 0
        since_reissue = 0
        step = 100
        while elapsed < timeout_ms:
            px, py = Player.GetXY()
            tx, ty = Agent.GetXY(target_id)
            if Utils.Distance((px, py), (tx, ty)) <= tolerance:
                break

            if since_reissue >= 1000:
                yield from Agents.TargetNearestGadgetXY(x, y, 100)
                yield from YieldPlayer.InteractTarget()
                since_reissue = 0

            yield from wait(step)
            elapsed += step
            since_reissue += step

        if elapsed >= timeout_ms:
            ConsoleLog("InteractWithAgentXY", "TIMEOUT waiting to reach target range.")
            return False

        yield from wait(500)
        return True

    @staticmethod
    def InteractWithItemXY(x: float, y: float, tolerance: float = 200.0, timeout_ms: int = 15000):
        from ...Py4GWcorelib import ConsoleLog, Utils
        yield from Agents.TargetNearestItemXY(x, y, 100)
        target_id = Player.GetTargetID()
        if not target_id:
            ConsoleLog("InteractWithItemXY", "No target after targeting.")
            return False

        yield from YieldPlayer.InteractTarget()

        elapsed = 0
        since_reissue = 0
        step = 100
        while elapsed < timeout_ms:
            px, py = Player.GetXY()
            tx, ty = Agent.GetXY(target_id)
            if Utils.Distance((px, py), (tx, ty)) <= tolerance:
                break

            if since_reissue >= 1000:
                yield from Agents.TargetNearestItemXY(x, y, 100)
                yield from YieldPlayer.InteractTarget()
                since_reissue = 0

            yield from wait(step)
            elapsed += step
            since_reissue += step

        if elapsed >= timeout_ms:
            ConsoleLog("InteractWithAgentXY", "TIMEOUT waiting to reach target range.")
            return False

        yield from wait(500)
        return True

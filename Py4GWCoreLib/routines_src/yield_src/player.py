from __future__ import annotations

from ...Py4GWcorelib import Console
from ..BehaviourTrees import BT
from .helpers import _run_bt_tree


class Player:
    @staticmethod
    def InteractAgent(agent_id: int, log: bool = False):
        """
        Purpose: Interact with the specified agent.
        Args:
            agent_id (int): The ID of the agent to interact with.
            log (bool) Optional: Whether to log the action. Default is False.
        """
        tree = BT.Player.InteractAgent(agent_id=agent_id, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def InteractTarget(log: bool = False):
        """
        Purpose: Interact with the currently selected target.
        Args:
            log (bool) Optional: Whether to log the action. Default is False.
        """
        tree = BT.Player.InteractTarget(log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def ChangeTarget(agent_id: int, log: bool = False):
        """
        Purpose: Change the player's target to the specified agent ID.
        Args:
            agent_id (int): The ID of the agent to target.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: None
        """
        tree = BT.Player.ChangeTarget(agent_id, log=log)
        yield from _run_bt_tree(tree, throttle_ms=250)

    @staticmethod
    def SendDialog(dialog_id: str, log: bool = False):
        """
        Purpose: Send a dialog to the specified dialog ID.
        Args:
            dialog_id (str): The ID of the dialog to send.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: None
        """
        tree = BT.Player.SendDialog(dialog_id, log=log)
        yield from _run_bt_tree(tree, throttle_ms=300)

    @staticmethod
    def SendAutomaticDialog(button_number: int, log: bool = False):
        """
        Purpose: Press the currently visible dialog button by 0-based position.
        Args:
            button_number (int): Visible button index starting at 0.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: None
        """
        tree = BT.Player.SendAutomaticDialog(button_number, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def SetTitle(title_id: int, log: bool = False):
        """
        Purpose: Set the player's title to the specified title ID.
        Args:
            title_id (int): The ID of the title to set.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: None
        """
        tree = BT.Player.SetTitle(title_id, log=log)
        yield from _run_bt_tree(tree, throttle_ms=300)

    @staticmethod
    def BuySkill(skill_id: int, log: bool = False):
        """
        Purpose: Buy/Learn a skill from a Skill Trainer.
        Args:
            skill_id (int): The ID of the skill to purchase.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: None
        """
        tree = BT.Player.BuySkill(skill_id, log=log)
        yield from _run_bt_tree(tree, throttle_ms=300)

    @staticmethod
    def UnlockBalthazarSkill(skill_id: int, use_pvp_remap: bool = True, log: bool = False):
        """
        Purpose: Unlock a skill from the Priest of Balthazar vendor.
        Args:
            skill_id (int): The ID of the skill to unlock.
            use_pvp_remap (bool) Optional: Whether to remap via PvP skill id. Default is True.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: None
        """
        tree = BT.Player.UnlockBalthazarSkill(skill_id, use_pvp_remap=use_pvp_remap, log=log)
        yield from _run_bt_tree(tree, throttle_ms=300)

    @staticmethod
    def SendChatCommand(command: str, log=False):
        """
        Purpose: Send a chat command.
        Args:
            command (str): The chat command to send.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: None
        """
        tree = BT.Player.SendChatCommand(command, log=log)
        yield from _run_bt_tree(tree, throttle_ms=300)

    @staticmethod
    def Resign(log: bool = False):
        """
        Purpose: Resign from the current map.
        Args:
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: None
        """
        tree = BT.Player.SendChatCommand("resign", log=log)
        yield from _run_bt_tree(tree, throttle_ms=250)

    @staticmethod
    def SendChatMessage(channel: str, message: str, log=False):
        """
        Purpose: Send a chat message to the specified channel.
        Args:
            channel (str): The channel to send the message to.
            message (str): The message to send.
            log (bool) Optional: Whether to log the action. Default is True.
        Returns: None
        """
        tree = BT.Player.SendChatMessage(channel, message, log=log)
        yield from _run_bt_tree(tree, throttle_ms=300)

    @staticmethod
    def PrintMessageToConsole(source: str, message: str, message_type: int = Console.MessageType.Info):
        """
        Purpose: Print a message to the console.
        Args:
            message (str): The message to print.
        Returns: None
        """
        tree = BT.Player.PrintMessageToConsole(source, message, message_type)
        yield from _run_bt_tree(tree, throttle_ms=100)

    @staticmethod
    def Move(x: float, y: float, log=False):
        """
        Purpose: Move the player to the specified coordinates.
        Args:
            x (float): The x coordinate.
            y (float): The y coordinate.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: None
        """
        tree = BT.Player.Move(x, y, log=log)
        yield from _run_bt_tree(tree, throttle_ms=100)

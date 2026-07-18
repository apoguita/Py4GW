from __future__ import annotations

from ...Py4GWcorelib import Utils
from ..BehaviourTrees import BT
from .helpers import _run_bt_tree


class Skills:
    @staticmethod
    def GenerateSkillbarTemplate():
        """
        Purpose: Generate template code for player's skillbar
        Args: None
        Returns: str: The current skillbar template.
        """
        skillbar_template = Utils.GenerateSkillbarTemplate()
        yield
        return skillbar_template

    @staticmethod
    def ParseSkillbarTemplate(template:str):
        '''
        Purpose: Parse a skillbar template into its components.
        Args:
            template (str): The skillbar template to parse.
        Returns:
            prof_primary (int): The primary profession ID.
            prof_secondary (int): The secondary profession ID.
            attributes (dict): A dictionary of attribute IDs and levels.
            skills (list): A list of skill IDs.
        '''

        result = Utils.ParseSkillbarTemplate(template)
        yield
        return result

    @staticmethod
    def LoadSkillbar(skill_template:str, log=False):
        """
        Purpose: Load the specified skillbar.
        Args:
            skill_template (str): The name of the skill template to load.
            log (bool) Optional: Whether to log the action. Default is True.
        Returns: None
        """
        tree = BT.Skills.LoadSkillbar(skill_template, log)
        yield from _run_bt_tree(tree, throttle_ms=500)

    @staticmethod
    def LoadHeroSkillbar(hero_index:int, skill_template:str, log=False):
        """
        Purpose: Load the specified hero skillbar.
        Args:
            hero_index (int): The index of the hero (1-4).
            skill_template (str): The name of the skill template to load.
            log (bool) Optional: Whether to log the action. Default is True.
        Returns: None
        """
        tree = BT.Skills.LoadHeroSkillbar(hero_index, skill_template, log)
        yield from _run_bt_tree(tree, throttle_ms=500)
    
        
    @staticmethod
    def IsSkillIDUsable(skill_id: int):
        """
        Purpose: Check if a skill by its ID is usable using a Behavior Tree.
        Args:
            skill_id (int): The ID of the skill to check.
        Returns: bool: True if the skill is usable, False otherwise.
        """
        tree = BT.Skills.IsSkillIDUsable(skill_id)
        result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=0)
        return result

    
    @staticmethod
    def IsSkillSlotUsable(skill_slot: int):
        """
        Purpose: Check if a skill in a specific slot is usable using a Behavior Tree.
        Args:
            skill_slot (int): The slot number of the skill to check.
        Returns: A Behavior Tree that checks if the skill in the slot is usable.
        """
        tree = BT.Skills.IsSkillSlotUsable(skill_slot)
        result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=0)
        return result
    
    @staticmethod    
    def CastSkillID (skill_id:int,target_agent_id:int =0, extra_condition=True, aftercast_delay=0,  log=False):
        """
        Purpose: Cast a skill by its ID using a coroutine.
        Args:
            skill_id (int): The ID of the skill to cast.
            target_agent_id (int) Optional: The ID of the target agent. Default is 0.
            extra_condition (bool) Optional: An extra condition to check before casting. Default is True.
            aftercast_delay (int) Optional: Delay in milliseconds after casting the skill. Default is 0.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: bool: True if the skill was cast successfully, False otherwise.
        """
        tree = BT.Skills.CastSkillID(skill_id, target_agent_id, extra_condition, aftercast_delay, log)
        result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=aftercast_delay)
        return result
        

    @staticmethod
    def CastSkillSlot(slot:int,extra_condition=True, aftercast_delay=0, log=False):
        """
        purpose: Cast a skill in a specific slot using a coroutine.

        Args:
            slot (int): The slot number of the skill to cast.
            extra_condition (bool) Optional: An extra condition to check before casting. Default is True.
            aftercast_delay (int) Optional: Delay in milliseconds after casting the skill. Default is 0.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: bool: True if the skill was cast successfully, False otherwise.
        """
        tree = BT.Skills.CastSkillSlot(slot=slot, extra_condition=extra_condition, aftercast_delay=aftercast_delay, log=log)
        result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=aftercast_delay)
        return result

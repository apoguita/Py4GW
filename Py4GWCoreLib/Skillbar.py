from PyAgent import AttributeClass
import PySkillbar
from typing import Dict, List, Tuple, Optional
from enum import IntEnum
from dataclasses import dataclass

from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


# ============================================================================
# Skill Usability Enum and Result (structured return instead of bare string)
# ============================================================================

class SkillUsability(IntEnum):
    """
    Enum for skill usability status.

    Use this instead of comparing strings to check why a skill can't be used.

    Example:
        result = SkillBar.GetSkillUsability(1)
        if result.status == SkillUsability.READY:
            SkillBar.UseSkill(1)
        elif result.status == SkillUsability.RECHARGING:
            print(f"Skill recharging, {result.value:.1f}s remaining")
    """
    READY = 0           # Skill can be used
    RECHARGING = 1      # Skill is on cooldown (value = remaining seconds)
    DISABLED = 2        # Player is disabled (casting/aftercast)
    NO_ENERGY = 3       # Not enough energy (value = current energy)
    NO_ADRENALINE = 4   # Not enough adrenaline (value = current adrenaline)
    EMPTY_SLOT = 5      # No skill in this slot


@dataclass
class SkillUsabilityResult:
    """
    Structured result for skill usability check.

    Attributes:
        status: SkillUsability enum indicating the reason
        value: Optional numeric value (e.g., remaining recharge seconds, current energy)
        required: Optional required value (e.g., energy cost, adrenaline cost)
    """
    status: SkillUsability
    value: Optional[float] = None
    required: Optional[float] = None

    def __str__(self) -> str:
        """Human-readable string representation."""
        if self.status == SkillUsability.READY:
            return "Ready"
        elif self.status == SkillUsability.RECHARGING:
            return f"Recharging ({self.value:.1f}s)"
        elif self.status == SkillUsability.DISABLED:
            return "Disabled"
        elif self.status == SkillUsability.NO_ENERGY:
            return f"No Energy ({int(self.value)}/{int(self.required)})"
        elif self.status == SkillUsability.NO_ADRENALINE:
            return f"No Adrenaline ({int(self.value)}/{int(self.required)})"
        elif self.status == SkillUsability.EMPTY_SLOT:
            return "Empty Slot"
        return "Unknown"


class SkillBar:
    @staticmethod
    def LoadSkillTemplate(skill_template):
        """
        Purpose: Load a skill template by name.
        Args:
            template_name (str): The name of the skill template to load.
        Returns: None
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.LoadSkillTemplate(skill_template)

    @staticmethod
    def LoadHeroSkillTemplate (hero_index, skill_template):
        """
        Purpose: Load a Hero skill template by Hero index and Template.
        Args:
            hero_index: int, template_name (str): The name of the skill template to load.
        Returns: None
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.LoadHeroSkillTemplate(hero_index, skill_template)

    @staticmethod
    def GetSkillbar():
        """
        Purpose: Retrieve the IDs of all 8 skills in the skill bar.
        Returns: list: A list containing the IDs of all 8 skills.
        """
        skill_ids = []
        for slot in range(1, 9):  # Loop through skill slots 1 to 8
            skill_id = SkillBar.GetSkillIDBySlot(slot)
            if skill_id != 0:
                skill_ids.append(skill_id)
        return skill_ids

    @staticmethod
    def GetZeroFilledSkillbar():
        skill_ids : dict[int, int] = {}
        for slot in range(1, 9):  # Loop through skill slots 1 to 8
            skill_ids[slot] = SkillBar.GetSkillIDBySlot(slot)

        return skill_ids

    @staticmethod
    def GetHeroSkillbar(hero_index):
        """
        Purpose: Retrieve the skill bar of a hero.
        Args:
            hero_index (int): The index of the hero to retrieve the skill bar from.
        Returns: list: A list of dictionaries containing skill details.
        """
        skillbar_instance = PySkillbar.Skillbar()
        hero_skillbar = skillbar_instance.GetHeroSkillbar(hero_index)
        return hero_skillbar


    @staticmethod
    def UseSkill(skill_slot, target_agent_id=0):
        """
        Purpose: Use a skill from the skill bar.
        Args:
            skill_slot (int): The slot number of the skill to use (1-8).
            target_agent_id (int, optional): The ID of the target agent. Default is 0.
        Returns: None
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.UseSkill(skill_slot, target_agent_id)

    @staticmethod
    def UseSkillTargetless(skill_slot):
        """
        Purpose: Use a skill from the skill bar without a target.
        Args:
            skill_slot (int): The slot number of the skill to use (1-8).
        Returns: None
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.UseSkillTargetless(skill_slot)

    @staticmethod
    def HeroUseSkill(target_agent_id, skill_number, hero_number):
        """
        Have a hero use a skill.
        Args:
            target_agent_id (int): The target agent ID.
            skill_number (int): The skill number (1-8)
            hero_number (int): The hero number (1-7)
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.HeroUseSkill(target_agent_id, skill_number, hero_number)

    @staticmethod
    def ChangeHeroSecondary(hero_index, secondary_profession):
        """
        Purpose: Change the secondary profession of a hero.
        Args:
            hero_index (int): The index of the hero to change.
            secondary_profession (int): The ID of the secondary profession to change to.
        Returns: None
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.ChangeHeroSecondary(hero_index, secondary_profession)

    @staticmethod
    def GetSkillIDBySlot(skill_slot):
        """
        Purpose: Retrieve the data of a skill by its slot number.
        Args:
            skill_slot (int): The slot number of the skill to retrieve (1-8).
        Returns: dict: A dictionary containing skill details retrieved by slot.
        """
        skillbar_instance = PySkillbar.Skillbar()
        skill = skillbar_instance.GetSkill(skill_slot)
        return skill.id.id

    #get the slot by skillid
    @staticmethod
    def GetSlotBySkillID(skill_id):
        """
        Purpose: Retrieve the slot number of a skill by its ID.
        Args:
            skill_id (int): The ID of the skill to retrieve.
        Returns: int: The slot number of the skill.
        """
        #search for all slots until skill found and return it
        for i in range(1, 9):
            if SkillBar.GetSkillIDBySlot(i) == skill_id:
                return i

        return 0

    @staticmethod
    def GetSkillData(slot):
        """
        Purpose: Retrieve the data of a skill by its ID.
        Args:
            slot (int): The slot number of the skill to retrieve (1-8).
        Returns: dict: A SkillbarSkill object containing skill details.
        """
        skill_instance = PySkillbar.Skillbar()
        return skill_instance.GetSkill(slot)

    @staticmethod
    def GetHoveredSkillID():
        """
        Purpose: Retrieve the ID of the skill that is currently hovered.
        Args: None
        Returns: int: The ID of the skill that is currently hovered.
        """
        skillbar_instance = PySkillbar.Skillbar()
        hovered_skill_id = skillbar_instance.GetHoveredSkill()
        return hovered_skill_id

    @staticmethod
    def IsSkillUnlocked(skill_id):
        """
        Purpose: Check if a skill is unlocked.
        Args:
            skill_id (int): The ID of the skill to check.
        Returns: bool: True if the skill is unlocked, False otherwise.
        """
        skillbar_instance = PySkillbar.Skillbar()
        return skillbar_instance.IsSkillUnlocked(skill_id)

    @staticmethod
    def IsSkillLearnt(skill_id):
        """
        Purpose: Check if a skill is learnt.
        Args:
            skill_id (int): The ID of the skill to check.
        Returns: bool: True if the skill is learnt, False otherwise.
        """
        skillbar_instance = PySkillbar.Skillbar()
        return skillbar_instance.IsSkillLearnt(skill_id)

    @staticmethod
    def GetAgentID():
        """
        Purpose: Retrieve the agent ID of the skill bar owner.
        Args: None
        Returns: int: The agent ID of the skill bar owner.
        """
        skillbar_instance = PySkillbar.Skillbar()
        return skillbar_instance.agent_id

    @staticmethod
    def GetDisabled():
        """
        Purpose: Check if the skill bar is disabled.
        Args: None
        Returns: bool: True if the skill bar is disabled, False otherwise.
        """
        skillbar_instance = PySkillbar.Skillbar()
        return skillbar_instance.disabled

    @staticmethod
    def GetCasting():
        """
        Purpose: Check if the skill bar is currently casting.
        Args: None
        Returns: bool: True if the skill bar is currently casting, False otherwise.
        """
        skillbar_instance = PySkillbar.Skillbar()
        return skillbar_instance.casting

    # =========================================================================
    # Skill Slot Live Data (Recharge, Adrenaline)
    # =========================================================================

    @staticmethod
    def GetSkillRecharge(slot: int) -> int:
        """
        Get the raw recharge timestamp for a skill slot.
        Args:
            slot: Skill slot (1-8)
        Returns:
            Raw recharge timestamp value.
        """
        skillbar_instance = PySkillbar.Skillbar()
        skill = skillbar_instance.GetSkill(slot)
        return skill.recharge

    @staticmethod
    def GetSkillRechargeRemaining(slot: int) -> int:
        """
        Get remaining recharge time in milliseconds for a skill slot.
        Args:
            slot: Skill slot (1-8)
        Returns:
            Remaining recharge time in milliseconds, 0 if recharged.
        """
        skillbar_instance = PySkillbar.Skillbar()
        skill = skillbar_instance.GetSkill(slot)
        return skill.get_recharge

    @staticmethod
    def IsSkillReady(slot: int) -> bool:
        """
        Check if a skill is ready to use (off cooldown).
        Args:
            slot: Skill slot (1-8)
        Returns:
            True if skill is recharged and ready.
        """
        return SkillBar.GetSkillRechargeRemaining(slot) == 0

    @staticmethod
    def GetSkillAdrenaline(slot: int) -> Tuple[int, int]:
        """
        Get the adrenaline values for a skill slot.
        Args:
            slot: Skill slot (1-8)
        Returns:
            Tuple of (adrenaline_a, adrenaline_b).
        """
        skillbar_instance = PySkillbar.Skillbar()
        skill = skillbar_instance.GetSkill(slot)
        return skill.adrenaline_a, skill.adrenaline_b

    @staticmethod
    def GetSkillEvent(slot: int) -> int:
        """
        Get the event value for a skill slot.
        Args:
            slot: Skill slot (1-8)
        Returns:
            Event value for the skill.
        """
        skillbar_instance = PySkillbar.Skillbar()
        skill = skillbar_instance.GetSkill(slot)
        return skill.event

    # =========================================================================
    # Hero Skillbar Live Data
    # =========================================================================

    @staticmethod
    def GetHeroSkillRecharge(hero_index: int, slot: int) -> int:
        """
        Get the raw recharge timestamp for a hero's skill slot.
        Args:
            hero_index: Hero index (1-7)
            slot: Skill slot (1-8)
        Returns:
            Raw recharge timestamp value.
        """
        skillbar_instance = PySkillbar.Skillbar()
        hero_skills = skillbar_instance.GetHeroSkillbar(hero_index)
        if slot < 1 or slot > len(hero_skills):
            return 0
        return hero_skills[slot - 1].recharge

    @staticmethod
    def GetHeroSkillRechargeRemaining(hero_index: int, slot: int) -> int:
        """
        Get remaining recharge time in milliseconds for a hero's skill slot.
        Args:
            hero_index: Hero index (1-7)
            slot: Skill slot (1-8)
        Returns:
            Remaining recharge time in milliseconds, 0 if recharged.
        """
        skillbar_instance = PySkillbar.Skillbar()
        hero_skills = skillbar_instance.GetHeroSkillbar(hero_index)
        if slot < 1 or slot > len(hero_skills):
            return 0
        return hero_skills[slot - 1].get_recharge

    @staticmethod
    def IsHeroSkillReady(hero_index: int, slot: int) -> bool:
        """
        Check if a hero's skill is ready to use (off cooldown).
        Args:
            hero_index: Hero index (1-7)
            slot: Skill slot (1-8)
        Returns:
            True if skill is recharged and ready.
        """
        return SkillBar.GetHeroSkillRechargeRemaining(hero_index, slot) == 0

    @staticmethod
    def GetHeroSkillAdrenaline(hero_index: int, slot: int) -> Tuple[int, int]:
        """
        Get the adrenaline values for a hero's skill slot.
        Args:
            hero_index: Hero index (1-7)
            slot: Skill slot (1-8)
        Returns:
            Tuple of (adrenaline_a, adrenaline_b).
        """
        skillbar_instance = PySkillbar.Skillbar()
        hero_skills = skillbar_instance.GetHeroSkillbar(hero_index)
        if slot < 1 or slot > len(hero_skills):
            return 0, 0
        skill = hero_skills[slot - 1]
        return skill.adrenaline_a, skill.adrenaline_b

    @staticmethod
    def GetHeroSkillIDBySlot(hero_index: int, slot: int) -> int:
        """
        Get the skill ID for a hero's skill slot.
        Args:
            hero_index: Hero index (1-7)
            slot: Skill slot (1-8)
        Returns:
            Skill ID in the slot, or 0 if invalid.
        """
        skillbar_instance = PySkillbar.Skillbar()
        hero_skills = skillbar_instance.GetHeroSkillbar(hero_index)
        if slot < 1 or slot > len(hero_skills):
            return 0
        return hero_skills[slot - 1].id.id

    # =========================================================================
    # Skill Usability Check
    # =========================================================================

    @staticmethod
    def CanUseSkill(slot: int, target_id: int = 0) -> bool:
        """
        Check if a skill can be used right now.

        Checks:
        - Skill is recharged
        - Player is not disabled (casting/aftercast)
        - Player has enough energy
        - Skill has enough adrenaline (if adrenaline skill)

        Args:
            slot: Skill slot (1-8)
            target_id: Optional target ID for range/target validation (not yet implemented)

        Returns:
            True if skill can be used.
        """
        from .Skill import Skill
        from .Agent import Agent
        from .Player import Player

        # Check if skill is recharged
        if not SkillBar.IsSkillReady(slot):
            return False

        # Check if disabled
        if SkillBar.GetDisabled():
            return False

        # Get skill ID and data
        skill_id = SkillBar.GetSkillIDBySlot(slot)
        if skill_id == 0:
            return False

        # Check energy cost
        energy_cost = Skill.Data.GetEnergyCost(skill_id)
        if energy_cost > 0:
            player_id = Player.GetAgentID()
            current_energy = Agent.GetEnergy(player_id)
            max_energy = Agent.GetMaxEnergy(player_id)
            if max_energy > 0:
                actual_energy = current_energy * max_energy
                if actual_energy < energy_cost:
                    return False

        # Check adrenaline (if skill uses adrenaline)
        adrenaline_cost = Skill.Data.GetAdrenaline(skill_id)
        if adrenaline_cost > 0:
            adrenaline_a, _ = SkillBar.GetSkillAdrenaline(slot)
            if adrenaline_a < adrenaline_cost:
                return False

        return True

    @staticmethod
    def GetSkillUsability(slot: int) -> SkillUsabilityResult:
        """
        Get structured information about why a skill can or cannot be used.

        Args:
            slot: Skill slot (1-8)

        Returns:
            SkillUsabilityResult with:
                - status: SkillUsability enum (READY, RECHARGING, NO_ENERGY, etc.)
                - value: Current value (e.g., current energy, remaining recharge)
                - required: Required value (e.g., energy cost, adrenaline cost)

        Example:
            result = SkillBar.GetSkillUsability(1)
            if result.status == SkillUsability.READY:
                SkillBar.UseSkill(1)
            elif result.status == SkillUsability.RECHARGING:
                print(f"Wait {result.value:.1f}s")
            elif result.status == SkillUsability.NO_ENERGY:
                print(f"Need {result.required - result.value:.0f} more energy")
        """
        from .Skill import Skill
        from .Agent import Agent
        from .Player import Player

        skill_id = SkillBar.GetSkillIDBySlot(slot)
        if skill_id == 0:
            return SkillUsabilityResult(SkillUsability.EMPTY_SLOT)

        if not SkillBar.IsSkillReady(slot):
            remaining = SkillBar.GetSkillRechargeRemaining(slot)
            return SkillUsabilityResult(SkillUsability.RECHARGING, value=remaining / 1000.0)

        if SkillBar.GetDisabled():
            return SkillUsabilityResult(SkillUsability.DISABLED)

        # Check energy
        energy_cost = Skill.Data.GetEnergyCost(skill_id)
        if energy_cost > 0:
            player_id = Player.GetAgentID()
            current_energy = Agent.GetEnergy(player_id)
            max_energy = Agent.GetMaxEnergy(player_id)
            if max_energy > 0:
                actual_energy = current_energy * max_energy
                if actual_energy < energy_cost:
                    return SkillUsabilityResult(
                        SkillUsability.NO_ENERGY,
                        value=actual_energy,
                        required=float(energy_cost)
                    )

        # Check adrenaline
        adrenaline_cost = Skill.Data.GetAdrenaline(skill_id)
        if adrenaline_cost > 0:
            adrenaline_a, _ = SkillBar.GetSkillAdrenaline(slot)
            if adrenaline_a < adrenaline_cost:
                return SkillUsabilityResult(
                    SkillUsability.NO_ADRENALINE,
                    value=float(adrenaline_a),
                    required=float(adrenaline_cost)
                )

        return SkillUsabilityResult(SkillUsability.READY)

    # =========================================================================
    # Template Encode/Decode (using Utils functions)
    # =========================================================================

    @staticmethod
    def DecodeTemplate(template_code: str) -> Optional[Dict]:
        """
        Decode a skill template code into its components.

        Args:
            template_code: The template string (e.g., "OgEUcZrSXzlYAVzlVAYzlZAA")

        Returns:
            Dictionary with keys:
                - primary: int (profession ID, 1-10)
                - secondary: int (profession ID, 0-10, 0=None)
                - skills: List[int] (8 skill IDs)
                - attributes: List[Tuple[int, int]] (attribute_id, points)
            Returns None if decode fails.
        """
        try:
            primary, secondary, attributes_dict, skills = Utils.ParseSkillbarTemplate(template_code)
            if primary is None:
                return None
            # Convert attributes dict to list of tuples for consistency
            attributes = [(attr_id, points) for attr_id, points in attributes_dict.items()]
            return {
                'primary': primary,
                'secondary': secondary,
                'skills': skills,
                'attributes': attributes
            }
        except Exception:
            return None

    @staticmethod
    def EncodeTemplate(primary: int, secondary: int, skills: List[int],
                       attributes: List[Tuple[int, int]]) -> Optional[str]:
        """
        Encode professions, skills, and attributes into a template code.

        Args:
            primary: Primary profession ID (1-10)
            secondary: Secondary profession ID (0-10, 0=None)
            skills: List of 8 skill IDs
            attributes: List of (attribute_id, points) tuples

        Returns:
            Template code string, or None if encoding fails.
        """
        try:
            # Convert list of tuples to dict for Utils
            attributes_dict = {attr_id: points for attr_id, points in attributes}
            return Utils.encode_skill_template(primary, secondary, attributes_dict, skills)
        except Exception:
            return None

    @staticmethod
    def GetCurrentTemplate() -> Optional[str]:
        """
        Get the current player skillbar as a template code.

        Returns:
            Template code string for the current build, or None if failed.
        """
        return Utils.GenerateSkillbarTemplate()


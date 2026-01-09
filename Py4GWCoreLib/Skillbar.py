from PyAgent import AttributeClass
import PySkillbar
from typing import Dict, List, Tuple, Optional

from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


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
    def GetSkillUsabilityReason(slot: int) -> str:
        """
        Get the reason why a skill cannot be used.

        Args:
            slot: Skill slot (1-8)

        Returns:
            String describing the skill state:
            - "Ready" if skill can be used
            - "Recharging" if on cooldown
            - "Disabled" if player is disabled
            - "No Energy" if not enough energy
            - "No Adrenaline" if not enough adrenaline
            - "Empty Slot" if no skill in slot
        """
        from .Skill import Skill
        from .Agent import Agent
        from .Player import Player

        skill_id = SkillBar.GetSkillIDBySlot(slot)
        if skill_id == 0:
            return "Empty Slot"

        if not SkillBar.IsSkillReady(slot):
            remaining = SkillBar.GetSkillRechargeRemaining(slot)
            return f"Recharging ({remaining / 1000:.1f}s)"

        if SkillBar.GetDisabled():
            return "Disabled"

        # Check energy
        energy_cost = Skill.Data.GetEnergyCost(skill_id)
        if energy_cost > 0:
            player_id = Player.GetAgentID()
            current_energy = Agent.GetEnergy(player_id)
            max_energy = Agent.GetMaxEnergy(player_id)
            if max_energy > 0:
                actual_energy = current_energy * max_energy
                if actual_energy < energy_cost:
                    return f"No Energy ({int(actual_energy)}/{energy_cost})"

        # Check adrenaline
        adrenaline_cost = Skill.Data.GetAdrenaline(skill_id)
        if adrenaline_cost > 0:
            adrenaline_a, _ = SkillBar.GetSkillAdrenaline(slot)
            if adrenaline_a < adrenaline_cost:
                return f"No Adrenaline ({adrenaline_a}/{adrenaline_cost})"

        return "Ready"

    # =========================================================================
    # Template Encode/Decode
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
        return _decode_template(template_code)

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
        return _encode_template(primary, secondary, skills, attributes)

    @staticmethod
    def GetCurrentTemplate(hero_index: int = 0) -> Optional[str]:
        """
        Get the current skillbar as a template code.

        Args:
            hero_index: 0 for player, 1-7 for heroes

        Returns:
            Template code string for the current build, or None if failed.
        """
        from .Agent import Agent
        from .Player import Player

        # Get skills
        if hero_index == 0:
            skills = []
            for slot in range(1, 9):
                skills.append(SkillBar.GetSkillIDBySlot(slot))
            agent_id = Player.GetAgentID()
        else:
            skillbar_instance = PySkillbar.Skillbar()
            hero_skills = skillbar_instance.GetHeroSkillbar(hero_index)
            skills = [s.id.id for s in hero_skills]
            # Pad to 8 if needed
            while len(skills) < 8:
                skills.append(0)
            # For heroes, we'd need hero agent ID - this is more complex
            # For now, return None for heroes (would need party context)
            return None

        # Get professions
        primary, secondary = Agent.GetProfessions(agent_id)

        # Get attributes
        attributes_raw = Agent.GetAttributes(agent_id)
        attributes = []
        for attr in attributes_raw:
            attr_id = int(attr.attribute_id)
            level = attr.level_base
            if level > 0:
                attributes.append((attr_id, level))

        return _encode_template(primary, secondary, skills, attributes)


# =============================================================================
# Internal: Skill Template Codec (not for direct use)
# =============================================================================

_BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_BASE64_VALUES = {c: i for i, c in enumerate(_BASE64_CHARS)}


def _write_bits(value: int, count: int = 6) -> List[int]:
    """Write value as count bits (LSB first)."""
    return [(value >> i) & 1 for i in range(count)]


def _read_bits(bits: List[int], offset: int, count: int) -> Tuple[int, int]:
    """Read count bits from offset, return (value, new_offset)."""
    value = 0
    for i in range(count):
        if offset + i < len(bits):
            value |= bits[offset + i] << i
    return value, offset + count


def _decode_template(template_code: str) -> Optional[Dict]:
    """Decode a skill template code into its components."""
    if not template_code:
        return None

    bits = []
    for char in template_code:
        if char not in _BASE64_VALUES:
            return None
        value = _BASE64_VALUES[char]
        bits.extend(_write_bits(value, 6))

    offset = 0
    header, offset = _read_bits(bits, offset, 4)
    if header != 0 and header != 14:
        return None

    if header == 14:
        _, offset = _read_bits(bits, offset, 4)

    prof_bits_code, offset = _read_bits(bits, offset, 2)
    bits_per_prof = 2 * prof_bits_code + 4

    primary, offset = _read_bits(bits, offset, bits_per_prof)
    secondary, offset = _read_bits(bits, offset, bits_per_prof)

    if primary < 1 or primary > 10 or secondary > 10:
        return None

    attr_count, offset = _read_bits(bits, offset, 4)
    attr_bits_code, offset = _read_bits(bits, offset, 4)
    bits_per_attr = attr_bits_code + 4

    attributes = []
    for _ in range(attr_count):
        attr_id, offset = _read_bits(bits, offset, bits_per_attr)
        attr_val, offset = _read_bits(bits, offset, 4)
        if attr_val > 0:
            attributes.append((attr_id, attr_val))

    skill_bits_code, offset = _read_bits(bits, offset, 4)
    bits_per_skill = skill_bits_code + 8

    skills = []
    for _ in range(8):
        if offset + bits_per_skill > len(bits):
            skills.append(0)
        else:
            skill_id, offset = _read_bits(bits, offset, bits_per_skill)
            skills.append(skill_id)

    return {
        'primary': primary,
        'secondary': secondary,
        'skills': skills,
        'attributes': attributes
    }


def _encode_template(primary: int, secondary: int, skills: List[int],
                     attributes: List[Tuple[int, int]]) -> Optional[str]:
    """Encode professions, skills, and attributes into a template code."""
    if primary < 1 or primary > 10 or secondary > 10:
        return None
    if len(skills) != 8:
        return None

    bits = []
    bits.extend(_write_bits(14, 4))
    bits.extend(_write_bits(0, 4))

    bits_per_prof = 4
    bits.extend(_write_bits((bits_per_prof - 4) // 2, 2))
    bits.extend(_write_bits(primary, bits_per_prof))
    bits.extend(_write_bits(secondary, bits_per_prof))

    valid_attrs = [(a, p) for a, p in attributes if p > 0]

    bits_per_attr = 4
    for attr_id, _ in valid_attrs:
        needed = attr_id.bit_length() if attr_id > 0 else 1
        if needed > bits_per_attr:
            bits_per_attr = needed

    bits.extend(_write_bits(len(valid_attrs), 4))
    bits.extend(_write_bits(bits_per_attr - 4, 4))

    for attr_id, attr_val in valid_attrs:
        bits.extend(_write_bits(attr_id, bits_per_attr))
        bits.extend(_write_bits(attr_val, 4))

    bits_per_skill = 8
    for skill_id in skills:
        if skill_id > 0:
            needed = skill_id.bit_length()
            if needed > bits_per_skill:
                bits_per_skill = needed

    bits.extend(_write_bits(bits_per_skill - 8, 4))

    for skill_id in skills:
        bits.extend(_write_bits(skill_id, bits_per_skill))

    bits.extend(_write_bits(0, 1))

    while len(bits) < 162:
        bits.append(0)

    while len(bits) % 6 != 0:
        bits.append(0)

    result = []
    for i in range(0, len(bits), 6):
        value = 0
        for j in range(6):
            if i + j < len(bits):
                value |= bits[i + j] << j
        result.append(_BASE64_CHARS[value])

    return ''.join(result)

from .Skill import Skill
from typing import List, Tuple, Optional
import re


class SkillProperties:
    """
    Skill properties detection based on skill descriptions and data.

    This class provides methods to determine what a skill DOES (causes interrupt,
    knockdown, applies conditions, etc.) rather than what TYPE it is.

    Uses skill descriptions from skill_descriptions.json combined with
    game data from PySkill to provide accurate skill behavior detection.

    Usage:
        # Check if a skill causes interrupt
        if SkillProperties.CausesInterrupt(skill_id):
            # This skill can interrupt

        # Check if skill has conditional bonus
        if SkillProperties.HasConditionalEffect(skill_id):
            conditions = SkillProperties.GetConditions(skill_id)
    """

    # Cache for parsed skill properties (skill_id -> properties dict)
    _properties_cache = {}

    # =========================================================================
    # Interrupt Detection
    # =========================================================================

    class Interrupt:
        """Methods for detecting interrupt-related skill properties."""

        @staticmethod
        def CausesInterrupt(skill_id: int) -> bool:
            """
            Purpose: Check if a skill causes interruption.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill can interrupt actions.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            # Check for interrupt as an EFFECT (not as a condition to trigger)
            # "Interrupts" at the start or after a period indicates the skill causes interrupt
            patterns = [
                r'\binterrupts?\b',           # "interrupt" or "interrupts"
                r'\binterrupt target\b',       # "interrupt target"
                r'\binterrupt that foe\b',     # "interrupt that foe"
                r'\binterruption effect\b',    # Has interruption effect
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    # Make sure it's not just "easily interrupted" (trap vulnerability)
                    if "easily interrupted" in desc and "interrupts" not in desc:
                        continue
                    return True

            return False

        @staticmethod
        def IsConditionalInterrupt(skill_id: int) -> bool:
            """
            Purpose: Check if the interrupt only triggers under certain conditions.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if interrupt requires a condition (e.g., "if target has Deep Wound").
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            # Check for conditional interrupt patterns
            conditional_patterns = [
                r'if.*interrupt',              # "if X, interrupts"
                r'interrupt.*if',              # "interrupts if X"
                r'when.*interrupt',            # "when X, interrupts"
            ]

            for pattern in conditional_patterns:
                if re.search(pattern, desc):
                    return True

            return False

        @staticmethod
        def GetInterruptCondition(skill_id: int) -> str:
            """
            Purpose: Get the condition required for interrupt to trigger.

            Args:
                skill_id: The skill ID to check.

            Returns:
                Description of the condition, or empty string if unconditional.
            """
            if not SkillProperties.Interrupt.IsConditionalInterrupt(skill_id):
                return ""

            desc = Skill.GetConciseDescription(skill_id).lower()

            # Common conditions
            conditions = {
                "deep wound": "Target must have Deep Wound",
                "critical hit": "Must land a critical hit",
                "casting a spell": "Target must be casting a spell",
                "using a skill": "Target must be using a skill",
                "cracked armor": "Target must have Cracked Armor",
            }

            for keyword, condition_desc in conditions.items():
                if keyword in desc:
                    return condition_desc

            return "Conditional (see description)"

    # =========================================================================
    # Knockdown Detection
    # =========================================================================

    class Knockdown:
        """Methods for detecting knockdown-related skill properties."""

        @staticmethod
        def CausesKnockdown(skill_id: int) -> bool:
            """
            Purpose: Check if a skill causes knockdown.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill can knock down targets.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            patterns = [
                r'\bknocked down\b',           # "knocked down"
                r'\bknockdown\b',              # "knockdown"
                r'\bknock down\b',             # "knock down"
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    # Make sure it's causing knockdown, not requiring it
                    # "if target is knocked down" is a requirement, not an effect
                    if re.search(r'if.*knocked down', desc):
                        # Check if there's also a knockdown effect
                        if re.search(r'(and|also).*knocked down|knocked down.*for', desc):
                            return True
                        continue
                    return True

            return False

        @staticmethod
        def GetKnockdownDuration(skill_id: int) -> Tuple[float, float]:
            """
            Purpose: Get the knockdown duration at 0 and max attribute.

            Args:
                skill_id: The skill ID to check.

            Returns:
                Tuple of (duration_at_0, duration_at_max) in seconds.
                Returns (0, 0) if not a knockdown skill or duration not found.
            """
            if not SkillProperties.Knockdown.CausesKnockdown(skill_id):
                return (0.0, 0.0)

            desc = Skill.GetDescription(skill_id)

            # Look for duration pattern like "[!2...3...4!] seconds"
            match = re.search(r'\[!(\d+)\.\.\.(\d+)\.\.\.(\d+)!\]\s*second', desc)
            if match:
                return (float(match.group(1)), float(match.group(3)))

            # Fixed duration pattern like "2 seconds"
            match = re.search(r'knocked down.*?(\d+)\s*second', desc.lower())
            if match:
                duration = float(match.group(1))
                return (duration, duration)

            # Default knockdown is typically 2-3 seconds
            return (2.0, 3.0)

    # =========================================================================
    # Condition Detection (Bleeding, Poison, etc.)
    # =========================================================================

    class Conditions:
        """Methods for detecting condition-related skill properties."""

        # All conditions in Guild Wars
        ALL_CONDITIONS = [
            "bleeding", "blind", "burning", "cracked armor", "crippled",
            "dazed", "deep wound", "disease", "poison", "weakness"
        ]

        @staticmethod
        def AppliesCondition(skill_id: int, condition: str = None) -> bool:
            """
            Purpose: Check if a skill applies a condition.

            Args:
                skill_id: The skill ID to check.
                condition: Specific condition to check for (optional).
                          If None, checks for any condition.

            Returns:
                True if the skill applies the specified condition (or any if None).
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            if condition:
                condition = condition.lower()
                # Check for "inflicts X" or "causes X" or just the condition name with duration
                patterns = [
                    rf'\binflicts?\s+{condition}\b',
                    rf'\bcauses?\s+{condition}\b',
                    rf'\b{condition}\s+condition\b',
                    rf'\b{condition}\s*\(\s*\d+',  # "bleeding (10 seconds)"
                ]
                for pattern in patterns:
                    if re.search(pattern, desc):
                        return True
                return False

            # Check for any condition
            for cond in SkillProperties.Conditions.ALL_CONDITIONS:
                if SkillProperties.Conditions.AppliesCondition(skill_id, cond):
                    return True

            return False

        @staticmethod
        def GetAppliedConditions(skill_id: int) -> List[str]:
            """
            Purpose: Get list of all conditions this skill applies.

            Args:
                skill_id: The skill ID to check.

            Returns:
                List of condition names applied by this skill.
            """
            conditions = []
            for cond in SkillProperties.Conditions.ALL_CONDITIONS:
                if SkillProperties.Conditions.AppliesCondition(skill_id, cond):
                    conditions.append(cond)
            return conditions

        @staticmethod
        def RemovesCondition(skill_id: int, condition: str = None) -> bool:
            """
            Purpose: Check if a skill removes conditions.

            Args:
                skill_id: The skill ID to check.
                condition: Specific condition to check for (optional).

            Returns:
                True if the skill removes the specified condition (or any if None).
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            removal_patterns = [
                r'removes?\s+\d*\s*conditions?',   # "remove 1 condition"
                r'cure\s+condition',               # "cure condition"
                r'cleanse',                        # "cleanse"
            ]

            if condition:
                removal_patterns.append(rf'removes?\s+{condition.lower()}')

            for pattern in removal_patterns:
                if re.search(pattern, desc):
                    return True

            return False

    # =========================================================================
    # Hex Detection
    # =========================================================================

    class Hexes:
        """Methods for detecting hex-related skill properties."""

        @staticmethod
        def AppliesHex(skill_id: int) -> bool:
            """
            Purpose: Check if a skill applies a hex.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill is a hex.
            """
            return Skill.Flags.IsHex(skill_id)

        @staticmethod
        def RemovesHex(skill_id: int) -> bool:
            """
            Purpose: Check if a skill removes hexes.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill removes hexes.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            patterns = [
                r'removes?\s+\d*\s*hexe?s?',   # "remove 1 hex"
                r'remove\s+a\s+hex',           # "remove a hex"
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    return True

            return False

        @staticmethod
        def IsDegenerationHex(skill_id: int) -> bool:
            """
            Purpose: Check if a hex causes health degeneration.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the hex causes health degen.
            """
            if not Skill.Flags.IsHex(skill_id):
                return False

            desc = Skill.GetConciseDescription(skill_id).lower()
            return "health degeneration" in desc or "degen" in desc

    # =========================================================================
    # Healing Detection
    # =========================================================================

    class Healing:
        """Methods for detecting healing-related skill properties."""

        @staticmethod
        def IsHealingSkill(skill_id: int) -> bool:
            """
            Purpose: Check if a skill provides healing.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill heals.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()
            target_type = Skill.Target.GetTargetType(skill_id)

            # Must affect allies (not foes)
            if target_type & Skill.Target.FOE and not (target_type & Skill.Target.ALLY):
                return False

            healing_patterns = [
                r'\bheals?\b',                 # "heal" or "heals"
                r'\bhealing\b',                # "healing"
                r'\bgain\s+\d+.*health\b',     # "gain X health"
                r'\brestore.*health\b',        # "restore health"
                r'\bregain.*health\b',         # "regain health"
            ]

            for pattern in healing_patterns:
                if re.search(pattern, desc):
                    return True

            return False

        @staticmethod
        def IsResurrectionSkill(skill_id: int) -> bool:
            """
            Purpose: Check if a skill can resurrect.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill can resurrect dead allies.
            """
            target_type = Skill.Target.GetTargetType(skill_id)

            # Must be able to target dead allies
            if target_type & Skill.Target.DEAD:
                return True

            desc = Skill.GetConciseDescription(skill_id).lower()
            return "resurrect" in desc or "returned to life" in desc

    # =========================================================================
    # Buff/Enchantment Detection
    # =========================================================================

    class Buffs:
        """Methods for detecting buff-related skill properties."""

        @staticmethod
        def IsBuffSkill(skill_id: int) -> bool:
            """
            Purpose: Check if a skill provides a beneficial effect (buff).

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill is a buff (enchantment, stance, etc. that helps).
            """
            _, type_name = Skill.GetType(skill_id)
            target_type = Skill.Target.GetTargetType(skill_id)

            # Traditional buff types
            buff_types = ["Enchantment", "Stance", "Form", "Preparation",
                         "Glyph", "Shout", "Chant", "EchoRefrain"]

            if type_name in buff_types:
                # Make sure it's not targeting enemies (some enchants are offensive)
                if target_type == 0 or target_type == Skill.Target.SELF:
                    return True
                if (target_type & Skill.Target.ALLY) and not (target_type & Skill.Target.FOE):
                    return True

            # Check for "Skill" or "Skill2" type self-buffs (e.g., Critical Eye)
            # These are self-targeting skills with a duration that provide beneficial effects
            # Note: Critical Eye is type "Skill2" (ID 16), not "Skill" (ID 10)
            if type_name in ("Skill", "Skill2"):
                # Must affect self (can be combined with other targets like Foe for attack buffs)
                # Use bitmask check since target_type can be combinations like Self/Foe (5)
                affects_self = (target_type == 0 or
                               (target_type & Skill.Target.SELF) != 0)
                if affects_self:
                    # Check if it has a duration (indicates it's a buff, not an attack)
                    duration_0, duration_15 = Skill.Attribute.GetDuration(skill_id)
                    if duration_0 > 0 or duration_15 > 0:
                        return True

                    # Also check description for duration pattern (some skills store duration differently)
                    desc = Skill.GetConciseDescription(skill_id).lower()
                    # Look for duration patterns like:
                    # - "for [!10...30...35!] seconds"
                    # - "( [!10...30...35!] seconds.)"
                    # - "for 10 seconds"
                    duration_patterns = [
                        r'for\s+\[',           # "for [!X...Y...Z!]"
                        r'for\s+\d+\s*second', # "for X seconds"
                        r'\(\s*\[',            # "( [!X...Y...Z!] seconds.)"
                        r'\(\s*\d+\s*second',  # "(X seconds)"
                    ]
                    has_duration = any(re.search(p, desc) for p in duration_patterns)
                    if has_duration:
                        # Make sure it's not an ATTACK SKILL (starts with "attack" or "X attack")
                        # But allow buffs that mention "when attacking" or "while attacking"
                        # e.g., Critical Eye says "when attacking" but is not an attack skill
                        is_attack_skill = (
                            desc.startswith("attack") or
                            re.search(r'^(melee|bow|axe|sword|hammer|dagger|scythe|spear|pet)\s+attack', desc) or
                            "strike for" in desc or
                            "strikes for" in desc
                        )
                        if not is_attack_skill:
                            return True

            return False

        @staticmethod
        def DebugIsBuffSkill(skill_id: int) -> str:
            """
            Debug version of IsBuffSkill - returns detailed reasoning.

            Args:
                skill_id: The skill ID to check.

            Returns:
                String with detailed debug info about why skill is/isn't a buff.
            """
            lines = []
            type_id, type_name = Skill.GetType(skill_id)
            target_type = Skill.Target.GetTargetType(skill_id)
            target_name = Skill.Target.GetTargetTypeName(skill_id)

            lines.append(f"Skill ID: {skill_id}")
            lines.append(f"Type: {type_name} ({type_id})")
            lines.append(f"Target: {target_name} ({target_type})")

            buff_types = ["Enchantment", "Stance", "Form", "Preparation",
                         "Glyph", "Shout", "Chant", "EchoRefrain"]

            if type_name in buff_types:
                lines.append(f"Type '{type_name}' is in buff_types")
                if target_type == 0 or target_type == Skill.Target.SELF:
                    lines.append("-> BUFF (self-target buff type)")
                    return "\n".join(lines)
                if (target_type & Skill.Target.ALLY) and not (target_type & Skill.Target.FOE):
                    lines.append("-> BUFF (ally-only buff type)")
                    return "\n".join(lines)
                lines.append("Targets foes, not a buff")

            if type_name in ("Skill", "Skill2"):
                lines.append(f"Type is '{type_name}', checking self-buff logic...")
                affects_self = (target_type == 0 or
                               (target_type & Skill.Target.SELF) != 0)
                lines.append(f"Affects self: {affects_self}")

                if affects_self:
                    duration_0, duration_15 = Skill.Attribute.GetDuration(skill_id)
                    lines.append(f"Duration from game data: {duration_0} / {duration_15}")

                    if duration_0 > 0 or duration_15 > 0:
                        lines.append("-> BUFF (has game duration)")
                        return "\n".join(lines)

                    desc = Skill.GetConciseDescription(skill_id).lower()
                    lines.append(f"Description: {desc[:100]}...")

                    duration_patterns = [
                        r'for\s+\[',
                        r'for\s+\d+\s*second',
                        r'\(\s*\[',
                        r'\(\s*\d+\s*second',
                    ]
                    pattern_matches = [(p, bool(re.search(p, desc))) for p in duration_patterns]
                    lines.append(f"Pattern matches: {pattern_matches}")
                    has_duration = any(m for _, m in pattern_matches)

                    if has_duration:
                        is_attack_skill = (
                            desc.startswith("attack") or
                            re.search(r'^(melee|bow|axe|sword|hammer|dagger|scythe|spear|pet)\s+attack', desc) or
                            "strike for" in desc or
                            "strikes for" in desc
                        )
                        lines.append(f"Is attack skill: {is_attack_skill}")
                        if not is_attack_skill:
                            lines.append("-> BUFF (desc has duration, not attack)")
                            return "\n".join(lines)
                        lines.append("Blocked: is attack skill")
                    else:
                        lines.append("No duration pattern matched")
                else:
                    lines.append("Does not affect self")
            else:
                lines.append(f"Type '{type_name}' not in buff_types and not 'Skill'/'Skill2'")

            lines.append("-> NOT A BUFF")
            return "\n".join(lines)

        @staticmethod
        def IsSelfBuff(skill_id: int) -> bool:
            """
            Purpose: Check if a skill is a self-only buff.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill only affects self.
            """
            if not SkillProperties.Buffs.IsBuffSkill(skill_id):
                return False

            target_type = Skill.Target.GetTargetType(skill_id)
            return target_type == 0 or target_type == Skill.Target.SELF

        @staticmethod
        def RemovesEnchantment(skill_id: int) -> bool:
            """
            Purpose: Check if a skill removes enchantments.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill removes enchantments from targets.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            patterns = [
                r'removes?\s+\d*\s*enchantments?',  # "remove 1 enchantment"
                r'strip\s+enchantment',              # "strip enchantment"
                r'lose\s+\d*\s*enchantments?',       # "lose 1 enchantment"
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    return True

            return False

    # =========================================================================
    # Conditional Effects Detection
    # =========================================================================

    class ConditionalEffects:
        """Methods for detecting conditional/bonus effects on skills."""

        @staticmethod
        def HasConditionalEffect(skill_id: int) -> bool:
            """
            Purpose: Check if a skill has conditional bonus effects.

            Examples: Unnatural Signet (bonus vs mesmer hexes),
                     Discord (bonus vs hex+condition), etc.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill has conditional bonuses.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            conditional_patterns = [
                r'\bif\s+target\b',                # "if target has..."
                r'\bif\s+foe\b',                   # "if foe is..."
                r'\bif\s+this\s+attack\b',         # "if this attack hits..."
                r'\bif\s+you\b',                   # "if you are..."
                r'\bwhen\s+target\b',              # "when target..."
                r'\bagainst\s+foes?\s+(with|that)\b',  # "against foes with..."
                r'\bwhile\s+',                     # "while X..."
                r'\b(more|extra|additional)\s+damage\s+if\b',  # "more damage if"
            ]

            for pattern in conditional_patterns:
                if re.search(pattern, desc):
                    return True

            return False

        @staticmethod
        def GetConditionalRequirements(skill_id: int) -> List[str]:
            """
            Purpose: Get the conditions required for bonus effects.

            Args:
                skill_id: The skill ID to check.

            Returns:
                List of conditions/requirements for bonus effects.
            """
            if not SkillProperties.ConditionalEffects.HasConditionalEffect(skill_id):
                return []

            desc = Skill.GetConciseDescription(skill_id).lower()
            requirements = []

            # Common conditional requirements
            condition_map = {
                r'if target.*hexed': "Target must be hexed",
                r'if target.*enchanted': "Target must be enchanted",
                r'if target.*condition': "Target must have a condition",
                r'if target.*bleeding': "Target must be bleeding",
                r'if target.*poisoned': "Target must be poisoned",
                r'if target.*burning': "Target must be burning",
                r'if target.*deep wound': "Target must have Deep Wound",
                r'if target.*knocked down': "Target must be knocked down",
                r'if target.*moving': "Target must be moving",
                r'if target.*attacking': "Target must be attacking",
                r'if target.*casting': "Target must be casting",
                r'if you.*enchanted': "You must be enchanted",
                r'if you.*moving': "You must be moving",
                r'while attacking': "Must be attacking",
                r'while moving': "Must be moving",
                r'mesmer hex': "Target must have a Mesmer hex",
                r'necromancer hex': "Target must have a Necromancer hex",
            }

            for pattern, requirement in condition_map.items():
                if re.search(pattern, desc):
                    requirements.append(requirement)

            return requirements

        @staticmethod
        def HasBonusDamage(skill_id: int) -> bool:
            """
            Purpose: Check if a skill has conditional bonus damage.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill deals extra damage under certain conditions.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            patterns = [
                r'\+.*damage\s+if\b',              # "+X damage if"
                r'deals?\s+\+?\s*\d+.*extra\s+damage',  # "deals extra damage"
                r'(more|additional|extra)\s+damage',    # "more damage"
                r'double\s+damage',                # "double damage"
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    return True

            return False

    # =========================================================================
    # Damage Type Detection
    # =========================================================================

    class Damage:
        """Methods for detecting damage-related skill properties."""

        DAMAGE_TYPES = ["fire", "cold", "lightning", "earth", "holy",
                       "dark", "chaos", "piercing", "slashing", "blunt"]

        @staticmethod
        def DealsDamage(skill_id: int) -> bool:
            """
            Purpose: Check if a skill deals damage.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill deals damage.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            patterns = [
                r'\bdeals?\s+\d+',              # "deal X"
                r'\bdamage\b',                  # "damage"
                r'\bstrikes?\s+for\b',          # "strike for"
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    return True

            return False

        @staticmethod
        def GetDamageType(skill_id: int) -> str:
            """
            Purpose: Get the damage type of a skill.

            Args:
                skill_id: The skill ID to check.

            Returns:
                Damage type name, or "physical" if not elemental.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            for damage_type in SkillProperties.Damage.DAMAGE_TYPES:
                if f"{damage_type} damage" in desc:
                    return damage_type

            # Check profession for default damage type
            _, profession = Skill.GetProfession(skill_id)
            if profession == "Elementalist":
                # Check for element keywords
                if "fire" in desc or "burning" in desc:
                    return "fire"
                if "cold" in desc or "water" in desc or "ice" in desc:
                    return "cold"
                if "lightning" in desc or "thunder" in desc:
                    return "lightning"
                if "earth" in desc or "stone" in desc:
                    return "earth"

            return "physical"

        @staticmethod
        def IsAoE(skill_id: int) -> bool:
            """
            Purpose: Check if a skill deals area damage.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill has an area effect.
            """
            # Check AoE range from skill data
            aoe_range = Skill.Data.GetAoERange(skill_id)
            if aoe_range > 0:
                return True

            desc = Skill.GetConciseDescription(skill_id).lower()

            aoe_patterns = [
                r'\badjacent\b',               # "adjacent foes"
                r'\bnearby\b',                 # "nearby"
                r'\bin the area\b',            # "in the area"
                r'\ball foes\b',               # "all foes"
                r'\barea\b',                   # "area"
            ]

            for pattern in aoe_patterns:
                if re.search(pattern, desc):
                    return True

            return False

    # =========================================================================
    # Skill Classification Helpers
    # =========================================================================

    class Classification:
        """High-level skill classification methods."""

        @staticmethod
        def GetSkillRole(skill_id: int) -> str:
            """
            Purpose: Get the primary role/function of a skill.

            Args:
                skill_id: The skill ID to check.

            Returns:
                One of: "interrupt", "knockdown", "damage", "heal", "buff",
                       "hex", "condition", "enchant_removal", "hex_removal",
                       "condition_removal", "resurrection", "utility"
            """
            # Check in priority order
            if SkillProperties.Healing.IsResurrectionSkill(skill_id):
                return "resurrection"

            if SkillProperties.Interrupt.CausesInterrupt(skill_id):
                return "interrupt"

            if SkillProperties.Knockdown.CausesKnockdown(skill_id):
                return "knockdown"

            if SkillProperties.Buffs.RemovesEnchantment(skill_id):
                return "enchant_removal"

            if SkillProperties.Hexes.RemovesHex(skill_id):
                return "hex_removal"

            if SkillProperties.Conditions.RemovesCondition(skill_id):
                return "condition_removal"

            if SkillProperties.Healing.IsHealingSkill(skill_id):
                return "heal"

            if SkillProperties.Buffs.IsBuffSkill(skill_id):
                return "buff"

            if SkillProperties.Hexes.AppliesHex(skill_id):
                return "hex"

            if SkillProperties.Conditions.AppliesCondition(skill_id):
                return "condition"

            if SkillProperties.Damage.DealsDamage(skill_id):
                return "damage"

            return "utility"

        @staticmethod
        def GetSkillRoles(skill_id: int) -> List[str]:
            """
            Purpose: Get all roles/functions of a skill (skills can have multiple).

            Args:
                skill_id: The skill ID to check.

            Returns:
                List of roles this skill fulfills.
            """
            roles = []

            if SkillProperties.Healing.IsResurrectionSkill(skill_id):
                roles.append("resurrection")

            if SkillProperties.Interrupt.CausesInterrupt(skill_id):
                roles.append("interrupt")

            if SkillProperties.Knockdown.CausesKnockdown(skill_id):
                roles.append("knockdown")

            if SkillProperties.Buffs.RemovesEnchantment(skill_id):
                roles.append("enchant_removal")

            if SkillProperties.Hexes.RemovesHex(skill_id):
                roles.append("hex_removal")

            if SkillProperties.Conditions.RemovesCondition(skill_id):
                roles.append("condition_removal")

            if SkillProperties.Healing.IsHealingSkill(skill_id):
                roles.append("heal")

            if SkillProperties.Buffs.IsBuffSkill(skill_id):
                roles.append("buff")

            if SkillProperties.Hexes.AppliesHex(skill_id):
                roles.append("hex")

            if SkillProperties.Conditions.AppliesCondition(skill_id):
                roles.append("condition")

            if SkillProperties.Damage.DealsDamage(skill_id):
                roles.append("damage")

            if not roles:
                roles.append("utility")

            return roles

        @staticmethod
        def IsOffensiveSkill(skill_id: int) -> bool:
            """
            Purpose: Check if a skill is primarily offensive.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill is used offensively against enemies.
            """
            target_type = Skill.Target.GetTargetType(skill_id)

            # Must affect enemies
            if not (target_type & Skill.Target.FOE):
                return False

            # Check for offensive properties
            return (SkillProperties.Damage.DealsDamage(skill_id) or
                    SkillProperties.Interrupt.CausesInterrupt(skill_id) or
                    SkillProperties.Knockdown.CausesKnockdown(skill_id) or
                    SkillProperties.Hexes.AppliesHex(skill_id) or
                    SkillProperties.Conditions.AppliesCondition(skill_id) or
                    SkillProperties.Buffs.RemovesEnchantment(skill_id))

        @staticmethod
        def IsDefensiveSkill(skill_id: int) -> bool:
            """
            Purpose: Check if a skill is primarily defensive.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill is used defensively to help allies.
            """
            return (SkillProperties.Healing.IsHealingSkill(skill_id) or
                    SkillProperties.Healing.IsResurrectionSkill(skill_id) or
                    SkillProperties.Hexes.RemovesHex(skill_id) or
                    SkillProperties.Conditions.RemovesCondition(skill_id) or
                    SkillProperties.Buffs.IsBuffSkill(skill_id))

        @staticmethod
        def IsSupportSkill(skill_id: int) -> bool:
            """
            Purpose: Check if a skill supports allies (healing, buffs, removal).

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill supports allies.
            """
            target_type = Skill.Target.GetTargetType(skill_id)

            # Must be able to affect allies or self
            if target_type & Skill.Target.FOE and not (target_type & Skill.Target.ALLY):
                if target_type != Skill.Target.SELF and target_type != 0:
                    return False

            return (SkillProperties.Healing.IsHealingSkill(skill_id) or
                    SkillProperties.Buffs.IsBuffSkill(skill_id) or
                    SkillProperties.Hexes.RemovesHex(skill_id) or
                    SkillProperties.Conditions.RemovesCondition(skill_id))

    # =========================================================================
    # Defense Detection (Blocking, Evasion, Damage Reduction)
    # =========================================================================

    class Defense:
        """Methods for detecting defensive skill properties."""

        @staticmethod
        def IsBlockingSkill(skill_id: int) -> bool:
            """
            Purpose: Check if a skill provides blocking.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill blocks attacks.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            patterns = [
                r'\bblocks?\b',                # "block" or "blocks"
                r'\bblocking\b',               # "blocking"
                r'\b75%\s*chance\b',           # "75% chance" (common block chance)
                r'\b50%\s*chance\b',           # "50% chance"
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    # Make sure it's about blocking attacks, not "blocked" as in prevented
                    if "block" in desc and ("attack" in desc or "melee" in desc or "projectile" in desc):
                        return True
                    # Stances that mention blocking
                    if Skill.Flags.IsStance(skill_id) and "block" in desc:
                        return True

            return False

        @staticmethod
        def BlocksMelee(skill_id: int) -> bool:
            """
            Purpose: Check if a skill specifically blocks melee attacks.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill blocks melee attacks.
            """
            if not SkillProperties.Defense.IsBlockingSkill(skill_id):
                return False

            desc = Skill.GetConciseDescription(skill_id).lower()
            return "melee" in desc or ("attack" in desc and "projectile" not in desc)

        @staticmethod
        def BlocksProjectiles(skill_id: int) -> bool:
            """
            Purpose: Check if a skill specifically blocks projectile attacks.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill blocks projectiles/ranged attacks.
            """
            if not SkillProperties.Defense.IsBlockingSkill(skill_id):
                return False

            desc = Skill.GetConciseDescription(skill_id).lower()
            return "projectile" in desc or "ranged" in desc or "arrow" in desc

        @staticmethod
        def IsEvasionSkill(skill_id: int) -> bool:
            """
            Purpose: Check if a skill provides evasion (chance to evade/dodge).

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill provides evasion.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            patterns = [
                r'\bevade\b',                  # "evade"
                r'\bevasion\b',                # "evasion"
                r'\bdodge\b',                  # "dodge"
                r'\bmiss\b',                   # "attacks miss"
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    return True

            return False

        @staticmethod
        def ProvidesDamageReduction(skill_id: int) -> bool:
            """
            Purpose: Check if a skill reduces incoming damage.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill reduces damage taken.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            patterns = [
                r'damage\s+reduction',         # "damage reduction"
                r'reduce.*damage',             # "reduce damage"
                r'takes?\s+\d+%?\s*less\s+damage',  # "take X% less damage"
                r'\+\d+\s*armor',              # "+X armor"
                r'armor\s+bonus',              # "armor bonus"
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    return True

            return False

        @staticmethod
        def PreventsEnchanting(skill_id: int) -> bool:
            """
            Purpose: Check if a skill prevents the target from being enchanted.

            This is critical for spike detection - skills like Shadow Shroud
            prevent enchanting, signaling an incoming spike.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill prevents enchanting.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            patterns = [
                r'cannot\s+be\s+enchanted',    # "cannot be enchanted"
                r'prevent.*enchant',           # "prevents enchanting"
                r'enchantments?\s+fail',       # "enchantments fail"
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    return True

            return False

        @staticmethod
        def IsAntiMelee(skill_id: int) -> bool:
            """
            Purpose: Check if a skill counters melee attackers.

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill is effective against melee.
            """
            desc = Skill.GetConciseDescription(skill_id).lower()

            # Blind counters melee
            if SkillProperties.Conditions.AppliesCondition(skill_id, "blind"):
                return True

            # Block melee
            if SkillProperties.Defense.BlocksMelee(skill_id):
                return True

            # Other anti-melee patterns
            patterns = [
                r'melee\s+attack.*fail',
                r'when\s+struck.*damage',      # Retaliation effects
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    return True

            return False

        @staticmethod
        def IsAntiCaster(skill_id: int) -> bool:
            """
            Purpose: Check if a skill counters casters (spellcasters).

            Args:
                skill_id: The skill ID to check.

            Returns:
                True if the skill is effective against casters.
            """
            # Dazed counters casters
            if SkillProperties.Conditions.AppliesCondition(skill_id, "dazed"):
                return True

            # Interrupts counter casters
            if SkillProperties.Interrupt.CausesInterrupt(skill_id):
                desc = Skill.GetConciseDescription(skill_id).lower()
                if "spell" in desc or "casting" in desc:
                    return True

            desc = Skill.GetConciseDescription(skill_id).lower()

            patterns = [
                r'spells?\s+fail',             # "spells fail"
                r'cannot\s+cast',              # "cannot cast"
                r'spell.*disabled',            # "spells disabled"
                r'interrupt.*spell',           # "interrupt spell"
            ]

            for pattern in patterns:
                if re.search(pattern, desc):
                    return True

            return False

        @staticmethod
        def GetDefenseType(skill_id: int) -> str:
            """
            Purpose: Get the primary defense type of a skill.

            Args:
                skill_id: The skill ID to check.

            Returns:
                One of: "block", "evasion", "damage_reduction", "anti_melee",
                       "anti_caster", "none"
            """
            if SkillProperties.Defense.IsBlockingSkill(skill_id):
                return "block"
            if SkillProperties.Defense.IsEvasionSkill(skill_id):
                return "evasion"
            if SkillProperties.Defense.ProvidesDamageReduction(skill_id):
                return "damage_reduction"
            if SkillProperties.Defense.IsAntiMelee(skill_id):
                return "anti_melee"
            if SkillProperties.Defense.IsAntiCaster(skill_id):
                return "anti_caster"

            return "none"

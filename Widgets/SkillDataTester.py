"""
SkillData Tester - Test and Demo Widget for Skill/Skillbar Functions
=====================================================================

Author: Paul (HamsterSerious)

This widget visualizes Skill and Skillbar data and demonstrates the API.
Use it as a reference for implementing skill tracking in your own bots.

Features:
---------
1. Skillbar Tab: View current skillbar with recharge/adrenaline states
2. Skill Info Tab: Query detailed skill data by ID or name
3. Skill Properties Tab: Test SkillProperties classification (interrupts, KD, conditions, etc.)
4. Weapon Sets Tab: View equipped weapon sets with damage types and mods
5. Item Weapons Tab: Base damage, attack speed, DPS reference for all weapon types
6. Template Tab: Test template encode/decode functions
7. Hero Skills Tab: View hero skillbars
8. Reference Tab: Quick reference for target/combo/weapon/range constants

================================================================================
EXAMPLE CODE PATTERNS - Copy these into your own bots!
================================================================================

1. Check if a skill is ready to use:
-----------------------------------
```python
from Py4GWCoreLib import SkillBar

# Check if skill in slot 1 is ready
if SkillBar.IsSkillReady(1):
    SkillBar.UseSkill(1, target_id)

# Get detailed reason why skill can't be used (structured result)
result = SkillBar.GetSkillUsability(1)
if result.status == SkillUsability.READY:
    print("Skill is ready!")
elif result.status == SkillUsability.RECHARGING:
    print(f"Recharging: {result.value:.1f}s remaining")

# Combined check (recharge, energy, adrenaline, disabled)
if SkillBar.CanUseSkill(1):
    SkillBar.UseSkill(1)
```

2. Get skill recharge/adrenaline:
---------------------------------
```python
from Py4GWCoreLib import SkillBar

# Get remaining recharge in milliseconds
remaining_ms = SkillBar.GetSkillRechargeRemaining(1)
print(f"Skill 1 recharges in {remaining_ms / 1000:.1f}s")

# Get adrenaline
adrenaline_a, adrenaline_b = SkillBar.GetSkillAdrenaline(1)
```

3. Template encode/decode:
--------------------------
```python
from Py4GWCoreLib import SkillBar

# Decode a template string
template_data = SkillBar.DecodeTemplate("OgEUcZrSXzlYAVzlVAYzlZAA")
if template_data:
    print(f"Primary: {template_data['primary']}")
    print(f"Secondary: {template_data['secondary']}")
    print(f"Skills: {template_data['skills']}")
    print(f"Attributes: {template_data['attributes']}")

# Get current build as template
my_template = SkillBar.GetCurrentTemplate()
print(f"Current build: {my_template}")

# Encode a custom template
template = SkillBar.EncodeTemplate(
    primary=1,  # Warrior
    secondary=5,  # Ranger
    skills=[123, 456, 789, 0, 0, 0, 0, 0],
    attributes=[(0, 12), (1, 9)]  # (attr_id, points)
)
```

4. Skill target type helpers:
-----------------------------
```python
from Py4GWCoreLib import Skill

# Check what a skill can target
print(f"Target type: {Skill.Target.GetTargetTypeName(skill_id)}")  # "Foe", "Ally", "Self/Ally", etc.

# Check specific target capabilities
if Skill.Target.AffectsFoe(skill_id):
    print("Can target enemies")
if Skill.Target.RequiresTarget(skill_id):
    print("Needs a target selected")
```

5. Assassin combo chain helpers:
--------------------------------
```python
from Py4GWCoreLib import Skill

if Skill.Combo.IsLeadAttack(skill_id):
    print("This is a Lead Attack - use it first!")
if Skill.Combo.RequiresLead(skill_id):
    print("Need to use a Lead Attack before this")
print(f"Combo type: {Skill.Combo.GetComboTypeName(skill_id)}")
```

6. Weapon requirement helpers:
------------------------------
```python
from Py4GWCoreLib import Skill

if Skill.Weapon.HasWeaponRequirement(skill_id):
    print(f"Requires: {Skill.Weapon.GetWeaponRequirementName(skill_id)}")
if Skill.Weapon.RequiresMelee(skill_id):
    print("Need a melee weapon equipped")
```

7. Range helpers:
-----------------
```python
from Py4GWCoreLib import Skill

print(f"Range type: {Skill.Range.GetRangeType(skill_id)}")  # "Touch", "Half Range", "Full Range"
print(f"Range: {Skill.Range.GetRangeInUnits(skill_id)} units")

# Check if target is in range
distance = 500  # game units
if Skill.Range.IsInRange(skill_id, distance):
    print("Target is in range!")
```

8. Skill Properties (what a skill DOES):
-----------------------------------------
```python
from Py4GWCoreLib import SkillProperties

# Classification
role = SkillProperties.Classification.GetSkillRole(skill_id)  # "interrupt", "damage", "heal", etc.
roles = SkillProperties.Classification.GetSkillRoles(skill_id)  # All roles

# Interrupt detection
if SkillProperties.Interrupt.CausesInterrupt(skill_id):
    print("This skill interrupts!")

# Condition detection
conditions = SkillProperties.Conditions.GetAppliedConditions(skill_id)
print(f"Applies: {', '.join(conditions)}")

# Buff detection
if SkillProperties.Buffs.IsBuffSkill(skill_id):
    print("This is a buff")

# Defense detection
if SkillProperties.Defense.IsBlockingSkill(skill_id):
    print(f"Defense type: {SkillProperties.Defense.GetDefenseType(skill_id)}")
```

9. Weapon Sets (native inventory):
-----------------------------------
```python
from Py4GWCoreLib import Inventory

# Get active weapon set
active = Inventory.GetActiveWeaponSet()
if active:
    print(f"Weapon damage type: {active.weapon_damage_type}")

# Find weapon set for Conjure Lightning
ws = Inventory.GetConjureWeaponSet("Conjure Lightning")
if ws:
    print(f"Use Set {ws.set_index + 1}")

# Find defensive set (shield)
shield_set = Inventory.GetDefensiveWeaponSet()
```

10. Item Weapon Stats:
----------------------
```python
from Py4GWCoreLib import Item

# Get base damage for a weapon type
min_dmg, max_dmg = Item.Weapon.GetBaseDamageRange("Sword")
print(f"Sword: {min_dmg}-{max_dmg}")

# Get DPS
dps = Item.Weapon.GetDPS("Sword")
print(f"Sword DPS: {dps}")

# Check melee/ranged
if Item.Weapon.IsMelee("Sword"):
    print("Melee weapon")
```

See Also:
---------
- Skillbar.py: SkillBar class with live data and template functions
- Skill.py: Skill class with Target, Combo, Weapon, Range helpers
- SkillProperties.py: Skill behavior classification (interrupt, KD, conditions, etc.)
- Inventory.py: Weapon set methods
- Item.py: Item.Weapon for base damage stats
- CombatEvents.py: Combat state tracking (see CombatEventsTester widget)
"""

from Py4GWCoreLib import *
from Py4GWCoreLib.enums import Profession_Names, AttributeNames
from Py4GWCoreLib.Skillbar import SkillUsability
from Py4GWCoreLib.SkillProperties import SkillProperties
from typing import List, Optional, Dict
import time

MODULE_NAME = "SkillData Tester"

# ============================================================================
# State tracking for the UI
# ============================================================================

class TesterState:
    """Global state for the tester widget."""
    def __init__(self):
        # Skill info lookup
        self.lookup_skill_id = 0
        self.lookup_skill_name = ""

        # Template testing
        self.template_input = ""
        self.template_decode_result = None
        self.encode_primary = 1
        self.encode_secondary = 0
        self.encode_skills = [0] * 8
        self.encode_attributes = []
        self.encoded_result = ""

        # Hero selection
        self.selected_hero_index = 1

        # Skill Properties lookup
        self.properties_skill_id = 0

        # Weapon sets cache
        self.weapon_sets_cache = None
        self.weapon_sets_last_update = 0.0


state = TesterState()

# ============================================================================
# Helper Functions
# ============================================================================

def get_skill_name_safe(skill_id: int) -> str:
    """Get skill name safely."""
    if skill_id == 0:
        return "(Empty)"
    try:
        name = Skill.GetName(skill_id)
        return name if name else f"Skill#{skill_id}"
    except:
        return f"Skill#{skill_id}"


def get_profession_name(prof_id: int) -> str:
    """Get profession name from ID using existing enum dictionary."""
    return Profession_Names.get(prof_id, f"Unknown ({prof_id})")


def get_attribute_name(attr_id: int) -> str:
    """Get attribute name from ID using existing enum dictionary."""
    return AttributeNames.get(attr_id, f"Attr#{attr_id}")


def bool_colored(label: str, value: bool):
    """Draw a bool value with green/red color."""
    if value:
        PyImGui.text_colored(f"{label}: Yes", (100, 255, 100, 255))
    else:
        PyImGui.text(f"{label}: No")


def _get_attr_name(attr_id: int) -> str:
    """Resolve attribute ID to name."""
    return AttributeNames.get(attr_id, f"Attribute({attr_id})")


def _get_dmg_type_name(dmg_id: int) -> str:
    """Resolve damage type ID to name."""
    from Py4GWCoreLib.native_src.context.InventoryContext import DamageType as DT_Enum
    try:
        return DT_Enum(dmg_id).name
    except ValueError:
        return f"Unknown({dmg_id})"


def _format_mod(identifier: int, arg1: int, arg2: int, weapon_attr: Optional[int] = None) -> str:
    """Format a single item modifier into a human-readable string.

    Args:
        weapon_attr: The weapon's required attribute ID (from requirement mod),
                     used for HCT/HSR mods that apply to the weapon's attribute.
    """
    # Weapon base stats
    if identifier == 42920:  # Damage range
        return f"{arg2}-{arg1} damage"
    if identifier == 42936:  # Shield armor
        return f"Armor: {arg1}"
    if identifier == 9400:   # Damage type
        return f"Damage type: {_get_dmg_type_name(arg1)}"
    if identifier == 10136 or identifier == 32784:  # Requires
        return f"Requires {arg2} {_get_attr_name(arg1)}"

    # Inherent / upgrade mods
    if identifier == 8760:   # Damage +X%
        return f"Damage +{arg2}%"
    if identifier == 9032:   # Health +X
        return f"Health +{arg1}"
    if identifier == 8392:   # Energy regen
        return f"Energy regeneration -{arg2}"

    # Inscription: damage conditionals
    if identifier == 8808:   return f"Damage +{arg2}% (while Enchanted)"
    if identifier == 8872:   return f"Damage +{arg2}% (while in a Stance)"
    if identifier == 8792:   return f"Damage +{arg2}% (vs. Hexed foes)"
    if identifier == 8824:   return f"Damage +{arg2}% (while Health is above {arg1}%)"
    if identifier == 8840:   return f"Damage +{arg2}% (while Health is below {arg1}%)"
    if identifier == 8856:   return f"Damage +{arg2}% (while Hexed)"
    if identifier == 8216:   return f"Armor -{arg2} (while attacking)"

    # Energy inscriptions
    if identifier == 8920:   return f"Energy +{arg2}"
    if identifier == 8952:   return f"Energy +{arg2} (while Enchanted)"
    if identifier == 8968:   return f"Energy +{arg2} (while Health is above {arg1}%)"
    if identifier == 8984:   return f"Energy +{arg2} (while Health is below {arg1}%)"
    if identifier == 9000:   return f"Energy +{arg2} (while Hexed)"
    if identifier == 8376:   return f"Energy -{arg2}"
    if identifier == 26568:  return f"Energy +{arg1}"

    # Casting / recharge (these use the weapon's required attribute)
    attr_name = _get_attr_name(weapon_attr) if weapon_attr is not None else "[Weapon Attribute]"
    if identifier == 10248:  return f"Halves casting time of {attr_name} spells (Chance: {arg1}%)"
    if identifier == 8712:   return f"Halves casting time of spells (Chance: {arg1}%)"
    if identifier == 10280:  return f"Halves skill recharge of {attr_name} spells (Chance: {arg1}%)"
    if identifier == 9112:   return f"Halves skill recharge of spells (Chance: {arg1}%)"
    if identifier == 9128:   return f"Halves skill recharge of spells (Chance: {arg1}%)"

    # Armor inscriptions
    if identifier == 8456:   return f"Armor +{arg2}"
    if identifier == 8488:   return f"Armor +{arg2} (vs. elemental damage)"
    if identifier == 8536:   return f"Armor +{arg2} (vs. physical damage)"
    if identifier == 8568:   return f"Armor +{arg2} (while attacking)"
    if identifier == 8584:   return f"Armor +{arg2} (while casting)"
    if identifier == 8600:   return f"Armor +{arg2} (while Enchanted)"
    if identifier == 8616:   return f"Armor +{arg2} (while Health is above {arg1}%)"
    if identifier == 8632:   return f"Armor +{arg2} (while Health is below {arg1}%)"
    if identifier == 8648:   return f"Armor +{arg2} (while Hexed)"
    if identifier == 41240:  return f"Armor +{arg2} (vs. {_get_dmg_type_name(arg1)} damage)"

    # Damage reduction
    if identifier == 8312:   return f"Received physical damage -{arg2} (Chance: {arg1}%)"
    if identifier == 8328:   return f"Received physical damage -{arg2} (while Enchanted)"
    if identifier == 8344:   return f"Received physical damage -{arg2} (while Hexed)"
    if identifier == 8360:   return f"Received physical damage -{arg2} (while in a Stance)"

    # Health
    if identifier == 8408:   return f"Health +{arg2}"
    if identifier == 8424:   return f"Health regeneration -{arg2}"
    if identifier == 9064:   return f"Health +{arg1} (while Enchanted)"
    if identifier == 9080:   return f"Health +{arg1} (while Hexed)"
    if identifier == 9096:   return f"Health +{arg1} (while in a Stance)"

    # Weapon upgrades
    if identifier == 9144:   return f"Double adrenaline gain (Chance: {arg2}%)"
    if identifier == 9208:   return f"Armor penetration +{arg2}% (Chance: {arg1}%)"
    if identifier == 9496:   return f"Energy gain on hit: {arg2}"
    if identifier == 9512:   return f"Life draining: {arg1}"
    if identifier == 8888:   return f"Enchantments last {arg2}% longer"
    if identifier == 9240:   return f"{_get_attr_name(arg1)} +1 ({arg2}% chance while using skills)"
    if identifier == 10296:  return f"{attr_name} +1 (Chance: {arg1}%)"
    if identifier == 9320:   return f"Lengthens condition duration on foes by 33%"
    if identifier == 9336:   return f"Reduces condition duration on you by 20%"
    if identifier == 10328:  return f"Reduces condition duration on you by 20%"
    if identifier == 41544:  return f"Damage +{arg1}% (vs. Undead)"

    # Sale / salvage
    if identifier == 9720:   return "Improved sale value"
    if identifier == 9736:   return "Highly salvageable"

    # Fallback: show raw identifier
    return f"[0x{identifier:04X}] arg1={arg1} arg2={arg2}"


def _format_item_mods(item):
    """Draw all modifiers for an item as human-readable lines."""
    from ctypes import cast as ct_cast, POINTER as CT_POINTER
    from Py4GWCoreLib.native_src.context.InventoryContext import ItemModifierStruct

    if not item.mod_struct_ptr or item.mod_struct_size == 0:
        PyImGui.text("    (no modifiers)")
        return

    mod_array = ct_cast(item.mod_struct_ptr, CT_POINTER(ItemModifierStruct * item.mod_struct_size))

    # First pass: find the weapon's required attribute (from requirement mod 10136 or 32784)
    weapon_attr = None
    for mi in range(item.mod_struct_size):
        m = mod_array.contents[mi]
        if m.identifier in (10136, 32784):  # Requirement modifiers
            weapon_attr = m.arg1  # arg1 = attribute ID
            break

    # Second pass: format and display all mods
    for mi in range(item.mod_struct_size):
        m = mod_array.contents[mi]
        desc = _format_mod(m.identifier, m.arg1, m.arg2, weapon_attr)
        PyImGui.text(f"    {desc}")


# ============================================================================
# UI Drawing - Skillbar Tab
# ============================================================================

def draw_skillbar_tab():
    """Draw the skillbar tab showing current skills and their states."""
    PyImGui.text("Current Skillbar")
    PyImGui.separator()

    try:
        # Get basic skillbar info
        agent_id = SkillBar.GetAgentID()
        is_disabled = SkillBar.GetDisabled()
        is_casting = SkillBar.GetCasting()

        PyImGui.text(f"Agent ID: {agent_id}")

        # Status colors
        if is_disabled:
            PyImGui.text_colored("Status: DISABLED", (255, 100, 100, 255))
        elif is_casting:
            PyImGui.text_colored("Status: CASTING", (255, 200, 100, 255))
        else:
            PyImGui.text_colored("Status: READY", (100, 255, 100, 255))

        PyImGui.separator()

        # Skill slots table
        if PyImGui.begin_child("SkillbarChild", (0, 350), True, 0):
            for slot in range(1, 9):
                skill_id = SkillBar.GetSkillIDBySlot(slot)
                skill_name = get_skill_name_safe(skill_id)

                # Get live data
                recharge_remaining = SkillBar.GetSkillRechargeRemaining(slot)
                is_ready = SkillBar.IsSkillReady(slot)
                adrenaline_a, adrenaline_b = SkillBar.GetSkillAdrenaline(slot)
                can_use = SkillBar.CanUseSkill(slot) if skill_id != 0 else False
                usability = SkillBar.GetSkillUsability(slot)

                # Header with slot number and skill name
                if PyImGui.collapsing_header(f"[{slot}] {skill_name} - {usability}", 0):
                    PyImGui.indent(20)

                    PyImGui.text(f"Skill ID: {skill_id}")

                    # Ready status
                    if is_ready:
                        PyImGui.text_colored("Recharge: READY", (100, 255, 100, 255))
                    else:
                        PyImGui.text_colored(f"Recharge: {recharge_remaining / 1000:.1f}s remaining", (255, 200, 100, 255))

                    # Adrenaline
                    if skill_id != 0:
                        adrenaline_cost = Skill.Data.GetAdrenaline(skill_id)
                        if adrenaline_cost > 0:
                            PyImGui.text(f"Adrenaline: {adrenaline_a}/{adrenaline_cost}")
                        else:
                            PyImGui.text(f"Adrenaline: {adrenaline_a}, {adrenaline_b}")

                    # Energy cost
                    if skill_id != 0:
                        energy_cost = Skill.Data.GetEnergyCost(skill_id)
                        PyImGui.text(f"Energy Cost: {energy_cost}")

                    # Can use status
                    if can_use:
                        PyImGui.text_colored("Can Use: YES", (100, 255, 100, 255))
                    else:
                        PyImGui.text_colored(f"Can Use: NO ({usability})", (255, 100, 100, 255))

                    PyImGui.unindent(20)

            PyImGui.end_child()

    except Exception as e:
        PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))


# ============================================================================
# UI Drawing - Skill Info Tab
# ============================================================================

def draw_skill_info_tab():
    """Draw the skill info lookup tab."""
    PyImGui.text("Skill Information Lookup")
    PyImGui.separator()

    # Lookup controls
    PyImGui.text("Lookup by ID:")
    state.lookup_skill_id = PyImGui.input_int("Skill ID", state.lookup_skill_id)

    # Buttons to quickly select skills from skillbar
    PyImGui.text("From Skillbar Slot:")
    for slot in range(1, 9):
        if PyImGui.button(f"{slot}##slot"):
            skill_id = SkillBar.GetSkillIDBySlot(slot)
            if skill_id > 0:
                state.lookup_skill_id = skill_id
        if slot < 8:
            PyImGui.same_line(0, -1)

    PyImGui.separator()

    skill_id = state.lookup_skill_id
    if skill_id <= 0:
        PyImGui.text("Enter a skill ID or click a slot button above.")
        return

    if PyImGui.begin_child("SkillInfoChild", (0, 450), True, 0):
        try:
            skill_name = get_skill_name_safe(skill_id)
            PyImGui.text_colored(f"{skill_name} (ID: {skill_id})", (100, 200, 255, 255))
            PyImGui.separator()

            # Basic info
            if PyImGui.collapsing_header("Basic Info", PyImGui.TreeNodeFlags.DefaultOpen):
                skill_type = Skill.GetType(skill_id)
                campaign = Skill.GetCampaign(skill_id)
                profession = Skill.GetProfession(skill_id)

                PyImGui.text(f"Type: {skill_type[1]} ({skill_type[0]})")
                PyImGui.text(f"Campaign: {campaign[1]} ({campaign[0]})")
                PyImGui.text(f"Profession: {profession[1]} ({profession[0]})")
                PyImGui.text(f"Elite: {'Yes' if Skill.Flags.IsElite(skill_id) else 'No'}")

            # Costs
            if PyImGui.collapsing_header("Costs & Timing", PyImGui.TreeNodeFlags.DefaultOpen):
                PyImGui.text(f"Energy: {Skill.Data.GetEnergyCost(skill_id)}")
                PyImGui.text(f"Adrenaline: {Skill.Data.GetAdrenaline(skill_id)}")
                PyImGui.text(f"Health Cost: {Skill.Data.GetHealthCost(skill_id)}")
                PyImGui.text(f"Overcast: {Skill.Data.GetOvercast(skill_id)}")
                PyImGui.text(f"Activation: {Skill.Data.GetActivation(skill_id):.2f}s")
                PyImGui.text(f"Aftercast: {Skill.Data.GetAftercast(skill_id):.2f}s")
                PyImGui.text(f"Recharge: {Skill.Data.GetRecharge(skill_id)}s")

            # Target / Affected Entities
            if PyImGui.collapsing_header("Affects (Target Field)", PyImGui.TreeNodeFlags.DefaultOpen):
                target_type = Skill.Target.GetTargetType(skill_id)
                target_name = Skill.Target.GetTargetTypeName(skill_id)
                PyImGui.text_colored("Note: This is which entities are AFFECTED,", (255, 200, 100, 255))
                PyImGui.text_colored("not necessarily who you can target in UI.", (255, 200, 100, 255))
                PyImGui.text(f"Affects: {target_name} ({target_type})")
                PyImGui.text(f"Requires Target Selection: {Skill.Target.RequiresTarget(skill_id)}")
                PyImGui.text(f"Affects Self: {Skill.Target.AffectsSelf(skill_id)}")
                PyImGui.text(f"Affects Ally: {Skill.Target.AffectsAlly(skill_id)}")
                PyImGui.text(f"Affects Foe: {Skill.Target.AffectsFoe(skill_id)}")
                PyImGui.text(f"Affects Dead: {Skill.Target.AffectsDead(skill_id)}")

            # Combo
            if PyImGui.collapsing_header("Combo Chain"):
                combo_type = Skill.Combo.GetComboType(skill_id)
                combo_name = Skill.Combo.GetComboTypeName(skill_id)
                combo_req = Skill.Combo.GetComboRequirement(skill_id)
                combo_req_name = Skill.Combo.GetComboRequirementName(skill_id)

                PyImGui.text(f"Combo Type: {combo_name} ({combo_type})")
                PyImGui.text(f"Combo Requirement: {combo_req_name} ({combo_req})")
                PyImGui.text(f"Is Lead Attack: {Skill.Combo.IsLeadAttack(skill_id)}")
                PyImGui.text(f"Is Off-Hand Attack: {Skill.Combo.IsOffhandAttack(skill_id)}")
                PyImGui.text(f"Is Dual Attack: {Skill.Combo.IsDualAttack(skill_id)}")

            # Weapon
            if PyImGui.collapsing_header("Weapon Requirement"):
                weapon_req = Skill.Weapon.GetWeaponRequirement(skill_id)
                weapon_name = Skill.Weapon.GetWeaponRequirementName(skill_id)

                PyImGui.text(f"Weapon Requirement: {weapon_name} ({weapon_req})")
                PyImGui.text(f"Has Requirement: {Skill.Weapon.HasWeaponRequirement(skill_id)}")
                PyImGui.text(f"Requires Melee: {Skill.Weapon.RequiresMelee(skill_id)}")
                PyImGui.text(f"Requires Ranged: {Skill.Weapon.RequiresRanged(skill_id)}")

            # Range
            if PyImGui.collapsing_header("Range"):
                range_type = Skill.Range.GetRangeType(skill_id)
                range_units = Skill.Range.GetRangeInUnits(skill_id)
                aoe_range = Skill.Range.GetAoERange(skill_id)

                PyImGui.text(f"Range Type: {range_type}")
                PyImGui.text(f"Range: {range_units:.0f} units")
                PyImGui.text(f"AoE Range: {aoe_range:.0f}")
                PyImGui.text(f"Is Touch Range: {Skill.Flags.IsTouchRange(skill_id)}")
                PyImGui.text(f"Is Half Range: {Skill.Flags.IsHalfRange(skill_id)}")

            # Attribute scaling
            if PyImGui.collapsing_header("Attribute Scaling"):
                scale_0, scale_15 = Skill.Attribute.GetScale(skill_id)
                bonus_0, bonus_15 = Skill.Attribute.GetBonusScale(skill_id)
                dur_0, dur_15 = Skill.Attribute.GetDuration(skill_id)

                PyImGui.text(f"Scale: {scale_0} - {scale_15} (0-15 pts)")
                PyImGui.text(f"Bonus Scale: {bonus_0} - {bonus_15}")
                PyImGui.text(f"Duration: {dur_0} - {dur_15}")

        except Exception as e:
            PyImGui.text_colored(f"Error loading skill data: {e}", (255, 0, 0, 255))

        PyImGui.end_child()


# ============================================================================
# UI Drawing - Skill Properties Tab
# ============================================================================

def draw_skill_properties_tab():
    """Draw the SkillProperties classification tab."""
    PyImGui.text("Skill Properties (behavior detection)")
    PyImGui.separator()

    # Lookup controls
    PyImGui.text("Lookup by ID:")
    state.properties_skill_id = PyImGui.input_int("Skill ID##props", state.properties_skill_id)

    # Buttons to quickly select skills from skillbar
    PyImGui.text("From Skillbar Slot:")
    for slot in range(1, 9):
        if PyImGui.button(f"{slot}##propslot"):
            skill_id = SkillBar.GetSkillIDBySlot(slot)
            if skill_id > 0:
                state.properties_skill_id = skill_id
        if slot < 8:
            PyImGui.same_line(0, -1)

    # Sync button
    if state.lookup_skill_id > 0:
        PyImGui.same_line(0, 20)
        if PyImGui.button("Use Skill Info ID"):
            state.properties_skill_id = state.lookup_skill_id

    PyImGui.separator()

    skill_id = state.properties_skill_id
    if skill_id <= 0:
        PyImGui.text("Enter a skill ID or click a slot button above.")
        return

    if PyImGui.begin_child("PropsChild", (0, 500), True, 0):
        try:
            skill_name = get_skill_name_safe(skill_id)
            PyImGui.text_colored(f"{skill_name} (ID: {skill_id})", (100, 200, 255, 255))
            PyImGui.separator()

            # Raw description (what the regex patterns match against)
            if PyImGui.collapsing_header("Raw Description (regex input)##props"):
                concise = Skill.GetConciseDescription(skill_id)
                full = Skill.GetDescription(skill_id)
                PyImGui.text_colored("Concise:", (200, 200, 100, 255))
                PyImGui.text_wrapped(concise)
                PyImGui.text("")
                PyImGui.text_colored("Full:", (200, 200, 100, 255))
                PyImGui.text_wrapped(full)

            # Classification
            if PyImGui.collapsing_header("Classification##props", PyImGui.TreeNodeFlags.DefaultOpen):
                role = SkillProperties.Classification.GetSkillRole(skill_id)
                roles = SkillProperties.Classification.GetSkillRoles(skill_id)

                PyImGui.text(f"Primary Role: {role}")
                PyImGui.text(f"All Roles: {', '.join(roles)}")
                bool_colored("Is Offensive", SkillProperties.Classification.IsOffensiveSkill(skill_id))
                bool_colored("Is Defensive", SkillProperties.Classification.IsDefensiveSkill(skill_id))
                bool_colored("Is Support", SkillProperties.Classification.IsSupportSkill(skill_id))

            # Interrupt
            if PyImGui.collapsing_header("Interrupt##props"):
                bool_colored("Causes Interrupt", SkillProperties.Interrupt.CausesInterrupt(skill_id))
                bool_colored("Conditional Interrupt", SkillProperties.Interrupt.IsConditionalInterrupt(skill_id))
                condition = SkillProperties.Interrupt.GetInterruptCondition(skill_id)
                if condition:
                    PyImGui.text(f"Condition: {condition}")

            # Knockdown
            if PyImGui.collapsing_header("Knockdown##props"):
                causes_kd = SkillProperties.Knockdown.CausesKnockdown(skill_id)
                bool_colored("Causes Knockdown", causes_kd)
                if causes_kd:
                    dur_min, dur_max = SkillProperties.Knockdown.GetKnockdownDuration(skill_id)
                    PyImGui.text(f"Duration: {dur_min:.1f}s - {dur_max:.1f}s")

            # Conditions
            if PyImGui.collapsing_header("Conditions##props"):
                bool_colored("Applies Condition", SkillProperties.Conditions.AppliesCondition(skill_id))
                applied = SkillProperties.Conditions.GetAppliedConditions(skill_id)
                if applied:
                    PyImGui.text(f"Applies: {', '.join(applied)}")
                bool_colored("Removes Condition", SkillProperties.Conditions.RemovesCondition(skill_id))

            # Hexes
            if PyImGui.collapsing_header("Hexes##props"):
                bool_colored("Applies Hex", SkillProperties.Hexes.AppliesHex(skill_id))
                bool_colored("Removes Hex", SkillProperties.Hexes.RemovesHex(skill_id))
                bool_colored("Is Degen Hex", SkillProperties.Hexes.IsDegenerationHex(skill_id))

            # Healing
            if PyImGui.collapsing_header("Healing##props"):
                bool_colored("Is Healing Skill", SkillProperties.Healing.IsHealingSkill(skill_id))
                bool_colored("Is Resurrection", SkillProperties.Healing.IsResurrectionSkill(skill_id))

            # Buffs
            if PyImGui.collapsing_header("Buffs / Enchantments##props"):
                bool_colored("Is Buff Skill", SkillProperties.Buffs.IsBuffSkill(skill_id))
                bool_colored("Is Self Buff", SkillProperties.Buffs.IsSelfBuff(skill_id))
                bool_colored("Removes Enchantment", SkillProperties.Buffs.RemovesEnchantment(skill_id))

            # Damage
            if PyImGui.collapsing_header("Damage##props"):
                bool_colored("Deals Damage", SkillProperties.Damage.DealsDamage(skill_id))
                if SkillProperties.Damage.DealsDamage(skill_id):
                    dmg_type = SkillProperties.Damage.GetDamageType(skill_id)
                    PyImGui.text(f"Damage Type: {dmg_type}")
                bool_colored("Is AoE", SkillProperties.Damage.IsAoE(skill_id))

            # Conditional Effects
            if PyImGui.collapsing_header("Conditional Effects##props"):
                bool_colored("Has Conditional Effect", SkillProperties.ConditionalEffects.HasConditionalEffect(skill_id))
                if SkillProperties.ConditionalEffects.HasConditionalEffect(skill_id):
                    reqs = SkillProperties.ConditionalEffects.GetConditionalRequirements(skill_id)
                    if reqs:
                        for req in reqs:
                            PyImGui.text(f"  - {req}")
                bool_colored("Has Bonus Damage", SkillProperties.ConditionalEffects.HasBonusDamage(skill_id))

            # Defense
            if PyImGui.collapsing_header("Defense##props"):
                bool_colored("Is Blocking Skill", SkillProperties.Defense.IsBlockingSkill(skill_id))
                if SkillProperties.Defense.IsBlockingSkill(skill_id):
                    bool_colored("  Blocks Melee", SkillProperties.Defense.BlocksMelee(skill_id))
                    bool_colored("  Blocks Projectiles", SkillProperties.Defense.BlocksProjectiles(skill_id))
                bool_colored("Is Evasion Skill", SkillProperties.Defense.IsEvasionSkill(skill_id))
                bool_colored("Damage Reduction", SkillProperties.Defense.ProvidesDamageReduction(skill_id))
                bool_colored("Prevents Enchanting", SkillProperties.Defense.PreventsEnchanting(skill_id))
                bool_colored("Is Anti-Melee", SkillProperties.Defense.IsAntiMelee(skill_id))
                bool_colored("Is Anti-Caster", SkillProperties.Defense.IsAntiCaster(skill_id))
                defense_type = SkillProperties.Defense.GetDefenseType(skill_id)
                if defense_type != "none":
                    PyImGui.text(f"Defense Type: {defense_type}")

        except Exception as e:
            PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

        PyImGui.end_child()


# ============================================================================
# UI Drawing - Weapon Sets Tab
# ============================================================================

def draw_weapon_sets_tab():
    """Draw the weapon sets tab showing equipped weapon data."""
    PyImGui.text("Weapon Sets (Native Inventory Context)")
    PyImGui.separator()

    try:
        active_index = Inventory.GetActiveWeaponSetIndex()
        if active_index < 0:
            PyImGui.text_colored("Inventory context not available.", (255, 100, 100, 255))
            PyImGui.text("Must be loaded into a map (not loading screen or char select).")
            # Diagnostics
            PyImGui.separator()
            PyImGui.text_colored("Diagnostics:", (255, 200, 100, 255))
            from Py4GWCoreLib.native_src.context.InventoryContext import (
                Inventory as NativeInv, ItemContext as NativeItemCtx
            )
            PyImGui.text(f"  Inventory._ptr:   {NativeInv.get_ptr()}")
            PyImGui.text(f"  ItemContext._ptr:  {NativeItemCtx.get_ptr()}")
            try:
                game_ctx = PyPlayer.PyPlayer().GetGameContextPtr()
                PyImGui.text(f"  GameContextPtr:   {game_ctx}")
            except Exception:
                PyImGui.text("  GameContextPtr:   (error getting)")
            return

        PyImGui.text(f"Active Weapon Set: {active_index + 1} (index {active_index})")
        PyImGui.separator()

        # Show all 4 weapon sets
        if PyImGui.begin_child("WeaponSetsChild", (0, 400), True, 0):
            all_sets = Inventory.GetAllWeaponSets()
            for ws in all_sets:
                if ws is None:
                    continue

                # Header with active indicator
                active_marker = " [ACTIVE]" if ws.is_active else ""
                header_label = f"Set {ws.set_index + 1}{active_marker}##ws{ws.set_index}"

                if PyImGui.collapsing_header(header_label, PyImGui.TreeNodeFlags.DefaultOpen):
                    PyImGui.indent(20)

                    # Main hand
                    if ws.has_weapon:
                        two_h = " (2H)" if ws.is_two_handed else ""
                        PyImGui.text_colored(f"Main Hand ({ws.weapon_type_name}{two_h}):", (100, 200, 255, 255))
                        PyImGui.text(f"  Item ID: {ws.weapon_item_id}")
                        PyImGui.text(f"  Damage Type: {ws.weapon_damage_type} ({ws.weapon_damage_type_id})")
                    else:
                        PyImGui.text("Main Hand: (empty)")

                    # Off-hand (hidden for 2-handed weapons)
                    if ws.is_two_handed:
                        PyImGui.text("Off-Hand: (N/A - two-handed weapon)")
                    elif ws.has_offhand:
                        offhand_type = "Shield" if ws.is_shield else "Focus" if ws.is_focus else "Off-Hand"
                        PyImGui.text_colored(f"Off-Hand ({offhand_type}):", (100, 200, 255, 255))
                        PyImGui.text(f"  Item ID: {ws.offhand_item_id}")
                        if ws.offhand_damage_type:
                            PyImGui.text(f"  Damage Type: {ws.offhand_damage_type} ({ws.offhand_damage_type_id})")
                    else:
                        PyImGui.text("Off-Hand: (empty)")

                    # Collapsible human-readable modifier display
                    raw_ws = Inventory.GetWeaponSetRaw(ws.set_index)
                    if raw_ws and PyImGui.tree_node(f"Item Modifiers##rawmods{ws.set_index}"):
                        items_to_show = [("Weapon", raw_ws.weapon)]
                        if not ws.is_two_handed:
                            items_to_show.append(("Offhand", raw_ws.offhand))
                        for label, item in items_to_show:
                            if item and item.mod_struct_ptr and item.mod_struct_size > 0:
                                type_name = ws.weapon_type_name if label == "Weapon" else ""
                                PyImGui.text_colored(f"  {label} ({type_name}):", (100, 200, 255, 255))
                                _format_item_mods(item)
                        PyImGui.tree_pop()

                    PyImGui.unindent(20)

            PyImGui.separator()

            # Quick lookup helpers
            PyImGui.text_colored("Quick Lookups:", (255, 200, 100, 255))

            defensive = Inventory.GetDefensiveWeaponSet()
            if defensive:
                PyImGui.text(f"  Shield Set: Set {defensive.set_index + 1}")
            else:
                PyImGui.text("  Shield Set: (none found)")

            casting = Inventory.GetCastingWeaponSet()
            if casting:
                PyImGui.text(f"  Casting Set (Focus): Set {casting.set_index + 1}")
            else:
                PyImGui.text("  Casting Set (Focus): (none found)")

            # Conjure lookups - only show if the skill is on the skillbar
            conjure_map = {
                "Conjure Lightning": False,
                "Conjure Frost": False,
                "Conjure Flame": False,
            }
            for slot in range(1, 9):
                skill_id = SkillBar.GetSkillIDBySlot(slot)
                if skill_id > 0:
                    name = get_skill_name_safe(skill_id)
                    if name in conjure_map:
                        conjure_map[name] = True

            for conjure_name, is_equipped in conjure_map.items():
                if is_equipped:
                    conjure_ws = Inventory.GetConjureWeaponSet(conjure_name)
                    if conjure_ws:
                        PyImGui.text(f"  {conjure_name}: Set {conjure_ws.set_index + 1} ({conjure_ws.weapon_damage_type})")
                    else:
                        PyImGui.text(f"  {conjure_name}: (no matching weapon set)")

            PyImGui.end_child()

    except Exception as e:
        PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))


# ============================================================================
# UI Drawing - Item Weapons Tab
# ============================================================================

def draw_item_weapons_tab():
    """Draw the Item.Weapon reference tab with base damage, speed, DPS."""
    PyImGui.text("Weapon Type Reference (Item.Weapon)")
    PyImGui.separator()

    if PyImGui.begin_child("ItemWeaponsChild", (0, 450), True, 0):
        try:
            all_types = Item.Weapon.GetAllWeaponTypes()

            # Header
            PyImGui.text_colored(
                f"{'Type':<10} {'Damage':<12} {'Speed':<8} {'DPS':<8} {'Range':<8} {'Category'}",
                (100, 200, 255, 255)
            )
            PyImGui.separator()

            for wtype in all_types:
                min_dmg, max_dmg = Item.Weapon.GetBaseDamageRange(wtype)
                speed = Item.Weapon.GetAttackSpeed(wtype)
                dps = Item.Weapon.GetDPS(wtype)
                wrange = Item.Weapon.GetWeaponRange(wtype)
                category = "Melee" if Item.Weapon.IsMelee(wtype) else "Ranged"

                PyImGui.text(
                    f"{wtype.name:<10} {min_dmg:>3}-{max_dmg:<3}       {speed:<8.2f} {dps:<8.1f} {wrange:<8} {category}"
                )

            PyImGui.separator()
            PyImGui.text_colored("Notes:", (255, 200, 100, 255))
            PyImGui.text("  Daggers: DPS doubled (double strike per cycle)")
            PyImGui.text("  Damage values are at max weapon requirement")
            PyImGui.text("  Speed is base (no IAS buffs)")
            PyImGui.text("  Aggro bubble ~ 1010 units")

        except Exception as e:
            PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

        PyImGui.end_child()


# ============================================================================
# UI Drawing - Template Tab
# ============================================================================

def draw_template_tab():
    """Draw the template encode/decode testing tab."""
    PyImGui.text("Template Encode/Decode")
    PyImGui.separator()

    if PyImGui.begin_tab_bar("TemplateTabBar"):
        # Decode tab
        if PyImGui.begin_tab_item("Decode"):
            PyImGui.text("Enter a template code to decode:")
            state.template_input = PyImGui.input_text("Template Code", state.template_input, 64)

            if PyImGui.button("Decode"):
                state.template_decode_result = SkillBar.DecodeTemplate(state.template_input)

            PyImGui.same_line(0, -1)
            if PyImGui.button("Use Current Build"):
                current = SkillBar.GetCurrentTemplate()
                if current:
                    state.template_input = current

            PyImGui.separator()

            if state.template_decode_result:
                result = state.template_decode_result
                PyImGui.text_colored("Decode successful!", (100, 255, 100, 255))

                PyImGui.text(f"Primary: {get_profession_name(result['primary'])} ({result['primary']})")
                PyImGui.text(f"Secondary: {get_profession_name(result['secondary'])} ({result['secondary']})")

                PyImGui.separator()
                PyImGui.text("Skills:")
                for i, skill_id in enumerate(result['skills'], 1):
                    skill_name = get_skill_name_safe(skill_id)
                    PyImGui.text(f"  [{i}] {skill_name} ({skill_id})")

                PyImGui.separator()
                PyImGui.text("Attributes:")
                if result['attributes']:
                    for attr_id, points in result['attributes']:
                        attr_name = get_attribute_name(attr_id)
                        PyImGui.text(f"  {attr_name}: {points}")
                else:
                    PyImGui.text("  (None)")
            elif state.template_input:
                PyImGui.text_colored("Invalid template or decode failed", (255, 100, 100, 255))

            PyImGui.end_tab_item()

        # Encode tab
        if PyImGui.begin_tab_item("Encode"):
            PyImGui.text("Build a template:")

            state.encode_primary = PyImGui.input_int("Primary (1-10)", state.encode_primary)
            state.encode_secondary = PyImGui.input_int("Secondary (0-10)", state.encode_secondary)

            PyImGui.separator()
            PyImGui.text("Skills (enter skill IDs):")
            for i in range(8):
                state.encode_skills[i] = PyImGui.input_int(f"Slot {i+1}", state.encode_skills[i])

            if PyImGui.button("Encode"):
                # Use empty attributes for now
                result = SkillBar.EncodeTemplate(
                    state.encode_primary,
                    state.encode_secondary,
                    state.encode_skills,
                    []  # Empty attributes
                )
                state.encoded_result = result if result else "Encode failed"

            PyImGui.separator()
            if state.encoded_result:
                PyImGui.text("Result:")
                PyImGui.text_colored(state.encoded_result, (100, 255, 100, 255))

            PyImGui.end_tab_item()

        # Current Build tab
        if PyImGui.begin_tab_item("Current Build"):
            PyImGui.text("Get current skillbar as template:")

            if PyImGui.button("Get Current Template"):
                result = SkillBar.GetCurrentTemplate()
                if result:
                    state.template_input = result
                    state.template_decode_result = SkillBar.DecodeTemplate(result)

            PyImGui.separator()

            if state.template_input:
                PyImGui.text("Template Code:")
                PyImGui.text_colored(state.template_input, (100, 200, 255, 255))

                PyImGui.separator()

                # Show current skillbar for reference
                PyImGui.text("Current Skillbar:")
                for slot in range(1, 9):
                    skill_id = SkillBar.GetSkillIDBySlot(slot)
                    skill_name = get_skill_name_safe(skill_id)
                    PyImGui.text(f"  [{slot}] {skill_name} ({skill_id})")

            PyImGui.end_tab_item()

        PyImGui.end_tab_bar()


# ============================================================================
# UI Drawing - Hero Skills Tab
# ============================================================================

def draw_hero_skills_tab():
    """Draw the hero skillbar tab."""
    PyImGui.text("Hero Skillbars")
    PyImGui.separator()

    # Hero selector
    PyImGui.text("Select Hero:")
    for i in range(1, 8):
        if PyImGui.button(f"Hero {i}"):
            state.selected_hero_index = i
        if i < 7:
            PyImGui.same_line(0, -1)

    PyImGui.separator()
    PyImGui.text(f"Viewing Hero {state.selected_hero_index}")

    if PyImGui.begin_child("HeroSkillsChild", (0, 400), True, 0):
        try:
            for slot in range(1, 9):
                skill_id = SkillBar.GetHeroSkillIDBySlot(state.selected_hero_index, slot)
                skill_name = get_skill_name_safe(skill_id)

                # Get hero skill live data
                recharge_remaining = SkillBar.GetHeroSkillRechargeRemaining(state.selected_hero_index, slot)
                is_ready = SkillBar.IsHeroSkillReady(state.selected_hero_index, slot)
                adrenaline_a, adrenaline_b = SkillBar.GetHeroSkillAdrenaline(state.selected_hero_index, slot)

                # Build status string for header
                if skill_id == 0:
                    status = "Empty"
                elif is_ready:
                    status = "Ready"
                else:
                    status = f"{recharge_remaining / 1000:.1f}s"

                if PyImGui.collapsing_header(f"[{slot}] {skill_name} - {status}", 0):
                    PyImGui.indent(20)

                    PyImGui.text(f"Skill ID: {skill_id}")

                    # Recharge status
                    if is_ready:
                        PyImGui.text_colored("Recharge: READY", (100, 255, 100, 255))
                    else:
                        PyImGui.text_colored(f"Recharge: {recharge_remaining / 1000:.1f}s remaining", (255, 200, 100, 255))

                    # Show skill data if valid skill
                    if skill_id != 0:
                        # Costs
                        energy_cost = Skill.Data.GetEnergyCost(skill_id)
                        adrenaline_cost = Skill.Data.GetAdrenaline(skill_id)
                        health_cost = Skill.Data.GetHealthCost(skill_id)

                        PyImGui.text(f"Energy Cost: {energy_cost}")
                        if adrenaline_cost > 0:
                            PyImGui.text(f"Adrenaline: {adrenaline_a}/{adrenaline_cost}")
                        else:
                            PyImGui.text(f"Adrenaline: {adrenaline_a}, {adrenaline_b}")
                        if health_cost > 0:
                            PyImGui.text(f"Health Cost: {health_cost}")

                        # Timing
                        activation = Skill.Data.GetActivation(skill_id)
                        aftercast = Skill.Data.GetAftercast(skill_id)
                        recharge = Skill.Data.GetRecharge(skill_id)
                        PyImGui.text(f"Cast: {activation:.2f}s | After: {aftercast:.2f}s | Recharge: {recharge}s")

                        # Type info
                        skill_type = Skill.GetType(skill_id)
                        PyImGui.text(f"Type: {skill_type[1]}")

                        # Affects
                        target_name = Skill.Target.GetTargetTypeName(skill_id)
                        PyImGui.text(f"Affects: {target_name}")

                        # Weapon requirement
                        if Skill.Weapon.HasWeaponRequirement(skill_id):
                            weapon_name = Skill.Weapon.GetWeaponRequirementName(skill_id)
                            PyImGui.text(f"Requires: {weapon_name}")

                    PyImGui.unindent(20)

        except Exception as e:
            PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

        PyImGui.end_child()


# ============================================================================
# UI Drawing - Quick Reference Tab
# ============================================================================

def draw_reference_tab():
    """Draw quick reference for target/combo/weapon types."""
    PyImGui.text("Quick Reference")
    PyImGui.separator()

    if PyImGui.begin_tab_bar("RefTabBar"):
        if PyImGui.begin_tab_item("Affects (Target)"):
            if PyImGui.begin_child("TargetRefChild", (0, 300), True, 0):
                PyImGui.text_colored("Note: This is which entities are AFFECTED,", (255, 200, 100, 255))
                PyImGui.text_colored("not necessarily who you can target in UI.", (255, 200, 100, 255))
                PyImGui.separator()
                PyImGui.text("Target Type Bitmask Values:")
                PyImGui.text(f"  NONE = {Skill.Target.NONE} (No target)")
                PyImGui.text(f"  SELF = {Skill.Target.SELF}")
                PyImGui.text(f"  ALLY = {Skill.Target.ALLY}")
                PyImGui.text(f"  FOE = {Skill.Target.FOE}")
                PyImGui.text(f"  DEAD = {Skill.Target.DEAD} (Dead ally)")
                PyImGui.text(f"  ITEM = {Skill.Target.ITEM}")
                PyImGui.text(f"  SPIRIT = {Skill.Target.SPIRIT}")
                PyImGui.separator()
                PyImGui.text("Combined values (examples):")
                PyImGui.text("  3 = Self/Ally (e.g. Healing Breeze)")
                PyImGui.text("  5 = Self/Foe (e.g. attacks, shadow steps)")
                PyImGui.text("  7 = Any")
                PyImGui.end_child()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("Combo Types"):
            if PyImGui.begin_child("ComboRefChild", (0, 300), True, 0):
                PyImGui.text("Assassin Combo Chain:")
                PyImGui.text("  Lead Attack -> Off-Hand Attack -> Dual Attack")
                PyImGui.separator()
                PyImGui.text("Combo Type Values (what skill provides):")
                PyImGui.text(f"  TYPE_NONE = {Skill.Combo.TYPE_NONE}")
                PyImGui.text(f"  TYPE_LEAD = {Skill.Combo.TYPE_LEAD}")
                PyImGui.text(f"  TYPE_OFFHAND = {Skill.Combo.TYPE_OFFHAND}")
                PyImGui.text(f"  TYPE_DUAL = {Skill.Combo.TYPE_DUAL}")
                PyImGui.separator()
                PyImGui.text("Combo Requirement Values (what skill needs):")
                PyImGui.text(f"  REQ_NONE = {Skill.Combo.REQ_NONE}")
                PyImGui.text(f"  REQ_LEAD = {Skill.Combo.REQ_LEAD}")
                PyImGui.text(f"  REQ_OFFHAND = {Skill.Combo.REQ_OFFHAND}")
                PyImGui.end_child()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("Weapon Types"):
            if PyImGui.begin_child("WeaponRefChild", (0, 300), True, 0):
                PyImGui.text("Weapon Requirement Values (bitmask):")
                PyImGui.text(f"  REQ_NONE = {Skill.Weapon.REQ_NONE}")
                PyImGui.text(f"  REQ_AXE = {Skill.Weapon.REQ_AXE}")
                PyImGui.text(f"  REQ_BOW = {Skill.Weapon.REQ_BOW}")
                PyImGui.text(f"  REQ_DAGGER = {Skill.Weapon.REQ_DAGGER}")
                PyImGui.text(f"  REQ_HAMMER = {Skill.Weapon.REQ_HAMMER}")
                PyImGui.text(f"  REQ_SCYTHE = {Skill.Weapon.REQ_SCYTHE}")
                PyImGui.text(f"  REQ_SPEAR = {Skill.Weapon.REQ_SPEAR}")
                PyImGui.text(f"  REQ_SWORD = {Skill.Weapon.REQ_SWORD}")
                PyImGui.text(f"  REQ_MELEE = {Skill.Weapon.REQ_MELEE} (combined)")
                PyImGui.end_child()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("Range Constants"):
            if PyImGui.begin_child("RangeRefChild", (0, 300), True, 0):
                PyImGui.text("Detectable Range Constants (game units):")
                PyImGui.text(f"  TOUCH = {Skill.Range.TOUCH}")
                PyImGui.text(f"  HALF_RANGE = {Skill.Range.HALF_RANGE}")
                PyImGui.text(f"  FULL_RANGE = {Skill.Range.FULL_RANGE}")
                PyImGui.text("")
                PyImGui.text("Reference values (not detectable from flags):")
                PyImGui.text("  ADJACENT ~ 166")
                PyImGui.text("  NEARBY ~ 252")
                PyImGui.text("  IN_THE_AREA ~ 322")
                PyImGui.text("  EARSHOT ~ 1010")
                PyImGui.text("  SPIRIT_RANGE ~ 2500")
                PyImGui.end_child()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("SkillUsability"):
            if PyImGui.begin_child("UsabilityRefChild", (0, 300), True, 0):
                PyImGui.text("SkillUsability IntEnum values:")
                PyImGui.text(f"  READY = {int(SkillUsability.READY)}")
                PyImGui.text(f"  RECHARGING = {int(SkillUsability.RECHARGING)}")
                PyImGui.text(f"  DISABLED = {int(SkillUsability.DISABLED)}")
                PyImGui.text(f"  NO_ENERGY = {int(SkillUsability.NO_ENERGY)}")
                PyImGui.text(f"  NO_ADRENALINE = {int(SkillUsability.NO_ADRENALINE)}")
                PyImGui.text(f"  EMPTY_SLOT = {int(SkillUsability.EMPTY_SLOT)}")
                PyImGui.separator()
                PyImGui.text("Usage:")
                PyImGui.text("  result = SkillBar.GetSkillUsability(slot)")
                PyImGui.text("  result.status  -> SkillUsability enum")
                PyImGui.text("  result.value    -> e.g. remaining recharge seconds")
                PyImGui.text("  result.required -> e.g. energy cost")
                PyImGui.end_child()
            PyImGui.end_tab_item()

        PyImGui.end_tab_bar()


# ============================================================================
# Main Window
# ============================================================================

def draw_main_window():
    """Draw the main tester window."""
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        # Main tab bar
        if PyImGui.begin_tab_bar("MainTabBar"):
            if PyImGui.begin_tab_item("Skillbar"):
                draw_skillbar_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Skill Info"):
                draw_skill_info_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Skill Properties"):
                draw_skill_properties_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Weapon Sets"):
                draw_weapon_sets_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Item Weapons"):
                draw_item_weapons_tab()
                PyImGui.end_tab_item()


            if PyImGui.begin_tab_item("Templates"):
                draw_template_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Hero Skills"):
                draw_hero_skills_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Reference"):
                draw_reference_tab()
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

        PyImGui.separator()
        PyImGui.text_colored("by Paul (HSTools)", (150, 150, 150, 255))

    PyImGui.end()


# ============================================================================
# Main Entry Points
# ============================================================================

def configure():
    """Configure function (called by widget system)."""
    pass


def main():
    """Main function (called every frame by widget system)."""
    if not Routines.Checks.Map.MapValid():
        return

    draw_main_window()


if __name__ == "__main__":
    main()

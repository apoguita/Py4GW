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
3. Target/Combo/Weapon Tab: Test new skill interpretation helpers
4. Template Tab: Test template encode/decode functions
5. Hero Skills Tab: View hero skillbars

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

# Get detailed reason why skill can't be used
reason = SkillBar.GetSkillUsabilityReason(1)
print(f"Slot 1: {reason}")  # "Ready", "Recharging (5.2s)", "No Energy", etc.

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
if Skill.Target.CanTargetFoe(skill_id):
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

See Also:
---------
- Skillbar.py: SkillBar class with live data and template functions
- Skill.py: Skill class with Target, Combo, Weapon, Range helpers
"""

from Py4GWCoreLib import *
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
    """Get profession name from ID."""
    names = {
        0: "None",
        1: "Warrior",
        2: "Ranger",
        3: "Monk",
        4: "Necromancer",
        5: "Mesmer",
        6: "Elementalist",
        7: "Assassin",
        8: "Ritualist",
        9: "Paragon",
        10: "Dervish",
    }
    return names.get(prof_id, f"Unknown ({prof_id})")


def get_attribute_name(attr_id: int) -> str:
    """Get attribute name from ID."""
    # Common attribute IDs
    names = {
        0: "Fast Casting",
        1: "Illusion Magic",
        2: "Domination Magic",
        3: "Inspiration Magic",
        4: "Blood Magic",
        5: "Death Magic",
        6: "Soul Reaping",
        7: "Curses",
        8: "Air Magic",
        9: "Earth Magic",
        10: "Fire Magic",
        11: "Water Magic",
        12: "Energy Storage",
        13: "Healing Prayers",
        14: "Smiting Prayers",
        15: "Protection Prayers",
        16: "Divine Favor",
        17: "Strength",
        18: "Axe Mastery",
        19: "Hammer Mastery",
        20: "Swordsmanship",
        21: "Tactics",
        22: "Beast Mastery",
        23: "Expertise",
        24: "Wilderness Survival",
        25: "Marksmanship",
        29: "Dagger Mastery",
        30: "Deadly Arts",
        31: "Shadow Arts",
        32: "Communing",
        33: "Restoration Magic",
        34: "Channeling Magic",
        35: "Critical Strikes",
        36: "Spawning Power",
        37: "Spear Mastery",
        38: "Command",
        39: "Motivation",
        40: "Leadership",
        41: "Scythe Mastery",
        42: "Wind Prayers",
        43: "Earth Prayers",
        44: "Mysticism",
    }
    return names.get(attr_id, f"Attr#{attr_id}")


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
                usability = SkillBar.GetSkillUsabilityReason(slot)

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
        PyImGui.text("Enter a skill ID or hover over a skill and click 'From Hovered'")
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
                PyImGui.text("Range Constants (game units):")
                PyImGui.text(f"  TOUCH = {Skill.Range.TOUCH}")
                PyImGui.text(f"  ADJACENT = {Skill.Range.ADJACENT}")
                PyImGui.text(f"  NEARBY = {Skill.Range.NEARBY}")
                PyImGui.text(f"  IN_THE_AREA = {Skill.Range.IN_THE_AREA}")
                PyImGui.text(f"  EARSHOT = {Skill.Range.EARSHOT}")
                PyImGui.text(f"  HALF_RANGE = {Skill.Range.HALF_RANGE}")
                PyImGui.text(f"  FULL_RANGE = {Skill.Range.FULL_RANGE}")
                PyImGui.text(f"  SPIRIT_RANGE = {Skill.Range.SPIRIT_RANGE}")
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

import PyImGui

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.py4gwcorelib_src.Timer import Timer
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.py4gwcorelib_src.Color import ColorPalette, Color
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.enums import Attribute

from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.party_teambuild_manager import SkillbarData

is_impersonated = False

# Profession mapping from ID to name
PROFESSION_MAP = {
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
    10: "Dervish"
}

def get_profession_name(profession_id):
    """Convert profession ID to readable name"""
    return PROFESSION_MAP.get(profession_id, "Unknown")

def get_profession_texture_path(profession_id):
    """Get profession icon texture path"""
    if profession_id == 0:
        return ""
    profession_name = get_profession_name(profession_id)
    return f"Textures\\Profession_Icons\\[{profession_id}] - {profession_name}.png"

def get_skill_name(skill_id):
    """Get skill name from skill ID"""
    try:
        return GLOBAL_CACHE.Skill.GetName(skill_id)
    except:
        return f"Skill {skill_id}"

def get_skill_texture_path(skill_id):
    """Get skill icon texture path"""
    try:
        return GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
    except:
        return ""

def get_attribute_name(attribute_id):
    """Convert attribute ID to readable name"""
    try:
        # Convert the attribute ID to the corresponding enum name
        attribute_enum = Attribute(attribute_id)
        # Convert enum name to readable format (e.g., FastCasting -> Fast Casting)
        name = attribute_enum.name
        # Add spaces before capital letters (except the first one)
        readable_name = ""
        for i, char in enumerate(name):
            if i > 0 and char.isupper():
                readable_name += " "
            readable_name += char
        return readable_name
    except (ValueError, KeyError):
        return f"Unknown Attribute {attribute_id}"

def format_attributes(attributes_dict):
    """Format attributes dictionary to readable string"""
    if not attributes_dict:
        return "No attributes"

    formatted_attrs = []
    for attr_id, level in attributes_dict.items():
        attr_name = get_attribute_name(attr_id)
        formatted_attrs.append(f"{attr_name}: {level}")

    return ", ".join(formatted_attrs)

# Attribute to profession mapping
ATTRIBUTE_TO_PROFESSION = {
    # Mesmer
    0: "Mesmer",    # Fast Casting
    1: "Mesmer",    # Illusion Magic
    2: "Mesmer",    # Domination Magic
    3: "Mesmer",    # Inspiration Magic
    # Necromancer
    4: "Necromancer",  # Blood Magic
    5: "Necromancer",  # Death Magic
    6: "Necromancer",  # Soul Reaping
    7: "Necromancer",  # Curses
    # Elementalist
    8: "Elementalist",   # Air Magic
    9: "Elementalist",   # Earth Magic
    10: "Elementalist",  # Fire Magic
    11: "Elementalist",  # Water Magic
    12: "Elementalist",  # Energy Storage
    # Monk
    13: "Monk",     # Healing Prayers
    14: "Monk",     # Smiting Prayers
    15: "Monk",     # Protection Prayers
    16: "Monk",     # Divine Favor
    # Warrior
    17: "Warrior",  # Strength
    18: "Warrior",  # Axe Mastery
    19: "Warrior",  # Hammer Mastery
    20: "Warrior",  # Swordsmanship
    21: "Warrior",  # Tactics
    # Ranger
    22: "Ranger",   # Beast Mastery
    23: "Ranger",   # Expertise
    24: "Ranger",   # Wilderness Survival
    25: "Ranger",   # Marksmanship
    # Unknown/Reserved
    26: "None",     # Unknown1
    27: "None",     # Unknown2
    28: "None",     # Unknown3
    # Assassin
    29: "Assassin", # Dagger Mastery
    30: "Assassin", # Deadly Arts
    31: "Assassin", # Shadow Arts
    # Ritualist
    32: "Ritualist", # Communing
    33: "Ritualist", # Restoration Magic
    34: "Ritualist", # Channeling Magic
    35: "Assassin",  # Critical Strikes
    36: "Ritualist", # Spawning Power
    # Paragon
    37: "Paragon",  # Spear Mastery
    38: "Paragon",  # Command
    39: "Paragon",  # Motivation
    40: "Paragon",  # Leadership
    # Dervish
    41: "Dervish",  # Scythe Mastery
    42: "Dervish",  # Wind Prayers
    43: "Dervish",  # Earth Prayers
    44: "Dervish",  # Mysticism
}

def get_profession_color(profession_name):
    """Get profession color from ColorPalette"""
    color = ColorPalette.GetColor("Gray")
    if profession_name == "Warrior":
        color = ColorPalette.GetColor("GW_Warrior")
    elif profession_name == "Ranger":
        color = ColorPalette.GetColor("GW_Ranger")
    elif profession_name == "Monk":
        color = ColorPalette.GetColor("GW_Monk")
    elif profession_name == "Necromancer":
        color = ColorPalette.GetColor("GW_Necromancer")
    elif profession_name == "Mesmer":
        color = ColorPalette.GetColor("GW_Mesmer")
    elif profession_name == "Elementalist":
        color = ColorPalette.GetColor("GW_Elementalist")
    elif profession_name == "Assassin":
        color = ColorPalette.GetColor("GW_Assassin")
    elif profession_name == "Ritualist":
        color = ColorPalette.GetColor("GW_Ritualist")
    elif profession_name == "Paragon":
        color = ColorPalette.GetColor("GW_Paragon")
    elif profession_name == "Dervish":
        color = ColorPalette.GetColor("GW_Dervish")
    return color

def get_attribute_profession(attribute_id):
    """Get the profession that owns this attribute"""
    return ATTRIBUTE_TO_PROFESSION.get(attribute_id, "None")

def create_colored_button(label, color, width=0, height=0):
    """Create a colored button with hover and active states and black text"""
    # Create slightly darker colors for hover and active states
    hovered_color = Color(
        max(0, color.r - 30),
        max(0, color.g - 30),
        max(0, color.b - 30),
        color.a
    )
    active_color = Color(
        max(0, color.r - 50),
        max(0, color.g - 50),
        max(0, color.b - 50),
        color.a
    )

    # Black text color
    black_color = Color(0, 0, 0, 255)

    # Push button colors and text color
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, color.to_tuple_normalized())
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hovered_color.to_tuple_normalized())
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active_color.to_tuple_normalized())
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, black_color.to_tuple_normalized())

    # Create button
    clicked = PyImGui.button(label, width, height)

    # Pop colors (4 colors now: button, hovered, active, text)
    PyImGui.pop_style_color(4)

    return clicked

def render_attribute_buttons(attributes_dict, template_index):
    """Render attributes as small colored buttons, each colored by its profession"""
    if not attributes_dict:
        PyImGui.text("No attributes")
        return

    button_count = 0
    for attr_id, level in attributes_dict.items():
        if button_count > 0 and button_count % 4 == 0:
            # Start new line after every 4 buttons
            pass  # PyImGui automatically goes to new line
        elif button_count > 0:
            PyImGui.same_line(0, 3)  # Small spacing between buttons on same line

        attr_name = get_attribute_name(attr_id)
        attr_profession = get_attribute_profession(attr_id)
        attr_color = get_profession_color(attr_profession)

        button_label = f"{attr_name}: {level}##attr_{template_index}_{attr_id}"

        # Create small colored button with attribute's profession color
        create_colored_button(button_label, attr_color, 0, 20)

        # Tooltip with full attribute name and profession
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.text(f"{attr_name}: {level}")
            PyImGui.text(f"({attr_profession} attribute)")
            PyImGui.end_tooltip()

        button_count += 1

def render():

    global is_impersonated

    # Create 2-column table with 70%/30% split
    if PyImGui.begin_table("main_layout", 2, PyImGui.TableFlags.SizingFixedFit):
        # Setup columns with specific widths
        PyImGui.table_setup_column("Left", PyImGui.TableColumnFlags.WidthStretch, 0.7)  # 70%
        PyImGui.table_setup_column("Right", PyImGui.TableColumnFlags.WidthStretch, 0.3)  # 30%

        PyImGui.table_next_row()

        # Left column (70%)
        PyImGui.table_set_column_index(0)
        PyImGui.text_wrapped("Display and modify all accounts skillbars.")
        PyImGui.text_wrapped("Gathering other account data is automatic.")

        # Right column (30%)
        PyImGui.table_set_column_index(1)

        if PyImGui.button("Copy to .pwnd format"):
            pawned2_string = CustomBehaviorParty().party_teambuild_manager.encode_to_pawned2_teambuild_pwnd_file()
            PyImGui.set_clipboard_text(pawned2_string)
        PyImGui.show_tooltip("Copy team builds to .pwnd format (the copied content can be pasted directly in pawned2)")

        is_impersonated = PyImGui.checkbox("Impersonate Names", is_impersonated)

        PyImGui.end_table()

    if not GLOBAL_CACHE.Party.IsPartyLeader():
        PyImGui.text("Feature restricted to party leader.")
        return

    PyImGui.separator()

    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    for i, account in enumerate(accounts):

        account_email = account.AccountEmail
        account_character_name = account.CharacterName
        if account_email not in CustomBehaviorParty().party_teambuild_manager.skillbar_datas:
            continue

        shared_data:SkillbarData | None = CustomBehaviorParty().party_teambuild_manager.skillbar_datas.get(account_email)
        if shared_data is None: continue

        primary_profession_id = shared_data.skillbar_parsed.primary_profession_id
        secondary_profession_id = shared_data.skillbar_parsed.secondary_profession_id
        attributes = shared_data.skillbar_parsed.attributes
        skills = shared_data.skillbar_parsed.skills

        primary_name = get_profession_name(primary_profession_id)
        secondary_name = get_profession_name(secondary_profession_id)
        primary_texture = get_profession_texture_path(primary_profession_id)
        secondary_texture = get_profession_texture_path(secondary_profession_id)

        faked = ["françois pignon", "paul palette", "grosse baguette", "jacques chirrac", "mario rossi", "pablo picasso", "pignol de pin", "hubert bonisseur"]
        if is_impersonated:
            if i < len(faked):
                PyImGui.text(f"{faked[i]}")
            else:
                PyImGui.text(f"{faked[0]}")

        else:
            PyImGui.text(f"{account_character_name}")
        PyImGui.same_line(0, 5)
        render_attribute_buttons(attributes, i)

            # Primary profession
        if primary_texture:
            ImGui.DrawTexture(primary_texture, 28, 28)

        PyImGui.same_line(0,5)

        # Secondary profession
        if secondary_texture:
            ImGui.DrawTexture(secondary_texture, 28, 28)

        for skill_row_idx in range(0, 8):

            PyImGui.same_line(0,5)
            skill_index = skill_row_idx
            if skill_index < len(skills):
                skill_id = skills[skill_index]

                if skill_id != 0:  # Valid skill
                    skill_texture = get_skill_texture_path(skill_id)
                    skill_name = get_skill_name(skill_id)

                    # Draw skill icon
                    if skill_texture:
                        ImGui.DrawTexture(skill_texture, 38, 38)
                        # Tooltip with skill name
                        if PyImGui.is_item_hovered():
                            PyImGui.begin_tooltip()
                            PyImGui.text(f"Slot {skill_index + 1}: {skill_name}")
                            PyImGui.end_tooltip()
                    else:
                        # Fallback if no texture
                        PyImGui.button(f"{skill_index + 1}##skill_{i}_{skill_index}", 38, 38)
                        if PyImGui.is_item_hovered():
                            PyImGui.begin_tooltip()
                            PyImGui.text(f"Slot {skill_index + 1}: {skill_name}")
                            PyImGui.end_tooltip()
                else:
                    # Empty skill slot
                    PyImGui.button(f"Empty##empty_{i}_{skill_index}", 38, 38)
                    if PyImGui.is_item_hovered():
                        PyImGui.begin_tooltip()
                        PyImGui.text(f"Slot {skill_index + 1}: Empty")
                        PyImGui.end_tooltip()

                # Same line for horizontal layout, except for last skill in row
                
        PyImGui.same_line(0,5)

        # Template actions
        if PyImGui.button(f"{IconsFontAwesome5.ICON_CLIPBOARD}##load_{i}"):
            template = PyImGui.get_clipboard_text()
            CustomBehaviorParty().party_teambuild_manager.apply_skillbar_template(template, account_email)
        PyImGui.show_tooltip("Apply Template from clipboard")

        PyImGui.same_line(0,5)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_COPY}##copy_{i}"):
            PyImGui.set_clipboard_text(shared_data.skillbar_template)
        PyImGui.show_tooltip("Copy Template to clipboard")

        PyImGui.separator()
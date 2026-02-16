"""
Flag Grid UI - Grid for character flag positioning assignment.

This module provides a grid UI for assigning characters to flag positions
for party formation management.
"""
import random
from Py4GWCoreLib import PyImGui, IconsFontAwesome5, ImGui, Player
from Py4GWCoreLib.GlobalCache.shared_memory_src.AccountStruct import AccountStruct
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ColorPalette
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator


# Profession ID to short name mapping (e.g., W, Mo, N/Me)
PROFESSION_SHORT_MAP: dict[int, str] = {
    0: "",
    1: "W",
    2: "R",
    3: "Mo",
    4: "N",
    5: "Me",
    6: "E",
    7: "A",
    8: "Rt",
    9: "P",
    10: "D",
}

# Color variation multipliers for same profession (up to 8 variations)
VARIATION_MULTIPLIERS: list[float] = [1.0, 0.85, 1.15, 0.70, 1.30, 0.55, 1.45, 0.40]


class CharacterData:
    """Data class representing a character for grid assignment."""
    def __init__(self, email: str, name: str, profession_id: int, color: Color, is_leader: bool = False, secondary_profession_id: int = 0):
        self.email = email
        self.name = name
        self.profession_id = profession_id
        self.secondary_profession_id = secondary_profession_id
        primary_short = PROFESSION_SHORT_MAP.get(profession_id, "?")
        secondary_short = PROFESSION_SHORT_MAP.get(secondary_profession_id, "")
        self.profession_name = f"{primary_short}/{secondary_short}" if secondary_short else primary_short
        self.color = color
        self.is_leader = is_leader
        self.short_label = name[:3] if len(name) >= 3 else name


class FlagGridUI:
    """Flag Grid UI for character positioning with 5x5 grid layout."""

    GRID_SIZE = 5
    TOTAL_SLOTS = GRID_SIZE * GRID_SIZE

    _grid_assignments: list[CharacterData | None] = [None] * TOTAL_SLOTS
    _selected_character: CharacterData | None = None
    _initialized: bool = False
    _persistence = PersistenceLocator().flagging

    @classmethod
    def render_configuration(cls) -> None:
        """Render the flag grid configuration UI."""
        characters = cls._get_party_characters()

        # Load persisted assignments on first render
        if not cls._initialized:
            cls._load_from_persistence(characters)
            cls._initialized = True

        PyImGui.separator()
        PyImGui.text("[FLAG GRID] Configure positions:")
        PyImGui.spacing()

        # Action buttons
        if PyImGui.button(f"{IconsFontAwesome5.ICON_SAVE} Save##flag_grid", 80, 25):
            cls._save()
        PyImGui.same_line(0, 10)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_TRASH_ALT} Reset All##flag_grid", 120, 25):
            cls._clear_all()
        PyImGui.same_line(0, 10)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_RANDOM} Random Assign##flag_grid", 140, 25):
            cls._random_assign(characters)

        PyImGui.spacing()
        PyImGui.columns(2, "flag_grid_columns", True)

        # Column 1: Grid
        cls._render_grid()
        PyImGui.next_column()

        # Column 2: Character list
        cls._render_character_list(characters)
        PyImGui.columns(1, "", False)

        PyImGui.spacing()
        if cls._selected_character is not None:
            PyImGui.text_colored(f"Selected: {cls._selected_character.name}", cls._selected_character.color.to_tuple_normalized())
            PyImGui.text("Click on a grid square to assign.")
        else:
            PyImGui.text_colored("Click a character to select, then click a grid square.", (0.7, 0.7, 0.7, 1.0))

    @classmethod
    def _render_grid(cls) -> None:
        """Render the grid of squares."""
        PyImGui.text_colored(f"Position Grid ({cls.GRID_SIZE}x{cls.GRID_SIZE}):", (0.0, 1.0, 1.0, 1.0))
        PyImGui.spacing()

        square_size = 35.0
        yellow_border = (1.0, 0.85, 0.0, 1.0)

        for row in range(cls.GRID_SIZE):
            for col in range(cls.GRID_SIZE):
                slot_index = row * cls.GRID_SIZE + col
                assigned = cls._grid_assignments[slot_index]
                is_leader_slot = assigned is not None and assigned.is_leader

                btn_color = assigned.color.to_tuple_normalized() if assigned else (0.3, 0.3, 0.3, 1.0)

                if is_leader_slot:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, yellow_border)
                    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3.0)

                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, btn_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (min(1.0, btn_color[0] + 0.1), min(1.0, btn_color[1] + 0.1), min(1.0, btn_color[2] + 0.1), btn_color[3]))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (max(0.0, btn_color[0] - 0.1), max(0.0, btn_color[1] - 0.1), max(0.0, btn_color[2] - 0.1), btn_color[3]))

                label = IconsFontAwesome5.ICON_CROWN if is_leader_slot else (assigned.short_label if assigned else f"{slot_index + 1}")
                if PyImGui.button(f"{label}##grid_{slot_index}", square_size, square_size):
                    cls._on_grid_click(slot_index)

                PyImGui.pop_style_color(3)
                if is_leader_slot:
                    PyImGui.pop_style_color(1)
                    PyImGui.pop_style_var(1)

                if PyImGui.is_item_hovered():
                    if assigned:
                        PyImGui.set_tooltip(f"Slot {slot_index + 1}: {assigned.name}{' [LEADER]' if is_leader_slot else ''}\nClass: {assigned.profession_name}\nClick to clear")
                    else:
                        PyImGui.set_tooltip(f"Slot {slot_index + 1}: Empty\nClick to assign selected character")

                if col < cls.GRID_SIZE - 1:
                    PyImGui.same_line(0, 5)

    @classmethod
    def _render_character_list(cls, characters: list[CharacterData]) -> None:
        """Render the list of characters."""
        PyImGui.text_colored("Characters:", (0.0, 1.0, 1.0, 1.0))
        PyImGui.spacing()

        if not characters:
            PyImGui.text_colored("No characters found.", (0.7, 0.7, 0.7, 1.0))
            return

        green_border = (0.0, 1.0, 0.0, 1.0)

        for char in characters:
            color = char.color.to_tuple_normalized()
            is_selected = cls._selected_character is not None and cls._selected_character.email == char.email

            if is_selected:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, green_border)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3.0)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (min(1.0, color[0] + 0.3), min(1.0, color[1] + 0.3), min(1.0, color[2] + 0.3), 1.0))
            else:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, color)

            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (min(1.0, color[0] + 0.15), min(1.0, color[1] + 0.15), min(1.0, color[2] + 0.15), color[3]))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (max(0.0, color[0] - 0.1), max(0.0, color[1] - 0.1), max(0.0, color[2] - 0.1), color[3]))
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 0.0, 0.0, 1.0))

            display_text = f"{IconsFontAwesome5.ICON_CROWN} {char.profession_name} | {char.name}" if char.is_leader else f"{char.profession_name} | {char.name}"
            if PyImGui.button(f"{display_text}##char_{char.email}", 220, 25):
                cls._selected_character = None if is_selected else char

            PyImGui.pop_style_color(4)
            if is_selected:
                PyImGui.pop_style_color(1)
                PyImGui.pop_style_var(1)

            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip(f"{char.name}{' [LEADER]' if char.is_leader else ''}\nClass: {char.profession_name}\nClick to select")

    @classmethod
    def _on_grid_click(cls, slot_index: int) -> None:
        """Handle click on a grid slot."""
        if cls._grid_assignments[slot_index] is not None:
            cls._grid_assignments[slot_index] = None
        elif cls._selected_character is not None:
            # Remove from any other slot
            for i in range(cls.TOTAL_SLOTS):
                assigned = cls._grid_assignments[i]
                if assigned is not None and assigned.email == cls._selected_character.email:
                    cls._grid_assignments[i] = None
            cls._grid_assignments[slot_index] = cls._selected_character
            cls._selected_character = None

    @classmethod
    def _save(cls) -> None:
        """Save assignments to INI."""
        cls._persistence.clear_all_assignments()
        for idx, char in enumerate(cls._grid_assignments):
            if char is not None:
                cls._persistence.write_assignment(idx, char.email)

    @classmethod
    def _clear_all(cls) -> None:
        """Clear all assignments."""
        cls._grid_assignments = [None] * cls.TOTAL_SLOTS
        cls._selected_character = None

    @classmethod
    def _random_assign(cls, characters: list[CharacterData]) -> None:
        """Randomly assign characters to slots."""
        cls._clear_all()
        slots = list(range(cls.TOTAL_SLOTS))
        random.shuffle(slots)
        for i, char in enumerate(characters):
            if i < len(slots):
                cls._grid_assignments[slots[i]] = char

    @classmethod
    def _load_from_persistence(cls, characters: list[CharacterData]) -> None:
        """Load assignments from INI."""
        assignments = cls._persistence.read_all_assignments()
        chars_by_email = {c.email: c for c in characters}
        for grid_index, email in assignments.items():
            if 0 <= grid_index < cls.TOTAL_SLOTS and email in chars_by_email:
                cls._grid_assignments[grid_index] = chars_by_email[email]

    @classmethod
    def _get_party_characters(cls) -> list[CharacterData]:
        """Get characters in the same map as the player."""
        characters: list[CharacterData] = []
        account_email = Player.GetAccountEmail()
        my_account : AccountStruct | None = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if my_account is None:
            return characters

        all_accounts : list[AccountStruct] = GLOBAL_CACHE.ShMem.GetAllAccountData()
        profession_counts: dict[int, int] = {}

        for account in all_accounts:
            is_in_map = (my_account.AgentData.Map.MapID == account.AgentData.Map.MapID
                         and my_account.AgentData.Map.Region == account.AgentData.Map.Region
                         and my_account.AgentData.Map.District == account.AgentData.Map.District)
            if is_in_map and account.IsAccount:
                profession_id = account.AgentData.Profession[0] if account.AgentData.Profession else 0
                secondary_profession_id = account.AgentData.Profession[1] if account.AgentData.Profession and len(account.AgentData.Profession) > 1 else 0
                char_name = account.AgentData.CharacterName if account.AgentData.CharacterName else account.AccountEmail
                variation_index = profession_counts.get(profession_id, 0) % 8
                profession_counts[profession_id] = profession_counts.get(profession_id, 0) + 1
                is_leader = account.AccountEmail == account_email
                color = cls._get_profession_color(profession_id, variation_index)
                characters.append(CharacterData(account.AccountEmail, char_name, profession_id, color, is_leader, secondary_profession_id))
        return characters

    @classmethod
    def _get_profession_color(cls, profession_id: int, variation_index: int) -> Color:
        """Get profession color with variation."""
        color_map = {1: "GW_Warrior", 2: "GW_Ranger", 3: "GW_Monk", 4: "GW_Necromancer", 5: "GW_Mesmer", 6: "GW_Elementalist", 7: "GW_Assassin", 8: "GW_Ritualist", 9: "GW_Paragon", 10: "GW_Dervish"}
        base = ColorPalette.GetColor(color_map.get(profession_id, "")) if profession_id in color_map else Color(128, 128, 128, 255)
        mult = VARIATION_MULTIPLIERS[variation_index % len(VARIATION_MULTIPLIERS)]
        return Color(int(min(255, max(0, base.r * mult))), int(min(255, max(0, base.g * mult))), int(min(255, max(0, base.b * mult))), base.a)

    @classmethod
    def get_assignments_dict(cls) -> dict[int, str]:
        """Get assignments as dict of grid_index -> email."""
        return {i: char.email for i, char in enumerate(cls._grid_assignments) if char is not None}

    @classmethod
    def reset_state(cls) -> None:
        """Reset all state."""
        cls._grid_assignments = [None] * cls.TOTAL_SLOTS
        cls._selected_character = None
        cls._initialized = False

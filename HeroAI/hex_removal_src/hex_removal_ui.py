"""HeroAI/hex_removal_ui.py - Hex Removal configuration tab.

Renders inside the HeroAI Build Matches window as a 4th tab. Profession
sub-tabs hold alphabetical, searchable lists of hexes; clicking a row
toggles inline expand-down configuration. A "Settings" sub-tab holds
Import/Export buttons, a Debug section, and a hard-reset-to-NONE
action. An "Info" sub-tab gives a short usage cheat-sheet. All
persistence delegates to HeroAI.hex_removal_config.
"""

from __future__ import annotations

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, ImGui
from Py4GWCoreLib.GlobalCache.HexRemovalPriority import (
    HEX_REMOVAL_PRIORITY,
    HexRemovalEntry,
    HexRemovalPriority,
    _build_hex_removal_priority,
    get_skill_id_to_name,
)

from .hex_removal_config import (
    ConfigState,
    _NAME_BY_PROFESSION_ID,
    _PROFESSION_BY_NAME,
    _PROFESSION_ORDER,
    clear_override,
    commit_imported,
    export_to_desktop,
    get_debug_flags,
    hard_reset_all_to_none,
    import_from_text,
    set_debug_flags,
    set_override,
)


# ============================================================================
# Constants
# ============================================================================

_PRIORITY_NAMES: list[str] = ["NONE", "LOW", "MED", "HIGH"]
_PRIORITY_VALUES: list[HexRemovalPriority] = [
    HexRemovalPriority.NONE,
    HexRemovalPriority.LOW,
    HexRemovalPriority.MEDIUM,
    HexRemovalPriority.HIGH,
]
_PRIORITY_NAME_BY_VALUE: dict[HexRemovalPriority, str] = dict(
    zip(_PRIORITY_VALUES, _PRIORITY_NAMES)
)
# Used only by the collapsed-row priority preview chips (per user request).
_PRIORITY_COLORS: dict[HexRemovalPriority, tuple[float, float, float, float]] = {
    HexRemovalPriority.NONE:    (0.55, 0.55, 0.55, 1.0),
    HexRemovalPriority.LOW:     (0.85, 0.80, 0.40, 1.0),
    HexRemovalPriority.MEDIUM:  (1.00, 0.65, 0.25, 1.0),
    HexRemovalPriority.HIGH:    (0.95, 0.40, 0.40, 1.0),
}

# Neutral blue-gray for the active priority button. No semantic priority
# tint - chips in the row preview keep the colored values; the configure
# panel uses one uniform highlight.
_ACTIVE_BTN_COLOR: tuple[float, float, float, float] = (0.30, 0.50, 0.70, 1.0)
# Red for the destructive Reset-config button + modal title.
_DANGER_COLOR: tuple[float, float, float, float] = (0.95, 0.55, 0.55, 1.0)

# Row geometry (~37% bigger than the original; icon 32 -> 42, row 32 -> 46).
_ROW_HEIGHT = 46
_ICON_SIZE = 42
_RESET_BTN_W = 70
_RESET_BTN_H = 26
_BUTTON_W = 60
_BUTTON_H = 24
_NAME_FONT = "Bold"
_NAME_FONT_SIZE = 16
_NAME_COLUMN_X = 70
_CHIPS_COLUMN_X = 280

# Configure-panel geometry.
_CFG_LABEL_COL_W = 160
# Vertical offset to center default-size label text against a _BUTTON_H row.
_CFG_LABEL_Y_OFFSET = max(0, (_BUTTON_H - 16) // 2)
# Width of the priority button column inside the configure tables.
_CFG_PRIO_COL_W = _BUTTON_W * 4 + 2 * 3 + 8
_CFG_REMOVE_BTN_W = 70

_HARD_RESET_POPUP_ID = "HardResetConfirm##hex_modal"

# Standard table flags for the dark-blue header bar look used in the
# HeroAI Skill Editor (Widgets/Guild Wars/Customization/HeroAi Skill Editor.py).
_TABLE_FLAGS = (
    PyImGui.TableFlags.Borders
    | PyImGui.TableFlags.RowBg
    | PyImGui.TableFlags.SizingStretchProp
)
# Minimal flags for plain alignment tables in the Info tab (no chrome).
_INFO_TABLE_FLAGS = PyImGui.TableFlags.SizingStretchProp
# Shared label-column width for every Info-tab term/description table so all
# description columns line up. Sized to fit the longest term, which is
# "Export config to desktop" in the Settings tab listing.
_INFO_LABEL_COL_W = 240


# ============================================================================
# State
# ============================================================================

class _State:
    search_text: dict[int, str] = {}
    expanded_hexes: set[str] = set()
    add_override_idx: dict[str, int] = {}
    grouped_cache: dict[int, list[tuple[int, str, str]]] | None = None
    grouped_cache_keycount: int = 0

    show_import_section: bool = False
    import_text_buffer: str = ""
    import_pending_state: ConfigState | None = None
    status_message: str = ""
    status_color: tuple[float, float, float, float] = (0.7, 0.9, 0.7, 1.0)


def _set_status(msg: str, ok: bool = True) -> None:
    _State.status_message = msg
    _State.status_color = (0.7, 0.9, 0.7, 1.0) if ok else (0.95, 0.55, 0.55, 1.0)


def _invalidate_grouped_cache() -> None:
    _State.grouped_cache = None
    _State.grouped_cache_keycount = 0


def _log(msg: str) -> None:
    try:
        from Py4GWCoreLib import ConsoleLog
        import Py4GW
        ConsoleLog("HexRemoval", msg, Py4GW.Console.MessageType.Info)
    except Exception:
        pass


# ============================================================================
# Public entry
# ============================================================================

def draw_tab() -> None:
    if _State.status_message:
        PyImGui.text_colored(_State.status_message, _State.status_color)
    _draw_profession_and_settings_tabs()


# ============================================================================
# Tab bar - profession sub-tabs + Settings + Info (no profession colors)
# ============================================================================

def _draw_profession_and_settings_tabs() -> None:
    grouped = _ensure_grouped_cache()
    if not grouped:
        PyImGui.text("No hexes resolved (skill database not loaded yet?).")
        return

    if PyImGui.begin_tab_bar("HexRemovalProfTabs"):
        for pid in _PROFESSION_ORDER:
            if pid not in grouped:
                continue
            label = _NAME_BY_PROFESSION_ID.get(pid, "?")
            count = len(grouped[pid])
            if PyImGui.begin_tab_item(f"{label} ({count})##hex_prof_{pid}"):
                _draw_profession_content(pid, grouped[pid])
                PyImGui.end_tab_item()

        if 0 in grouped and grouped[0]:
            count = len(grouped[0])
            if PyImGui.begin_tab_item(f"Other ({count})##hex_prof_0"):
                _draw_profession_content(0, grouped[0])
                PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("Settings##hex_settings_tab"):
            _draw_settings_section()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("Info##hex_info_tab"):
            _draw_info_section()
            PyImGui.end_tab_item()

        PyImGui.end_tab_bar()


# ============================================================================
# Settings sub-tab content (Import/Export + Debug + Reset config)
# ============================================================================

def _draw_settings_section() -> None:
    PyImGui.dummy(0, 6)

    if PyImGui.button("Import config##hex_settings_import", 130, 26):
        _State.show_import_section = not _State.show_import_section
        if not _State.show_import_section:
            _State.import_pending_state = None
    PyImGui.same_line(0, 8)
    if PyImGui.button("Export config to desktop##hex_settings_export", 200, 26):
        ok, info = export_to_desktop()
        _set_status(f"Exported to {info}" if ok else f"Export failed: {info}", ok)

    if _State.show_import_section:
        PyImGui.dummy(0, 4)
        _draw_import_section()

    PyImGui.dummy(0, 12)

    # === Debug section (plain bold header) ===
    ImGui.push_font("Bold", 14)
    PyImGui.text("Debug")
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.dummy(0, 4)

    hex_debug, lock_debug = get_debug_flags()
    new_hex = PyImGui.checkbox("Hex removal logs##hex_dbg", hex_debug)
    PyImGui.text_colored(
        "    Logs detection / picking / casting / removed events.",
        (0.7, 0.7, 0.7, 1.0),
    )

    PyImGui.dummy(0, 8)

    new_lock = PyImGui.checkbox("Hex removal lock logs##hex_lock_dbg", lock_debug)
    PyImGui.text_colored(
        "    Logs cross-hero whiteboard POST/CLEAR/SWEEP for hex-removal locks.",
        (0.7, 0.7, 0.7, 1.0),
    )

    if new_hex != hex_debug or new_lock != lock_debug:
        set_debug_flags(new_hex, new_lock)

    PyImGui.dummy(0, 16)

    # === Reset config section ===
    ImGui.push_font("Bold", 14)
    PyImGui.text("Reset config")
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.dummy(0, 4)

    PyImGui.text_colored(
        "Hard reset sets every hex to NONE on caster / ranged-martial / melee\n"
        "and removes every profession override. Irreversible - export your\n"
        "config first if you want a backup.",
        (0.7, 0.7, 0.7, 1.0),
    )
    PyImGui.dummy(0, 4)

    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.55, 0.20, 0.20, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.75, 0.25, 0.25, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.45, 0.15, 0.15, 1.0))
    if PyImGui.button("Hard reset (set everything to NONE)##hex_hard_reset", 320, 26):
        PyImGui.open_popup(_HARD_RESET_POPUP_ID)
    PyImGui.pop_style_color(3)

    _draw_hard_reset_modal()


def _draw_hard_reset_modal() -> None:
    if not PyImGui.begin_popup_modal(
        _HARD_RESET_POPUP_ID, True, PyImGui.WindowFlags.AlwaysAutoResize
    ):
        return

    ImGui.push_font("Bold", 16)
    PyImGui.text_colored("Hard reset - confirm", _DANGER_COLOR)
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.dummy(0, 4)
    PyImGui.text("This will:")
    PyImGui.bullet_text("Set Caster, Ranged-martial, and Melee priorities to NONE")
    PyImGui.bullet_text("Remove every profession override")
    PyImGui.bullet_text("Apply to every hex in every profession sub-tab")
    PyImGui.dummy(0, 4)
    PyImGui.text_colored(
        "This action is IRREVERSIBLE. Export your config to the Desktop\n"
        "first if you want a backup.",
        (1.0, 0.85, 0.4, 1.0),
    )
    PyImGui.dummy(0, 8)

    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.55, 0.20, 0.20, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.75, 0.25, 0.25, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.45, 0.15, 0.15, 1.0))
    if PyImGui.button("Yes, reset everything to NONE##hex_modal_yes", 280, 28):
        hard_reset_all_to_none()
        _log("hard reset: every hex set to NONE on every role")
        _set_status("Hard reset done - all hexes set to NONE.", True)
        PyImGui.close_current_popup()
    PyImGui.pop_style_color(3)

    PyImGui.same_line(0, 8)
    if PyImGui.button("Cancel##hex_modal_no", 100, 28):
        PyImGui.close_current_popup()

    PyImGui.end_popup_modal()


def _draw_import_section() -> None:
    PyImGui.text("Import - paste exported JSONC into clipboard, then Validate.")

    if PyImGui.button("Paste from Clipboard##hex_paste"):
        try:
            _State.import_text_buffer = PyImGui.get_clipboard_text() or ""
            n = len(_State.import_text_buffer)
            _set_status(f"Clipboard captured ({n} chars). Click Validate to check.", True)
        except Exception as exc:
            _set_status(f"Clipboard read failed: {exc!r}", False)
    PyImGui.same_line(0, 8)
    if PyImGui.button("Validate##hex_validate"):
        ok, msg, parsed = import_from_text(_State.import_text_buffer)
        _set_status(msg, ok)
        _State.import_pending_state = parsed if ok else None
    PyImGui.same_line(0, 8)
    if PyImGui.button("Clear##hex_clear_buf"):
        _State.import_text_buffer = ""
        _State.import_pending_state = None
        _set_status("Buffer cleared.", True)

    if _State.import_pending_state is not None:
        n = len(_State.import_pending_state.hexes)
        PyImGui.text_colored(
            f"Ready to import {n} entries. This will REPLACE the active account's config.",
            (1.0, 0.85, 0.4, 1.0),
        )
        if PyImGui.button("Replace##hex_confirm_import"):
            ok = commit_imported(_State.import_pending_state)
            _set_status("Import complete." if ok else "Import failed (write error).", ok)
            _State.import_pending_state = None
            _State.import_text_buffer = ""
            _State.show_import_section = False
            _invalidate_grouped_cache()
        PyImGui.same_line(0, 8)
        if PyImGui.button("Cancel##hex_cancel_import"):
            _State.import_pending_state = None
            _set_status("Import cancelled.", True)


# ============================================================================
# Info sub-tab content (aligned via 2-col tables)
# ============================================================================

def _draw_info_two_col_table(
    table_id: str, label_col_w: int, rows: list[tuple[str, str]]
) -> None:
    """Render label/description rows in clean 2-column alignment."""
    if not PyImGui.begin_table(f"##{table_id}", 2, _INFO_TABLE_FLAGS, 0, 0):
        return
    PyImGui.table_setup_column(
        "##label", PyImGui.TableColumnFlags.WidthFixed, label_col_w
    )
    PyImGui.table_setup_column(
        "##desc", PyImGui.TableColumnFlags.WidthStretch, 0
    )
    for label, desc in rows:
        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0)
        PyImGui.text(label)
        PyImGui.table_set_column_index(1)
        PyImGui.text(desc)
    PyImGui.end_table()


def _draw_info_section() -> None:
    PyImGui.dummy(0, 6)

    ImGui.push_font("Bold", 16)
    PyImGui.text("How Hex Removal works")
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.dummy(0, 4)

    PyImGui.text_wrapped(
        "Each profession sub-tab lists hexes from that profession. Click a row "
        "to expand its configuration. Each hex has a removal priority for three "
        "target roles, plus optional per-profession overrides."
    )

    PyImGui.dummy(0, 10)
    ImGui.push_font("Bold", 14)
    PyImGui.text("Priorities")
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.dummy(0, 2)
    _draw_info_two_col_table("info_priorities", _INFO_LABEL_COL_W, [
        ("NONE", "never remove on this role"),
        ("LOW",  "remove only if nothing better"),
        ("MED",  "standard cleanup"),
        ("HIGH", "urgent removal"),
    ])

    PyImGui.dummy(0, 10)
    ImGui.push_font("Bold", 14)
    PyImGui.text("Roles")
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.dummy(0, 2)
    _draw_info_two_col_table("info_roles", _INFO_LABEL_COL_W, [
        ("Caster",         "Mesmer, Necromancer, Elementalist, Monk, Ritualist"),
        ("Ranged-martial", "Ranger, Paragon"),
        ("Melee",          "Warrior, Assassin, Dervish"),
    ])

    PyImGui.dummy(0, 10)
    ImGui.push_font("Bold", 14)
    PyImGui.text("Profession overrides")
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.text_wrapped(
        "Profession overrides take precedence over the role priority. Example: "
        "a hex with caster=HIGH and {Monk: NONE} stays on monks (NONE) and is "
        "removed urgently from any other caster (HIGH)."
    )

    PyImGui.dummy(0, 10)
    ImGui.push_font("Bold", 14)
    PyImGui.text("Per-row controls")
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.dummy(0, 2)
    _draw_info_two_col_table("info_row_controls", _INFO_LABEL_COL_W, [
        ("Click row",   "expand or collapse the configuration."),
        ("Hover icon",  "show the in-game skill description."),
        ("Reset button", "restore that hex to its default values."),
    ])

    PyImGui.dummy(0, 10)
    ImGui.push_font("Bold", 14)
    PyImGui.text("Settings tab")
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.dummy(0, 2)
    _draw_info_two_col_table("info_settings", _INFO_LABEL_COL_W, [
        ("Import config",            "paste a previously exported config from clipboard."),
        ("Export config to desktop", "save a JSONC file you can back up or share."),
        ("Debug toggles",            "control [HexRemoval] and lock-related console logs."),
        ("Reset config",             "set every hex to NONE everywhere (irreversible)."),
    ])

    PyImGui.dummy(0, 10)
    PyImGui.text_colored(
        "Config file lives at: Settings/<account-email>/HeroAI/Hex removal/"
        "<character-name>/hex_removal_config.json",
        (0.7, 0.7, 0.7, 1.0),
    )


# ============================================================================
# Profession grouping cache
# ============================================================================

def _ensure_grouped_cache() -> dict[int, list[tuple[int, str, str]]]:
    _build_hex_removal_priority()
    keycount = len(HEX_REMOVAL_PRIORITY)
    if _State.grouped_cache is not None and _State.grouped_cache_keycount == keycount:
        return _State.grouped_cache

    name_by_id = get_skill_id_to_name()
    grouped: dict[int, list[tuple[int, str, str]]] = {}
    for sid in HEX_REMOVAL_PRIORITY.keys():
        try:
            prof_value, _ = GLOBAL_CACHE.Skill.GetProfession(sid)
            pid = int(prof_value or 0)
        except Exception:
            pid = 0
        name = name_by_id.get(sid, f"skill#{sid}")
        try:
            texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(sid) or ""
        except Exception:
            texture_path = ""
        grouped.setdefault(pid, []).append((sid, name, texture_path))
    for pid in grouped:
        grouped[pid].sort(key=lambda x: x[1].lower())

    _State.grouped_cache = grouped
    _State.grouped_cache_keycount = keycount
    return grouped


def _draw_profession_content(pid: int, hexes: list[tuple[int, str, str]]) -> None:
    current_search = _State.search_text.get(pid, "")
    new_search = PyImGui.input_text(f"Search##hex_search_{pid}", current_search)
    if new_search != current_search:
        _State.search_text[pid] = new_search

    PyImGui.separator()

    if PyImGui.begin_child(f"##hex_list_{pid}", (0, 0), False, 0):
        search_lower = new_search.strip().lower()
        for skill_id, name, texture_path in hexes:
            if search_lower and search_lower not in name.lower():
                continue
            _draw_hex_row(skill_id, name, texture_path)
        PyImGui.end_child()


# ============================================================================
# Hex row
# ============================================================================

def _draw_hex_row(skill_id: int, name: str, texture_path: str) -> None:
    entry = HEX_REMOVAL_PRIORITY.get(skill_id)
    if entry is None:
        return
    is_expanded = name in _State.expanded_hexes

    avail_x = PyImGui.get_content_region_avail()[0]
    row_start_x, row_start_y = PyImGui.get_cursor_pos()

    reset_zone_w = _RESET_BTN_W + 24
    selectable_w = max(80, avail_x - reset_zone_w)
    if PyImGui.selectable(
        f"##hex_row_{name}",
        is_expanded,
        PyImGui.SelectableFlags.NoFlag,
        (selectable_w, _ROW_HEIGHT),
    ):
        if is_expanded:
            _State.expanded_hexes.discard(name)
        else:
            _State.expanded_hexes.add(name)

    icon_x = row_start_x + 8
    PyImGui.set_cursor_pos(icon_x, row_start_y + (_ROW_HEIGHT - _ICON_SIZE) // 2)
    if texture_path:
        ImGui.DrawTexture(texture_path, _ICON_SIZE, _ICON_SIZE)
    else:
        PyImGui.text("?")
    if PyImGui.is_item_hovered():
        PyImGui.begin_tooltip()
        _draw_skill_tooltip(skill_id)
        PyImGui.end_tooltip()

    text_y = row_start_y + (_ROW_HEIGHT - _NAME_FONT_SIZE - 4) // 2
    PyImGui.set_cursor_pos(row_start_x + _NAME_COLUMN_X, text_y)
    ImGui.push_font(_NAME_FONT, _NAME_FONT_SIZE)
    PyImGui.text(name.replace("_", " "))
    ImGui.pop_font()

    PyImGui.set_cursor_pos(row_start_x + _CHIPS_COLUMN_X, text_y)
    _draw_priority_chips(entry)

    btn_y = row_start_y + (_ROW_HEIGHT - _RESET_BTN_H) // 2
    PyImGui.set_cursor_pos(row_start_x + avail_x - _RESET_BTN_W - 8, btn_y)
    if PyImGui.button(f"Reset##reset_{name}", _RESET_BTN_W, _RESET_BTN_H):
        clear_override(name)
        _log(f"'{name}' - reset to default")
        _set_status(f"Reset '{name}' to default.", True)

    PyImGui.set_cursor_pos(row_start_x, row_start_y + _ROW_HEIGHT + 2)

    if is_expanded:
        _draw_hex_configure(name, entry)

    PyImGui.separator()


def _draw_skill_tooltip(skill_id: int) -> None:
    try:
        from HeroAI.ui_base import HeroAI_BaseUI
        HeroAI_BaseUI._draw_skill_info_card(skill_id, compact=True, tooltip=True)
    except Exception:
        try:
            sname = GLOBAL_CACHE.Skill.GetName(skill_id) or f"skill#{skill_id}"
            PyImGui.text(sname)
        except Exception:
            PyImGui.text(f"skill#{skill_id}")


def _draw_priority_chips(entry: HexRemovalEntry) -> None:
    """Collapsed-row preview - keeps the per-priority colors per user request."""
    role_specs = [
        ("Caster",         entry.caster),
        ("Ranged-martial", entry.ranged_martial),
        ("Melee",          entry.melee),
    ]
    for i, (label, prio) in enumerate(role_specs):
        PyImGui.text(f"{label}:")
        PyImGui.same_line(0, 4)
        PyImGui.text_colored(_PRIORITY_NAME_BY_VALUE[prio], _PRIORITY_COLORS[prio])
        if i < len(role_specs) - 1:
            PyImGui.same_line(0, 14)
    if entry.by_profession:
        n = len(entry.by_profession)
        suffix = "s" if n != 1 else ""
        PyImGui.same_line(0, 14)
        PyImGui.text_colored(f"(+{n} override{suffix})", (0.7, 0.7, 0.95, 1.0))


# ============================================================================
# Configure panel - Skill Editor table style
# ============================================================================

def _draw_hex_configure(name: str, entry: HexRemovalEntry) -> None:
    PyImGui.indent(60)
    PyImGui.dummy(0, 4)

    new_caster = entry.caster
    new_ranged = entry.ranged_martial
    new_melee = entry.melee

    # === Role / Priority section (table with dark-blue header bar) ===
    if PyImGui.begin_table(f"##hex_role_table_{name}", 2, _TABLE_FLAGS, 0, 0):
        PyImGui.table_setup_column(
            "Role", PyImGui.TableColumnFlags.WidthFixed, _CFG_LABEL_COL_W
        )
        PyImGui.table_setup_column(
            "Priority", PyImGui.TableColumnFlags.WidthStretch, 0
        )
        PyImGui.table_headers_row()

        new_caster = _draw_role_priority_table_row("Caster", entry.caster, f"{name}_c")
        new_ranged = _draw_role_priority_table_row(
            "Ranged-martial", entry.ranged_martial, f"{name}_r"
        )
        new_melee = _draw_role_priority_table_row("Melee", entry.melee, f"{name}_m")

        PyImGui.end_table()

    PyImGui.dummy(0, 8)

    # === Profession overrides section (table with dark-blue header bar) ===
    new_by_profession = _draw_profession_overrides_table(name, entry.by_profession)

    PyImGui.dummy(0, 6)
    PyImGui.unindent(60)

    new_entry = HexRemovalEntry(
        caster=new_caster,
        ranged_martial=new_ranged,
        melee=new_melee,
        by_profession=new_by_profession,
    )
    _emit_changes_and_save(name, entry, new_entry)


def _draw_role_priority_table_row(
    label: str, current: HexRemovalPriority, key_suffix: str
) -> HexRemovalPriority:
    """One row of the Role/Priority table with the label vertically centered."""
    PyImGui.table_next_row()
    PyImGui.table_set_column_index(0)
    cell_top_y = PyImGui.get_cursor_pos_y()
    PyImGui.set_cursor_pos_y(cell_top_y + _CFG_LABEL_Y_OFFSET)
    PyImGui.text(label)
    PyImGui.table_set_column_index(1)
    return _draw_priority_segments(current, key_suffix)


def _draw_priority_segments(
    current: HexRemovalPriority, key_suffix: str
) -> HexRemovalPriority:
    """4-button segmented control. Inactive = default grey, active = neutral
    blue-gray (no priority colour). Priority colours are kept in the row
    preview chips only.
    """
    selected = current
    for i, (prio_name, prio_val) in enumerate(zip(_PRIORITY_NAMES, _PRIORITY_VALUES)):
        is_active = (current == prio_val)
        if is_active:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, _ACTIVE_BTN_COLOR)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, _ACTIVE_BTN_COLOR)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, _ACTIVE_BTN_COLOR)
        if PyImGui.button(f"{prio_name}##{key_suffix}_{prio_name}", _BUTTON_W, _BUTTON_H):
            selected = prio_val
        if is_active:
            PyImGui.pop_style_color(3)
        if i < len(_PRIORITY_NAMES) - 1:
            PyImGui.same_line(0, 2)
    return selected


def _draw_profession_overrides_table(
    hex_name: str, current: dict[int, HexRemovalPriority]
) -> dict[int, HexRemovalPriority]:
    new_dict = dict(current)

    if not PyImGui.begin_table(
        f"##hex_overrides_table_{hex_name}", 3, _TABLE_FLAGS, 0, 0
    ):
        return new_dict

    PyImGui.table_setup_column(
        "Profession overrides", PyImGui.TableColumnFlags.WidthFixed, _CFG_LABEL_COL_W
    )
    PyImGui.table_setup_column(
        "Priority", PyImGui.TableColumnFlags.WidthFixed, _CFG_PRIO_COL_W
    )
    PyImGui.table_setup_column(
        "##action_col", PyImGui.TableColumnFlags.WidthStretch, 0
    )
    PyImGui.table_headers_row()

    for pid in _PROFESSION_ORDER:
        if pid not in new_dict:
            continue
        prof_name = _NAME_BY_PROFESSION_ID[pid]

        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0)
        cell_top_y = PyImGui.get_cursor_pos_y()
        PyImGui.set_cursor_pos_y(cell_top_y + _CFG_LABEL_Y_OFFSET)
        PyImGui.text(prof_name)

        PyImGui.table_set_column_index(1)
        new_prio = _draw_priority_segments(new_dict[pid], f"ov_{hex_name}_{pid}")
        if new_prio != new_dict[pid]:
            new_dict[pid] = new_prio

        PyImGui.table_set_column_index(2)
        if PyImGui.button(
            f"Remove##rm_{hex_name}_{pid}", _CFG_REMOVE_BTN_W, _BUTTON_H
        ):
            del new_dict[pid]

    available_pids = [p for p in _PROFESSION_ORDER if p not in new_dict]
    if available_pids:
        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0)
        cell_top_y = PyImGui.get_cursor_pos_y()
        PyImGui.set_cursor_pos_y(cell_top_y + _CFG_LABEL_Y_OFFSET)
        PyImGui.text("Add override:")

        PyImGui.table_set_column_index(1)
        prof_names = [_NAME_BY_PROFESSION_ID[p] for p in available_pids]
        idx = _State.add_override_idx.get(hex_name, 0)
        if idx >= len(prof_names):
            idx = 0
        new_idx = PyImGui.combo(f"##add_prof_{hex_name}", idx, prof_names)
        if new_idx != idx:
            _State.add_override_idx[hex_name] = new_idx
            idx = new_idx

        PyImGui.table_set_column_index(2)
        if PyImGui.button(f"+ Add##add_btn_{hex_name}"):
            new_dict[available_pids[idx]] = HexRemovalPriority.MEDIUM
            _State.add_override_idx[hex_name] = 0

    PyImGui.end_table()
    return new_dict


# ============================================================================
# Per-change logging (no arrow symbol, granular events)
# ============================================================================

def _emit_changes_and_save(
    name: str, old: HexRemovalEntry, new: HexRemovalEntry
) -> None:
    """Diff old vs new entry, emit per-change log lines, save once."""
    changed = (
        old.caster != new.caster
        or old.ranged_martial != new.ranged_martial
        or old.melee != new.melee
        or old.by_profession != new.by_profession
    )
    if not changed:
        return

    role_pairs = [
        ("caster",         old.caster,         new.caster),
        ("ranged_martial", old.ranged_martial, new.ranged_martial),
        ("melee",          old.melee,          new.melee),
    ]
    for role_name, old_val, new_val in role_pairs:
        if old_val != new_val:
            _log(
                f"'{name}' - changed {role_name} priority to "
                f"{_PRIORITY_NAME_BY_VALUE[new_val]}"
            )

    old_overrides = old.by_profession
    new_overrides = new.by_profession
    for pid, prio in new_overrides.items():
        if pid not in old_overrides:
            _log(
                f"'{name}' - added {_NAME_BY_PROFESSION_ID[pid]} override "
                f"({_PRIORITY_NAME_BY_VALUE[prio]})"
            )
        elif old_overrides[pid] != prio:
            _log(
                f"'{name}' - changed {_NAME_BY_PROFESSION_ID[pid]} override to "
                f"{_PRIORITY_NAME_BY_VALUE[prio]}"
            )
    for pid in old_overrides:
        if pid not in new_overrides:
            _log(f"'{name}' - removed {_NAME_BY_PROFESSION_ID[pid]} override")

    set_override(name, new)

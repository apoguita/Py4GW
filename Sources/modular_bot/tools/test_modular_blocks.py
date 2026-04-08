"""
Unified modular block tester with folder-aware selection.

UI flow:
1) Pick kind (Mission / Quest / Route / Farm / Dungeon / Vanquish / Bounty)
2) Pick folder (e.g. prophecies / factions / nightfall / root)
3) Pick block file (without .json)
4) Press Start in ModularBot to run selected block
"""

from __future__ import annotations

import json
import os

import PyImGui

from Sources.modular_bot import ModularBot, Phase
from Sources.modular_bot.hero_setup import draw_configure_teams_section
from Sources.modular_bot.recipes.combat_engine import (
    ENGINE_CUSTOM_BEHAVIORS,
    ENGINE_HERO_AI,
    resolve_active_engine,
)
from Sources.modular_bot.recipes import list_available_blocks, modular_block_run


_KIND_LABEL_TO_KEY: dict[str, str] = {
    "Mission": "missions",
    "Quest": "quests",
    "Route": "routes",
    "Farm": "farms",
    "Dungeon": "dungeons",
    "Vanquish": "vanquishes",
    "Bounty": "bounties",
}
_KIND_ORDER = ["Mission", "Quest", "Route", "Farm", "Dungeon", "Vanquish", "Bounty"]

_selected_kind_label = "Mission"
_selected_folder = ""
_selected_block = ""
_status = ""
_selection_dirty = False
_loop_selected_block = False
_auto_resize_panel = True
_SAFE_MAIN_DIMS: tuple[int, int] = (860, 560)

# Cache: kind_key -> ["folder/name", ...] or ["name", ...]
_blocks_by_kind: dict[str, list[str]] = {}
# Cache: kind_key -> {"folder/name": "Display Name", ...}
_block_display_names: dict[str, dict[str, str]] = {}


def _startup_engine_profile() -> tuple[str, bool, str]:
    """
    Pick tester template/CB mode from currently enabled combat engine.
    """
    try:
        engine = str(resolve_active_engine() or "none").strip().lower()
    except Exception:
        engine = "none"

    if engine == ENGINE_HERO_AI:
        # Keep HeroAI as the active backend.
        return ("multibox_aggressive", False, engine)
    if engine == ENGINE_CUSTOM_BEHAVIORS:
        # Keep CustomBehaviors as the active backend.
        return ("aggressive", True, engine)
    # No external engine active: default to plain aggressive botting.
    return ("aggressive", False, engine)


_START_TEMPLATE, _START_USE_CB, _START_ENGINE = _startup_engine_profile()
_status = f"Startup engine detected: {_START_ENGINE or 'none'}"


def _resolve_modular_root() -> str:
    # Py4GW runtime may execute scripts via exec(...) where __file__ is missing.
    script_file = globals().get("__file__", "")
    if script_file:
        return os.path.normpath(os.path.join(os.path.dirname(str(script_file)), ".."))

    cwd = os.path.abspath(os.getcwd())
    candidate = os.path.join(cwd, "Sources", "modular_bot")
    if os.path.isdir(candidate):
        return os.path.normpath(candidate)
    return os.path.normpath(os.path.join(cwd, "modular_bot"))


def _refresh_cache() -> None:
    global _blocks_by_kind, _block_display_names
    _blocks_by_kind = {kind_key: list_available_blocks(kind=kind_key) for kind_key in _KIND_LABEL_TO_KEY.values()}
    _block_display_names = {}
    modular_root = _resolve_modular_root()
    for kind_key, entries in _blocks_by_kind.items():
        name_map: dict[str, str] = {}
        base_dir = os.path.join(modular_root, kind_key)
        for entry in entries:
            label = entry.split("/")[-1]
            path = os.path.join(base_dir, f"{entry}.json")
            try:
                with open(path, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                json_name = str(data.get("name", "") or "").strip()
                if json_name:
                    label = json_name
            except Exception:
                pass
            name_map[entry] = label
        _block_display_names[kind_key] = name_map


def _get_kind_key() -> str:
    return _KIND_LABEL_TO_KEY.get(_selected_kind_label, "missions")


def _folders_for_kind(kind_key: str) -> list[str]:
    folders = {""}
    for entry in _blocks_by_kind.get(kind_key, []):
        if "/" in entry:
            folders.add(entry.split("/", 1)[0])
    return sorted(folders, key=lambda value: (value != "", value.lower()))


def _blocks_for_folder(kind_key: str, folder: str) -> list[str]:
    entries = _blocks_by_kind.get(kind_key, [])
    filtered: list[str] = []
    prefix = f"{folder}/" if folder else ""
    for entry in entries:
        if folder:
            if not entry.startswith(prefix):
                continue
            filtered.append(entry[len(prefix):])
        else:
            if "/" in entry:
                continue
            filtered.append(entry)
    return sorted(filtered, key=str.lower)


def _selected_block_key() -> str:
    if not _selected_block:
        return ""
    return f"{_selected_folder}/{_selected_block}" if _selected_folder else _selected_block


def _block_display_name(kind_key: str, block_key: str) -> str:
    name_map = _block_display_names.get(kind_key, {})
    return name_map.get(block_key, block_key.split("/")[-1])


def _run_selected_block(bot) -> None:
    from Py4GWCoreLib import ConsoleLog

    global _status
    _ensure_valid_selection()
    key = _selected_block_key()
    if not key:
        _status = "No block selected. Pick kind/folder/block, then press Start."
        ConsoleLog("Modular Block Tester", "Run requested with empty selection; nothing to register.")
        return
    ConsoleLog("Modular Block Tester", f"Registering selection: kind={_get_kind_key()}, block={key}")
    try:
        modular_block_run(bot, key, kind=_get_kind_key(), recipe_name="ModularBlockTest")
        state_count = int(getattr(bot.config.FSM, "get_state_count", lambda: 0)() or 0)
        ConsoleLog("Modular Block Tester", f"FSM states after registration: {state_count}")
    except Exception as exc:
        _status = f"Failed to register block '{key}': {exc}"
        ConsoleLog("Modular Block Tester", _status)


def _mark_selection_dirty(reason: str) -> None:
    global _selection_dirty, _status
    _selection_dirty = True
    _status = reason


def _ensure_valid_selection() -> None:
    global _selected_folder, _selected_block

    if not _blocks_by_kind:
        _refresh_cache()

    kind_key = _get_kind_key()
    folders = _folders_for_kind(kind_key)
    if _selected_folder not in folders:
        _selected_folder = folders[0] if folders else ""
    blocks = _blocks_for_folder(kind_key, _selected_folder)
    if _selected_block not in blocks:
        _selected_block = blocks[0] if blocks else ""


def _apply_pending_selection_rebuild_if_safe() -> None:
    global _selection_dirty, _status
    if not _selection_dirty:
        return

    try:
        cfg = bot.bot.config
        if bool(getattr(cfg, "fsm_running", False)):
            return
        fsm = cfg.FSM

        # Hard-reset FSM graph while stopped so we do not keep stale states
        # from previous selections.
        try:
            fsm.RemoveAllManagedCoroutines()
        except Exception:
            pass
        try:
            fsm.stop()
        except Exception:
            pass

        fsm.states.clear()
        fsm.state_counter = 0
        fsm.current_state = None
        fsm.finished = False
        fsm.paused = False

        # Clear ModularBot phase/header caches; routine build will repopulate.
        try:
            bot._phase_headers.clear()
            bot._header_to_phase.clear()
            bot._runtime_anchor_header = None
        except Exception:
            pass

        cfg.initialized = False
        cfg.fsm_running = False
        cfg.state_description = "Idle"
        _selection_dirty = False
        _status = "Selection applied. Press Start to run the selected block."
    except Exception as exc:
        _status = f"Selection refresh failed: {exc}"


def _draw_main() -> None:
    global _selected_kind_label, _selected_folder, _selected_block, _status, _loop_selected_block, _auto_resize_panel

    if not _blocks_by_kind:
        _refresh_cache()
    _ensure_valid_selection()

    if PyImGui.button("Refresh Blocks"):
        _refresh_cache()
        _ensure_valid_selection()
        _mark_selection_dirty("Refreshed block list. Press Start to apply.")
    PyImGui.same_line(0, 8)
    draw_configure_teams_section(ui_id="modular_block_tester", button_label="Configure Teams")
    loop_now = PyImGui.checkbox("Loop Selected Block", _loop_selected_block)
    if bool(loop_now) != bool(_loop_selected_block):
        _loop_selected_block = bool(loop_now)
        bot._loop = bool(_loop_selected_block)
        _mark_selection_dirty(f"Loop mode set to: {'ON' if _loop_selected_block else 'OFF'}. Press Start to apply.")
    PyImGui.same_line(0, 12)
    auto_resize_now = PyImGui.checkbox("Auto Resize Panel", _auto_resize_panel)
    if bool(auto_resize_now) != bool(_auto_resize_panel):
        _auto_resize_panel = bool(auto_resize_now)
        mode = "enabled" if _auto_resize_panel else "disabled"
        _status = f"Auto Resize Panel {mode}."

    PyImGui.separator()
    PyImGui.text("Kind")
    for idx, label in enumerate(_KIND_ORDER):
        selected = label == _selected_kind_label
        if selected:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.20, 0.45, 0.20, 1.0))
        if PyImGui.button(f"{label}##kind_{label}"):
            _selected_kind_label = label
            _selected_folder = ""
            _selected_block = ""
            _mark_selection_dirty(f"Selected kind: {label}. Press Start to run this selection.")
        if selected:
            PyImGui.pop_style_color(1)
        if idx < len(_KIND_ORDER) - 1:
            PyImGui.same_line(0, 6)

    kind_key = _get_kind_key()
    folders = _folders_for_kind(kind_key)

    PyImGui.separator()
    PyImGui.text("Folder")
    if not folders:
        PyImGui.text("No folders available.")
    else:
        for idx, folder in enumerate(folders):
            folder_label = "[root]" if folder == "" else folder
            selected = folder == _selected_folder
            if selected:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.20, 0.35, 0.50, 1.0))
            if PyImGui.button(f"{folder_label}##folder_{folder_label}_{idx}"):
                _selected_folder = folder
                _selected_block = ""
                _mark_selection_dirty(
                    f"Selected folder: {folder_label}. Press Start to run this selection."
                )
            if selected:
                PyImGui.pop_style_color(1)
            if idx < len(folders) - 1:
                PyImGui.same_line(0, 6)

    blocks = _blocks_for_folder(kind_key, _selected_folder)

    PyImGui.separator()
    PyImGui.text("Blocks")
    if not blocks:
        PyImGui.text("No blocks found for selected kind/folder.")
    else:
        blocks_with_labels = [
            (block, _block_display_name(kind_key, f"{_selected_folder}/{block}" if _selected_folder else block))
            for block in blocks
        ]
        blocks_with_labels.sort(key=lambda item: (item[1].lower(), item[0].lower()))
        if PyImGui.begin_table("modular_blocks_table", 2, PyImGui.TableFlags.SizingStretchSame):
            for idx, (block, display_name) in enumerate(blocks_with_labels):
                PyImGui.table_next_column()
                selected = block == _selected_block
                if selected:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.55, 0.42, 0.12, 1.0))
                if PyImGui.button(f"{idx + 1:02d}. {display_name}##block_{idx}_{block}"):
                    _selected_block = block
                    _mark_selection_dirty(
                        f"Selected block: {_selected_block_key()}. Press Start to run this selection."
                    )
                if selected:
                    PyImGui.pop_style_color(1)
            PyImGui.end_table()

    PyImGui.separator()
    selected_key = _selected_block_key()
    if selected_key:
        PyImGui.text_wrapped(
            f"Selected: kind={kind_key}, folder={_selected_folder or '[root]'}, block={selected_key}"
        )
    else:
        PyImGui.text("Selected: <none>")

    if _status:
        PyImGui.text_wrapped(_status)


def _main_dimensions() -> tuple[int, int]:
    if not _blocks_by_kind:
        _refresh_cache()

    kind_key = _get_kind_key()
    folders = _folders_for_kind(kind_key)
    active_folder = _selected_folder if _selected_folder in folders else (folders[0] if folders else "")
    blocks = _blocks_for_folder(kind_key, active_folder)

    # Blocks render in a 2-column table.
    block_rows = (len(blocks) + 1) // 2

    # Folder buttons are rendered inline; estimate wrapping rows from folder label width.
    folder_label_lengths = [len("[root]" if folder == "" else folder) for folder in folders]
    max_folder_label_len = max(folder_label_lengths, default=6)
    if max_folder_label_len <= 10:
        folder_cols = 6
    elif max_folder_label_len <= 16:
        folder_cols = 5
    elif max_folder_label_len <= 24:
        folder_cols = 4
    else:
        folder_cols = 3
    folder_rows = max(1, (len(folders) + folder_cols - 1) // folder_cols) if folders else 1

    # Base UI rows cover buttons, labels, separators, and selection/status lines.
    base_rows = 16
    total_rows = base_rows + folder_rows + block_rows
    height = max(420, 170 + (total_rows * 26))

    # Expand width a bit when labels are long to reduce wrapping/truncation pressure.
    display_name_map = _block_display_names.get(kind_key, {})
    longest_label = 0
    for block in blocks:
        block_key = f"{active_folder}/{block}" if active_folder else block
        longest_label = max(longest_label, len(display_name_map.get(block_key, block)))
    width = 760 + max(0, min(280, (longest_label - 38) * 5))
    width = max(760, width)
    # Hard cap fallback even when display size isn't available.
    width = min(width, 1200)
    height = min(height, 900)

    # Keep window within the visible display while staying as large as possible.
    try:
        io = PyImGui.get_io()
        display_w = int(getattr(io, "display_size_x", 0) or 0)
        display_h = int(getattr(io, "display_size_y", 0) or 0)
        if display_w > 0:
            width = min(width, max(760, display_w - 120))
        if display_h > 0:
            height = min(height, max(420, display_h - 170))
    except Exception:
        pass

    return (int(width), int(height))


bot = ModularBot(
    name="Modular Block Tester",
    phases=[Phase("Run Selected Modular Block", _run_selected_block, anchor=True)],
    loop=_loop_selected_block,
    template=_START_TEMPLATE,
    use_custom_behaviors=_START_USE_CB,
    upkeep_auto_inventory_management_active=True,
    on_party_wipe="Run Selected Modular Block",
    on_death=None,
    main_ui=_draw_main,
    main_child_dimensions=_SAFE_MAIN_DIMS,
)


def main():
    global _status
    try:
        _apply_pending_selection_rebuild_if_safe()
        if _auto_resize_panel:
            try:
                bot._main_child_dimensions = _main_dimensions()
            except Exception:
                bot._main_child_dimensions = _SAFE_MAIN_DIMS
        else:
            bot._main_child_dimensions = _SAFE_MAIN_DIMS
        bot.update()
    except Exception as exc:
        _status = f"Tester runtime error: {exc}"

from __future__ import annotations

import io
import keyword
import os
import re
import tokenize
from typing import Callable
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

import PyImGui

from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


MODULE_NAME = "Bot Factory"
MODULE_ICON = "Textures/Module_Icons/Template.png"
SCRIPT_REVISION = "2026-03-30-bot-factory-2"
INI_KEY = ""
INI_PATH = "Widgets/BotFactory"
INI_FILENAME = "BotFactory.ini"


def _normalize_input_text(result, current: str) -> str:
    if isinstance(result, tuple):
        if len(result) >= 2:
            return str(result[1])
        if len(result) == 1:
            return str(result[0])
    if result is None:
        return str(current)
    return str(result)


def _add_config_vars() -> None:
    """Register Bot Factory ini-backed configuration values."""
    global INI_KEY
    IniManager().add_bool(INI_KEY, "init", "Window config", "init", default=True)
    IniManager().add_str(INI_KEY, "active_tab", "Tabs", "active_tab", default="Untitled")


def _run_tk_dialog(dialog_callback: Callable[[], str]) -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return str(dialog_callback() or "")
    finally:
        root.destroy()


def _run_tk_bool_dialog(dialog_callback: Callable[[], bool | None]) -> bool | None:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return dialog_callback()
    finally:
        root.destroy()


class BotFactoryCodeRow:
    def __init__(self, source_text: str, markup_text: str = "") -> None:
        self.source_text = source_text
        self.markup_text = markup_text


class BotFactoryPythonLexer:
    def __init__(self) -> None:
        self.builtin_type_names = {
            "str",
            "int",
            "float",
            "bool",
            "bytes",
            "list",
            "dict",
            "tuple",
            "set",
            "frozenset",
            "object",
            "type",
            "None",
        }
        self.color_map: dict[str, Color] = {
            "@plain": ColorPalette.GetColor("white").copy(),
            "@keyword": ColorPalette.GetColor("gw_blue").copy(),
            "@function": ColorPalette.GetColor("khaki").copy(),
            "@string": ColorPalette.GetColor("coral").copy(),
            "@comment": ColorPalette.GetColor("gw_ranger").copy(),
            "@number": ColorPalette.GetColor("sky_blue").copy(),
            "@operator": ColorPalette.GetColor("light_yellow").copy(),
            "@delimiter": ColorPalette.GetColor("light_gold").copy(),
            "@variable": ColorPalette.GetColor("sky_blue").copy(),
            "@type": ColorPalette.GetColor("turquoise").copy(),
        }
        self.color_tuples_map: dict[str, tuple[float, float, float, float]] = {
            key: color.to_tuple_normalized()
            for key, color in self.color_map.items()
        }

    def build_row(self, source_text: str) -> BotFactoryCodeRow:
        return BotFactoryCodeRow(
            source_text=str(source_text),
            markup_text=self.to_markup(str(source_text)),
        )

    def update_row(self, row: BotFactoryCodeRow, source_text: str) -> None:
        row.source_text = str(source_text)
        row.markup_text = self.to_markup(row.source_text)

    def to_markup(self, source_text: str) -> str:
        if not source_text:
            return self._wrap("@plain", "")

        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(source_text).readline))
        except Exception:
            return self._to_markup_fallback(source_text)

        parts: list[str] = []
        cursor_col = 0
        expect_function_name = False
        significant_tokens = [
            token_info
            for token_info in tokens
            if token_info.type not in {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT}
            and token_info.start[0] == 1
        ]
        significant_index_by_id = {
            id(token_info): index
            for index, token_info in enumerate(significant_tokens)
        }

        for token_info in tokens:
            token_type = token_info.type
            token_text = token_info.string
            start_line, start_col = token_info.start

            if token_type in {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL}:
                continue
            if start_line != 1:
                continue

            if start_col > cursor_col:
                gap_text = source_text[cursor_col:start_col]
                parts.append(self._wrap("@plain", gap_text))

            significant_index = significant_index_by_id.get(id(token_info), -1)
            previous_significant_text = (
                significant_tokens[significant_index - 1].string
                if significant_index > 0
                else ""
            )
            next_significant_text = (
                significant_tokens[significant_index + 1].string
                if 0 <= significant_index < len(significant_tokens) - 1
                else ""
            )
            color_key = self._token_color_key(
                token_type,
                token_text,
                expect_function_name,
                previous_significant_text,
                next_significant_text,
            )
            parts.append(self._wrap(color_key, token_text))
            cursor_col = start_col + len(token_text)

            if token_type == tokenize.NAME and token_text == "def":
                expect_function_name = True
            elif token_type == tokenize.NAME and expect_function_name:
                expect_function_name = False

        if cursor_col < len(source_text):
            parts.append(self._wrap("@plain", source_text[cursor_col:]))

        return "".join(parts) if parts else self._wrap("@plain", source_text)

    def _to_markup_fallback(self, source_text: str) -> str:
        token_pattern = re.compile(
            r"(?P<comment>#.*$)"
            r"|(?P<string>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"
            r"|(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
            r"|(?P<number>\d+(?:\.\d+)?)"
            r"|(?P<operator>->|==|!=|<=|>=|//=|\*\*=|//=|:=|[+\-*/%=&|^~<>!.]+)"
            r"|(?P<delimiter>[()\[\]{}:,\.])"
            r"|(?P<whitespace>\s+)"
            r"|(?P<other>.)"
        )

        parts: list[str] = []
        matches = list(token_pattern.finditer(source_text))

        for index, match in enumerate(matches):
            token_kind = match.lastgroup or "other"
            token_text = match.group(0)
            previous_text = matches[index - 1].group(0) if index > 0 else ""
            next_text = matches[index + 1].group(0) if index < len(matches) - 1 else ""

            if token_kind == "comment":
                parts.append(self._wrap("@comment", token_text))
            elif token_kind == "string":
                parts.append(self._wrap("@string", token_text))
            elif token_kind == "name":
                color_key = self._fallback_name_color(token_text, previous_text, next_text)
                parts.append(self._wrap(color_key, token_text))
            elif token_kind == "number":
                parts.append(self._wrap("@number", token_text))
            elif token_kind == "operator":
                parts.append(self._wrap("@operator", token_text))
            elif token_kind == "delimiter":
                color_key = "@operator" if token_text == "." else "@delimiter"
                parts.append(self._wrap(color_key, token_text))
            else:
                parts.append(self._wrap("@plain", token_text))

        return "".join(parts) if parts else self._wrap("@plain", source_text)

    def _fallback_name_color(self, token_text: str, previous_text: str, next_text: str) -> str:
        if keyword.iskeyword(token_text):
            return "@keyword"
        if next_text == "(":
            return "@function"
        if previous_text in {":", "->"}:
            return "@type"
        if token_text in self.builtin_type_names:
            return "@type"
        if token_text[:1].isupper():
            return "@type"
        return "@variable"

    def _token_color_key(
        self,
        token_type: int,
        token_text: str,
        expect_function_name: bool,
        previous_significant_text: str,
        next_significant_text: str,
    ) -> str:
        if token_type == tokenize.NAME:
            if expect_function_name:
                return "@function"
            if keyword.iskeyword(token_text):
                return "@keyword"
            if next_significant_text == "(":
                return "@function"
            if previous_significant_text in {":", "->"}:
                return "@type"
            if token_text in self.builtin_type_names:
                return "@type"
            if token_text[:1].isupper():
                return "@type"
            return "@variable"
        if token_type == tokenize.STRING:
            return "@string"
        if token_type == tokenize.NUMBER:
            return "@number"
        if token_type == tokenize.COMMENT:
            return "@comment"
        if token_type == tokenize.OP:
            if token_text in {"(", ")", "{", "}", "[", "]", ",", ":"}:
                return "@delimiter"
            return "@operator"
        return "@plain"

    def _wrap(self, color_key: str, text: str) -> str:
        return f"<c={color_key}>{text}</c>"


class BotFactoryMenuBar:
    def __init__(self) -> None:
        self.on_add_script: Callable[[], None] | None = None
        self.on_load_script: Callable[[], None] | None = None
        self.on_save_script: Callable[[], None] | None = None
        self.on_copy_script: Callable[[], None] | None = None
        self.on_paste_script_from_clipboard: Callable[[], None] | None = None
        self.on_add_command: Callable[[], None] | None = None
        self.on_add_variable: Callable[[], None] | None = None

    def draw(self) -> None:
        if not PyImGui.begin_menu_bar():
            return

        if PyImGui.begin_menu("File"):
            self._draw_menu_item(f"{IconsFontAwesome5.ICON_FILE_CIRCLE_PLUS} Add Script", self.on_add_script)
            self._draw_menu_item(f"{IconsFontAwesome5.ICON_FOLDER_CLOSED} Load Script", self.on_load_script)
            self._draw_menu_item(f"{IconsFontAwesome5.ICON_SAVE} Save Script", self.on_save_script)
            self._draw_menu_item(f"{IconsFontAwesome5.ICON_CLIPBOARD} Copy Script", self.on_copy_script)
            self._draw_menu_item(f"{IconsFontAwesome5.ICON_PASTE} Paste Script", self.on_paste_script_from_clipboard)
            PyImGui.end_menu()
        if PyImGui.begin_menu("Edit"):
            self._draw_menu_item(f"{IconsFontAwesome5.ICON_PLUS} Add Command", self.on_add_command)
            self._draw_menu_item(f"{IconsFontAwesome5.ICON_PLUS_SQUARE} Add Variable", self.on_add_variable)
            PyImGui.end_menu()
        if PyImGui.begin_menu("View"):
            PyImGui.end_menu()

        PyImGui.end_menu_bar()

    def _draw_menu_item(self, label: str, callback: Callable[[], None] | None) -> None:
        if callback is not None and PyImGui.menu_item(label):
            callback()


class BotFactoryButtonBar:
    def __init__(self) -> None:
        self.height = 35
        self.font_sizes = [12, 14, 16, 18, 20, 22, 24, 28, 32]
        self.selected_font_size_index = self.font_sizes.index(22)
        self.on_add_script: Callable[[], None] | None = None
        self.on_load_script: Callable[[], None] | None = None
        self.on_save_script: Callable[[], None] | None = None
        self.on_copy_script: Callable[[], None] | None = None
        self.on_paste_script_from_clipboard: Callable[[], None] | None = None
        self.on_add_command: Callable[[], None] | None = None
        self.on_add_variable: Callable[[], None] | None = None
        self.on_font_size_changed: Callable[[int], None] | None = None

    def draw(self) -> None:
        if PyImGui.begin_child("BotFactoryTopBar", (0, self.height), True, PyImGui.WindowFlags.NoScrollbar):
            self._draw_button(
                f"{IconsFontAwesome5.ICON_FILE_CIRCLE_PLUS}##Add Script",
                "",
                "Add a new bot script to the factory.",
                callback=self.on_add_script,
            )
            self._draw_button(
                f"{IconsFontAwesome5.ICON_FOLDER_CLOSED}##Load Script",
                "",
                "Load an existing bot script from file.",
                callback=self.on_load_script,
            )
            self._draw_button(
                f"{IconsFontAwesome5.ICON_SAVE}##Save Script",
                "",
                "Save the current bot script to file.",
                callback=self.on_save_script,
            )
            self._draw_button(
                f"{IconsFontAwesome5.ICON_CLIPBOARD}##Copy Script",
                "",
                "Copy the current bot script to clipboard.",
                callback=self.on_copy_script,
            )
            self._draw_button(
                f"{IconsFontAwesome5.ICON_PASTE}##Paste Script",
                "",
                "Create a new bot script from clipboard contents.",
                callback=self.on_paste_script_from_clipboard,
            )
            self._draw_separator()
            self._draw_button(
                f"{IconsFontAwesome5.ICON_PLUS}##Add Command",
                "",
                "Add a new command to the current bot script.",
                callback=self.on_add_command,
            )
            self._draw_button(
                f"{IconsFontAwesome5.ICON_PLUS_SQUARE}##Add Variable",
                "",
                "Add a new variable to the current bot script.",
                callback=self.on_add_variable,
            )
            self._draw_separator()
            PyImGui.text("Font")
            PyImGui.same_line(0, -1)
            PyImGui.push_item_width(50)
            new_index = PyImGui.combo(
                "##BotFactoryFontSize",
                self.selected_font_size_index,
                [str(size) for size in self.font_sizes],
            )
            PyImGui.pop_item_width()
            if new_index != self.selected_font_size_index:
                self.selected_font_size_index = new_index
                if self.on_font_size_changed is not None:
                    self.on_font_size_changed(self.font_sizes[self.selected_font_size_index])
        PyImGui.end_child()

    def _draw_button(self, label: str, click_message: str, tooltip_text: str, callback=None) -> None:
        if PyImGui.button(label):
            if callback is not None:
                callback()
            elif click_message:
                print(click_message)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip(tooltip_text)
        PyImGui.same_line(0, -1)

    def _draw_separator(self) -> None:
        PyImGui.text("|")
        PyImGui.same_line(0, -1)


class BotFactoryDetailDisplay:
    def __init__(self) -> None:
        self.lexer = BotFactoryPythonLexer()
        self.font_size = 22
        self.rows: list[BotFactoryCodeRow] = [
            self.lexer.build_row("Main Column"),
        ]
        self.row_clipboard = ""
        self.saved_snapshot = ""
        self.pending_direct_action: tuple[str, int] | None = None
        self.modal_popup_id = "BotFactoryRowEditorModal"
        self.modal_open_requested = False
        self.modal_action = ""
        self.modal_row_index = -1
        self.modal_input_text = ""
        self.document_modal_popup_id = "BotFactoryDocumentModal"
        self.document_modal_open_requested = False
        self.document_modal_action = ""
        self.document_modal_preview = ""

    def draw(self) -> None:
        outer_child_flags = PyImGui.WindowFlags.HorizontalScrollbar
        if PyImGui.begin_child("BotFactoryTableOuterChild", (0, 0), True, outer_child_flags):
            table_width = self._get_scroll_dummy_width()
            table_flags = (
                PyImGui.TableFlags.Borders
                | PyImGui.TableFlags.RowBg
            )

            if PyImGui.begin_table("BotFactoryMainTable", 2, table_flags, table_width, 0):
                self._draw_table()
                PyImGui.end_table()
            ImGui.dummy(table_width, 1)
        PyImGui.end_child()
        self._apply_pending_direct_action()
        self._draw_row_editor_modal()
        self._draw_document_modal()

    def get_document_text(self) -> str:
        return "\n".join(row.source_text for row in self.rows)

    def copy_document_to_clipboard(self) -> None:
        PyImGui.set_clipboard_text(self.get_document_text())

    def save_document(self) -> None:
        self.saved_snapshot = self.get_document_text()

    def load_document_text(self, document_text: str) -> None:
        loaded_rows = str(document_text).splitlines()
        self.rows = [self.lexer.build_row(text) for text in loaded_rows] if loaded_rows else [self.lexer.build_row("")]

    def request_add_command(self) -> None:
        self._open_row_modal("Add Command", len(self.rows) - 1, "")

    def request_add_variable(self) -> None:
        self._open_row_modal("Add Variable", len(self.rows) - 1, "")

    def request_new_script(self) -> None:
        self.document_modal_action = "Add Script"
        self.document_modal_preview = ""
        self.document_modal_open_requested = True

    def request_load_script(self) -> None:
        self.document_modal_action = "Load Script"
        self.document_modal_preview = PyImGui.get_clipboard_text() or ""
        self.document_modal_open_requested = True

    def _draw_table(self) -> None:
        PyImGui.table_setup_column("#", PyImGui.TableColumnFlags.WidthFixed, 36.0)
        PyImGui.table_setup_column("Command", PyImGui.TableColumnFlags.WidthStretch, 0.0)
        PyImGui.table_headers_row()

        for row_index, row in enumerate(self.rows, start=1):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            PyImGui.text(str(row_index))
            PyImGui.table_next_column()
            popup_id = f"BotFactoryRowContext##{row_index}"
            self._draw_markup_row(row, row_index)
            if PyImGui.is_item_hovered() and PyImGui.is_mouse_clicked(1):
                PyImGui.open_popup(popup_id)
            self._draw_row_context_menu(popup_id, row_index)

    def _draw_markup_row(self, row: BotFactoryCodeRow, row_index: int) -> None:
        render_width = self._measure_row_width(row)
        row_height = max(PyImGui.get_text_line_height_with_spacing() + 6.0, 24.0)
        tokenized_lines = Utils.TokenizeMarkupText(row.markup_text, max_width=max(render_width, 100000.0))
        child_flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse

        if PyImGui.begin_child(f"BotFactoryRowRender##{row_index}", (render_width, row_height), False, child_flags):
            ImGui.push_font("Regular", self.font_size)
            ImGui.render_tokenized_markup(
                tokenized_lines,
                max_width=render_width,
                COLOR_MAP=self.lexer.color_tuples_map,
            )
            ImGui.pop_font()
        PyImGui.end_child()

    def set_font_size(self, font_size: int) -> None:
        self.font_size = max(8, int(font_size))

    def _get_scroll_dummy_width(self) -> float:
        row_number_width = 36.0
        content_width = max((self._measure_row_width(row) for row in self.rows), default=120.0)
        return row_number_width + content_width

    def _measure_row_width(self, row: BotFactoryCodeRow) -> float:
        ImGui.push_font("Regular", self.font_size)
        try:
            text_width = PyImGui.calc_text_size(row.source_text if row.source_text else " ")[0]
        finally:
            ImGui.pop_font()
        token_spacing = max(row.markup_text.count("</c><c=") * 2.0, 0.0)
        renderer_padding = 48.0
        return max(text_width + token_spacing + renderer_padding, 120.0)

    def _draw_row_context_menu(self, popup_id: str, row_index: int) -> None:
        if not PyImGui.begin_popup(popup_id):
            return

        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_CUT} Cut", "cut", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_COPY} Copy", "copy", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_PASTE} Paste", "paste", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_PEN} Edit Row", "edit", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_PLUS} Insert Above", "insert_above", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_PLUS_SQUARE} Insert Below", "insert_below", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_ARROW_UP} Move Up", "move_up", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_ARROW_DOWN} Move Down", "move_down", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_TRASH} Delete Row", "delete", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_PLUS} Add Command", "add_command", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_PLUS_SQUARE} Add Variable", "add_variable", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_SAVE} Save", "save", row_index)
        self._draw_row_context_action(f"{IconsFontAwesome5.ICON_CLIPBOARD} Copy To Clipboard", "copy_to_clipboard", row_index)

        PyImGui.end_popup()

    def _draw_row_context_action(self, menu_label: str, action_name: str, row_index: int) -> None:
        if PyImGui.menu_item(menu_label):
            self._handle_row_action(action_name, row_index)

    def _handle_row_action(self, action_name: str, row_index: int) -> None:
        row_offset = row_index - 1
        if row_offset < 0 or row_offset >= len(self.rows):
            return

        if action_name == "copy":
            self.row_clipboard = self.rows[row_offset].source_text
            PyImGui.set_clipboard_text(self.row_clipboard)
            return
        if action_name == "copy_to_clipboard":
            PyImGui.set_clipboard_text(self.rows[row_offset].source_text)
            return
        if action_name == "cut":
            self.row_clipboard = self.rows[row_offset].source_text
            PyImGui.set_clipboard_text(self.row_clipboard)
            self.pending_direct_action = ("delete", row_offset)
            return
        if action_name in {"move_up", "move_down", "delete", "save"}:
            self.pending_direct_action = (action_name, row_offset)
            return
        if action_name == "paste":
            initial_text = self.row_clipboard or PyImGui.get_clipboard_text()
            self._open_row_modal("Paste Row", row_offset, initial_text)
            return
        if action_name == "edit":
            self._open_row_modal("Edit Row", row_offset, self.rows[row_offset].source_text)
            return
        if action_name == "insert_above":
            self._open_row_modal("Insert Row Above", row_offset, "")
            return
        if action_name == "insert_below":
            self._open_row_modal("Insert Row Below", row_offset, "")
            return
        if action_name == "add_command":
            self._open_row_modal("Add Command", row_offset, "")
            return
        if action_name == "add_variable":
            self._open_row_modal("Add Variable", row_offset, "")

    def _open_row_modal(self, action_name: str, row_index: int, initial_text: str) -> None:
        self.modal_action = action_name
        self.modal_row_index = row_index
        self.modal_input_text = initial_text
        self.modal_open_requested = True

    def _apply_pending_direct_action(self) -> None:
        if self.pending_direct_action is None:
            return

        action_name, row_index = self.pending_direct_action
        self.pending_direct_action = None

        if row_index < 0 or row_index >= len(self.rows):
            return

        if action_name == "move_up" and row_index > 0:
            self.rows[row_index - 1], self.rows[row_index] = self.rows[row_index], self.rows[row_index - 1]
            return
        if action_name == "move_down" and row_index < len(self.rows) - 1:
            self.rows[row_index + 1], self.rows[row_index] = self.rows[row_index], self.rows[row_index + 1]
            return
        if action_name == "delete":
            if len(self.rows) == 1:
                self.lexer.update_row(self.rows[0], "")
            else:
                self.rows.pop(row_index)
            return
        if action_name == "save":
            self.save_document()

    def _draw_row_editor_modal(self) -> None:
        if self.modal_open_requested:
            PyImGui.open_popup(self.modal_popup_id)
            self.modal_open_requested = False

        if not PyImGui.begin_popup_modal(self.modal_popup_id, True, PyImGui.WindowFlags.AlwaysAutoResize):
            return

        PyImGui.text(self.modal_action or "Row Editor")
        PyImGui.separator()
        self.modal_input_text = _normalize_input_text(
            ImGui.input_text("Row Text", self.modal_input_text, 0),
            self.modal_input_text,
        )
        PyImGui.spacing()

        if PyImGui.button("Confirm", 90, 0):
            self._commit_modal_action()
            PyImGui.close_current_popup()
        PyImGui.same_line(0, -1)
        if PyImGui.button("Cancel", 90, 0):
            self._reset_modal_state()
            PyImGui.close_current_popup()

        PyImGui.end_popup_modal()

    def _commit_modal_action(self) -> None:
        row_index = self.modal_row_index
        row_text = self.modal_input_text

        if self.modal_action == "Paste Row" and 0 <= row_index < len(self.rows):
            self.lexer.update_row(self.rows[row_index], row_text)
        elif self.modal_action == "Edit Row" and 0 <= row_index < len(self.rows):
            self.lexer.update_row(self.rows[row_index], row_text)
        elif self.modal_action == "Insert Row Above" and 0 <= row_index <= len(self.rows):
            self.rows.insert(row_index, self.lexer.build_row(row_text))
        elif self.modal_action == "Insert Row Below" and 0 <= row_index < len(self.rows):
            self.rows.insert(row_index + 1, self.lexer.build_row(row_text))
        elif self.modal_action in {"Add Command", "Add Variable"} and 0 <= row_index < len(self.rows):
            self.rows.insert(row_index + 1, self.lexer.build_row(row_text))

        self._reset_modal_state()

    def _reset_modal_state(self) -> None:
        self.modal_action = ""
        self.modal_row_index = -1
        self.modal_input_text = ""

    def _draw_document_modal(self) -> None:
        if self.document_modal_open_requested:
            PyImGui.open_popup(self.document_modal_popup_id)
            self.document_modal_open_requested = False

        if not PyImGui.begin_popup_modal(self.document_modal_popup_id, True, PyImGui.WindowFlags.AlwaysAutoResize):
            return

        PyImGui.text(self.document_modal_action or "Document Action")
        PyImGui.separator()

        if self.document_modal_action == "Add Script":
            PyImGui.text_wrapped("Create a new empty script and replace the current rows.")
        elif self.document_modal_action == "Load Script":
            PyImGui.text_wrapped("Import the current clipboard contents into rows. Each line becomes one row.")
            PyImGui.separator()
            preview_text = self.document_modal_preview if self.document_modal_preview else "(Clipboard is empty)"
            PyImGui.text_wrapped(preview_text)

        PyImGui.spacing()
        if PyImGui.button("Confirm", 90, 0):
            self._commit_document_modal_action()
            PyImGui.close_current_popup()
        PyImGui.same_line(0, -1)
        if PyImGui.button("Cancel", 90, 0):
            self._reset_document_modal_state()
            PyImGui.close_current_popup()

        PyImGui.end_popup_modal()

    def _commit_document_modal_action(self) -> None:
        if self.document_modal_action == "Add Script":
            self.rows = [self.lexer.build_row("")]
            self.saved_snapshot = ""
        elif self.document_modal_action == "Load Script":
            clipboard_text = PyImGui.get_clipboard_text() or ""
            loaded_rows = clipboard_text.splitlines()
            self.rows = [self.lexer.build_row(text) for text in loaded_rows] if loaded_rows else [self.lexer.build_row("")]

        self._reset_document_modal_state()

    def _reset_document_modal_state(self) -> None:
        self.document_modal_action = ""
        self.document_modal_preview = ""


class BotFactoryDetailTabs:
    def __init__(self) -> None:
        self.tabs: list[BotFactoryDocumentTab] = []
        self.active_tab_index = 0
        self.font_size = 22
        self._next_tab_number = 1
        self.rename_popup_id = "BotFactoryRenameTabModal"
        self.rename_tab_index = -1
        self.rename_input_text = ""
        self.rename_popup_open_requested = False
        self._append_new_tab()

    def _append_new_tab(self, file_path: str = "", document_text: str = "") -> "BotFactoryDocumentTab":
        tab_label = os.path.basename(file_path) if file_path else f"Untitled {self._next_tab_number}"
        self._next_tab_number += 1
        tab = BotFactoryDocumentTab(tab_label, self.font_size, file_path=file_path)
        tab.detail_display.load_document_text(document_text)
        self.tabs.append(tab)
        self.active_tab_index = len(self.tabs) - 1
        return tab

    def _get_active_tab(self) -> "BotFactoryDocumentTab":
        if not self.tabs:
            self._append_new_tab()
        self.active_tab_index = max(0, min(self.active_tab_index, len(self.tabs) - 1))
        return self.tabs[self.active_tab_index]

    def load_from_ini(self, ini_key: str) -> None:
        active_label = IniManager().getStr(ini_key, "active_tab", self._get_active_tab().tab_label, section="Tabs")
        for index, tab in enumerate(self.tabs):
            if tab.tab_label == active_label:
                self.active_tab_index = index
                break

    def save_to_ini(self, ini_key: str) -> None:
        IniManager().set(ini_key, "active_tab", self._get_active_tab().tab_label, section="Tabs")

    def copy_document_to_clipboard(self) -> None:
        self._get_active_tab().detail_display.copy_document_to_clipboard()

    def save_document(self) -> None:
        self.save_document_as_file()

    def request_add_command(self) -> None:
        self._get_active_tab().detail_display.request_add_command()

    def request_add_variable(self) -> None:
        self._get_active_tab().detail_display.request_add_variable()

    def request_new_script(self) -> None:
        self._append_new_tab()

    def request_load_script(self) -> None:
        file_path = _run_tk_dialog(
            lambda: filedialog.askopenfilename(
                title="Open Script",
                filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
            )
        )
        if not file_path:
            return
        with open(file_path, "r", encoding="utf-8") as file_handle:
            document_text = file_handle.read()
        self._append_new_tab(file_path=file_path, document_text=document_text)

    def set_font_size(self, font_size: int) -> None:
        self.font_size = font_size
        for tab in self.tabs:
            tab.detail_display.set_font_size(font_size)

    def save_document_as_file(self) -> None:
        active_tab = self._get_active_tab()
        file_path = active_tab.file_path or self._prompt_save_path(active_tab)
        if not file_path:
            return
        self._write_tab_to_file(active_tab, file_path)

    def paste_script_from_clipboard(self) -> None:
        clipboard_text = PyImGui.get_clipboard_text() or ""
        file_path = _run_tk_dialog(
            lambda: filedialog.asksaveasfilename(
                title="Paste Script From Clipboard",
                defaultextension=".py",
                filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
                initialfile=f"Clipboard Script {self._next_tab_number}.py",
            )
        )
        if not file_path:
            return
        with open(file_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(clipboard_text)
        self._append_new_tab(file_path=file_path, document_text=clipboard_text)

    def draw(self) -> None:
        tab_bar_flags = PyImGui.TabBarFlags.AutoSelectNewTabs | PyImGui.TabBarFlags.Reorderable
        if not PyImGui.begin_tab_bar("BotFactoryDetailTabs", tab_bar_flags):
            self._draw_rename_tab_modal()
            return

        close_tab_index: int | None = None
        close_other_tabs_index: int | None = None
        for index, tab in enumerate(list(self.tabs)):
            opened, is_open = PyImGui.begin_tab_item_closable(tab.tab_label, True, PyImGui.TabItemFlags.NoFlag)
            if opened:
                self.active_tab_index = index
                tab.detail_display.draw()
                PyImGui.end_tab_item()
            if not is_open and close_tab_index is None:
                close_tab_index = index
            if PyImGui.is_item_hovered() and PyImGui.is_mouse_clicked(1):
                PyImGui.open_popup(f"BotFactoryTabContext##{index}")
            if PyImGui.begin_popup(f"BotFactoryTabContext##{index}"):
                if PyImGui.menu_item(f"{IconsFontAwesome5.ICON_PEN} Rename Tab"):
                    self.rename_tab_index = index
                    self.rename_input_text = tab.tab_label
                    self.rename_popup_open_requested = True
                if PyImGui.menu_item(f"{IconsFontAwesome5.ICON_SQUARE_XMARK} Close Tab"):
                    close_tab_index = index
                if PyImGui.menu_item(f"{IconsFontAwesome5.ICON_LAYER_GROUP} Close Others"):
                    close_other_tabs_index = index
                PyImGui.end_popup()

        PyImGui.end_tab_bar()
        if close_other_tabs_index is not None and 0 <= close_other_tabs_index < len(self.tabs):
            self._close_other_tabs(close_other_tabs_index)
        elif close_tab_index is not None:
            self._close_tab(close_tab_index)
        self._draw_rename_tab_modal()

    def _close_tab(self, tab_index: int) -> None:
        if not (0 <= tab_index < len(self.tabs)):
            return
        if not self._save_tab_on_close(tab_index):
            return
        if len(self.tabs) == 1:
            self.tabs[0] = BotFactoryDocumentTab(f"Untitled {self._next_tab_number}", self.font_size)
            self._next_tab_number += 1
            self.active_tab_index = 0
            return
        self.tabs.pop(tab_index)
        if self.active_tab_index >= len(self.tabs):
            self.active_tab_index = len(self.tabs) - 1
        elif tab_index <= self.active_tab_index:
            self.active_tab_index = max(0, self.active_tab_index - 1)

    def _close_other_tabs(self, keep_index: int) -> None:
        if not (0 <= keep_index < len(self.tabs)):
            return
        for index in range(len(self.tabs) - 1, -1, -1):
            if index == keep_index:
                continue
            if not self._save_tab_on_close(index):
                return
            self.tabs.pop(index)
            if index < keep_index:
                keep_index -= 1
        self.active_tab_index = keep_index

    def _save_tab_on_close(self, tab_index: int) -> bool:
        if not (0 <= tab_index < len(self.tabs)):
            return False
        tab = self.tabs[tab_index]
        save_choice = _run_tk_bool_dialog(
            lambda: messagebox.askyesnocancel(
                "Save Script",
                f"Do you want to save '{tab.tab_label}' before closing?",
            )
        )
        if save_choice is None:
            return False
        if save_choice is False:
            return True
        file_path = tab.file_path or self._prompt_save_path(tab)
        if not file_path:
            return False
        self._write_tab_to_file(tab, file_path)
        return True

    def _prompt_save_path(self, tab: "BotFactoryDocumentTab") -> str:
        return _run_tk_dialog(
            lambda: filedialog.asksaveasfilename(
                title="Save Script",
                defaultextension=".py",
                filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
                initialfile=f"{tab.tab_label}.py" if not tab.file_path else os.path.basename(tab.file_path),
            )
        )

    def _write_tab_to_file(self, tab: "BotFactoryDocumentTab", file_path: str) -> None:
        with open(file_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(tab.detail_display.get_document_text())
        tab.set_file_path(file_path)
        tab.detail_display.save_document()

    def _draw_rename_tab_modal(self) -> None:
        if self.rename_popup_open_requested:
            PyImGui.open_popup(self.rename_popup_id)
            self.rename_popup_open_requested = False

        if not PyImGui.begin_popup_modal(self.rename_popup_id, True, PyImGui.WindowFlags.AlwaysAutoResize):
            return

        PyImGui.text("Rename Tab")
        PyImGui.separator()
        self.rename_input_text = _normalize_input_text(
            ImGui.input_text("Tab Name", self.rename_input_text, 0),
            self.rename_input_text,
        )
        PyImGui.spacing()

        if PyImGui.button("Confirm", 90, 0):
            self._commit_rename_tab()
            PyImGui.close_current_popup()
        PyImGui.same_line(0, -1)
        if PyImGui.button("Cancel", 90, 0):
            self._reset_rename_tab_state()
            PyImGui.close_current_popup()

        PyImGui.end_popup_modal()

    def _commit_rename_tab(self) -> None:
        if 0 <= self.rename_tab_index < len(self.tabs):
            new_label = self.rename_input_text.strip()
            if new_label:
                self.tabs[self.rename_tab_index].tab_label = new_label
        self._reset_rename_tab_state()

    def _reset_rename_tab_state(self) -> None:
        self.rename_tab_index = -1
        self.rename_input_text = ""


class BotFactoryDocumentTab:
    def __init__(self, tab_label: str, font_size: int, file_path: str = "") -> None:
        self.tab_label = tab_label
        self.file_path = file_path
        self.detail_display = BotFactoryDetailDisplay()
        self.detail_display.set_font_size(font_size)

    def set_file_path(self, file_path: str) -> None:
        self.file_path = file_path
        if file_path:
            self.tab_label = os.path.basename(file_path)


class BotFactoryWindow:
    def __init__(self) -> None:
        self.menu_bar = BotFactoryMenuBar()
        self.button_bar = BotFactoryButtonBar()
        self.detail_tabs = BotFactoryDetailTabs()
        self.menu_bar.on_add_script = self.request_new_script
        self.menu_bar.on_load_script = self.request_load_script
        self.menu_bar.on_save_script = self.save_document
        self.menu_bar.on_copy_script = self.copy_document_to_clipboard
        self.menu_bar.on_paste_script_from_clipboard = self.paste_script_from_clipboard
        self.menu_bar.on_add_command = self.request_add_command
        self.menu_bar.on_add_variable = self.request_add_variable
        self.button_bar.on_add_script = self.request_new_script
        self.button_bar.on_load_script = self.request_load_script
        self.button_bar.on_save_script = self.save_document
        self.button_bar.on_copy_script = self.copy_document_to_clipboard
        self.button_bar.on_paste_script_from_clipboard = self.paste_script_from_clipboard
        self.button_bar.on_add_command = self.request_add_command
        self.button_bar.on_add_variable = self.request_add_variable
        self.button_bar.on_font_size_changed = self.set_font_size

    def draw(self, ini_key: str) -> None:
        PyImGui.set_next_window_size_constraints((400.0, 400.0), (0.0, 0.0))
        window_flags = PyImGui.WindowFlags.MenuBar
        if ImGui.Begin(ini_key, MODULE_NAME, flags=window_flags):
            self.menu_bar.draw()
            self.button_bar.draw()
            self.detail_tabs.draw()
        self.save_to_ini(ini_key)
        ImGui.End(ini_key)

    def load_from_ini(self, ini_key: str) -> None:
        self.detail_tabs.load_from_ini(ini_key)

    def save_to_ini(self, ini_key: str) -> None:
        self.detail_tabs.save_to_ini(ini_key)

    def copy_document_to_clipboard(self) -> None:
        self.detail_tabs.copy_document_to_clipboard()

    def save_document(self) -> None:
        self.detail_tabs.save_document()

    def request_add_command(self) -> None:
        self.detail_tabs.request_add_command()

    def request_add_variable(self) -> None:
        self.detail_tabs.request_add_variable()

    def request_new_script(self) -> None:
        self.detail_tabs.request_new_script()

    def request_load_script(self) -> None:
        self.detail_tabs.request_load_script()

    def set_font_size(self, font_size: int) -> None:
        self.detail_tabs.set_font_size(font_size)

    def paste_script_from_clipboard(self) -> None:
        self.detail_tabs.paste_script_from_clipboard()


app = BotFactoryWindow()


def tooltip() -> None:
    PyImGui.begin_tooltip()
    PyImGui.text(MODULE_NAME)
    PyImGui.separator()
    PyImGui.text("Bot Factory UI shell.")
    PyImGui.end_tooltip()


def main() -> None:
    if not _initialize():
        return
    app.draw(INI_KEY)


initialized = False


def _initialize() -> bool:
    global INI_KEY, initialized
    if initialized:
        return True

    if not INI_KEY:
        INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
        if not INI_KEY:
            return False
        _add_config_vars()
        IniManager().load_once(INI_KEY)
        IniManager().set(INI_KEY, "init", True, section="Window config")
        IniManager().save_vars(INI_KEY)

    app.load_from_ini(INI_KEY)
    initialized = True
    return True


if __name__ == "__main__":
    main()

from __future__ import annotations

import PyImGui

from Py4GWCoreLib import ImGui


MODULE_NAME = "Bot Factory"
MODULE_ICON = "Textures/Module_Icons/Template.png"
SCRIPT_REVISION = "2026-03-30-bot-factory-2"


class BotFactoryApp:
    def draw(self) -> None:
        PyImGui.set_next_window_size_constraints((400.0, 400.0), (0.0, 0.0))
        window_flags = PyImGui.WindowFlags.MenuBar
        if ImGui.Begin(MODULE_NAME, MODULE_NAME, flags=window_flags):
            self._draw_menu_bar()
            self._draw_top_bar()
            self._draw_main_table()
        ImGui.End(MODULE_NAME)

    def _draw_menu_bar(self) -> None:
        if not PyImGui.begin_menu_bar():
            return

        if PyImGui.begin_menu("File"):
            PyImGui.end_menu()
        if PyImGui.begin_menu("Edit"):
            PyImGui.end_menu()
        if PyImGui.begin_menu("View"):
            PyImGui.end_menu()

        PyImGui.end_menu_bar()

    def _draw_top_bar(self) -> None:
        top_bar_height = 56
        if PyImGui.begin_child("BotFactoryTopBar", (0, top_bar_height), True, PyImGui.WindowFlags.NoScrollbar):
            PyImGui.text("Top Area")
        PyImGui.end_child()

    def _draw_main_table(self) -> None:
        rows = ["Main Column"]
        child_flags = PyImGui.WindowFlags.HorizontalScrollbar | PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin_child("BotFactoryTableChild", (0, 0), True, child_flags):
            table_flags = (
                PyImGui.TableFlags.Borders
                | PyImGui.TableFlags.RowBg
                | PyImGui.TableFlags.Resizable
                | PyImGui.TableFlags.ScrollX
                | PyImGui.TableFlags.ScrollY
            )

            if PyImGui.begin_table("BotFactoryMainTable", 2, table_flags):
                PyImGui.table_setup_column("#", PyImGui.TableColumnFlags.WidthFixed, 36.0)
                PyImGui.table_setup_column("Command", PyImGui.TableColumnFlags.WidthStretch, 0.0)
                PyImGui.table_headers_row()

                for row_index, row_text in enumerate(rows, start=1):
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(str(row_index))
                    PyImGui.table_next_column()
                    PyImGui.text(row_text)

                PyImGui.end_table()
        PyImGui.end_child()


app = BotFactoryApp()


def tooltip() -> None:
    PyImGui.begin_tooltip()
    PyImGui.text(MODULE_NAME)
    PyImGui.separator()
    PyImGui.text("Bot Factory UI shell.")
    PyImGui.end_tooltip()


def main() -> None:
    app.draw()


if __name__ == "__main__":
    main()

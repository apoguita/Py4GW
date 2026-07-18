from Py4GWCoreLib import *

MODULE_NAME = "Color Palette Explorer"
MODULE_ICON = "Textures/Module_Icons/Color Palette.png"

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Color Palette Explorer", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An interactive reference library for the Py4GW constant color")
    PyImGui.text("palette. This utility allows for quick browsing of predefined")
    PyImGui.text("colors with instant code generation for style implementation.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Visual Grid: Displays the full range of colors from the ColorPalette library")
    PyImGui.bullet_text("Adaptive Buttons: Each entry uses its own color for its 'Copy' button background")
    PyImGui.bullet_text("Contrast Logic: Automatically negates text color to ensure visibility on any background")
    PyImGui.bullet_text("Quick Copy: Copy the raw color name directly to your clipboard")
    PyImGui.bullet_text("Code Snippets: Copy the full 'ColorPalette.GetColor()' method call for easy pasting")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()

def main():
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):

        # 3 colors per row → 3 columns per color → 9 columns
        if PyImGui.begin_table(
            "color_table",
            9,
            PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg
        ):
            # Headers (visible text the same, IDs disambiguated with ##)
            PyImGui.table_setup_column("Name##1")
            PyImGui.table_setup_column("NAME##1")
            PyImGui.table_setup_column("Copy##1")

            PyImGui.table_setup_column("Name##2")
            PyImGui.table_setup_column("NAME##2")
            PyImGui.table_setup_column("Copy##2")

            PyImGui.table_setup_column("Name##3")
            PyImGui.table_setup_column("NAME##3")
            PyImGui.table_setup_column("Copy##3")

            PyImGui.table_headers_row()

            colors = list(ColorPalette.ListColors())
            total = len(colors)

            # Process colors in chunks of 3 per row
            i = 0
            while i < total:
                PyImGui.table_next_row()

                # up to 3 colors in this row
                for slot in range(3):
                    idx = i + slot
                    if idx >= total:
                        # No more colors → leave remaining cells empty
                        continue

                    color_name = colors[idx]
                    color = ColorPalette.GetColor(color_name)
                    norm = color.to_tuple_normalized()

                    # Column base for this slot (0, 3, 6)
                    base_col = slot * 3

                    # ---- (Name) ----
                    PyImGui.table_set_column_index(base_col + 0)
                    PyImGui.text_colored(color_name.upper(), norm)
                    if PyImGui.is_item_hovered():
                        PyImGui.set_tooltip(
                            f"{color_name} = Color{str(color.get_rgba())}"
                        )

                    # ---- (NAME button) ----
                    PyImGui.table_set_column_index(base_col + 1)
                    button_color = color.to_tuple_normalized()
                    hovered_color = color.saturate(1.2).to_tuple_normalized()
                    active_color = color.saturate(0.8).to_tuple_normalized()
                    text_color = color.Negate().to_tuple_normalized()

                    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, button_color)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hovered_color)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active_color)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, text_color)

                    btn_label = f"Copy##{color_name}"
                    if PyImGui.button(btn_label):
                        PyImGui.set_clipboard_text(color_name)
                    
                    PyImGui.pop_style_color(4)
                    
                    if PyImGui.is_item_hovered():
                        PyImGui.set_tooltip(f"{color_name}")

                    # ---- Copy button ----
                    PyImGui.table_set_column_index(base_col + 2)
                    btn_label = f"Dict Get##{color_name}"
                    if PyImGui.button(btn_label):
                        PyImGui.set_clipboard_text(f'ColorPalette.GetColor("{color_name}")')
                    if PyImGui.is_item_hovered():
                        PyImGui.set_tooltip(f'ColorPalette.GetColor("{color_name}")')

                    PyImGui.pop_style_color(4)

                i += 3  # next group of 3 colors

            PyImGui.end_table()

    PyImGui.end()



if __name__ == "__main__":
    main()

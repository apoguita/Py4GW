from Py4GWCoreLib import *

MODULE_NAME = "Icon Explorer"

all_names = list(dir(IconsFontAwesome5))
filter_text = ""

def DrawWindow(title: str = "FontAwesome Icon Names"):
    """Draw a grid showing only the names of the FontAwesome icons."""
    global filter_text
    try:
        flags = PyImGui.WindowFlags.AlwaysAutoResize
        table_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable

        headers = ["Icon 1", "Icon 2", "Icon 3", "Icon 4"]
        num_columns = len(headers)

        PyImGui.set_next_window_size(1200, 800)
        
        if PyImGui.begin(title):
            PyImGui.text("Filter Icons:")
            PyImGui.same_line(0,-1)
            filter_text = PyImGui.input_text("##IconFilter", filter_text)

            if PyImGui.begin_table("IconTable", 4, PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV):
                for header in headers:
                    PyImGui.table_setup_column(header)
                PyImGui.table_headers_row()

                row = []
                for name in all_names:
                    if filter_text.lower() in name.lower():
                        value = getattr(IconsFontAwesome5, name)
                        if isinstance(value, str):
                            row.append(value + f" name: {name}")
                            if len(row) == 4:
                                PyImGui.table_next_row(0, 32)
                                for i, cell in enumerate(row):
                                    PyImGui.table_set_column_index(i)
                                    PyImGui.text(cell)
                                row = []

                if row:
                    PyImGui.table_next_row()
                    for i, cell in enumerate(row):
                        PyImGui.table_set_column_index(i)
                        PyImGui.text(cell)

                PyImGui.end_table()
            PyImGui.end()



    except Exception as e:
        Py4GW.Console.Log("ICON_GRID", f"Error: {str(e)}", Py4GW.Console.MessageType.Error)




def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Icon Explorer", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A specialized utility for browsing and searching the integrated")
    PyImGui.text("FontAwesome 5 icon library. This tool allows developers to")
    PyImGui.text("quickly find icon names and visual representations for UI design.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Icon Grid: Displays a 4-column visual gallery of all available icons")
    PyImGui.bullet_text("Live Filtering: Search for specific icons by name in real-time")
    PyImGui.bullet_text("Direct Referencing: Shows the exact constant name used in code")
    PyImGui.bullet_text("Comprehensive Library: Lists all members of the IconsFontAwesome5 class")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()

def main():
    """Runs every frame."""
    DrawWindow()

if __name__ == "__main__":
    main()

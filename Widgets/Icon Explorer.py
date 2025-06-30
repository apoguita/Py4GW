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




def configure():
    pass

def main():
    """Runs every frame."""
    DrawWindow()

if __name__ == "__main__":
    main()

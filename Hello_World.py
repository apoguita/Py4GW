from Py4GWCoreLib import *
import re
import sys

MODULE_NAME = "tester for everything"


message = ""
selected_channel = 0
def DrawWindow():
    global message,selected_channel
    try:
        flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("Py4GW", flags):
            if PyImGui.begin_table("TableRow1", 2, PyImGui.TableFlags.SizingFixedFit):  # Ensures columns fit their content
                PyImGui.table_setup_column("InputColumn")  # Use available function
                PyImGui.table_setup_column("ButtonColumn")  # Use available function

                PyImGui.table_next_row()

                # First Column: Input Field (Auto-sized)
                PyImGui.table_next_column()
                PyImGui.set_next_item_width(70)  # Explicitly set InputText width
                message = PyImGui.input_text("##text_id", message)

                # Second Column: Button
                PyImGui.table_next_column()
                if PyImGui.button(IconsFontAwesome5.ICON_FOLDER_OPEN + "##ICON_FOLDER_OPEN",30,30):
                    Py4GW.Console.Log("tester", message, Py4GW.Console.MessageType.Info)

                PyImGui.end_table()

            if PyImGui.begin_table("ButtonTable", 3):
                
                # Row 2: (Pause, Stop, Maximize)
                PyImGui.table_next_column()
                if PyImGui.button(IconsFontAwesome5.ICON_PAUSE + "##ICON_PAUSE",30,30):
                    Py4GW.Console.Log("tester", message, Py4GW.Console.MessageType.Info)

                PyImGui.table_next_column()
                if PyImGui.button(IconsFontAwesome5.ICON_STOP + "##ICON_STOP",30,30):
                    Py4GW.Console.Log("tester", message, Py4GW.Console.MessageType.Info)

                PyImGui.table_next_column()
                if PyImGui.button(IconsFontAwesome5.ICON_WINDOW_MAXIMIZE + "##ICON_WINDOW_MAXIMIZE",30,30):
                    Py4GW.Console.Log("tester", message, Py4GW.Console.MessageType.Info)

                # Row 3: (Sticky Note, Save, Copy)
                PyImGui.table_next_column()
                if PyImGui.button(IconsFontAwesome5.ICON_STICKY_NOTE + "##ICON_STICKY_NOTE",30,30):
                    Py4GW.Console.Log("tester", message, Py4GW.Console.MessageType.Info)

                PyImGui.table_next_column()
                if PyImGui.button(IconsFontAwesome5.ICON_SAVE + "##ICON_SAVE",30,30):
                    Py4GW.Console.Log("tester", message, Py4GW.Console.MessageType.Info)

                PyImGui.table_next_column()
                if PyImGui.button(IconsFontAwesome5.ICON_COPY + "##ICON_COPY",30,30):
                    Py4GW.Console.Log("tester", message, Py4GW.Console.MessageType.Info)

                PyImGui.end_table()
                PyImGui.separator()
                PyImGui.text_colored("Stopped",(1,0,0,1))
            

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)






def main():
    DrawWindow()


if __name__ == "__main__":
    main()

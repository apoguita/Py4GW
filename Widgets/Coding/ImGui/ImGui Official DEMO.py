from Py4GWCoreLib import *

MODULE_NAME = "ImGui DEMO"
MODULE_ICON = "Textures/Module_Icons/ImGui.png"

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("ImGui Official Demo", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("This widget launches the official Dear ImGui demonstration window.")
    PyImGui.text("It serves as the primary visual documentation for all UI widgets,")
    PyImGui.text("layouts, and styling options available in the library.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Widget Gallery: Buttons, sliders, inputs, and selectors")
    PyImGui.bullet_text("Layout Examples: Tables, columns, and child windows")
    PyImGui.bullet_text("Advanced Tools: Color pickers, graphs, and tree nodes")
    PyImGui.bullet_text("Style Editor: Real-time manipulation of UI colors and spacing")
    PyImGui.bullet_text("Metric Viewer: Debugging tool for draw calls and vertex counts")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Integrated by Apo")
    PyImGui.bullet_text("Original Library: ocornut/imgui")

    PyImGui.end_tooltip()

def main():
    PyImGui.show_demo_window()        

    
if __name__ == "__main__":
    main()

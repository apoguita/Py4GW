from Py4GWCoreLib import *
import PyMap, PyImGui

MODULE_NAME = "Style tester"

ImGuiCol_ = PyImGui.ImGuiCol

style = PyImGui.StyleConfig()
button_color:Tuple[float, float, float, float] = style.get_color(ImGuiCol_.Button)  # RGBA format
button_hover_color:Tuple[float, float, float, float] = style.get_color(ImGuiCol_.ButtonHovered)
button_active_color:Tuple[float, float, float, float] = style.get_color(ImGuiCol_.ButtonActive)

def main():
    global style, button_color, button_hover_color, button_active_color

    if PyImGui.begin("Style Tester", PyImGui.WindowFlags.AlwaysAutoResize):
        button_color = PyImGui.color_edit4("Button Color", button_color)
        button_hover_color = PyImGui.color_edit4("Button Hover Color", button_hover_color)
        button_active_color = PyImGui.color_edit4("Button Active Color", button_active_color)

        style.set_color(ImGuiCol_.Button, button_color[0], button_color[1], button_color[2], button_color[3])
        style.set_color(ImGuiCol_.ButtonHovered, button_hover_color[0], button_hover_color[1], button_hover_color[2], button_hover_color[3])
        style.set_color(ImGuiCol_.ButtonActive, button_active_color[0], button_active_color[1], button_active_color[2], button_active_color[3])

        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, button_color)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, button_hover_color)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, button_active_color)
        if PyImGui.button("Example Button"):
            print("clicked!")

        PyImGui.pop_style_color(3)
        
        if PyImGui.button("Reset to Default"):
            style.Reset()

        if PyImGui.button("reset to current Style"):
            style.Pull()

        if PyImGui.button("Apply Style Globally"):
            style.Push()

    PyImGui.end()


if __name__ == "__main__":
    main()

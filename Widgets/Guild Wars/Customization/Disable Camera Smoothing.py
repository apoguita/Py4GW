from Py4GWCoreLib import *

MODULE_NAME = "Disable Camera Smoothing"

def main():
    pos = Camera.GetCameraPositionToGo()
    Camera.SetCameraPosition(pos[0], pos[1], pos[2])

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Disable Camera Smoothing", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    #ellaborate a better description 
    PyImGui.text("This widget disables camera smoothing in Guild Wars by setting the camera position directly each frame.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Disables camera smoothing for a more responsive camera experience.")
    PyImGui.bullet_text("Updates camera position every frame to eliminate lag.")
    PyImGui.bullet_text("Simple and lightweight implementation.")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by fruitchewy")

    PyImGui.end_tooltip()

if __name__ == "__main__":
    main()

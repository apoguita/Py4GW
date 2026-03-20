import PyImGui
from Py4GWCoreLib import *



font_size = 30
font_size2 = 30
def main():
    global font_size
    global font_size2

    if PyImGui.begin ("Immediate Window Reference"):
        font_size = PyImGui.slider_int("Font Size", font_size, 1, 100)
        ImGui.push_font("Regular", font_size)
        if PyImGui.button("O"):
            pass
        ImGui.pop_font()
        font_size2 = PyImGui.slider_int("Font Size 2", font_size2, 1, 100)
        ImGui.push_font("Regular", font_size2)
        
        if PyImGui.button("+"):
            pass
        ImGui.pop_font()
    PyImGui.end()


if __name__ == "__main__":
    main()

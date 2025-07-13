import Py4GW
from Py4GWCoreLib import *
import webbrowser

MODULE_NAME = "tester for fonts"

class ImGuiMouseCursor(IntEnum):
    _None = -1
    Arrow = 0
    TextInput = 1
    ResizeAll = 2 #(Unused by Dear ImGui functions)
    ResizeNS=3 # When hovering over a horizontal border
    ResizeEW =4 # When hovering over a vertical border or a column
    ResizeNESW =5 # When hovering over the bottom-left corner of a window
    ResizeNWSE =6 # When hovering over the bottom-right corner of a window
    Hand = 7 # (Unused by Dear ImGui functions. Use for e.g. hyperlinks)
    NotAllowed = 8 # When hovering something with disallowed interaction. Usually a crossed circle.


    

selected_skill = 0
def main():
    global selected_skill
    try:
        window_flags=PyImGui.WindowFlags.AlwaysAutoResize #| PyImGui.WindowFlags.MenuBar
        if PyImGui.begin("move", window_flags):
            hovered_skill = GLOBAL_CACHE.SkillBar.GetHoveredSkillID()
            PyImGui.text(f"Hovered Skill ID: {hovered_skill}")
            if hovered_skill != 0:
                selected_skill = hovered_skill
                
            selected_skill = PyImGui.input_int("Selected Skill ID", selected_skill)
            
            if selected_skill != 0:
                PyImGui.text(f"Selected Skill: {GLOBAL_CACHE.Skill.GetNameFromWiki(selected_skill)}")
                # Display URL as clickable
                url = GLOBAL_CACHE.Skill.GetURL(selected_skill)
                #PyImGui.text_colored(f"URL: {url}", (0.26, 0.59, 0.98, 1.0))  # light blue
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))  # Transparent background
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.2, 0.4, 0.9, 0.3))  # Hover background
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.26, 0.59, 0.98, 1.0))  # Link color

                if PyImGui.button(f"URL: {url}"):
                    webbrowser.open(url)

                PyImGui.pop_style_color(3)

                PyImGui.text(f"Description: {GLOBAL_CACHE.Skill.GetDescription(selected_skill)}")
                PyImGui.text(f"Concise Description: {GLOBAL_CACHE.Skill.GetConciseDescription(selected_skill)}")
                ImGui.DrawTexture(GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(selected_skill), 64, 64)
            
            
        PyImGui.end()
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()

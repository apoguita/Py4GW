from Py4GWCoreLib import *

MODULE_NAME = "Color Picker"

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Color Picker & Stylist", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A specialized design utility for testing and generating UI color")
    PyImGui.text("schemes. This tool allows for real-time manipulation of button")
    PyImGui.text("states and provides code-ready snippets for script development.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("State Management: Configure separate colors for Normal, Hovered, and Active states")
    PyImGui.bullet_text("Precise Selection: Integrated RGBA color editors with normalized float support")
    PyImGui.bullet_text("Clipboard Integration: Copy individual colors or complete style blocks instantly")
    PyImGui.bullet_text("Live Preview: Interactive button that reflects your current color configuration")
    PyImGui.bullet_text("Format Conversion: Automatically converts normalized UI values back to standard Color tuples")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()

button_color:Tuple[float, float, float, float] = Color(90,0,10,255).to_tuple_normalized()  # RGBA format
hovered_color:Tuple[float, float, float, float] = Color(160,0,15,255).to_tuple_normalized()  # RGBA format
active_color:Tuple[float, float, float, float] = Color(210,0,20,255).to_tuple_normalized()  # RGBA format
def main():
    global button_color, hovered_color, active_color
    
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text("Button Color:")
        PyImGui.same_line(0,-1)
        button_color = PyImGui.color_edit4("Flag Color", button_color)
        rgb_button_color:Color = Utils.NormalToColor(button_color)
        PyImGui.same_line(0,-1)
        if PyImGui.button("Copy To Clipboard##buttoncolor"):
            PyImGui.set_clipboard_text(f"Color{rgb_button_color.to_tuple()}")
            print("Copied to clipboard!")
       
        PyImGui.text("Hovered Color:")   
        PyImGui.same_line(0,-1)
        hovered_color = PyImGui.color_edit4("Flag Hovered Color", hovered_color)
        rgb_hovered_color:Color = Utils.NormalToColor(hovered_color)
        PyImGui.same_line(0,-1)
        if PyImGui.button("Copy To Clipboard##hoveredcolor"):
            PyImGui.set_clipboard_text(f"Color{rgb_hovered_color.to_tuple()}")
            print("Copied to clipboard!")
        PyImGui.text("Active Color:")
        PyImGui.same_line(0,-1)
        active_color = PyImGui.color_edit4("Flag Active Color", active_color)
        rgb_active_color:Color = Utils.NormalToColor(active_color)
        PyImGui.same_line(0,-1)
        if PyImGui.button("Copy To Clipboard##activecolor"):
            PyImGui.set_clipboard_text(f"Color{rgb_active_color.to_tuple()}")
            print("Copied to clipboard!")  
            
            
        PyImGui.text_colored("Button Color:", button_color)
        PyImGui.text_colored("Hovered Color:", hovered_color)
        PyImGui.text_colored("Active Color:", active_color)
        
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, button_color)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hovered_color)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active_color)
        if PyImGui.button("Copy To Clipboard##allcolors"):
            PyImGui.set_clipboard_text(
                f"button_color = Color{rgb_button_color.to_tuple()}\n"
                f"hovered_color = Color{rgb_hovered_color.to_tuple()}\n"
                f"active_color = Color{rgb_active_color.to_tuple()}"
            )
            print("Colors copied to clipboard!")

        PyImGui.pop_style_color(3)
            
    PyImGui.end()
    
if __name__ == "__main__":
    main()

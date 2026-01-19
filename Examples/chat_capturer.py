import Py4GW
from Py4GWCoreLib import *

MODULE_NAME = "tester for fonts"

chat_text_frame_hash = 4223760173
text_input = ""

focus_set = False
def floating_input_text(label, value, x, y, width=120, height=24, color: Color = Color(255, 255, 255, 255)):
    global focus_set
    # Set the position and size of the floating input
    PyImGui.set_next_window_pos(x, y)
    PyImGui.set_next_window_size(width, height)

    flags = (
        PyImGui.WindowFlags.NoCollapse |
        PyImGui.WindowFlags.NoTitleBar |
        PyImGui.WindowFlags.NoScrollbar |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.AlwaysAutoResize
    )

    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0.0, 0.0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 3, 5)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, color.to_tuple_normalized())

    new_value = value
    if PyImGui.begin(f"##invisible_window_input_{label}", flags):
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0.2, 0.3, 0.4, 0.1))
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0.3, 0.4, 0.5, 0.1))
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0.4, 0.5, 0.6, 0.1))
        if not focus_set:
            PyImGui.set_keyboard_focus_here(0)
            focus_set = True
        new_value = PyImGui.input_text(f"##floating_input_text_{label}", value)

        PyImGui.pop_style_color(3)
    PyImGui.end()

    PyImGui.pop_style_var(3)
    PyImGui.pop_style_color(1)
    return new_value


def main():
    global text_input, chat_text_frame_hash, focus_set
    try:
        chat_text_frame_id = UIManager.GetFrameIDByHash(chat_text_frame_hash)
        if UIManager.FrameExists(chat_text_frame_id) and Player.IsTyping():
            #UIManager().DrawFrame(chat_text_frame_id, ColorPalette.GetColor("GW_White").to_color())
            left,top, right, bottom = UIManager.GetFrameCoords(chat_text_frame_id)
            width = right - left
            height = bottom - top
            
            text_input = floating_input_text("TextOverride", text_input,x = left, y = top, width=width, height=height, color=Color(255, 255, 0, 255))
        else:
            focus_set = False

        window_flags=PyImGui.WindowFlags.AlwaysAutoResize #| PyImGui.WindowFlags.MenuBar
        if PyImGui.begin("chat status", window_flags):
            PyImGui.text(Player.IsTyping() and "Player is typing..." or "Player is not typing")
        PyImGui.end()
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()

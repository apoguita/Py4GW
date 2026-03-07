import PyKeystroke
import PyImGui
import Py4GW
from Py4GWCoreLib import *

salvage_materials_frame = 0
window_id = 0
def draw_window():
    global salvage_materials_frame, window_id
    
    
    if PyImGui.begin("dialog tester"):
        salvage_materials_frame = UIManager.GetChildFrameID(140452905, [6, 109, 6])
        PyImGui.text(f"Frame exists: {UIManager.FrameExists(salvage_materials_frame)}")
        
        window_id = PyImGui.input_int("Window ID", window_id)
        inv_open = UIManager.IsWindowVisible(window_id)
        
        for _wid in range(0x0, 0x90):
            is_open = UIManager.IsWindowVisible(_wid)
            PyImGui.text_colored(f"Window ID {_wid} open: {is_open} HEX: {hex(_wid)}", (0.0, 1.0, 0.0, 1.0) if is_open else (1.0, 0.0, 0.0, 1.0))

        
    PyImGui.end()

def main():
    draw_window()


if __name__ == "__main__":
    main()

import Py4GW
from Py4GWCoreLib import *

MODULE_NAME = "tester for fonts"
       
        
_from = 0
_to = 20

def main():
    global _from, _to
    try:
        window_flags=PyImGui.WindowFlags.AlwaysAutoResize #| PyImGui.WindowFlags.MenuBar
        if PyImGui.begin("Font Preview", window_flags):
            _from = PyImGui.input_int("From", _from, 1, 10, 0)
            _to = PyImGui.input_int("To", _to, 1, 10, 0)
            if _from < 1:
                _from = 1
                
            if _to < 1:
                _to = 1
                
            if _to < _from:
                _to = _from
                
            for font_size in range(_from, _to + 1):
                families = ["Regular", "Bold", "Italic", "BoldItalic"]
                for i, font_family in enumerate(families):
                    try:
                        ImGui.push_font(font_family, font_size)
                        PyImGui.text(f"{font_family} {font_size}px")
                    except ValueError as e:
                        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
                    finally:
                        ImGui.pop_font()
                    
                    # Only add same_line if not the last font family
                    if i != len(families) - 1:
                        PyImGui.same_line(0, -1)

                
        PyImGui.end()
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()

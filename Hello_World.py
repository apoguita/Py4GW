from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

capture_mouse = False
mouse_x, mouse_y, pos_z = 0.0, 0.0, 0.0
def main():
    global capture_mouse, mouse_x, mouse_y, pos_z
    
    if PyImGui.begin("timer test"):
        if PyImGui.button("right"):
            Keystroke.Press(Key.RightArrow.value)
            
        if PyImGui.button("release right"):
            Keystroke.Release(Key.RightArrow.value)
            
        if PyImGui.button("A"):
            Keystroke.Press(Key.A.value)
        if PyImGui.button("Release A"):
            Keystroke.Release(Key.A.value)
            
        
    PyImGui.end()
    
if __name__ == "__main__":
    main()

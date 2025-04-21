from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

capture_mouse = False
mouse_x, mouse_y, pos_z = 0.0, 0.0, 0.0
def main():
    global capture_mouse, mouse_x, mouse_y, pos_z
    
    if PyImGui.begin("timer test"):
        if PyImGui.button("use Item"):
            capture_mouse = not capture_mouse
            
        if capture_mouse:
            mouse_x,mouse_y,_ = Overlay().GetMouseWorldPos()
            pos_z = Overlay().FindZ(mouse_x, mouse_y)
            
        PyImGui.text(f"Mouse X: {mouse_x}")
        PyImGui.text(f"Mouse Y: {mouse_y}")
        PyImGui.text(f"Mouse Z: {pos_z}")

            
        
    PyImGui.end()
    
if __name__ == "__main__":
    main()

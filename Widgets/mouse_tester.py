from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

mouse_handler = PyMouse.PyMouse()
mouse_button = MouseButton.Left.value
x,y = 0,0
mouse_x, mouse_y = 0,0
def main():
    global x,y, mouse_button, mouse_x, mouse_y, mouse_handler
    if PyImGui.begin("mouse test"):
        mouse_x, mouse_y = Mouse.GetPosition()        
        PyImGui.text(f"Mouse coords: {mouse_x}, {mouse_y}")
        
        button_names = [button.name for button in MouseButton]
        mouse_button = PyImGui.combo("Mouse Button", mouse_button, button_names)
  
        x = PyImGui.input_int("x", x)
        y = PyImGui.input_int("y", y)
        if PyImGui.button("move mouse"):
            mouse_handler.MoveMouse(x, y)
        if PyImGui.button("click"):
            mouse_handler.Click(mouse_button,x, y)
        if PyImGui.button("double click"):
            mouse_handler.DoubleClick(mouse_button,x, y)
        if PyImGui.button("scroll"):
            mouse_handler.Scroll(mouse_button, x, y)
  
        
    PyImGui.end()
    
if __name__ == "__main__":
    main()

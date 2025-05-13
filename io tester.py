from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

width, height = 0,0
def main():
    global width, height
    
    if PyImGui.begin("timer test"):
        if PyImGui.button("get Client Size"):
            io = PyImGui.get_io()
            print(f"Client Size: {io.display_size_x}, {io.display_size_y}")   
    PyImGui.end()
    
if __name__ == "__main__":
    main()

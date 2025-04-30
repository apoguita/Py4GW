from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

this_is_a_global_variable = False


def main():
    global this_is_a_global_variable
    this_is_not_a_global_variable = False
    
    if PyImGui.begin("timer test"):
        this_is_a_global_variable = PyImGui.checkbox("this is a global variable", this_is_a_global_variable)
        this_is_not_a_global_variable = PyImGui.checkbox("this is not a global variable", this_is_not_a_global_variable)    
    PyImGui.end()
    
if __name__ == "__main__":
    main()

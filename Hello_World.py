from Py4GWCoreLib import *


def DrawWindow():

    try:
        if PyImGui.begin("Tester"):
            PyImGui.text("Hello World")
            if PyImGui.button("create bag"):
                bag_instance = PyInventory.Bag(1,"bag1")
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error{str(e)}", Py4GW.Console.MessageType.Error)



def main():
    DrawWindow()

if __name__ == "__main__":
    main()
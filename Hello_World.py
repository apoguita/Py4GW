from Py4GWCoreLib import *

counter = 0

def update():
    global counter
    counter += 1


def draw():
    global counter
    if PyImGui.begin("hello world"):
        PyImGui.text("Hello World from Python!")
        PyImGui.text(f"Counter: {counter}")
    PyImGui.end()

if __name__ == "__main__":
    update()
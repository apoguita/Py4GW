from typing import Generator, Any

from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

@staticmethod
def wait_for(milliseconds) -> Generator[Any, Any, Any]:
    start_time = time.time()
    print(f"wait_for__{milliseconds}ms")

    while (time.time() - start_time) < milliseconds / 1000:
        yield 'wait'  # Pause and allow resumption while waiting
    return

def main_generator():
    while True:
        print(f"step1")
        yield from wait_for(1000) # that stuff is not blocking
        print(f"step2")

width, height = 0,0
gen = main_generator()

def main():
    global width, height
    
    if PyImGui.begin("timer test"):
        if PyImGui.button("get Client Size"):
            io = PyImGui.get_io()
            print(f"Client Size: {io.display_size_x}, {io.display_size_y}")   
    PyImGui.end()

    try:
        next(gen)
    except StopIteration:
        print(f"StopIteration.")
    except Exception as e:
        print(f"is not expected to exit : {e}")


if __name__ == "__main__":
    main()

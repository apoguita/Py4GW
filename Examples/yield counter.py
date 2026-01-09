from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

counter = 0

def _add_1():
    global counter
    counter += 1
    yield
    
def _count():
    global counter
    while True:
        yield from _add_1()
        yield from Routines.Yield.wait(1000)  # Wait for 1 second


def main():
        try:
            if PyImGui.begin("counter"):
                PyImGui.text(f"this will count each second")
                PyImGui.text(f"Counter: {counter}")
                if PyImGui.button("Start Counting"):
                    GLOBAL_CACHE.Coroutines.append(_count())
                if PyImGui.button("Stop Counting"):
                    GLOBAL_CACHE.Coroutines.clear()
            PyImGui.end()
            


        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
            raise


    
if __name__ == "__main__":
    main()

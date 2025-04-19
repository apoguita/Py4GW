from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"
timer = Timer()
timer.Start()

def main():
    global timer
    if PyImGui.begin("timer test"):
        PyImGui.text(f"Time Passed: {timer.GetElapsedTime()} milliseconds")
        PyImGui.text(f"Ahs 5000 ms passed? {timer.HasElapsed(5000)}")
    PyImGui.end()
    
if __name__ == "__main__":
    main()

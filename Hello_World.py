from Py4GWCoreLib import *
import sys
import os
import site
import sysconfig

site_packages_path = r"C:\Users\Apo\AppData\Local\Programs\Python\Python313-32\Lib\site-packages"

if site_packages_path not in sys.path:
    sys.path.append(site_packages_path)



def get_base_timestamp():
    # Use midnight today as the reference point
    #return int((time.perf_counter() - START_TIME) * 1000)  # Convert seconds to milliseconds
    return int( time.time()*1000)
    now = time.time()
    last_hour = int(now // 3600 * 3600) 
    return int((now - last_hour) * 1000)

def enter_challenge():
    """Function that Lua will call to execute Map.EnterChallenge()"""
    Py4GW.Console.Log("tester", "Lua called Map.EnterChallenge()", Py4GW.Console.MessageType.Info)
    Map.EnterChallenge()

def DrawWindow():
    global fetch_time
    global lua, lua_code
    try:
        if PyImGui.begin("Hello, world!"):
            PyImGui.text(f"base time {get_base_timestamp()}")
            PyImGui.text(f"timestamp {int( time.time())}")
            PyImGui.text(f"timestamp {int( time.time()*1000)}")

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)


def main():
    DrawWindow()

if __name__ == "__main__":
    main()

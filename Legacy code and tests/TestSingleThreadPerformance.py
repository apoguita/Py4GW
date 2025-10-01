import time
import threading
from Py4GWCoreLib import *

is_script_running = False

def RunBotSequentialLogic():
    global is_script_running
    total = 0
    start_time = time.time()
    for i in range(1, 100000000):
        total += i
    print(f"Found {total} after {time.time()-start_time} seconds")
    is_script_running = False


def main():
    global is_script_running

    if not is_script_running:
        t = threading.Thread(target=RunBotSequentialLogic)
        is_script_running = True
        t.start()


if __name__ == "__main__":
    main()

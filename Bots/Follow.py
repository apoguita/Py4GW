from Py4GWCoreLib import *
import time
last_follow = {'ts': 0}

def main():
    now = int(time.time() * 1000)
    last_follow_time = now - last_follow['ts']
    if last_follow_time > 5000:
        last_follow['ts'] = now
        Keystroke.PressAndRelease(Key.Space.value)
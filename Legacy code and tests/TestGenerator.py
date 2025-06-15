import time
from enum import Enum
from typing import Any, Generator

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

# Consume the main generator
gen = main_generator()

while True: # the main function, that loop very fast.
    try:
        next(gen)
    except StopIteration:
        print(f"CustomCombatBehaviorBase.act is not expected to StopIteration.")
        break
    except Exception as e:
        print(f"CustomCombatBehaviorBase.act is not expected to exit : {e}")




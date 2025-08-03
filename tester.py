from Py4GWCoreLib import *
from OutpostRunnerDA import OutpostRunnerDA

MODULE_NAME = "Outpost Runner Tester"

# Create runner instance
runner_build = OutpostRunnerDA()

# Track coroutine & state
runner_coroutine = None
runner_running = False


def main():
    global runner_running, runner_coroutine

    try:
        if PyImGui.begin("Outpost Runner Tester", PyImGui.WindowFlags.AlwaysAutoResize):

            # START button
            if not runner_running:
                if PyImGui.button("Start Runner"):
                    # Create coroutine ONCE
                    runner_coroutine = runner_build.ProcessSkillCasting()

                    # Register it so the engine advances it automatically
                    GLOBAL_CACHE.Coroutines.append(runner_coroutine)

                    runner_running = True
                    ConsoleLog(MODULE_NAME, "Runner started.")

            # STOP button
            else:
                if PyImGui.button("Stop Runner"):
                    # Remove coroutine cleanly
                    if runner_coroutine in GLOBAL_CACHE.Coroutines:
                        GLOBAL_CACHE.Coroutines.remove(runner_coroutine)

                    runner_running = False
                    ConsoleLog(MODULE_NAME, "Runner stopped.")

        PyImGui.end()

    except Exception as e:
        ConsoleLog(MODULE_NAME, f"Error: {str(e)}", Console.MessageType.Error)
        raise


if __name__ == "__main__":
    main()

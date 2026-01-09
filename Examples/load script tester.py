from __future__ import annotations
from typing import Optional
import os

import PyImGui
from Py4GWCoreLib import Py4GW


def get_script_path_for_model(model: int) -> Optional[str]:
    """
    Resolve the script filename for a given model ID.
    Returns the full path if found, otherwise None.
    """
    base_path = Py4GW.Console.get_projects_path()
    bots_path = os.path.join(base_path, "Bots", "Nicholas the Traveler")

    try:
        for file in os.listdir(bots_path):
            if file.startswith(f"{model}-") and file.endswith(".py"):
                return os.path.join(bots_path, file)
    except Exception as e:
        Py4GW.Console.Log(
            "script loader",
            f"Error scanning for model {model}: {str(e)}",
            Py4GW.Console.MessageType.Error,
        )

    return None


def main():
    try:
        model = 807
        if PyImGui.begin("script loader"):
            PyImGui.text("Click the button below to load the farming script.")

            if PyImGui.button("load model script"):
                script_path = get_script_path_for_model(model)
                if script_path:
                    Py4GW.Console.Log(
                        "script loader",
                        f"Loading script from {script_path}",
                        Py4GW.Console.MessageType.Info,
                    )
                    Py4GW.Console.defer_stop_load_and_run(script_path)
                else:
                    Py4GW.Console.Log(
                        "script loader",
                        f"No script found for model {model}",
                        Py4GW.Console.MessageType.Error,
                    )

    except Exception as e:
        Py4GW.Console.Log("script loader", f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


if __name__ == "__main__":
    main()

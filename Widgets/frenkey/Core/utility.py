import os

##TODO: Make this more robust to handle different parent folder names
def GetPy4GWPath() -> str:
        file_path = os.path.abspath(__file__)
        marker = os.sep + "Py4GW" + os.sep
        base_path = file_path.partition(marker)[0] + marker if marker in file_path else file_path

        return base_path
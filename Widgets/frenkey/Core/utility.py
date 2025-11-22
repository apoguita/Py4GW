import difflib
import os
from pathlib import Path
import re

from Py4GW import Console
from urllib import parse

##TODO: Make this more robust to handle different parent folder names
def GetPy4GWPath() -> str:
        file_path = os.path.abspath(__file__)
        marker = os.sep + "Py4GW" + os.sep
        base_path = file_path.partition(marker)[0] + marker if marker in file_path else file_path

        return base_path

@staticmethod
def string_similarity(a: str, b: str) -> float:
    """
    Returns similarity ratio between two strings (0.0 to 1.0).
    """
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

@staticmethod            
def get_image_name(url: str) -> str:
    # Extract the last part of the URL (the filename)
    last_part = url.rsplit('/', 1)[-1]

    # Remove "File:" prefix if present
    last_part = last_part.replace("File:", "")

    # Remove px size prefix like "134px-"
    last_part = re.sub(r'^\d+px-', '', last_part)
    last_part = last_part.replace("%22", "")  # Remove URL-encoded quotes

    # Decode URL-encoded characters
    decoded = parse.unquote(last_part)

    decoded = decoded.replace("_", " ")  # Replace spaces with underscores

    # Allow characters valid on most filesystems: keep letters, numbers, spaces, underscores,
    # dashes, apostrophes, parentheses, and periods
    # Replace only truly invalid characters with underscore
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', decoded)

    # Replace multiple underscores with one (optional cleanup)
    sanitized = re.sub(r'_+', '_', sanitized)

    # Strip leading/trailing spaces/underscores
    return sanitized.strip(" _")
    
class ImGuiIniReader:
    class ImGuiWindowConfig:
        def __init__(self, pos=(0.0, 0.0), size=(0.0, 0.0), collapsed=False):
            self.pos = pos              # tuple[float, float]
            self.size = size            # tuple[float, float]
            self.collapsed = collapsed  # bool

        def __repr__(self):
            return f"ImGuiWindowConfig(pos={self.pos}, size={self.size}, collapsed={self.collapsed})"
        
    def __init__(self):
        self.path = Path(Console.get_projects_path(), "imgui.ini")
        self.windows: dict[str, "ImGuiIniReader.ImGuiWindowConfig"] = {}
        self._parse()

    def _parse(self):
        current_window = None
        current_data = {}

        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";"):
                    continue

                # section header: [Window][WindowName]
                if line.startswith("[Window]"):
                    # save last window before starting new
                    if current_window and current_data:
                        self._store_window(current_window, current_data)
                        current_data = {}

                    start = line.find("][") + 2
                    end = line.rfind("]")
                    current_window = line[start:end]

                elif "=" in line and current_window:
                    key, value = line.split("=", 1)
                    current_data[key.strip()] = value.strip()

            # save last one
            if current_window and current_data:
                self._store_window(current_window, current_data)

    def _store_window(self, name: str, data: dict[str, str]):
        pos = tuple(map(float, data.get("Pos", "0,0").split(",")))
        size = tuple(map(float, data.get("Size", "0,0").split(",")))
        collapsed = data.get("Collapsed", "0") == "1"

        self.windows[name] = ImGuiIniReader.ImGuiWindowConfig(pos, size, collapsed)

    def get(self, window: str) -> "ImGuiIniReader.ImGuiWindowConfig | None":
        return self.windows.get(window)
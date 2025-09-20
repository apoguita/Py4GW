from pathlib import Path


class ImGuiIniReader:
    class ImGuiWindowConfig:
        def __init__(self, pos=(0.0, 0.0), size=(0.0, 0.0), collapsed=False):
            self.pos = pos              # tuple[float, float]
            self.size = size            # tuple[float, float]
            self.collapsed = collapsed  # bool

        def __repr__(self):
            return f"ImGuiWindowConfig(pos={self.pos}, size={self.size}, collapsed={self.collapsed})"
        
    def __init__(self):
        self.path = Path("imgui.ini")
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
from enum import IntEnum
from Py4GWCoreLib import Color
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import PyImGui
from datetime import datetime
from typing import Optional


#region Logconsole  
class LogConsole:
    class LogSeverity(IntEnum):
        INFO = 0
        WARNING = 1
        ERROR = 2
        CRITICAL = 3
        SUCCESS = 4

        def __str__(self):
            return self.name.capitalize()

        def to_color(self) -> 'Color':
            if self == self.INFO:
                return Color(255, 255, 255, 255)  # White
            elif self == self.WARNING:
                return Color(255, 255, 0, 255)    # Yellow
            elif self == self.ERROR:
                return Color(255, 0, 0, 255)      # Red
            elif self == self.CRITICAL:
                return Color(128, 0, 128, 255)    # Purple
            elif self == self.SUCCESS:
                return Color(0, 255, 0, 255)      # Green
            return Color(255, 255, 255, 255)      # Default

    class LogEntry:
        def __init__(self, message: str, extra_info: Optional[str],severity: Optional['LogConsole.LogSeverity'] = None):
            if severity is None:
                severity = LogConsole.LogSeverity.INFO
            self.message: str = message
            self.extra_info: str = extra_info if extra_info is not None else ""
            self.severity: LogConsole.LogSeverity = severity
            self.color: Color = severity.to_color()
            self.timestamp = datetime.now()

        def __str__(self):
            return f"[{self.severity}] {self.message}"

    def __init__(self,module_name="LogConsole", window_pos= (100, 100), window_size= (400, 300), is_snapped= True,  log_to_file: bool = False):
        self.messages: list[LogConsole.LogEntry] = []
        self.log_to_file: bool = log_to_file
        self.window_flags = PyImGui.WindowFlags(
            PyImGui.WindowFlags.AlwaysAutoResize
        )
        self.main_window_pos = (100, 100)  # fallback default
        self.main_window_size = (400, 300)
        
        self.window_pos = window_pos
        self.window_size = window_size
        self.is_snapped = is_snapped
        self.window_snapped_border = "Right"
        self.window_module_initialized = False
        self.window_module = ImGui.WindowModule(
            module_name=module_name,
            window_name=module_name,
            window_pos=self.window_pos,
            window_size=self.window_size,
            window_flags=self.window_flags,
            
        )
        
    def SetLogToFile(self, log_to_file: bool):
        """Set whether to log messages to a file."""
        self.log_to_file = log_to_file     
    
    def SetSnapped(self, is_snapped: bool, snapped_border: str = "Right"):
        """Set whether the console window is snapped to the main window."""
        self.is_snapped = is_snapped
        self.window_snapped_border = snapped_border
        
    def SetWindowPosition(self, pos: tuple[int, int]):
        """Set the position of the log console window."""
        self.window_pos = pos
            
    def SetWindowSize(self, size: tuple[int, int]):
        """Set the size of the log console window."""
        self.window_size = size
        
    def SetMainWindowPosition(self, pos):
        """Set the position of the main window."""
        self.main_window_pos = pos
        
    def SetMainWindowSize(self, size):
        """Set the size of the main window."""
        self.main_window_size = size

    def LogMessage(self, message: str, extra_info: Optional[str], severity: Optional['LogConsole.LogSeverity'] = None):
        """Add a new log entry to the console."""
        entry = LogConsole.LogEntry(message, extra_info, severity)
        self.messages.append(entry)

    def DrawConsole(self):
        """Draw the log console window."""
        self.window_module.initialize()
        border = self.window_snapped_border.lower()
        if border == "right":
            snapped_x = self.main_window_pos[0] + self.main_window_size[0] + 1
            snapped_y = self.main_window_pos[1]
        elif border == "left":
            snapped_x = self.main_window_pos[0] - self.main_window_size[0] - 1
            snapped_y = self.main_window_pos[1]
        elif border == "top":
            snapped_x = self.main_window_pos[0]
            snapped_y = self.main_window_pos[1] - self.window_size[1] - 1
        elif border == "bottom":
            snapped_x = self.main_window_pos[0]
            snapped_y = self.main_window_pos[1] + self.main_window_size[1] + 1
        else:
            # Fallback to right
            snapped_x = self.main_window_pos[0] + self.main_window_size[0] + 1
            snapped_y = self.main_window_pos[1]

        if self.is_snapped:
            PyImGui.set_next_window_pos(snapped_x, snapped_y)
            
        PyImGui.set_next_window_size(self.main_window_size[0] * 2, self.main_window_size[1])
            
        if self.window_module.begin():
            if PyImGui.begin_child("Log Messages", (0, 0), True, PyImGui.WindowFlags.AlwaysVerticalScrollbar):
                if PyImGui.begin_table("LogTable", 3, PyImGui.TableFlags.RowBg | PyImGui.TableFlags.ScrollY | PyImGui.TableFlags.Borders):
                    PyImGui.table_setup_column("Time", PyImGui.TableColumnFlags.WidthFixed, 75)
                    PyImGui.table_setup_column("Message", PyImGui.TableColumnFlags.WidthFixed, 150)
                    PyImGui.table_setup_column("Reason", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_headers_row()
                    for message in reversed(self.messages):
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text(f"{message.timestamp.strftime('%H:%M:%S')}")
                        
                        PyImGui.table_set_column_index(1)
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, message.color.to_tuple_normalized())
                        PyImGui.text_wrapped(message.message)
                        PyImGui.table_set_column_index(2)
                        PyImGui.text_wrapped(message.extra_info)
                        PyImGui.pop_style_color(1)
                    PyImGui.end_table()
                PyImGui.end_child()
            self.window_module.process_window()
        self.window_module.end()

    
    
#endregion

from Py4GWCoreLib import *
import os
module_name = "Instance Timer"

script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
ini_file_location = os.path.join(root_directory, "Widgets/Config/InstanceTimer.ini")

ini_handler = IniHandler(ini_file_location)
sync_interval = 1000

class Config:
    global ini_handler, module_name, sync_interval

    def __init__(self):
        # Read configuration values from INI file
        self.x = ini_handler.read_int(module_name, "x", 100)
        self.y = ini_handler.read_int(module_name, "y", 100)
        self.scale = ini_handler.read_float(module_name, "scale", 4.0)
        self.color = (
            ini_handler.read_float(module_name, "color_r", 1.0),
            ini_handler.read_float(module_name, "color_g", 1.0),
            ini_handler.read_float(module_name, "color_b", 1.0),
            ini_handler.read_float(module_name, "color_a", 1.0),
        )
        self.string = "00:00:00:000"
        self.true_instance_timer = ini_handler.read_bool(module_name, "true_instance_timer", False)
        self.instance_entry_time = 0
        self.initialized = False
        self.sync_interval = sync_interval

    def save(self):
        """Save the current configuration to the INI file."""
        ini_handler.write_key(module_name, "x", str(self.x))
        ini_handler.write_key(module_name, "y", str(self.y))
        ini_handler.write_key(module_name, "scale", str(self.scale))
        ini_handler.write_key(module_name, "color_r", str(self.color[0]))
        ini_handler.write_key(module_name, "color_g", str(self.color[1]))
        ini_handler.write_key(module_name, "color_b", str(self.color[2]))
        ini_handler.write_key(module_name, "color_a", str(self.color[3]))
        ini_handler.write_key(module_name, "true_instance_timer", str(self.true_instance_timer))


widget_config = Config()
window_module = ImGui.WindowModule(
    module_name, 
    window_name="Intance Timer##Instance Timer",
    window_size=(100, 100), 
    window_flags=PyImGui.WindowFlags(
        PyImGui.WindowFlags.AlwaysAutoResize | 
        PyImGui.WindowFlags.NoBackground | 
        PyImGui.WindowFlags.NoTitleBar | 
        PyImGui.WindowFlags.NoCollapse
    )
)

config_module = ImGui.WindowModule(f"Config {module_name}", window_name="Instance Timer Configuration##Instance Timer", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
window_x = ini_handler.read_int(module_name + " Config", "config_x", 100)
window_y = ini_handler.read_int(module_name + " Config", "config_y", 100)

config_module.window_pos = (window_x, window_y)

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()
instance_uptime = 0
is_map_ready = False
is_party_loaded = False

def configure():
    global widget_config, config_module, ini_handler

    if config_module.first_run:
        PyImGui.set_next_window_size(config_module.window_size[0], config_module.window_size[1])
        PyImGui.set_next_window_pos(config_module.window_pos[0], config_module.window_pos[1])
        config_module.first_run = False

    end_pos = config_module.window_pos
    if PyImGui.begin(config_module.window_name, config_module.window_flags):
        new_collapsed = PyImGui.is_window_collapsed()
        overlay = Overlay()
        screen_width, screen_height = overlay.GetDisplaySize().x, overlay.GetDisplaySize().y
        widget_config.x = PyImGui.slider_int("X", widget_config.x, 0, screen_width)
        widget_config.y = PyImGui.slider_int("Y", widget_config.y, 0, screen_height)
        widget_config.scale = PyImGui.slider_float("Scale", widget_config.scale, 1.0, 10.0)
        widget_config.color = PyImGui.color_edit4("Color", widget_config.color)
        widget_config.true_instance_timer = PyImGui.checkbox("True Instance Timer", widget_config.true_instance_timer)

        widget_config.save()
        end_pos = PyImGui.get_window_pos()

    PyImGui.end()

    if end_pos[0] != config_module.window_pos[0] or end_pos[1] != config_module.window_pos[1]:
        config_module.window_pos = (int(end_pos[0]), int(end_pos[1]))
        ini_handler.write_key(module_name + " Config", "config_x", str(int(end_pos[0])))
        ini_handler.write_key(module_name + " Config", "config_y", str(int(end_pos[1])))


def DrawWindow():
    global widget_config, window_module
    global instance_uptime

    if instance_uptime > 3600000:
        widget_config.string = FormatTime(instance_uptime, "hh:mm:ss:ms")
    else:
        widget_config.string = FormatTime(instance_uptime, "mm:ss:ms")

    PyImGui.set_next_window_pos(widget_config.x, widget_config.y)

    if PyImGui.begin(window_module.window_name, window_module.window_flags):
        PyImGui.text_scaled(widget_config.string,widget_config.color,widget_config.scale)
    PyImGui.end()




def main():
    global widget_config, instance_uptime
    global game_throttle_timer, game_throttle_time, is_map_ready, is_party_loaded

    if not widget_config.initialized and Map.IsMapReady():
        widget_config.initialized = True
        widget_config.instance_entry_time = Map.GetInstanceUptime()
        
    if game_throttle_timer.HasElapsed(game_throttle_time):
        is_map_ready = Map.IsMapReady()
        is_party_loaded = Party.IsPartyLoaded()
        
        if is_map_ready and is_party_loaded:
            instance_uptime = Map.GetInstanceUptime() - (0 if widget_config.true_instance_timer else widget_config.instance_entry_time )
        game_throttle_timer.Reset()

    if is_map_ready and is_party_loaded:
        DrawWindow()
    else:
        widget_config.initialized = False

if __name__ == "__main__":
    main()



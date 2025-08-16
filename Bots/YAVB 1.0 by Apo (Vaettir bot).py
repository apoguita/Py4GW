
from YAVB.YAVBMain import YAVB
from YAVB.LogConsole import LogConsole


_YAVB = YAVB()

def main():
    _YAVB.GUI.DrawMainWindow()
    if _YAVB.option_window_visible:
        _YAVB.GUI.DrawOptionsWindow()
    if _YAVB.console_visible:
        _YAVB.console.SetMainWindowPosition(_YAVB.main_window_pos)
        main_width, main_height = _YAVB.main_window_size
        options_width, options_height = _YAVB.option_window_size
        
        if _YAVB.option_window_snapped and _YAVB.option_window_visible:
            total_height = main_height + options_height
        else:
            total_height = main_height
        
        _YAVB.console.SetMainWindowSize((main_width, total_height))
        _YAVB.console.SetLogToFile(_YAVB.console_log_to_file)
        _YAVB.console.SetSnapped(_YAVB.console_snapped, _YAVB.console_snapped_border)
        _YAVB.console.DrawConsole()
        
    if _YAVB.FSM.finished:
        if _YAVB.script_running:
            _YAVB.script_running = False
            _YAVB.script_paused = False
            _YAVB.LogMessage("Script finished", "", LogConsole.LogSeverity.INFO)
            _YAVB.state = "Idle"
            _YAVB.FSM.stop()

            
    if _YAVB.script_running:
        _YAVB.FSM.update()
    
if __name__ == "__main__":
    main()

import PyImGui

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Widgets.CustomBehaviors.primitives.botting.botting_loader import BottingLoader, AvailableBot

# Global state for bot selection and control
_selected_bot_index = 0
_current_bot_instance = None
_bot_state = "STOPPED"  # STOPPED, PLAYING, PAUSED

def render():
    global _selected_bot_index, _current_bot_instance, _bot_state
    
    PyImGui.text(f"Multiboxing Bot Collection")
    PyImGui.separator()

    if not GLOBAL_CACHE.Party.IsPartyLeader():
        PyImGui.text(f"Feature restricted to party leader.")
        return

    # Load bot list if not already loaded
    botting_loader = BottingLoader()
    if not botting_loader._has_loaded:
        botting_loader.load_bot_list()

    # Bot selection combo box
    if len(botting_loader.available_bots) > 0:
        # Filter out bots with invalid names and create valid bot list
        valid_bots = []
        for bot in botting_loader.available_bots:
            if bot.instance.name is not None and bot.instance.name.strip():
                valid_bots.append(bot)
        
        if len(valid_bots) > 0:
            bot_names = [""] + [bot.instance.name for bot in valid_bots]
            # Ensure selected index is within bounds
            if _selected_bot_index >= len(bot_names):
                _selected_bot_index = 0
            
            # Initialize _current_bot_instance if it's None and we have valid bots
            if _current_bot_instance is None:
                _current_bot_instance = valid_bots[_selected_bot_index - 1].instance if _selected_bot_index > 0 else None
            
            new_index = PyImGui.combo("Select Bot", _selected_bot_index, bot_names)
            if new_index != _selected_bot_index:
                _selected_bot_index = new_index
                _current_bot_instance = valid_bots[_selected_bot_index - 1].instance if _selected_bot_index > 0 else None
                _bot_state = "STOPPED"  # Reset state when changing bots
        else:
            PyImGui.text("No valid bots available (all bots have invalid names)")
            return
        
        PyImGui.text(f"{_current_bot_instance}")


        # Display bot name and description
        if _current_bot_instance:
            PyImGui.text(f"Name: {_current_bot_instance.name}")
            PyImGui.text(f"Description: {_current_bot_instance.description}")
            PyImGui.separator()
            
            # Control buttons
            PyImGui.text(f"Status: {_bot_state}")
            
            if PyImGui.button("PLAY"):
                if _bot_state == "STOPPED" or _bot_state == "PAUSED":
                    _current_bot_instance.initialize()
                    _bot_state = "PLAYING"
            
            PyImGui.same_line(0.0, 5.0)
            if PyImGui.button("PAUSE"):
                if _bot_state == "PLAYING":
                    _bot_state = "PAUSED"
            
            PyImGui.same_line(0.0, 5.0)
            if PyImGui.button("STOP"):
                if _bot_state == "PLAYING" or _bot_state == "PAUSED":
                    _current_bot_instance.stop()
                    _bot_state = "STOPPED"
            
            # Execute bot logic if playing
            if _bot_state == "PLAYING":
                _current_bot_instance.act()
        else:
            PyImGui.text("No bot selected")
    else:
        PyImGui.text("No bots available")
        if PyImGui.button("Refresh Bot List"):
            botting_loader.refresh_bot_list()


    
import PyImGui

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract, StickPosition
from Widgets.CustomBehaviors.primitives.botting.botting_loader import BottingLoader, AvailableBot

# Global state for bot selection and control
_selected_bot_index = 0

def render():
    global _selected_bot_index
    
    PyImGui.text(f"Multiboxing Bot Collection")
    PyImGui.separator()
    
    if not GLOBAL_CACHE.Party.IsPartyLeader():
        PyImGui.text(f"Feature restricted to party leader.")
        return

    PyImGui.text_colored(f"additionnal custom_behaviors will be injected in the party leader.", Utils.ColorToTuple(Utils.RGBToColor(131, 250, 146, 255)))
    PyImGui.text_colored(f"it would act autonomously", Utils.ColorToTuple(Utils.RGBToColor(131, 250, 146, 255)))
    PyImGui.bullet_text(f"resign_if_needed_utility")
    PyImGui.bullet_text(f"move_to_distant_chest_if_path_exists_utility")
    PyImGui.bullet_text(f"move_if_stuck_utility")
    PyImGui.bullet_text(f"move_to_party_member_if_in_aggro_utility")
    PyImGui.bullet_text(f"move_to_enemy_if_close_enough_utility")
    PyImGui.bullet_text(f"move_to_party_member_if_dead_utility")
    PyImGui.bullet_text(f"wait_if_party_member_mana_too_low_utility")
    PyImGui.bullet_text(f"wait_if_party_member_too_far_utility")
    PyImGui.bullet_text(f"wait_if_party_member_needs_to_loot_utility")
    PyImGui.bullet_text(f"wait_if_in_aggro_utility")
    PyImGui.bullet_text(f"wait_if_lock_taken_utility")
    PyImGui.separator()


    # Load bot list if not already loaded
    botting_loader = BottingLoader()
    # if not botting_loader._has_loaded:
    #     botting_loader.load_bot_list()

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
            
            # Initialize botting_loader.current_bot_instance if it's None and we have valid bots
            new_index = PyImGui.combo("Select Bot", _selected_bot_index, bot_names)

            if new_index != _selected_bot_index:
                _old_index = _selected_bot_index
                _selected_bot_index = new_index

                # open new selected bot
                if _selected_bot_index > 0:
                    botting_loader.define_bot_as_active(_selected_bot_index - 1)
                    if botting_loader.get_active_bot() is not None:
                        botting_loader.get_active_bot().open_bot()
                else:
                    botting_loader.define_bot_as_active(None)

                #close previous one
                if _old_index > 0:
                    botting_loader.available_bots[_old_index - 1].instance.close_bot()

            

                #= valid_bots[_selected_bot_index - 1].instance if _selected_bot_index > 0 else None
        else:
            PyImGui.text("No valid bots available (all bots have invalid names)")
            return

        # Display bot name and description
        if botting_loader.get_active_bot() is not None:

            if botting_loader.get_active_bot().is_openned_bot():
                PyImGui.text(f"Name: {botting_loader.get_active_bot().name}")
                PyImGui.text_wrapped(f"Description: {botting_loader.get_active_bot().description}")
                PyImGui.separator()

                if not botting_loader.get_active_bot().is_botting_behavior_injected:
                    if PyImGui.button("inject custom botting behaviors"):
                        botting_loader.get_active_bot().inject_botting_behavior()
                else:
                    if PyImGui.button("remove custom botting behaviors"):
                        botting_loader.get_active_bot().remove_botting_behavior()
                
                if PyImGui.button("Toggle bot UI"):
                    botting_loader.get_active_bot().toggle_ui()
                if botting_loader.get_active_bot()._is_ui_visible:
                    PyImGui.same_line(0,5)
                    if PyImGui.button("Stick Left"):
                        botting_loader.get_active_bot().ui_stick_position = StickPosition.Left
                    PyImGui.same_line(0,5)
                    if PyImGui.button("Stick Right"):
                        botting_loader.get_active_bot().ui_stick_position = StickPosition.Right
                    PyImGui.same_line(0,5)
                    if PyImGui.button("Stick Bottom"):
                        botting_loader.get_active_bot().ui_stick_position = StickPosition.Bottom

        else:
            PyImGui.text("No bot selected")
    else:
        PyImGui.text("No bots available")
        if PyImGui.button("Refresh Bot List"):
            botting_loader.refresh_bot_list()
            botting_loader.load_bot_list()




    
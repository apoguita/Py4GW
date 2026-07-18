from Py4GWCoreLib import *
import os
module_name = "PCons Manager"

script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
ini_file_location = os.path.join(root_directory, "Widgets/Config/PCons.ini")
matching_items = []

ini_handler = IniHandler(ini_file_location)

class PCons:
    global ini_handler
    def __init__(self):
        self.ini_entry_name = module_name
        self.enable_module = ini_handler.read_bool(self.ini_entry_name, "Enable Module", False)
        self.aftercast = 500
        self.aftercast_timer = Timer()
        self.aftercast_timer.Start()
        self.pcons = {
            'Essence of Celerity': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Essence of Celerity", False),
                'effect_id': 2522,
                'model_id': 24859,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Grail of Might': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Grail of Might", False),
                'effect_id': 2521,
                'model_id': 24860,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Armor of Salvation': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Armor of Salvation", False),
                'effect_id': 2520,
                'model_id': 24861,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Red Rock Candy': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Red Rock Candy", False),
                'effect_id': 2973,
                'model_id': 21492,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Blue Rock Candy': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Blue Rock Candy", False),
                'effect_id': 2971,
                'model_id': 21488,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Green Rock Candy': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Green Rock Candy", False),
                'effect_id': 2972,
                'model_id': 21489,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Golden Egg': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Golden Egg", False),
                'effect_id': 1934,
                'model_id': 22752,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Birthday Cupcake': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Birthday Cupcake", False),
                'effect_id': 1945,
                'model_id': 22269,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Candy Corn': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Candy Corn", False),
                'effect_id': 2604,
                'model_id': 28433,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Candy Apple': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Candy Apple", False),
                'effect_id': 2605,
                'model_id': 28431,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Slice of Pumpkin Pie': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Slice of Pumpkin Pie", False),
                'effect_id': 2649,
                'model_id': 28432,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'War Supplies': {
                'active': ini_handler.read_bool(self.ini_entry_name, "War Supplies", False),
                'effect_id': 3174,
                'model_id': 32558,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Drake Kabob': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Drake Kabob", False),
                'effect_id': 1680,
                'model_id': 17060,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
            'Bowl of Skalefin Soup': {
                'active': ini_handler.read_bool(self.ini_entry_name, "Bowl of Skalefin Soup", False),
                'effect_id': 1681,
                'model_id': 17061,
                'internal_cooldown': 5000,
                'internal_timer': Timer()
            },
        }

    def save(self):
        ini_handler.write_key(self.ini_entry_name, "Enable Module", str(self.enable_module))
        for name, data in self.pcons.items():
            ini_handler.write_key(self.ini_entry_name,
                                  name, str(data['active']))

widget_config = PCons()
window_module = ImGui.WindowModule(module_name,window_name="PCons Manager", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

window_x = ini_handler.read_int(module_name +str(" Config"), "x", 100)
window_y = ini_handler.read_int(module_name +str(" Config"), "y", 100)
window_collapsed = ini_handler.read_bool(module_name +str(" Config"), "collapsed", False)

window_module.window_pos = (window_x, window_y)
window_module.collapse = window_collapsed

def handle_pcons():
    """Check and use PCONS if needed"""
    global widget_config, matching_items
    try:
        player_id = Player.GetAgentID()
        for pcon_name, data in widget_config.pcons.items():
            if data['active']:
                stack_size = 0
                if matching_items:
                    item = matching_items[0]
                    stack_size = Item.Properties.GetQuantity(item)
                    
                if stack_size == 0:
                    continue
                        
                has_effect = Effects.EffectExists(player_id, data['effect_id']) or Effects.BuffExists(player_id, data['effect_id'])
            
                if not has_effect:
                    items = ItemArray.GetItemArray([Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2])
                    matching_items = ItemArray.Filter.ByCondition(items, lambda item_id: Item.GetModelID(item_id) == data['model_id'])
                    if matching_items:
                        if data['internal_timer'].IsStopped() or data['internal_timer'].HasElapsed(data['internal_cooldown']):
                            data['internal_timer'].Stop()
                            Py4GW.Console.Log(module_name, f"Using {pcon_name}.", Py4GW.Console.MessageType.Debug)
                            ActionQueueManager().AddAction("ACTION", "UseItem", matching_items[0])
                            widget_config.aftercast_timer.Reset()
                            data['internal_timer'].Start()
                            return  # Exit after using one pcon

    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error monitoring PCONS: {str(e)}", Py4GW.Console.MessageType.Debug)

def DrawWindow():
    """Draw the PCONS manager window"""
    global window_module, widget_config, matching_items
    try:
        if window_module.first_run:
            PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])     
            PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
            PyImGui.set_next_window_collapsed(window_module.collapse, 0)
            window_module.first_run = False

        new_collapsed = True
        end_pos = window_module.window_pos

        if PyImGui.begin(window_module.window_name, window_module.window_flags):
            new_collapsed = PyImGui.is_window_collapsed()
            PyImGui.text("PCons Auto-Usage")
            PyImGui.separator()

            widget_config.enable_module = PyImGui.checkbox("PCcons enabled", widget_config.enable_module)

            if not widget_config.enable_module:
                PyImGui.text_colored("PCcons Module is disabled", (0.5, 0.5, 0.5, 1.0))
            else:
                if not Map.IsExplorable():
                    PyImGui.text_colored("PCcons Module only works in explorable area", (1.0, 1.0, 0.0, 1.0))

                PyImGui.separator()

                for name, data in widget_config.pcons.items():
                      
                    items = ItemArray.GetItemArray([Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2])
                    matching_items = ItemArray.Filter.ByCondition(items, lambda item_id: Item.GetModelID(item_id) == data['model_id'])
                    stack_size = 0
                
                    if matching_items:
                        item = matching_items[0]
                        stack_size = Item.Properties.GetQuantity(item)
                    
                    #color_status = data['active']
                    #if color_status:
                    #    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.RGBToNormal(200, 255, 150, 255))
                      
                    data['active'] = PyImGui.checkbox(f"{name} [{stack_size}] ", data['active'])   
                    
                    #if color_status:
                    #    PyImGui.pop_style_color(1)            
                    
                    if PyImGui.is_item_hovered():
                        ImGui.show_tooltip(f"Effect ID: {data['effect_id']}, Model ID: {data['model_id']}")
                        
                    

            widget_config.save()
            end_pos = PyImGui.get_window_pos()

        PyImGui.end()

        if end_pos[0] != window_module.window_pos[0] or end_pos[1] != window_module.window_pos[1]:
            ini_handler.write_key(module_name + " Config", "config_x", str(int(end_pos[0])))
            ini_handler.write_key(module_name + " Config", "config_y", str(int(end_pos[1])))

        if new_collapsed != window_module.collapse:
            ini_handler.write_key(module_name + " Config", "collapsed", str(new_collapsed))

    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Debug)

def main():
    """Required main function for the widget"""
    global widget_config
    
    return #disable the widget

    if Routines.Checks.Map.MapValid():
        DrawWindow()

        if widget_config.aftercast_timer.IsStopped() or widget_config.aftercast_timer.HasElapsed(widget_config.aftercast):
            widget_config.aftercast_timer.Stop()

            if widget_config.enable_module and Map.IsExplorable():
                handle_pcons()
                
        ActionQueueManager().ProcessQueue("ACTION")
    else:
        ActionQueueManager().ResetQueue("ACTION")



def configure():
    """Required configuration function for the widget"""
    pass

# These functions need to be available at module level
__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()

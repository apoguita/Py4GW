
from Py4GWCoreLib import *

#This script is intended to be a showcase of every Methos and all the data that can be accessed from Py4GW
#current status, not complete

module_name = "Py4GW DEMO"

class WindowState:
    def __init__(self):
        self.window_name = ""
        self.is_window_open =[]
        self.button_list = []
        self.description_list = []
        self.method_mapping = {}
        self.values = []

main_window_state = WindowState()
ImGui_window_state = WindowState()
ImGui_selectables_window_state = WindowState()
ImGui_input_fields_window_state = WindowState()
ImGui_tables_window_state = WindowState()
ImGui_misc_window_state = WindowState()

PyMap_window_state = WindowState()
PyMap_Travel_Window_state = WindowState()
PyMap_Extra_InfoWindow_state = WindowState()
PyAgent_window_state = WindowState()
PyAgent_agent_window_state = WindowState()
PyPlayer_window_state = WindowState()
PyParty_window_state = WindowState()
PyItem_window_state = WindowState()
PySkill_window_state = WindowState()
PyBuffs_window_state = WindowState()
Py4GW_window_state = WindowState()
Py4GW_descriptions = WindowState()
PyMerchant_descriptions = WindowState()


def calculate_grid_layout(total_buttons):
    # Find the smallest perfect square greater than or equal to total_buttons
    next_square = math.ceil(math.sqrt(total_buttons)) ** 2  # Next perfect square
    columns = int(math.sqrt(next_square))  # Number of columns is the square root of next_square
    rows = math.ceil(total_buttons / columns)  # Calculate number of rows needed
    return columns, rows


ping_handler = Py4GW.PingHandler()
timer_instance = Timer()
show_mouse_world_pos = False
show_area_rings = False
mark_target = False

quest_id = 0

def ShowQuestWindow():
    global merchant_index, PyMerchant_descriptions, hovered_item
    global w_width, w_height
    global quest_id
    try: 
        PyImGui.set_next_window_size(w_width, height_list[merchant_index])
        if PyImGui.begin(f"Quests"):
            
            PyImGui.text(f"Active Quest ID: {GLOBAL_CACHE.Quest.GetActiveQuest()}")
            quest_id = PyImGui.input_int("Quest ID", quest_id)

            if PyImGui.button("Set Active Quest"):
                GLOBAL_CACHE.Quest.SetActiveQuest(quest_id)

            if PyImGui.button("Abandon Quest"):
                GLOBAL_CACHE.Quest.AbandonQuest(quest_id)


        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowQuestWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
PyMerchant_descriptions.values = ["","","","","","","","","","","","",""]
PyMerchant_descriptions.values[0] = "PyMerchant class is in charge of handling every type of merchant.\nIt has methods pertinent to the merchants, \nTraders, Crafters and Collectors."
PyMerchant_descriptions.values[1] = """Traders
	    Material Trader
	    Rare Material Trader
	    Rune Trader
	    Dye Trader
	    Scroll Trader"""
PyMerchant_descriptions.values[2] = "Merchants"
PyMerchant_descriptions.values[3] = """Crafters
	    Weapon Crafters
	    Armor Crafters
	    Artisans [Material Crafters]
	    Consumable Crafters"""
PyMerchant_descriptions.values[4] = "Collectors"
merchant_index = 0
hovered_item = 0

w_width, w_height = 400,350
height_list = [450,650,750,800,800,0,0,0,0,0,0,0]

item_id = 0
item_to_pay = 0
cost= 0 
quote_requested = False
quantity = 0
trade_item_list = []
quantity_list = []

def ShowMerchantWindow():
    global merchant_index, PyMerchant_descriptions, hovered_item
    global w_width, w_height
    global item_id, cost
    global quote_requested, quantity, item_to_pay
    global trade_item_list, quantity_list
    try: 
        PyImGui.set_next_window_size(w_width, height_list[merchant_index])
        if PyImGui.begin(f"Merchants, Traders, Crafters and Collectors"):
            #ImGui.DrawTextWithTitle("PyMerchant class", PyMerchant_descriptions.values[merchant_index],8)

            if PyImGui.begin_child("Merchant Description Child", size=(w_width-20, 150),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
                PyImGui.text(f"{PyMerchant_descriptions.values[merchant_index]}")
                PyImGui.end_child()

            items = ["Select One..", "Traders", "Merchants", "Crafters", "Collectors"]
            merchant_index = PyImGui.combo("Type", merchant_index, items)
            PyImGui.text(f"Selected Combo Item: {merchant_index}")
            PyImGui.separator()

            item_list = GLOBAL_CACHE.Trading.Trader.GetOfferedItems()
            merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
            quoted_item_id = GLOBAL_CACHE.Trading.Trader.GetQuotedItemID()
            quoted_value = GLOBAL_CACHE.Trading.Trader.GetQuotedValue()
            transaction_complete = GLOBAL_CACHE.Trading.IsTransactionComplete()
            hover = GLOBAL_CACHE.Inventory.GetHoveredItemID()
            if hover != 0 :
                hovered_item = hover

            headers = ["Value", "Data"]

            data = [("Hovered Item:", hovered_item)]

            if merchant_index == 1:
                data.append(("Quoted Item ID:", quoted_item_id))
                data.append(("Quoted Value:", quoted_value))
                data.append(("Transaction Complete:", transaction_complete))

            ImGui.table("Trader Info", headers, data)

            if merchant_index == 1:
                PyImGui.text("Items Offered")
                

                if not item_list:
                    PyImGui.text("Interact with a trader to see their available Items")
                else:
                    if PyImGui.begin_table("Scrollable Table", 5, PyImGui.TableFlags.Borders | PyImGui.TableFlags.ScrollX | PyImGui.TableFlags.ScrollY | PyImGui.TableFlags.SizingStretchSame, w_width - 20, 150):
                        for index, item in enumerate(item_list):
                            if index % 5 == 0:
                                PyImGui.table_next_row()
                            PyImGui.table_set_column_index(index % 5)
                            PyImGui.text(f"{item}")
                        PyImGui.end_table()
            elif merchant_index > 1:
                PyImGui.text("Items Offered")
                if not merchant_item_list:
                    PyImGui.text("Interact with a merchant/crafter/collector to see their available Items")
                else:
                    if PyImGui.begin_table("Scrollable merchant Table", 5, PyImGui.TableFlags.Borders | PyImGui.TableFlags.ScrollX | PyImGui.TableFlags.ScrollY | PyImGui.TableFlags.SizingStretchSame, w_width - 20, 150):
                        for index, item in enumerate(merchant_item_list):
                            if index % 5 == 0:
                                PyImGui.table_next_row()
                            PyImGui.table_set_column_index(index % 5)
                            PyImGui.text(f"{item}")
                        PyImGui.end_table()

            PyImGui.text("Items to trade")
            item_id = PyImGui.input_int("Item ID", item_id)

            if merchant_index == 1:
                PyImGui.text(f"Cost: {quoted_value}")
                cost = quoted_value
            else:
                if merchant_index in [1,2,3]:
                    cost = PyImGui.input_int("Cost", cost)
                else:
                    cost = 0

            if merchant_index > 1:
                PyImGui.separator()
                PyImGui.text("Items to Pay with")
                item_to_pay = PyImGui.input_int("Item to Pay with", item_to_pay)
                quantity = PyImGui.input_int("Quantity", quantity)


            if merchant_index == 1:
                if PyImGui.begin_table("QuoteButtonTable", 2):
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)

                    if PyImGui.button("Request Trader Quote"):
                        GLOBAL_CACHE.Trading.Trader.RequestQuote(item_id)
                
                    PyImGui.table_set_column_index(1)
                
                    if PyImGui.button("Request Trader Sell Quote"):
                        GLOBAL_CACHE.Trading.Trader.RequestSellQuote(item_id)

                    PyImGui.end_table()

                if PyImGui.begin_table("TradeButtonTable", 2):
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)

                    if PyImGui.button("Buy Item"):
                        GLOBAL_CACHE.Trading.Trader.BuyItem(item_id, cost)

                    PyImGui.table_set_column_index(1)

                    if PyImGui.button("Sell Item"):
                        GLOBAL_CACHE.Trading.Trader.SellItem(item_id, cost)

                    PyImGui.end_table()

            if merchant_index == 2:
                if PyImGui.begin_table("TradeButtonTable", 2):
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)

                    if PyImGui.button("Buy Item"):
                        GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, cost)

                    PyImGui.table_set_column_index(1)

                    if PyImGui.button("Sell Item"):
                        GLOBAL_CACHE.Trading.Merchant.SellItem(item_id, cost)

                    PyImGui.end_table()

            if merchant_index in [3,4]:
                if PyImGui.begin_table("CrafterButtonTable", 2):
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)

                    if PyImGui.button("Add Item"):
                        trade_item_list.append(item_to_pay)
                        quantity_list.append(quantity)

                    PyImGui.table_set_column_index(1)

                    if PyImGui.button("Clear List"):
                        trade_item_list.clear()
                        quantity_list.clear()

                    PyImGui.end_table()

                if PyImGui.begin_table("Scrollable MultiItem Table", 2, PyImGui.TableFlags.Borders | PyImGui.TableFlags.ScrollX | PyImGui.TableFlags.ScrollY | PyImGui.TableFlags.SizingStretchSame, w_width - 20, 100):
                    for index, item in enumerate(trade_item_list):
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text(f"{item}")
                        PyImGui.table_set_column_index(1)
                        PyImGui.text(f"{quantity_list[index]}")
                    PyImGui.end_table()

            if merchant_index == 3:
                if PyImGui.begin_table("CrafterButtonTable", 2):
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)

                    if PyImGui.button("Craft Item"):
                        GLOBAL_CACHE.Trading.Crafter.CraftItem(item_id, cost, trade_item_list, quantity_list)
                    PyImGui.end_table()

            if merchant_index == 4:
                if PyImGui.begin_table("CollectorButtonTable", 2):
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)

                    if PyImGui.button("Exchange Item"):
                        GLOBAL_CACHE.Trading.Collector.ExghangeItem(item_id, cost, trade_item_list, quantity_list)
                    PyImGui.end_table()

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowMerchantWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


Py4GW_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Py4GW_descriptions.values = ["","","","","","","","","","","","",""]
Py4GW_descriptions.values[0] = "Py4Gw Provides a set of complementary classes that will aid in the development of scripts.\nRefer to the code for the complete instruction set."
Py4GW_descriptions.values[1] = "PyKeystroke class is in charge of handling the keystrokes.\nIt provides methods to send keystrokes aswell as key combos.\nIt has methods pertinent to the keystrokes and related to controlling key, keybind actions. \nYou can Interact with the game Keybind Engine aswell as controlling your character."
Py4GW_descriptions.values[2] = "PingHandler class is in charge of getting latency data froim the game.\nIt stores a given number of ticks in history and can handle basic statistics."       
Py4GW_descriptions.values[3] = "Timer class is in charge of handling timers.\n It provides methods to create, start, stop, and reset timers.\nIt has methods pertinent to the timers and related to controlling timer actions."
Py4GW_descriptions.values[4] = "Overlay() class is in charge of handling the Overlay().\nIt provides methods to show, hide, and toggle the Overlay().\nIt has methods pertinent to the Overlay() and related to controlling Overlay() actions."

description_index = 0

def ShowPy4GW_Window_main():
    global Py4GW_window_state, Py4GW_descriptions, description_index, ping_handler, timer_instance
    global show_mouse_world_pos, show_area_rings,mark_target
    global test_keystroke
    try: 
        width, height = 500,800
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Py4GW"):
           
            ImGui.DrawTextWithTitle("Py4GW class", Py4GW_descriptions.values[description_index],7)   

            PyImGui.separator()
            if PyImGui.collapsing_header("PyKeystroke"):
                if PyImGui.button("Show PyKeystroke Info"):
                    description_index = 1
            
                PyImGui.separator()

                key_names = [key.name for key in Key]
                if Py4GW_window_state.values[1] == 0:
                    Py4GW_window_state.values[1] = key_names.index("W")  # Default to W

                Py4GW_window_state.values[1] = PyImGui.combo(
                    "Key Combo",
                    Py4GW_window_state.values[1],  # Current selected index
                    key_names  # List of options to display
                )

                selected_key_name = key_names[Py4GW_window_state.values[1]]
                selected_key = Key[selected_key_name]  # Map to the actual Key enum

                PyImGui.text(f"Selected Combo Key: {selected_key_name}")

                if PyImGui.begin_table("ButtonTable", 3, PyImGui.TableFlags.Borders):
                    PyImGui.table_next_row()

                    # First button: Press the selected key
                    PyImGui.table_next_column()
                    if PyImGui.button(f"Press Key {selected_key_name}"):
                        Keystroke.Press(selected_key.value)

                    # Second button: Release the selected key
                    PyImGui.table_next_column()
                    if PyImGui.button(f"Release Key {selected_key_name}"):
                        Keystroke.Release(selected_key.value)

                    # Third button: Push (Press and Release) the selected key
                    PyImGui.table_next_column()
                    if PyImGui.button(f"Push Keystroke {selected_key_name}"):
                        Keystroke.PressAndRelease(selected_key.value)

                    PyImGui.end_table() 

            PyImGui.separator()

            if PyImGui.collapsing_header("PingHandler"):
                if PyImGui.button("Show PingHandler Info"):
                    description_index = 2


                current_ping = ping_handler.GetCurrentPing()
                average_ping = ping_handler.GetAveragePing()
                min_ping = ping_handler.GetMinPing()
                max_ping = ping_handler.GetMaxPing()

                headers = ["Value", "Data"]

                data = [
                    ("Current Ping:", current_ping),
                    ("Average Ping:", average_ping),
                    ("Min Ping:", min_ping),
                    ("Max Ping:", max_ping)
                 ]

                ImGui.table("PingHandler info", headers, data)

            PyImGui.separator()
            if PyImGui.collapsing_header("Timer"):
                if PyImGui.button("Show Timer Info"):
                    description_index = 3

                elapsed_time = timer_instance.GetElapsedTime()
                is_stopped = timer_instance.IsStopped()
                is_running = timer_instance.IsRunning()
                is_paused = timer_instance.IsPaused()
                has_elapsed_5000ms = timer_instance.HasElapsed(5000)

                headers = ["Value", "Data"]
                data = [
                    ("Elapsed Time:", elapsed_time),
                    ("Is Stopped:", is_stopped),
                    ("Is Running:", is_running),
                    ("Is Paused:", is_paused),
                    ("Has Elapsed 5000ms:", has_elapsed_5000ms) 
                 ]

                if PyImGui.button("Start Timer"):
                    timer_instance.Start()

                if PyImGui.button("Stop Timer"):
                    timer_instance.Stop()

                if PyImGui.button("Pause Timer"):
                    timer_instance.Pause()

                if PyImGui.button("Resume Timer"):
                    timer_instance.Resume()

                ImGui.table("Timer info", headers, data)

            if PyImGui.collapsing_header("Overlay()"):
                if PyImGui.button("Show Overlay() Info"):
                    description_index = 4

                mouse_x, mouse_y = Overlay().GetMouseCoords()

                headers = ["Mouse X", "Mouse Y"]
                data = [
                    (mouse_x, mouse_y)
                ]

                ImGui.table("Overlay() info", headers, data)

                mark_target = PyImGui.checkbox("Mark Target", mark_target)
                if mark_target:
                    target_id = GLOBAL_CACHE.Player.GetTargetID()
                    if target_id:
                        target_x, target_y, target_z = Agent.GetXYZ(target_id)
                        Overlay().DrawPoly3D(target_x, target_y, target_z, radius=72, color=0xFFFF0000,numsegments=32,thickness=5.0)
                        z_coord = Overlay().FindZ(target_x, target_y)
                        screen_x, screen_y = Overlay().WorldToScreen(target_x, target_y, z_coord)
                        Overlay().DrawText3D(target_x, target_y, target_z-130, "TARGET", color=0xFFFF0000, autoZ=False, centered=True, scale=2.0)


                show_mouse_world_pos= PyImGui.checkbox("Show Mouse World Position", show_mouse_world_pos)
                if show_mouse_world_pos:
                    PyImGui.text_colored("Do not abuse this function!",(1, 0, 0, 1))
                    PyImGui.text_colored("it is unstable on some conditions",(1, 0, 0, 1))
                    x,y,z = Overlay().GetMouseWorldPos()
                    agent_id = GLOBAL_CACHE.Player.GetAgentID()
                    player_x, player_y, player_z = GLOBAL_CACHE.Agent.GetXYZ(agent_id)
                    
                    headers = ["X", "Y", "Z"]
                    data = [
                        (f"{x:.2f}", f"{y:.2f}", f"{z:.2f}"),
                    ]

                    ImGui.table("Mouse World Position", headers, data)

                    headers = ["PlayerX", "PlayerY", "PlayerZ"]
                    data = [
                        (f"{player_x:.2f}", f"{player_y:.2f}", f"{player_z:.2f}")
                    ]

                    ImGui.table("Player Position", headers, data)

                PyImGui.separator()
                Overlay().DrawLine(100, 100, 500, 500)

                show_area_rings = PyImGui.checkbox("Show Area Rings", show_area_rings)
                if show_area_rings:
                    player_x, player_y, player_z = GLOBAL_CACHE.Agent.GetXYZ(GLOBAL_CACHE.Player.GetAgentID())

                    #GW Areas
                    Touch = 144
                    Adjacent = 166
                    Nearby = 252
                    Area = 322
                    Earshot = 1012
                    Spellcast = 1248
                    Spirit = 2500
                    Compass = 5000

                    segments = 64
                    Overlay().DrawPoly3D(player_x, player_y, player_z, radius=72, color=0xFF1E90FF,numsegments=segments,thickness=5.0)
                    Overlay().DrawPoly3D(player_x, player_y, player_z, radius=Touch, color=0xAB5A1EFF,numsegments=segments,thickness=5.0)
                    Overlay().DrawPoly3D(player_x, player_y, player_z, radius=Adjacent, color=0x3BC154FF,numsegments=segments,thickness=5.0)
                    Overlay().DrawPoly3D(player_x, player_y, player_z, radius=Nearby, color=0xE39626FF,numsegments=segments,thickness=5.0)
                    Overlay().DrawPoly3D(player_x, player_y, player_z, radius=Area, color=0xE3357EFF,numsegments=segments,thickness=5.0)


        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPy4GW_Window_main: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


PySkill_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
def ShowEffectsWindow():
    try: 
        width, height = 600,300
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Buffs and Effects"):

            buff_list = GLOBAL_CACHE.Effects.GetBuffs(GLOBAL_CACHE.Player.GetAgentID())
            effect_list = GLOBAL_CACHE.Effects.GetEffects(GLOBAL_CACHE.Player.GetAgentID())

            effects_headers = ["Effect ID", "Skill ID", "Skill Name", "Duration", "Attr. Level", "Time Remaining"]
            effects_data = [(effect.effect_id, effect.skill_id, PySkill.Skill(effect.skill_id).id.GetName(), 
                            effect.duration, effect.attribute_level, effect.time_remaining) for effect in effect_list]

            ImGui.table("Effects", effects_headers, effects_data)

            buffs_headers = ["Buff ID", "Skill ID","Name", "Target Agent"]
            buffs_data = [(buff.buff_id, buff.skill_id,PySkill.Skill(buff.skill_id).id.GetName(), buff.target_agent_id) for buff in buff_list]
            
            ImGui.table("Buffs", buffs_headers, buffs_data)

            PySkill_window_state.values[0] = PyImGui.input_int("Buff ID", PySkill_window_state.values[0])
            PySkill_window_state.values[1]  = ImGui.toggle_button("Drop Buff", PySkill_window_state.values[1])

            if PySkill_window_state.values[1]:
                GLOBAL_CACHE.Effects.DropBuff(PySkill_window_state.values[0])

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowEffectsWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def ShowSkillbarWindow():
    global PyAgent_agent_window_state
    try: 
        width, height = 300,500
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Skillbar"):

            if PyImGui.collapsing_header("Skillbar"):
                for skill_slot in range(1, 9):  # Loop from 1 to 8 (range is exclusive of the upper bound)
                    skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(skill_slot)
                    skill_name = GLOBAL_CACHE.Skill.GetName(skill_id)
                    if PyImGui.collapsing_header(skill_name):
                        skill = GLOBAL_CACHE.SkillBar.GetSkillData(skill_slot)
                        adrenaline_a = skill.adrenaline_a
                        adrenaline_b = skill.adrenaline_b
                        recharge = skill.recharge
                        event = skill.event

                        if PyImGui.button("Use Skill " + skill_name):
                            GLOBAL_CACHE.SkillBar.UseSkill(skill_slot)

                        headers = ["Values", "Data"]
                        data = [
                            ("Skill ID:", skill_id),
                            ("Adrenaline A:", adrenaline_a),
                            ("Adrenaline B:", adrenaline_b),
                            ("Recharge(cast timestamp):", recharge),
                            ("Event:", event)
                        ]
                        ImGui.table("skillbar skill info" + str(skill_slot), headers, data)
            
            if Party.GetHeroCount == 0:
                PyImGui.text("No Heroes in Party")
            else:
                if PyImGui.collapsing_header("Heroes"):
                    heroes = GLOBAL_CACHE.Party.GetHeroes()

                    for idx, hero in enumerate(heroes):
                        hero_id = hero.hero_id.GetID()
                        agent_id = hero.agent_id
                        hero_name = GLOBAL_CACHE.Party.Heroes.GetHeroNameById(hero_id)
                        hero_index = idx + 1

                        if PyImGui.collapsing_header(hero_name):

                            hero_skillbar = GLOBAL_CACHE.SkillBar.GetHeroSkillbar(hero_index)

                            for skill_slot in range(1, 9): 
                                if skill_slot - 1 < len(hero_skillbar):  # Ensure the index is valid
                                    skill = hero_skillbar[skill_slot-1]
                                    skill_name = GLOBAL_CACHE.Skill.GetName(skill.id.id)

                                    if PyImGui.collapsing_header(skill_name):
                                        adrenaline_a = skill.adrenaline_a
                                        adrenaline_b = skill.adrenaline_b
                                        recharge = skill.recharge
                                        event = skill.event

                                        if PyImGui.button("Hero Use Skill " + skill_name):
                                            GLOBAL_CACHE.SkillBar.HeroUseSkill(agent_id, skill_slot, hero_index)

                                        headers = ["Values", "Data"]
                                        data = [
                                            ("Skill ID:", skill.id.id),
                                            ("Adrenaline A:", adrenaline_a),
                                            ("Adrenaline B:", adrenaline_b),
                                            ("Recharge(cast timestamp):", recharge),
                                            ("Event:", event)
                                        ]
                                        ImGui.table("hero skillbar skill info" + str(skill_slot), headers, data)

                    

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowAgentArrayWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def ShowSkillDataWindow(skill_id):
    global PyAgent_agent_window_state
    try: 
        width, height = 550,600
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Skill" + str(skill_id)):  

            
            name = GLOBAL_CACHE.Skill.GetName(skill_id)
            type_id, type_name = GLOBAL_CACHE.Skill.GetType(skill_id)
            campaign_id, campaign_name = GLOBAL_CACHE.Skill.GetCampaign(skill_id)
            profession_id, profession_name = GLOBAL_CACHE.Skill.GetProfession(skill_id)

            headers = ["Values","Data"]
            data = [
                ("skill_id:", skill_id),
                ("Name:", name),
                ("Type:", f"{type_id} - {type_name}"),
                ("Campaign:", f"{campaign_id} - {campaign_name}"),
                ("Profession:", f"{profession_id} - {profession_name}")
            ]
            
            ImGui.table("skill comon info" + str(skill_id), headers, data)

            if PyImGui.collapsing_header("Skill Data"):

                combo = GLOBAL_CACHE.Skill.Data.GetCombo(skill_id)
                combo_req = GLOBAL_CACHE.Skill.Data.GetComboReq(skill_id)
                weapon_req = GLOBAL_CACHE.Skill.Data.GetWeaponReq(skill_id)
                overcast = GLOBAL_CACHE.Skill.Data.GetOvercast(skill_id)
                energy_cost = GLOBAL_CACHE.Skill.Data.GetEnergyCost(skill_id)
                health_cost = GLOBAL_CACHE.Skill.Data.GetHealthCost(skill_id)
                adrenaline = GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id)
                adrenaline_a = GLOBAL_CACHE.Skill.Data.GetAdrenalineA(skill_id)
                adrenaline_b = GLOBAL_CACHE.Skill.Data.GetAdrenalineB(skill_id)
                activation = GLOBAL_CACHE.Skill.Data.GetActivation(skill_id)
                aftercast = GLOBAL_CACHE.Skill.Data.GetAftercast(skill_id)
                recharge = GLOBAL_CACHE.Skill.Data.GetRecharge(skill_id)
                recharge2 = GLOBAL_CACHE.Skill.Data.GetRecharge2(skill_id)
                aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(skill_id)

                headers = ["Values","Data"]
                data = [
                    ("Combo:", combo),
                    ("Combo Req:", combo_req),
                    ("Weapon Req:", weapon_req),
                    ("Overcast:", overcast),
                    ("Energy Cost:", energy_cost),
                    ("Health Cost:", health_cost),
                    ("Adrenaline:", adrenaline),
                    ("Adrenaline A:", adrenaline_a),
                    ("Adrenaline B:", adrenaline_b),
                    ("Activation:", activation),
                    ("Aftercast:", aftercast),
                    ("Recharge:", recharge),
                    ("Recharge2:", recharge2),
                    ("Aoe Range:", aoe_range)
                ]
            
                ImGui.table("skill data info" + str(skill_id), headers, data)

            if PyImGui.collapsing_header("Attribute"):
                
                attribute = GLOBAL_CACHE.Skill.Attribute.GetAttribute(skill_id)
                attribute_name = attribute.GetName()
                attribute_level = attribute.level
                attribute_level_base = attribute.level_base
                scale0, scale15 = GLOBAL_CACHE.Skill.Attribute.GetScale(skill_id)
                bonus_ascale0, bonus_ascale15 = GLOBAL_CACHE.Skill.Attribute.GetBonusScale(skill_id)
                duration_0, duration_15 = GLOBAL_CACHE.Skill.Attribute.GetDuration(skill_id)


                headers = ["Values","Data"]
                data = [
                    ("Name:", attribute_name),
                    ("Level:", attribute_level),
                    ("Level Base:", attribute_level_base),
                    ("Scale 0:", scale0),
                    ("Scale 15:", scale15),
                    ("Bonus Scale 0:", bonus_ascale0),
                    ("Bonus Scale 15:", bonus_ascale15),
                    ("Duration 0:", duration_0),
                    ("Duration 15:", duration_15)
                ]
            
                ImGui.table("skill attribute info" + str(skill_id), headers, data)

            if PyImGui.collapsing_header("Flags"):
                is_touch_range = GLOBAL_CACHE.Skill.Flags.IsTouchRange(skill_id)
                is_elite = GLOBAL_CACHE.Skill.Flags.IsElite(skill_id)
                is_half_range = GLOBAL_CACHE.Skill.Flags.IsHalfRange(skill_id)
                is_pvp = GLOBAL_CACHE.Skill.Flags.IsPvP(skill_id)
                is_pve = GLOBAL_CACHE.Skill.Flags.IsPvE(skill_id)
                is_playable = GLOBAL_CACHE.Skill.Flags.IsPlayable(skill_id)
                is_stacking = GLOBAL_CACHE.Skill.Flags.IsStacking(skill_id)
                is_non_stacking = GLOBAL_CACHE.Skill.Flags.IsNonStacking(skill_id)
                is_unused = GLOBAL_CACHE.Skill.Flags.IsUnused(skill_id)
                is_hex = GLOBAL_CACHE.Skill.Flags.IsHex(skill_id)
                is_bounty = GLOBAL_CACHE.Skill.Flags.IsBounty(skill_id)
                is_scroll = GLOBAL_CACHE.Skill.Flags.IsScroll(skill_id)
                is_stance = GLOBAL_CACHE.Skill.Flags.IsStance(skill_id)
                is_spell = GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id)
                is_enchantment = GLOBAL_CACHE.Skill.Flags.IsEnchantment(skill_id)
                is_signet = GLOBAL_CACHE.Skill.Flags.IsSignet(skill_id)
                is_condition = GLOBAL_CACHE.Skill.Flags.IsCondition(skill_id)
                is_well = GLOBAL_CACHE.Skill.Flags.IsWell(skill_id)
                is_skill = GLOBAL_CACHE.Skill.Flags.IsSkill(skill_id)
                is_ward = GLOBAL_CACHE.Skill.Flags.IsWard(skill_id)
                is_glyph = GLOBAL_CACHE.Skill.Flags.IsGlyph(skill_id)
                is_title = GLOBAL_CACHE.Skill.Flags.IsTitle(skill_id)
                is_attack = GLOBAL_CACHE.Skill.Flags.IsAttack(skill_id)
                is_shout = GLOBAL_CACHE.Skill.Flags.IsShout(skill_id)
                is_skill2 = GLOBAL_CACHE.Skill.Flags.IsSkill2(skill_id)
                is_passive = GLOBAL_CACHE.Skill.Flags.IsPassive(skill_id)
                is_environmental = GLOBAL_CACHE.Skill.Flags.IsEnvironmental(skill_id)
                is_preparation = GLOBAL_CACHE.Skill.Flags.IsPreparation(skill_id)
                is_pet_attack = GLOBAL_CACHE.Skill.Flags.IsPetAttack(skill_id)
                is_trap = GLOBAL_CACHE.Skill.Flags.IsTrap(skill_id)
                is_ritual = GLOBAL_CACHE.Skill.Flags.IsRitual(skill_id)
                is_environmantal_trap = GLOBAL_CACHE.Skill.Flags.IsEnvironmentalTrap(skill_id)
                is_item_spell = GLOBAL_CACHE.Skill.Flags.IsItemSpell(skill_id)
                is_weapon_spell = GLOBAL_CACHE.Skill.Flags.IsWeaponSpell(skill_id)
                is_form = GLOBAL_CACHE.Skill.Flags.IsForm(skill_id)
                is_chant = GLOBAL_CACHE.Skill.Flags.IsChant(skill_id)
                is_echo_refrain = GLOBAL_CACHE.Skill.Flags.IsEchoRefrain(skill_id)
                is_disguise = GLOBAL_CACHE.Skill.Flags.IsDisguise(skill_id)


                headers = ["Values","Data"]
                data = [
                    ("Is Touch Range:", is_touch_range),
                    ("Is Elite:", is_elite),
                    ("Is Half Range:", is_half_range),
                    ("Is PvP:", is_pvp),
                    ("Is PvE:", is_pve),
                    ("Is Playable:", is_playable),
                    ("Is Stacking:", is_stacking),
                    ("Is Non Stacking:", is_non_stacking),
                    ("Is Unused:", is_unused),
                    ("Is Hex:", is_hex),
                    ("Is Bounty:", is_bounty),
                    ("Is Scroll:", is_scroll),
                    ("Is Stance:", is_stance),
                    ("Is Spell:", is_spell),
                    ("Is Enchantment:", is_enchantment),
                    ("Is Signet:", is_signet),
                    ("Is Condition:", is_condition),
                    ("Is Well:", is_well),
                    ("Is Skill:", is_skill),
                    ("Is Ward:", is_ward),
                    ("Is Glyph:", is_glyph),
                    ("Is Title:", is_title),
                    ("Is Attack:", is_attack),
                    ("Is Shout:", is_shout),
                    ("Is Skill2:", is_skill2),
                    ("Is Passive:", is_passive),
                    ("Is Environmental:", is_environmental),
                    ("Is Preparation:", is_preparation),
                    ("Is Pet Attack:", is_pet_attack),
                    ("Is Trap:", is_trap),
                    ("Is Ritual:", is_ritual),
                    ("Is Environmental Trap:", is_environmantal_trap),
                    ("Is Item Spell:", is_item_spell),
                    ("Is Weapon Spell:", is_weapon_spell),
                    ("Is Form:", is_form),
                    ("Is Chant:", is_chant),
                    ("Is Echo Refrain:", is_echo_refrain),
                    ("Is Disguise:", is_disguise)
                ]
                
                ImGui.table("skill flags info" + str(skill_id), headers, data)

            if PyImGui.collapsing_header("Animations"):

                effect1, effect2 = GLOBAL_CACHE.Skill.Animations.GetEffects(skill_id)
                special = GLOBAL_CACHE.Skill.Animations.GetSpecial(skill_id)
                const_effect = GLOBAL_CACHE.Skill.Animations.GetConstEffect(skill_id)
                caster_overhead_animation_id = GLOBAL_CACHE.Skill.Animations.GetCasterOverheadAnimationID(skill_id)
                caster_body_animation_id = GLOBAL_CACHE.Skill.Animations.GetCasterBodyAnimationID(skill_id)
                target_body_animation_id = GLOBAL_CACHE.Skill.Animations.GetTargetBodyAnimationID(skill_id)
                target_overhead_animation_id = GLOBAL_CACHE.Skill.Animations.GetTargetOverheadAnimationID(skill_id)
                projectile_animation_1,projectile_animation_2 = GLOBAL_CACHE.Skill.Animations.GetProjectileAnimationID(skill_id)
                icon_file_id1, icon_file_id2 = GLOBAL_CACHE.Skill.Animations.GetIconFileID(skill_id)

                headers = ["Values","Data"]

                data = [
                    ("Effect 1:", effect1),
                    ("Effect 2:", effect2),
                    ("Special:", special),
                    ("Const Effect:", const_effect),
                    ("Caster Overhead Animation ID:", caster_overhead_animation_id),
                    ("Caster Body Animation ID:", caster_body_animation_id),
                    ("Target Body Animation ID:", target_body_animation_id),
                    ("Target Overhead Animation ID:", target_overhead_animation_id),
                    ("Projectile Animation 1:", projectile_animation_1),
                    ("Projectile Animation 2:", projectile_animation_2),
                    ("Icon File ID 1:", icon_file_id1),
                    ("Icon File ID 2:", icon_file_id2)
                ]

                ImGui.table("skill animations info" + str(skill_id), headers, data)

            if PyImGui.collapsing_header("ExtraData"):
                condition = GLOBAL_CACHE.Skill.ExtraData.GetCondition(skill_id)
                title = GLOBAL_CACHE.Skill.ExtraData.GetTitle(skill_id)
                id_pvp = GLOBAL_CACHE.Skill.ExtraData.GetIDPvP(skill_id)
                target = GLOBAL_CACHE.Skill.ExtraData.GetTarget(skill_id)
                skill_equip_type = GLOBAL_CACHE.Skill.ExtraData.GetSkillEquipType(skill_id)
                skill_arguments = GLOBAL_CACHE.Skill.ExtraData.GetSkillArguments(skill_id)
                name_id = GLOBAL_CACHE.Skill.ExtraData.GetNameID(skill_id)
                concise = GLOBAL_CACHE.Skill.ExtraData.GetConcise(skill_id)
                description_id = GLOBAL_CACHE.Skill.ExtraData.GetDescriptionID(skill_id)

                headers = ["Values","Data"]
                data = [
                    ("Condition:", condition),
                    ("Title:", title),
                    ("ID PvP:", id_pvp),
                    ("Target:", target),
                    ("Equip Type:", skill_equip_type),
                    ("Skill Arguments:", skill_arguments),
                    ("Name ID:", name_id),
                    ("Concise:", concise),
                    ("Description ID:", description_id)
                ]

                ImGui.table("skill extra data info" + str(skill_id), headers, data)

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowSkillDataWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

PySkill_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
def ShowSkillWindow():
    global PyAgent_agent_window_state
    try: 
        width, height = 550,300
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Skill"):

            description = "Skill class is in charge of handling the skills.\nIt provides methods to retrieve skill data, like skill name, description, type, etc.\nIt has methods pertinent to the skill and related to controlling skill actions."
            ImGui.DrawTextWithTitle("AgentArray class", description,6)   

            hovered_skill = GLOBAL_CACHE.SkillBar.GetHoveredSkillID()
            headers = ["Hovered Skill","Name"]
            data = [
                (hovered_skill, GLOBAL_CACHE.Skill.GetName(hovered_skill).replace("_", " "))
            ]
            
            ImGui.table("hovered info", headers, data)

            PySkill_window_state.values[0] = PyImGui.input_int("SkillID", PySkill_window_state.values[0])
            PySkill_window_state.values[1]  = ImGui.toggle_button("Show Item Data", PySkill_window_state.values[1])

            if  PySkill_window_state.values[1]:
                ShowSkillDataWindow(PySkill_window_state.values[0])

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowSkillWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

inventory_handler = PyInventory.PyInventory()

def ShowInventoryWindow():
    global PyAgent_agent_window_state, inventory_handler, salvage_timer
    try: 
        width, height = 500,500
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Inventory"):

            description = """The ItemArray class is in charge of handling the items in the game.\nIt provides methods to retrieve item data, like item type, rarity, properties, etc.\n They can be filtered, sorted, and manipulated in a way that is useful for inventory analysis.\nRefer to code for complete instruction set."""

            ImGui.DrawTextWithTitle("Inventory class", description,7) 
            
            def format_currency(amount):
                platinum = amount // 1000 
                gold = amount % 1000 
                return f"{platinum} plat {gold} gold"

            headers = ["Value","Data"]
            data = [
                ("Hovered ItemID:", GLOBAL_CACHE.Inventory.GetHoveredItemID()),
                ("ID Kit with lowest uses:", GLOBAL_CACHE.Inventory.GetFirstIDKit()),
                ("Salvage Kit with lowest uses", GLOBAL_CACHE.Inventory.GetFirstSalvageKit()),
                ("First Unidentified Item in bags:", GLOBAL_CACHE.Inventory.GetFirstUnidentifiedItem()),
                ("Fisrt Unsalvaged Item on Bags",GLOBAL_CACHE.Inventory.GetFirstSalvageableItem()),
                ("Gold On Character:", format_currency(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())),
                ("Gold In Storage:", format_currency(GLOBAL_CACHE.Inventory.GetGoldInStorage())),
            ]

            ImGui.table("Inventory common info", headers, data)

            if PyImGui.button("Identify First Available Item"):
                GLOBAL_CACHE.Inventory.IdentifyFirst()

            PyImGui.separator()

            if PyImGui.button("Salvage First Available Item"):

                # Get the first available Salvage Kit
                salvage_kit_id = GLOBAL_CACHE.Inventory.GetFirstSalvageKit()
                if salvage_kit_id == 0:
                    Py4GW.Console.Log("SalvageFirst", "No salvage kit found.")
                    return False

                # Find the first salvageable item based on the rarity filter
                salvage_item_id = GLOBAL_CACHE.Inventory.GetFirstSalvageableItem()
                if salvage_item_id == 0:
                    Py4GW.Console.Log("SalvageFirst", "No salvageable item found.")
                    return False

                # Use the Salvage Kit to salvage the item
                GLOBAL_CACHE.Inventory.SalvageItem(salvage_item_id,salvage_kit_id)
                Py4GW.Console.Log("SalvageFirst", f"Started salvaging item with Item ID: {salvage_item_id} using Salvage Kit ID: {salvage_kit_id}")

            if PyImGui.button("Handle Salvage UI"):
                inventory_handler.AcceptSalvageWindow()


            PyImGui.separator()
            if GLOBAL_CACHE.Inventory.IsStorageOpen():
                button_caption = "Inventory Open"
            else:
                button_caption = "Inventory Closed"
            
            PyImGui.text(button_caption)
            if PyImGui.button("Open Xunlai Chest"):
                GLOBAL_CACHE.Inventory.OpenXunlaiWindow()





        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowInventoryWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def format_binary_grouped(value: int, group_size: int = 4) -> str:
    binary_str = bin(value)[2:]  # strip the "0b"
    pad_len = (group_size - len(binary_str) % group_size) % group_size
    binary_str = '0' * pad_len + binary_str
    return ' '.join(binary_str[i:i + group_size] for i in range(0, len(binary_str), group_size))


_item_names = {}

def ShowItemDataWindow(item_id):
    global _item_name
    try: 
        width, height = 700,700
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Item: " + str(item_id)):
            pass
            
            item_type_id, item_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
            
            if item_id in _item_names:
                item_name = _item_names[item_id]
            else:
                item_name = GLOBAL_CACHE.Item.GetName(item_id)
                if item_name:  # Only cache if a valid (non-empty) name is returned
                    _item_names[item_id] = item_name
                else:
                    item_name = "Not recieved"  # Show placeholder, don't cache yet

                

            headers = ["Value","Data"]
            data = [
                ("Item Name:", item_name),
                ("Item Type:", f"{item_type_id} - {item_type_name}"),
                ("Model Id:", GLOBAL_CACHE.Item.GetModelID(item_id)),
                ("Slot(pick up to see):", GLOBAL_CACHE.Item.GetSlot(item_id)),
                ("AgentId(drop in ground to see)",GLOBAL_CACHE.Item.GetAgentID(item_id)),
                ("AgentItemID",GLOBAL_CACHE.Item.GetAgentItemID(item_id)),
            ]

            ImGui.table("Item common info", headers, data)
            
            if PyImGui.collapsing_header("Rarity"):
            
                rarity_id, rarity_name = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
                is_white = GLOBAL_CACHE.Item.Rarity.IsWhite(item_id)
                is_blue = GLOBAL_CACHE.Item.Rarity.IsBlue(item_id)
                is_purple = GLOBAL_CACHE.Item.Rarity.IsPurple(item_id)
                is_gold = GLOBAL_CACHE.Item.Rarity.IsGold(item_id)
                is_green = GLOBAL_CACHE.Item.Rarity.IsGreen(item_id)
                
                if is_white:
                    rarity_name = "White"
                elif is_blue:
                    rarity_name = "Blue"
                elif is_purple:
                    rarity_name = "Purple"
                elif is_gold:
                    rarity_name = "Gold"
                elif is_green:
                    rarity_name = "Green"
                    
                PyImGui.text(f"Rarity: {rarity_name}")

                headers = ["Rarity Type", "Rarity"]
                data = [
                    (rarity_id,rarity_name)
                ]

                ImGui.table("Item rarity common info", headers, data)

            if PyImGui.collapsing_header("Properties"):
                
   
                headers = ["Value", "Data"]
                data = [
                    ("IsCustomized:",GLOBAL_CACHE.Item.Properties.IsCustomized(item_id)),
                    ("Value:",GLOBAL_CACHE.Item.Properties.GetValue(item_id)),
                    ("Quantity:",GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)),
                    ("IsEquipped:",GLOBAL_CACHE.Item.Properties.IsEquipped(item_id)),
                    ("Profession:",GLOBAL_CACHE.Item.Properties.GetProfession(item_id)),
                    ("Interaction:",GLOBAL_CACHE.Item.Properties.GetInteraction(item_id)),
                    ("Interaction(Bin):",bin(GLOBAL_CACHE.Item.Properties.GetInteraction(item_id))),
                ]
                ImGui.table("Item properties common info", headers, data)

            if PyImGui.collapsing_header("Type"):

                headers = ["Value", "Data"]
                data = [
                    ("IsWeapon:",GLOBAL_CACHE.Item.Type.IsWeapon(item_id)),
                    ("IsArmor:",GLOBAL_CACHE.Item.Type.IsArmor(item_id)),
                    ("IsInventoryItem:",GLOBAL_CACHE.Item.Type.IsInventoryItem(item_id)),
                    ("IsStorageItem:",GLOBAL_CACHE.Item.Type.IsStorageItem(item_id)),
                    ("IsMaterial:",GLOBAL_CACHE.Item.Type.IsMaterial(item_id)),
                    ("IsRareMaterial:",GLOBAL_CACHE.Item.Type.IsMaterial(item_id)),
                    ("IsZCoin:",GLOBAL_CACHE.Item.Type.IsZCoin(item_id)),
                    ("IsTome",GLOBAL_CACHE.Item.Type.IsTome(item_id)),
                ]
                ImGui.table("Item properties common info", headers, data)

            if PyImGui.collapsing_header("Usage"):

                headers = ["Value", "Data"]
                data = [
                    ("IsUsable:",GLOBAL_CACHE.Item.Usage.IsUsable(item_id)),
                    ("Uses:",GLOBAL_CACHE.Item.Usage.GetUses(item_id)),
                    ("IsSalvageable:",GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id)),
                    ("IsMaterialSalvageable:",GLOBAL_CACHE.Item.Usage.IsMaterialSalvageable(item_id)),
                    ("IsSalvageKit:",GLOBAL_CACHE.Item.Usage.IsSalvageKit(item_id)),
                    ("IsLesserKit:",GLOBAL_CACHE.Item.Usage.IsLesserKit(item_id)),
                    ("IsExpertSalvageKit:",GLOBAL_CACHE.Item.Usage.IsExpertSalvageKit(item_id)),
                    ("IsPerfectSalvageKit:",GLOBAL_CACHE.Item.Usage.IsPerfectSalvageKit(item_id)),
                    ("IsIDKit:",GLOBAL_CACHE.Item.Usage.IsIDKit(item_id)),
                    ("IsIdentified:",GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)),

                ]
                ImGui.table("Item usage common info", headers, data)

            if PyImGui.collapsing_header("customization"):

                interaction_value = Item.Properties.GetInteraction(item_id)
                formatted_bin = format_binary_grouped(interaction_value)

                headers = ["Value", "Data"]
                data = [
                    ("IsInscription:",GLOBAL_CACHE.Item.Customization.IsInscription(item_id)),
                    ("IsInscribable:",GLOBAL_CACHE.Item.Customization.IsInscribable(item_id)),
                    ("IsPrefixUpgradable:",GLOBAL_CACHE.Item.Customization.IsPrefixUpgradable(item_id)),
                    ("IsSuffixUpgradable:",GLOBAL_CACHE.Item.Customization.IsSuffixUpgradable(item_id)),
                    ("Item Formula:",GLOBAL_CACHE.Item.Customization.GetItemFormula(item_id)),
                    ("Item Formula(Hex):",hex(GLOBAL_CACHE.Item.Customization.GetItemFormula(item_id))),
                    ("Item Formula(Bin):",bin(GLOBAL_CACHE.Item.Customization.GetItemFormula(item_id))),
                    ("Interaction:",GLOBAL_CACHE.Item.Properties.GetInteraction(item_id)),
                    ("Interaction(Bin):",formatted_bin),
                    
                    ("IsStackable:",GLOBAL_CACHE.Item.Customization.IsStackable(item_id)),
                    ("IsSparkly:",GLOBAL_CACHE.Item.Customization.IsSparkly(item_id)),
                ]
                ImGui.table("Item customization common info", headers, data)

                if PyImGui.collapsing_header("Modifiers"):

                    modifiers = GLOBAL_CACHE.Item.Customization.Modifiers.GetModifiers(item_id)
                    modifier_count = GLOBAL_CACHE.Item.Customization.Modifiers.GetModifierCount(item_id)

                    PyImGui.text("Modifier Count: " + str(modifier_count))


                    if modifier_count == 0:
                        PyImGui.text("No Modifiers")
                    else:
                        for idx, modifier in enumerate(modifiers):
                            identifier = modifier.GetIdentifier()
                            is_valid = modifier.IsValid()
                            arg = modifier.GetArg()
                            arg1 = modifier.GetArg1()
                            arg2 = modifier.GetArg2()
                            headers = ["Value", "Dec", "Hex", "Bin"]
                            data = [
                                ("Identifier:",identifier,hex(identifier),bin(identifier)),
                                ("IsValid:",is_valid,hex(is_valid),bin(is_valid)),
                                ("Arg:",arg,hex(arg),bin(arg)),
                                ("Arg1:",arg1,hex(arg1),bin(arg1)),
                                ("Arg2:",arg2,hex(arg2),bin(arg2)),
                            ]
                            ImGui.table("Item modifier common info"+ str(idx + 1), headers, data)

                if PyImGui.collapsing_header("DyeInfo"):
                    dye_info = GLOBAL_CACHE.Item.Customization.GetDyeInfo(item_id)
                    dye_tint = dye_info.dye_tint

                    PyImGui.text(f"Dye Tint: {dye_tint}")
                    
                    dye1 = dye_info.dye1
                    dye2 = dye_info.dye2
                    dye3 = dye_info.dye3
                    dye4 = dye_info.dye4

                    headers = ["Value", "ID", "Name"]
                    data = [
                    ("Dye1:",dye1.ToInt(),dye1.ToString()),
                    ("Dye2:",dye2.ToInt(),dye2.ToString()),
                    ("Dye3:",dye3.ToInt(),dye3.ToString()),
                    ("Dye4:",dye4.ToInt(),dye4.ToString()),
                    ]

                    ImGui.table("Item Dye common info", headers, data)

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowItemWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

PyItem_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
def ShowItemWindow():
    global PyItem_window_state
    try: 
        width, height = 400,300
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Items"):

            description = "Item class is in charge of handling the items.\nIt provides methods to retrieve ittem data. \nIn Py4GW Item Attributres are categorized in subclasses, \nbut this has no bearing on the actual item funciton."
            ImGui.DrawTextWithTitle("Item class", description,7)   

            hovered_item = GLOBAL_CACHE.Inventory.GetHoveredItemID()

            headers = ["Hovered ItemID"]
            data = [
                (f"{hovered_item}")
            ]

            ImGui.table("Item info", headers, data)

            PyItem_window_state.values[0] = PyImGui.input_int("ItemID", PyItem_window_state.values[0])

            PyItem_window_state.values[1]  = ImGui.toggle_button("Show Item Data",PyItem_window_state.values[1])

            if PyItem_window_state.values[1]:
                GLOBAL_CACHE.Item.RequestName(PyItem_window_state.values[0])
                ShowItemDataWindow(PyItem_window_state.values[0])

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowItemWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

PyParty_window_state.values = [0, 0, "Ogden Stonehealer", 0, 0, 0, 0, 0, 0, 0, 0]
def ShowPartyWindow():
    global PyParty_window_state
    try: 
        width, height = 800,800
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Party"):

            #description = "Party class is in charge of handling the party members.\nIt provides methods to retrieve party data, like heroes, henchmen, players and pets.\nIt has methods pertinent to the party and related to controlling party actions.\nParty members are agents, and as such, their data is retrieved from the Agent object."
            #ImGui.DrawTextWithTitle("Party class", description,7)  

            login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(Player.GetAgentID())
            party_number = GLOBAL_CACHE.Party.Players.GetPartyNumberFromLoginNumber(login_number)
            
            headers = ["Info", "Value"]
            data = [
                ("Party ID:", GLOBAL_CACHE.Party.GetPartyID()),
                ("Leader ID:", GLOBAL_CACHE.Party.GetPartyLeaderID()),
                ("Login Number:", login_number),
                ("Party Number:", party_number),
                ("AgentId By Login Number:", GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(login_number)),
                ("Is Hard Mode Unlocked:", GLOBAL_CACHE.Party.IsHardModeUnlocked()),
                ("Is Hard Mode:", GLOBAL_CACHE.Party.IsHardMode()),
                ("Is Normal More:", GLOBAL_CACHE.Party.IsNormalMode()),
                ("Party Size:", GLOBAL_CACHE.Party.GetPartySize()),
                ("Player Count:", GLOBAL_CACHE.Party.GetPlayerCount()),
                ("Hero Count:", GLOBAL_CACHE.Party.GetHeroCount()),
                ("Henchman Count:", GLOBAL_CACHE.Party.GetHenchmanCount()),
                ("Is Party Defeated:", GLOBAL_CACHE.Party.IsPartyDefeated()),
                ("Is Party Loaded:", GLOBAL_CACHE.Party.IsPartyLoaded()),
                ("Is Party Leader:", GLOBAL_CACHE.Party.IsPartyLeader()),
                ("Is all party ticked:", GLOBAL_CACHE.Party.IsAllTicked()),
                ("Is Player Ticked:", GLOBAL_CACHE.Party.IsPlayerTicked(party_number))
            ]

            ImGui.table("party info", headers, data)

            if PyImGui.button("Toggle Party Tick"):
                GLOBAL_CACHE.Party.ToggleTicked()

            if GLOBAL_CACHE.Party.IsPartyLeader():
                if GLOBAL_CACHE.Party.IsHardMode():
                    if PyImGui.button("Set Normal Mode"):
                        GLOBAL_CACHE.Party.SetNormalMode()
                else:
                    if PyImGui.button("Set Hard Mode"):
                        GLOBAL_CACHE.Party.SetHardMode()
            else:
                PyImGui.text("Only the party leader can change the party mode")

            PyImGui.separator()

            if PyImGui.collapsing_header("Players"):

                # Interactive Method: Kick Player
                PyParty_window_state.values[0] = PyImGui.input_int("Player ID to Kick", PyParty_window_state.values[0])

                if PyImGui.button("Invite Player"):
                    GLOBAL_CACHE.Party.Players.InvitePlayer(PyParty_window_state.values[0])

                if PyImGui.button("Kick Player"):
                    GLOBAL_CACHE.Party.Players.KickPlayer(PyParty_window_state.values[0])
                PyImGui.separator()
                PyImGui.text("Player Data")

                players = GLOBAL_CACHE.Party.GetPlayers()

                for player in players:
                    agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
                    headers = ["Player" + str(party_number)]
                    data = [
                        (f"Name: {GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(player.login_number)}"),
                        (f"Login Number (player_id): {player.login_number}"),
                        (f"Agent ID: {agent_id}"),
                        (f"Called Target ID: {player.called_target_id}"),
                        (f"Is Connected? {'Yes' if player.is_connected else 'No'}"),
                        (f"Is Ticked? {'Yes' if player.is_ticked else 'No'}")
                    ]

                    ImGui.table("player info"+ str(party_number), headers, data)
                    PyImGui.separator()

            if PyImGui.collapsing_header("Heroes"):
                PyParty_window_state.values[1] = PyImGui.input_int("Hero ID to handle", PyParty_window_state.values[1])
                PyParty_window_state.values[2] = PyImGui.input_text("Hero Name to handle", PyParty_window_state.values[2])
                
                hero = PyParty.Hero(PyParty_window_state.values[2])
                PyImGui.text(f"Hero ID:  {hero.GetID()}")

                if PyImGui.button("Add Hero By ID"):
                    GLOBAL_CACHE.Party.Heroes.AddHero(PyParty_window_state.values[1])

                if PyImGui.button("Kick Hero By ID"):
                    GLOBAL_CACHE.Party.Heroes.KickHero(PyParty_window_state.values[1])

                if PyImGui.button("Add Hero By Name"):
                    #GLOBAL_CACHE.Party.Heroes.AddHeroByName(PyParty_window_state.values[2])
                    Party.Heroes.AddHeroByName(PyParty_window_state.values[2])

                if PyImGui.button("Kick Hero By Name"):
                    GLOBAL_CACHE.Party.Heroes.KickHeroByName(PyParty_window_state.values[2])

                if PyImGui.button("Kick All Heroes"):
                    GLOBAL_CACHE.Party.Heroes.KickAllHeroes()

                PyParty_window_state.values[4] = PyImGui.input_float("Hero X Position", PyParty_window_state.values[4])
                PyParty_window_state.values[5] = PyImGui.input_float("Hero Y Position", PyParty_window_state.values[5])

                if PyImGui.button("Hero Use Skill #4"):
                    hero_agent_id = PyParty_window_state.values[1]
                    GLOBAL_CACHE.Party.Heroes.UseSkill(hero_agent_id, 4,hero_agent_id)
                if PyImGui.button("Flag Hero"):
                    GLOBAL_CACHE.Party.Heroes.FlagHero(PyParty_window_state.values[1], PyParty_window_state.values[4], PyParty_window_state.values[5])

                if PyImGui.button("Set Hero Behavior Fight"):
                    GLOBAL_CACHE.Party.Heroes.SetHeroBehavior(PyParty_window_state.values[1], 0)

                if PyImGui.button("Set Hero Behavior Guard"):
                    GLOBAL_CACHE.Party.Heroes.SetHeroBehavior(PyParty_window_state.values[1], 1)

                if PyImGui.button("Set Hero Behavior Avoid"):
                    GLOBAL_CACHE.Party.Heroes.SetHeroBehavior(PyParty_window_state.values[1], 2)

                PyImGui.separator()

                PyImGui.separator()

                PyImGui.separator()
                PyImGui.text("Hero Data")

                heroes = GLOBAL_CACHE.Party.GetHeroes()

                for hero in heroes:
                    hero_id = hero.hero_id.GetID()
                    agent_id = hero.agent_id

                    headers = ["Hero:" + str(hero_id)]
                    data = [
                        (f"Name: {GLOBAL_CACHE.Party.Heroes.GetHeroNameById(hero_id)}"),
                        (f"Hero ID: {hero_id}"),
                        (f"Agent ID: {hero.agent_id}"),
                        (f"Owner Player ID: {hero.owner_player_id}"),
                        (f"Level: {hero.level}"),
                        (f"Profession: {hero.primary.GetName()} / {hero.secondary.GetName()}")
                    ]

                    ImGui.table("hero info"+ str(hero_id), headers, data)
                    
                    PyImGui.separator()

            if PyImGui.collapsing_header("Henchmen"):
                PyParty_window_state.values[3] = PyImGui.input_int("Henchman ID to Handle", PyParty_window_state.values[3])

                if PyImGui.button("Add Henchman"):
                    GLOBAL_CACHE.Party.Henchmen.AddHenchman(PyParty_window_state.values[3])

                if PyImGui.button("Kick Henchman"):
                    GLOBAL_CACHE.Party.Henchmen.KickHenchman(PyParty_window_state.values[3])


                PyImGui.separator()

                PyImGui.text("Henchman Data")

                henchmen = GLOBAL_CACHE.Party.GetHenchmen()

                for henchman in henchmen:
                    agent_id = henchman.agent_id

                    headers = ["Henchman:" + str(agent_id)]
                    data = [
                        (f"Agent ID: {agent_id}"),
                        (f"Level: {henchman.level}"),
                        (f"Profession: {henchman.profession.GetName()}")
                    ]

                    ImGui.table("henchman info"+ str(agent_id), headers, data)
                    
                    PyImGui.separator()

            if PyImGui.collapsing_header("Pets"):
                PyImGui.text("Pet Data")

                lock_target_id = 0

                if PyImGui.button("Set Pet Behavior Fight"):
                    GLOBAL_CACHE.Party.Pets.SetPetBehavior(0,lock_target_id) #need an offensive target

                if PyImGui.button("Set Pet Behavior Guard"):
                    GLOBAL_CACHE.Party.Pets.SetPetBehavior(1,lock_target_id)

                if PyImGui.button("Set Pet Behavior Avoid"):
                    GLOBAL_CACHE.Party.Pets.SetPetBehavior(2,lock_target_id)

                pet = GLOBAL_CACHE.Party.Pets.GetPetInfo(GLOBAL_CACHE.Player.GetAgentID())

                headers = ["Pet"]
                data = [
                    (f"Agent ID: {pet.agent_id}"),
                    (f"Owner ID: {pet.owner_agent_id}"),
                    (f"Pet Name: {pet.pet_name}"),
                    (f"Model File ID1: {pet.model_file_id1}"),
                    (f"Model File ID2: {pet.model_file_id2}"),
                    (f"Behavior: {pet.behavior}"),
                    (f"Locked Target Id: {pet.locked_target_id}")
                ]

                ImGui.table("pet info", headers, data)
            

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPartyWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

PyPlayer_window_state.values = [0, 0, "", 0.0, 0.0, 0, 0, 0, 0, 0, 0]

def ShowPlayerWindow():
    global PyPlayer_window_state
    try: 
        width, height = 450,840
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Player"):

            description = "The player class is in charge of handling the player agent.\nIt provides methods to retrieve player data, like name, position, target, etc.\nIt has methods pertinent to the  controlled player and related to controlling game actions from the player perspective.\nThe Player itself is an agent, and as such, its data is retrieved from the Agent object."
            ImGui.DrawTextWithTitle("Player class", description)

            posx, posy = GLOBAL_CACHE.Player.GetXY()

            headers = ["Info", "Value"]
            data = [
                ("Agent ID:", GLOBAL_CACHE.Player.GetAgentID()),
                ("Name:", GLOBAL_CACHE.Player.GetName()),
                ("XY:", f"({posx:.2f}, {posy:.2f})"),
                ("Target ID:", GLOBAL_CACHE.Player.GetTargetID()),
                ("MouseOver ID:", GLOBAL_CACHE.Player.GetMouseOverID()),
                ("Observing ID:", GLOBAL_CACHE.Player.GetObservingID())
            ]

            ImGui.table("player info", headers, data)
            PyPlayer_window_state.values[0] = PyImGui.checkbox("Show agent data", PyPlayer_window_state.values[0])

            if PyPlayer_window_state.values[0]:
                draw_agent_window(GLOBAL_CACHE.Player.GetAgentID())

            PyImGui.separator()
            if PyImGui.collapsing_header("Player data"):
                headers = ["Info", "Value"]
                
                rank, rating, qualifier_points, wins, losses = GLOBAL_CACHE.Player.GetRankData()
                tournament_reward_points = GLOBAL_CACHE.Player.GetTournamentRewardPoints()
                morale = GLOBAL_CACHE.Player.GetMorale()
                experience = GLOBAL_CACHE.Player.GetExperience()
                current_skill_points, total_earned_skill_points = GLOBAL_CACHE.Player.GetSkillPointData()
                current_kurzick, total_earned_kurzick, max_kurzick = GLOBAL_CACHE.Player.GetKurzickData()
                current_luxon, total_earned_luxon, max_luxon = GLOBAL_CACHE.Player.GetLuxonData()
                current_imperial, total_earned_imperial, max_imperial = GLOBAL_CACHE.Player.GetImperialData()
                current_balthazar, total_earned_balthazar, max_balthazar = GLOBAL_CACHE.Player.GetBalthazarData()
                account_name = GLOBAL_CACHE.Player.GetAccountName()
                account_email = GLOBAL_CACHE.Player.GetAccountEmail()
                
                data = [
                    ("account_name:", account_name),
                    ("account_email:", account_email),
                    ("Rank:", rank),
                    ("Rating:", rating),
                    ("Qualifier Points:", qualifier_points),
                    ("Wins:", wins),
                    ("Losses:", losses),
                    ("Tournament Reward Points:", tournament_reward_points),
                    ("Morale:", morale),
                    ("Experience:", experience),
                    ("Current Skill Points:", current_skill_points),
                    ("Total Earned Skill Points:", total_earned_skill_points),
                    ("Current Kurzick:", current_kurzick),
                    ("Total Earned Kurzick:", total_earned_kurzick),
                    ("Max Kurzick:", max_kurzick),
                    ("Current Luxon:", current_luxon),
                    ("Total Earned Luxon:", total_earned_luxon),
                    ("Max Luxon:", max_luxon),
                    ("Current Imperial:", current_imperial),
                    ("Total Earned Imperial:", total_earned_imperial),
                    ("Max Imperial:", max_imperial),
                    ("Current Balthazar:", current_balthazar),
                    ("Total Earned Balthazar:", total_earned_balthazar),
                    ("Max Balthazar:", max_balthazar)
                ]
                ImGui.table("PlayerData info", headers, data)
                                
                if PyImGui.button("Deposit Faction"):
                    GLOBAL_CACHE.Player.DepositFaction(FactionAllegiance.Kurzick.value)
                    
            if PyImGui.collapsing_header("Titles"):
                current_title = GLOBAL_CACHE.Player.GetActiveTitleID()
                title_data = GLOBAL_CACHE.Player.GetTitle(current_title)
                
                headers = ["Info", "Value"]
                
                props = title_data.props
                current_points = title_data.current_points
                current_title_tier_index = title_data.current_title_tier_index
                points_needed_current_rank = title_data.points_needed_current_rank
                next_title_tier_index = title_data.next_title_tier_index
                points_needed_next_rank = title_data.points_needed_next_rank
                max_title_rank = title_data.max_title_rank
                max_title_tier_index = title_data.max_title_tier_index
                is_percentage_based = title_data.is_percentage_based
                has_tiers = title_data.has_tiers
                title_name = TITLE_NAME.get(TitleID(current_title), "Unknown")

                data = [
                    ("TitleID:", current_title),
                    ("Name:",title_name),
                    ("Properties:", props),
                    ("Current Points:", current_points),
                    ("Current Tier Index:", current_title_tier_index),
                    ("Points Needed for Current Rank:", points_needed_current_rank),
                    ("Next Tier Index:", next_title_tier_index),
                    ("Points Needed for Next Rank:", points_needed_next_rank),
                    ("Max Title Rank:", max_title_rank),
                    ("Max Tier Index:", max_title_tier_index),
                    ("Is Percentage Based:", is_percentage_based),
                    ("Has Tiers:", has_tiers)
                ]
                
                ImGui.table("Title info", headers, data)
                
                if PyImGui.button("remove Current Title"):
                    GLOBAL_CACHE.Player.RemoveActiveTitle()
                    
                if PyImGui.button("Set Norn Title"):
                    GLOBAL_CACHE.Player.SetActiveTitle(TitleID.Norn.value)
                
                
            if PyImGui.collapsing_header("Methods"):

                PyImGui.text("test fields")
                PyPlayer_window_state.values[1] = PyImGui.input_int("Number", PyPlayer_window_state.values[1])
                PyPlayer_window_state.values[2] = PyImGui.input_text("Text", PyPlayer_window_state.values[2])
                
                PyImGui.separator()

                if PyImGui.button("Send Dialog"):
                    hex_input = PyPlayer_window_state.values[2] #if the number is 0x84, the text must be 84
                    dialog_value = int(hex_input, 16)
                    #The values recieved by this function are in hex, so we need to convert them to int
                    #toolbox data shows Hex values, hex(0x84) = 0x84, int(0x84) = 132
                    #Player.SendDialog(0x84)
                    GLOBAL_CACHE.Player.SendDialog(dialog_value)

                if PyImGui.button("dialog take (SendChatCommand preferred method)"):
                    GLOBAL_CACHE.Player.SendChatCommand("dialog take")
                
                PyImGui.separator()
                if PyImGui.button("SendChat command"):
                    GLOBAL_CACHE.Player.SendChatCommand('target Adept Nai')

                if PyImGui.button("SendChat"):
                    GLOBAL_CACHE.Player.SendChat('#',PyPlayer_window_state.values[2])

                if PyImGui.button("Send Whisper"):
                    GLOBAL_CACHE.Player.SendWhisper(PyPlayer_window_state.values[2],"Hello")

                PyImGui.separator()

                if PyImGui.button("change target"):
                    GLOBAL_CACHE.Player.ChangeTarget(PyPlayer_window_state.values[1])

                if PyImGui.button("Interact"):
                    GLOBAL_CACHE.Player.Interact(PyPlayer_window_state.values[1], call_target=False)

                PyImGui.text("Note: it it preferred to disable key use from toolbox")

                PyPlayer_window_state.values[3] = PyImGui.input_float("X", PyPlayer_window_state.values[3])
                PyPlayer_window_state.values[4] = PyImGui.input_float("Y", PyPlayer_window_state.values[4])

                if PyImGui.button("Move"):
                    x = PyPlayer_window_state.values[3]
                    y = PyPlayer_window_state.values[4]
                    GLOBAL_CACHE.Player.Move(x, y)

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPlayerWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def ShowAgentArrayWindow():
    global PyAgent_agent_window_state
    try: 
        width, height = 800,760
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"AgenArray"):

            description = """AgentArray is a class dedicated to manipulating arrays.
            Why is that? 
                The core of combat functionality for any bot requires analysis of the game state, 
                and the game state is represented by agents and their properties. 
                
                This class provides a way to manipulate, sort, and filter agents in a way that is useful for combat analysis.

            In Guild Wars, agents are entities such as players, NPCs, items, gadgets, etc.
            Agent arrays are collections of agents.
            Guild Wars originally handles only one unfiltered agent array. 
            Py4GW provides not only that array but also a set of pre-filtered agent arrays categorized by agent type.

                *-AgentArray (Unfiltered original GW agent Array)
                *-AllyArray (Allegiance Ally, players, heroes, henchman, includes yourself)
                *-NeutralArray (Allegiance Neutral, i.e., animals, etc.)
                *-EnemyArray (Allegiance Enemy, foes)
                *-SpiritPetArray (spirits and pets are the same in GWCA)
                *-MinionArray (spawned creatures)
                *-NPCMinipetArray (non-player characters and minipets)
                *-ItemArray (agents of item type)
                *-GadgetArray (signposts, chests, trebuchets, etc.)

            AgentArray class provides Methods to Filter, Sort, Manipulate, and Retrieve Agents from the game state.

            Refer to the class documentation to see how to use the AgentArray class
            """
            ImGui.DrawTextWithTitle("AgentArray class", description,35)   

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowAgentArrayWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def ShowGadgetAgentData(agent_id):
    global PyAgent_agent_window_state
    try: 
        width, height = 750,800
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"AgentGadget: {agent_id}"):

            if agent_id != 0:
                description = "here you can see all the item agent data available"
                ImGui.DrawTextWithTitle("Agentgadget " + str(agent_id), description,3)

                PyImGui.text("Agent Item Data:")

                # Assume the gadget item data has been retrieved from Agent.GetGadgetItem
                gadget_data = GLOBAL_CACHE.Agent.GetGadgetAgent(agent_id)

                # Prepare the data, converting uint32_t fields to decimal, hex, and binary
                headers = ["Info", "Value"]
                data = [
                    ("Agent ID:", gadget_data.agent_id),
                    ("Gadget ID:", gadget_data.gadget_id),
                    ("Extra Type:", gadget_data.extra_type),
                    ("h00C4 (decimal):", gadget_data.h00C4),
                    ("h00C4 (hex):", hex(gadget_data.h00C4)),
                    ("h00C4 (binary):", bin(gadget_data.h00C4)),
                    ("h00C8 (decimal):", gadget_data.h00C8),
                    ("h00C8 (hex):", hex(gadget_data.h00C8)),
                    ("h00C8 (binary):", bin(gadget_data.h00C8)),
                ]

                # Handle h00D4 vector (which is a list of uint32_t values)
                # Append each element from h00D4 with its different representations
                for i, h00D4_val in enumerate(gadget_data.h00D4):
                    data.append((f"h00D4[{i}] (decimal):", h00D4_val))
                    data.append((f"h00D4[{i}] (hex):", hex(h00D4_val)))
                    data.append((f"h00D4[{i}] (binary):", bin(h00D4_val)))

                # Display the table using the provided table function
                ImGui.table("gadget item info", headers, data)

                

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowItemAgentData: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


def ShowItemAgentData(agent_id):
    global PyAgent_agent_window_state
    try: 
        width, height = 750,800
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"AgentItem: {agent_id}"):

            if agent_id != 0:
                description = "here you can see all the item agent data available"
                ImGui.DrawTextWithTitle("AgentItem " + str(agent_id), description,3)

                PyImGui.text("Agent Item Data:")

                item_data = GLOBAL_CACHE.Agent.GetItemAgent(agent_id)

                headers = ["Info", "Value"]
                data = [
                    ("Agent ID:", item_data.agent_id),
                    ("Owner ID:", item_data.owner_id),
                    ("Item ID:", item_data.item_id),
                    ("h00CC (decimal):", item_data.h00CC),
                    ("h00CC (hex):", hex(item_data.h00CC)),
                    ("h00CC (binary):", bin(item_data.h00CC)),
                    ("ExtraType (decimal):", item_data.extra_type),
                    ("ExtraType (hex):", hex(item_data.extra_type)),
                    ("ExtraType (binary):", bin(item_data.extra_type))
                ]

                ImGui.table("agent common info",headers,data)
                

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowItemAgentData: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


def ShowLivingAgentData(agent_id):
    global PyAgent_agent_window_state
    try: 
        width, height = 750,800
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"AgentLiving: {agent_id}"):

            if agent_id != 0:
                description = "here you can see all the living agent data available"
                ImGui.DrawTextWithTitle("AgentLiving " + str(agent_id), description,3)

                PyImGui.text("Agent Living Data:")

                pprof_id, sprof_id = GLOBAL_CACHE.Agent.GetProfessionIDs(agent_id)
                pprof_name, sprof_name = GLOBAL_CACHE.Agent.GetProfessionNames(agent_id)
                pprof_short, sprof_short = GLOBAL_CACHE.Agent.GetProfessionShortNames(agent_id)

                profs_id = f"{pprof_id}/{sprof_id}"
                profs_name = f"{pprof_name}/{sprof_name}"
                profs_short = f"{pprof_short}/{sprof_short}"

                alliegance_id, alliegance_name = GLOBAL_CACHE.Agent.GetAllegiance(agent_id)
                alliegance = f"{alliegance_id}/{alliegance_name}"
                
                #GLOBAL_CACHE.Agent.RequestName(agent_id)

                # Combine info and value into a single string
                combined_data = [
                    f"Agent ID: {agent_id}",
                    f"Owner Id: {GLOBAL_CACHE.Agent.GetOwnerID(agent_id)}",
                    f"Player Number: {GLOBAL_CACHE.Agent.GetPlayerNumber(agent_id)}",
                    f"Login Number: {GLOBAL_CACHE.Agent.GetLoginNumber(agent_id)}",
                    f"Professions ID: {profs_id}",
                    f"Professions Name: {profs_name}",
                    f"Professions ShortName: {profs_short}",
                    f"Level: {GLOBAL_CACHE.Agent.GetLevel(agent_id)}",
                    f"Energy: {GLOBAL_CACHE.Agent.GetEnergy(agent_id):.2f}",
                    f"Max Energy: {GLOBAL_CACHE.Agent.GetMaxEnergy(agent_id)}",
                    f"Energy Regen: {GLOBAL_CACHE.Agent.GetEnergyRegen(agent_id):.2f}",
                    f"Health: {GLOBAL_CACHE.Agent.GetHealth(agent_id):.2f}",
                    f"Max Health: {GLOBAL_CACHE.Agent.GetMaxHealth(agent_id)}",
                    f"Health Regen: {GLOBAL_CACHE.Agent.GetHealthRegen(agent_id):.2f}",
                    f"Name: {GLOBAL_CACHE.Agent.GetName(agent_id)}",
                    f"Strike Dagger Status: {GLOBAL_CACHE.Agent.GetDaggerStatus(agent_id)}",
                    f"Alliegance: {alliegance}"
                ]

                # Format data into rows of 3 columns
                formatted_data = []
                for i in range(0, len(combined_data), 3):
                    row = combined_data[i:i + 3]
                    # Pad the row with empty strings if it has less than 3 items
                    while len(row) < 3:
                        row.append("")
                    formatted_data.append(tuple(row))  # Convert the row to a tuple

                # Define headers for the 3-column table
                headers = ["Data 1", "Data 2", "Data 3"]

                # Call the table function to display the data
                ImGui.table("Agent Positional Common Info", headers, formatted_data)

                PyImGui.text("Weapon Data:")

                weapon_id, weapon_name = GLOBAL_CACHE.Agent.GetWeaponType(agent_id)
                weapon = f"{weapon_id}/{weapon_name}"
                PyImGui.text(f"Weapon Type: {weapon}")
                weapon_item_id, weapon_item_type, offhand_item_id, offhand_item_type = GLOBAL_CACHE.Agent.GetWeaponExtraData(agent_id)

                headers = ["Info", "Value"]
                data = [(f"Weapon Item ID: {weapon_item_id}",f"Weapon Item Type: {weapon_item_type}"),
                        (f"Offhand Item ID: {offhand_item_id}",f"Offhand Item Type: {offhand_item_type}")]

                ImGui.table("weapon data",headers,data)

                PyImGui.text("Pve properties:")
                PyImGui.text("State:")

                headers = ["IsPlayer", "IsNpc"]
                data = [(f"{GLOBAL_CACHE.Agent.IsPlayer(agent_id)}",f"{GLOBAL_CACHE.Agent.IsNPC(agent_id)}"),
                        (f"IsDead: {GLOBAL_CACHE.Agent.IsDead(agent_id)}",f"IsAlive: {GLOBAL_CACHE.Agent.IsAlive(agent_id)}")]
                ImGui.table("Agent state", headers, data)  

                PyImGui.text("Model State:")
                combined_data = [
                    f"IsMoving: {GLOBAL_CACHE.Agent.IsMoving(agent_id)}",
                    f"IsAttacking: {GLOBAL_CACHE.Agent.IsAttacking(agent_id)}",
                    f"IsCasting: {GLOBAL_CACHE.Agent.IsCasting(agent_id)}",
                    f"IsIdle: {GLOBAL_CACHE.Agent.IsIdle(agent_id)}",
                    f"IsKnockedDown: {GLOBAL_CACHE.Agent.IsKnockedDown(agent_id)}"  
                ]

                # Format data into rows of 3 columns
                columns = 3
                formatted_data = []
                for i in range(0, len(combined_data), columns):
                    row = combined_data[i:i + columns]
                    # Pad the row with empty strings if it has less than 3 items
                    while len(row) < columns:
                        row.append("")
                    formatted_data.append(tuple(row))  # Convert the row to a tuple

                # Define headers for the 3-column table
                headers = ["Data 1", "Data 2", "Data 3"]

                # Call the table function to display the data
                ImGui.table("agent living pve Info", headers, formatted_data)

                PyImGui.text("Agent TypeMap Bitmasks:")
                combined_data = [
                    f"InCombatStance: {GLOBAL_CACHE.Agent.IsInCombatStance(agent_id)}",
                    f"HasQuest: {GLOBAL_CACHE.Agent.HasQuest(agent_id)}",
                    f"IsDeadByTypeMap: {GLOBAL_CACHE.Agent.IsDeadByTypeMap(agent_id)}",
                    f"IsFemale: {GLOBAL_CACHE.Agent.IsFemale(agent_id)}",
                    f"HasBossGlow: {GLOBAL_CACHE.Agent.HasBossGlow(agent_id)}",
                    f"IsHidingCape: {GLOBAL_CACHE.Agent.IsHidingCape(agent_id)}",
                    f"CanBeViewedInPartyWindow: {GLOBAL_CACHE.Agent.CanBeViewedInPartyWindow(agent_id)}",
                    f"IsSpawned: {GLOBAL_CACHE.Agent.IsSpawned(agent_id)}",
                    f"IsBeingObserved: {GLOBAL_CACHE.Agent.IsBeingObserved(agent_id)}"
                ]

                # Format data into rows of 3 columns
                columns = 3
                formatted_data = []
                for i in range(0, len(combined_data), columns):
                    row = combined_data[i:i + columns]
                    # Pad the row with empty strings if it has less than 3 items
                    while len(row) < columns:
                        row.append("")
                    formatted_data.append(tuple(row))  # Convert the row to a tuple

                # Define headers for the 3-column table
                headers = ["Data 1", "Data 2", "Data 3"]

                # Call the table function to display the data
                ImGui.table("agent living pve Info", headers, formatted_data)

                PyImGui.text("Agent Combat Info:")
                combined_data = [
                    f"IsConditioned: {GLOBAL_CACHE.Agent.IsConditioned(agent_id)}",
                    f"IsBleeding: {GLOBAL_CACHE.Agent.IsBleeding(agent_id)}",
                    f"IsCrippled: {GLOBAL_CACHE.Agent.IsCrippled(agent_id)}",
                    f"IsDeepWounded: {GLOBAL_CACHE.Agent.IsDeepWounded(agent_id)}",
                    f"isPoisoned: {GLOBAL_CACHE.Agent.IsPoisoned(agent_id)}",
                    f"IsEnchanted: {GLOBAL_CACHE.Agent.IsEnchanted(agent_id)}",
                    f"IsHexed: {GLOBAL_CACHE.Agent.IsHexed(agent_id)}",
                    f"IsdegenHexed: {GLOBAL_CACHE.Agent.IsDegenHexed(agent_id)}",
                    f"IsWeaponSpelled: {GLOBAL_CACHE.Agent.IsWeaponSpelled(agent_id)}",
                    f"CastingSkillId: {GLOBAL_CACHE.Agent.GetCastingSkill(agent_id)}",
                    f"Overcast: {GLOBAL_CACHE.Agent.GetOvercast(agent_id)}"
                ]

                # Format data into rows of 3 columns
                columns = 3
                formatted_data = []
                for i in range(0, len(combined_data), columns):
                    row = combined_data[i:i + columns]
                    # Pad the row with empty strings if it has less than 3 items
                    while len(row) < columns:
                        row.append("")
                    formatted_data.append(tuple(row))  # Convert the row to a tuple

                # Define headers for the 3-column table
                headers = ["Data 1", "Data 2", "Data 3"]

                # Call the table function to display the data
                ImGui.table("agent living pve Info", headers, formatted_data)
                
                AGENT_INSTANCE = Agent.agent_instance(agent_id).living_agent
                
                PyImGui.text("Extra data:")
                combined_data = []
                """
                    f"h00C8: {AGENT_INSTANCE.h00C8}",
                    f"h00CC: {AGENT_INSTANCE.h00CC}",
                    f"h00D0: {AGENT_INSTANCE.h00D0}",
                    f"h00D4: {AGENT_INSTANCE.h00D4}",
                    f"animation_type: {AGENT_INSTANCE.animation_type}",
                    f"h00E4: {AGENT_INSTANCE.h00E4}",
                    f"weapon_attack_speed: {AGENT_INSTANCE.weapon_attack_speed}",
                    f"attack_speed_modifier: {AGENT_INSTANCE.attack_speed_modifier}",
                    f"agent_model_type: {AGENT_INSTANCE.agent_model_type}",
                    f"transmog_npc_id: {AGENT_INSTANCE.transmog_npc_id}",
                    f"h0100: {AGENT_INSTANCE.h0100}",
                    f"guild_id: {AGENT_INSTANCE.guild_id}",
                    f"team_id: {AGENT_INSTANCE.team_id}",
                    f"h0108: {AGENT_INSTANCE.h0108}",
                    f"h0110: {AGENT_INSTANCE.h0110}",
                    f"h0124: {AGENT_INSTANCE.h0124}",
                    f"h012C: {AGENT_INSTANCE.h012C}",
                    f"effects: {AGENT_INSTANCE.effects}",
                    f"h013C: {AGENT_INSTANCE.h013C}",
                    f"model_state: {AGENT_INSTANCE.model_state}",
                    f"type_map: {AGENT_INSTANCE.type_map}",
                    f"h017C: {AGENT_INSTANCE.h017C}",
                    f"animation_speed: {AGENT_INSTANCE.animation_speed}",
                    f"animation_code: {AGENT_INSTANCE.animation_code}",
                    f"animation_id: {AGENT_INSTANCE.animation_id}",
                    f"h01B6: {AGENT_INSTANCE.h01B6}",
                ]
                """

                # Format data into rows of 3 columns
                columns = 5
                formatted_data = []
                for i in range(0, len(combined_data), columns):
                    row = combined_data[i:i + columns]
                    # Pad the row with empty strings if it has less than 3 items
                    while len(row) < columns:
                        row.append("")
                    formatted_data.append(tuple(row))  # Convert the row to a tuple

                # Define headers for the 3-column table
                headers = ["Data 1", "Data 2", "Data 3", "Data 4", "Data 5"]

                # Call the table function to display the data
                ImGui.table("agent living extra pve Info", headers, formatted_data)

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowLivingAgentData: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


PyAgent_agent_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
def draw_agent_window(agent_id):
    global PyAgent_agent_window_state
    try: 
        width, height = 450,700
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(f"Agent: {agent_id}"):

            if agent_id != 0:
                description = "in GWCA not all agents are trated equally, theres data that is not availble for some agent types, like enemies, in most cases youll have acces to all your private data and your own heroes, all the remaining agents have a limited set of data to query from"
                ImGui.DrawTextWithTitle("Agent " + str(agent_id), description,5)

                PyImGui.text("Agent common Data:")
   
                headers = ["Info", "Value"]
                data = [("Agent ID:", agent_id),
                        ("Is LivingAgent:", GLOBAL_CACHE.Agent.IsLiving(agent_id)),
                        ("Is ItemAgent:", GLOBAL_CACHE.Agent.IsItem(agent_id)),
                        ("Is GadgetAgent:", GLOBAL_CACHE.Agent.IsGadget(agent_id))]

                ImGui.table("agent common info",headers,data)

                PyImGui.text("Positional Data:")

                agent_x, agent_y, agent_z = GLOBAL_CACHE.Agent.GetXYZ(agent_id)
                pos_str = f"({agent_x:.2f}, {agent_y:.2f}, {agent_z:.2f})"

                vel_x, vel_y = GLOBAL_CACHE.Agent.GetVelocityXY(agent_id)
                vel_str = f"({vel_x:.2f}, {vel_y:.2f})"

                headers = ["Info", "Value"]
                data = [("(X,Y,Z):", pos_str),
                        ("zplane:", GLOBAL_CACHE.Agent.IsLiving(agent_id)),
                        ("Rotation Angle:", GLOBAL_CACHE.Agent.GetRotationAngle(agent_id)),
                        ("Rotation cosine:", GLOBAL_CACHE.Agent.GetRotationCos(agent_id)),
                        ("Rotation sine:", GLOBAL_CACHE.Agent.GetRotationSin(agent_id)),
                        ("Velocity (X,Y):", vel_str)]

                ImGui.table("agent positional common info",headers,data)

                PyImGui.separator()

                PyImGui.text("Attributes:")

                attributes = GLOBAL_CACHE.Agent.GetAttributes(agent_id)

                headers = ["Attribute", "Base Level", "Level"]
                data = []
                for attribute in attributes:
                    data.append((attribute.GetName(), str(attribute.level_base), str(attribute.level)))

                ImGui.table("Attributes Info", headers, data)

                PyImGui.text("Show Agent type Specific data")

                if GLOBAL_CACHE.Agent.IsLiving(agent_id):
                    PyAgent_agent_window_state.values[0] = ImGui.toggle_button("Show Living Agent Data", PyAgent_agent_window_state.values[0])

                if GLOBAL_CACHE.Agent.IsItem(agent_id):
                    PyAgent_agent_window_state.values[1] = ImGui.toggle_button("Show Item Agent Data", PyAgent_agent_window_state.values[1])

                if GLOBAL_CACHE.Agent.IsGadget(agent_id):
                    PyAgent_agent_window_state.values[2] = ImGui.toggle_button("Show Gadget Agent Data", PyAgent_agent_window_state.values[2])


                if PyAgent_agent_window_state.values[0]:
                    ShowLivingAgentData(agent_id)

                if PyAgent_agent_window_state.values[1]:
                    ShowItemAgentData(agent_id)

                if PyAgent_agent_window_state.values[2]:
                    ShowGadgetAgentData(agent_id)

 

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in draw_agent_window: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


#PyAgent Demo Section
PyAgent_window_state.window_name = "PyAgent DEMO"
PyAgent_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def ShowPyAgentWindow():
    global module_name
    global PyAgent_window_state
    description = "This section demonstrates the use of PyAgent functions in Py4GW. \nPyAgent provides access to in-game entities (agents) such as players, NPCs, gadgets, and items. \nIn this demo, you can see how to create and use PyAgent objects to interact with agents in the game."

    try:     
        width, height = 375,525
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(PyAgent_window_state.window_name):
            # Show description text
            ImGui.DrawTextWithTitle(PyAgent_window_state.window_name, description)

            if not GLOBAL_CACHE.Map.IsMapReady():
                    PyImGui.text_colored("Travel : Map is not ready",(1, 0, 0, 1))

            if GLOBAL_CACHE.Map.IsMapReady():
                # Fetch nearest entities
                player_x, player_y = GLOBAL_CACHE.Player.GetXY()
                player_id = GLOBAL_CACHE.Player.GetAgentID()
                
                enemy_array = GLOBAL_CACHE.AgentArray.GetEnemyArray()
                enemy_array = AgentArray.Sort.ByDistance(enemy_array, (player_x,player_y))
                closest_enemy = next(iter(enemy_array), 0)

                ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
                ally_array = AgentArray.Manipulation.Subtract(ally_array, [player_id]) #remove player_id from ally array
                ally_array = AgentArray.Sort.ByDistance(ally_array, (player_x,player_y))
                closest_ally = next(iter(ally_array), 0)

                item_array = GLOBAL_CACHE.AgentArray.GetItemArray()
                item_array = AgentArray.Sort.ByDistance(item_array, (player_x,player_y))
                closest_item = next(iter(item_array), 0)
                
                gadget_array = GLOBAL_CACHE.AgentArray.GetGadgetArray()
                gadget_array = AgentArray.Sort.ByDistance(gadget_array, (player_x,player_y))
                closest_gadget = next(iter(gadget_array), 0)

                npc_array = GLOBAL_CACHE.AgentArray.GetNPCMinipetArray()
                npc_array = AgentArray.Sort.ByDistance(npc_array, (player_x,player_y))
                closest_npc = next(iter(npc_array), 0)

                player_target = GLOBAL_CACHE.Player.GetTargetID()

                # Display table headers
                PyImGui.text("Nearest Entities:")
                
                merchant_id = GLOBAL_CACHE.Agent.GetAgentIDByName("[Merchant]")
                
                headers = ["Info", "Value"]
                data = [("Enemy:", closest_enemy),
                        ("Ally:", closest_ally),
                        ("Item:", closest_item),
                        ("Gadget:", closest_gadget),
                        ("NPC/Minipet:", closest_npc),
                        ("Player AgentID:", player_id),
                        ("TargetID",player_target),
                        ("Merchant ID:", merchant_id)]

                ImGui.table("Nearest info Table",headers,data)


            # Input field for Agent ID
            PyImGui.text("Input an Agent Id to see its data")
            PyAgent_window_state.values[0] = PyImGui.input_int("Agent ID", PyAgent_window_state.values[0])
            PyImGui.separator()
            PyAgent_window_state.values[1] = ImGui.toggle_button("AgentArray", PyAgent_window_state.values[1])
            # If an agent ID is entered, display agent details
            if PyAgent_window_state.values[0] != 0:
                draw_agent_window(PyAgent_window_state.values[0])

            if PyAgent_window_state.values[1] != 0:
                ShowAgentArrayWindow()

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPyAgentWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


PyMap_Extra_InfoWindow_state.window_name = "PyMap Extra Info DEMO"
pathing_map = None

def ShowPyImGuiExtraMaplWindow():
    global module_name
    global PyMap_Extra_InfoWindow_state,pathing_map
    description = "This section demonstrates the use of extra map information in PyMap. \nExtra map information includes region types, instance types, and map context. \nIn this demo, you can see how to create and use PyMap objects to interact with the map in the game."

    try:
        width, height = 375,400
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(PyMap_Extra_InfoWindow_state.window_name, PyImGui.WindowFlags.NoResize):
            #ImGui.DrawTextWithTitle(PyMap_Extra_InfoWindow_state.window_name, description)

            map_instance = GLOBAL_CACHE.Map._map_instance
            map_instance.GetContext()

            if not GLOBAL_CACHE.Map.IsOutpost():
                PyImGui.text("Get to an Outpost to see this data")
                PyImGui.separator()
    
            if GLOBAL_CACHE.Map.IsOutpost():

                headers = ["Info", "Value"]
                data = [("Campaign:", GLOBAL_CACHE.Map.GetCampaign()[1]),
                        ("Continent:", GLOBAL_CACHE.Map.GetContinent()[1]),
                        ("Region:", f"{GLOBAL_CACHE.Map.GetRegion()[1]} ({GLOBAL_CACHE.Map.GetRegion()[0]})"),
                        ("District:", GLOBAL_CACHE.Map.GetDistrict()),
                        ("Language:", GLOBAL_CACHE.Map.GetLanguage()[1])]

                ImGui.table("Instance Info Table",headers,data)

                PyImGui.separator()

                PyImGui.text("Outpost Specific Information")
                if PyImGui.begin_table("OutpostInfoTable", 2, PyImGui.TableFlags.Borders):
                    PyImGui.table_next_row()

                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("Has Enter Button?")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text(f"{'Yes' if GLOBAL_CACHE.Map.HasEnterChallengeButton() else 'No'}")

                    PyImGui.end_table()

                    if not map_instance.has_enter_button:
                        PyImGui.text("Get to an outpost with Enter Button to see this data")


                    if map_instance.has_enter_button:
                        if PyImGui.begin_table("OutpostEnterMissionTable", 2, PyImGui.TableFlags.Borders):
                            PyImGui.table_next_row()
                            PyImGui.table_set_column_index(0)
                            if PyImGui.button("Enter Mission"):
                                GLOBAL_CACHE.Map.EnterChallenge()

                            PyImGui.table_set_column_index(1)
                            if PyImGui.button("Cancel Enter"):
                               GLOBAL_CACHE.Map.CancelEnterChallenge()
                    
                            PyImGui.end_table()

                PyImGui.separator()

            # Explorable Specific Fields
            if not GLOBAL_CACHE.Map.IsExplorable():
                PyImGui.text("Get to an Explorable Zone to see this data")
                PyImGui.separator()

            if GLOBAL_CACHE.Map.IsExplorable():
                PyImGui.text("Explorable Zone Specific Information")
           
                if PyImGui.begin_table("ExplorableNormalTable", 2, PyImGui.TableFlags.Borders):
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("Is Vanquishable?")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text(f"{'Yes' if map_instance.is_vanquishable_area else 'No'}")

                    PyImGui.end_table()
                if not GLOBAL_CACHE.Party.IsHardMode():
                    PyImGui.text("Enter Hard mode to see this data")

                if GLOBAL_CACHE.Party.IsHardMode():
                    PyImGui.separator()

                    headers = ["Foes Killed", "Foes To Kill"]
                    data = [(map_instance.foes_killed, map_instance.foes_to_kill)]

                    ImGui.table("Vanquish Info Table",headers,data)

        PyImGui.end()

    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPyImGuiExtraMaplWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

PyMap_Travel_Window_state.window_name = "PyMap Travel DEMO"

def ShowPyImGuiTravelWindow():
    global module_name
    global PyMap_Travel_Window_state
    description = "This section demonstrates the use of travel functions in PyMap. \nTravel functions allow you to move between different locations in the game. \nIn this demo, you can see how to use travel functions to move to different districts and outposts."

    try:
        width, height = 375,360
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(PyMap_Travel_Window_state.window_name, PyImGui.WindowFlags.NoResize):
            ImGui.DrawTextWithTitle(PyMap_Travel_Window_state.window_name, description,8)

            if not GLOBAL_CACHE.Map.IsMapReady():
                    PyImGui.text_colored("Travel : Map is not ready",(1, 0, 0, 1))
               
            if GLOBAL_CACHE.Map.IsMapReady():

                PyImGui.text("Travel to default district")
                if PyImGui.button(GLOBAL_CACHE.Map.GetMapName(857)): #Embark Beach
                    GLOBAL_CACHE.Map.Travel(857)

                PyImGui.text("Travel to specific district")
                if PyImGui.button(GLOBAL_CACHE.Map.GetMapName(248)): #Great Temple of Balthazar
                    GLOBAL_CACHE.Map.TravelToDistrict(248, 0, 0)

                PyImGui.text("Travel trough toolbox chat command")
                if PyImGui.button("Eye Of The North"):
                    GLOBAL_CACHE.Player.SendChatCommand("tp eotn")

        PyImGui.end()

    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPyImGuiTravelWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


#PyMap Demo Section
PyMap_window_state.window_name = "PyMap DEMO"
PyMap_window_state.button_list = ["Travel", "Extra Info"]
PyMap_window_state.is_window_open = [False, False]

def ShowPyMapWindow():
    global module_name
    global PyMap_window_state
    description = "This section demonstrates the use of PyMap functions in Py4GW. \nPyMap provides access to map-related data such as region types, instance types, and map context. \nIn this demo, you can see how to create and use PyMap objects to interact with the map in the game."

    try:
        width, height = 375,490
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(PyMap_window_state.window_name, PyImGui.WindowFlags.NoResize):
            ImGui.DrawTextWithTitle(PyMap_window_state.window_name, description,8)

            map_instance = GLOBAL_CACHE.Map._map_instance

            # Instance Fields (General map data)
            PyImGui.text("Instance Information")


            instance_time = GLOBAL_CACHE.Map.GetInstanceUptime()
            instance_time_seconds = instance_time / 1000  # Convert to seconds
            formatted_time = time.strftime('%H:%M:%S', time.gmtime(instance_time_seconds))
            time_text = f"{formatted_time} - [{map_instance.instance_time}]"

            headers = ["Info", "Value"]
            data = [("Instance ID:", GLOBAL_CACHE.Map.GetMapID()),
                    ("Instance Name:", GLOBAL_CACHE.Map.GetMapName()),
                    ("Instance Time:", time_text),
                    ("Amount of Players in Instance:",GLOBAL_CACHE.Map.GetAmountOfPlayersInInstance())]

            ImGui.table("Instance Info Table",headers,data)

            PyImGui.separator()

            headers = ["Info", "Value"]
            data = [("Outpost:", GLOBAL_CACHE.Map.IsOutpost()),
                    ("Explorable:", GLOBAL_CACHE.Map.IsExplorable()),
                    ("Loading:", GLOBAL_CACHE.Map.IsMapLoading()),
                    ("Ready:", GLOBAL_CACHE.Map.IsMapReady())]

            ImGui.table("Map Status Info Table",headers,data)

            PyImGui.separator()

             # Calculate dynamic grid layout based on number of buttons
            total_buttons = len(PyMap_window_state.button_list)
            columns, rows = calculate_grid_layout(total_buttons)

            # Create a table with dynamically calculated columns
            if PyImGui.begin_table("ImGuiButtonTable", columns):  # Dynamic number of columns
                for button_index, button_label in enumerate(PyMap_window_state.button_list):
                    PyImGui.table_next_column()  # Move to the next column

                    selected_button_index = button_index
                    PyMap_window_state.is_window_open[selected_button_index] = ImGui.toggle_button(button_label, PyMap_window_state.is_window_open[selected_button_index])
                    
                    if PyMap_window_state.is_window_open[selected_button_index]:
                        title = PyMap_window_state.button_list[selected_button_index]

                
                PyImGui.end_table()  # End the table
                
            PyImGui.separator()  # Separator between sections

            
            if PyMap_window_state.is_window_open[0]:
                ShowPyImGuiTravelWindow()

            if PyMap_window_state.is_window_open[1]:
                ShowPyImGuiExtraMaplWindow()

            


        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in ShowPyMapWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

                    

#ImGgui DEMO Section
ImGui_misc_window_state.window_name = "PyImGui Miscelaneous DEMO"
ImGui_misc_window_state.values = [
        [0.0, 0.0, 0.0],  # RGB placeholder (3 floats)
        [0.0, 0.0, 0.0, 1.0],  # RGBA placeholder (4 floats)
        0.0  # Progress bar value
    ]

def ShowPyImGuiMiscelaneousWindow():
    global module_name
    global ImGui_misc_window_state
    description = "This section demonstrates the use of miscellaneous functions in PyImGui. \nThese functions include color pickers, progress bars, and tooltips. \nIn this demo, you can see how to create and use these functions in your interface."

    try:  
        width, height = 350,375
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(ImGui_misc_window_state.window_name,PyImGui.WindowFlags.NoResize):

            ImGui.DrawTextWithTitle(ImGui_misc_window_state.window_name, description,8)

            # Color Picker for RGB values
            ImGui_misc_window_state.values[0] = PyImGui.color_edit3("RGB Color Picker", ImGui_misc_window_state.values[0])
            PyImGui.text(f"RGB Color: {ImGui_misc_window_state.values[0]}")
            PyImGui.separator()
            
            # Color Picker for RGBA values
            ImGui_misc_window_state.values[1] = PyImGui.color_edit4("RGBA Color Picker", ImGui_misc_window_state.values[1])
            PyImGui.text(f"RGBA Color: {ImGui_misc_window_state.values[1]}")
            PyImGui.separator()

            # Progress Bar
            ImGui_misc_window_state.values[2] += 0.01  # Increment the progress by a small amount
            if ImGui_misc_window_state.values[2] > 1.0:  # If progress exceeds 1.0 (100%), reset to 0.0
                ImGui_misc_window_state.values[2] = 0.0
            PyImGui.progress_bar(ImGui_misc_window_state.values[2], 100.0, "Progress Bar") 

            # Tooltip
            PyImGui.text("Hover over the button to see a tooltip:")
            PyImGui.same_line(0.0, -1.0)
            
            if PyImGui.button("Hover Me!"):
                Py4GW.Console.Log(module_name,"Button clicked!")
            PyImGui.show_tooltip("This is a tooltip for the button.")

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPyImGuiMiscelaneousWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

ImGui_tables_window_state.window_name = "PyImGui Tables DEMO"
ImGui_tables_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def ShowPyImGuiTablesWindow():
    global module_name
    global ImGui_tables_window_state
    description = "This section demonstrates the use of tables in PyImGui. \nTables allow users to display and interact with data in a structured format. \nIn this demo, you can see how to create and use tables in your interface. Tables can be customized with different columns, headers, and rows, can be sorted, and can contain various data types."

    try:   
       width, height = 600,430
       PyImGui.set_next_window_size(width, height)
       if PyImGui.begin(ImGui_tables_window_state.window_name,PyImGui.WindowFlags.NoResize):

            ImGui.DrawTextWithTitle(ImGui_tables_window_state.window_name, description,8)

            # Table with 3 columns and 5 rows
            if PyImGui.begin_table("Table1", 3):
                PyImGui.table_setup_column("Column 1", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 2", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 3", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_headers_row()
                for row in range(5):
                    PyImGui.table_next_row()
                    for column in range(3):
                        PyImGui.table_set_column_index(column)
                        PyImGui.text(f"Row {row}, Column {column}")
                PyImGui.end_table()

            PyImGui.separator()

            # Table with 5 columns and 3 rows
            if PyImGui.begin_table("Table2", 5):
                PyImGui.table_setup_column("Column 1", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 2", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 3", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 4", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 5", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_headers_row()
                for row in range(3):
                    PyImGui.table_next_row()
                    for column in range(5):
                        PyImGui.table_set_column_index(column)
                        PyImGui.text(f"Row {row}, Column {column}")
                PyImGui.end_table()


       PyImGui.end()

    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPyImGuiTablesWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

ImGui_input_fields_window_state.window_name = "PyImGui Input Fields DEMO"
ImGui_input_fields_window_state.values = [0.0, 0, 0.0, 0, ""]

def ShowPyImGuiInputFieldsWindow():
    global module_name
    global ImGui_input_fields_window_state
    description = "This section demonstrates the use of input \nfields in PyImGui. \nInput fields allow users to input values such \nas numbers, text, and colors. \nIn this demo, you can see how to create \nand use input fields in your interface."

    try: 
       width, height = 310,510
       PyImGui.set_next_window_size(width, height)
       if PyImGui.begin(ImGui_input_fields_window_state.window_name,PyImGui.WindowFlags.NoResize):

            ImGui.DrawTextWithTitle(ImGui_input_fields_window_state.window_name, description)

            # Slider for float values
            ImGui_input_fields_window_state.values[0] = PyImGui.slider_float("Adjust Float", ImGui_input_fields_window_state.values[0], 0.0, 1.0)
            PyImGui.text(f"Float Value: {ImGui_input_fields_window_state.values[0]:.2f}")
            PyImGui.separator()
            
            # Slider for integer values
            ImGui_input_fields_window_state.values[1] = PyImGui.slider_int("Adjust Int", ImGui_input_fields_window_state.values[1], 0, 100)
            PyImGui.text(f"Int Value: {ImGui_input_fields_window_state.values[1]}")
            PyImGui.separator()

            # Input for float values
            ImGui_input_fields_window_state.values[2] = PyImGui.input_float("Float Input", ImGui_input_fields_window_state.values[2])
            PyImGui.text(f"Float Input: {ImGui_input_fields_window_state.values[2]:.2f}")
            PyImGui.separator()

            # Input for integer values
            ImGui_input_fields_window_state.values[3] = PyImGui.input_int("Int Input", ImGui_input_fields_window_state.values[3])

            PyImGui.text(f"Int Input: {ImGui_input_fields_window_state.values[3]}")
            PyImGui.separator()

            if not isinstance(ImGui_input_fields_window_state.values[4], str):
                ImGui_input_fields_window_state.values[4] = "forced text value"
            # Text Input
            ImGui_input_fields_window_state.values[4] = PyImGui.input_text("Enter Text", ImGui_input_fields_window_state.values[4])
            PyImGui.text(f"Entered Text: {ImGui_input_fields_window_state.values[4]}")
            PyImGui.separator()

       PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPyImGuiInputFieldsWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

ImGui_selectables_window_state.window_name = "PyImGui Selectables DEMO"
ImGui_selectables_window_state.values = [True, 0, 0]

def ShowPyImGuiSelectablesWindow():
    global module_name
    global ImGui_selectables_window_state
    description = "This section demonstrates the use of selectables in PyImGui. \nSelectables allow users to interact with items by clicking on them. \nIn this demo, you can see how to create and use selectables in your interface."

    try:  
       width, height = 300,425
       PyImGui.set_next_window_size(width, height)
       if PyImGui.begin(ImGui_selectables_window_state.window_name,PyImGui.WindowFlags.NoResize):

            ImGui.DrawTextWithTitle(ImGui_selectables_window_state.window_name, description, 8)

            ImGui_selectables_window_state.values[0] = PyImGui.checkbox("Check Me!", ImGui_selectables_window_state.values[0])
            PyImGui.text(f"Checkbox is {'checked' if ImGui_selectables_window_state.values[0] else 'unchecked'}")
            PyImGui.separator()
        
            ImGui_selectables_window_state.values[1] = PyImGui.radio_button("Radio Button 1", ImGui_selectables_window_state.values[1], 0)
            ImGui_selectables_window_state.values[1] = PyImGui.radio_button("Radio Button 2", ImGui_selectables_window_state.values[1], 1)
            ImGui_selectables_window_state.values[1] = PyImGui.radio_button("Radio Button 3", ImGui_selectables_window_state.values[1], 2)

            PyImGui.text(f"Selected Radio Button: {ImGui_selectables_window_state.values[1] + 1}")
            PyImGui.separator()
                
            # Combo Box
            items = ["Item 1", "Item 2", "Item 3"]
            ImGui_selectables_window_state.values[2] = PyImGui.combo("Combo Box", ImGui_selectables_window_state.values[2], items)
            PyImGui.text(f"Selected Combo Item: {items[ImGui_selectables_window_state.values[2]]}")
            PyImGui.separator()

       PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPyImGuiSelectablesWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


ImGui_window_state.window_name = "PyImGui DEMO"
ImGui_window_state.button_list = ["Selectables", "Input Fields", "Tables", "Miscelaneous", "Official DEMO"]
ImGui_window_state.is_window_open = [False, False, False, False, False]
    
def ShowPyImGuiDemoWindow():
    global module_name
    global ImGui_window_state
    description = "This library has hundreds of functions and demoing each of them is unpractical. \nHere you will find a demo with most useful ImGui functions aswell as an oficial DEMO.\nFor a full detailed list of methods available consult the 'stubs' folder. \nFunctions that are unavailable can be added upon request, \ncontact the autor of the library and request them to be added."

    selected_button_index = 0
    try:
        width, height = 460,340
        PyImGui.set_next_window_size(width, height)

        if PyImGui.begin(ImGui_window_state.window_name,PyImGui.WindowFlags.NoResize):
            ImGui.DrawTextWithTitle("PyImGui ATTENTION", description)

        
            # ----- Top Section: Dynamic Tileset of Buttons -----
            PyImGui.text("Select a Feature:")

            # Calculate dynamic grid layout based on number of buttons
            total_buttons = len(ImGui_window_state.button_list)
            columns, rows = calculate_grid_layout(total_buttons)

            # Create a table with dynamically calculated columns
            if PyImGui.begin_table("ImGuiButtonTable", columns):  # Dynamic number of columns
                for button_index, button_label in enumerate(ImGui_window_state.button_list):
                    PyImGui.table_next_column()  # Move to the next column

                    selected_button_index = button_index
                    ImGui_window_state.is_window_open[selected_button_index] = ImGui.toggle_button(button_label, ImGui_window_state.is_window_open[selected_button_index])
                    
                    if ImGui_window_state.is_window_open[selected_button_index]:
                        title = ImGui_window_state.button_list[selected_button_index]

                
                PyImGui.end_table()  # End the table
                
            PyImGui.separator()  # Separator between sections

            
            if ImGui_window_state.is_window_open[0]:
                ShowPyImGuiSelectablesWindow()

            if ImGui_window_state.is_window_open[1]:
                ShowPyImGuiInputFieldsWindow()

            if ImGui_window_state.is_window_open[2]:
                ShowPyImGuiTablesWindow()

            if ImGui_window_state.is_window_open[3]:
                ShowPyImGuiMiscelaneousWindow()

            if ImGui_window_state.is_window_open[4]:
                PyImGui.show_demo_window()

            

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPyImGuiDemoWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


main_window_state.window_name = "Py4GW Lib DEMO"

main_window_state.is_window_open = [False, False, False, False, False, False, False, False, False, False, False, False, False,False]

main_window_state.button_list = [
    "PyImGui", "PyMap", "PyAgent", "PyPlayer", "PyParty", 
    "PyItem", "PyInventory", "PySkill", "PySkillbar", "PyEffects",
    "PyMerchant","PyQuest","Py4GW"
]

main_window_state.description_list = [
    "PyImGui: Provides bindings for creating and managing graphical user interfaces within the game using ImGui. \nIncludes support for text, buttons, tables, sliders, and other GUI elements.",   
    "PyMap: Manages map-related functions such as handling travel, region data, instance types, and map context. \nIncludes functionality for interacting with server regions, campaigns, and continents.",    
    "PyAgent: Handles in-game entities (agents) such as players, NPCs, gadgets, and items. \nProvides methods for manipulating and interacting with agents, including movement, targeting, and context updates.",    
    "PyPlayer: Provides access to the player-specific operations.\nIncludes functionality for interacting with agents, changing targets, issuing chat commands, and other player-related actions such as moving or interacting with the game environment.",   
    "PyParty: Manages party composition and party-related actions.\n This includes adding/kicking party members (players, heroes, henchmen), flagging heroes, and responding to party requests.\nAllows access to party details like members, size, and mode (e.g., Hard Mode).",   
    "PyItem: Provides functions for handling in-game items.\nThis includes retrieving item information (modifiers, rarity, type), context updates, and operations like dyeing or identifying items.",
    "PyInventory: Manages the player's inventory, including Xunlai storage interactions, item manipulation (pick up, drop, equip, destroy), and salvage operations. \nAlso includes functions for managing gold and moving items between inventory bags.", 
    "PySkill: Handles in-game skills and their properties.\nProvides access to skill-related data such as skill effects, costs (energy, health, adrenaline), and professions.\nIncludes methods for interacting with individual skills and loading skill templates.",
    "PySkillbar: Manages the player's skillbar, including loading skill templates, using skills in specific slots, and refreshing the skillbar context. \nEach skill in the skillbar can be interacted with or updated.",
    "PyEffects: Provides functions for handling in-game effects, including conditions, hexes, enchantments, and other status effects. \nIncludes methods for removing, and updating effects on the player.",
    "PyMerchant: Manages interactions with in-game merchants, including buying and selling items, requesting price quotes, and checking transaction status. \nProvides methods to handle trade-related actions and merchant-specific functionality.",
    "PyQuest: Provides functions for handling in-game quests. \nIncludes methods for handling active quests and abandoning them, more info is yet to be shared.",
    "Py4GW: Is a collection of miscellaneous functions that are not covered by the other modules. \nThis includes utility functions, helper methods, and additional features that enhance the Py4GW library."
]

main_window_state.is_window_open = [False, False, False, False, False, False, False, False, False, False, False, False, False, False,False]

title = "Welcome"
explanation_text_content = "Select a feature to see its details here."

test_button = False

# Example of additional utility function
def DrawWindow():
    global module_name
    global main_window_state

    global title
    global explanation_text_content
    global test_button

    selected_button_index = 0
    try:
        width, height = 400,360
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(main_window_state.window_name,PyImGui.WindowFlags.NoResize):
        
            # ----- Top Section: Dynamic Tileset of Buttons -----
            PyImGui.text("Select a Feature:")

            # Calculate dynamic grid layout based on number of buttons
            total_buttons = len(main_window_state.button_list)
            columns, rows = calculate_grid_layout(total_buttons)

            # Create a table with dynamically calculated columns
            if PyImGui.begin_table("MainWindowButtonTable", columns):  # Dynamic number of columns
                for button_index, button_label in enumerate(main_window_state.button_list):
                    PyImGui.table_next_column()  # Move to the next column

                    selected_button_index = button_index
                    main_window_state.is_window_open[selected_button_index] = ImGui.toggle_button(button_label, main_window_state.is_window_open[selected_button_index])
                    
                    if main_window_state.is_window_open[selected_button_index]:
                        title = main_window_state.button_list[selected_button_index]
                        explanation_text_content = main_window_state.description_list[selected_button_index]

                
                PyImGui.end_table()  # End the table
                
            PyImGui.separator()  # Separator between sections

            ImGui.DrawTextWithTitle(title, explanation_text_content)
            

            if main_window_state.is_window_open[0]:
                ShowPyImGuiDemoWindow()

            if main_window_state.is_window_open[1]:
                ShowPyMapWindow()

            if main_window_state.is_window_open[2]:
                ShowPyAgentWindow()

            if main_window_state.is_window_open[3]:
                ShowPlayerWindow()

            if main_window_state.is_window_open[4]:
                ShowPartyWindow()

            if main_window_state.is_window_open[5]:
                ShowItemWindow()

            if main_window_state.is_window_open[6]:
                ShowInventoryWindow()

            if main_window_state.is_window_open[7]:
                ShowSkillWindow()

            if main_window_state.is_window_open[8]:
                ShowSkillbarWindow()

            if main_window_state.is_window_open[9]:
                ShowEffectsWindow()

            if main_window_state.is_window_open[10]:
                ShowMerchantWindow()

            if main_window_state.is_window_open[11]:
                ShowQuestWindow()

            if main_window_state.is_window_open[12]:
                ShowPy4GW_Window_main()

        PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def CloseAllWindows():
    global main_window_state, ImGui_window_state, ImGui_selectables_window_state, ImGui_input_fields_window_state, ImGui_tables_window_state
    global ImGui_misc_window_state, PyMap_window_state, PyMap_Travel_Window_state, PyMap_Extra_InfoWindow_state, PyAgent_window_state
    
    # List of all window states
    window_states = [
        main_window_state,
        ImGui_window_state,
        ImGui_selectables_window_state,
        ImGui_input_fields_window_state,
        ImGui_tables_window_state,
        ImGui_misc_window_state,
        PyMap_window_state,
        PyMap_Travel_Window_state,
        PyMap_Extra_InfoWindow_state,
        PyAgent_window_state
    ]
    
    # Iterate over each window state object
    for window_state in window_states:
        # Assuming each window_state has an attribute `is_window_open` that is a list
        for i in range(len(window_state.is_window_open)):
            window_state.is_window_open[i] = False  # Close each window

def configure():
    pass

# main function must exist in every script and is the entry point for your script's execution.
def main():
    global module_name
    try:
        if GLOBAL_CACHE.Map.IsMapReady():    
            DrawWindow()
        else:
            CloseAllWindows()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()



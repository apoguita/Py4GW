import PyImGui

import PyCallback
from Py4GWCoreLib import ImGui, Color
from Py4GWCoreLib.IniManager import IniManager

show_disabled = False
    
def draw_window():
    global show_disabled
    # 1. Grab current snapshot from C++
    # Structure: (id, name, phase, context, priority, order)
    callback_list = PyCallback.PyCallback.GetCallbackInfo()

    # 2. Define our display order and names explicitly (Avoids 'not iterable' error)
    contexts = [
        (PyCallback.Context.Update, "UPDATE (Logic)[update loop]"),
        (PyCallback.Context.Draw, "DRAW (Visuals[draw loop])"),
        (PyCallback.Context.Main, "MAIN (Scripts)[draw loop]")
    ]
    
    phases = [
        (PyCallback.Phase.PreUpdate, "Pre-Update (Initialization)"),
        (PyCallback.Phase.Data, "Data Gathering (Pre-Logic)"),
        (PyCallback.Phase.Update, "Update (Execution)")
    ]

    # 3. Group and Sort Data
    # Final structure: grouped[context][phase] = [sorted_list]
    # 3. Group and Sort Data
    grouped = {}
    for cb in callback_list:
        # Unpack indices
        cb_id, cb_name, cb_phase_idx, cb_ctx_idx, cb_priority, cb_order, cb_enabled = cb
        
        # FIX: Ensure we are using the Enum type for the keys
        # This matches the 'contexts' and 'phases' lists used in the draw loop
        try:
            cb_context = PyCallback.Context(cb_ctx_idx)
            cb_phase = PyCallback.Phase(cb_phase_idx)
        except ValueError:
            # Fallback for unexpected values
            continue
        
        if cb_context not in grouped:
            grouped[cb_context] = {}
        if cb_phase not in grouped[cb_context]:
            grouped[cb_context][cb_phase] = []
            
        grouped[cb_context][cb_phase].append(cb)

    # Sort each list by Priority then Order
    for ctx_id in grouped:
        for ph_id in grouped[ctx_id]:
            grouped[ctx_id][ph_id].sort(key=lambda x: (x[4], x[5]))

    # 4. Draw the ImGui Window
    if ImGui.Begin(INI_KEY,"Callback Monitor"):
        
        # --- TOTALS SUMMARY ---
        total_cbs = len(callback_list)
        PyImGui.text(f"Active Callbacks: {total_cbs}")
        PyImGui.separator()
        show_disabled = PyImGui.checkbox("Show Disabled Callbacks", show_disabled)
        PyImGui.spacing()

        # --- CONTEXT ITERATION ---
        for ctx_val, ctx_name in contexts:
            if ctx_val not in grouped:
                continue
            
            # Show top-level header for Draw vs Update
            if PyImGui.collapsing_header(ctx_name, PyImGui.TreeNodeFlags.DefaultOpen):
                PyImGui.indent(20)
                
                # --- PHASE ITERATION ---
                for ph_val, ph_name in phases:
                    ph_list = grouped[ctx_val].get(ph_val, [])
                    if not ph_list:
                        continue

                    # Use a tree node for the Phase to keep it clean
                    if PyImGui.tree_node(f"{ph_name} ({len(ph_list)})###{ctx_val}_{ph_val}"):
                        
                        # Use a table for better alignment of IDs and Priorities
                        if PyImGui.begin_table(f"table_{ctx_val}_{ph_val}", 5, PyImGui.TableFlags.BordersInnerV):
                            PyImGui.table_setup_column("Priority", PyImGui.TableColumnFlags.WidthFixed, 50)
                            PyImGui.table_setup_column("Name", PyImGui.TableColumnFlags.WidthStretch)
                            PyImGui.table_setup_column("ID", PyImGui.TableColumnFlags.WidthFixed, 40)
                            PyImGui.table_setup_column("Enabled", PyImGui.TableColumnFlags.WidthFixed, 60)
                            PyImGui.table_setup_column("Pause", PyImGui.TableColumnFlags.WidthFixed, 60)
                            PyImGui.table_headers_row()

                            for cb in ph_list:
                                if not show_disabled and cb[6]:
                                    continue
                                PyImGui.table_next_row()
                                PyImGui.table_next_column()
                                PyImGui.text(f"P: {cb[4]}")
                                
                                PyImGui.table_next_column()
                                PyImGui.text(cb[1]) # Name
                                
                                PyImGui.table_next_column()
                                PyImGui.text(str(cb[0])) # ID

                                PyImGui.table_next_column()
                                PyImGui.text("Yes" if not cb[6] else "No") # Enabled
                                
                                PyImGui.table_next_column()
                                if PyImGui.button(f"Toggle##{cb[0]}"):
                                    if not cb[6]: # If currently enabled, disable it
                                        PyCallback.PyCallback.PauseById(cb[0])
                                    else: # If currently disabled, enable it
                                        PyCallback.PyCallback.ResumeById(cb[0])
                                

                            PyImGui.end_table()
                        
                        PyImGui.tree_pop()
                
                PyImGui.unindent(20)
                PyImGui.spacing()

        if PyImGui.button("Clear All Callbacks"):
            PyCallback.PyCallback.Clear()

        ImGui.End(INI_KEY)
        
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Frame Callback Monitor", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A low-level debugging utility for monitoring the Py4GW engine.")
    PyImGui.text("It visualizes the internal execution order of scripts and engine")
    PyImGui.text("callbacks across the different update phases of the game frame.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Phase Tracking: Categorizes callbacks into PreUpdate, Data, and Update phases")
    PyImGui.bullet_text("Priority Visualization: Displays execution order based on priority and ID")
    PyImGui.bullet_text("Real-time Metrics: Shows the number of active callbacks per phase")
    PyImGui.bullet_text("Deep Inspection: Identifies specific scripts by name to find performance bottlenecks")
    PyImGui.bullet_text("UI Organization: Uses collapsing headers to keep the debug view manageable")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")


    PyImGui.end_tooltip()

INI_KEY = ""
INI_PATH = "Widgets/CallbackMonitor" #path to save ini key
INI_FILENAME = "CallbackMonitor.ini" #ini file name



def main():
    global INI_KEY
     #one time initialization
    if not INI_KEY:
        INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
        if not INI_KEY:
            return
        IniManager().load_once(INI_KEY)

    draw_window()

if __name__ == "__main__":
    main()

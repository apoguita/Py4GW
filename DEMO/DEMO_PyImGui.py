# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui     #ImGui wrapper
import PyMap        #Map functions and classes
import PyAgent      #Agent functions and classes
import PyPlayer     #Player functions and classes
import PyParty      #Party functions and classes
import PyItem       #Item functions and classes
import PyInventory  #Inventory functions and classes
import PySkill      #Skill functions and classes
import PySkillbar   #Skillbar functions and classes
import PyMerchant   #Merchant functions and classes
import traceback    #traceback to log stack traces
# End Necessary Imports


# Persistent state variables
module_name = "PyImGui DEMO"

class AppState:
    def __init__(self):
        self.counter = 0
        self.checkbox_state = False
        self.radio_button_selected = 0
        self.slider_float_value = 0.5
        self.slider_int_value = 50
        self.input_float_value = 1.0
        self.input_int_value = 10
        self.color3 = [1.0, 0.0, 0.0]  # RGB color
        self.color4 = [1.0, 0.0, 0.0, 1.0]  # RGBA color
        self.progress = 0.5
        self.combo_selected = 0
        self.text_input = "default text"
        self.show_demo_window = False

state = AppState()

def AddNumber(a, b):
    return a + b

def DrawWindow():
    global module_name
    global state

    # Begin the ImGui window with MenuBar flag
    if PyImGui.begin("PyImGui Demo Window"):
        PyImGui.text("Basic Widgets")
        PyImGui.separator()

        PyImGui.text("Welcome to the PyImGui Demo!")
        PyImGui.separator()
        if PyImGui.collapsing_header("Buttons", PyImGui.TreeNodeFlags.DefaultOpen):

            if PyImGui.button("Click Me!"):
                PyImGui.same_line(0.0, -1.0)
                PyImGui.set_tooltip("Button clicked!")
                PyImGui.text("Button clicked!")
                Py4GW.Console.Log(module_name, "Button Clicked!")
            PyImGui.separator()

            if PyImGui.button("Increment Counter"):
                state.counter = AddNumber(state.counter, 1)
            PyImGui.text(f"Counter: {state.counter}")
            PyImGui.separator()

        if PyImGui.collapsing_header("Selectables", PyImGui.TreeNodeFlags.Bullet):
            state.checkbox_state = PyImGui.checkbox("Check Me!", state.checkbox_state)
            PyImGui.text(f"Checkbox is {'checked' if state.checkbox_state else 'unchecked'}")
            PyImGui.separator()
            
            # Radio Buttons with a single integer state variable
            state.radio_button_selected = PyImGui.radio_button("Radio Button 1", state.radio_button_selected, 0)
            state.radio_button_selected = PyImGui.radio_button("Radio Button 2", state.radio_button_selected, 1)
            state.radio_button_selected = PyImGui.radio_button("Radio Button 3", state.radio_button_selected, 2)

            PyImGui.text(f"Selected Radio Button: {state.radio_button_selected + 1}")
            PyImGui.separator()
            
            # Combo Box
            items = ["Item 1", "Item 2", "Item 3"]
            state.combo_selected = PyImGui.combo("Combo Box", state.combo_selected, items)
            PyImGui.text(f"Selected Combo Item: {items[state.combo_selected]}")
            PyImGui.separator()
        
        if PyImGui.collapsing_header("Input Fields"):
            # Slider for float values
            state.slider_float_value = PyImGui.slider_float("Adjust Float", state.slider_float_value, 0.0, 1.0)
            PyImGui.text(f"Float Value: {state.slider_float_value:.2f}")
            PyImGui.separator()
            
            # Slider for integer values
            state.slider_int_value = PyImGui.slider_int("Adjust Int", state.slider_int_value, 0, 100)
            PyImGui.text(f"Int Value: {state.slider_int_value}")
            PyImGui.separator()

            # Input for float values
            state.input_float_value = PyImGui.input_float("Float Input", state.input_float_value)
            PyImGui.text(f"Float Input: {state.input_float_value:.2f}")
            PyImGui.separator()

            # Input for integer values
            state.input_int_value = PyImGui.input_int("Int Input", state.input_int_value)
            PyImGui.text(f"Int Input: {state.input_int_value}")
            PyImGui.separator()

            if not isinstance(state.text_input, str):
                state.text_input = "forced text value"
            # Text Input
            state.text_input = PyImGui.input_text("Enter Text", state.text_input)
            PyImGui.text(f"Entered Text: {state.text_input}")
            PyImGui.separator()
            
        if PyImGui.collapsing_header("Tables"):
            # Test Table
            if PyImGui.begin_table("Test Table", 3):  # Begin a table with 3 columns
                PyImGui.table_setup_column("Column 1")
                PyImGui.table_setup_column("Column 2")
                PyImGui.table_setup_column("Column 3")
                PyImGui.table_headers_row()

                # First row
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text("Cell 1, Column 1")
                PyImGui.table_set_column_index(1)
                PyImGui.text("Cell 1, Column 2")
                PyImGui.table_set_column_index(2)
                PyImGui.text("Cell 1, Column 3")
                
                # Second row
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text("Cell 2, Column 1")
                PyImGui.table_set_column_index(1)
                PyImGui.text("Cell 2, Column 2")
                PyImGui.table_set_column_index(2)
                PyImGui.text("Cell 2, Column 3")

                PyImGui.end_table()
                
        if PyImGui.collapsing_header("Miscellaneous"):
            # Color Edit (RGB)
            state.color3 = PyImGui.color_edit3("Pick a Color (RGB)", state.color3)
            PyImGui.text(f"Selected Color (RGB): {state.color3}")
            PyImGui.separator()

            # Color Edit (RGBA)
            state.color4 = PyImGui.color_edit4("Pick a Color (RGBA)", state.color4)
            PyImGui.text(f"Selected Color (RGBA): {state.color4}")
            PyImGui.separator()
            
            # Progress Bar
            state.progress += 0.01  # Increment the progress by all amount
            if state.progress > 1.0:  # If progress exceeds 1.0 (100%), reset to 0.0
                state.progress = 0.0
            PyImGui.progress_bar(state.progress, 100.0, "Progress Bar")  # Show progress in the range [0.0, 1.0]
            PyImGui.separator()

            # Test bullet text
            PyImGui.bullet_text("Test Bullet Point")
            PyImGui.separator()
            
            # Toggle Demo Window
            if PyImGui.button("Toggle Demo Window"):
                state.show_demo_window = not state.show_demo_window
            
            if state.show_demo_window:
                PyImGui.show_demo_window()

        PyImGui.end()

def main():
    try:
        DrawWindow()
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}")
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}")
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}")
    finally:
        pass  # Replace with your actual code

if __name__ == "__main__":
    main()

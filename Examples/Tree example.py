from Py4GWCoreLib import *

# Persistent state variables
checkbox_state = True
expanded_subtree_states = [False, False, False]  # States for expanded subtrees

def DrawWindow():
    global checkbox_state
    global expanded_subtree_states

    if PyImGui.begin("Elaborate Tree Example"):
        # Top-level tree node
        if PyImGui.tree_node("Root Node"):
            PyImGui.text("Root Node Content")
            
            # First Subtree
            if PyImGui.tree_node("Subtree 1"):
                PyImGui.text("Content inside Subtree 1")
                PyImGui.separator()
                PyImGui.text("More content can go here.")
                PyImGui.tree_pop()
            
            # Second Subtree with Checkbox
            if PyImGui.tree_node("Subtree 2"):
                expanded_subtree_states[1] = PyImGui.checkbox("Toggle Me!", expanded_subtree_states[1])
                PyImGui.text(f"Checkbox is {'Checked' if expanded_subtree_states[1] else 'Unchecked'}")
                PyImGui.tree_pop()
            
            # Third Subtree with Nested Subtree
            if PyImGui.tree_node("Subtree 3"):
                PyImGui.text("This subtree contains another tree:")
                if PyImGui.tree_node("Nested Subtree"):
                    PyImGui.text("Content inside the Nested Subtree")
                    PyImGui.tree_pop()
                PyImGui.tree_pop()
            
            # End of the Root Node
            PyImGui.tree_pop()
        
    PyImGui.end()

# Entry point for the script
def main():
    DrawWindow()

if __name__ == "__main__":
    main()

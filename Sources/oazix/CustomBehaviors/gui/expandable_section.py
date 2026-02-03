from Py4GWCoreLib import PyImGui


class ExpandableSection:
    """
    Generic reusable class for managing expand/collapse UI state.

    This class provides a simple way to add expand/collapse functionality to any UI section.
    It manages the state and provides a toggle button that shows [+] when collapsed and [-] when expanded.

    Example Usage:
        # 1. Create an instance for your section (typically at module level or as a class attribute)
        inventory_section = ExpandableSection(initially_expanded=False)

        # 2. In your render code, add the toggle button
        inventory_section.render_expand_toggle("", "expand_inventory")

        # 3. Check if expanded to conditionally show/hide content
        if inventory_section.is_expanded():
            # Render your expanded content here
            if PyImGui.begin_child("inventory_panel", size=(0, 300), border=True):
                PyImGui.text("Your inventory configuration here...")
                PyImGui.end_child()

    Advanced Usage:
        # You can also programmatically control the state
        inventory_section.set_expanded(True)  # Force expand
        inventory_section.toggle()  # Toggle the state

        # Add a label prefix to the toggle button
        inventory_section.render_expand_toggle("Options", "expand_inventory")
        # This will show "Options [+]##expand_inventory" or "Options [-]##expand_inventory"
    """
    
    def __init__(self, initially_expanded: bool = False):
        """
        Initialize an expandable section.
        
        Args:
            initially_expanded: Whether the section should start expanded (default: False)
        """
        self.expanded: bool = initially_expanded
    
    def is_expanded(self) -> bool:
        """
        Check if the section is currently expanded.
        
        Returns:
            True if expanded, False otherwise
        """
        return self.expanded
    
    def set_expanded(self, expanded: bool) -> None:
        """
        Programmatically set the expanded state.
        
        Args:
            expanded: The new expanded state
        """
        self.expanded = expanded
    
    def toggle(self) -> bool:
        """
        Toggle the expanded state.
        
        Returns:
            The new expanded state
        """
        self.expanded = not self.expanded
        return self.expanded
    
    def render_expand_toggle(self, label_prefix: str = "", id_suffix: str = "expand_toggle") -> bool:
        """
        Render a small button that toggles the expanded state.
        
        Args:
            label_prefix: Optional text to show before the [+]/[-] symbol
            id_suffix: Unique ID suffix for the button (required for ImGui)
        
        Returns:
            The current expanded state after rendering
        """
        toggle_label = "[-]" if self.expanded else "[+]"
        label = f"{label_prefix} {toggle_label}##{id_suffix}" if label_prefix else f"{toggle_label}##{id_suffix}"
        if PyImGui.small_button(label):
            self.expanded = not self.expanded
        return self.expanded


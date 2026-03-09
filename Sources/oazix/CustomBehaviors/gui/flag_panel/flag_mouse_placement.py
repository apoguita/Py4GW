"""
Flag Placement - Mouse-based flag placement functionality.

This module provides functionality for placing character flags at mouse cursor positions
in the game world using a two-phase interaction system.
"""
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.Py4GWcorelib import Utils
from Py4GWCoreLib.enums import Key, MouseButton
from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager


class FlagMousePlacement:
    """Handles mouse-based flag placement for characters."""
    
    _active_character_email: str | None = None  # Email of character waiting for flag placement
    
    @classmethod
    def is_active(cls) -> bool:
        """Check if flag placement mode is currently active."""
        return cls._active_character_email is not None
    
    @classmethod
    def get_active_character_email(cls) -> str | None:
        """Get the email of the character in placement mode."""
        return cls._active_character_email
    
    @classmethod
    def activate(cls, character_email: str) -> None:
        """Activate flag placement mode for a character."""
        cls._active_character_email = character_email
    
    @classmethod
    def deactivate(cls) -> None:
        """Deactivate flag placement mode."""
        cls._active_character_email = None
    
    @classmethod
    def toggle(cls, character_email: str) -> None:
        """Toggle flag placement mode for a character."""
        if cls._active_character_email == character_email:
            cls.deactivate()
        else:
            cls.activate(character_email)
    
    @classmethod
    def check_and_handle_input(cls) -> None:
        """Check for user input and handle flag placement or cancellation."""
        if not cls.is_active():
            return

        # Check for ESC key to cancel
        if PyImGui.is_key_pressed(Key.Escape.value):
            cls.deactivate()
            return

        # Check for right-click to place flag
        if PyImGui.is_mouse_clicked(MouseButton.Right.value):
            cls._place_flag_at_mouse()
    
    @classmethod
    def _place_flag_at_mouse(cls) -> None:
        """Place a flag at the current mouse position."""
        if not cls.is_active() or cls._active_character_email is None:
            return

        try:
            # Get mouse world position
            overlay = Overlay()
            mouse_x, mouse_y, _ = overlay.GetMouseWorldPos()

            # Find the appropriate flag slot
            flag_manager = PartyFlaggingManager()
            flag_index = cls._find_flag_slot(flag_manager, cls._active_character_email)

            # Set the flag
            flag_manager.set_flag_data(flag_index, cls._active_character_email, mouse_x, mouse_y)

            # Exit placement mode
            cls.deactivate()

        except Exception:
            # Silently fail if there's an issue getting mouse position
            pass
    
    @classmethod
    def _find_flag_slot(cls, flag_manager: PartyFlaggingManager, character_email: str) -> int:
        """
        Find the appropriate flag slot for a character.
        
        Priority:
        1. Existing flag slot for this character
        2. First empty slot
        3. Slot 0 (overwrite)
        
        Args:
            flag_manager: The flag manager instance
            character_email: Email of the character to flag
            
        Returns:
            Flag slot index (0-11)
        """
        # Try to find an existing flag for this character
        for i in range(12):
            existing_email = flag_manager.get_flag_account_email(i)
            if existing_email == character_email:
                return i
        
        # If no existing flag, find first empty slot
        for i in range(12):
            existing_email = flag_manager.get_flag_account_email(i)
            if not existing_email or existing_email == "":
                return i
        
        # If all slots are occupied, use slot 0 (overwrite)
        return 0
    
    @classmethod
    def reset(cls) -> None:
        """Reset flag placement state."""
        cls._active_character_email = None

    @classmethod
    def clear_character_flag(cls, character_email: str) -> bool:
        """
        Clear/drop the flag for a specific character.

        Args:
            character_email: Email of the character whose flag should be cleared

        Returns:
            True if a flag was found and cleared, False otherwise
        """
        flag_manager = PartyFlaggingManager()

        # Find the flag index for this character
        for i in range(12):
            existing_email = flag_manager.get_flag_account_email(i)
            if existing_email == character_email:
                # Clear this flag
                flag_manager.clear_flag(i)
                return True

        return False

    @classmethod
    def draw_overlay(cls) -> None:
        """Draw visual overlay at mouse position when in placement mode."""
        if not cls.is_active():
            return

        try:
            overlay = Overlay()
            overlay.BeginDraw("FlagPlacement")

            # Get mouse world position
            mouse_x, mouse_y, mouse_z = overlay.GetMouseWorldPos()

            # Draw a large green circle at mouse position
            overlay.DrawPolyFilled3D(mouse_x, mouse_y, mouse_z, 60,
                                    Utils.RGBToColor(0, 255, 0, 100), numsegments=32)

            # Draw circle outline (bright green)
            overlay.DrawPoly3D(mouse_x, mouse_y, mouse_z, 60,
                              Utils.RGBToColor(0, 255, 0, 255), numsegments=32, thickness=4.0)

            # Draw inner circle (pulsing effect)
            overlay.DrawPoly3D(mouse_x, mouse_y, mouse_z, 40,
                              Utils.RGBToColor(255, 255, 255, 200), numsegments=24, thickness=2.0)

            # Draw text above the circle
            overlay.DrawText3D(mouse_x, mouse_y, mouse_z - 100,
                             "RIGHT-CLICK TO PLACE FLAG",
                             Utils.RGBToColor(0, 255, 0, 255),
                             autoZ=False, centered=True, scale=1.2)

            # Draw coordinates
            overlay.DrawText3D(mouse_x, mouse_y, mouse_z - 140,
                             f"({mouse_x:.0f}, {mouse_y:.0f})",
                             Utils.RGBToColor(255, 255, 255, 255),
                             autoZ=False, centered=True, scale=0.9)

            overlay.EndDraw()

        except Exception:
            # Silently fail if there's an issue
            pass


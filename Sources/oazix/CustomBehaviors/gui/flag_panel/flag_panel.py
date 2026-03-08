from Py4GWCoreLib import PyImGui
from Sources.oazix.CustomBehaviors.gui.flag_panel.flag_custom_grid_placement import FlagCustomGridPlacement
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager


class FlagPanel:
    _persistence = PersistenceLocator().flagging
    _spacing_initialized: bool = False
    _movement_threshold_initialized: bool = False

    @staticmethod
    def render_configuration() -> None:
        """
        Render the configurable flags/formation UI.
        Note: The caller should check if the section is expanded before calling this method.
        """
        flag_manager = PartyFlaggingManager()

        # Load spacing from INI on first render (ALWAYS, even if header is closed)
        if not FlagPanel._spacing_initialized:
            saved_spacing = FlagPanel._persistence.read_spacing_radius()
            flag_manager.spacing_radius = saved_spacing
            FlagPanel._spacing_initialized = True

        # Load movement threshold from INI on first render (ALWAYS, even if header is closed)
        if not FlagPanel._movement_threshold_initialized:
            saved_movement_threshold = FlagPanel._persistence.read_follow_flag_threshold() or 50.0
            flag_manager.movement_threshold = saved_movement_threshold
            FlagPanel._movement_threshold_initialized = True

        # Always enable overlay; remove UI toggle
        flag_manager.enable_debug_overlay = True

        # Ensure FlagGridUI is initialized even when header is closed
        FlagCustomGridPlacement.ensure_initialized()

        # Wrap in collapsing header
        if PyImGui.collapsing_header("Flag Configuration"):
            # Use a child window to control width
            if PyImGui.begin_child("flag_config_child", (600, 400), False, PyImGui.WindowFlags.NoFlag):

                flag_manager = PartyFlaggingManager()

                # Movement threshold slider
                current_movement_threshold = flag_manager.movement_threshold
                new_movement_threshold = PyImGui.slider_float("Movement Threshold", current_movement_threshold, 10.0, 450.0)
                PyImGui.same_line(0.0, -1.0)
                PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("How much players can move from their assigned flag before repositioning (game units)")
                if new_movement_threshold != current_movement_threshold:
                    flag_manager.movement_threshold = new_movement_threshold
                    # Save to INI when changed
                    FlagPanel._persistence.write_follow_flag_threshold(new_movement_threshold)

                PyImGui.spacing()

                # Spacing radius slider
                current_spacing = flag_manager.spacing_radius
                new_spacing = PyImGui.slider_float("Spacing Radius", current_spacing, 50.0, 300.0)
                PyImGui.same_line(0.0, -1.0)
                PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("Distance between flags in the grid formation (game units)")
                if new_spacing != current_spacing:
                    flag_manager.spacing_radius = new_spacing
                    # Save to INI when changed
                    FlagPanel._persistence.write_spacing_radius(new_spacing)

                PyImGui.spacing()


                # Tabs for configuration
                if PyImGui.begin_tab_bar("flag_config_tabs"):

                    # Grid layout with FlagGridUI
                    if PyImGui.begin_tab_item("Preset 0 : Custom Grid"):
                        FlagCustomGridPlacement.render_configuration()
                        PyImGui.end_tab_item()
                    
                    # Preset 1: GridBackWard Leader
                    if PyImGui.begin_tab_item("Preset 1 : AutoGrid BackWard Leader"):
                        PyImGui.text("All flags are placed behind the leader position, in a 3x4 grid.")
                        PyImGui.text("NO ADDITIONAL CONFIGURATION IS NEEDED FOR THIS PRESET.")
                        PyImGui.end_tab_item()

                    # Preset 2: Stacked
                    if PyImGui.begin_tab_item("Preset 2 : Stacked"):
                        PyImGui.text("All flags are stacked at the leader position.\nNo additional configuration is needed here.")
                        PyImGui.text("NO ADDITIONAL CONFIGURATION IS NEEDED FOR THIS PRESET.")
                        PyImGui.end_tab_item()

                    # Debug
                    if PyImGui.begin_tab_item("Debug"):
                        if PyImGui.button("Auto Assign Emails##auto_assign_emails"):
                            flag_manager.auto_assign_emails_if_none_assigned()
                        for i in range(12):
                            email, x, y = flag_manager.get_flag_data(i)
                            PyImGui.bullet_text(f"Flag {i}: {email} - ({x}, {y})")
                        PyImGui.end_tab_item()


                    PyImGui.end_tab_bar()

                PyImGui.end_child()

    @staticmethod
    def render_overlay() -> None:
        flag_manager = PartyFlaggingManager()
        # Force overlay always on from UI perspective
        flag_manager.enable_debug_overlay = True
        if flag_manager.enable_debug_overlay:
            behavior = CustomBehaviorLoader().custom_combat_behavior
            if behavior is not None:
                current_state = behavior.get_final_state()

                # find the flagging utility skill
                skills_list = behavior.additional_autonomous_skills
                from Sources.oazix.CustomBehaviors.skills.following.follow_flag_utility import FollowFlagUtility
                flagging_utility_skill = next((skill for skill in skills_list if skill.custom_skill.skill_name == FollowFlagUtility.Name), None)
                if isinstance(flagging_utility_skill, FollowFlagUtility):
                    flagging_utility_skill.draw_overlay(current_state)
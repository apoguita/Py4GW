
import PyImGui
from Py4GWCoreLib import Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.parties.party_following_manager import PartyFollowingManager
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import MAX_FLAG_POSITIONS
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator


class FollowingPanel:
    _forces_initialized: bool = False

    @staticmethod
    def render_configuration() -> None:
        following_manager = PartyFollowingManager()

        # Load force settings from persistence on first render
        if not FollowingPanel._forces_initialized:
            FollowingPanel._load_forces_from_persistence(following_manager)
            FollowingPanel._forces_initialized = True

        # Wrap in collapsing header
        if PyImGui.collapsing_header("Following Configuration"):
            # Use a child window to control width - wraps the tab bar
            if PyImGui.begin_child("following_config_child", (600, 400), False, PyImGui.WindowFlags.NoFlag):
                
                enable_debug_overlay = following_manager.enable_debug_overlay
                new_enable_debug_overlay = PyImGui.checkbox("Enable Debug Overlay##following_manager_enable_debug_overlay", enable_debug_overlay)
                if new_enable_debug_overlay != enable_debug_overlay:
                    following_manager.enable_debug_overlay = new_enable_debug_overlay

                # Create tab bar inside the child window
                if PyImGui.begin_tab_bar("FollowingConfigTabs"):

                    if PyImGui.begin_tab_item("Per-Account Forces"):
                        FollowingPanel._render_per_account_forces_tab(following_manager)
                        PyImGui.end_tab_item()

                    if PyImGui.begin_tab_item("Weights and thresholds"):
                        FollowingPanel._render_global_settings_tab(following_manager)
                        PyImGui.end_tab_item()

                    PyImGui.end_tab_bar()

                PyImGui.end_child()

    @staticmethod
    def _render_global_settings_tab(following_manager: PartyFollowingManager) -> None:
        """Render the global settings tab with thresholds and weights"""

        # === VECTOR FIELD CONFIGURATION (IN_AGGRO) ===
        PyImGui.text("Vector Field Configuration (IN_AGGRO):")
        PyImGui.spacing()

        # Enemy Repulsion
        PyImGui.text_colored("Enemy Repulsion:", (1.0, 0.84, 0.0, 1.0))  # Gold

        current_enemy_threshold = following_manager.enemy_repulsion_threshold
        new_enemy_threshold = PyImGui.slider_float(
            "Enemy Repulsion Threshold",
            current_enemy_threshold,
            50.0,
            400.0
        )
        PyImGui.same_line(0.0, -1.0)
        PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Distance from enemies to start repelling")
        if new_enemy_threshold != current_enemy_threshold:
            following_manager.enemy_repulsion_threshold = new_enemy_threshold

        current_enemy_weight = following_manager.enemy_repulsion_weight
        new_enemy_weight = PyImGui.slider_float(
            "Enemy Repulsion Weight",
            current_enemy_weight,
            0.0,
            300.0
        )
        PyImGui.same_line(0.0, -1.0)
        PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("How strongly to push away from enemies")
        if new_enemy_weight != current_enemy_weight:
            following_manager.enemy_repulsion_weight = new_enemy_weight

        PyImGui.spacing()

        # Leader Attraction
        PyImGui.text_colored("Leader Attraction:", (1.0, 0.84, 0.0, 1.0))  # Gold

        current_leader_threshold = following_manager.leader_attraction_threshold
        new_leader_threshold = PyImGui.slider_float(
            "Leader Attraction Threshold",
            current_leader_threshold,
            50.0,
            800.0
        )
        PyImGui.same_line(0.0, -1.0)
        PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Distance from leader to start attraction")
        if new_leader_threshold != current_leader_threshold:
            following_manager.leader_attraction_threshold = new_leader_threshold

        current_leader_weight = following_manager.leader_attraction_weight
        new_leader_weight = PyImGui.slider_float(
            "Leader Attraction Weight",
            current_leader_weight,
            0.0,
            300.0
        )
        PyImGui.same_line(0.0, -1.0)
        PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("How strongly to pull toward leader")
        if new_leader_weight != current_leader_weight:
            following_manager.leader_attraction_weight = new_leader_weight

        PyImGui.spacing()

        # Allies Repulsion
        PyImGui.text_colored("Allies Repulsion:", (1.0, 0.84, 0.0, 1.0))  # Gold

        current_allies_threshold = following_manager.allies_repulsion_threshold
        new_allies_threshold = PyImGui.slider_float(
            "Allies Repulsion Threshold",
            current_allies_threshold,
            50.0,
            400.0
        )
        PyImGui.same_line(0.0, -1.0)
        PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Distance from allies to start repelling")
        if new_allies_threshold != current_allies_threshold:
            following_manager.allies_repulsion_threshold = new_allies_threshold

        current_allies_weight = following_manager.allies_repulsion_weight
        new_allies_weight = PyImGui.slider_float(
            "Allies Repulsion Weight",
            current_allies_weight,
            0.0,
            300.0
        )
        PyImGui.same_line(0.0, -1.0)
        PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("How strongly to push away from allies")
        if new_allies_weight != current_allies_weight:
            following_manager.allies_repulsion_weight = new_allies_weight

        PyImGui.spacing()
        PyImGui.spacing()

        # Movement Parameters
        PyImGui.text_colored("Movement Parameters:", (1.0, 0.84, 0.0, 1.0))  # Gold

        current_min_threshold = following_manager.min_move_threshold
        new_min_threshold = PyImGui.slider_float(
            "Min Move Threshold",
            current_min_threshold,
            0.1,
            5.0
        )
        PyImGui.same_line(0.0, -1.0)
        PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Minimum vector magnitude to trigger movement (prevents jitter)")
        if new_min_threshold != current_min_threshold:
            following_manager.min_move_threshold = new_min_threshold

        current_max_distance = following_manager.max_move_distance
        new_max_distance = PyImGui.slider_float(
            "Max Move Distance",
            current_max_distance,
            50.0,
            500.0
        )
        PyImGui.same_line(0.0, -1.0)
        PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Maximum distance to move in one step")
        if new_max_distance != current_max_distance:
            following_manager.max_move_distance = new_max_distance

        PyImGui.spacing()

    @staticmethod
    def _render_per_account_forces_tab(following_manager: PartyFollowingManager) -> None:
        """Render the per-account force activation settings tab"""

        if PyImGui.button(f"{IconsFontAwesome5.ICON_SAVE} Save##following_forces_save", 80, 25):
            FollowingPanel._persist_forces_configuration(following_manager)
        PyImGui.same_line(0, 10)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_TRASH_ALT} Reset All##following_forces_reset", 120, 25):
            FollowingPanel._reset_all_forces(following_manager)

        PyImGui.text("Presets:")

        if PyImGui.button(f"{IconsFontAwesome5.ICON_ARROWS_ALT} Scatter party only"):
            following_manager.scatter_party()

        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_ARROWS_TO_CIRCLE} Close to leader"):
            following_manager.close_to_leader()

        

        PyImGui.text_colored("Per-Account Force Activation Settings", (0.0, 1.0, 1.0, 1.0))
        PyImGui.text("Each account can have different force activation settings.")
        PyImGui.spacing()

        # Create table with columns: Email, Allies Repulsion, Leader Attraction, Enemies Repulsion
        # Remove ScrollY to prevent flickering - table will size naturally
        if PyImGui.begin_table("PerAccountForcesTable", 4, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):

            # Setup columns
            PyImGui.table_setup_column("Account Name", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Allies Repulsion", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Leader Attraction", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Enemies Repulsion", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_headers_row()

            # Iterate through all account slots - display with checkboxes
            for idx in range(MAX_FLAG_POSITIONS):
                email = following_manager.get_account_email(idx)

                # Skip empty slots
                if not email or email.strip() == "":
                    continue
                account_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(email)
                
                PyImGui.table_next_row()

                # Column 1: AccountName
                PyImGui.table_next_column()
                if account_data is None:
                    PyImGui.text("N/A")
                else:
                    PyImGui.text(str(account_data.AgentData.CharacterName))

                # Column 2: Allies Repulsion (checkbox)
                PyImGui.table_next_column()
                current_allies_repulsion = following_manager.get_is_repulsion_allies_active_by_index(idx)
                new_allies_repulsion = PyImGui.checkbox(f"##allies_repulsion_{idx}", current_allies_repulsion)
                if new_allies_repulsion != current_allies_repulsion:
                    following_manager.set_is_repulsion_allies_active(email, new_allies_repulsion)

                # Column 3: Leader Attraction (checkbox)
                PyImGui.table_next_column()
                current_leader_attraction = following_manager.get_is_attraction_leader_active_by_index(idx)
                new_leader_attraction = PyImGui.checkbox(f"##leader_attraction_{idx}", current_leader_attraction)
                if new_leader_attraction != current_leader_attraction:
                    following_manager.set_is_attraction_leader_active(email, new_leader_attraction)

                # Column 4: Enemies Repulsion (checkbox)
                PyImGui.table_next_column()
                current_enemies_repulsion = following_manager.get_is_repulsion_enemies_active_by_index(idx)
                new_enemies_repulsion = PyImGui.checkbox(f"##enemies_repulsion_{idx}", current_enemies_repulsion)
                if new_enemies_repulsion != current_enemies_repulsion:
                    following_manager.set_is_repulsion_enemies_active(email, new_enemies_repulsion)

            PyImGui.end_table()

    @staticmethod
    def render_overlay() -> None:
        following_manager = PartyFollowingManager()
        # Only draw overlay if enabled
        if following_manager.enable_debug_overlay:
            behavior = CustomBehaviorLoader().custom_combat_behavior
            if behavior is not None:
                current_state = behavior.get_final_state()

                # find the flagging utility skill
                skills_list = behavior.additional_autonomous_skills
                from Sources.oazix.CustomBehaviors.skills.following.spread_during_combat_utility import SpreadDuringCombatUtility
                flagging_utility_skill = next((skill for skill in skills_list if skill.custom_skill.skill_name == SpreadDuringCombatUtility.Name), None)
                if isinstance(flagging_utility_skill, SpreadDuringCombatUtility):
                    flagging_utility_skill.draw_overlay(current_state)

    @staticmethod
    def _persist_forces_configuration(following_manager: PartyFollowingManager) -> None:
        """Save all force activation settings to persistence."""
        persistence = PersistenceLocator().following

        # Save force settings for all registered accounts
        saved_count = 0
        for idx in range(MAX_FLAG_POSITIONS):
            email = following_manager.get_account_email(idx)

            # Skip empty slots
            if not email or email.strip() == "":
                continue

            # Get current force settings
            allies_repulsion = following_manager.get_is_repulsion_allies_active_by_index(idx)
            leader_attraction = following_manager.get_is_attraction_leader_active_by_index(idx)
            enemies_repulsion = following_manager.get_is_repulsion_enemies_active_by_index(idx)

            # Save to persistence
            persistence.write_force_settings(email, allies_repulsion, leader_attraction, enemies_repulsion)
            saved_count += 1

        print(f"Persisted forces configuration for {saved_count} account(s)")

    @staticmethod
    def _reset_all_forces(following_manager: PartyFollowingManager) -> None:
        """Reset all force activation settings to defaults and clear persistence."""
        # Reset in-memory configuration
        following_manager.reset_all_forces()

        # Clear persistence
        persistence = PersistenceLocator().following
        persistence.clear_all_force_settings()

        print("Reset all forces to defaults and cleared persistence")

    @staticmethod
    def _load_forces_from_persistence(following_manager: PartyFollowingManager) -> None:
        """Load force activation settings from persistence."""
        persistence = PersistenceLocator().following
        all_settings = persistence.read_all_force_settings()

        if not all_settings:
            return

        # Apply loaded settings to shared memory
        loaded_count = 0
        for email, (allies_repulsion, leader_attraction, enemies_repulsion) in all_settings.items():
            following_manager.set_account_forces(email, allies_repulsion, leader_attraction, enemies_repulsion)
            loaded_count += 1

        if loaded_count > 0:
            print(f"Loaded forces configuration for {loaded_count} account(s) from persistence")
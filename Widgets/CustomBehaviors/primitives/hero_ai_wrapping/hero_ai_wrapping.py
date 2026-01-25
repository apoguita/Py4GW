from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.ImGui_src.WindowModule import WindowModule

from HeroAI.cache_data import CacheData
from HeroAI.settings import Settings

class HeroAiWrapping:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HeroAiWrapping, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.settings_write_throttler = ThrottledTimer(1_000)
            self._settings:Settings = Settings()
            self._cached_data:CacheData = CacheData()
            self.hero_windows: dict[str, WindowModule] = {}
            self.heroai_fallack_mecanism_throttler = ThrottledTimer(500)

    def _update_hero_ai_players(self, cached_data:CacheData):
        """Update HeroAI player registration and status"""
        if self.heroai_fallack_mecanism_throttler.IsExpired():
            self.heroai_fallack_mecanism_throttler.Reset()
            
            ##TODO: this is not needed anymore with the new shared memory changes

    def _initialize_and_persist_settings(self, settings:Settings):
        """
        Handle settings initialization and periodic persistence.
        Returns True if settings are ready, False if we should abort.
        """
        if self.settings_write_throttler.IsExpired():
            self.settings_write_throttler.Reset()

            # Ensure settings are initialized and loaded for the current account
            if not settings.ensure_initialized():
                # Account changed or not initialized - clear windows and return
                self.hero_windows.clear()
                return False

            settings.Anonymous_PanelNames = False
            settings.ShowHeroPanels = False
            settings.ShowPartyOverlay = False
            settings.ShowDialogOverlay = True
            settings.ShowLeaderPanel = True
            settings.ShowCommandPanel = False

            # Write settings to disk
            settings.write_settings()

        return True

    def _initialize_account_game_options(self, settings, cached_data, accounts):
        """Initialize game options for each account"""
        from HeroAI.constants import NUMBER_OF_SKILLS

        for account in accounts:
            # Ensure account has a panel position entry
            if account.AccountEmail not in settings.HeroPanelPositions:
                settings.HeroPanelPositions[account.AccountEmail] = settings.HeroPanelInfo()

            # Initialize game options for this account's party position (set all skills to active)
            party_pos = account.PartyPosition
            if party_pos >= 0 and party_pos < len(cached_data.HeroAI_vars.all_game_option_struct):
                game_options = cached_data.HeroAI_vars.all_game_option_struct[party_pos]
                # Set all skills to active if not already initialized
                for i in range(NUMBER_OF_SKILLS):
                    game_options.Skills[i].Active = True

    def act(self):
        """
        Main entry point for HeroAI logic:
        - Updates player registration
        - Manages settings lifecycle
        - Initializes game options
        - Renders GUI
        - Persists window positions
        """
        # Update HeroAI player registration
        self._update_hero_ai_players(self._cached_data)

        ##TODO: this is not needed anymore with the new shared memory changes
        # Update combat and game options
        # self._cached_data.UpdateCombat()
        # self._cached_data.UpdateGameOptions()

        # Initialize and persist settings (abort if not ready)
        if not self._initialize_and_persist_settings(self._settings):
            return

        # Get all accounts and messages
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        messages = GLOBAL_CACHE.ShMem.GetAllMessages()

        # Initialize game options for each account
        self._initialize_account_game_options(self._settings, self._cached_data, accounts)

        # Render GUI
        self._render_gui(self._settings, self._cached_data, accounts, messages)

        # Persist window positions after rendering
        self._persist_window_positions(self._settings)

    def _persist_window_positions(self, settings):
        """Save window positions if they changed (only when window is active)"""
        from Py4GWCoreLib.py4gwcorelib_src.Console import Console

        if not Console.is_window_active():
            return

        for account_email, window in self.hero_windows.items():
            window_info = settings.HeroPanelPositions.get(account_email, None)
            if window_info and (window.changed or window.collapse != window_info.collapsed or window.open != window_info.open):
                window_info.x = round(window.window_pos[0])
                window_info.y = round(window.window_pos[1])
                window_info.collapsed = window.collapse
                window_info.open = window.open
                settings.save_settings()

    def are_all_panels_visible(self) -> bool:
        """
        Check if all hero panels are currently visible.

        Returns:
            True if all panels are visible, False otherwise
        """
        if not self._settings.HeroPanelPositions:
            return False

        return all(
            info.open
            for info in self._settings.HeroPanelPositions.values()
        )

    def toggle_all_panels(self, visible: bool | None = None):
        """
        Toggle visibility of all hero panels.

        Args:
            visible: If True, show all panels. If False, hide all panels.
                    If None, toggle based on current state (if any panel is hidden, show all; otherwise hide all)
        """
        settings = self._settings

        if visible is None:
            # Auto-detect: if any panel is hidden, show all; otherwise hide all
            any_hidden = any(
                not info.open
                for info in settings.HeroPanelPositions.values()
            )
            visible = any_hidden

        # Update all panel positions
        for info in settings.HeroPanelPositions.values():
            info.open = visible

        # Save settings
        settings.save_settings()

    def _render_gui(self, settings, cached_data, accounts, messages):
        """Handle GUI rendering for HeroAI panels"""
        from HeroAI.ui import draw_hero_panel, draw_dialog_overlay

        # Create windows and draw hero panels for each account
        for account in accounts:
            # Skip leader's panel if ShowLeaderPanel is False
            # if account.AccountEmail == cached_data.account_email:
            if GLOBAL_CACHE.Party.IsPartyLeader() and not settings.ShowLeaderPanel:
                continue

            """Create WindowModule for account if it doesn't exist"""
            if account.AccountEmail not in self.hero_windows:
                info = settings.HeroPanelPositions.get(account.AccountEmail, settings.HeroPanelInfo())
                self.hero_windows[account.AccountEmail] = WindowModule(
                    module_name=f"HeroAI - {account.AccountEmail}",
                    window_name=f"##HeroAI - {account.AccountEmail}",
                    window_pos=(info.x, info.y),
                    collapse=info.collapsed,
                    can_close=False,
                )

            # Sync window visibility with settings before drawing
            window = self.hero_windows[account.AccountEmail]
            window_info = settings.HeroPanelPositions.get(account.AccountEmail, None)
            if window_info:
                window.open = window_info.open
                window.collapse = window_info.collapsed

            # Draw the hero panel
            draw_hero_panel(window, account, cached_data, messages)

        draw_dialog_overlay(accounts, cached_data, messages)
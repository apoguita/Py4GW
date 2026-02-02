from Py4GWCoreLib import Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import SharedMessage
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.ImGui_src.WindowModule import WindowModule

from HeroAI.cache_data import CacheData
from HeroAI.settings import Settings
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers

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
            self._is_heroai_ui_visible:bool = False
            self.dialog_throttle = ThrottledTimer(500)

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

            # Re-apply current visibility state to all panel positions
            # (in case load_settings() overwrote them with old values from disk)
            for info in settings.HeroPanelPositions.values():
                info.open = self._is_heroai_ui_visible

            # Write settings to disk
            settings.write_settings()

        return True

    def act(self):
        """
        Main entry point for HeroAI logic:
        - Updates player registration
        - Manages settings lifecycle
        - Initializes game options
        - Renders GUI
        - Persists window positions
        """

        # ----------------- MANAGE HERO SKILL FALLBACK -----------------

        # Update HeroAI player registration
        self._update_hero_ai_players(self._cached_data)

        # Get all accounts for forcing game options
        # accounts:list[AccountData] = GLOBAL_CACHE.ShMem.GetAllAccountData()

        # Force game options for each account (in shared memory) BEFORE syncing local cache
        # self._force_account_heroai_game_options(self._settings, self._cached_data, accounts)

        # Now sync local cache from shared memory (will read the forced values)
        # from HeroAI.game_option import UpdateGameOptions
        # UpdateGameOptions(self._cached_data)

        # Update combat and game options from local cache
        self._cached_data.Update()
        # self._cached_data.UpdateCombat()
        # self._cached_data.UpdateGameOptions()

        # ----------------- MANAGE HERO AI UI -----------------
        if not self._is_heroai_ui_visible: return
        if not custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader(): return

        # Initialize and persist settings (abort if not ready)
        if not self._initialize_and_persist_settings(self._settings):
            return

        # Get messages for GUI
        messages:list[tuple[int, SharedMessage]] = GLOBAL_CACHE.ShMem.GetAllMessages()

        # Get accounts from cached party data
        accounts = list(self._cached_data.party.accounts.values())

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

    def is_heroai_ui_visible(self) -> bool:
        return self._is_heroai_ui_visible
    
    def change_heroai_ui_visibility(self, is_visible: bool):

        self._is_heroai_ui_visible = is_visible

        settings = self._settings
        # Update all panel positions & save
        for info in settings.HeroPanelPositions.values():
            info.open = is_visible

        # Also update all existing window.open states to prevent _persist_window_positions from overwriting
        for window in self.hero_windows.values():
            window.open = is_visible

        settings.save_settings()

    def _render_gui(self, settings, cached_data, accounts, messages):
        """Handle GUI rendering for HeroAI panels"""
        from HeroAI.ui import draw_hero_panel, draw_dialog_overlay

        # Create windows and draw hero panels for each account
        for account in accounts:
            # Skip leader's own panel if ShowLeaderPanel is False
            is_own_panel = account.AccountEmail == cached_data.account_email
            if is_own_panel and custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader() and not settings.ShowLeaderPanel:
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
        
        draw_dialog_overlay(cached_data, messages)
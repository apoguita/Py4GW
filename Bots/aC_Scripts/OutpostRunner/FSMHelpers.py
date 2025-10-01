from Py4GWCoreLib import *
from OutpostRunner.map_loader import load_map_data
from Py4GW_widget_manager import handler

cached_enabled_widgets = []  # cache for later restore

MyList = [
    "Skip Cinematics",
    "Titles",
    "Environment Upkeeper",
    "Messaging"
]

class OutpostRunnerFSMHelpers:
    def __init__(self):
        self.current_map_script = None
        self.current_map_data = None
        self.current_path_index = 0
        self.last_valid_next_point = None

    def load_map_script(self, script_name):
        """
        Given a chain entry like:
            "Eye_Of_The_North__1_Eotn_To_Gunnars"
        (note the DOUBLE-underscore between region and run),
        split it properly and delegate to map_loader.
        """
        # split on the double-underscore delimiter
        if "__" in script_name:
            region, run = script_name.split("__", 1)
        else:
            # fallback (shouldn't happen with our UI)
            region, run = script_name.split("_", 1)

        # now load the Python file at maps/<region>/<run>.py
        data = load_map_data(region, run)
        self.current_map_data = data
        return {
            "outpost_path":     data["outpost_path"],
            "segments":         data["segments"],
            "ids":              data["ids"],
        }

    @staticmethod
    def travel_to_outpost(outpost_id):
        if GLOBAL_CACHE.Map.GetMapID() == outpost_id:
            ConsoleLog("OutpostRunnerFSM", "Already at outpost. Skipping travel.", Console.MessageType.Info)
            return

        ConsoleLog("OutpostRunnerFSM", f"Initiating safe travel to outpost ID {outpost_id}")
        if GLOBAL_CACHE.Map.IsExplorable():
            # === STEP 1: Broadcast resign command to other accounts ===
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
            for account in accounts:
                ConsoleLog("OutpostRunnerFSM", f"Resigning account: {account.AccountEmail}")
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0, 0, 0, 0))
            # === STEP 2: Wait for defeat to trigger Return To Outpost ===
            timeout = 20
            start_time = time.time()

            while time.time() - start_time < timeout:
                if (GLOBAL_CACHE.Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded() and GLOBAL_CACHE.Map.IsExplorable() and GLOBAL_CACHE.Party.IsPartyDefeated()):
                    GLOBAL_CACHE.Party.ReturnToOutpost()
                    break

                yield from Routines.Yield.wait(500)
            else:
                ConsoleLog("OutpostRunnerFSM", "Resign return timed out. Stopping bot.", Console.MessageType.Error)
                return

            # === STEP 3: Wait for outpost map to load ===
            timeout = 20
            start_time = time.time()

            while time.time() - start_time < timeout:
                if Routines.Checks.Map.MapValid() and GLOBAL_CACHE.Map.IsOutpost():
                    ConsoleLog("OutpostRunnerFSM", "Returned to outpost. Proceeding to travel...")
                    break

                yield from Routines.Yield.wait(500)
            else:
                ConsoleLog("OutpostRunnerFSM", "Failed to load outpost. Aborting travel.", Console.MessageType.Error)
                return

        # === STEP 4: Perform actual outpost travel ===
        ConsoleLog("OutpostRunnerFSM", f"Traveling to outpost ID {outpost_id}")
        yield from Routines.Yield.Map.TravelToOutpost(outpost_id)

    def wait_for_map_load(self, expected_map_id, timeout=15000):
        """Wait until we’re in the expected map."""
        return Routines.Yield.Map.WaitforMapLoad(expected_map_id, timeout=timeout)

    def follow_path(self, path_coords):
        """Use the official Yield.Path interface but update current_path_index and last_valid_next_point for UI + skills."""
        
        def progress_cb(progress):
            idx = int(progress * len(path_coords))
            self.current_path_index = idx + 1
            
            if len(path_coords) > 0:
                safe_idx = min(self.current_path_index, len(path_coords)-1)
                self.last_valid_next_point = path_coords[safe_idx]
        
        if path_coords:
            self.last_valid_next_point = path_coords[0]
        
        return Routines.Yield.Movement.FollowPath(path_coords, progress_callback=progress_cb)
    
    def get_next_path_point(self):
        """Returns the current active path point based on progress."""
        if not self.current_map_data:
            return self.last_valid_next_point
        
        # Merge all paths for current map
        all_points = []
        if self.current_map_data.get("outpost_path"):
            all_points.extend(self.current_map_data["outpost_path"])
        if self.current_map_data.get("segments"):
            for seg in self.current_map_data["segments"]:
                all_points.extend(seg.get("path", []))

        # Clamp index in case we reach the end
        idx = min(self.current_path_index, len(all_points) - 1)
        if idx >= 0 and idx < len(all_points):
            self.last_valid_next_point = all_points[idx]
            return all_points[idx]

        return self.last_valid_next_point
    
    def enable_custom_widget_list(self):
        """Enable only the widgets in ALWAYS_ENABLE_WIDGETS list."""
        for widget_name in MyList:
            handler.enable_widget(widget_name)
            ConsoleLog("WidgetHandler", f"'{widget_name}' is Enabled", Console.MessageType.Info)

    def cache_and_disable_all_widgets(self):
        global cached_enabled_widgets
        cached_enabled_widgets = handler.list_enabled_widgets()  # ✅ only enabled ones
        ConsoleLog("WidgetHandler", f"Currently enabled widgets: {cached_enabled_widgets}", Console.MessageType.Debug)

        # Disable all
        for widget_name in cached_enabled_widgets:
            handler.disable_widget(widget_name)
        ConsoleLog("WidgetHandler", f"Disabled {len(cached_enabled_widgets)} widgets", Console.MessageType.Info)


    def restore_cached_widgets(self):
        global cached_enabled_widgets
        if not cached_enabled_widgets:
            ConsoleLog("WidgetHandler", "No cached widgets to restore!", Console.MessageType.Warning)
            return

        for widget_name in cached_enabled_widgets:
            handler.enable_widget(widget_name)

        ConsoleLog("WidgetHandler", f"Restored {len(cached_enabled_widgets)} widgets", Console.MessageType.Info)
        cached_enabled_widgets = []  # clear after restore
import re
import difflib
import time
import csv
import os
import shutil
import json
import datetime
from typing import Any
import PyInventory
from Py4GWCoreLib.Item import Item
from Py4GWCoreLib.ItemArray import ItemArray
from Sources.oazix.CustomBehaviors.primitives import constants
from Py4GWCoreLib import * # Includes Map, Player

class DropViewerWindow:
    def __init__(self):
        self.window_name = "Drop Tracker Viewer"
        self.log_path = constants.DROP_LOG_PATH
        self.saved_logs_dir = os.path.join(os.path.dirname(constants.DROP_LOG_PATH), "SavedLogs")
        
        # Data
        self.raw_drops = []
        self.aggregated_drops = {} # Key: ItemName, Value: {Quantity, Rarity, Count}
        self.total_drops = 0
        
        # State
        self.last_read_time = 0
        self.auto_scroll = True
        self.view_mode = "Aggregated" # "Log", "Aggregated"
        self.show_save_popup = False
        self.save_filename = "Run_001"
        self.status_message = ""
        self.status_time = 0
        
        # Logging State
        self.last_processed_message = None
        self.last_update_time = 0
        self.chat_requested = False
        self.last_chat_index = -1
        
        # Regex matches: "[Timestamp] Player picks up [Quantity] <Color>ItemName</Color>."
        self.pickup_regex = re.compile(
            r"^(?:\[([\d: ]+[ap]m)\] )?(?:<c=#(?:[A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})>)?(You|.+?)(?:<\/c>)? (?:picks? up) (?:the )?(?:(\d+) )?(?:<c=#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})>)?(.+?)(?:<\/c>)?\.?$"
        )
        
        # Regex matches: "Monster drops [a/an/the] <Color>ItemName</Color>..."
        # Captures: 1=Monster, 2=ColorHex, 3=ItemName
        self.drop_regex = re.compile(
            r"^(?:\[([\d: ]+[ap]m)\] )?(?:<c=#(?:[A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})>)?(.+?)(?:<\/c>)? drops (?:an?|the)?\s*(?:<c=#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})>)?(.+?)(?:<\/c>)?(?:, which your party reserves for .+)?\.?$"
        )
        
        self.gold_regex = re.compile(r"^(?:\[([\d: ]+[ap]m)\] )?Your party shares ([\d,]+) gold\.$")
        
        self.last_auto_refresh_time = 0
        self.paused = False
        self.shmem_bootstrap_done = False
        self.player_name = "Unknown"
        self.recent_log_cache = {}
        self.enable_chat_item_tracking = False
        self.max_shmem_messages_per_tick = 25
        self.verbose_shmem_item_logs = False

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        os.makedirs(self.saved_logs_dir, exist_ok=True)

        # Always start each run with a fresh live log file + empty runtime data.
        self._reset_live_session()

    def _ensure_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="ignore")
            except Exception:
                return ""
        return str(value)

    def _strip_tags(self, text: Any) -> str:
        return re.sub(r"<[^>]+>", "", self._ensure_text(text))

    def _clean_item_name(self, name: Any) -> str:
        cleaned = self._strip_tags(name).strip()
        cleaned = re.sub(r"^[\d,]+\s+", "", cleaned)
        return cleaned

    def _normalize_item_name(self, name: Any) -> str:
        return self._clean_item_name(name).lower()

    def _normalize_rarity_label(self, item_name: Any, rarity: Any) -> str:
        name = self._clean_item_name(item_name)
        r = self._ensure_text(rarity).strip() or "Unknown"
        # Canonical buckets override color rarities.
        if "Key" in name:
            return "Keys"
        if "Vial of Dye" in name or "Dye" in name:
            return "Dyes"
        if "Tome" in name:
            return "Tomes"
        return r

    def _reset_live_log_file(self):
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "ViewerBot", "MapID", "MapName", "Player", "ItemName", "Quantity", "Rarity"])
            self.last_read_time = os.path.getmtime(self.log_path)
        except Exception as e:
            Py4GW.Console.Log("DropViewer", f"Failed to reset live log file: {e}", Py4GW.Console.MessageType.Warning)

    def _reset_live_session(self):
        self.raw_drops = []
        self.aggregated_drops = {}
        self.total_drops = 0
        self.shmem_bootstrap_done = False
        self.last_read_time = 0
        self.recent_log_cache = {}
        self._reset_live_log_file()

    def load_drops(self):
        if not os.path.isfile(self.log_path):
            self.raw_drops = []
            self.aggregated_drops = {}
            self.total_drops = 0
            return

        try:
            current_mtime = os.path.getmtime(self.log_path)
            if current_mtime <= self.last_read_time:
                return # No change
            
            self.last_read_time = current_mtime
            
            self._parse_log_file(self.log_path)
            
        except Exception as e:
            self.set_status(f"Error reading log: {e}")

    def _parse_log_file(self, filepath):
        temp_drops = []
        temp_agg = {}
        total = 0
        
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None) # Skip header
            
            has_map_name = False
            if header and "MapName" in header:
                has_map_name = True

            for row in reader:
                # Basic validation
                if len(row) < 7: continue 
                
                if has_map_name:
                    # New Format
                    timestamp, bot, map_id, map_name, player, item_name, quantity_str, rarity = row[:8]
                else:
                    # Old Format
                    timestamp, bot, map_id, player, item_name, quantity_str, rarity = row[:7]
                    map_name = "Unknown"
                    try:
                         mid = int(map_id)
                         map_name = Map.GetMapName(mid)
                    except: pass
                    
                    row.insert(3, map_name) # Insert MapName at index 3
                
                quantity = 1
                try: quantity = int(quantity_str)
                except: pass
                
                temp_drops.append(row)
                total += quantity
                
                key = (item_name, rarity)
                if key not in temp_agg:
                    temp_agg[key] = {"Quantity": 0, "Count": 0}
                
                temp_agg[key]["Quantity"] += quantity
                temp_agg[key]["Count"] += 1
                
        self.raw_drops = temp_drops
        self.aggregated_drops = temp_agg
        self.total_drops = total

    def set_status(self, msg):
        self.status_message = msg
        self.status_time = time.time()

    def save_run(self):
        if not os.path.exists(self.saved_logs_dir):
            os.makedirs(self.saved_logs_dir)
            
        target = os.path.join(self.saved_logs_dir, f"{self.save_filename}.csv")
        try:
            shutil.copy2(self.log_path, target)
            self.set_status(f"Saved to {self.save_filename}.csv")
            self.show_save_popup = False
        except Exception as e:
            self.set_status(f"Save failed: {e}")

    def load_run(self, filename):
        target = os.path.join(self.saved_logs_dir, filename)
        if not os.path.exists(target): return
        
        self.paused = True
        try:
            self._parse_log_file(target)
            self.set_status(f"Loaded {filename}")
        except Exception as e:
            self.set_status(f"Load failed: {e}")

    def merge_run(self, filename):
        target = os.path.join(self.saved_logs_dir, filename)
        if not os.path.exists(target): return
        
        self.paused = True
        
        temp_agg = self.aggregated_drops.copy()
        temp_drops = list(self.raw_drops)
        total = self.total_drops
        
        try:
             with open(target, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                has_map_name = header and "MapName" in header
                
                for row in reader:
                    if len(row) < 7: continue
                    
                    if has_map_name:
                         item_name = row[5]
                         quantity_str = row[6]
                         rarity = row[7]
                    else:
                         item_name = row[4]
                         quantity_str = row[5]
                         rarity = row[6]
                         # Patch row for raw view
                         mid = int(row[2]) if row[2].isdigit() else 0
                         mname = Map.GetMapName(mid)
                         row.insert(3, mname)

                    quantity = int(quantity_str) if quantity_str.isdigit() else 1
                    
                    temp_drops.append(row)
                    total += quantity
                    
                    key = (item_name, rarity)
                    if key not in temp_agg:
                        temp_agg[key] = {"Quantity": 0, "Count": 0}
                    temp_agg[key]["Quantity"] += quantity
                    temp_agg[key]["Count"] += 1
            
             self.raw_drops = temp_drops
             self.aggregated_drops = temp_agg
             self.total_drops = total
             self.set_status(f"Merged {filename}")
             
        except Exception as e:
            self.set_status(f"Merge failed: {e}")

    def draw(self):
        if PyImGui.begin(self.window_name):
            
            # -- Auto Refresh --
            current_time = time.time()
            if not self.paused and current_time - self.last_auto_refresh_time > 1.0:
                 self.last_auto_refresh_time = current_time
                 self.load_drops()

            # -- Toolbar --
            if PyImGui.button("Refresh (Live)" if self.paused else "Refresh"):
                self.paused = False
                self.last_read_time = 0 
                self.load_drops() # Re-read main log
            
            PyImGui.same_line(0.0, 10.0)
            
            # View Mode Switch
            if self.view_mode == "Aggregated":
                if PyImGui.button("Show Logs"): self.view_mode = "Log"
            else:
                if PyImGui.button("Show Stats"): self.view_mode = "Aggregated"
                
            PyImGui.same_line(0.0, 10.0)
            
            if PyImGui.button("Save"):
                self.show_save_popup = not self.show_save_popup
                
            if self.show_save_popup:
                PyImGui.same_line(0.0, 10.0)
                PyImGui.push_item_width(100)
                self.save_filename = PyImGui.input_text("", self.save_filename)
                PyImGui.pop_item_width()
                PyImGui.same_line(0.0, 10.0)
                if PyImGui.button("OK"):
                    self.save_run()
            
            PyImGui.same_line(0.0, 10.0)
            
            # Load/Merge Logic
            if PyImGui.button("Load/Merge.."):
                PyImGui.open_popup("LoadMergePopup")

            if PyImGui.begin_popup("LoadMergePopup"):
                 if os.path.exists(self.saved_logs_dir):
                     files = [f for f in os.listdir(self.saved_logs_dir) if f.endswith(".csv")]
                     if not files:
                         PyImGui.text("No saved logs")
                     else:
                         for f in files:
                             if PyImGui.begin_menu(f):
                                 if PyImGui.menu_item("Load"):
                                     self.load_run(f)
                                 if PyImGui.menu_item("Merge"):
                                     self.merge_run(f)
                                 PyImGui.end_menu()
                 else:
                     PyImGui.text("Directory not found")
                 PyImGui.end_popup()


            PyImGui.same_line(0.0, 40.0)
            if PyImGui.button("Clear/Reset"):
                 try:
                    # Reset file + in-memory state to a clean live session.
                    self._reset_live_session()
                    
                    # Reset chat bookmark state to "from now".
                    self.last_chat_index = -1 
                    if Player.IsChatHistoryReady():
                         self.last_chat_index = len(Player.GetChatHistory())

                    self.set_status("Log Cleared")
                 except Exception as e:
                     Py4GW.Console.Log("DropViewer", f"Clear failed: {e}", Py4GW.Console.MessageType.Error)

            # -- Status Bar --
            if time.time() - self.status_time < 5:
                PyImGui.text_colored(self.status_message, (0.0, 1.0, 0.0, 1.0))

            PyImGui.separator()
            
            # -- Main Content --
            if self.view_mode == "Aggregated":
                self._draw_aggregated()
            else:
                self._draw_log()

        PyImGui.end()
        
    def _draw_aggregated(self):
        total_items_without_gold = self.total_drops
        
        gold_qty = 0
        for (name, rar), data in self.aggregated_drops.items():
            if name == "Gold":
                gold_qty += data["Quantity"]
        
        total_items_without_gold -= gold_qty

        PyImGui.text(f"Total Items: {total_items_without_gold}")
        
        if PyImGui.begin_table("AggTable", 5, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.Resizable | PyImGui.TableFlags.Sortable):
            PyImGui.table_setup_column("Item Name")
            PyImGui.table_setup_column("Quantity")
            PyImGui.table_setup_column("%")
            PyImGui.table_setup_column("Rarity")
            PyImGui.table_setup_column("Count") 
            PyImGui.table_headers_row()
            
            # Sort by Item Name then Rarity
            display_items = list(self.aggregated_drops.items())
            
            sorted_items = sorted(display_items, key=lambda x: (x[0][0], x[0][1]))
            
            for (item_name, rarity), data in sorted_items:
                PyImGui.table_next_row()
                
                qty = data["Quantity"]
                
                if item_name == "Gold":
                    pct_str = "---"
                else:
                    pct = (qty / total_items_without_gold * 100) if total_items_without_gold > 0 else 0
                    pct_str = f"{pct:.1f}%"
                
                # Get Color
                r, g, b, a = self._get_rarity_color(rarity)

                PyImGui.table_set_column_index(0)
                PyImGui.text_colored(item_name, (r, g, b, a))
                
                PyImGui.table_set_column_index(1)
                PyImGui.text(str(qty))
                
                PyImGui.table_set_column_index(2)
                PyImGui.text(pct_str)
                
                PyImGui.table_set_column_index(3)
                PyImGui.text_colored(rarity, (r, g, b, a))
                
                PyImGui.table_set_column_index(4)
                PyImGui.text(str(data["Count"]))
                
            PyImGui.end_table()

    def _draw_log(self):
        self.auto_scroll = PyImGui.checkbox("Auto Scroll", self.auto_scroll)
        
        if PyImGui.begin_table("DropsLogTable", 8, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.Resizable | PyImGui.TableFlags.ScrollY):
            PyImGui.table_setup_column("Timestamp")
            PyImGui.table_setup_column("Logger")     
            PyImGui.table_setup_column("MapID")
            PyImGui.table_setup_column("MapName")
            PyImGui.table_setup_column("Player")     
            PyImGui.table_setup_column("Item")
            PyImGui.table_setup_column("Qty")
            PyImGui.table_setup_column("Rarity")
            PyImGui.table_headers_row()

            for row in self.raw_drops:
                PyImGui.table_next_row()
                rarity = row[7] if len(row) > 7 else "Unknown"
                r, g, b, a = self._get_rarity_color(rarity)

                for i, col in enumerate(row):
                    if i >= 8: break
                    PyImGui.table_set_column_index(i)
                    
                    if i == 5 or i == 7:
                        PyImGui.text_colored(str(col), (r, g, b, a))
                    else:
                        PyImGui.text(str(col))

            if self.auto_scroll:
                PyImGui.set_scroll_here_y(1.0)

            PyImGui.end_table()

    def update(self):
        # Only run every 3 seconds? No, 0.5s is fine for response
        now = time.time()
        if now - self.last_update_time < 0.5:
            return
        self.last_update_time = now

        try:
            # Poll shared memory reliably every tick
            self._poll_shared_memory()

            if self.player_name == "Unknown":
                try:
                    self.player_name = Player.GetName()
                except: pass

            # Step 1: Request chat history for Gold tracking ONLY
            if not self.chat_requested:
                Player.player_instance().RequestChatHistory()
                self.chat_requested = True
                return

            if not Player.IsChatHistoryReady():
                return

            chat_history = Player.GetChatHistory()
            self.chat_requested = False
            
            if not chat_history:
                return

            current_len = len(chat_history)
            
            # First run
            if self.last_chat_index < 0:
                self.last_chat_index = current_len
                return

            # Buffer wrapped
            if current_len < self.last_chat_index:
                self.last_chat_index = 0

            # Process only NEW messages
            new_messages = []
            if current_len > self.last_chat_index:
                new_messages = chat_history[self.last_chat_index:]
                self.last_chat_index = current_len

            # Check for chat events
            for msg in new_messages:
                self._process_chat_message(msg)

        except Exception as e:
            Py4GW.Console.Log("DropViewer", f"Update error: {e}", Py4GW.Console.MessageType.Error)

    def _process_chat_message(self, msg: Any):
        text = self._ensure_text(msg)

        # Gold tracking: keep leader-only guard to avoid party-wide duplicates.
        match_gold = self.gold_regex.search(text)
        if match_gold:
            try:
                my_id = Player.GetAgentID()
                leader_id = Party.GetPartyLeaderID()
                if my_id == leader_id:
                    amount = int(match_gold.group(2).replace(',', ''))
                    self._log_drop_to_file(Player.GetName(), "Gold", amount, "Currency")
                    Py4GW.Console.Log("DropViewer", f"TRACKED: Gold x{amount}", Py4GW.Console.MessageType.Info)
            except Exception:
                pass
            return

        if not self.enable_chat_item_tracking:
            return

        # Item pickup tracking from chat:
        # Examples:
        # - "Trovacica Dusa picks up the Summit Axe."
        # - "Mesmer Cetiri picks up 2 Stone Summit Badge."
        match_pickup = self.pickup_regex.search(text)
        if not match_pickup:
            return

        player_name = self._strip_tags(match_pickup.group(2)).strip() if match_pickup.group(2) else "Unknown"
        quantity_text = match_pickup.group(3)
        color_hex = match_pickup.group(4)
        item_name = self._clean_item_name(match_pickup.group(5) if match_pickup.group(5) else "Unknown Item")

        quantity = 1
        if quantity_text and quantity_text.isdigit():
            quantity = int(quantity_text)

        rarity = self._get_rarity_from_color_hex(color_hex) if color_hex else "Unknown"
        if not self._is_recent_duplicate(player_name, item_name, quantity):
            self._log_drop_to_file(player_name, item_name, quantity, rarity)
            Py4GW.Console.Log(
                "DropViewer",
                f"TRACKED CHAT: {item_name} x{quantity} ({rarity}) [{player_name}]",
                Py4GW.Console.MessageType.Info
            )

    def _poll_shared_memory(self):
        def _c_wchar_array_to_str(arr) -> str:
            return "".join(ch for ch in arr if ch != '\0').rstrip()
        
        def _normalize_shmem_text(value: Any) -> str:
            if value is None:
                return ""
            # c_wchar arrays are iterable and need explicit conversion.
            if not isinstance(value, str) and hasattr(value, "__iter__"):
                try:
                    return _c_wchar_array_to_str(value)
                except Exception:
                    pass
            return str(value).strip()
            
        try:
            my_email = Player.GetAccountEmail()
            if not my_email: return

            # Only leader client should ingest TrackerDrop messages into the shared CSV.
            try:
                if Player.GetAgentID() != Party.GetPartyLeaderID():
                    return
            except Exception:
                return

            # Use core global cache directly; Py4GW module may not expose GLOBAL_CACHE.
            shmem = getattr(GLOBAL_CACHE, "ShMem", None)
            if shmem is None:
                return

            # DropViewer must never clear global message queues on startup.
            self.shmem_bootstrap_done = True
            
            # Get ALL active messages and filter for ours
            messages = shmem.GetAllMessages()
            processed_tracker_msgs = 0
            batch_rows = []
            batch_logged_count = 0

            for msg_idx, shared_msg in messages:
                if processed_tracker_msgs >= self.max_shmem_messages_per_tick:
                    break
                receiver_email = _normalize_shmem_text(getattr(shared_msg, "ReceiverEmail", ""))
                if receiver_email != my_email:
                    continue
                    
                command_value = int(getattr(shared_msg, "Command", 0))
                expected_custom_behavior_command = 997
                try:
                    expected_custom_behavior_command = int(SharedCommandType.CustomBehaviors.value)
                except Exception:
                    pass
                if command_value != expected_custom_behavior_command and command_value != 997:
                    continue
                    
                is_tracker_message = False
                try:
                    extra_data_list = shared_msg.ExtraData
                    if len(extra_data_list) == 0:
                        continue
                        
                    extra_0 = _c_wchar_array_to_str(extra_data_list[0])
                    if extra_0 != "TrackerDrop":
                        # Do not consume messages owned by other subsystems.
                        continue
                    
                    is_tracker_message = True

                    item_name = _c_wchar_array_to_str(extra_data_list[1]) if len(extra_data_list) > 1 else "Unknown Item"
                    exact_rarity = _c_wchar_array_to_str(extra_data_list[2]) if len(extra_data_list) > 2 else "Unknown"
                    display_time = _c_wchar_array_to_str(extra_data_list[3]) if len(extra_data_list) > 3 else ""
                    exact_rarity = self._normalize_rarity_label(item_name, exact_rarity)


                    quantity_param = shared_msg.Params[0] if len(shared_msg.Params) > 0 else 0
                    quantity = int(round(quantity_param)) if quantity_param > 0 else 1

                    sender_email = _normalize_shmem_text(getattr(shared_msg, "SenderEmail", ""))
                    sender_name = "Follower"
                    # Resolve sender name
                    sender_account = shmem.GetAccountDataFromEmail(sender_email)
                    if sender_account:
                        sender_name = sender_account.AgentData.CharacterName

                    if not self._is_recent_duplicate(sender_name, item_name, quantity):
                        batch_rows.append((
                            sender_name,
                            item_name,
                            quantity,
                            exact_rarity,
                            display_time if display_time else None
                        ))
                        if self.verbose_shmem_item_logs and batch_logged_count < 5:
                            log_msg = f"TRACKED: {item_name} x{quantity} ({exact_rarity}) [{sender_name}] (ShMem)"
                            Py4GW.Console.Log("DropViewer", log_msg, Py4GW.Console.MessageType.Info)
                            batch_logged_count += 1

                    # Mark it finished so it's not processed again
                    shmem.MarkMessageAsFinished(my_email, msg_idx)
                    processed_tracker_msgs += 1
                except Exception as msg_e:
                    Py4GW.Console.Log("DropViewer", f"Error parsing ShMem msg: {msg_e}", Py4GW.Console.MessageType.Warning)
                    if is_tracker_message:
                        shmem.MarkMessageAsFinished(my_email, msg_idx)
                    continue

            if batch_rows:
                self._log_drops_batch(batch_rows)
                Py4GW.Console.Log(
                    "DropViewer",
                    f"TRACKED BATCH: {len(batch_rows)} items (ShMem)",
                    Py4GW.Console.MessageType.Info
                )
        except Exception as e:
            pass # ShMem might not be ready

    def _is_recent_duplicate(self, player_name, item_name, quantity, window_seconds=1.5):
        now = time.time()
        # Keep only very recent keys to avoid suppressing legitimate repeated loots.
        self.recent_log_cache = {
            key: ts for key, ts in self.recent_log_cache.items()
            if now - ts <= window_seconds
        }

        key = (str(player_name), str(item_name), int(quantity))
        previous = self.recent_log_cache.get(key)
        if previous is not None and (now - previous) <= window_seconds:
            return True

        self.recent_log_cache[key] = now
        return False

    def _get_rarity_from_color_hex(self, hex_code):
        code = (hex_code or "").upper()
        if len(code) == 8:
            code = code[-6:]
        if code == "FFFFFF": return "White"
        if code in ["0000FF", "8080FF", "00FFFF", "1010FF"]: return "Blue"
        if code in ["800080", "A020F0", "CC00CC", "990099"]: return "Purple"
        if code in ["FFD700", "FFFF00", "D9C330", "D4AF37"]: return "Gold"
        if code in ["00FF00", "00CC00", "008000"]: return "Green"
        
        Py4GW.Console.Log("RarityDebug", f"Unknown Color Hex: {code}", Py4GW.Console.MessageType.Warning)
        return "Unknown (Color)"

    def _get_inventory_snapshot(self):
        snapshot = {}
        try:
             bags = ItemArray.CreateBagList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
             items = ItemArray.GetItemArray(bags)
             for item_id in items:
                 is_stackable = Item.Customization.IsStackable(item_id)
                 is_weapon = Item.Type.IsWeapon(item_id)
                 is_armor = Item.Type.IsArmor(item_id)
                 
                 name = self._ensure_text(Item.GetName(item_id))
                 
                 if not name or not Item.IsNameReady(item_id):
                     Item.RequestName(item_id)
                     rarity = "Unknown" 
                 else:
                     clean_name = self._clean_item_name(name)
                     rarity = Item.Rarity.GetRarity(item_id)[1]
                     
                     if Item.Type.IsTome(item_id): rarity = "Tomes"
                     elif "Dye" in clean_name or "Vial of Dye" in clean_name: rarity = "Dyes"
                     elif "Key" in clean_name: rarity = "Keys"
                     elif Item.Type.IsMaterial(item_id) or Item.Type.IsRareMaterial(item_id): rarity = "Material"
                     
                     name = clean_name
                 
                 snapshot[item_id] = (name, rarity, is_stackable, is_weapon, is_armor)
        except Exception as e:
             Py4GW.Console.Log("RarityDebug", f"Snapshot Error: {e}", Py4GW.Console.MessageType.Error)
        return snapshot

    def _log_drop_to_file(self, player_name, item_name, quantity, extra_info, timestamp_override=None):
        self._log_drops_batch([(player_name, item_name, quantity, extra_info, timestamp_override)])

    def _log_drops_batch(self, entries):
        try:
            bot_name = Player.GetName()
            map_id = Map.GetMapID()
            map_name = Map.GetMapName(map_id)

            # Write to CSV
            file_exists = os.path.isfile(self.log_path)
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

            with open(self.log_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Timestamp", "ViewerBot", "MapID", "MapName", "Player", "ItemName", "Quantity", "Rarity"])

                for player_name, item_name, quantity, extra_info, timestamp_override in entries:
                    timestamp = timestamp_override if timestamp_override else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    rarity = self._normalize_rarity_label(item_name, extra_info if extra_info else "Unknown")
                    qty = int(quantity) if quantity else 1
                    if qty < 1:
                        qty = 1
                    writer.writerow([timestamp, bot_name, map_id, map_name, player_name, item_name, qty, rarity])

                    # --- Update In-Memory Data ---
                    row = [timestamp, bot_name, str(map_id), map_name, player_name, item_name, str(qty), rarity]
                    self.raw_drops.append(row)
                    self.total_drops += qty

                    key = (item_name, rarity)
                    if key not in self.aggregated_drops:
                        self.aggregated_drops[key] = {"Quantity": 0, "Count": 0}

                    self.aggregated_drops[key]["Quantity"] += qty
                    self.aggregated_drops[key]["Count"] += 1

            self.last_read_time = os.path.getmtime(self.log_path) if os.path.exists(self.log_path) else time.time()

        except Exception as e:
            print(f"Log Error: {e}")

    def _get_rarity_color(self, rarity):
        col = (1.0, 1.0, 1.0, 1.0)
        
        if rarity == "Blue": col = (0.0, 0.8, 1.0, 1.0)
        elif rarity == "Purple": col = (0.8, 0.4, 1.0, 1.0)
        elif rarity == "Gold": col = (1.0, 0.84, 0.0, 1.0)
        elif rarity == "Green": col = (0.0, 1.0, 0.0, 1.0) 
        elif rarity == "Dyes": col = (1.0, 0.6, 0.8, 1.0) 
        elif rarity == "Keys": col = (0.8, 0.8, 0.8, 1.0) 
        elif rarity == "Tomes": col = (0.0, 0.8, 0.0, 1.0) 
        elif rarity == "Currency": col = (1.0, 1.0, 0.0, 1.0)
        elif rarity == "Unknown": col = (0.5, 0.5, 0.5, 1.0) 
        elif rarity == "...": col = (0.5, 0.5, 0.5, 1.0) 
        
        return col

drop_viewer = DropViewerWindow()

def main():
    pass

def draw_window():
    drop_viewer.update()    
    if not drop_viewer.paused:
        drop_viewer.load_drops()
    drop_viewer.draw()

def update():
    drop_viewer.update()

if __name__ == "__main__":
    pass

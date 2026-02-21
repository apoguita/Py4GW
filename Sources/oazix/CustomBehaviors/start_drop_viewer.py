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
from Sources.oazix.CustomBehaviors.PathLocator import PathLocator
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import (
    decode_name_chunk_meta,
    parse_drop_meta,
)
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
        self.max_shmem_messages_per_tick = 80
        self.max_shmem_scan_per_tick = 600
        self.verbose_shmem_item_logs = False
        self.send_tracker_ack_enabled = True
        self.enable_perf_logs = False
        self.seen_event_ttl_seconds = 900.0
        self.seen_events = {}
        self.name_chunk_buffers = {}
        self.full_name_by_signature = {}
        self.last_shmem_poll_ms = 0.0
        self.last_shmem_processed = 0
        self.last_shmem_scanned = 0
        self.last_ack_sent = 0
        self.perf_timer = ThrottledTimer(5000)
        self.config_poll_timer = ThrottledTimer(2000)
        self.runtime_config_path = os.path.join(os.path.dirname(constants.DROP_LOG_PATH), "drop_tracker_runtime_config.json")
        self.runtime_config = self._default_runtime_config()
        self.runtime_config_dirty = False

        # Fancy/friendly UI state
        self.search_text = ""
        self.filter_player = ""
        self.filter_map = ""
        self.filter_rarity_idx = 0
        self.filter_rarity_options = [
            "All", "Blue", "Purple", "Gold", "Green",
            "Dyes", "Keys", "Tomes", "Currency", "Unknown"
        ]
        self.only_rare = False
        self.hide_gold = False
        self.min_qty = 1
        self.show_runtime_panel = False
        self.selected_item_key = None
        self.hover_handle_mode = True
        self.hover_pin_open = False
        self.hover_is_visible = True
        self.hover_hide_delay_s = 0.35
        self.hover_hide_deadline = 0.0
        self.hover_icon_path = PathLocator.get_custom_behaviors_root_directory() + "\\gui\\textures\\loot.png"
        self.hover_handle_initialized = False
        self.viewer_window_initialized = False
        self.saved_hover_handle_pos = None
        self.saved_viewer_window_pos = None
        self.saved_viewer_window_size = None
        self.layout_save_timer = ThrottledTimer(750)

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        os.makedirs(self.saved_logs_dir, exist_ok=True)

        self._load_runtime_config()
        self._load_ui_layout_from_config()
        # Always start each run with a fresh live log file + empty runtime data.
        self._reset_live_session()

    def _default_runtime_config(self):
        return {
            "debug_pipeline_logs": False,
            "enable_perf_logs": False,
            "enable_delivery_ack": True,
            "max_send_per_tick": 12,
            "max_outbox_size": 2000,
            "retry_interval_seconds": 1.0,
            "max_retry_attempts": 12,
            "verbose_shmem_item_logs": False,
            "max_shmem_messages_per_tick": 80,
            "max_shmem_scan_per_tick": 600,
            "send_tracker_ack_enabled": True,
        }

    def _apply_runtime_config(self):
        cfg = self.runtime_config if isinstance(self.runtime_config, dict) else self._default_runtime_config()
        self.verbose_shmem_item_logs = bool(cfg.get("verbose_shmem_item_logs", self.verbose_shmem_item_logs))
        self.max_shmem_messages_per_tick = max(5, int(cfg.get("max_shmem_messages_per_tick", self.max_shmem_messages_per_tick)))
        self.max_shmem_scan_per_tick = max(20, int(cfg.get("max_shmem_scan_per_tick", self.max_shmem_scan_per_tick)))
        self.send_tracker_ack_enabled = bool(cfg.get("send_tracker_ack_enabled", self.send_tracker_ack_enabled))
        self.enable_perf_logs = bool(cfg.get("enable_perf_logs", self.enable_perf_logs))

    def _load_ui_layout_from_config(self):
        cfg = self.runtime_config if isinstance(self.runtime_config, dict) else {}
        try:
            pos = cfg.get("drop_viewer_handle_pos", None)
            if isinstance(pos, list) and len(pos) == 2:
                self.saved_hover_handle_pos = (float(pos[0]), float(pos[1]))
        except Exception:
            self.saved_hover_handle_pos = None
        try:
            pos = cfg.get("drop_viewer_window_pos", None)
            if isinstance(pos, list) and len(pos) == 2:
                self.saved_viewer_window_pos = (float(pos[0]), float(pos[1]))
        except Exception:
            self.saved_viewer_window_pos = None
        try:
            size = cfg.get("drop_viewer_window_size", None)
            if isinstance(size, list) and len(size) == 2:
                self.saved_viewer_window_size = (float(size[0]), float(size[1]))
        except Exception:
            self.saved_viewer_window_size = None

    def _persist_layout_value(self, key: str, value: tuple[float, float] | None):
        if value is None:
            return False
        current = self.runtime_config.get(key, None) if isinstance(self.runtime_config, dict) else None
        next_value = [float(value[0]), float(value[1])]
        if isinstance(current, list) and len(current) == 2:
            try:
                if abs(float(current[0]) - next_value[0]) < 0.5 and abs(float(current[1]) - next_value[1]) < 0.5:
                    return False
            except Exception:
                pass
        self.runtime_config[key] = next_value
        self.runtime_config_dirty = True
        return True

    def _flush_runtime_config_if_dirty(self):
        if not self.runtime_config_dirty:
            return
        if not self.layout_save_timer.IsExpired():
            return
        self.layout_save_timer.Reset()
        self._sync_runtime_config_from_state()
        self._save_runtime_config()
        self.runtime_config_dirty = False

    def _load_runtime_config(self):
        try:
            if not os.path.exists(self.runtime_config_path):
                self.runtime_config = self._default_runtime_config()
                return
            with open(self.runtime_config_path, mode="r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                cfg = self._default_runtime_config()
                cfg.update(loaded)
                self.runtime_config = cfg
            else:
                self.runtime_config = self._default_runtime_config()
        except Exception:
            self.runtime_config = self._default_runtime_config()
        self._apply_runtime_config()

    def _save_runtime_config(self):
        try:
            os.makedirs(os.path.dirname(self.runtime_config_path), exist_ok=True)
            with open(self.runtime_config_path, mode="w", encoding="utf-8") as f:
                json.dump(self.runtime_config, f, indent=2)
        except Exception as e:
            Py4GW.Console.Log("DropViewer", f"Runtime config save failed: {e}", Py4GW.Console.MessageType.Warning)

    def _sync_runtime_config_from_state(self):
        cfg = self.runtime_config if isinstance(self.runtime_config, dict) else self._default_runtime_config()
        cfg["verbose_shmem_item_logs"] = bool(self.verbose_shmem_item_logs)
        cfg["max_shmem_messages_per_tick"] = int(self.max_shmem_messages_per_tick)
        cfg["max_shmem_scan_per_tick"] = int(self.max_shmem_scan_per_tick)
        cfg["send_tracker_ack_enabled"] = bool(self.send_tracker_ack_enabled)
        cfg["enable_perf_logs"] = bool(self.enable_perf_logs)
        self.runtime_config = cfg

    def _send_tracker_ack(self, receiver_email: str, event_id: str) -> bool:
        if not self.send_tracker_ack_enabled:
            return False
        event_id_text = (event_id or "").strip()
        if not receiver_email or not event_id_text:
            return False
        try:
            my_email = Player.GetAccountEmail()
            if not my_email:
                return False
            sent_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email=my_email,
                receiver_email=receiver_email,
                command=SharedCommandType.CustomBehaviors,
                params=(0.0, 0.0, 0.0, 0.0),
                ExtraData=("TrackerAckV2", event_id_text[:31], "", ""),
            )
            if sent_index != -1:
                self.last_ack_sent += 1
            return sent_index != -1
        except Exception:
            return False

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

    def _canonical_agg_item_name(self, item_name: Any, rarity: Any, agg: dict) -> str:
        name = self._clean_item_name(item_name)
        if not name:
            return "Unknown Item"
        if name == "Gold":
            return "Gold"

        rarity_text = self._ensure_text(rarity).strip() or "Unknown"
        lower_name = name.lower()
        singular = lower_name[:-1] if lower_name.endswith("s") and len(lower_name) > 1 else lower_name
        plural = singular + "s"

        for (existing_name, existing_rarity) in agg.keys():
            if self._ensure_text(existing_rarity).strip() != rarity_text:
                continue
            ex_lower = self._clean_item_name(existing_name).lower()
            if ex_lower == lower_name:
                return existing_name
            # Conservative singular/plural normalization for same-rarity rows.
            if ex_lower == singular or ex_lower == plural:
                return existing_name
        return name

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
                
                canonical_name = self._canonical_agg_item_name(item_name, rarity, temp_agg)
                key = (canonical_name, rarity)
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

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _is_rare_rarity(self, rarity):
        return rarity == "Gold"

    def _passes_filters(self, row):
        if len(row) < 8:
            return False

        player_name = self._ensure_text(row[4])
        item_name = self._ensure_text(row[5])
        qty = self._safe_int(row[6], 1)
        rarity = self._ensure_text(row[7]).strip() or "Unknown"
        map_name = self._ensure_text(row[3])

        if qty < max(1, int(self.min_qty)):
            return False
        if self.only_rare and not self._is_rare_rarity(rarity):
            return False
        if self.hide_gold and self._clean_item_name(item_name) == "Gold":
            return False
        if self.filter_rarity_idx > 0:
            wanted = self.filter_rarity_options[self.filter_rarity_idx]
            if wanted == "Unknown":
                if "Unknown" not in rarity:
                    return False
            elif rarity != wanted:
                return False

        search = self.search_text.strip().lower()
        if search:
            haystack = f"{item_name} {player_name} {map_name} {rarity}".lower()
            if search not in haystack:
                return False

        fp = self.filter_player.strip().lower()
        if fp and fp not in player_name.lower():
            return False

        fm = self.filter_map.strip().lower()
        if fm and fm not in map_name.lower():
            return False

        return True

    def _get_filtered_rows(self):
        return [row for row in self.raw_drops if self._passes_filters(row)]

    def _is_gold_row(self, row):
        if len(row) < 6:
            return False
        return self._clean_item_name(row[5]) == "Gold"

    def _get_filtered_aggregated(self, filtered_rows):
        agg = {}
        total_qty = 0
        for row in filtered_rows:
            if len(row) < 8:
                continue
            item_name = row[5]
            rarity = row[7]
            qty = self._safe_int(row[6], 1)
            total_qty += qty
            canonical_name = self._canonical_agg_item_name(item_name, rarity, agg)
            key = (canonical_name, rarity)
            if key not in agg:
                agg[key] = {"Quantity": 0, "Count": 0}
            agg[key]["Quantity"] += qty
            agg[key]["Count"] += 1
        return agg, total_qty

    def _get_session_duration_text(self):
        if len(self.raw_drops) < 2:
            return "00:00"
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            first_ts = datetime.datetime.strptime(self.raw_drops[0][0], fmt)
            last_ts = datetime.datetime.strptime(self.raw_drops[-1][0], fmt)
            total_seconds = max(0, int((last_ts - first_ts).total_seconds()))
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            return f"{minutes:02d}:{seconds:02d}"
        except Exception:
            return "--:--"

    def _draw_metric_card(self, card_id, title, value, accent_color):
        PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, (0.10, 0.12, 0.16, 0.85))
        if PyImGui.begin_child(card_id, size=(0, 52), border=True, flags=PyImGui.WindowFlags.NoFlag):
            PyImGui.text_colored(title, accent_color)
            PyImGui.text(value)
            PyImGui.end_child()
        PyImGui.pop_style_color(1)

    def _draw_summary_bar(self, filtered_rows):
        total_qty = 0
        rare_count = 0
        gold_qty = 0
        for row in filtered_rows:
            qty = self._safe_int(row[6], 1)
            total_qty += qty
            rarity = self._ensure_text(row[7]).strip() or "Unknown"
            if self._is_rare_rarity(rarity):
                rare_count += 1
            if self._clean_item_name(row[5]) == "Gold":
                gold_qty += qty

        session_time = self._get_session_duration_text()

        flags = PyImGui.TableFlags.SizingStretchSame
        if PyImGui.begin_table("DropViewerSummary", 4, flags):
            PyImGui.table_next_row()

            PyImGui.table_set_column_index(0)
            self._draw_metric_card("CardSession", "Session", session_time, (0.55, 0.85, 1.0, 1.0))
            PyImGui.table_set_column_index(1)
            self._draw_metric_card("CardDrops", "Total Drops", str(total_qty), (0.8, 0.9, 1.0, 1.0))
            PyImGui.table_set_column_index(2)
            self._draw_metric_card("CardGold", "Gold Value", f"{gold_qty:,}", (0.72, 0.72, 0.72, 1.0))
            PyImGui.table_set_column_index(3)
            self._draw_metric_card("CardRare", "Rare Drops", str(rare_count), (1.0, 0.84, 0.0, 1.0))

            PyImGui.end_table()

    def _draw_runtime_controls(self):
        PyImGui.text("Runtime")
        if PyImGui.button(f"Verbose Logs: {'ON' if self.verbose_shmem_item_logs else 'OFF'}"):
            self.verbose_shmem_item_logs = not self.verbose_shmem_item_logs
            self.runtime_config_dirty = True
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button(f"ACK: {'ON' if self.send_tracker_ack_enabled else 'OFF'}"):
            self.send_tracker_ack_enabled = not self.send_tracker_ack_enabled
            self.runtime_config_dirty = True
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button(f"Perf Logs: {'ON' if self.enable_perf_logs else 'OFF'}"):
            self.enable_perf_logs = not self.enable_perf_logs
            self.runtime_config_dirty = True

        sender_debug_logs = bool(self.runtime_config.get("debug_pipeline_logs", False))
        sender_ack = bool(self.runtime_config.get("enable_delivery_ack", True))
        sender_max_send = int(self.runtime_config.get("max_send_per_tick", 12))
        sender_outbox = int(self.runtime_config.get("max_outbox_size", 2000))
        sender_retry_s = float(self.runtime_config.get("retry_interval_seconds", 1.0))
        sender_max_retries = int(self.runtime_config.get("max_retry_attempts", 12))

        if PyImGui.button(f"Sender Debug: {'ON' if sender_debug_logs else 'OFF'}"):
            self.runtime_config["debug_pipeline_logs"] = not sender_debug_logs
            self.runtime_config_dirty = True
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button(f"Sender ACK: {'ON' if sender_ack else 'OFF'}"):
            self.runtime_config["enable_delivery_ack"] = not sender_ack
            self.runtime_config_dirty = True

        PyImGui.text(f"Sender max_send/tick: {sender_max_send}")
        if PyImGui.button("- Send"):
            self.runtime_config["max_send_per_tick"] = max(1, sender_max_send - 1)
            self.runtime_config_dirty = True
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button("+ Send"):
            self.runtime_config["max_send_per_tick"] = min(100, sender_max_send + 1)
            self.runtime_config_dirty = True

        PyImGui.same_line(0.0, 25.0)
        PyImGui.text(f"Sender outbox: {sender_outbox}")
        if PyImGui.button("- Outbox"):
            self.runtime_config["max_outbox_size"] = max(100, sender_outbox - 100)
            self.runtime_config_dirty = True
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button("+ Outbox"):
            self.runtime_config["max_outbox_size"] = min(20000, sender_outbox + 100)
            self.runtime_config_dirty = True

        PyImGui.text(f"Sender retry_s: {sender_retry_s:.1f} max_retries: {sender_max_retries}")
        if PyImGui.button("- RetryS"):
            self.runtime_config["retry_interval_seconds"] = max(0.2, round(sender_retry_s - 0.1, 2))
            self.runtime_config_dirty = True
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button("+ RetryS"):
            self.runtime_config["retry_interval_seconds"] = min(10.0, round(sender_retry_s + 0.1, 2))
            self.runtime_config_dirty = True
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button("- Retries"):
            self.runtime_config["max_retry_attempts"] = max(1, sender_max_retries - 1)
            self.runtime_config_dirty = True
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button("+ Retries"):
            self.runtime_config["max_retry_attempts"] = min(100, sender_max_retries + 1)
            self.runtime_config_dirty = True

        PyImGui.text(f"ShMem msg/tick: {self.max_shmem_messages_per_tick}")
        if PyImGui.button("- Msg"):
            self.max_shmem_messages_per_tick = max(5, self.max_shmem_messages_per_tick - 5)
            self.runtime_config_dirty = True
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button("+ Msg"):
            self.max_shmem_messages_per_tick = min(300, self.max_shmem_messages_per_tick + 5)
            self.runtime_config_dirty = True

        PyImGui.same_line(0.0, 25.0)
        PyImGui.text(f"ShMem scan/tick: {self.max_shmem_scan_per_tick}")
        if PyImGui.button("- Scan"):
            self.max_shmem_scan_per_tick = max(20, self.max_shmem_scan_per_tick - 20)
            self.runtime_config_dirty = True
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button("+ Scan"):
            self.max_shmem_scan_per_tick = min(3000, self.max_shmem_scan_per_tick + 20)
            self.runtime_config_dirty = True

        if self.runtime_config_dirty:
            self._flush_runtime_config_if_dirty()

        PyImGui.text(
            f"Perf: poll_ms={self.last_shmem_poll_ms:.2f} "
            f"processed={self.last_shmem_processed} scanned={self.last_shmem_scanned} ack_sent={self.last_ack_sent}"
        )

    def _mouse_in_current_window_rect(self):
        try:
            io = PyImGui.get_io()
            mx = float(getattr(io, "mouse_pos_x", -1.0))
            my = float(getattr(io, "mouse_pos_y", -1.0))
            wx, wy = PyImGui.get_window_pos()
            ww, wh = PyImGui.get_window_size()
            return (mx >= wx) and (mx <= (wx + ww)) and (my >= wy) and (my <= (wy + wh))
        except Exception:
            return False

    def _draw_hover_handle(self):
        io = PyImGui.get_io()
        display_w = float(getattr(io, "display_size_x", 1920.0) or 1920.0)

        icon_size = 40.0
        handle_w = 68.0
        handle_h = 68.0
        x = max(8.0, (display_w * 0.5) - (handle_w * 0.5))
        y = 4.0

        if not self.hover_handle_initialized:
            if self.saved_hover_handle_pos is not None:
                PyImGui.set_next_window_pos(self.saved_hover_handle_pos[0], self.saved_hover_handle_pos[1])
            else:
                PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(handle_w, handle_h)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0.0, 0.0)
        flags = (
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoResize |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.NoCollapse
        )

        hovered = False
        if PyImGui.begin("Drop Tracker##HoverHandle", flags):
            self.hover_handle_initialized = True
            self._persist_layout_value("drop_viewer_handle_pos", PyImGui.get_window_pos())
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0.0, 0.0)
            if self.hover_pin_open:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, (0.30, 0.92, 0.35, 1.0))
            else:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, (0.95, 0.28, 0.22, 1.0))

            icon_x = max(0.0, (handle_w - icon_size) * 0.5)
            icon_y = max(0.0, (handle_h - icon_size) * 0.5)
            PyImGui.set_cursor_pos(icon_x, icon_y)

            clicked = False
            if os.path.exists(self.hover_icon_path):
                clicked = ImGui.ImageButton("drop_viewer_handle_icon", self.hover_icon_path, icon_size, icon_size)
            else:
                clicked = PyImGui.button("Loot##DropHandleBtn", icon_size, icon_size)

            if clicked:
                self.hover_pin_open = not self.hover_pin_open
            PyImGui.pop_style_var(2)
            PyImGui.pop_style_color(1)

            if PyImGui.is_item_hovered():
                tip = "Drop Tracker (click to pin)" if not self.hover_pin_open else "Drop Tracker (click to unpin)"
                ImGui.show_tooltip(tip)

            hovered = self._mouse_in_current_window_rect() or PyImGui.is_window_hovered() or PyImGui.is_any_item_hovered()
        PyImGui.end()
        PyImGui.pop_style_var(1)
        return hovered

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
                    
                    canonical_name = self._canonical_agg_item_name(item_name, rarity, temp_agg)
                    key = (canonical_name, rarity)
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
        now = time.time()
        handle_hovered = False
        if self.hover_handle_mode:
            handle_hovered = self._draw_hover_handle()
            if handle_hovered:
                self.hover_is_visible = True
                self.hover_hide_deadline = now + self.hover_hide_delay_s
            if self.hover_pin_open:
                self.hover_is_visible = True
            if not self.hover_is_visible and not self.hover_pin_open:
                return
        else:
            self.hover_is_visible = True

        main_window_hovered = False
        if not self.viewer_window_initialized:
            if self.saved_viewer_window_pos is not None:
                PyImGui.set_next_window_pos(self.saved_viewer_window_pos[0], self.saved_viewer_window_pos[1])
            if self.saved_viewer_window_size is not None:
                PyImGui.set_next_window_size(self.saved_viewer_window_size[0], self.saved_viewer_window_size[1])
        if PyImGui.begin(self.window_name):
            self.viewer_window_initialized = True
            self._persist_layout_value("drop_viewer_window_pos", PyImGui.get_window_pos())
            self._persist_layout_value("drop_viewer_window_size", PyImGui.get_window_size())
            
            # -- Auto Refresh --
            # Live mode already updates in-memory stats from ShMem/chat handlers.
            # Avoid reparsing full CSV continuously, which can hitch on long sessions.
            current_time = time.time()
            if self.paused and current_time - self.last_auto_refresh_time > 1.0:
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

            if PyImGui.button("Pause" if not self.paused else "Resume"):
                self.paused = not self.paused

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

            filtered_rows = self._get_filtered_rows()
            table_rows = [row for row in filtered_rows if not self._is_gold_row(row)]
            self._draw_summary_bar(filtered_rows)

            # -- Status Bar --
            if time.time() - self.status_time < 5:
                PyImGui.text_colored(self.status_message, (0.0, 1.0, 0.0, 1.0))

            PyImGui.separator()

            # -- Main Content: Left filter rail + right data panel --
            left_w = 280.0
            if PyImGui.begin_child("DropViewerLeftRail", size=(left_w, 0), border=True, flags=PyImGui.WindowFlags.NoFlag):
                PyImGui.text("Filters")
                self.search_text = PyImGui.input_text("Search", self.search_text)
                self.filter_player = PyImGui.input_text("Player", self.filter_player)
                self.filter_map = PyImGui.input_text("Map", self.filter_map)

                self.filter_rarity_idx = int(PyImGui.combo("Rarity", int(self.filter_rarity_idx), self.filter_rarity_options))
                self.only_rare = PyImGui.checkbox("Only Rare", self.only_rare)
                self.hide_gold = PyImGui.checkbox("Hide Gold", self.hide_gold)
                self.min_qty = max(1, int(PyImGui.input_int("Min Qty", int(self.min_qty))))
                self.auto_scroll = PyImGui.checkbox("Auto Scroll", self.auto_scroll)
                prev_hover_mode = self.hover_handle_mode
                self.hover_handle_mode = PyImGui.checkbox("Hover Handle Mode", self.hover_handle_mode)
                if self.hover_handle_mode:
                    self.hover_pin_open = PyImGui.checkbox("Pin Open", self.hover_pin_open)
                if self.hover_handle_mode and not prev_hover_mode:
                    self.hover_is_visible = True
                    self.hover_hide_deadline = now + self.hover_hide_delay_s

                if PyImGui.button("Quick: Rare Only"):
                    self.only_rare = True
                    self.hide_gold = True
                    self.filter_rarity_idx = 0
                if PyImGui.button("Clear Filters"):
                    self.search_text = ""
                    self.filter_player = ""
                    self.filter_map = ""
                    self.filter_rarity_idx = 0
                    self.only_rare = False
                    self.hide_gold = False
                    self.min_qty = 1

                PyImGui.separator()
                self.show_runtime_panel = PyImGui.checkbox("Advanced Runtime Controls", self.show_runtime_panel)
                if self.show_runtime_panel:
                    PyImGui.separator()
                    self._draw_runtime_controls()
                PyImGui.end_child()

            PyImGui.same_line(0.0, 10.0)

            if PyImGui.begin_child("DropViewerDataPanel", size=(0, 0), border=False, flags=PyImGui.WindowFlags.NoFlag):
                if self.view_mode == "Aggregated":
                    self._draw_aggregated(table_rows)
                else:
                    self._draw_log(table_rows)
                PyImGui.end_child()

            main_window_hovered = self._mouse_in_current_window_rect() or PyImGui.is_window_hovered() or PyImGui.is_any_item_hovered()

        PyImGui.end()
        self._flush_runtime_config_if_dirty()
        if self.hover_handle_mode:
            if main_window_hovered:
                self.hover_is_visible = True
                self.hover_hide_deadline = now + self.hover_hide_delay_s
            if not self.hover_pin_open and not handle_hovered and not main_window_hovered and now >= self.hover_hide_deadline:
                self.hover_is_visible = False
        
    def _draw_aggregated(self, filtered_rows):
        filtered_agg, total_filtered_qty = self._get_filtered_aggregated(filtered_rows)
        total_items_without_gold = total_filtered_qty - sum(
            data["Quantity"] for (name, _), data in filtered_agg.items() if name == "Gold"
        )

        PyImGui.text(f"Total Items (filtered): {max(0, total_items_without_gold)}")

        if PyImGui.begin_table("AggTable", 5, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.Resizable | PyImGui.TableFlags.Sortable | PyImGui.TableFlags.ScrollY, 0.0, 360.0):
            PyImGui.table_setup_column("Item Name")
            PyImGui.table_setup_column("Quantity")
            PyImGui.table_setup_column("%")
            PyImGui.table_setup_column("Rarity")
            PyImGui.table_setup_column("Count") 
            PyImGui.table_headers_row()
            
            # Sort by Item Name then Rarity
            display_items = list(filtered_agg.items())
            
            sorted_items = sorted(display_items, key=lambda x: (x[0][0], x[0][1]))
            
            for idx, ((item_name, rarity), data) in enumerate(sorted_items):
                PyImGui.table_next_row()
                
                qty = data["Quantity"]
                
                if item_name == "Gold":
                    pct_str = "---"
                else:
                    pct = (qty / total_items_without_gold * 100) if total_items_without_gold > 0 else 0
                    pct_str = f"{pct:.1f}%"
                
                # Get Color
                r, g, b, a = self._get_rarity_color(rarity)

                row_key = (item_name, rarity)

                PyImGui.table_set_column_index(0)
                if PyImGui.selectable(f"{item_name}##agg_{idx}", self.selected_item_key == row_key, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                    self.selected_item_key = row_key
                PyImGui.same_line(0.0, 8.0)
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

        if self.selected_item_key and self.selected_item_key in filtered_agg:
            sel_qty = filtered_agg[self.selected_item_key]["Quantity"]
            sel_count = filtered_agg[self.selected_item_key]["Count"]
            sel_name, sel_rarity = self.selected_item_key
            PyImGui.separator()
            PyImGui.text("Selection")
            PyImGui.text_colored(f"{sel_name} ({sel_rarity})", self._get_rarity_color(sel_rarity))
            PyImGui.text(f"Total Quantity: {sel_qty}")
            PyImGui.text(f"Drop Count: {sel_count}")

    def _draw_log(self, filtered_rows):
        if PyImGui.begin_table("DropsLogTable", 8, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.Resizable | PyImGui.TableFlags.ScrollY, 0.0, 0.0):
            PyImGui.table_setup_column("Timestamp")
            PyImGui.table_setup_column("Logger")     
            PyImGui.table_setup_column("MapID")
            PyImGui.table_setup_column("MapName")
            PyImGui.table_setup_column("Player")     
            PyImGui.table_setup_column("Item")
            PyImGui.table_setup_column("Qty")
            PyImGui.table_setup_column("Rarity")
            PyImGui.table_headers_row()

            for row in filtered_rows:
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
            if self.config_poll_timer.IsExpired():
                self.config_poll_timer.Reset()
                self._load_runtime_config()

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
            
        poll_started = time.perf_counter()
        processed_tracker_msgs = 0
        scanned_msgs = 0
        batch_rows = []
        ack_sent_this_tick = 0
        try:
            my_email = Player.GetAccountEmail()
            if not my_email:
                return

            # Only leader client should ingest TrackerDrop messages into the shared CSV.
            try:
                if Player.GetAgentID() != Party.GetPartyLeaderID():
                    return
            except Exception:
                return

            shmem = getattr(GLOBAL_CACHE, "ShMem", None)
            if shmem is None:
                return

            self.shmem_bootstrap_done = True

            # Keep only recent dedupe and partial-name buffers.
            now_ts = time.time()
            self.seen_events = {
                key: ts for key, ts in self.seen_events.items()
                if (now_ts - ts) <= self.seen_event_ttl_seconds
            }
            self.name_chunk_buffers = {
                sig: data for sig, data in self.name_chunk_buffers.items()
                if (now_ts - float(data.get("updated_at", now_ts))) <= 30.0
            }

            messages = shmem.GetAllMessages()
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

                should_finish = False
                try:
                    should_finish = False
                    extra_data_list = getattr(shared_msg, "ExtraData", None)
                    if not extra_data_list or len(extra_data_list) == 0:
                        continue

                    extra_0 = _c_wchar_array_to_str(extra_data_list[0])
                    if extra_0 == "TrackerNameV2":
                        should_finish = True
                        scanned_msgs += 1
                        name_sig = _c_wchar_array_to_str(extra_data_list[1]) if len(extra_data_list) > 1 else ""
                        chunk_text = _c_wchar_array_to_str(extra_data_list[2]) if len(extra_data_list) > 2 else ""
                        chunk_meta = _c_wchar_array_to_str(extra_data_list[3]) if len(extra_data_list) > 3 else ""
                        chunk_idx, chunk_total = decode_name_chunk_meta(chunk_meta)
                        if name_sig:
                            bucket = self.name_chunk_buffers.get(name_sig, {"chunks": {}, "total": chunk_total, "updated_at": now_ts})
                            bucket["total"] = max(int(bucket.get("total", 1)), int(chunk_total))
                            bucket["chunks"][int(chunk_idx)] = chunk_text
                            bucket["updated_at"] = now_ts
                            self.name_chunk_buffers[name_sig] = bucket
                            if len(bucket["chunks"]) >= int(bucket["total"]):
                                merged = "".join(bucket["chunks"].get(i, "") for i in range(1, int(bucket["total"]) + 1)).strip()
                                if merged:
                                    self.full_name_by_signature[name_sig] = merged
                                self.name_chunk_buffers.pop(name_sig, None)
                        shmem.MarkMessageAsFinished(my_email, msg_idx)
                        continue

                    if extra_0 != "TrackerDrop":
                        continue

                    should_finish = True
                    scanned_msgs += 1
                    if scanned_msgs > self.max_shmem_scan_per_tick:
                        break

                    item_name = _c_wchar_array_to_str(extra_data_list[1]) if len(extra_data_list) > 1 else "Unknown Item"
                    exact_rarity = _c_wchar_array_to_str(extra_data_list[2]) if len(extra_data_list) > 2 else "Unknown"
                    meta_text = _c_wchar_array_to_str(extra_data_list[3]) if len(extra_data_list) > 3 else ""
                    meta = parse_drop_meta(meta_text)
                    event_id = meta.get("event_id", "")
                    name_sig = meta.get("name_signature", "")

                    resolved_name = self.full_name_by_signature.get(name_sig, "") if name_sig else ""
                    if resolved_name:
                        item_name = resolved_name
                    elif name_sig and len(item_name) >= 31:
                        item_name = f"{item_name}~{name_sig[:4]}"

                    exact_rarity = self._normalize_rarity_label(item_name, exact_rarity)

                    quantity_param = shared_msg.Params[0] if len(shared_msg.Params) > 0 else 0
                    quantity = int(round(quantity_param)) if quantity_param > 0 else 1
                    item_id_param = int(round(shared_msg.Params[1])) if len(shared_msg.Params) > 1 and shared_msg.Params[1] > 0 else 0
                    model_id_param = int(round(shared_msg.Params[2])) if len(shared_msg.Params) > 2 and shared_msg.Params[2] > 0 else 0
                    slot_encoded = int(round(shared_msg.Params[3])) if len(shared_msg.Params) > 3 and shared_msg.Params[3] > 0 else 0
                    slot_bag = int((slot_encoded >> 16) & 0xFFFF) if slot_encoded > 0 else 0
                    slot_index = int(slot_encoded & 0xFFFF) if slot_encoded > 0 else 0

                    sender_email = _normalize_shmem_text(getattr(shared_msg, "SenderEmail", ""))
                    sender_name = "Follower"
                    sender_account = shmem.GetAccountDataFromEmail(sender_email)
                    if sender_account:
                        sender_name = sender_account.AgentData.CharacterName

                    event_key = f"{sender_email}:{event_id}" if event_id else ""
                    is_duplicate = False
                    if event_key:
                        if event_key in self.seen_events:
                            is_duplicate = True
                        else:
                            self.seen_events[event_key] = now_ts

                    if not is_duplicate:
                        batch_rows.append((
                            sender_name,
                            item_name,
                            quantity,
                            exact_rarity,
                            None,
                        ))

                    if event_id and self._send_tracker_ack(sender_email, event_id):
                        ack_sent_this_tick += 1

                    if self.verbose_shmem_item_logs:
                        log_msg = (
                            f"TRACKED: {item_name} x{quantity} ({exact_rarity}) "
                            f"[{sender_name}] (ShMem idx={msg_idx} item_id={item_id_param} "
                            f"model_id={model_id_param} slot={slot_bag}:{slot_index} ev={event_id} dup={is_duplicate})"
                        )
                        Py4GW.Console.Log("DropViewer", log_msg, Py4GW.Console.MessageType.Info)

                    shmem.MarkMessageAsFinished(my_email, msg_idx)
                    processed_tracker_msgs += 1
                except Exception as msg_e:
                    Py4GW.Console.Log("DropViewer", f"Error parsing ShMem msg: {msg_e}", Py4GW.Console.MessageType.Warning)
                    try:
                        if should_finish:
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                    except Exception:
                        pass
                    continue

            if batch_rows:
                self._log_drops_batch(batch_rows)
                Py4GW.Console.Log(
                    "DropViewer",
                    f"TRACKED BATCH: {len(batch_rows)} items (ShMem)",
                    Py4GW.Console.MessageType.Info
                )
        except Exception:
            pass  # ShMem might not be ready
        finally:
            self.last_shmem_poll_ms = (time.perf_counter() - poll_started) * 1000.0
            self.last_shmem_processed = processed_tracker_msgs
            self.last_shmem_scanned = scanned_msgs
            if self.enable_perf_logs and self.perf_timer.IsExpired():
                self.perf_timer.Reset()
                Py4GW.Console.Log(
                    "DropViewer",
                    (
                        f"perf poll_ms={self.last_shmem_poll_ms:.2f} "
                        f"processed={self.last_shmem_processed} scanned={self.last_shmem_scanned} "
                        f"ack_sent={ack_sent_this_tick}"
                    ),
                    Py4GW.Console.MessageType.Info,
                )

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

                    canonical_name = self._canonical_agg_item_name(item_name, rarity, self.aggregated_drops)
                    key = (canonical_name, rarity)
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
    drop_viewer.draw()

def update():
    drop_viewer.update()

if __name__ == "__main__":
    pass

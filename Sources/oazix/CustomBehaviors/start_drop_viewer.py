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
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions import IdentifyResponseScheduler
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions import run_inventory_action
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import DROP_LOG_HEADER
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import append_drop_log_rows
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import parse_drop_log_file
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_event_id
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_item_id
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_sender_email
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_item_stats
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import parse_runtime_row
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import set_runtime_row_item_id
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import set_runtime_row_item_stats
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import update_rows_item_stats_by_event_and_sender
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_stats_render import get_cached_rendered_stats
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_stats_render import prune_render_cache
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_stats_render import update_render_cache
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import build_tracker_drop_message
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_inventory_action_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_inventory_stats_request_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_inventory_stats_response_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_drop_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_name_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_stats_payload_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_stats_text_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import extract_event_id_hint
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import is_duplicate_event
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import mark_seen_event
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import merge_name_chunk
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import merge_stats_payload_chunk
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import merge_stats_text_chunk
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import payload_has_valid_mods_json
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_ui_panels import default_ui_colors
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_ui_panels import draw_runtime_controls_panel
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import (
    build_name_chunks,
    make_name_signature,
    encode_name_chunk_meta,
    decode_name_chunk_meta,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.item_mod_render_utils import (
    build_known_spellcasting_mod_lines,
    prune_generic_attribute_bonus_lines,
    render_mod_description_template,
    sort_stats_lines_like_ingame,
)
from Py4GWCoreLib import * # Includes Map, Player

IMPORT_OPTIONAL_ERRORS = (ImportError, ModuleNotFoundError, AttributeError)
EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)

try:
    from Py4GWCoreLib.enums_src.Item_enums import ItemType
    from Sources.marks_sources.mods_parser import ModDatabase, parse_modifiers, is_matching_item_type
except IMPORT_OPTIONAL_ERRORS:
    ItemType = None
    ModDatabase = None
    parse_modifiers = None
    is_matching_item_type = None

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
        self.stats_by_event = {}
        self.stats_chunk_buffers = {}
        self.stats_payload_by_event = {}
        self.stats_payload_chunk_buffers = {}
        self.stats_render_cache_by_event = {}
        self.stats_name_signature_by_event = {}
        self.mod_db = self._load_mod_database()
        self.enable_chat_item_tracking = False
        self.max_shmem_messages_per_tick = 80
        self.max_shmem_scan_per_tick = 600
        self.verbose_shmem_item_logs = False
        self.debug_item_stats_panel = False
        self.debug_item_stats_panel_height = 180
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
        self.last_seen_map_id = 0
        self.map_change_ignore_until = 0.0
        self.perf_timer = ThrottledTimer(5000)
        self.shmem_error_timer = ThrottledTimer(5000)
        self.config_poll_timer = ThrottledTimer(2000)
        self.runtime_config_path = os.path.join(os.path.dirname(constants.DROP_LOG_PATH), "drop_tracker_runtime_config.json")
        self.runtime_config = self._default_runtime_config()
        self.runtime_config_dirty = False
        self.inventory_action_tag = "TrackerInvActionV1"
        self.inventory_stats_request_tag = "TrackerInvStatReq"
        self.inventory_stats_response_tag = "TrackerInvStatRes"
        self.id_sel_white = False
        self.id_sel_blue = True
        self.id_sel_green = True
        self.id_sel_purple = True
        self.id_sel_gold = True
        self.salvage_sel_white = True
        self.salvage_sel_blue = True
        self.salvage_sel_green = False
        self.salvage_sel_purple = True
        self.salvage_sel_gold = False
        self.inventory_kit_stats_by_email = {}
        self.inventory_kit_stats_refresh_timer = ThrottledTimer(3000)
        self.remote_stats_request_last_by_event = {}
        self.remote_stats_pending_by_event = {}
        self.auto_conset_enabled = False
        self.auto_conset_armor = True
        self.auto_conset_grail = True
        self.auto_conset_essence = True
        self.auto_conset_legionnaire = True
        self.auto_conset_timer = ThrottledTimer(1500)
        self.conset_effect_id_cache = {}
        self.identify_response_scheduler = IdentifyResponseScheduler()
        self.drop_viewer_assets_dir = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Assets", "DropViewer")
        self.conset_armor_icon = os.path.join(self.drop_viewer_assets_dir, "ArmorOfSalvation.jpg")
        self.conset_grail_icon = os.path.join(self.drop_viewer_assets_dir, "GrailOfMight.jpg")
        self.conset_essence_icon = os.path.join(self.drop_viewer_assets_dir, "EssenceOfCelerity.jpg")
        self.conset_legionnaire_icon = os.path.join(self.drop_viewer_assets_dir, "LegiStone.jpg")

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
        self.selected_log_row = None
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
            "debug_item_stats_panel": False,
            "debug_item_stats_panel_height": 180,
            "id_sel_white": False,
            "id_sel_blue": True,
            "id_sel_green": True,
            "id_sel_purple": True,
            "id_sel_gold": True,
            "salvage_sel_white": True,
            "salvage_sel_blue": True,
            "salvage_sel_green": False,
            "salvage_sel_purple": True,
            "salvage_sel_gold": False,
            "auto_conset_enabled": False,
            "auto_conset_armor": True,
            "auto_conset_grail": True,
            "auto_conset_essence": True,
            "auto_conset_legionnaire": True,
        }

    def _apply_runtime_config(self):
        cfg = self.runtime_config if isinstance(self.runtime_config, dict) else self._default_runtime_config()
        self.verbose_shmem_item_logs = bool(cfg.get("verbose_shmem_item_logs", self.verbose_shmem_item_logs))
        self.max_shmem_messages_per_tick = max(5, int(cfg.get("max_shmem_messages_per_tick", self.max_shmem_messages_per_tick)))
        self.max_shmem_scan_per_tick = max(20, int(cfg.get("max_shmem_scan_per_tick", self.max_shmem_scan_per_tick)))
        self.send_tracker_ack_enabled = bool(cfg.get("send_tracker_ack_enabled", self.send_tracker_ack_enabled))
        self.debug_item_stats_panel = bool(cfg.get("debug_item_stats_panel", self.debug_item_stats_panel))
        self.debug_item_stats_panel_height = max(120, min(900, int(cfg.get("debug_item_stats_panel_height", self.debug_item_stats_panel_height))))
        self.enable_perf_logs = bool(cfg.get("enable_perf_logs", self.enable_perf_logs))
        self.id_sel_white = bool(cfg.get("id_sel_white", self.id_sel_white))
        self.id_sel_blue = bool(cfg.get("id_sel_blue", self.id_sel_blue))
        self.id_sel_green = bool(cfg.get("id_sel_green", self.id_sel_green))
        self.id_sel_purple = bool(cfg.get("id_sel_purple", self.id_sel_purple))
        self.id_sel_gold = bool(cfg.get("id_sel_gold", self.id_sel_gold))
        self.salvage_sel_white = bool(cfg.get("salvage_sel_white", self.salvage_sel_white))
        self.salvage_sel_blue = bool(cfg.get("salvage_sel_blue", self.salvage_sel_blue))
        self.salvage_sel_green = bool(cfg.get("salvage_sel_green", self.salvage_sel_green))
        self.salvage_sel_purple = bool(cfg.get("salvage_sel_purple", self.salvage_sel_purple))
        self.salvage_sel_gold = bool(cfg.get("salvage_sel_gold", self.salvage_sel_gold))
        self.auto_conset_enabled = bool(cfg.get("auto_conset_enabled", self.auto_conset_enabled))
        self.auto_conset_armor = bool(cfg.get("auto_conset_armor", self.auto_conset_armor))
        self.auto_conset_grail = bool(cfg.get("auto_conset_grail", self.auto_conset_grail))
        self.auto_conset_essence = bool(cfg.get("auto_conset_essence", self.auto_conset_essence))
        self.auto_conset_legionnaire = bool(cfg.get("auto_conset_legionnaire", self.auto_conset_legionnaire))

    def _load_ui_layout_from_config(self):
        cfg = self.runtime_config if isinstance(self.runtime_config, dict) else {}
        try:
            pos = cfg.get("drop_viewer_handle_pos", None)
            if isinstance(pos, list) and len(pos) == 2:
                self.saved_hover_handle_pos = (float(pos[0]), float(pos[1]))
        except EXPECTED_RUNTIME_ERRORS:
            self.saved_hover_handle_pos = None
        try:
            pos = cfg.get("drop_viewer_window_pos", None)
            if isinstance(pos, list) and len(pos) == 2:
                self.saved_viewer_window_pos = (float(pos[0]), float(pos[1]))
        except EXPECTED_RUNTIME_ERRORS:
            self.saved_viewer_window_pos = None
        try:
            size = cfg.get("drop_viewer_window_size", None)
            if isinstance(size, list) and len(size) == 2:
                self.saved_viewer_window_size = (float(size[0]), float(size[1]))
        except EXPECTED_RUNTIME_ERRORS:
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
            except EXPECTED_RUNTIME_ERRORS:
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
        except EXPECTED_RUNTIME_ERRORS:
            self.runtime_config = self._default_runtime_config()
        self._apply_runtime_config()

    def _save_runtime_config(self):
        try:
            os.makedirs(os.path.dirname(self.runtime_config_path), exist_ok=True)
            with open(self.runtime_config_path, mode="w", encoding="utf-8") as f:
                json.dump(self.runtime_config, f, indent=2)
        except EXPECTED_RUNTIME_ERRORS as e:
            Py4GW.Console.Log("DropViewer", f"Runtime config save failed: {e}", Py4GW.Console.MessageType.Warning)

    def _sync_runtime_config_from_state(self):
        cfg = self.runtime_config if isinstance(self.runtime_config, dict) else self._default_runtime_config()
        cfg["verbose_shmem_item_logs"] = bool(self.verbose_shmem_item_logs)
        cfg["max_shmem_messages_per_tick"] = int(self.max_shmem_messages_per_tick)
        cfg["max_shmem_scan_per_tick"] = int(self.max_shmem_scan_per_tick)
        cfg["send_tracker_ack_enabled"] = bool(self.send_tracker_ack_enabled)
        cfg["debug_item_stats_panel"] = bool(self.debug_item_stats_panel)
        cfg["debug_item_stats_panel_height"] = int(self.debug_item_stats_panel_height)
        cfg["enable_perf_logs"] = bool(self.enable_perf_logs)
        cfg["id_sel_white"] = bool(self.id_sel_white)
        cfg["id_sel_blue"] = bool(self.id_sel_blue)
        cfg["id_sel_green"] = bool(self.id_sel_green)
        cfg["id_sel_purple"] = bool(self.id_sel_purple)
        cfg["id_sel_gold"] = bool(self.id_sel_gold)
        cfg["salvage_sel_white"] = bool(self.salvage_sel_white)
        cfg["salvage_sel_blue"] = bool(self.salvage_sel_blue)
        cfg["salvage_sel_green"] = bool(self.salvage_sel_green)
        cfg["salvage_sel_purple"] = bool(self.salvage_sel_purple)
        cfg["salvage_sel_gold"] = bool(self.salvage_sel_gold)
        cfg["auto_conset_enabled"] = bool(self.auto_conset_enabled)
        cfg["auto_conset_armor"] = bool(self.auto_conset_armor)
        cfg["auto_conset_grail"] = bool(self.auto_conset_grail)
        cfg["auto_conset_essence"] = bool(self.auto_conset_essence)
        cfg["auto_conset_legionnaire"] = bool(self.auto_conset_legionnaire)
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
        except EXPECTED_RUNTIME_ERRORS:
            return False

    def _ensure_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="ignore")
            except EXPECTED_RUNTIME_ERRORS:
                return ""
        return str(value)

    def _strip_tags(self, text: Any) -> str:
        return re.sub(r"<[^>]+>", "", self._ensure_text(text))

    def _clean_item_name(self, name: Any) -> str:
        cleaned = self._strip_tags(name).strip()
        cleaned = re.sub(r"^[\d,]+\s+", "", cleaned)
        return cleaned

    def _load_mod_database(self):
        if ModDatabase is None:
            return None
        candidate_dirs = []
        try:
            sources_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            candidate_dirs.append(os.path.join(sources_root, "marks_sources", "mods_data"))
        except EXPECTED_RUNTIME_ERRORS:
            pass
        try:
            project_root = PathLocator.get_project_root_directory()
            candidate_dirs.append(os.path.join(project_root, "Sources", "marks_sources", "mods_data"))
        except EXPECTED_RUNTIME_ERRORS:
            pass

        seen = set()
        for data_dir in candidate_dirs:
            norm = os.path.normcase(os.path.normpath(self._ensure_text(data_dir)))
            if not norm or norm in seen:
                continue
            seen.add(norm)
            if not os.path.isdir(data_dir):
                continue
            try:
                return ModDatabase.load(data_dir)
            except EXPECTED_RUNTIME_ERRORS:
                continue
        return None

    def _format_attribute_name(self, attr_name: Any) -> str:
        txt = self._ensure_text(attr_name).replace("_", " ").strip()
        txt = re.sub(r"([a-z])([A-Z])", r"\1 \2", txt)
        return txt

    def _render_mod_description_template(
        self,
        description: str,
        matched_modifiers: list[tuple[int, int, int]],
        default_value: int = 0,
        attribute_name: str = "",
    ) -> list[str]:
        def _resolve_attribute_name(attr_id: int) -> str:
            try:
                return self._format_attribute_name(getattr(Attribute(int(attr_id)), "name", ""))
            except EXPECTED_RUNTIME_ERRORS:
                return ""

        return render_mod_description_template(
            description=self._ensure_text(description),
            matched_modifiers=list(matched_modifiers or []),
            default_value=int(default_value),
            attribute_name=self._ensure_text(attribute_name),
            resolve_attribute_name_fn=_resolve_attribute_name,
            format_attribute_name_fn=self._format_attribute_name,
            unknown_attribute_template="Attribute {id}",
        )

    def _match_mod_definition_against_raw(self, definition_modifiers, raw_mods) -> list[tuple[int, int, int]]:
        meaningful = []
        for dm in list(definition_modifiers or []):
            mode = self._ensure_text(getattr(dm, "modifier_value_arg", "")).lower()
            if "none" in mode:
                continue
            meaningful.append(dm)
        if not meaningful:
            return []

        matched = []
        for dm in meaningful:
            ident = int(getattr(dm, "identifier", 0))
            arg1 = int(getattr(dm, "arg1", 0))
            arg2 = int(getattr(dm, "arg2", 0))
            min_v = int(getattr(dm, "min", 0))
            max_v = int(getattr(dm, "max", 0))
            mode = self._ensure_text(getattr(dm, "modifier_value_arg", "")).lower()
            found = None
            for rid, ra1, ra2 in raw_mods:
                if int(rid) != ident:
                    continue
                if "arg1" in mode:
                    if int(ra2) == arg2 and min_v <= int(ra1) <= max_v:
                        found = (int(rid), int(ra1), int(ra2))
                        break
                elif "arg2" in mode:
                    if int(ra1) == arg1 and min_v <= int(ra2) <= max_v:
                        found = (int(rid), int(ra1), int(ra2))
                        break
                elif "fixed" in mode:
                    if int(ra1) == arg1 and int(ra2) == arg2:
                        found = (int(rid), int(ra1), int(ra2))
                        break
            if found is None:
                return []
            matched.append(found)
        return matched

    def _weapon_mod_type_matches(self, weapon_mod, item_type) -> bool:
        if item_type is None or is_matching_item_type is None:
            return False
        try:
            target_types = list(getattr(weapon_mod, "target_types", []) or [])
            for target in target_types:
                try:
                    if is_matching_item_type(item_type, target):
                        return True
                except EXPECTED_RUNTIME_ERRORS:
                    continue
            item_mods = getattr(weapon_mod, "item_mods", {}) or {}
            for target in list(item_mods.keys()):
                try:
                    if is_matching_item_type(item_type, target):
                        return True
                except EXPECTED_RUNTIME_ERRORS:
                    continue
        except EXPECTED_RUNTIME_ERRORS:
            return False
        return False

    def _collect_fallback_mod_lines(self, raw_mods, item_attr_txt: str, item_type=None) -> list[str]:
        lines = []
        if self.mod_db is None:
            return lines
        best_by_ident = {}
        try:
            for weapon_mod in list(getattr(self.mod_db, "weapon_mods", {}).values()):
                matched = self._match_mod_definition_against_raw(getattr(weapon_mod, "modifiers", []), raw_mods)
                if not matched:
                    continue
                ident_set = {int(m[0]) for m in matched}
                if not ident_set:
                    continue
                desc = self._ensure_text(getattr(weapon_mod, "description", "")).strip()
                rendered = self._render_mod_description_template(desc, matched, 0, item_attr_txt)
                if rendered:
                    first_line = rendered[0]
                    lower_desc = desc.lower()
                    has_old_school = "[old school]" in lower_desc
                    type_match = self._weapon_mod_type_matches(weapon_mod, item_type)
                    # Ranking:
                    # - direct type match is strongest signal,
                    # - old-school descriptors are allowed cross-type fallback,
                    # - plain cross-type matches are heavily penalized.
                    score = 0
                    if type_match:
                        score += 100
                    if has_old_school:
                        score += 20
                    if not type_match and not has_old_school:
                        score -= 60
                    score += min(len(matched), 3)
                    for ident in ident_set:
                        prev = best_by_ident.get(ident, None)
                        if prev is None or score > int(prev.get("score", -999)):
                            best_by_ident[ident] = {"line": first_line, "score": score}
        except EXPECTED_RUNTIME_ERRORS:
            return lines
        for ident in sorted(best_by_ident.keys()):
            line = self._ensure_text(best_by_ident[ident].get("line", "")).strip()
            if line:
                lines.append(line)
        return lines

    def _collect_fallback_rune_lines(self, raw_mods, item_attr_txt: str) -> list[str]:
        lines = []
        if self.mod_db is None:
            return lines
        best_by_ident = {}
        try:
            for rune in list(getattr(self.mod_db, "runes", {}).values()):
                matched = self._match_mod_definition_against_raw(getattr(rune, "modifiers", []), raw_mods)
                if not matched:
                    continue
                ident_set = {int(m[0]) for m in matched}
                if not ident_set:
                    continue
                desc = self._ensure_text(getattr(rune, "description", "")).strip()
                rune_name = self._ensure_text(getattr(rune, "name", "")).strip()
                rendered = self._render_mod_description_template(desc, matched, 0, item_attr_txt)
                candidate_lines = []
                if rune_name:
                    candidate_lines.append(rune_name)
                candidate_lines.extend(rendered)
                if not candidate_lines and rune_name:
                    candidate_lines = [rune_name]
                deduped_candidates = []
                seen_line_keys = set()
                for candidate in candidate_lines:
                    candidate_txt = self._ensure_text(candidate).strip()
                    if not candidate_txt:
                        continue
                    line_key = re.sub(r"[^a-z0-9]+", "", candidate_txt.lower())
                    if line_key in seen_line_keys:
                        continue
                    seen_line_keys.add(line_key)
                    deduped_candidates.append(candidate_txt)
                candidate_lines = deduped_candidates
                if not candidate_lines:
                    continue
                score = min(len(matched), 4)
                for ident in ident_set:
                    prev = best_by_ident.get(ident, None)
                    if prev is None or score > int(prev.get("score", -999)):
                        best_by_ident[ident] = {"lines": list(candidate_lines), "score": score}
        except EXPECTED_RUNTIME_ERRORS:
            return lines
        for ident in sorted(best_by_ident.keys()):
            for line in list(best_by_ident[ident].get("lines", []) or []):
                txt = self._ensure_text(line).strip()
                if txt:
                    lines.append(txt)
        return lines

    def _build_known_spellcast_mod_lines(self, raw_mods, item_attr_txt: str, item_type=None) -> list[str]:
        def _resolve_attribute_name(attr_id: int) -> str:
            try:
                return self._format_attribute_name(getattr(Attribute(int(attr_id)), "name", ""))
            except EXPECTED_RUNTIME_ERRORS:
                return ""
        return build_known_spellcasting_mod_lines(
            raw_mods,
            item_attr_txt=self._ensure_text(item_attr_txt),
            item_type=item_type,
            resolve_attribute_name_fn=_resolve_attribute_name,
            include_raw_when_no_chance=True,
            use_range_chance=True,
        )

    def _normalize_item_name(self, name: Any) -> str:
        return self._clean_item_name(name).lower()

    def _extract_mod_lines_from_item_name(self, item_name: Any) -> list[str]:
        name_text = self._clean_item_name(item_name)
        if "|" not in name_text:
            return []
        parts = [self._ensure_text(part).strip() for part in name_text.split("|")]
        if len(parts) <= 1:
            return []
        lines = []
        seen = set()
        for part in parts[1:]:
            if not part:
                continue
            key = re.sub(r"[^a-z0-9]+", "", part.lower())
            if not key or key in seen:
                continue
            seen.add(key)
            lines.append(part)
        return lines

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
                writer.writerow(list(DROP_LOG_HEADER))
            self.last_read_time = os.path.getmtime(self.log_path)
        except EXPECTED_RUNTIME_ERRORS as e:
            Py4GW.Console.Log("DropViewer", f"Failed to reset live log file: {e}", Py4GW.Console.MessageType.Warning)

    def _reset_live_session(self):
        self.raw_drops = []
        self.aggregated_drops = {}
        self.total_drops = 0
        self.shmem_bootstrap_done = False
        self.last_read_time = 0
        self.recent_log_cache = {}
        self.stats_by_event = {}
        self.stats_chunk_buffers = {}
        self.stats_payload_by_event = {}
        self.stats_payload_chunk_buffers = {}
        self.stats_render_cache_by_event = {}
        self.stats_name_signature_by_event = {}
        self.identify_response_scheduler.clear()
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
            
        except EXPECTED_RUNTIME_ERRORS as e:
            self.set_status(f"Error reading log: {e}")

    def _parse_log_file(self, filepath):
        temp_drops = []
        temp_agg = {}
        total = 0
        temp_stats_by_event = {}
        parsed_rows = parse_drop_log_file(filepath, map_name_resolver=Map.GetMapName)
        for parsed in parsed_rows:
            row = parsed.to_runtime_row()
            temp_drops.append(row)
            total += int(parsed.quantity)
            if parsed.event_id:
                sender_email = self._ensure_text(parsed.sender_email).strip().lower()
                stats_cache_key = self._make_stats_cache_key(parsed.event_id, sender_email, parsed.player_name)
                if stats_cache_key:
                    temp_stats_by_event[stats_cache_key] = parsed.item_stats

            canonical_name = self._canonical_agg_item_name(parsed.item_name, parsed.rarity, temp_agg)
            key = (canonical_name, parsed.rarity)
            if key not in temp_agg:
                temp_agg[key] = {"Quantity": 0, "Count": 0}

            temp_agg[key]["Quantity"] += int(parsed.quantity)
            temp_agg[key]["Count"] += 1
                
        self.raw_drops = temp_drops
        self.aggregated_drops = temp_agg
        self.total_drops = total
        self.stats_by_event = temp_stats_by_event
        self.stats_name_signature_by_event = {}

    def set_status(self, msg):
        self.status_message = msg
        self.status_time = time.time()

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except EXPECTED_RUNTIME_ERRORS:
            return default

    def _parse_drop_row(self, row: Any) -> DropLogRow | None:
        return parse_runtime_row(row)

    def _set_row_item_stats(self, row: Any, item_stats: str) -> None:
        set_runtime_row_item_stats(row, self._ensure_text(item_stats).strip())

    def _set_row_item_id(self, row: Any, item_id: int) -> None:
        set_runtime_row_item_id(row, int(item_id))

    def _is_rare_rarity(self, rarity):
        return rarity == "Gold"

    def _passes_filters(self, row):
        parsed = self._parse_drop_row(row)
        if parsed is None:
            return False

        player_name = self._ensure_text(parsed.player_name)
        item_name = self._ensure_text(parsed.item_name)
        qty = int(parsed.quantity)
        rarity = self._ensure_text(parsed.rarity).strip() or "Unknown"
        map_name = self._ensure_text(parsed.map_name)

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
        parsed = self._parse_drop_row(row)
        if parsed is None:
            return False
        return self._clean_item_name(parsed.item_name) == "Gold"

    def _get_filtered_aggregated(self, filtered_rows):
        agg = {}
        total_qty = 0
        for row in filtered_rows:
            parsed = self._parse_drop_row(row)
            if parsed is None:
                continue
            item_name = parsed.item_name
            rarity = parsed.rarity
            qty = int(parsed.quantity)
            total_qty += qty
            canonical_name = self._canonical_agg_item_name(item_name, rarity, agg)
            key = (canonical_name, rarity)
            if key not in agg:
                agg[key] = {"Quantity": 0, "Count": 0}
            agg[key]["Quantity"] += qty
            agg[key]["Count"] += 1
        return agg, total_qty

    def _extract_row_event_id(self, row) -> str:
        return self._ensure_text(extract_runtime_row_event_id(row)).strip()

    def _extract_row_item_stats(self, row) -> str:
        return self._ensure_text(extract_runtime_row_item_stats(row)).strip()

    def _extract_row_item_id(self, row) -> int:
        return max(0, int(extract_runtime_row_item_id(row)))

    def _extract_row_sender_email(self, row) -> str:
        return self._ensure_text(extract_runtime_row_sender_email(row)).strip().lower()

    def _make_sender_identifier(self, sender_email: str = "", player_name: str = "") -> str:
        sender_key = self._ensure_text(sender_email).strip().lower()
        if sender_key:
            return f"email:{sender_key}"
        player_key = self._ensure_text(player_name).strip().lower()
        if player_key:
            return f"player:{player_key}"
        return "unknown"

    def _make_stats_cache_key(self, event_id: str, sender_email: str = "", player_name: str = "") -> str:
        event_key = self._ensure_text(event_id).strip()
        if not event_key:
            return ""
        sender_ident = self._make_sender_identifier(sender_email, player_name)
        return f"{sender_ident}:{event_key}"

    def _resolve_sender_name_from_email(self, sender_email: str) -> str:
        sender_name = ""
        try:
            shmem = getattr(GLOBAL_CACHE, "ShMem", None)
            sender_account = shmem.GetAccountDataFromEmail(sender_email) if shmem is not None else None
            if sender_account:
                sender_name = sender_account.AgentData.CharacterName
        except EXPECTED_RUNTIME_ERRORS:
            pass
        return sender_name

    def _resolve_stats_cache_key_for_row(self, row) -> str:
        event_id = self._extract_row_event_id(row)
        if not event_id:
            return ""
        parsed = self._parse_drop_row(row)
        player_name = self._ensure_text(parsed.player_name).strip() if parsed else ""
        sender_email = self._extract_row_sender_email(row)
        return self._make_stats_cache_key(event_id, sender_email, player_name)

    def _get_cached_stats_text(self, cache: dict[str, str], event_key: str) -> str:
        lookup_key = self._ensure_text(event_key).strip()
        if not lookup_key:
            return ""
        return self._ensure_text(cache.get(lookup_key, "")).strip()

    def _resolve_live_item_id_for_row(self, row, prefer_unidentified: bool = False) -> int:
        parsed = self._parse_drop_row(row)
        target_name = self._clean_item_name(parsed.item_name) if parsed else ""
        target_rarity = self._ensure_text(parsed.rarity).strip() if parsed else ""
        target_rarity = target_rarity or "Unknown"
        recorded_item_id = max(0, int(parsed.item_id)) if parsed else 0

        try:
            bags = ItemArray.CreateBagList(1, 2, 3, 4)
            item_ids = list(ItemArray.GetItemArray(bags) or [])
        except EXPECTED_RUNTIME_ERRORS:
            item_ids = []

        if not item_ids:
            return 0

        item_id_set = {int(i) for i in item_ids}
        if recorded_item_id > 0 and recorded_item_id in item_id_set:
            return int(recorded_item_id)

        best_any = 0
        best_unidentified = 0
        for inv_item_id in item_ids:
            inv_item_id = int(inv_item_id)
            try:
                if not Item.IsNameReady(inv_item_id):
                    Item.RequestName(inv_item_id)
                    continue
            except EXPECTED_RUNTIME_ERRORS:
                continue

            try:
                inv_name = self._clean_item_name(Item.GetName(inv_item_id))
            except EXPECTED_RUNTIME_ERRORS:
                inv_name = ""
            if target_name and inv_name and not self._item_names_match(target_name, inv_name):
                continue

            inv_rarity = "Unknown"
            try:
                inv_rarity = self._ensure_text(Item.Rarity.GetRarity(inv_item_id)[1]).strip() or "Unknown"
            except EXPECTED_RUNTIME_ERRORS:
                inv_rarity = "Unknown"
            if target_rarity != "Unknown" and inv_rarity != target_rarity:
                # Keep as fallback when only rarity differs due transient name/rarity resolution.
                if best_any <= 0:
                    best_any = inv_item_id
                continue

            if best_any <= 0:
                best_any = inv_item_id
            try:
                is_identified = bool(Item.Usage.IsIdentified(inv_item_id))
            except EXPECTED_RUNTIME_ERRORS:
                is_identified = False
            if not is_identified and best_unidentified <= 0:
                best_unidentified = inv_item_id
                if prefer_unidentified:
                    break

        if prefer_unidentified and best_unidentified > 0:
            return int(best_unidentified)
        if best_any > 0:
            return int(best_any)
        return 0

    def _resolve_live_item_id_by_name(self, item_name: Any, prefer_identified: bool = False) -> int:
        target_name = self._clean_item_name(item_name)
        if not target_name:
            return 0
        try:
            bags = ItemArray.CreateBagList(1, 2, 3, 4)
            item_ids = list(ItemArray.GetItemArray(bags) or [])
        except EXPECTED_RUNTIME_ERRORS:
            item_ids = []
        if not item_ids:
            return 0
        best_any = 0
        best_identified = 0
        for inv_item_id in item_ids:
            inv_item_id = int(inv_item_id)
            try:
                if not Item.IsNameReady(inv_item_id):
                    Item.RequestName(inv_item_id)
                    continue
                inv_name = self._clean_item_name(Item.GetName(inv_item_id))
            except EXPECTED_RUNTIME_ERRORS:
                continue
            if not self._item_names_match(target_name, inv_name):
                continue
            if best_any <= 0:
                best_any = inv_item_id
            if prefer_identified:
                try:
                    if bool(Item.Usage.IsIdentified(inv_item_id)):
                        best_identified = inv_item_id
                        break
                except EXPECTED_RUNTIME_ERRORS:
                    pass
        if prefer_identified and best_identified > 0:
            return int(best_identified)
        if best_any > 0:
            return int(best_any)
        return 0

    def _resolve_live_item_id_by_signature(
        self,
        name_signature: Any,
        rarity_hint: Any = "",
        prefer_identified: bool = False,
    ) -> int:
        target_sig = self._ensure_text(name_signature).strip().lower()
        if not target_sig:
            return 0
        target_rarity = self._ensure_text(rarity_hint).strip() or "Unknown"
        try:
            bags = ItemArray.CreateBagList(1, 2, 3, 4)
            item_ids = list(ItemArray.GetItemArray(bags) or [])
        except EXPECTED_RUNTIME_ERRORS:
            item_ids = []
        if not item_ids:
            return 0

        best_any = 0
        best_identified = 0
        for inv_item_id in item_ids:
            inv_item_id = int(inv_item_id)
            try:
                if not Item.IsNameReady(inv_item_id):
                    Item.RequestName(inv_item_id)
                    continue
                inv_name = self._clean_item_name(Item.GetName(inv_item_id))
            except EXPECTED_RUNTIME_ERRORS:
                continue
            if not inv_name:
                continue
            if make_name_signature(inv_name) != target_sig:
                continue
            if target_rarity != "Unknown":
                try:
                    inv_rarity = self._ensure_text(Item.Rarity.GetRarity(inv_item_id)[1]).strip() or "Unknown"
                except EXPECTED_RUNTIME_ERRORS:
                    inv_rarity = "Unknown"
                if inv_rarity != target_rarity:
                    continue
            if best_any <= 0:
                best_any = inv_item_id
            if prefer_identified:
                try:
                    if bool(Item.Usage.IsIdentified(inv_item_id)):
                        best_identified = inv_item_id
                        break
                except EXPECTED_RUNTIME_ERRORS:
                    pass
        if prefer_identified and best_identified > 0:
            return int(best_identified)
        if best_any > 0:
            return int(best_any)
        return 0

    def _resolve_account_email_by_character_name(self, character_name: str) -> str:
        target_name = self._ensure_text(character_name).strip().lower()
        if not target_name:
            return ""
        try:
            shmem = getattr(GLOBAL_CACHE, "ShMem", None)
            if shmem is None:
                return ""
            my_email = self._ensure_text(Player.GetAccountEmail()).strip()
            my_account = shmem.GetAccountDataFromEmail(my_email) if my_email else None
            my_party_id = int(getattr(my_account.AgentPartyData, "PartyID", 0)) if my_account else 0
            my_map_id = int(getattr(my_account.AgentData.Map, "MapID", 0)) if my_account else 0
            for account in shmem.GetAllAccountData():
                account_email = self._ensure_text(getattr(account, "AccountEmail", "")).strip()
                if not account_email:
                    continue
                account_name = self._ensure_text(getattr(account.AgentData, "CharacterName", "")).strip().lower()
                if account_name != target_name:
                    continue
                if my_party_id > 0 and int(getattr(account.AgentPartyData, "PartyID", 0)) != my_party_id:
                    continue
                if my_map_id > 0 and int(getattr(account.AgentData.Map, "MapID", 0)) != my_map_id:
                    continue
                return account_email
        except EXPECTED_RUNTIME_ERRORS:
            return ""
        return ""

    def _send_inventory_action_to_email(self, receiver_email: str, action_code: str, action_payload: str = "", action_meta: str = "") -> bool:
        receiver = self._ensure_text(receiver_email).strip()
        if not receiver:
            return False
        try:
            sender_email = self._ensure_text(Player.GetAccountEmail()).strip()
            if not sender_email:
                return False
            sent_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email=sender_email,
                receiver_email=receiver,
                command=SharedCommandType.CustomBehaviors,
                params=(0.0, 0.0, 0.0, 0.0),
                ExtraData=(
                    self.inventory_action_tag,
                    self._ensure_text(action_code)[:31],
                    self._ensure_text(action_payload)[:31],
                    self._ensure_text(action_meta)[:31],
                ),
            )
            return sent_index != -1
        except EXPECTED_RUNTIME_ERRORS:
            return False

    def _send_tracker_stats_chunks_to_email(self, receiver_email: str, event_id: str, item_stats: str, tag: str = "TrackerStatsV1") -> bool:
        receiver = self._ensure_text(receiver_email).strip()
        event_id_text = self._ensure_text(event_id).strip()
        stats_text = self._ensure_text(item_stats).strip()
        if not receiver or not event_id_text or not stats_text:
            return False
        try:
            sender_email = self._ensure_text(Player.GetAccountEmail()).strip()
            if not sender_email:
                return False
            # Keep chunks conservative; 31-char shmem slots can truncate edge characters.
            chunks = build_name_chunks(stats_text, 24)
            for idx, total, chunk in chunks:
                sent_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email=sender_email,
                    receiver_email=receiver,
                    command=SharedCommandType.CustomBehaviors,
                    params=(0.0, 0.0, 0.0, 0.0),
                    ExtraData=(
                        self._ensure_text(tag).strip() or "TrackerStatsV1",
                        event_id_text[:31],
                        (chunk or "")[:31],
                        encode_name_chunk_meta(idx, total)[:31],
                    ),
                )
                if sent_index == -1:
                    return False
            return True
        except EXPECTED_RUNTIME_ERRORS:
            return False

    def _send_tracker_stats_payload_chunks_to_email(self, receiver_email: str, event_id: str, payload_text: str) -> bool:
        return self._send_tracker_stats_chunks_to_email(receiver_email, event_id, payload_text, tag="TrackerStatsV2")

    def _get_live_item_snapshot(self, item_id: int, item_name: str = "") -> dict[str, Any]:
        item_id = int(item_id or 0)
        if item_id <= 0:
            return {}
        snapshot: dict[str, Any] = {
            "name": "",
            "value": 0,
            "model_id": 0,
            "item_type": 0,
            "raw_mods": [],
        }
        try:
            clean_name = ""
            try:
                if Item.IsNameReady(item_id):
                    clean_name = self._clean_item_name(Item.GetName(item_id))
                else:
                    Item.RequestName(item_id)
            except EXPECTED_RUNTIME_ERRORS:
                clean_name = ""
            if not clean_name:
                clean_name = self._clean_item_name(item_name)
            snapshot["name"] = clean_name

            try:
                snapshot["value"] = max(0, self._safe_int(Item.Properties.GetValue(item_id), 0))
            except EXPECTED_RUNTIME_ERRORS:
                snapshot["value"] = 0
            try:
                snapshot["model_id"] = max(0, self._safe_int(Item.GetModelID(item_id), 0))
            except EXPECTED_RUNTIME_ERRORS:
                snapshot["model_id"] = 0
            try:
                item_type_int, _ = Item.GetItemType(item_id)
                snapshot["item_type"] = max(0, self._safe_int(item_type_int, 0))
            except EXPECTED_RUNTIME_ERRORS:
                snapshot["item_type"] = 0
                try:
                    item_instance = Item.item_instance(item_id)
                    if item_instance and getattr(item_instance, "item_type", None):
                        snapshot["item_type"] = max(0, self._safe_int(item_instance.item_type.ToInt(), 0))
                except EXPECTED_RUNTIME_ERRORS:
                    snapshot["item_type"] = 0

            raw_mods = []
            for mod in Item.Customization.Modifiers.GetModifiers(item_id):
                raw_mods.append((int(mod.GetIdentifier()), int(mod.GetArg1()), int(mod.GetArg2())))
            snapshot["raw_mods"] = raw_mods
        except EXPECTED_RUNTIME_ERRORS:
            return {}
        return snapshot

    def _build_item_snapshot_payload_from_live_item(self, item_id: int, item_name: str = "") -> str:
        snapshot = self._get_live_item_snapshot(item_id, item_name)
        if not snapshot:
            return ""
        try:
            payload = {
                "n": self._ensure_text(snapshot.get("name", "")),
                "v": int(self._safe_int(snapshot.get("value", 0), 0)),
                "m": int(self._safe_int(snapshot.get("model_id", 0), 0)),
                "t": int(self._safe_int(snapshot.get("item_type", 0), 0)),
                "mods": [
                    [int(mod[0]), int(mod[1]), int(mod[2])]
                    for mod in list(snapshot.get("raw_mods", []) or [])
                    if isinstance(mod, (list, tuple)) and len(mod) >= 3
                ],
            }
            return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        except EXPECTED_RUNTIME_ERRORS:
            return ""

    def _build_item_stats_from_snapshot(self, snapshot: dict[str, Any]) -> str:
        try:
            if not isinstance(snapshot, dict):
                return ""
            lines = []
            clean_name = self._clean_item_name(snapshot.get("name", ""))
            if "|" in clean_name:
                clean_name = clean_name.split("|", 1)[0].strip()
            if clean_name:
                lines.append(clean_name)

            value = max(0, self._safe_int(snapshot.get("value", 0), 0))
            if value > 0:
                lines.append(f"Value: {value} gold")

            raw_mods = []
            for mod in list(snapshot.get("raw_mods", []) or []):
                if not isinstance(mod, (list, tuple)) or len(mod) < 3:
                    continue
                raw_mods.append((int(mod[0]), int(mod[1]), int(mod[2])))
            if not raw_mods:
                return "\n".join(lines)

            req_attr = 0
            req_val = 0
            for ident, arg1, arg2 in raw_mods:
                if ident in (42920, 42120):
                    if int(arg2) > 0 and int(arg1) > 0:
                        lines.append(f"Damage: {int(arg2)}-{int(arg1)}")
                elif ident == 42936:
                    if int(arg1) > 0:
                        lines.append(f"Armor: {int(arg1)}" if int(arg2) <= 0 else f"Armor: {int(arg1)} (vs {int(arg2)})")
                elif ident == 10136:
                    req_attr = int(arg1)
                    req_val = int(arg2)
                elif ident == 9720:
                    lines.append("Improved sale value")
            if req_val > 0:
                attr_txt = ""
                try:
                    attr_txt = self._format_attribute_name(getattr(Attribute(req_attr), "name", ""))
                except EXPECTED_RUNTIME_ERRORS:
                    attr_txt = ""
                lines.append(f"Requires {req_val} {attr_txt}".rstrip())

            item_type = None
            item_type_int = max(0, self._safe_int(snapshot.get("item_type", 0), 0))
            if ItemType is not None:
                try:
                    item_type = ItemType(item_type_int)
                except EXPECTED_RUNTIME_ERRORS:
                    item_type = None

            item_attr_txt_for_known = ""
            if req_val > 0:
                try:
                    item_attr_txt_for_known = self._format_attribute_name(getattr(Attribute(req_attr), "name", ""))
                except EXPECTED_RUNTIME_ERRORS:
                    item_attr_txt_for_known = ""

            parsed_any_mod_line = False
            if self.mod_db is not None:
                parser_attr_txt = item_attr_txt_for_known
                if parse_modifiers is not None and item_type is not None:
                    try:
                        parsed = parse_modifiers(raw_mods, item_type, int(self._safe_int(snapshot.get("model_id", 0), 0)), self.mod_db)
                        item_attr_txt = self._format_attribute_name(getattr(parsed.attribute, "name", ""))
                        if item_attr_txt:
                            parser_attr_txt = item_attr_txt
                            item_attr_txt_for_known = item_attr_txt
                        for mod in parsed.weapon_mods:
                            nm = self._ensure_text(getattr(mod.weapon_mod, "name", "")).strip()
                            if not nm:
                                continue
                            val = int(getattr(mod, "value", 0))
                            matched_mods = list(getattr(mod, "matched_modifiers", []) or [])
                            desc = self._ensure_text(getattr(mod.weapon_mod, "description", "")).strip()
                            rendered_lines = self._render_mod_description_template(desc, matched_mods, val, parser_attr_txt)
                            if rendered_lines:
                                lines.extend(rendered_lines)
                                parsed_any_mod_line = True
                            else:
                                lines.append(f"{nm} ({val})" if val else nm)
                                parsed_any_mod_line = True
                        for rune in parsed.runes:
                            rune_name = self._ensure_text(getattr(rune.rune, "name", "")).strip()
                            rune_desc = self._ensure_text(getattr(rune.rune, "description", "")).strip()
                            rune_mods = list(getattr(rune, "modifiers", []) or [])
                            rendered_lines = self._render_mod_description_template(rune_desc, rune_mods, 0, parser_attr_txt)
                            if rune_name:
                                lines.append(rune_name)
                                parsed_any_mod_line = True
                            if rendered_lines:
                                lines.extend(rendered_lines)
                                parsed_any_mod_line = True
                    except EXPECTED_RUNTIME_ERRORS:
                        pass
                # Broad fallback matching is only trustworthy when item type is known.
                # With unknown type (common on remote payloads), it can produce false rune/mod lines.
                if item_type is not None:
                    if not parsed_any_mod_line:
                        lines.extend(self._collect_fallback_mod_lines(raw_mods, parser_attr_txt, item_type))
                    lines.extend(self._collect_fallback_rune_lines(raw_mods, parser_attr_txt))

            if not parsed_any_mod_line:
                name_mod_lines = self._extract_mod_lines_from_item_name(snapshot.get("name", ""))
                if name_mod_lines:
                    lines.extend(name_mod_lines)
                    parsed_any_mod_line = True

            lines.extend(self._build_known_spellcast_mod_lines(raw_mods, item_attr_txt_for_known, item_type))

            normalized_lines = []
            split_pattern = re.compile(
                r"(?i)(?<!^)(requires\s+\d+|damage:\s*\d|armor:\s*\d|energy\s*[+-]\d|halves\s|reduces\s|value:\s*\d|improved sale value)"
            )
            for line in lines:
                txt = self._ensure_text(line).strip()
                if not txt:
                    continue
                # Fix occasional glued lines such as "Armor16(vs8)requires11 tactics".
                while True:
                    m = split_pattern.search(txt)
                    if not m:
                        break
                    left = txt[:m.start()].strip()
                    right = txt[m.start():].strip()
                    if left:
                        normalized_lines.append(left)
                    txt = right
                if txt:
                    normalized_lines.append(txt)

            return self._normalize_stats_text("\n".join(normalized_lines))
        except EXPECTED_RUNTIME_ERRORS:
            return ""

    def _normalize_stats_text(self, stats_text: Any) -> str:
        text = self._ensure_text(stats_text).strip()
        if not text:
            return ""
        split_pattern = re.compile(
            r"(?i)(?<!^)(requires\s+\d+|damage:\s*\d|damage\s*\d|armor:\s*\d|armor\s*\d|energy\s*[+-]\d|halves\s|reduces\s|value:\s*\d|improved sale value)"
        )
        normalized_lines = []
        for raw in text.splitlines():
            txt = self._ensure_text(raw).strip()
            if not txt:
                continue
            while True:
                m = split_pattern.search(txt)
                if not m:
                    break
                left = txt[:m.start()].strip()
                right = txt[m.start():].strip()
                if left:
                    normalized_lines.append(left)
                txt = right
            if txt:
                normalized_lines.append(txt)

        canonical = []
        seen = set()
        for line in normalized_lines:
            l = self._ensure_text(line).strip()
            if not l:
                continue
            l = re.sub(r"(?i)^damage\s*(\d+\s*-\s*\d+)$", r"Damage: \1", l)
            l = re.sub(r"(?i)^armor\s*(\d+)(\b.*)$", r"Armor: \1\2", l)
            l = re.sub(r"(?i)^requires\s*(\d+)\s*", r"Requires \1 ", l)
            l = re.sub(r"\s+", " ", l).strip()
            key = re.sub(r"[^a-z0-9]+", "", l.lower())
            if not key or key in seen:
                continue
            seen.add(key)
            canonical.append(l)
        canonical = prune_generic_attribute_bonus_lines(canonical)
        canonical = sort_stats_lines_like_ingame(canonical)
        return "\n".join(canonical)

    def _build_item_stats_from_payload_text(self, payload_text: str, fallback_item_name: str = "") -> str:
        payload_raw = self._ensure_text(payload_text).strip()
        if not payload_raw:
            return ""
        try:
            payload = json.loads(payload_raw)
            if not isinstance(payload, dict):
                return ""
        except EXPECTED_RUNTIME_ERRORS:
            return ""
        snapshot = {
            "name": self._clean_item_name(payload.get("n", "")) or self._clean_item_name(fallback_item_name),
            "value": self._safe_int(payload.get("v", 0), 0),
            "model_id": self._safe_int(payload.get("m", 0), 0),
            "item_type": self._safe_int(payload.get("t", 0), 0),
            "raw_mods": payload.get("mods", []),
        }
        return self._build_item_stats_from_snapshot(snapshot)

    def _clear_event_stats_cache(self, event_id: str, sender_email: str = "", player_name: str = "", clear_all_matching: bool = False):
        event_id_key = self._ensure_text(event_id).strip()
        if not event_id_key:
            return
        scoped_key = self._make_stats_cache_key(event_id_key, sender_email, player_name)
        clear_keys = {scoped_key} if scoped_key else set()
        if clear_all_matching:
            suffix = f":{event_id_key}".lower()
            cache_maps = (
                self.stats_by_event,
                self.stats_payload_by_event,
                self.stats_chunk_buffers,
                self.stats_payload_chunk_buffers,
                self.stats_render_cache_by_event,
                self.remote_stats_request_last_by_event,
                self.remote_stats_pending_by_event,
                self.stats_name_signature_by_event,
            )
            for cache_map in cache_maps:
                for key in list(cache_map.keys()):
                    key_text = self._ensure_text(key).strip().lower()
                    if key_text.endswith(suffix):
                        clear_keys.add(self._ensure_text(key).strip())
        for event_key in clear_keys:
            self.stats_by_event.pop(event_key, None)
            self.stats_payload_by_event.pop(event_key, None)
            self.stats_chunk_buffers.pop(event_key, None)
            self.stats_payload_chunk_buffers.pop(event_key, None)
            self.stats_render_cache_by_event.pop(event_key, None)
            self.remote_stats_request_last_by_event.pop(event_key, None)
            self.remote_stats_pending_by_event.pop(event_key, None)
            self.stats_name_signature_by_event.pop(event_key, None)

    def _render_payload_stats_cached(self, cache_key: str, payload_text: str, fallback_item_name: str = "") -> str:
        event_key = self._ensure_text(cache_key).strip()
        payload_raw = self._ensure_text(payload_text).strip()
        if not event_key or not payload_raw:
            return ""
        cached_rendered = get_cached_rendered_stats(self.stats_render_cache_by_event, event_key, payload_raw)
        if cached_rendered:
            cached = self.stats_render_cache_by_event.get(event_key, None)
            if isinstance(cached, dict):
                cached["updated_at"] = time.time()
            return cached_rendered
        rendered = self._build_item_stats_from_payload_text(payload_raw, fallback_item_name).strip()
        update_render_cache(self.stats_render_cache_by_event, event_key, payload_raw, rendered, time.time())
        return rendered

    def _request_remote_stats_for_row(self, row):
        parsed = self._parse_drop_row(row)
        if parsed is None:
            return
        target_player = self._ensure_text(parsed.player_name).strip()
        if not target_player:
            return
        my_name = self._ensure_text(Player.GetName()).strip()
        if my_name and target_player.lower() == my_name.lower():
            return
        event_id = self._extract_row_event_id(row)
        item_id = self._extract_row_item_id(row)
        item_name = self._clean_item_name(parsed.item_name)
        item_rarity = self._ensure_text(parsed.rarity).strip() or "Unknown"
        if not event_id:
            return
        event_cache_key = self._resolve_stats_cache_key_for_row(row)
        if self._get_cached_stats_text(self.stats_payload_by_event, event_cache_key):
            return
        now_ts = time.time()
        pending_ts = float(self.remote_stats_pending_by_event.get(event_cache_key, 0.0))
        if pending_ts > 0 and (now_ts - pending_ts) < 8.0:
            return
        last_ts = float(self.remote_stats_request_last_by_event.get(event_cache_key, 0.0))
        if (now_ts - last_ts) < 1.5:
            return
        target_email = self._resolve_account_email_by_character_name(target_player)
        if not target_email:
            return
        sent = False
        if item_id > 0:
            sent = self._send_inventory_action_to_email(target_email, "push_item_stats", str(item_id), event_id)
        if not sent:
            item_signature = self._ensure_text(self.stats_name_signature_by_event.get(event_cache_key, "")).strip().lower()
            if not item_signature and item_name:
                item_signature = make_name_signature(item_name)
            if item_signature:
                sig_payload = item_signature[:8]
                if item_rarity:
                    sig_payload = f"{sig_payload}|{item_rarity[:20]}"
                sent_by_sig = self._send_inventory_action_to_email(
                    target_email,
                    "push_item_stats_sig",
                    sig_payload,
                    event_id,
                )
                sent = sent or sent_by_sig
        if (not sent) and item_name and len(item_name) <= 31:
            sent_by_name = self._send_inventory_action_to_email(
                target_email,
                "push_item_stats_name",
                item_name,
                event_id,
            )
            sent = sent or sent_by_name
        if sent:
            self.remote_stats_request_last_by_event[event_cache_key] = now_ts
            self.remote_stats_pending_by_event[event_cache_key] = now_ts
            if self.verbose_shmem_item_logs:
                Py4GW.Console.Log(
                    "DropViewer",
                    f"STATS REQ ev={event_id} player={target_player} item_id={item_id} item_name={item_name}",
                    Py4GW.Console.MessageType.Info,
                )

    def _build_item_stats_from_live_item(self, item_id: int, item_name: str = "") -> str:
        snapshot = self._get_live_item_snapshot(item_id, item_name)
        if not snapshot:
            return ""
        return self._build_item_stats_from_snapshot(snapshot)

    def _stats_text_is_basic(self, stats_text: Any) -> bool:
        text = self._normalize_stats_text(stats_text)
        if not text:
            return True
        lines = [self._ensure_text(line).strip() for line in text.splitlines() if self._ensure_text(line).strip()]
        if not lines:
            return True
        lower_lines = [line.lower() for line in lines]
        detail_markers = (
            "rune",
            "insignia",
            "halves ",
            "reduces ",
            "lengthens ",
            "increases ",
            "while ",
            "chance while using skills",
            "(chance:",
            "improved sale value",
        )
        for line in lower_lines:
            if any(marker in line for marker in detail_markers):
                return False
            if re.match(r"^[a-z][a-z ']+\s*\+\s*\d+\s*\(\d+% chance while using skills\)$", line):
                return False
        # Name-only or name + value rows are considered basic.
        if len(lines) <= 2:
            return True
        # Three+ generic lines without detail markers are still likely non-useful.
        return True

    def _identify_item_from_row(self, row) -> bool:
        parsed = self._parse_drop_row(row)
        target_player = self._ensure_text(parsed.player_name).strip() if parsed else ""
        my_name = self._ensure_text(Player.GetName()).strip()
        event_id = self._extract_row_event_id(row)
        if target_player and my_name and target_player.lower() != my_name.lower():
            remote_item_id = self._extract_row_item_id(row)
            target_email = self._resolve_account_email_by_character_name(target_player)
            if not target_email:
                self.set_status(f"Identify failed: follower '{target_player}' not found")
                return False
            if remote_item_id <= 0:
                self.set_status("Identify failed: remote item_id unavailable")
                return False
            if self._send_inventory_action_to_email(target_email, "id_item_id", str(remote_item_id), event_id):
                if event_id:
                    self._clear_event_stats_cache(event_id, target_email, target_player)
                    self._set_row_item_stats(row, "")
                    if self.selected_log_row and isinstance(self.selected_log_row, list):
                        if self._extract_row_event_id(self.selected_log_row) == event_id:
                            self._set_row_item_stats(self.selected_log_row, "")
                self.set_status(f"Identify request sent to {target_player}")
                return True
            self.set_status(f"Identify failed: could not send request to {target_player}")
            return False

        item_id = self._resolve_live_item_id_for_row(row, prefer_unidentified=True)
        if item_id <= 0:
            self.set_status("Identify failed: live item not found in inventory")
            return False
        self._set_row_item_id(row, item_id)
        try:
            if Item.Usage.IsIdentified(item_id):
                self.set_status("Item already identified")
                return False
        except EXPECTED_RUNTIME_ERRORS:
            pass
        kit_id = 0
        try:
            kit_id = int(GLOBAL_CACHE.Inventory.GetFirstIDKit())
        except EXPECTED_RUNTIME_ERRORS:
            kit_id = 0
        if kit_id <= 0:
            self.set_status("Identify failed: no ID kit found")
            return False
        try:
            result = GLOBAL_CACHE.Inventory.IdentifyItem(item_id, kit_id)
            if result is False:
                self.set_status("Identify failed: API rejected request")
                return False
            if event_id:
                row_sender_email = self._extract_row_sender_email(row)
                row_player_name = self._ensure_text(parsed.player_name).strip() if parsed else ""
                self._clear_event_stats_cache(event_id, row_sender_email, row_player_name)
                self._set_row_item_stats(row, "")
                if self.selected_log_row and isinstance(self.selected_log_row, list):
                    if self._extract_row_event_id(self.selected_log_row) == event_id:
                        self._set_row_item_stats(self.selected_log_row, "")
            self.set_status("Identify queued for selected item")
            return True
        except EXPECTED_RUNTIME_ERRORS as e:
            self.set_status(f"Identify failed: {e}")
            return False

    def _get_row_stats_text(self, row) -> str:
        event_id = self._extract_row_event_id(row)
        event_cache_key = self._resolve_stats_cache_key_for_row(row)
        parsed = self._parse_drop_row(row)
        row_player = self._ensure_text(parsed.player_name).strip() if parsed else ""
        my_player = self._ensure_text(Player.GetName()).strip()
        is_local_row = bool(row_player and my_player and row_player.lower() == my_player.lower())

        # For follower-owned rows, never resolve by local inventory name matching on leader.
        # That can bind to unrelated local items and overwrite valid remote stats.
        if is_local_row:
            live_item_id = self._resolve_live_item_id_for_row(row, prefer_unidentified=False)
            if live_item_id > 0:
                self._set_row_item_id(row, live_item_id)
                live_text = self._build_item_stats_from_live_item(
                    live_item_id,
                    "",
                ).strip()
                if live_text:
                    # Prefer local live item data so stats update after identification.
                    self._set_row_item_stats(row, live_text)
                    if event_cache_key:
                        self.stats_by_event[event_cache_key] = live_text
                    if self.selected_log_row and isinstance(self.selected_log_row, list):
                        selected_event_id = self._extract_row_event_id(self.selected_log_row)
                        if selected_event_id and selected_event_id == event_id:
                            self._set_row_item_stats(self.selected_log_row, live_text)
                    return live_text
        payload_text = self._get_cached_stats_text(self.stats_payload_by_event, event_cache_key)
        if event_cache_key and payload_text:
            rendered = self._render_payload_stats_cached(
                event_cache_key,
                payload_text,
                self._ensure_text(parsed.item_name) if parsed else "",
            ).strip()
            if rendered:
                self._set_row_item_stats(row, rendered)
                self.stats_by_event[event_cache_key] = rendered
                return rendered

        text = self._extract_row_item_stats(row)
        if text:
            normalized_text = self._normalize_stats_text(text)
            self._set_row_item_stats(row, normalized_text)
            if event_cache_key:
                self.stats_by_event[event_cache_key] = normalized_text
            if not is_local_row and (
                (not payload_text) and self._stats_text_is_basic(normalized_text)
            ):
                self._request_remote_stats_for_row(row)
            return normalized_text
        if event_cache_key:
            cached_text = self._normalize_stats_text(self._get_cached_stats_text(self.stats_by_event, event_cache_key))
            if cached_text:
                self._set_row_item_stats(row, cached_text)
                return cached_text
            if not is_local_row:
                self._request_remote_stats_for_row(row)
            return ""
        return ""

    def _build_selected_row_debug_lines(self, row) -> list[str]:
        lines = []
        parsed = self._parse_drop_row(row)
        if parsed is None:
            return lines
        event_id = self._extract_row_event_id(row)
        item_id = self._extract_row_item_id(row)
        row_player = self._ensure_text(parsed.player_name).strip()
        row_name = self._clean_item_name(parsed.item_name)
        my_player = self._ensure_text(Player.GetName()).strip()
        is_local_row = bool(row_player and my_player and row_player.lower() == my_player.lower())
        lines.append(f"event_id={event_id or '-'}")
        lines.append(f"row_player={row_player or '-'} local_row={is_local_row}")
        lines.append(f"row_item_name={row_name or '-'} row_item_id={item_id}")
        event_cache_key = self._resolve_stats_cache_key_for_row(row)
        if event_cache_key:
            last_req = float(self.remote_stats_request_last_by_event.get(event_cache_key, 0.0))
            pending_req = float(self.remote_stats_pending_by_event.get(event_cache_key, 0.0))
            now_ts = time.time()
            lines.append(
                f"req_last_age_s={(now_ts - last_req):.2f}" if last_req > 0 else "req_last_age_s=-"
            )
            lines.append(
                f"req_pending_age_s={(now_ts - pending_req):.2f}" if pending_req > 0 else "req_pending_age_s=-"
            )

        payload_text = self._get_cached_stats_text(self.stats_payload_by_event, event_cache_key)
        lines.append(f"payload_cached={bool(payload_text)} payload_len={len(payload_text)}")
        if payload_text:
            preview = payload_text[:220].replace("\n", " ")
            lines.append(f"payload_head={preview}")
        if payload_text:
            try:
                payload = json.loads(payload_text)
                if isinstance(payload, dict):
                    mods = list(payload.get("mods", []) or [])
                    lines.append(
                        f"payload_name={self._clean_item_name(payload.get('n', '')) or '-'} "
                        f"type={self._safe_int(payload.get('t', 0), 0)} model={self._safe_int(payload.get('m', 0), 0)} "
                        f"value={self._safe_int(payload.get('v', 0), 0)} mods={len(mods)}"
                    )
                    for idx, mod in enumerate(mods[:30]):
                        if isinstance(mod, (list, tuple)) and len(mod) >= 3:
                            lines.append(f"mod[{idx}] id={self._safe_int(mod[0], 0)} a1={self._safe_int(mod[1], 0)} a2={self._safe_int(mod[2], 0)}")
                else:
                    lines.append("payload_parse=non-dict")
            except EXPECTED_RUNTIME_ERRORS as e:
                lines.append(f"payload_parse_error={e}")
        elif is_local_row:
            live_item_id = self._resolve_live_item_id_for_row(row, prefer_unidentified=False)
            lines.append(f"live_resolved_item_id={live_item_id}")
            if live_item_id > 0:
                snap = self._get_live_item_snapshot(live_item_id, row_name)
                mods = list(snap.get("raw_mods", []) or [])
                lines.append(
                    f"live_name={self._clean_item_name(snap.get('name', '')) or '-'} "
                    f"type={self._safe_int(snap.get('item_type', 0), 0)} model={self._safe_int(snap.get('model_id', 0), 0)} "
                    f"value={self._safe_int(snap.get('value', 0), 0)} mods={len(mods)}"
                )
                for idx, mod in enumerate(mods[:30]):
                    if isinstance(mod, (list, tuple)) and len(mod) >= 3:
                        lines.append(f"mod[{idx}] id={self._safe_int(mod[0], 0)} a1={self._safe_int(mod[1], 0)} a2={self._safe_int(mod[2], 0)}")

        rendered_text = self._ensure_text(self._extract_row_item_stats(row)).strip()
        if rendered_text:
            lines.append("rendered_lines:")
            for idx, line in enumerate(rendered_text.splitlines()[:25]):
                lines.append(f"  [{idx}] {self._ensure_text(line).strip()}")
        return lines

    def _item_names_match(self, selected_name: Any, row_name: Any) -> bool:
        selected_norm = self._normalize_item_name(selected_name)
        row_norm = self._normalize_item_name(row_name)
        if selected_norm == row_norm:
            return True
        if selected_norm.endswith("s") and selected_norm[:-1] == row_norm:
            return True
        if row_norm.endswith("s") and row_norm[:-1] == selected_norm:
            return True
        return False

    def _row_matches_selected_item(self, row) -> bool:
        parsed = self._parse_drop_row(row)
        if not self.selected_item_key or parsed is None:
            return False
        sel_name, sel_rarity = self.selected_item_key
        row_rarity = self._ensure_text(parsed.rarity).strip() or "Unknown"
        if row_rarity != sel_rarity:
            return False
        return self._item_names_match(sel_name, parsed.item_name)

    def _find_best_row_for_item(self, item_name: str, rarity: str, rows) -> Any:
        if not rows:
            return None
        best_with_item_id = None
        best_any = None
        for row in reversed(list(rows)):
            parsed = self._parse_drop_row(row)
            if parsed is None:
                continue
            row_rarity = self._ensure_text(parsed.rarity).strip() or "Unknown"
            if row_rarity != rarity:
                continue
            if not self._item_names_match(item_name, parsed.item_name):
                continue
            if best_any is None:
                best_any = row
            if self._extract_row_item_id(row) > 0:
                best_with_item_id = row
                break
        return list(best_with_item_id) if best_with_item_id is not None else (list(best_any) if best_any is not None else None)

    def _find_best_row_for_item_and_character(self, item_name: str, rarity: str, character_name: str, rows=None) -> Any:
        pool = rows if rows is not None else self.raw_drops
        if not pool:
            return None
        target_char = self._ensure_text(character_name).strip().lower()
        if not target_char:
            return None
        best_with_item_id = None
        best_any = None
        for row in reversed(list(pool)):
            parsed = self._parse_drop_row(row)
            if parsed is None:
                continue
            row_char = self._ensure_text(parsed.player_name).strip().lower()
            if row_char != target_char:
                continue
            row_rarity = self._ensure_text(parsed.rarity).strip() or "Unknown"
            if row_rarity != rarity:
                continue
            if not self._item_names_match(item_name, parsed.item_name):
                continue
            if best_any is None:
                best_any = row
            if self._extract_row_item_id(row) > 0:
                best_with_item_id = row
                break
        return list(best_with_item_id) if best_with_item_id is not None else (list(best_any) if best_any is not None else None)

    def _identify_item_for_all_characters(self, item_name: str, rarity: str, rows=None) -> bool:
        pool = rows if rows is not None else self.raw_drops
        if not pool:
            self.set_status("Identify failed: no matching rows")
            return False

        target_chars = []
        seen_chars = set()
        for row in reversed(list(pool)):
            parsed = self._parse_drop_row(row)
            if parsed is None:
                continue
            row_rarity = self._ensure_text(parsed.rarity).strip() or "Unknown"
            if row_rarity != rarity:
                continue
            if not self._item_names_match(item_name, parsed.item_name):
                continue
            char_name = self._ensure_text(parsed.player_name).strip()
            if not char_name:
                continue
            char_key = char_name.lower()
            if char_key in seen_chars:
                continue
            seen_chars.add(char_key)
            target_chars.append(char_name)

        if not target_chars:
            self.set_status("Identify failed: no matching characters")
            return False

        success = 0
        selected_row = None
        for char_name in target_chars:
            target_row = self._find_best_row_for_item_and_character(item_name, rarity, char_name, pool)
            if target_row is None:
                continue
            if self._identify_item_from_row(target_row):
                success += 1
                if selected_row is None:
                    selected_row = target_row

        if selected_row is not None:
            self.selected_log_row = selected_row

        total = len(target_chars)
        if success <= 0:
            self.set_status(f"Identify failed for all characters ({total})")
            return False
        if success < total:
            self.set_status(f"Identify sent to {success}/{total} characters")
            return True
        self.set_status(f"Identify sent to all {total} characters")
        return True

    def _collect_selected_item_stats(self):
        if not self.selected_item_key:
            return None

        sel_name, sel_rarity = self.selected_item_key
        total_qty = 0
        total_count = 0
        by_character = {}

        for row in self.raw_drops:
            if not self._row_matches_selected_item(row):
                continue

            parsed = self._parse_drop_row(row)
            if parsed is None:
                continue
            qty = int(parsed.quantity)
            if qty < 1:
                qty = 1
            character = self._ensure_text(parsed.player_name).strip() or "Unknown"

            total_qty += qty
            total_count += 1
            if character not in by_character:
                by_character[character] = {"Quantity": 0, "Count": 0}
            by_character[character]["Quantity"] += qty
            by_character[character]["Count"] += 1

        if total_count <= 0:
            return None

        sorted_characters = sorted(
            by_character.items(),
            key=lambda kv: (-kv[1]["Quantity"], -kv[1]["Count"], kv[0].lower())
        )
        return {
            "name": sel_name,
            "rarity": sel_rarity,
            "quantity": total_qty,
            "count": total_count,
            "characters": sorted_characters,
        }

    def _draw_selected_item_details(self):
        stats = self._collect_selected_item_stats()
        if not stats:
            return

        PyImGui.separator()
        PyImGui.text("Selected Item Stats")
        PyImGui.text_colored(
            f"{stats['name']} ({stats['rarity']})",
            self._get_rarity_color(stats["rarity"])
        )
        PyImGui.text(f"Total Quantity: {stats['quantity']}")
        PyImGui.text(f"Drop Count: {stats['count']}")

        if self.selected_log_row and self._row_matches_selected_item(self.selected_log_row):
            selected_parsed = self._parse_drop_row(self.selected_log_row)
            selected_char = self._ensure_text(selected_parsed.player_name if selected_parsed else "").strip() or "Unknown"
            selected_map = self._ensure_text(selected_parsed.map_name if selected_parsed else "").strip() or "Unknown"
            selected_ts = self._ensure_text(selected_parsed.timestamp if selected_parsed else "").strip() or "Unknown"
            PyImGui.text(f"Selected Entry: {selected_char} | {selected_map} | {selected_ts}")
            stats_text = self._get_row_stats_text(self.selected_log_row)
            if stats_text:
                PyImGui.separator()
                PyImGui.text("Item Mods / Stats")
                for line in stats_text.splitlines():
                    line_txt = self._ensure_text(line).strip()
                    if line_txt:
                        PyImGui.text(line_txt)
            else:
                PyImGui.text_colored("No detailed mod stats available for this row.", (0.78, 0.78, 0.78, 1.0))
            if self.debug_item_stats_panel:
                debug_lines = self._build_selected_row_debug_lines(self.selected_log_row)
                PyImGui.separator()
                PyImGui.text_colored("Debug Item Pipeline", (0.95, 0.78, 0.38, 1.0))
                if self._styled_button("Copy Debug", "secondary", tooltip="Copy debug pipeline text to clipboard."):
                    try:
                        PyImGui.set_clipboard_text("\n".join(debug_lines))
                        self.set_status("Debug pipeline copied to clipboard")
                    except EXPECTED_RUNTIME_ERRORS as e:
                        self.set_status(f"Clipboard copy failed: {e}")
                if PyImGui.begin_child(
                    "DropTrackerItemDebugPanel",
                    size=(0.0, float(self.debug_item_stats_panel_height)),
                    border=True,
                    flags=PyImGui.WindowFlags.HorizontalScrollbar
                ):
                    for line in debug_lines:
                        PyImGui.text(self._ensure_text(line))
                    PyImGui.end_child()

        flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp
        if PyImGui.begin_table("DropTrackerSelectedItemCharacters", 3, flags, 0.0, 150.0):
            PyImGui.table_setup_column("Character")
            PyImGui.table_setup_column("Qty")
            PyImGui.table_setup_column("Drops")
            PyImGui.table_headers_row()

            selected_char_name = ""
            if self.selected_log_row and self._row_matches_selected_item(self.selected_log_row):
                selected_parsed = self._parse_drop_row(self.selected_log_row)
                selected_char_name = self._ensure_text(selected_parsed.player_name if selected_parsed else "").strip().lower()

            for char_idx, (character, char_stats) in enumerate(stats["characters"]):
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                row_is_selected = bool(selected_char_name and selected_char_name == self._ensure_text(character).strip().lower())
                if PyImGui.selectable(
                    f"{character}##char_pick_{char_idx}",
                    row_is_selected,
                    PyImGui.SelectableFlags.NoFlag,
                    (0.0, 0.0)
                ):
                    target_row = self._find_best_row_for_item_and_character(stats["name"], stats["rarity"], character)
                    if target_row is not None:
                        self.selected_log_row = target_row
                if PyImGui.is_item_hovered():
                    ImGui.show_tooltip("Click to view this character's item stats.")
                PyImGui.table_set_column_index(1)
                PyImGui.text(str(char_stats["Quantity"]))
                PyImGui.table_set_column_index(2)
                PyImGui.text(str(char_stats["Count"]))
            PyImGui.end_table()

    def _get_session_duration_text(self):
        if len(self.raw_drops) < 2:
            return "00:00"
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            first_row = self._parse_drop_row(self.raw_drops[0]) if self.raw_drops else None
            last_row = self._parse_drop_row(self.raw_drops[-1]) if self.raw_drops else None
            if first_row is None or last_row is None:
                return "--:--"
            first_ts = datetime.datetime.strptime(first_row.timestamp, fmt)
            last_ts = datetime.datetime.strptime(last_row.timestamp, fmt)
            total_seconds = max(0, int((last_ts - first_ts).total_seconds()))
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            return f"{minutes:02d}:{seconds:02d}"
        except EXPECTED_RUNTIME_ERRORS:
            return "--:--"

    def _ui_colors(self):
        return default_ui_colors()

    def _push_button_style(self, variant: str = "secondary"):
        c = self._ui_colors()
        styles = {
            "primary": (c["primary_btn"], c["primary_hover"], c["primary_active"], (1.0, 1.0, 1.0, 1.0)),
            "secondary": (c["secondary_btn"], c["secondary_hover"], c["secondary_active"], (0.96, 0.96, 0.98, 1.0)),
            "success": (c["success_btn"], c["success_hover"], c["success_active"], (1.0, 1.0, 1.0, 1.0)),
            "warning": (c["warn_btn"], c["warn_hover"], c["warn_active"], (1.0, 0.98, 0.90, 1.0)),
            "danger": (c["danger_btn"], c["danger_hover"], c["danger_active"], (1.0, 0.95, 0.95, 1.0)),
        }
        btn, hover, active, text_col = styles.get(variant, styles["secondary"])
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, btn)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hover)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, text_col)

    def _styled_button(self, label: str, variant: str = "secondary", width: float = 0.0, height: float = 0.0, tooltip: str = ""):
        self._push_button_style(variant)
        clicked = PyImGui.button(label, width, height)
        PyImGui.pop_style_color(4)
        if tooltip and PyImGui.is_item_hovered():
            ImGui.show_tooltip(tooltip)
        return clicked

    def _draw_section_header(self, title: str):
        c = self._ui_colors()
        PyImGui.text_colored(title, c["accent"])
        PyImGui.separator()

    def _draw_status_toast(self, message: str):
        msg = self._ensure_text(message).strip()
        if not msg:
            return
        col = self._status_color(msg)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, (col[0] * 0.22, col[1] * 0.22, col[2] * 0.22, 0.96))
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, (col[0], col[1], col[2], 0.95))
        if PyImGui.begin_child("DropTrackerStatusToast", size=(0, 28), border=True, flags=PyImGui.WindowFlags.NoScrollbar):
            PyImGui.text_colored(msg, col)
            PyImGui.end_child()
        PyImGui.pop_style_color(2)

    def _draw_rarity_chips(self, prefix: str, rarities: list[str]):
        c = self._ui_colors()
        PyImGui.text_colored(prefix, c["muted"])
        if not rarities:
            PyImGui.same_line(0.0, 6.0)
            PyImGui.text_colored("[None]", c["muted"])
            return
        for idx, rarity in enumerate(rarities):
            PyImGui.same_line(0.0, 6.0)
            r, g, b, a = self._get_rarity_color(rarity)
            PyImGui.text_colored(f"[{rarity}]", (r, g, b, a))
            if idx >= 6:
                PyImGui.same_line(0.0, 6.0)
                PyImGui.text_colored("...", c["muted"])
                break

    def _status_color(self, msg: str):
        txt = self._ensure_text(msg).lower()
        if "fail" in txt or "error" in txt:
            return (1.0, 0.46, 0.42, 1.0)
        if "warn" in txt:
            return (1.0, 0.80, 0.34, 1.0)
        return (0.40, 0.95, 0.56, 1.0)

    def _draw_metric_card(self, card_id, title, value, accent_color):
        c = self._ui_colors()
        PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, c["panel_bg"])
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, (0.28, 0.35, 0.43, 0.72))
        if PyImGui.begin_child(card_id, size=(0, 52), border=True, flags=PyImGui.WindowFlags.NoFlag):
            PyImGui.text_colored(title, accent_color)
            PyImGui.text_colored(value, (0.94, 0.96, 1.0, 1.0))
            PyImGui.end_child()
        PyImGui.pop_style_color(2)

    def _draw_summary_bar(self, filtered_rows):
        total_qty_without_gold = 0
        rare_count = 0
        gold_qty = 0
        for row in filtered_rows:
            parsed = self._parse_drop_row(row)
            if parsed is None:
                continue
            qty = int(parsed.quantity)
            rarity = self._ensure_text(parsed.rarity).strip() or "Unknown"
            if self._is_rare_rarity(rarity):
                rare_count += 1
            if self._is_gold_row(row):
                gold_qty += qty
            else:
                total_qty_without_gold += qty

        session_time = self._get_session_duration_text()

        c = self._ui_colors()
        PyImGui.text_colored("Session Snapshot", c["accent"])
        flags = PyImGui.TableFlags.SizingStretchSame
        if PyImGui.begin_table("DropViewerSummary", 4, flags):
            PyImGui.table_next_row()

            PyImGui.table_set_column_index(0)
            self._draw_metric_card("CardSession", "Session", session_time, (0.55, 0.85, 1.0, 1.0))
            PyImGui.table_set_column_index(1)
            self._draw_metric_card("CardDrops", "Total Drops", str(total_qty_without_gold), (0.8, 0.9, 1.0, 1.0))
            PyImGui.table_set_column_index(2)
            self._draw_metric_card("CardGold", "Gold Value", f"{gold_qty:,}", (0.72, 0.72, 0.72, 1.0))
            PyImGui.table_set_column_index(3)
            self._draw_metric_card("CardRare", "Rare Drops", str(rare_count), (1.0, 0.84, 0.0, 1.0))

            PyImGui.end_table()

    def _draw_runtime_controls(self):
        draw_runtime_controls_panel(self, PyImGui)

    def _get_selected_id_rarities(self):
        rarities = []
        if self.id_sel_white:
            rarities.append("White")
        if self.id_sel_blue:
            rarities.append("Blue")
        if self.id_sel_green:
            rarities.append("Green")
        if self.id_sel_purple:
            rarities.append("Purple")
        if self.id_sel_gold:
            rarities.append("Gold")
        return rarities

    def _get_selected_salvage_rarities(self):
        rarities = []
        if self.salvage_sel_white:
            rarities.append("White")
        if self.salvage_sel_blue:
            rarities.append("Blue")
        if self.salvage_sel_green:
            rarities.append("Green")
        if self.salvage_sel_purple:
            rarities.append("Purple")
        if self.salvage_sel_gold:
            rarities.append("Gold")
        return rarities

    def _encode_rarities(self, rarities):
        return ",".join(rarities)

    def _decode_rarities(self, payload):
        txt = self._ensure_text(payload).strip()
        if not txt:
            return []
        out = []
        allowed = {"White", "Blue", "Green", "Purple", "Gold"}
        for r in txt.split(","):
            rt = r.strip().title()
            if rt in allowed:
                out.append(rt)
        return out

    def _mouse_in_current_window_rect(self):
        try:
            io = PyImGui.get_io()
            mx = float(getattr(io, "mouse_pos_x", -1.0))
            my = float(getattr(io, "mouse_pos_y", -1.0))
            wx, wy = PyImGui.get_window_pos()
            ww, wh = PyImGui.get_window_size()
            return (mx >= wx) and (mx <= (wx + ww)) and (my >= wy) and (my <= (wy + wh))
        except EXPECTED_RUNTIME_ERRORS:
            return False

    def _get_display_size(self):
        io = PyImGui.get_io()
        w = float(getattr(io, "display_size_x", 1920.0) or 1920.0)
        h = float(getattr(io, "display_size_y", 1080.0) or 1080.0)
        return max(320.0, w), max(240.0, h)

    def _clamp_pos(self, x, y, w, h, margin=4.0):
        disp_w, disp_h = self._get_display_size()
        max_x = max(margin, disp_w - w - margin)
        max_y = max(margin, disp_h - h - margin)
        return min(max(float(x), margin), max_x), min(max(float(y), margin), max_y)

    def _clamp_size(self, w, h, min_w=420.0, min_h=280.0, margin=20.0):
        disp_w, disp_h = self._get_display_size()
        max_w = max(min_w, disp_w - margin)
        max_h = max(min_h, disp_h - margin)
        cw = min(max(float(w), min_w), max_w)
        ch = min(max(float(h), min_h), max_h)
        return cw, ch

    def _draw_hover_handle(self):
        display_w, _ = self._get_display_size()

        btn_w = 48.0
        btn_h = 48.0
        win_w = btn_w + 4.0
        win_h = btn_h + 4.0
        default_x = max(8.0, (display_w * 0.5) - (btn_w * 0.5))
        default_y = 4.0

        if self.saved_hover_handle_pos is None:
            self.saved_hover_handle_pos = (default_x, default_y)

        x, y = self.saved_hover_handle_pos
        x, y = self._clamp_pos(x, y, btn_w, btn_h)
        self.saved_hover_handle_pos = (x, y)
        button_rect = (x, y, btn_w, btn_h)

        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(win_w, win_h)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0.0, 0.0)
        flags = (
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoResize |
            PyImGui.WindowFlags.NoMove |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoBackground
        )

        hovered = False
        if PyImGui.begin("Drop Tracker##HoverHandle", flags):
            # Travel-like themed floating background.
            is_hover = ImGui.is_mouse_in_rect(button_rect)
            try:
                match(ImGui.get_style().Theme):
                    case Style.StyleTheme.Guild_Wars:
                        ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
                            button_rect[:2], button_rect[2:],
                            tint=(255, 255, 255, 255) if is_hover else (200, 200, 200, 255),
                        )
                        ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
                            button_rect[:2], button_rect[2:],
                            tint=(255, 255, 255, 255) if is_hover else (200, 200, 200, 255),
                        )
                    case _:
                        PyImGui.draw_list_add_rect_filled(
                            button_rect[0] + 1, button_rect[1] + 1,
                            button_rect[0] + button_rect[2] - 1, button_rect[1] + button_rect[3] - 1,
                            Utils.RGBToColor(51, 76, 102, 255) if is_hover else Utils.RGBToColor(26, 38, 51, 255),
                            4, 0
                        )
                        PyImGui.draw_list_add_rect(
                            button_rect[0] + 1, button_rect[1] + 1,
                            button_rect[0] + button_rect[2] - 1, button_rect[1] + button_rect[3] - 1,
                            Utils.RGBToColor(204, 204, 212, 50), 4, 0, 1
                        )
            except EXPECTED_RUNTIME_ERRORS:
                pass

            # Pin indicator frame (green pinned / red unpinned)
            frame_col = Utils.RGBToColor(76, 235, 89, 255) if self.hover_pin_open else Utils.RGBToColor(242, 71, 56, 255)
            PyImGui.draw_list_add_rect(
                button_rect[0] + 1, button_rect[1] + 1,
                button_rect[0] + button_rect[2] - 1, button_rect[1] + button_rect[3] - 1,
                frame_col, 4, 0, 3
            )

            # Icon in drawlist, centered in the floating button.
            tint = (255, 255, 255, 255) if is_hover else (210, 210, 210, 255)
            icon_rect = (button_rect[0] + 8, button_rect[1] + 6, 32, 32)
            if os.path.exists(self.hover_icon_path):
                ImGui.DrawTextureInDrawList(icon_rect[:2], icon_rect[2:], self.hover_icon_path, tint=tint)

            if PyImGui.invisible_button("##DropHandleBtn", button_rect[2], button_rect[3]):
                self.hover_pin_open = not self.hover_pin_open
            elif PyImGui.is_item_active():
                delta = PyImGui.get_mouse_drag_delta(0, 0.0)
                PyImGui.reset_mouse_drag_delta(0)
                x = x + delta[0]
                y = y + delta[1]
                x, y = self._clamp_pos(x, y, btn_w, btn_h)
                self.saved_hover_handle_pos = (x, y)
                self._persist_layout_value("drop_viewer_handle_pos", self.saved_hover_handle_pos)

            if PyImGui.is_item_hovered():
                tip = "Drop Tracker (click to pin)" if not self.hover_pin_open else "Drop Tracker (click to unpin)"
                ImGui.show_tooltip(tip)

            hovered = ImGui.is_mouse_in_rect(button_rect)
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
        except EXPECTED_RUNTIME_ERRORS as e:
            self.set_status(f"Save failed: {e}")

    def load_run(self, filename):
        target = os.path.join(self.saved_logs_dir, filename)
        if not os.path.exists(target): return
        
        self.paused = True
        try:
            self._parse_log_file(target)
            self.set_status(f"Loaded {filename}")
        except EXPECTED_RUNTIME_ERRORS as e:
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
                event_idx = header.index("EventID") if header and "EventID" in header else -1
                stats_idx = header.index("ItemStats") if header and "ItemStats" in header else -1
                item_id_idx = header.index("ItemID") if header and "ItemID" in header else -1
                
                for row in reader:
                    fallback_map_name = "Unknown"
                    if not has_map_name:
                        try:
                            fallback_map_name = self._ensure_text(Map.GetMapName(self._safe_int(row[2], 0))) or "Unknown"
                        except EXPECTED_RUNTIME_ERRORS:
                            fallback_map_name = "Unknown"

                    parsed = DropLogRow.from_csv_row(
                        row,
                        has_map_name=bool(has_map_name),
                        event_idx=event_idx,
                        stats_idx=stats_idx,
                        item_id_idx=item_id_idx,
                        map_name_fallback=fallback_map_name,
                    )
                    if parsed is None:
                        continue

                    temp_drops.append(parsed.to_runtime_row())
                    total += int(parsed.quantity)
                    
                    canonical_name = self._canonical_agg_item_name(parsed.item_name, parsed.rarity, temp_agg)
                    key = (canonical_name, parsed.rarity)
                    if key not in temp_agg:
                        temp_agg[key] = {"Quantity": 0, "Count": 0}
                    temp_agg[key]["Quantity"] += int(parsed.quantity)
                    temp_agg[key]["Count"] += 1
            
             self.raw_drops = temp_drops
             self.aggregated_drops = temp_agg
             self.total_drops = total
             self.set_status(f"Merged {filename}")
             
        except EXPECTED_RUNTIME_ERRORS as e:
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
                sw, sh = self.saved_viewer_window_size if self.saved_viewer_window_size is not None else (760.0, 520.0)
                sw, sh = self._clamp_size(sw, sh)
                px, py = self._clamp_pos(self.saved_viewer_window_pos[0], self.saved_viewer_window_pos[1], sw, sh)
                PyImGui.set_next_window_pos(px, py)
            if self.saved_viewer_window_size is not None:
                sw, sh = self._clamp_size(self.saved_viewer_window_size[0], self.saved_viewer_window_size[1])
                PyImGui.set_next_window_size(sw, sh)
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
            if self._styled_button(
                "Refresh (Live)" if self.paused else "Refresh",
                "primary",
                tooltip="Reload from current live session file."
            ):
                self.paused = False
                self.last_read_time = 0 
                self.load_drops() # Re-read main log
            
            PyImGui.same_line(0.0, 10.0)
            
            # View Mode Switch
            if self.view_mode == "Aggregated":
                if self._styled_button("Show Logs", "secondary", tooltip="Switch to raw event log view"):
                    self.view_mode = "Log"
            else:
                if self._styled_button("Show Stats", "secondary", tooltip="Switch to aggregated item stats"):
                    self.view_mode = "Aggregated"
                
            PyImGui.same_line(0.0, 10.0)

            if self._styled_button(
                "Pause" if not self.paused else "Resume",
                "warning" if not self.paused else "success",
                tooltip="Pause or resume live updates."
            ):
                self.paused = not self.paused

            PyImGui.same_line(0.0, 10.0)
            
            if self._styled_button("Save", "secondary", tooltip="Save current session log snapshot"):
                self.show_save_popup = not self.show_save_popup
                
            if self.show_save_popup:
                PyImGui.same_line(0.0, 10.0)
                PyImGui.push_item_width(100)
                self.save_filename = PyImGui.input_text("", self.save_filename)
                PyImGui.pop_item_width()
                PyImGui.same_line(0.0, 10.0)
                if self._styled_button("OK", "primary"):
                    self.save_run()
            
            PyImGui.same_line(0.0, 10.0)
            
            # Load/Merge Logic
            if self._styled_button("Load/Merge..", "secondary", tooltip="Load or merge a saved log file"):
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
            if self._styled_button("Clear/Reset", "danger", tooltip="Clear live file and in-memory drop stats"):
                 try:
                    # Reset file + in-memory state to a clean live session.
                    self._reset_live_session()
                    
                    # Reset chat bookmark state to "from now".
                    self.last_chat_index = -1 
                    if Player.IsChatHistoryReady():
                         self.last_chat_index = len(Player.GetChatHistory())

                    self.set_status("Log Cleared")
                 except EXPECTED_RUNTIME_ERRORS as e:
                     Py4GW.Console.Log("DropViewer", f"Clear failed: {e}", Py4GW.Console.MessageType.Error)

            filtered_rows = self._get_filtered_rows()
            table_rows = [row for row in filtered_rows if not self._is_gold_row(row)]
            self._draw_summary_bar(filtered_rows)

            # -- Status Bar --
            if time.time() - self.status_time < 5:
                self._draw_status_toast(self.status_message)

            PyImGui.separator()

            # -- Main Content: Left filter rail + right data panel --
            left_w = 280.0
            if PyImGui.begin_child("DropViewerLeftRail", size=(left_w, 0), border=True, flags=PyImGui.WindowFlags.NoFlag):
                self._draw_section_header("Filters")
                if PyImGui.collapsing_header("Filter Settings"):
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
                    if PyImGui.is_item_hovered():
                        ImGui.show_tooltip("Show as hoverable floating handle instead of always-open window.")
                    if self.hover_handle_mode:
                        self.hover_pin_open = PyImGui.checkbox("Pin Open", self.hover_pin_open)
                    if self.hover_handle_mode and not prev_hover_mode:
                        self.hover_is_visible = True
                        self.hover_hide_deadline = now + self.hover_hide_delay_s

                    if self._styled_button("Quick: Rare Only", "primary", tooltip="Enable Rare-only filters quickly"):
                        self.only_rare = True
                        self.hide_gold = True
                        self.filter_rarity_idx = 0
                    if self._styled_button("Clear Filters", "secondary", tooltip="Reset all filter fields"):
                        self.search_text = ""
                        self.filter_player = ""
                        self.filter_map = ""
                        self.filter_rarity_idx = 0
                        self.only_rare = False
                        self.hide_gold = False
                        self.min_qty = 1

                self._draw_conset_controls()
                self._draw_section_header("Inventory Actions")
                if self._styled_button("Auto Identify", "primary", tooltip="Runs identify using selected ID Settings rarities."):
                    self._trigger_inventory_action("id_selected", self._encode_rarities(self._get_selected_id_rarities()))
                PyImGui.same_line(0.0, 10.0)
                if self._styled_button("Auto Salvage", "primary", tooltip="Runs salvage using selected Salvage Settings rarities."):
                    self._trigger_inventory_action("salvage_selected", self._encode_rarities(self._get_selected_salvage_rarities()))
                self._draw_rarity_chips("ID:", self._get_selected_id_rarities())
                self._draw_rarity_chips("Salvage:", self._get_selected_salvage_rarities())

                if PyImGui.begin_tab_bar("DropTrackerInventoryTabs"):
                    if PyImGui.begin_tab_item("ID/Salvage Settings"):
                        if PyImGui.collapsing_header("ID Settings"):
                            old_id = (self.id_sel_white, self.id_sel_blue, self.id_sel_green, self.id_sel_purple, self.id_sel_gold)
                            self.id_sel_white = PyImGui.checkbox("ID White", self.id_sel_white)
                            self.id_sel_blue = PyImGui.checkbox("ID Blue", self.id_sel_blue)
                            self.id_sel_green = PyImGui.checkbox("ID Green", self.id_sel_green)
                            self.id_sel_purple = PyImGui.checkbox("ID Purple", self.id_sel_purple)
                            self.id_sel_gold = PyImGui.checkbox("ID Gold", self.id_sel_gold)
                            if old_id != (self.id_sel_white, self.id_sel_blue, self.id_sel_green, self.id_sel_purple, self.id_sel_gold):
                                self.runtime_config_dirty = True

                        if PyImGui.collapsing_header("Salvage Settings"):
                            old_salvage = (self.salvage_sel_white, self.salvage_sel_blue, self.salvage_sel_green, self.salvage_sel_purple, self.salvage_sel_gold)
                            self.salvage_sel_white = PyImGui.checkbox("Salvage White", self.salvage_sel_white)
                            self.salvage_sel_blue = PyImGui.checkbox("Salvage Blue", self.salvage_sel_blue)
                            self.salvage_sel_green = PyImGui.checkbox("Salvage Green", self.salvage_sel_green)
                            self.salvage_sel_purple = PyImGui.checkbox("Salvage Purple", self.salvage_sel_purple)
                            self.salvage_sel_gold = PyImGui.checkbox("Salvage Gold", self.salvage_sel_gold)
                            if old_salvage != (self.salvage_sel_white, self.salvage_sel_blue, self.salvage_sel_green, self.salvage_sel_purple, self.salvage_sel_gold):
                                self.runtime_config_dirty = True

                        PyImGui.end_tab_item()

                    if PyImGui.begin_tab_item("Inventory Kits"):
                        self._draw_inventory_kit_stats_tab()
                        PyImGui.end_tab_item()
                    PyImGui.end_tab_bar()

                self._draw_section_header("Advanced")
                self.show_runtime_panel = PyImGui.checkbox("Advanced Runtime Controls", self.show_runtime_panel)
                if self.show_runtime_panel:
                    self._draw_runtime_controls()
                PyImGui.end_child()

            PyImGui.same_line(0.0, 10.0)

            if PyImGui.begin_child("DropViewerDataPanel", size=(0, 0), border=False, flags=PyImGui.WindowFlags.NoFlag):
                if self.view_mode == "Aggregated":
                    self._draw_aggregated(table_rows)
                else:
                    self._draw_log(table_rows)
                PyImGui.end_child()

            main_window_hovered = self._mouse_in_current_window_rect() or PyImGui.is_window_hovered()

        PyImGui.end()
        self._flush_runtime_config_if_dirty()
        if self.hover_handle_mode:
            if main_window_hovered:
                self.hover_is_visible = True
                self.hover_hide_deadline = now + self.hover_hide_delay_s
            if not self.hover_pin_open and not handle_hovered and not main_window_hovered and now >= self.hover_hide_deadline:
                self.hover_is_visible = False
        
    def _draw_aggregated(self, filtered_rows):
        c = self._ui_colors()
        filtered_agg, total_filtered_qty = self._get_filtered_aggregated(filtered_rows)
        total_items_without_gold = total_filtered_qty - sum(
            data["Quantity"] for (name, _), data in filtered_agg.items() if name == "Gold"
        )

        PyImGui.text_colored(f"Total Items (filtered): {max(0, total_items_without_gold)}", c["muted"])
        if not filtered_agg:
            PyImGui.separator()
            PyImGui.text_colored("No drops match your current filters.", c["muted"])
            PyImGui.text("Try clearing filters or switching to Log view.")
            return

        PyImGui.push_style_color(PyImGui.ImGuiCol.TableHeaderBg, (0.16, 0.20, 0.27, 0.95))
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
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (r, g, b, a))
                if PyImGui.selectable(f"{item_name}##agg_{idx}", self.selected_item_key == row_key, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                    self.selected_item_key = row_key
                    self.selected_log_row = self._find_best_row_for_item(item_name, rarity, filtered_rows)
                if PyImGui.is_item_clicked(1):
                    PyImGui.open_popup(f"DropAggRowMenu##{idx}")
                if PyImGui.begin_popup(f"DropAggRowMenu##{idx}"):
                    target_row = self._find_best_row_for_item(item_name, rarity, filtered_rows)
                    if target_row is None:
                        PyImGui.text("No concrete row available")
                    else:
                        self.selected_item_key = row_key
                        self.selected_log_row = target_row
                        if PyImGui.menu_item("Identify item"):
                            self._identify_item_for_all_characters(item_name, rarity)
                    PyImGui.end_popup()
                if PyImGui.is_item_hovered():
                    ImGui.show_tooltip("Left click: view stats. Right click: item actions.")
                PyImGui.pop_style_color(1)
                
                PyImGui.table_set_column_index(1)
                PyImGui.text(str(qty))
                
                PyImGui.table_set_column_index(2)
                PyImGui.text(pct_str)
                
                PyImGui.table_set_column_index(3)
                PyImGui.text_colored(rarity, (r, g, b, a))
                
                PyImGui.table_set_column_index(4)
                PyImGui.text(str(data["Count"]))
                
            PyImGui.end_table()
        PyImGui.pop_style_color(1)
        self._draw_selected_item_details()

    def _draw_log(self, filtered_rows):
        c = self._ui_colors()
        if not filtered_rows:
            PyImGui.text_colored("No log entries to show.", c["muted"])
            PyImGui.text("Drops will appear here as they are tracked.")
            return

        PyImGui.push_style_color(PyImGui.ImGuiCol.TableHeaderBg, (0.16, 0.20, 0.27, 0.95))
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

            for row_idx, row in enumerate(filtered_rows):
                PyImGui.table_next_row()
                parsed = self._parse_drop_row(row)
                if parsed is None:
                    continue
                rarity = self._ensure_text(parsed.rarity).strip() or "Unknown"
                r, g, b, a = self._get_rarity_color(rarity)
                selected_key = (
                    self._canonical_agg_item_name(parsed.item_name, rarity, self.aggregated_drops),
                    self._ensure_text(rarity).strip() or "Unknown"
                )

                for i, col in enumerate(row):
                    if i >= 8: break
                    PyImGui.table_set_column_index(i)
                    
                    if i == 5:
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (r, g, b, a))
                        if PyImGui.selectable(
                            f"{str(col)}##log_item_{row_idx}",
                            self.selected_item_key == selected_key,
                            PyImGui.SelectableFlags.NoFlag,
                            (0.0, 0.0)
                        ):
                            self.selected_item_key = selected_key
                            self.selected_log_row = list(row)
                        if PyImGui.is_item_clicked(1):
                            PyImGui.open_popup(f"DropLogRowMenu##{row_idx}")
                        if PyImGui.begin_popup(f"DropLogRowMenu##{row_idx}"):
                            if PyImGui.menu_item("Identify item"):
                                self._identify_item_for_all_characters(parsed.item_name, rarity)
                            PyImGui.end_popup()
                        if PyImGui.is_item_hovered():
                            ImGui.show_tooltip("Left click: view stats. Right click: item actions.")
                        PyImGui.pop_style_color(1)
                    elif i == 7:
                        PyImGui.text_colored(str(col), (r, g, b, a))
                    else:
                        PyImGui.text(str(col))

            if self.auto_scroll:
                PyImGui.set_scroll_here_y(1.0)

            PyImGui.end_table()
        PyImGui.pop_style_color(1)
        self._draw_selected_item_details()

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

            # Auto-reset tracking whenever the player enters a new ready map instance.
            current_map_id = Map.GetMapID()
            if current_map_id > 0:
                if self.last_seen_map_id <= 0:
                    self.last_seen_map_id = current_map_id
                elif current_map_id != self.last_seen_map_id:
                    self.last_seen_map_id = current_map_id
                    self._reset_live_session()
                    self.map_change_ignore_until = time.time() + 3.0
                    self.last_chat_index = -1
                    if Player.IsChatHistoryReady():
                        self.last_chat_index = len(Player.GetChatHistory())
                    self.set_status("Auto reset on map change")
                    return
                elif self.raw_drops:
                    try:
                        last_parsed = self._parse_drop_row(self.raw_drops[-1]) if self.raw_drops else None
                        last_logged_map = self._safe_int(last_parsed.map_id if last_parsed else 0, 0)
                    except EXPECTED_RUNTIME_ERRORS:
                        last_logged_map = 0
                    if last_logged_map > 0 and last_logged_map != current_map_id:
                        self._reset_live_session()
                        self.map_change_ignore_until = time.time() + 3.0
                        self.last_chat_index = -1
                        if Player.IsChatHistoryReady():
                            self.last_chat_index = len(Player.GetChatHistory())
                        self.set_status("Auto reset on map sync")
                        return

            # Poll shared memory reliably every tick
            self._process_pending_identify_responses()
            self._poll_shared_memory()
            self._run_auto_conset_tick()

            if self.player_name == "Unknown":
                try:
                    self.player_name = Player.GetName()
                except EXPECTED_RUNTIME_ERRORS:
                    pass

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

        except EXPECTED_RUNTIME_ERRORS as e:
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
            except EXPECTED_RUNTIME_ERRORS:
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
                except (TypeError, ValueError, RuntimeError, AttributeError):
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

            is_leader_client = False
            try:
                is_leader_client = (Player.GetAgentID() == Party.GetPartyLeaderID())
            except EXPECTED_RUNTIME_ERRORS:
                is_leader_client = False

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
            self.stats_chunk_buffers = {
                sig: data for sig, data in self.stats_chunk_buffers.items()
                if (now_ts - float(data.get("updated_at", now_ts))) <= 30.0
            }
            self.stats_payload_chunk_buffers = {
                sig: data for sig, data in self.stats_payload_chunk_buffers.items()
                if (now_ts - float(data.get("updated_at", now_ts))) <= 30.0
            }
            self.stats_render_cache_by_event = prune_render_cache(self.stats_render_cache_by_event, now_ts, ttl_seconds=1800.0)

            ignore_tracker_messages = now_ts < float(self.map_change_ignore_until)
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
                except EXPECTED_RUNTIME_ERRORS:
                    pass
                if command_value != expected_custom_behavior_command and command_value != 997:
                    continue

                should_finish = False
                extra_data_list = None
                try:
                    should_finish = False
                    extra_data_list = getattr(shared_msg, "ExtraData", None)
                    if not extra_data_list or len(extra_data_list) == 0:
                        continue

                    extra_0 = _c_wchar_array_to_str(extra_data_list[0])
                    if handle_inventory_action_branch(
                        extra_0=extra_0,
                        expected_tag=self.inventory_action_tag,
                        extra_data_list=extra_data_list,
                        shared_msg=shared_msg,
                        to_text_fn=_c_wchar_array_to_str,
                        normalize_text_fn=_normalize_shmem_text,
                        run_inventory_action_fn=self._run_inventory_action,
                    ):
                        should_finish = True
                        shmem.MarkMessageAsFinished(my_email, msg_idx)
                        processed_tracker_msgs += 1
                        continue

                    if handle_inventory_stats_request_branch(
                        extra_0=extra_0,
                        expected_tag=self.inventory_stats_request_tag,
                        shared_msg=shared_msg,
                        my_email=my_email,
                        normalize_text_fn=_normalize_shmem_text,
                        send_inventory_kit_stats_response_fn=self._send_inventory_kit_stats_response,
                    ):
                        should_finish = True
                        shmem.MarkMessageAsFinished(my_email, msg_idx)
                        processed_tracker_msgs += 1
                        continue

                    if handle_inventory_stats_response_branch(
                        extra_0=extra_0,
                        expected_tag=self.inventory_stats_response_tag,
                        extra_data_list=extra_data_list,
                        shared_msg=shared_msg,
                        to_text_fn=_c_wchar_array_to_str,
                        normalize_text_fn=_normalize_shmem_text,
                        safe_int_fn=self._safe_int,
                        get_account_data_fn=shmem.GetAccountDataFromEmail,
                        upsert_inventory_kit_stats_fn=self._upsert_inventory_kit_stats,
                    ):
                        should_finish = True
                        shmem.MarkMessageAsFinished(my_email, msg_idx)
                        processed_tracker_msgs += 1
                        continue

                    if extra_0 == "TrackerNameV2":
                        if not is_leader_client:
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                            continue
                        if ignore_tracker_messages:
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                            continue
                        should_finish = True
                        scanned_msgs += 1
                        if handle_tracker_name_branch(
                            extra_0=extra_0,
                            expected_tag="TrackerNameV2",
                            extra_data_list=extra_data_list,
                            to_text_fn=_c_wchar_array_to_str,
                            decode_chunk_meta_fn=decode_name_chunk_meta,
                            merge_name_chunk_fn=merge_name_chunk,
                            name_chunk_buffers=self.name_chunk_buffers,
                            full_name_by_signature=self.full_name_by_signature,
                            now_ts=now_ts,
                        ):
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                            continue

                    if extra_0 == "TrackerStatsV2":
                        if not is_leader_client:
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                            continue
                        if ignore_tracker_messages:
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                            continue
                        should_finish = True
                        scanned_msgs += 1
                        stats_sender_email = _normalize_shmem_text(getattr(shared_msg, "SenderEmail", ""))
                        stats_sender_name = self._resolve_sender_name_from_email(stats_sender_email)

                        def _merge_payload_chunk_scoped(
                            buffers: dict[str, dict[str, Any]],
                            event_id_arg: str,
                            chunk_text_arg: str,
                            chunk_idx_arg: int,
                            chunk_total_arg: int,
                            now_ts_arg: float,
                        ) -> str:
                            scoped_key = self._make_stats_cache_key(event_id_arg, stats_sender_email, stats_sender_name)
                            return merge_stats_payload_chunk(
                                buffers,
                                scoped_key,
                                chunk_text_arg,
                                chunk_idx_arg,
                                chunk_total_arg,
                                now_ts_arg,
                            )

                        def _on_payload_merged(event_id: str, merged_payload: str) -> None:
                            stats_cache_key = self._make_stats_cache_key(event_id, stats_sender_email, stats_sender_name)
                            payload_ok = payload_has_valid_mods_json(merged_payload)
                            if not payload_ok:
                                if self.verbose_shmem_item_logs or self.debug_item_stats_panel:
                                    preview = merged_payload[:220].replace("\n", " ")
                                    Py4GW.Console.Log(
                                        "DropViewer",
                                        f"STATS V2 parse error ev={event_id} | payload_head={preview}",
                                        Py4GW.Console.MessageType.Warning,
                                    )
                                self.stats_payload_by_event.pop(stats_cache_key, None)
                                self.remote_stats_pending_by_event.pop(stats_cache_key, None)
                                self.remote_stats_request_last_by_event[stats_cache_key] = 0.0
                                self.stats_render_cache_by_event.pop(stats_cache_key, None)
                                return

                            rendered = self._render_payload_stats_cached(stats_cache_key, merged_payload, "").strip()
                            if rendered:
                                self.stats_by_event[stats_cache_key] = rendered
                            self.stats_payload_by_event[stats_cache_key] = merged_payload
                            self.remote_stats_pending_by_event.pop(stats_cache_key, None)
                            if rendered:
                                update_rows_item_stats_by_event_and_sender(
                                    self.raw_drops,
                                    event_id,
                                    stats_sender_email,
                                    rendered,
                                    player_name=stats_sender_name,
                                )
                            if self.selected_log_row and self._extract_row_event_id(self.selected_log_row) == event_id:
                                selected_row = self._parse_drop_row(self.selected_log_row)
                                selected_player = self._ensure_text(selected_row.player_name).strip() if selected_row else ""
                                can_update_selected = False
                                if stats_sender_name:
                                    can_update_selected = selected_player.lower() == stats_sender_name.lower()
                                else:
                                    event_matches = 0
                                    for raw_row in self.raw_drops:
                                        if self._extract_row_event_id(raw_row) == event_id:
                                            event_matches += 1
                                            if event_matches > 1:
                                                break
                                    can_update_selected = event_matches <= 1
                                if rendered and can_update_selected:
                                    self._set_row_item_stats(self.selected_log_row, rendered)

                        if handle_tracker_stats_payload_branch(
                            extra_0=extra_0,
                            expected_tag="TrackerStatsV2",
                            extra_data_list=extra_data_list,
                            to_text_fn=_c_wchar_array_to_str,
                            decode_chunk_meta_fn=decode_name_chunk_meta,
                            merge_stats_payload_chunk_fn=_merge_payload_chunk_scoped,
                            stats_payload_chunk_buffers=self.stats_payload_chunk_buffers,
                            now_ts=now_ts,
                            on_merged_payload_fn=_on_payload_merged,
                        ):
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                            continue

                    if extra_0 == "TrackerStatsV1":
                        if not is_leader_client:
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                            continue
                        if ignore_tracker_messages:
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                            continue
                        should_finish = True
                        scanned_msgs += 1
                        stats_sender_email = _normalize_shmem_text(getattr(shared_msg, "SenderEmail", ""))
                        stats_sender_name = self._resolve_sender_name_from_email(stats_sender_email)

                        def _merge_text_chunk_scoped(
                            buffers: dict[str, dict[str, Any]],
                            event_id_arg: str,
                            chunk_text_arg: str,
                            chunk_idx_arg: int,
                            chunk_total_arg: int,
                            now_ts_arg: float,
                        ) -> str:
                            scoped_key = self._make_stats_cache_key(event_id_arg, stats_sender_email, stats_sender_name)
                            return merge_stats_text_chunk(
                                buffers,
                                scoped_key,
                                chunk_text_arg,
                                chunk_idx_arg,
                                chunk_total_arg,
                                now_ts_arg,
                            )

                        def _on_text_merged(event_id: str, merged: str) -> None:
                            stats_cache_key = self._make_stats_cache_key(event_id, stats_sender_email, stats_sender_name)
                            normalized_merged = self._normalize_stats_text(merged)
                            self.stats_by_event[stats_cache_key] = normalized_merged
                            self.remote_stats_pending_by_event.pop(stats_cache_key, None)
                            # Update any existing row for this event_id (overwrite stale/unidentified stats too).
                            update_rows_item_stats_by_event_and_sender(
                                self.raw_drops,
                                event_id,
                                stats_sender_email,
                                normalized_merged,
                                player_name=stats_sender_name,
                            )
                            if self.selected_log_row and self._extract_row_event_id(self.selected_log_row) == event_id:
                                selected_row = self._parse_drop_row(self.selected_log_row)
                                selected_player = self._ensure_text(selected_row.player_name).strip() if selected_row else ""
                                can_update_selected = False
                                if stats_sender_name:
                                    can_update_selected = selected_player.lower() == stats_sender_name.lower()
                                else:
                                    event_matches = 0
                                    for raw_row in self.raw_drops:
                                        if self._extract_row_event_id(raw_row) == event_id:
                                            event_matches += 1
                                            if event_matches > 1:
                                                break
                                    can_update_selected = event_matches <= 1
                                if can_update_selected:
                                    self._set_row_item_stats(self.selected_log_row, normalized_merged)

                        if handle_tracker_stats_text_branch(
                            extra_0=extra_0,
                            expected_tag="TrackerStatsV1",
                            extra_data_list=extra_data_list,
                            to_text_fn=_c_wchar_array_to_str,
                            decode_chunk_meta_fn=decode_name_chunk_meta,
                            merge_stats_text_chunk_fn=_merge_text_chunk_scoped,
                            stats_chunk_buffers=self.stats_chunk_buffers,
                            now_ts=now_ts,
                            on_merged_text_fn=_on_text_merged,
                        ):
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                            continue

                    if extra_0 != "TrackerDrop":
                        continue

                    if not is_leader_client:
                        shmem.MarkMessageAsFinished(my_email, msg_idx)
                        continue

                    if ignore_tracker_messages:
                        shmem.MarkMessageAsFinished(my_email, msg_idx)
                        continue

                    should_finish = True
                    scanned_msgs += 1
                    if scanned_msgs > self.max_shmem_scan_per_tick:
                        break

                    drop_msg = handle_tracker_drop_branch(
                        extra_0=extra_0,
                        expected_tag="TrackerDrop",
                        extra_data_list=extra_data_list,
                        shared_msg=shared_msg,
                        to_text_fn=_c_wchar_array_to_str,
                        normalize_text_fn=_normalize_shmem_text,
                        build_tracker_drop_message_fn=build_tracker_drop_message,
                        resolve_full_name_fn=lambda sig: self.full_name_by_signature.get(sig, ""),
                        normalize_rarity_label_fn=self._normalize_rarity_label,
                    )
                    if drop_msg is None:
                        continue

                    event_id = drop_msg.event_id
                    item_name = drop_msg.item_name
                    exact_rarity = drop_msg.rarity
                    quantity = drop_msg.quantity
                    row_item_id = drop_msg.item_id
                    model_id_param = drop_msg.model_id
                    slot_bag = drop_msg.slot_bag
                    slot_index = drop_msg.slot_index
                    sender_email = drop_msg.sender_email
                    sender_name_raw = self._resolve_sender_name_from_email(sender_email)
                    sender_name = sender_name_raw or "Follower"
                    stats_cache_key = self._make_stats_cache_key(event_id, sender_email, sender_name_raw)
                    stats_text = self._get_cached_stats_text(self.stats_by_event, stats_cache_key)
                    if stats_cache_key and drop_msg.name_signature:
                        self.stats_name_signature_by_event[stats_cache_key] = self._ensure_text(drop_msg.name_signature).strip().lower()

                    event_key = drop_msg.event_key
                    is_duplicate = is_duplicate_event(self.seen_events, event_key)
                    if not is_duplicate:
                        mark_seen_event(self.seen_events, event_key, now_ts)

                    if not is_duplicate:
                        batch_rows.append(
                            {
                                "player_name": sender_name,
                                "item_name": item_name,
                                "quantity": quantity,
                                "extra_info": exact_rarity,
                                "timestamp_override": None,
                                "event_id": event_id,
                                "item_stats": stats_text,
                                "item_id": row_item_id,
                                "sender_email": sender_email,
                            }
                        )

                    if event_id and self._send_tracker_ack(sender_email, event_id):
                        ack_sent_this_tick += 1

                    if self.verbose_shmem_item_logs:
                        log_msg = (
                            f"TRACKED: {item_name} x{quantity} ({exact_rarity}) "
                            f"[{sender_name}] (ShMem idx={msg_idx} item_id={row_item_id} "
                            f"model_id={model_id_param} slot={slot_bag}:{slot_index} ev={event_id} dup={is_duplicate})"
                        )
                        Py4GW.Console.Log("DropViewer", log_msg, Py4GW.Console.MessageType.Info)

                    shmem.MarkMessageAsFinished(my_email, msg_idx)
                    processed_tracker_msgs += 1
                except (TypeError, ValueError, RuntimeError, AttributeError, IndexError) as msg_e:
                    event_hint = ""
                    tag_hint = ""
                    try:
                        tag_hint = _c_wchar_array_to_str(extra_data_list[0]) if extra_data_list and len(extra_data_list) > 0 else ""
                    except (TypeError, ValueError, RuntimeError, AttributeError, IndexError):
                        tag_hint = ""
                    try:
                        event_hint = extract_event_id_hint(
                            extra_0=tag_hint,
                            extra_data_list=extra_data_list,
                            to_text_fn=_c_wchar_array_to_str,
                        )
                    except (TypeError, ValueError, RuntimeError, AttributeError, IndexError):
                        event_hint = ""
                    Py4GW.Console.Log(
                        "DropViewer",
                        f"ShMem parse warning idx={msg_idx} tag={tag_hint} ev={event_hint}: {msg_e}",
                        Py4GW.Console.MessageType.Warning,
                    )
                    try:
                        if should_finish:
                            shmem.MarkMessageAsFinished(my_email, msg_idx)
                    except (TypeError, ValueError, RuntimeError, AttributeError):
                        pass
                    continue

            if batch_rows:
                self._log_drops_batch(batch_rows)
                Py4GW.Console.Log(
                    "DropViewer",
                    f"TRACKED BATCH: {len(batch_rows)} items (ShMem)",
                    Py4GW.Console.MessageType.Info
                )
        except (TypeError, ValueError, RuntimeError, AttributeError) as e:
            if self.shmem_error_timer.IsExpired():
                self.shmem_error_timer.Reset()
                Py4GW.Console.Log(
                    "DropViewer",
                    f"ShMem poll skipped: {e}",
                    Py4GW.Console.MessageType.Warning,
                )
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
        except EXPECTED_RUNTIME_ERRORS as e:
             Py4GW.Console.Log("RarityDebug", f"Snapshot Error: {e}", Py4GW.Console.MessageType.Error)
        return snapshot

    def _queue_identify_for_rarities(self, rarities):
        try:
            items = Routines.Items.GetUnidentifiedItems(list(rarities), [])
            if not items:
                return 0
            GLOBAL_CACHE.Coroutines.append(Routines.Yield.Items.IdentifyItems(items, log=True))
            return len(items)
        except EXPECTED_RUNTIME_ERRORS as e:
            Py4GW.Console.Log("DropViewer", f"Identify queue failed: {e}", Py4GW.Console.MessageType.Warning)
            return 0

    def _queue_salvage_for_rarities(self, rarities):
        try:
            items = Routines.Items.GetSalvageableItems(list(rarities), [])
            if not items:
                return 0
            GLOBAL_CACHE.Coroutines.append(Routines.Yield.Items.SalvageItems(items, log=True))
            return len(items)
        except EXPECTED_RUNTIME_ERRORS as e:
            Py4GW.Console.Log("DropViewer", f"Salvage queue failed: {e}", Py4GW.Console.MessageType.Warning)
            return 0

    def _process_pending_identify_responses(self):
        def _is_identified(item_id: int) -> bool:
            try:
                return bool(Item.Usage.IsIdentified(int(item_id)))
            except (TypeError, ValueError, RuntimeError, AttributeError):
                return False

        try:
            completed = self.identify_response_scheduler.tick(
                build_payload_fn=lambda item_id: self._build_item_snapshot_payload_from_live_item(int(item_id), ""),
                is_identified_fn=_is_identified,
                send_payload_fn=lambda receiver_email, event_id, payload: self._send_tracker_stats_payload_chunks_to_email(
                    receiver_email,
                    event_id,
                    payload,
                ),
                build_stats_fn=lambda item_id: self._build_item_stats_from_live_item(int(item_id), ""),
                send_stats_fn=lambda receiver_email, event_id, stats: self._send_tracker_stats_chunks_to_email(
                    receiver_email,
                    event_id,
                    stats,
                ),
            )
            if completed > 0 and self.verbose_shmem_item_logs:
                Py4GW.Console.Log(
                    "DropViewer",
                    f"ASYNC ID responses completed={completed} pending={self.identify_response_scheduler.pending_count()}",
                    Py4GW.Console.MessageType.Info,
                )
        except (TypeError, ValueError, RuntimeError, AttributeError) as e:
            Py4GW.Console.Log(
                "DropViewer",
                f"ASYNC ID scheduler error: {e}",
                Py4GW.Console.MessageType.Warning,
            )

    def _run_inventory_action(self, action_code: str, action_payload: str = "", action_meta: str = "", reply_email: str = ""):
        return run_inventory_action(self, action_code, action_payload, action_meta, reply_email)

    def _broadcast_inventory_action_to_followers(self, action_code: str, action_payload: str = ""):
        sent = 0
        try:
            sender_email = self._ensure_text(Player.GetAccountEmail()).strip()
            if not sender_email:
                return 0

            shmem = getattr(GLOBAL_CACHE, "ShMem", None)
            if shmem is None:
                return 0

            self_account = shmem.GetAccountDataFromEmail(sender_email)
            if self_account is None:
                return 0

            self_party_id = int(getattr(self_account.AgentPartyData, "PartyID", 0))
            self_map_id = int(getattr(self_account.AgentData.Map, "MapID", 0))
            if self_party_id <= 0 or self_map_id <= 0:
                return 0

            for account in shmem.GetAllAccountData():
                target_email = self._ensure_text(getattr(account, "AccountEmail", "")).strip()
                if not target_email or target_email == sender_email:
                    continue
                if not bool(getattr(account, "IsAccount", False)):
                    continue

                target_party_id = int(getattr(account.AgentPartyData, "PartyID", 0))
                target_map_id = int(getattr(account.AgentData.Map, "MapID", 0))
                if target_party_id != self_party_id or target_map_id != self_map_id:
                    continue

                sent_index = shmem.SendMessage(
                    sender_email=sender_email,
                    receiver_email=target_email,
                    command=SharedCommandType.CustomBehaviors,
                    params=(0.0, 0.0, 0.0, 0.0),
                    ExtraData=(self.inventory_action_tag, action_code[:31], action_payload[:31], ""),
                )
                if sent_index != -1:
                    sent += 1
        except EXPECTED_RUNTIME_ERRORS as e:
            Py4GW.Console.Log("DropViewer", f"Inventory action broadcast failed: {e}", Py4GW.Console.MessageType.Warning)
        return sent

    def _trigger_inventory_action(self, action_code: str, action_payload: str = ""):
        self._run_inventory_action(action_code, action_payload)
        try:
            if Player.GetAgentID() != Party.GetPartyLeaderID():
                return
        except EXPECTED_RUNTIME_ERRORS:
            return

        sent = self._broadcast_inventory_action_to_followers(action_code, action_payload)
        if sent > 0:
            self.set_status(f"{self.status_message} | Sent to {sent} follower(s)")

    def _is_leader_client(self) -> bool:
        try:
            return Player.GetAgentID() == Party.GetPartyLeaderID()
        except EXPECTED_RUNTIME_ERRORS:
            return False

    def _get_conset_specs(self):
        return [
            {
                "key": "armor",
                "name": "Armor of Salvation",
                "model_id": int(getattr(ModelID, "Armor_Of_Salvation", 24860)),
                "effect_name": "Armor_of_Salvation_item_effect",
                "icon": self.conset_armor_icon,
                "enabled": bool(self.auto_conset_armor),
            },
            {
                "key": "grail",
                "name": "Grail of Might",
                "model_id": int(getattr(ModelID, "Grail_Of_Might", 24861)),
                "effect_name": "Grail_of_Might_item_effect",
                "icon": self.conset_grail_icon,
                "enabled": bool(self.auto_conset_grail),
            },
            {
                "key": "essence",
                "name": "Essence of Celerity",
                "model_id": int(getattr(ModelID, "Essence_Of_Celerity", 24859)),
                "effect_name": "Essence_of_Celerity_item_effect",
                "icon": self.conset_essence_icon,
                "enabled": bool(self.auto_conset_essence),
            },
            {
                "key": "legionnaire",
                "name": "Legionnaire Summoning Crystal",
                "model_id": int(getattr(ModelID, "Legionnaire_Summoning_Crystal", 37810)),
                "effect_name": "Summoning_Sickness",
                "icon": self.conset_legionnaire_icon,
                "enabled": bool(self.auto_conset_legionnaire),
            },
        ]

    def _get_effect_id_cached(self, effect_name: str) -> int:
        key = self._ensure_text(effect_name).strip()
        if not key:
            return 0
        if key in self.conset_effect_id_cache:
            return int(self.conset_effect_id_cache[key])
        try:
            skill_id = int(GLOBAL_CACHE.Skill.GetID(key))
        except EXPECTED_RUNTIME_ERRORS:
            skill_id = 0
        self.conset_effect_id_cache[key] = skill_id
        return skill_id

    def _use_model_from_leader_inventory(self, model_id: int, label: str) -> bool:
        if not self._is_leader_client():
            self.set_status(f"{label}: leader only")
            return False
        try:
            item_id = int(GLOBAL_CACHE.Inventory.GetFirstModelID(int(model_id)))
        except EXPECTED_RUNTIME_ERRORS:
            item_id = 0
        if item_id <= 0:
            self.set_status(f"{label}: not found in leader inventory")
            return False
        try:
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            self.set_status(f"{label}: used")
            return True
        except EXPECTED_RUNTIME_ERRORS as e:
            self.set_status(f"{label}: use failed ({e})")
            return False

    def _run_auto_conset_tick(self):
        if not self.auto_conset_enabled:
            return
        if not self._is_leader_client():
            return
        if not self.auto_conset_timer.IsExpired():
            return
        self.auto_conset_timer.Reset()
        try:
            if not Map.IsExplorable():
                return
            if Agent.IsDead(Player.GetAgentID()):
                return
        except EXPECTED_RUNTIME_ERRORS:
            return

        for spec in self._get_conset_specs():
            if not bool(spec["enabled"]):
                continue
            effect_name = self._ensure_text(spec["effect_name"])
            effect_id = 2886 if effect_name == "Summoning_Sickness" else self._get_effect_id_cached(effect_name)
            has_effect = False
            try:
                has_effect = effect_id > 0 and bool(GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), effect_id))
            except EXPECTED_RUNTIME_ERRORS:
                has_effect = False
            if has_effect:
                continue
            if self._use_model_from_leader_inventory(int(spec["model_id"]), self._ensure_text(spec["name"])):
                break

    def _draw_conset_controls(self):
        self._draw_section_header("Conset")
        PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, self._ui_colors()["panel_bg"])
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, (0.28, 0.35, 0.43, 0.72))
        if PyImGui.begin_child("DropTrackerConsetCard", size=(0, 210), border=True, flags=PyImGui.WindowFlags.NoScrollbar):
            before = (self.auto_conset_enabled, self.auto_conset_armor, self.auto_conset_grail, self.auto_conset_essence, self.auto_conset_legionnaire)
            if PyImGui.collapsing_header("Conset Settings"):
                self.auto_conset_enabled = PyImGui.checkbox("Auto Conset (Leader Only)", self.auto_conset_enabled)
                self.auto_conset_armor = PyImGui.checkbox("Auto Armor of Salvation", self.auto_conset_armor)
                self.auto_conset_grail = PyImGui.checkbox("Auto Grail of Might", self.auto_conset_grail)
                self.auto_conset_essence = PyImGui.checkbox("Auto Essence of Celerity", self.auto_conset_essence)
                self.auto_conset_legionnaire = PyImGui.checkbox("Auto Legionnaire Summoning Crystal", self.auto_conset_legionnaire)
            if before != (self.auto_conset_enabled, self.auto_conset_armor, self.auto_conset_grail, self.auto_conset_essence, self.auto_conset_legionnaire):
                self.runtime_config_dirty = True

            PyImGui.separator()
            PyImGui.text_colored("Manual Use", self._ui_colors()["muted"])

            specs = self._get_conset_specs()
            counts = {}
            for spec in specs:
                try:
                    counts[spec["key"]] = int(GLOBAL_CACHE.Inventory.GetModelCount(int(spec["model_id"])))
                except EXPECTED_RUNTIME_ERRORS:
                    counts[spec["key"]] = 0

            if PyImGui.begin_table("DropTrackerConsetIcons", len(specs), PyImGui.TableFlags.SizingStretchSame):
                PyImGui.table_next_row()
                for idx, spec in enumerate(specs):
                    label = self._ensure_text(spec["name"])
                    icon_path = self._ensure_text(spec["icon"])
                    PyImGui.table_set_column_index(idx)
                    clicked = False
                    if os.path.exists(icon_path):
                        self._push_button_style("secondary")
                        clicked = bool(ImGui.ImageButton(f"##droptracker_conset_{spec['key']}", icon_path, 30, 30))
                        PyImGui.pop_style_color(4)
                    else:
                        clicked = self._styled_button(label, "secondary")
                    if clicked:
                        self._use_model_from_leader_inventory(int(spec["model_id"]), label)
                    if PyImGui.is_item_hovered():
                        ImGui.show_tooltip(f"{label}\nLeader inventory: {counts.get(spec['key'], 0)}\nClick to use now")

                PyImGui.table_next_row()
                for idx, spec in enumerate(specs):
                    PyImGui.table_set_column_index(idx)
                    PyImGui.text_colored(f"x{counts.get(spec['key'], 0)}", self._ui_colors()["muted"])

                PyImGui.end_table()

            PyImGui.end_child()
        PyImGui.pop_style_color(2)

    def _collect_local_inventory_kit_stats(self):
        salvage_uses = 0
        salvage_kits = 0
        superior_id_uses = 0
        superior_id_kits = 0
        salvage_kit_model = 2992
        try:
            superior_id_model = int(ModelID.Superior_Identification_Kit.value)
        except EXPECTED_RUNTIME_ERRORS:
            superior_id_model = 5899
        try:
            salvage_kit_model = int(ModelID.Salvage_Kit.value)
        except EXPECTED_RUNTIME_ERRORS:
            salvage_kit_model = 2992
        try:
            bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
            item_array = ItemArray.GetItemArray(bags_to_check)
            for item_id in item_array:
                if int(item_id) <= 0:
                    continue
                try:
                    uses = int(Item.Usage.GetUses(item_id))
                except EXPECTED_RUNTIME_ERRORS:
                    uses = 0
                model_id = 0
                try:
                    model_id = int(Item.GetModelID(item_id))
                except EXPECTED_RUNTIME_ERRORS:
                    model_id = 0
                try:
                    if model_id == salvage_kit_model:
                        salvage_kits += 1
                        salvage_uses += max(0, uses)
                except EXPECTED_RUNTIME_ERRORS:
                    pass
                try:
                    if model_id == superior_id_model:
                        superior_id_kits += 1
                        superior_id_uses += max(0, uses)
                except EXPECTED_RUNTIME_ERRORS:
                    pass
        except EXPECTED_RUNTIME_ERRORS:
            pass
        return {
            "salvage_uses": int(salvage_uses),
            "salvage_kits": int(salvage_kits),
            "superior_id_uses": int(superior_id_uses),
            "superior_id_kits": int(superior_id_kits),
        }

    def _upsert_inventory_kit_stats(self, email: str, character_name: str, party_position: int, stats: dict, map_id: int = 0, party_id: int = 0):
        if not email:
            return
        self.inventory_kit_stats_by_email[email] = {
            "email": email,
            "character_name": character_name or email,
            "party_position": int(party_position),
            "map_id": int(map_id),
            "party_id": int(party_id),
            "salvage_uses": int(stats.get("salvage_uses", 0)),
            "salvage_kits": int(stats.get("salvage_kits", 0)),
            "superior_id_uses": int(stats.get("superior_id_uses", 0)),
            "superior_id_kits": int(stats.get("superior_id_kits", 0)),
            "updated_at": float(time.time()),
        }

    def _request_inventory_kit_stats(self):
        try:
            my_email = self._ensure_text(Player.GetAccountEmail()).strip()
            if not my_email:
                return 0
            shmem = getattr(GLOBAL_CACHE, "ShMem", None)
            if shmem is None:
                return 0

            self_account = shmem.GetAccountDataFromEmail(my_email)
            if self_account is None:
                return 0

            my_stats = self._collect_local_inventory_kit_stats()
            my_name = self._ensure_text(getattr(self_account.AgentData, "CharacterName", "")).strip() or Player.GetName()
            my_party_pos = int(getattr(self_account.AgentPartyData, "PartyPosition", 0))
            my_party_id = int(getattr(self_account.AgentPartyData, "PartyID", 0))
            my_map_id = int(getattr(self_account.AgentData.Map, "MapID", 0))
            self._upsert_inventory_kit_stats(my_email, my_name, my_party_pos, my_stats, my_map_id, my_party_id)

            if my_party_id <= 0 or my_map_id <= 0:
                return 0

            sent = 0
            for account in shmem.GetAllAccountData():
                target_email = self._ensure_text(getattr(account, "AccountEmail", "")).strip()
                if not target_email or target_email == my_email:
                    continue
                if not bool(getattr(account, "IsAccount", False)):
                    continue
                target_party_id = int(getattr(account.AgentPartyData, "PartyID", 0))
                target_map_id = int(getattr(account.AgentData.Map, "MapID", 0))
                if target_party_id != my_party_id or target_map_id != my_map_id:
                    continue
                sent_index = shmem.SendMessage(
                    sender_email=my_email,
                    receiver_email=target_email,
                    command=SharedCommandType.CustomBehaviors,
                    params=(0.0, 0.0, 0.0, 0.0),
                    ExtraData=(self.inventory_stats_request_tag, "", "", ""),
                )
                if sent_index != -1:
                    sent += 1
            return sent
        except EXPECTED_RUNTIME_ERRORS as e:
            Py4GW.Console.Log("DropViewer", f"Kit stats request failed: {e}", Py4GW.Console.MessageType.Warning)
            return 0

    def _send_inventory_kit_stats_response(self, receiver_email: str):
        try:
            receiver_email = self._ensure_text(receiver_email).strip()
            if not receiver_email:
                return False
            my_email = self._ensure_text(Player.GetAccountEmail()).strip()
            if not my_email:
                return False
            shmem = getattr(GLOBAL_CACHE, "ShMem", None)
            if shmem is None:
                return False
            my_account = shmem.GetAccountDataFromEmail(my_email)
            if my_account is None:
                return False

            my_name = self._ensure_text(getattr(my_account.AgentData, "CharacterName", "")).strip() or Player.GetName()
            my_party_pos = int(getattr(my_account.AgentPartyData, "PartyPosition", 0))
            my_party_id = int(getattr(my_account.AgentPartyData, "PartyID", 0))
            my_map_id = int(getattr(my_account.AgentData.Map, "MapID", 0))
            stats = self._collect_local_inventory_kit_stats()
            self._upsert_inventory_kit_stats(my_email, my_name, my_party_pos, stats, my_map_id, my_party_id)

            sent_index = shmem.SendMessage(
                sender_email=my_email,
                receiver_email=receiver_email,
                command=SharedCommandType.CustomBehaviors,
                params=(
                    float(stats["salvage_uses"]),
                    float(stats["superior_id_uses"]),
                    float(stats["salvage_kits"]),
                    float(stats["superior_id_kits"]),
                ),
                ExtraData=(self.inventory_stats_response_tag, my_name[:31], str(my_party_pos)[:31], ""),
            )
            return sent_index != -1
        except EXPECTED_RUNTIME_ERRORS:
            return False

    def _draw_inventory_kit_stats_tab(self):
        c = self._ui_colors()
        if self._styled_button("Refresh Kit Stats", "secondary", tooltip="Request updated kit uses from party members in current map."):
            sent = self._request_inventory_kit_stats()
            self.set_status(f"Requested kit stats from {sent} member(s)")
            self.inventory_kit_stats_refresh_timer.Reset()
        elif self.inventory_kit_stats_refresh_timer.IsExpired():
            self._request_inventory_kit_stats()
            self.inventory_kit_stats_refresh_timer.Reset()

        my_party_id = 0
        my_map_id = 0
        try:
            my_email = self._ensure_text(Player.GetAccountEmail()).strip()
            shmem = getattr(GLOBAL_CACHE, "ShMem", None)
            if shmem is not None and my_email:
                my_account = shmem.GetAccountDataFromEmail(my_email)
                if my_account is not None:
                    my_party_id = int(getattr(my_account.AgentPartyData, "PartyID", 0))
                    my_map_id = int(getattr(my_account.AgentData.Map, "MapID", 0))
        except EXPECTED_RUNTIME_ERRORS:
            pass

        rows = []
        now_ts = time.time()
        for row in self.inventory_kit_stats_by_email.values():
            if my_party_id > 0 and my_map_id > 0:
                if int(row.get("party_id", 0)) != my_party_id or int(row.get("map_id", 0)) != my_map_id:
                    continue
            rows.append(row)

        rows = sorted(rows, key=lambda r: (int(r.get("party_position", 99)), self._ensure_text(r.get("character_name", "")).lower()))
        if not rows:
            PyImGui.text_colored("No kit data yet. Click refresh and ensure followers run Drop Tracker.", c["muted"])
            return

        flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.Resizable | PyImGui.TableFlags.ScrollY
        if PyImGui.begin_table("DropTrackerKitStats", 5, flags, 0.0, 180.0):
            PyImGui.table_setup_column("Character")
            PyImGui.table_setup_column("Role")
            PyImGui.table_setup_column("Salvage Uses")
            PyImGui.table_setup_column("Superior ID Uses")
            PyImGui.table_setup_column("Age")
            PyImGui.table_headers_row()
            for row in rows:
                age_s = max(0, int(now_ts - float(row.get("updated_at", now_ts))))
                role = "Leader" if int(row.get("party_position", 1)) == 0 else "Follower"
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text(self._ensure_text(row.get("character_name", "")))
                PyImGui.table_set_column_index(1)
                PyImGui.text_colored(role, (0.95, 0.86, 0.40, 1.0) if role == "Leader" else c["muted"])
                PyImGui.table_set_column_index(2)
                PyImGui.text(str(int(row.get("salvage_uses", 0))))
                PyImGui.table_set_column_index(3)
                PyImGui.text(str(int(row.get("superior_id_uses", 0))))
                PyImGui.table_set_column_index(4)
                PyImGui.text(f"{age_s}s")
            PyImGui.end_table()

    def _log_drop_to_file(
        self,
        player_name,
        item_name,
        quantity,
        extra_info,
        timestamp_override=None,
        event_id="",
        item_stats="",
        item_id=0,
        sender_email="",
    ):
        self._log_drops_batch(
            [
                {
                    "player_name": player_name,
                    "item_name": item_name,
                    "quantity": quantity,
                    "extra_info": extra_info,
                    "timestamp_override": timestamp_override,
                    "event_id": event_id,
                    "item_stats": item_stats,
                    "item_id": item_id,
                    "sender_email": sender_email,
                }
            ]
        )

    def _build_drop_log_row_from_entry(self, entry: Any, bot_name: str, map_id: int, map_name: str) -> DropLogRow:
        if isinstance(entry, DropLogRow):
            sender_email = self._ensure_text(entry.sender_email).strip().lower()
            if not sender_email:
                sender_email = self._resolve_account_email_by_character_name(self._ensure_text(entry.player_name).strip())
            return DropLogRow(
                timestamp=self._ensure_text(entry.timestamp) or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                viewer_bot=self._ensure_text(bot_name),
                map_id=max(0, self._safe_int(map_id, 0)),
                map_name=self._ensure_text(map_name) or "Unknown",
                player_name=self._ensure_text(entry.player_name) or "Unknown",
                item_name=self._ensure_text(entry.item_name) or "Unknown Item",
                quantity=max(1, self._safe_int(entry.quantity, 1)),
                rarity=self._normalize_rarity_label(entry.item_name, entry.rarity),
                event_id=self._ensure_text(entry.event_id).strip(),
                item_stats=self._ensure_text(entry.item_stats).strip(),
                item_id=max(0, self._safe_int(entry.item_id, 0)),
                sender_email=sender_email,
            )
        if isinstance(entry, dict):
            player_name = entry.get("player_name", "Unknown")
            item_name = entry.get("item_name", "Unknown Item")
            quantity = entry.get("quantity", 1)
            extra_info = entry.get("extra_info", "Unknown")
            timestamp_override = entry.get("timestamp_override", None)
            event_id = self._ensure_text(entry.get("event_id", "")).strip()
            item_stats = self._ensure_text(entry.get("item_stats", "")).strip()
            item_id = max(0, self._safe_int(entry.get("item_id", 0), 0))
            sender_email = self._ensure_text(entry.get("sender_email", "")).strip().lower()
        else:
            player_name = entry[0] if len(entry) > 0 else "Unknown"
            item_name = entry[1] if len(entry) > 1 else "Unknown Item"
            quantity = entry[2] if len(entry) > 2 else 1
            extra_info = entry[3] if len(entry) > 3 else "Unknown"
            timestamp_override = entry[4] if len(entry) > 4 else None
            event_id = self._ensure_text(entry[5]).strip() if len(entry) > 5 else ""
            item_stats = self._ensure_text(entry[6]).strip() if len(entry) > 6 else ""
            item_id = max(0, self._safe_int(entry[7], 0)) if len(entry) > 7 else 0
            sender_email = self._ensure_text(entry[8]).strip().lower() if len(entry) > 8 else ""
        if not sender_email:
            sender_email = self._resolve_account_email_by_character_name(self._ensure_text(player_name).strip())
        if event_id and not item_stats:
            stats_cache_key = self._make_stats_cache_key(event_id, sender_email, player_name)
            item_stats = self._get_cached_stats_text(self.stats_by_event, stats_cache_key)

        timestamp = timestamp_override if timestamp_override else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rarity = self._normalize_rarity_label(item_name, extra_info if extra_info else "Unknown")
        qty = max(1, self._safe_int(quantity, 1))
        return DropLogRow(
            timestamp=timestamp,
            viewer_bot=self._ensure_text(bot_name),
            map_id=max(0, self._safe_int(map_id, 0)),
            map_name=self._ensure_text(map_name) or "Unknown",
            player_name=self._ensure_text(player_name) or "Unknown",
            item_name=self._ensure_text(item_name) or "Unknown Item",
            quantity=qty,
            rarity=rarity,
            event_id=event_id,
            item_stats=item_stats,
            item_id=item_id,
            sender_email=sender_email,
        )

    def _log_drops_batch(self, entries):
        try:
            bot_name = Player.GetName()
            map_id = Map.GetMapID()
            map_name = Map.GetMapName(map_id)
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            drop_rows: list[DropLogRow] = []
            for entry in entries:
                drop_rows.append(self._build_drop_log_row_from_entry(entry, bot_name, map_id, map_name))
            append_drop_log_rows(self.log_path, drop_rows)

            for drop_row in drop_rows:
                if drop_row.event_id:
                    sender_email = self._ensure_text(drop_row.sender_email).strip().lower()
                    stats_cache_key = self._make_stats_cache_key(drop_row.event_id, sender_email, drop_row.player_name)
                    if stats_cache_key:
                        self.stats_by_event[stats_cache_key] = drop_row.item_stats

                row = drop_row.to_runtime_row()
                self.raw_drops.append(row)
                self.total_drops += int(drop_row.quantity)

                canonical_name = self._canonical_agg_item_name(drop_row.item_name, drop_row.rarity, self.aggregated_drops)
                key = (canonical_name, drop_row.rarity)
                if key not in self.aggregated_drops:
                    self.aggregated_drops[key] = {"Quantity": 0, "Count": 0}

                self.aggregated_drops[key]["Quantity"] += int(drop_row.quantity)
                self.aggregated_drops[key]["Count"] += 1

            self.last_read_time = os.path.getmtime(self.log_path) if os.path.exists(self.log_path) else time.time()

        except EXPECTED_RUNTIME_ERRORS as e:
            Py4GW.Console.Log("DropViewer", f"Log Error: {e}", Py4GW.Console.MessageType.Warning)

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


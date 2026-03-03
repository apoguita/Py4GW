import re
import difflib
import time
import csv
import os
import shutil
import json
import datetime
import traceback
from typing import Any, Generator
import PyInventory
import PyAgent
from Py4GWCoreLib.Item import Item
from Py4GWCoreLib.ItemArray import ItemArray
from Py4GWCoreLib.native_src.internals.helpers import encoded_wstr_to_str
from Sources.oazix.CustomBehaviors.PathLocator import PathLocator
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions import IdentifyResponseScheduler
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions import InventoryActionResult
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions import run_inventory_action_result
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import DROP_LOG_HEADER
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import parse_drop_log_file
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import build_state_from_parsed_rows
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import merge_parsed_rows_into_state
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
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_drop_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import extract_event_id_hint
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import iter_circular_indices
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import should_skip_inventory_action_message
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_utility import DropTrackerSender
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_inventory import process_inventory_message
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_event_state import (
    extract_payload_item_name,
    get_cached_stats_text,
    get_event_state,
    get_event_state_payload_text,
    get_event_state_stats_text,
    get_row_names_by_event_and_sender,
    make_sender_identifier,
    make_stats_cache_key,
    update_event_state,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_batch_store import (
    log_drop_to_file,
    log_drops_batch,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_filters import (
    get_filtered_aggregated,
    get_filtered_rows,
    is_gold_row,
    is_rare_rarity,
    passes_filters,
    rebuild_aggregates_from_raw_drops,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_row_updates import (
    build_drop_log_row_from_entry,
    item_names_match,
    set_row_item_name,
    set_row_item_stats,
    should_allow_late_name_update,
    update_rows_item_name_by_event_and_sender,
    update_rows_item_name_by_signature_and_sender,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_item_stats_runtime import (
    build_item_snapshot_payload_from_live_item,
    build_item_stats_from_payload_text,
    build_item_stats_from_snapshot,
    get_live_item_snapshot,
    render_payload_stats_cached,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_inventory_runtime import (
    is_monitoring_settled_for_auto_inventory,
    process_pending_identify_mod_capture,
    process_pending_identify_responses,
    queue_identify_for_rarities,
    queue_salvage_for_rarities,
    refresh_auto_inventory_pending_counts,
    remember_identify_mod_capture_candidates,
    run_auto_inventory_actions_tick,
    run_inventory_routine_job,
)

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_item_selection_runtime import (
    build_item_stats_from_live_item,
    build_selected_row_debug_lines,
    clear_event_stats_cache,
    clear_hover_item_preview,
    collect_selected_item_stats,
    find_best_row_for_item,
    find_best_row_for_item_and_character,
    get_row_stats_text,
    get_selected_item_rows,
    get_selected_row_index,
    identify_item_for_all_characters,
    identify_item_from_row,
    normalize_stats_text,
    render_payload_stats_cached_local,
    request_remote_stats_for_row,
    resolve_account_email_by_character_name,
    resolve_live_item_id_by_name,
    resolve_live_item_id_by_signature,
    resolve_live_item_id_for_row,
    row_matches_selected_item,
    send_inventory_action_to_email,
    send_tracker_stats_chunks_to_email,
    send_tracker_stats_payload_chunks_to_email,
    set_hover_item_preview,
    stats_text_is_basic,
)

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_merchant_runtime import (
    build_auto_buy_kits_merchant_debug_report,
    dump_auto_buy_kits_merchant_debug_report,
    find_merchant_item_by_model,
    find_nearby_merchant_agent_id,
    get_nearby_merchant_candidate_agent_ids,
    get_offered_merchant_items,
    handle_lions_arch_merchant_dialog_if_visible,
    is_merchant_frame_open,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_outpost_jobs_runtime import (
    approach_and_open_merchant,
    build_inventory_slot_order,
    buy_item_from_merchant,
    collect_kit_item_ids_for_sort,
    collect_kit_quantity_map,
    deposit_materials_and_tomes_to_storage,
    inventory_reorder_bucket,
    is_rune_item_for_reorder,
    queue_auto_gold_balance,
    queue_auto_inventory_reorder,
    queue_buy_kits_if_needed,
    queue_manual_sell_gold_items,
    reorder_inventory_after_kits,
    run_auto_gold_balance_job,
    run_auto_inventory_reorder_job,
    run_buy_kits_if_needed_job,
    run_manual_sell_gold_items_job,
    run_outpost_store_job,
    sell_gold_items_except_runes,
    sort_kits_to_front,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_outpost_entry_runtime import (
    refresh_auto_outpost_store_entry_key,
    run_auto_buy_kits_once_on_outpost_entry_tick,
    run_auto_gold_balance_once_on_outpost_entry_tick,
    run_auto_inventory_reorder_once_on_outpost_entry_tick,
    run_auto_outpost_store_tick,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_party_actions import (
    broadcast_inventory_action_to_followers,
    get_party_chesting_enabled,
    is_leader_client,
    schedule_party_action,
    sync_auto_inventory_config_to_followers,
    toggle_party_chesting,
    trigger_inventory_action,
    trigger_party_interact_leader_target,
    trigger_party_invite_all_followers,
    trigger_party_resign_to_outpost,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_conset_and_kit_stats import (
    collect_local_inventory_kit_stats,
    collect_total_identification_uses,
    draw_conset_controls,
    draw_inventory_kit_stats_tab,
    get_conset_specs,
    get_effect_id_cached,
    refresh_legionnaire_entry_key,
    request_inventory_kit_stats,
    run_auto_conset_tick,
    send_inventory_kit_stats_response,
    upsert_inventory_kit_stats,
    use_model_from_leader_inventory,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_unknown_mod_storage import (
    collect_known_mod_ids,
    export_unknown_mod_catalog,
    flush_unknown_mod_catalog_if_dirty,
    get_unknown_mod_count,
    get_unknown_mod_custom_name,
    is_known_or_excluded_mod_id,
    load_mod_database,
    load_unknown_mod_catalog,
    load_unknown_mod_name_map,
    load_unknown_mod_pending_notes,
    normalize_unknown_mod_entry,
    remove_unknown_mod_pending_note,
    save_unknown_mod_catalog,
    save_unknown_mod_name_map,
    save_unknown_mod_pending_notes,
    set_unknown_mod_custom_name,
    unknown_mod_name_map_summary_lines,
    unknown_mod_pending_count,
    unknown_mod_pending_lines,
    upsert_unknown_mod_pending_note,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_unknown_mod_analysis import (
    auto_export_unknown_mod_artifacts_if_due,
    collect_manual_named_mod_lines,
    export_unknown_mod_guess_report,
    get_unknown_mod_unresolved_count,
    guess_unknown_mod_entry,
    unknown_mod_guess_report_entries,
    unknown_mod_guess_summary_lines,
    unknown_mod_item_type_labels,
    unknown_mod_summary_lines,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_unknown_mod_tracking import (
    notify_new_unknown_mod_discovered,
    push_unknown_mod_notification,
    record_unknown_mod_identifiers,
    unknown_mod_notification_lines,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_item_mod_logic import (
    build_identified_name_from_modifiers,
    build_known_spellcast_mod_lines,
    canonical_agg_item_name,
    collect_fallback_mod_lines,
    collect_fallback_rune_lines,
    extract_mod_lines_from_item_name,
    extract_parsed_mod_name_parts,
    format_attribute_name,
    match_mod_definition_against_raw,
    normalize_item_name,
    normalize_rarity_label,
    render_mod_description_template_local,
    weapon_mod_type_matches,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_runtime_config import (
    apply_runtime_config,
    default_runtime_config,
    flush_runtime_config_if_dirty,
    load_runtime_config,
    load_ui_layout_from_config,
    persist_layout_value,
    save_runtime_config,
    sync_runtime_config_from_state,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_session_runtime import (
    arm_reset_trace,
    begin_new_explorable_session,
    clear_map_watch_lines,
    clear_reset_trace_lines,
    flush_pending_tracker_messages,
    get_map_watch_lines,
    get_reset_trace_lines,
    load_drops,
    log_map_watch,
    log_reset_trace,
    parse_log_file_local,
    reset_live_log_file,
    reset_live_session,
    reset_sender_tracking_session,
    reset_trace_active,
    reset_trace_actor_label,
    seal_sender_session_floors,
)

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_runtime_update import (
    process_chat_message,
    run_update_tick,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_status_runtime import (
    get_rarity_color,
    send_tracker_ack,
    set_paused,
    set_status,
    toggle_follower_inventory_viewer,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_base_utils import (
    clean_item_name,
    default_auto_buy_kits_map_model_hints,
    ensure_text,
    get_known_merchant_model_ids,
    is_auto_buy_kits_allowed_outpost,
    is_unknown_item_label,
    normalize_name_for_compare,
    record_successful_kit_merchant_model,
    remember_model_name,
    resolve_unknown_name_from_model,
    safe_int,
    sanitize_map_model_hints,
    should_abort_auto_buy_kits,
    strip_tags,
    trace_auto_buy_kits,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_theme_ui import (
    draw_inline_rarity_filter_buttons,
    draw_runtime_controls,
    draw_runtime_controls_popout,
    draw_section_header,
    draw_status_chip,
    get_session_duration_text,
    push_button_style,
    set_filter_rarity_label,
    styled_button,
    theme_names,
    theme_presets,
    ui_colors,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_ui_state import (
    apply_auto_buy_kits_config_payload,
    apply_auto_buy_kits_sort_config_payload,
    apply_auto_gold_balance_config_payload,
    apply_auto_id_config_payload,
    apply_auto_outpost_store_config_payload,
    apply_auto_salvage_config_payload,
    apply_selected_id_rarities,
    apply_selected_salvage_rarities,
    bitmask_to_rarities,
    decode_auto_action_payload,
    decode_rarities,
    encode_auto_action_payload,
    encode_rarities,
    get_selected_id_rarities,
    get_selected_salvage_rarities,
    parse_toggle_payload,
    rarities_to_bitmask,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_window_file_io import (
    clamp_pos,
    clamp_size,
    draw_hover_handle,
    get_display_size,
    get_inventory_snapshot,
    load_run,
    merge_run,
    mouse_in_current_window_rect,
    save_run,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_draw_tables import (
    draw_aggregated,
    draw_log,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_draw_window import draw_window as render_drop_viewer_window
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_draw_panels import (
    collect_live_status_snapshot,
    draw_auto_inventory_activity,
    draw_inventory_action_cards,
    draw_live_status_chips,
    draw_metric_card,
    draw_rarity_chips,
    draw_selected_item_details,
    draw_status_toast,
    draw_summary_bar,
    draw_top_control_strip,
    draw_view_and_theme_controls,
    format_elapsed_since,
    status_color,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_poll import poll_shared_memory
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats import (
    process_tracker_name_message,
    process_tracker_stats_payload_message,
    process_tracker_stats_text_message,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_tracker import process_tracker_drop_message
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_live_debug import (
    append_live_debug_log,
    clear_live_debug_log,
    get_live_debug_log_path,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_chat import make_chat_dedupe_key
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_chat import pickup_regex
from Sources.oazix.CustomBehaviors.primitives.helpers.map_instance_helper import (
    classify_map_instance_transition,
    read_current_map_instance,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import (
    build_name_chunks,
    make_name_signature,
    encode_name_chunk_meta,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.item_mod_render_utils import (
    build_known_spellcasting_mod_lines,
    prune_generic_attribute_bonus_lines,
    render_mod_description_template,
    sort_stats_lines_like_ingame,
)
from Py4GWCoreLib import * # Includes Map, Player
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

IMPORT_OPTIONAL_ERRORS = (ImportError, ModuleNotFoundError, AttributeError)
EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)

# IDs in this set are known or structural helper modifiers and should not be
# counted as "unknown" even if they are not present in local mods_data files.
UNKNOWN_MOD_EXCLUDE_IDS = frozenset(
    {
        8408,
        8680,
        8728,
        8920,
        8952,
        8968,
        8984,
        9000,
        9112,
        9128,
        9240,
        9400,
        9656,
        9720,
        9736,
        9880,
        10136,
        10296,
        25288,
        26568,
        42120,
        42920,
        42936,
        49152,
    }
)

# Human-readable hints for known IDs that can still exist in historical exports.
UNKNOWN_MOD_KNOWN_NAME_HINTS = {
    8408: "Health loss component",
    8680: "Rune attribute component",
    8728: "Halves casting time of [Attribute] spells",
    8920: "Energy +X",
    8952: "Energy +X (while Enchanted)",
    8968: "Energy +X (while Health is above X%)",
    8984: "Energy +X (while Health is below X%)",
    9000: "Energy +X (while hexed)",
    9112: "Halves skill recharge of [Attribute] spells",
    9128: "Halves skill recharge of spells",
    9240: "[Attribute] +1 (Chance while using skills)",
    9400: "Damage type component",
    9656: "Target item type component",
    9720: "Improved sale value",
    9736: "Highly salvageable",
    9880: "Caster metadata marker",
    10136: "Requirement",
    10296: "[Attribute] +1 (Chance: X%)",
    25288: "Energy +X",
    26568: "Energy +X",
    42120: "Damage (no requirement)",
    42920: "Damage",
    42936: "Shield armor",
    49152: "Structural marker",
}

UNKNOWN_MOD_ITEM_TYPE_HINTS = {
    0: "Salvage",
    5: "Upgrade",
    9: "Tome",
    11: "Material",
    12: "Offhand",
    22: "Wand",
    24: "Shield",
    26: "Staff",
    27: "Sword",
    32: "Daggers",
}

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
        self._log_autoscroll_initialized = False
        self._last_log_autoscroll_total_drops = 0
        self._request_log_scroll_bottom = False
        self._request_agg_scroll_bottom = False
        self._log_table_reset_nonce = 0
        self._agg_table_reset_nonce = 0
        self.view_mode = "Aggregated" # "Log", "Aggregated", "Materials"
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
        self.pickup_regex = pickup_regex()
        
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
        self.event_state_by_key = {}
        self.stats_render_cache_by_event = {}
        self.stats_name_signature_by_event = {}
        self.model_name_by_id = {}
        self.sender_session_floor_by_email = {}
        self.sender_session_last_seen_by_email = {}
        self.mod_db = self._load_mod_database()
        self.known_mod_ids = self._collect_known_mod_ids()
        self.unknown_mod_exclude_ids = set(UNKNOWN_MOD_EXCLUDE_IDS)
        self.unknown_mod_catalog_path = os.path.join(os.path.dirname(constants.DROP_LOG_PATH), "drop_tracker_unknown_mod_ids.json")
        self.unknown_mod_guess_report_path = os.path.join(
            os.path.dirname(constants.DROP_LOG_PATH),
            "drop_tracker_unknown_mod_guesses.json",
        )
        self.unknown_mod_pending_notes_path = os.path.join(
            os.path.dirname(constants.DROP_LOG_PATH),
            "drop_tracker_unknown_mod_pending.json",
        )
        self.unknown_mod_name_map_path = os.path.join(
            os.path.dirname(constants.DROP_LOG_PATH),
            "drop_tracker_unknown_mod_names.json",
        )
        self.unknown_mod_catalog = {}
        self.unknown_mod_catalog_dirty = False
        self.unknown_mod_catalog_flush_timer = ThrottledTimer(1500)
        self.unknown_mod_auto_export_enabled = True
        self.unknown_mod_auto_export_timer = ThrottledTimer(1200)
        self.unknown_mod_guess_auto_export_timer = ThrottledTimer(2500)
        self.unknown_mod_recent_seen = {}
        self.unknown_mod_recent_ttl_s = 15.0
        self.unknown_mod_notify_enabled = True
        self.unknown_mod_recent_notifications: list[str] = []
        self.unknown_mod_recent_notifications_max = 10
        self.unknown_mod_last_notify_status_ts = 0.0
        self.unknown_mod_pending_notes: dict[str, dict[str, Any]] = {}
        self.unknown_mod_popup_enabled = True
        self.unknown_mod_popup_pending = False
        self.unknown_mod_popup_message = ""
        self.unknown_mod_custom_names: dict[str, str] = {}
        self.unknown_mod_name_edit_id = 0
        self.unknown_mod_name_edit_text = ""
        self._load_unknown_mod_catalog()
        self._load_unknown_mod_pending_notes()
        self._load_unknown_mod_name_map()
        self.enable_chat_item_tracking = False
        self.max_shmem_messages_per_tick = 80
        self.max_shmem_scan_per_tick = 600
        self.verbose_shmem_item_logs = False
        self.debug_item_stats_panel = False
        self.debug_item_stats_panel_height = 180
        self.name_trace_recent_lines: list[str] = []
        self.send_tracker_ack_enabled = True
        self.enable_perf_logs = False
        self.seen_event_ttl_seconds = 900.0
        self.seen_events = {}
        self.name_chunk_buffers = {}
        self.full_name_by_signature = {}
        self.last_shmem_poll_ms = 0.0
        self.last_shmem_processed = 0
        self.last_shmem_scanned = 0
        self._shmem_scan_start_index = 0
        self.last_ack_sent = 0
        self.last_seen_map_id = 0
        self.last_seen_instance_uptime_ms = 0
        self.map_change_ignore_until = 0.0
        self.reset_trace_until = 0.0
        self.reset_trace_drop_logs_remaining = 0
        self.reset_trace_lines: list[str] = []
        self.map_watch_lines: list[str] = []
        self.map_watch_last_map_id = 0
        self.map_watch_last_instance_uptime_ms = 0
        self.perf_timer = ThrottledTimer(5000)
        self.shmem_error_timer = ThrottledTimer(5000)
        self.config_poll_timer = ThrottledTimer(2000)
        self.runtime_config_path = os.path.join(os.path.dirname(constants.DROP_LOG_PATH), "drop_tracker_runtime_config.json")
        self.runtime_config = self._default_runtime_config()
        self.runtime_config_dirty = False
        self.live_debug_log_path = get_live_debug_log_path(constants.DROP_LOG_PATH)
        self.inventory_action_tag = "TrackerInvActionV1"
        self.inventory_stats_request_tag = "TrackerInvStatReq"
        self.inventory_stats_response_tag = "TrackerInvStatRes"
        self.id_sel_white = False
        self.id_sel_blue = True
        self.id_sel_green = True
        self.id_sel_purple = True
        self.id_sel_gold = True
        self.auto_id_enabled = False
        self.salvage_sel_white = True
        self.salvage_sel_blue = True
        self.salvage_sel_green = False
        self.salvage_sel_purple = True
        self.salvage_sel_gold = False
        self.auto_salvage_enabled = False
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
        self.auto_legionnaire_last_explorable = False
        self.auto_legionnaire_last_map_id = 0
        self.auto_legionnaire_last_instance_uptime_ms = 0
        self.auto_legionnaire_entry_nonce = 0
        self.auto_legionnaire_current_entry_key = ""
        self.auto_legionnaire_used_entry_key = ""
        self.identify_response_scheduler = IdentifyResponseScheduler()
        self.pending_identify_mod_capture: dict[int, float] = {}
        self.pending_identify_mod_capture_ttl_s = 20.0
        self.pending_identify_mod_capture_max_scan_per_tick = 16
        self.auto_id_timer = ThrottledTimer(2500)
        self.auto_salvage_timer = ThrottledTimer(3000)
        self.auto_buy_kits_timer = ThrottledTimer(4000)
        self.auto_gold_balance_timer = ThrottledTimer(4000)
        self.auto_inventory_snapshot_timer = ThrottledTimer(900)
        self.auto_id_pending_jobs = 0
        self.auto_salvage_pending_jobs = 0
        self.auto_id_last_queued = 0
        self.auto_salvage_last_queued = 0
        self.auto_id_total_queued = 0
        self.auto_salvage_total_queued = 0
        self.auto_id_last_run_ts = 0.0
        self.auto_salvage_last_run_ts = 0.0
        self.auto_monitoring_settle_seconds = 1.2
        self.auto_monitoring_last_gate_status_ts = 0.0
        self.strict_event_stats_binding = True
        self.event_identity_resolve_grace_s = 1.2
        self.auto_queue_progress_cap = 25
        self.auto_id_job_running = False
        self.auto_salvage_job_running = False
        self.auto_buy_kits_enabled = False
        self.auto_buy_kits_sort_to_front_enabled = True
        self.auto_buy_kits_job_running = False
        self.auto_buy_kits_abort_requested = False
        self.auto_buy_kits_handled_entry_key = ""
        self.auto_inventory_reorder_job_running = False
        self.auto_inventory_reorder_handled_entry_key = ""
        # Merchant restock priority list (first matching name in this order is used).
        self.auto_buy_kits_merchant_names = [
            "Answa",
            "Volsung",
            "Bodrus the Outfitter",
            "Hasrah",
            "Acolyte Singpa",
        ]
        self.auto_buy_kits_last_seen_npc_names = []
        self.auto_buy_kits_last_seen_npc_models = []
        self.auto_buy_kits_debug_trace = []
        self.auto_buy_kits_merchant_model_ids_loaded = False
        self.auto_buy_kits_merchant_model_ids = set()
        self.auto_buy_kits_map_model_hints = self._default_auto_buy_kits_map_model_hints()
        self.auto_gold_balance_enabled = False
        self.auto_gold_balance_target = 10_000
        self.auto_gold_balance_job_running = False
        self.auto_gold_balance_handled_entry_key = ""
        self.auto_outpost_store_enabled = False
        self.auto_outpost_store_job_running = False
        self.auto_outpost_store_last_is_outpost = False
        self.auto_outpost_store_last_map_id = 0
        self.auto_outpost_store_last_instance_uptime_ms = 0
        self.auto_outpost_store_entry_nonce = 0
        self.auto_outpost_store_current_entry_key = ""
        self.auto_outpost_store_handled_entry_key = ""
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
            "All", "White", "Blue", "Purple", "Gold", "Green",
            "Dyes", "Keys", "Tomes", "Currency", "Unknown"
        ]
        self.only_rare = False
        self.hide_gold = False
        self.min_qty = 1
        self.show_runtime_panel = False
        self.runtime_controls_popout = False
        self.runtime_popout_initialized = False
        self.compact_mode = False
        self.ui_theme_name = "Midnight"
        self.selected_item_key = None
        self.selected_log_row = None
        self.hover_preview_item_key = None
        self.hover_preview_log_row = None
        self.hover_handle_mode = False
        self.hover_pin_open = False
        self.hover_is_visible = True
        self.hover_hide_delay_s = 0.35
        self.hover_hide_deadline = 0.0
        self.hover_icon_path = PathLocator.get_custom_behaviors_root_directory() + "\\gui\\textures\\Loot.png"
        self.hover_handle_initialized = False
        self.hover_handle_dragging = False
        self.hover_handle_drag_offset = (0.0, 0.0)
        self.viewer_window_initialized = False
        self.saved_hover_handle_pos = None
        self.saved_viewer_window_pos = None
        self.saved_viewer_window_size = None
        self.last_main_window_rect = (0.0, 0.0, 0.0, 0.0)
        self.left_rail_scroll_y = 0.0
        self.layout_save_timer = ThrottledTimer(750)

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        os.makedirs(self.saved_logs_dir, exist_ok=True)

        self._load_runtime_config()
        self._load_ui_layout_from_config()
        # Always start each run with a fresh live log file + empty runtime data.
        self._reset_live_session()

    def _default_runtime_config(self):
        return default_runtime_config(self)


    def _apply_runtime_config(self):
        return apply_runtime_config(self)


    def _load_ui_layout_from_config(self):
        return load_ui_layout_from_config(self)


    def _persist_layout_value(self, key: str, value: tuple[float, float] | None):
        return persist_layout_value(self, key, value)


    def _flush_runtime_config_if_dirty(self):
        return flush_runtime_config_if_dirty(self)


    def _load_runtime_config(self):
        return load_runtime_config(self)


    def _save_runtime_config(self):
        return save_runtime_config(self)


    def _sync_runtime_config_from_state(self):
        return sync_runtime_config_from_state(self)


    def _send_tracker_ack(self, receiver_email: str, event_id: str) -> bool:
        return send_tracker_ack(self, receiver_email, event_id)

    def _append_live_debug_log(self, event: str, message: str, **fields: Any):
        return append_live_debug_log(
            actor="viewer",
            event=event,
            message=message,
            drop_log_path=constants.DROP_LOG_PATH,
            **fields,
        )

    def _clear_live_debug_log(self):
        return clear_live_debug_log(constants.DROP_LOG_PATH)

    def _ensure_text(self, value: Any) -> str:
        return ensure_text(self, value)

    def _normalize_name_for_compare(self, value: Any) -> str:
        return normalize_name_for_compare(self, value)

    def _trace_auto_buy_kits(self, message: Any):
        return trace_auto_buy_kits(self, message)

    def _should_abort_auto_buy_kits(self) -> bool:
        return should_abort_auto_buy_kits(self)

    def _is_auto_buy_kits_allowed_outpost(self) -> bool:
        return is_auto_buy_kits_allowed_outpost(self)

    def _default_auto_buy_kits_map_model_hints(self) -> dict[str, list[int]]:
    # Known working merchant model IDs per map (can be extended/overridden by runtime learning).
        return default_auto_buy_kits_map_model_hints(self)

    def _sanitize_map_model_hints(self, value: Any) -> dict[str, list[int]]:
        return sanitize_map_model_hints(self, value)

    def _get_known_merchant_model_ids(self) -> set[int]:
        return get_known_merchant_model_ids(self)

    def _record_successful_kit_merchant_model(self, agent_id: int):
        return record_successful_kit_merchant_model(self, agent_id)

    def _strip_tags(self, text: Any) -> str:
        return strip_tags(self, text)

    def _clean_item_name(self, name: Any) -> str:
        return clean_item_name(self, name)

    def _is_unknown_item_label(self, name: Any) -> bool:
        return is_unknown_item_label(self, name)

    def _remember_model_name(self, model_id: Any, item_name: Any):
        return remember_model_name(self, model_id, item_name)

    def _resolve_unknown_name_from_model(self, item_name: Any, model_id: Any) -> str:
        return resolve_unknown_name_from_model(self, item_name, model_id)

    def _load_mod_database(self):
        return load_mod_database(self)


    def _collect_known_mod_ids(self) -> set[int]:
        return collect_known_mod_ids(self)


    def _normalize_unknown_mod_entry(self, entry: Any) -> dict[str, Any]:
        return normalize_unknown_mod_entry(self, entry)


    def _load_unknown_mod_catalog(self):
        return load_unknown_mod_catalog(self)


    def _load_unknown_mod_name_map(self):
        return load_unknown_mod_name_map(self)


    def _load_unknown_mod_pending_notes(self):
        return load_unknown_mod_pending_notes(self)


    def _save_unknown_mod_pending_notes(self) -> bool:
        return save_unknown_mod_pending_notes(self)


    def _upsert_unknown_mod_pending_note(
        self,
        ident: int,
        owner_name: str = "",
        item_name: str = "",
        arg1: int = 0,
        arg2: int = 0,
        item_type: int = 0,
        model_id: int = 0,
        source: str = "",
    ):
        return upsert_unknown_mod_pending_note(self, ident, owner_name, item_name, arg1, arg2, item_type, model_id, source)


    def _remove_unknown_mod_pending_note(self, ident: int) -> bool:
        return remove_unknown_mod_pending_note(self, ident)


    def _unknown_mod_pending_lines(self, limit: int = 8) -> list[str]:
        return unknown_mod_pending_lines(self, limit)


    def _unknown_mod_pending_count(self) -> int:
        return unknown_mod_pending_count(self)


    def _save_unknown_mod_name_map(self) -> bool:
        return save_unknown_mod_name_map(self)


    def _set_unknown_mod_custom_name(self, ident: int, name: str) -> bool:
        return set_unknown_mod_custom_name(self, ident, name)


    def _get_unknown_mod_custom_name(self, ident: int) -> str:
        return get_unknown_mod_custom_name(self, ident)


    def _unknown_mod_name_map_summary_lines(self, limit: int = 4) -> list[str]:
        return unknown_mod_name_map_summary_lines(self, limit)


    def _collect_manual_named_mod_lines(self, raw_mods) -> list[str]:
        return collect_manual_named_mod_lines(self, raw_mods)


    def _save_unknown_mod_catalog(self):
        return save_unknown_mod_catalog(self)


    def _flush_unknown_mod_catalog_if_dirty(self, force: bool = False):
        return flush_unknown_mod_catalog_if_dirty(self, force)


    def _get_unknown_mod_count(self) -> int:
        return get_unknown_mod_count(self)


    def _is_known_or_excluded_mod_id(self, ident: int) -> bool:
        return is_known_or_excluded_mod_id(self, ident)


    def _unknown_mod_item_type_labels(self, item_types, limit: int = 3) -> list[str]:
        return unknown_mod_item_type_labels(self, item_types, limit)


    def _unknown_mod_summary_lines(self, limit: int = 8) -> list[str]:
        return unknown_mod_summary_lines(self, limit)


    def _push_unknown_mod_notification(self, line: str):
        return push_unknown_mod_notification(self, line)


    def _unknown_mod_notification_lines(self, limit: int = 4) -> list[str]:
        return unknown_mod_notification_lines(self, limit)


    def _notify_new_unknown_mod_discovered(
        self,
        ident: int,
        arg1: int,
        arg2: int,
        owner_name: str = "",
        item_name: str = "",
        item_type: int = 0,
        model_id: int = 0,
        source: str = "",
    ):
        return notify_new_unknown_mod_discovered(self, ident, arg1, arg2, owner_name, item_name, item_type, model_id, source)


    def _guess_unknown_mod_entry(self, ident: int, entry: dict[str, Any]) -> dict[str, Any]:
        return guess_unknown_mod_entry(self, ident, entry)


    def _unknown_mod_guess_report_entries(self, include_known: bool = True) -> list[dict[str, Any]]:
        return unknown_mod_guess_report_entries(self, include_known)


    def _get_unknown_mod_unresolved_count(self) -> int:
        return get_unknown_mod_unresolved_count(self)


    def _unknown_mod_guess_summary_lines(self, limit: int = 8, include_known: bool = False) -> list[str]:
        return unknown_mod_guess_summary_lines(self, limit, include_known)


    def _export_unknown_mod_guess_report(self, include_known: bool = True) -> str:
        return export_unknown_mod_guess_report(self, include_known)


    def _auto_export_unknown_mod_artifacts_if_due(self, force: bool = False):
        return auto_export_unknown_mod_artifacts_if_due(self, force)


    def _record_unknown_mod_identifiers(
        self,
        raw_mods,
        snapshot: dict[str, Any] | None = None,
        source: str = "",
        suppress_mod_ids: set[int] | None = None,
    ):
        return record_unknown_mod_identifiers(self, raw_mods, snapshot, source, suppress_mod_ids)


    def _export_unknown_mod_catalog(self) -> str:
        return export_unknown_mod_catalog(self)


    def _format_attribute_name(self, attr_name: Any) -> str:
        return format_attribute_name(self, attr_name)


    def _render_mod_description_template(
        self,
        description: str,
        matched_modifiers: list[tuple[int, int, int]],
        default_value: int = 0,
        attribute_name: str = "",
    ) -> list[str]:
        return render_mod_description_template_local(self, description, matched_modifiers, default_value, attribute_name)


    def _match_mod_definition_against_raw(self, definition_modifiers, raw_mods) -> list[tuple[int, int, int]]:
        return match_mod_definition_against_raw(self, definition_modifiers, raw_mods)


    def _weapon_mod_type_matches(self, weapon_mod, item_type) -> bool:
        return weapon_mod_type_matches(self, weapon_mod, item_type)


    def _collect_fallback_mod_lines(self, raw_mods, item_attr_txt: str, item_type=None) -> list[str]:
        return collect_fallback_mod_lines(self, raw_mods, item_attr_txt, item_type)


    def _collect_fallback_rune_lines(self, raw_mods, item_attr_txt: str) -> list[str]:
        return collect_fallback_rune_lines(self, raw_mods, item_attr_txt)


    def _build_known_spellcast_mod_lines(self, raw_mods, item_attr_txt: str, item_type=None) -> list[str]:
        return build_known_spellcast_mod_lines(self, raw_mods, item_attr_txt, item_type)


    def _normalize_item_name(self, name: Any) -> str:
        return normalize_item_name(self, name)


    def _extract_mod_lines_from_item_name(self, item_name: Any) -> list[str]:
        return extract_mod_lines_from_item_name(self, item_name)


    def _extract_parsed_mod_name_parts(self, parsed_result) -> tuple[str, str, str]:
        return extract_parsed_mod_name_parts(self, parsed_result)


    def _build_identified_name_from_modifiers(
        self,
        base_name: Any,
        raw_mods: list[tuple[int, int, int]],
        item_type_int: int,
        model_id: int,
    ) -> str:
        return build_identified_name_from_modifiers(self, base_name, raw_mods, item_type_int, model_id)


    def _canonical_agg_item_name(self, item_name: Any, rarity: Any, agg: dict) -> str:
        return canonical_agg_item_name(self, item_name, rarity, agg)


    def _normalize_rarity_label(self, item_name: Any, rarity: Any) -> str:
        return normalize_rarity_label(self, item_name, rarity)


    def _reset_live_log_file(self):
        return reset_live_log_file(self)


    def _reset_live_session(self):
        return reset_live_session(self)


    def _arm_reset_trace(
        self,
        reason: str,
        previous_map_id: int = 0,
        current_map_id: int = 0,
        previous_instance_uptime_ms: int = 0,
        current_instance_uptime_ms: int = 0,
    ):
        return arm_reset_trace(
            self,
            reason,
            previous_map_id,
            current_map_id,
            previous_instance_uptime_ms,
            current_instance_uptime_ms,
        )


    def _reset_trace_active(self) -> bool:
        return reset_trace_active(self)


    def _reset_trace_actor_label(self) -> str:
        return reset_trace_actor_label(self)


    def _log_reset_trace(self, message: str, consume: bool = False):
        return log_reset_trace(self, message, consume)


    def _get_reset_trace_lines(self) -> list[str]:
        return get_reset_trace_lines(self)


    def _clear_reset_trace_lines(self):
        return clear_reset_trace_lines(self)


    def _log_map_watch(self, message: str):
        return log_map_watch(self, message)


    def _get_map_watch_lines(self) -> list[str]:
        return get_map_watch_lines(self)


    def _clear_map_watch_lines(self):
        return clear_map_watch_lines(self)


    def _seal_sender_session_floors(self):
        return seal_sender_session_floors(self)


    def _reset_sender_tracking_session(self, current_map_id: int = 0, current_instance_uptime_ms: int = 0):
        return reset_sender_tracking_session(self, current_map_id, current_instance_uptime_ms)


    def _begin_new_explorable_session(
        self,
        reason: str,
        current_map_id: int = 0,
        current_instance_uptime_ms: int = 0,
        status_message: str = "Auto reset on map change",
    ):
        self._append_live_debug_log(
            "viewer_session_reset",
            f"reason={str(reason or '').strip() or 'unknown'}",
            reason=str(reason or "").strip() or "unknown",
            current_map_id=int(current_map_id or 0),
            current_instance_uptime_ms=int(current_instance_uptime_ms or 0),
            status_message=str(status_message or ""),
            total_drops=int(self.total_drops),
        )
        return begin_new_explorable_session(
            self,
            reason,
            current_map_id,
            current_instance_uptime_ms,
            status_message,
        )


    def _flush_pending_tracker_messages(self) -> int:
        return flush_pending_tracker_messages(self)


    def load_drops(self):
        return load_drops(self)


    def _parse_log_file(self, filepath):
        return parse_log_file_local(self, filepath)


    def set_status(self, msg):
        return set_status(self, msg)

    def _set_paused(self, paused: bool):
        return set_paused(self, paused)

    def _toggle_follower_inventory_viewer(self):
        return toggle_follower_inventory_viewer(self)

    def _safe_int(self, value, default=0):
        return safe_int(self, value, default)

    def _parse_drop_row(self, row: Any) -> DropLogRow | None:
        return parse_runtime_row(row)

    def _set_row_item_stats(self, row: Any, item_stats: str) -> None:
        set_row_item_stats(self, row, item_stats)

    def _set_row_item_id(self, row: Any, item_id: int) -> None:
        set_runtime_row_item_id(row, int(item_id))

    def _set_row_item_name(self, row: Any, item_name: Any) -> None:
        set_row_item_name(self, row, item_name)

    def _should_allow_late_name_update(self, rarity: Any, current_name: Any, proposed_name: Any = "") -> bool:
        return should_allow_late_name_update(self, rarity, current_name, proposed_name)

    def _update_rows_item_name_by_event_and_sender(
        self,
        event_id: str,
        sender_email: str,
        item_name: Any,
        player_name: str = "",
        only_if_unknown: bool = False,
    ) -> int:
        return update_rows_item_name_by_event_and_sender(
            self,
            event_id,
            sender_email,
            item_name,
            player_name=player_name,
            only_if_unknown=only_if_unknown,
        )

    def _update_rows_item_name_by_signature_and_sender(
        self,
        name_signature: str,
        sender_email: str,
        item_name: Any,
        player_name: str = "",
    ) -> int:
        return update_rows_item_name_by_signature_and_sender(
            self,
            name_signature,
            sender_email,
            item_name,
            player_name=player_name,
        )

    def _rebuild_aggregates_from_raw_drops(self) -> None:
        return rebuild_aggregates_from_raw_drops(self)

    def _is_rare_rarity(self, rarity):
        return is_rare_rarity(self, rarity)

    def _passes_filters(self, row):
        return passes_filters(self, row)

    def _get_filtered_rows(self):
        return get_filtered_rows(self)

    def _is_gold_row(self, row):
        return is_gold_row(self, row)

    def _get_filtered_aggregated(self, filtered_rows):
        return get_filtered_aggregated(self, filtered_rows)

    def _extract_row_event_id(self, row) -> str:
        return self._ensure_text(extract_runtime_row_event_id(row)).strip()

    def _extract_row_item_stats(self, row) -> str:
        return self._ensure_text(extract_runtime_row_item_stats(row)).strip()

    def _extract_row_item_id(self, row) -> int:
        return max(0, int(extract_runtime_row_item_id(row)))

    def _extract_row_sender_email(self, row) -> str:
        return self._ensure_text(extract_runtime_row_sender_email(row)).strip().lower()

    def _make_sender_identifier(self, sender_email: str = "", player_name: str = "") -> str:
        return make_sender_identifier(self, sender_email, player_name)

    def _make_stats_cache_key(self, event_id: str, sender_email: str = "", player_name: str = "") -> str:
        return make_stats_cache_key(self, event_id, sender_email, player_name)

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
        return get_cached_stats_text(self, cache, event_key)

    def _log_name_trace(self, message: str) -> None:
        if not bool(getattr(self, "verbose_shmem_item_logs", False)):
            return
        line = self._ensure_text(message).strip()
        if not line:
            return
        recent = getattr(self, "name_trace_recent_lines", None)
        if not isinstance(recent, list):
            self.name_trace_recent_lines = []
            recent = self.name_trace_recent_lines
        recent.append(line)
        if len(recent) > 120:
            del recent[:-120]
        Py4GW.Console.Log(
            "DropViewerNameTrace",
            line,
            Py4GW.Console.MessageType.Info,
        )

    def _get_row_names_by_event_and_sender(
        self,
        event_id: str,
        sender_email: str = "",
        player_name: str = "",
    ) -> list[str]:
        return get_row_names_by_event_and_sender(self, event_id, sender_email, player_name)

    def _build_unidentified_stats_text(self) -> str:
        return "Unidentified"

    def _is_unidentified_stats_text(self, stats_text: Any) -> bool:
        return self._normalize_stats_text(stats_text).lower() == "unidentified"

    def _infer_identified_from_stats_text(self, stats_text: Any):
        normalized = self._normalize_stats_text(stats_text)
        if not normalized:
            return None
        if normalized.lower() == "unidentified":
            return False
        return True

    def _payload_is_identified(self, payload_text: str):
        payload_raw = self._ensure_text(payload_text).strip()
        if not payload_raw:
            return None
        try:
            payload = json.loads(payload_raw)
        except EXPECTED_RUNTIME_ERRORS:
            return None
        if not isinstance(payload, dict):
            return None
        if "i" in payload:
            return bool(payload.get("i"))
        mods = list(payload.get("mods", []) or [])
        if mods:
            return True
        return None

    def _get_event_state(self, cache_key: str, create: bool = False) -> dict[str, Any]:
        return get_event_state(self, cache_key, create)

    def _update_event_state(
        self,
        cache_key: str,
        identified: Any = None,
        name_signature: str = "",
        payload_text: str = "",
        stats_text: str = "",
        set_payload_text: bool = False,
        set_stats_text: bool = False,
    ) -> dict[str, Any]:
        return update_event_state(
            self,
            cache_key,
            identified=identified,
            payload_text=payload_text,
            stats_text=stats_text,
            set_payload_text=set_payload_text,
            set_stats_text=set_stats_text,
        )

    def _get_event_state_stats_text(self, cache_key: str) -> str:
        return get_event_state_stats_text(self, cache_key)

    def _get_event_state_payload_text(self, cache_key: str) -> str:
        return get_event_state_payload_text(self, cache_key)

    def _resolve_live_item_id_for_row(self, row, prefer_unidentified: bool = False) -> int:
        return resolve_live_item_id_for_row(self, row, prefer_unidentified)

    def _resolve_live_item_id_by_name(self, item_name: Any, prefer_identified: bool = False) -> int:
        return resolve_live_item_id_by_name(self, item_name, prefer_identified)

    def _resolve_live_item_id_by_signature(
        self,
        name_signature: Any,
        rarity_hint: Any = "",
        prefer_identified: bool = False,
    ) -> int:
        return resolve_live_item_id_by_signature(self, name_signature, rarity_hint, prefer_identified)

    def _resolve_account_email_by_character_name(self, character_name: str) -> str:
        return resolve_account_email_by_character_name(self, character_name)

    def _send_inventory_action_to_email(self, receiver_email: str, action_code: str, action_payload: str = "", action_meta: str = "") -> bool:
        return send_inventory_action_to_email(self, receiver_email, action_code, action_payload, action_meta)

    def _send_tracker_stats_chunks_to_email(self, receiver_email: str, event_id: str, item_stats: str, tag: str = "TrackerStatsV1") -> bool:
        return send_tracker_stats_chunks_to_email(self, receiver_email, event_id, item_stats, tag)

    def _send_tracker_stats_payload_chunks_to_email(self, receiver_email: str, event_id: str, payload_text: str) -> bool:
        return send_tracker_stats_payload_chunks_to_email(self, receiver_email, event_id, payload_text)

    def _get_live_item_snapshot(self, item_id: int, item_name: str = "") -> dict[str, Any]:
        return get_live_item_snapshot(self, item_id, item_name)

    def _build_item_snapshot_payload_from_live_item(self, item_id: int, item_name: str = "") -> str:
        return build_item_snapshot_payload_from_live_item(self, item_id, item_name)

    def _build_item_stats_from_snapshot(self, snapshot: dict[str, Any]) -> str:
        return build_item_stats_from_snapshot(self, snapshot)

    def _normalize_stats_text(self, stats_text: Any) -> str:
        return normalize_stats_text(self, stats_text)

    def _build_item_stats_from_payload_text(
        self,
        payload_text: str,
        fallback_item_name: str = "",
        owner_name: str = "",
    ) -> str:
        return build_item_stats_from_payload_text(self, payload_text, fallback_item_name, owner_name)

    def _extract_payload_item_name(self, payload_text: str, fallback_item_name: str = "") -> str:
        return extract_payload_item_name(self, payload_text, fallback_item_name)

    def _clear_event_stats_cache(self, event_id: str, sender_email: str = "", player_name: str = "", clear_all_matching: bool = False):
        return clear_event_stats_cache(self, event_id, sender_email, player_name, clear_all_matching)

    def _render_payload_stats_cached(
        self,
        cache_key: str,
        payload_text: str,
        fallback_item_name: str = "",
        owner_name: str = "",
    ) -> str:
        return render_payload_stats_cached_local(self, cache_key, payload_text, fallback_item_name, owner_name)

    def _request_remote_stats_for_row(self, row, force_refresh: bool = False):
        return request_remote_stats_for_row(self, row, force_refresh)

    def _build_item_stats_from_live_item(self, item_id: int, item_name: str = "") -> str:
        return build_item_stats_from_live_item(self, item_id, item_name)

    def _stats_text_is_basic(self, stats_text: Any) -> bool:
        return stats_text_is_basic(self, stats_text)

    def _identify_item_from_row(self, row) -> bool:
        return identify_item_from_row(self, row)

    def _get_row_stats_text(self, row) -> str:
        return get_row_stats_text(self, row)

    def _build_selected_row_debug_lines(self, row) -> list[str]:
        return build_selected_row_debug_lines(self, row)

    def _item_names_match(self, selected_name: Any, row_name: Any) -> bool:
        return item_names_match(self, selected_name, row_name)

    def _clear_hover_item_preview(self) -> None:
        return clear_hover_item_preview(self)

    def _set_hover_item_preview(self, item_key: Any, row: Any) -> None:
        return set_hover_item_preview(self, item_key, row)

    def _row_matches_selected_item(self, row, item_key=None) -> bool:
        return row_matches_selected_item(self, row, item_key)

    def _find_best_row_for_item(self, item_name: str, rarity: str, rows) -> Any:
        return find_best_row_for_item(self, item_name, rarity, rows)

    def _find_best_row_for_item_and_character(self, item_name: str, rarity: str, character_name: str, rows=None) -> Any:
        return find_best_row_for_item_and_character(self, item_name, rarity, character_name, rows)

    def _get_selected_item_rows(self, rows=None, item_key=None) -> list[Any]:
        return get_selected_item_rows(self, rows, item_key)

    def _get_selected_row_index(self, selected_rows: list[Any]) -> int:
        return get_selected_row_index(self, selected_rows)

    def _identify_item_for_all_characters(self, item_name: str, rarity: str, rows=None) -> bool:
        return identify_item_for_all_characters(self, item_name, rarity, rows)

    def _collect_selected_item_stats(self, item_key=None):
        return collect_selected_item_stats(self, item_key)

    def _draw_selected_item_details(self):
        draw_selected_item_details(self)

    def _get_session_duration_text(self):
        return get_session_duration_text(self)

    def _ui_colors(self):
        return ui_colors(self)

    def _theme_presets(self):
        return theme_presets(self)

    def _theme_names(self):
        return theme_names(self)

    def _push_button_style(self, variant: str = "secondary"):
        return push_button_style(self, variant)

    def _styled_button(self, label: str, variant: str = "secondary", width: float = 0.0, height: float = 0.0, tooltip: str = ""):
        return styled_button(self, label, variant, width, height, tooltip)

    def _set_filter_rarity_label(self, rarity_label: str) -> None:
        return set_filter_rarity_label(self, rarity_label)

    def _draw_inline_rarity_filter_buttons(self) -> None:
        return draw_inline_rarity_filter_buttons(self)

    def _draw_section_header(self, title: str):
        return draw_section_header(self, title)

    def _draw_status_chip(self, label: str, variant: str = "secondary", tooltip: str = ""):
        return draw_status_chip(self, label, variant, tooltip)

    def _collect_live_status_snapshot(self):
        return collect_live_status_snapshot(self)

    def _draw_top_control_strip(self):
        draw_top_control_strip(self)

    def _draw_live_status_chips(self):
        draw_live_status_chips(self)

    def _format_elapsed_since(self, timestamp_value: float) -> str:
        return format_elapsed_since(self, timestamp_value)

    def _refresh_auto_inventory_pending_counts(self, force: bool = False):
        refresh_auto_inventory_pending_counts(self, force=force)

    def _draw_auto_inventory_activity(self):
        draw_auto_inventory_activity(self)

    def _draw_view_and_theme_controls(self):
        draw_view_and_theme_controls(self)

    def _draw_inventory_action_cards(self):
        draw_inventory_action_cards(self)

    def _draw_status_toast(self, message: str):
        draw_status_toast(self, message)

    def _draw_rarity_chips(self, prefix: str, rarities: list[str]):
        draw_rarity_chips(self, prefix, rarities)

    def _status_color(self, msg: str):
        return status_color(self, msg)

    def _draw_metric_card(self, card_id, title, value, accent_color):
        draw_metric_card(self, card_id, title, value, accent_color)

    def _draw_summary_bar(self, filtered_rows):
        draw_summary_bar(self, filtered_rows)

    def _draw_runtime_controls(self):
        return draw_runtime_controls(self)

    def _draw_runtime_controls_popout(self):
        return draw_runtime_controls_popout(self)

    def _get_selected_id_rarities(self):
        return get_selected_id_rarities(self)

    def _get_selected_salvage_rarities(self):
        return get_selected_salvage_rarities(self)

    def _encode_rarities(self, rarities):
        return encode_rarities(self, rarities)

    def _decode_rarities(self, payload):
        return decode_rarities(self, payload)

    def _apply_selected_id_rarities(self, rarities):
        return apply_selected_id_rarities(self, rarities)

    def _apply_selected_salvage_rarities(self, rarities):
        return apply_selected_salvage_rarities(self, rarities)

    def _rarities_to_bitmask(self, rarities):
        return rarities_to_bitmask(self, rarities)

    def _bitmask_to_rarities(self, mask):
        return bitmask_to_rarities(self, mask)

    def _encode_auto_action_payload(self, enabled: bool, rarities):
        return encode_auto_action_payload(self, enabled, rarities)

    def _decode_auto_action_payload(self, payload, default_enabled: bool, default_rarities):
        return decode_auto_action_payload(self, payload, default_enabled, default_rarities)

    def _apply_auto_id_config_payload(self, payload):
        return apply_auto_id_config_payload(self, payload)

    def _apply_auto_salvage_config_payload(self, payload):
        return apply_auto_salvage_config_payload(self, payload)

    def _parse_toggle_payload(self, payload: str, fallback: bool = False) -> bool:
        return parse_toggle_payload(self, payload, fallback)

    def _apply_auto_outpost_store_config_payload(self, payload: str):
        return apply_auto_outpost_store_config_payload(self, payload)

    def _apply_auto_buy_kits_config_payload(self, payload: str):
        return apply_auto_buy_kits_config_payload(self, payload)

    def _apply_auto_buy_kits_sort_config_payload(self, payload: str):
        return apply_auto_buy_kits_sort_config_payload(self, payload)

    def _apply_auto_gold_balance_config_payload(self, payload: str):
        return apply_auto_gold_balance_config_payload(self, payload)

    def _mouse_in_current_window_rect(self):
        return mouse_in_current_window_rect(self)

    def _get_display_size(self):
        return get_display_size(self)

    def _clamp_pos(self, x, y, w, h, margin=4.0):
        return clamp_pos(self, x, y, w, h, margin)

    def _clamp_size(self, w, h, min_w=420.0, min_h=280.0, margin=20.0):
        return clamp_size(self, w, h, min_w, min_h, margin)

    def _draw_hover_handle(self):
        return draw_hover_handle(self)

    def save_run(self):
        return save_run(self)

    def load_run(self, filename):
        return load_run(self, filename)

    def merge_run(self, filename):
        return merge_run(self, filename)

    def draw(self):
        return render_drop_viewer_window(self)

    def _draw_aggregated(self, filtered_rows, materials_only=False):
        return draw_aggregated(self, filtered_rows, materials_only)

    def _draw_log(self, filtered_rows):
        return draw_log(self, filtered_rows)

    def update(self):
        return run_update_tick(self)

    def _process_chat_message(self, msg: Any):
        return process_chat_message(self, msg)

    def _poll_shared_memory(self):
        return poll_shared_memory(self)

    def _get_inventory_snapshot(self):
        return get_inventory_snapshot(self)

    def _find_merchant_item_by_model(self, model_id: int) -> int:
        return find_merchant_item_by_model(self, model_id)


    def _build_auto_buy_kits_merchant_debug_report(self) -> str:
        return build_auto_buy_kits_merchant_debug_report(self)


    def _dump_auto_buy_kits_merchant_debug_report(self) -> int:
        return dump_auto_buy_kits_merchant_debug_report(self)


    def _build_inventory_slot_order(self) -> list[tuple[int, int]]:
        return build_inventory_slot_order(self)


    def _collect_kit_item_ids_for_sort(self) -> list[int]:
        return collect_kit_item_ids_for_sort(self)


    def _collect_kit_quantity_map(self) -> dict[int, int]:
        return collect_kit_quantity_map(self)


    def _is_rune_item_for_reorder(self, item_id: int) -> bool:
        return is_rune_item_for_reorder(self, item_id)


    def _inventory_reorder_bucket(self, item_id: int) -> int:
        return inventory_reorder_bucket(self, item_id)


    def _reorder_inventory_after_kits(self) -> Generator[Any, Any, int]:
        return reorder_inventory_after_kits(self)


    def _sort_kits_to_front(self, priority_item_ids: list[int] | None = None) -> Generator[Any, Any, int]:
        return sort_kits_to_front(self, priority_item_ids)


    def _buy_item_from_merchant(self, offered_item_id: int, quantity: int) -> Generator[Any, Any, int]:
        return buy_item_from_merchant(self, offered_item_id, quantity)


    def _approach_and_open_merchant(self, agent_id: int) -> Generator[Any, Any, bool]:
        return approach_and_open_merchant(self, agent_id)


    def _run_buy_kits_if_needed_job(self, verbose_status: bool = True) -> Generator[Any, Any, None]:
        return run_buy_kits_if_needed_job(self, verbose_status)


    def _queue_buy_kits_if_needed(self, verbose_status: bool = True) -> int:
        return queue_buy_kits_if_needed(self, verbose_status)


    def _run_auto_gold_balance_job(self, verbose_status: bool = True) -> Generator[Any, Any, None]:
        return run_auto_gold_balance_job(self, verbose_status)


    def _queue_auto_gold_balance(self, verbose_status: bool = True) -> int:
        return queue_auto_gold_balance(self, verbose_status)


    def _run_auto_gold_balance_once_on_outpost_entry_tick(self) -> bool:
        return run_auto_gold_balance_once_on_outpost_entry_tick(self)


    def _run_auto_inventory_reorder_job(self, verbose_status: bool = True) -> Generator[Any, Any, None]:
        return run_auto_inventory_reorder_job(self, verbose_status)


    def _queue_auto_inventory_reorder(self, verbose_status: bool = True) -> int:
        return queue_auto_inventory_reorder(self, verbose_status)


    def _run_auto_inventory_reorder_once_on_outpost_entry_tick(self) -> bool:
        return run_auto_inventory_reorder_once_on_outpost_entry_tick(self)


    def _run_auto_buy_kits_once_on_outpost_entry_tick(self) -> bool:
        return run_auto_buy_kits_once_on_outpost_entry_tick(self)


    def _refresh_auto_outpost_store_entry_key(self) -> str:
        return refresh_auto_outpost_store_entry_key(self)


    def _deposit_materials_and_tomes_to_storage(self):
        return deposit_materials_and_tomes_to_storage(self)


    def _sell_gold_items_except_runes(self):
        return sell_gold_items_except_runes(self)


    def _run_manual_sell_gold_items_job(self):
        return run_manual_sell_gold_items_job(self)


    def _queue_manual_sell_gold_items(self) -> int:
        return queue_manual_sell_gold_items(self)


    def _run_outpost_store_job(self, entry_key: str):
        return run_outpost_store_job(self, entry_key)


    def _run_auto_outpost_store_tick(self, force: bool = False) -> bool:
        return run_auto_outpost_store_tick(self, force)


    def _remember_identify_mod_capture_candidates(self, item_ids) -> int:
        return remember_identify_mod_capture_candidates(self, item_ids)

    def _process_pending_identify_mod_capture(self):
        process_pending_identify_mod_capture(self)

    def _process_pending_identify_responses(self):
        process_pending_identify_responses(self)

    def _run_auto_inventory_actions_tick(self):
        run_auto_inventory_actions_tick(self)

    def _run_inventory_action(self, action_code: str, action_payload: str = "", action_meta: str = "", reply_email: str = ""):
        return run_inventory_action_result(self, action_code, action_payload, action_meta, reply_email)

    def _broadcast_inventory_action_to_followers(self, action_code: str, action_payload: str = ""):
        return broadcast_inventory_action_to_followers(self, action_code, action_payload)


    def _trigger_inventory_action(self, action_code: str, action_payload: str = ""):
        return trigger_inventory_action(self, action_code, action_payload)


    def _sync_auto_inventory_config_to_followers(self):
        return sync_auto_inventory_config_to_followers(self)


    def _is_leader_client(self) -> bool:
        return is_leader_client(self)


    def _schedule_party_action(self, action_gen, action_label: str) -> bool:
        return schedule_party_action(self, action_gen, action_label)


    def _trigger_party_resign_to_outpost(self) -> bool:
        return trigger_party_resign_to_outpost(self)


    def _trigger_party_invite_all_followers(self) -> bool:
        return trigger_party_invite_all_followers(self)


    def _get_party_chesting_enabled(self) -> bool:
        return get_party_chesting_enabled(self)


    def _toggle_party_chesting(self) -> bool:
        return toggle_party_chesting(self)


    def _trigger_party_interact_leader_target(self) -> bool:
        return trigger_party_interact_leader_target(self)


    def _get_conset_specs(self):
        return get_conset_specs(self)


    def _get_effect_id_cached(self, effect_name: str) -> int:
        return get_effect_id_cached(self, effect_name)


    def _use_model_from_leader_inventory(self, model_id: int, label: str) -> bool:
        return use_model_from_leader_inventory(self, model_id, label)


    def _run_auto_conset_tick(self):
        return run_auto_conset_tick(self)


    def _refresh_legionnaire_entry_key(self) -> str:
        return refresh_legionnaire_entry_key(self)


    def _draw_conset_controls(self, card_height=None):
        return draw_conset_controls(self, card_height)


    def _collect_local_inventory_kit_stats(self):
        return collect_local_inventory_kit_stats(self)


    def _collect_total_identification_uses(self) -> int:
        return collect_total_identification_uses(self)


    def _upsert_inventory_kit_stats(self, email: str, character_name: str, party_position: int, stats: dict, map_id: int = 0, party_id: int = 0):
        return upsert_inventory_kit_stats(self, email, character_name, party_position, stats, map_id, party_id)


    def _request_inventory_kit_stats(self):
        return request_inventory_kit_stats(self)


    def _send_inventory_kit_stats_response(self, receiver_email: str):
        return send_inventory_kit_stats_response(self, receiver_email)


    def _draw_inventory_kit_stats_tab(self):
        return draw_inventory_kit_stats_tab(self)


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
        return log_drop_to_file(
            self,
            player_name,
            item_name,
            quantity,
            extra_info,
            timestamp_override=timestamp_override,
            event_id=event_id,
            item_stats=item_stats,
            item_id=item_id,
            sender_email=sender_email,
        )

    def _build_drop_log_row_from_entry(self, entry: Any, bot_name: str, map_id: int, map_name: str) -> DropLogRow:
        return build_drop_log_row_from_entry(self, entry, bot_name, map_id, map_name)

    def _log_drops_batch(self, entries):
        log_drops_batch(self, entries)

    def _get_rarity_color(self, rarity):
        return get_rarity_color(self, rarity)

drop_viewer = DropViewerWindow()

def main():
    pass

def draw_window():
    try:
        drop_viewer.update()
        drop_viewer.draw()
    except Exception as e:
        try:
            Py4GW.Console.Log("DropViewer", f"draw_window failed: {e}", Py4GW.Console.MessageType.Error)
            tb_text = traceback.format_exc(limit=4)
            for line in str(tb_text or "").splitlines():
                line = str(line or "").strip()
                if line:
                    Py4GW.Console.Log("DropViewer", line, Py4GW.Console.MessageType.Error)
        except Exception:
            pass

def update():
    try:
        drop_viewer.update()
    except Exception as e:
        try:
            Py4GW.Console.Log("DropViewer", f"update failed: {e}", Py4GW.Console.MessageType.Error)
        except Exception:
            pass

if __name__ == "__main__":
    pass





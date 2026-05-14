import os
from dataclasses import dataclass
from typing import Optional

import Py4GW
import PyImGui

from Py4GWCoreLib import Map, Merchant, Player, Routines
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.enums_src.GameData_enums import Attribute, Profession
from Py4GWCoreLib.enums_src.Item_enums import INVENTORY_BAGS, STORAGE_BAGS, Bags, ItemType
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.item_data.ItemData import ITEM_DATA, ItemData
from Py4GWCoreLib.item_data.item_snapshot import ItemSnapshot
from Py4GWCoreLib.native_src.internals import string_table
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

MODULE_NAME = 'Data Collector'
MODULE_ICON = os.path.join(Py4GW.Console.get_projects_path(), 'Textures', 'Module_Icons', 'Data Collector.png')
widget_handler = get_widget_handler()

@dataclass
class DataCollectorConfig:
    ini_path: str = 'Widgets/System/'
    main_ini_filename: str = 'DataCollector.ini'
    floating_ini_filename: str = 'DataCollectorFloating.ini'
    settings_section: str = 'Settings'
    enabled_var_name: str = 'collector_enabled'
    enabled_key_name: str = 'collector_enabled'

    main_ini_key: str = ''
    floating_ini_key: str = ''
    ini_init: bool = False
    icon_path: str = MODULE_ICON

    def _ensure_ini(self) -> bool:
        if self.ini_init:
            return True

        ini = IniManager()
        self.main_ini_key = ini.ensure_global_key(
            self.ini_path,
            self.main_ini_filename,
        )
        self.floating_ini_key = ini.ensure_global_key(
            self.ini_path,
            self.floating_ini_filename,
        )
        if not self.main_ini_key or not self.floating_ini_key:
            return False

        ini.add_bool(
            self.main_ini_key,
            self.enabled_var_name,
            self.settings_section,
            self.enabled_key_name,
            True,
        )
        ini.load_once(self.main_ini_key)
        ini.load_once(self.floating_ini_key)

        self.ini_init = True
        
        return True

class ItemDataCollector:
    def __init__(self, inventory_interval_ms: int = 5_000, save_interval_ms: int = 1_000):
        self.checked_item_ids: set[int] = set()
        self.checked_model_keys: set[tuple[ItemType, int]] = set()
        self.current_context_key = ''
        self.storage_checked_for_context = False
        self.force_inventory_scan = True

        self.run_throttle = ThrottledTimer(250)
        self.inventory_throttle = ThrottledTimer(inventory_interval_ms)
        self.trader_throttle = ThrottledTimer(1_000)
        self.save_throttle = ThrottledTimer(save_interval_ms)

    def run(self):
        if not self.run_throttle.IsExpired():
            self.flush_pending_save()
            return

        self.run_throttle.Reset()
        self.flush_pending_save()

        if not self._is_ready():
            return

        self._handle_context_change()

        if not self.storage_checked_for_context:
            self._scan_bags(STORAGE_BAGS)
            self.storage_checked_for_context = True

        if self.force_inventory_scan or self.inventory_throttle.IsExpired():
            self.inventory_throttle.Reset()
            self.force_inventory_scan = False
            self._scan_bags(INVENTORY_BAGS)

        if self.trader_throttle.IsExpired():
            self.trader_throttle.Reset()
            self._scan_trader_items()

        self.flush_pending_save()

    def flush_pending_save(self):
        if ITEM_DATA.requires_save and self.save_throttle.IsExpired():
            ITEM_DATA.save_data_if_queued()
            self.save_throttle.Reset()

    def request_inventory_scan(self):
        self.force_inventory_scan = True

    def _is_ready(self) -> bool:
        return Map.IsMapReady() and Player.IsPlayerLoaded()

    def _handle_context_change(self):
        context_key = self._get_context_key()
        if context_key == self.current_context_key:
            return

        self.current_context_key = context_key
        self.storage_checked_for_context = False
        self.force_inventory_scan = True
        self.checked_item_ids.clear()
        self.checked_model_keys.clear()

    def _get_context_key(self) -> str:
        account_email = str(Player.GetAccountEmail() or '').strip()
        player_name = str(Player.GetName() or '').strip()
        map_id = int(Map.GetMapID() or 0)
        return f'{account_email}|{player_name}|{map_id}'

    def _scan_bags(self, bags: list[Bags]):
        import PyInventory

        snapshot: dict[Bags, dict[int, Optional[ItemSnapshot]]] = {}

        for bag in bags:
            inventory_bag = PyInventory.Bag(bag.value, bag.name)
            bag_snapshot: dict[int, Optional[ItemSnapshot]] = {}

            bag_size = inventory_bag.GetSize()

            for slot in range(bag_size):
                bag_snapshot[slot] = None

            for item in inventory_bag.GetItems():
                slot = item.slot
                bag_snapshot[slot] = ItemSnapshot.from_item_id(item.item_id, item) if item else None

            snapshot[bag] = bag_snapshot

        items = [item for bag in snapshot.values() for item in bag.values() if item is not None]

        for item in items:
            self._collect_item(item)

    def _scan_trader_items(self):
        offered_items = Merchant.Trading.Merchant.GetOfferedItems()
        offered_items = offered_items + Merchant.Trading.Trader.GetOfferedItems()
        offered_items = offered_items + Merchant.Trading.Trader.GetOfferedItems2()
        offered_items = offered_items + Merchant.Trading.Crafter.GetOfferedItems()
        offered_items = offered_items + Merchant.Trading.Collector.GetOfferedItems()

        for item_id in offered_items:
            item = ItemSnapshot.from_item_id(item_id) if item_id else None
            if item is None:
                continue
            self._collect_item(item)

    def _collect_item(self, item: ItemSnapshot):
        if not item.is_valid or item.model_id <= 0 or item.item_type == ItemType.Unknown:
            return

        model_key = (item.item_type, item.model_id)
        item_data = ITEM_DATA.get_or_create_item_data(item.item_type, item.model_id)
        if (item.id in self.checked_item_ids or model_key in self.checked_model_keys) and not self._item_needs_more_data(item_data):
            return

        changed = False

        if item_data.model_file_id <= 0 and item.model_file_id > 0:
            item_data.model_file_id = item.model_file_id
            changed = True

        name_encoded = self._get_name_enc_encoded(item)
        if name_encoded and item_data.name_encoded != name_encoded:
            item_data.name_encoded = name_encoded
            changed = True

        name_enc = self._get_name_enc(item)
        if name_enc and item_data.english_name != name_enc:
            item_data.english_name = name_enc
            changed = True

        if item.attribute not in (None, Attribute.None_) and item.attribute not in item_data.attributes:
            item_data.attributes = sorted(item_data.attributes + [item.attribute], key=lambda attr: attr.name)
            changed = True

        if item.profession not in (None, Profession._None) and item_data.profession != item.profession:
            item_data.profession = item.profession
            changed = True

        if changed:
            ITEM_DATA.queue_save()

        if not self._item_needs_more_data(item_data):
            self.checked_item_ids.add(item.id)
            self.checked_model_keys.add(model_key)

    def _item_needs_more_data(self, item_data: ItemData) -> bool:
        return (
            item_data.model_file_id <= 0
            or not item_data.name_encoded
            or not item_data.english_name
            or (
                item_data.item_type in {
                    ItemType.Axe,
                    ItemType.Bow,
                    ItemType.Daggers,
                    ItemType.Hammer,
                    ItemType.Offhand,
                    ItemType.Scythe,
                    ItemType.Shield,
                    ItemType.Spear,
                    ItemType.Staff,
                    ItemType.Sword,
                    ItemType.Wand,
                    ItemType.Headpiece,
                    ItemType.Chestpiece,
                    ItemType.Gloves,
                    ItemType.Leggings,
                    ItemType.Boots,
                }
                and len(item_data.attributes) == 0
            )
        )

    def _get_name_enc_encoded(self, item: ItemSnapshot) -> bytes:
        name_enc = item.name_enc
        try:
            if isinstance(name_enc, bytes):
                return name_enc
            if isinstance(name_enc, bytearray):
                return bytes(name_enc)
            if isinstance(name_enc, (list, tuple)):
                return bytes(name_enc)
        except Exception:
            pass

        return bytes()

    def _get_name_enc(self, item: ItemSnapshot) -> str:
        candidate = self._coerce_bytes(item.name_enc)
        if candidate:
            try:
                decoded = string_table.decode_plain(candidate, language=ServerLanguage.English)
                if decoded:
                    return decoded
            except Exception:
                pass

        return ''

    def _coerce_bytes(self, value) -> bytes:
        try:
            if isinstance(value, bytes):
                return value
            if isinstance(value, bytearray):
                return bytes(value)
            if isinstance(value, (list, tuple)):
                return bytes(value)
        except Exception:
            pass

        return bytes()

class DataCollector:
    def __init__(self):
        self.config = DataCollectorConfig()
        self.run_throttle = ThrottledTimer(250)
        self.item_data_collector = ItemDataCollector()
        
        self.collector_enabled = True
        self.floating_button: ImGui.FloatingIcon | None = None
        self._settings_loaded = False
        self._startup_sync_done = False

    def _apply_startup_enabled_state(self):
        if self._startup_sync_done:
            return

        self._startup_sync_done = True
        if not self.collector_enabled:
            widget_handler.disable_widget(MODULE_NAME)

    def _sync_manual_widget_enable(self):
        if not self._startup_sync_done or self.collector_enabled:
            return

        info = widget_handler.get_widget_info(MODULE_NAME)
        if info is None or not info.enabled:
            return

        self.set_collector_enabled(True)

    def _ensure_state(self) -> bool:
        if not self.config._ensure_ini():
            return False

        if not self._settings_loaded:
            self._load_settings()
            self._settings_loaded = True
            self._apply_startup_enabled_state()
        else:
            self._sync_manual_widget_enable()

        if self.floating_button is None:
            self.floating_button = ImGui.FloatingIcon(
                icon_path=MODULE_ICON,
                window_id='##floating_icon_data_collector_button',
                window_name='Data Collector Toggle',
                tooltip_visible='Hide data collector window',
                tooltip_hidden='Show data collector window',
                toggle_ini_key=self.config.floating_ini_key,
                toggle_var_name='show_main_window',
                toggle_default=True,
                draw_callback=self.draw_window,
            )
            
        return True
    
    def _load_settings(self):
        self.collector_enabled = bool(
            IniManager().getBool(
                self.config.main_ini_key,
                self.config.enabled_var_name,
                default=True,
                section=self.config.settings_section,
            )
        )
        
    def _save_settings(self):
        ini = IniManager()
        ini.set(
            self.config.main_ini_key,
            self.config.enabled_var_name,
            bool(self.collector_enabled),
            section=self.config.settings_section,
        )
        ini.save_vars(self.config.main_ini_key)

    def set_collector_enabled(self, enabled: bool):
        enabled = bool(enabled)
        if self.collector_enabled == enabled:
            return

        self.collector_enabled = enabled
        self._save_settings()
        
        if not self.collector_enabled:
            Py4GW.Console.Log(MODULE_NAME, 'Data collector is disabled. Enable the widgete again to start contributing by collecting data.', Py4GW.Console.MessageType.Warning)
            widget_handler.disable_widget(MODULE_NAME)
        else:
            Py4GW.Console.Log(MODULE_NAME, 'Data collector is enabled. Thank you for contributing by collecting data!', Py4GW.Console.MessageType.Success)
            widget_handler.enable_widget(MODULE_NAME)

    def draw_window(self):
        if not self._ensure_state() or not self.floating_button:
            return
        
        PyImGui.set_next_window_size((400, 0), PyImGui.ImGuiCond.FirstUseEver)
        expanded, open_ = ImGui.BeginWithClose(
            ini_key=self.config.main_ini_key,
            name=MODULE_NAME,
            p_open=self.floating_button.visible,
            flags=PyImGui.WindowFlags.NoFlag,
        )
        self.floating_button.sync_begin_with_close(open_)

        if expanded:
            style = ImGui.get_style()
            color = ColorPalette.DarkGreen.value if self.collector_enabled else ColorPalette.DarkRed.value
            
            style.Button.push_color_direct(color.opacity(0.6).rgb_tuple)
            style.ButtonActive.push_color_direct(color.opacity(0.7).rgb_tuple)
            style.ButtonHovered.push_color_direct(color.opacity(0.8).rgb_tuple)            
            if ImGui.button("Collecting data ..." if self.collector_enabled else "Stopped!", width=-1):
                self.set_collector_enabled(not self.collector_enabled)
                
            style.Button.pop_color_direct()
            style.ButtonActive.pop_color_direct()
            style.ButtonHovered.pop_color_direct()
            
            PyImGui.separator()
            PyImGui.text(f'Collector status: {"Running" if self.collector_enabled else "Paused"}')
            PyImGui.text(f'Map ready: {"Yes" if Map.IsMapReady() else "No"}')
            PyImGui.text(f'Player loaded: {"Yes" if Player.IsPlayerLoaded() else "No"}')
            PyImGui.text(f'Current context: {self.item_data_collector.current_context_key or "-"}')
            PyImGui.text(f'Collected item ids: {len(self.item_data_collector.checked_item_ids)}')
            PyImGui.text(f'Collected models: {len(self.item_data_collector.checked_model_keys)}')
            PyImGui.text(f'Pending item-data save: {"Yes" if ITEM_DATA.requires_save else "No"}')

        ImGui.End(self.config.main_ini_key)

    def draw(self):
        if not self._ensure_state():
            return
        
        if self.floating_button is not None:
            self.floating_button.draw(self.config.floating_ini_key)
    
    def run(self):
        if not self._ensure_state():
            return

        if not self.run_throttle.IsExpired():
            return

        self.run_throttle.Reset()

        if not Map.IsMapReady() or not Player.IsPlayerLoaded():
            return

        if self.collector_enabled:
            self.item_data_collector.run()
            
    def flush(self):
        self.item_data_collector.flush_pending_save()

DATA_COLLECTOR = DataCollector()
    
def on_disable():
    DATA_COLLECTOR.set_collector_enabled(False)

def tooltip():
    PyImGui.set_next_window_size((600, 0))
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.image(MODULE_ICON, (32, 32))
    PyImGui.same_line(0, 10)
    ImGui.push_font('Regular', 20)
    ImGui.text_aligned(MODULE_NAME, alignment=Alignment.MidLeft, color=title_color.color_tuple, height=32)
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text('Collects and enriches item metadata while you play.')
    PyImGui.text('It inspects inventory, storage, and merchant offerings')
    PyImGui.text('to fill in missing model ids, encoded names, English names,')
    PyImGui.text('and relevant attribute or profession data.')
    PyImGui.spacing()
    PyImGui.text_colored('Features:', title_color.to_tuple_normalized())
    PyImGui.bullet_text('Floating icon with a small persisted control window.')
    PyImGui.bullet_text('INI-backed toggle to pause or resume collection.')
    PyImGui.bullet_text('On-demand inventory rescan and queued-save flush.')
    PyImGui.spacing()
    PyImGui.text_colored('Credits:', title_color.to_tuple_normalized())
    PyImGui.bullet_text('Developed by frenkey')
    PyImGui.end_tooltip()

def main():
    try:
        if not DATA_COLLECTOR._ensure_state():
            return
        
        if not Routines.Checks.Map.MapValid():
            return
        
        DATA_COLLECTOR.run()
            
    except Exception as exc:
        Py4GW.Console.Log(MODULE_NAME, f'Error: {exc}', Py4GW.Console.MessageType.Error)
        raise


__all__ = ['main']


if __name__ == '__main__':
    main()

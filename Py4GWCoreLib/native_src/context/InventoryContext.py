import PyPointers
import PyCallback
from ctypes import (
    Structure, POINTER,
    c_uint32, c_uint16, c_uint8, c_float, c_void_p,
    cast
)
from ..internals.gw_array import GW_Array, GW_Array_Value_View
from ..internals.types import DyeInfoStruct
from typing import List, Optional

# Import DamageType enum - handle import path for both direct and package use
try:
    from Py4GWCoreLib.enums_src.GameData_enums import DamageType
except ImportError:
    from ...enums_src.GameData_enums import DamageType


# GameContext offsets (from GWCA GameContext.h)
GAMECONTEXT_ITEMCONTEXT_OFFSET = 0x40  # ItemContext* items at offset 0x40
# ItemContext offsets (from GWCA ItemContext.h)
ITEMCONTEXT_INVENTORY_OFFSET = 0xF8    # Inventory* inventory at offset 0xF8

# Damage type modifier identifier (from GWCA)
DAMAGE_TYPE_MODIFIER_ID = 9400

# Common weapon modifier identifiers (from GWCA ItemModifier.h)
# These are the identifier values (mod >> 16)
MOD_ID_HSR = 0x2509  # Half Skill Recharge (arg = attribute, arg2 = chance)
MOD_ID_HCT = 0x2508  # Half Casting Time (arg = attribute, arg2 = chance)
MOD_ID_ENERGY = 0x24F8  # +Energy
MOD_ID_ARMOR = 0x24E8  # +Armor
MOD_ID_HP = 0x24FE  # +Health
MOD_ID_ENCHANT_DURATION = 0x250F  # Enchantment duration +%


class ItemModifierStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("mod", c_uint32),
    ]

    @property
    def identifier(self) -> int:
        return self.mod >> 16

    @property
    def arg1(self) -> int:
        return (self.mod & 0x0000FF00) >> 8

    @property
    def arg2(self) -> int:
        return self.mod & 0x000000FF

    @property
    def arg(self) -> int:
        return self.mod & 0x0000FFFF


class BagStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("bag_type", c_uint32),       # +0x0000 BagType enum
        ("index", c_uint32),          # +0x0004
        ("_unknown0", c_uint32),      # +0x0008
        ("container_item", c_uint32), # +0x000C
        ("items_count", c_uint32),    # +0x0010
        ("bag_array", c_void_p),      # +0x0014 Bag*
        ("items", GW_Array),          # +0x0018 ItemArray
    ]

    @property
    def is_inventory_bag(self) -> bool:
        return self.bag_type == 1  # BagType::Inventory

    @property
    def is_storage_bag(self) -> bool:
        return self.bag_type == 4  # BagType::Storage

    @property
    def is_material_storage(self) -> bool:
        return self.bag_type == 5  # BagType::MaterialStorage


class ItemStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("item_id", c_uint32),             # +0x0000
        ("agent_id", c_uint32),            # +0x0004
        ("bag_equipped_ptr", c_void_p),    # +0x0008 Bag*
        ("bag_ptr", c_void_p),             # +0x000C Bag*
        ("mod_struct_ptr", c_void_p),      # +0x0010 ItemModifier*
        ("mod_struct_size", c_uint32),     # +0x0014
        ("customized_ptr", c_void_p),      # +0x0018 wchar_t*
        ("model_file_id", c_uint32),       # +0x001C
        ("type", c_uint8),                 # +0x0020 ItemType
        ("dye", DyeInfoStruct),            # +0x0021
        ("value", c_uint16),               # +0x0024
        ("h0026", c_uint16),               # +0x0026
        ("interaction", c_uint32),         # +0x0028
        ("model_id", c_uint32),            # +0x002C
        ("info_string_ptr", c_void_p),     # +0x0030 wchar_t*
        ("name_enc_ptr", c_void_p),        # +0x0034 wchar_t*
        ("complete_name_enc_ptr", c_void_p), # +0x0038 wchar_t*
        ("single_item_name_ptr", c_void_p), # +0x003C wchar_t*
        ("h0040", c_uint32 * 2),           # +0x0040
        ("item_formula", c_uint16),        # +0x0048
        ("is_material_salvageable", c_uint8), # +0x004A
        ("h004B", c_uint8),                # +0x004B
        ("quantity", c_uint16),            # +0x004C
        ("equipped", c_uint8),             # +0x004E
        ("profession", c_uint8),           # +0x004F
        ("slot", c_uint8),                 # +0x0050
    ]

    def get_modifier(self, identifier: int) -> Optional[ItemModifierStruct]:
        """Get a specific modifier by identifier."""
        if not self.mod_struct_ptr or self.mod_struct_size == 0:
            return None

        mod_array = cast(self.mod_struct_ptr, POINTER(ItemModifierStruct * self.mod_struct_size))
        if not mod_array:
            return None

        for i in range(self.mod_struct_size):
            mod = mod_array.contents[i]
            if mod.identifier == identifier:
                return mod
        return None

    def get_damage_type(self) -> int:
        """Get the damage type of the item (-1 if none/unknown)."""
        mod = self.get_modifier(DAMAGE_TYPE_MODIFIER_ID)
        if mod:
            return mod.arg1
        return -1

    def get_damage_type_name(self) -> str:
        """Get the damage type name of the item."""
        damage_type = self.get_damage_type()
        if damage_type >= 0:
            try:
                return DamageType(damage_type).name
            except ValueError:
                return "Physical"
        return "Physical"

    def get_mod_summary(self) -> str:
        """Get a brief summary of important item modifiers."""
        if not self.mod_struct_ptr or self.mod_struct_size == 0:
            return ""

        summaries = []

        try:
            mod_array = cast(self.mod_struct_ptr, POINTER(ItemModifierStruct * self.mod_struct_size))
            if not mod_array:
                return ""

            hsr_total = 0
            hct_total = 0
            energy_bonus = 0
            armor_bonus = 0
            hp_bonus = 0

            for i in range(self.mod_struct_size):
                mod = mod_array.contents[i]
                ident = mod.identifier

                if ident == MOD_ID_HSR:
                    hsr_total = max(hsr_total, mod.arg2)
                elif ident == MOD_ID_HCT:
                    hct_total = max(hct_total, mod.arg2)
                elif ident == MOD_ID_ENERGY:
                    energy_bonus += mod.arg2
                elif ident == MOD_ID_ARMOR:
                    armor_bonus += mod.arg2
                elif ident == MOD_ID_HP:
                    hp_bonus += mod.arg2

            if hct_total > 0 and hsr_total > 0:
                summaries.append(f"{hct_total}/{hsr_total}")
            elif hct_total > 0:
                summaries.append(f"{hct_total}% HCT")
            elif hsr_total > 0:
                summaries.append(f"{hsr_total}% HSR")

            if energy_bonus > 0:
                summaries.append(f"+{energy_bonus}e")
            if armor_bonus > 0:
                summaries.append(f"+{armor_bonus}AR")
            if hp_bonus > 0:
                summaries.append(f"+{hp_bonus}HP")

        except (ValueError, OSError):
            pass

        return " ".join(summaries)


class WeaponSetStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("weapon_ptr", POINTER(ItemStruct)),   # +0x0000 Item*
        ("offhand_ptr", POINTER(ItemStruct)),  # +0x0004 Item*
    ]

    @property
    def weapon(self) -> Optional[ItemStruct]:
        """Return the main hand weapon item if available."""
        if self.weapon_ptr:
            try:
                return self.weapon_ptr.contents
            except ValueError:
                return None
        return None

    @property
    def offhand(self) -> Optional[ItemStruct]:
        """Return the off-hand item if available."""
        if self.offhand_ptr:
            try:
                return self.offhand_ptr.contents
            except ValueError:
                return None
        return None

    @property
    def has_weapon(self) -> bool:
        return self.weapon is not None

    @property
    def has_offhand(self) -> bool:
        return self.offhand is not None

    @property
    def weapon_damage_type(self) -> int:
        """Get the damage type of the main weapon (-1 if none)."""
        weapon = self.weapon
        if weapon:
            return weapon.get_damage_type()
        return -1

    @property
    def weapon_damage_type_name(self) -> str:
        """Get the damage type name of the main weapon."""
        weapon = self.weapon
        if weapon:
            return weapon.get_damage_type_name()
        return "Physical"

    @property
    def offhand_damage_type(self) -> int:
        """Get the damage type of the off-hand (-1 if none or not applicable)."""
        offhand = self.offhand
        if offhand:
            # Exclude shield (24) and focus/offhand (12) - they don't have damage types
            if offhand.type not in (24, 12):
                return offhand.get_damage_type()
        return -1

    @property
    def offhand_damage_type_name(self) -> str:
        """Get the damage type name of the off-hand weapon."""
        offhand = self.offhand
        if offhand and offhand.type not in (24, 12):
            return offhand.get_damage_type_name()
        return ""

    # Two-handed weapon types: Staff, Hammer, Bow, Scythe, Daggers
    _TWO_HANDED_TYPES = {26, 15, 5, 35, 32}

    # Weapon type names for display
    _WEAPON_TYPE_NAMES = {
        2: "Axe", 5: "Bow", 15: "Hammer", 22: "Wand",
        26: "Staff", 27: "Sword", 32: "Daggers",
        35: "Scythe", 36: "Spear",
    }

    @property
    def weapon_type_name(self) -> str:
        """Get the weapon type name (Sword, Wand, Staff, etc.)."""
        weapon = self.weapon
        if weapon:
            return self._WEAPON_TYPE_NAMES.get(weapon.type, f"Unknown({weapon.type})")
        return ""

    @property
    def is_two_handed(self) -> bool:
        """Check if main hand weapon is two-handed (Staff, Hammer, Bow, Scythe, Daggers)."""
        weapon = self.weapon
        return weapon is not None and weapon.type in self._TWO_HANDED_TYPES

    @property
    def is_shield(self) -> bool:
        """Check if off-hand is a shield."""
        offhand = self.offhand
        return offhand is not None and offhand.type == 24

    @property
    def is_focus(self) -> bool:
        """Check if off-hand is a focus (ItemType.Offhand = 12)."""
        offhand = self.offhand
        return offhand is not None and offhand.type == 12

    @property
    def weapon_mods_summary(self) -> str:
        """Get a summary of weapon mods (HCT/HSR, +energy, etc.)."""
        weapon = self.weapon
        if weapon:
            return weapon.get_mod_summary()
        return ""

    @property
    def offhand_mods_summary(self) -> str:
        """Get a summary of off-hand mods."""
        offhand = self.offhand
        if offhand:
            return offhand.get_mod_summary()
        return ""


class InventoryStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("bags", c_void_p * 23),              # +0x0000 Bag*[23]
        ("bundle_ptr", c_void_p),             # +0x005C Item*
        ("storage_panes_unlocked", c_uint32), # +0x0060
        ("weapon_sets", WeaponSetStruct * 4), # +0x0064 WeaponSet[4]
        ("active_weapon_set", c_uint32),      # +0x0084
        ("h0088", c_uint32 * 2),              # +0x0088
        ("gold_character", c_uint32),         # +0x0090
        ("gold_storage", c_uint32),           # +0x0094
    ]

    def get_weapon_set(self, index: int) -> Optional[WeaponSetStruct]:
        """Get a specific weapon set by index (0-3)."""
        if 0 <= index <= 3:
            return self.weapon_sets[index]
        return None

    @property
    def active_weapon_set_index(self) -> int:
        """Get the index of the currently active weapon set."""
        return self.active_weapon_set

    def get_active_weapon_set(self) -> Optional[WeaponSetStruct]:
        """Get the currently active weapon set."""
        return self.get_weapon_set(self.active_weapon_set)

    def get_all_weapon_sets(self) -> List[WeaponSetStruct]:
        """Get all 4 weapon sets."""
        return [self.weapon_sets[i] for i in range(4)]


class ItemContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", GW_Array),                  # +0x0000 Array<void*>
        ("h0010", GW_Array),                  # +0x0010 Array<void*>
        ("h0020", c_uint32),                  # +0x0020
        ("bags_array", GW_Array),             # +0x0024 Array<Bag*>
        ("h0034", c_uint8 * 12),              # +0x0034
        ("h0040", GW_Array),                  # +0x0040 Array<void*>
        ("h0050", GW_Array),                  # +0x0050 Array<void*>
        ("h0060", c_uint8 * 88),              # +0x0060
        ("item_array", GW_Array),             # +0x00B8 Array<Item*>
        ("h00C8", c_uint8 * 48),              # +0x00C8
        ("inventory_ptr", POINTER(InventoryStruct)), # +0x00F8 Inventory*
        ("h00FC", GW_Array),                  # +0x00FC Array<void*>
    ]

    @property
    def inventory(self) -> Optional[InventoryStruct]:
        """Return the Inventory if available."""
        if self.inventory_ptr:
            try:
                return self.inventory_ptr.contents
            except ValueError:
                return None
        return None

    @property
    def items(self) -> List[Optional[ItemStruct]]:
        """Get the item array as a list of ItemStruct (or None for empty slots)."""
        if not self.item_array.m_buffer or self.item_array.m_size == 0:
            return []

        ptrs = GW_Array_Value_View(self.item_array, POINTER(ItemStruct)).to_list()
        if not ptrs:
            return []

        out: List[Optional[ItemStruct]] = []
        for ptr in ptrs:
            if not ptr:
                out.append(None)
                continue
            try:
                out.append(ptr.contents)
            except ValueError:
                out.append(None)
        return out

    def get_item_by_id(self, item_id: int) -> Optional[ItemStruct]:
        """Get an item by its ID."""
        items = self.items
        if item_id > 0 and item_id < len(items):
            return items[item_id]
        return None


def _read_ptr_at_offset(base_ptr: int, offset: int) -> int:
    """Read a pointer value from memory at base_ptr + offset."""
    if not base_ptr:
        return 0
    try:
        ptr_addr = base_ptr + offset
        return cast(ptr_addr, POINTER(c_uint32)).contents.value
    except (ValueError, OSError):
        return 0


class ItemContext:
    _ptr: int = 0
    _cached_ptr: int = 0
    _cached_ctx: Optional[ItemContextStruct] = None
    _callback_name = "ItemContext.UpdateItemContextPtr"

    @staticmethod
    def get_ptr() -> int:
        return ItemContext._ptr

    @staticmethod
    def _update_ptr():
        game_ctx_ptr = PyPointers.PyPointers.GetGameContextPtr()
        if game_ctx_ptr:
            ItemContext._ptr = _read_ptr_at_offset(game_ctx_ptr, GAMECONTEXT_ITEMCONTEXT_OFFSET)
        else:
            ItemContext._ptr = 0

    @staticmethod
    def enable():
        PyCallback.PyCallback.Register(
            ItemContext._callback_name,
            PyCallback.Phase.PreUpdate,
            ItemContext._update_ptr,
        )

    @staticmethod
    def disable():
        PyCallback.PyCallback.RemoveByName(ItemContext._callback_name)
        ItemContext._ptr = 0
        ItemContext._cached_ptr = 0
        ItemContext._cached_ctx = None

    @staticmethod
    def get_context() -> Optional[ItemContextStruct]:
        ptr = ItemContext._ptr
        if not ptr:
            ItemContext._cached_ptr = 0
            ItemContext._cached_ctx = None
            return None

        if ptr != ItemContext._cached_ptr:
            ItemContext._cached_ptr = ptr
            ItemContext._cached_ctx = cast(
                ptr,
                POINTER(ItemContextStruct)
            ).contents

        return ItemContext._cached_ctx


class Inventory:
    _ptr: int = 0
    _cached_ptr: int = 0
    _cached_ctx: Optional[InventoryStruct] = None
    _callback_name = "InventoryContext.UpdateInventoryPtr"

    @staticmethod
    def get_ptr() -> int:
        return Inventory._ptr

    @staticmethod
    def _update_ptr():
        game_ctx_ptr = PyPointers.PyPointers.GetGameContextPtr()
        if game_ctx_ptr:
            item_ctx_ptr = _read_ptr_at_offset(game_ctx_ptr, GAMECONTEXT_ITEMCONTEXT_OFFSET)
            if item_ctx_ptr:
                Inventory._ptr = _read_ptr_at_offset(item_ctx_ptr, ITEMCONTEXT_INVENTORY_OFFSET)
            else:
                Inventory._ptr = 0
        else:
            Inventory._ptr = 0

    @staticmethod
    def enable():
        PyCallback.PyCallback.Register(
            Inventory._callback_name,
            PyCallback.Phase.PreUpdate,
            Inventory._update_ptr,
        )

    @staticmethod
    def disable():
        PyCallback.PyCallback.RemoveByName(Inventory._callback_name)
        Inventory._ptr = 0
        Inventory._cached_ptr = 0
        Inventory._cached_ctx = None

    @staticmethod
    def get_context() -> Optional[InventoryStruct]:
        ptr = Inventory._ptr
        if not ptr:
            Inventory._cached_ptr = 0
            Inventory._cached_ctx = None
            return None

        if ptr != Inventory._cached_ptr:
            Inventory._cached_ptr = ptr
            Inventory._cached_ctx = cast(
                ptr,
                POINTER(InventoryStruct)
            ).contents

        return Inventory._cached_ctx


# Enable both contexts on import
Inventory.enable()
ItemContext.enable()

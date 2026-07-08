import Py4GW
from Py4GWCoreLib import Inventory, Item, ItemArray, Party, Player, PyImGui
from Py4GWCoreLib.enums_src.Item_enums import (
    ARMOR_INSIGNIA_UPGRADE_SLOT,
    ARMOR_RUNE_UPGRADE_SLOT,
    EQUIPPED_WEAPON_SLOTS,
    INVENTORY_BAGS,
    RUNE_MOD_ITEM_TYPE,
    WEAPON_PREFIX_NAME_MARKERS,
    WEAPON_SUFFIX_NAME_MARKERS,
    WEAPON_UPGRADE_CLASSIFICATION_SLOT,
    WEAPON_UPGRADE_REQUEST_SLOTS,
)


MODULE_NAME = "Inventory Weapon Upgrader"
MODULE_ICON = "Textures/Module_Icons/Inventory.png"

_selected_weapon_index = 0
_selected_upgrade_index = 0
_last_status = "Ready."
_item_name_cache = {}
_item_name_requested = set()


def _log_status(message, message_type):
    global _last_status
    _last_status = message
    Py4GW.Console.Log(MODULE_NAME, message, message_type)


def _inventory_bag_ids():
    return [int(getattr(bag, "value", bag)) for bag in INVENTORY_BAGS]


def _safe_item_name(item_id):
    item_id = int(item_id or 0)
    if item_id in _item_name_cache:
        return _item_name_cache[item_id]

    try:
        if Item.IsNameReady(item_id):
            name = Item.GetName(item_id)
            if name and name not in ("Unknown", "Timeout"):
                _item_name_cache[item_id] = name
                _item_name_requested.discard(item_id)
                return name
    except Exception:
        pass

    if item_id not in _item_name_requested:
        try:
            Item.RequestName(item_id)
            _item_name_requested.add(item_id)
        except Exception:
            pass
    return f"item {item_id}"


def _get_inventory_items():
    try:
        bags = ItemArray.CreateBagList(*_inventory_bag_ids())
        return [int(item_id) for item_id in ItemArray.GetItemArray(bags)]
    except Exception:
        return []


def _is_weapon_item(item_id):
    try:
        return bool(Item.IsWeapon(item_id))
    except Exception:
        return False


def _is_inscription_item(item_id):
    try:
        if bool(Item.Customization.IsInscription(item_id)):
            return True
    except Exception:
        pass
    return _is_inscription_display_name(item_id)


def _is_inscription_display_name(item_id):
    name = _safe_item_name(item_id).strip().lower()
    return name.startswith("inscription:")


def _normalized_item_name(item_id):
    return _safe_item_name(item_id).strip().lower()


def _is_armor_upgrade_display_name(item_id):
    name = _normalized_item_name(item_id)
    return "insignia" in name or "rune" in name


def _classify_weapon_upgrade_from_display_name(item_id):
    if _is_inscription_display_name(item_id):
        return "inscription"
    if _is_armor_upgrade_display_name(item_id):
        return "armor"

    name = _normalized_item_name(item_id)
    if any(marker in name for marker in WEAPON_PREFIX_NAME_MARKERS):
        return "prefix"
    if any(marker in name for marker in WEAPON_SUFFIX_NAME_MARKERS):
        return "suffix"
    if "@itemenhance" in name:
        return "weapon"
    return "unknown"


def _is_rune_mod_item(item_id):
    try:
        item_type_value, item_type_name = Item.GetItemType(item_id)
    except Exception:
        return False
    try:
        if int(item_type_value) == RUNE_MOD_ITEM_TYPE:
            return True
    except Exception:
        pass
    return str(item_type_name or "") == "Rune_Mod"


def _is_weapon_upgrade_item(item_id):
    display_kind = _classify_weapon_upgrade_from_display_name(item_id)
    if display_kind in ("prefix", "suffix", "inscription"):
        return True
    if display_kind == "armor":
        return False

    try:
        upgrade_slot = int(Inventory.GetUpgradeSlot(item_id) or 0)
        if upgrade_slot in (ARMOR_RUNE_UPGRADE_SLOT, ARMOR_INSIGNIA_UPGRADE_SLOT):
            return False
        if upgrade_slot == WEAPON_UPGRADE_CLASSIFICATION_SLOT:
            return True
    except Exception:
        pass
    if _is_inscription_item(item_id):
        return True
    return _is_rune_mod_item(item_id) and not _is_armor_upgrade_display_name(item_id)


def _get_inventory_weapon_items():
    return [(entry["item_id"], entry["name"]) for entry in _get_inventory_weapon_target_entries()]


def _make_weapon_target_entry(item_id, name, label=None, inventory_id=0, target_agent_id=0, source="inventory"):
    return {
        "item_id": int(item_id or 0),
        "name": str(name or ""),
        "label": str(label or name or f"item {int(item_id or 0)}"),
        "inventory_id": int(inventory_id or 0),
        "target_agent_id": int(target_agent_id or 0),
        "source": str(source or ""),
    }


def _get_inventory_weapon_target_entries():
    weapons = []
    target_agent_id, inventory_id = _get_player_inventory_context()
    for item_id in _get_inventory_items():
        if not _is_weapon_item(item_id):
            continue
        name = _safe_item_name(item_id)
        weapons.append(_make_weapon_target_entry(
            item_id,
            name,
            inventory_id=inventory_id,
            target_agent_id=target_agent_id,
            source="inventory",
        ))
    return weapons


def _get_party_weapon_target_agents():
    agents = []
    seen_agent_ids = set()

    try:
        player_agent_id = int(Player.GetAgentID() or 0)
    except Exception:
        player_agent_id = 0
    if player_agent_id:
        agents.append((player_agent_id, "Player"))
        seen_agent_ids.add(player_agent_id)

    try:
        heroes = list(Party.GetHeroes() or [])
    except Exception:
        heroes = []

    for hero_index, hero in enumerate(heroes, start=1):
        try:
            agent_id = int(getattr(hero, "agent_id", 0) or 0)
        except Exception:
            agent_id = 0
        if not agent_id or agent_id in seen_agent_ids:
            continue

        try:
            name = Party.Heroes.GetNameByAgentID(agent_id) or ""
        except Exception:
            name = ""
        if not name:
            name = f"Hero {hero_index}"

        agents.append((agent_id, name))
        seen_agent_ids.add(agent_id)

    return agents


def _get_equipped_weapon_target_entries():
    weapons = []
    for agent_id, agent_label in _get_party_weapon_target_agents():
        try:
            inventory_id = int(Inventory.GetInventoryIDFromAgent(agent_id) or 0)
        except Exception:
            inventory_id = 0
        if not inventory_id:
            continue

        for slot_label, equip_slot in EQUIPPED_WEAPON_SLOTS:
            try:
                item_id = int(Inventory.GetEquippedItemID(inventory_id, equip_slot) or 0)
            except Exception:
                item_id = 0
            if not item_id or not _is_weapon_item(item_id):
                continue

            name = _safe_item_name(item_id)
            weapons.append(_make_weapon_target_entry(
                item_id,
                name,
                label=f"{agent_label} {slot_label}: {name}",
                inventory_id=inventory_id,
                target_agent_id=agent_id,
                source=f"equipped:{slot_label}",
            ))

    return weapons


def _get_weapon_target_entries():
    return _get_inventory_weapon_target_entries() + _get_equipped_weapon_target_entries()


def _get_inventory_weapon_upgrade_items():
    upgrades = []
    for item_id in _get_inventory_items():
        if not _is_weapon_upgrade_item(item_id):
            continue
        upgrades.append((item_id, _safe_item_name(item_id)))
    return upgrades


def _clamp_selected_indexes(weapons, upgrades):
    global _selected_weapon_index, _selected_upgrade_index
    if weapons:
        _selected_weapon_index = max(0, min(_selected_weapon_index, len(weapons) - 1))
    else:
        _selected_weapon_index = 0
    if upgrades:
        _selected_upgrade_index = max(0, min(_selected_upgrade_index, len(upgrades) - 1))
    else:
        _selected_upgrade_index = 0


def _classify_weapon_upgrade(item_id):
    display_kind = _classify_weapon_upgrade_from_display_name(item_id)
    if display_kind in ("prefix", "suffix", "inscription"):
        return display_kind
    if _is_inscription_item(item_id):
        return "inscription"
    try:
        if int(Inventory.GetUpgradeSlot(item_id) or 0) == WEAPON_UPGRADE_CLASSIFICATION_SLOT:
            return "weapon"
    except Exception:
        pass
    return "unknown"


def _get_confirmed_weapon_request_slot(upgrade_item_id):
    upgrade_kind = _classify_weapon_upgrade(upgrade_item_id)
    return WEAPON_UPGRADE_REQUEST_SLOTS.get(upgrade_kind)


def _get_player_inventory_context():
    try:
        target_agent_id = int(Player.GetAgentID() or 0)
    except Exception:
        target_agent_id = 0
    try:
        inventory_id = int(Inventory.GetInventoryIDFromAgent(target_agent_id) or 0) if target_agent_id else 0
    except Exception:
        inventory_id = 0
    return target_agent_id, inventory_id


def _get_weapon_target_context(target_context=None):
    if isinstance(target_context, dict):
        try:
            target_agent_id = int(target_context.get("target_agent_id", 0) or 0)
        except Exception:
            target_agent_id = 0
        try:
            inventory_id = int(target_context.get("inventory_id", 0) or 0)
        except Exception:
            inventory_id = 0
        return target_agent_id, inventory_id
    return _get_player_inventory_context()


def _resolve_weapon_upgrade_application(target_weapon_id, upgrade_item_id, target_context=None):
    try:
        target_weapon_id = int(target_weapon_id or 0)
        upgrade_item_id = int(upgrade_item_id or 0)
    except Exception:
        return False, "target_item=0, upgrade_item=0", None

    if not target_weapon_id:
        return False, f"target_item={target_weapon_id}, upgrade_item={upgrade_item_id}", None
    if not upgrade_item_id:
        return False, f"target_item={target_weapon_id}, upgrade_item=0", None
    if target_weapon_id == upgrade_item_id:
        return False, f"target_item={target_weapon_id}, upgrade_item={upgrade_item_id}", None
    if not _is_weapon_item(target_weapon_id):
        return False, f"target_item={target_weapon_id}, upgrade_item={upgrade_item_id}, target_weapon=0", None
    if not _is_weapon_upgrade_item(upgrade_item_id):
        return False, f"target_item={target_weapon_id}, upgrade_item={upgrade_item_id}, weapon_upgrade=0", None

    validate_ok = bool(Inventory.ValidateUpgrade(target_weapon_id, upgrade_item_id))
    if not validate_ok:
        return False, f"target_item={target_weapon_id}, upgrade_item={upgrade_item_id}, validate=0", None

    request_slot = _get_confirmed_weapon_request_slot(upgrade_item_id)
    if request_slot is None:
        return (
            False,
            f"target_item={target_weapon_id}, upgrade_item={upgrade_item_id}, validate=1, request_slot=unconfirmed",
            None,
        )

    target_agent_id, inventory_id = _get_weapon_target_context(target_context)
    if not target_agent_id or not inventory_id:
        return (
            False,
            (
                f"target_item={target_weapon_id}, upgrade_item={upgrade_item_id}, validate=1, "
                f"request_slot={int(request_slot)}, target_agent_id={target_agent_id}, inventory_id={inventory_id}"
            ),
            None,
        )

    request = {
        "inventory_id": inventory_id,
        "target_item_id": target_weapon_id,
        "upgrade_item_id": upgrade_item_id,
        "upgrade_slot": int(request_slot),
        "target_agent_id": target_agent_id,
    }
    return (
        True,
        (
            f"target_item={target_weapon_id}, upgrade_item={upgrade_item_id}, validate=1, "
            f"request_slot={int(request_slot)}, target_agent_id={target_agent_id}, inventory_id={inventory_id}"
        ),
        request,
    )


def _apply_selected_weapon_upgrade():
    weapons = _get_weapon_target_entries()
    upgrades = _get_inventory_weapon_upgrade_items()
    _clamp_selected_indexes(weapons, upgrades)

    if not weapons:
        _log_status("No weapon found in inventory bags or equipped by party.", Py4GW.Console.MessageType.Warning)
        return False
    if not upgrades:
        _log_status("No weapon upgrade component found in inventory bags.", Py4GW.Console.MessageType.Warning)
        return False

    target_weapon = weapons[_selected_weapon_index]
    target_weapon_id = int(target_weapon["item_id"])
    target_weapon_name = str(target_weapon["label"])
    upgrade_item_id, upgrade_name = upgrades[_selected_upgrade_index]
    ok, diagnostic, request = _resolve_weapon_upgrade_application(target_weapon_id, upgrade_item_id, target_weapon)
    if not ok or request is None:
        if "request_slot=unconfirmed" in diagnostic:
            _log_status(
                f"Unsupported weapon upgrade type for {upgrade_name} on {target_weapon_name} ({diagnostic}).",
                Py4GW.Console.MessageType.Warning,
            )
        else:
            _log_status(
                f"Native validation refused {upgrade_name} on {target_weapon_name} ({diagnostic}).",
                Py4GW.Console.MessageType.Warning,
            )
        return False

    sent = bool(Inventory.ApplyUpgrade(
        request["inventory_id"],
        request["target_item_id"],
        request["upgrade_item_id"],
        request["upgrade_slot"],
        request["target_agent_id"],
    ))
    if not sent:
        _log_status(
            f"Native upgrade order refused for {upgrade_name} on {target_weapon_name} ({diagnostic}).",
            Py4GW.Console.MessageType.Error,
        )
        return False

    _log_status(
        f"Native upgrade order sent for {upgrade_name} on {target_weapon_name} ({diagnostic}).",
        Py4GW.Console.MessageType.Info,
    )
    return True


def main():
    global _selected_weapon_index, _selected_upgrade_index

    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        weapons = _get_weapon_target_entries()
        upgrades = _get_inventory_weapon_upgrade_items()
        _clamp_selected_indexes(weapons, upgrades)

        if weapons:
            weapon_labels = [f"{entry['label']} ({entry['item_id']})" for entry in weapons]
            _selected_weapon_index = PyImGui.combo("Weapon", _selected_weapon_index, weapon_labels)
        else:
            PyImGui.text("No weapon found in inventory bags or equipped by party.")

        if upgrades:
            upgrade_labels = [f"{name} ({item_id})" for item_id, name in upgrades]
            _selected_upgrade_index = PyImGui.combo("Upgrade", _selected_upgrade_index, upgrade_labels)
        else:
            PyImGui.text("No weapon upgrade component found in inventory bags.")

        if PyImGui.button("Apply upgrade", width=180, height=26):
            _apply_selected_weapon_upgrade()

        PyImGui.text_wrapped(_last_status)

    PyImGui.end()


if __name__ == "__main__":
    main()

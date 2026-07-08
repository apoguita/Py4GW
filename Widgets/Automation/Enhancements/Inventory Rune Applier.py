import Py4GW
from Py4GWCoreLib import Inventory, Item, ItemArray, Party, Player, PyImGui
from Py4GWCoreLib.enums_src.Item_enums import (
    ARMOR_EQUIPMENT_SLOTS,
    ARMOR_INSIGNIA_UPGRADE_SLOT,
    ARMOR_UPGRADE_SLOTS,
    INVENTORY_BAGS,
)


MODULE_NAME = "Inventory Armor Upgrader"
MODULE_ICON = "Textures/Module_Icons/Inventory.png"

_selected_rune_index = 0
_selected_armor_slot_index = 0
_selected_target_agent_index = 0
_target_agent_options = []
_last_status = "Ready."
_rune_name_cache = {}
_rune_name_requested = set()


def _log_status(message, message_type):
    global _last_status
    _last_status = message
    Py4GW.Console.Log(MODULE_NAME, message, message_type)


def _inventory_bag_ids():
    return [int(getattr(bag, "value", bag)) for bag in INVENTORY_BAGS]


def _safe_item_name(item_id):
    if item_id in _rune_name_cache:
        return _rune_name_cache[item_id]

    try:
        if Item.IsNameReady(item_id):
            name = Item.GetName(item_id)
            if name and name not in ("Unknown", "Timeout"):
                _rune_name_cache[item_id] = name
                _rune_name_requested.discard(item_id)
                return name
    except Exception:
        pass

    if item_id not in _rune_name_requested:
        try:
            Item.RequestName(item_id)
            _rune_name_requested.add(item_id)
        except Exception:
            pass
    return f"item {item_id}"


def _get_inventory_upgrade_items():
    upgrades = []
    bags = ItemArray.CreateBagList(*_inventory_bag_ids())
    for item_id in ItemArray.GetItemArray(bags):
        try:
            if int(Inventory.GetUpgradeSlot(item_id)) not in ARMOR_UPGRADE_SLOTS:
                continue
        except Exception:
            continue
        upgrades.append((int(item_id), _safe_item_name(int(item_id))))
    return upgrades


def _get_target_agent_id(options=None):
    if options is None:
        options = _target_agent_options or _get_target_agent_options()
    if not options:
        return 0

    index = max(0, min(_selected_target_agent_index, len(options) - 1))
    return int(options[index][0] or 0)


def _get_target_agent_options():
    options = []
    seen_agent_ids = set()

    try:
        player_agent_id = int(Player.GetAgentID() or 0)
    except Exception:
        player_agent_id = 0
    if player_agent_id:
        options.append((player_agent_id, f"Player ({player_agent_id})"))
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

        options.append((agent_id, f"{name} ({agent_id})"))
        seen_agent_ids.add(agent_id)

    return options


def _clamp_selected_indexes(runes, target_options=None):
    global _selected_rune_index, _selected_armor_slot_index, _selected_target_agent_index
    if runes:
        _selected_rune_index = max(0, min(_selected_rune_index, len(runes) - 1))
    else:
        _selected_rune_index = 0
    _selected_armor_slot_index = max(0, min(_selected_armor_slot_index, len(ARMOR_EQUIPMENT_SLOTS) - 1))
    if target_options:
        _selected_target_agent_index = max(0, min(_selected_target_agent_index, len(target_options) - 1))
    else:
        _selected_target_agent_index = 0


def _get_upgrade_request_slot(item_upgrade_slot):
    if item_upgrade_slot == ARMOR_INSIGNIA_UPGRADE_SLOT:
        return 0
    return item_upgrade_slot


def _resolve_upgrade_application(agent_id, equip_slot, upgrade_item_id):
    inventory_id = int(Inventory.GetInventoryIDFromAgent(agent_id) or 0)
    if not inventory_id:
        return False, "inventory_id=0", None

    target_item_id = int(Inventory.GetEquippedItemID(inventory_id, equip_slot) or 0)
    if not target_item_id:
        return False, f"inventory_id={inventory_id}, target_item=0", None
    if target_item_id == int(upgrade_item_id):
        return False, f"inventory_id={inventory_id}, target_item={target_item_id}, upgrade_item={int(upgrade_item_id)}", None

    upgrade_slot = int(Inventory.GetUpgradeSlot(upgrade_item_id) or 0)
    if upgrade_slot not in ARMOR_UPGRADE_SLOTS:
        return False, f"inventory_id={inventory_id}, target_item={target_item_id}, upgrade_item={int(upgrade_item_id)}, upgrade_slot={upgrade_slot}", None
    request_upgrade_slot = _get_upgrade_request_slot(upgrade_slot)

    validate_ok = bool(Inventory.ValidateUpgrade(target_item_id, upgrade_item_id))
    if not validate_ok:
        return False, f"inventory_id={inventory_id}, target_item={target_item_id}, upgrade_item={int(upgrade_item_id)}, validate=0", None

    request = {
        "inventory_id": inventory_id,
        "target_item_id": target_item_id,
        "upgrade_slot": request_upgrade_slot,
    }
    diagnostic = f"inventory_id={inventory_id}, target_item={target_item_id}, upgrade_item={int(upgrade_item_id)}, upgrade_slot={request_upgrade_slot}"
    if request_upgrade_slot != upgrade_slot:
        diagnostic = f"{diagnostic}, item_upgrade_slot={upgrade_slot}"
    return True, diagnostic, request


def _apply_selected_upgrade():
    upgrades = _get_inventory_upgrade_items()
    target_options = _get_target_agent_options()
    _clamp_selected_indexes(upgrades, target_options)
    if not upgrades:
        _log_status("No applicable armor upgrade found in inventory.", Py4GW.Console.MessageType.Warning)
        return False

    agent_id = _get_target_agent_id(target_options)
    if not agent_id:
        _log_status("No target agent available.", Py4GW.Console.MessageType.Warning)
        return False

    upgrade_item_id, upgrade_name = upgrades[_selected_rune_index]
    armor_label, equip_slot = ARMOR_EQUIPMENT_SLOTS[_selected_armor_slot_index]
    try:
        request_ok, diagnostic, request = _resolve_upgrade_application(agent_id, equip_slot, upgrade_item_id)
        applied = bool(request_ok and request and Inventory.ApplyUpgrade(
            request["inventory_id"],
            request["target_item_id"],
            upgrade_item_id,
            request["upgrade_slot"],
            agent_id,
        ))
    except Exception as exception:
        _log_status(f"Upgrade application error: {exception}", Py4GW.Console.MessageType.Error)
        return False

    if applied:
        _log_status(
            f"Application request sent for {upgrade_name} on {armor_label} (agent {agent_id}; {diagnostic}).",
            Py4GW.Console.MessageType.Info,
        )
        return True

    _log_status(
        f"Native application refused for {upgrade_name} on {armor_label} (agent {agent_id}; {diagnostic}).",
        Py4GW.Console.MessageType.Warning,
    )
    return False


def _safe_apply_selected_upgrade():
    try:
        return _apply_selected_upgrade()
    except Exception as exception:
        _log_status(f"Upgrade widget error: {exception}", Py4GW.Console.MessageType.Error)
        return False


def main():
    global _selected_rune_index, _selected_armor_slot_index, _selected_target_agent_index, _target_agent_options

    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        upgrades = _get_inventory_upgrade_items()
        _target_agent_options = _get_target_agent_options()
        _clamp_selected_indexes(upgrades, _target_agent_options)

        if _target_agent_options:
            target_labels = [label for _, label in _target_agent_options]
            _selected_target_agent_index = PyImGui.combo("Target", _selected_target_agent_index, target_labels)
        else:
            PyImGui.text("No player or hero available.")

        if upgrades:
            upgrade_labels = [f"{name} ({item_id})" for item_id, name in upgrades]
            _selected_rune_index = PyImGui.combo("Upgrade", _selected_rune_index, upgrade_labels)
        else:
            PyImGui.text("No applicable armor upgrade in bags.")

        armor_labels = [label for label, _ in ARMOR_EQUIPMENT_SLOTS]
        _selected_armor_slot_index = PyImGui.combo("Armor piece", _selected_armor_slot_index, armor_labels)

        target_agent_id = _get_target_agent_id()
        PyImGui.text(f"Target agent: {target_agent_id or 'none'}")

        if PyImGui.button("Apply upgrade", width=180, height=28):
            _safe_apply_selected_upgrade()

        PyImGui.text(_last_status)

    PyImGui.end()

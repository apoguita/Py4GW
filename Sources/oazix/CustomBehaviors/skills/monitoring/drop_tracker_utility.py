import datetime
import re

from Py4GWCoreLib import GLOBAL_CACHE, Item, ItemArray, Party, Player, Py4GW, Routines
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.enums import SharedCommandType
from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers_party import CustomBehaviorHelperParty


class DropTrackerSender:
    """
    Non-blocking shared-memory drop sender.
    Runs from daemon() and never participates in utility score arbitration.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DropTrackerSender, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.inventory_poll_timer = ThrottledTimer(500)
        self.last_inventory_snapshot: dict[int, tuple[str, str, int]] = {}
        self.enabled = True
        self.gold_regex = re.compile(r"^(?:\[([\d: ]+[ap]m)\] )?Your party shares ([\d,]+) gold\.$")
        self.warn_timer = ThrottledTimer(3000)
        self.debug_timer = ThrottledTimer(5000)
        self.snapshot_error_timer = ThrottledTimer(5000)
        self.debug_enabled = True
        self.last_snapshot_total = 0
        self.last_snapshot_ready = 0
        self.last_snapshot_not_ready = 0
        self.last_sent_count = 0
        self.is_warmed_up = False
        self.stable_snapshot_count = 0
        self.pending_slot_deltas: dict[tuple[int, int], int] = {}
        self.outbox_queue: list[tuple[str, int, str, str]] = []
        self.max_send_per_tick = 6

    def _reset_tracking_state(self):
        self.last_inventory_snapshot = {}
        self.pending_slot_deltas = {}
        self.outbox_queue = []
        self.last_sent_count = 0
        self.is_warmed_up = False
        self.stable_snapshot_count = 0

    def _strip_tags(self, text: str) -> str:
        return re.sub(r"<[^>]+>", "", text or "")

    def _resolve_party_leader_email(self) -> str | None:
        try:
            helper_leader_email = CustomBehaviorHelperParty._get_party_leader_email()
            if helper_leader_email:
                return helper_leader_email

            leader_id = Party.GetPartyLeaderID()
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                if int(account.AgentData.AgentID) == leader_id:
                    return account.AccountEmail

            # Fallback to leader slot in same party/map shard.
            my_party_id = GLOBAL_CACHE.Party.GetPartyID()
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                if not account.IsAccount:
                    continue
                if int(account.AgentPartyData.PartyID) != int(my_party_id):
                    continue
                if int(account.AgentPartyData.PartyPosition) == 0:
                    return account.AccountEmail
        except Exception:
            return None
        return None

    def _send_drop(self, item_name: str, quantity: int, rarity: str, display_time: str = "") -> bool:
        try:
            my_email = Player.GetAccountEmail()
            if not my_email:
                return False
            receiver_email = self._resolve_party_leader_email() or my_email
            sent_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email=my_email,
                receiver_email=receiver_email,
                command=SharedCommandType.CustomBehaviors,
                params=(float(max(1, quantity)), 0.0, 0.0, 0.0),
                ExtraData=(
                    "TrackerDrop",
                    (item_name or "Unknown Item")[:31],
                    (rarity or "Unknown")[:31],
                    (display_time or "")[:31],
                ),
            )
            if sent_index == -1 and self.warn_timer.IsExpired():
                self.warn_timer.Reset()
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    f"SendMessage failed (inbox full?): sender={my_email}, receiver={receiver_email}, item={item_name}",
                    Py4GW.Console.MessageType.Warning,
                )
            return sent_index != -1
        except Exception:
            return False

    def _queue_drop(self, item_name: str, quantity: int, rarity: str, display_time: str):
        self.outbox_queue.append((item_name, max(1, int(quantity)), rarity or "Unknown", display_time or ""))

    def _flush_outbox(self) -> int:
        sent = 0
        while self.outbox_queue and sent < self.max_send_per_tick:
            item_name, quantity, rarity, display_time = self.outbox_queue[0]
            if not self._send_drop(item_name, quantity, rarity, display_time):
                break
            self.outbox_queue.pop(0)
            sent += 1
        return sent

    def _take_inventory_snapshot(self) -> dict[tuple[int, int], tuple[str, str, int, int]]:
        # key: (bag_id, slot_id)
        # value: (name, rarity, qty, model_id)
        snapshot: dict[tuple[int, int], tuple[str, str, int, int]] = {}
        try:
            # Player inventory only (avoid storage/material tabs).
            bag_ids = (1, 2, 3, 4)
            bags = ItemArray.CreateBagList(*bag_ids)
            item_ids = ItemArray.GetItemArray(bags)
            self.last_snapshot_total = len(item_ids)
            ready_count = 0
            not_ready_count = 0
            for bag_id in bag_ids:
                bag_items = ItemArray.GetItemArray(ItemArray.CreateBagList(bag_id))
                for item_id in bag_items:
                    item_instance = Item.item_instance(item_id)
                    if item_instance:
                        slot_id = int(item_instance.slot)
                        model_id = int(item_instance.model_id)
                        rarity = item_instance.rarity.name if getattr(item_instance, "rarity", None) else "Unknown"
                        qty = int(item_instance.quantity) if getattr(item_instance, "quantity", None) is not None else 1
                    else:
                        slot_id = int(Item.GetSlot(item_id))
                        model_id = int(Item.GetModelID(item_id))
                        rarity = Item.Rarity.GetRarity(item_id)[1]
                        qty = Item.Properties.GetQuantity(item_id)
                        qty = max(1, int(qty) if qty is not None else 1)

                    is_name_ready = Item.IsNameReady(item_id)
                    raw_name = ""
                    if is_name_ready:
                        raw_name = Item.GetName(item_id) or ""
                        ready_count += 1
                    else:
                        not_ready_count += 1
                        try:
                            Item.RequestName(item_id)
                        except Exception:
                            pass

                    clean_name = self._strip_tags(raw_name).strip() if raw_name else ""
                    clean_name = re.sub(r"^[\d,]+\s+", "", clean_name) if clean_name else ""
                    if not clean_name:
                        # Keep deterministic placeholder; never emit this as a drop.
                        clean_name = f"Model#{model_id}"

                    if Item.Type.IsTome(item_id):
                        rarity = "Tomes"
                    elif "Dye" in clean_name or "Vial of Dye" in clean_name:
                        rarity = "Dyes"
                    elif "Key" in clean_name:
                        rarity = "Keys"
                    elif Item.Type.IsMaterial(item_id) or Item.Type.IsRareMaterial(item_id):
                        rarity = "Material"
                    snapshot[(bag_id, slot_id)] = (clean_name, rarity, qty, model_id)

            self.last_snapshot_ready = ready_count
            self.last_snapshot_not_ready = not_ready_count
        except Exception:
            if self.snapshot_error_timer.IsExpired():
                self.snapshot_error_timer.Reset()
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    "Inventory snapshot failed.",
                    Py4GW.Console.MessageType.Warning,
                )
            return snapshot
        return snapshot

    def _process_inventory_deltas(self):
        current_snapshot = self._take_inventory_snapshot()

        # Guard against transient invalid snapshots (observed: ready=0/not_ready=N spikes).
        if self.last_snapshot_total > 0 and self.last_snapshot_ready == 0:
            self.last_sent_count = 0
            return

        if not current_snapshot:
            self.last_sent_count = 0
            return

        # Warm-up baseline to avoid counting existing inventory as drops.
        readiness = (float(self.last_snapshot_ready) / float(self.last_snapshot_total)) if self.last_snapshot_total else 0.0
        if not self.is_warmed_up:
            if readiness >= 0.7:
                self.stable_snapshot_count += 1
            else:
                self.stable_snapshot_count = 0
            self.last_inventory_snapshot = current_snapshot
            self.last_sent_count = 0
            if self.stable_snapshot_count >= 2:
                self.is_warmed_up = True
            return

        # Guard against mass-delta churn due slot/index instability or inventory refresh.
        if abs(len(current_snapshot) - len(self.last_inventory_snapshot)) > 12:
            self._reset_tracking_state()
            self.last_inventory_snapshot = current_snapshot
            self.is_warmed_up = True
            return

        time_str = datetime.datetime.now().strftime("%I:%M %p")
        candidate_events: list[tuple[str, int, str]] = []
        live_slots = set()
        for slot_key, (name, rarity, qty, _model_id) in current_snapshot.items():
            live_slots.add(slot_key)
            previous = self.last_inventory_snapshot.get(slot_key)
            is_unknown_name = name.startswith("Model#")
            if previous is None:
                if is_unknown_name:
                    prev_qty = self.pending_slot_deltas.get(slot_key, 0)
                    self.pending_slot_deltas[slot_key] = prev_qty + qty
                else:
                    candidate_events.append((name, qty, rarity))
                continue
            prev_qty = previous[2]
            if qty > prev_qty:
                delta = qty - prev_qty
                if is_unknown_name:
                    prev_pending = self.pending_slot_deltas.get(slot_key, 0)
                    self.pending_slot_deltas[slot_key] = prev_pending + delta
                else:
                    candidate_events.append((name, delta, rarity))

            # If an item name became ready after we buffered its delta, flush now.
            if not is_unknown_name and slot_key in self.pending_slot_deltas:
                pending_qty = self.pending_slot_deltas.pop(slot_key)
                if pending_qty > 0:
                    # Use current resolved rarity, not stale buffered rarity.
                    candidate_events.append((name, pending_qty, rarity))

        # Drop stale pending slots (item moved/consumed before name became ready).
        stale_slots = [slot_key for slot_key in self.pending_slot_deltas.keys() if slot_key not in live_slots]
        for slot_key in stale_slots:
            self.pending_slot_deltas.pop(slot_key, None)

        # Suppress only extreme churn bursts (inventory refresh), not normal multi-loot bursts.
        if len(candidate_events) > 30:
            self.last_inventory_snapshot = current_snapshot
            self.last_sent_count = 0
            return

        enqueued_count = 0
        for name, qty, rarity in candidate_events:
            self._queue_drop(name, qty, rarity, time_str)
            enqueued_count += 1

        sent_count = self._flush_outbox()
        self.last_inventory_snapshot = current_snapshot
        self.last_sent_count = sent_count if enqueued_count == 0 else min(enqueued_count, sent_count)

    def act(self):
        if not self.enabled:
            return
        try:
            if not Routines.Checks.Map.MapValid():
                self._reset_tracking_state()
                return
            if self.debug_enabled and self.debug_timer.IsExpired():
                self.debug_timer.Reset()
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    (
                        "active "
                        f"snapshot_size={len(self.last_inventory_snapshot)} "
                        f"items={self.last_snapshot_total} "
                        f"ready={self.last_snapshot_ready} "
                        f"not_ready={self.last_snapshot_not_ready} "
                        f"sent={self.last_sent_count} "
                        f"queued={len(self.outbox_queue)} "
                        f"pending_names={len(self.pending_slot_deltas)} "
                        f"warmed={self.is_warmed_up}"
                    ),
                    Py4GW.Console.MessageType.Info,
                )
            if self.inventory_poll_timer.IsExpired():
                self.inventory_poll_timer.Reset()
                self._process_inventory_deltas()
            if self.outbox_queue:
                self._flush_outbox()
        except Exception:
            return

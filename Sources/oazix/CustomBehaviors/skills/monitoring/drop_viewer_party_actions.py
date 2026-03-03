import sys

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _viewer_runtime_module(viewer):
    try:
        return sys.modules.get(viewer.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _bind_impl(viewer, export_name: str):
    module = _viewer_runtime_module(viewer)
    if module is None:
        raise RuntimeError("viewer runtime module unavailable")
    impl_name = f"_drop_viewer_party_actions_impl_{export_name}"
    if hasattr(module, impl_name):
        return getattr(module, impl_name)
    source = _SOURCES[export_name]
    exec(source, module.__dict__, module.__dict__)
    return getattr(module, impl_name)


_SOURCES = {
    'broadcast_inventory_action_to_followers': 'def _drop_viewer_party_actions_impl_broadcast_inventory_action_to_followers(viewer, action_code: str, action_payload: str = ""):\n    sent = 0\n    try:\n        sender_email = viewer._ensure_text(Player.GetAccountEmail()).strip()\n        if not sender_email:\n            return 0\n\n        shmem = getattr(GLOBAL_CACHE, "ShMem", None)\n        if shmem is None:\n            return 0\n\n        self_account = shmem.GetAccountDataFromEmail(sender_email)\n        if self_account is None:\n            return 0\n\n        self_party_id = int(getattr(self_account.AgentPartyData, "PartyID", 0))\n        self_map_id = int(getattr(self_account.AgentData.Map, "MapID", 0))\n        if self_party_id <= 0 or self_map_id <= 0:\n            return 0\n\n        for account in shmem.GetAllAccountData():\n            target_email = viewer._ensure_text(getattr(account, "AccountEmail", "")).strip()\n            if not target_email or target_email == sender_email:\n                continue\n            if not bool(getattr(account, "IsAccount", False)):\n                continue\n\n            target_party_id = int(getattr(account.AgentPartyData, "PartyID", 0))\n            target_map_id = int(getattr(account.AgentData.Map, "MapID", 0))\n            if target_party_id != self_party_id or target_map_id != self_map_id:\n                continue\n\n            sent_index = shmem.SendMessage(\n                sender_email=sender_email,\n                receiver_email=target_email,\n                command=SharedCommandType.CustomBehaviors,\n                params=(0.0, 0.0, 0.0, 0.0),\n                ExtraData=(viewer.inventory_action_tag, action_code[:31], action_payload[:31], ""),\n            )\n            if sent_index != -1:\n                sent += 1\n    except EXPECTED_RUNTIME_ERRORS as e:\n        Py4GW.Console.Log("DropViewer", f"Inventory action broadcast failed: {e}", Py4GW.Console.MessageType.Warning)\n    return sent',
    'trigger_inventory_action': 'def _drop_viewer_party_actions_impl_trigger_inventory_action(viewer, action_code: str, action_payload: str = ""):\n    viewer._run_inventory_action(action_code, action_payload)\n    try:\n        if Player.GetAgentID() != Party.GetPartyLeaderID():\n            return\n    except EXPECTED_RUNTIME_ERRORS:\n        return\n\n    sent = viewer._broadcast_inventory_action_to_followers(action_code, action_payload)\n    if sent > 0:\n        viewer.set_status(f"{viewer.status_message} | Sent to {sent} follower(s)")',
    'sync_auto_inventory_config_to_followers': 'def _drop_viewer_party_actions_impl_sync_auto_inventory_config_to_followers(viewer):\n    try:\n        if Player.GetAgentID() != Party.GetPartyLeaderID():\n            return 0\n    except EXPECTED_RUNTIME_ERRORS:\n        return 0\n\n    id_payload = viewer._encode_auto_action_payload(viewer.auto_id_enabled, viewer._get_selected_id_rarities())\n    salvage_payload = viewer._encode_auto_action_payload(viewer.auto_salvage_enabled, viewer._get_selected_salvage_rarities())\n    kits_payload = "1" if viewer.auto_buy_kits_enabled else "0"\n    kits_sort_payload = "1" if viewer.auto_buy_kits_sort_to_front_enabled else "0"\n    gold_payload = "1" if viewer.auto_gold_balance_enabled else "0"\n    store_payload = "1" if viewer.auto_outpost_store_enabled else "0"\n    sent = 0\n    sent += viewer._broadcast_inventory_action_to_followers("cfg_auto_id", id_payload)\n    sent += viewer._broadcast_inventory_action_to_followers("cfg_auto_salvage", salvage_payload)\n    sent += viewer._broadcast_inventory_action_to_followers("cfg_auto_buy_kits", kits_payload)\n    sent += viewer._broadcast_inventory_action_to_followers("cfg_auto_buy_kits_sort", kits_sort_payload)\n    sent += viewer._broadcast_inventory_action_to_followers("cfg_auto_gold_balance", gold_payload)\n    sent += viewer._broadcast_inventory_action_to_followers("cfg_auto_outpost_store", store_payload)\n    if sent > 0:\n        viewer.set_status(f"Auto inventory config synced to followers ({sent} messages)")\n    return sent',
    'is_leader_client': 'def _drop_viewer_party_actions_impl_is_leader_client(viewer) -> bool:\n    try:\n        return Player.GetAgentID() == Party.GetPartyLeaderID()\n    except EXPECTED_RUNTIME_ERRORS:\n        return False',
    'schedule_party_action': 'def _drop_viewer_party_actions_impl_schedule_party_action(viewer, action_gen, action_label: str) -> bool:\n    label = viewer._ensure_text(action_label).strip() or "Party action"\n    try:\n        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty\n        party_controller = CustomBehaviorParty()\n        if not party_controller.is_ready_for_action():\n            viewer.set_status(f"{label}: waiting for previous party action")\n            return False\n        accepted = bool(party_controller.schedule_action(action_gen))\n        if accepted:\n            viewer.set_status(f"{label}: started")\n            return True\n        viewer.set_status(f"{label}: busy")\n        return False\n    except EXPECTED_RUNTIME_ERRORS as e:\n        viewer.set_status(f"{label}: failed ({e})")\n        return False',
    'trigger_party_resign_to_outpost': 'def _drop_viewer_party_actions_impl_trigger_party_resign_to_outpost(viewer) -> bool:\n    if Map.IsOutpost():\n        viewer.set_status("Resign + Outpost: already in outpost")\n        return False\n    from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants\n    return viewer._schedule_party_action(\n        PartyCommandConstants.resign_and_return_to_outpost,\n        "Resign + Outpost",\n    )',
    'trigger_party_invite_all_followers': 'def _drop_viewer_party_actions_impl_trigger_party_invite_all_followers(viewer) -> bool:\n    from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants\n    return viewer._schedule_party_action(\n        PartyCommandConstants.invite_all_to_leader_party,\n        "Join Followers",\n    )',
    'get_party_chesting_enabled': 'def _drop_viewer_party_actions_impl_get_party_chesting_enabled(viewer) -> bool:\n    try:\n        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty\n        return bool(CustomBehaviorParty().get_party_is_chesting_enabled())\n    except EXPECTED_RUNTIME_ERRORS:\n        return False',
    'toggle_party_chesting': 'def _drop_viewer_party_actions_impl_toggle_party_chesting(viewer) -> bool:\n    if not viewer._is_leader_client():\n        viewer.set_status("Party chesting: leader only")\n        return False\n    try:\n        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty\n        party_controller = CustomBehaviorParty()\n        next_value = not bool(party_controller.get_party_is_chesting_enabled())\n        party_controller.set_party_is_chesting_enabled(next_value)\n        viewer.set_status(f"Party chesting: {\'ON\' if next_value else \'OFF\'}")\n        return True\n    except EXPECTED_RUNTIME_ERRORS as e:\n        viewer.set_status(f"Party chesting: failed ({e})")\n        return False',
    'trigger_party_interact_leader_target': 'def _drop_viewer_party_actions_impl_trigger_party_interact_leader_target(viewer) -> bool:\n    if not viewer._is_leader_client():\n        viewer.set_status("Interact Leader Target: leader only")\n        return False\n    try:\n        target_id = int(Player.GetTargetID())\n        if target_id <= 0:\n            from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty\n            target_id = int(CustomBehaviorParty().get_party_custom_target() or 0)\n        if target_id is None or int(target_id) <= 0:\n            viewer.set_status("Interact Leader Target: no leader target selected")\n            return False\n    except EXPECTED_RUNTIME_ERRORS:\n        viewer.set_status("Interact Leader Target: no leader target selected")\n        return False\n    from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants\n    return viewer._schedule_party_action(\n        PartyCommandConstants.interract_with_leader_selected_target,\n        "Interact Leader Target",\n    )',
}


def broadcast_inventory_action_to_followers(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'broadcast_inventory_action_to_followers')(viewer, *args, **kwargs)

def trigger_inventory_action(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'trigger_inventory_action')(viewer, *args, **kwargs)

def sync_auto_inventory_config_to_followers(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'sync_auto_inventory_config_to_followers')(viewer, *args, **kwargs)

def is_leader_client(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'is_leader_client')(viewer, *args, **kwargs)

def schedule_party_action(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'schedule_party_action')(viewer, *args, **kwargs)

def trigger_party_resign_to_outpost(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'trigger_party_resign_to_outpost')(viewer, *args, **kwargs)

def trigger_party_invite_all_followers(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'trigger_party_invite_all_followers')(viewer, *args, **kwargs)

def get_party_chesting_enabled(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'get_party_chesting_enabled')(viewer, *args, **kwargs)

def toggle_party_chesting(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'toggle_party_chesting')(viewer, *args, **kwargs)

def trigger_party_interact_leader_target(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'trigger_party_interact_leader_target')(viewer, *args, **kwargs)

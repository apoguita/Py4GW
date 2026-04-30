"""
Reusable Botting interaction and targeting state helpers.

Adapters provide selector callbacks; this module owns the runtime interaction
work against Botting, agents, items, dialogs, and shared command dispatch.
"""
from __future__ import annotations

from time import monotonic
from typing import Callable, Iterable

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_movement import cutscene_active, request_skip_cinematic


CoordResolver = Callable[[], tuple[float, float] | None]
AgentResolver = Callable[[], int | None]
LogFn = Callable[[str], None]


def _noop_log(_message: str) -> None:
    return


def add_interact_npc_state(bot, *, coords_resolver: CoordResolver, name: str = "Interact NPC") -> None:
    def _interact_npc():
        coords = coords_resolver()
        if coords is None:
            return
        x, y = coords
        yield from bot.Move._coro_xy(x, y, step_name=name or "Interact NPC")
        if cutscene_active():
            return
        yield from bot.Interact._coro_with_npc_at_xy(x, y, step_name=name)

    bot.States.AddCustomState(_interact_npc, str(name or "Interact NPC"))


def add_interact_npc_at_xy_state(bot, *, coords_resolver: CoordResolver, name: str = "Interact NPC") -> None:
    def _interact_npc_at_xy():
        coords = coords_resolver()
        if coords is None:
            return
        if cutscene_active():
            return
        x, y = coords
        yield from bot.Interact._coro_with_npc_at_xy(x, y)

    bot.States.AddCustomState(_interact_npc_at_xy, str(name or "Interact NPC"))


def add_dialog_state(bot, *, coords_resolver: CoordResolver, dialog_id, name: str = "Dialog") -> None:
    def _dialog_core():
        coords = coords_resolver()
        if coords is None:
            return
        x, y = coords
        yield from bot.Move._coro_xy(x, y, step_name=name or "Dialog")
        if cutscene_active():
            return
        yield from bot.Dialogs._coro_at_xy(x, y, dialog_id)

    bot.States.AddCustomState(_dialog_core, str(name or "Dialog"))


def add_dialog_with_model_state(bot, *, model_id: int, dialog_id: int, name: str = "Dialog With Model") -> None:
    def _dialog_with_model():
        from Py4GWCoreLib import Agent, Routines

        agent_id = Routines.Agents.GetAgentIDByModelID(int(model_id))
        x, y = Agent.GetXY(agent_id)
        yield from bot.Move._coro_xy(x, y, step_name=name or "Dialog With Model")
        if cutscene_active():
            return
        yield from bot.Dialogs._coro_at_xy(x, y, int(dialog_id))

    bot.States.AddCustomState(_dialog_with_model, str(name or "Dialog With Model"))


def add_dialogs_state(
    bot,
    *,
    coords_resolver: CoordResolver,
    dialog_ids: Iterable[int],
    interval_ms: int = 200,
    name: str = "Dialogs",
) -> None:
    ids = [int(value) for value in dialog_ids]

    def _dialogs_core():
        from Py4GWCoreLib import Player

        coords = coords_resolver()
        if coords is None:
            return
        x, y = coords
        yield from bot.Move._coro_xy(x, y, step_name=name)
        if cutscene_active():
            return
        yield from bot.Interact._coro_with_npc_at_xy(x, y, step_name=name)
        if cutscene_active():
            return
        for idx, dialog_id in enumerate(ids):
            if cutscene_active():
                return
            Player.SendDialog(dialog_id)
            if idx < len(ids) - 1 and interval_ms > 0:
                yield from bot.Wait._coro_for_time(int(interval_ms))

    bot.States.AddCustomState(_dialogs_core, str(name))


def add_dialog_multibox_state(
    bot,
    *,
    coords_resolver: CoordResolver,
    dialog_ids: Iterable[int],
    interval_ms: int = 200,
    send_wait_step_ms: int = 50,
    send_timeout_ms: int = 5000,
    name: str = "Dialog Multibox",
    log: LogFn | None = None,
) -> None:
    ids = [int(value) for value in dialog_ids]
    log_fn = log or _noop_log

    def _wait_for_send_dialog_to_target(sender_email: str, refs: list[tuple[str, int]]):
        from Py4GWCoreLib import GLOBAL_CACHE, Routines, SharedCommandType

        if not refs:
            return
        deadline = monotonic() + (max(250, int(send_timeout_ms)) / 1000.0)
        pending = {(email, idx) for email, idx in refs if idx >= 0}
        while pending and monotonic() < deadline:
            if cutscene_active():
                return
            completed: list[tuple[str, int]] = []
            for account_email, message_index in pending:
                message = GLOBAL_CACHE.ShMem.GetInbox(message_index)
                is_same_message = (
                    bool(getattr(message, "Active", False))
                    and str(getattr(message, "ReceiverEmail", "") or "") == account_email
                    and str(getattr(message, "SenderEmail", "") or "") == sender_email
                    and int(getattr(message, "Command", -1)) == int(SharedCommandType.SendDialogToTarget)
                )
                if not is_same_message:
                    completed.append((account_email, message_index))
            for key in completed:
                pending.discard(key)
            if pending:
                yield from Routines.Yield.wait(max(10, int(send_wait_step_ms)))

    def _dialogs_multibox_core():
        from Py4GWCoreLib import GLOBAL_CACHE, Player, SharedCommandType

        coords = coords_resolver()
        if coords is not None:
            x, y = coords
            yield from bot.Move._coro_xy(x, y, step_name=name)
            if cutscene_active():
                return
            yield from bot.Interact._coro_with_npc_at_xy(x, y, step_name=name)
            if cutscene_active():
                return

        sender_email = str(Player.GetAccountEmail() or "")
        target_id = int(Player.GetTargetID() or 0)
        if target_id <= 0:
            log_fn("dialog_multibox has no target.")
            return

        account_emails = [
            str(getattr(account, "AccountEmail", "") or "")
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData()
        ]
        account_emails = [email for email in account_emails if email and email != sender_email]

        for idx, dialog_id in enumerate(ids):
            if cutscene_active():
                return
            Player.SendDialog(dialog_id)
            sent_messages: list[tuple[str, int]] = []
            for account_email in account_emails:
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.SendDialogToTarget,
                    (float(target_id), float(dialog_id), 0.0, 0.0),
                )
                sent_messages.append((account_email, int(message_index)))
            yield from _wait_for_send_dialog_to_target(sender_email, sent_messages)
            if idx < len(ids) - 1 and interval_ms > 0:
                yield from bot.Wait._coro_for_time(int(interval_ms))

    bot.States.AddCustomState(_dialogs_multibox_core, str(name))


def add_interact_gadget_state(bot, *, coords_resolver: CoordResolver, name: str = "Interact Gadget") -> None:
    def _interact_gadget():
        coords = coords_resolver()
        if coords is None:
            return
        if cutscene_active():
            return
        x, y = coords
        yield from bot.Interact._coro_with_gadget_at_xy(x, y)

    bot.States.AddCustomState(_interact_gadget, str(name))


def add_loot_chest_state(
    bot,
    *,
    coords_resolver: CoordResolver,
    max_dist: float,
    multibox: bool = False,
    name: str = "Loot Chest",
    log: LogFn | None = None,
) -> None:
    log_fn = log or _noop_log
    chest_range = float(max_dist if max_dist > 0 else 2500.0)

    def _command_type_routine_in_message_is_active(account_email, shared_command_type) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE

        index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
        return bool(index != -1 and message is not None and message.Command == shared_command_type)

    def _loot():
        from Py4GWCoreLib import AgentArray, GLOBAL_CACHE, Player, Routines, SharedCommandType

        coords = coords_resolver()
        if coords is None:
            yield
            return
        x, y = coords
        yield from bot.Move._coro_xy(x, y, name)
        if cutscene_active():
            return
        yield from bot.Wait._coro_for_time(250)

        chests = AgentArray.GetGadgetArray()
        chests = AgentArray.Filter.ByDistance(chests, (x, y), chest_range)
        chests = AgentArray.Sort.ByDistance(chests, Player.GetXY())
        if not chests:
            log_fn(f"loot_chest found no chest near ({x}, {y})")
            yield
            return

        target = int(chests[0])
        Player.ChangeTarget(target)
        yield from Routines.Yield.wait(150)
        if cutscene_active():
            return
        Player.Interact(target, False)
        yield from Routines.Yield.wait(150)
        if not multibox:
            yield
            return

        sender_email = str(Player.GetAccountEmail() or "")
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email) if sender_email else None
        sender_party_id = int(getattr(sender_account.AgentPartyData, "PartyID", 0) or 0) if sender_account else 0
        sender_map_id = int(getattr(sender_account.AgentData.Map, "MapID", 0) or 0) if sender_account else 0
        sender_region = int(getattr(sender_account.AgentData.Map, "Region", 0) or 0) if sender_account else 0
        sender_district = int(getattr(sender_account.AgentData.Map, "District", 0) or 0) if sender_account else 0
        sender_language = int(getattr(sender_account.AgentData.Map, "Language", 0) or 0) if sender_account else 0

        while _command_type_routine_in_message_is_active(sender_email, SharedCommandType.InteractWithTarget):
            yield from Routines.Yield.wait(250)
        while _command_type_routine_in_message_is_active(sender_email, SharedCommandType.PickUpLoot):
            yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.wait(1000)

        recipients_sent = 0
        for account in accounts:
            account_email = str(getattr(account, "AccountEmail", "") or "")
            if not account_email or account_email == sender_email:
                continue
            if sender_party_id > 0 and int(getattr(account.AgentPartyData, "PartyID", 0) or 0) != sender_party_id:
                continue
            account_map_id = int(getattr(account.AgentData.Map, "MapID", 0) or 0)
            account_region = int(getattr(account.AgentData.Map, "Region", 0) or 0)
            account_district = int(getattr(account.AgentData.Map, "District", 0) or 0)
            account_language = int(getattr(account.AgentData.Map, "Language", 0) or 0)
            if sender_map_id > 0 and (
                account_map_id != sender_map_id
                or account_region != sender_region
                or account_district != sender_district
                or account_language != sender_language
            ):
                continue
            message_index = int(
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.InteractWithTarget,
                    (target, 0, 0, 0),
                )
            )
            if message_index < 0:
                log_fn(f"loot_chest multibox dispatch failed sender={sender_email} receiver={account_email}")
                continue
            recipients_sent += 1
            yield from Routines.Yield.wait(3000)

        if recipients_sent == 0:
            log_fn(f"loot_chest multibox found no valid same-party same-map recipients; sender={sender_email}")
        yield

    bot.States.AddCustomState(_loot, str(name))


def add_interact_item_state(
    bot,
    *,
    model_id: int | None,
    has_model_filter: bool,
    max_dist: float,
    name: str = "Interact Item",
) -> None:
    item_range = float(max_dist if max_dist > 0 else 1200.0)

    def _interact():
        from Py4GWCoreLib import Agent, AgentArray, Item, Player

        item_array = AgentArray.GetItemArray()
        px, py = Player.GetXY()
        item_array = AgentArray.Filter.ByDistance(item_array, (px, py), item_range)
        if not item_array:
            yield
            return
        item_array = AgentArray.Sort.ByDistance(item_array, (px, py))
        target_ground_agent_id = 0
        if not has_model_filter:
            target_ground_agent_id = int(item_array[0])
        else:
            me = int(Player.GetAgentID())
            for ground_agent_id in item_array:
                owner = int(Agent.GetItemAgentOwnerID(ground_agent_id))
                if owner not in (0, me):
                    continue
                item_id = int(Agent.GetItemAgentItemID(ground_agent_id))
                if item_id > 0 and int(Item.GetModelID(item_id)) == int(model_id):
                    target_ground_agent_id = int(ground_agent_id)
                    break
        if target_ground_agent_id <= 0:
            yield
            return
        item_x, item_y = Agent.GetXY(target_ground_agent_id)
        yield from bot.Move._coro_xy(item_x, item_y, name)
        if cutscene_active():
            return
        Player.Interact(target_ground_agent_id, call_target=False)
        yield from bot.Wait._coro_for_time(1000)

    bot.States.AddCustomState(_interact, str(name))


def add_use_item_state(bot, *, model_id: int, name: str | None = None) -> None:
    def _use() -> None:
        from Py4GWCoreLib import GLOBAL_CACHE

        item_id = int(GLOBAL_CACHE.Inventory.GetFirstModelID(int(model_id)))
        if item_id > 0:
            GLOBAL_CACHE.Inventory.UseItem(item_id)

    bot.States.AddCustomState(_use, str(name or f"UseItem {model_id}"))


def add_interact_quest_npc_state(bot, *, name: str = "Interact Quest NPC") -> None:
    def _interact() -> None:
        from Py4GWCoreLib import Agent, AgentArray, Player

        if cutscene_active():
            return
        ally_array = AgentArray.GetNPCMinipetArray()
        px, py = Player.GetXY()
        ally_array = AgentArray.Filter.ByDistance(ally_array, (px, py), 5000)
        quest_npcs = [agent_id for agent_id in ally_array if Agent.HasQuest(agent_id)]
        if quest_npcs:
            Player.Interact(quest_npcs[0], call_target=False)

    bot.States.AddCustomState(_interact, str(name))


def add_skip_cutscene_state(
    bot,
    *,
    wait_ms: int = 10000,
    poll_ms: int = 250,
    pre_skip_delay_ms: int = 3000,
    name: str = "Skip Cutscene",
) -> None:
    def _wait_without_transition_break(duration_ms: int):
        from Py4GWCoreLib import Routines

        deadline = monotonic() + (max(0, int(duration_ms)) / 1000.0)
        while monotonic() < deadline:
            remaining_ms = int((deadline - monotonic()) * 1000.0)
            yield from Routines.Yield.wait(max(50, min(250, remaining_ms)), break_on_map_transition=False)

    def _skip():
        from Py4GWCoreLib import Map

        poll = max(50, int(poll_ms))
        deadline = monotonic() + (max(0, int(wait_ms)) / 1000.0)
        while monotonic() < deadline:
            if cutscene_active():
                delay_ms = max(0, int(pre_skip_delay_ms))
                if delay_ms > 0:
                    yield from _wait_without_transition_break(delay_ms)
                    if not cutscene_active():
                        return
                request_skip_cinematic()
                break
            yield from bot.Wait._coro_for_time(poll)
        while cutscene_active() or Map.IsMapLoading():
            yield from bot.Wait._coro_for_time(poll)

    bot.States.AddCustomState(_skip, str(name))


def add_key_press_state(bot, *, key_name: str, name: str | None = None, log: LogFn | None = None) -> bool:
    from Py4GWCoreLib import Key, Keystroke

    log_fn = log or _noop_log
    normalized = str(key_name or "").upper()
    mapped = {
        "F1": "F1",
        "F2": "F2",
        "SPACE": "Space",
        "ENTER": "Enter",
        "ESCAPE": "Escape",
        "ESC": "Escape",
    }.get(normalized)
    if mapped is None:
        log_fn(f"Unsupported key_press key: {normalized!r}")
        return False
    bot.States.AddCustomState(
        lambda _k=mapped: Keystroke.PressAndRelease(getattr(Key, _k).value),
        str(name or f"KeyPress {normalized}"),
    )
    return True


def add_emote_state(bot, *, command: str, name: str | None = None) -> None:
    from Py4GWCoreLib import Player

    raw_command = str(command or "kneel").strip()
    normalized = raw_command[1:] if raw_command.startswith("/") else raw_command
    if not normalized:
        normalized = "kneel"
    bot.States.AddCustomState(
        lambda _cmd=normalized: Player.SendChatCommand(_cmd),
        str(name or f"Emote /{normalized}"),
    )


def add_target_enemy_state(
    bot,
    *,
    enemy_resolver: AgentResolver,
    set_party_target: bool = False,
    party_target_setter: Callable[[int], None] | None = None,
    name: str = "Target Enemy",
) -> None:
    def _target_enemy() -> None:
        from Py4GWCoreLib import Player

        target_agent_id = enemy_resolver()
        if target_agent_id is None:
            return
        Player.ChangeTarget(target_agent_id)
        if set_party_target and party_target_setter is not None:
            party_target_setter(int(target_agent_id))

    bot.States.AddCustomState(_target_enemy, str(name))


def add_wait_model_has_quest_state(bot, *, model_id: int) -> None:
    bot.Wait.UntilModelHasQuest(int(model_id))


def add_debug_nearby_enemies_state(
    bot,
    *,
    max_dist: float,
    limit: int,
    include_dead: bool,
    enabled: Callable[[], bool],
    name: str,
    log: LogFn | None = None,
) -> None:
    log_fn = log or _noop_log

    def _debug_nearby_enemies() -> None:
        from Py4GWCoreLib import Agent, AgentArray, Player, Utils

        if not enabled():
            return
        px, py = Player.GetXY()
        enemies = AgentArray.GetEnemyArray()
        enemies = AgentArray.Filter.ByDistance(enemies, (px, py), float(max_dist))
        enemies = AgentArray.Filter.ByCondition(
            enemies,
            lambda agent_id: Agent.IsSpawned(agent_id) and (include_dead or Agent.IsAlive(agent_id)),
        )
        enemies = AgentArray.Sort.ByDistance(enemies, (px, py))
        log_fn(f"debug_nearby_enemies found {len(enemies)} enemies within {float(max_dist):.0f}")
        for idx, agent_id in enumerate(enemies[: max(1, int(limit))]):
            ax, ay = Agent.GetXY(agent_id)
            distance = Utils.Distance((px, py), (ax, ay))
            log_fn(
                f"[{idx + 1}] agent_id={int(agent_id)} model_id={int(Agent.GetModelID(agent_id))} "
                f"distance={distance:.0f} alive={Agent.IsAlive(agent_id)} name={Agent.GetNameByID(agent_id)!r}"
            )

    bot.States.AddCustomState(_debug_nearby_enemies, str(name))


def add_debug_nearby_agents_state(
    bot,
    *,
    max_dist: float,
    limit: int,
    include_dead: bool,
    enabled: Callable[[], bool],
    name: str,
    log: LogFn | None = None,
) -> None:
    log_fn = log or _noop_log

    def _debug_nearby_agents() -> None:
        from Py4GWCoreLib import Agent, AgentArray, Player, Utils

        if not enabled():
            return
        px, py = Player.GetXY()
        agents = AgentArray.GetAgentArray()
        agents = AgentArray.Filter.ByDistance(agents, (px, py), float(max_dist))
        agents = AgentArray.Filter.ByCondition(
            agents,
            lambda agent_id: Agent.IsValid(agent_id) and (include_dead or Agent.IsAlive(agent_id)),
        )
        agents = AgentArray.Sort.ByDistance(agents, (px, py))
        log_fn(f"debug_nearby_agents found {len(agents)} agents within {float(max_dist):.0f}")
        for idx, agent_id in enumerate(agents[: max(1, int(limit))]):
            ax, ay = Agent.GetXY(agent_id)
            distance = Utils.Distance((px, py), (ax, ay))
            log_fn(
                f"[{idx + 1}] agent_id={int(agent_id)} model_id={int(Agent.GetModelID(agent_id))} "
                f"distance={distance:.0f} alive={Agent.IsAlive(agent_id)} spawned={Agent.IsSpawned(agent_id)} "
                f"living={Agent.IsLiving(agent_id)} item={Agent.IsItem(agent_id)} gadget={Agent.IsGadget(agent_id)} "
                f"allegiance={Agent.GetAllegiance(agent_id)[1]!r} name={Agent.GetNameByID(agent_id)!r}"
            )

    bot.States.AddCustomState(_debug_nearby_agents, str(name))

"""
Reusable consumable helpers for Botting-style runtimes.
"""
from __future__ import annotations

from typing import Callable


LogFn = Callable[[str], None]


def _noop_log(_message: str) -> None:
    return


def consumable_specs(mode: str) -> list[tuple[int, str]]:
    from Py4GWCoreLib.enums import ModelID

    conset = [
        (int(ModelID.Essence_Of_Celerity.value), "Essence_of_Celerity_item_effect"),
        (int(ModelID.Grail_Of_Might.value), "Grail_of_Might_item_effect"),
        (int(ModelID.Armor_Of_Salvation.value), "Armor_of_Salvation_item_effect"),
    ]
    pcons = [
        (int(ModelID.Birthday_Cupcake.value), "Birthday_Cupcake_skill"),
        (int(ModelID.Golden_Egg.value), "Golden_Egg_skill"),
        (int(ModelID.Candy_Corn.value), "Candy_Corn_skill"),
        (int(ModelID.Candy_Apple.value), "Candy_Apple_skill"),
        (int(ModelID.Slice_Of_Pumpkin_Pie.value), "Pie_Induced_Ecstasy"),
        (int(ModelID.Drake_Kabob.value), "Drake_Skin"),
        (int(ModelID.Bowl_Of_Skalefin_Soup.value), "Skale_Vigor"),
        (int(ModelID.Pahnai_Salad.value), "Pahnai_Salad_item_effect"),
        (int(ModelID.War_Supplies.value), "Well_Supplied"),
    ]
    if mode == "conset":
        return conset
    if mode == "pcons":
        return pcons
    return conset + pcons


def consumable_property_names(mode: str) -> tuple[str, ...]:
    conset = ("essence_of_celerity", "grail_of_might", "armor_of_salvation")
    pcons = (
        "birthday_cupcake",
        "golden_egg",
        "candy_corn",
        "candy_apple",
        "slice_of_pumpkin_pie",
        "drake_kabob",
        "bowl_of_skalefin_soup",
        "pahnai_salad",
        "war_supplies",
    )
    if mode == "conset":
        return conset
    if mode == "pcons":
        return pcons
    return conset + pcons


def normalize_consumable_mode(raw_mode: object, default: str = "all") -> str:
    token = str(raw_mode or default).strip().lower()
    aliases = {
        "all": "all",
        "all_consumables": "all",
        "consumables": "all",
        "use_all": "all",
        "cons": "conset",
        "conset": "conset",
        "pcon": "pcons",
        "pcons": "pcons",
        "essence": "essence",
        "essence_of_celerity": "essence",
        "grail": "grail",
        "grail_of_might": "grail",
        "armor": "armor",
        "armor_of_salvation": "armor",
    }
    return aliases.get(token, "")


def local_effect_active(effect_id: int) -> bool:
    if effect_id <= 0:
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE, Player

        return bool(GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), effect_id))
    except Exception:
        return False


def use_local_consumable(model_id: int, effect_id: int) -> bool:
    if local_effect_active(effect_id):
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        item_id = int(GLOBAL_CACHE.Inventory.GetFirstModelID(model_id) or 0)
        if item_id <= 0:
            return False
        GLOBAL_CACHE.Inventory.UseItem(item_id)
        return True
    except Exception:
        return False


def should_skip_local_consumable_for_non_leader(*, leader_only: bool, log: LogFn | None = None) -> bool:
    log_fn = log or _noop_log
    if not leader_only:
        return False
    try:
        from Py4GWCoreLib import Party

        if not Party.IsPartyLoaded():
            return False
        if int(Party.GetPlayerCount() or 0) <= 1:
            return False
        if not Party.IsPartyLeader():
            log_fn("use_consumables local execution skipped on non-leader account (leader_only=true).")
            return True
    except Exception as exc:
        log_fn(f"use_consumables leader_only guard failed: {exc}")
    return False


def add_use_single_consumable_state(
    bot,
    *,
    model_id: int,
    effect_name: str,
    multibox: bool,
    leader_only: bool = True,
    name: str = "",
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE

    log_fn = log or _noop_log
    effect_id = int(GLOBAL_CACHE.Skill.GetID(effect_name) or 0)
    if multibox:
        bot.Multibox.UseConsumable(model_id, effect_id)
        return

    def _use_local_consumable_runtime() -> None:
        if should_skip_local_consumable_for_non_leader(leader_only=leader_only, log=log_fn):
            return
        if local_effect_active(effect_id):
            log_fn(f"use_consumables skipped for model_id={model_id}: effect already active.")
            return
        item_id = int(GLOBAL_CACHE.Inventory.GetFirstModelID(model_id) or 0)
        if item_id <= 0:
            log_fn(f"use_consumables skipped for model_id={model_id}: item not found.")
            return
        GLOBAL_CACHE.Inventory.UseItem(item_id)
        log_fn(f"use_consumables used model_id={model_id} item_id={item_id}.")

    bot.States.AddCustomState(_use_local_consumable_runtime, str(name or f"Use {effect_name}"))


def account_map_id(account) -> int:
    map_obj = getattr(getattr(account, "AgentData", None), "Map", None)
    return int(getattr(account, "MapID", 0) or getattr(map_obj, "MapID", 0) or 0)


def send_consumable_to_accounts(model_id: int, effect_id: int, *, include_self: bool = False) -> list[tuple[str, int]]:
    from Py4GWCoreLib import GLOBAL_CACHE, Map, Player, SharedCommandType

    sender_email = str(Player.GetAccountEmail() or "")
    current_map_id = int(Map.GetMapID() or 0)
    refs: list[tuple[str, int]] = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        email = str(getattr(account, "AccountEmail", "") or "")
        if not email or (email == sender_email and not include_self):
            continue
        if current_map_id > 0 and account_map_id(account) != current_map_id:
            continue
        idx = GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            email,
            SharedCommandType.PCon,
            (int(model_id), int(effect_id), 0, 0),
        )
        refs.append((email, int(idx)))
    return refs


def yield_upkeep_local(bot, specs: list[tuple[int, str]], poll_ms: int, *, log: LogFn | None = None):
    from Py4GWCoreLib import GLOBAL_CACHE

    log_fn = log or _noop_log
    for model_id, effect_name in specs:
        effect_id = int(GLOBAL_CACHE.Skill.GetID(effect_name) or 0)
        if use_local_consumable(model_id, effect_id):
            log_fn(f"upkeep_consumables used local model_id={model_id}.")
            yield from bot.Wait._coro_for_time(500)
    yield from bot.Wait._coro_for_time(poll_ms)


def yield_upkeep_multibox(
    bot,
    specs: list[tuple[int, str]],
    mode: str,
    poll_ms: int,
    *,
    log: LogFn | None = None,
):
    from Py4GWCoreLib import GLOBAL_CACHE

    log_fn = log or _noop_log
    for model_id, effect_name in specs:
        effect_id = int(GLOBAL_CACHE.Skill.GetID(effect_name) or 0)
        used_local = use_local_consumable(model_id, effect_id)
        if used_local:
            log_fn(f"upkeep_consumables used local model_id={model_id}.")
            yield from bot.Wait._coro_for_time(500)
        if mode == "pcons" or not local_effect_active(effect_id):
            refs = send_consumable_to_accounts(model_id, effect_id)
            if refs:
                log_fn(f"upkeep_consumables sent model_id={model_id} to {len(refs)} account(s).")
            yield from bot.Wait._coro_for_time(1200 if mode == "conset" else 350)
    yield from bot.Wait._coro_for_time(poll_ms)

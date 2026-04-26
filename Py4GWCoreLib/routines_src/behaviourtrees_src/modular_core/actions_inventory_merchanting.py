"""
actions_inventory_merchanting module

This module provides merchant/trader-oriented inventory step handlers.
"""
from __future__ import annotations

from time import monotonic

from .actions_inventory import (
    _apply_default_npc_selector,
    _encode_material_model_filter,
    _get_leftover_material_item_ids,
    _get_nonsalvageable_gold_item_ids,
    _iter_other_account_emails,
    _parse_widget_names,
    _wait_for_outbound_messages,
)
from .step_registration import modular_step
from .step_context import StepContext
from .step_selectors import resolve_agent_xy_from_step
from .step_utils import log_recipe, parse_step_bool, parse_step_int, wait_after_step


def handle_sell_materials(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType
    from Py4GWCoreLib.enums_src.Item_enums import MaterialMap
    from Py4GWCoreLib.enums_src.Model_enums import ModelID

    selector_step = dict(ctx.step)

    name = ctx.step.get("name", "Sell Materials")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))
    reverse_material_map = {material_name.lower(): int(model_id.value) for model_id, material_name in MaterialMap.items()}

    def _resolve_selected_models_runtime() -> set[int] | None:
        selected_models: set[int] | None = None
        raw_materials = ctx.step.get("materials")
        if raw_materials is None:
            return None

        if not isinstance(raw_materials, (list, tuple, set)):
            raw_materials = [raw_materials]

        selected_models = set()
        for raw_material in raw_materials:
            if isinstance(raw_material, str):
                material_key = raw_material.strip()
                model_enum = ModelID.__members__.get(material_key)
                if model_enum is not None:
                    selected_models.add(int(model_enum.value))
                    continue

                resolved_model = reverse_material_map.get(material_key.lower())
                if resolved_model is not None:
                    selected_models.add(resolved_model)
                    continue

            model_id = parse_step_int(raw_material, -1)
            if model_id >= 0:
                selected_models.add(model_id)

        return selected_models

    def _sell_local():
        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "materials")
        selected_models = _resolve_selected_models_runtime()
        log_recipe(ctx, f"sell_materials start: selector={step_selector!r}")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "sell_materials: failed to resolve Crafting Material Trader coordinates.")
            yield
            return

        x, y = coords
        sent_messages: list[tuple[str, int]] = []
        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("sell", _encode_material_model_filter(selected_models), "", "")
            for account_email in account_emails:
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
            log_recipe(
                ctx,
                f"sell_materials: dispatched multibox sell command to {len(sent_messages)} account(s) before local execution.",
            )

        log_recipe(ctx, f"sell_materials: resolved trader at ({x}, {y}), executing local merchant routine.")
        sell_metrics = yield from Routines.Yield.Merchant.SellMaterialsAtTrader(
            x,
            y,
            selected_models=selected_models,
        )
        log_recipe(ctx, f"sell_materials metrics: {sell_metrics}")

        if multibox:
            yield from _wait_for_outbound_messages(
                ctx,
                "sell_materials",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )

        log_recipe(ctx, "sell_materials: completed.")
        yield

    ctx.bot.States.AddCustomState(_sell_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_deposit_materials(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Inventory, Player, Routines, SharedCommandType
    from Py4GWCoreLib.enums_src.Item_enums import MaterialMap
    from Py4GWCoreLib.enums_src.Model_enums import ModelID

    name = ctx.step.get("name", "Deposit Materials")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))
    max_deposit_items_raw = parse_step_int(ctx.step.get("max_deposit_items", 0), 0)
    max_deposit_items = max_deposit_items_raw if max_deposit_items_raw > 0 else None
    exact_quantity_raw = parse_step_int(ctx.step.get("exact_quantity", 250), 250)
    exact_quantity = exact_quantity_raw if exact_quantity_raw > 0 else None
    open_wait_ms = max(0, parse_step_int(ctx.step.get("open_wait_ms", 1000), 1000))
    deposit_wait_ms = max(0, parse_step_int(ctx.step.get("deposit_wait_ms", 250), 250))
    max_passes = max(1, parse_step_int(ctx.step.get("max_passes", 2), 2))
    reverse_material_map = {material_name.lower(): int(model_id.value) for model_id, material_name in MaterialMap.items()}

    selected_models: set[int] | None = None
    raw_materials = ctx.step.get("materials")
    if raw_materials is not None:
        if not isinstance(raw_materials, (list, tuple, set)):
            raw_materials = [raw_materials]

        selected_models = set()
        for raw_material in raw_materials:
            if isinstance(raw_material, str):
                material_key = raw_material.strip()
                model_enum = ModelID.__members__.get(material_key)
                if model_enum is not None:
                    selected_models.add(int(model_enum.value))
                    continue

                resolved_model = reverse_material_map.get(material_key.lower())
                if resolved_model is not None:
                    selected_models.add(resolved_model)
                    continue

            model_id = parse_step_int(raw_material, -1)
            if model_id >= 0:
                selected_models.add(model_id)

    def _deposit_local():
        if not Inventory.IsStorageOpen():
            log_recipe(ctx, "deposit_materials: opening Xunlai window.")
        deposit_metrics = yield from Routines.Yield.Merchant.DepositMaterials(
            selected_models=selected_models,
            exact_quantity=exact_quantity,
            max_deposit_items=max_deposit_items,
            open_wait_ms=open_wait_ms,
            deposit_wait_ms=deposit_wait_ms,
            max_passes=max_passes,
        )
        log_recipe(ctx, f"deposit_materials metrics: {deposit_metrics}")

        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("deposit", _encode_material_model_filter(selected_models), str(max_deposit_items or 0), str(exact_quantity or 0))
            sent_messages: list[tuple[str, int]] = []
            for account_email in account_emails:
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (0.0, 0.0, 0.0, 0.0),
                    extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
            yield from _wait_for_outbound_messages(
                ctx,
                "deposit_materials",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )

        log_recipe(ctx, "deposit_materials: completed.")
        yield

    ctx.bot.States.AddCustomState(_deposit_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_sell_nonsalvageable_golds(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)
    name = ctx.step.get("name", "Sell Non-Salvageable Golds")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))

    def _sell_local():
        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "merchant")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "sell_nonsalvageable_golds: failed to resolve Merchant coordinates.")
            yield
            return

        x, y = coords
        sent_messages: list[tuple[str, int]] = []
        if multibox:
            sender_email = Player.GetAccountEmail()
            for account_email in _iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    ("sell_nonsalvageable_golds", "", "", ""),
                )
                sent_messages.append((account_email, int(message_index)))

        sell_ids = _get_nonsalvageable_gold_item_ids()
        if sell_ids:
            yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
            yield from ctx.bot.Wait._coro_for_time(1200)
            yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
            log_recipe(ctx, f"sell_nonsalvageable_golds: sold {len(sell_ids)} item(s).")
        else:
            log_recipe(ctx, "sell_nonsalvageable_golds: no eligible gold items.")

        if multibox:
            yield from _wait_for_outbound_messages(
                ctx,
                "sell_nonsalvageable_golds",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )
        yield

    ctx.bot.States.AddCustomState(_sell_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_sell_leftover_materials(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)
    name = ctx.step.get("name", "Sell Leftover Materials")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    batch_size = max(1, parse_step_int(ctx.step.get("batch_size", 10), 10))
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))

    def _sell_local():
        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "merchant")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "sell_leftover_materials: failed to resolve Merchant coordinates.")
            yield
            return

        x, y = coords
        sent_messages: list[tuple[str, int]] = []
        if multibox:
            sender_email = Player.GetAccountEmail()
            for account_email in _iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    ("sell_merchant_leftovers", "", str(batch_size), ""),
                )
                sent_messages.append((account_email, int(message_index)))

        sell_ids = _get_leftover_material_item_ids(batch_size=batch_size)
        if sell_ids:
            yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
            yield from ctx.bot.Wait._coro_for_time(1200)
            yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
            log_recipe(ctx, f"sell_leftover_materials: sold {len(sell_ids)} stack(s) with qty < {batch_size}.")
        else:
            log_recipe(ctx, f"sell_leftover_materials: no common material stacks below {batch_size}.")

        if multibox:
            yield from _wait_for_outbound_messages(
                ctx,
                "sell_leftover_materials",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )
        yield

    ctx.bot.States.AddCustomState(_sell_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_sell_scrolls(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)
    name = ctx.step.get("name", "Sell Scrolls")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))
    scroll_models = set(int(v) for v in ctx.step.get("scroll_models", [5594, 5595, 5611, 5853, 5975, 5976, 21233]))

    def _sell_local():
        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "merchant")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "sell_scrolls: failed to resolve Merchant coordinates.")
            yield
            return

        x, y = coords
        sent_messages: list[tuple[str, int]] = []
        if multibox:
            sender_email = Player.GetAccountEmail()
            filter_raw = ",".join(str(mid) for mid in sorted(scroll_models))
            for account_email in _iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    ("sell_scrolls", filter_raw, "", ""),
                )
                sent_messages.append((account_email, int(message_index)))

        bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
        sell_ids = [int(item_id) for item_id in item_array if int(GLOBAL_CACHE.Item.GetModelID(item_id)) in scroll_models]
        if sell_ids:
            yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
            yield from ctx.bot.Wait._coro_for_time(1200)
            yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
            log_recipe(ctx, f"sell_scrolls: sold {len(sell_ids)} scroll(s).")
        else:
            log_recipe(ctx, "sell_scrolls: no matching scrolls.")

        if multibox:
            yield from _wait_for_outbound_messages(
                ctx,
                "sell_scrolls",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )
        yield

    ctx.bot.States.AddCustomState(_sell_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_buy_ectoplasm(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)

    name = ctx.step.get("name", "Buy Ectoplasm")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))
    use_storage_gold = str(ctx.step.get("use_storage_gold", True)).strip().lower() in ("1", "true", "yes", "on")
    start_storage_gold_threshold = parse_step_int(ctx.step.get("start_storage_gold_threshold", 900_000), 900_000)
    stop_storage_gold_threshold = parse_step_int(ctx.step.get("stop_storage_gold_threshold", 500_000), 500_000)
    max_ecto_to_buy_raw = parse_step_int(ctx.step.get("max_ecto_to_buy", 0), 0)
    max_ecto_to_buy = max_ecto_to_buy_raw if max_ecto_to_buy_raw > 0 else None
    if stop_storage_gold_threshold < 0:
        stop_storage_gold_threshold = 0
    if start_storage_gold_threshold < stop_storage_gold_threshold:
        start_storage_gold_threshold = stop_storage_gold_threshold

    def _buy_local():
        storage_gold = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())
        character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
        if use_storage_gold:
            if storage_gold <= start_storage_gold_threshold:
                log_recipe(
                    ctx,
                    f"buy_ectoplasm: skipped, storage gold {storage_gold} is not above start threshold {start_storage_gold_threshold}.",
                )
                yield
                return
        elif character_gold <= 0:
            log_recipe(ctx, "buy_ectoplasm: skipped, character has no gold and storage mode is disabled.")
            yield
            return

        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "rare_materials")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "buy_ectoplasm: failed to resolve Rare Material Trader coordinates.")
            yield
            return

        x, y = coords
        log_recipe(
            ctx,
            f"buy_ectoplasm: use_storage_gold={use_storage_gold}, start storage_gold={storage_gold}, stop_threshold={stop_storage_gold_threshold}, trader=({x}, {y}).",
        )
        ecto_metrics = yield from Routines.Yield.Merchant.BuyEctoplasm(
            x=x,
            y=y,
            use_storage_gold=use_storage_gold,
            start_threshold=start_storage_gold_threshold,
            stop_threshold=stop_storage_gold_threshold,
            max_ecto_to_buy=max_ecto_to_buy,
        )
        log_recipe(ctx, f"buy_ectoplasm metrics: {ecto_metrics}")

        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("buy_ectoplasm", "1" if use_storage_gold else "0", str(max_ecto_to_buy or 0), "")
            sent_messages: list[tuple[str, int]] = []
            for account_email in account_emails:
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (
                        float(x),
                        float(y),
                        float(start_storage_gold_threshold),
                        float(stop_storage_gold_threshold),
                    ),
                    extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
            yield from _wait_for_outbound_messages(
                ctx,
                "buy_ectoplasm",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )

        log_recipe(ctx, f"buy_ectoplasm: completed with storage_gold={int(GLOBAL_CACHE.Inventory.GetGoldInStorage())}.")
        yield

    ctx.bot.States.AddCustomState(_buy_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_merchant_rules_execute(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

    name = str(ctx.step.get("name", "Merchant Rules Execute") or "Merchant Rules Execute")
    multibox = parse_step_bool(ctx.step.get("multibox", True), True)
    local = parse_step_bool(ctx.step.get("local", True), True)
    auto_enable_widget = parse_step_bool(ctx.step.get("auto_enable_widget", True), True)
    enable_wait_ms = max(0, parse_step_int(ctx.step.get("enable_wait_ms", 350), 350))
    include_protected = parse_step_bool(ctx.step.get("include_protected", False), False)
    instant_destroy = parse_step_bool(ctx.step.get("instant_destroy", False), False)
    wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 90_000), 90_000))
    wait_ms = max(0, parse_step_int(ctx.step.get("ms", 0), 0))
    widget_names = _parse_widget_names(ctx.step.get("widget_names", ["MerchantRules", "Merchant Rules"]))
    if not widget_names:
        widget_names = ["MerchantRules", "Merchant Rules"]

    def _execute():
        widget_handler = get_widget_handler()
        def _local_merchant_rules_enabled() -> bool:
            for widget_name in widget_names:
                widget_info = widget_handler.get_widget_info(widget_name)
                if widget_info is not None and bool(getattr(widget_info, "enabled", False)):
                    return True
            return False

        sender_email = str(Player.GetAccountEmail() or "").strip()
        if not sender_email:
            log_recipe(ctx, "merchant_rules_execute: sender account email is unavailable.")
            yield
            return

        target_emails: list[str] = []
        if local:
            target_emails.append(sender_email)
        if multibox:
            target_emails.extend(_iter_other_account_emails())
        target_emails = list(dict.fromkeys(email for email in target_emails if email))

        if auto_enable_widget:
            for widget_name in widget_names:
                widget_handler.enable_widget(widget_name)

            sent_enable_messages: list[tuple[str, int]] = []
            for account_email in target_emails:
                if account_email == sender_email:
                    continue
                for widget_name in widget_names:
                    message_index = GLOBAL_CACHE.ShMem.SendMessage(
                        sender_email,
                        account_email,
                        SharedCommandType.EnableWidget,
                        (0.0, 0.0, 0.0, 0.0),
                        (widget_name, "", "", ""),
                    )
                    sent_enable_messages.append((account_email, int(message_index)))

            yield from _wait_for_outbound_messages(
                ctx,
                "merchant_rules_enable_widget",
                sent_enable_messages,
                SharedCommandType.EnableWidget,
                wait_step_ms=wait_step_ms,
                timeout_ms=min(wait_timeout_ms, 30_000),
            )
            if enable_wait_ms > 0:
                yield from Routines.Yield.wait(enable_wait_ms)

        local_enabled = _local_merchant_rules_enabled()
        if local and not local_enabled:
            target_emails = [email for email in target_emails if email != sender_email]
            log_recipe(
                ctx,
                "merchant_rules_execute: Merchant Rules widget is not enabled locally; executing multibox targets only.",
            )

        if not target_emails:
            log_recipe(ctx, "merchant_rules_execute: no target accounts selected.")
            yield
            return

        request_id = str(ctx.step.get("request_id", "") or "").strip()
        if not request_id:
            request_id = f"modular_{ctx.recipe_name}_{ctx.step_idx}_{int(monotonic() * 1000)}"
        request_id = request_id[:60]

        include_protected_flag = "1" if include_protected else "0"
        instant_destroy_flag = "1" if instant_destroy else "0"

        message_refs: list[tuple[str, int]] = []
        for account_email in target_emails:
            message_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                account_email,
                SharedCommandType.MerchantRules,
                (3.0, 0.0, 0.0, 0.0),  # MERCHANT_RULES_OPCODE_EXECUTE
                (request_id, "Execute", include_protected_flag, instant_destroy_flag),
            )
            message_refs.append((account_email, int(message_index)))

        yield from _wait_for_outbound_messages(
            ctx,
            "merchant_rules_execute",
            message_refs,
            SharedCommandType.MerchantRules,
            wait_step_ms=wait_step_ms,
            timeout_ms=wait_timeout_ms,
        )

        if wait_ms > 0:
            yield from Routines.Yield.wait(wait_ms)

        log_recipe(
            ctx,
            f"merchant_rules_execute: dispatched execute to {len(target_emails)} account(s) "
            f"(multibox={multibox}, local={local}).",
        )
        yield

    ctx.bot.States.AddCustomState(_execute, name)
    wait_after_step(ctx.bot, ctx.step)


modular_step(
    step_type="buy_ectoplasm",
    category="inventory",
    allowed_params=(
        "max_ecto_to_buy",
        "ms",
        "multibox",
        "multibox_wait_step_ms",
        "multibox_wait_timeout_ms",
        "name",
        "npc",
        "start_storage_gold_threshold",
        "stop_storage_gold_threshold",
        "use_storage_gold",
    ),
    node_class_name="BuyEctoplasmNode",
)(handle_buy_ectoplasm)
modular_step(
    step_type="deposit_materials",
    category="inventory",
    allowed_params=(
        "deposit_wait_ms",
        "exact_quantity",
        "materials",
        "max_deposit_items",
        "max_passes",
        "ms",
        "multibox",
        "multibox_wait_step_ms",
        "multibox_wait_timeout_ms",
        "name",
        "open_wait_ms",
    ),
    node_class_name="DepositMaterialsNode",
)(handle_deposit_materials)
modular_step(
    step_type="merchant_rules_execute",
    category="inventory",
    allowed_params=(
        "auto_enable_widget",
        "enable_wait_ms",
        "include_protected",
        "instant_destroy",
        "local",
        "ms",
        "multibox",
        "multibox_wait_step_ms",
        "multibox_wait_timeout_ms",
        "name",
        "request_id",
        "widget_names",
    ),
    node_class_name="MerchantRulesExecuteNode",
)(handle_merchant_rules_execute)
modular_step(
    step_type="sell_leftover_materials",
    category="inventory",
    allowed_params=(
        "batch_size",
        "ms",
        "multibox",
        "multibox_wait_step_ms",
        "multibox_wait_timeout_ms",
        "name",
        "npc",
    ),
    node_class_name="SellLeftoverMaterialsNode",
)(handle_sell_leftover_materials)
modular_step(
    step_type="sell_materials",
    category="inventory",
    allowed_params=(
        "materials",
        "ms",
        "multibox",
        "multibox_wait_step_ms",
        "multibox_wait_timeout_ms",
        "name",
        "npc",
    ),
    node_class_name="SellMaterialsNode",
)(handle_sell_materials)
modular_step(
    step_type="sell_nonsalvageable_golds",
    category="inventory",
    allowed_params=(
        "ms",
        "multibox",
        "multibox_wait_step_ms",
        "multibox_wait_timeout_ms",
        "name",
        "npc",
    ),
    node_class_name="SellNonsalvageableGoldsNode",
)(handle_sell_nonsalvageable_golds)
modular_step(
    step_type="sell_scrolls",
    category="inventory",
    allowed_params=(
        "ms",
        "multibox",
        "multibox_wait_step_ms",
        "multibox_wait_timeout_ms",
        "name",
        "npc",
        "scroll_models",
    ),
    node_class_name="SellScrollsNode",
)(handle_sell_scrolls)

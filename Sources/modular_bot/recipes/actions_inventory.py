from __future__ import annotations

from typing import Callable

from .step_context import StepContext
from .step_selectors import resolve_agent_xy_from_step
from .step_utils import wait_after_step


def handle_restock_kits(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, ModelID, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)
    if (
        "x" not in selector_step
        and "y" not in selector_step
        and "npc" not in selector_step
        and "target" not in selector_step
        and "name_contains" not in selector_step
        and "agent_name" not in selector_step
        and "model_id" not in selector_step
        and "nearest" not in selector_step
    ):
        selector_step["npc"] = "MERCHANT"

    name = ctx.step.get("name", "Restock Kits")
    multibox_raw = ctx.step.get("multibox", False)

    try:
        id_kits_target = int(ctx.step.get("id_kits", 2))
    except (TypeError, ValueError):
        id_kits_target = 2

    try:
        salvage_kits_target = int(ctx.step.get("salvage_kits", 8))
    except (TypeError, ValueError):
        salvage_kits_target = 8

    multibox = (
        multibox_raw.strip().lower() in ("1", "true", "yes", "on")
        if isinstance(multibox_raw, str)
        else bool(multibox_raw)
    )

    if id_kits_target < 0:
        id_kits_target = 0
    if salvage_kits_target < 0:
        salvage_kits_target = 0

    def _restock_local():
        coords = resolve_agent_xy_from_step(
            selector_step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            yield
            return
        x, y = coords
        yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
        yield from ctx.bot.Wait._coro_for_time(1200)

        id_kits_in_inv = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit.value))
        sup_id_kits_in_inv = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value))
        salvage_kits_in_inv = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value))

        id_kits_to_buy = max(0, id_kits_target - (id_kits_in_inv + sup_id_kits_in_inv))
        salvage_kits_to_buy = max(0, salvage_kits_target - salvage_kits_in_inv)

        yield from Routines.Yield.Merchant.BuyIDKits(id_kits_to_buy)
        yield from Routines.Yield.Merchant.BuySalvageKits(salvage_kits_to_buy)

        if multibox:
            sender_email = Player.GetAccountEmail()
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                account_email = str(getattr(account, "AccountEmail", "") or "")
                if not account_email or account_email == sender_email:
                    continue
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantItems,
                    (x, y, float(id_kits_target), float(salvage_kits_target)),
                )

        yield

    ctx.bot.States.AddCustomState(_restock_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_restock_cons(ctx: StepContext) -> None:
    from Py4GWCoreLib import ConsoleLog, Inventory

    name = ctx.step.get("name", "Restock Consumables")
    restock_specs = (
        ("birthday_cupcake", "BirthdayCupcake"),
        ("candy_apple", "CandyApple"),
        ("honeycomb", "Honeycomb"),
        ("war_supplies", "WarSupplies"),
        ("essence_of_celerity", "EssenceOfCelerity"),
        ("grail_of_might", "GrailOfMight"),
        ("armor_of_salvation", "ArmorOfSalvation"),
        ("golden_egg", "GoldenEgg"),
        ("candy_corn", "CandyCorn"),
        ("slice_of_pumpkin_pie", "SliceOfPumpkinPie"),
        ("drake_kabob", "DrakeKabob"),
        ("bowl_of_skalefin_soup", "BowlOfSkalefinSoup"),
        ("pahnai_salad", "PahnaiSalad"),
    )

    ctx.bot.States.AddCustomState(
        lambda: Inventory.OpenXunlaiWindow() if not Inventory.IsStorageOpen() else None,
        f"{name} Open Xunlai",
    )
    ctx.bot.Wait.ForTime(1000)

    def _enable_restock_properties() -> None:
        for prop_name, _ in restock_specs:
            if not ctx.bot.Properties.exists(prop_name):
                continue
            is_active = bool(ctx.bot.Properties.Get(prop_name, "active"))
            qty = int(ctx.bot.Properties.Get(prop_name, "restock_quantity") or 0)
            if not is_active and qty > 0:
                ctx.bot.Properties.Enable(prop_name)

    ctx.bot.States.AddCustomState(_enable_restock_properties, f"{name} Enable Properties")

    scheduled = 0
    for _, method_name in restock_specs:
        method = getattr(ctx.bot.Items.Restock, method_name, None)
        if callable(method):
            method()
            scheduled += 1

    if scheduled == 0:
        ctx.bot.States.AddCustomState(
            lambda: ConsoleLog(
                f"Recipe:{ctx.recipe_name}",
                "restock_cons found no restock methods to execute.",
            ),
            f"{name} Warn: No Restock Methods",
        )

    wait_after_step(ctx.bot, ctx.step)


HANDLERS: dict[str, Callable[[StepContext], None]] = {
    "restock_kits": handle_restock_kits,
    "restock_cons": handle_restock_cons,
}

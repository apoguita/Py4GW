
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple
from Py4GWCoreLib import *


MODULE_NAME = "Super Item Eater"
MODULE_ICON = "Textures\\Module_Icons\\Item Eater.png"
MODULE_TAGS = ["Sweets", "Alcohol", "Party", "Spam", "Titles", "Exchange"]
quantity_to_consume = 250


def _count_item(model_id: int) -> int:
    """Return the total quantity of *model_id* across all inventory bags."""
    total = 0
    for bag_id in (1, 2, 3, 4):
        try:
            bag = PyInventory.Bag(bag_id, f"Bag_{bag_id}")
            for bag_item in bag.GetItems():
                if int(getattr(bag_item, "model_id", 0) or 0) == model_id:
                    total += int(getattr(bag_item, "quantity", 0) or 0)
        except Exception:
            pass
    return total


def _get_title_info(title_id: int) -> Tuple[int, str, int]:
    """Return (current_points, current_tier_name, points_to_next_tier).

    points_to_next_tier is 0 when the title is fully maxed.
    """
    try:
        title_data = Player.GetTitle(title_id)
        current = title_data.current_points if title_data else 0
    except Exception:
        current = 0

    tiers = TITLE_TIERS.get(title_id, [])
    tier_name  = "Untitled"
    next_req   = tiers[0].required if tiers else 0

    for tier in tiers:
        if current >= tier.required:
            tier_name = tier.name
            next_req  = 0
        else:
            next_req = tier.required
            break

    return current, tier_name, next_req


_TONIC_SICKNESS_EFFECT_ID = 3402  # "Tonic Tipsiness" -- blocks reuse of normal tonics

_TRANSACTION_TIMEOUT_MS = 5000


@dataclass
class CollectorExchange:
    name:             str  # display name shown in UI
    give_model_id:    int  # item you hand in
    receive_model_id: int  # item you receive
    exchange_rate:    int  # give items required per receive item


# Lunar Fortune model IDs follow the 12-year zodiac cycle.
# The sequence below is anchored to 2026 (Horse) per the in-game calendar.
_LUNAR_FORTUNE_CYCLE: List[int] = [
    ModelID.Lunar_Fortune_2014_Horse.value,    # Horse   -- 2026, 2038 ...
    ModelID.Lunar_Fortune_2015_Sheep.value,    # Sheep   -- 2027, 2039 ...
    ModelID.Lunar_Fortune_2016_Monkey.value,   # Monkey  -- 2028, 2040 ...
    ModelID.Lunar_Fortune_2017_Rooster.value,  # Rooster -- 2029, 2041 ...
    ModelID.Lunar_Fortune_2018_Dog.value,      # Dog     -- 2030, 2042 ...
    ModelID.Lunar_Fortune_2007_Pig.value,      # Pig     -- 2031, 2043 ...
    ModelID.Lunar_Fortune_2008_Rat.value,      # Rat     -- 2032, 2044 ...
    ModelID.Lunar_Fortune_2009_Ox.value,       # Ox      -- 2033, 2045 ...
    ModelID.Lunar_Fortune_2010_Tiger.value,    # Tiger   -- 2034, 2046 ...
    ModelID.Lunar_Fortune_2011_Rabbit.value,   # Rabbit  -- 2035, 2047 ...
    ModelID.Lunar_Fortune_2012_Dragon.value,   # Dragon  -- 2036, 2048 ...
    ModelID.Lunar_Fortune_2013_Snake.value,    # Snake   -- 2037, 2049 ...
]

def _lunar_fortune_model_id() -> int:
    """Return the Lunar Fortune model ID for the current calendar year."""
    return _LUNAR_FORTUNE_CYCLE[(time.localtime().tm_year - 2026) % 12]


_COLLECTOR_EXCHANGES: List[CollectorExchange] = [
    CollectorExchange("Confessor's Orders", 35123, 35121, 3),
    CollectorExchange("Lunar Tokens", ModelID.Lunar_Token.value, _lunar_fortune_model_id(), 3),
]


def eat_items(model_id: int, quantity: int):
    for _ in range(quantity):
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if item_id:
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            yield from Routines.Yield.wait(50)


def eat_tonic(model_id: int, quantity: int):
    """Like eat_items but waits for Tonic Tipsiness to clear between each use."""
    me_id = Player.GetAgentID()
    for _ in range(quantity):
        while GLOBAL_CACHE.Effects.HasEffect(me_id, _TONIC_SICKNESS_EFFECT_ID):
            yield from Routines.Yield.wait(500)
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if item_id:
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            yield from Routines.Yield.wait(100)


def use_to_max(items: List[Tuple[str, int, int]], title_id: int, consume_fn=None):
    """Use items to reach the next title tier, starting with the highest point value.

    *consume_fn* defaults to eat_items.  Pass eat_tonic for gated items (tonics).
    """
    if consume_fn is None:
        consume_fn = eat_items

    current, _, next_req = _get_title_info(title_id)
    if next_req == 0:
        ConsoleLog(MODULE_NAME, "Title already maxed.", Py4GW.Console.MessageType.Info)
        return

    points_needed = next_req - current
    if points_needed <= 0:
        return

    sorted_items = sorted(
        [(model_id, pts) for _, model_id, pts in items if pts > 0],
        key=lambda x: x[1],
        reverse=True,
    )

    for model_id, pts in sorted_items:
        if points_needed <= 0:
            break
        count = _count_item(model_id)
        if count == 0:
            continue
        to_use = min(count, math.ceil(points_needed / pts))
        yield from consume_fn(model_id, to_use)
        points_needed -= to_use * pts

    ConsoleLog(MODULE_NAME, "Use to max complete.", Py4GW.Console.MessageType.Info)


def exchange_pumpkins_for_pie(quantity: int):
    for _ in range(quantity):
        target = Player.GetTargetID()
        Player.Interact(target, False)
        yield from Routines.Yield.wait(250)
        UIManager.ClickDialogButton(int(2))
        yield from Routines.Yield.wait(100)
        UIManager.ClickDialogButton(int(1))
        yield from Routines.Yield.wait(100)

# (display name, model_id, points_per_use)
_SWEETS: List[Tuple[str, int, int]] = [
    ("Creme Brulee",          ModelID.Creme_Brulee.value,          3),
    ("Chocolate Bunny",       ModelID.Chocolate_Bunny.value,       2),
    ("Delicious Cake",        ModelID.Delicious_Cake.value,        50),
    ("Fruitcake",             ModelID.Fruitcake.value,             1),
    ("Jar of Honey",          ModelID.Jar_Of_Honey.value,          2),
    ("Krytan Lokum",          ModelID.Krytan_Lokum.value,          3),
    ("Mandragor Root Cake",   ModelID.Mandragor_Root_Cake.value,   1),
    ("Minitreat of Purity",   ModelID.Minitreat_Of_Purity.value,   3),
    ("Red Bean Cake",         ModelID.Red_Bean_Cake.value,         2),
    ("Sugary Blue Drink",     ModelID.Sugary_Blue_Drink.value,     1),
]

_PARTY_SPAMMABLE: List[Tuple[str, int, int]] = [
    ("Bottle Rocket",    ModelID.Bottle_Rocket.value,    1),
    ("Champagne Popper", ModelID.Champagne_Popper.value, 1),
    ("Ghost-in-the-Box", ModelID.Ghost_In_The_Box.value, 1),
    ("Snowman Summoner", ModelID.Snowman_Summoner.value,  1),
    ("Sparkler",         ModelID.Sparkler.value,          1),
    ("Squash Serum",     ModelID.Squash_Serum.value,      1),
]

_PARTY_SPAMMABLE_TONICS: List[Tuple[str, int, int]] = [
    ("Minutely Mad King Tonic", ModelID.Minutely_Mad_King_Tonic.value, 3),
    ("Transmogrifier Tonic",    ModelID.Transmogrifier_Tonic.value,    2),
    ("Yuletide Tonic",          ModelID.Yuletide_Tonic.value,          2),
    ("Zaishen Tonic",           ModelID.Zaishen_Tonic.value,           3),
]

_PARTY_NORMAL_TONICS: List[Tuple[str, int, int]] = [
    ("Abominable Tonic",           ModelID.Abominable_Tonic.value,           2),
    ("Abyssal Tonic",              ModelID.Abyssal_Tonic.value,              2),
    ("Automatonic Tonic",          ModelID.Automatonic_Tonic.value,          2),
    ("Beetle Juice Tonic",         ModelID.Beetle_Juice_Tonic.value,         2),
    ("Boreal Tonic",               ModelID.Boreal_Tonic.value,               2),
    ("Cerebral Tonic",             ModelID.Cerebral_Tonic.value,             2),
    ("Cottontail Tonic",           ModelID.Cottontail_Tonic.value,           2),
    ("Frosty Tonic",               ModelID.Frosty_Tonic.value,               2),
    ("Gelatinous Tonic",           ModelID.Gelatinous_Tonic.value,           2),
    ("Macabre Tonic",              ModelID.Macabre_Tonic.value,              2),
    ("Mischievous Tonic",          ModelID.Mischievious_Tonic.value,         2),
    ("Mysterious Tonic",           ModelID.Mysterious_Tonic.value,           3),
    ("Phantasmal Tonic",           ModelID.Phantasmal_Tonic.value,           2),
    ("Searing Tonic",              ModelID.Searing_Tonic.value,              2),
    ("Sinister Automatonic Tonic", ModelID.Sinister_Automatonic_Tonic.value, 2),
    ("Spooky Tonic",               ModelID.Spooky_Tonic.value,               25),
    ("Skeletonic Tonic",           ModelID.Skeletonic_Tonic.value,           2),
    ("Trapdoor Tonic",             ModelID.Trapdoor_Tonic.value,             2),
    ("Unseen Tonic",               ModelID.Unseen_Tonic.value,               2),
]

_ALCOHOL: List[Tuple[str, int, int]] = [
    ("Aged Dwarven Ale",        ModelID.Aged_Dwarven_Ale.value,        3),
    ("Aged Hunter's Ale",       ModelID.Aged_Hunters_Ale.value,        3),
    ("Battle Isle Iced Tea",    ModelID.Battle_Isle_Iced_Tea.value,    50),
    ("Bottle of Grog",          ModelID.Bottle_Of_Grog.value,          3),
    ("Bottle of Juniberry Gin", ModelID.Bottle_Of_Juniberry_Gin.value, 1),
    ("Bottle of Rice Wine",     ModelID.Bottle_Of_Rice_Wine.value,     1),
    ("Bottle of Vabbian Wine",  ModelID.Bottle_Of_Vabbian_Wine.value,  1),
    ("Dwarven Ale",             ModelID.Dwarven_Ale.value,             1),
    ("Eggnog",                  ModelID.Eggnog.value,                  1),
    ("Flask of Firewater",      ModelID.Flask_Of_Firewater.value,      3),
    ("Hard Apple Cider",        ModelID.Hard_Apple_Cider.value,        1),
    ("Hunter's Ale",            ModelID.Hunters_Ale.value,             1),
    ("Keg of Hunter's Ale",     ModelID.Keg_Of_Aged_Hunters_Ale.value, 3),
    ("Krytan Brandy",           ModelID.Krytan_Brandy.value,           3),
    ("Shamrock Ale",            ModelID.Shamrock_Ale.value,            1),
    ("Spiked Eggnog",           ModelID.Spiked_Eggnog.value,           3),
    ("Vial of Absinthe",        ModelID.Vial_Of_Absinthe.value,        1),
    ("Witch's Brew",            ModelID.Witchs_Brew.value,             1),
]

_GIFTS: List[Tuple[str, int, int]] = [
    ("Birthday Present",                ModelID.Birthday_Present.value,             0),
    ("Champion's Zaishen Strongbox",    ModelID.Champions_Zaishen_Strongbox.value,  0),
    ("Coffer of Whispers",              ModelID.Coffer_Of_Whispers.value,           0),
    ("Festival Prize",                  ModelID.Festival_Prize.value,               0),
    ("Gift of the Huntsman",            ModelID.Gift_Of_The_Huntsman.value,         0),
    ("Gift of the Traveler",            ModelID.Gift_Of_The_Traveller.value,        0),
    ("Gladiator's Zaishen Strongbox",   ModelID.Gladiators_Zaishen_Strongbox.value, 0),
    ("Hero's Zaishen Strongbox",        ModelID.Heros_Zaishen_Strongbox.value,      0),
    ("Imperial Guard Lockbox",          ModelID.Imperial_Guard_Lockbox.value,       0),
    ("Paper Wrapped Parcel",            ModelID.Paper_Wrapped_Parcel.value,         0),
    ("Red Gift Bag",                    ModelID.Red_Gift_Bag.value,                 0),
    ("Royal Gift",                      ModelID.Royal_Gift.value,                   0),
    ("Sack of Random Junk",             ModelID.Sack_Of_Random_Junk.value,          0),
    ("Strategist's Zaishen Strongbox",  ModelID.Strategists_Zaishen_Strongbox.value,0),
    ("Trick-or-Treat Bag",              ModelID.Trick_Or_Treat_Bag.value,           0),
    ("Wintersday Gift",                 ModelID.Wintersday_Gift.value,              0),
    # TODO: Add 3 Zaishen Decade Chests once added to ModelID enum
]

_PARTY_SUBS = [
    ("Spammable",        _PARTY_SPAMMABLE),
    ("Spammable Tonics", _PARTY_SPAMMABLE_TONICS),
    ("Normal Tonics",    _PARTY_NORMAL_TONICS),
]

# (label, items, title_id or None, sub_sections or None)
_CATEGORIES: List[Tuple[str, List, Optional[int], Optional[List]]] = [
    ("Sweets",          _SWEETS,   TitleID.Sweet_Tooth, None),
    ("Party",           [],        TitleID.PartyAnimal,  _PARTY_SUBS),
    ("Alcohol",         _ALCOHOL,  TitleID.Drunkard,     None),
    ("Gift Containers", _GIFTS,    None,                 None),
]


def _format_duration(seconds: int) -> str:
    """Format a duration in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m {s}s" if s else f"{m}m"
    h, m = divmod(m, 60)
    return f"{h}h {m}m" if m else f"{h}h"


def _pack_color(r: float, g: float, b: float, a: float) -> int:
    """Pack RGBA floats (0.0-1.0) into an ImGui color int."""
    return (int(a * 255) << 24) | (int(b * 255) << 16) | (int(g * 255) << 8) | int(r * 255)

_PROGRESS_COLOR_T0 = _pack_color(0.40, 0.75, 1.00, 0.45)  # light blue  — tier 0 → 1
_PROGRESS_COLOR_T1 = _pack_color(0.30, 0.85, 0.40, 0.45)  # light green — tier 1 → 2
_PROGRESS_COLOR_T2 = _pack_color(0.85, 0.70, 0.10, 0.55)  # gold        — maxed


def _draw_progress_overlay(current: int, next_req: int, title_id: int) -> None:
    """Overlay a left-to-right fill on the last drawn header based on within-tier progress.

    Color changes per tier:  light blue → light green → gold (maxed).
    The bar resets at each tier boundary and fills within the current tier.
    """
    tiers = TITLE_TIERS.get(title_id, [])
    if not tiers:
        return

    # Find which tier we are currently in and the boundaries for that tier
    tier_start = 0
    tier_end   = tiers[0].required
    color      = _PROGRESS_COLOR_T0

    for i, tier in enumerate(tiers):
        if current >= tier.required:
            if i + 1 < len(tiers):
                tier_start = tier.required
                tier_end   = tiers[i + 1].required
                color      = _PROGRESS_COLOR_T1
            else:
                # Maxed — full bar in gold
                tier_start = tiers[-1].required
                tier_end   = tiers[-1].required
                color      = _PROGRESS_COLOR_T2

    t = 1.0 if tier_end == tier_start else min(1.0, (current - tier_start) / max(1, tier_end - tier_start))
    if t <= 0.0:
        return

    min_x, min_y = PyImGui.get_item_rect_min()
    max_x, max_y = PyImGui.get_item_rect_max()
    fill_x = min_x + (max_x - min_x) * t
    PyImGui.draw_list_add_rect_filled(min_x, min_y, fill_x, max_y, color, 0.0, 0)


def _draw_smart_title(
    label: str,
    items: List[Tuple[str, int, int]],
    title_id: int,
    sub_sections: Optional[List[Tuple[str, List[Tuple[str, int, int]]]]] = None,
) -> None:
    """Draw collapsing header with title progress overlay and Smart Title Max button(s)."""
    all_items = [i for entry in sub_sections for i in entry[1]] if sub_sections else items
    total_in_category = sum(_count_item(model_id) for _, model_id, _ in all_items)

    current, tier_name, next_req = _get_title_info(title_id)
    maxed = next_req == 0
    progress_str = f"  |  !!! {tier_name} !!!" if maxed else f"  |  {current:,} / {next_req:,}"
    expanded = PyImGui.collapsing_header(f"{label}  ({total_in_category} total){progress_str}###smart_{label}")
    _draw_progress_overlay(current, next_req, title_id)

    if not expanded:
        return

    PyImGui.indent(8.0)

    if maxed:
        PyImGui.text("Title maxed!")
    elif sub_sections:
        for sub_label, sub_items in sub_sections:
            consume_fn = eat_tonic if sub_label == "Normal Tonics" else eat_items
            sub_total = sum(_count_item(model_id) for _, model_id, _ in sub_items)
            if sub_total == 0:
                continue

            if sub_label == "Spammable Tonics":
                PyImGui.text("  These tonics must be used at Zinn's Laboratory.")
                PyImGui.text("  Loose Magic will make spamming much faster.")
            elif sub_label == "Normal Tonics":
                _nt_needed = next_req - current
                _nt_count  = 0
                if _nt_needed > 0:
                    for _, _nt_mid, _nt_pts in sorted(
                        [(n, m, p) for n, m, p in sub_items if p > 0],
                        key=lambda x: x[2], reverse=True,
                    ):
                        if _nt_needed <= 0:
                            break
                        _nt_c = _count_item(_nt_mid)
                        if _nt_c == 0:
                            continue
                        _nt_use = min(_nt_c, math.ceil(_nt_needed / _nt_pts))
                        _nt_count  += _nt_use
                        _nt_needed -= _nt_use * _nt_pts
                _nt_time = _format_duration(_nt_count * 5)
                PyImGui.text("  Normal tonics are technically spammable but have a mandatory 5s cooldown.")
                PyImGui.text(f"  Approximate time until title maxed: {_nt_time}")

            if PyImGui.button(f"Smart Title Max -- {sub_label}##{sub_label}", PyImGui.get_content_region_avail()[0], 0):
                GLOBAL_CACHE.Coroutines.append(use_to_max(sub_items, title_id, consume_fn))
            _sub_needed = next_req - current
            for _s_name, _s_model_id, _s_pts in sorted(
                [(n, m, p) for n, m, p in sub_items if p > 0],
                key=lambda x: x[2], reverse=True,
            ):
                if _sub_needed <= 0:
                    break
                _s_count = _count_item(_s_model_id)
                if _s_count == 0:
                    continue
                _s_use = min(_s_count, math.ceil(_sub_needed / _s_pts))
                PyImGui.text(f"  {_s_name}: {_s_use}")
                _sub_needed -= _s_use * _s_pts
            PyImGui.spacing()
    else:
        if PyImGui.button(f"Smart Title Max##smart_{label}", PyImGui.get_content_region_avail()[0], 0):
            GLOBAL_CACHE.Coroutines.append(use_to_max(items, title_id))
        _needed = next_req - current
        for _name, _mid, _pts in sorted(
            [(n, m, p) for n, m, p in items if p > 0],
            key=lambda x: x[2], reverse=True,
        ):
            if _needed <= 0:
                break
            _c = _count_item(_mid)
            if _c == 0:
                continue
            _use = min(_c, math.ceil(_needed / _pts))
            PyImGui.text(f"  {_name}: {_use}")
            _needed -= _use * _pts

    PyImGui.unindent(8.0)


def _draw_precise_section(
    label: str,
    items: List[Tuple[str, int, int]],
    sub_sections: Optional[List[Tuple[str, List[Tuple[str, int, int]]]]] = None,
) -> None:
    """Draw collapsing header with per-item consume buttons for one category."""
    all_items = [i for entry in sub_sections for i in entry[1]] if sub_sections else items
    total = sum(_count_item(model_id) for _, model_id, _ in all_items)
    if total == 0:
        return

    if not PyImGui.collapsing_header(f"{label}  ({total} total)###eat_{label}"):
        return

    PyImGui.indent(8.0)

    if sub_sections:
        for sub_label, sub_items in sub_sections:
            consume_fn = eat_tonic if sub_label == "Normal Tonics" else eat_items
            sub_total = sum(_count_item(model_id) for _, model_id, _ in sub_items)
            if sub_total == 0:
                continue
            PyImGui.text(f"[ {sub_label} ]")
            for name, model_id, pts in sub_items:
                count = _count_item(model_id)
                if count == 0:
                    continue
                point_str = f"  [{count * pts:,} pts]" if pts > 0 else ""
                PyImGui.text(f"{name}: {count}{point_str}")
                PyImGui.same_line(0.0, 8.0)
                if PyImGui.button(f"Consume {quantity_to_consume}##{name}"):
                    GLOBAL_CACHE.Coroutines.append(consume_fn(model_id, quantity_to_consume))
                PyImGui.same_line(0.0, 4.0)
                if PyImGui.button(f"Consume All ({count})##{name}_all"):
                    GLOBAL_CACHE.Coroutines.append(consume_fn(model_id, count))
            PyImGui.spacing()
    else:
        for name, model_id, pts in items:
            count = _count_item(model_id)
            if count == 0:
                continue
            point_str = f"  [{count * pts:,} pts]" if pts > 0 else ""
            PyImGui.text(f"{name}: {count}{point_str}")
            PyImGui.same_line(0.0, 8.0)
            if PyImGui.button(f"Consume {quantity_to_consume}##{name}"):
                GLOBAL_CACHE.Coroutines.append(eat_items(model_id, quantity_to_consume))
            PyImGui.same_line(0.0, 4.0)
            if PyImGui.button(f"Consume All ({count})##{name}_all"):
                GLOBAL_CACHE.Coroutines.append(eat_items(model_id, count))

    PyImGui.unindent(8.0)


def _get_item_stacks(model_id: int) -> List[Tuple[int, int]]:
    """Return all (item_id, quantity) pairs for the given model across all inventory bags."""
    stacks: List[Tuple[int, int]] = []
    for bag_id in (1, 2, 3, 4):
        try:
            bag = PyInventory.Bag(bag_id, f"Bag_{bag_id}")
            for bag_item in bag.GetItems():
                if int(getattr(bag_item, "model_id", 0) or 0) == model_id:
                    item_id = int(getattr(bag_item, "item_id", 0) or 0)
                    qty     = int(getattr(bag_item, "quantity", 0) or 0)
                    if item_id > 0 and qty > 0:
                        stacks.append((item_id, qty))
        except Exception:
            pass
    return stacks


def _build_turn_in(stacks: List[Tuple[int, int]], needed: int) -> Tuple[List[int], List[int]]:
    """Build give_ids / give_qtys to satisfy 'needed' items, drawing across stacks as required.
    Returns empty lists if the total across all stacks is insufficient."""
    give_ids:  List[int] = []
    give_qtys: List[int] = []
    remaining = needed
    for item_id, qty in stacks:
        if remaining <= 0:
            break
        take = min(qty, remaining)
        if take > 0:
            give_ids.append(item_id)
            give_qtys.append(take)
            remaining -= take
    if remaining > 0:
        return [], []
    return give_ids, give_qtys


def _run_exchange(exchange: CollectorExchange):
    """Generic collector exchange coroutine -- requires the collector dialog to already be open."""
    offered = GLOBAL_CACHE.Trading.Collector.GetOfferedItems() or []
    receive_item_id = next((iid for iid in offered if Item.GetModelID(iid) == exchange.receive_model_id), 0)
    if receive_item_id == 0:
        ConsoleLog(MODULE_NAME,
                   f"[{exchange.name}] Receive item not found in collector offers -- open the collector dialog first.",
                   Py4GW.Console.MessageType.Warning)
        return

    stacks = _get_item_stacks(exchange.give_model_id)
    total  = sum(qty for _, qty in stacks)
    ConsoleLog(MODULE_NAME,
               f"[{exchange.name}] Starting: {total} -> {total // exchange.exchange_rate}",
               Py4GW.Console.MessageType.Info)

    while True:
        stacks = _get_item_stacks(exchange.give_model_id)
        give_ids, give_qtys = _build_turn_in(stacks, exchange.exchange_rate)
        if not give_ids:
            break
        GLOBAL_CACHE.Trading.Collector.ExghangeItem(receive_item_id, 0, give_ids, give_qtys)
        elapsed = 0
        while not GLOBAL_CACHE.Trading.IsTransactionComplete() and elapsed < _TRANSACTION_TIMEOUT_MS:
            yield from Routines.Yield.wait(100)
            elapsed += 100
        yield from Routines.Yield.wait(200)

    ConsoleLog(MODULE_NAME, f"[{exchange.name}] Exchange complete.", Py4GW.Console.MessageType.Info)


def _draw_exchanges_tab() -> None:
    """Draw the Exchange NPCs tab -- items that require interacting with an NPC."""
    any_shown = False

    # Collector exchanges (requires collector dialog to be open)
    for exchange in _COLLECTOR_EXCHANGES:
        stacks    = _get_item_stacks(exchange.give_model_id)
        total     = sum(qty for _, qty in stacks)
        if total == 0:
            continue
        any_shown = True
        yield_count = total // exchange.exchange_rate
        PyImGui.text(f"{exchange.name} : {total}")
        PyImGui.text(f"Yield : {yield_count}")
        if yield_count > 0:
            if PyImGui.button(f"Exchange All##{exchange.name}", PyImGui.get_content_region_avail()[0], 0):
                GLOBAL_CACHE.Coroutines.append(_run_exchange(exchange))
        else:
            PyImGui.text(f"(need at least {exchange.exchange_rate})")
        PyImGui.spacing()

    # Pumpkin Cookie -> Pie
    pumpkin_count = _count_item(ModelID.Pumpkin_Cookie.value)
    if pumpkin_count > 0:
        any_shown = True
        PyImGui.text(f"Pumpkin Cookie: {pumpkin_count}")
        PyImGui.same_line(0.0, 8.0)
        if PyImGui.button("exchange for pie"):
            GLOBAL_CACHE.Coroutines.append(exchange_pumpkins_for_pie(quantity_to_consume))

    if not any_shown:
        PyImGui.text("No exchangeable items in inventory.")


def main():
    global quantity_to_consume

    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.begin_tab_bar("##ItemEaterTabs"):

            if PyImGui.begin_tab_item("Smart Titles"):
                for label, items, title_id, sub_sections in _CATEGORIES:
                    if title_id is None:
                        continue
                    _draw_smart_title(label, items, title_id, sub_sections)
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Precise Consumption"):
                quantity_to_consume = PyImGui.input_int("Quantity", quantity_to_consume)
                PyImGui.separator()
                any_items = any(
                    _count_item(model_id) > 0
                    for _, items, _, sub_sections in _CATEGORIES
                    for _, model_id, _ in ([i for e in sub_sections for i in e[1]] if sub_sections else items)
                )
                if any_items:
                    for label, items, title_id, sub_sections in _CATEGORIES:
                        _draw_precise_section(label, items, sub_sections)
                else:
                    PyImGui.text("No applicable consumables in inventory.")
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Exchange NPCs"):
                _draw_exchanges_tab()
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    PyImGui.end()


def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Item Eater", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text("A utility for consuming and managing in-game items")
    PyImGui.spacing()
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    PyImGui.bullet_text("Contributors: LeZgw")

    PyImGui.end_tooltip()


if __name__ == "__main__":
    main()

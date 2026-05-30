from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]


class _StripRelativeImports(ast.NodeTransformer):
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.level:
            return None
        return node


def _load_methods(path: Path, class_name: str, method_names: set[str], globals_: dict):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    source_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    methods = [
        _StripRelativeImports().visit(node)
        for node in source_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in method_names
    ]
    class_node = ast.ClassDef(
        name=class_name,
        bases=[],
        keywords=[],
        decorator_list=[],
        body=methods,
    )
    module = ast.fix_missing_locations(ast.Module(body=[class_node], type_ignores=[]))
    namespace = dict(globals_)
    exec(compile(module, str(path), 'exec'), namespace)
    return namespace[class_name]


def _drain(generator):
    while True:
        try:
            next(generator)
        except StopIteration as stop:
            return stop.value


def _wait(_milliseconds):
    yield None


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _test_buy_material_waits_for_requested_offer() -> None:
    offer_reads = {'count': 0}
    quoted_items: list[int] = []
    purchases: list[tuple[int, int]] = []
    logs: list[str] = []

    def _get_offered_items():
        offer_reads['count'] += 1
        if offer_reads['count'] < 3:
            return []
        return [501, 502]

    cache = SimpleNamespace(
        Item=SimpleNamespace(GetModelID=lambda item_id: {501: 946, 502: 940}.get(int(item_id), 0)),
        Trading=SimpleNamespace(
            Trader=SimpleNamespace(
                GetOfferedItems=_get_offered_items,
                GetQuotedItemID=lambda: 502,
                GetQuotedValue=lambda: 125,
                RequestQuote=lambda item_id: quoted_items.append(int(item_id)),
                BuyItem=lambda item_id, cost: purchases.append((int(item_id), int(cost))),
            ),
            IsTransactionComplete=lambda: True,
        ),
    )
    merchant = _load_methods(
        ROOT / 'Py4GWCoreLib/routines_src/yield_src/merchant.py',
        'Merchant',
        {
            '_get_trader_batch_size',
            '_wait_for_trader_item',
            '_wait_for_quote',
            '_wait_for_transaction',
            'BuyMaterial',
        },
        {
            'GLOBAL_CACHE': cache,
            'ModelID': SimpleNamespace(Wood_Plank=SimpleNamespace(value=946)),
            'Console': SimpleNamespace(MessageType=SimpleNamespace(Warning='warning', Success='success')),
            'ConsoleLog': lambda _module, message, _level: logs.append(message),
            'wait': _wait,
        },
    )

    result = _drain(merchant.BuyMaterial(940))

    _expect(result is True, 'BuyMaterial should wait for the requested trader offer.')
    _expect(offer_reads['count'] >= 3, 'BuyMaterial should retry while trader offers are still loading.')
    _expect(quoted_items == [502], 'BuyMaterial should quote the resolved trader item.')
    _expect(purchases == [(502, 125)], 'BuyMaterial should buy the resolved trader item.')


def _test_craft_item_waits_for_requested_offer() -> None:
    offer_reads = {'count': 0}
    crafts: list[tuple[int, int, list[int], list[int]]] = []

    def _get_offered_items():
        offer_reads['count'] += 1
        if offer_reads['count'] < 3:
            return [700]
        return [900]

    cache = SimpleNamespace(
        Inventory=SimpleNamespace(GetFirstModelID=lambda model_id: {940: 41, 929: 42}.get(int(model_id), 0)),
        Item=SimpleNamespace(GetModelID=lambda item_id: {700: 940, 900: 17777}.get(int(item_id), 0)),
        Trading=SimpleNamespace(
            Merchant=SimpleNamespace(GetOfferedItems=_get_offered_items),
            Crafter=SimpleNamespace(
                CraftItem=lambda item_id, cost, trade_items, quantities: crafts.append(
                    (int(item_id), int(cost), list(trade_items), list(quantities))
                )
            ),
        ),
    )
    items = _load_methods(
        ROOT / 'Py4GWCoreLib/routines_src/yield_src/items.py',
        'Items',
        {'_wait_for_crafter_item', 'CraftItem'},
        {
            'GLOBAL_CACHE': cache,
            'wait': _wait,
        },
    )

    result = _drain(items.CraftItem(17777, 75, [940, 929], [2, 2]))

    _expect(result is True, 'CraftItem should wait for the requested crafter offer.')
    _expect(offer_reads['count'] >= 3, 'CraftItem should ignore stale offers while the crafter window is loading.')
    _expect(crafts == [(900, 75, [41, 42], [2, 2])], 'CraftItem should dispatch the resolved armor craft.')


def main() -> None:
    _test_buy_material_waits_for_requested_offer()
    _test_craft_item_waits_for_requested_offer()
    print('yield offer wait regression checks passed')


if __name__ == '__main__':
    main()

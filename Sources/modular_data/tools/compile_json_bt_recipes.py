"""
Compile every modular JSON recipe with the canonical JSON-to-BT compiler.

This imports Py4GWCoreLib runtime modules, so it is expected to run in an
environment where the Py4GW bindings are importable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Root folder containing modular JSON recipes.",
    )
    args = parser.parse_args(argv)

    try:
        from Py4GWCoreLib.modular.json_bt_compiler import compile_recipe_to_bt
    except ModuleNotFoundError as exc:
        print(f"Cannot import Py4GW runtime bindings: {exc}")
        return 2

    failures: list[str] = []
    compiled = 0
    for path in sorted(args.root.rglob("*.json")):
        try:
            recipe = json.loads(path.read_text(encoding="utf-8-sig"))
            compile_recipe_to_bt(recipe, recipe_name=str(recipe.get("name", path.stem)))
            compiled += 1
        except Exception as exc:
            failures.append(f"{path}: {type(exc).__name__}: {exc}")

    if failures:
        print(f"Compiled {compiled} recipe(s), {len(failures)} failure(s):")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(f"Compiled {compiled} recipe(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

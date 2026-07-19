"""Reforged Mission Assistant behavior-tree entry point."""

from __future__ import annotations

from Py4GWCoreLib.BottingTree import BottingTree
from Sources.RootTerm import ui as rma_ui
from Sources.RootTerm.bt_runner import build_execution_steps
from Sources.RootTerm.options import OPTIONS

MODULE_NAME = 'Reforged Mission Assistant'

botting_tree: BottingTree | None = None
_last_build_key: tuple | None = None


def ensure_botting_tree() -> BottingTree:
    global botting_tree
    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            pause_on_combat=True,
            multi_account=False,
            auto_loot=True,
            isolation_enabled=True,
        )
        botting_tree.SetMainRoutine(
            build_execution_steps(botting_tree),
            name='Mission Queue',
            repeat=False,
            reset=True,
        )
        botting_tree.UI.override_draw_texture(lambda: None)
    return botting_tree


def _rebuild_if_selection_changed(tree: BottingTree) -> None:
    global _last_build_key
    key = OPTIONS.selection_key()
    if _last_build_key == key:
        return
    if tree.IsStarted():
        return

    tree.SetMainRoutine(
        build_execution_steps(tree),
        name='Mission Queue',
        repeat=False,
        reset=True,
    )
    _last_build_key = key


def main() -> None:
    tree = ensure_botting_tree()
    _rebuild_if_selection_changed(tree)
    tree.tick()
    tree.UI.draw_window(
        main_child_dimensions=(380, 320),
        iconwidth=0,
        additional_ui=rma_ui.draw_main_summary,
        extra_tabs=[('Missions', rma_ui.draw_missions_tab)],
    )


if __name__ == '__main__':
    main()

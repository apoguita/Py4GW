"""
BT routines support file notes
==============================

This file is both:
- part of the BT routines support layer
- shared helper code used by other BT routine groups

Authoring and discovery conventions
-----------------------------------
- Keep existing class names as the system-level grouping surface.
- Use `PascalCase` for public/front-facing routine methods.
- Use `snake_case` for helper/internal methods.
- Use `_snake_case` for explicitly private helpers.
- Treat this file as support code rather than a primary discovery surface.

Routine docstring template
--------------------------
Each routine docstring should use:
- a free human-readable description first
- a structured `Meta:` block after it

Template:

    \"\"\"
    One or more human-readable paragraphs explaining what the routine builds.

    Meta:
      Expose: false
      Audience: advanced
      Display: Internal Sequence Helper
      Purpose: Support other BT routine builders.
      UserDescription: Internal support routine.
      Notes: Keep metadata single-line. Structural truth should stay in code.
    \"\"\"

Docstring parsing rules
-----------------------
- Only the `Meta:` section is intended for machine parsing.
- Keep metadata lines single-line and in `Key: Value` form.
- Unknown keys should be safe for tooling to ignore.
- Prefer adding presentation/help metadata in docstrings instead of duplicating
  structural metadata that already exists in code.
"""

from __future__ import annotations

from typing import Callable

from ...py4gwcorelib_src.BehaviorTree import BehaviorTree


class BTCompositeHelpers:
    """
    Internal helper layer for composite BT routine builders.

    This module exists to keep private builder/composition helpers physically
    separated from the user-facing `BT.*` routines surface.

    Meta:
      Expose: false
      Audience: advanced
      Display: Internal Composite Helpers
      Purpose: Hold support-only builder helpers used by BT composite support routines.
      UserDescription: Internal support helper class.
      Notes: This class is not intended for configurator discovery and exists only to support other BT helpers.
    """

    SequenceBuildable = Callable[[], BehaviorTree | BehaviorTree.Node] | BehaviorTree | BehaviorTree.Node

    @staticmethod
    def as_tree(subtree: BehaviorTree | BehaviorTree.Node) -> BehaviorTree:
        """
        Convert a node-or-tree input into a `BehaviorTree` wrapper.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal As Tree Helper
          Purpose: Normalize a node or tree value into a behavior tree instance.
          UserDescription: Internal support routine.
          Notes: Wraps raw nodes in `BehaviorTree` and raises when the value is not tree-compatible.
        """
        if isinstance(subtree, BehaviorTree):
            return subtree
        if isinstance(subtree, BehaviorTree.Node):
            return BehaviorTree(subtree)
        raise TypeError("Composite helpers expect a BehaviorTree or BehaviorTree.Node.")

    @staticmethod
    def resolve_subtree_factory(
        subtree_or_builder: SequenceBuildable,
    ) -> BehaviorTree:
        """
        Resolve a subtree input that may already be a tree or may need to be built first.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Resolve Subtree Factory Helper
          Purpose: Normalize direct subtree values and callable subtree builders into a behavior tree instance.
          UserDescription: Internal support routine.
          Notes: Calls the builder when needed and then delegates normalization to `as_tree`.
        """
        subtree = subtree_or_builder() if callable(subtree_or_builder) else subtree_or_builder
        return BTCompositeHelpers.as_tree(subtree)

    @staticmethod
    def move_and_target(move_tree: BehaviorTree, target_tree: BehaviorTree) -> BehaviorTree:
        """
        Build an internal support sequence that moves first and then targets.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Move And Target Helper
          Purpose: Compose a move routine and a target routine into a support sequence.
          UserDescription: Internal support routine.
          Notes: Uses the non-front-facing composite sequence helper and is not intended for direct discovery.
        """
        from ..BehaviourTrees import BT

        return BT.Composite.Sequence(
            move_tree,
            target_tree,
            name="MoveAndTarget",
        )

    @staticmethod
    def target_and_interact(target_tree: BehaviorTree, log: bool = False) -> BehaviorTree:
        """
        Build an internal support sequence that targets first and then interacts.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Target And Interact Helper
          Purpose: Compose a target routine and an interact routine into a support sequence.
          UserDescription: Internal support routine.
          Notes: Reuses `BT.Player.InteractTarget` after the provided target routine completes.
        """
        from ..BehaviourTrees import BT

        return BT.Composite.Sequence(
            target_tree,
            BT.Player.InteractTarget(log=log),
            name="TargetAndInteract",
        )

    @staticmethod
    def move_target_and_interact(
        move_tree: BehaviorTree,
        target_tree: BehaviorTree,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build an internal support sequence that moves, targets, and then interacts.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Move Target And Interact Helper
          Purpose: Compose move, target, and interact routines into a support sequence.
          UserDescription: Internal support routine.
          Notes: Reuses the support composite sequence helper and keeps this composition out of the public catalog.
        """
        from ..BehaviourTrees import BT

        return BT.Composite.Sequence(
            move_tree,
            target_tree,
            BT.Player.InteractTarget(log=log),
            name="MoveTargetAndInteract",
        )

    @staticmethod
    def target_interact_and_dialog(
        target_tree: BehaviorTree,
        dialog_id: str | int,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build an internal support sequence that targets, interacts, and then sends dialog.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Target Interact And Dialog Helper
          Purpose: Compose target, interact, and dialog routines into a support sequence.
          UserDescription: Internal support routine.
          Notes: Sends the provided dialog id only after the interact step completes.
        """
        from ..BehaviourTrees import BT

        return BT.Composite.Sequence(
            target_tree,
            BT.Player.InteractTarget(log=log),
            BT.Player.SendDialog(dialog_id=dialog_id, log=log),
            name="TargetInteractAndDialog",
        )

    @staticmethod
    def target_interact_and_automatic_dialog(
        target_tree: BehaviorTree,
        button_number: int,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build an internal support sequence that targets, interacts, and presses an automatic dialog button.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Target Interact And Automatic Dialog Helper
          Purpose: Compose target, interact, and automatic dialog routines into a support sequence.
          UserDescription: Internal support routine.
          Notes: Uses the automatic dialog helper after the interact step completes.
        """
        from ..BehaviourTrees import BT

        return BT.Composite.Sequence(
            target_tree,
            BT.Player.InteractTarget(log=log),
            BT.Player.SendAutomaticDialog(button_number=button_number, log=log),
            name="TargetInteractAndAutomaticDialog",
        )

    @staticmethod
    def move_target_interact_and_dialog(
        move_tree: BehaviorTree,
        target_tree: BehaviorTree,
        dialog_id: str | int,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build an internal support sequence that moves, targets, interacts, and then sends dialog.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Move Target Interact And Dialog Helper
          Purpose: Compose move, target, interact, and dialog routines into a support sequence.
          UserDescription: Internal support routine.
          Notes: Keeps dialog-enabled flow composition out of the front-facing BT catalog.
        """
        from ..BehaviourTrees import BT

        return BT.Composite.Sequence(
            move_tree,
            target_tree,
            BT.Player.InteractTarget(log=log),
            BT.Player.SendDialog(dialog_id=dialog_id, log=log),
            name="MoveTargetInteractAndDialog",
        )

    @staticmethod
    def _interact_and_automatic_dialog(
        move_tree: BehaviorTree,
        target_tree: BehaviorTree,
        button_number: int,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build an internal support sequence that moves, targets, interacts, and presses an automatic dialog button.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Move Target Interact And Automatic Dialog Helper
          Purpose: Compose move, target, interact, and automatic dialog routines into a support sequence.
          UserDescription: Internal support routine.
          Notes: Keeps automatic-dialog flow composition out of the front-facing BT catalog.
        """
        from ..BehaviourTrees import BT

        return BT.Composite.Sequence(
            move_tree,
            BT.Player.Wait(duration_ms=150, log=False),
            target_tree,
            BT.Player.InteractTarget(log=log),
            BT.Player.Wait(duration_ms=150, log=False),
            BT.Player.SendAutomaticDialog(button_number=button_number, log=log),
            name="MoveTargetInteractAndAutomaticDialog",
        )

class BTComposite:
    """
    Support BT helper group for shared sequence-building routines.

    Meta:
      Expose: false
      Audience: advanced
      Display: Internal Composite Support
      Purpose: Hold shared support routines used by other BT helper groups.
      UserDescription: Internal support helper group.
      Notes: This class is not intended to be treated as a primary discovery group.
    """
    SequenceBuildable = Callable[[], BehaviorTree | BehaviorTree.Node] | BehaviorTree | BehaviorTree.Node

    @staticmethod
    def Sequence(*subtrees: BehaviorTree | BehaviorTree.Node, name: str = "CompositeSequence") -> BehaviorTree:
        """
        Build a sequence tree from several child subtrees or nodes.

        Meta:
          Expose: false
          Audience: intermediate
          Display: Internal Sequence Helper
          Purpose: Wrap several subtrees into a support sequence routine.
          UserDescription: Internal support routine.
          Notes: Each child is wrapped as a subtree step named `Step1`, `Step2`, and so on.
        """
        children = [
            BehaviorTree.SubtreeNode(
                name=f"Step{index + 1}",
                subtree_fn=lambda node, subtree=subtree: BTCompositeHelpers.as_tree(subtree),
            )
            for index, subtree in enumerate(subtrees)
        ]
        return BehaviorTree(BehaviorTree.SequenceNode(name=name, children=children))

    @staticmethod
    def SequenceNames(steps: list[tuple[str, "BTComposite.SequenceBuildable"]]) -> list[str]:
        """
        Return the ordered step names from a named sequence definition.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Sequence Names Helper
          Purpose: Extract step names for support logic.
          UserDescription: Internal support routine.
          Notes: This is mainly a utility for restart or resume workflows built on named sequences.
        """
        return [step_name for step_name, _ in steps]

    @staticmethod
    def SequenceFrom(
        steps: list[tuple[str, "BTComposite.SequenceBuildable"]],
        start_from: str | None = None,
        name: str = "NamedSequence",
    ) -> BehaviorTree:
        """
        Build a named sequence tree from step definitions, optionally starting from a later step.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Sequence From Helper
          Purpose: Build a support sequence from named steps with optional restart from a specific step.
          UserDescription: Internal support routine.
          Notes: Raises a `ValueError` if `start_from` does not match one of the provided step names.
        """
        if not steps:
            return BehaviorTree(BehaviorTree.SequenceNode(name=name, children=[]))

        start_index = 0
        if start_from is not None:
            step_names = BTComposite.SequenceNames(steps)
            if start_from not in step_names:
                raise ValueError(f"Unknown sequence step '{start_from}'. Valid values: {', '.join(step_names)}")
            start_index = step_names.index(start_from)

        children = [
            BehaviorTree.SubtreeNode(
                name=step_name,
                subtree_fn=lambda node, subtree_or_builder=subtree_or_builder: BTCompositeHelpers.resolve_subtree_factory(subtree_or_builder),
            )
            for step_name, subtree_or_builder in steps[start_index:]
        ]
        return BehaviorTree(BehaviorTree.SequenceNode(name=name, children=children))

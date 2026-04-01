"""
BehaviorTree module notes
=========================

This file is both:
- the runtime implementation for core BehaviorTree nodes
- a discovery source for higher-level tooling

Authoring and discovery conventions
-----------------------------------
- Keep class names canonical and explicit, for example `SequenceNode`.
- Keep `node_type` equal to the class name unless there is a very strong reason not to.
- Keep the default `name` equal to the class name unless a caller overrides it.
- Use `node_category` to declare the structural family explicitly, for example
  `leaf`, `composite`, `decorator`, `repeater`, `router`, or `wait`.
- Keep runtime-only fields private with a leading underscore.
- Keep authored/configuration fields public when they are part of the node's
  intended setup surface.

Node docstring template
-----------------------
Each user-facing node class should use:
- a free human-readable description first
- a structured `Meta:` block after it

Template:

    \"\"\"
    One or more human-readable paragraphs explaining the node behavior.

    Meta:
      Expose: true
      Audience: beginner
      Display: Sequence Node
      Purpose: Execute several child nodes from first to last.
      UserDescription: Use this when steps must happen in order.
      Notes: Stops on first failure. Resumes from the running child on the next tick.
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

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Callable, List, Optional, Sequence, cast
import uuid
import inspect

import PyImGui
from .Color import Color, ColorPalette
from .Utils import Utils
from ..Py4GWcorelib import ConsoleLog, Console
from ..ImGui_src.IconsFontAwesome5 import IconsFontAwesome5


# --------------------------------------------------------
# Behavior Tree
# --------------------------------------------------------
class BehaviorTree:
    """
    Root behavior tree wrapper that owns the shared blackboard and drives the root node.

    This class is part of the parseable behavior tree foundation rather than a
    front-facing helper routine group. It wraps a root node, propagates shared
    state, and exposes tree-level lifecycle helpers such as `tick()` and
    `reset()`.

    Meta:
      Expose: true
      Audience: advanced
      Display: Behavior Tree
      Purpose: Wrap a root node and manage shared tree execution state.
      UserDescription: Use this as the root container for a behavior tree built from parseable node classes.
      Notes: Owns the shared blackboard, propagates it to descendants, and provides tree-level tick, reset, print, and draw helpers.
    """
    
    class NodeState(Enum):
        RUNNING = auto()
        SUCCESS = auto()
        FAILURE = auto()
        
    # --------------------------------------------------------
    #region Base Node
    # --------------------------------------------------------

    class Node(ABC):
        """
        Base class for all behavior tree nodes.

        This is the structural foundation for built-in node types. It provides
        the public tick wrapper, execution timing, blackboard access, and common
        tree inspection helpers. Concrete node subclasses inherit from this
        class and supply behavior through `_tick_impl()`.

        Meta:
          Expose: false
          Audience: advanced
          Display: Base Node
          Purpose: Provide shared execution, timing, and blackboard behavior for concrete node classes.
          UserDescription: Internal base class for parseable behavior tree nodes. Use concrete node subclasses instead of instantiating this directly.
          Notes: Supplies the public tick wrapper, reset behavior, child inspection helpers, and runtime metadata used by all built-in nodes.
        """

        def __init__(
            self,
            name: str = "",
            node_type: str = "",
            node_category: str = "",
            icon: str = "",
            color: Color = ColorPalette.GetColor("white"),
        ):
            self.id: str = uuid.uuid4().hex
            self.name: str = name or self.__class__.__name__
            self.node_type: str = node_type or self.__class__.__name__
            self.node_category: str = node_category
            self.icon: str = icon if icon else IconsFontAwesome5.ICON_CIRCLE
            self.color: Color = color

            self.last_state: Optional[BehaviorTree.NodeState] = None
            self.tick_count: int = 0
            self.blackboard: dict = {}

            # ---- execution timing ----
            self.last_tick_time_ms: float = 0.0
            self.total_time_ms: float = 0.0
            self.avg_time_ms: float = 0.0
            
            self._run_start_time_ms: Optional[int] = None
            self.run_last_duration_ms: float = 0.0
            self.run_accumulated_ms: float = 0.0

            
        @abstractmethod
        def _tick_impl(self) -> BehaviorTree.NodeState:
            """
            INTERNAL IMPLEMENTATION — overridden by each node.
            The public tick() wrapper measures time and updates metadata.
            """
            pass

        def tick(self) -> BehaviorTree.NodeState:
            """
            Wrapper around _tick_impl():
            - Starts timer
            - Calls child implementation
            - Ends timer
            - Updates metadata
            """
            start = Utils.GetBaseTimestamp()
            trace_enabled = bool(self.blackboard.get("BT_TRACE", False)) if isinstance(self.blackboard, dict) else False
            if trace_enabled:
                ConsoleLog("BT", f"ENTER {self.node_type}:{self.name}", Console.MessageType.Debug, log=True)

            result = self._tick_impl()   # <--- overridden in subclasses
            normalized = self._normalize_state(result)
            if normalized is None:
                raise TypeError(
                    f"{self.node_type}:{self.name} returned invalid state "
                    f"{result!r} ({type(result).__name__}); expected BehaviorTree.NodeState."
                )
            result = normalized

            end = Utils.GetBaseTimestamp()
            
            elapsed_cpu = float(end - start)
            self.last_tick_time_ms = elapsed_cpu
            self.total_time_ms += elapsed_cpu
            self.tick_count += 1
            if self.tick_count > 0:
                self.avg_time_ms = self.total_time_ms / self.tick_count
                
            # ========= REAL "LOGICAL RUNTIME" TRACKING =========
            now = Utils.GetBaseTimestamp()

            if result == BehaviorTree.NodeState.RUNNING:
                # First time entering RUNNING
                if self._run_start_time_ms is None:
                    self._run_start_time_ms = now
                # Update current duration
                self.run_last_duration_ms = now - self._run_start_time_ms

            else:
                # Node just finished (SUCCESS or FAILURE)
                if self._run_start_time_ms is not None:
                    # accumulate real active time
                    self.run_last_duration_ms = now - self._run_start_time_ms
                    self.run_accumulated_ms += self.run_last_duration_ms
                    self._run_start_time_ms = None  # reset for next activation

            self.last_state = result
            if trace_enabled:
                ConsoleLog("BT", f"EXIT  {self.node_type}:{self.name} -> {result}", Console.MessageType.Debug, log=True)
            return result

        @staticmethod
        def _normalize_state(result) -> Optional["BehaviorTree.NodeState"]:
            if isinstance(result, BehaviorTree.NodeState):
                return result
            if isinstance(result, Enum) and result.name in BehaviorTree.NodeState.__members__:
                return BehaviorTree.NodeState[result.name]
            return None

        @staticmethod
        def _coerce_node(value) -> "BehaviorTree.Node":
            if isinstance(value, BehaviorTree):
                return value.root
            if hasattr(value, "root") and hasattr(getattr(value, "root"), "tick") and hasattr(getattr(value, "root"), "get_children"):
                return value.root
            if isinstance(value, BehaviorTree.Node):
                return value
            if (
                hasattr(value, "tick")
                and hasattr(value, "reset")
                and hasattr(value, "get_children")
                and hasattr(value, "blackboard")
            ):
                return value
            raise TypeError(
                f"Expected a BehaviorTree or BehaviorTree.Node, got {type(value).__name__}."
            )

        @staticmethod
        def _coerce_children(children) -> List["BehaviorTree.Node"]:
            return [BehaviorTree.Node._coerce_node(child) for child in (children or [])]
        
        def reset(self) -> None:
            """
            Reset *transient execution state* for this node.

            Base implementation:
            - clears last_state only.
            - leaves metrics (tick_count, timings) intact so you can keep history.
            Subclasses that keep internal state (indices, timers, flags) should
            override this and call `super().reset()` first.
            """
            self.last_state = None
            # (metrics intentionally NOT reset here, unless you later decide otherwise)

    

        # --- structural helpers, used for drawing ---
        def get_children(self) -> List["BehaviorTree.Node"]:
            """
            Default: a leaf has no children.
            Composite/decorator nodes override this.
            """
            return []

        # ----- PRINT TREE -----
        def print(
            self,
            indent: int = 0,
            is_last: bool = True,
            prefix: str = ""
        ) -> List[str]:
            """
            Build a list of text lines that visually represent this node
            and its subtree as an ASCII tree.

            Example shape:

            - [SelectorNode] SelectorNode
            ├─ [ConditionNode] AlreadyInMap
            └─ [SequenceNode] TravelSequence
                ├─ [ActionNode] TravelAction
                ├─ [WaitForTimeNode] WaitForTimeNode
                └─ [WaitNode] TravelReady
            """
            # Top-level calls will typically only pass indent, so if no prefix is
            # given, derive it from indent for backward compatibility.
            if prefix == "" and indent > 0:
                prefix = "  " * (indent - 1)

            connector = "|_ " if is_last else "|- "

            state_str = self.last_state.name if self.last_state is not None else "NONE"

            line = f"{prefix}{connector}[{self.node_type}] {self.name} " \
                f"(state={state_str}, ticks={self.tick_count})"

            lines = [line]

            children = self.get_children()
            child_count = len(children)

            if child_count == 0:
                return lines

            # For children: continue the vertical bar if this node is not last,
            # otherwise just spaces.
            child_prefix_base = prefix + ("   " if is_last else "|  ")

            for idx, child in enumerate(children):
                child_is_last = (idx == child_count - 1)
                lines.extend(child.print(
                    indent=indent + 1,
                    is_last=child_is_last,
                    prefix=child_prefix_base
                ))

            return lines

        # -------- PyImGui drawing --------
        def _format_duration(self, ms: float) -> str:
            if ms is None:
                return "0 ms"

            # clamp negatives if your timer can underflow
            if ms < 0:
                ms = 0

            # milliseconds
            if ms < 1000:
                return f"{ms:.0f} ms"

            total_seconds = ms / 1000.0

            # seconds (keep decimals only in the pure-seconds range)
            if total_seconds < 60:
                return f"{total_seconds:.2f} s"

            # from here on, use integer breakdown
            s = int(total_seconds)  # floor
            minutes, seconds = divmod(s, 60)

            if minutes < 60:
                return f"{minutes}m {seconds:02d}s"

            hours, minutes = divmod(minutes, 60)
            return f"{hours}h {minutes:02d}m {seconds:02d}s"


    
        def draw(self, indent: int = 0) -> None:
            """
            Correct PyImGui tree drawing:
            - Collapsed: show only single-line label
            - Expanded: show label and children
            """

            # Choose color based on state
            if self.last_state == BehaviorTree.NodeState.SUCCESS:
                color = (0.5, 1.0, 0.5, 1.0)
            elif self.last_state == BehaviorTree.NodeState.FAILURE:
                color = (1.0, 0.5, 0.5, 1.0)
            elif self.last_state == BehaviorTree.NodeState.RUNNING:
                color = (1.0, 1.0, 0.5, 1.0)
            else:
                color = (0.3, 0.3, 0.3, 1.0)

            # ----- TREE NODE HEADER -----
            # This creates the arrow widget AND controls collapse/expand
            open_ = PyImGui.tree_node_ex(
                f"##{self.id}",                     # Hidden ID-only label
                PyImGui.TreeNodeFlags.SpanFullWidth
            )

            # Draw the visible label *next to* the arrow
            # (this draws ALWAYS — both expanded & collapsed)
            PyImGui.same_line(0,-1)
            PyImGui.text_colored(self.icon, self.color.to_tuple_normalized())

            PyImGui.same_line(0,-1)
            PyImGui.text_colored(f"[{self.node_type}]", self.color.to_tuple_normalized())

            PyImGui.same_line(0,-1)
            time_elapsed_str = self._format_duration(self.run_last_duration_ms) if self.run_last_duration_ms > 0 else str(self.total_time_ms) + "ms"

            PyImGui.text_colored(f" {self.name}({time_elapsed_str})", color)

            # ----- IF NODE IS COLLAPSED -----
            if not open_:
                return  # DO NOT draw children

            # ----- IF NODE IS EXPANDED -----
            # Draw metadata
            state_str = self.last_state.name if self.last_state else "NONE"
            PyImGui.text(f"State: {state_str}")
            #PyImGui.text(f"Start Time:  {self._run_start_time_ms:.3f} ms")
            PyImGui.text(f"Last Duration: {self._format_duration(self.run_last_duration_ms)}")
            PyImGui.text(f"Accumulated:   {self._format_duration(self.run_accumulated_ms)}")


            # Draw children
            for child in self.get_children():
                child.draw(indent + 1)

            PyImGui.tree_pop()


        
    # --------------------------------------------------------
    #region ActionNode
    # -------------------------------------------------------- 
    class ActionNode(Node):
        """
        ActionNode:
            - Executes a user-provided function once (action_fn).
            - The function must return a NodeState (SUCCESS / FAILURE / RUNNING).
            - If the function returns RUNNING → ActionNode returns RUNNING and
            will call the function again on the next tick.
            - If the function returns SUCCESS or FAILURE:
                • The node enters an optional wait period (aftercast_ms ms).
                • During the wait, the node returns RUNNING.
                • After the wait completes → returns the action's final state.
            - Supports action functions with signature action_fn() or action_fn(node).
            - After returning a final state, internal state resets so the node can be re-used.

        Meta:
          Expose: true
          Audience: advanced
          Display: Action Node
          Purpose: Execute a callback that returns a node state.
          UserDescription: Use this when behavior is driven by a custom action function.
          Notes: Supports action_fn() and action_fn(node). Aftercast keeps the node running before returning its final state.
        """

        def __init__(self, action_fn, aftercast_ms: int = 0,
                    name: str = "ActionNode"):
            super().__init__(name=name,
                            node_type="ActionNode",
                            node_category="leaf",
                            icon=IconsFontAwesome5.ICON_PLAY,
                            color=ColorPalette.GetColor("dark_orange"))
            self.action_fn = action_fn
            self.aftercast_ms = aftercast_ms
    
            self._action_done = False
            self._action_result = None
            self._start_time = None
            
            # --- blackboard support: detect if action_fn wants the node ---
            try:
                sig = inspect.signature(action_fn)
                self._accepts_node = (len(sig.parameters) >= 1)
            except (TypeError, ValueError):
                self._accepts_node = False
            # --- end blackboard support ---

        def _tick_impl(self) -> BehaviorTree.NodeState:
            if self._start_time is None:
                self._start_time = Utils.GetBaseTimestamp()
                
            # 1) Run the action first
            if not self._action_done:
                # --- blackboard support: call with node if requested ---
                if getattr(self, "_accepts_node", False):
                    result = self.action_fn(self)
                else:
                    result = self.action_fn()
                # --- end blackboard support ---
                result = self._normalize_state(result)
                
                # If action still running - return RUNNING
                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING

                # Action completed (SUCCESS or FAILURE)
                self._action_done = True
                self._action_result = result
                self._start_time = Utils.GetBaseTimestamp()
                return BehaviorTree.NodeState.RUNNING

            # 2) Action finished → now wait
            now = Utils.GetBaseTimestamp()
            elapsed = now - self._start_time

            if elapsed >= self.aftercast_ms:
                # Reset state so node is re-usable
                final = self._action_result
                if final is None:
                    final = BehaviorTree.NodeState.FAILURE  # Safety fallback
                self._action_done = False
                self._action_result = None
                self._start_time = None
                return final  # SUCCESS or FAILURE (propagates action result)

            return BehaviorTree.NodeState.RUNNING

        def reset(self) -> None:
            super().reset()
            self._action_done = False
            self._action_result = None
            self._start_time = None
        
    # --------------------------------------------------------
    #region ConditionNode
    # --------------------------------------------------------     

    class ConditionNode(Node):
        """
        ConditionNode:
            - Evaluates a user-provided condition function (condition_fn).
            - The function may return:
                • bool        → converted to SUCCESS (True) or FAILURE (False)
                • NodeState   → used directly
            - Supports both signatures:
                • condition_fn()
                • condition_fn(node)
            - Returns:
                • SUCCESS → condition true
                • FAILURE → condition false
                • (never returns RUNNING)
            - Any invalid return type raises a TypeError.

        Meta:
          Expose: true
          Audience: advanced
          Display: Condition Node
          Purpose: Run a predicate-like callback to gate behavior flow.
          UserDescription: Use this when logic depends on a custom condition function.
          Notes: Supports condition_fn() and condition_fn(node). Bool results are converted to success or failure.
        """

        def __init__(self, condition_fn, name: str = "ConditionNode"):
            super().__init__(name=name, node_type="ConditionNode",
                            node_category="leaf",
                            icon=IconsFontAwesome5.ICON_QUESTION,
                            color=ColorPalette.GetColor("teal"))
            self.condition_fn = condition_fn
            
            try:
                sig = inspect.signature(condition_fn)
                self._accepts_node = (len(sig.parameters) >= 1)
            except (TypeError, ValueError):
                self._accepts_node = False

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # Call with or without node depending on signature
            if self._accepts_node:
                result = self.condition_fn(self)
            else:
                result = self.condition_fn()

            normalized = self._normalize_state(result)
            if normalized is not None:
                return normalized

            # ---- CASE 1: NodeState directly ----
            if isinstance(result, BehaviorTree.NodeState):
                return result

            # ---- CASE 2: boolean → convert ----
            if isinstance(result, bool):
                return (BehaviorTree.NodeState.SUCCESS
                        if result
                        else BehaviorTree.NodeState.FAILURE)

            # ---- CASE 3: invalid return ----
            raise TypeError(
                f"ConditionNode expected bool or NodeState, got: {type(result).__name__}"
            )

         
    # --------------------------------------------------------
    #region SequenceNode
    # --------------------------------------------------------
    class SequenceNode(Node):
        """
        SequenceNode:
            - Ticks its children in order (left to right).
            - Behavior:
                • If a child returns FAILURE → Sequence returns FAILURE immediately.
                • If a child returns RUNNING → Sequence returns RUNNING and will
                resume from that same child on the next tick.
                • If a child returns SUCCESS → Sequence advances to the next child.
            - Only when ALL children return SUCCESS → Sequence returns SUCCESS.
            - Resets its child index after SUCCESS or FAILURE.

        Meta:
          Expose: true
          Audience: beginner
          Display: Sequence Node
          Purpose: Execute several child nodes from first to last.
          UserDescription: Use this when steps must happen in order.
          Notes: Stops on first failure. Resumes from the running child on the next tick.
        """

        def __init__(self, children=None, name: str = "SequenceNode"):
            super().__init__(name=name, node_type="SequenceNode", 
                             node_category="composite",
                             icon=IconsFontAwesome5.ICON_SORT_AMOUNT_DOWN_ALT,
                             color= ColorPalette.GetColor("dodger_blue"))
            self.children: List[BehaviorTree.Node] = self._coerce_children(children)
            self._current_child_index: int = 0

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def reset(self) -> None:
            super().reset()
            self._current_child_index = 0
            for child in self.children:
                child.reset()

        def _reset_children(self) -> None:
            for child in self.children:
                child.reset()

        def _tick_impl(self) -> BehaviorTree.NodeState:
            while self._current_child_index < len(self.children):
                # ---- BLACKBOARD SUPPORT ----
                child = self.children[self._current_child_index]
                child.blackboard = self.blackboard
                # ----------------------------

                result = self._normalize_state(child.tick())

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    self._current_child_index = 0
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING

                if result == BehaviorTree.NodeState.FAILURE:
                    self._current_child_index = 0
                    self._reset_children()
                    return BehaviorTree.NodeState.FAILURE

                # SUCCESS → continue to next child
                self._current_child_index += 1

            # Completed sequence
            self._current_child_index = 0
            self._reset_children()
            return BehaviorTree.NodeState.SUCCESS

    # --------------------------------------------------------
    #region SelectorNode
    # --------------------------------------------------------
    class SelectorNode(Node):
        """
        SelectorNode:
            - Ticks its children in order (left to right).
            - Behavior:
                • If a child returns SUCCESS → Selector returns SUCCESS immediately.
                • If a child returns RUNNING → Selector returns RUNNING and will
                resume from the same child on the next tick.
                • If a child returns FAILURE → tries the next child.
            - Only when ALL children return FAILURE → Selector returns FAILURE.
            - Resets its child index after SUCCESS or FAILURE.

        Meta:
          Expose: true
          Audience: beginner
          Display: Selector Node
          Purpose: Evaluate fallback branches from left to right.
          UserDescription: Use this when you want backup options if earlier children fail.
          Notes: Stops on first success. Resumes from the running child on the next tick.
        """

        def __init__(self, children=None, name: str = "SelectorNode"):
            super().__init__(name=name, node_type="SelectorNode", 
                             node_category="composite",
                             icon=IconsFontAwesome5.ICON_LIST_CHECK,
                             color= ColorPalette.GetColor("turquoise"))
            self.children: List[BehaviorTree.Node] = self._coerce_children(children)
            self._current_child_index: int = 0

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def reset(self) -> None:
            super().reset()
            self._current_child_index = 0
            for child in self.children:
                child.reset()

        def _reset_children(self) -> None:
            for child in self.children:
                child.reset()

        def _tick_impl(self) -> BehaviorTree.NodeState:
            while self._current_child_index < len(self.children):
                # ----- BLACKBOARD -----
                child = self.children[self._current_child_index]
                child.blackboard = self.blackboard
                # -----------------------

                result = self._normalize_state(child.tick())

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    self._current_child_index = 0
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING

                if result == BehaviorTree.NodeState.SUCCESS:
                    self._current_child_index = 0
                    self._reset_children()
                    return BehaviorTree.NodeState.SUCCESS

                # FAILURE → continue to next child
                self._current_child_index += 1

            # All children failed
            self._current_child_index = 0
            self._reset_children()
            return BehaviorTree.NodeState.FAILURE
      
    # --------------------------------------------------------
    #region ChoiceNode
    # --------------------------------------------------------  
    class ChoiceNode(Node):
        """
        ChoiceNode:
            - Ticks its children in order.
            - Returns the first result that is NOT FAILURE (i.e., SUCCESS or RUNNING).
            - Behavior:
                • If a child returns SUCCESS → ChoiceNode returns SUCCESS.
                • If a child returns RUNNING → ChoiceNode returns RUNNING.
                • If a child returns FAILURE → tries the next child.
            - Only when ALL children return FAILURE → ChoiceNode returns FAILURE.
            - Does not resume from a specific child; each tick reevaluates from the top.

        Meta:
          Expose: true
          Audience: advanced
          Display: Choice Node
          Purpose: Evaluate options from the top and return the first non-failure result.
          UserDescription: Use this when each tick should reevaluate choices from the beginning.
          Notes: Unlike SelectorNode, this reevaluates from the top every tick.
        """

        def __init__(self, children=None, name: str = "ChoiceNode"):
            super().__init__(name=name, node_type="ChoiceNode", 
                             node_category="composite",
                             icon=IconsFontAwesome5.ICON_ARROW_UP_1_9,
                             color= ColorPalette.GetColor("olive"))
            self.children: List[BehaviorTree.Node] = self._coerce_children(children)

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def reset(self) -> None:
            super().reset()
            for child in self.children:
                child.reset()

        def _reset_children(self) -> None:
            for child in self.children:
                child.reset()

        def _tick_impl(self) -> BehaviorTree.NodeState:
            for child in self.children:
                # ----- BLACKBOARD -----
                child.blackboard = self.blackboard
                # ----------------------

                result = self._normalize_state(child.tick())

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    return BehaviorTree.NodeState.FAILURE

                # The FIRST non-failure result is returned immediately
                if result != BehaviorTree.NodeState.FAILURE:
                    if result != BehaviorTree.NodeState.RUNNING:
                        self._reset_children()
                    return result

            # All children returned FAILURE
            self._reset_children()
            return BehaviorTree.NodeState.FAILURE

    # --------------------------------------------------------
    #region SwitchNode
    # --------------------------------------------------------
    class SwitchNode(Node):
        """
        SwitchNode:
            - Selects one case based on a selector function or blackboard-aware callback.
            - Lazily builds the selected subtree when first needed.
            - If the selected case changes while running, the previous subtree is reset and discarded.
            - Returns the selected subtree result directly.
            - If no case matches and no default is provided, returns FAILURE.

        Meta:
          Expose: true
          Audience: advanced
          Display: Switch Node
          Purpose: Choose one case dynamically and execute its tree.
          UserDescription: Use this when different branches should run based on current state or blackboard values.
          Notes: Rebuilds or swaps the active subtree when the selected case changes.
        """

        def __init__(
            self,
            selector_fn,
            cases,
            default_case: "BehaviorTree | BehaviorTree.Node | Callable[[], BehaviorTree | BehaviorTree.Node] | None" = None,
            name: str = "SwitchNode",
        ):
            super().__init__(
                name=name,
                node_type="SwitchNode",
                node_category="router",
                icon=IconsFontAwesome5.ICON_CODE_BRANCH,
                color=ColorPalette.GetColor("orange"),
            )
            self.selector_fn = selector_fn
            self.cases = list(cases.items()) if isinstance(cases, dict) else list(cases or [])
            self.default_case = default_case
            self._selected_key = None
            self._active_tree: Optional[BehaviorTree] = None

            try:
                sig = inspect.signature(selector_fn)
                self._accepts_node = (len(sig.parameters) >= 1)
            except (TypeError, ValueError):
                self._accepts_node = False

        def reset(self) -> None:
            super().reset()
            self._selected_key = None
            if self._active_tree is not None:
                self._active_tree.reset()
                self._active_tree = None

        def _coerce_tree(self, value) -> "BehaviorTree":
            subtree = value() if callable(value) else value
            if isinstance(subtree, BehaviorTree):
                return subtree
            if isinstance(subtree, BehaviorTree.Node):
                return BehaviorTree(subtree)
            if hasattr(subtree, "root") and hasattr(subtree, "tick") and hasattr(subtree, "reset"):
                return cast("BehaviorTree", subtree)
            raise TypeError(
                f"SwitchNode expected a BehaviorTree or BehaviorTree.Node, got {type(subtree).__name__}."
            )

        def get_children(self) -> List["BehaviorTree.Node"]:
            if self._active_tree is None:
                return []
            return [self._active_tree.root]

        def _resolve_case(self, selected_key):
            for case_key, case_value in self.cases:
                if case_key == selected_key:
                    return case_value
            return self.default_case

        def _tick_impl(self) -> BehaviorTree.NodeState:
            selected_key = self.selector_fn(self) if self._accepts_node else self.selector_fn()
            selected_case = self._resolve_case(selected_key)

            if selected_case is None:
                if self._active_tree is not None:
                    self._active_tree.reset()
                    self._active_tree = None
                self._selected_key = None
                return BehaviorTree.NodeState.FAILURE

            if self._selected_key != selected_key or self._active_tree is None:
                if self._active_tree is not None:
                    self._active_tree.reset()
                self._selected_key = selected_key
                self._active_tree = self._coerce_tree(selected_case)

            if self.blackboard is not None and self._active_tree is not None:
                self._active_tree.blackboard = self.blackboard

            result = self._normalize_state(self._active_tree.tick() if self._active_tree is not None else None)
            if result is None:
                raise TypeError(f"SwitchNode '{self.name}' active case returned a non-NodeState result.")
            return result
        
    # --------------------------------------------------------
    #region RepeaterNode
    # --------------------------------------------------------
    class RepeaterNode(Node):   
        """
        RepeaterNode:
            - Executes its child a fixed number of times (repeat_count).
            - Behavior:
                • If the child returns RUNNING → Repeater returns RUNNING and
                will resume from the same child without advancing the count.
                • If the child returns SUCCESS or FAILURE → the repetition count
                increases and the next repetition begins.
            - When all repetitions are completed → Repeater returns SUCCESS.
            - Internal counter resets after completion or failure.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Repeater Node
          Purpose: Repeat a child node until the configured count is reached.
          UserDescription: Use this when the same step should run multiple times.
          Notes: The repeat counter only advances after success or failure, not while the child is running.
        """

        def __init__(self, child: "BehaviorTree.Node", repeat_count: int = 1, name: str = "RepeaterNode"):
            super().__init__(name=name, node_type="RepeaterNode", 
                             node_category="repeater",
                             icon=IconsFontAwesome5.ICON_HISTORY,
                             color= ColorPalette.GetColor("light_green"))
            self.child = self._coerce_node(child)
            self.repeat_count = repeat_count
            self._current_repeat_count: int = 0

        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def reset(self) -> None:
            super().reset()
            self._current_repeat_count = 0
            self.child.reset()

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # ----- Blackboard -----
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # -----------------------

            while self._current_repeat_count < self.repeat_count:
                result = self._normalize_state(self.child.tick())

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{self.child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    self._current_repeat_count = 0
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING

                # On SUCCESS or FAILURE, increment and continue
                self._current_repeat_count += 1

            # Completed all repetitions → reset counter
            self._current_repeat_count = 0
            return BehaviorTree.NodeState.SUCCESS
        
    # --------------------------------------------------------
    #region RepeaterUntilSuccessNode
    # --------------------------------------------------------
    class RepeaterUntilSuccessNode(Node):
        """
        RepeaterUntilSuccessNode:
            - Repeatedly ticks its child until the child returns SUCCESS.
            - Behavior:
                • If the child returns RUNNING → returns RUNNING.
                • If the child returns FAILURE → immediately tries again.
                • If the child returns SUCCESS → node returns SUCCESS.
            - Optional timeout:
                • If timeout_ms > 0 and the total elapsed time exceeds it →
                node returns FAILURE.
            - Internal timing resets once SUCCESS or timeout occurs.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Repeater Until Success Node
          Purpose: Keep retrying a child until it returns success.
          UserDescription: Use this when a step should be retried until it works.
          Notes: Failure retries immediately. Timeout causes the repeater itself to fail.
        """

        def __init__(self, child: "BehaviorTree.Node", timeout_ms: int = 0, name: str = "RepeaterUntilSuccessNode"):
            super().__init__(name=name, node_type="RepeaterUntilSuccessNode", 
                             node_category="repeater",
                             icon=IconsFontAwesome5.ICON_ROTATE_RIGHT,
                             color= ColorPalette.GetColor("light_yellow"))
            self.child = self._coerce_node(child)
            self.timeout_ms = timeout_ms
            self._start_time_ms = None

        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def reset(self) -> None:
            super().reset()
            self._start_time_ms = None
            self.child.reset()

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # ---------- INIT TIME ----------
            if self._start_time_ms is None:
                self._start_time_ms = Utils.GetBaseTimestamp()

            # ---------- TIMEOUT CHECK ----------
            if self.timeout_ms > 0:
                elapsed = Utils.GetBaseTimestamp() - self._start_time_ms
                if elapsed >= self.timeout_ms:
                    self._start_time_ms = None
                    return BehaviorTree.NodeState.FAILURE

            # ---------- BLACKBOARD ----------
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # --------------------------------

            # ---------- CHILD EXECUTION LOOP ----------
            while True:
                result = self._normalize_state(self.child.tick())

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{self.child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING

                if result == BehaviorTree.NodeState.SUCCESS:
                    self._start_time_ms = None  # reset fully for next run
                    return BehaviorTree.NodeState.SUCCESS

                # On FAILURE → repeat (loop again)
      
    # --------------------------------------------------------
    #region RepeaterUntilFailureNode
    # --------------------------------------------------------          
    class RepeaterUntilFailureNode(Node):
        """
        RepeaterUntilFailureNode:
            - Repeatedly ticks its child until the child returns FAILURE.
            - Behavior:
                • If the child returns RUNNING → node returns RUNNING.
                • If the child returns SUCCESS → immediately repeats.
                • If the child returns FAILURE → node returns SUCCESS.
            - Optional timeout:
                • If timeout_ms > 0 and total elapsed time exceeds it →
                node returns FAILURE.
            - Internal timing resets once the stop condition or timeout occurs.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Repeater Until Failure Node
          Purpose: Keep retrying a child until it returns failure.
          UserDescription: Use this when success should loop and failure should stop the repeater.
          Notes: Child failure makes this node succeed. Timeout makes the repeater fail.
        """

        def __init__(self, child: "BehaviorTree.Node", timeout_ms: int = 0, name: str = "RepeaterUntilFailureNode"):
            super().__init__(name=name, node_type="RepeaterUntilFailureNode", 
                             node_category="repeater",
                             icon=IconsFontAwesome5.ICON_ROTATE_LEFT,
                             color= ColorPalette.GetColor("light_pink"))
            self.child = self._coerce_node(child)
            self.timeout_ms = timeout_ms
            self._start_time_ms = None
            
        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def reset(self) -> None:
            super().reset()
            self._start_time_ms = None
            self.child.reset()

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # ---------- INIT TIME ----------
            if self._start_time_ms is None:
                self._start_time_ms = Utils.GetBaseTimestamp()

            # ---------- TIMEOUT CHECK ----------
            if self.timeout_ms > 0:
                elapsed = Utils.GetBaseTimestamp() - self._start_time_ms
                if elapsed >= self.timeout_ms:
                    self._start_time_ms = None
                    return BehaviorTree.NodeState.FAILURE

            # ---------- BLACKBOARD ----------
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # ----------------------------------

            # ---------- CHILD EXECUTION LOOP ----------
            while True:
                result = self._normalize_state(self.child.tick())

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{self.child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING

                if result == BehaviorTree.NodeState.FAILURE:
                    # End and succeed because FAILURE is our stop condition
                    self._start_time_ms = None  # reset for next run
                    return BehaviorTree.NodeState.SUCCESS

                # If SUCCESS → repeat forever
     
    # --------------------------------------------------------
    #region RepeaterForeverNode
    # --------------------------------------------------------           
    class RepeaterForeverNode(Node):
        """
        RepeaterForeverNode:
            - Continuously ticks its child with no stop condition.
            - Behavior:
                • The child is ticked every cycle.
                • The child’s returned state is ignored.
                • The node itself always returns RUNNING.
            - Optional timeout:
                • If timeout_ms > 0 and elapsed time exceeds it →
                node returns FAILURE.
            - Timing resets after timeout.

        Meta:
          Expose: true
          Audience: advanced
          Display: Repeater Forever Node
          Purpose: Keep driving a child indefinitely.
          UserDescription: Use this for maintenance or service behaviors that should always keep running.
          Notes: Ignores the child result and returns running unless the optional timeout is exceeded.
        """

        def __init__(self, child: "BehaviorTree.Node", timeout_ms: int = 0, name: str = "RepeaterForeverNode"):
            super().__init__(name=name, node_type="RepeaterForeverNode", 
                             node_category="repeater",
                             icon=IconsFontAwesome5.ICON_INFINITY,
                             color= ColorPalette.GetColor("creme"))
            self.child = self._coerce_node(child)
            self.timeout_ms = timeout_ms
            self._start_time_ms = None
            
        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def reset(self) -> None:
            super().reset()
            self._start_time_ms = None
            self.child.reset()

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # ---------- INIT TIME ----------
            if self._start_time_ms is None:
                self._start_time_ms = Utils.GetBaseTimestamp()
                
            # ---------- TIMEOUT CHECK ----------
            if self.timeout_ms > 0:
                elapsed = Utils.GetBaseTimestamp() - self._start_time_ms
                if elapsed >= self.timeout_ms:
                    self._start_time_ms = None
                    return BehaviorTree.NodeState.FAILURE
                    
            # --- blackboard support ---
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # --------------------------

            # Tick the child but ignore its result completely
            self.child.tick()

            # Always RUNNING
            return BehaviorTree.NodeState.RUNNING
        
    # --------------------------------------------------------
    #region ParallelNode
    # --------------------------------------------------------
    
    class ParallelNode(Node):
        """
        ParallelNode:
            - Ticks all children on every tick().
            - Behavior:
                • If ANY child returns FAILURE → ParallelNode returns FAILURE immediately.
                • If ALL children return SUCCESS → ParallelNode returns SUCCESS.
                • Otherwise (at least one RUNNING, none FAILED) → ParallelNode returns RUNNING.
            - Notes:
                • All children execute every tick, regardless of their previous result.
                • Blackboard is propagated to all children before execution.
        Meta:
          Expose: true
          Audience: intermediate
          Display: Parallel Node
          Purpose: Run multiple child branches together on each tick.
          UserDescription: Use this when several behaviors should be evaluated at the same time.
          Notes: Any child failure fails the node. All-child success succeeds the node.
        """

        def __init__(self, children=None, name: str = "ParallelNode"):
            super().__init__(name=name, node_type="ParallelNode", 
                             node_category="composite",
                             icon=IconsFontAwesome5.ICON_PROJECT_DIAGRAM,
                             color= ColorPalette.GetColor("light_purple"))
            self.children: List[BehaviorTree.Node] = self._coerce_children(children)

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def reset(self) -> None:
            super().reset()
            for child in self.children:
                child.reset()

        def _reset_children(self) -> None:
            for child in self.children:
                child.reset()

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # --- blackboard support ---
            if self.blackboard is not None:
                for child in self.children:
                    child.blackboard = self.blackboard
            # ---------------------------

            all_success = True

            for child in self.children:
                result = self._normalize_state(child.tick())

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.FAILURE:
                    self._reset_children()
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    all_success = False

            if all_success:
                self._reset_children()
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.NodeState.RUNNING
            
    # --------------------------------------------------------
    #region SubtreeNode
    # --------------------------------------------------------
    
    class SubtreeNode(Node):
        """
        SubtreeNode:
            - Dynamically constructs a full BehaviorTree when ticked.
            - The subtree is created lazily by calling `subtree_fn(self)`:
                • Allows the factory to read this node’s blackboard.
                • Supports dynamic data, runtime state, and external context.
            - Behavior:
                • On first tick, builds the subtree and stores it.
                • On every tick, forwards the tick() to the subtree’s root.
                • If the parent has a blackboard, it is propagated to the subtree root.
            - reset():
                • Resets both this node and the subtree (if already created).
            - Typical Use:
                • When a tree must be generated at runtime, based on live data.
                • When you need a “tree factory” instead of a static tree structure.
                • When you need to run another BehaviorTree as a child node.
        
        Meta:
          Expose: true
          Audience: advanced
          Display: Subtree Node
          Purpose: Execute another behavior tree as a child branch.
          UserDescription: Use this to plug a tree factory or reusable subtree into the current tree.
          Notes: The subtree is created on first use and can depend on live blackboard state.
        """

        def __init__(self, subtree_fn: Callable[["BehaviorTree.Node"], "BehaviorTree | BehaviorTree.Node"], name: str = "SubtreeNode"):
            if not callable(subtree_fn):
                raise TypeError("SubtreeNode requires a callable returning a BehaviorTree or BehaviorTree.Node.")

            super().__init__(
                name=name,
                node_type="SubtreeNode",
                node_category="router",
                icon=IconsFontAwesome5.ICON_SITEMAP,
                color=ColorPalette.GetColor("light_green")
            )

            self._factory = subtree_fn
            self._subtree: "BehaviorTree | None" = None
        
        def reset(self):
            super().reset()
            if self._subtree is not None:
                self._subtree.reset()
                self._subtree = None

        def _ensure_subtree(self):
            """
            Create the subtree only when the node is ticked for the first time,
            and pass THIS node to the factory, allowing dynamic values.
            """
            if self._subtree is None:
                subtree = self._factory(self)
                if subtree is None:
                    raise ValueError("subtree_fn() returned None; expected a BehaviorTree or BehaviorTree.Node.")
                if isinstance(subtree, BehaviorTree):
                    self._subtree = subtree
                elif isinstance(subtree, BehaviorTree.Node):
                    self._subtree = BehaviorTree(subtree)
                elif (
                    hasattr(subtree, "root")
                    and hasattr(subtree, "tick")
                    and hasattr(subtree, "reset")
                    and hasattr(getattr(subtree, "root"), "tick")
                ):
                    self._subtree = cast("BehaviorTree", subtree)
                else:
                    raise TypeError(
                        f"subtree_fn() returned invalid type {type(subtree).__name__}; "
                        "expected a BehaviorTree or BehaviorTree.Node."
                    )

        def get_children(self) -> List["BehaviorTree.Node"]:
            if self._subtree is not None:
                return [self._subtree.root]
            return []  # subtree not created yet

        def _tick_impl(self) -> BehaviorTree.NodeState:
            self._ensure_subtree()

            tree = self._subtree
            if tree is None:
                raise RuntimeError("SubtreeNode: _subtree is None after _ensure_subtree().")

            # propagate blackboard
            if self.blackboard is not None:
                tree.root.blackboard = self.blackboard

            # tick subtree root
            return tree.root.tick()

 
    # --------------------------------------------------------
    #region InverterNode
    # --------------------------------------------------------
    class InverterNode(Node):
        """
        Inverter:
            - Flips the child’s result:
                • SUCCESS → FAILURE
                • FAILURE → SUCCESS
                • RUNNING → RUNNING (unchanged)
            - Propagates the blackboard to the child.
            - Useful when a condition must be logically negated.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Inverter Node
          Purpose: Negate the result of a child branch.
          UserDescription: Use this when a condition or subtree should be treated as the opposite result.
          Notes: Running stays running. Only success and failure are flipped.
        """

        def __init__(self, child: "BehaviorTree.Node", name: str = "InverterNode"):
            super().__init__(name=name, node_type="InverterNode", 
                             node_category="decorator",
                             icon=IconsFontAwesome5.ICON_CIRCLE_MINUS,
                             color= ColorPalette.GetColor("purple"))
            self.child = self._coerce_node(child)

        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def reset(self) -> None:
            super().reset()
            self.child.reset()

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # ----- BLACKBOARD -----
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # -----------------------

            # Tick child
            result = self.child.tick()
            result = self._normalize_state(result)

            if result is None:
                ConsoleLog(
                    "BT",
                    f"ERROR: Node '{self.child.name}' returned None!",
                    Console.MessageType.Error
                )
                return BehaviorTree.NodeState.FAILURE

            # Invert SUCCESS/FAILURE
            if result == BehaviorTree.NodeState.SUCCESS:
                return BehaviorTree.NodeState.FAILURE

            if result == BehaviorTree.NodeState.FAILURE:
                return BehaviorTree.NodeState.SUCCESS

            # RUNNING stays RUNNING
            return BehaviorTree.NodeState.RUNNING
        
    # --------------------------------------------------------
    #region WaitNode
    # --------------------------------------------------------
    class WaitNode(Node):
        """
        WaitNode:
            - Repeatedly calls check_fn() each tick until:
                • check_fn returns SUCCESS → WaitNode returns SUCCESS.
                • check_fn returns FAILURE → WaitNode returns FAILURE.
                • timeout_ms is reached      → WaitNode returns FAILURE.
            - If check_fn returns RUNNING → WaitNode stays RUNNING.
            - If timeout_ms = 0 → no timeout (wait indefinitely).
            - check_fn must return a NodeState (SUCCESS / FAILURE / RUNNING).
            - THIS NODE IS NOT THROTTLED: check_fn is called every tick.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait Node
          Purpose: Keep checking a callback until it resolves.
          UserDescription: Use this when something should be checked continuously until it completes.
          Notes: This node is not throttled. The callback runs every tick.
        """

        def __init__(self, check_fn, timeout_ms: int = 0, name: str = "WaitNode"):
            super().__init__(name=name, node_type="WaitNode", 
                             node_category="wait",
                             icon=IconsFontAwesome5.ICON_HAND,
                             color = ColorPalette.GetColor("light_cyan"))
            self.check_fn = check_fn
            self.timeout_ms = timeout_ms
            self._start_time_ms: Optional[int] = None

        def _tick_impl(self) -> BehaviorTree.NodeState:
            now = Utils.GetBaseTimestamp()

            # start timer on first tick
            if self._start_time_ms is None:
                self._start_time_ms = now

            # run check
            result = self.check_fn()
            result = self._normalize_state(result) or result

            # invalid return
            if result is None:
                ConsoleLog("BT", f"ERROR: Node '{self.name}' returned None!", Console.MessageType.Error)
                self._start_time_ms = None
                return BehaviorTree.NodeState.FAILURE

            # pass through SUCCESS
            if result == BehaviorTree.NodeState.SUCCESS:
                self._start_time_ms = None
                return BehaviorTree.NodeState.SUCCESS

            # pass through FAILURE
            if result == BehaviorTree.NodeState.FAILURE:
                self._start_time_ms = None
                return BehaviorTree.NodeState.FAILURE

            # still running → check timeout
            if self.timeout_ms > 0:
                if (now - self._start_time_ms) >= self.timeout_ms:
                    self._start_time_ms = None
                    return BehaviorTree.NodeState.FAILURE

            # continue waiting
            return BehaviorTree.NodeState.RUNNING

        def reset(self) -> None:
            super().reset()
            self._start_time_ms = None
     
    # --------------------------------------------------------
    #region WaitUntilNode
    # --------------------------------------------------------   
    class WaitUntilNode(Node):
        """
        WaitUntilNode:
            - Periodically evaluates condition_fn.
            - The condition_fn may return:
                • bool      → True = SUCCESS, False = FAILURE
                • NodeState → direct meaning
            - Supports condition_fn() or condition_fn(node).
            - SUCCESS  → stop waiting
            - FAILURE  → stop waiting
            - RUNNING  → keep waiting
            - Evaluates at most once every interval_ms.
            - If timeout_ms > 0 and exceeded → FAILURE.
            - THIS NODE IS THROTTLED: condition_fn is called at most once every interval_ms.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait Until Node
          Purpose: Throttle condition checks while waiting for a result.
          UserDescription: Use this when a condition should be checked repeatedly but not every tick.
          Notes: Supports condition_fn() and condition_fn(node). This node throttles evaluation by interval.
        """

        def __init__(self, condition_fn,
                    throttle_interval_ms: int = 100,
                    timeout_ms: int = 0,
                    name: str = "WaitUntilNode"):

            super().__init__(
                name=name,
                node_type="WaitUntilNode",
                node_category="wait",
                icon=IconsFontAwesome5.ICON_CLOCK,
                color=ColorPalette.GetColor("light_green")
            )

            self.condition_fn = condition_fn
            self.interval_ms = throttle_interval_ms
            self.timeout_ms = timeout_ms

            try:
                sig = inspect.signature(condition_fn)
                self._accepts_node = (len(sig.parameters) >= 1)
            except (TypeError, ValueError):
                self._accepts_node = False

            self._start_time_ms = None
            self._last_check_time_ms = None

        def _tick_impl(self) -> BehaviorTree.NodeState:
            now = Utils.GetBaseTimestamp()

            # --- INIT ---
            if self._start_time_ms is None:
                self._start_time_ms = now
                self._last_check_time_ms = 0
                #ConsoleLog("WaitUntilNode", f"[{self.name}] Init start_time={self._start_time_ms}", log=True)

            # --- TIMEOUT ---
            if self.timeout_ms > 0 and (now - self._start_time_ms) >= self.timeout_ms:
                #ConsoleLog("WaitUntilNode",f"[{self.name}] TIMEOUT exceeded ({now - self._start_time_ms} ms >= {self.timeout_ms})",log=True)
                self._start_time_ms = None
                self._last_check_time_ms = None
                return BehaviorTree.NodeState.FAILURE

            # --- THROTTLE ---
            if self._last_check_time_ms and ((now - self._last_check_time_ms) < self.interval_ms):
                #ConsoleLog("WaitUntilNode",f"[{self.name}] Throttled ({now - self._last_check_time_ms} < {self.interval_ms})",log=True)
                return BehaviorTree.NodeState.RUNNING

            self._last_check_time_ms = now

            # --- CALL CONDITION ---
            #ConsoleLog("WaitUntilNode",f"[{self.name}] Calling condition_fn (_accepts_node={self._accepts_node})",log=True)

            try:
                if getattr(self, "_accepts_node", False):
                    result = self.condition_fn(self)
                else:
                    result = self.condition_fn()
            except Exception as e:
                ConsoleLog("WaitUntilNode",f"[{self.name}] ERROR evaluating condition_fn: {repr(e)}",log=True)
                raise

            #ConsoleLog("WaitUntilNode",f"[{self.name}] condition_fn returned: {result} (type={type(result).__name__})",log=True)

            result = self._normalize_state(result) or result

            # --- NodeState ---
            if isinstance(result, BehaviorTree.NodeState):
                #ConsoleLog("WaitUntilNode", f"[{self.name}] Returning NodeState: {result}",log=True)
                
                # FIX: reset state so next tick does not throttle
                self._start_time_ms = None
                self._last_check_time_ms = None
                
                return result

            # --- BOOL ---
            if isinstance(result, bool):
                state = (BehaviorTree.NodeState.SUCCESS if result
                        else BehaviorTree.NodeState.FAILURE)

                #ConsoleLog("WaitUntilNode",f"[{self.name}] Converted bool → {state}",log=True)
                self._start_time_ms = None
                self._last_check_time_ms = None
                return state


            # --- INVALID ---
            #ConsoleLog("WaitUntilNode",
            #        f"[{self.name}] INVALID return type from condition_fn: {type(result).__name__}",
            #        log=True)

            raise TypeError(
                f"WaitUntilNode expected bool or NodeState, got: {type(result).__name__}"
            )

        def reset(self) -> None:
            super().reset()
            self._start_time_ms = None
            self._last_check_time_ms = None


    # --------------------------------------------------------
    #region WaitUntilSuccessNode
    # --------------------------------------------------------  
    class WaitUntilSuccessNode(Node):
        """
        WaitUntilSuccessNode:
            - Periodically evaluates condition_fn.
            - The condition_fn may return:
                • bool        → True = SUCCESS, False = FAILURE(retry)
                • NodeState   → SUCCESS = success, FAILURE/RUNNING = retry
            - Repeats until SUCCESS.
            - Timeout → FAILURE.
            - Supports condition_fn() or condition_fn(node).
            - EXACT same behavior style as WaitUntilNode (logging + validation).

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait Until Success Node
          Purpose: Retry a condition check until success.
          UserDescription: Use this when only success should stop the waiting loop.
          Notes: Failure and running both keep the node waiting. Timeout causes failure.
        """

        def __init__(self, condition_fn,
                    throttle_interval_ms: int = 100,
                    timeout_ms: int = 0,
                    name: str = "WaitUntilSuccessNode"):

            super().__init__(
                name=name,
                node_type="WaitUntilSuccessNode",
                node_category="wait",
                icon=IconsFontAwesome5.ICON_HOURGLASS_HALF,
                color=ColorPalette.GetColor("yellow")
            )

            self.condition_fn = condition_fn
            self.interval_ms = throttle_interval_ms
            self.timeout_ms = timeout_ms

            try:
                sig = inspect.signature(condition_fn)
                self._accepts_node = (len(sig.parameters) >= 1)
            except (TypeError, ValueError):
                self._accepts_node = False

            self._start_time_ms = None
            self._last_check_time_ms = None

        def _tick_impl(self) -> BehaviorTree.NodeState:
            now = Utils.GetBaseTimestamp()

            # --- INIT ---
            if self._start_time_ms is None:
                self._start_time_ms = now
                self._last_check_time_ms = now
                ConsoleLog("WaitUntilSuccessNode",
                    f"[{self.name}] Init start_time={self._start_time_ms}", log=True)

            # --- TIMEOUT ---
            if self.timeout_ms > 0 and (now - self._start_time_ms) >= self.timeout_ms:
                ConsoleLog("WaitUntilSuccessNode",
                    f"[{self.name}] TIMEOUT ({now - self._start_time_ms} >= {self.timeout_ms})",
                    log=True)
                self._start_time_ms = None
                self._last_check_time_ms = None
                return BehaviorTree.NodeState.FAILURE

            # --- THROTTLE ---
            if self._last_check_time_ms and ((now - self._last_check_time_ms) < self.interval_ms):
                ConsoleLog("WaitUntilSuccessNode",
                    f"[{self.name}] Throttled ({now - self._last_check_time_ms} < {self.interval_ms})",
                    log=True)
                return BehaviorTree.NodeState.RUNNING

            self._last_check_time_ms = now

            # --- CALL CONDITION ---
            ConsoleLog("WaitUntilSuccessNode",
                f"[{self.name}] Calling condition_fn (_accepts_node={self._accepts_node})",
                log=True)

            try:
                if getattr(self, "_accepts_node", False):
                    result = self.condition_fn(self)
                else:
                    result = self.condition_fn()
            except Exception as e:
                ConsoleLog("WaitUntilSuccessNode",
                    f"[{self.name}] ERROR evaluating condition_fn: {repr(e)}",
                    log=True)
                raise

            ConsoleLog("WaitUntilSuccessNode",
                f"[{self.name}] condition_fn returned: {result} (type={type(result).__name__})",
                log=True)

            result = self._normalize_state(result) or result

            # --- Normalize bool ---
            if isinstance(result, bool):
                result = (BehaviorTree.NodeState.SUCCESS if result
                        else BehaviorTree.NodeState.FAILURE)

            # --- SUCCESS → done ---
            if result == BehaviorTree.NodeState.SUCCESS:
                ConsoleLog("WaitUntilSuccessNode",
                    f"[{self.name}] Returning SUCCESS",
                    log=True)
                self._start_time_ms = None
                self._last_check_time_ms = None
                return BehaviorTree.NodeState.SUCCESS

            # --- FAILURE or RUNNING → retry ---
            if result in (BehaviorTree.NodeState.FAILURE, BehaviorTree.NodeState.RUNNING):
                ConsoleLog("WaitUntilSuccessNode",
                    f"[{self.name}] Retry (result={result})",
                    log=True)
                return BehaviorTree.NodeState.RUNNING

            # --- INVALID ---
            ConsoleLog("WaitUntilSuccessNode",
                f"[{self.name}] INVALID return type: {type(result).__name__}",
                log=True)

            raise TypeError(
                f"WaitUntilSuccessNode expected bool or NodeState, got: {type(result).__name__}"
            )

        def reset(self) -> None:
            super().reset()
            self._start_time_ms = None
            self._last_check_time_ms = None



    # --------------------------------------------------------
    #region WaitUntilFailureNode
    # --------------------------------------------------------   
    class WaitUntilFailureNode(Node):
        """
        WaitUntilFailureNode:
            - Periodically evaluates condition_fn.
            - The condition_fn may return:
                • bool        → False = SUCCESS (condition failed), True = retry
                • NodeState   → FAILURE = SUCCESS, SUCCESS/RUNNING = retry
            - Repeats until FAILURE.
            - Timeout → FAILURE.
            - EXACT same behavior style as WaitUntilNode.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait Until Failure Node
          Purpose: Retry a condition check until failure becomes the stop condition.
          UserDescription: Use this when the waiting loop should end only after the condition fails.
          Notes: A condition failure makes this node succeed. Timeout causes failure.
        """

        def __init__(self, condition_fn,
                    throttle_interval_ms: int = 100,
                    timeout_ms: int = 0,
                    name: str = "WaitUntilFailureNode"):

            super().__init__(
                name=name,
                node_type="WaitUntilFailureNode",
                node_category="wait",
                icon=IconsFontAwesome5.ICON_HOURGLASS_END,
                color=ColorPalette.GetColor("light_red")
            )

            self.condition_fn = condition_fn
            self.interval_ms = throttle_interval_ms
            self.timeout_ms = timeout_ms

            try:
                sig = inspect.signature(condition_fn)
                self._accepts_node = (len(sig.parameters) >= 1)
            except (TypeError, ValueError):
                self._accepts_node = False

            self._start_time_ms = None
            self._last_check_time_ms = None

        def _tick_impl(self) -> BehaviorTree.NodeState:
            now = Utils.GetBaseTimestamp()

            # --- INIT ---
            if self._start_time_ms is None:
                self._start_time_ms = now
                self._last_check_time_ms = now
                ConsoleLog("WaitUntilFailureNode",
                    f"[{self.name}] Init start_time={self._start_time_ms}", log=True)

            # --- TIMEOUT ---
            if self.timeout_ms > 0 and (now - self._start_time_ms) >= self.timeout_ms:
                ConsoleLog("WaitUntilFailureNode",
                    f"[{self.name}] TIMEOUT ({now - self._start_time_ms} >= {self.timeout_ms})",
                    log=True)
                self._start_time_ms = None
                self._last_check_time_ms = None
                return BehaviorTree.NodeState.FAILURE

            # --- THROTTLE ---
            if self._last_check_time_ms and ((now - self._last_check_time_ms) < self.interval_ms):
                ConsoleLog("WaitUntilFailureNode",
                    f"[{self.name}] Throttled ({now - self._last_check_time_ms} < {self.interval_ms})",
                    log=True)
                return BehaviorTree.NodeState.RUNNING

            self._last_check_time_ms = now

            # --- CALL CONDITION ---
            ConsoleLog("WaitUntilFailureNode",
                f"[{self.name}] Calling condition_fn (_accepts_node={self._accepts_node})",
                log=True)

            try:
                if getattr(self, "_accepts_node", False):
                    result = self.condition_fn(self)
                else:
                    result = self.condition_fn()
            except Exception as e:
                ConsoleLog("WaitUntilFailureNode",
                    f"[{self.name}] ERROR evaluating condition_fn: {repr(e)}",
                    log=True)
                raise

            ConsoleLog("WaitUntilFailureNode",
                f"[{self.name}] condition_fn returned: {result} (type={type(result).__name__})",
                log=True)

            result = self._normalize_state(result) or result

            # --- Normalize bool ---
            if isinstance(result, bool):
                result = (BehaviorTree.NodeState.SUCCESS if result
                        else BehaviorTree.NodeState.FAILURE)

            # --- FAILURE → this node SUCCESS ---
            if result == BehaviorTree.NodeState.FAILURE:
                ConsoleLog("WaitUntilFailureNode",
                    f"[{self.name}] Returning SUCCESS (condition FAILED)",
                    log=True)
                self._start_time_ms = None
                self._last_check_time_ms = None
                return BehaviorTree.NodeState.SUCCESS

            # --- Otherwise retry (SUCCESS or RUNNING) ---
            ConsoleLog("WaitUntilFailureNode",
                f"[{self.name}] Retry (result={result})",
                log=True)

            return BehaviorTree.NodeState.RUNNING

        def reset(self) -> None:
            super().reset()
            self._start_time_ms = None
            self._last_check_time_ms = None



    # --------------------------------------------------------
    #region WaitForTimeNode
    # --------------------------------------------------------
    class WaitForTimeNode(Node):
        """
        WaitForTimeNode:
            - Waits for a fixed duration in milliseconds.
            - Behavior:
                • Returns RUNNING until the elapsed time >= duration_ms.
                • Returns SUCCESS once the duration has fully passed.
            - Notes:
                • On first tick(), the node records a start timestamp.
                • After SUCCESS, the start time is reset so the node can be reused.
        
        Meta:
          Expose: true
          Audience: beginner
          Display: Wait For Time Node
          Purpose: Delay execution for a known amount of time.
          UserDescription: Use this when the tree should pause for a fixed duration.
          Notes: Returns running until the configured duration has elapsed.
        """

        def __init__(self, duration_ms: int, base_timestamp: int = 0, name: str = "WaitForTimeNode"):
            super().__init__(name=name, node_type="WaitForTimeNode", 
                             node_category="wait",
                             icon=IconsFontAwesome5.ICON_HOURGLASS_HALF,
                             color = ColorPalette.GetColor("sky_blue"))
            self.duration_ms = duration_ms
            self._start_time_ms: Optional[int] = base_timestamp if base_timestamp > 0 else None

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # First tick → capture start timestamp
            if self._start_time_ms is None:
                self._start_time_ms = Utils.GetBaseTimestamp()

            now = Utils.GetBaseTimestamp()
            elapsed = now - self._start_time_ms

            if elapsed >= self.duration_ms:
                self._start_time_ms = None  # reset for next activation
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.NodeState.RUNNING

        def reset(self) -> None:
            super().reset()
            self._start_time_ms = None
    
    # --------------------------------------------------------
    #region SucceederNode
    # --------------------------------------------------------
    class SucceederNode(Node):
        """
        SucceederNode:
            - A simple leaf node that always returns SUCCESS.
            - Useful as a fallback or default branch inside Selector or Choice nodes.
            - Has no children and performs no action.
        
        Meta:
          Expose: true
          Audience: intermediate
          Display: Succeeder Node
          Purpose: Provide a branch that always succeeds.
          UserDescription: Use this when a tree needs a guaranteed success result.
          Notes: This node has no children and performs no action.
        """

        def __init__(self, name: str = "SucceederNode"):
            super().__init__(
                name=name,
                node_type="SucceederNode",
                node_category="leaf",
                icon=IconsFontAwesome5.ICON_CHECK,
                color=ColorPalette.GetColor("green")
            )

        def get_children(self) -> list:
            return []

        def _tick_impl(self) -> BehaviorTree.NodeState:
            return BehaviorTree.NodeState.SUCCESS
        
    # --------------------------------------------------------
    #region FailureNode
    # --------------------------------------------------------
        
    class FailerNode(Node):
        """
        FailerNode:
            - A simple leaf node that always returns FAILURE.
            - Useful for explicitly forcing a failure branch inside Selector or Choice nodes.
            - Has no children and performs no action.
        
        Meta:
          Expose: true
          Audience: intermediate
          Display: Failer Node
          Purpose: Provide a branch that always fails.
          UserDescription: Use this when a tree needs a guaranteed failure result.
          Notes: This node has no children and performs no action.
        """

        def __init__(self, name: str = "FailerNode"):
            super().__init__(
                name=name,
                node_type="FailerNode",
                node_category="leaf",
                icon=IconsFontAwesome5.ICON_TIMES,
                color=ColorPalette.GetColor("red")
            )

        def get_children(self) -> list:
            return []

        def _tick_impl(self) -> BehaviorTree.NodeState:
            return BehaviorTree.NodeState.FAILURE


    # --------------------------------------------------------
    #region BehaviorTree Class
    # --------------------------------------------------------
    def __init__(self, root: Node):
        self.root: BehaviorTree.Node = root
        self.blackboard = {} # Shared data storage for the tree
        
    def _propagate_blackboard(self, node: "BehaviorTree.Node"):
        """
        Assigns this tree’s blackboard to `node` and all its descendants.
        Ensures every node reads/writes the same shared dictionary.
        """
        node.blackboard = self.blackboard
        for child in node.get_children():
            self._propagate_blackboard(child)

    def tick(self) -> BehaviorTree.NodeState:
        """
        Ticks the root node once and returns its resulting NodeState.
        """
        self._propagate_blackboard(self.root)
        result = self.Node._normalize_state(self.root.tick())
        if result is None:
            raise TypeError("BehaviorTree root returned a non-NodeState result.")
        return result

    def reset(self) -> None:
        """
        Resets the root node and its subtree execution state.
        """
        self.root.reset()

    # -------- tree-level debug helpers --------
    def print(self) -> None:
        """
        Prints a plain-text representation of the behavior tree.
        """
        lines = self.root.print()
        for L in lines:
            print(repr(L))

    def draw(self, indent: int = 0) -> None:
        """
        Draws the behavior tree using PyImGui for debugging or visualization.
        """
        self.root.draw(indent=indent)
        
        

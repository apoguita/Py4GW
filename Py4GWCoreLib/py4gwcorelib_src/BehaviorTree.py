from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Callable, List, Optional
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
    BehaviorTree:
        - Wraps a root node and manages blackboard propagation.
        - Provides a single `tick()` entry point for running the whole tree.
        - Owns a shared blackboard dictionary accessible by all nodes.
        - Includes optional helpers for printing/drawing the structure.
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
        Base class for all Behaviour Tree nodes.

        Responsibilities:
            - Provides a unified tick() wrapper around `_tick_impl()`.
            - Tracks timing, tick count, and the last returned state.
            - Stores and propagates a shared blackboard dict.
            - Allows subclasses to implement custom behavior via `_tick_impl()`.

        Behavior:
            - tick() handles timing and metadata, then calls `_tick_impl()`.
            - `_tick_impl()` must return a NodeState (SUCCESS / FAILURE / RUNNING).
            - `reset()` clears transient execution state; subclasses may override it.
            - `get_children()` returns child nodes (leaf nodes return an empty list).

        Common Data:
            - id: unique identifier for this node instance.
            - name: display-friendly name (defaults to class name).
            - node_type: logical category (Action, Sequence, Selector, etc.).
            - icon/color: used for UI rendering.
            - last_state: state returned by the most recent tick().
            - tick_count: number of tick() calls processed.
            - blackboard: shared dictionary for passing values between nodes.

        Timing Metrics:
            - last_tick_time_ms: execution time of the last `_tick_impl()` call.
            - run_last_duration_ms: duration of the most recent RUNNING stretch.
            - run_accumulated_ms: total time spent in RUNNING.
        """

        def __init__(self, name: str = "", node_type: str = "",icon: str = "", color: Color = ColorPalette.GetColor("white")):
            self.id: str = uuid.uuid4().hex
            self.name: str = name or self.__class__.__name__
            self.node_type: str = node_type or self.__class__.__name__
            self.icon: str = icon if icon else IconsFontAwesome5.ICON_CIRCLE
            self.color: Color = color

            self.last_state: Optional[BehaviorTree.NodeState] = None
            self.tick_count: int = 0
            self.blackboard: dict = {}

            # ---- execution timing ----
            self.last_tick_time_ms: float = 0.0
            self.total_time_ms: float = 0.0
            self.avg_time_ms: float = 0.0
            
            self.run_start_time: Optional[int] = None
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

            result = self._tick_impl()   # <--- overridden in subclasses

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
                if self.run_start_time is None:
                    self.run_start_time = now
                # Update current duration
                self.run_last_duration_ms = now - self.run_start_time

            else:
                # Node just finished (SUCCESS or FAILURE)
                if self.run_start_time is not None:
                    # accumulate real active time
                    self.run_last_duration_ms = now - self.run_start_time
                    self.run_accumulated_ms += self.run_last_duration_ms
                    self.run_start_time = None  # reset for next activation

            self.last_state = result
            return result
        
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

            - [Selector] Selector
            ├─ [Condition] AlreadyInMap
            └─ [Sequence] TravelSequence
                ├─ [Action] TravelAction
                ├─ [WaitForTime] WaitForTime
                └─ [Wait] TravelReady
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
            if ms < 1000:
                return f"{ms:.3f} ms"
            else:
                return f"{ms/1000:.4f} s"
    
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
            #PyImGui.text(f"Start Time:  {self.run_start_time:.3f} ms")
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
        """

        def __init__(self, action_fn, aftercast_ms: int = 0,
                    name: str = "Action"):
            super().__init__(name=name,
                            node_type="Action",
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
        """

        def __init__(self, condition_fn, name: str = "Condition"):
            super().__init__(name=name, node_type="Condition",
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
        """

        def __init__(self, children=None, name: str = "Sequence"):
            super().__init__(name=name, node_type="Sequence", 
                             icon=IconsFontAwesome5.ICON_SORT_AMOUNT_DOWN_ALT,
                             color= ColorPalette.GetColor("dodger_blue"))
            self.children: List[BehaviorTree.Node] = children or []
            self.current: int = 0

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def _tick_impl(self) -> BehaviorTree.NodeState:
            while self.current < len(self.children):
                # ---- BLACKBOARD SUPPORT ----
                child = self.children[self.current]
                child.blackboard = self.blackboard
                # ----------------------------

                result = child.tick()

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    self.current = 0
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING

                if result == BehaviorTree.NodeState.FAILURE:
                    self.current = 0
                    return BehaviorTree.NodeState.FAILURE

                # SUCCESS → continue to next child
                self.current += 1

            # Completed sequence
            self.current = 0
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
        """

        def __init__(self, children=None, name: str = "Selector"):
            super().__init__(name=name, node_type="Selector", 
                             icon=IconsFontAwesome5.ICON_LIST_CHECK,
                             color= ColorPalette.GetColor("turquoise"))
            self.children: List[BehaviorTree.Node] = children or []
            self.current: int = 0

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def _tick_impl(self) -> BehaviorTree.NodeState:
            while self.current < len(self.children):
                # ----- BLACKBOARD -----
                child = self.children[self.current]
                child.blackboard = self.blackboard
                # -----------------------

                result = child.tick()

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    self.current = 0
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING

                if result == BehaviorTree.NodeState.SUCCESS:
                    self.current = 0
                    return BehaviorTree.NodeState.SUCCESS

                # FAILURE → continue to next child
                self.current += 1

            # All children failed
            self.current = 0
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
        """

        def __init__(self, children=None, name: str = "Choice"):
            super().__init__(name=name, node_type="Choice", 
                             icon=IconsFontAwesome5.ICON_ARROW_UP_1_9,
                             color= ColorPalette.GetColor("olive"))
            self.children: List[BehaviorTree.Node] = children or []

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def _tick_impl(self) -> BehaviorTree.NodeState:
            for child in self.children:
                # ----- BLACKBOARD -----
                child.blackboard = self.blackboard
                # ----------------------

                result = child.tick()

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    return BehaviorTree.NodeState.FAILURE

                # The FIRST non-failure result is returned immediately
                if result != BehaviorTree.NodeState.FAILURE:
                    return result

            # All children returned FAILURE
            return BehaviorTree.NodeState.FAILURE
        
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
        """

        def __init__(self, child: "BehaviorTree.Node", repeat_count: int = 1, name: str = "Repeater"):
            super().__init__(name=name, node_type="Repeater", 
                             icon=IconsFontAwesome5.ICON_HISTORY,
                             color= ColorPalette.GetColor("light_green"))
            self.child = child
            self.repeat_count = repeat_count
            self.current_count: int = 0

        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # ----- Blackboard -----
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # -----------------------

            while self.current_count < self.repeat_count:
                result = self.child.tick()

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{self.child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    self.current_count = 0
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING

                # On SUCCESS or FAILURE, increment and continue
                self.current_count += 1

            # Completed all repetitions → reset counter
            self.current_count = 0
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
        """

        def __init__(self, child: "BehaviorTree.Node", timeout_ms: int = 0, name: str = "RepeaterUntilSuccess"):
            super().__init__(name=name, node_type="RepeaterUntilSuccess", 
                             icon=IconsFontAwesome5.ICON_ROTATE_RIGHT,
                             color= ColorPalette.GetColor("light_yellow"))
            self.child = child
            self.timeout_ms = timeout_ms
            self.start_time = None

        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # ---------- INIT TIME ----------
            if self.start_time is None:
                self.start_time = Utils.GetBaseTimestamp()

            # ---------- TIMEOUT CHECK ----------
            if self.timeout_ms > 0:
                elapsed = Utils.GetBaseTimestamp() - self.start_time
                if elapsed >= self.timeout_ms:
                    self.start_time = None
                    return BehaviorTree.NodeState.FAILURE

            # ---------- BLACKBOARD ----------
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # --------------------------------

            # ---------- CHILD EXECUTION LOOP ----------
            while True:
                result = self.child.tick()

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
                    self.start_time = None  # reset fully for next run
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
        """

        def __init__(self, child: "BehaviorTree.Node", timeout_ms: int = 0, name: str = "RepeaterUntilFailure"):
            super().__init__(name=name, node_type="RepeaterUntilFailure", 
                             icon=IconsFontAwesome5.ICON_ROTATE_LEFT,
                             color= ColorPalette.GetColor("light_pink"))
            self.child = child
            self.timeout_ms = timeout_ms
            self.start_time = None
            
        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # ---------- INIT TIME ----------
            if self.start_time is None:
                self.start_time = Utils.GetBaseTimestamp()

            # ---------- TIMEOUT CHECK ----------
            if self.timeout_ms > 0:
                elapsed = Utils.GetBaseTimestamp() - self.start_time
                if elapsed >= self.timeout_ms:
                    self.start_time = None
                    return BehaviorTree.NodeState.FAILURE

            # ---------- BLACKBOARD ----------
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # ----------------------------------

            # ---------- CHILD EXECUTION LOOP ----------
            while True:
                result = self.child.tick()

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
                    self.start_time = None  # reset for next run
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
        """

        def __init__(self, child: "BehaviorTree.Node", timeout_ms: int = 0, name: str = "RepeaterForever"):
            super().__init__(name=name, node_type="RepeaterForever", 
                             icon=IconsFontAwesome5.ICON_INFINITY,
                             color= ColorPalette.GetColor("creme"))
            self.child = child
            self.timeout_ms = timeout_ms
            self.start_time = None
            
        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # ---------- INIT TIME ----------
            if self.start_time is None:
                self.start_time = Utils.GetBaseTimestamp()
                
            # ---------- TIMEOUT CHECK ----------
            if self.timeout_ms > 0:
                elapsed = Utils.GetBaseTimestamp() - self.start_time
                if elapsed >= self.timeout_ms:
                    self.start_time = None
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
        """

        def __init__(self, children=None, name: str = "Parallel"):
            super().__init__(name=name, node_type="Parallel", 
                             icon=IconsFontAwesome5.ICON_PROJECT_DIAGRAM,
                             color= ColorPalette.GetColor("light_purple"))
            self.children: List[BehaviorTree.Node] = children or []

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # --- blackboard support ---
            if self.blackboard is not None:
                for child in self.children:
                    child.blackboard = self.blackboard
            # ---------------------------

            all_success = True

            for child in self.children:
                result = child.tick()

                if result is None:
                    ConsoleLog(
                        "BT",
                        f"ERROR: Node '{child.name}' returned None!",
                        Console.MessageType.Error
                    )
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.FAILURE:
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    all_success = False

            if all_success:
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
        """

        def __init__(self, subtree_fn: Callable[["BehaviorTree.Node"], "BehaviorTree"], name: str = "Subtree"):
            if not callable(subtree_fn):
                raise TypeError("SubtreeNode requires a callable returning a BehaviorTree.")

            super().__init__(
                name=name,
                node_type="SubtreeNode",
                icon=IconsFontAwesome5.ICON_SITEMAP,
                color=ColorPalette.GetColor("light_green")
            )

            self._factory = subtree_fn
            self._subtree: "BehaviorTree | None" = None
        
        def reset(self):
            super().reset()
            if self._subtree is not None:
                self._subtree.root.reset()

        def _ensure_subtree(self):
            """
            Create the subtree only when the node is ticked for the first time,
            and pass THIS node to the factory, allowing dynamic values.
            """
            if self._subtree is None:
                tree = self._factory(self)
                if tree is None:
                    raise ValueError("subtree_fn() returned None; expected a BehaviorTree.")
                self._subtree = tree

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
        """

        def __init__(self, child: "BehaviorTree.Node", name: str = "Inverter"):
            super().__init__(name=name, node_type="Inverter", 
                             icon=IconsFontAwesome5.ICON_CIRCLE_MINUS,
                             color= ColorPalette.GetColor("purple"))
            self.child = child

        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # ----- BLACKBOARD -----
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # -----------------------

            # Tick child
            result = self.child.tick()

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
        """

        def __init__(self, check_fn, timeout_ms: int = 0, name: str = "Wait"):
            super().__init__(name=name, node_type="Wait", 
                             icon=IconsFontAwesome5.ICON_HAND,
                             color = ColorPalette.GetColor("light_cyan"))
            self.check_fn = check_fn
            self.timeout_ms = timeout_ms
            self.start_time: Optional[int] = None

        def _tick_impl(self) -> BehaviorTree.NodeState:
            now = Utils.GetBaseTimestamp()

            # start timer on first tick
            if self.start_time is None:
                self.start_time = now

            # run check
            result = self.check_fn()

            # invalid return
            if result is None:
                ConsoleLog("BT", f"ERROR: Node '{self.name}' returned None!", Console.MessageType.Error)
                self.start_time = None
                return BehaviorTree.NodeState.FAILURE

            # pass through SUCCESS
            if result == BehaviorTree.NodeState.SUCCESS:
                self.start_time = None
                return BehaviorTree.NodeState.SUCCESS

            # pass through FAILURE
            if result == BehaviorTree.NodeState.FAILURE:
                self.start_time = None
                return BehaviorTree.NodeState.FAILURE

            # still running → check timeout
            if self.timeout_ms > 0:
                if (now - self.start_time) >= self.timeout_ms:
                    self.start_time = None
                    return BehaviorTree.NodeState.FAILURE

            # continue waiting
            return BehaviorTree.NodeState.RUNNING
     
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
        """

        def __init__(self, condition_fn,
                    throttle_interval_ms: int = 100,
                    timeout_ms: int = 0,
                    name: str = "WaitUntil"):

            super().__init__(
                name=name,
                node_type="WaitUntil",
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

            self.start_time = None
            self.last_check_time = None

        def _tick_impl(self) -> BehaviorTree.NodeState:
            now = Utils.GetBaseTimestamp()

            # --- INIT ---
            if self.start_time is None:
                self.start_time = now
                self.last_check_time = 0
                #ConsoleLog("WaitUntilNode", f"[{self.name}] Init start_time={self.start_time}", log=True)

            # --- TIMEOUT ---
            if self.timeout_ms > 0 and (now - self.start_time) >= self.timeout_ms:
                #ConsoleLog("WaitUntilNode",f"[{self.name}] TIMEOUT exceeded ({now - self.start_time} ms >= {self.timeout_ms})",log=True)
                self.start_time = None
                self.last_check_time = None
                return BehaviorTree.NodeState.FAILURE

            # --- THROTTLE ---
            if self.last_check_time and ((now - self.last_check_time) < self.interval_ms):
                #ConsoleLog("WaitUntilNode",f"[{self.name}] Throttled ({now - self.last_check_time} < {self.interval_ms})",log=True)
                return BehaviorTree.NodeState.RUNNING

            self.last_check_time = now

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

            # --- NodeState ---
            if isinstance(result, BehaviorTree.NodeState):
                #ConsoleLog("WaitUntilNode", f"[{self.name}] Returning NodeState: {result}",log=True)
                
                # FIX: reset state so next tick does not throttle
                self.start_time = None
                self.last_check_time = None
                
                return result

            # --- BOOL ---
            if isinstance(result, bool):
                state = (BehaviorTree.NodeState.SUCCESS if result
                        else BehaviorTree.NodeState.FAILURE)

                #ConsoleLog("WaitUntilNode",f"[{self.name}] Converted bool → {state}",log=True)
                self.start_time = None
                self.last_check_time = None
                return state


            # --- INVALID ---
            #ConsoleLog("WaitUntilNode",
            #        f"[{self.name}] INVALID return type from condition_fn: {type(result).__name__}",
            #        log=True)

            raise TypeError(
                f"WaitUntilNode expected bool or NodeState, got: {type(result).__name__}"
            )


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
        """

        def __init__(self, condition_fn,
                    throttle_interval_ms: int = 100,
                    timeout_ms: int = 0,
                    name: str = "WaitUntilSuccess"):

            super().__init__(
                name=name,
                node_type="WaitUntilSuccess",
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

            self.start_time = None
            self.last_check_time = None

        def _tick_impl(self) -> BehaviorTree.NodeState:
            now = Utils.GetBaseTimestamp()

            # --- INIT ---
            if self.start_time is None:
                self.start_time = now
                self.last_check_time = now
                ConsoleLog("WaitUntilSuccessNode",
                    f"[{self.name}] Init start_time={self.start_time}", log=True)

            # --- TIMEOUT ---
            if self.timeout_ms > 0 and (now - self.start_time) >= self.timeout_ms:
                ConsoleLog("WaitUntilSuccessNode",
                    f"[{self.name}] TIMEOUT ({now - self.start_time} >= {self.timeout_ms})",
                    log=True)
                self.start_time = None
                self.last_check_time = None
                return BehaviorTree.NodeState.FAILURE

            # --- THROTTLE ---
            if self.last_check_time and ((now - self.last_check_time) < self.interval_ms):
                ConsoleLog("WaitUntilSuccessNode",
                    f"[{self.name}] Throttled ({now - self.last_check_time} < {self.interval_ms})",
                    log=True)
                return BehaviorTree.NodeState.RUNNING

            self.last_check_time = now

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

            # --- Normalize bool ---
            if isinstance(result, bool):
                result = (BehaviorTree.NodeState.SUCCESS if result
                        else BehaviorTree.NodeState.FAILURE)

            # --- SUCCESS → done ---
            if result == BehaviorTree.NodeState.SUCCESS:
                ConsoleLog("WaitUntilSuccessNode",
                    f"[{self.name}] Returning SUCCESS",
                    log=True)
                self.start_time = None
                self.last_check_time = None
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
        """

        def __init__(self, condition_fn,
                    throttle_interval_ms: int = 100,
                    timeout_ms: int = 0,
                    name: str = "WaitUntilFailure"):

            super().__init__(
                name=name,
                node_type="WaitUntilFailure",
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

            self.start_time = None
            self.last_check_time = None

        def _tick_impl(self) -> BehaviorTree.NodeState:
            now = Utils.GetBaseTimestamp()

            # --- INIT ---
            if self.start_time is None:
                self.start_time = now
                self.last_check_time = now
                ConsoleLog("WaitUntilFailureNode",
                    f"[{self.name}] Init start_time={self.start_time}", log=True)

            # --- TIMEOUT ---
            if self.timeout_ms > 0 and (now - self.start_time) >= self.timeout_ms:
                ConsoleLog("WaitUntilFailureNode",
                    f"[{self.name}] TIMEOUT ({now - self.start_time} >= {self.timeout_ms})",
                    log=True)
                self.start_time = None
                self.last_check_time = None
                return BehaviorTree.NodeState.FAILURE

            # --- THROTTLE ---
            if self.last_check_time and ((now - self.last_check_time) < self.interval_ms):
                ConsoleLog("WaitUntilFailureNode",
                    f"[{self.name}] Throttled ({now - self.last_check_time} < {self.interval_ms})",
                    log=True)
                return BehaviorTree.NodeState.RUNNING

            self.last_check_time = now

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

            # --- Normalize bool ---
            if isinstance(result, bool):
                result = (BehaviorTree.NodeState.SUCCESS if result
                        else BehaviorTree.NodeState.FAILURE)

            # --- FAILURE → this node SUCCESS ---
            if result == BehaviorTree.NodeState.FAILURE:
                ConsoleLog("WaitUntilFailureNode",
                    f"[{self.name}] Returning SUCCESS (condition FAILED)",
                    log=True)
                self.start_time = None
                self.last_check_time = None
                return BehaviorTree.NodeState.SUCCESS

            # --- Otherwise retry (SUCCESS or RUNNING) ---
            ConsoleLog("WaitUntilFailureNode",
                f"[{self.name}] Retry (result={result})",
                log=True)

            return BehaviorTree.NodeState.RUNNING



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
        """

        def __init__(self, duration_ms: int, base_timestamp: int = 0, name: str = "WaitForTime"):
            super().__init__(name=name, node_type="WaitForTime", 
                             icon=IconsFontAwesome5.ICON_HOURGLASS_HALF,
                             color = ColorPalette.GetColor("sky_blue"))
            self.duration_ms = duration_ms
            self.start_time: Optional[int] = base_timestamp if base_timestamp > 0 else None

        def _tick_impl(self) -> BehaviorTree.NodeState:
            # First tick → capture start timestamp
            if self.start_time is None:
                self.start_time = Utils.GetBaseTimestamp()

            now = Utils.GetBaseTimestamp()
            elapsed = now - self.start_time

            if elapsed >= self.duration_ms:
                self.start_time = None  # reset for next activation
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.NodeState.RUNNING
    
    # --------------------------------------------------------
    #region SucceederNode
    # --------------------------------------------------------
    class SucceederNode(Node):
        """
        SucceederNode:
            - A simple leaf node that always returns SUCCESS.
            - Useful as a fallback or default branch inside Selector or Choice nodes.
            - Has no children and performs no action.
        """

        def __init__(self, name: str = "Succeeder"):
            super().__init__(
                name=name,
                node_type="Succeeder",
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
        """

        def __init__(self, name: str = "Failer"):
            super().__init__(
                name=name,
                node_type="Failer",
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
    """
    BehaviorTree:
        - Wraps a root node and manages blackboard propagation.
        - Provides a single `tick()` entry point for running the whole tree.
        - Owns a shared blackboard dictionary accessible by all nodes.
        - Includes optional helpers for printing/drawing the structure.
    """

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
        return self.root.tick()

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
        
        
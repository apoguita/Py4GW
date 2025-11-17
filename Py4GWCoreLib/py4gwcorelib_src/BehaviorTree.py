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

        Metadata:
        - id:        unique identifier (stable per node instance)
        - name:      user-friendly label (can be passed in or default to class name)
        - node_type: logical kind of node (Action, Condition, Sequence, Selector, etc.)
        - last_state: last BehaviorTree.NodeState returned by tick()
        - tick_count: how many times this node was ticked
        """

        def __init__(self, name: str = "", node_type: str = "", icon: str = "", color: Color = ColorPalette.GetColor("white")):
            self.id: str = uuid.uuid4().hex
            self.name: str = name or self.__class__.__name__
            self.node_type: str = node_type or self.__class__.__name__
            self.icon: str = icon if icon else IconsFontAwesome5.ICON_CIRCLE
            self.color: Color = color
            self.last_state: Optional[BehaviorTree.NodeState] = None
            self.tick_count: int = 0
            self.blackboard: dict = {}

        @abstractmethod
        def tick(self) -> BehaviorTree.NodeState:
            """
            Execute one logical step of this node and return its BehaviorTree.NodeState.
            """
            pass
        

        # -------- metadata helpers --------
        def _update_metadata(self, result: BehaviorTree.NodeState) -> None:
            self.last_state = result
            self.tick_count += 1

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
            PyImGui.text_colored(f" {self.name}({self.tick_count})", color)

            # ----- IF NODE IS COLLAPSED -----
            if not open_:
                return  # DO NOT draw children

            # ----- IF NODE IS EXPANDED -----
            # Draw metadata
            PyImGui.text(f"Ticks: {self.tick_count}")
            state_str = self.last_state.name if self.last_state else "NONE"
            PyImGui.text(f"State: {state_str}")

            # Draw children
            for child in self.get_children():
                child.draw(indent + 1)

            PyImGui.tree_pop()


        
    # --------------------------------------------------------
    #region ActionNode
    # -------------------------------------------------------- 
    class ActionNode(Node):
        """
        Runs an action_fn once (must return SUCCESS/FAILURE/RUNNING),
        then waits duration_ms before returning SUCCESS.
        Useful when every action needs a delay after execution.
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

        def tick(self) -> BehaviorTree.NodeState:
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
                
                self._update_metadata(result)

                # If action still running → return RUNNING
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
                self._update_metadata(final)
                self._action_done = False
                self._action_result = None
                self._start_time = None
                return final  # SUCCESS or FAILURE (propagates action result)

            self._update_metadata(BehaviorTree.NodeState.RUNNING)
            return BehaviorTree.NodeState.RUNNING
        
    # --------------------------------------------------------
    #region ConditionNode
    # --------------------------------------------------------     

    class ConditionNode(Node):
        """
        Evaluates a condition function.
        
        - If the condition_fn returns a boolean → convert to SUCCESS/FAILURE.
        - If it returns a NodeState → use it directly.
        - Supports condition_fn() and condition_fn(node).
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

        def tick(self) -> BehaviorTree.NodeState:
            # Call with or without node depending on signature
            if self._accepts_node:
                result = self.condition_fn(self)
            else:
                result = self.condition_fn()

            # ----- CASE 1: result is a NodeState -----
            if isinstance(result, BehaviorTree.NodeState):
                final = result

            # ----- CASE 2: result is boolean -----
            elif isinstance(result, bool):
                final = (BehaviorTree.NodeState.SUCCESS
                        if result
                        else BehaviorTree.NodeState.FAILURE)

            # ----- CASE 3: invalid return type -----
            else:
                raise TypeError(
                    f"ConditionNode expected bool or NodeState, got: {type(result).__name__}"
                )

            self._update_metadata(final)
            return final

         
    # --------------------------------------------------------
    #region SequenceNode
    # --------------------------------------------------------
    class SequenceNode(Node):
        """
        Sequence:
        - Ticks children in order.
        - If a child FAILS -> whole sequence FAILS.
        - If a child RUNS  -> sequence RUNNING and will resume from that child.
        - Only when all children SUCCESS -> sequence SUCCESS.
        """

        def __init__(self, children=None, name: str = "Sequence"):
            super().__init__(name=name, node_type="Sequence", 
                             icon=IconsFontAwesome5.ICON_SORT_AMOUNT_DOWN_ALT,
                             color= ColorPalette.GetColor("dodger_blue"))
            self.children: List[BehaviorTree.Node] = children or []
            self.current: int = 0

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def tick(self) -> BehaviorTree.NodeState:
            while self.current < len(self.children):
                # --- BLACKBOARD SUPPORT (added) ---
                child = self.children[self.current]
                child.blackboard = self.blackboard
                # ----------------------------------
                
                result = self.children[self.current].tick()
                
                if result is None:
                    # Illegal state: node did not return a valid NodeState
                    ConsoleLog("BT", f"ERROR: Node '{self.children[self.current].name}' returned None!", Console.MessageType.Error)
                    self.current = 0
                    self._update_metadata(BehaviorTree.NodeState.FAILURE)
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    self._update_metadata(BehaviorTree.NodeState.RUNNING)
                    return BehaviorTree.NodeState.RUNNING

                if result == BehaviorTree.NodeState.FAILURE:
                    self.current = 0
                    self._update_metadata(BehaviorTree.NodeState.FAILURE)
                    return BehaviorTree.NodeState.FAILURE

                # Success → go to next child
                self.current += 1

            # Completed sequence
            self.current = 0
            self._update_metadata(BehaviorTree.NodeState.SUCCESS)
            return BehaviorTree.NodeState.SUCCESS

    # --------------------------------------------------------
    #region SelectorNode
    # --------------------------------------------------------
    class SelectorNode(Node):
        """
        Selector:
        - Ticks children in order.
        - If a child SUCCEEDS -> whole selector SUCCEEDS.
        - If a child RUNS     -> selector RUNNING and will resume from that child.
        - Only when all children FAIL -> selector FAILURE.
        """

        def __init__(self, children=None, name: str = "Selector"):
            super().__init__(name=name, node_type="Selector", 
                             icon=IconsFontAwesome5.ICON_LIST_CHECK,
                             color= ColorPalette.GetColor("turquoise"))
            self.children: List[BehaviorTree.Node] = children or []
            self.current: int = 0

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def tick(self) -> BehaviorTree.NodeState:
            while self.current < len(self.children):
                # --- BLACKBOARD SUPPORT (added) ---
                child = self.children[self.current]
                child.blackboard = self.blackboard
                # ----------------------------------
                
                result = self.children[self.current].tick()
                
                if result is None:
                    # Illegal state: node did not return a valid NodeState
                    ConsoleLog("BT", f"ERROR: Node '{self.children[self.current].name}' returned None!", Console.MessageType.Error)
                    self.current = 0
                    self._update_metadata(BehaviorTree.NodeState.FAILURE)
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    self._update_metadata(BehaviorTree.NodeState.RUNNING)
                    return BehaviorTree.NodeState.RUNNING

                if result == BehaviorTree.NodeState.SUCCESS:
                    self.current = 0
                    self._update_metadata(BehaviorTree.NodeState.SUCCESS)
                    return BehaviorTree.NodeState.SUCCESS

                # Failure → try next
                self.current += 1

            # All failed
            self.current = 0
            self._update_metadata(BehaviorTree.NodeState.FAILURE)
            return BehaviorTree.NodeState.FAILURE
      
    # --------------------------------------------------------
    #region ChoiceNode
    # --------------------------------------------------------  
    class ChoiceNode(Node):
        """
        Choice:
        - Ticks children in order.
        - Returns the state of the first child that is not FAILURE.
        - If all children FAIL -> choice FAILURE.
        """

        def __init__(self, children=None, name: str = "Choice"):
            super().__init__(name=name, node_type="Choice", 
                             icon=IconsFontAwesome5.ICON_ARROW_UP_1_9,
                             color= ColorPalette.GetColor("olive"))
            self.children: List[BehaviorTree.Node] = children or []

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def tick(self) -> BehaviorTree.NodeState:
            for child in self.children:
                # --- BLACKBOARD SUPPORT (added) ---
                child.blackboard = self.blackboard
                # ----------------------------------
                result = child.tick()
                
                if result is None:
                    # Illegal state: node did not return a valid NodeState
                    ConsoleLog("BT", f"ERROR: Node '{self.children[self.current].name}' returned None!", Console.MessageType.Error)
                    self.current = 0
                    self._update_metadata(BehaviorTree.NodeState.FAILURE)
                    return BehaviorTree.NodeState.FAILURE

                if result != BehaviorTree.NodeState.FAILURE:
                    self._update_metadata(result)
                    return result

            # All failed
            self._update_metadata(BehaviorTree.NodeState.FAILURE)
            return BehaviorTree.NodeState.FAILURE
        
    # --------------------------------------------------------
    #region RepeaterNode
    # --------------------------------------------------------
    class RepeaterNode(Node):   
        """
        Repeater:
        - Ticks its child a fixed number of times.
        - Always returns SUCCESS when done.
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

        def tick(self) -> BehaviorTree.NodeState:
            # --- blackboard support ---
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # --------------------------
            while self.current_count < self.repeat_count:
                result = self.child.tick()
                
                if result is None:
                    # Illegal state: node did not return a valid NodeState
                    ConsoleLog("BT", f"ERROR: Node '{self.child.name}' returned None!", Console.MessageType.Error)
                    self.current_count = 0
                    self._update_metadata(BehaviorTree.NodeState.FAILURE)
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    self._update_metadata(BehaviorTree.NodeState.RUNNING)
                    return BehaviorTree.NodeState.RUNNING

                # On SUCCESS or FAILURE, increment count and repeat
                self.current_count += 1

            # Completed all repetitions
            self.current_count = 0
            self._update_metadata(BehaviorTree.NodeState.SUCCESS)
            return BehaviorTree.NodeState.SUCCESS
        
    # --------------------------------------------------------
    #region RepeaterUntilSuccessNode
    # --------------------------------------------------------
    class RepeaterUntilSuccessNode(Node):
        """
        Repeater Until Success:
        - Ticks its child until it returns SUCCESS.
        - Always returns SUCCESS when done.
        """

        def __init__(self, child: "BehaviorTree.Node", name: str = "RepeaterUntilSuccess"):
            super().__init__(name=name, node_type="RepeaterUntilSuccess", 
                             icon=IconsFontAwesome5.ICON_ROTATE_RIGHT,
                             color= ColorPalette.GetColor("light_yellow"))
            self.child = child

        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def tick(self) -> BehaviorTree.NodeState:
            # --- blackboard support ---
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # --------------------------
            while True:
                result = self.child.tick()
                
                if result is None:
                    # Illegal state: node did not return a valid NodeState
                    ConsoleLog("BT", f"ERROR: Node '{self.child.name}' returned None!", Console.MessageType.Error)
                    self._update_metadata(BehaviorTree.NodeState.FAILURE)
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    self._update_metadata(BehaviorTree.NodeState.RUNNING)
                    return BehaviorTree.NodeState.RUNNING

                if result == BehaviorTree.NodeState.SUCCESS:
                    self._update_metadata(BehaviorTree.NodeState.SUCCESS)
                    return BehaviorTree.NodeState.SUCCESS

                # On FAILURE, repeat indefinitely
      
    # --------------------------------------------------------
    #region RepeaterUntilFailureNode
    # --------------------------------------------------------          
    class RepeaterUntilFailureNode(Node):
        """
        Repeater Until Failure:
        - Ticks its child until it returns FAILURE.
        - Always returns SUCCESS when done.
        """

        def __init__(self, child: "BehaviorTree.Node", name: str = "RepeaterUntilFailure"):
            super().__init__(name=name, node_type="RepeaterUntilFailure", 
                             icon=IconsFontAwesome5.ICON_ROTATE_LEFT,
                             color= ColorPalette.GetColor("light_pink"))
            self.child = child

        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def tick(self) -> BehaviorTree.NodeState:
            # --- blackboard support ---
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # --------------------------
            while True:
                result = self.child.tick()
                
                if result is None:
                    # Illegal state: node did not return a valid NodeState
                    ConsoleLog("BT", f"ERROR: Node '{self.child.name}' returned None!", Console.MessageType.Error)
                    self._update_metadata(BehaviorTree.NodeState.FAILURE)
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    self._update_metadata(BehaviorTree.NodeState.RUNNING)
                    return BehaviorTree.NodeState.RUNNING

                if result == BehaviorTree.NodeState.FAILURE:
                    self._update_metadata(BehaviorTree.NodeState.SUCCESS)
                    return BehaviorTree.NodeState.SUCCESS

                # On SUCCESS, repeat indefinitely
     
    # --------------------------------------------------------
    #region RepeaterForeverNode
    # --------------------------------------------------------           
    class RepeaterForeverNode(Node):
        """
        Repeater Forever:
        - Ticks its child indefinitely.
        - Always returns RUNNING.
        """

        def __init__(self, child: "BehaviorTree.Node", name: str = "RepeaterForever"):
            super().__init__(name=name, node_type="RepeaterForever", 
                             icon=IconsFontAwesome5.ICON_INFINITY,
                             color= ColorPalette.GetColor("creme"))
            self.child = child

        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def tick(self) -> BehaviorTree.NodeState:
            # --- blackboard support ---
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # --------------------------
            
            self.child.tick()
            self._update_metadata(BehaviorTree.NodeState.RUNNING)
            return BehaviorTree.NodeState.RUNNING

    # --------------------------------------------------------
    #region ParallelNode
    # --------------------------------------------------------
    
    class ParallelNode(Node):
        """
        Parallel:
        - Ticks all children every tick.
        - SUCCESS if all children SUCCESS.
        - FAILURE if any child FAILS.
        - RUNNING otherwise.
        """

        def __init__(self, children=None, name: str = "Parallel"):
            super().__init__(name=name, node_type="Parallel", 
                             icon=IconsFontAwesome5.ICON_PROJECT_DIAGRAM,
                             color= ColorPalette.GetColor("light_purple"))
            self.children: List[BehaviorTree.Node] = children or []

        def get_children(self) -> List["BehaviorTree.Node"]:
            return self.children

        def tick(self) -> BehaviorTree.NodeState:
            # --- blackboard support ---
            if self.blackboard is not None:
                for child in self.children:
                    child.blackboard = self.blackboard
            # ---------------------------
            
            all_success = True

            for child in self.children:
                result = child.tick()
                
                if result is None:
                    # Illegal state: node did not return a valid NodeState
                    ConsoleLog("BT", f"ERROR: Node '{child.name}' returned None!", Console.MessageType.Error)
                    self._update_metadata(BehaviorTree.NodeState.FAILURE)
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.FAILURE:
                    self._update_metadata(BehaviorTree.NodeState.FAILURE)
                    return BehaviorTree.NodeState.FAILURE

                if result == BehaviorTree.NodeState.RUNNING:
                    all_success = False

            if all_success:
                self._update_metadata(BehaviorTree.NodeState.SUCCESS)
                return BehaviorTree.NodeState.SUCCESS
            else:
                self._update_metadata(BehaviorTree.NodeState.RUNNING)
                return BehaviorTree.NodeState.RUNNING
            
    # --------------------------------------------------------
    #region SubtreeNode
    # --------------------------------------------------------
    
    class SubtreeNode(Node):
        """
        A subtree node that constructs its subtree lazily and **correctly at tick time**.
        subtree_fn receives this node as an argument, so it can read:
            - node.blackboard
            - external shared dict
            - dynamic data
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

        def _ensure_subtree(self):
            """
            Create the subtree only when the node is ticked for the first time,
            and pass THIS node to the factory, allowing dynamic values.
            """
            if self._subtree is None:
                tree = self._factory(self)   # <-- PASS THE NODE
                if tree is None:
                    raise ValueError("subtree_fn() returned None; expected a BehaviorTree.")
                self._subtree = tree

        def get_children(self) -> List["BehaviorTree.Node"]:
            # Return children *only after subtree is created*
            if self._subtree is not None:
                return [self._subtree.root]
            return []  # before ticking subtree isn't created yet

        def tick(self) -> BehaviorTree.NodeState:
            self._ensure_subtree()

            # --- guard + local var to satisfy Pylance and runtime ---
            tree = self._subtree
            if tree is None:
                raise RuntimeError("SubtreeNode: _subtree is None after _ensure_subtree().")
            # --------------------------------------------------------

            # --- blackboard support ---
            if self.blackboard is not None:
                tree.root.blackboard = self.blackboard
            # --------------------------

            result = tree.root.tick()
            self._update_metadata(result)
            return result

 
    # --------------------------------------------------------
    #region InverterNode
    # --------------------------------------------------------
    class InverterNode(Node):
        """
        Inverter:
        - SUCCESS -> FAILURE
        - FAILURE -> SUCCESS
        - RUNNING -> RUNNING
        """

        def __init__(self, child: "BehaviorTree.Node", name: str = "Inverter"):
            super().__init__(name=name, node_type="Inverter", 
                             icon=IconsFontAwesome5.ICON_CIRCLE_MINUS,
                             color= ColorPalette.GetColor("purple"))
            self.child = child

        def get_children(self) -> List["BehaviorTree.Node"]:
            return [self.child]

        def tick(self) -> BehaviorTree.NodeState:
            # --- blackboard support ---
            if self.blackboard is not None:
                self.child.blackboard = self.blackboard
            # --------------------------
        
            child_result = self.child.tick()
            
            if child_result is None:
                # Illegal state: node did not return a valid NodeState
                ConsoleLog("BT", f"ERROR: Node '{self.child.name}' returned None!", Console.MessageType.Error)
                self._update_metadata(BehaviorTree.NodeState.FAILURE)
                return BehaviorTree.NodeState.FAILURE

            if child_result == BehaviorTree.NodeState.SUCCESS:
                result = BehaviorTree.NodeState.FAILURE
            elif child_result == BehaviorTree.NodeState.FAILURE:
                result = BehaviorTree.NodeState.SUCCESS
            else:
                result = BehaviorTree.NodeState.RUNNING

            self._update_metadata(result)
            return result
        
    # --------------------------------------------------------
    # Wait WaitNode
    # --------------------------------------------------------
    class WaitNode(Node):
        """
        A node that repeatedly checks a function until it reports SUCCESS,
        or until timeout expires (if timeout_ms != 0).

        check_fn must return one of:
            BehaviorTree.NodeState.RUNNING
            BehaviorTree.NodeState.SUCCESS
            BehaviorTree.NodeState.FAILURE
        """

        def __init__(self, check_fn, timeout_ms: int = 0, name: str = "Wait"):
            super().__init__(name=name, node_type="Wait", 
                             icon=IconsFontAwesome5.ICON_HAND,
                             color = ColorPalette.GetColor("light_cyan"))
            self.check_fn = check_fn
            self.timeout_ms = timeout_ms
            self.start_time: Optional[int] = None

        def tick(self) -> BehaviorTree.NodeState:
            # --- blackboard support ---
            # Leaf node: no children to propagate to, nothing else needed.
            # node.blackboard is already available for check_fn via closure.
            # ---------------------------------------
        
            # Start timing on first tick
            if self.start_time is None:
                self.start_time = Utils.GetBaseTimestamp()

            # Execute the condition function
            result = self.check_fn()
            
            if result is None:
                # Illegal state: node did not return a valid NodeState
                ConsoleLog("BT", f"ERROR: Node '{self.name}' returned None!", Console.MessageType.Error)
                self.start_time = None
                self._update_metadata(BehaviorTree.NodeState.FAILURE)
                return BehaviorTree.NodeState.FAILURE

            # If SUCCESS or FAILURE → pass through immediately
            if result == BehaviorTree.NodeState.SUCCESS:
                self.start_time = None
                self._update_metadata(BehaviorTree.NodeState.SUCCESS)
                return BehaviorTree.NodeState.SUCCESS

            if result == BehaviorTree.NodeState.FAILURE:
                self.start_time = None
                self._update_metadata(BehaviorTree.NodeState.FAILURE)
                return BehaviorTree.NodeState.FAILURE

            # If still RUNNING, check timeout (if enabled)
            if self.timeout_ms > 0:
                now = Utils.GetBaseTimestamp()
                if (now - self.start_time) >= self.timeout_ms:
                    # timeout reached → FAILURE
                    self.start_time = None
                    self._update_metadata(BehaviorTree.NodeState.FAILURE)
                    return BehaviorTree.NodeState.FAILURE

            # Still waiting
            self._update_metadata(BehaviorTree.NodeState.RUNNING)
            return BehaviorTree.NodeState.RUNNING

    class WaitForTimeNode(Node):
        """
        Waits until a given amount of time (in milliseconds) has passed.
        Returns:
            RUNNING until time has elapsed
            SUCCESS once elapsed
        """

        def __init__(self, duration_ms: int, base_timestamp: int = 0, name: str = "WaitForTime"):
            super().__init__(name=name, node_type="WaitForTime", 
                             icon=IconsFontAwesome5.ICON_HOURGLASS_HALF,
                             color = ColorPalette.GetColor("sky_blue"))
            self.duration_ms = duration_ms
            self.start_time: Optional[int] = base_timestamp if base_timestamp > 0 else None

        def tick(self) -> BehaviorTree.NodeState:
            # --- blackboard support ---
            # Leaf node: no children to propagate to, nothing else needed.
            # node.blackboard is already available for check_fn via closure.
            # ---------------------------------------
            
            # First tick → capture start timestamp
            if self.start_time is None:
                self.start_time = Utils.GetBaseTimestamp()

            now = Utils.GetBaseTimestamp()
            elapsed = now - self.start_time

            if elapsed >= self.duration_ms:
                self.start_time = None  # reset for next activation
                self._update_metadata(BehaviorTree.NodeState.SUCCESS)
                return BehaviorTree.NodeState.SUCCESS

            self._update_metadata(BehaviorTree.NodeState.RUNNING)
            return BehaviorTree.NodeState.RUNNING

    # --------------------------------------------------------
    #region BehaviorTree Class
    # --------------------------------------------------------

    def __init__(self, root: Node):
        """
        A BehaviorTree is just a root node plus helpers
        for ticking and drawing the whole tree.
        """
        self.root: BehaviorTree.Node = root
        self.blackboard = {} # Shared data storage for the tree
        
    def _propagate_blackboard(self, node: "BehaviorTree.Node"):
        """
        Assign this tree's blackboard to the given node and all its children.
        This ensures every node can read/write self.blackboard.
        """
        node.blackboard = self.blackboard
        for child in node.get_children():
            self._propagate_blackboard(child)

    def tick(self) -> BehaviorTree.NodeState:
        """
        Tick the root node once and return its BehaviorTree.NodeState.
        """
        self._propagate_blackboard(self.root)
        return self.root.tick()

    # -------- tree-level debug helpers --------
    def print(self) -> None:
        """
        Print a text-based representation of the whole tree.
        """
        lines = self.root.print()
        for L in lines:
            print(repr(L))

    def draw(self, indent: int = 0) -> None:
        """
        Draw the whole tree using PyImGui.
        """
        self.root.draw(indent=indent)
        
        
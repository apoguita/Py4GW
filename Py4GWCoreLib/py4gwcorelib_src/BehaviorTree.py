from abc import ABC, abstractmethod
from enum import Enum
from .Timer import Timer

#region BehaviorTree
class BehaviorTree:
    class NodeState(Enum):
        RUNNING = 0
        SUCCESS = 1
        FAILURE = 2
 
    class Node(ABC):
        def __init__(self):
            self.state: "BehaviorTree.NodeState" = BehaviorTree.NodeState.RUNNING  # Default state

        @abstractmethod
        def tick(self) -> "BehaviorTree.NodeState":
            """This method should be implemented in subclasses to define behavior."""
            pass

        def run(self) -> "BehaviorTree.NodeState":
            """Executes the tick method and returns the node's current state."""
            self.state = self.tick()  # Calls the tick method
            return self.state

        def reset(self):
            """Resets the node's state to allow restarting the behavior tree."""
            self.state = BehaviorTree.NodeState.RUNNING

    class ActionNode(Node):
        def __init__(self, action):
            super().__init__()
            self.action = action  # The action function this node will execute

        def tick(self):
            """Executes the action and returns the result."""
            return self.action()  # Call the action function


    class ConditionNode(Node):
        def __init__(self, condition):
            super().__init__()
            self.condition = condition  # The condition function this node will evaluate

        def tick(self):
            """Checks the condition and returns the result."""
            if self.condition():  # Evaluate the condition function
                return BehaviorTree.NodeState.SUCCESS
            else:
                return BehaviorTree.NodeState.FAILURE

    class CompositeNode(Node):
        def __init__(self, children=None):
            super().__init__()
            self.children = children if children else []  # A list of child nodes

        def add_child(self, child):
            """Adds a child node to the composite node."""
            self.children.append(child)

        def reset(self):
            """Reset all child nodes' states."""
            for child in self.children:
                child.reset()
            super().reset()

    # Sequence Node - executes children in sequence
    class SequenceNode(CompositeNode):
        def tick(self):
            """Executes children in sequence."""
            for child in self.children:
                result = child.run()  # Run each child node
            
                if result == BehaviorTree.NodeState.FAILURE:
                    return BehaviorTree.NodeState.FAILURE  # Stop if any child fails
            
                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING  # If a child is still running, keep running
            
            return BehaviorTree.NodeState.SUCCESS  # Only return success if all children succeed


    # Selector Node - executes children in order, returns success if any succeed
    class SelectorNode(CompositeNode):
        def tick(self):
            """Executes children in order, returns success if any succeed."""
            for child in self.children:
                result = child.run()  # Run each child node
            
                if result == BehaviorTree.NodeState.SUCCESS:
                    return BehaviorTree.NodeState.SUCCESS  # Stop if any child succeeds
            
                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING  # If a child is still running, keep running

            return BehaviorTree.NodeState.FAILURE  # Only return failure if all children fail


    # Parallel Node - runs all children in parallel, succeeds or fails based on thresholds
    class ParallelNode(CompositeNode):
        def __init__(self, success_threshold=1, failure_threshold=1, children=None):
            super().__init__(children)
            self.success_threshold = success_threshold  # Number of successes needed for SUCCESS
            self.failure_threshold = failure_threshold  # Number of failures needed for FAILURE

        def tick(self):
            """Executes all children in parallel."""
            success_count = 0
            failure_count = 0

            for child in self.children:
                result = child.run()  # Run each child node

                if result == BehaviorTree.NodeState.SUCCESS:
                    success_count += 1
                elif result == BehaviorTree.NodeState.FAILURE:
                    failure_count += 1

                # Check if the success or failure threshold is reached
                if success_count >= self.success_threshold:
                    return BehaviorTree.NodeState.SUCCESS
                if failure_count >= self.failure_threshold:
                    return BehaviorTree.NodeState.FAILURE

            return BehaviorTree.NodeState.RUNNING  # If thresholds are not met, it's still running


    # Inverter Node - inverts the result of its child node
    class InverterNode(Node):
        def __init__(self, child):
            super().__init__()
            self.child = child  # The node to invert

        def tick(self):
            """Inverts the result of the child node."""
            result = self.child.run()  # Run the child node
        
            if result == BehaviorTree.NodeState.SUCCESS:
                return BehaviorTree.NodeState.FAILURE  # Invert SUCCESS to FAILURE
            elif result == BehaviorTree.NodeState.FAILURE:
                return BehaviorTree.NodeState.SUCCESS  # Invert FAILURE to SUCCESS
            else:
                return BehaviorTree.NodeState.RUNNING  # RUNNING remains unchanged

    # Succeeder Node - always returns success, regardless of child result
    class SucceederNode(Node):
        def __init__(self, child):
            super().__init__()
            self.child = child  # The node whose result will be modified

        def tick(self):
            """Succeeder always returns SUCCESS."""
            self.child.run()  # Run the child, but ignore its result
            return BehaviorTree.NodeState.SUCCESS  # Always return SUCCESS

    class RepeaterNode(Node):
        def __init__(self, child, repeat_interval=1000, repeat_limit=-1):
            """
            Initialize the RepeaterNode with an optional repeat limit.

            :param child: The child node to repeat.
            :param repeat_interval: Time in milliseconds between repetitions (cooldown period).
            :param repeat_limit: Maximum number of times to repeat (-1 for unlimited).
            """
            super().__init__()
            self.child = child  # The child node to repeat
            self.repeat_interval = repeat_interval  # Time in milliseconds between repetitions
            self.repeat_limit = repeat_limit  # Maximum number of repetitions (-1 for unlimited)
            self.current_repeats = 0  # Counter to track the number of repetitions
            self.timer = Timer()  # Instance of Timer class
            self.timer.Start()  # Start the timer immediately
            self.repetition_allowed = False  # Whether the child can be run again

        def tick(self):
            """Run the child node if the cooldown has passed and repeat limit is not reached."""
            # Check if the repeat limit has been reached
            if self.repeat_limit != -1 and self.current_repeats >= self.repeat_limit:
                return BehaviorTree.NodeState.SUCCESS  # Stop after reaching the repeat limit

            # If the repetition is allowed, run the child node
            if self.repetition_allowed:
                result = self.child.run()  # Run the child node

                if result in [BehaviorTree.NodeState.SUCCESS, BehaviorTree.NodeState.FAILURE]:
                    # After the child finishes, start the cooldown timer
                    self.timer.Start()
                    self.repetition_allowed = False  # Prevent running until the cooldown ends
                    self.current_repeats += 1  # Increment the repeat counter

                return result

            # Check if the cooldown has elapsed
            if self.timer.HasElapsed(self.repeat_interval):
                self.repetition_allowed = True  # Allow the next repetition
                self.timer.Stop()  # Reset the timer

            return BehaviorTree.NodeState.RUNNING  # Keep the node in the running state during cooldown

        def reset(self):
            """Reset the repeater node and the child state."""
            self.current_repeats = 0  # Reset the repeat count
            self.repetition_allowed = False  # Disallow immediate repetition
            self.timer.Start()  # Restart the timer
            self.child.reset()  # Reset the child node
            super().reset()  # Reset the node state

    class CreateBehaviorTree(SequenceNode):
        def __init__(self, nodes=None):
            # Initialize the behavior tree with a list of nodes (can be Sequence, Selector, etc.)
            super().__init__(nodes)
#endregion
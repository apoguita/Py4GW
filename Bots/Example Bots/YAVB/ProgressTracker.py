class ProgressTracker:
    def __init__(self):
        self.steps: list[tuple[str, float]] = []   # [(name, weight)]
        self.completed_weight: float = 0.0         # Total from past steps
        self.state: str = ""
        self.state_weight: float = 0.0
        self.state_percentage: float = 0.0
        self.reset()
        
    def reset(self):
        """
        Reset the progress tracker to initial state.
        """
        self.steps.clear()
        self.completed_weight = 0.0
        self.state = ""
        self.state_weight = 0.0
        self.state_percentage = 0.0

    def set_step(self, name: str, weight: float):
        """
        Start a new step with a given weight. Internally finalizes previous one.
        """
        if self.state:
            # Force complete previous step at 100%
            self.completed_weight += self.state_weight  # assume full completion
            self.state_percentage = 1.0  # just for reference
        self.steps.append((name, weight))
        self.state = name
        self.state_weight = weight
        self.state_percentage = 0.0
        
    def finalize_current_step(self):
        """
        Marks the current step as complete (100%) and adds to total progress.
        """
        if self.state:
            self.completed_weight += self.state_weight
            self.state_percentage = 1.0
            self.state = ""
            self.state_weight = 0.0

    def update_progress(self, percent: float):
        """
        Update the progress of the current step (0.0 to 1.0).
        """
        self.state_percentage = max(0.0, min(percent, 1.0))

    def get_overall_progress(self) -> float:
        """
        Return total progress: completed steps + current step's progress × weight.
        """
        return self.completed_weight + self.state_percentage * self.state_weight
    
    def get_step_name(self) -> str:
        """
        Return the name of the current step.
        """
        return self.state if self.state else "Idle"

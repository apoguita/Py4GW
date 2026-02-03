import time


class CooldownTimer:
    """
    A timer class for managing cooldowns.
    
    Unlike ThrottledTimer which starts immediately, CooldownTimer starts in an "expired" state
    (not in cooldown) and must be explicitly restarted to begin a cooldown period.
    
    Usage:
        cooldown = CooldownTimer(5000)  # 5 second cooldown
        
        # Initially not in cooldown
        if not cooldown.IsInCooldown():
            # Do something
            cooldown.Restart()  # Start the cooldown
        
        # Now in cooldown for 5 seconds
        if cooldown.IsInCooldown():
            # Skip action during cooldown
            pass
    """
    
    def __init__(self, cooldown_duration_ms: int):
        """
        Initialize a CooldownTimer.
        
        Args:
            cooldown_duration_ms: The cooldown duration in milliseconds
        """
        self.cooldown_duration = cooldown_duration_ms
        self.start_time = 0.0  # Initialize to 0, meaning not in cooldown
        
    def Restart(self) -> None:
        """
        Restart the cooldown timer, beginning a new cooldown period.
        """
        self.start_time = time.perf_counter()
        
    def IsInCooldown(self) -> bool:
        """
        Check if the timer is currently in cooldown.
        
        Returns:
            True if still in cooldown, False if cooldown has expired or never started
        """
        if self.start_time == 0.0:
            return False  # Never started, not in cooldown
        
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        return elapsed_ms < self.cooldown_duration
    
    def GetTimeRemaining(self) -> float:
        """
        Get the remaining cooldown time in milliseconds.
        
        Returns:
            Remaining time in milliseconds, or 0 if not in cooldown
        """
        if self.start_time == 0.0:
            return 0.0
        
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        remaining = self.cooldown_duration - elapsed_ms
        return max(0.0, remaining)
    
    def GetTimeElapsed(self) -> float:
        """
        Get the elapsed time since the cooldown started in milliseconds.
        
        Returns:
            Elapsed time in milliseconds, or 0 if never started
        """
        if self.start_time == 0.0:
            return 0.0
        
        return (time.perf_counter() - self.start_time) * 1000
    
    def Reset(self) -> None:
        """
        Reset the timer to its initial state (not in cooldown).
        This is different from Restart() which begins a new cooldown period.
        """
        self.start_time = 0.0
    
    def SetCooldownDuration(self, cooldown_duration_ms: int) -> None:
        """
        Change the cooldown duration.
        
        Args:
            cooldown_duration_ms: The new cooldown duration in milliseconds
        """
        self.cooldown_duration = cooldown_duration_ms
    
    def __repr__(self) -> str:
        if self.IsInCooldown():
            return f"<CooldownTimer in_cooldown=True remaining={self.GetTimeRemaining():.0f}ms>"
        return f"<CooldownTimer in_cooldown=False>"


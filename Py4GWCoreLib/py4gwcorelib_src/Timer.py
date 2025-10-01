import time

#region Timer
class Timer:
    def __init__(self):
        """Initialize the Timer object with default values."""
        self.start_time = 0.0
        self.paused_time = 0.0
        self.running = False
        self.paused = False

    def Start(self):
        """Start the timer."""
        self.Stop()
        if not self.running:
            self.start_time = time.perf_counter()  # High-precision time
            self.running = True
            self.paused = False
            self.paused_time = 0.0  # Reset paused time

    def Stop(self):
        """Stop the timer."""
        self.running = False
        self.paused = False
        
    def Reset(self):
        """Reset the timer."""
        self.Start()

    def Pause(self):
        """Pause the timer."""
        if self.running and not self.paused:
            self.paused_time = time.perf_counter() - self.start_time  # Capture elapsed time
            self.paused = True

    def Resume(self):
        """Resume the timer."""
        if self.running and self.paused:
            self.start_time = time.perf_counter() - self.paused_time  # Adjust start time
            self.paused = False

    def IsStopped(self):
        """Check if the timer is stopped."""
        return not self.running

    def IsRunning(self):
        """Check if the timer is running."""
        return self.running and not self.paused

    def IsPaused(self):
        """Check if the timer is paused."""
        return self.paused

    def GetElapsedTime(self):
        """Get the elapsed time in milliseconds."""
        if not self.running:
            return 0
        if self.paused:
            return self.paused_time * 1000  # Convert to milliseconds
        return (time.perf_counter() - self.start_time) * 1000  # Convert to milliseconds

    def HasElapsed(self, milliseconds):
        """Check if the specified time has elapsed."""
        if not self.running or self.paused:
            return False
        return self.GetElapsedTime() >= milliseconds

    def FormatElapsedTime(self, mask="hh:mm:ss:ms"):
        return FormatTime(self.GetElapsedTime(), mask)
    
    def __repr__(self):
        return f"<Timer running={self.IsRunning()}>"

def FormatTime(time_ms, mask="hh:mm:ss:ms"):
        """Get the formatted elapsed time string based on the mask provided."""
        ms = int(time_ms)
        seconds = ms // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        milliseconds = ms % 1000  # Directly get remaining milliseconds

        # Apply the mask
        formatted_time = mask
        if "hh" in mask:
            formatted_time = formatted_time.replace("hh", f"{hours:02}")
        if "mm" in mask:
            formatted_time = formatted_time.replace("mm", f"{minutes:02}")
        if "ss" in mask:
            formatted_time = formatted_time.replace("ss", f"{secs:02}")
        if "ms" in mask:
            formatted_time = formatted_time.replace("ms", f"{milliseconds:03}")

        return formatted_time
#endregion
#region ThrottledTimer

class ThrottledTimer:
    def __init__(self, throttle_time=1000):
        self.throttle_time = throttle_time
        self.timer = Timer()
        self.timer.Start()
        
    def IsExpired(self):
        return self.timer.HasElapsed(self.throttle_time)
    
    def Reset(self):
        self.timer.Reset()
        
    def Start(self):
        self.timer.Start()
        
    def Stop(self):
        self.timer.Stop()
    
    def IsStopped(self):
        return self.timer.IsStopped()
    
    
    def SetThrottleTime(self, throttle_time):
        self.throttle_time = throttle_time
        
    def GetTimeElapsed(self):
        return self.timer.GetElapsedTime()
    
    def GetTimeRemaining(self):
        if self.timer.IsStopped():
            return 0
        return max(0, self.throttle_time - self.timer.GetElapsedTime())

#endregion
from datetime import datetime
from Py4GWCoreLib import IconsFontAwesome5

class RunInfo:
    def __init__(self, order, id, origin, destination, region=None, run_name=None):
        self.order = order
        self.id = id  # e.g. "Eye_Of_The_North__1_Eotn_To_Gunnars"
        self.origin = origin
        self.destination = destination
        self.display = f"{origin} {IconsFontAwesome5.ICON_ARROWS_ALT_H} {destination}"
        self.region = region
        self.run_name = run_name

        # Extract region and run_name from the id string
        #if "__" in id:
        #    self.region, self.run_name = id.split("__", 1)
        #else:
            # fallback if no double underscore
        #    parts = id.split("_", 1)
        #    self.region = parts[0] if parts else ""
        #    self.run_name = parts[1] if len(parts) > 1 else id

        # Progress flags
        self.started = False
        self.finished = False
        
        # Timing
        self.start_time = None
        self.end_time = None
        self.duration = 0
        
        # Fail tracking
        self.failures = 0
        self.deaths = 0
        self.stuck_timeouts = 0

    def mark_started(self):
        self.started = True
        self.start_time = datetime.now()

    def mark_finished(self, failed=False, deaths=0, stuck_timeouts=0):
        self.finished = True
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        else:
            self.duration = 0
        self.deaths += deaths
        self.stuck_timeouts += stuck_timeouts
        if failed:
            self.failures += 1

    def get_duration(self):
        if self.end_time:
            return self.duration
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0
    
class ChainStatistics:
    def __init__(self, chain_runs: list[RunInfo]):
        self.runs = chain_runs
        self.chain_start = None
        self.chain_end = None
    
    def start_chain(self):
        self.chain_start = datetime.now()
    
    def finish_chain(self):
        self.chain_end = datetime.now()
    
    def total_chain_time(self):
        if not self.chain_start:
            return 0
        if self.chain_end:
            return (self.chain_end - self.chain_start).total_seconds()
        return (datetime.now() - self.chain_start).total_seconds()
    
    def runs_completed(self):
        return sum(1 for r in self.runs if r.finished)
    
    def runs_failed(self):
        return sum(r.failures for r in self.runs)
    
    def map_run_times(self):
        return [r.duration for r in self.runs if r.finished]

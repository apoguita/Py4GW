from datetime import datetime
from typing import Optional, List

class RunStatistics:
    class RunNode:
        def __init__(self, runid: int = 0):
            self.runID:int = runid
            self.start_time: datetime = datetime.now()
            self.end_time: Optional[datetime] = None
            self.TARGET_VAETTIR_KILLS: int = 60
            self.vaettir_kills: int = 0
            self.deaths: int = 0
            self.stuck_timeouts: int = 0
            self.failed = False
            
        def Start(self):
            self.start_time = datetime.now()

        def End(self, vaettirs_killed: int = 0, failed: bool = False, deaths: int = 0, stuck_timeouts: int = 0):
            self.end_time = datetime.now()
            self.vaettir_kills = vaettirs_killed
            self.deaths = deaths
            self.stuck_timeouts = stuck_timeouts
            self.failed = failed
            
        def GetRunDuration(self) -> float:
            """Returns the duration of the run in seconds, or None if the run has not ended."""
            if self.end_time is None:
                return (datetime.now() - self.start_time).total_seconds()
            return (self.end_time - self.start_time).total_seconds()
    
    def __init__(self):
        self.run_nodes: List[RunStatistics.RunNode] = []
        self.current_run_node: Optional[RunStatistics.RunNode] = None
        self.run_id_counter: int = 0
        
    def StartNewRun(self):
        """Starts a new run and initializes the run node."""
        self.run_id_counter += 1
        new_run_node = RunStatistics.RunNode(runid=self.run_id_counter)
        new_run_node.Start()
        self.run_nodes.append(new_run_node)
        self.current_run_node = new_run_node
        
    def EndCurrentRun(self, vaettirs_killed: int = 0, failed: bool = False, deaths: int = 0, stuck_timeouts: int = 0):
        """Ends the current run and updates the run node."""
        if self.current_run_node is not None:
            self.current_run_node.End(vaettirs_killed, failed,deaths, stuck_timeouts)
            self.current_run_node = None
            
    def GetCurrentRun(self) -> Optional["RunStatistics.RunNode"]:
        """Returns the current run node, or None if no run is in progress."""
        return self.current_run_node
    
    def _get_successful_runs(self) -> List["RunStatistics.RunNode"]:
        return [node for node in self.run_nodes if not node.failed and node.end_time is not None]

    
    def GetQuickestRun(self) -> Optional["RunStatistics.RunNode"]:
        successful = self._get_successful_runs()
        return min(successful, key=lambda node: node.GetRunDuration(), default=None)
    
    def GetLongestRun(self) -> Optional["RunStatistics.RunNode"]:
        successful = self._get_successful_runs()
        return max(successful, key=lambda node: node.GetRunDuration(), default=None)
    
    def GetAverageRunDuration(self) -> float:
        successful = self._get_successful_runs()
        if not successful:
            return 0.0
        total_duration = sum(node.GetRunDuration() for node in successful)
        if len(successful) == 0:
            return 0.0
        return total_duration / len(successful)
    
    def GetKillEffectivity(self) -> float:
        successful = self._get_successful_runs()
        if not successful:
            return 0.0
        total_kills = sum(node.vaettir_kills for node in successful)
        total_target_kills = sum(node.TARGET_VAETTIR_KILLS for node in successful)
        if total_target_kills == 0:
            return 0.0
        return (total_kills / total_target_kills) * 100.0
    
    def GetRuneffectivity(self) -> float:
        total_runs = len(self.run_nodes)
        if total_runs == 0:
            return 0.0
        successful_runs = sum(1 for node in self.run_nodes if not node.failed)
        return (successful_runs / total_runs) * 100.0
    
    def GetDeaths(self) -> int:
        return sum(node.deaths for node in self.run_nodes)

    def GetTimeouts(self) -> int:
        return sum(node.stuck_timeouts for node in self.run_nodes)
    
    def GetFailedRuns(self) -> List["RunStatistics.RunNode"]:
        return [node for node in self.run_nodes if node.failed and node.end_time is not None]

    def GetAverageKillsOnSuccess(self) -> float:
        successful = self._get_successful_runs()
        if not successful:
            return 0.0
        return sum(n.vaettir_kills for n in successful) / len(successful)
    
    def GetAverageDeathsOnSuccess(self) -> float:
        successful = self._get_successful_runs()
        if not successful:
            return 0.0
        return sum(n.deaths for n in successful) / len(successful)
    
    def GetTotalRuns(self) -> int:
        return len(self.run_nodes)
    
    def GetTotalSuccesses(self) -> int:
        return sum(1 for node in self.run_nodes if not node.failed)
    
    def GetTotalFailures(self) -> int:
        return sum(1 for node in self.run_nodes if node.failed)




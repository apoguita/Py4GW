
from Py4GWCoreLib.Agent import Agent
import time


class AgentCache:
    def __init__(self):

        self.name_cache: dict[int, tuple[str, float]] = {}  # agent_id -> (name, timestamp)
        self.name_requested: set[int] = set()
        self.name_timeout_ms = 1_000

        
    def _update_cache(self):
        """Should be called every frame to resolve names when ready."""
        now = time.time() * 1000
        for agent_id in list(self.name_requested):
            name = Agent.GetNameByID(agent_id)

            self.name_cache[agent_id] = (name, now)
            self.name_requested.discard(agent_id)
                
    def _reset_cache(self):
        """Resets the name cache and requested set."""
        self.name_cache.clear()
        self.name_requested.clear()


   




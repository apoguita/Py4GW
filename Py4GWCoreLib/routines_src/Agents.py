import importlib, typing

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()


#region Agents
class Agents:    
    @staticmethod
    def GetNearestNPCXY(x,y, distance):
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        scan_pos = (x,y)
        npc_array = GLOBAL_CACHE.AgentArray.GetNPCMinipetArray()
        npc_array = AgentArray.Filter.ByDistance(npc_array,scan_pos, distance)
        npc_array = AgentArray.Sort.ByDistance(npc_array, scan_pos)
        if len(npc_array) > 0:
            return npc_array[0]
        return 0    
    
    @staticmethod
    def GetNearestGadgetXY(x,y, distance):
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        scan_pos = (x,y)
        gadget_array = GLOBAL_CACHE.AgentArray.GetGadgetArray()
        gadget_array = AgentArray.Filter.ByDistance(gadget_array,scan_pos, distance)
        gadget_array = AgentArray.Sort.ByDistance(gadget_array, scan_pos)
        if len(gadget_array) > 0:
            return gadget_array[0]
        return 0    
                
    @staticmethod
    def GetNearestItemXY(x,y, distance):
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        scan_pos = (x,y)
        item_array = GLOBAL_CACHE.AgentArray.GetItemArray()
        item_array = AgentArray.Filter.ByDistance(item_array,scan_pos, distance)
        item_array = AgentArray.Sort.ByDistance(item_array, scan_pos)
        if len(item_array) > 0:
            return item_array[0]
        return 0  
    
    @staticmethod
    def GetNearestNPC(distance:float = 4500.0):
        from ..GlobalCache import GLOBAL_CACHE
        player_pos = GLOBAL_CACHE.Player.GetXY()
        return Agents.GetNearestNPCXY(player_pos[0], player_pos[1], distance)
    
    @staticmethod
    def GetAgentIDByModelID(model_id: int) -> int:
        """
        Purpose: Get the closest agent ID with the given model ID (closest to the player).
        Args:
            model_id (int): The model ID of the agent.
        Returns:
            int: The closest matching agent ID, or 0 if none found.
        """
        from ..GlobalCache import GLOBAL_CACHE
        from ..Py4GWcorelib import Utils

        agent_ids = GLOBAL_CACHE.AgentArray.GetAgentArray()
        px, py = GLOBAL_CACHE.Player.GetXY()

        best_id = 0
        best_dist = float("inf")

        for agent_id in agent_ids:
            if GLOBAL_CACHE.Agent.GetModelID(agent_id) == model_id:
                ax, ay = GLOBAL_CACHE.Agent.GetXY(agent_id)
                d = Utils.Distance((px, py), (ax, ay))
                if d < best_dist:
                    best_dist = d
                    best_id = agent_id

        return best_id

        
    @staticmethod
    def GetFilteredEnemyArray(x, y, max_distance=4500.0, aggressive_only = False):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        """
        Purpose: filters enemies within the specified range.
        Args:
            range (int): The maximum distance to search for enemies.
        Returns: List of enemy agent IDs
        """
        from ..GlobalCache import GLOBAL_CACHE
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Utils.Distance((x,y), GLOBAL_CACHE.Agent.GetXY(agent_id)) <= max_distance)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Player.GetAgentID() != agent_id)
        if aggressive_only:
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAggressive(agent_id))
        return enemy_array
                    
    @staticmethod
    def GetNearestEnemy(max_distance=4500.0, aggressive_only = False):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)
    
    @staticmethod
    def GetNearestEnemyCaster(max_distance=4500.0, aggressive_only = False):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsCaster(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)
        
    @staticmethod
    def GetNearestEnemyMartial(max_distance=4500.0, aggressive_only = False):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsMartial(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)   
    
    @staticmethod
    def GetNearestEnemyMelee(max_distance=4500.0, aggressive_only = False):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsMelee(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)
    
    @staticmethod
    def GetNearestEnemyRanged(max_distance=4500.0, aggressive_only = False):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsRanged(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)
        
    @staticmethod
    def GetFilteredAllyArray(x, y, max_distance=4500.0, other_ally=False):
        from ..AgentArray import AgentArray
        """
        Purpose: filters allies within the specified range.
        Args:
            range (int): The maximum distance to search for allies.
            other_ally (bool): Whether to include other allies in the search.
        Returns: List of ally agent IDs
        """
        from ..GlobalCache import GLOBAL_CACHE
        ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
        ally_array = AgentArray.Filter.ByDistance(ally_array, (x,y), max_distance)
        ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        if other_ally:
            ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Player.GetAgentID() != agent_id)
            
        return ally_array

    
    @staticmethod
    def GetNearestAlly(max_distance=4500.0, exclude_self=True):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        self_id = GLOBAL_CACHE.Player.GetAgentID()
        player_pos = GLOBAL_CACHE.Player.GetXY()
        ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
        ally_array = AgentArray.Filter.ByDistance(ally_array, player_pos, max_distance)
        ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        if exclude_self:
            ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: agent_id != self_id)
        ally_array = AgentArray.Sort.ByDistance(ally_array, player_pos)
        return Utils.GetFirstFromArray(ally_array)
    
    @staticmethod   
    def GetDeadAlly(max_distance=4500.0):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        distance = max_distance
        ally_array = AgentArray.GetAllyArray()
        ally_array = AgentArray.Filter.ByDistance(ally_array, GLOBAL_CACHE.Player.GetXY(), distance)
        ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsDead(agent_id))
        ally_array = AgentArray.Sort.ByDistance(ally_array, GLOBAL_CACHE.Player.GetXY())
        return Utils.GetFirstFromArray(ally_array)
    
    @staticmethod
    def GetNearestCorpse(max_distance=4500.0):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE
        
        def _AllowedAlliegance(agent_id):
            _, alliegance = GLOBAL_CACHE.Agent.GetAllegiance(agent_id)

            if (alliegance == "Ally" or
                alliegance == "Neutral" or 
                alliegance == "Enemy" or 
                alliegance == "NPC/Minipet"
                ):
                return True
            return False

        distance = max_distance
        corpse_array = GLOBAL_CACHE.AgentArray.GetAgentArray()
        corpse_array = AgentArray.Filter.ByDistance(corpse_array, GLOBAL_CACHE.Player.GetXY(), distance)
        corpse_array = AgentArray.Filter.ByCondition(corpse_array, lambda agent_id: GLOBAL_CACHE.Agent.IsDead(agent_id))
        corpse_array = AgentArray.Filter.ByCondition(corpse_array, lambda agent_id: _AllowedAlliegance(agent_id))
        corpse_array = AgentArray.Sort.ByDistance(corpse_array, GLOBAL_CACHE.Player.GetXY())
        return Utils.GetFirstFromArray(corpse_array)
        
    @staticmethod
    def GetNearestSpirit(max_distance=4500.0):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE
        distance = max_distance
        spirit_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
        spirit_array = AgentArray.Filter.ByDistance(spirit_array, GLOBAL_CACHE.Player.GetXY(), distance)
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: GLOBAL_CACHE.Agent.IsSpawned(agent_id))
        spirit_array = AgentArray.Sort.ByDistance(spirit_array, GLOBAL_CACHE.Player.GetXY())
        return Utils.GetFirstFromArray(spirit_array)
    
    @staticmethod
    def GetFilteredSpiritArray(x, y, max_distance=4500.0):
        from ..AgentArray import AgentArray
        """
        Purpose: filters spirits within the specified range.
        Args:
            range (int): The maximum distance to search for spirits.
        Returns: List of spirit agent IDs
        """
        from ..GlobalCache import GLOBAL_CACHE
        spirit_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
        spirit_array = AgentArray.Filter.ByDistance(spirit_array, (x,y), max_distance)
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: GLOBAL_CACHE.Agent.IsSpawned(agent_id))
        return spirit_array
        
    @staticmethod
    def GetLowestMinion(max_distance=4500.0):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE
        
        distance = max_distance
        minion_array = GLOBAL_CACHE.AgentArray.GetMinionArray()
        minion_array = AgentArray.Filter.ByDistance(minion_array, GLOBAL_CACHE.Player.GetXY(), distance)
        minion_array = AgentArray.Filter.ByCondition(minion_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        minion_array = AgentArray.Sort.ByHealth(minion_array)
        return Utils.GetFirstFromArray(minion_array)            
        
    @staticmethod
    def GetFilteredMinionArray(x, y, max_distance=4500.0):
        from ..AgentArray import AgentArray
        """
        Purpose: filters minions within the specified range.
        Args:
            range (int): The maximum distance to search for minions.
        Returns: List of minion agent IDs
        """
        from ..GlobalCache import GLOBAL_CACHE
        minion_array = GLOBAL_CACHE.AgentArray.GetMinionArray()
        minion_array = AgentArray.Filter.ByDistance(minion_array, (x,y), max_distance)
        minion_array = AgentArray.Filter.ByCondition(minion_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        return minion_array    
    
    
    @staticmethod
    def GetNearestItem(max_distance=4500.0):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        item_array = AgentArray.GetItemArray()
        item_array = AgentArray.Filter.ByDistance(item_array, GLOBAL_CACHE.Player.GetXY(), max_distance)
        item_array = AgentArray.Sort.ByDistance(item_array,GLOBAL_CACHE.Player.GetXY())
        return Utils.GetFirstFromArray(item_array)   

    @staticmethod
    def GetNearestGadget(max_distance=4500.0):
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        gadget_array = GLOBAL_CACHE.AgentArray.GetGadgetArray()
        gadget_array = AgentArray.Filter.ByDistance(gadget_array, GLOBAL_CACHE.Player.GetXY(), max_distance)
        gadget_array = AgentArray.Sort.ByDistance(gadget_array,GLOBAL_CACHE.Player.GetXY())
        return Utils.GetFirstFromArray(gadget_array)
        
    @staticmethod
    def GetNearestChest(max_distance=5000):
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        """
        Purpose: Get the nearest chest within the specified range.
        Args:
            range (int): The maximum distance to search for chests.
        Returns: Agent ID or None
        """
        gadget_array = AgentArray.GetGadgetArray()
        gadget_array = AgentArray.Filter.ByDistance(gadget_array, GLOBAL_CACHE.Player.GetXY(), max_distance)
        gadget_array = AgentArray.Sort.ByDistance(gadget_array,GLOBAL_CACHE.Player.GetXY())
        for agent_id in gadget_array:
            if GLOBAL_CACHE.Agent.GetGadgetID(agent_id) == 9: #9 is the ID for Hidden Stash (Pre-Searing)
                return agent_id
            if GLOBAL_CACHE.Agent.GetGadgetID(agent_id) == 69: #69 is the ID for Ascalonian Chest
                return agent_id
            if GLOBAL_CACHE.Agent.GetGadgetID(agent_id) == 4579: #4579 is the ID for Shing Jea Chest
                return agent_id
            if GLOBAL_CACHE.Agent.GetGadgetID(agent_id) == 8141: #8141 is the ID for a chest
                return agent_id

        return 0

    @staticmethod
    def GetBestTarget(a_range=1320, casting_only=False, no_hex_only=False, enchanted_only=False):
        """
        Purpose: Returns the best target within the specified range based on criteria like whether the agent is casting, enchanted, or hexed.
        Args:
            a_range (int): The maximum distance for selecting targets.
            casting_only (bool): If True, only select agents that are casting.
            no_hex_only (bool): If True, only select agents that are not hexed.
            enchanted_only (bool): If True, only select agents that are enchanted.
        Returns: PyAgent.PyAgent: The best target agent object, or None if no target matches.
        """
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        best_target = None
        lowest_sum = float('inf')
        nearest_enemy = None
        nearest_distance = float('inf')
        lowest_hp_target = None
        lowest_hp = float('inf')

        player_pos = GLOBAL_CACHE.Player.GetXY()
        agents = GLOBAL_CACHE.AgentArray.GetEnemyArray()
        agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        agents = AgentArray.Filter.ByDistance(agents, player_pos, a_range)

        if enchanted_only:
            agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: GLOBAL_CACHE.Agent.IsEnchanted(agent_id))

        if no_hex_only:
            agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: GLOBAL_CACHE.Agent.IsHexed(agent_id))

        if casting_only:
            agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: GLOBAL_CACHE.Agent.IsCasting(agent_id))

        for agent_id in agents:
            agent = GLOBAL_CACHE.Player.GetAgentID()
            x,y = GLOBAL_CACHE.Agent.GetXY(agent)

            distance_to_self = Utils.Distance(GLOBAL_CACHE.Player.GetXY(), (x, y))

            # Track the nearest enemy
            if distance_to_self < nearest_distance:
                nearest_enemy = agent
                nearest_distance = distance_to_self

            # Track the agent with the lowest HP
            agent_hp = GLOBAL_CACHE.Agent.GetHealth(agent)
            if agent_hp < lowest_hp:
                lowest_hp = agent_hp
                lowest_hp_target = agent

            # Calculate the sum of distances between this agent and other agents within range
            sum_distances = 0
            for other_agent_id in agents:
                other_x, other_y = GLOBAL_CACHE.Agent.GetXY(other_agent_id)
                #no need to filter any agent since the array is filtered already
                sum_distances += Utils.Distance((x, y), (other_x, other_y))

            # Track the best target based on the sum of distances
            if sum_distances < lowest_sum:
                lowest_sum = sum_distances
                best_target = agent

        return best_target

    @staticmethod
    def GetBestMeleeTarget(a_range=1320, casting_only=False, no_hex_only=False, enchanted_only=False):
        """
        Purpose: Returns the best melee most baslled up target within the specified range based on criteria like whether the agent is casting, enchanted, or hexed.
        Args:
            a_range (int): The maximum distance for selecting targets.
            casting_only (bool): If True, only select agents that are casting.
            no_hex_only (bool): If True, only select agents that are not hexed.
            enchanted_only (bool): If True, only select agents that are enchanted.
        Returns: PyAgent.PyAgent: The best melee target agent object, or None if no target matches.
        """
        from ..AgentArray import AgentArray
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE

        best_target = None
        lowest_sum = float('inf')
        nearest_enemy = None
        nearest_distance = float('inf')
        lowest_hp_target = None
        lowest_hp = float('inf')

        player_pos = GLOBAL_CACHE.Player.GetXY()
        agents = AgentArray.GetEnemyArray()

        # Filter out dead, distant, and non-melee agents
        agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: GLOBAL_CACHE.Agent.IsMelee(agent_id))
        agents = AgentArray.Filter.ByDistance(agents, player_pos, a_range)


        if enchanted_only:
            agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: GLOBAL_CACHE.Agent.IsEnchanted(agent_id))

        if no_hex_only:
            agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: GLOBAL_CACHE.Agent.IsHexed(agent_id))

        if casting_only:
            agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: GLOBAL_CACHE.Agent.IsCasting(agent_id))


        for agent_id in agents:
            
            x, y = GLOBAL_CACHE.Agent.GetXY(agent_id)

            distance_to_self = Utils.Distance(GLOBAL_CACHE.Player.GetXY(), (x, y))

            # Track the nearest melee enemy
            if distance_to_self < nearest_distance:
                nearest_distance = distance_to_self

            # Track the agent with the lowest HP
            agent_hp = GLOBAL_CACHE.Agent.GetHealth(agent_id) 
            if agent_hp < lowest_hp:
                lowest_hp = agent_hp


            # Calculate the sum of distances between this agent and other agents within range
            sum_distances = 0
            for other_agent_id in agents:
                other_agent_x, other_agent_y = GLOBAL_CACHE.Agent.GetXY(other_agent_id)
                sum_distances += Utils.Distance((x, y), (other_agent_x, other_agent_y))

            # Track the best melee target based on the sum of distances
            if sum_distances < lowest_sum:
                lowest_sum = sum_distances
                best_target = agent_id

        return best_target
    
    @staticmethod
    def GetPartyTargetID():
        from ..GlobalCache import GLOBAL_CACHE
        if not GLOBAL_CACHE.Party.IsPartyLoaded():
            return 0

        players = GLOBAL_CACHE.Party.GetPlayers()
        target = players[0].called_target_id

        if target is None or target == 0:
            return 0
        else:
            return target


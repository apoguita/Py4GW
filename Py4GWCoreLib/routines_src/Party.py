import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()

#region Agents
class Party:   
    @staticmethod
    def GetPartyTargetID():
        from ..GlobalCache import GLOBAL_CACHE
        if not GLOBAL_CACHE.Party.IsPartyLoaded():
            return 0

        players = GLOBAL_CACHE.Party.GetPlayers()
        target = players[0].called_target_id

        if GLOBAL_CACHE.Agent.IsValid(target):
            return target  
        
        return 0   
    
    @staticmethod
    def IsPartyMember(agent_id: int) -> bool:
        from ..GlobalCache import GLOBAL_CACHE
        players = GLOBAL_CACHE.Party.GetPlayers()
        for player in players:
            player_agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            if player_agent_id == agent_id:
                return True
            
        heroes = GLOBAL_CACHE.Party.GetHeroes()
        for hero in heroes:
            if hero.agent_id == agent_id:
                return True
            
        henchmen = GLOBAL_CACHE.Party.GetHenchmen()
        for henchman in henchmen:
            if henchman.agent_id == agent_id:
                return True
            
        return False
    
    @staticmethod
    def GetDeadPartyMemberID():
        from ..GlobalCache import GLOBAL_CACHE
        from ..Routines import Checks
        if not Checks.Map.MapValid():
            return 0
        players = GLOBAL_CACHE.Party.GetPlayers()
        henchmen = GLOBAL_CACHE.Party.GetHenchmen()
        heroes = GLOBAL_CACHE.Party.GetHeroes()

        for player in players:
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            if GLOBAL_CACHE.Agent.IsDead(agent_id):
                return agent_id

        for henchman in henchmen:
            if GLOBAL_CACHE.Agent.IsDead(henchman.agent_id):
                return henchman.agent_id
            
        for hero in heroes:
            if GLOBAL_CACHE.Agent.IsDead(hero.agent_id):
                return hero.agent_id

        return 0
    
    
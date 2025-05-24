import PyParty
from Py4GWCoreLib import Player
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager

class PartyCache:
    def __init__(self, action_queue_manager, map_cache, player_cache):
        self._action_queue_manager:ActionQueueManager = action_queue_manager
        self._party_instance = PyParty.PyParty()
        self.Players = self._Players(self)
        self.Heroes = self._Heroes(self)
        self.Henchmen = self._Henchmen(self)
        self.Pets = self._Pets(self)
        self._map_cache = map_cache
        self._player_cache = player_cache
    
    def _update_cache(self):
        self._party_instance.GetContext()
        
    def GetPartyID(self):
        if not self.IsPartyLoaded():
            return 0
        return self._party_instance.party_id
    
    def GetPlayers(self):
        if not self.IsPartyLoaded():
            return []
        return self._party_instance.players
    
    def GetHeroes(self):
        if not self.IsPartyLoaded():
            return []
        return self._party_instance.heroes
    
    def GetHenchmen(self):
        if not self.IsPartyLoaded():
            return []
        return self._party_instance.henchmen
    
    def GetPlayerCount(self):
        if not self.IsPartyLoaded():
            return 0
        return self._party_instance.party_player_count
    
    def GetHeroCount(self):
        if not self.IsPartyLoaded():
            return 0
        return self._party_instance.party_hero_count
    
    def GetHenchmanCount(self):
        if not self.IsPartyLoaded():
            return 0
        return self._party_instance.party_henchman_count

    def GetPartyLeaderID(self):
        if not self.IsPartyLoaded():
            return 0
        players = self.GetPlayers()
        leader =  players[0]
        return self.Players.GetAgentIDByLoginNumber(leader.login_number)
    
    def GetOwnPartyNumber(self):
        if not self.IsPartyLoaded():
            return -1
        agent_id = self._player_cache.GetAgentID()
        players = self.GetPlayers()
        for i in range(self.GetPlayerCount()):
            player_id = self.Players.GetAgentIDByLoginNumber(players[i].login_number)
            if player_id == agent_id:
                return i
        return -1
    
    def IsHardModeUnlocked(self):
        return self._party_instance.is_hard_mode_unlocked
    
    def IsHardMode(self):
        return self._party_instance.is_in_hard_mode
    
    def IsNormalMode(self):
        return not self.IsHardMode()
    
    def GetPartySize(self):
        return self._party_instance.party_size
    
    def IsPartyDefeated(self):
        return self._party_instance.is_party_defeated
    
    def IsPartyLoaded(self):
        if self._map_cache.IsMapLoading():
            return False
        return self._party_instance.is_party_loaded
    
    def IsPartyLeader(self):
        return self._party_instance.is_party_leader
        
    def SetTickasToggle(self, enabled):
        self._action_queue_manager.AddAction("ACTION", self._party_instance.tick.SetTickToggle, enabled)
    
    def IsAllTicked(self):
        return self._party_instance.tick.IsTicked()
    
    def IsPlayerTicked (self, party_number):
        return self._party_instance.GetIsPlayerTicked(party_number)
    
    def SetTicked(self, ticked):
        self._action_queue_manager.AddAction("ACTION", self._party_instance.tick.SetTicked, ticked)
        
    def ToggleTicked(self):
        agent_id = self._player_cache.GetAgentID()
        login_number = self.Players.GetLoginNumberByAgentID(agent_id)
        party_number = self.Players.GetPartyNumberFromLoginNumber(login_number)
        
        if self.IsPlayerTicked(party_number):
            self._action_queue_manager.AddAction("ACTION", self._party_instance.tick.SetTicked, False)
        else:
            self._action_queue_manager.AddAction("ACTION", self._party_instance.tick.SetTicked, True)
            
    def SetHardMode(self):
        if self.IsHardModeUnlocked() and self.IsNormalMode():
            self._action_queue_manager.AddAction("ACTION", self._party_instance.SetHardMode, True)
            
    def SetNormalMode(self):
        if self.IsHardMode():
            self._action_queue_manager.AddAction("ACTION", self._party_instance.SetHardMode, False)
            
    def SearchParty(self, search_type, advertisement):
        self._action_queue_manager.AddAction("ACTION", self._party_instance.SearchParty, search_type, advertisement)
        
    def SearchPartyCancel(self):
        self._action_queue_manager.AddAction("ACTION", self._party_instance.SearchPartyCancel)
        
    def SearchPartyReply(self, accept=True):
        self._action_queue_manager.AddAction("ACTION", self._party_instance.SearchPartyReply, accept)
        
    def RespondToPartyRequest(self, party_id, accept):
        self._action_queue_manager.AddAction("ACTION", self._party_instance.RespondToPartyRequest, party_id, accept)
        
    def ReturnToOutpost(self):
        self._action_queue_manager.AddAction("ACTION", self._party_instance.ReturnToOutpost)
    
    def LeaveParty(self):
        self._action_queue_manager.AddAction("ACTION", self._party_instance.LeaveParty)

        
    class _Players:
        def __init__(self, parent):
            self._parent = parent
   
        def GetAgentIDByLoginNumber(self, login_number):
            return self._parent._party_instance.GetAgentIDByLoginNumber(login_number)
        
        def GetLoginNumberByAgentID(self, agent_id):
            players = self._parent.GetPlayers()
            if len(players) == 0:
                return 0
            
            for player in players:
                player_agent_id = self.GetAgentIDByLoginNumber(player.login_number)
                if player_agent_id == agent_id:
                    return player.login_number
            
            return 0
        
        def GetPartyNumberFromLoginNumber(self, login_number):
            players = self._parent.GetPlayers()
            if len(players) == 0:
                return 0
            
            for i in range(self._parent.GetPlayerCount()):
                player = players[i]
                if player.login_number == login_number:
                    return i
            
            return -1
        
        def GetPlayerNameByLoginNumber(self, login_number):
            return self._parent._party_instance.GetPlayerNameByLoginNumber(login_number)
        
        def InvitePlayer(self, agent_id_or_name):
            """
            Invite a player by ID (int) or name (str).
            Args: 
                player (int or str): The player ID or player name.
            """
            if isinstance(agent_id_or_name, int):
                self._parent._action_queue_manager.AddAction("ACTION",self._parent._party_instance.InvitePlayer,agent_id_or_name)
            elif isinstance(agent_id_or_name, str):
                self._parent._action_queue_manager.AddAction("ACTION",Player.SendChatCommand,"invite " + agent_id_or_name)
                
        def KickPlayer(self, login_number):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.KickPlayer, login_number)
            
    class _Heroes:
        def __init__(self, parent):
            self._parent = parent
            
        def GetHeroAgentIDByPartyPosition(self,hero_position):
            return self._parent._party_instance.GetHeroAgentID(hero_position)
        
        def GetHeroIDByAgentID(self, agent_id):
            heroes = self._parent.GetHeroes()
            if len(heroes) == 0:
                return 0
            for hero in heroes:
                if hero.agent_id == agent_id:
                    return hero.hero_id.GetID()
            return 0
        
        def GetHeroIDByPartyPosition(self, party_position):
            heroes = self._parent.GetHeroes()
            if len(heroes) == 0:
                return 0
            for index, hero in enumerate(heroes):
                if index == party_position:
                    return hero.hero_id.GetID()
                
        def GetHeroIdByName(self, hero_name):
            hero = PyParty.Hero(hero_name)
            return hero.GetID()
        
        def GetHeroNameById(self, hero_id):
            hero = PyParty.Hero(hero_id)
            return hero.GetName()
        
        def GetNameByAgentID(self, agent_id):
            heroes = self._parent.GetHeroes()
            if len(heroes) == 0:
                return ""
            for hero in heroes:
                if hero.agent_id == agent_id:
                    return hero.hero_id.GetName()
            return ""
        
        def AddHero(self, hero_id):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.AddHero, hero_id)
            
        def AddHeroByName(self, hero_name):
            hero = PyParty.Hero(hero_name)
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.AddHero, hero.GetID())
            
        def KickHero(self, hero_id):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.KickHero, hero_id)
            
        def KickHeroByName(self, hero_name):
            hero = PyParty.Hero(hero_name)
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.KickHero, hero.GetID())
            
        def KickAllHeroes(self):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.KickAllHeroes)
        
        def UseSkill(self, hero_agent_id, slot, target_id):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.UseHeroSkill, hero_agent_id, slot, target_id)
            
        def FlagHero (self, hero_id, x, y): 
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.FlagHero, hero_id, x, y)  
            
        def FlagAllHeroes(self, x, y):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.FlagAllHeroes, x, y)
            
        def UnflagHero(self, hero_id):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.UnflagHero, hero_id)
            
        def UnflagAllHeroes(self):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.UnflagAllHeroes)
        
        def IsHeroFlagged(self, hero_party_number):
            return self._parent._party_instance.IsHeroFlagged(hero_party_number)   

        def IsAllFlagged(self):
            return self._parent._party_instance.IsAllFlagged()
        
        def GetAllFlag(self):
            return self._parent._party_instance.GetAllFlagX(), self._parent._party_instance.GetAllFlagY()
        
        def SetHeroBehavior (self,hero_agent_id, behavior):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.SetHeroBehavior, hero_agent_id, behavior)
            
    class _Henchmen:
        def __init__(self, parent):
            self._parent = parent
            
        def AddHenchman(self, henchman_id):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.AddHenchman, henchman_id)
            
        def KickHenchman(self, henchman_id):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.KickHenchman, henchman_id)
            
    class _Pets:
        def __init__(self, parent):
            self._parent = parent
            
        def SetPetBehavior(self, behavior, lock_target_id):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._party_instance.SetPetBehavior, behavior, lock_target_id)
            
        def GetPetInfo(self, owner_id):
            return self._parent._party_instance.GetPetInfo(owner_id)

        def GetPetBehavior(self, owner_id):
            pet_info =  self.GetPetInfo(owner_id)
            if not pet_info:
                return False
            return pet_info.behavior
        
        def GetPetID(self, owner_id):
            pet_info =  self.GetPetInfo(owner_id)
            if not pet_info:
                return 0
            return pet_info.agent_id
            
            
            
            
        
        
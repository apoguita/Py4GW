import PyPlayer
from Py4GWCoreLib.Agent import AgentName
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
from Py4GWCoreLib import ThrottledTimer

class PlayerCache:
    def __init__(self, action_queue_manager):
        self._player_instance = PyPlayer.PyPlayer()
        self._title_instances: dict[int, PyPlayer.PyTitle] = {}
        self._title_throttle_timer = ThrottledTimer(250)
        self._title_array: list[int] = []
        self._active_title_id: int = -1
        self._name_object = AgentName(self._player_instance.id,1000)
        self._name = ""
        self._action_queue_manager:ActionQueueManager = action_queue_manager
        self.login_characters = []

    def _format_uuid_as_email(self, player_uuid):
        if not player_uuid:
            return ""
        try:
            return "uuid_" + "_".join(str(part) for part in player_uuid)
        except TypeError:
            return str(player_uuid)
        
    def _update_cache(self):
        self._player_instance.GetContext()
        self._name_object.agent_id = self._player_instance.id
        if self._title_throttle_timer.IsExpired():
            self._title_throttle_timer.Reset()
            self._active_title_id = self._player_instance.GetActiveTitleId()
            self._title_array = self._player_instance.GetTitleArray()
            for title_id in self._title_array:
                if title_id in self._title_instances:
                    self._title_instances[title_id].GetContext()
                    continue
                title = PyPlayer.PyTitle(title_id)
                if title:
                    self._title_instances[title_id] = title
            #using same timer to update login characters
            self.login_characters = self._player_instance.GetAvailableCharacters()
                
                
        
    def GetAgentID(self):
        return self._player_instance.id
    
    def GetName(self):
        self._name = self._name_object.get_name()
        return self._name

    def GetXY(self):
        x = self._player_instance.agent.x
        y = self._player_instance.agent.y
        return x, y

    def GetTargetID(self):
        return self._player_instance.target_id
        
    def GetAgent(self):
        return self._player_instance.agent
    
    def GetMouseOverID(self):
        return self._player_instance.mouse_over_id
    
    def GetObservingID(self):
        return self._player_instance.observing_id
    
    def SendDialog(self, dialog_id: str | int):
        if isinstance(dialog_id, int):
            dialog = dialog_id
        else:
            # clean 0x or 0X and convert
            cleaned = dialog_id.strip().lower().replace("0x", "")
            dialog = int(cleaned, 16)
                            
        self._action_queue_manager.AddAction("ACTION", self._player_instance.SendDialog,dialog)
        
    def RequestChatHistory(self):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.RequestChatHistory)
        
    def IsChatHistoryReady(self):
        return self._player_instance.IsChatHistoryReady()

    def GetChatHistory(self):
        chat_history = self._player_instance.GetChatHistory()
        return chat_history
    
    def IsTyping(self):
        return self._player_instance.Istyping()
    
    def SendChatCommand(self, msg):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.SendChatCommand,msg)
        
    def SendChat(self, channel, msg):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.SendChat,channel, msg)
        
    def SendWhisper(self, name, msg):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.SendWhisper,name, msg)
        
    def SendFakeChat(self, channel, msg):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.SendFakeChat,channel, msg)
        
    def SendFakeChatColored(self, channel, msg, r, g, b):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.SendFakeChatColored,channel, msg, r, g, b)
        
    def FormatChatMessage(self, message, r, g, b):
        return self._player_instance.FormatChatMessage(message, r, g, b)
    
    def ChangeTarget(self, target_id):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.ChangeTarget, target_id)
        
    def Interact(self, agent_id, call_target):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.InteractAgent, agent_id, call_target)
        
    def Move(self, x, y):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.Move, x, y)
        
    def MoveXYZ(self, x, y, zplane):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.Move, x, y, zplane)
        
    def GetAccountName(self):
        return self._player_instance.account_name
    
    def GetAccountEmail(self):
        account_email = self._player_instance.account_email
        if account_email:
            return account_email
        return self._format_uuid_as_email(self._player_instance.player_uuid)
    
    def GetPlayerUUID(self):
        return self._player_instance.player_uuid

    def GetRankData(self):
        return self._player_instance.rank, self._player_instance.rating, self._player_instance.qualifier_points, self._player_instance.wins, self._player_instance.losses
    
    def GetTournamentRewardPoints(self):
        return self._player_instance.tournament_reward_points
    
    def GetMorale(self):
        return self._player_instance.morale

    def GetPartyMorale(self) -> list[tuple[int, int]]:
        return self._player_instance.party_morale

    def GetExperience(self):
        return self._player_instance.experience
    
    def GetLevel(self):
        return self._player_instance.level
    
    def GetSkillPointData(self):
        return self._player_instance.current_skill_points, self._player_instance.total_earned_skill_points
    
    def GetMissionsCompleted(self):
        return self._player_instance.missions_completed
    
    def GetMissionsBonusCompleted(self):
        return self._player_instance.missions_bonus
    
    def GetMissionsCompletedHM(self):
        return self._player_instance.missions_completed_hm
    
    def GetMissionsBonusCompletedHM(self):
        return self._player_instance.missions_bonus_hm
    
    def GetControlledMinions(self):
        return self._player_instance.controlled_minions
    
    def GetLearnableCharacterSkills(self):
        return self._player_instance.learnable_character_skills
    
    def GetUnlockedCharacterSkills(self):
        return self._player_instance.unlocked_character_skills
    
    def GetKurzickData(self):
        return self._player_instance.current_kurzick, self._player_instance.total_earned_kurzick, self._player_instance.max_kurzick
    
    def GetLuxonData(self):
        return self._player_instance.current_luxon, self._player_instance.total_earned_luxon, self._player_instance.max_luxon
    
    def GetImperialData(self):
        return self._player_instance.current_imperial, self._player_instance.total_earned_imperial, self._player_instance.max_imperial
    
    def GetBalthazarData(self):
        return self._player_instance.current_balth, self._player_instance.total_earned_balth, self._player_instance.max_balth
    
    def GetActiveTitleID(self):
        return self._active_title_id
    
    def GetTitleArray(self):
        return self._title_array
    
    def GetTitle(self, title_id) -> PyPlayer.PyTitle | None:
        return self._title_instances.get(title_id, None)
    
    def RemoveActiveTitle(self):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.RemoveActiveTitle)
        
    def SetActiveTitle(self, title_id):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.SetActiveTitle, title_id)
    
    def DepositFaction(self, allegiance):
        """0 = Kurzick, 1 = Luxon"""
        self._action_queue_manager.AddAction("ACTION", self._player_instance.DepositFaction, allegiance)
        
    def LogoutToCharacterSelect(self):
        self._action_queue_manager.AddAction("ACTION", self._player_instance.LogouttoCharacterSelect)
        
    def InCharacterSelectScreen(self):
        return self._player_instance.GetIsCharacterSelectReady()
        
    def GetLoginCharacters(self):
        return self.login_characters
    
    def GetPreGameContext(self):
        return self._player_instance.GetPreGameContext()
    
    def GetPreGameContextPtr(self):
        return self._player_instance.GetPreGameContextPtr()

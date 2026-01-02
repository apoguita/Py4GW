import PyPlayer

from .enums import *
from .Map import *
from .Agent import *


# Player
class Player:
    @staticmethod
    def _format_uuid_as_email(player_uuid):
        if not player_uuid:
            return ""
        try:
            return "uuid_" + "_".join(str(part) for part in player_uuid)
        except TypeError:
            return str(player_uuid)
        except Exception:
            return ""

    @staticmethod
    def player_instance():
        """
        Helper method to create and return a PyPlayer instance.
        Args:
            None
        Returns:
            PyAgent: The PyAgent instance for the given ID.
        """
        return PyPlayer.PyPlayer()

    @staticmethod
    def GetAgentID():
        """
        Purpose: Retrieve the agent ID of the player.
        Args: None
        Returns: int
        """
        return Player.player_instance().id

    @staticmethod
    def GetName():
        """
        Purpose: Retrieve the player's name.
        Args: None
        Returns: str
        """
        return Agent.GetName(Player.GetAgentID())

    @staticmethod
    def GetXY():
        """
        Purpose: Retrieve the player's current X and Y coordinates.
        Args: None
        Returns: tuple (x, y)
        """
        return Agent.GetXY(Player.GetAgentID())

    
    @staticmethod
    def GetTargetID():
        """
        Purpose: Retrieve the ID of the player's target.
        Args: None
        Returns: int
        """
        return Player.player_instance().target_id

    @staticmethod
    def GetAgent():
        """
        Purpose: Retrieve the player's agent.
        Args: None
        Returns: PyAgent
        """
        return Player.player_instance().agent

    @staticmethod
    def GetMouseOverID():
        """
        Purpose: Retrieve the ID of the agent the mouse is currently over.
        Args: None
        Returns: int
        """
        return Player.player_instance().mouse_over_id

    @staticmethod
    def GetObservingID():
        """
        Purpose: Retrieve the ID of the agent the player is observing.
        Args: None
        Returns: int
        """
        return Player.player_instance().observing_id

    @staticmethod
    def SendDialog(dialog_id: str | int):
        """
        Purpose: Send a dialog response.
        Args:
            dialog_id (int): The ID of the dialog.
        Returns: None
        """
        if isinstance(dialog_id, int):
            dialog = dialog_id
        else:
            # clean 0x or 0X and convert
            cleaned = dialog_id.strip().lower().replace("0x", "")
            dialog = int(cleaned, 16)
            
        Player.player_instance().SendDialog(dialog)
        
    @staticmethod
    def RequestChatHistory():
        """
        Purpose: Request the player's chat history.
        Args: None
        Returns: None
        """
        Player.player_instance().RequestChatHistory()
    
    @staticmethod
    def IsChatHistoryReady():
        """
        Purpose: Check if the player's chat history is ready.
        Args: None
        Returns: bool
        """
        return Player.player_instance().IsChatHistoryReady()
    
    @staticmethod
    def IsTyping():
        """
        Purpose: Check if the player is currently typing.
        Args: None
        Returns: bool
        """
        return Player.player_instance().Istyping()

    @staticmethod
    def GetChatHistory():
        """
        Purpose: Retrieve the player's chat history.
        Args: None
        Returns: list
        """
        return Player.player_instance().GetChatHistory()
    
    @staticmethod
    def SendChatCommand(command):
        """
        Purpose: Send a '/' chat command.
        Args:
            command (str): The command to send.
        Returns: None
        """
        Player.player_instance().SendChatCommand(command)

    @staticmethod
    def SendChat(channel, message):
        """
        Purpose: Send a chat message to a channel.
        Args:
            channel (char): The channel to send the message to.
            message (str): The message to send.
        Returns: None
        """
        Player.player_instance().SendChat(channel, message)

    @staticmethod
    def SendWhisper(target_name, message):
        """
        Purpose: Send a whisper to a target player.
        Args:
            target_name (str): The name of the target player.
            message (str): The message to send.
        Returns: None
        """
        Player.player_instance().SendWhisper(target_name, message)

    @staticmethod
    def SendFakeChat(channel:ChatChannel, message):
        """
        Purpose: Send a fake chat message to a channel.
        Args:
            channel (char): The channel to send the message to.
            message (str): The message to send.
        Returns: None
        """
        Player.player_instance().SendFakeChat(channel.value, message)
        
    @staticmethod
    def SendFakeChatColored(channel:ChatChannel, message, r, g, b):
        """
        Purpose: Send a fake chat message to a channel with color.
        Args:
            channel (char): The channel to send the message to.
            message (str): The message to send.
            r (int): The red color value.
            g (int): The green color value.
            b (int): The blue color value.
        Returns: None
        """
        Player.player_instance().SendFakeChatColored(channel.value, message, r, g, b)
        
    @staticmethod
    def FormatChatMessage(message, r, g, b):
        """
        Purpose: Format a chat message.
        Args:
            message (str): The message to format.
            r (int): The red color value.
            g (int): The green color value.
            b (int): The blue color value.
        Returns: str
        """
        return Player.player_instance().FormatChatMessage(message, r, g, b)

    @staticmethod
    def ChangeTarget(agent_id):
        """
        Purpose: Change the player's target.
        Args:
            agent_id (int): The ID of the agent to target.
        Returns: None
        """
        Player.player_instance().ChangeTarget(agent_id)
               
    @staticmethod
    def Interact(agent_id, call_target=False):
        """
        Purpose: Interact with an agent.
        Args:
            agent_id (int): The ID of the agent to interact with.
            call_target (bool, optional): Whether to call the agent as a target.
        Returns: None
        """
        Player.player_instance().InteractAgent(agent_id, call_target)

    @staticmethod
    def OpenLockedChest(use_key=False):
        """
        Purpose: Open a locked chest. This function is no longer available from toolbox!!
        Args:
            use_key (bool): Whether to use a key to open the chest.
        Returns: None
        """
        #This function is no longer available from toolbox!!
        Player.player_instance().OpenLockedChest(use_key)

    @staticmethod
    def Move(x, y):
        """
        Purpose: Move the player to specified X and Y coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
        Returns: None
        """
        Player.player_instance().Move(x, y)

    @staticmethod
    def MoveXYZ(x, y, zindex=1):
        """
        Purpose: Move the player to specified X and Y coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
        Returns: None
        """
        Player.player_instance().Move(x, y, zindex)

    @staticmethod
    def CancelMove():
        """
        Purpose: Cancel the player's current move action.
        Args: None
        Returns: None
        """
        player_agent = Player.GetAgent()
        if Map.IsMapReady():
            Player.player_instance().Move(player_agent.x, player_agent.y)
    
    @staticmethod
    def GetAccountName():
        """
        Purpose: Retrieve the player's account name.
        Args: None
        Returns: str
        """
        return Player.player_instance().account_name
    
    @staticmethod
    def GetAccountEmail():
        """
        Purpose: Retrieve the player's account email.
        Args: None
        Returns: str
        """
        try:
            player_instance = Player.player_instance()
            account_email = player_instance.account_email
            if account_email:
                return account_email
            player_uuid = player_instance.player_uuid
            if all(part == 0 for part in player_uuid):
                return ""
            return Player._format_uuid_as_email(player_uuid)
        except Exception:
            return ""
    
    @staticmethod
    def GetPlayerUUID():
        """
        Purpose: Retrieve the player's UUID.
        Args: None
        Returns: tuple[int,int,int,int]
        """
        return Player.player_instance().player_uuid
    
    @staticmethod
    def GetRankData():
        """
        Purpose: Retrieve the player's current rank data.
        Args: None
        Returns: int
        """
        return Player.player_instance().rank, Player.player_instance().rating, Player.player_instance().qualifier_points, Player.player_instance().wins, Player.player_instance().losses
    @staticmethod
    def GetTournamentRewardPoints():
        """
        Purpose: Retrieve the player's current tournament reward points.
        Args: None
        Returns: int
        """
        return Player.player_instance().tournament_reward_points
    
    @staticmethod
    def GetMorale():
        """
        Purpose: Retrieve the player's current morale.
        Args: None
        Returns: int
        """
        return Player.player_instance().morale
    
    @staticmethod
    def GetPartyMorale() -> List[Tuple[int, int]]:
        """
        Purpose: Retrieve the player's current party morale.
        Args: None
        Returns: list of tuples (current_morale, max_morale)
        """
        return Player.player_instance().party_morale
    
    @staticmethod
    def GetExperience():
        """
        Purpose: Retrieve the player's current experience.
        Args: None
        Returns: int
        """
        return Player.player_instance().experience
    
    @staticmethod
    def GetLevel():
        """
        Purpose: Retrieve the player's current level.
        Args: None
        Returns: int
        """
        return Player.player_instance().level
    
    @staticmethod
    def GetSkillPointData():
        """
        Purpose: Retrieve the player's current skill point data.
        Args: None
        Returns: int
        """
        return Player.player_instance().current_skill_points, Player.player_instance().total_earned_skill_points
    
    @staticmethod
    def GetMissionsCompleted():
        """
        Purpose: Retrieve the player's completed missions.
        Args: None
        Returns: list
        """
        return Player.player_instance().missions_completed
    
    @staticmethod
    def GetMissionsBonusCompleted():
        """
        Purpose: Retrieve the player's mission bonus data.
        Args: None
        Returns: list
        """
        return Player.player_instance().missions_bonus
    
    @staticmethod
    def GetMissionsCompletedHM():
        """
        Purpose: Retrieve the player's completed hard mode missions.
        Args: None
        Returns: list
        """
        return Player.player_instance().missions_completed_hm
    
    @staticmethod
    def GetMissionsBonusCompletedHM():
        """
        Purpose: Retrieve the player's hard mode mission bonus data.
        Args: None
        Returns: list
        """
        return Player.player_instance().missions_bonus_hm
    
    @staticmethod
    def GetControlledMinions():
        """
        Purpose: Retrieve the player's controlled minions.
        Args: None
        Returns: tuple (agent_id, minion_count)
        """
        return Player.player_instance().controlled_minions
    
    @staticmethod
    def GetLearnableCharacterSkills():
        """
        Purpose: populated at skill trainer and when using signet of capture
        Args: None
        Returns: list
        """
        return Player.player_instance().learnable_character_skills
    
    @staticmethod
    def GetUnlockedCharacterSkills():
        """
        Purpose: Retrieve the player's unlocked character skills.
        Args: None
        Returns: list
        """
        return Player.player_instance().unlocked_character_skills
    
    @staticmethod
    def GetKurzickData():
        """
        Purpose: Retrieve the player's current Kurzick data.
        Args: None
        Returns: int
        """
        return Player.player_instance().current_kurzick, Player.player_instance().total_earned_kurzick, Player.player_instance().max_kurzick
    
    @staticmethod
    def GetLuxonData():
        """
        Purpose: Retrieve the player's current Luxon data.
        Args: None
        Returns: int
        """
        return Player.player_instance().current_luxon, Player.player_instance().total_earned_luxon, Player.player_instance().max_luxon
    
    
    @staticmethod
    def GetImperialData():
        """
        Purpose: Retrieve the player's current Imperial faction.
        Args: None
        Returns: int
        """
        return Player.player_instance().current_imperial, Player.player_instance().total_earned_imperial, Player.player_instance().max_imperial
    
    @staticmethod
    def GetBalthazarData():
        """
        Purpose: Retrieve the player's current Balthazar faction.
        Args: None
        Returns: int
        """
        return Player.player_instance().current_balth, Player.player_instance().total_earned_balth, Player.player_instance().max_balth
    
    @staticmethod
    def GetActiveTitleID():
        """
        Purpose: Retrieve the player's active title ID.
        Args: None
        Returns: int
        """
        return Player.player_instance().GetActiveTitleId()
    
    @staticmethod
    def GetTitleArray():
        """
        Purpose: Retrieve the player's title array.
        Args: None
        Returns: list
        """
        return Player.player_instance().GetTitleArray()
    
    @staticmethod
    def GetTitle(title_id):
        """
        Purpose: Retrieve the player's title data.
        Args:
            title_id (int): The ID of the title to retrieve.
        Returns: int
        """
        return PyPlayer.PyTitle(title_id)
    
    @staticmethod
    def RemoveActiveTitle():
        """
        Purpose: Remove the player's active title.
        Args: None
        Returns: None
        """
        Player.player_instance().RemoveActiveTitle()
        
    @staticmethod
    def SetActiveTitle(title_id):
        """
        Purpose: Set the player's active title.
        Args:
            title_id (int): The ID of the title to set.
        Returns: None
        """
        Player.player_instance().SetActiveTitle(title_id)
        
    @staticmethod
    def DepositFaction(faction_id):
        """
        Purpose: Deposit faction points. need to be talking with an embassador.
        Args:
            faction_id (int): 0= Kurzick, 1= Luxon
        Returns: None
        """
        Player.player_instance().DepositFaction(faction_id)
        
    @staticmethod
    def LogoutToCharacterSelect():
        """
        Purpose: Logout to the character select screen.
        Args: None
        Returns: None
        """
        Player.player_instance().LogouttoCharacterSelect()
        
    @staticmethod
    def InCharacterSelectScreen():
        """
        Purpose: Check if the character select screen is ready.
        Args: None
        Returns: bool
        """
        return Player.player_instance().GetIsCharacterSelectReady()
    
    @staticmethod
    def GetLoginCharacters():
        """
        Purpose: Retrieve the available characters.
        Args: None
        Returns: list
        """
        return Player.player_instance().GetAvailableCharacters()
    
    @staticmethod
    def GetPreGameContext():
        """
        Purpose: Retrieve the pre-game context.
        Args: None
        Returns: PreGameContext
        """
        return Player.player_instance().GetPreGameContext()

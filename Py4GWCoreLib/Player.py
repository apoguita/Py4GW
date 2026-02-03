import PyPlayer

from .enums import *
from .Agent import Agent
from .native_src.internals.helpers import encoded_wstr_to_str
from .Context import GWContext
from functools import wraps
from .native_src.context.AgentContext import AgentStruct
from .native_src.context.WorldContext import TitleStruct
from .native_src.methods.PlayerMethods import PlayerMethods
from .py4gwcorelib_src.ActionQueue import ActionQueueManager

# Player
class Player:
    @staticmethod
    def _format_uuid_as_email(player_uuid) -> str:
        if not player_uuid:
            return ""
        try:
            result = encoded_wstr_to_str("uuid_" + "_".join(str(part) for part in player_uuid))
            return result if result else "INVALID"
        except TypeError:
            return str(player_uuid)
    
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
    def GetPlayerNumber() -> int | None:
        """
        Purpose: Retrieve the player's number.
        Args: None
        Returns: int
        """
        if (char_ctx := GWContext.Char.GetContext()) is None:
            return None
        return char_ctx.player_number
    
    @staticmethod
    def IsPlayerLoaded() -> bool:
        """
        Purpose: Check if the player is loaded.
        Args: None
        Returns: bool
        """
        from .Map import Map
        if not Map.IsMapReady():
            return False  
        if (player_number := Player.GetPlayerNumber()) is None:
            return False   
        if (party_ctx := GWContext.Party.GetContext()) is None:
            return False     
        if (party_info := party_ctx.player_party) is None:
            return False     
        if (players := party_info.players) is None or len(players) == 0:
            return False     
         
        for player in players:
            if player.login_number == player_number:
                return player.is_connected
            
        if (world_ctx := GWContext.World.GetContext()) is None:
            return False
        if (player_controlled_character := world_ctx.player_controlled_character) is None:
            return False
        agent_id = player_controlled_character.agent_id
        if not Agent.IsValid(agent_id):
            return False
        
        if not Agent.GetInstanceUptime(agent_id) > 750:
            return False
            
        return False
    
    @staticmethod
    def _require_player_loaded(default=None):
        """
        Decorator to ensure the player is loaded before executing the function.
        Returns `default` if not loaded.
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not Player.IsPlayerLoaded():
                    return default
                return func(*args, **kwargs)
            return wrapper
        return decorator

    #region Data
    @staticmethod
    def GetAgentID() -> int:
        """
        Purpose: Retrieve the agent ID of the player.
        Args: None
        Returns: int
        """
        if not Player.IsPlayerLoaded():
            return 0
        if (world_ctx := GWContext.World.GetContext()) is None:
            return 0
        if (player_controlled_character := world_ctx.player_controlled_character) is None:
            return 0
        return player_controlled_character.agent_id
        

    @staticmethod
    def GetName() -> str:
        """
        Purpose: Retrieve the player's name.
        Args: None
        Returns: str
        """
        return Agent.GetNameByID(Player.GetAgentID())

    @staticmethod
    def GetXY() -> tuple[float, float]:
        """
        Purpose: Retrieve the player's current X and Y coordinates.
        Args: None
        Returns: tuple (x, y)
        """
        return Agent.GetXY(Player.GetAgentID())

    
    @staticmethod
    def GetTargetID() -> int:
        """
        Purpose: Retrieve the ID of the player's target.
        Args: None
        Returns: int
        """
        return Player.player_instance().target_id

    @staticmethod
    def GetAgent() -> AgentStruct | None:
        """
        Purpose: Retrieve the player's agent.
        Args: None
        Returns: PyAgent
        """
        if not Player.IsPlayerLoaded():
            return None
        
        return Agent.GetAgentByID(Player.GetAgentID())

    @staticmethod
    def GetObservingID() -> int:
        """
        Purpose: Retrieve the ID of the agent the player is observing.
        Args: None
        Returns: int
        """
        return Player.player_instance().observing_id
    
    @staticmethod
    def GetAccountName() -> str:
        """
        Purpose: Retrieve the player's account name.
        Args: None
        Returns: str
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return ""
        if (account_info := world_ctx.account_info) is None:
            return ""
        if (account_name := account_info.account_name_str) is None:
            return ""
        return account_name
    
    @staticmethod
    def GetAccountEmail() -> str:
        """
        Purpose: Retrieve the player's account email.
        Args: None
        Returns: str
        """
        try:
            if not Player.IsPlayerLoaded():
                return ""
            
            if (char_ctx := GWContext.Char.GetContext()) is None:
                return ""
            account_email = char_ctx.player_email_str
            if account_email:
                return account_email
            player_uuid = Player.GetPlayerUUID()
            if all(part == 0 for part in player_uuid):
                return ""
            #return Player._format_uuid_as_email(player_uuid)
            return "steam_account"  # Placeholder for Steam accounts
        except Exception:
            return ""
    
    @staticmethod
    def GetPlayerUUID() -> tuple[int, int, int, int]:
        """
        Purpose: Retrieve the player's UUID.
        Args: None
        Returns: tuple[int,int,int,int]
        """
        if (char_ctx := GWContext.Char.GetContext()) is None:
            return (0, 0, 0, 0)
        player_uuid = char_ctx.player_uuid
        return player_uuid
    
    @staticmethod
    def GetInstanceUptime() -> int:
        """
        Purpose: Retrieve the player's instance uptime in seconds.
        Args: None
        Returns: int
        """
        return Agent.GetInstanceUptime(Player.GetAgentID())
    
    @staticmethod
    def GetRankData() -> tuple[int, int, int, int, int]:
        """
        Purpose: Retrieve the player's current rank data.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return 0, 0, 0, 0, 0
        if (account_info := world_ctx.account_info) is None:
            return 0, 0, 0, 0, 0
        rank = account_info.rank
        rating = account_info.rating
        qualifier_points = account_info.qualifier_points
        wins = account_info.wins
        losses = account_info.losses
        if any(value is None for value in (rank, rating, qualifier_points, wins, losses)):
            return 0, 0, 0, 0, 0
        return rank, rating, qualifier_points, wins, losses
    
    @staticmethod
    def GetTournamentRewardPoints() -> int:
        """
        Purpose: Retrieve the player's current tournament reward points.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return 0
        if (account_info := world_ctx.account_info) is None:
            return 0
        return account_info.tournament_reward_points
    
    @staticmethod
    def GetMorale() -> int:
        """
        Purpose: Retrieve the player's current morale.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return 0
        return max(world_ctx.morale, world_ctx.morale_dupe)
    
    @staticmethod
    def GetExperience() -> int:
        """
        Purpose: Retrieve the player's current experience.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return 0
        return max(world_ctx.experience, world_ctx.experience_dupe)
    
    @staticmethod
    def GetLevel() -> int:
        """
        Purpose: Retrieve the player's current level.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return 0
        return max(world_ctx.level, world_ctx.level_dupe)
    
    @staticmethod
    def GetSkillPointData() -> tuple[int, int]:
        """
        Purpose: Retrieve the player's current skill point data.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return 0, 0
        return world_ctx.current_skill_points, world_ctx.total_earned_skill_points
    
    @staticmethod
    def GetMissionsCompleted() -> list[int]:
        """
        Purpose: Retrieve the player's completed missions.
        Args: None
        Returns: list
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        if (missions_completed := world_ctx.missions_completed) is None:
            return []
        return missions_completed
    
    @staticmethod
    def GetMissionsBonusCompleted() -> list[int]:
        """
        Purpose: Retrieve the player's mission bonus data.
        Args: None
        Returns: list
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        if (missions_bonus := world_ctx.missions_bonus) is None:
            return []
        return missions_bonus
    
    @staticmethod
    def GetMissionsCompletedHM() -> list[int]:
        """
        Purpose: Retrieve the player's completed hard mode missions.
        Args: None
        Returns: list
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        if (missions_completed_hm := world_ctx.missions_completed_hm) is None:
            return []
        return missions_completed_hm
    
    @staticmethod
    def GetMissionsBonusCompletedHM() -> list[int]:
        """
        Purpose: Retrieve the player's hard mode mission bonus data.
        Args: None
        Returns: list
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        if (missions_bonus_hm := world_ctx.missions_bonus_hm) is None:
            return []
        return missions_bonus_hm
    
    @staticmethod
    def GetControlledMinions() -> list[tuple[int, int]]:
        """
        Purpose: Retrieve the player's controlled minions.
        Args: None
        Returns: tuple (agent_id, minion_count)
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        if (controlled_minions := world_ctx.controlled_minions) is None:
            return []
        result = []
        for controlled_minion in controlled_minions:
            result.append((controlled_minion.agent_id, controlled_minion.minion_count))
        return result
    
    @staticmethod
    def GetLearnableCharacterSkills() -> list[int]:
        """
        Purpose: populated at skill trainer and when using signet of capture
        Args: None
        Returns: list
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        if (learnable_character_skills := world_ctx.learnable_character_skills) is None:
            return []
        return learnable_character_skills
    
    @staticmethod
    def GetUnlockedCharacterSkills():
        """
        Purpose: Retrieve the player's unlocked character skills.
        Args: None
        Returns: list
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        if (unlocked_character_skills := world_ctx.unlocked_character_skills) is None:
            return []
        return unlocked_character_skills
        
    @staticmethod
    def GetKurzickData():
        """
        Purpose: Retrieve the player's current Kurzick data.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        current_kurzick = max(world_ctx.current_kurzick, world_ctx.current_kurzick_dupe)
        total_earned_kurzick = max(world_ctx.total_earned_kurzick, world_ctx.total_earned_kurzick_dupe)
        max_kurzick = world_ctx.max_kurzick
        return current_kurzick, total_earned_kurzick, max_kurzick

    @staticmethod
    def GetLuxonData():
        """
        Purpose: Retrieve the player's current Luxon data.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        current_luxon = max(world_ctx.current_luxon, world_ctx.current_luxon_dupe)
        total_earned_luxon = max(world_ctx.total_earned_luxon, world_ctx.total_earned_luxon_dupe)
        max_luxon = world_ctx.max_luxon
        return current_luxon, total_earned_luxon, max_luxon
    
    @staticmethod
    def GetImperialData():
        """
        Purpose: Retrieve the player's current Imperial faction.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        current_imperial = max(world_ctx.current_imperial, world_ctx.current_imperial_dupe)
        total_earned_imperial = max(world_ctx.total_earned_imperial, world_ctx.total_earned_imperial_dupe)
        max_imperial = world_ctx.max_imperial
        return current_imperial, total_earned_imperial, max_imperial
    
    @staticmethod
    def GetBalthazarData():
        """
        Purpose: Retrieve the player's current Balthazar faction.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        current_balthazar = max(world_ctx.current_balth, world_ctx.current_balth_dupe)
        total_earned_balthazar = max(world_ctx.total_earned_balth, world_ctx.total_earned_balth_dupe)
        max_balthazar = world_ctx.max_balth
        return current_balthazar, total_earned_balthazar, max_balthazar
    
    @staticmethod
    def GetActiveTitleID() -> int:
        """
        Purpose: Retrieve the player's active title ID.
        Args: None
        Returns: int
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return 0
        if (player_number := Player.GetPlayerNumber()) is None:
            return 0
        if (player := world_ctx.GetPlayerById(player_number)) is None:
            return 0
        if (active_title_tier := player.active_title_tier) is None:
            return 0
        if (titles := world_ctx.titles) is None:
            return 0
        for i, title in enumerate(titles):
            if title.current_title_tier_index == active_title_tier:
                return i
        return 0
    
    @staticmethod
    def GetTitleArrayRaw():
        """
        Purpose: Retrieve the player's title array.
        Args: None
        Returns: list
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        if (player_number := Player.GetPlayerNumber()) is None:
            return []
        if (player := world_ctx.GetPlayerById(player_number)) is None:
            return []
        if (titles := world_ctx.titles) is None:
            return []
        return titles

    
    @staticmethod
    def GetTitleArray() -> list[int]:
        """
        Purpose: Retrieve the player's title array.
        Args: None
        Returns: list
        """
        if (world_ctx := GWContext.World.GetContext()) is None:
            return []
        if (player_number := Player.GetPlayerNumber()) is None:
            return []
        if (player := world_ctx.GetPlayerById(player_number)) is None:
            return []
        if (titles := world_ctx.titles) is None:
            return []
        return [i for i,title in enumerate(titles)]
    
    @staticmethod
    def GetTitle(title_id: int) -> TitleStruct | None:
        """
        Purpose: Retrieve a title by TitleID (array index).
        Returns: TitleStruct or None
        """
        titles = Player.GetTitleArrayRaw()
        if not titles:
            return None

        if title_id < 0 or title_id >= len(titles):
            return None

        return titles[title_id]


    #region Methods
    @staticmethod
    def ChangeTarget(agent_id):
        """
        Purpose: Change the player's target.
        Args:
            agent_id (int): The ID of the agent to target.
        Returns: None
        """
        def _do_action():
            Player.player_instance().ChangeTarget(agent_id)
        #ActionQueueManager().AddAction("ACTION",PlayerMethods.ChangeTarget,agent_id)
        ActionQueueManager().AddAction("ACTION",_do_action)
        
               
    @staticmethod
    def Interact(agent_id, call_target=False):
        """
        Purpose: Interact with an agent.
        Args:
            agent_id (int): The ID of the agent to interact with.
            call_target (bool, optional): Whether to call the agent as a target.
        Returns: None
        """
        def _do_action():
            Player.player_instance().InteractAgent(agent_id, call_target)

        ActionQueueManager().AddAction("ACTION",_do_action)
        
        #ActionQueueManager().AddAction("ACTION",
        #PlayerMethods.InteractAgent,agent_id, call_target)

    @staticmethod
    def Move(x:float, y:float, zPlane:int=0):
        """
        Purpose: Move the player to specified X and Y coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
        Returns: None
        """
        ActionQueueManager().AddAction("ACTION",
        PlayerMethods.Move, x, y, zPlane)
        
    @staticmethod
    def DepositFaction(faction_id):
        """
        Purpose: Deposit faction points. need to be talking with an embassador.
        Args:
            faction_id (int): 0= Kurzick, 1= Luxon
        Returns: None
        """
        ActionQueueManager().AddAction("ACTION",
        PlayerMethods.DepositFaction,faction_id)

    @staticmethod
    def RemoveActiveTitle():
        """
        Purpose: Remove the player's active title.
        Args: None
        Returns: None
        """
        ActionQueueManager().AddAction("ACTION",
        PlayerMethods.RemoveActiveTitle)
        
    @staticmethod
    def SetActiveTitle(title_id):
        """
        Purpose: Set the player's active title.
        Args:
            title_id (int): The ID of the title to set.
        Returns: None
        """
        ActionQueueManager().AddAction("ACTION",
        PlayerMethods.SetActiveTitle,title_id)
    
    @staticmethod
    def SendRawDialog(dialog_id: int):
        """Send dialog using kSendAgentDialog. Works for NPC dialogs, skill trainers, etc."""
        PlayerMethods.SendRawDialog(dialog_id)

    @staticmethod
    def BuySkill(skill_id: int):
        """Buy/Learn a skill from a Skill Trainer."""
        PlayerMethods.SendSkillTrainerDialog(skill_id)
        
    
    #region Not Worked
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
            
        ActionQueueManager().AddAction("ACTION",
        Player.player_instance().SendDialog,dialog)
        
    @staticmethod
    def RequestChatHistory():
        """
        Purpose: Request the player's chat history.
        Args: None
        Returns: None
        """
        ActionQueueManager().AddAction("ACTION",
        Player.player_instance().RequestChatHistory)
    
    @staticmethod
    def IsChatHistoryReady():
        """
        Purpose: Check if the player's chat history is ready.
        Args: None
        Returns: bool
        """
        return Player.player_instance().IsChatHistoryReady()
    
    @staticmethod
    def GetChatHistory():
        """
        Purpose: Retrieve the player's chat history.
        Args: None
        Returns: list
        """
        return Player.player_instance().GetChatHistory()
    
    @staticmethod
    def IsTyping():
        """
        Purpose: Check if the player is currently typing.
        Args: None
        Returns: bool
        """
        return Player.player_instance().Istyping()
    
    @staticmethod
    def SendChatCommand(command):
        """
        Purpose: Send a '/' chat command.
        Args:
            command (str): The command to send.
        Returns: None
        """
        ActionQueueManager().AddAction("ACTION",
        Player.player_instance().SendChatCommand,command)

    @staticmethod
    def SendChat(channel, message):
        """
        Purpose: Send a chat message to a channel.
        Args:
            channel (char): The channel to send the message to.
            message (str): The message to send.
        Returns: None
        """
        ActionQueueManager().AddAction("ACTION",
        Player.player_instance().SendChat,channel, message)

    @staticmethod
    def SendWhisper(target_name, message):
        """
        Purpose: Send a whisper to a target player.
        Args:
            target_name (str): The name of the target player.
            message (str): The message to send.
        Returns: None
        """
        ActionQueueManager().AddAction("ACTION",
        Player.player_instance().SendWhisper,target_name, message)

    @staticmethod
    def SendFakeChat(channel:ChatChannel, message):
        """
        Purpose: Send a fake chat message to a channel.
        Args:
            channel (char): The channel to send the message to.
            message (str): The message to send.
        Returns: None
        """
        ActionQueueManager().AddAction("ACTION",
        Player.player_instance().SendFakeChat,channel.value, message)
        
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
        colored_msg = Player.FormatChatMessage(message, r, g, b)
        ActionQueueManager().AddAction("ACTION",
        Player.player_instance().SendFakeChat,channel.value, colored_msg, r, g, b)
        
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
        r = max(1, min(255, r))
        g = max(1, min(255, g))
        b = max(1, min(255, b))

        return f"<c=#{r:02X}{g:02X}{b:02X}>{message}</c>"

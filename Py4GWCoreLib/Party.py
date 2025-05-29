
import PyParty

from .Player import Player


class Party:
    @staticmethod
    def party_instance():
        """Return the PyMap instance. """
        return PyParty.PyParty()


    @staticmethod
    def GetPartyID():
        """
        Retrieve the party ID.
        Args: None
        Returns: int
        """
        return Party.party_instance().party_id

    @staticmethod
    def GetPartyLeaderID():
        """
        Purpose: Get the agent ID of the party leader.
        Args: None
        Returns: int: The agent ID of the party leader.
        """
        players = Party.GetPlayers()
        leader =  players[0]
        return Party.Players.GetAgentIDByLoginNumber(leader.login_number)

    @staticmethod
    def GetOwnPartyNumber():
        """
        Purpose: Get the party number of the player.
        Args: None
        Returns: int: The party number of the player.
        """
        for i in range(Party.party_instance().party_player_count):
            player_id = Party.Players.GetAgentIDByLoginNumber(Party.GetPlayers()[i].login_number)
            if player_id == Player.GetAgentID():
                return i # Return the 0-based party number

        # Return -1 if the player is not found in the party
        return -1

    @staticmethod
    def GetPlayers():
        """
        Purpose: Get the list of player IDs in the party.
        Args: None
        Returns: list: A list of player IDs in the party.
        """
        return Party.party_instance().players
    
    @staticmethod
    def GetHeroes():
        """
        Purpose: Get the list of hero IDs in the party.
        Args: None
        Returns: list: A list of hero IDs in the party.
        """
        return Party.party_instance().heroes

    @staticmethod
    def GetHenchmen():
        """
        Purpose: Get the list of henchmen IDs in the party.
        Args: None
        Returns: list: A list of henchmen IDs in the party.
        """
        return Party.party_instance().henchmen
    
    @staticmethod
    def GetOthers():
        """
        Purpose: Get the list of other party members.
        Args: None
        Returns: list: A list of other party members.
        """
        return Party.party_instance().others

    @staticmethod
    def IsHardModeUnlocked():
        """
        Check if hard mode is unlocked.
        Args: None
        Returns: bool
        """
        return Party.party_instance().is_hard_mode_unlocked

    @staticmethod
    def IsHardMode():
        """
        Check if the party is in hard mode.
        Args: None
        Returns: bool
        """
        return Party.party_instance().is_in_hard_mode

    @staticmethod
    def IsNormalMode():
        """
        Check if the party is in normal mode.
        Args: None
        Returns: bool
        """
        return not Party.IsHardMode()

    @staticmethod
    def GetPartySize():
        """
        Purpose: Retrieve the size of the party.
        Args: None
        Returns: int
        """
        return Party.party_instance().party_size

    @staticmethod
    def GetPlayerCount():
        """
        Purpose: Retrieve the number of players in the party.
        Args: None
        Returns: int
        """
        return Party.party_instance().party_player_count

    @staticmethod
    def GetHeroCount():
        """
        Purpose: Retrieve the number of heroes in the party.
        Args: None
        Returns: int
        """
        return Party.party_instance().party_hero_count

    @staticmethod
    def GetHenchmanCount():
        """
        Purpose: Retrieve the number of henchmen in the party.
        Args: None
        Returns: int
        """
        return Party.party_instance().party_henchman_count

    @staticmethod
    def IsPartyDefeated():
        """
        Purpose: Check if the party has been defeated.
        Args: None
        Returns: bool
        """
        return Party.party_instance().is_party_defeated

    @staticmethod
    def IsPartyLoaded():
        """
        Purpose: Check if the party is loaded.
        Args: None
        Returns: bool
        """
        return Party.party_instance().is_party_loaded

    @staticmethod
    def IsPartyLeader():
        """
        Purpose: Check if the player is the party leader.
        Args: None
        Returns: bool
        """
        return Party.party_instance().is_party_leader

    #tick is an option to check if party member is ready
    @staticmethod
    def SetTickasToggle(enable):
        """
        Purpose: Set the tick as a toggle.
        Args: Bool
        Returns: None
        """
        Party.party_instance().tick.SetTickToggle(enable)

    @staticmethod
    def IsAllTicked():
        """
        Purpose: Check if the player is ready.
        Args: None
        Returns: bool
        """
        return Party.party_instance().tick.IsTicked()

    @staticmethod
    def IsPlayerTicked (login_number):
        """
        Purpose: Check if the player is ready.
        Args: None
        Returns: bool
        """
        return Party.party_instance().GetIsPlayerTicked(login_number)

    @staticmethod
    def SetTicked(ticked):
        """
        Purpose: Set the player as ready.
        Args: None
        Returns: None
        """
        Party.party_instance().tick.SetTicked(ticked)

    @staticmethod
    def ToggleTicked():
        """
        Purpose: Toggle the player ready status.
        Args: None
        Returns: None
        """
        login_number = Party.Players.GetLoginNumberByAgentID(Player.GetAgentID())
        party_number = Party.Players.GetPartyNumberFromLoginNumber(login_number)

        if Party.IsPlayerTicked(party_number):
            Party.SetTicked(False)
        else:
            Party.SetTicked(True)
            
        #Party.party_instance().tick.ToggleTicked() #faulty from toolbox

    @staticmethod
    def SetHardMode():
        """
        Set the party to hard mode.
        Args: None
        """
        if Party.IsHardModeUnlocked() and Party.IsNormalMode():
            Party.party_instance().SetHardMode(True)

    @staticmethod
    def SetNormalMode():
        """
        Set the party to normal mode.
        Args: None
        """

        if Party.IsHardMode():
            Party.party_instance().SetHardMode(False)

    @staticmethod
    def SearchParty(search_type, advertisement):
        """
        Search for a party.
        Args:
            search_type (int): The search type.
            advertisement (str): The advertisement.
        Returns: bool
        """
        return Party.party_instance().SearchParty(search_type, advertisement)

    @staticmethod
    def SearchPartyCancel():
        """
        Cancel the party search.
        Args: None
        Returns: None
        """
        Party.party_instance().SearchPartyCancel()

    @staticmethod
    def SearchPartyReply(accept=True):
        """
        Reply to a party search.
        Args:
            accept (bool): Whether to accept the party search.
        Returns: bool
        """
        return Party.party_instance().SearchPartyReply(accept)

    @staticmethod
    def RespondToPartyRequest(party_id, accept):
        """
        Respond to a party request.
        Args:
            party_id (int): The party ID.
            accept (bool): Whether to accept the party request.
        Returns: bool
        """
        Party.party_instance().RespondToPartyRequest(party_id, accept)

    @staticmethod
    def ReturnToOutpost():
        """
        Return to the outpost.
        Args: None
        """
        Party.party_instance().ReturnToOutpost()

    @staticmethod
    def LeaveParty():
        """
        Leave the party.
        Args: None
        """
        Party.party_instance().LeaveParty()

    class Players:
        @staticmethod
        def GetAgentIDByLoginNumber(login_number):
            """
            Retrieve the agent ID by login number.
            Args:
                login_number (int): The login number.
            Returns: int
            """
            return Party.party_instance().GetAgentIDByLoginNumber(login_number)

        @staticmethod
        def GetPlayerNameByLoginNumber(login_number):
            """
            Retrieve the player name by login number.
            Args:
                login_number (int): The login number.
            Returns: str
            """
            return Party.party_instance().GetPlayerNameByLoginNumber(login_number)

        @staticmethod
        def GetPartyNumberFromLoginNumber(login_number):
            """
            Retrieve the party number from the login number.
            Args:
                login_number (int): The login number.
            Returns: int
            """
            players = Party.GetPlayers()

            for index, player in enumerate(players):
                if player.login_number == login_number:
                    return index

            return -1

        @staticmethod
        def GetLoginNumberByAgentID(agent_id):
            """
            Retrieve the login number by agent ID.
            Args:
                agent_id (int): The agent ID.
            Returns: int
            """
            players = Party.GetPlayers()
            if len(players) > 0:
                for player in players:
                    Pagent_id = Party.Players.GetAgentIDByLoginNumber(player.login_number)
                    if agent_id == Pagent_id:
                        return player.login_number
            return 0

        @staticmethod
        def InvitePlayer(agent_id_or_name):
            """
            Invite a player by ID (int) or name (str).
            Args: 
                player (int or str): The player ID or player name.
            """
            if isinstance(agent_id_or_name, int):
                Party.party_instance().InvitePlayer(agent_id_or_name)
            elif isinstance(agent_id_or_name, str):
                Player.SendChatCommand("invite " + agent_id_or_name)

            else:
                raise TypeError("Invalid argument type. Must be int (ID) or str (name).")

        @staticmethod
        def KickPlayer(login_number):
            """
            Kick a player from the party by ID.
            Args: 
                login_number (int): The player ID.
            """
            Party.party_instance().KickPlayer(login_number)

    class Heroes:
        @staticmethod
        def GetHeroAgentIDByPartyPosition(hero_position):
            """
            Retrieve the Agent ID by hero ID.
            Args:
                hero_index (int): The hero index.
            Returns: int
            """
            return Party.party_instance().GetHeroAgentID(hero_position)

        @staticmethod
        def GetHeroIDByAgentID(agent_id):
            """
            Retrieve the hero ID of an agent.
            Args:
                agent_id (int): The agent ID.
            Returns: int
            """
            heroes = Party.GetHeroes()
            for hero in heroes:
                if hero.agent_id == agent_id:
                    return hero.hero_id.GetID()


        @staticmethod
        def GetHeroIDByPartyPosition(hero_position):
            """
            Retrieve the hero ID by party position.
            Args:
                hero_position (int): The hero position.
            Returns: int
            """
            heroes = Party.GetHeroes()
            for index, hero in enumerate(heroes):
                if index == hero_position:
                    return hero.hero_id.GetID()

        @staticmethod
        def GetHeroIdByName(hero_name):
            """
            Retrieve the hero ID by name.
            Args:
                hero_name (str): The hero name.
            Returns: int
            """
            hero = PyParty.Hero(hero_name)
            return hero.GetID()

        @staticmethod
        def GetHeroNameById(hero_id):
            """
            Retrieve the hero name by ID.
            Args:
                hero_id (int): The hero ID.
            Returns: str
            """
            hero = PyParty.Hero(hero_id)
            return hero.GetName()

        @staticmethod
        def GetNameByAgentID(agent_id):
            """
            Retrieve the hero name by agent ID.
            Args:
                agent_id (int): The agent ID.
            Returns: str
            """
            heroes = Party.GetHeroes()
            for hero in heroes:
                if hero.agent_id == agent_id:
                    return hero.hero_id.GetName()


        @staticmethod
        def AddHero(hero_id):
            """
            Add a hero to the party by ID.
            Args: 
                hero_id (int): The hero ID.
            """
            Party.party_instance().AddHero(hero_id)

        @staticmethod
        def AddHeroByName(hero_name):
            """
            Add a hero to the party by name.
            Args: 
                hero_name (str): The hero name.
            """
            hero = PyParty.Hero(hero_name)
            Party.party_instance().AddHero(hero.GetID())

        @staticmethod
        def KickHero(hero_id):
            """
            Kick a hero from the party by ID.
            Args: 
                hero_id (int): The hero ID.
            """
            Party.party_instance().KickHero(hero_id)

        @staticmethod
        def KickHeroByName(hero_name):
            """
            Kick a hero from the party by name.
            Args: 
                hero_name (str): The hero name.
            """
            hero = PyParty.Hero(hero_name)
            Party.party_instance().KickHero(hero.GetID())

        @staticmethod
        def KickAllHeroes():
            """
            Kick all heroes from the party.
            Args: None
            """
            Party.party_instance().KickAllHeroes()
            
        @staticmethod
        def UseSkill(hero_agent_id, slot, target_id):
            """
            Use a skill on a hero.
            Args:
                hero_id (int): The hero ID.
                slot (int): The skill slot.
            """
            #return #function is not working atm
            Party.party_instance().UseHeroSkill(hero_agent_id, slot, target_id)

        @staticmethod
        def FlagHero (hero_id, x, y):
            """
            Flag a hero to a specific location.
            Args:
                hero_id (int): The hero ID.
                x (float): The X coordinate.
                y (float): The Y coordinate.
            """
            Party.party_instance().FlagHero(hero_id, x, y)
        
        @staticmethod
        def FlagAllHeroes(x, y):
            """
            Flag all heroes to a specific location.
            Args:
                x (float): The X coordinate.
                y (float): The Y coordinate.
            """
            Party.party_instance().FlagAllHeroes(x, y)

        @staticmethod
        def UnflagHero(hero_id):
            """
            Unflag a hero.
            Args:
                hero_id (int): The hero ID.
            """
            Party.party_instance().UnflagHero(hero_id)
        
        @staticmethod
        def UnflagAllHeroes():
            """
            Unflag all heroes.
            Args: None
            """
            Party.party_instance().UnflagAllHeroes()

        @staticmethod
        def IsHeroFlagged(hero_party_number):
            """
            Check if a hero is flagged.
            Args:
                hero_id (int): The hero ID.
            Returns: bool
            """
            return Party.party_instance().IsHeroFlagged(hero_party_number)

        @staticmethod
        def IsAllFlagged():
            """
            Check if all heroes are flagged.
            Args: None
            Returns: bool
            """
            return Party.party_instance().IsAllFlagged()

        @staticmethod
        def GetAllFlag():
            """
            Get all flags.
            Args: None
            Returns: list
            """
            return Party.party_instance().GetAllFlagX(), Party.party_instance().GetAllFlagY()

        @staticmethod
        def SetHeroBehavior (hero_agent_id, behavior):
            """
            Set the behavior of a hero.
            Args:
                hero_id (int): The hero agent ID.
                behavior (int): 0=Fight, 1=Guard, 2=Avoid
            """
            Party.party_instance().SetHeroBehavior(hero_agent_id, behavior)

    class Henchmen:
        @staticmethod
        def AddHenchman(henchman_id):
            """
            Add a henchman to the party by ID.
            Args: 
                henchman_id (int): The henchman ID.
            """
            Party.party_instance().AddHenchman(henchman_id)

        @staticmethod
        def KickHenchman(henchman_id):
            """
            Kick a henchman from the party by ID.
            Args: 
                henchman_id (int): The henchman ID.
            """
            Party.party_instance().KickHenchman(henchman_id)

    class Pets:
        @staticmethod
        def SetPetBehavior(behavior, lock_target_id):
            """
            Set the behavior of a pet.
            Args:
                pet_id (int): The pet agent ID.
                behavior (int): 0=Fight, 1=Guard, 2=Avoid
            """
            Party.party_instance().SetPetBehavior(behavior, lock_target_id)

        @staticmethod
        def GetPetBehavior(owner_id):
            """
            Get the pet behavior.
            Args:
                owner_id (int): The owner ID.
            Returns: int
            """
            pet_info =  Party.party_instance().GetPetInfo(owner_id)
            if not pet_info:
                return False
            return pet_info.behavior

        @staticmethod
        def GetPetInfo(owner_id):
            """
            Get the pet information.
            Args:
                owner_id (int): The owner ID.
            Returns: tuple
            """
            return Party.party_instance().GetPetInfo(owner_id)

        @staticmethod
        def GetPetID(owner_id):
            """
            Get the pet ID.
            Args:
                owner_id (int): The owner ID.
            Returns: int
            """
            pet_info =  Party.party_instance().GetPetInfo(owner_id)
            if not pet_info:
                return 0
            return pet_info.agent_id
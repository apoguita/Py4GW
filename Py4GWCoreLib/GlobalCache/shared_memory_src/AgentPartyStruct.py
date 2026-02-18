from ctypes import Structure, c_uint, c_bool

class AgentPartyStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("IsTicked", c_bool),
        ("PartyID", c_uint),
        ("PartyPosition", c_uint),
        ("IsPartyLeader", c_bool),
    ]

    # Inline annotations for IntelliSense
    IsTicked: bool
    PartyID: int
    PartyPosition: int
    IsPartyLeader: bool

    def reset(self) -> None:
        """Reset all fields to zero or false."""
        self.IsTicked = False
        self.PartyID = 0
        self.PartyPosition = 0
        self.IsPartyLeader = False
        
    def GetLoginNumber(self):
        from ...Player import Player
        import PyParty
        
        if (party_instance := PyParty.PyParty()) is None: return 0
        players = party_instance.players if party_instance else []
        agent_id = Player.GetAgentID() if Player.IsPlayerLoaded() else 0
        if len(players) > 0:
            for player in players:
                Pagent_id = party_instance.GetAgentIDByLoginNumber(player.login_number) if party_instance else 0
                if agent_id == Pagent_id:
                    return player.login_number
        return 0  
        
    def GetPartyNumber(self):
        import PyParty
        if (party_instance := PyParty.PyParty()) is None: return 0
        login_number = self.GetLoginNumber()
        players = party_instance.players if party_instance else []

        for index, player in enumerate(players):
            if player.login_number == login_number:
                return index

        return -1
        
    def from_context(self) -> None:
        from ...Party import Party
        party_number = self.GetPartyNumber()
        
        self.IsTicked = Party.IsPlayerTicked(party_number)
        self.PartyID = Party.GetPartyID()
        self.PartyPosition = party_number
        self.IsPartyLeader = Party.IsPartyLeader()


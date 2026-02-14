from ctypes import Structure, c_uint
#region Rank
class RankStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Rank", c_uint),
        ("Rating", c_uint),
        ("QualifierPoints", c_uint),
        ("Wins", c_uint),
        ("Losses", c_uint),
        ("TournamentRewardPoints", c_uint),
    ]
    
    # Inline annotations for IntelliSense
    Rank: int
    Rating: int
    QualifierPoints: int
    Wins: int
    Losses: int
    TournamentRewardPoints: int
    
    def reset(self) -> None:
        """Return a blank RankStruct with all fields set to zero."""
        self.Rank = 0
        self.Rating = 0
        self.QualifierPoints = 0
        self.Wins = 0
        self.Losses = 0
        self.TournamentRewardPoints = 0
        
    def from_context (self):
        from ...Player import Player
        rank_data = Player.GetRankData()

        self.Rank = rank_data[0]
        self.Rating = rank_data[1]
        self.QualifierPoints = rank_data[2]
        self.Wins = rank_data[3]
        self.Losses = rank_data[4]
        self.TournamentRewardPoints = Player.GetTournamentRewardPoints()
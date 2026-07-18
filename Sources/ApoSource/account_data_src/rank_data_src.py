from Py4GWCoreLib import Player
import PyImGui
#region RankData
class RankData:
    def __init__(self):
        self.rank = 0
        self.rating = 0
        self.qualifier_points = 0
        self.wins = 0
        self.losses = 0
        self.tournament_reward_points = 0
    
    def update(self):
        rank_data = Player.GetRankData()
        self.rank = rank_data[0]
        self.rating = rank_data[1]
        self.qualifier_points = rank_data[2]
        self.wins = rank_data[3]
        self.losses = rank_data[4]
        self.tournament_reward_points = Player.GetTournamentRewardPoints()

    def draw_content(self):
        PyImGui.text(f"Rank: {self.rank}")
        PyImGui.text(f"Rating: {self.rating}")
        PyImGui.text(f"Qualifier Points: {self.qualifier_points}")
        PyImGui.text(f"Wins: {self.wins}")
        PyImGui.text(f"Losses: {self.losses}")
        PyImGui.text(f"Tournament Reward Points: {self.tournament_reward_points}")
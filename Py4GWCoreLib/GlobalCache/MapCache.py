
from ..Map import Map
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
from Py4GWCoreLib.enums import outposts, explorables, name_to_map_id

class MapCache:
    def __init__(self, action_queue_manager: ActionQueueManager):
        self._name = ""
        self._action_queue_manager = action_queue_manager
        
    def _update_cache(self):
        pass
        
    def IsMapReady(self):
        return Map.IsMapReady()
    
    def IsOutpost(self):
        return Map.IsOutpost()
    
    def IsExplorable(self):
        return Map.IsExplorable()
    
    def IsMapLoading(self):
        return Map.IsMapLoading()
    
    def GetMapName(self, mapid: int | None = None) -> str:
        return Map.GetMapName(mapid)
 
    def GetMapID(self):
        return Map.GetMapID()

    def GetOutpostIDs(self):
        """Retrieve the outpost IDs."""
        global outposts
        return list(outposts.keys())
    
    def GetOutpostNames(self):
        """Retrieve the outpost names."""
        global outposts
        return list(outposts.values())
    
    def GetMapIDByName(self, name: str) -> int:
        return Map.GetMapIDByName(name)
    
    def GetExplorableIDs(self):
        return list(explorables.keys())

    def GetExplorableNames(self):
        return list(explorables.values())
    
    def Travel(self, map_id):
        self._action_queue_manager.AddAction("ACTION", Map.Travel, map_id)
        
    def TravelToDistrict(self, map_id, district=0, district_number=0):
        self._action_queue_manager.AddAction("ACTION", Map.TravelToDistrict, map_id, district, district_number)
        
    def TravelToRegion(self, map_id, server_region, district_number, language=0):
        self._action_queue_manager.AddAction("ACTION", Map.TravelToRegion, map_id, server_region, district_number, language)
        
    def TravelGH(self):
        self._action_queue_manager.AddAction("ACTION", Map.TravelGH)
        
    def LeaveGH(self):
        self._action_queue_manager.AddAction("ACTION", Map.LeaveGH)
        
    def GetInstanceUptime(self):
        return Map.GetInstanceUptime()
    
    def GetMaxPartySize(self):
        return Map.GetMaxPartySize()
    
    def GetMinPartySize(self):
        return Map.GetMinPartySize()
    
    def IsInCinematic(self):
        return Map.IsInCinematic()
    
    def SkipCinematic(self):        
        self._action_queue_manager.AddAction("TRANSITION", Map.SkipCinematic)
        
    def HasEnterChallengeButton(self):
        return Map.HasEnterChallengeButton()
    
    def IsOnWorldMap(self):
        return Map.IsOnWorldMap()
    
    def IsPVP(self):
        return Map.IsPVP()
    
    def IsGuildHall(self):
        return Map.IsGuildHall()
    
    def EnterChallenge(self):
        self._action_queue_manager.AddAction("ACTION", Map.EnterChallenge)
        
    def CancelEnterChallenge(self):
        self._action_queue_manager.AddAction("ACTION", Map.CancelEnterChallenge)
        
    def IsVanquishable(self):
        return Map.IsVanquishable()
    
    def GetFoesKilled(self):
        return Map.GetFoesKilled()
    
    def GetFoesToKill(self):
        return Map.GetFoesToKill()
    
    def GetIsVanquishComplete(self):
        if self.IsVanquishable():
            return Map.GetFoesToKill() == 0
        return False
    
    def GetCampaign(self):
        return Map.GetCampaign()
    
    def GetContinent(self):
        return Map.GetContinent()
    
    def GetRegionType(self):
        return Map.GetRegionType()
    
    def GetDistrict(self):
        return Map.GetDistrict()
    
    def GetRegion(self):
        return Map.GetRegion()
    
    def GetLanguage(self):
        return Map.GetLanguage()
    
    def GetIsMapUnlocked(self,mapid=None):
        """Check if the map is unlocked."""
        return Map.IsMapUnlocked(mapid)

    def GetAmountOfPlayersInInstance(self):
        return Map.GetAmountOfPlayersInInstance()
    
    def GetFlags(self):
        return Map.GetFlags()
    
    def GetThumbnailID(self):
        return Map.GetThumbnailID()
    
    def GetMinPlayerSize(self):
        return Map.GetMinPlayerSize()
    
    def GetMaxPlayerSize(self):
        return Map.GetMaxPlayerSize()
    
    def GetControlledOutpostID(self):
        return Map.GetControlledOutpostID()
    
    def GetFractionMission(self):
        return Map.GetFractionMission()
       
    def GetMinLevel(self):
        return Map.GetMinLevel()
    
    def GetMaxLevel(self):
        return Map.GetMaxLevel()
    
    def GetNeededPQ(self):
        return Map.GetNeededPQ()
    
    def GetMissionMapsTo(self):
        return Map.GetMissionMapsTo()
    
    def GetIconPosition(self):
        return Map.GetIconPosition
    
    def GetIconStartPosition(self):
        return Map.GetIconStartPosition()
    
    def GetIconEndPosition(self):
        return Map.GetIconEndPosition()

    def GetFileID(self):
        return Map.GetFileID()
        
    def GetMissionChronology(self):
        return Map.GetMissionChronology()
        
    def GetHAChronology(self):
        return Map.GetHAChronology()

    def GetNameID(self):
        return Map.GetNameID()

    def GetDescriptionID(self):
        return Map.GetDescriptionID()
    
    def GetMapWorldMapBounds(self):
        import PyMap
        map_info = PyMap.PyMap()

        if map_info.icon_start_x == 0 and map_info.icon_start_y == 0 and map_info.icon_end_x == 0 and map_info.icon_end_y == 0:
            left   = float(map_info.icon_start_x_dupe)
            top    = float(map_info.icon_start_y_dupe)
            right  = float(map_info.icon_end_x_dupe)
            bottom = float(map_info.icon_end_y_dupe)
        else:
            left   = float(map_info.icon_start_x)
            top    = float(map_info.icon_start_y)
            right  = float(map_info.icon_end_x)
            bottom = float(map_info.icon_end_y)

        return left, top, right, bottom
    
    def GetMapBoundaries(self):
        import PyMap
        boundaries = PyMap.PyMap().map_boundaries
        if len(boundaries) < 5:
            return 0.0, 0.0, 0.0, 0.0  # Optional: fallback for safety

        min_x = boundaries[1]
        min_y = boundaries[2]
        max_x = boundaries[3]
        max_y = boundaries[4]

        return min_x, min_y, max_x, max_y
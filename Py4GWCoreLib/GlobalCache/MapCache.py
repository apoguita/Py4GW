import PyMap
from PyMap import MapID

from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
from Py4GWCoreLib.enums import outposts, explorables, explorable_name_to_id

class MapCache:
    def __init__(self, action_queue_manager: ActionQueueManager):
        self._map_instance = PyMap.PyMap()
        self._name = ""
        self._action_queue_manager = action_queue_manager
        
    def _update_cache(self):
        self._map_instance.GetContext()
        
    def IsMapReady(self):
        return self._map_instance.is_map_ready
    
    def IsOutpost(self):
        return self._map_instance.instance_type.GetName() == "Outpost"
    
    def IsExplorable(self):
        return self._map_instance.instance_type.GetName() == "Explorable"
    
    def IsMapLoading(self):
        return self._map_instance.instance_type.GetName() == "Loading"
    
    def GetMapName(self, mapid=None):
        if mapid is None:
            map_id = self._map_instance.map_id.ToInt()
        else:
            map_id = mapid

        if map_id in outposts:
            return outposts[map_id]
        if map_id in explorables:
            return explorables[map_id]

        map_id_instance = MapID(map_id)
        return map_id_instance.GetName()
    
    def GetMapID(self):
        return self._map_instance.map_id.ToInt()

    def GetOutpostIDs(self):
        """Retrieve the outpost IDs."""
        global outposts
        return list(outposts.keys())
    
    def GetOutpostNames(self):
        """Retrieve the outpost names."""
        global outposts
        return list(outposts.values())
    
    def GetMapIDByName(self, name) -> int:
        global explorable_name_to_id
        map_id = explorable_name_to_id.get(name)
        if map_id is not None:
            return map_id

        outpost_ids = self.GetOutpostIDs()
        outpost_names = self.GetOutpostNames()
        outpost_name_to_id = {name: id for name, id in zip(outpost_names, outpost_ids)}
        return int(outpost_name_to_id.get(name, 0))

    
    def GetExplorableIDs(self):
        return list(explorables.keys())

    def GetExplorableNames(self):
        return list(explorables.values())
    
    def Travel(self, map_id):
        self._action_queue_manager.AddAction("ACTION", self._map_instance.Travel, map_id)
        
    def TravelToDistrict(self, map_id, district=0, district_number=0):
        self._action_queue_manager.AddAction("ACTION", self._map_instance.Travel, map_id, district, district_number)
        
    def TravelToRegion(self, map_id, server_region, district_number, language=0):
        self._action_queue_manager.AddAction("ACTION", self._map_instance.Travel, map_id, server_region, district_number, language)
        
    def TravelGH(self):
        self._action_queue_manager.AddAction("ACTION", self._map_instance.TravelGH)
        
    def LeaveGH(self):
        self._action_queue_manager.AddAction("ACTION", self._map_instance.LeaveGH)
        
    def GetInstanceUptime(self):
        return self._map_instance.instance_time
    
    def GetMaxPartySize(self):
        return self._map_instance.max_party_size
    
    def GetMinPartySize(self):
        return self._map_instance.min_party_size
    
    def IsInCinematic(self):
        return self._map_instance.is_in_cinematic
    
    def SkipCinematic(self):
        self._action_queue_manager.AddAction("ACTION", self._map_instance.SkipCinematic)
        
    def HasEnterChallengeButton(self):
        return self._map_instance.has_enter_button
    
    def EnterChallenge(self):
        self._action_queue_manager.AddAction("ACTION", self._map_instance.EnterChallenge)
        
    def CancelEnterChallenge(self):
        self._action_queue_manager.AddAction("ACTION", self._map_instance.CancelEnterChallenge)
        
    def IsVanquishable(self):
        return self._map_instance.is_vanquishable_area
    
    def GetFoesKilled(self):
        return self._map_instance.foes_killed
    
    def GetFoesToKill(self):
        return self._map_instance.foes_to_kill
    
    def GetCampaign(self):
        campaign = self._map_instance.campaign
        return campaign.ToInt(), campaign.GetName()
    
    def GetContinent(self):
        continent = self._map_instance.continent
        return continent.ToInt(), continent.GetName()
    
    def GetRegionType(self):
        region_type = self._map_instance.region_type
        return region_type.ToInt(), region_type.GetName()
    
    def GetDistrict(self):
        return self._map_instance.district
    
    def GetRegion(self):
        return self._map_instance.server_region.ToInt(), self._map_instance.server_region.GetName()
    
    def GetLanguage(self):
        return self._map_instance.language.ToInt(), self._map_instance.language.GetName()
    
    def RegionFromDistrict(self, district):
        region = self._map_instance.RegionFromDistrict(district)
        return region.ToInt(), region.GetName()

    def LanguageFromDistrict(self, district):
        language = self._map_instance.LanguageFromDistrict(district)
        return language.ToInt(), language.GetName()
    
    def GetIsMapUnlocked(self,mapid=None):
        """Check if the map is unlocked."""
        if mapid is None:
            map_id = self._map_instance.map_id.ToInt()
        else:
            map_id = mapid
        return self._map_instance.GetIsMapUnlocked(map_id)

    def GetAmountOfPlayersInInstance(self):
        return self._map_instance.amount_of_players_in_instance
    
    def GetFlags(self):
        return self._map_instance.flags
    
    def GetThumbnailID(self):
        return self._map_instance.thumbnail_id
    
    def GetMinPlayerSize(self):
        return self._map_instance.min_player_size
    
    def GetMaxPlayerSize(self):
        return self._map_instance.max_player_size
    
    def GetControlledOutpostID(self):
        return self._map_instance.controlled_outpost_id
    
    def GetFractionMission(self):
        return self._map_instance.fraction_mission
       
    def GetMinLevel(self):
        return self._map_instance.min_level
    
    def GetMaxLevel(self):
        return self._map_instance.max_level
    
    def GetNeededPQ(self):
        return self._map_instance.needed_pq
    
    def GetMissionMapsTo(self):
        return self._map_instance.mission_maps_to
    
    def GetIconPosition(self):
        return self._map_instance.icon_position_x, self._map_instance.icon_position_y
    
    def GetIconStartPosition(self):
        return self._map_instance.icon_start_x, self._map_instance.icon_start_y
    
    def GetIconEndPosition(self):
        return self._map_instance.icon_end_x, self._map_instance.icon_end_y
    
    def GetIconStartPositionDupe(self):
        return self._map_instance.icon_start_x_dupe, self._map_instance.icon_start_y_dupe
    
    def GetIconEndPositionDupe(self):
        return self._map_instance.icon_end_x_dupe, self._map_instance.icon_end_y_dupe

    def GetFileID(self):
        return self._map_instance.file_id
        
    def GetMissionChronology(self):
        return self._map_instance.mission_chronology
        
    def GetHAChronology(self):
        return self._map_instance.ha_map_chronology

    def GetNameID(self):
        return self._map_instance.name_id

    def GetDescriptionID(self):
        return self._map_instance.description_id
    
    def GetMapWorldMapBounds(self):
        map_info = self._map_instance

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
        boundaries = self._map_instance.map_boundaries
        if len(boundaries) < 5:
            return 0.0, 0.0, 0.0, 0.0  # Optional: fallback for safety

        min_x = boundaries[1]
        min_y = boundaries[2]
        max_x = boundaries[3]
        max_y = boundaries[4]

        return min_x, min_y, max_x, max_y
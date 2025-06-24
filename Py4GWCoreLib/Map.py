import Py4GW
import PyMap
import PyMissionMap
import PyPathing
import PyOverlay
from .enums import outposts, outpost_name_to_id, explorables, explorable_name_to_id, FlagPreference
from .UIManager import *
from .Overlay import *
from collections import deque
import time
import math

class Map:
    @staticmethod
    def map_instance():
        """Return the PyMap instance. """
        return PyMap.PyMap() 

    @staticmethod
    def IsMapReady():
        """Check if the map is ready to be handled."""
        return Map.map_instance().is_map_ready

    @staticmethod
    def IsOutpost():
        """Check if the map instance is an outpost."""
        return Map.map_instance().instance_type.GetName() == "Outpost"

    @staticmethod
    def IsExplorable():
        """Check if the map instance is explorable."""
        return Map.map_instance().instance_type.GetName() == "Explorable"

    @staticmethod
    def IsMapLoading():
        """Check if the map instance is loading."""
        return Map.map_instance().instance_type.GetName() == "Loading"

    @staticmethod
    def GetMapName(mapid=None):
        """
        Retrieve the name of a map by its ID.
        Args:
            mapid (int, optional): The ID of the map to retrieve. Defaults to the current map.
        Returns: str
        """
        global outposts, explorables
        if mapid is None:
            map_id = Map.GetMapID()
        else:
            map_id = mapid

        if map_id in outposts:
            return outposts[map_id]
        if map_id in explorables:
            return explorables[map_id]

        map_id_instance = PyMap.MapID(map_id)
        return map_id_instance.GetName()

    @staticmethod
    def GetMapID():
        """Retrieve the ID of the current map."""
        return Map.map_instance().map_id.ToInt()

    @staticmethod
    def GetOutpostIDs():
        """Retrieve the outpost IDs."""
        global outposts
        return list(outposts.keys())

    @staticmethod
    def GetOutpostNames():
        """Retrieve the outpost names."""
        global outposts
        return list(outposts.values())
    
    @staticmethod
    def GetMapIDByName(name) -> int:
        global explorable_name_to_id
        """Retrieve the ID of a map by its name."""
        map_id = explorable_name_to_id.get(name)
        if map_id is not None:
            return map_id

        # Get outpost IDs and names, and build a reverse lookup map
        outpost_ids = Map.GetOutpostIDs()
        outpost_names = Map.GetOutpostNames()
        outpost_name_to_id = {name: id for id, name in zip(outpost_names, outpost_ids)}

        # Check if the name exists in outposts
        return int(outpost_name_to_id.get(name, 0))
        

    @staticmethod
    def GetExplorableIDs():
        """
        Retrieve all explorable map IDs.
        Returns: list[int]
        """
        global explorables
        return list(explorables.keys())

    @staticmethod
    def GetExplorableNames():
        """
        Retrieve all explorable map names.
        Returns: list[str]
        """
        global explorables
        return list(explorables.values())
        

    @staticmethod
    def Travel(map_id):
        """Travel to a map by its ID."""
        Map.map_instance().Travel(map_id)

    @staticmethod
    def TravelToDistrict(map_id, district=0, district_number=0):
        """
        Travel to a map by its ID and district.
        Args:
            map_id (int): The ID of the map to travel to.
            district (int): The district to travel to.
            district_number (int): The number of the district to travel to.
        Returns: None
        """
        Map.map_instance().Travel(map_id, district, district_number)
        
    #bool Travel(int map_id, int server_region, int district_number, int language);
    @staticmethod
    def TravelToRegion(map_id, server_region, district_number, language=0):
        """
        Travel to a map by its ID and region.
        Args:
            map_id (int): The ID of the map to travel to.
            server_region (int): The region to travel to.
            district_number (int): The number of the district to travel to.
            language (int): The language to travel to.
        Returns: None
        """
        Map.map_instance().Travel(map_id, server_region, district_number, language)
    
    @staticmethod
    def TravelGH():
        """Travel to the Guild Hall."""
        Map.map_instance().TravelGH()
        
    @staticmethod
    def LeaveGH():
        """Leave the Guild Hall."""
        Map.map_instance().LeaveGH()

    @staticmethod
    def GetInstanceUptime():
        """Retrieve the uptime of the current instance."""
        return Map.map_instance().instance_time

    @staticmethod
    def GetMaxPartySize():
        """ Retrieve the maximum party size of the current map."""
        return Map.map_instance().max_party_size
    
    @staticmethod
    def GetMinPartySize():
        """ Retrieve the minimum party size of the current map."""
        return Map.map_instance().min_party_size

    @staticmethod
    def IsInCinematic():
        """Check if the map is in a cinematic."""
        return Map.map_instance().is_in_cinematic

    @staticmethod
    def SkipCinematic():
        """ Skip the cinematic."""
        Map.map_instance().SkipCinematic()

    @staticmethod
    def HasEnterChallengeButton():
        """Check if the map has an enter challenge button."""
        return Map.map_instance().has_enter_button

    @staticmethod
    def EnterChallenge():
        """Enter the challenge."""
        Map.map_instance().EnterChallenge()

    @staticmethod
    def CancelEnterChallenge():
        """Cancel entering the challenge."""
        Map.map_instance().CancelEnterChallenge()

    @staticmethod
    def IsVanquishable():
        """Check if the map is vanquishable."""
        return Map.map_instance().is_vanquishable_area

    @staticmethod
    def GetFoesKilled():
        """
        Retrieve the number of foes killed in the current map.
        Args: None
        Returns: int
        """
        return Map.map_instance().foes_killed

    @staticmethod
    def GetFoesToKill():
        """
        Retrieve the number of foes to kill in the current map.
        Args: None
        Returns: int
        """
        return Map.map_instance().foes_to_kill

    @staticmethod
    def GetCampaign():
        """
        Retrieve the campaign of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        campaign = Map.map_instance().campaign
        return campaign.ToInt(), campaign.GetName()

    @staticmethod
    def GetContinent():
        """
        Retrieve the continent of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        continent = Map.map_instance().continent
        return continent.ToInt(), continent.GetName()

    @staticmethod
    def GetRegionType():
        """
        Retrieve the region type of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        region_type = Map.map_instance().region_type
        return region_type.ToInt(), region_type.GetName()

    @staticmethod
    def GetDistrict():
        """Retrieve the district of the current map."""
        return Map.map_instance().district

    @staticmethod
    def GetRegion():
        """Retrieve the region of the current map."""
        region = Map.map_instance().server_region
        return region.ToInt(), region.GetName()

    @staticmethod
    def GetLanguage():
        """
        Retrieve the language of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        language = Map.map_instance().language
        return language.ToInt(), language.GetName()

    @staticmethod
    def RegionFromDistrict(district):
        """
        Retrieve the region from a district.
        Args:
            district (int): The district to retrieve the region from.
        Returns: tuple (int, str)
        """
        region = Map.map_instance().RegionFromDistrict(district)
        return region.ToInt(), region.GetName()

    @staticmethod
    def LanguageFromDistrict(district):
        """
        Retrieve the language from a district.
        Args:
            district (int): The district to retrieve the language from.
        Returns: tuple (int, str)
        """
        language = Map.map_instance().LanguageFromDistrict(district)
        return language.ToInt(), language.GetName()

    @staticmethod
    def GetIsMapUnlocked(mapid=None):
        """Check if the map is unlocked."""
        if mapid is None:
            map_id = Map.GetMapID()
        else:
            map_id = mapid
        return Map.map_instance().GetIsMapUnlocked(map_id)

    @staticmethod
    def GetAmountOfPlayersInInstance():
        """Retrieve the amount of players in the current instance."""
        return Map.map_instance().amount_of_players_in_instance
    
    @staticmethod
    def GetFlags():
        """Retrieve the flags of the current map."""
        return Map.map_instance().flags
    
    @staticmethod
    def GetThumbnailID():
        """Retrieve the thumbnail ID of the current map."""
        return Map.map_instance().thumbnail_id
    
    @staticmethod
    def GetMinPlayerSize():
        """Retrieve the minimum player size of the current map."""
        return Map.map_instance().min_player_size
    
    @staticmethod
    def GetMaxPlayerSize():
        """Retrieve the maximum player size of the current map."""
        return Map.map_instance().max_player_size
    
    @staticmethod
    def GetControlledOutpostID():
        """Retrieve the controlled outpost ID of the current map."""
        return Map.map_instance().controlled_outpost_id
    
    @staticmethod
    def GetFractionMission():
        """Retrieve the fraction mission of the current map."""
        return Map.map_instance().fraction_mission
    
    @staticmethod
    def GetMinLevel():
        """Retrieve the minimum level of the current map."""
        return Map.map_instance().min_level
    
    @staticmethod
    def GetMaxLevel():
        """Retrieve the maximum level of the current map."""
        return Map.map_instance().max_level
    
    @staticmethod
    def GetNeededPQ():
        """Retrieve the needed PQ of the current map."""
        return Map.map_instance().needed_pq
    
    @staticmethod
    def GetMissionMapsTo():
        """Retrieve the mission maps to of the current map."""
        return Map.map_instance().mission_maps_to
    
    @staticmethod
    def GetIconPosition():
        """Retrieve the icon position of the current map."""
        return Map.map_instance().icon_position_x, Map.map_instance().icon_position_y
    
    @staticmethod
    def GetIconStartPosition():
        """Retrieve the icon start position of the current map."""
        return Map.map_instance().icon_start_x, Map.map_instance().icon_start_y
    
    @staticmethod
    def GetIconEndPosition():
        """Retrieve the icon end position of the current map."""
        return Map.map_instance().icon_end_x, Map.map_instance().icon_end_y
    
    @staticmethod
    def GetIconStartPositionDupe():
        """Retrieve the icon start position dupe of the current map."""
        return Map.map_instance().icon_start_x_dupe, Map.map_instance().icon_start_y_dupe
    
    @staticmethod
    def GetIconEndPositionDupe():
        """Retrieve the icon end position dupe of the current map."""
        return Map.map_instance().icon_end_x_dupe, Map.map_instance().icon_end_y_dupe

    @staticmethod
    def GetFileID():
        """Retrieve the file ID of the current map."""
        return Map.map_instance().file_id
    
    @staticmethod
    def GetMissionChronology():
        """Retrieve the mission chronology of the current map."""
        return Map.map_instance().mission_chronology
    
    @staticmethod
    def GetHAChronology():
        """Retrieve the HA chronology of the current map."""
        return Map.map_instance().ha_map_chronology
    
    @staticmethod
    def GetNameID():
        """Retrieve the name ID of the current map."""
        return Map.map_instance().name_id
    
    @staticmethod
    def GetDescriptionID():
        """Retrieve the description ID of the current map."""
        return Map.map_instance().description_id
    
    @staticmethod
    def GetMapWorldMapBounds():
        map_info = Map.map_instance()

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
    
    @staticmethod
    def GetMapBoundaries():
        """Retrieve the map boundaries of the current map."""
        boundaries = Map.map_instance().map_boundaries
        if len(boundaries) < 5:
            return 0.0, 0.0, 0.0, 0.0  # Optional: fallback for safety

        min_x = boundaries[1]
        min_y = boundaries[2]
        max_x = boundaries[3]
        max_y = boundaries[4]

        return min_x, min_y, max_x, max_y

    class Pathing:
        @staticmethod
        def GetPathingMaps() -> List[PyPathing.PathingMap]:
            return PyPathing.get_pathing_maps()

        @staticmethod
        def WorldToScreen(x,y,z=0.0):
            if z == 0.0:
                z = Overlay.FindZ(x, y)

            screen_pos = PyOverlay.Overlay().WorldToScreen(x, y, z)
            return screen_pos.x, screen_pos.y
        
        class Quad:
            def __init__(self, trapezoid : PyPathing.PathingTrapezoid):
                self.trapezoid = trapezoid
                
                self.top_left:PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XTL), int(trapezoid.YT))
                self.top_right:PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XTR), int(trapezoid.YT))
                self.bottom_left:PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XBL), int(trapezoid.YB))
                self.bottom_right:PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XBR), int(trapezoid.YB))
                
                
                screen_TL = Map.MissionMap.MapProjection.GameMapToScreen(self.top_left.x, self.top_left.y)
                screen_TR = Map.MissionMap.MapProjection.GameMapToScreen(self.top_right.x, self.top_right.y)
                screen_BL = Map.MissionMap.MapProjection.GameMapToScreen(self.bottom_left.x, self.bottom_left.y)
                screen_BR = Map.MissionMap.MapProjection.GameMapToScreen(self.bottom_right.x, self.bottom_right.y)
                
                self.screen_top_left:PyOverlay.Point2D = PyOverlay.Point2D(int(screen_TL[0]), int(screen_TL[1]))
                self.screen_top_right:PyOverlay.Point2D = PyOverlay.Point2D(int(screen_TR[0]), int(screen_TR[1]))
                self.screen_bottom_left:PyOverlay.Point2D = PyOverlay.Point2D(int(screen_BL[0]), int(screen_BL[1]))
                self.screen_bottom_right:PyOverlay.Point2D = PyOverlay.Point2D(int(screen_BR[0]), int(screen_BR[1]))
                
            def GetPoints(self) -> List[PyOverlay.Point2D]:
                return [self.top_left, self.top_right, self.bottom_left, self.bottom_right]
            
            def GetScreenPoints(self) -> List[PyOverlay.Point2D]:
                return [self.screen_top_left, self.screen_top_right, self.screen_bottom_left, self.screen_bottom_right]
            
            def GetShiftedPoints(self, origin_x: float, origin_y: float) -> List[PyOverlay.Point2D]:
                return [
                    PyOverlay.Point2D(int(self.top_left.x - origin_x), int(self.top_left.y - origin_y)),
                    PyOverlay.Point2D(int(self.top_right.x - origin_x), int(self.top_right.y - origin_y)),
                    PyOverlay.Point2D(int(self.bottom_left.x - origin_x), int(self.bottom_left.y - origin_y)),
                    PyOverlay.Point2D(int(self.bottom_right.x - origin_x), int(self.bottom_right.y - origin_y)),
                ]

            def GetShiftedScreenPoints(self, origin_x: float, origin_y: float) -> List[PyOverlay.Point2D]:
                shifted = self.GetShiftedPoints(origin_x, origin_y)
                shifted_tl = Map.MissionMap.MapProjection.GameMapToScreen(shifted[0].x, shifted[0].y)
                shifted_tr = Map.MissionMap.MapProjection.GameMapToScreen(shifted[1].x, shifted[1].y)
                shifted_bl = Map.MissionMap.MapProjection.GameMapToScreen(shifted[2].x, shifted[2].y)
                shifted_br = Map.MissionMap.MapProjection.GameMapToScreen(shifted[3].x, shifted[3].y)
                return [
                    PyOverlay.Point2D(int(shifted_tl[0]), int(shifted_tl[1])),
                    PyOverlay.Point2D(int(shifted_tr[0]), int(shifted_tr[1])),
                    PyOverlay.Point2D(int(shifted_bl[0]), int(shifted_bl[1])),
                    PyOverlay.Point2D(int(shifted_br[0]), int(shifted_br[1])),
                ]
                
        @staticmethod
        def GetComputedGeometry() -> List[List[PyOverlay.Point2D]]:
            pathintg_maps = Map.Pathing.GetPathingMaps()
            geometry = []
            for layer in pathintg_maps:
                for trapezoid in layer.trapezoids:
                    geometry.append(Map.Pathing.Quad(trapezoid).GetPoints())
            return geometry
                    
                
        @staticmethod
        def GetScreenComputedGeometry() -> List[List[PyOverlay.Point2D]]:
            pathintg_maps = Map.Pathing.GetPathingMaps()
            geometry = []
            for layer in pathintg_maps:
                for trapezoid in layer.trapezoids:
                    geometry.append(Map.Pathing.Quad(trapezoid).GetScreenPoints())
            return geometry
            
        @staticmethod
        def GetShiftedComputedGeometry(origin_x: float, origin_y: float) -> List[List[PyOverlay.Point2D]]:
            pathing_maps = Map.Pathing.GetPathingMaps()
            geometry = []
            for layer in pathing_maps:
                for trapezoid in layer.trapezoids:
                    quad = Map.Pathing.Quad(trapezoid)
                    geometry.append(quad.GetShiftedPoints(origin_x, origin_y))
            return geometry

        @staticmethod
        def GetshiftedScreenComputedGeometry(origin_x: float, origin_y: float) -> List[List[PyOverlay.Point2D]]:
            pathing_maps = Map.Pathing.GetPathingMaps()
            geometry = []
            for layer in pathing_maps:
                for trapezoid in layer.trapezoids:
                    quad = Map.Pathing.Quad(trapezoid)
                    geometry.append(quad.GetShiftedScreenPoints(origin_x, origin_y))
            return geometry
    
    class MissionMap:
        @staticmethod
        def _mission_map_instance():
            """Return the PyMapMissionMap instance. """
            return PyMissionMap.PyMissionMap()
        
        @staticmethod
        def GetContext():
            """Get the context of the mission map."""
            return Map.MissionMap._mission_map_instance().GetContext()
        
        @staticmethod
        def IsWindowOpen():
            """Check if the mission map window is open."""
            return Map.MissionMap._mission_map_instance().window_open
        
        @staticmethod
        def GetFrameID():
            """Get the frame ID of the mission map."""
            return Map.MissionMap._mission_map_instance().frame_id
        
        @staticmethod
        def GetWindowCoords():
            """Get the window coordinates of the mission map."""
            return Map.MissionMap._mission_map_instance().left, Map.MissionMap._mission_map_instance().top, Map.MissionMap._mission_map_instance().right, Map.MissionMap._mission_map_instance().bottom
        
        @staticmethod
        def GetScale():
            """Get the scale of the mission map."""
            return Map.MissionMap._mission_map_instance().scale_x, Map.MissionMap._mission_map_instance().scale_y
        
        @staticmethod
        def GetZoom():
            """Get the zoom level of the mission map."""
            return Map.MissionMap._mission_map_instance().zoom
        
        @staticmethod
        def GetAdjustedZoom(_zoom, zoom_offset=0.0):
            """Adjust the zoom level of the mission map."""
            zoom = _zoom + zoom_offset
            if zoom == 1.0:
                return zoom + 0.0
            
            if 1.0 < zoom <= 1.5:
                return zoom + 0.0449
            
            if zoom > 1.5:
                step = 0.5
                # Snap to step count safely
                times = int((zoom - 1.5 + 1e-6) // step)  # avoids float precision issues
                return zoom + (0.0449 + (0.02449 * times))
            
            return zoom + 0.0
        
        @staticmethod
        def GetCenter():
            """Get the center coordinates of the mission map."""
            return Map.MissionMap._mission_map_instance().center_x, Map.MissionMap._mission_map_instance().center_y
        
        @staticmethod
        def GetLastClickCoords():
            """Get the last click coordinates on the mission map."""
            return Map.MissionMap._mission_map_instance().last_click_x, Map.MissionMap._mission_map_instance().last_click_y
        
        @staticmethod
        def GetPanOffset():
            """Get the pan offset of the mission map."""
            return Map.MissionMap._mission_map_instance().pan_offset_x, Map.MissionMap._mission_map_instance().pan_offset_y
        
        @staticmethod
        def GetMapScreenCenter():
            """Get the map screen center coordinates."""
            return Map.MissionMap._mission_map_instance().mission_map_screen_center_x, Map.MissionMap._mission_map_instance().mission_map_screen_center_y
        
        class MapProjection:
            @staticmethod
            def GamePosToWorldMap(x: float, y: float):
                gwinches = 96.0

                # Step 1: Get map bounds in UI space
                left, top, right, bottom = Map.GetMapWorldMapBounds()

                # Step 2: Get game-space boundaries from map context
                boundaries = Map.map_instance().map_boundaries
                if len(boundaries) < 5:
                    return 0.0, 0.0  # fail-safe

                min_x = boundaries[1]
                max_y = boundaries[4]

                # Step 3: Compute origin on the world map based on boundary distances
                origin_x = left + abs(min_x) / gwinches
                origin_y = top + abs(max_y) / gwinches

                # Step 4: Convert game-space (gwinches) to world map space (screen)
                screen_x = (x / gwinches) + origin_x
                screen_y = (-y / gwinches) + origin_y  # Inverted Y

                return screen_x, screen_y
            
            @staticmethod
            def WorldMapToGamePos(x: float, y: float):
                from .Map import Map
                gwinches = 96.0

                # Step 1: Get the world map bounds in screen-space
                left, top, right, bottom = Map.GetMapWorldMapBounds()

                # Step 2: Check if input point is within the map bounds
                #if not (left <= x <= right and top <= y <= bottom):
                #    return 0.0, 0.0  # Equivalent to ImRect.Contains check

                # Step 3: Get game-space boundaries (min_x, ..., max_y)
                bounds = Map.map_instance().map_boundaries
                if len(bounds) < 5:
                    return 0.0, 0.0

                min_x = bounds[1]
                max_y = bounds[4]

                # Step 4: Compute the world map anchor point (same logic as forward)
                origin_x = left + abs(min_x) / gwinches
                origin_y = top + abs(max_y) / gwinches

                # Step 5: Convert world map coords to game-space
                game_x = (x - origin_x) * gwinches
                game_y = (y - origin_y) * gwinches * -1.0  # Inverted Y

                return game_x, game_y
    
            @staticmethod
            def WorldMapToScreen(x: float, y: float, zoom_offset=0.0):
                # World map coordinates (x, y) to screen space
                pan_offset_x, pan_offset_y = Map.MissionMap.GetPanOffset()
                offset_x = x - pan_offset_x
                offset_y = y - pan_offset_y

                scale_x, scale_y = Map.MissionMap.GetScale()
                scaled_x = offset_x * scale_x
                scaled_y = offset_y * scale_y

                zoom = Map.MissionMap.GetZoom() + zoom_offset
                mission_map_screen_center_x, mission_map_screen_center_y = Map.MissionMap.GetMapScreenCenter()
                screen_x = scaled_x * zoom + mission_map_screen_center_x
                screen_y = scaled_y * zoom + mission_map_screen_center_y

                return screen_x, screen_y

            @staticmethod
            def ScreenToWorldMap(screen_x: float, screen_y: float, zoom_offset=0.0):
                from .Map import Map
                mmap = Map.MissionMap
                if not mmap.IsWindowOpen():
                    return 0.0, 0.0

                zoom = Map.MissionMap.GetZoom() + zoom_offset
                scale_x, scale_y = Map.MissionMap.GetScale()
                center_x, center_y = Map.MissionMap.GetMapScreenCenter()
                pan_offset_x, pan_offset_y = Map.MissionMap.GetPanOffset()

                # Invert transform from screen space back to world space
                offset_x = (screen_x - center_x) / (zoom * scale_x)
                offset_y = (screen_y - center_y) / (zoom * scale_y)

                world_x = pan_offset_x + offset_x
                world_y = pan_offset_y + offset_y

                return world_x, world_y
    
            @staticmethod
            def GameMapToScreen(x, y, zoom_offset=0.0):
                world_x, world_y = Map.MissionMap.MapProjection.GamePosToWorldMap(x, y)
                return Map.MissionMap.MapProjection.WorldMapToScreen(world_x, world_y, zoom_offset)
            
            @staticmethod
            def ScreenToGameMap(x, y, zoom_offset=0.0):
                world_x, world_y = Map.MissionMap.MapProjection.ScreenToWorldMap(x, y, zoom_offset)
                return Map.MissionMap.MapProjection.WorldMapToGamePos(world_x, world_y)
            
            @staticmethod
            def NormalizedScreenToScreen(x, y):
                # Convert from [-1, 1] to [0, 1] with Y-inversion
                norm_x, norm_y = Map.MissionMap.GetLastClickCoords()
                adjusted_x = (norm_x + 1.0) / 2.0
                adjusted_y = (1.0 - norm_y) / 2.0

                # Compute width and height of the map frame
                coords = Map.MissionMap.GetWindowCoords()
                left, top, right, bottom = int(coords[0]-5), int(coords[1]-1), int(coords[2]+5), int(coords[3]+2)
                width = right - left
                height = bottom - top

                screen_x = left + adjusted_x * width
                screen_y = top + adjusted_y * height

                return screen_x, screen_y
            
            @staticmethod
            def ScreenToNormalizedScreen(screen_x: float, screen_y: float):
                # Compute width and height of the map frame
                coords = Map.MissionMap.GetWindowCoords()
                left, top, right, bottom = int(coords[0]-5), int(coords[1]-1), int(coords[2]+5), int(coords[3]+2)
                width = right - left
                height = bottom - top

                # Relative position in [0, 1] range
                rel_x = (screen_x - left) / width
                rel_y = (screen_y - top) / height

                # Convert to normalized [-1, 1], Y is inverted
                norm_x = rel_x * 2.0 - 1.0
                norm_y = (1.0 - rel_y) * 2.0 - 1.0

                return norm_x, norm_y
            
            @staticmethod
            def NormalizedScreenToWorldMap(x, y, zoom_offset=0.0):
                screen_x, screen_y = Map.MissionMap.MapProjection.NormalizedScreenToScreen(x, y)
                return Map.MissionMap.MapProjection.ScreenToWorldMap(screen_x, screen_y, zoom_offset)
            
            @staticmethod
            def NormalizedScreenToGameMap(x, y, zoom_offset=0.0):
                #game_map_pos = PyOverlay.Overlay().NormalizedScreenToGameMap(x, y)
                #return game_map_pos.x, game_map_pos.y
                world_x, world_y = Map.MissionMap.MapProjection.NormalizedScreenToWorldMap(x, y, zoom_offset)
                return Map.MissionMap.MapProjection.WorldMapToGamePos(world_x, world_y)
             
            @staticmethod
            def GamePosToNormalizedScreen(x, y):
                screen_x, screen_y = Map.MissionMap.MapProjection.GameMapToScreen(x, y)
                return Map.MissionMap.MapProjection.ScreenToNormalizedScreen(screen_x, screen_y)
            
            @staticmethod
            def GamePosToScreen(x, y, zoom_offset=0.0):
                world_x, world_y = Map.MissionMap.MapProjection.GamePosToWorldMap(x, y)
                return Map.MissionMap.MapProjection.WorldMapToScreen(world_x, world_y, zoom_offset)
            
            @staticmethod
            def ScreenToGamePos(x, y, zoom_offset=0.0):
                world_x, world_y = Map.MissionMap.MapProjection.ScreenToWorldMap(x, y, zoom_offset)
                return Map.MissionMap.MapProjection.WorldMapToGamePos(world_x, world_y)
    
            
            @staticmethod
            def WorldPosToMissionMapScreen(x: float, y: float, zoom_offset=0.0):
                # 1. Convert game position (gwinches) to world map coordinates
                world_x, world_y = Map.MissionMap.MapProjection.GamePosToWorldMap(x, y)

                # 2. Project onto the mission map screen space
                screen_x, screen_y = Map.MissionMap.MapProjection.WorldMapToScreen(world_x, world_y, zoom_offset)

                return screen_x, screen_y
            
            @staticmethod
            def ScreenToWorldPos(screen_x: float, screen_y: float, zoom_offset=0.0):
                # Step 1: Convert from screen-space to world map coordinates
                world_x, world_y = Map.MissionMap.MapProjection.ScreenToWorldMap(screen_x, screen_y, zoom_offset)

                # Step 2: Convert from world map coordinates to in-game game coordinates (gwinches)
                game_x, game_y = Map.MissionMap.MapProjection.WorldMapToGamePos(world_x, world_y)

                return game_x, game_y

    class MiniMap:
        @staticmethod
        def GetFrameID():
            """Get the frame ID of the mini map."""
            hash = UIManager.GetHashByLabel("compass") #3268554015
            return UIManager.GetFrameIDByHash(hash)
            
        @staticmethod
        def FrameExists():
            """Check if the mini map frame is visible."""
            return UIManager.FrameExists(Map.MiniMap.GetFrameID())
        
        @staticmethod
        def IsWindowOpen():
            """Check if the mini map window is open."""
            return Map.MiniMap.FrameExists()
        
        @staticmethod
        def GetWindowCoords():
            """Get the coordinates of the mini map."""
            return UIManager.GetFrameCoords(Map.MiniMap.GetFrameID())
        
        @staticmethod
        def IsLocked():
            """Check if the mini map is locked."""
            return UIManager.GetBoolPreference(FlagPreference.LockCompassRotation)
        
        @staticmethod
        def GetPanOffset():
            """Get the pan offset of the mini map."""
            return [0.0,0.0]
        
        @staticmethod
        def GetScale(coords = None):
            """Get the scale of the mini map."""
            if not coords:
                left,top,right,bottom = Map.MiniMap.GetWindowCoords()
            else:
                left,top,right,bottom = coords

            height = bottom - top
            diff = height - (height/1.05)
            left   += diff
            right  -= diff

            scale = (right-left)/2.0

            return scale
        
        @staticmethod
        def GetRotation():
            """Get the rotation of the mini map."""
            from .Camera import Camera

            if Map.MiniMap.IsLocked():
                return 0
            else:
                return Camera.GetCurrentYaw() - math.pi/2
        
        @staticmethod
        def GetZoom():
            """Get the zoom level of the mini map."""
            return 1.0
        
        @staticmethod
        def GetLastClickCoords():
            """Get the last click coordinates on the mini map."""
            return [0.0,0.0]
        
        @staticmethod
        def GetMapScreenCenter(coords = None):
            """Get the map screen center coordinates."""
            if not coords:
                left,top,right,bottom = Map.MiniMap.GetWindowCoords()
            else:
                left,top,right,bottom = coords
            height = bottom - top
            diff = height - (height/1.05)

            top    += diff
            left   += diff
            right  -= diff

            center_x = (left + right)/2.0
            center_y = top + (right - left)/2.0

            return center_x, center_y
        
        class MapProjection:
            @staticmethod
            def GamePosToScreen(game_x, game_y,
                                player_x = None, player_y = None,
                                center_x = None, center_y = None,
                                scale = None, rotation = None):
                """ Convert a game position to a position on the screen relative to the compass."""
                from .Player import Player
                
                if player_x == None or player_y == None:
                    player_x, player_y = Player.GetXY()
                if center_x == None or center_y == None:
                    center_x, center_y = Map.MiniMap.GetMapScreenCenter()
                if scale == None:
                    scale = Map.MiniMap.GetScale()
                if rotation == None:
                    rotation = Map.MiniMap.GetRotation()

                x = center_x - (player_x - game_x)*scale/5000
                y = center_y + (player_y - game_y)*scale/5000

                screen_x = center_x + math.cos(rotation)*(x - center_x) - math.sin(rotation)*(y - center_y)
                screen_y = center_y + math.sin(rotation)*(x - center_x) + math.cos(rotation)*(y - center_y)

                return screen_x, screen_y
            
            @staticmethod
            def ScreenToGamePos(screen_x, screen_y,
                                player_x = None, player_y = None,
                                center_x = None, center_y = None,
                                scale = None, rotation = None):
                """ Convert a screen position relative to the compass to a position in the game."""
                from .Player import Player

                if player_x == None or player_y == None:
                    player_x, player_y = Player.GetXY()
                if center_x == None or center_y == None:
                    center_x, center_y = Map.MiniMap.GetMapScreenCenter()
                if scale == None:
                    scale = Map.MiniMap.GetScale()
                if rotation == None:
                    rotation = Map.MiniMap.GetRotation()

                x = center_x + math.cos(-rotation)*(screen_x - center_x) - math.sin(-rotation)*(screen_y - center_y)
                y = center_y + math.sin(-rotation)*(screen_x - center_x) + math.cos(-rotation)*(screen_y - center_y)

                game_x = player_x + (x - center_x)*5000/scale
                game_y = player_y - (y - center_y)*5000/scale

                return game_x, game_y
            
            @staticmethod
            def ComputedPathingGeometryToScreen(map_bounds = None,
                                                   player_x = None, player_y = None,
                                                   center_x = None, center_y = None,
                                                   scale = None, rotation = None):
                """ Convert a screen position of pathing geometry to a screen position relative to the compass."""
                from .Player import Player
                
                # Step 1: Get map bounds
                if not map_bounds:
                    map_bounds = Map.GetMapBoundaries()
                
                map_min_x = map_bounds[0]
                map_min_y = map_bounds[1]
                map_max_x = map_bounds[2]
                map_max_y = map_bounds[3]
                map_mid_x = (map_min_x + map_max_x)/2
                map_mid_y = (map_min_y + map_max_y)/2

                # Step 2: Get compass position/scale/rotation
                if center_x == None or center_y == None:
                    center_x, center_y = Map.MiniMap.GetMapScreenCenter()
                if scale == None:
                    scale = Map.MiniMap.GetScale()
                if rotation == None:
                    rotation = Map.MiniMap.GetRotation()

                # Step 3: Get Player position
                if player_x == None or player_y == None:
                    player_x, player_y = Player.GetXY()

                # Step 4: Get geometry zoom
                zoom = scale/5000

                # Step 5: Get Player position geometry offset
                x_pos_offset = map_mid_x - player_x
                y_pos_offset = map_mid_y - player_y

                # Step 6: Get rotation offset
                player_x_rotated = player_x*math.cos(-rotation) - player_y*math.sin(-rotation)
                player_y_rotated = player_x*math.sin(-rotation) + player_y*math.cos(-rotation)

                x_rot_offset = player_x - player_x_rotated
                y_rot_offset = player_y - player_y_rotated

                # Step 7: Get final offset
                x_offset = zoom*(x_pos_offset + x_rot_offset - (map_max_x + map_min_x)/2)
                y_offset = zoom*(y_pos_offset + y_rot_offset - (map_max_y + map_min_y)/2)

                return x_offset, y_offset, zoom

            @staticmethod
            def GamePosToWorldMap(x: float, y: float):
                gwinches = 96.0

                # Step 1: Get map bounds in UI space
                left, top, right, bottom = Map.GetMapWorldMapBounds()

                # Step 2: Get game-space boundaries from map context
                boundaries = Map.map_instance().map_boundaries
                if len(boundaries) < 5:
                    return 0.0, 0.0  # fail-safe

                min_x = boundaries[1]
                max_y = boundaries[4]

                # Step 3: Compute origin on the world map based on boundary distances
                origin_x = left + abs(min_x) / gwinches
                origin_y = top + abs(max_y) / gwinches

                # Step 4: Convert game-space (gwinches) to world map space (screen)
                screen_x = (x / gwinches) + origin_x
                screen_y = (-y / gwinches) + origin_y  # Inverted Y

                return screen_x, screen_y
            
            @staticmethod
            def WorldMapToGamePos(x: float, y: float):
                gwinches = 96.0
                left, top, right, bottom = Map.GetMapWorldMapBounds()
                bounds = Map.map_instance().map_boundaries
                if len(bounds) < 5:
                    return 0.0, 0.0

                min_x = bounds[1]
                max_y = bounds[4]

                # Step 4: Compute the world map anchor point (same logic as forward)
                origin_x = left + abs(min_x) / gwinches
                origin_y = top + abs(max_y) / gwinches

                # Step 5: Convert world map coords to game-space
                game_x = (x - origin_x) * gwinches
                game_y = (y - origin_y) * gwinches * -1.0  # Inverted Y

                return game_x, game_y
    
            @staticmethod
            def WorldMapToScreen(x: float, y: float):
                # World map coordinates (x, y) to screen space
                pan_offset_x, pan_offset_y = Map.MiniMap.GetPanOffset()
                offset_x = x - pan_offset_x
                offset_y = y - pan_offset_y

                scale = Map.MiniMap.GetScale()
                scaled_x = offset_x * scale
                scaled_y = offset_y * scale

                zoom = Map.MiniMap.GetZoom()
                mission_map_screen_center_x, mission_map_screen_center_y = Map.MiniMap.GetMapScreenCenter()
                screen_x = scaled_x * zoom + mission_map_screen_center_x
                screen_y = scaled_y * zoom + mission_map_screen_center_y

                return screen_x, screen_y

            @staticmethod
            def ScreenToWorldMap(screen_x: float, screen_y: float):

                zoom = Map.MiniMap.GetZoom()
                scale = Map.MiniMap.GetScale()
                center_x, center_y = Map.MiniMap.GetMapScreenCenter()
                pan_offset_x, pan_offset_y = Map.MiniMap.GetPanOffset()

                # Invert transform from screen space back to world space
                offset_x = (screen_x - center_x) / (zoom * scale)
                offset_y = (screen_y - center_y) / (zoom * scale)

                world_x = pan_offset_x + offset_x
                world_y = pan_offset_y + offset_y

                return world_x, world_y
    
            @staticmethod
            def GameMapToScreen(x, y):
                world_x, world_y = Map.MiniMap.MapProjection.GamePosToWorldMap(x, y)
                return Map.MiniMap.MapProjection.WorldMapToScreen(world_x, world_y)
            
            @staticmethod
            def ScreenToGameMap(x, y):
                world_x, world_y = Map.MiniMap.MapProjection.ScreenToWorldMap(x, y)
                return Map.MiniMap.MapProjection.WorldMapToGamePos(world_x, world_y)
            
            @staticmethod
            def NormalizedScreenToScreen(x, y):
                # Convert from [-1, 1] to [0, 1] with Y-inversion
                norm_x, norm_y = Map.MiniMap.GetLastClickCoords()
                adjusted_x = (norm_x + 1.0) / 2.0
                adjusted_y = (1.0 - norm_y) / 2.0

                # Compute width and height of the map frame
                coords = Map.MiniMap.GetWindowCoords()
                left, top, right, bottom = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
                width = right - left
                height = bottom - top

                screen_x = left + adjusted_x * width
                screen_y = top + adjusted_y * height

                return screen_x, screen_y
            
            @staticmethod
            def ScreenToNormalizedScreen(screen_x: float, screen_y: float):
                # Compute width and height of the map frame
                coords = Map.MiniMap.GetWindowCoords()
                left, top, right, bottom = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
                width = right - left
                height = bottom - top

                # Relative position in [0, 1] range
                rel_x = (screen_x - left) / width
                rel_y = (screen_y - top) / height

                # Convert to normalized [-1, 1], Y is inverted
                norm_x = rel_x * 2.0 - 1.0
                norm_y = (1.0 - rel_y) * 2.0 - 1.0

                return norm_x, norm_y
            
            @staticmethod
            def NormalizedScreenToWorldMap(x, y):
                screen_x, screen_y = Map.MiniMap.MapProjection.NormalizedScreenToScreen(x, y)
                return Map.MiniMap.MapProjection.ScreenToWorldMap(screen_x, screen_y)
            
            @staticmethod
            def NormalizedScreenToGameMap(x, y):
                world_x, world_y = Map.MiniMap.MapProjection.NormalizedScreenToWorldMap(x, y)
                return Map.MiniMap.MapProjection.WorldMapToGamePos(world_x, world_y)
             
            @staticmethod
            def GamePosToNormalizedScreen(x, y):
                screen_x, screen_y = Map.MiniMap.MapProjection.GameMapToScreen(x, y)
                return Map.MiniMap.MapProjection.ScreenToNormalizedScreen(screen_x, screen_y)

            @staticmethod
            def WorldPosToMiniMapScreen(x: float, y: float):
                # 1. Convert game position (gwinches) to world map coordinates
                world_x, world_y = Map.MiniMap.MapProjection.GamePosToWorldMap(x, y)

                # 2. Project onto the mission map screen space
                screen_x, screen_y = Map.MiniMap.MapProjection.WorldMapToScreen(world_x, world_y)

                return screen_x, screen_y
            
            @staticmethod
            def ScreenToWorldPos(screen_x: float, screen_y: float):
                # Step 1: Convert from screen-space to world map coordinates
                world_x, world_y = Map.MiniMap.MapProjection.ScreenToWorldMap(screen_x, screen_y)

                # Step 2: Convert from world map coordinates to in-game game coordinates (gwinches)
                game_x, game_y = Map.MiniMap.MapProjection.WorldMapToGamePos(world_x, world_y)

                return game_x, game_y

import PyOverlay
from typing import Tuple

class Overlay:
    def __init__(self):
        self.overlay_instance = PyOverlay.Overlay()

    def IsMouseClicked(self):
        return self.overlay_instance.IsMouseClicked(0)

    def GetMouseCoords(self) -> Tuple[float, float]:
        mouse_point = self.overlay_instance.GetMouseCoords()
        return mouse_point.x, mouse_point.y

    def GetMouseWorldPos(self):
        world_pos = self.overlay_instance.GetMouseWorldPos()
        return world_pos.x, world_pos.y, world_pos.z

    @staticmethod
    def WorldToScreen(x,y,z=0.0):
        if z == 0.0:
            z = Overlay.FindZ(x, y)

        screen_pos = PyOverlay.Overlay().WorldToScreen(x, y, z)
        return screen_pos.x, screen_pos.y

    @staticmethod
    def GamePosToWorldMap(x: float, y: float):
        from .Map import Map
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
        #game_pos = PyOverlay.Overlay().WorlMapToGamePos(x, y)
        #return game_pos.x, game_pos.y
        #data is good from the dll but we can do it manually

        from .Map import Map
        gwinches = 96.0

        # Step 1: Get the world map bounds in screen-space
        left, top, right, bottom = Map.GetMapWorldMapBounds()

        # Step 2: Check if input point is within the map bounds
        if not (left <= x <= right and top <= y <= bottom):
            return 0.0, 0.0  # Equivalent to ImRect.Contains check

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
    def WorldMapToScreen(x: float, y: float):
        #screen_pos = PyOverlay.Overlay().WorldMapToScreen(x, y)
        #return screen_pos.x, screen_pos.y
        #data is good from the dll but we can do it manually
        from .Map import Map
        mmap = Map.MissionMap
        if not mmap.IsWindowOpen():
            return 0.0, 0.0

        # World map coordinates (x, y) to screen space
        pan_offset_x, pan_offset_y = Map.MissionMap.GetPanOffset()
        offset_x = x - pan_offset_x
        offset_y = y - pan_offset_y

        scale_x, scale_y = Map.MissionMap.GetScale()
        scaled_x = offset_x * scale_x
        scaled_y = offset_y * scale_y

        zoom = Map.MissionMap.GetZoom()
        mission_map_screen_center_x, mission_map_screen_center_y = Map.MissionMap.GetMapScreenCenter()
        screen_x = scaled_x * zoom + mission_map_screen_center_x
        screen_y = scaled_y * zoom + mission_map_screen_center_y

        return screen_x, screen_y

    
    @staticmethod
    def ScreenToWorldMap(screen_x: float, screen_y: float):
        #world_map_pos = PyOverlay.Overlay().ScreenToWorldMap(x, y)
        #return world_map_pos.x, world_map_pos.y
        #data is good from the dll but we can do it manually
        from .Map import Map
        mmap = Map.MissionMap
        if not mmap.IsWindowOpen():
            return 0.0, 0.0

        zoom = Map.MissionMap.GetZoom()
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
    def GameMapToScreen(x, y):
        #screen_pos = PyOverlay.Overlay().GameMapToScreen(x, y)
        #return screen_pos.x, screen_pos.y
        world_x, world_y = Overlay.GamePosToWorldMap(x, y)
        return Overlay.WorldMapToScreen(world_x, world_y)
    
    @staticmethod
    def ScreenToGameMap(x, y):
        #game_pos = PyOverlay.Overlay().ScreenToGameMapPos(x, y)
        #return game_pos.x, game_pos.y
        world_x, world_y = Overlay.ScreenToWorldMap(x, y)
        return Overlay.WorldMapToGamePos(world_x, world_y)
    
    @staticmethod
    def NormalizedScreenToScreen(x, y):
        #screen_pos = PyOverlay.Overlay().NormalizedScreenToScreen(x, y)
        #return screen_pos.x, screen_pos.y
        #data is good from the dll but we can do it manually
        from .Map import Map
        if not Map.MissionMap.IsWindowOpen():
            return 0.0, 0.0

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
        #normalized_screen_pos = PyOverlay.Overlay().ScreenToNormalizedScreen(x, y)
        #return normalized_screen_pos.x, normalized_screen_pos.y
        #data is good from the dll but we can do it manually
        from .Map import Map
        if not Map.MissionMap.IsWindowOpen():
            return 0.0, 0.0

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
    def NormalizedScreenToWorldMap(x, y):
        #world_map_pos = PyOverlay.Overlay().NormalizedScreenToWorldMap(x, y)
        #return world_map_pos.x, world_map_pos.y
        screen_x, screen_y = Overlay.NormalizedScreenToScreen(x, y)
        return Overlay.ScreenToWorldMap(screen_x, screen_y)
    
    @staticmethod
    def NormalizedScreenToGameMap(x, y):
        #game_map_pos = PyOverlay.Overlay().NormalizedScreenToGameMap(x, y)
        #return game_map_pos.x, game_map_pos.y
        world_x, world_y = Overlay.NormalizedScreenToWorldMap(x, y)
        return Overlay.WorldMapToGamePos(world_x, world_y)
    
    @staticmethod
    def GamePosToNormalizedScreen(x, y):
        #normalized_screen_pos = PyOverlay.Overlay().GamePosToNormalizedScreen(x, y)
        #return normalized_screen_pos.x, normalized_screen_pos.y
        screen_x, screen_y = Overlay.GameMapToScreen(x, y)
        return Overlay.ScreenToNormalizedScreen(screen_x, screen_y)
    
    @staticmethod
    def GamePosToScreen(x, y):
        world_x, world_y = Overlay.GamePosToWorldMap(x, y)
        return Overlay.WorldMapToScreen(world_x, world_y)
    
    @staticmethod
    def ScreenToGamePos(x, y):
        world_x, world_y = Overlay.ScreenToWorldMap(x, y)
        return Overlay.WorldMapToGamePos(world_x, world_y)
    

    @staticmethod
    def WorldPosToMissionMapScreen(x: float, y: float):
        # 1. Convert game position (gwinches) to world map coordinates
        world_x, world_y = Overlay.GamePosToWorldMap(x, y)

        # 2. Project onto the mission map screen space
        screen_x, screen_y = Overlay.WorldMapToScreen(world_x, world_y)

        return screen_x, screen_y
    
    @staticmethod
    def ScreenToWorldPos(screen_x: float, screen_y: float):
        # Step 1: Convert from screen-space to world map coordinates
        world_x, world_y = Overlay.ScreenToWorldMap(screen_x, screen_y)

        # Step 2: Convert from world map coordinates to in-game game coordinates (gwinches)
        game_x, game_y = Overlay.WorldMapToGamePos(world_x, world_y)

        return game_x, game_y



    @staticmethod
    def FindZ (x, y, z=0):
        """Find The altitude of the ground at the given x,y coordinates based on Pathing Maps"""
        return PyOverlay.Overlay().FindZ(x, y, z)

    def RefreshDrawList(self):
        self.overlay_instance.RefreshDrawList()

    def BeginDraw(self, name: str = "", x: int = 0, y: int = 0, width: int = 0, height: int = 0) -> None:
        if not name:
            self.overlay_instance.BeginDraw()
        elif width > 0 and height > 0:
            self.overlay_instance.BeginDraw(name, x, y, width, height)
        else:
            self.overlay_instance.BeginDraw(name)

    def EndDraw(self):
        self.overlay_instance.EndDraw()

    def DrawLine(self, x1, y1, x2, y2, color=0xFFFFFFFF, thickness=1.0):
        pos1 = PyOverlay.Point2D(int(x1), int(y1))
        pos2 = PyOverlay.Point2D(int(x2), int(y2))
        self.overlay_instance.DrawLine(pos1, pos2, color, thickness)  # Pass color and thickness

    def DrawLine3D(self, x1, y1, z1, x2, y2, z2, color=0xFFFFFFFF, thickness=1.0):
        pos1 = PyOverlay.Point3D(x1, y1, z1)
        pos2 = PyOverlay.Point3D(x2, y2, z2)
        self.overlay_instance.DrawLine3D(pos1, pos2, color, thickness)
        
    def DrawTriangle(self, x1, y1, x2, y2, x3, y3, color=0xFFFFFFFF, thickness=1.0):
        p1 = PyOverlay.Point2D(int(x1), int(y1))
        p2 = PyOverlay.Point2D(int(x2), int(y2))
        p3 = PyOverlay.Point2D(int(x3), int(y3))
        self.overlay_instance.DrawTriangle(p1, p2, p3, color, thickness)
        
    def DrawTriangle3D(self, x1, y1, z1, x2, y2, z2, x3, y3, z3, color=0xFFFFFFFF, thickness=1.0):
        p1 = PyOverlay.Point3D(x1, y1, z1)
        p2 = PyOverlay.Point3D(x2, y2, z2)
        p3 = PyOverlay.Point3D(x3, y3, z3)
        self.overlay_instance.DrawTriangle3D(p1, p2, p3, color, thickness)
        
    def DrawTriangleFilled(self, x1, y1, x2, y2, x3, y3, color=0xFFFFFFFF):
        p1 = PyOverlay.Point2D(int(x1), int(y1))
        p2 = PyOverlay.Point2D(int(x2), int(y2))
        p3 = PyOverlay.Point2D(int(x3), int(y3))
        self.overlay_instance.DrawTriangleFilled(p1, p2, p3, color)
        
    def DrawTriangleFilled3D(self, x1, y1, z1, x2, y2, z2, x3, y3, z3, color=0xFFFFFFFF):
        p1 = PyOverlay.Point3D(x1, y1, z1)
        p2 = PyOverlay.Point3D(x2, y2, z2)
        p3 = PyOverlay.Point3D(x3, y3, z3)
        self.overlay_instance.DrawTriangleFilled3D(p1, p2, p3, color)
     
    def DrawQuad(self, x1, y1, x2, y2, x3, y3, x4, y4, color=0xFFFFFFFF, thickness=1.0):
        p1 = PyOverlay.Point2D(x1, y1)
        p2 = PyOverlay.Point2D(x2, y2)
        p3 = PyOverlay.Point2D(x3, y3)
        p4 = PyOverlay.Point2D(x4, y4)
        self.overlay_instance.DrawQuad(p1, p2, p3, p4, color, thickness)   
    
    def DrawQuad3D(self, x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4, color=0xFFFFFFFF, thickness=1.0):
        p1 = PyOverlay.Point3D(x1, y1, z1)
        p2 = PyOverlay.Point3D(x2, y2, z2)
        p3 = PyOverlay.Point3D(x3, y3, z3)
        p4 = PyOverlay.Point3D(x4, y4, z4)
        self.overlay_instance.DrawQuad3D(p1, p2, p3, p4, color, thickness)
        
    def DrawQuadFilled(self, x1, y1, x2, y2, x3, y3, x4, y4, color=0xFFFFFFFF):
        p1 = PyOverlay.Point2D(x1, y1)
        p2 = PyOverlay.Point2D(x2, y2)
        p3 = PyOverlay.Point2D(x3, y3)
        p4 = PyOverlay.Point2D(x4, y4)
        self.overlay_instance.DrawQuadFilled(p1, p2, p3, p4, color)
        
    def DrawQuadFilled3D(self, x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4, color=0xFFFFFFFF):
        p1 = PyOverlay.Point3D(x1, y1, z1)
        p2 = PyOverlay.Point3D(x2, y2, z2)
        p3 = PyOverlay.Point3D(x3, y3, z3)
        p4 = PyOverlay.Point3D(x4, y4, z4)
        self.overlay_instance.DrawQuadFilled3D(p1, p2, p3, p4, color)

    def DrawPoly(self, center_x, center_y, radius, color=0xFFFFFFFF, numsegments =32, thickness=1.0):
        center = PyOverlay.Point2D(int(center_x), int(center_y))
        self.overlay_instance.DrawPoly(center, radius, color, numsegments, thickness)

    def DrawPoly3D(self, center_x, center_y, center_z, radius, color=0xFFFFFFFF,numsegments =32, thickness=1.0, autoz = True ):
        center = PyOverlay.Point3D(center_x, center_y, center_z)
        self.overlay_instance.DrawPoly3D(center, radius, color, numsegments, thickness)
        
    def DrawPolyFilled(self, center_x, center_y, radius, color=0xFFFFFFFF, numsegments =32):
        center = PyOverlay.Point2D(int(center_x), int(center_y))
        self.overlay_instance.DrawPolyFilled(center, radius, color, numsegments)
        
    def DrawPolyFilled3D(self, center_x, center_y, center_z, radius, color=0xFFFFFFFF,numsegments =32):
        center = PyOverlay.Point3D(center_x, center_y, center_z)
        self.overlay_instance.DrawPolyFilled3D(center, radius, color, numsegments)
        
    def DrawCubeOutline(self, x, y, z, size, color=0xFFFFFFFF):
        center = PyOverlay.Point3D(x, y, z)
        self.overlay_instance.DrawCubeOutline(center, size, color)
        
    def DrawCubeFilled(self, x, y, z, size, color=0xFFFFFFFF):
        center = PyOverlay.Point3D(x, y, z)
        self.overlay_instance.DrawCubeFilled(center, size, color)

    def DrawText(self, x, y, text, color=0xFFFFFFFF, centered = True, scale=1.0):
        pos = PyOverlay.Point2D(int(x), int(y))
        self.overlay_instance.DrawText(pos, text, color, centered, scale)

    def DrawText3D(self, x, y, z, text, color=0xFFFFFFFF, autoZ= True, centered = True, scale=1.0):
        pos = PyOverlay.Point3D(x, y, z)
        self.overlay_instance.DrawText3D(pos, text, color, autoZ, centered,scale)



    def GetDisplaySize(self):
        return self.overlay_instance.GetDisplaySize()
    
   
        
    
        
    
        

        
    def PushClipRect(self, x, y, x2, y2):
        self.overlay_instance.PushClipRect(x, y, x2, y2)
        
    def PopClipRect(self):
        self.overlay_instance.PopClipRect()

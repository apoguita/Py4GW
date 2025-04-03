# PyMissionMap.pyi

class PyMissionMap:
    def __init__(self) -> None: ...
    
    def GetContext(self) -> None: ...
    
    window_open: bool
    frame_id: int

    left: float
    top: float
    right: float
    bottom: float

    scale_x: float
    scale_y: float
    zoom: float

    center_x: float
    center_y: float

    last_click_x: float
    last_click_y: float

    pan_offset_x: float
    pan_offset_y: float

    mission_map_screen_center_x: float
    mission_map_screen_center_y: float

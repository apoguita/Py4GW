# PyCamera.pyi

from typing import List

class Point3D:
    x: float
    y: float
    z: float

    def __init__(self, x: float, y: float, z: float): ...

class PyCamera:
    look_at_agent_id: int
    h0004: int
    h0008: int
    h000C: int
    max_distance: float
    h0014: int
    yaw: float
    current_yaw: float
    pitch: float
    camera_zoom: float
    h0024: List[float]  # size 4
    yaw_right_click: float
    yaw_right_click2: float
    pitch_right_click: float
    distance2: float
    acceleration_constant: float
    time_since_last_keyboard_rotation: float
    time_since_last_mouse_rotation: float
    time_since_last_mouse_move: float
    time_since_last_agent_selection: float
    time_in_the_map: float
    time_in_the_district: float
    yaw_to_go: float
    pitch_to_go: float
    dist_to_go: float
    max_distance2: float
    h0070: List[float]  # size 2
    position: Point3D
    camera_pos_to_go: Point3D
    cam_pos_inverted: Point3D
    cam_pos_inverted_to_go: Point3D
    look_at_target: Point3D
    look_at_to_go: Point3D
    field_of_view: float
    field_of_view2: float

    def __init__(self) -> None: ...
    def GetContext(self) -> None: ...
    def SetYaw(self, yaw: float) -> None: ...
    def SetPitch(self, pitch: float) -> None: ...
    def SetMaxDist(self, dist: float) -> None: ...
    def SetFieldOfView(self, fov: float) -> None: ...
    def UnlockCam(self, unlock: bool) -> None: ...
    def GetCameraUnlock(self) -> bool: ...
    def ForwardMovement(self, amount: float, true_forward: bool) -> None: ...
    def VerticalMovement(self, amount: float) -> None: ...
    def SideMovement(self, amount: float) -> None: ...
    def RotateMovement(self, angle: float) -> None: ...
    def ComputeCameraPos(self) -> Point3D: ...
    def UpdateCameraPos(self) -> None: ...
    def SetCameraPos(self,x: float, y: float, z: float) -> None: ...
    def SetLookAtTarget(self,x: float, y: float, z: float) -> None: ...
    def SetFog(self, fog:bool) -> None: ...

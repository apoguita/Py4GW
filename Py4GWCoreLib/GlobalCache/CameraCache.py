import PyCamera
import math
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager

class CameraCache:
    def __init__(self, action_queue_manager):
        self._camera_instance = PyCamera.PyCamera()
        self._action_queue_manager:ActionQueueManager = action_queue_manager
        
    def _update_cache(self):
        self._camera_instance.GetContext()
    
    def GetLookAtAgentID(self):
        return self._camera_instance.look_at_agent_id
    
    def GetMaxDistance(self):
        return self._camera_instance.max_distance
    
    def GetYaw(self):
        return self._camera_instance.yaw
    
    def GetPosition(self):
        return self._camera_instance.position.x, self._camera_instance.position.y, self._camera_instance.position.z
    
    def GetLookAtTarget(self):
        return self._camera_instance.look_at_target.x, self._camera_instance.look_at_target.y, self._camera_instance.look_at_target.z
    
    def GetCurrentYaw(self):
        pos = self.GetPosition()
        lat = self.GetLookAtTarget()
        
        x = pos[0] - lat[0]
        y = pos[1] - lat[1]
        
        curtan = math.atan2(y,x)
        
        if curtan >= 0:
            return curtan - math.pi
        else:
            return curtan + math.pi
        
    def GetPitch(self):
        return self._camera_instance.pitch
    
    def GetCameraZoom(self):
        return self._camera_instance.camera_zoom
    
    def GetYawRightClick(self):
        return self._camera_instance.yaw_right_click
    
    def GetYawRightClick2(self):
        return self._camera_instance.yaw_right_click2
    
    def GetPitchRightClick(self):
        return self._camera_instance.pitch_right_click
    
    def GetDistance2(self):
        return self._camera_instance.distance2
    
    def GetAccelerationConstant(self):
        return self._camera_instance.acceleration_constant
    
    def GetTimeSinceLastKeyboardRotation(self):
        return self._camera_instance.time_since_last_keyboard_rotation
    
    def GetTimeSinceLastMouseRotation(self):
        return self._camera_instance.time_since_last_mouse_rotation
    
    def GetTimeSinceLastMouseMove(self):
        return self._camera_instance.time_since_last_mouse_move
    
    def GetTimeSinceLastAgentSelection(self):
        return self._camera_instance.time_since_last_agent_selection
    
    def GetTimeInTheMap(self):
        return self._camera_instance.time_in_the_map
    
    def GetTimeInTheDistrict(self):
        return self._camera_instance.time_in_the_district
    
    def GetYawToGo(self):
        return self._camera_instance.yaw_to_go
    
    def GetPitchToGo(self):
        return self._camera_instance.pitch_to_go
    
    def GetDistanceToGo(self):
        return self._camera_instance.dist_to_go
    
    def GetMaxDistance2(self):
        return self._camera_instance.max_distance2
    
    def GetCameraPositionToGo(self):
        return self._camera_instance.camera_pos_to_go.x, self._camera_instance.camera_pos_to_go.y, self._camera_instance.camera_pos_to_go.z
    
    def GetCameraPositionInverted(self):
        return self._camera_instance.cam_pos_inverted.x, self._camera_instance.cam_pos_inverted.y, self._camera_instance.cam_pos_inverted.z
    
    def GetCameraPositionInvertedToGo(self):
        return self._camera_instance.cam_pos_inverted_to_go.x, self._camera_instance.cam_pos_inverted_to_go.y, self._camera_instance.cam_pos_inverted_to_go.z
    
    def GetAtTargetToGo(self):
        return self._camera_instance.look_at_to_go.x, self._camera_instance.look_at_to_go.y, self._camera_instance.look_at_to_go.z
    
    def GetFieldOfView(self):
        return self._camera_instance.field_of_view
    
    def GetFielsOfView2(self):
        return self._camera_instance.field_of_view2
    
    def SetYaw(self, yaw):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.SetYaw,yaw)
    
    def SetPitch(self, pitch):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.SetPitch,pitch)
    
    def SetMaxDistance(self, dist):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.SetMaxDist,dist)
    
    def SetFieldOfView(self, fov):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.SetFieldOfView,fov)
    
    def SetCameraUnlock(self, unlock):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.UnlockCam,unlock)
        
    def GetCameraUnlock(self):
        return self._camera_instance.GetCameraUnlock()
    
    def ForwardMovement(self, amount, true_forward):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.ForwardMovement,amount, true_forward)
    
    def VerticalMovement(self, amount):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.VerticalMovement,amount)
    
    def SideMovement(self, amount):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.SideMovement,amount)
    
    def RotateMovement(self, angle):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.RotateMovement,angle)
        
    def ComputeCameraPos(self):
        return self._camera_instance.ComputeCameraPos()    
        
    def UpdateCameraPos(self):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.UpdateCameraPos)   
        
    def SetCameraPosition(self, x, y, z):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.SetCameraPos,x, y, z)    
        
    def SetLookAtTarget(self, x, y, z):
        self._action_queue_manager.AddAction("ACTION", self._camera_instance.SetLookAtTarget,x, y, z)    
        
    
    def IsPointInFOV(self, target_x: float, target_y: float) -> bool:
        """
        Determines if a game position point is within the camera's field of view.
        """
        
        cam_x, cam_y, _ = self.GetPosition()
        yaw = self.GetYaw()
        
        if yaw == float('inf') or yaw == float('-inf'):
            return False
        
        fov = self.GetFieldOfView()

        dx = target_x - cam_x
        dy = target_y - cam_y

        dist = math.hypot(dx, dy)
        if dist == 0:
            return True

        angle_to_target = math.atan2(dy, dx)
        angle_diff = angle_to_target - yaw

        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        half_fov = (fov / 2) + 0.2
        return abs(angle_diff) < half_fov   
    
    
    
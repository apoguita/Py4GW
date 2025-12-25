import PyCamera
import math

class Camera:
    @staticmethod
    def camera_instance():
        """
        Returns the camera instance.
        """
        return PyCamera.PyCamera()

    @staticmethod
    def GetLookAtAgentID():
        """
        Returns the agent ID of the camera's look-at target.
        """
        return Camera.camera_instance().look_at_agent_id
    
    @staticmethod
    def GetMaxDistance():
        """
        Returns the maximum distance of the camera.
        """
        return Camera.camera_instance().max_distance
    
    @staticmethod
    def GetYaw():
        """
        Returns the yaw of the camera.
        """
        return Camera.camera_instance().yaw
    
    @staticmethod
    def GetCurrentYaw():
        """
        Returns the current yaw of the camera.
        """
        pos = Camera.GetPosition()
        lat = Camera.GetLookAtTarget()
        
        x = pos[0] - lat[0]
        y = pos[1] - lat[1]
        
        curtan = math.atan2(y,x)
        
        if curtan >= 0:
            return curtan - math.pi
        else:
            return curtan + math.pi
    
    @staticmethod
    def GetPitch():
        """
        Returns the pitch of the camera.
        """
        return Camera.camera_instance().pitch
    
    @staticmethod
    def GetCameraZoom():
        """
        Returns the camera zoom.
        """
        return Camera.camera_instance().camera_zoom
    
    @staticmethod
    def GetYawRightClick():
        """
        Returns the yaw right-click.
        """
        return Camera.camera_instance().yaw_right_click
    
    @staticmethod
    def GetYawRightClick2():
        """
        Returns the yaw right-click.
        """
        return Camera.camera_instance().yaw_right_click2
    
    @staticmethod
    def GetPitchRightClick():
        """
        Returns the pitch right-click.
        """
        return Camera.camera_instance().pitch_right_click
    
    @staticmethod
    def GetDistance2():
        """
        Returns the distance squared.
        """
        return Camera.camera_instance().distance2
    
    @staticmethod
    def GetAccelerationConstant():
        """
        Returns the acceleration constant.
        """
        return Camera.camera_instance().acceleration_constant
    
    @staticmethod
    def GetTimeSinceLastKeyboardRotation():
        """
        Returns the time since the last keyboard rotation.
        """
        return Camera.camera_instance().time_since_last_keyboard_rotation
    
    @staticmethod
    def GetTimeSinceLastMouseRotation():
        """
        Returns the time since the last mouse rotation.
        """
        return Camera.camera_instance().time_since_last_mouse_rotation
    
    @staticmethod
    def GetTimeSinceLastMouseMove():
        """
        Returns the time since the last mouse move.
        """
        return Camera.camera_instance().time_since_last_mouse_move
    
    @staticmethod
    def GetTimeSinceLastAgentSelection():
        """
        Returns the time since the last agent selection.
        """
        return Camera.camera_instance().time_since_last_agent_selection
    
    @staticmethod
    def GetTimeInTheMap():
        """
        Returns the time in the map.
        """
        return Camera.camera_instance().time_in_the_map
    
    @staticmethod
    def GetTimeInTheDistrict():
        """
        Returns the time in the district.
        """
        return Camera.camera_instance().time_in_the_district
    
    @staticmethod
    def GetYawToGo():
        """
        Returns the yaw to go.
        """
        return Camera.camera_instance().yaw_to_go
    
    @staticmethod
    def GetPitchToGo():
        """
        Returns the pitch to go.
        """
        return Camera.camera_instance().pitch_to_go
    
    @staticmethod
    def GetDistanceToGo():
        """
        Returns the distance to go.
        """
        return Camera.camera_instance().dist_to_go
    
    @staticmethod
    def GetMaxDistance2():
        """
        Returns the maximum distance squared.
        """
        return Camera.camera_instance().max_distance2
    
    @staticmethod
    def GetPosition():
        """
        Returns the position of the camera.
        """
        position = Camera.camera_instance().position
        return position.x, position.y, position.z
    
    @staticmethod
    def GetCameraPositionToGo():
        """
        Returns the camera position to go.
        """
        position_to_go = Camera.camera_instance().camera_pos_to_go
        return position_to_go.x, position_to_go.y, position_to_go.z
    
    @staticmethod
    def GetCameraPositionInverted():
        """
        Returns the inverted camera position.
        """
        inverted_position = Camera.camera_instance().cam_pos_inverted
        return inverted_position.x, inverted_position.y, inverted_position.z
    
    @staticmethod
    def GetCameraPositionInvertedToGo():
        """
        Returns the inverted camera position to go.
        """
        inverted_position_to_go = Camera.camera_instance().cam_pos_inverted_to_go
        return inverted_position_to_go.x, inverted_position_to_go.y, inverted_position_to_go.z
    
    @staticmethod
    def GetLookAtTarget():
        """
        Returns the look-at target of the camera.
        """
        target = Camera.camera_instance().look_at_target
        return target.x, target.y, target.z
    
    @staticmethod
    def GetAtTargetToGo():
        """
        Returns the look-at target to go.
        """
        target_to_go = Camera.camera_instance().look_at_to_go
        return target_to_go.x, target_to_go.y, target_to_go.z
    
    @staticmethod
    def GetFieldOfView():
        """
        Returns the field of view of the camera.
        """
        return Camera.camera_instance().field_of_view
    
    @staticmethod
    def GetFielsOfView2():
        """
        Returns the field of view squared.
        """
        return Camera.camera_instance().field_of_view2
    
    @staticmethod
    def SetYaw(yaw):
        """
        Sets the yaw of the camera.
        """
        Camera.camera_instance().SetYaw(yaw)
        
    @staticmethod
    def SetPitch(pitch):
        """
        Sets the pitch of the camera.
        """
        Camera.camera_instance().SetPitch(pitch)
        
    @staticmethod
    def SetMaxDistance(dist):
        """
        Sets the maximum distance of the camera.
        """
        Camera.camera_instance().SetMaxDist(dist)
        
    @staticmethod
    def SetFieldOfView(fov):
        """
        Sets the field of view of the camera.
        """
        Camera.camera_instance().SetFieldOfView(fov)
        
    @staticmethod
    def SetCameraUnlock(unlock):
        """
        Sets the camera unlock state.
        """
        Camera.camera_instance().UnlockCam(unlock)
        
    @staticmethod
    def GetCameraUnlock():
        """
        Returns the camera unlock state.
        """
        return Camera.camera_instance().GetCameraUnlock()
    
    @staticmethod
    def ForwardMovement(amount, true_forward):
        """
        Moves the camera forward.
        """
        Camera.camera_instance().ForwardMovement(amount, true_forward)
        
    @staticmethod
    def VerticalMovement(amount):
        """
        Moves the camera vertically.
        """
        Camera.camera_instance().VerticalMovement(amount)
        
    @staticmethod
    def SideMovement(amount):
        """
        Moves the camera sideways.
        """
        Camera.camera_instance().SideMovement(amount)
        
    @staticmethod
    def RotateMovement(angle):
        """
        Rotates the camera.
        """
        Camera.camera_instance().RotateMovement(angle)
        
    @staticmethod
    def ComputeCameraPos():
        """
        Computes the camera position.
        """
        return Camera.camera_instance().ComputeCameraPos()
    
    @staticmethod
    def UpdateCameraPos():
        """
        Updates the camera position.
        """
        Camera.camera_instance().UpdateCameraPos()
        
    @staticmethod
    def SetCameraPosition(x, y, z):
        """
        Sets the camera position.
        """
        Camera.camera_instance().SetCameraPos(x, y, z)
        
    @staticmethod
    def SetLookAtTarget(x, y, z):
        """
        Sets the look-at target of the camera.
        """
        Camera.camera_instance().SetLookAtTarget(x, y, z)
        
    @staticmethod
    def SetFog(fog: bool):
        """
        Sets the fog state of the camera.
        """
        Camera.camera_instance().SetFog(fog)
            
    @staticmethod
    def IsPointInFOV(target_x: float, target_y: float) -> bool:
        cam_x, cam_y, _ = Camera.GetPosition()
        yaw = Camera.GetYaw()
        fov = Camera.GetFieldOfView()

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
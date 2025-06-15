import Py2DRenderer
import PyOverlay

class DXOverlay:
        def __init__(self):
            self.renderer = Py2DRenderer.Py2DRenderer()
            self.world_space = self._WorldSpace(self)
            self.screen_space = self._ScreenSpace(self)
            self.mask = self._Mask(self)

        def set_primitives(self, shapes, color):
            self.renderer.set_primitives(shapes, color)

        def render(self):
            self.renderer.render()
            
        def ApplyStencilMask(self):
            self.renderer.ApplyStencilMask()
            
        def ResetStencilMask(self):
            self.renderer.ResetStencilMask()
        
        @staticmethod
        def WorldToScreen(x,y,z=0.0):
            if z == 0.0:
                z = DXOverlay.FindZ(x, y)

            screen_pos = PyOverlay.Overlay().WorldToScreen(x, y, z)
            return screen_pos.x, screen_pos.y
            
        @staticmethod
        def FindZ (x, y, z=0):
            """Find The altitude of the ground at the given x,y coordinates based on Pathing Maps"""
            return PyOverlay.Overlay().FindZ(x, y, z)
    
        def DrawLine(self, _from_x, _from_y, _to_x, _to_y, color, thickness = 1):
            _from = PyOverlay.Point2D(int(_from_x), int(_from_y))
            _to = PyOverlay.Point2D(int(_to_x), int(_to_y))
            self.renderer.DrawLine(_from, _to, color, thickness)
            
        def DrawLine3D(self, _from_x, _from_y, _from_z, _to_x, _to_y, _to_z, color, use_occlusion = True):
            if _from_z == 0:
                _from_z = DXOverlay.FindZ(_from_x, _from_y)
            if _to_z == 0:
                _to_z = DXOverlay.FindZ(_to_x, _to_y)
                
            _from = PyOverlay.Point3D(_from_x, _from_y, _from_z+100)
            _to = PyOverlay.Point3D(_to_x, _to_y, _to_z+100)
            
            self.renderer.DrawLine3D(_from, _to, color, use_occlusion)
            
        def DrawTriangle(self, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, color, thickness = 1.0):
            p1 = PyOverlay.Point2D(int(p1_x), int(p1_y))
            p2 = PyOverlay.Point2D(int(p2_x), int(p2_y))
            p3 = PyOverlay.Point2D(int(p3_x), int(p3_y))
            self.renderer.DrawTriangle(p1, p2, p3, color, thickness)
            
        def DrawTriangleFilled(self, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, color):
            p1 = PyOverlay.Point2D(int(p1_x), int(p1_y))
            p2 = PyOverlay.Point2D(int(p2_x), int(p2_y))
            p3 = PyOverlay.Point2D(int(p3_x), int(p3_y))
            self.renderer.DrawTriangleFilled(p1, p2, p3, color)
            
        def DrawTriangle3D(self, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, p3_x, p3_y, p3_z, color, use_occlusion = True):
            if p1_z == 0:
                p1_z = DXOverlay.FindZ(p1_x, p1_y)
            if p2_z == 0:
                p2_z = DXOverlay.FindZ(p2_x, p2_y)
            if p3_z == 0:
                p3_z = DXOverlay.FindZ(p3_x, p3_y)
                
            p1 = PyOverlay.Point3D(p1_x, p1_y, p1_z+100)
            p2 = PyOverlay.Point3D(p2_x, p2_y, p2_z+100)
            p3 = PyOverlay.Point3D(p3_x, p3_y, p3_z+100)
            
            self.renderer.DrawTriangle3D(p1, p2, p3, color, use_occlusion)
            
        def DrawTriangleFilled3D(self, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, p3_x, p3_y, p3_z, color, use_occlusion = True):
            if p1_z == 0:
                p1_z = DXOverlay.FindZ(p1_x, p1_y)
            if p2_z == 0:
                p2_z = DXOverlay.FindZ(p2_x, p2_y)
            if p3_z == 0:
                p3_z = DXOverlay.FindZ(p3_x, p3_y)
                
            p1 = PyOverlay.Point3D(p1_x, p1_y, p1_z+100)
            p2 = PyOverlay.Point3D(p2_x, p2_y, p2_z+100)
            p3 = PyOverlay.Point3D(p3_x, p3_y, p3_z+100)
            
            self.renderer.DrawTriangleFilled3D(p1, p2, p3, color, use_occlusion)
            
        def DrawQuad(self, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y, color, thickness = 1):
            p1 = PyOverlay.Point2D(int(p1_x), int(p1_y))
            p2 = PyOverlay.Point2D(int(p2_x), int(p2_y))
            p3 = PyOverlay.Point2D(int(p3_x), int(p3_y))
            p4 = PyOverlay.Point2D(int(p4_x), int(p4_y))
            self.renderer.DrawQuad(p1, p2, p3, p4, color, thickness)
            
        def DrawQuadFilled(self, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y, color):
            p1 = PyOverlay.Point2D(int(p1_x), int(p1_y))
            p2 = PyOverlay.Point2D(int(p2_x), int(p2_y))
            p3 = PyOverlay.Point2D(int(p3_x), int(p3_y))
            p4 = PyOverlay.Point2D(int(p4_x), int(p4_y))
            self.renderer.DrawQuadFilled(p1, p2, p3, p4, color)
            
        def DrawQuad3D(self, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, p3_x, p3_y, p3_z, p4_x, p4_y, p4_z, color, use_occlusion = True):
            if p1_z == 0:
                p1_z = DXOverlay.FindZ(p1_x, p1_y)
            if p2_z == 0:
                p2_z = DXOverlay.FindZ(p2_x, p2_y)
            if p3_z == 0:
                p3_z = DXOverlay.FindZ(p3_x, p3_y)
            if p4_z == 0:
                p4_z = DXOverlay.FindZ(p4_x, p4_y)
                
            p1 = PyOverlay.Point3D(p1_x, p1_y, p1_z+100)
            p2 = PyOverlay.Point3D(p2_x, p2_y, p2_z+100)
            p3 = PyOverlay.Point3D(p3_x, p3_y, p3_z+100)
            p4 = PyOverlay.Point3D(p4_x, p4_y, p4_z+100)
            
            self.renderer.DrawQuad3D(p1, p2, p3, p4, color, use_occlusion)
            
        def DrawQuadFilled3D(self, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, p3_x, p3_y, p3_z, p4_x, p4_y, p4_z, color, use_occlusion = True):
            if p1_z == 0:
                p1_z = DXOverlay.FindZ(p1_x, p1_y)
            if p2_z == 0:
                p2_z = DXOverlay.FindZ(p2_x, p2_y)
            if p3_z == 0:
                p3_z = DXOverlay.FindZ(p3_x, p3_y)
            if p4_z == 0:
                p4_z = DXOverlay.FindZ(p4_x, p4_y)
                
            p1 = PyOverlay.Point3D(p1_x, p1_y, p1_z+100)
            p2 = PyOverlay.Point3D(p2_x, p2_y, p2_z+100)
            p3 = PyOverlay.Point3D(p3_x, p3_y, p3_z+100)
            p4 = PyOverlay.Point3D(p4_x, p4_y, p4_z+100)
            
            self.renderer.DrawQuadFilled3D(p1, p2, p3, p4, color, use_occlusion)
            
        def DrawPoly(self, center_x, center_y, radius, color, segments = 32, thickness = 1):
            center = PyOverlay.Point2D(int(center_x), int(center_y))
            self.renderer.DrawPoly(center, radius, color, segments, thickness)
            
        def DrawPolyFilled(self, center_x, center_y, radius, color, segments = 32):
            center = PyOverlay.Point2D(int(center_x), int(center_y))
            self.renderer.DrawPolyFilled(center, radius, color, segments)
            
        def DrawPoly3D(self, center_x, center_y, center_z, radius, color, segments = 32, use_occlusion = True):
            if center_z == 0:
                center_z = DXOverlay.FindZ(center_x, center_y)
                
            center = PyOverlay.Point3D(center_x, center_y, center_z+100)
            self.renderer.DrawPoly3D(center, radius, color, segments, use_occlusion)
            
        def DrawPolyFilled3D(self, center_x, center_y, center_z, radius, color, segments = 32, use_occlusion = True):
            if center_z == 0:
                center_z = DXOverlay.FindZ(center_x, center_y)
                
            center = PyOverlay.Point3D(center_x, center_y, center_z+100)
            self.renderer.DrawPolyFilled3D(center, radius, color, segments, use_occlusion)
            
        def DrawCubeOutline(self, center_x, center_y, center_z, size, color, use_occlusion = True):
            if center_z == 0:
                center_z = DXOverlay.FindZ(center_x, center_y)
                
            center = PyOverlay.Point3D(center_x, center_y, center_z+100)
            self.renderer.DrawCubeOutline(center, size, color, use_occlusion)
            
        def DrawCubeFilled(self, center_x, center_y, center_z, size, color, use_occlusion = True):
            if center_z == 0:
                center_z = DXOverlay.FindZ(center_x, center_y)
                
            center = PyOverlay.Point3D(center_x, center_y, center_z+100)
            self.renderer.DrawCubeFilled(center, size, color, use_occlusion)
            
            
        def DrawTexture(self, file_path, screen_pos_x, screen_pos_y, width, height, tint=0xFFFFFFFF):
            if width <= 0 or height <= 0:
                raise ValueError("Width and height must be greater than zero.")
            self.renderer.DrawTexture(file_path, screen_pos_x, screen_pos_y, width, height, tint)
            
        def DrawTexture3D(self, file_path, world_pos_x, world_pos_y, world_pos_z, width, height, use_occlusion=True, tint=0xFFFFFFFF):
            if width <= 0 or height <= 0:
                raise ValueError("Width and height must be greater than zero.")
            if world_pos_z == 0:
                world_pos_z = DXOverlay.FindZ(world_pos_x, world_pos_y)
                
            self.renderer.DrawTexture3D(file_path, world_pos_x, world_pos_y, world_pos_z+100, width, height, use_occlusion, tint)
            
        def DrawQuadTextured3D(self, file_path, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, p3_x, p3_y, p3_z, p4_x, p4_y, p4_z, use_occlusion=True, tint=0xFFFFFFFF):
            if p1_z == 0:
                p1_z = DXOverlay.FindZ(p1_x, p1_y)
            if p2_z == 0:
                p2_z = DXOverlay.FindZ(p2_x, p2_y)
            if p3_z == 0:
                p3_z = DXOverlay.FindZ(p3_x, p3_y)
            if p4_z == 0:
                p4_z = DXOverlay.FindZ(p4_x, p4_y)
                
            p1 = PyOverlay.Point3D(p1_x, p1_y, p1_z-100)
            p2 = PyOverlay.Point3D(p2_x, p2_y, p2_z-100)
            p3 = PyOverlay.Point3D(p3_x, p3_y, p3_z-100)
            p4 = PyOverlay.Point3D(p4_x, p4_y, p4_z-100)
            
            self.renderer.DrawQuadTextured3D(file_path, p1, p2, p3, p4, use_occlusion, tint) 

            
        class _ScreenSpace:
            def __init__(self, parent):
                self._renderer = parent.renderer

            def set_screen_space(self, enabled):
                self._renderer.set_screen_space(enabled)

            def set_zoom_x(self, zoom):
                self._renderer.set_screen_zoom_x(zoom)

            def set_zoom_y(self, zoom):
                self._renderer.set_screen_zoom_y(zoom)

            def set_zoom(self, zoom):
                self.set_zoom_x(zoom)
                self.set_zoom_y(-zoom)

            def set_pan(self, x, y):
                self._renderer.set_screen_offset(x, y)

            def set_rotation(self, rotation):
                self._renderer.set_screen_rotation(rotation)

        class _WorldSpace:
            def __init__(self, parent):
                self._renderer = parent.renderer

            def set_world_space(self, enabled):
                self._renderer.set_world_space(enabled)

            def set_zoom_x(self, zoom):
                self._renderer.set_world_zoom_x(zoom)

            def set_zoom_y(self, zoom):
                self._renderer.set_world_zoom_y(zoom)

            def set_zoom(self, zoom):
                self.set_zoom_x(zoom)
                self.set_zoom_y(-zoom)

            def set_pan(self, x, y):
                self._renderer.set_world_pan(x, y)
                
            def set_scale(self, scale):
                self._renderer.set_world_scale(scale)

            def set_rotation(self, rotation):
                self._renderer.set_world_rotation(rotation)
                
        class _Mask:
            def __init__(self, parent):
                self._renderer = parent.renderer
                
            def set_circular_mask(self, enabled):
                self._renderer.set_circular_mask(enabled)

            def set_mask_radius(self, radius):
                self._renderer.set_circular_mask_radius(radius)

            def set_mask_center(self, x, y):
                self._renderer.set_circular_mask_center(x, y)
                
            def set_rectangle_mask(self, enabled):
                self._renderer.set_rectangle_mask(enabled)
                
            def set_rectangle_mask_bounds(self, x, y, width, height):
                self._renderer.set_rectangle_mask_bounds(x, y, width, height)

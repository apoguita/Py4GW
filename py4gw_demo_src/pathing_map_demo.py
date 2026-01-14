from Py4GWCoreLib import *
import PyImGui

module_name = "Pathing Maps"


class MapBoundaries:
    def __init__(self, x_min, x_max, y_min, y_max, unk):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.unk = unk


class PathingMapRenderer:
    def __init__(self):
        # Window state
        self.WINDOW_WIDTH = 1000
        self.WINDOW_HEIGHT = 1000

        # Pan/zoom state (multipliers over base fit)
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

        # Merging params
        self.BUCKET_SIZE = 100.0
        self.MIN_PIXEL_SIZE = 0

        # Map state
        min_x, min_y, max_x, max_y = Map.GetMapBoundaries()
        self.map_boundaries = MapBoundaries(min_x, max_x, min_y, max_y, 0)

        self.pathing_map = []
        self.quad_cache = {}
        self.last_window_state = (0, 0, 0, 0)
        self.initialized = False
        self.draw_maps = True
        self.clicked_points: list[tuple[float, float]] = []
        self.paths: list[list[tuple[float, float, float]]] = []
        

    # -------------------------------
    # Pan + Zoom handling
    # -------------------------------
    def update_pan_zoom_with_mouse(self, child_pos):
        """Update pan (mouse drag) and zoom (mouse wheel), cursor anchored accurately."""
        if PyImGui.is_window_hovered():
            io = PyImGui.get_io()

            # --- Zoom ---
            if io.mouse_wheel != 0.0:
                mouse_x = io.mouse_pos_x - child_pos[0]
                mouse_y = io.mouse_pos_y - child_pos[1]

                world_x, world_y = self.screen_to_world(mouse_x, mouse_y, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

                zoom_step = 1.25
                if io.mouse_wheel > 0:
                    self.zoom_factor *= zoom_step
                else:
                    self.zoom_factor /= zoom_step
                self.zoom_factor = max(0.1, min(self.zoom_factor, 100.0))

                new_sx, new_sy = self.scale_coords(world_x, world_y, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
                self.pan_x += mouse_x - new_sx
                self.pan_y += mouse_y - new_sy

            # --- Pan ---
            left = 0
            if PyImGui.is_mouse_dragging(left, 0.0):
                dx, dy = PyImGui.get_mouse_drag_delta(left, 0.0)
                self.pan_x += dx
                self.pan_y += dy
                PyImGui.reset_mouse_drag_delta(left)

            # --- Double-click: store world coords ---
            if PyImGui.is_mouse_double_clicked(0):  # left button
                mouse_x = io.mouse_pos_x - child_pos[0]
                mouse_y = io.mouse_pos_y - child_pos[1]
                wx, wy = self.screen_to_world(mouse_x, mouse_y, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

                # Store every clicked point (no limit)
                self.clicked_points.append((wx, wy))
                
                if len(self.clicked_points) >= 2:
                    sx, sy = self.clicked_points[-2]
                    gx, gy = self.clicked_points[-1]
                    # use nav coords for pathing (Y negated)
                    self.schedule_pathfinding((sx, -sy), (gx, -gy))


    def apply_pan_zoom(self, sx: float, sy: float) -> tuple[float, float]:
        """Apply pan only (zoom happens in scale_coords)."""
        return sx + self.pan_x, sy + self.pan_y

    def screen_to_world(self, sx: float, sy: float, window_w: float, window_h: float) -> tuple[float, float]:
        """Convert screen coords to world coords (inverse of scale_coords, without pan/zoom)."""
        world_w = self.map_boundaries.x_max - self.map_boundaries.x_min
        world_h = self.map_boundaries.y_max - self.map_boundaries.y_min

        aspect_world = world_w / world_h
        aspect_window = window_w / window_h if window_h != 0 else aspect_world

        if aspect_world > aspect_window:
            fit_scale = window_w / world_w
            offset_x = 0
            offset_y = (window_h - world_h * fit_scale) / 2
        else:
            fit_scale = window_h / world_h
            offset_x = (window_w - world_w * fit_scale) / 2
            offset_y = 0

        # Remove pan first
        sx -= self.pan_x
        sy -= self.pan_y

        # Undo zoom
        scale = fit_scale * self.zoom_factor
        wx = (sx - offset_x) / scale + self.map_boundaries.x_min
        wy = (sy - offset_y) / scale + self.map_boundaries.y_min

        return wx, wy


    def scale_coords(self, x, y, window_w, window_h, flip_y: bool = False):
        """
        Scale (x, y) from world coordinates to ImGui window coordinates,
        then apply pan + zoom.
        """
        world_w = self.map_boundaries.x_max - self.map_boundaries.x_min
        world_h = self.map_boundaries.y_max - self.map_boundaries.y_min

        if world_w == 0 or world_h == 0:
            return 0.0, 0.0

        if flip_y:
            y = self.map_boundaries.y_max - (y - self.map_boundaries.y_min)

        # Fit-to-window base scale
        aspect_world = world_w / world_h
        aspect_window = window_w / window_h if window_h != 0 else aspect_world

        if aspect_world > aspect_window:
            fit_scale = window_w / world_w
            offset_x = 0
            offset_y = (window_h - world_h * fit_scale) / 2
        else:
            fit_scale = window_h / world_h
            offset_x = (window_w - world_w * fit_scale) / 2
            offset_y = 0

        #Apply zoom factor here
        scale = fit_scale * self.zoom_factor

        sx = (x - self.map_boundaries.x_min) * scale + offset_x
        sy = (y - self.map_boundaries.y_min) * scale + offset_y

        return self.apply_pan_zoom(sx, sy)
    

    # -------------------------------
    # Merging
    # -------------------------------
    def bucket_merge_trapezoids(self, trapezoids, window_w, window_h):
        buckets = {}
        for t in trapezoids:
            cx = (t.XTL + t.XTR + t.XBL + t.XBR) / 4
            cy = (t.YT + t.YB) / 2
            bx = int(cx // self.BUCKET_SIZE)
            by = int(cy // self.BUCKET_SIZE)

            key = (bx, by)
            if key not in buckets:
                buckets[key] = {
                    "XTL": t.XTL, "XTR": t.XTR,
                    "XBL": t.XBL, "XBR": t.XBR,
                    "YT": t.YT, "YB": t.YB
                }
            else:
                b = buckets[key]
                b["XTL"] = min(b["XTL"], t.XTL)
                b["XTR"] = max(b["XTR"], t.XTR)
                b["XBL"] = min(b["XBL"], t.XBL)
                b["XBR"] = max(b["XBR"], t.XBR)
                b["YT"] = max(b["YT"], t.YT)
                b["YB"] = min(b["YB"], t.YB)

        merged = list(buckets.values())
        for b in merged:
            if b["YT"] < b["YB"]:
                b["YT"], b["YB"] = b["YB"], b["YT"]

        result = []
        for b in merged:
            tl_x, tl_y = self.scale_coords(b["XTL"], b["YT"], window_w, window_h)
            br_x, br_y = self.scale_coords(b["XBR"], b["YB"], window_w, window_h)
            if abs(br_x - tl_x) >= self.MIN_PIXEL_SIZE and abs(br_y - tl_y) >= self.MIN_PIXEL_SIZE:
                result.append(b)
        return result

    def merge_horizontal_strips(self, quads):
        if not quads:
            return []
        quads.sort(key=lambda q: (q["YB"], q["XTL"]))
        merged = []
        current = quads[0].copy()

        for t in quads[1:]:
            same_band = abs(current["YB"] - t["YB"]) < 1e-3 and abs(current["YT"] - t["YT"]) < 1e-3
            overlap_or_touch = not (t["XTL"] > current["XTR"] + 1e-3 or t["XTR"] < current["XTL"] - 1e-3)

            if same_band and overlap_or_touch:
                current["XTR"] = max(current["XTR"], t["XTR"])
                current["XBR"] = max(current["XBR"], t["XBR"])
                current["XTL"] = min(current["XTL"], t["XTL"])
                current["XBL"] = min(current["XBL"], t["XBL"])
            else:
                merged.append(current)
                current = t.copy()
        merged.append(current)
        return merged

    # -------------------------------
    # Quad cache + drawing
    # -------------------------------
    def get_layer_quads(self, index, layer, window_w, window_h, window_pos):
        current_state = (window_w, window_h, int(window_pos[0]), int(window_pos[1]),
                        round(self.zoom_factor, 3), round(self.pan_x, 1), round(self.pan_y, 1))
        last_w, last_h, last_x, last_y, last_zoom, last_panx, last_pany = (
            self.last_window_state if len(self.last_window_state) == 7 else (0, 0, 0, 0, 1.0, 0.0, 0.0)
        )
        cur_w, cur_h, cur_x, cur_y, cur_zoom, cur_panx, cur_pany = current_state
        cache_key = (index, cur_w, cur_h, cur_zoom, cur_panx, cur_pany)

        if (cur_w, cur_h, cur_zoom, cur_panx, cur_pany) != (last_w, last_h, last_zoom, last_panx, last_pany):
            self.quad_cache.clear()

        if cache_key not in self.quad_cache:
            quads = []
            merged_traps = self.bucket_merge_trapezoids(layer.trapezoids, cur_w, cur_h)
            merged_traps = self.merge_horizontal_strips(merged_traps)

            for t in merged_traps:
                tl_x, tl_y = self.scale_coords(t["XTL"], t["YT"], cur_w, cur_h)
                tr_x, tr_y = self.scale_coords(t["XTR"], t["YT"], cur_w, cur_h)
                br_x, br_y = self.scale_coords(t["XBR"], t["YB"], cur_w, cur_h)
                bl_x, bl_y = self.scale_coords(t["XBL"], t["YB"], cur_w, cur_h)

                quads.append((tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y))

            self.quad_cache[cache_key] = quads

        # Apply window offset
        quads_with_offset = []
        for q in self.quad_cache[cache_key]:
            tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y = q
            tl_x += cur_x; tl_y += cur_y
            tr_x += cur_x; tr_y += cur_y
            br_x += cur_x; br_y += cur_y
            bl_x += cur_x; bl_y += cur_y
            quads_with_offset.append((tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y))

        self.last_window_state = current_state
        return quads_with_offset


    def draw_trapezoids(self, index, layer, clip_rect, color: Color = Color(130, 130, 130, 255)):
        x1, y1, x2, y2 = clip_rect

        quads = self.get_layer_quads(index, layer, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, (x1, y1))

        for q in quads:
            tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y = q

            xs = [tl_x, tr_x, br_x, bl_x]
            ys = [tl_y, tr_y, br_y, bl_y]

            if max(xs) < x1 or min(xs) > x2:
                continue
            if max(ys) < y1 or min(ys) > y2:
                continue

            PyImGui.draw_list_add_quad_filled(
                tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y, color.to_color()
            )



    # -------------------------------
    # Geometry transforms
    # -------------------------------
    def flip_layer_geometry(self, layer):
        world_h = self.map_boundaries.y_max - self.map_boundaries.y_min
        for t in layer.trapezoids:
            new_YT = world_h - (t.YB - self.map_boundaries.y_min)
            new_YB = world_h - (t.YT - self.map_boundaries.y_min)
            t.YT, t.YB = new_YT, new_YB
            t.XTL, t.XBL = t.XBL, t.XTL
            t.XTR, t.XBR = t.XBR, t.XTR
        return layer

    def shift_layer_geometry(self, layer):
        world_h = (self.map_boundaries.y_max - self.map_boundaries.y_min) / 2
        for t in layer.trapezoids:
            t.YT -= world_h
            t.YB -= world_h
        return layer

    # -------------------------------
    # Windows
    # -------------------------------

    def DrawMapWindow(self):
        if not self.initialized:
            PyImGui.set_next_window_size(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
            self.initialized = True

        flags = (
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse
        )
        #if PyImGui.begin("Pathing Map", flags):
            # Parent window info
        parent_pos = PyImGui.get_window_pos()
        parent_size = PyImGui.get_window_size()
        self.WINDOW_WIDTH, self.WINDOW_HEIGHT = int(parent_size[0]), int(parent_size[1])

        # Child region = full content area
        avail_w, avail_h = PyImGui.get_content_region_avail()
        if PyImGui.begin_child(
            "MapCanvas",
            (avail_w, avail_h),
            border=False,
            flags=PyImGui.WindowFlags.NoMove | PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse
        ):
            # Inside DrawMapWindow -> inside child block
            child_pos = PyImGui.get_window_pos()
            child_size = PyImGui.get_window_size()
            self.WINDOW_WIDTH, self.WINDOW_HEIGHT = int(child_size[0]), int(child_size[1])

            # Compute absolute clip rect for child content
            child_min = PyImGui.get_window_content_region_min()
            child_max = PyImGui.get_window_content_region_max()
            clip_x1 = child_pos[0] + child_min[0]
            clip_y1 = child_pos[1] + child_min[1]
            clip_x2 = child_pos[0] + child_max[0]
            clip_y2 = child_pos[1] + child_max[1]

            # Update pan/zoom
            self.update_pan_zoom_with_mouse(child_pos)


            # Draw map with proper clip rect
            for index, layer in enumerate(self.pathing_map):
                color = Color(255, 255, 255, 255) if index == 0 else Color(230, 0, 255, 255)
                self.draw_trapezoids(index, layer, (clip_x1, clip_y1, clip_x2, clip_y2), color)

            # Draw player
            self.draw_player_position(child_pos)
            self.draw_clicked_points(child_pos)

        PyImGui.end_child()
           # PyImGui.end()


    def Draw_PathingMap_Window(self):
        if not self.pathing_map:
            if PyImGui.button("Populate Pathing Maps"):
                self.pathing_map = Map.Pathing.GetPathingMaps()
                self.pathing_map = [
                    self.shift_layer_geometry(self.flip_layer_geometry(layer))
                    for layer in self.pathing_map
                ]

        # Toggle
        #self.draw_maps = PyImGui.checkbox("Draw Pathing Maps", self.draw_maps)

        # Zoom slider
        self.zoom_factor = PyImGui.slider_float("Zoom", self.zoom_factor, 0.1, 5.0)

        # Pan sliders
        self.pan_x = PyImGui.slider_float("Pan X", self.pan_x, -500.0, 500.0)
        PyImGui.same_line(0,-1)
        self.pan_y = PyImGui.slider_float("Pan Y", self.pan_y, -500.0, 500.0)

        # Reset
        if PyImGui.button("Reset Pan/Zoom"):
            self.zoom_factor = 1.0
            self.pan_x = 0.0
            self.pan_y = 0.0
            
        PyImGui.same_line(0,-1)
        PyImGui.text("Drag your mouse to pan, scroll to zoom, double-click to set path points.")

        PyImGui.separator()
        

        # Draw the actual map if enabled
        if self.draw_maps and self.pathing_map:
            self.DrawMapWindow()
                
    def draw_player_position(
        self,
        window_pos,
        color: Color = Color(0, 255, 0, 255),
        base_radius: int = 5,
        min_radius: int = 5,
        max_radius: int = 20
    ):
        try:
            player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        except Exception:
            return

        sx, sy = self.scale_coords(player_x, player_y, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, flip_y=True)

        # Apply window offset
        sx += window_pos[0]
        sy += window_pos[1]

        # Scale radius based on zoom
        scaled_radius = base_radius * self.zoom_factor
        scaled_radius = max(min_radius, min(max_radius, scaled_radius))

        PyImGui.draw_list_add_circle_filled(
            sx, sy,
            scaled_radius,
            color.to_color(),
            12
        )
        
    def draw_clicked_points(self, window_pos, radius: int = 8, thickness: float = 2.0):
        screen_points = []

        for i, (wx, wy) in enumerate(self.clicked_points):
            # clicked points are already in flipped world coords, so no flip here
            sx, sy = self.scale_coords(wx, wy, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, flip_y=False)
            sx += window_pos[0]
            sy += window_pos[1]
            screen_points.append((sx, sy))

            # Draw rectangle at point
            half = radius / 2
            x1, y1 = sx - half, sy - half  # top-left
            x2, y2 = sx + half, sy - half  # top-right
            x3, y3 = sx + half, sy + half  # bottom-right
            x4, y4 = sx - half, sy + half  # bottom-left

            color = Color(0, 128, 255, 255) if i == 0 else Color(255, 64, 64, 255)
            PyImGui.draw_list_add_quad_filled(x1, y1, x2, y2, x3, y3, x4, y4, color.to_color())
            
        # Draw full cached paths
        for path in self.paths:
            for i in range(len(path) - 1):
                wx1, wy1, _ = path[i]
                wx2, wy2, _ = path[i + 1]

                sx1, sy1 = self.scale_coords(wx1, wy1, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, flip_y=True)
                sx2, sy2 = self.scale_coords(wx2, wy2, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, flip_y=True)

                sx1 += window_pos[0]; sy1 += window_pos[1]
                sx2 += window_pos[0]; sy2 += window_pos[1]

                PyImGui.draw_list_add_line(sx1, sy1, sx2, sy2, Color(255, 0, 255, 255).to_color(), thickness)
            
            
    def get_path(self, start: tuple[float, float], end: tuple[float, float]):
        zplane1 = 0 # DXOverlay.FindZ(start[0], start[1])
        zplane2 = 0 # DXOverlay.FindZ(end[0], end[1])

        point1 = (start[0], start[1], zplane1)
        point2 = (end[0], end[1], zplane2)

        path = yield from AutoPathing().get_path(point1, point2)

        # Cache the path in 2D (drop z)
        if path:
            self.paths.append([(px, py, pz) for (px, py, pz) in path])
            #print("Path found:", path)
        else:
            #print("No path found")
            pass



    def schedule_pathfinding(self, start: tuple[float, float], end: tuple[float, float]):
        GLOBAL_CACHE.Coroutines.append(self.get_path(start, end))



renderer = PathingMapRenderer()

"""def main():
    x,y = GLOBAL_CACHE,Player.GetXY()
    renderer.Draw_PathingMap_Window()


if __name__ == "__main__":
    main()
"""
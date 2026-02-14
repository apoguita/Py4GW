"""PathingDataDumper - Capture Guild Wars pathing data for testing.

This widget captures complete pathing maps (trapezoids, portals), blocking props
(collision circles), and test markers to a single JSON file per map for offline
testing of pathfinding algorithms.

Usage:
1. Navigate to a map you want to capture
2. Open mission map (U key)
3. Click on mission map to place markers
4. Click "Capture Current Map" to save data
5. Output: Tests/pathing/dumps/map_{id}.json.gz
"""

import PyImGui
import Py4GW
import json
import gzip
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

from Py4GWCoreLib import Map, Player, Agent, Routines, Color, GLOBAL_CACHE, ImGui
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.native_src.context.MapContext import MapContext

MODULE_NAME = "Pathing Data Dumper"

@dataclass
class MarkerData:
    """Test marker with coordinates and metadata."""
    coords: tuple[float, float]
    z_plane: int
    trapezoid_id: Optional[int]
    notes: str
    name: str


class PathingDataDumper:
    """Manages pathing data capture and test marker placement."""

    def __init__(self):
        root = Py4GW.Console.get_projects_path()
        self.base_dir = Path(root) / "Tests" / "pathing"
        self.maps_dir = self.base_dir / "dumps"
        self.maps_dir.mkdir(parents=True, exist_ok=True)

        self.capture_markers: list[MarkerData] = []
        self.current_map_id: int = Map.GetMapID()
        self.last_capture_map_id: Optional[int] = None
        self.status_message: str = ""
        self.status_color: Color = Color(255, 255, 255, 255)
        self.show_markers_3d: bool = True
        self.show_markers_map: bool = True
        self.last_click_normalized: tuple[float, float] = Map.MissionMap.GetLastClickCoords()
        self.editing_marker_index: Optional[int] = None
        self.editing_notes_buffer: str = ""
        self.show_edit_popup: bool = False

        # Load existing markers for current map
        self._load_markers_from_file()

    def check_map_change(self) -> None:
        """Detect map change; clear markers and re-sync click state."""
        map_id = Map.GetMapID()
        if map_id == self.current_map_id:
            return

        self.current_map_id = map_id
        self.capture_markers.clear()
        # Re-sync to current click coords so stale travel-click doesn't
        # trigger a phantom marker in the new map.
        self.last_click_normalized = Map.MissionMap.GetLastClickCoords()
        self._set_status("Map changed — markers cleared", is_error=False)

        # Load any previously saved markers for this map
        self._load_markers_from_file()

    def update_mission_map_clicks(self) -> None:
        """Detect clicks on mission map and add markers."""
        if not Map.MissionMap.IsWindowOpen():
            return

        # Get normalized mission map click coordinates
        nx, ny = Map.MissionMap.GetLastClickCoords()

        # Only add marker if coordinates changed (new click detected)
        if (nx, ny) != self.last_click_normalized and (nx != 0.0 or ny != 0.0):
            self.last_click_normalized = (nx, ny)

            # Convert normalized coords to game world coords
            gx, gy = Map.MissionMap.MapProjection.NormalizedScreenToGamePos(nx, ny)
            self._add_marker_at_coords(gx, gy)

    def _add_marker_at_coords(self, x: float, y: float) -> None:
        """Add marker at specific world coordinates."""
        try:
            player_z_plane = Agent.GetZPlane(Player.GetAgentID())

            # Find trapezoid ID - ensure navmesh is loaded first
            trap_id = None
            debug_info = []

            pathing_maps = Map.Pathing.GetPathingMaps()
            debug_info.append(f"PathingMaps: {'Yes' if pathing_maps else 'No'}")

            if pathing_maps:
                debug_info.append(f"Layers: {len(pathing_maps)}")

                # Force navmesh to be built by running load_pathing_maps coroutine
                autopath = AutoPathing()
                loader = autopath.load_pathing_maps()
                try:
                    while True:
                        next(loader)
                except StopIteration:
                    pass

                navmesh = autopath.get_navmesh()
                debug_info.append(f"NavMesh: {'Yes' if navmesh else 'No'}")

                if navmesh:
                    debug_info.append(f"Total traps: {len(navmesh.trapezoids)}")

                    # Check spatial grid
                    gx = int(x) // navmesh.GRID_SIZE
                    gy = int(y) // navmesh.GRID_SIZE
                    candidates = navmesh.spatial_grid.get((gx, gy), [])
                    debug_info.append(f"Grid ({gx},{gy}) candidates: {len(candidates)}")

                    trap_id = navmesh.find_trapezoid_id_by_coord((x, y))
                    debug_info.append(f"TrapID: {trap_id}")

            marker = MarkerData(
                coords=(x, y),
                z_plane=player_z_plane,
                trapezoid_id=trap_id,
                notes="",
                name=f"marker_{len(self.capture_markers)}"
            )
            self.capture_markers.append(marker)

            status_msg = f"Added at ({x:.1f}, {y:.1f}) | {' | '.join(debug_info)}"
            self._set_status(status_msg, is_error=False)
            self._save_markers_to_file()

        except Exception as e:
            self._set_status(f"Error adding marker: {str(e)}", is_error=True)

    def capture_current_map(self) -> None:
        """Capture complete pathing + props data for current map to JSON."""
        map_id = Map.GetMapID()
        if not map_id:
            self._set_status("No map loaded", is_error=True)
            return

        try:
            pathing_maps = Map.Pathing.GetPathingMaps()
            if not pathing_maps:
                self._set_status("No pathing maps available", is_error=True)
                return

            data = {
                "map_id": map_id,
                "map_name": Map.GetMapName(),
                "capture_timestamp": datetime.now().isoformat(),
                "layers": [],
                "blocking_props": [],
            }

            for layer in pathing_maps:
                layer_data = {
                    "zplane": layer.zplane,
                    "trapezoid_count": len(layer.trapezoids),
                    "portal_count": len(layer.portals),
                    "trapezoids": [self._serialize_trapezoid(t) for t in layer.trapezoids],
                    "portals": [self._serialize_portal(p) for p in layer.portals]
                }
                data["layers"].append(layer_data)

            map_ctx = MapContext.get_context()

            # Capture blocking props (collision circles with position + radius)
            blocking_info = "Blocking: N/A"
            if map_ctx:
                blocking_list = map_ctx.blocking_props
                data["blocking_props"] = [
                    {"x": bp.pos.x, "y": bp.pos.y, "radius": bp.radius}
                    for bp in blocking_list
                ]
                blocking_info = f"Blocking: {len(data['blocking_props'])}"

            data["test_points"] = [
                {
                    "name": marker.name,
                    "coords": list(marker.coords),
                    "z_plane": marker.z_plane,
                    "trapezoid_id": marker.trapezoid_id,
                    "notes": marker.notes
                }
                for marker in self.capture_markers
            ]

            maps_filepath = self.maps_dir / f"map_{map_id}.json.gz"
            with gzip.open(maps_filepath, 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            self.last_capture_map_id = map_id
            trap_count = sum(len(layer.trapezoids) for layer in pathing_maps)
            self._set_status(
                f"Saved: {trap_count} traps, {len(pathing_maps)} layers, {blocking_info}",
                is_error=False,
            )

        except Exception as e:
            self._set_status(f"Error: {str(e)}", is_error=True)

    def add_marker_at_player(self) -> None:
        """Add test marker at current player position."""
        try:
            player_x, player_y = Player.GetXY()
            self._add_marker_at_coords(player_x, player_y)
        except Exception as e:
            self._set_status(f"Error adding marker: {str(e)}", is_error=True)

    def delete_marker(self, index: int) -> None:
        """Remove marker by index."""
        if 0 <= index < len(self.capture_markers):
            self.capture_markers.pop(index)
            self._set_status(f"Deleted marker {index}", is_error=False)
            self._save_markers_to_file()

    def clear_markers(self) -> None:
        """Clear all test markers."""
        self.capture_markers.clear()
        self.last_click_normalized = (0.0, 0.0)
        self._set_status("Cleared all markers", is_error=False)
        self._save_markers_to_file()

    def render_markers_3d(self) -> None:
        """Draw 3D markers at marker positions in world."""
        if not self.show_markers_3d or not self.capture_markers:
            return

        overlay = Overlay()
        overlay.BeginDraw()

        for i, marker in enumerate(self.capture_markers):
            x, y = marker.coords

            # Skip if not in FOV
            if not GLOBAL_CACHE.Camera.IsPointInFOV(x, y):
                continue

            z = overlay.FindZ(x, y, marker.z_plane)

            # Color: yellow for valid, red if no trapezoid found
            if marker.trapezoid_id is not None:
                color = Color(255, 255, 0, 200)
            else:
                color = Color(255, 0, 0, 200)

            # Draw filled circle
            overlay.DrawPolyFilled3D(x, y, z, 25, color.to_color(), 16)
            overlay.DrawPoly3D(x, y, z, 28, Color(0, 0, 0, 255).to_color(), 16, 2.0, False)

            # Draw index label
            overlay.DrawText3D(x, y, z - 80, f"{i}", Color(0, 0, 0, 255).to_color(), False, False, 4.0)
            overlay.DrawText3D(x, y, z - 80, f"{i}", Color(255, 255, 255, 255).to_color(), False, False, 3.5)

        overlay.EndDraw()

    def render_markers_on_map(self) -> None:
        """Draw markers on mission map overlay."""
        if not self.show_markers_map or not self.capture_markers:
            return

        if not Map.MissionMap.IsWindowOpen():
            return

        overlay = Overlay()
        overlay.BeginDraw()

        for i, marker in enumerate(self.capture_markers):
            x, y = marker.coords

            # Convert game world coords to mission map screen coords
            screen_x, screen_y = Map.MissionMap.MapProjection.GameMapToScreen(x, y)

            # Color based on trapezoid validity
            if marker.trapezoid_id is not None:
                color = Color(255, 255, 0, 255)  # Yellow
            else:
                color = Color(255, 0, 0, 255)    # Red

            # Draw circle at position
            overlay.DrawPoly(screen_x, screen_y, 8.0, color.to_color(), 16, 2.0)

        overlay.EndDraw()

    def draw_ui(self) -> None:
        """Draw the main UI window."""
        map_id = Map.GetMapID()
        map_name = Map.GetMapName() if map_id else "N/A"

        # Header
        title_color = Color(255, 200, 100, 255)
        ImGui.push_font("Regular", 18)
        PyImGui.text_colored("Pathing Data Dumper", title_color.to_tuple_normalized())
        ImGui.pop_font()
        PyImGui.separator()

        # Map info
        PyImGui.text(f"Map: {map_id} - {map_name}")
        PyImGui.text(f"Markers: {len(self.capture_markers)}")

        # Status message
        if self.status_message:
            PyImGui.text_colored(self.status_message, self.status_color.to_tuple_normalized())

        PyImGui.separator()

        # Capture section
        PyImGui.text_colored("Capture:", title_color.to_tuple_normalized())
        if PyImGui.button("Capture Current Map"):
            self.capture_current_map()

        PyImGui.same_line(0, -1)
        if PyImGui.button("Open Output Folder"):
            import subprocess
            subprocess.Popen(['explorer', str(self.base_dir)])

        PyImGui.separator()

        # Marker controls
        PyImGui.text_colored("Markers:", title_color.to_tuple_normalized())
        PyImGui.text_wrapped("Open mission map (U) and click to place markers, or:")

        if PyImGui.button("Add Marker at Player"):
            self.add_marker_at_player()

        PyImGui.same_line(0, -1)
        if PyImGui.button("Clear All Markers"):
            self.clear_markers()

        # Display options
        self.show_markers_3d = PyImGui.checkbox("Show in 3D World", self.show_markers_3d)
        PyImGui.same_line(0, -1)
        self.show_markers_map = PyImGui.checkbox("Show on Mission Map", self.show_markers_map)

        PyImGui.separator()

        # Marker list
        if self.capture_markers:
            PyImGui.text_colored(f"Marker List ({len(self.capture_markers)}):", title_color.to_tuple_normalized())
            self._draw_marker_table()

    def _draw_marker_table(self) -> None:
        """Draw table of markers with edit/delete buttons."""
        table_flags = (
            PyImGui.TableFlags.Borders |
            PyImGui.TableFlags.RowBg
        )

        if PyImGui.begin_table("##markers", 7, table_flags):
            # Setup columns
            PyImGui.table_setup_column("Idx", PyImGui.TableFlags.NoFlag, 40.0)
            PyImGui.table_setup_column("X", PyImGui.TableFlags.NoFlag, 80.0)
            PyImGui.table_setup_column("Y", PyImGui.TableFlags.NoFlag, 80.0)
            PyImGui.table_setup_column("Z-Plane", PyImGui.TableFlags.NoFlag, 60.0)
            PyImGui.table_setup_column("Trap ID", PyImGui.TableFlags.NoFlag, 70.0)
            PyImGui.table_setup_column("Notes", PyImGui.TableFlags.NoFlag, 150.0)
            PyImGui.table_setup_column("Actions", PyImGui.TableFlags.NoFlag, 70.0)
            PyImGui.table_headers_row()

            # Rows
            to_delete = -1
            for i, marker in enumerate(self.capture_markers):
                PyImGui.table_next_row()

                # Index
                PyImGui.table_set_column_index(0)
                PyImGui.text(str(i))

                # X
                PyImGui.table_set_column_index(1)
                PyImGui.text(f"{marker.coords[0]:.1f}")

                # Y
                PyImGui.table_set_column_index(2)
                PyImGui.text(f"{marker.coords[1]:.1f}")

                # Z-Plane
                PyImGui.table_set_column_index(3)
                PyImGui.text(str(marker.z_plane))

                # Trap ID
                PyImGui.table_set_column_index(4)
                if marker.trapezoid_id is not None:
                    PyImGui.text(str(marker.trapezoid_id))
                else:
                    PyImGui.text_colored("None", (1.0, 0.0, 0.0, 1.0))

                # Notes
                PyImGui.table_set_column_index(5)
                PyImGui.text(marker.notes if marker.notes else "")

                # Actions
                PyImGui.table_set_column_index(6)
                PyImGui.push_id(f"edit_{i}")
                if PyImGui.button("Edit"):
                    self.editing_marker_index = i
                    self.editing_notes_buffer = marker.notes
                    self.show_edit_popup = True
                PyImGui.pop_id()

                PyImGui.same_line(0, 5)

                PyImGui.push_id(f"del_{i}")
                if PyImGui.button("Del"):
                    to_delete = i
                PyImGui.pop_id()

            # Delete after iteration
            if to_delete >= 0:
                self.delete_marker(to_delete)

            PyImGui.end_table()

        # Edit notes popup
        if self.show_edit_popup:
            PyImGui.open_popup("Edit Notes")

        if PyImGui.begin_popup_modal("Edit Notes", True, PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.text("Edit marker notes:")
            self.editing_notes_buffer = PyImGui.input_text("##edit_notes", self.editing_notes_buffer)

            if PyImGui.button("Save"):
                if self.editing_marker_index is not None and 0 <= self.editing_marker_index < len(self.capture_markers):
                    self.capture_markers[self.editing_marker_index].notes = self.editing_notes_buffer
                    self._set_status(f"Updated notes for marker {self.editing_marker_index}", is_error=False)
                    self._save_markers_to_file()
                self.editing_marker_index = None
                self.show_edit_popup = False
                PyImGui.close_current_popup()

            PyImGui.same_line(0, 10)
            if PyImGui.button("Cancel"):
                self.editing_marker_index = None
                self.show_edit_popup = False
                PyImGui.close_current_popup()

            PyImGui.end_popup()

    def _serialize_trapezoid(self, trap) -> dict:
        """Convert PathingTrapezoid to JSON dict."""
        return {
            "id": trap.id,
            "XTL": trap.XTL,
            "XTR": trap.XTR,
            "YT": trap.YT,
            "XBL": trap.XBL,
            "XBR": trap.XBR,
            "YB": trap.YB,
            "neighbor_ids": list(trap.neighbor_ids) if trap.neighbor_ids else [],
            "portal_left": trap.portal_left,
            "portal_right": trap.portal_right
        }

    def _serialize_portal(self, portal) -> dict:
        """Convert Portal to JSON dict."""
        return {
            "left_layer_id": portal.left_layer_id,
            "right_layer_id": portal.right_layer_id,
            "trapezoid_indices": list(portal.trapezoid_indices) if portal.trapezoid_indices else [],
            "pair_index": getattr(portal, 'pair_index', None)
        }

    def _load_markers_from_file(self) -> None:
        """Load markers from existing file if it exists."""
        map_id = Map.GetMapID()
        if not map_id:
            return

        filepath = self.maps_dir / f"map_{map_id}.json.gz"
        if not filepath.exists():
            return

        try:
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                data = json.load(f)

            # Load markers from test_points
            if "test_points" in data:
                self.capture_markers.clear()
                for point in data["test_points"]:
                    marker = MarkerData(
                        coords=tuple(point["coords"]),
                        z_plane=point["z_plane"],
                        trapezoid_id=point.get("trapezoid_id"),
                        notes=point.get("notes", ""),
                        name=point.get("name", f"marker_{len(self.capture_markers)}")
                    )
                    self.capture_markers.append(marker)
                self._set_status(f"Loaded {len(self.capture_markers)} markers", is_error=False)

        except Exception as e:
            self._set_status(f"Failed to load markers: {str(e)}", is_error=True)

    def _save_markers_to_file(self) -> None:
        """Save/update markers in existing capture file or create markers-only file."""
        map_id = Map.GetMapID()
        if not map_id:
            return

        filepath = self.maps_dir / f"map_{map_id}.json.gz"

        try:
            # Try to load existing capture file
            if filepath.exists():
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                # Create minimal structure if no capture exists yet
                data = {
                    "map_id": map_id,
                    "map_name": Map.GetMapName(),
                    "capture_timestamp": datetime.now().isoformat(),
                    "layers": []
                }

            # Update markers
            data["test_points"] = [
                {
                    "name": marker.name,
                    "coords": list(marker.coords),
                    "z_plane": marker.z_plane,
                    "trapezoid_id": marker.trapezoid_id,
                    "notes": marker.notes
                }
                for marker in self.capture_markers
            ]

            # Write back to compressed file
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self._set_status(f"Failed to save markers: {str(e)}", is_error=True)

    def _set_status(self, message: str, is_error: bool = False) -> None:
        """Set status message with color."""
        self.status_message = message
        if is_error:
            self.status_color = Color(255, 100, 100, 255)
        else:
            self.status_color = Color(100, 255, 100, 255)


# Global state
dumper: Optional[PathingDataDumper] = None
initialized = False


def tooltip():
    """Widget tooltip shown in widget manager."""
    PyImGui.begin_tooltip()

    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Pathing Data Dumper", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    PyImGui.text("Capture pathing data and place test markers for offline testing.")
    PyImGui.spacing()

    PyImGui.text_colored("Usage:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Open mission map (U key)")
    PyImGui.bullet_text("Click on map to place test markers")
    PyImGui.bullet_text("Add notes to markers in the table")
    PyImGui.bullet_text("Click 'Capture Current Map' to save")

    PyImGui.spacing()
    PyImGui.text_colored("Output:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Saved to Tests/pathing/dumps/map_{id}.json.gz")

    PyImGui.end_tooltip()


def main():
    """Main widget entry point (called every frame)."""
    global dumper, initialized

    if not initialized:
        if not Routines.Checks.Map.MapValid():
            return

        dumper = PathingDataDumper()
        initialized = True

    if not Map.IsMapReady():
        return

    # Detect map changes before processing clicks
    dumper.check_map_change()

    # Check for mission map clicks
    dumper.update_mission_map_clicks()

    # Draw UI
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        dumper.draw_ui()
        PyImGui.end()

    # Render markers
    dumper.render_markers_3d()
    dumper.render_markers_on_map()


if __name__ == "__main__":
    main()

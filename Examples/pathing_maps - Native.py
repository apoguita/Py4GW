from Py4GWCoreLib import *

module_name = "Pathing Maps"
pathing_map = None
show_map = False
draw_all_layers = False
reverse_y_axis = False

# Global caches for minimap drawing commands
quad_count = 0

class MapBoundaries:
    """
    Class to hold map boundaries.
    """
    def __init__(self, x_min, x_max, y_min, y_max, unk):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.unk = unk

map_boundaries = None


def initialize_map_boundaries(map_boundaries_vector):
    """
    Initialize the global map boundaries from the provided vector.
    """
    global map_boundaries
    if map_boundaries_vector is not None:
        map_boundaries = MapBoundaries(
            x_min=map_boundaries_vector[1],
            y_min=map_boundaries_vector[2],
            x_max=map_boundaries_vector[3],
            y_max=map_boundaries_vector[4],
            unk=map_boundaries_vector[0],  # Any additional data in the vector
        )

initialize_map_boundaries(Map.GetMapBoundaries())

def scale_coords(x, y, width, height, primary_layer_boundaries):
    """
    Scale (x, y) from game coordinates to window coordinates using map and layer boundaries.
    """
    global map_boundaries

    if not map_boundaries:
        raise ValueError("Map boundaries are not initialized.")

    # Layer 0 boundaries for drawing
    x_min, x_max = primary_layer_boundaries["x_min"], primary_layer_boundaries["x_max"]
    y_min, y_max = primary_layer_boundaries["y_min"], primary_layer_boundaries["y_max"]

    scale_x = (x - x_min) / (x_max - x_min) * width
    scale_y = (y - y_min) / (y_max - y_min) * height

    return scale_x, scale_y

precomputed_geometry = {}

def precompute_layer_geometry(pathing_map, width, height):
    global precomputed_geometry, map_boundaries, reverse_y_axis
    global quad_count
    precomputed_geometry.clear()

    if not map_boundaries:
        Py4GW.Console.Log(module_name, "Map boundaries are not initialized.", Py4GW.Console.MessageType.Error)
        return

    # Extract Layer 0 boundaries as primary
    primary_layer = pathing_map[0]  # Layer 0 is used as the base reference
    primary_layer_boundaries = {
        "x_min": min(t.XTL for t in primary_layer.trapezoids),
        "x_max": max(t.XTR for t in primary_layer.trapezoids),
        "y_min": min(t.YB for t in primary_layer.trapezoids),
        "y_max": max(t.YT for t in primary_layer.trapezoids),
    }

    for layer in pathing_map:
        geometry = []
        for trapezoid in layer.trapezoids:
            try:
                tl_x, tl_y = scale_coords(trapezoid.XTL, trapezoid.YT, width, height, primary_layer_boundaries)
                tr_x, tr_y = scale_coords(trapezoid.XTR, trapezoid.YT, width, height, primary_layer_boundaries)
                bl_x, bl_y = scale_coords(trapezoid.XBL, trapezoid.YB, width, height, primary_layer_boundaries)
                br_x, br_y = scale_coords(trapezoid.XBR, trapezoid.YB, width, height, primary_layer_boundaries)
                geometry.append((tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y))
                quad_count += 1
            except Exception as e:
                Py4GW.Console.Log(module_name, f"Error processing trapezoid {trapezoid.id}: {str(e)}", Py4GW.Console.MessageType.Warning)
        precomputed_geometry[layer.zplane] = geometry



def draw_minimap_layer(layer, width=500, height=500):
    """
    Draw the minimap using precomputed geometry aligned with Layer 0 and map boundaries.
    """
    global precomputed_geometry

    if layer.zplane not in precomputed_geometry:
        Py4GW.Console.Log(module_name, f"No precomputed geometry for z-plane {layer.zplane}.", Py4GW.Console.MessageType.Warning)
        return

    PyImGui.set_next_window_size(width, height)
    if PyImGui.begin(f"Minimap (Z-plane: {layer.zplane})", True):
        window_pos = PyImGui.get_window_pos()

        # Render precomputed trapezoids
        for quad in precomputed_geometry[layer.zplane]:
            tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y = quad
            # Offset by window position
            tl_x += window_pos[0]
            tl_y += window_pos[1]
            tr_x += window_pos[0]
            tr_y += window_pos[1]
            bl_x += window_pos[0]
            bl_y += window_pos[1]
            br_x += window_pos[0]
            br_y += window_pos[1]

            PyImGui.draw_list_add_quad_filled(tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y, 0xFFFFFFFF)

        PyImGui.end()


def draw_minimap_layers(layers, width=500, height=500):
    """
    Draw all minimap layers in a single window using precomputed geometry with rounded coordinates.
    """
    global precomputed_geometry, reverse_y_axis

    if not layers or not precomputed_geometry:
        Py4GW.Console.Log(module_name, "No layers or precomputed geometry available for drawing.", Py4GW.Console.MessageType.Warning)
        return

    PyImGui.set_next_window_size(width, height)
    if PyImGui.begin("Minimap", True):
        window_pos = PyImGui.get_window_pos()

        for layer in layers:
            if layer.zplane not in precomputed_geometry:
                Py4GW.Console.Log(module_name, f"No precomputed geometry for z-plane {layer.zplane}.", Py4GW.Console.MessageType.Warning)
                continue

            for quad in precomputed_geometry[layer.zplane]:
                tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y = quad

                # Handle Y-axis flipping if required
                if reverse_y_axis:
                    tl_y, tr_y, br_y, bl_y = height - tl_y, height - tr_y, height - br_y, height - bl_y

                # Offset coordinates by the window position
                tl_x = round(tl_x + window_pos[0])
                tl_y = round(tl_y + window_pos[1])
                tr_x = round(tr_x + window_pos[0])
                tr_y = round(tr_y + window_pos[1])
                bl_x = round(bl_x + window_pos[0])
                bl_y = round(bl_y + window_pos[1])
                br_x = round(br_x + window_pos[0])
                br_y = round(br_y + window_pos[1])

                # Correct vertex order for consistent rendering
                PyImGui.draw_list_add_quad_filled(
                    tl_x, tl_y,  # Top-left
                    tr_x, tr_y,  # Top-right
                    br_x, br_y,  # Bottom-right
                    bl_x, bl_y,  # Bottom-left
                    0xFFFFFFFF
                )

        PyImGui.end()






def log_all_pathing_maps():
    """
    Log all pathing maps and their data to the console.
    """
    global pathing_map
    if pathing_map is None:
        Py4GW.Console.Log(module_name, "No pathing maps to log. Fetch them first.", Py4GW.Console.MessageType.Warning)
        return

    for i, layer in enumerate(pathing_map):
        Py4GW.Console.Log(module_name, f"Layer {i} (Z-plane: {layer.zplane})", Py4GW.Console.MessageType.Info)
        Py4GW.Console.Log(module_name, f"  Trapezoids: {len(layer.trapezoids)}", Py4GW.Console.MessageType.Info)

        for trapezoid in layer.trapezoids:
            Py4GW.Console.Log(
                module_name,
                f"    Trapezoid {trapezoid.id}: "
                f"XTL={trapezoid.XTL}, XTR={trapezoid.XTR}, YT={trapezoid.YT}, "
                f"XBL={trapezoid.XBL}, XBR={trapezoid.XBR}, YB={trapezoid.YB}, "
                f"Portals (left={trapezoid.portal_left}, right={trapezoid.portal_right}), "
                f"Neighbors={trapezoid.neighbor_ids}",
                Py4GW.Console.MessageType.Debug,
            )

        Py4GW.Console.Log(module_name, f"  Portals: {len(layer.portals)}", Py4GW.Console.MessageType.Info)
        for portal in layer.portals:
            Py4GW.Console.Log(
                module_name,
                f"    Portal (left_layer_id={portal.left_layer_id}, right_layer_id={portal.right_layer_id}): "
                f"Trapezoids={portal.trapezoid_indices}, Pair={portal.pair_index}",
                Py4GW.Console.MessageType.Debug,
            )

        Py4GW.Console.Log(module_name, f"  SinkNodes: {len(layer.sink_nodes)}", Py4GW.Console.MessageType.Info)
        for sink_node in layer.sink_nodes:
            Py4GW.Console.Log(
                module_name,
                f"    SinkNode {sink_node.id}: Trapezoid IDs={sink_node.trapezoid_ids}",
                Py4GW.Console.MessageType.Debug,
            )

        Py4GW.Console.Log(module_name, f"  XNodes: {len(layer.x_nodes)}", Py4GW.Console.MessageType.Info)
        for x_node in layer.x_nodes:
            Py4GW.Console.Log(
                module_name,
                f"    XNode {x_node.id}: Position={x_node.pos}, Direction={x_node.dir}, "
                f"Left={x_node.left_id}, Right={x_node.right_id}",
                Py4GW.Console.MessageType.Debug,
            )

        Py4GW.Console.Log(module_name, f"  YNodes: {len(layer.y_nodes)}", Py4GW.Console.MessageType.Info)
        for y_node in layer.y_nodes:
            Py4GW.Console.Log(
                module_name,
                f"    YNode {y_node.id}: Position={y_node.pos}, "
                f"Left={y_node.left_id}, Right={y_node.right_id}",
                Py4GW.Console.MessageType.Debug,
            )

def DrawWindow():
    """
    Main draw function for the GUI window.
    """
    global module_name, pathing_map, show_map, draw_all_layers, reverse_y_axis
    global minimap_draw_cache, thread_manager, map_boundaries, quad_count

    try:
        if PyImGui.begin(module_name):
            PyImGui.text("Pathing Maps Debug Window")
            PyImGui.separator()

            player_z_plane = Agent.GetZPlane(Player.GetAgentID())
            PyImGui.text(f"Player Zplane: {player_z_plane}")
            if map_boundaries is not None:
                PyImGui.text(f"Map Boundaries: {map_boundaries.x_min}, {map_boundaries.x_max}, {map_boundaries.y_min}, {map_boundaries.y_max}")
           
            PyImGui.text(f"Quad Count: {quad_count}")
            PyImGui.separator()

            if PyImGui.button("Get Pathing Maps!"):
                
                pathing_map = Map.Pathing.GetPathingMaps()
                Py4GW.Console.Log(module_name, "Pathing maps acquired!", Py4GW.Console.MessageType.Success)
                precompute_layer_geometry(pathing_map, width=500, height=500)
                Py4GW.Console.Log(module_name, "Pathing maps precomputed!", Py4GW.Console.MessageType.Success)


            if pathing_map is not None:

                show_map = PyImGui.checkbox("Show Minimap", show_map)
                draw_all_layers = PyImGui.checkbox("Show All Layers", draw_all_layers)
                reverse_y_axis = PyImGui.checkbox("Reverse Y-Axis", reverse_y_axis)

                if show_map:
                    if draw_all_layers:
                        draw_minimap_layers(pathing_map)
                    else:
                        zplane = Agent.GetZPlane(Player.GetAgentID())
                        if zplane < len(pathing_map):
                            draw_minimap_layer(pathing_map[zplane])
                        else:
                            Py4GW.Console.Log(
                                module_name, f"No corresponding layer found for z-plane {zplane}.",
                                Py4GW.Console.MessageType.Warning,
                            )
            
                if PyImGui.button("Log All Pathing Maps"):
                    log_all_pathing_maps()

            PyImGui.separator()
            PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def main():
    global module_name
    try:
        DrawWindow()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
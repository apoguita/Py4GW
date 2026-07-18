import pygame

from Py4GWCoreLib import *

module_name = "Pathing Maps"
pathing_map = None
show_map = False
draw_all_layers = False
reverse_y_axis = False

# Global variables for drawing
quad_count = 0
precomputed_geometry = {}
map_boundaries = None
screen = None
pygame_initialized = False
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

def initialize_pygame():
    """Initialize Pygame and set up the drawing surface."""
    global pygame_initialized, screen
    if not pygame_initialized:
        pygame.init()
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Pathing Maps Minimap")
        pygame_initialized = True

def shutdown_pygame():
    """Shut down Pygame and release resources."""
    global pygame_initialized
    if pygame_initialized:
        pygame.quit()
        pygame_initialized = False


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
    """Scale (x, y) from game coordinates to window coordinates using layer boundaries."""
    global reverse_y_axis

    x_min, x_max = primary_layer_boundaries["x_min"], primary_layer_boundaries["x_max"]
    y_min, y_max = primary_layer_boundaries["y_min"], primary_layer_boundaries["y_max"]

    scale_x = (x - x_min) / (x_max - x_min) * width
    scale_y = (y - y_min) / (y_max - y_min) * height

    return scale_x, scale_y


precomputed_geometry = {}

def precompute_layer_geometry(pathing_map, width, height):
    """Precompute geometry for all layers in the pathing map using map boundaries."""
    global precomputed_geometry, map_boundaries
    precomputed_geometry.clear()

    if not map_boundaries:
        Py4GW.Console.Log(module_name, "Map boundaries are not initialized.", Py4GW.Console.MessageType.Error)
        return

    # Use Layer 0 as primary reference
    primary_layer = pathing_map[0]
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
                geometry.append([(tl_x, tl_y), (tr_x, tr_y), (br_x, br_y), (bl_x, bl_y)])
            except Exception as e:
                Py4GW.Console.Log(module_name, f"Error processing trapezoid {trapezoid.id}: {str(e)}", Py4GW.Console.MessageType.Warning)
        precomputed_geometry[layer.zplane] = geometry





def draw_minimap_layers(layers, width, height):
    """Draw layers onto the Pygame surface."""
    global precomputed_geometry, screen

    if not layers or not precomputed_geometry:
        Py4GW.Console.Log(module_name, "No layers or precomputed geometry available for drawing.", Py4GW.Console.MessageType.Warning)
        return

    #screen.fill((0, 0, 0))  # Clear screen
    for layer in layers:
        if layer.zplane not in precomputed_geometry:
            Py4GW.Console.Log(module_name, f"No geometry for z-plane {layer.zplane}. Skipping layer.", Py4GW.Console.MessageType.Warning)
            continue

        for quad in precomputed_geometry[layer.zplane]:
            if len(quad) != 4:  # Ensure quad is properly formatted
                Py4GW.Console.Log(module_name, "Invalid quad data detected. Skipping.", Py4GW.Console.MessageType.Warning)
                continue

            pygame.draw.polygon(
                screen,
                (255, 255, 255),
                [(int(p[0]), int(p[1])) for p in quad],  # Ensure integer coordinates
            )
    pygame.display.flip()  # Update the display




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
    global map_boundaries

    try:
        # Ensure Pygame is initialized before any rendering
        
        if PyImGui.begin(module_name):
            PyImGui.text("Pathing Maps Debug Window")
            PyImGui.separator()

            # Display player Z-plane and map boundaries
            player_z_plane = Agent.GetZPlane(Player.GetAgentID())
            PyImGui.text(f"Player Zplane: {player_z_plane}")
            if map_boundaries is not None:
                PyImGui.text(f"Map Boundaries: {map_boundaries.x_min}, {map_boundaries.x_max}, {map_boundaries.y_min}, {map_boundaries.y_max}")
            PyImGui.separator()

            # Fetch and precompute pathing maps
            if PyImGui.button("Get Pathing Maps!"):
                try:
                    pathing_map = Map.Pathing.GetPathingMaps()
                    Py4GW.Console.Log(module_name, "Pathing maps acquired!", Py4GW.Console.MessageType.Success)
                    if pathing_map:
                        precompute_layer_geometry(pathing_map, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
                        Py4GW.Console.Log(module_name, "Pathing maps precomputed!", Py4GW.Console.MessageType.Success)
                        show_map = True
                    else:
                        Py4GW.Console.Log(module_name, "No pathing maps returned.", Py4GW.Console.MessageType.Warning)
                except Exception as e:
                    Py4GW.Console.Log(module_name, f"Error fetching or precomputing pathing maps: {str(e)}", Py4GW.Console.MessageType.Error)

            # Display and handle rendering options
            if pathing_map:
                show_map = PyImGui.checkbox("Show Minimap", show_map)
                reverse_y_axis = PyImGui.checkbox("Reverse Y-Axis", reverse_y_axis)

                # Render minimap if enabled
                if show_map:
                    try:
                        if not pygame_initialized:
                            initialize_pygame()
                        draw_minimap_layers(pathing_map, WINDOW_WIDTH, WINDOW_HEIGHT)
                    except Exception as e:
                        Py4GW.Console.Log(module_name, f"Error drawing minimap: {str(e)}", Py4GW.Console.MessageType.Error)
                else:
                    if pygame_initialized:
                        shutdown_pygame()


                # Log all pathing maps
                if PyImGui.button("Log All Pathing Maps"):
                    try:
                        log_all_pathing_maps()
                    except Exception as e:
                        Py4GW.Console.Log(module_name, f"Error logging pathing maps: {str(e)}", Py4GW.Console.MessageType.Error)

            PyImGui.separator()
            PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


def main():
    global module_name
    try:
        DrawWindow()
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
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()

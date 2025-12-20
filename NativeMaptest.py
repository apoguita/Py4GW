import PyImGui
from Py4GWCoreLib.native_src.internals.gw_array import GW_Array_View
from Py4GWCoreLib.native_src.context.GameplayContext import (GameplayContextStruct,GameplayContext)
from Py4GWCoreLib.native_src.context.WorldMapContext import (WorldMapContext, WorldMapContextStruct)
from Py4GWCoreLib.native_src.context.MissionMapContext import (MissionMapContext, MissionMapContextStruct,MissionMapSubContext)

def draw_window():
    if PyImGui.begin("Native Map Tester", True, PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.collapsing_header("World Map Context"): 
            world_map_ptr:WorldMapContextStruct | None = WorldMapContext.get_context()
            if not world_map_ptr:
                PyImGui.text("WorldMapContext not available.")
            else:
                PyImGui.text(f"frame_id: {world_map_ptr.frame_id}")
                PyImGui.text(f"h0004: {world_map_ptr.h0004}")
                PyImGui.text(f"h0008: {world_map_ptr.h0008}")
                PyImGui.text(f"h000c: {world_map_ptr.h000c}")
                PyImGui.text(f"h0010: {world_map_ptr.h0010}")
                PyImGui.text(f"h0014: {world_map_ptr.h0014}")
                PyImGui.text(f"h0018: {world_map_ptr.h0018}")
                PyImGui.text(f"h001c: {world_map_ptr.h001c}")
                PyImGui.text(f"h0020: {world_map_ptr.h0020}")
                PyImGui.text(f"h0024: {world_map_ptr.h0024}")
                PyImGui.text(f"h0028: {world_map_ptr.h0028}")
                PyImGui.text(f"h002c: {world_map_ptr.h002c}")
                PyImGui.text(f"h0030: {world_map_ptr.h0030}")
                PyImGui.text(f"h0034: {world_map_ptr.h0034}")
                
                PyImGui.text(f"zoom: {world_map_ptr.zoom}")
                PyImGui.text(f"top_left: ({world_map_ptr.top_left.x}, {world_map_ptr.top_left.y})")
                PyImGui.text(f"bottom_right: ({world_map_ptr.bottom_right.x}, {world_map_ptr.bottom_right.y})")
                PyImGui.text(f"h004c: {list(world_map_ptr.h004c)}")
                PyImGui.text(f"h0068: {world_map_ptr.h0068}")
                PyImGui.text(f"h006c: {world_map_ptr.h006c}")
                PyImGui.text(f"params: {list(world_map_ptr.params)}")
        if PyImGui.collapsing_header("Mission Map Context"):
            mission_map_ptr:MissionMapContextStruct | None = MissionMapContext.get_context()
            if not mission_map_ptr:
                PyImGui.text("MissionMapContext not available.")
            else:
                PyImGui.text(f"size: {mission_map_ptr.size.x} x {mission_map_ptr.size.y}")
                PyImGui.text(f"h0008: {mission_map_ptr.h0008}")
                PyImGui.text(f"last_mouse_location: ({mission_map_ptr.last_mouse_location.x}, {mission_map_ptr.last_mouse_location.y})")
                PyImGui.text(f"frame_id: {mission_map_ptr.frame_id}")
                PyImGui.text(f"player_mission_map_pos: ({mission_map_ptr.player_mission_map_pos.x}, {mission_map_ptr.player_mission_map_pos.y})")
                subcontexts = GW_Array_View(mission_map_ptr.h0020, MissionMapSubContext)
                items = subcontexts.to_list()
                if PyImGui.collapsing_header(f"Mission Map Subcontexts ({len(items)})"):
                    for i, sc in enumerate(items):
                        PyImGui.text(f"Subcontext {i}: h0000[0]={sc.h0000[0]}")
                PyImGui.text(f"h0030: {mission_map_ptr.h0030}")
                PyImGui.text(f"h0034: {mission_map_ptr.h0034}")
                PyImGui.text(f"h0038: {mission_map_ptr.h0038}")
                # MissionMapSubContext2*
                sub2_ptr = mission_map_ptr.h003c
                if not sub2_ptr:
                    PyImGui.text("MissionMapSubContext2 not available.")
                else:
                    #sub2 = sub2_ptr.contents
                    PyImGui.text(f"h0000: {sub2_ptr.contents.h0000}")
                    PyImGui.text(f"player_mission_map_pos: ({sub2_ptr.contents.player_mission_map_pos.x}, {sub2_ptr.contents.player_mission_map_pos.y})")
                    PyImGui.text(f"h000c: {sub2_ptr.contents.h000c}")
                    PyImGui.text(f"mission_map_size: ({sub2_ptr.contents.mission_map_size.x}, {sub2_ptr.contents.mission_map_size.y})")
                    PyImGui.text(f"unk: {sub2_ptr.contents.unk}")
                    PyImGui.text(f"mission_map_pan_offset: ({sub2_ptr.contents.mission_map_pan_offset.x}, {sub2_ptr.contents.mission_map_pan_offset.y})")
                    PyImGui.text(f"mission_map_pan_offset2: ({sub2_ptr.contents.mission_map_pan_offset2.x}, {sub2_ptr.contents.mission_map_pan_offset2.y})")
                    PyImGui.text(f"unk2: {list(sub2_ptr.contents.unk2)}")
                    PyImGui.text(f"unk3: {list(sub2_ptr.contents.unk3)}")
                PyImGui.text(f"h0040: {mission_map_ptr.h0040}")
                PyImGui.text(f"h0044: {mission_map_ptr.h0044}")
        if PyImGui.collapsing_header("Gameplay Context"):
            gameplay_ctx: GameplayContextStruct | None = GameplayContext.get_context()
            if not gameplay_ctx:
                PyImGui.text("GameplayContext not available.")
            else:
                # h0000 array
                h0000 = gameplay_ctx.h0000
                for i, value in enumerate(h0000):
                    PyImGui.text(f"h0000[{i}]: {value}")

                PyImGui.separator()

                # mission_map_zoom
                PyImGui.text(f"mission_map_zoom: {gameplay_ctx.mission_map_zoom}")

                PyImGui.separator()

                # unk array
                unk = gameplay_ctx.unk
                for i, value in enumerate(unk):
                    PyImGui.text(f"unk[{i}]: {value}")


                    



        
    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()

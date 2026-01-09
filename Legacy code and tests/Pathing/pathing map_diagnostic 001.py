import Py4GW
from Py4GWCoreLib import *
from typing import List, Tuple, Dict
import math

MODULE_NAME = "NavMesh Diagnostics"

Point2D = Tuple[float, float]
PathingTrapezoid = PyPathing.PathingTrapezoid



def print_trapezoid_info():

    pathing_maps = Map.Pathing.GetPathingMaps()

    traps_per_zplane = defaultdict(list)
    trap_to_zplane = {}
    portal_count = 0
    cross_z_links = 0
    broken_portals = 0
    paired_portals = 0


    print("[DIAG] Loaded", len(pathing_maps), "zplane layers")

    # Step 1: Collect all traps and map to their zplane
    for layer in pathing_maps:
        zplane = layer.zplane
        for trap in layer.trapezoids:
            traps_per_zplane[zplane].append(trap.id)
            trap_to_zplane[trap.id] = zplane

    print("[DIAG] == LAYER USAGE ==")
    for z, traps in traps_per_zplane.items():
        print(f"Zplane {z}: {len(traps)} trapezoids")

    # Step 2: Inspect portals
    print("[DIAG] == PORTAL ANALYSIS ==")
    for layer in pathing_maps:
        for portal in layer.portals:
            portal_count += 1
            traps = portal.trapezoid_indices

            # Expect exactly 2 trapezoids
            if len(traps) != 2:
                print(f"Portal {portal_count} invalid trap count: {len(traps)}")
                broken_portals += 1
                continue

            trap1, trap2 = traps
            z1 = trap_to_zplane.get(trap1, None)
            z2 = trap_to_zplane.get(trap2, None)

            expected_zs = (portal.left_layer_id, portal.right_layer_id)

            # Verify both traps are from correct zplanes
            match1 = z1 in expected_zs
            match2 = z2 in expected_zs

            if match1 and match2:
                if z1 != z2:
                    cross_z_links += 1
                paired_portals += 1
            else:
                broken_portals += 1
                print(f"[MISMATCH] Portal #{portal_count} | Traps: {trap1}@{z1}, {trap2}@{z2} | Expected Zs: {expected_zs}")

    print("[DIAG] == STATS ==")
    print(f"Total portals: {portal_count}")
    print(f"Paired portals: {paired_portals}")
    print(f"Cross-zplane links: {cross_z_links}")
    print(f"Broken/mismatched portals: {broken_portals}")


from Py4GWCoreLib import Map
from collections import defaultdict

def main():
    
    # Optional GUI window
    if PyImGui.begin("NavMesh Portal Debug"):
        if PyImGui.button("Print Trapezoid Info"):
            print_trapezoid_info()
    PyImGui.end()

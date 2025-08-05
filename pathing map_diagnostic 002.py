import Py4GW
from Py4GWCoreLib import *
from typing import List, Tuple, Dict
import math

from Py4GWCoreLib import DXOverlay, Map
from typing import Tuple

Vec2f = Tuple[float, float]
Z_INVALID = 0xFFFFFFFF

def FindZ(x: float, y: float) -> int:
    return int(DXOverlay.FindZ(x, y))

def debug_pathing_map_structure():
    pathing_layers = Map.Pathing.GetPathingMaps()
    all_trapezoids = {}
    z_to_traps = {}
    trap_to_z = {}
    duplicate_traps = {}

    print("[DIAG] === TRAPEZOID → Z-PLANE ASSIGNMENT ===")

    for z, layer in enumerate(pathing_layers):
        z_to_traps[z] = set()
        for trap in layer.trapezoids:
            all_trapezoids[trap.id] = trap
            trap_to_z[trap.id] = z
            z_to_traps[z].add(trap.id)
            print(f"Trap {trap.id} assigned to Z={z}")

    # Detect duplicates
    print("\n[DIAG] === DUPLICATE TRAPEZOIDS ACROSS LAYERS ===")
    seen = {}
    for z, traps in z_to_traps.items():
        for tid in traps:
            if tid in seen:
                print(f"[DUPLICATE] Trapezoid {tid} exists in Z={seen[tid]} and Z={z}")
                duplicate_traps[tid] = (seen[tid], z)
            else:
                seen[tid] = z

    # Analyze portals
    print("\n[DIAG] === PORTAL Z-LAYER LINK CHECK ===")
    mismatch_count = 0
    total_portals = 0

    for z, layer in enumerate(pathing_layers):
        for portal in layer.portals:
            total_portals += 1
            tids = portal.trapezoid_indices
            if len(tids) != 2:
                print(f"[INVALID] Portal #{total_portals} has {len(tids)} trapezoids: {tids}")
                continue

            t1, t2 = tids
            z1 = trap_to_z.get(t1, Z_INVALID)
            z2 = trap_to_z.get(t2, Z_INVALID)

            mismatch = z1 == z2 or Z_INVALID in (z1, z2)

            if mismatch:
                mismatch_count += 1
                print(f"[MISMATCH] Portal #{total_portals} | Traps: {t1}@{z1}, {t2}@{z2}")
            else:
                print(f"[OK] Portal #{total_portals} | Traps: {t1}@{z1}, {t2}@{z2}")

    print("\n[DIAG] === STATS ===")
    print(f"Total z-layers: {len(pathing_layers)}")
    print(f"Total trapezoids: {len(all_trapezoids)}")
    print(f"Duplicate trapezoids: {len(duplicate_traps)}")
    print(f"Total portals: {total_portals}")
    print(f"Mismatched portals: {mismatch_count}")
    print(f"Valid cross-z-plane links: {total_portals - mismatch_count}")

def main():
    
    # Optional GUI window
    if PyImGui.begin("NavMesh Portal Debug"):
        if PyImGui.button("Print Trapezoid Info"):
            debug_pathing_map_structure()
    PyImGui.end()

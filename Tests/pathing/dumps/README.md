# Pathing Dump Schema

Gzipped JSON files (`map_*.json.gz`) captured by the Pathing Data Dumper widget.

```jsonc
{
  "map_id": 558,              // GW map hash
  "map_name": "Some Area",
  "layers": [
    {
      "trapezoids": [
        {
          "id": 0,
          "XTL": 0.0, "XTR": 100.0, "YT": 200.0,   // top edge
          "XBL": 0.0, "XBR": 100.0, "YB": 100.0,   // bottom edge
          "neighbor_ids": [1, 2],
          "portal_left": 0,    // portal struct index (0 = none)
          "portal_right": 0
        }
      ],
      "portals": [
        {
          "layer_index": 0,
          "left_layer_id": 0,
          "right_layer_id": 1,
          "trapezoid_indices": [42, 43],
          "pair_index": 3
        }
      ]
    }
  ],
  "test_points": [
    {
      "name": "gate_entrance",
      "coords": [1234.5, 6789.0],
      "z_plane": 0,
      "trapezoid_id": 42,
      "notes": ""               // optional
    }
  ],
  "blocking_props": [
    { "x": 100.0, "y": 200.0, "radius": 50.0 }
  ]
}
```

- **layers** — one per z-plane. Each contains trapezoids (walkable geometry) and portals (cross-layer connections).
- **trapezoids** — axis-aligned-ish quadrilaterals. Top edge `(XTL,YT)-(XTR,YT)`, bottom edge `(XBL,YB)-(XBR,YB)`. `YT >= YB` normally, but inverted coords exist in real data. `neighbor_ids` come directly from game memory.
- **portals** — connect trapezoids across layers (e.g. bridges, stairs). `left/right_layer_id` identify the two layers; `trapezoid_indices` are the trap IDs involved.
- **test_points** — manually placed markers with known trap IDs, used for pathfinding validation.
- **blocking_props** — collision circles from `MapStaticData`. Used for pathfinding obstacle avoidance, not yet integrated into tests.

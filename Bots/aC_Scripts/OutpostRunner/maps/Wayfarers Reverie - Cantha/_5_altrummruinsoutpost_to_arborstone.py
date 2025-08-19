from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_5_altrummruinsoutpost_to_arborstone_ids = {
    "outpost_id": 272,
}

# 2) Outpost exit path
_5_altrummruinsoutpost_to_arborstone_outpost_path = [
    (4570, 6344),
    (5568, 6659),
    (6329, 7421),
]

# 3) Segments
_5_altrummruinsoutpost_to_arborstone_segments = [
    {
        "map_id": 244,
        "path": [
            (9552, -19769),
            (10603, -18041),
            (10311, -16016),
            (8929, -14551),
            (7484, -13122),
            (6047, -11701),
            (4691, -10136),
            (3381, -8538),
        ],
    },
    {
        "map_id": 244,
        "path": [],  # no further walking once you arrive
    },
]

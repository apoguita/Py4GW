from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_2_sifhalla_to_drakkarlake_ids = {
    "outpost_id": 643,
}

# 2) Outpost exit path
_2_sifhalla_to_drakkarlake_outpost_path = [
    (11055, 23616),
    (10010, 23761),
    (9400, 23841),
]

# 3) Segments
_2_sifhalla_to_drakkarlake_segments = [
    {
        "map_id": 513,
        "path": [
            (13588.061523, 18813.888672),
            (13873.824219, 14656.845703),
            (14312.882812, 10549.458984),
            (13637.276367,  6380.870117),
            (13246.373047,  3795.225098),
            (10406.242188,   566.432251),
            ( 7413.555664, -1949.163208),
            ( 3217.478516, -4939.254395),
            ( 2438.613037, -6341.578125),
        ],
    },
    {
        "map_id": 513,
        "path": [],  # no further walking once you arrive
    },
]

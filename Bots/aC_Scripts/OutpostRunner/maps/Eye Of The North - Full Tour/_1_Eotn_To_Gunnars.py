from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id
# 1) IDs
_1_eotn_to_gunnars_ids = {
    "outpost_id": 642,
}

# 2) Outpost exit path (in map 642)
_1_eotn_to_gunnars_outpost_path = [
    (-1814, 2917),
    (-964, 2270),
    (-115, 1677),
    (718, 1060),
    (1522, 464),
]

# 3) Segments  
_1_eotn_to_gunnars_segments = [
    {
        # “Ice Cliff Chasms” explorable
        "map_id": 499,
        "path": [
            (2233, 77),
            (2586, 2100),
            (2547, 4173),
            (2588, 6226),
            (1481, 7941),
            (498, 9692),
            (661, 11769),
            (1021, 13809),
            (800, 15865),
            (465, 17890),
            (375, 19935),
            (-912, 21480),
            (-1995, 23186),
            (-2682, 25118),
            (-3591, 26974),
            (-4031, 27872),
        ],
    },
    {
        # “Norrhart Domains” explorable
        "map_id": 548,
        "path": [
            (11007, -13090),
            (12261, -11439),
            (11975, -9409),
            (11775, -7333),
            (13639, -6465),
            (14546, -6043),
            (15578, -6548),
        ],
    },
    {
        # “Gunnar’s Hold” explorable
        "map_id": 644,
        "path": [],  # no further walking once you arrive
    },
]

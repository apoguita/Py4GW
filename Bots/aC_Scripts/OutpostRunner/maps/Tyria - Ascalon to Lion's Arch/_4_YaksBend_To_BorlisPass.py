from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_4_yaksbend_to_borlispass_ids = {
    "outpost_id": outpost_name_to_id["Yaks Bend"],
}

# 2) Outpost exit path (inside Yak's Bend)
_4_yaksbend_to_borlispass_outpost_path = [
    (9295, 4145),
    (9280, 4050),
]

# 3) Segments 
_4_yaksbend_to_borlispass_segments = [
    {
        "map_id": explorable_name_to_id["Traveler's Vale"],
        "path": [
            (8815.0, 2563.0),
            (8245.0, -696.0),
            (7710.0, -1050.0),
            (6752.0, -1858.0),
            (5425.0, -2008.0),
            (3188, -4312),
            (2502, -7419),
            (1173, -11150),
            (-2162, -13016),
            (-5355, -12534),
            (-7880, -11869),
            (-10046, -8700),
            (-11000, -8460),
        ],
    },
    {
        "map_id": outpost_name_to_id["Borlis Pass outpost"],
        "path": [],
    },
]

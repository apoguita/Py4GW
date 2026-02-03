from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_4_beetletun_to_divinitycoast_ids = {
    "outpost_id": outpost_name_to_id["Beetletun"],
}

# 2) Outpost exit path
_4_beetletun_to_divinitycoast_outpost_path = [
    (17636, -10144),
    (17425, -9933),
]

# 3) Segments
_4_beetletun_to_divinitycoast_segments = [
    {
        "map_id": explorable_name_to_id["Watchtower Coast"],
        "path": [
            (14746.0, -6604.0),
            (12251.0, -4646.0),
            (11135.0, -5199.0),
            (9601.0, -6899.0),
            (8706.0, -8150.0),
            (7916.0, -8420.0),
            (5919.0, -7917.0),
            (4496.0, -8905.0),
            (3166.0, -10389.0),
            (117.0, -11503.0),
            (-1586.0, -11038.0),
            (-4018.0, -11049.0),
            (-5579.0, -10439.0),
            (-7538.0, -9364.0),
            (-10201.0, -8409.0),
            (-12212.0, -7788.0),
            (-13452.0, -8024.0),
            (-14585.0, -8548.0),
            (-17348.0, -9023.0),
            (-18293.0, -9190.0),
            (-19195.0, -10063.0),
            (-20032.0, -10697.0),
            (-21734.0, -10735.0),
            (-21965.0, -10622.0)
        ],
    },
    {
        "map_id": outpost_name_to_id["Divinity Coast outpost"],
        "path": [],  # no further walking once you arrive
    },
]

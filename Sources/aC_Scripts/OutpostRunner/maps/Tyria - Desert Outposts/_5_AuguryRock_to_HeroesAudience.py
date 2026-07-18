from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_5_auguryrock_to_heroesaudience_ids = {
    "outpost_id": outpost_name_to_id["Augury Rock outpost"],
}

# 2) Outpost exit path
_5_auguryrock_to_heroesaudience_outpost_path = [
    (-17223, -1165),
    (-19166, -393),
    (-20105, -377),
]

# 3) Segments
_5_auguryrock_to_heroesaudience_segments = [
    {
        "map_id": explorable_name_to_id["Prophet's Path"],
        "path": [
            (19314, -374),
            (18883, 1588),
            (16880, 1294),
            (15102, 341),
            (13380, -755),
            (11801, -2046),
            (10730, -3802),
            (9605, -5485),
            (8608, -7256),
            (6761, -8094),
            (4804, -8706),
            (2871, -9388),
            (959, -10085),
            (-1005, -10721),
            (-2961, -11253),
            (-4914, -11729),
            (-6885, -12294),
            (-8883, -12797),
            (-10835, -13322),
            (-12801, -13873),
            (-14745, -14455),
            (-15360, -14677),
        ],
    },
    {
        "map_id": outpost_name_to_id["Heroes Audience"],
        "path": [],  # no further walking once you arrive
    },
]

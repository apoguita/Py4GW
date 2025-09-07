from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_6_heroesaudience_to_dunesofdespair_ids = {
    "outpost_id": outpost_name_to_id["Heroes Audience"],
}

# 2) Outpost exit path
_6_heroesaudience_to_dunesofdespair_outpost_path = [
    (-15762, -15166),
    (-14902, -14435),
]

# 3) Segments
_6_heroesaudience_to_dunesofdespair_segments = [
    {
        "map_id": explorable_name_to_id["Prophet's Path"],
        "path": [
            (-14661, -14372),
            (-12676, -14117),
            (-10664, -13674),
            (-8683, -13205),
            (-6638, -13313),
            (-4967, -14517),
            (-4118, -16391),
            (-3374, -18263),
            (-1411, -18725),
            (646, -18713),
            (1646, -18707),
            (1286, -19523),
            (1314, -20022),
        ],
    },
    {
        "map_id": explorable_name_to_id["Vulture Drifts"],
        "path": [
            (-7912, 19442),
            (-6246, 18294),
            (-4328, 17686),
            (-3457, 15841),
            (-3670, 13818),
            (-3650, 11796),
            (-2822, 9955),
            (-985, 9076),
            (1026, 9123),
            (2275, 7528),
            (2816, 5580),
            (3070, 3579),
            (2920, 1542),
            (2525, -432),
            (2373, -2471),
            (2016, -4467),
            (57, -5016),
            (-1975, -4645),
            (-1596, -6633),
            (78, -7787),
            (688, -9743),
            (-29, -11645),
            (-1380, -13185),
            (-3064, -14288),
            (-4826, -13297),
            (-4833, -12563),
            (-4564, -11973),
        ],
    },
    {
        "map_id": outpost_name_to_id["Dunes of Despair outpost"],
        "path": [],  # no further walking once you arrive
    },
]

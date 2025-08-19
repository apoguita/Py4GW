from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_8_themouthoftorment_to_crystaloverlook_ids = {
    "outpost_id": 440,
}

# 2) Outpost exit path
_8_themouthoftorment_to_crystaloverlook_outpost_path = [
    (-984, -5223),
    (-1956, -5530),
    (-2938, -5827),
    (-3912, -6161),
    (-4889, -6540),
    (-5822, -6901),
]

# 3) Segments
_8_themouthoftorment_to_crystaloverlook_segments = [
    {
        "map_id": 439,
        "path": [
            (-5013, -6571),
            (-6915, -5733),
            (-8250, -4242),
            (-9941, -3123),
            (-11993, -2979),
            (-13765, -2022),
            (-15272, -698),
            (-16608, 883),
            (-18511, 1668),
            (-19436, 2050),
        ],
    },
    {
        "map_id": 448,
        "path": [
            (13233.972656, 21073.199219),
            (11546.242188, 18832.789062),
            (10527.395508, 17061.298828),
            (8690.286133, 13467.123047),
            (5965.479492, 11260.658203),
            (1879.476074, 10375.625000),
            (-746.290344, 9523.731445),
            (-1876.130127, 7971.493164),
            (-7916.277832, 6807.095215),
            (-9847.409180, 8500.535156),
            (-10749.522461, 10543.705078),
        ],
    },
    {
        "map_id": 448,
        "path": [],  # no further walking once you arrive
    },
]

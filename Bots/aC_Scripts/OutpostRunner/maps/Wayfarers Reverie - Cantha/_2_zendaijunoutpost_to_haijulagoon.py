from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_2_zendaijunoutpost_to_haijulagoon_ids = {
    "outpost_id": 213,
}

# 2) Outpost exit path
_2_zendaijunoutpost_to_haijulagoon_outpost_path = [
    (18255, 11594),
    (18729, 12534),
    (18982, 13543),
    (19225, 14513),
]

# 3) Segments
_2_zendaijunoutpost_to_haijulagoon_segments = [
    {
        "map_id": 237,
        "path": [
            (17409, -20918),
            (15890, -19609),
            (14056, -18715),
            (12299, -17686),
            (10566, -16653),
            (8661, -15885),
            (7427, -14250),
            (6022, -12764),
            (4572, -11365),
            (4216, -9359),
            (4289, -7332),
            (4521, -5315),
            (4021, -3326),
            (3328, -1389),
            (2479, 462),
            (1516, 2294),
            (-135, 3511),
            (-1764, 4721),
            (-3186, 6184),
        ],
    },
    {
        "map_id": 237,
        "path": [],  # no further walking once you arrive
    },
]

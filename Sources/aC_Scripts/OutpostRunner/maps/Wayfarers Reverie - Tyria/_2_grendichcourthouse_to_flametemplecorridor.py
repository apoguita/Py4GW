from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_2_grendichcourthouse_to_flametemplecorridor_ids = {
    "outpost_id": 36,
}

# 2) Outpost exit path
_2_grendichcourthouse_to_flametemplecorridor_outpost_path = [
    (435, 13591),
    (1421, 13852),
    (2387, 14107),
]

# 3) Segments
_2_grendichcourthouse_to_flametemplecorridor_segments = [
    {
        "map_id": 13,
        "path": [
            (3093, 13016),
            (3975, 14840),
            (5899, 15621),
            (7901, 15751),
            (9853, 16354),
            (12059, 16449),
            (14034, 15833),
            (14783, 13898),
            (16783, 14361),
            (18593, 15244),
            (20618, 15437),
            (21090, 15575),
            (21318, 17657),
        ],
    },
    {
        "map_id": 106,
        "path": [
            (-18633, -12862),
            (-18547, -10814),
            (-19683, -9083),
            (-18490, -7450),
            (-16862, -6266),
            (-15242, -7483),
            (-13520, -8571),
            (-11501, -8622),
            (-9451, -8512),
            (-7872, -7263),
            (-7452, -5251),
            (-6756, -3350),
            (-6296, -2653),
        ],
    },
    {
        "map_id": 106,
        "path": [],  # no further walking once you arrive
    },
]

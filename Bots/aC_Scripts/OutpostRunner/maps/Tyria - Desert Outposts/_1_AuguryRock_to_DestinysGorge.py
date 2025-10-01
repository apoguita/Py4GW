from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_1_auguryrock_to_destinysgorge_ids = {
    "outpost_id": outpost_name_to_id["Augury Rock outpost"],
}

# 2) Outpost exit path
_1_auguryrock_to_destinysgorge_outpost_path = [
    (-15239, 1001),
    (-15208, 2489),
]

# 3) Segments
_1_auguryrock_to_destinysgorge_segments = [
    {
        "map_id": explorable_name_to_id["Skyward Reach"],
        "path": [
            (-15096, 3695),
            (-13326, 4746),
            (-11474, 5518),
            (-9618, 6333),
            (-7784, 7184),
            (-5753, 7478),
            (-3751, 7506),
            (-1708, 7550),
            (326, 7584),
            (2372, 7713),
            (4408, 7822),
            (6433, 7990),
            (8443, 8212),
            (10101, 9347),
            (12027, 10625),
            (12843, 12299),
            (13942, 14007),
            (15040, 15706),
            (16178, 17390),
            (17536, 18864),
            (19179, 19599),
            (19750, 19475),
        ],
    },
    {
        "map_id": outpost_name_to_id["Destinys Gorge"],
        "path": [],  # no further walking once you arrive
    },
]

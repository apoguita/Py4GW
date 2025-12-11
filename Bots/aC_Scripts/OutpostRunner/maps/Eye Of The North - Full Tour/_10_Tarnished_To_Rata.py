# maps/EOTN/_10_tarnished_to_rata.py

# 1) IDs
_10_tarnished_to_rata_ids = {
    "outpost_id": 641,  # outpost_name_to_id["Tarnished Haven"]
}

# 2) Exit path from Tarnished Haven (map 641)
_10_tarnished_to_rata_outpost_path = [
    (22425, -12046),  # move toward Alcazia entrance
    (19089, -10621),  # closer to segment start
]

# 3) Explorable segments
_10_tarnished_to_rata_segments = [
    {
        # Alcazia Tangle
        "map_id": 572,  # explorable_name_to_id["Alcazia Tangle"]
        "path": [
            (18184.322265, -7412.855957),
            (17944.570312, -5153.674316),
            (16707, -3236),
            (19498.818359,     7.423645),
            (20078, 1566),
            (20919.000000,  7807.995117),
            (18432.478515,  7579.394531),
            (16062, 8801),
            (14848, 8332),
            (12101, 9560),
            (9699, 10557),
            (7245, 11574),
            (4707.063964, 12058.528320),
            (1914.881225, 13594.415039),
            (410.270294, 13274.137695),
            (-2543, 14793),
            (-3755, 15789),
            (-4056.763671, 16237.483398),
            (-3986.755126, 16859.513671), # Move into Riven Earth
        ],
    },
    {
        # Riven Earth
        "map_id": 501,  # explorable_name_to_id["Riven Earth"]
        "path": [
            (-11733.154296, -11176.163085),
            (-16270.063476,  -9512.484375),
            (-20738.242187,  -7199.259765),
            (-24031.421875,  -5271.342773),
            (-25487.144531,  -4222.924316),
            (-26255.710937,  -4118.685058), # Move into Rata Sum
        ],
    },
    {
        # Rata Sum (final outpost, ID 640)
        "map_id": 640,  # outpost_name_to_id["Rata Sum"]
        "path": [],
    },
]

# maps/EOTN/_10_tarnished_to_rata.py

from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_10_tarnished_to_rata_ids = {
    "outpost_id": outpost_name_to_id["Tarnished Haven"],  # 641
}

# 2) Exit path from Tarnished Haven (map 641)
_10_tarnished_to_rata_outpost_path = [
    (18132.033203, -7464.680175),   # first _Run
    (17079.275390, -2616.100097),   # Move into Alcazia Tangle
]

# 3) Explorable segments
_10_tarnished_to_rata_segments = [
    {
        # Alcazia Tangle
        "map_id": explorable_name_to_id["Alcazia Tangle"],
        "path": [
            (18184.322265, -7412.855957),
            (17944.570312, -5153.674316),
            (17909.607421, -2014.430664),
            (19498.818359,     7.423645),
            (20919.000000,  7807.995117),
            (18432.478515,  7579.394531),
            (16303.985351,  8577.814453),
            (12488.981445,  9278.306640),
            ( 9015.265625, 10940.495117),
            ( 4707.063964, 12058.528320),
            ( 1914.881225, 13594.415039),
            (  410.270294, 13274.137695),
            (-1868.005126, 12807.320312),
            (-3186.585937, 14853.175781),
            (-4056.763671, 16237.483398),
            (-3986.755126, 16859.513671), # Move into Riven Earth
        ],
    },
    {
        # Riven Earth
        "map_id": explorable_name_to_id["Riven Earth"],
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
        "map_id": outpost_name_to_id["Rata Sum"],
        "path": [],
    },
]
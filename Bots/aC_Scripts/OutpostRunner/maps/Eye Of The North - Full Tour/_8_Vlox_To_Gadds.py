# maps/EOTN/_8_vlox_to_gadds.py

# 1) Teleport ID
_8_vlox_to_gadds_ids = {
    "outpost_id": 624,  # outpost_name_to_id["Vlox's Falls"]
}

_8_vlox_to_gadds_outpost_path = [
    (16356, 14638),
    (15737, 13131),  # move toward Arbor Bay entrance
    (15471, 12385),  # closer to segment start
]

_8_vlox_to_gadds_segments = [
    {
        "map_id": 485,  # explorable_name_to_id["Arbor Bay"]
        "path": [
            (13957.639648, 10939.767578),
            (11597.432617,  6914.898925),
            (10650.434570,  1715.632202),
            (10843.333984, -1363.161132),
            (9930.636718, -4877.984375),
            (9027.03, -6093.33),
            (8212.88, -10234.18),
            (9693.83, -14933.47),
            (10640.22, -18084.69),
            (8943.773437, -20526.845703),
        ],
    },
    {
        "map_id": 581,  # explorable_name_to_id["Shards of Oor (level 1)"]
        "path": [
            (-14101.30, 8759.58),
            (-11921.27, 9941.48),
            (-9500, 9850),  # intermediate waypoint to avoid terrain
            (-7805.76, 9829.48),
            (-6000, 10500),  # smooth transition
            (-4170.037597, 11332.016601),
            (-1382.473144, 12572.248046),
            (1604.056274, 15276.850585),
            (6105.577148, 14172.998046),
            (10786.185546, 13449.357421),
            (12490.760742, 15101.247070),
            (14073, 16225),
            (16029.09, 16965.08),
            (17142.95, 13564.01),
            (16172.89, 11677.63),
            (14106, 12184),
        ],
    },
    {
        # Gadds Encampment (map 638) — final arrival, no walking needed
        "map_id": 638,  # outpost_name_to_id["Gadd's Encampment"]
        "path": [],
    },
]

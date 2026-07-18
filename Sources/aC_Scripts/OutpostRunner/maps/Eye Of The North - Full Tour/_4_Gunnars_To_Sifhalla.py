# maps/EOTN/_4_gunnars_to_sifhalla.py

# 1) IDs
_4_gunnars_to_sifhalla_ids = {
    # Teleport to Gunnar's Hold (644)
    "outpost_id": 644,  # outpost_name_to_id["Gunnar's Hold"]
}

# 2) Exit path from outpost 644
_4_gunnars_to_sifhalla_outpost_path = [
    (16003.853515, -6544.087402),  # initial run point
    (15193.037109, -6387.140625),  # into Norrhart Domains
]

# 3) Explorable segments
_4_gunnars_to_sifhalla_segments = [
    {
        # Norrhart Domains (ID 548)
        "map_id": 548,  # explorable_name_to_id["Norrhart Domains"],
        "path": [
            (13410, -3952),
            (10150, -323),
            (8119, 2417),
            (5626, 2300),
            (1010, 1936),
            (-500, 2100),
            (-1200, 3400),
            (-2013, 3261),
            (-3766.605468,  3390.211669),
            (-7325.385253,  2669.518066),
            (-9555.996093,  5570.137695),
            (-11109, 6200),
            (-14153.492187,  5198.475585),
            (-18538.169921,  7079.861816),
            (-22717.630859,  8757.812500),
            (-25531.134765, 10925.241210),
            (-26333.171875, 11242.023437),  # portal to Drakkar Lake
        ],
    },
    {
        # Drakkar Lake (ID 513)
        "map_id": 513,  # explorable_name_to_id["Drakkar Lake"],
        "path": [
            (14399.201171, -16963.455078),
            (12510.431640, -13414.477539),
            (12011.655273,  -9633.283203),
            (11484.183593,  -5569.488769),
            (12456.843750,  -411.864135),
            (13398.728515,   4328.439453),
            (14000.825195,   8676.782226),
            (14210.789062,  12432.768554),
            (13846.647460,  15850.121093),
            (13595.982421,  18950.578125),
            (13567.612304,  19432.314453),  # portal to Sifhalla
        ],
    },
    {
        # Sifhalla (final outpost, ID 643)
        "map_id": 643,  # outpost_name_to_id["Sifhalla"],
        "path": [],  # no further walking once you arrive
    },
]

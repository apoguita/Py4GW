# maps/EOTN/_5_sifhalla_to_olafstead.py

# 1) IDs
_5_sifhalla_to_olafstead_ids = {
    "outpost_id": 643,  # outpost_name_to_id["Sifhalla"]
}

# 2) Exit path from Sifhalla (map 643)
_5_sifhalla_to_olafstead_outpost_path = [
    (13510.718750, 19647.238281),
    (13596.396484, 19212.427734),  # into Drakkar Lake
]

# 3) Explorable segments
_5_sifhalla_to_olafstead_segments = [
    {
        # Drakkar Lake (ID 513)
        "map_id": 513,  # explorable_name_to_id["Drakkar Lake"]
        "path": [
            (13946,14287),
            (14388,10508),
            (14100,8500),
            (14288,6756),
            (14684,3461),
            (13005,2702),
            (10141,2868),
            (5936,3486),
            (3749,3286),
            (-12,-245),
            (-2285,-2268),
            (-2515,-3421),
            (-3937,-3302),
            (-5991,-4153),
            (-6873,-7715),
            (-7917,-9408),
            (-9268,-10470),
            (-9944,-13188),
            (-10744,-16592),
            (-12095,-20022),
            (-11484,-22223),
            (-11179,-24669),
            (-11041,-25654),
            (-11020,-26164),
        ],
    },
    {
        # Varajar Fells (ID 553)
        "map_id": 553,  # explorable_name_to_id["Varajar Fells"] returns 708 due to enum duplication, use correct ID directly
        "path": [
            (-997,15641),
            (-1723,11580),
            (-2496,7633),
            (-1901,4041),
            (-3998,972),
            (-4223,-2591),
            (-4014,-4621),
            (-2510,-3570),
            (-2980,-2797),
            (-3477,-1458),
            (-2889,134),
            (-1891,1086),
            (-1394,1212),
            (-1090,1276),
        ],
    },
    {
        # Olafstead (final outpost, ID 645)
        "map_id": 645,  # outpost_name_to_id["Olafstead"]
        "path": [],  # end of run
    },
]

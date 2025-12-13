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
            (13946.335937, 14286.607421),
            (14388, 10508),
            (14100, 8500),
            (13599.999023,  6967.771484),
            (13396.375000,  4099.683105),
            (10782.618164,  3919.063720),
            ( 5936.016113,  3485.744873),
            ( 3749.377929,  3285.844482),
            (-12.388924,  -244.892211),
            (-2623.909912, -3307.028076),
            (-3937, -3302),
            (-5991.19, -4153.14),
            (-7885.518554, -9186.645507),
            (-9944.139648,-13188.315429),
            (-10946.782226,-16388.703125),
            (-11847.703125,-19820.244140),
            (-11442.958984,-22719.455078),
            (-11040.512695,-25654.402343),
            (-11019.546875,-26164.341796),  # portal to Varajar Fells
        ],
    },
    {
        # Varajar Fells (ID 553)
        "map_id": 553,  # explorable_name_to_id["Varajar Fells"] returns 708 due to enum duplication, use correct ID directly
        "path": [
            (-997, 15641),
            (-1723, 11580),
            (-2496, 7633),
            (-1901, 4041),
            (-3998, 972),
            (-4223, -2591),
            (-4013.81, -4620.70),
            (-2980, -2797),
            (-2889, 134),
            (-1891, 1086),
            (-1350, 1236),
            (-371, 1440),
        ],
    },
    {
        # Olafstead (final outpost, ID 645)
        "map_id": 645,  # outpost_name_to_id["Olafstead"]
        "path": [],  # end of run
    },
]

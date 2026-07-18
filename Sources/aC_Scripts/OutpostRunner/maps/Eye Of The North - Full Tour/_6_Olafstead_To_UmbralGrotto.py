# maps/EOTN/_6_olafstead_to_umbralgrotto.py

# 1) IDs
_6_olafstead_to_umbralgrotto_ids = {
    "outpost_id": 645,  # outpost_name_to_id["Olafstead"]
}

# 2) Exit path from Olafstead (map 645)
_6_olafstead_to_umbralgrotto_outpost_path = [
    (-883.285644, 1212.171020),
    (-1452.154785, 1177.976684),  # into Varajar Fells
]

# 3) Explorable segments
_6_olafstead_to_umbralgrotto_segments = [
    {
        # Varajar Fells (ID 553)
        "map_id": 553,  # explorable_name_to_id["Varajar Fells"] (use explicit ID to avoid enum duplicates)
        "path": [
            (-3272, -730),
            (-3173, -2716),
            (-3166, -3963),
            (-4055.151855, -4363.498046),
            (-6962.863769, -3716.343017),
            (-11109.900390, -5252.222167),
            (-14969.330078, -6789.452148),
            (-19738.699218, -9123.355468),
            (-22088.320312,-10958.295898),
            (-24810.935546,-12084.257812),
            (-25980.177734,-13108.872070),  # portal to Verdant Cascades
        ],
    },
    {
        # Verdant Cascades (ID 566)
        "map_id": 566,  # explorable_name_to_id["Verdant Cascades"] (use explicit ID)
        "path": [
            (22595.748046, 12731.708984),
            (18976.330078, 11093.851562),
            (16437, 9139),
            (15406.838867,  7549.499023),
            (14353, 7411),
            (13416.123046,  4368.934570),
            (13584.649414,   156.471313),
            (14162.473632, -1488.160766),
            (13519.756835, -3782.271240),
            (11266.111328, -4884.791992),
            (7803.414550, -2783.716552),
            (6404.752441,  1633.880249),
            (6022.716796,  4174.048828),
            (3498.960205,  7248.467773),
            (3548, 7485),
            (1051, 7097),
            (-1762, 5021),
            (-4137, 4404),
            (-5300, 1686),
            (-7645, 1717),
            (-8373.044921,  2405.973632),
            (-11243.640625, 3636.515625),
            (-14829.459960, 4882.503417),
            (-18093.113281, 5579.701660),
            (-20726.955078, 5951.445312),
            (-22423.933593, 6339.730468),
            (-22984.621093, 6892.540527),  # portal to Umbral Grotto
        ],
    },
    {
        # Umbral Grotto (final outpost, ID 639)
        "map_id": 639,  # outpost_name_to_id["Umbral Grotto"]
        "path": [],  # end of run
    },
]

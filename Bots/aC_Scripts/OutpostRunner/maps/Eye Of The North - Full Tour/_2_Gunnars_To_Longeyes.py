from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_2_gunnars_to_longeyes_ids = {
    "outpost_id": outpost_name_to_id["Gunnar's Hold"],   # Teleport into Gunnar’s Hold (644)
}

# 2) Outpost exit path (in map 644)
_2_gunnars_to_longeyes_outpost_path = [
    (15886.204101, -6687.815917),
    (15183.199218, -6381.958984),
]

# 3) Explorable segments
_2_gunnars_to_longeyes_segments = [
    {
        # Norrhart Domains
        "map_id": explorable_name_to_id["Norrhart Domains"],
        "path": [
            (14233.820312, -3638.702636),
            (14944.690429,  1197.740966),
            (14855.548828,  4450.144531),
            (17964.738281,  6782.413574),
            (19127.484375,  9809.458984),
            (21742.705078, 14057.231445),
            (19933.869140, 15609.059570),
            (16294.676757, 16369.736328),
            (16392.476562, 16768.855468),
        ],
    },
    {
        # Bjora Marches
        "map_id": explorable_name_to_id["Bjora Marches"],
        "path": [
            (-11232.550781, -16722.859375),
            (-7655.780273 , -13250.316406),
            (-6672.132324 , -13080.853515),
            (-5497.732421 , -11904.576171),
            (-3598.337646 , -11162.589843),
            (-3013.927490 ,  -9264.664062),
            (-1002.166198 ,  -8064.565429),
            ( 3533.099609 ,  -9982.698242),
            ( 7472.125976 , -10943.370117),
            (12984.513671 , -15341.864257),
            (17305.523437 , -17686.404296),
            (19048.208984 , -18813.695312),
            (019634.173828, -19118.777343),
        ],
    },
    {
        # Longeyes Ledge (outpost 650)
        "map_id": outpost_name_to_id["Longeyes Ledge"],
        "path": [],  # no further walking once you arrive
    },
]
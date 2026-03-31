# 1) IDs
_2_gunnars_to_longeyes_ids = {
    "outpost_id": 644,  # outpost_name_to_id["Gunnar's Hold"]
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
        "map_id": 548,  # explorable_name_to_id["Norrhart Domains"],
        "path": [
            (14234,-3639),
            (14945,1198),
            (14856,4450),
            (16039,5238),
            (17835,6892),
            (19469,7258),
            (19128,10532),
            (22362,13906),
            (20039,15751),
            (16295,16370),
            (16392,16769),
        ],
    },
    {
        # Bjora Marches
        "map_id": 482,  # explorable_name_to_id["Bjora Marches"],
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
            (19634.173828, -19118.777343),
        ],
    },
    {
        # Longeyes Ledge (outpost 650)
        "map_id": 650,  # outpost_name_to_id["Longeyes Ledge"],
        "path": [],  # no further walking once you arrive
    },
]

# maps/EOTN/_3_longeyes_to_doomlore.py

# 1) IDs
_3_longeyes_to_doomlore_ids = {
    # Teleport to Longeye's Ledge outpost
    "outpost_id": 650,  # outpost_name_to_id["Longeyes Ledge"]
}

# 2) Exit path from the outpost (in map 650)
_3_longeyes_to_doomlore_outpost_path = [
    (-22469.261718, 13327.513671),  # Into town
    (-21791.328125, 12595.533203),  # Towards Grothmar Wardowns
]

# 3) Explorable segments
_3_longeyes_to_doomlore_segments = [
    {
        # Grothmar Wardowns
        "map_id": 649,  # explorable_name_to_id["Grothmar Wardowns"],
        "path": [
            (-18582.023437, 10399.527343),
            (-13987.378906, 10078.552734),
            (-10700.551757,  9980.495117),
            ( -7340.849121,  9353.873046),
            ( -4436.997070,  8518.824218),
            ( -0445.930755,  8262.403320),
            (  3324.289062,  8156.203613),
            (  7149.326660,  8494.817382),
            ( 11733.867187,  7774.760253),
            ( 15031.326171,  9167.790039),
            ( 18174.601562, 10689.784179),
            ( 20369.773437, 12352.750000),
            ( 22427.097656, 14882.499023),
            ( 24355.289062, 15175.175781),
            ( 25188.230468, 15229.357421),  # Portal to Dalada Uplands
        ],
    },
    {
        # Dalada Uplands
        "map_id": 647,  # explorable_name_to_id["Dalada Uplands"],
        "path": [
            (-16292.620117,  -715.887329),
            (-13617.916992,   405.243469),
            (-13256.524414,  2634.142089),
            (-15958.702148,  6655.416015),
            (-14465.992187,  9742.127929),
            (-13779.127929, 11591.517578),
            (-14929.544921, 13145.501953),
            (-15581.598632, 13865.584960),  # Portal to Doomlore Shrine
        ],
    },
    {
        # Doomlore Shrine (final map, no walking needed)
        "map_id": 648,  # outpost_name_to_id["Doomlore Shrine"],
        "path": [],
    },
]

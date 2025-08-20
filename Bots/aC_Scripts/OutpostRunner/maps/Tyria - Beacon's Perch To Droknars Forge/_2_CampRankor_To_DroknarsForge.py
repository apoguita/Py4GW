from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_2_camprankor_to_droknarsforge_ids = {
    "outpost_id": outpost_name_to_id["Camp Rankor"],
}

# 2) Outpost exit path
_2_camprankor_to_droknarsforge_outpost_path = [
    (7555, -45050),
]

# 3) Segments
_2_camprankor_to_droknarsforge_segments = [
 
    {
        "map_id": explorable_name_to_id["Talus Chute"],
        "path": [
            (-22278.0, 16193.0),
            (-22507.0, 13902.0),
            (-21768.0, 13325.0),
            (-20623.0, 13697.0),
            (-19025.0, 14729.0),
            (-17952.0, 14216.0),
            (-17951.0, 13383.0),
            (-18479.0, 11569.0),
            (-17968.0, 10803.0),
            (-15333.0, 10484.0),
            (-14280.0, 10064.0),
            (-13592.0, 8250.0),
            (-14931.0, 4803.0),
            (-15404.0, 3848.0),
            (-14444.0, 1333.0),
            (-12319.0, -850.0),
            (-9806.0, -1678.0),
            (-4801.0, -6345.0),
            (-1876.0, -7797.0),
            (-604.0, -9050.0),
            (2555.0, -11337.0),
            (4249.0, -12732.0),
            (6038.0, -14065.0),
            (8624.0, -16461.0),
            (8900.0, -16750.0),
        ],
    },

    {
        "map_id": outpost_name_to_id["Droknar's Forge"],
        "path": [],  # no further walking once you arrive
    },
]
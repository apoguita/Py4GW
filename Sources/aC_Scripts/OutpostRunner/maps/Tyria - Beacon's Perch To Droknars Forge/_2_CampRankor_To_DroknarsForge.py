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
            (-22278,16193),
            (-22615,13826),
            (-21861,13087),
            (-20510,13716),
            (-19018,14831),
            (-17840,14234),
            (-17778,13395),
            (-18759,11545),
            (-18059,10644),
            (-16533,10626),
            (-15297,10646),
            (-14280,10064),
            (-13452,8296),
            (-14385,5321),
            (-15642,4096),
            (-14558,1143),
            (-12531,-1151),
            (-9311,-1716),
            (-5462,-6385),
            (-2250,-7085),
            (781,-8860),
            (2431,-11467),
            (4249,-12732),
            (6038,-14065),
            (8624,-16461),
            (9167,-17017),
        ],
    },

    {
        "map_id": outpost_name_to_id["Droknar's Forge"],
        "path": [],  # no further walking once you arrive
    },
]
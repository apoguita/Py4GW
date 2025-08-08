from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id
# 1) IDs
_1_eotn_to_gunnars_ids = {
    "outpost_id": outpost_name_to_id["Eye of the North outpost"],
}

# 2) Outpost exit path (in map 642)
_1_eotn_to_gunnars_outpost_path = [
    (332.802429, 1432.140747),
    (1203.269165,  839.428955),
]

# 3) Segments  
_1_eotn_to_gunnars_segments = [
    {
        # “Ice Cliff Chasms” explorable
        "map_id": explorable_name_to_id["Ice Cliff Chasms"],
        "path": [
            (2324.802734,  5434.397460),
            ( 715.669250,  8835.476562),
            ( 504.575317, 11846.961914),
            ( 825.868530, 15970.333007),
            ( 173.692352, 20100.667968),
            (-2415.995361, 22778.201171),
            (-3309.545166, 24568.648437),
            (-3680.492919, 26832.437500),
            (-3818.726562, 27936.259765),
        ],
    },
    {
        # “Norrhart Domains” explorable
        "map_id": explorable_name_to_id["Norrhart Domains"],
        "path": [
            (11973.490234, -12021.736328),
            (12131.014648,  -9444.603515),
            (12851.580078,  -7496.924804),
            (14836.394531,  -6503.532714),
            (15347.208007,  -6517.461914),
        ],
    },
    {
        # “Gunnar’s Hold” explorable
        "map_id": outpost_name_to_id["Gunnar's Hold"],
        "path": [],  # no further walking once you arrive
    },
]
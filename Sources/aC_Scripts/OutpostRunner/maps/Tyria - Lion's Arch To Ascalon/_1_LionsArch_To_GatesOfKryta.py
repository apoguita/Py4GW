from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_1_lionsarch_to_gatesofkryta_ids = {
    "outpost_id": outpost_name_to_id["Lions Arch"],
}

# 2) Outpost exit path (inside Lion's Arch)
_1_lionsarch_to_gatesofkryta_outpost_path = [
    (1219, 7222),
    (1021, 10651),
    (250, 12350),
]

# 3) Segments
_1_lionsarch_to_gatesofkryta_segments = [
    {
        # "North Kryta Province" explorable
        "map_id": explorable_name_to_id["North Kryta Province"],
        "path": [
            (6367.0, -16387.0),
            (7051.0, -15604.0),
            (7786.0, -15095.0),
            (8428.0, -14254.0),
            (9947.0, -13037.0),
            (10867.0, -11511.0),
            (11531.0, -10530.0),
            (12271.0, -8982.0),
            (12921.0, -6362.0),
            (12394.0, -3336.0),
            (11328.0, -1729.0),
            (11373.0, 128.0),
            (10652.0, 2788.0),
            (10400.0, 4890.0),
            (9678.0, 5853.0),
            (9351.0, 6604.0),
            (9758.0, 7049.0),
            (11899.0, 8604.0),
            (12383.0, 9352.0),
            (15322.0, 12030.0),
            (17182.0, 12514.0),
            (19257.0, 10757.0),
            (19900.0, 11100.0),
            (20150.0, 11340.0),
        ],
    },

    {
        # "Scoundrel's Rise" explorable
        "map_id": explorable_name_to_id["Scoundrel's Rise"],
        "path": [
            (-6464.0, 9034.0),
            (-5671.0, 9090.0),
            (-4253.0, 8575.0),
            (-2787.0, 7865.0),
            (-1178.0, 5704.0),
            (-73.0, 4279.0),
            (1943.0, 2316.0),
            (3615.0, 318.0),
            (4031.0, 104.0),
            (3554.0, -1795.0),
            (2096.0, -2269.0),
            (200.0, -2640.0),
            (-1897.0, -4791.0),
            (-1418.0, -6793.0),
            (-1070.0, -7304.0),
        ],
    },

    {
        # "Gates of Kryta" outpost
        "map_id": outpost_name_to_id["Gates of Kryta outpost"],
        "path": [],  # no further walking once you arrive
    },
]

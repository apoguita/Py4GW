from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_7_gatesofkryta_to_lionsarch_ids = {
    "outpost_id": outpost_name_to_id["Gates of Kryta outpost"],
}

# 2) Outpost exit path (inside Gates of Kryta)
_7_gatesofkryta_to_lionsarch_outpost_path = [
    (-4203, 26650),
    (-4333, 26800),
]

# 3) Segments
_7_gatesofkryta_to_lionsarch_segments = [
    {
        "map_id": explorable_name_to_id["Scoundrel's Rise"],
        "path": [
            (200.0, -2640.0),
            (2096.0, -2269.0),
            (3554.0, -1795.0),
            (4031.0, 104.0),
            (3615.0, 318.0),
            (1943.0, 2316.0),
            (-73.0, 4279.0),
            (-1178.0, 5704.0),
            (-2787.0, 7865.0),
            (-4253.0, 8575.0),
            (-5671.0, 9090.0),
            (-6464.0, 9034.0),
            (-7000.0, 9000.0),
            (-7600, 8150),        
        ],
    },
    
    {
        "map_id": explorable_name_to_id["North Kryta Province"],
        "path": [
            (19257.0, 10757.0),
            (17182.0, 12514.0),
            (15322.0, 12030.0),
            (12383.0, 9352.0),
            (11899.0, 8604.0),
            (9758.0, 7049.0),
            (9351.0, 6604.0),
            (9678.0, 5853.0),
            (10400.0, 4890.0),
            (10652.0, 2788.0),
            (11373.0, 128.0),
            (11328.0, -1729.0),
            (12394.0, -3336.0),
            (12921.0, -6362.0),
            (12271.0, -8982.0),
            (11531.0, -10530.0),
            (10867.0, -11511.0),
            (9947.0, -13037.0),
            (8428.0, -14254.0),
            (7786.0, -15095.0),
            (7051.0, -15604.0),
            (6367.0, -16387.0),
            (5875, -17438),
            (6554, -18552)
        ],
    },
    {
        "map_id": outpost_name_to_id["Lions Arch"],
        "path": [],
    },
]

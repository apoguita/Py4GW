from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_1_lionsarch_to_dalessioseaboard_ids = {
    "outpost_id": outpost_name_to_id["Lions Arch"],
}

# 2) Outpost exit path (inside Lion's Arch)
_1_lionsarch_to_dalessioseaboard_outpost_path = [
    (1219, 7222),
    (1021, 10651),
    (250, 12350),
]

# 3) Segments
_1_lionsarch_to_dalessioseaboard_segments = [
    {
        # "North Kryta Province" explorable
        "map_id": explorable_name_to_id["North Kryta Province"],
        "path": [
            (5116.0, -17415.0),
            (2346.0, -17307.0),
            (757.0, -16768.0),
            (-1521.0, -16726.0),
            (-3246.0, -16407.0),
            (-6042.0, -16126.0),
            (-7706.0, -17248.0),
            (-8910.0, -17561.0),
            (-9893.0, -17625.0),
            (-11325.0, -18358.0),
            (-11553.0, -19246.0),
            (-11600.0, -19500.0)
        ],
    },
    {
        # "Gates of Kryta" outpost
        "map_id": outpost_name_to_id["D'Alessio Seaboard outpost"],
        "path": [],  # no further walking once you arrive
    },
]

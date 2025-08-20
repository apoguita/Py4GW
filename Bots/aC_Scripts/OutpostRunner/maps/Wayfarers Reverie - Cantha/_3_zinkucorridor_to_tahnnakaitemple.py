from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_3_zinkucorridor_to_tahnnakaitemple_ids = {
    "outpost_id": 284,
}

# 2) Outpost exit path
_3_zinkucorridor_to_tahnnakaitemple_outpost_path = [
    (8473, -18234),
    (7516, -17849),
    (6574, -17425),
    (5528, -17333),
    (4523, -17287),
    (3471, -17177),
    (2746, -16467),
    (2717, -15753),
]

# 3) Segments
_3_zinkucorridor_to_tahnnakaitemple_segments = [
    {
        "map_id": 269,
        "path": [
            (2845, -15259),
            (2820, -13228),
            (2875, -11167),
            (3316, -9698),
            (3086, -9157),
        ],
    },
    {
        "map_id": 269,
        "path": [],  # no further walking once you arrive
    },
]

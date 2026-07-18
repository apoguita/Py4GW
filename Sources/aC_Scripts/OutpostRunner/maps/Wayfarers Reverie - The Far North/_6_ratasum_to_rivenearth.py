from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_6_ratasum_to_rivenearth_ids = {
    "outpost_id": 640,
}

# 2) Outpost exit path
_6_ratasum_to_rivenearth_outpost_path = [
    (19948, 16851),
    (20332, 16845),
]

# 3) Segments
_6_ratasum_to_rivenearth_segments = [
    {
        "map_id": 501,
        "path": [
            (-25000, -3996),
            (-23845, -2283),
            (-22707, -634),
            (-21571, 1071),
            (-20448, 2744),
            (-20880, 4726),
            (-21502, 6645),
            (-20510, 8434),
            (-18695, 9337),
            (-16692, 9407),
            (-16443, 9285),
        ],
    },
    {
        "map_id": 501,
        "path": [],  # no further walking once you arrive
    },
]

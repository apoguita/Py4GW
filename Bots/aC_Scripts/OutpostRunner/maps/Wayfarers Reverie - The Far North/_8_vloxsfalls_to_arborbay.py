from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_8_vloxsfalls_to_arborbay_ids = {
    "outpost_id": 624,
}

# 2) Outpost exit path
_8_vloxsfalls_to_arborbay_outpost_path = [
    (16143, 14059),
    (15750, 13101),
    (15435, 12349),
]

# 3) Segments
_8_vloxsfalls_to_arborbay_segments = [
    {
        "map_id": 485,
        "path": [
            (15381, 12281),
            (13734, 11132),
            (12182, 9782),
            (11314, 7973),
            (10474, 6078),
            (9561, 4287),
            (8338, 2636),
            (6589, 1624),
            (4834, 499),
            (3263, -780),
            (1225, -879),
            (-750, -1345),
            (-2522, -2374),
            (-3840, -3935),
            (-4973, -5613),
            (-5793, -7459),
            (-7139, -8991),
            (-6785, -10961),
            (-5844, -11643),
        ],
    },
    {
        "map_id": 485,
        "path": [],  # no further walking once you arrive
    },
]

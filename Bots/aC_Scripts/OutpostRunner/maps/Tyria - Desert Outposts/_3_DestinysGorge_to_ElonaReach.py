from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_3_destinysgorge_to_elonareach_ids = {
    "outpost_id": outpost_name_to_id["Destinys Gorge"],
}

# 2) Outpost exit path
_3_destinysgorge_to_elonareach_outpost_path = [
    (-16383, 20844),
    (-16799, 22406),
    (-17338, 22559),
]

# 3) Segments
_3_destinysgorge_to_elonareach_segments = [
    {
        "map_id": explorable_name_to_id["Skyward Reach"],
        "path": [
            (19210, 19533),
            (17634, 19258),
            (15029, 16382),
            (14395, 14588),
            (13958, 13943),
            (12123, 12770),
            (9076, 14667),
            (9777, 15898),
            (8417, 18046),
            (8201, 18954),
            (8526, 19367),
        ],
    },
    {
        "map_id": explorable_name_to_id["Diviner's Ascent"],
        "path": [
            (-3661, -20516),
            (-4470, -18674),
            (-4281, -16627),
            (-3201, -14921),
            (-1533, -13805),
            (139, -12687),
            (1853, -11536),
            (3531, -10403),
            (5210, -9269),
            (6882, -8104),
            (8322, -6661),
            (8995, -4743),
            (9118, -2724),
            (9240, -701),
            (9345, 1351),
            (10569, 2978),
            (10750, 4994),
            (9142, 6244),
            (7183, 6834),
            (5213, 7255),
            (3192, 7412),
            (1187, 7066),
            (-788, 6520),
            (-2736, 6004),
            (-3909, 5739),
            (-5661, 3704),
            (-7304, 3721),
            (-7802, 3766),
        ],
    },
    {
        "map_id": outpost_name_to_id["Elona Reach outpost"],
        "path": [],  # no further walking once you arrive
    },
]

from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_4_elonareach_to_seekerspassage_ids = {
    "outpost_id": outpost_name_to_id["Elona Reach outpost"],
}

# 2) Outpost exit path
_4_elonareach_to_seekerspassage_outpost_path = [
    (15788, 7231),
    (17299, 6827),
]

# 3) Segments
_4_elonareach_to_seekerspassage_segments = [
    {
        "map_id": explorable_name_to_id["Diviner's Ascent"],
        "path": [
            (-5661, 3704),
            (-4372, 5279),
            (-3023, 6817),
            (-2227, 8668),
            (-1967, 10663),
            (-1605, 12683),
            (-1438, 14736),
            (-1738, 16728),
            (-3566, 15864),
            (-5338, 14872),
            (-7028, 13759),
            (-8499, 12370),
            (-10238, 11311),
            (-11940, 10249),
            (-13932, 10005),
            (-15119, 11619),
            (-16417, 13180),
            (-17735, 14709),
            (-19154, 16132),
            (-19861, 16840),
            (-19558, 16209),
        ],
    },
    {
        "map_id": explorable_name_to_id["Salt Flats"],
        "path": [
            (19645, 16331),
            (18578, 14585),
            (17492, 12839),
            (16737, 10985),
            (16199, 8994),
            (14570, 7763),
            (12615, 8329),
            (10952, 9451),
            (9022, 10019),
            (7046, 10605),
            (5111, 11179),
            (3124, 11626),
            (1120, 11961),
            (-866, 12318),
            (-2863, 12638),
            (-4505, 13884),
            (-5938, 15359),
            (-7743, 14465),
            (-9214, 13044),
            (-10651, 11571),
            (-11987, 10072),
            (-12592, 8155),
            (-13020, 6632),
            (-14169, 6091),
            (-15733, 7096),
            (-16159, 7515),
            (-16600, 8100)
        ],
    },
    {
        "map_id": outpost_name_to_id["Seekers Passage"],
        "path": [],  # no further walking once you arrive
    },
]


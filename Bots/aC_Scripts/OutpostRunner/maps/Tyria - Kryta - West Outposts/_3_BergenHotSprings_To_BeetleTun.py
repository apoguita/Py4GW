from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_3_bergenhotsprings_to_beetletun_ids = {
    "outpost_id": outpost_name_to_id["Bergen Hot Springs"],
}

# 2) Outpost exit path
_3_bergenhotspring_to_beetletun_outpost_path = [
    (15521, -15378),
    (15450, -15050),
]

# 3) Segments
_3_bergenhotspring_to_beetletun_segments = [
    {
        "map_id": explorable_name_to_id["Nebo Terrace"],
        "path": [
            (14184.0, -9819.0),
            (15157.0, -7087.0),
            (15504.0, -5348.0),
            (13235.0, -3726.0),
            (10232.0, -1900.0),
            (7462.0, 2907.0),
            (6130.0, 6205.0),
            (4827.0, 7899.0),
            (4446.0, 10193.0),
            (5245.0, 13323.0),
            (3349.0, 15344.0),
            (843.0, 16419.0),
            (-789.0, 16865.0),
            (-3397.0, 17382.0),
            (-8063.0, 17752.0),
            (-12320.0, 18594.0),
            (-14360.0, 19097.0),
            (-14500.0, 19085.0)
        ],
    },
    {
        "map_id": outpost_name_to_id["Beetletun"],
        "path": [],  # no further walking once you arrive
    },
]

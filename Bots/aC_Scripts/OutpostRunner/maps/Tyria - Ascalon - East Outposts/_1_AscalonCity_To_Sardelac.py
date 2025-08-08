from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_1_ascaloncity_to_sardelac_ids = {
    "outpost_id": outpost_name_to_id["Ascalon City"],
}
# 2) Outpost exit path
_1_ascaloncity_to_sardelac_outpost_path = [
    (594, 1903),
    (-84, 1857),
    (-380, 1860)
]
# 3) Segments
_1_ascaloncity_to_sardelac_segments = [
    {
        "map_id": explorable_name_to_id["Old Ascalon"],
        "path": [
            (16659.0, 10483.0),
            (15084.0, 9586.0),
            (13409.0, 8508.0),
            (11066.0, 6218.0),
            (9028.0, 4097.0),
            (7872.0, 2656.0),
            (6295.0, 1250.0),
            (4847.0, 327.0),
            (3216.0, -425.0),
            (2059.0, -662.0),
            (715.0, -600.0),
            (-885.0, -175.0),
            (-2411.0, 478.0),
            (-3115.0, 463.0),
            (-4760.0, -30.0),
            (-5100.0, -51.0),
        ],
    },
    {
        "map_id": outpost_name_to_id["Sardelac Sanitarium"],
        "path": [
        ],
    }
]
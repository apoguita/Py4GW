from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_2_dalessioseaboard_to_bergenhotsprings_ids = {
    "outpost_id": outpost_name_to_id["D'Alessio Seaboard outpost"],
}

# 2) Outpost exit path
_2_dalessioseaboard_to_bergenhotsprings_outpost_path = [
    (16000, 17080),
    (16030, 17200),
]

# 3) Segments
_2_dalessioseaboard_to_bergenhotsprings_segments = [
    {
        "map_id": explorable_name_to_id["North Kryta Province"],
        "path": [
            (-11453.0, -18065.0),
            (-10991.0, -16776.0),
            (-10791.0, -15737.0),
            (-10130.0, -14138.0),
            (-10106.0, -13005.0),
            (-10558.0, -9708.0),
            (-10319.0, -7888.0),
            (-10798.0, -5941.0),
            (-10958.0, -1009.0),
            (-10572.0, 2332.0),
            (-10784.0, 3710.0),
            (-11125.0, 4650.0),
            (-11690.0, 5496.0),
            (-12931.0, 6726.0),
            (-13340.0, 7971.0),
            (-13932.0, 9091.0),
            (-13937.0, 11521.0),
            (-14639.0, 13496.0),
            (-15090.0, 14734.0),
            (-16653.0, 16226.0),
            (-18944.0, 14799.0),
            (-19468.0, 15449.0),
            (-19550.0, 15625.0)
        ],
    },
    {
        "map_id": explorable_name_to_id["Nebo Terrace"],
        "path": [
            (19271.0, 5207.0),
            (18307.0, 5369.0),
            (17704.0, 4786.0),
            (17801.0, 2710.0),
            (18221.0, 506.0),
            (18133.0, -1406.0),
            (16546.0, -4102.0),
            (15434.0, -6217.0),
            (14927.0, -8731.0),
            (14297.0, -10366.0),
            (14347.0, -12097.0),
            (15373.0, -14769.0),
            (15425.0, -15035.0)
        ],
    },
    {
        # "Gates of Kryta" outpost
        "map_id": outpost_name_to_id["Bergen Hot Springs"],
        "path": [],  # no further walking once you arrive
    },
]

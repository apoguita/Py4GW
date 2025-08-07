from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_6_grendichcourthouse_to_nolaniacademy_ids = {
    "outpost_id": outpost_name_to_id["Grendich Courthouse"],
}
# 2) Outpost exit path (Ascalon City)
_6_grendichcourthouse_to_nolaniacademy_outpost_path = [
    (1686, 13755),
    (1900, 13600),
]
# 3) Segments
_6_grendichcourthouse_to_nolaniacademy_segments = [
    {
        # "Diessa Lowlands" explorable
        "map_id": explorable_name_to_id["Diessa Lowlands"],
        "path": [          
            (2172.0, 9693.0),
            (-132.0, 6987.0),
            (-1720.0, 5518.0),
            (-3413.0, 4789.0),
            (-6892.0, 3712.0),
            (-8278.0, 2620.0),
            (-9349.0, 484.0),
            (-11123.0, -1221.0),
            (-11903.0, -3784.0),
            (-12422.0, -7262.0),
            (-12632.0, -8557.0),
            (-12375.0, -10069.0),
            (-12267.0, -11143.0),
            (-12699.0, -11534.0),
            (-16222.0, -13083.0),
            (-17736.0, -13932.0),
            (-18895.0, -14607.0),
            (-20908.0, -15054.0),
            (-22072.0, -16178.0),
            (-22547.0, -16659.0),
            (-22780.0, -16810.0),
        ],
    },

    {
        # "Nolani Academy outpost" outpost
        "map_id": outpost_name_to_id["Nolani Academy outpost"],
        "path": [],  # no further walking once you arrive
    },
]
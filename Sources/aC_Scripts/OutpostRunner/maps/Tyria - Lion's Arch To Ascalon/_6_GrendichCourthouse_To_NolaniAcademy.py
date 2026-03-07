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
            (2172,9693),
            (-132,6987),
            (-1720,5518),
            (-3413,4789),
            (-6892,3712),
            (-8278,2620),
            (-9349,484),
            (-11123,-1221),
            (-11903,-3784),
            (-11503,-5396),
            (-12422,-7262),
            (-12632,-8557),
            (-12375,-10069),
            (-12267,-11143),
            (-12699,-11534),
            (-16222,-13083),
            (-17736,-13932),
            (-18895,-14607),
            (-20908,-15054),
            (-22072,-16178),
            (-22547,-16659),
            (-22780,-16810),
        ],
    },

    {
        # "Nolani Academy outpost" outpost
        "map_id": outpost_name_to_id["Nolani Academy outpost"],
        "path": [],  # no further walking once you arrive
    },
]

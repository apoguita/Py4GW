from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_5_frontiergate_to_ruinsofsurmia_ids = {
    "outpost_id": outpost_name_to_id["Frontier Gate"],
}
# 2) Outpost exit path
_5_frontiergate_to_ruinsofsurmia_outpost_path = [
    (-14118, 4331),
    (-14050, 4330)
]
# 3) Segments
_5_frontiergate_to_ruinsofsurmia_segments = [
    {
        "map_id": explorable_name_to_id["Eastern Frontier"],
        "path": [
            (-11559.0, 4274.0),
            (-10746.0, 4448.0),
            (-10568.0, 5703.0),
            (-9843.0, 6564.0),
            (-8474.0, 7400.0),
            (-7650.0, 8582.0),
            (-8013.0, 10065.0),
            (-9907.0, 10888.0),
            (-11343.0, 11268.0),
            (-12114.0, 11735.0),
            (-12636.0, 12735.0),
            (-12891.0, 13564.0),
            (-13680.0, 14052.0),
            (-15520.0, 12625.0),
            (-17823.0, 11146.0),
            (-19072.0, 10998.0),
            (-19875.0, 10914.0),
            (-19975.0, 10900.0)
        ],
    },
    {
        "map_id": outpost_name_to_id["Ruins of Surmia outpost"],
        "path": [
        ],
    }
]
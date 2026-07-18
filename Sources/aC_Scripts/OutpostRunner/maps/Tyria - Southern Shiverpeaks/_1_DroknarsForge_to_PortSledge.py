from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_1_DroknarsForge_to_PortSledge_ids = {
    "outpost_id": 20,
}

# 2) Outpost exit path
_1_DroknarsForge_to_PortSledge_outpost_path = [
    (3003,3940),
    (4992,3001),
    (5558,1588),
    (6151,1079),
]

# 3) Segments
_1_DroknarsForge_to_PortSledge_segments = [
    {
        "map_id": 95,
        "path": [
            (-17339,6163),
            (-14780,7524),
            (-14404,8395),
            (-12036,7494),
            (-9512,7085),
            (-9140,5367),
            (-6211,2587),
            (-2999,2587),
            (-3289,2123),
            (-7123,-1204),
            (-7326,-2367),
            (-7388,-2828),
        ],
    },
    {
        "map_id": 158,
        "path": [],  # no further walking once you arrive
    },
]

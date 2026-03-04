from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_2_pikensquare_to_grendichcourthouse_ids = {
    "outpost_id": outpost_name_to_id["Piken Square"],
}

# 2) Outpost exit path (inside Piken Square)
_2_pikensquare_to_grendichcourthouse_outpost_path = [
    (20238, 7794),
    (20235, 7654),
]

# 3) Segments - Reversed from the original _7_GrendichCourthouse_To_PikenSquare.py
_2_pikensquare_to_grendichcourthouse_segments = [
    {
        "map_id": explorable_name_to_id["The Breach"],
        "path": [
            (20267,6698),
            (19654,6404),
            (17767,6616),
            (15395,5869),
            (15270,6635),
            (15649,7795),
            (14172,7817),
            (12439,6921),
            (11693,8284),
            (10307,8661),
            (8906,9399),
            (2464,7979),
            (1740,8990),
            (707,9965),
            (-493,10852),
            (-2457,10638),
            (-3434,9745),
            (-7322,9368),
            (-8287,9486),
            (-9700,9933),
            (-11530,9531),
            (-12997,8352),
            (-13361,6232),
            (-14360,5178),
            (-15757,4064),
            (-17702,3932),
            (-18456,3414),
            (-19129,3231),
            (-19694,3228),
        ],
    },
    
    {
        "map_id": explorable_name_to_id["Diessa Lowlands"],
        "path": [
            (22147,-15153),
            (21412,-14600),
            (20887,-13781),
            (18751,-12262),
            (17518,-11380),
            (15665,-10984),
            (11153,-11017),
            (10907,-9688),
            (10102,-8946),
            (9324,-6571),
            (8386,-3041),
            (7314,-206),
            (6782,767),
            (5355,1200),
            (2391,1683),
            (897,1037),
            (-1200,2592),
            (-1401,4000),
            (-1848,5185),
            (-184,6984),
            (1717,8738),
            (2326,10173),
            (2917,11657),
            (3090,13016),
            (2000,13500),
        ],
    },
    {
        "map_id": outpost_name_to_id["Grendich Courthouse"],
        "path": [],
    },   
]



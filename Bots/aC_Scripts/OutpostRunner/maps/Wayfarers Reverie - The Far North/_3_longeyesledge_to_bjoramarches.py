from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_3_longeyesledge_to_bjoramarches_ids = {
    "outpost_id": 650,
}

# 2) Outpost exit path
_3_longeyesledge_to_bjoramarches_outpost_path = [
    (-24897, 15360),
    (-25798, 15873),
    (-26622, 16274),
]

# 3) Segments
_3_longeyesledge_to_bjoramarches_segments = [
    {
        "map_id": 482,
        "path": [
            (18184.009766, -17519.433594),
            (16278.378906, -13816.135742),
            (14912.120117,  -9862.690430),
            (13107.225586,  -6577.242188),
            (12435.006836,  -4496.427246),
            ( 9087.493164,  -2764.180664),
            ( 6993.439941,   -658.132935),
            ( 6487.164062,   2904.162842),
            ( 5687.984375,   7627.857910),
            ( 3874.116943,   8687.326172),
            ( 4460.297852,  12783.406250),
            (  947.482727,  14094.935547),
        ],
    },
    {
        "map_id": 482,
        "path": [],  # no further walking once you arrive
    },
]

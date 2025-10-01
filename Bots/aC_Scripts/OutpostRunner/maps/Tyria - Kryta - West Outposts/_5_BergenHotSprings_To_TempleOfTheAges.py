from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_5_bergenhotsprings_to_templeoftheages_ids = {
    "outpost_id": outpost_name_to_id["Bergen Hot Springs"],
}

# 2) Outpost exit path
_5_bergenhotsprings_to_templeoftheages_outpost_path = [
    (15521, -15378),
    (15450, -15050),
]

# 3) Segments
_5_bergenhotsprings_to_templeoftheages_segments = [
    {
        "map_id": explorable_name_to_id["Nebo Terrace"],
        "path": [
            (13276.0, -14317.0),
            (10761.0, -14522.0),
            (8660.0, -12109.0),
            (6637.0, -9216.0),
            (4995.0, -7951.0),
            (1522.0, -7990.0),
            (-924.0, -10670.0),
            (-3489.0, -11607.0),
            (-4086.0, -11692.0),
            (-4290.0, -11599.0)
        ],
    },
    {
        "map_id": explorable_name_to_id["Cursed Lands"],
        "path": [
            (-4523.0, -9755.0),
            (-4067.0, -8786.0),
            (-4207.0, -7806.0),
            (-5497.0, -6137.0),
            (-7331.0, -6178.0),
            (-8784.0, -4598.0),
            (-9053.0, -2929.0),
            (-9610.0, -2136.0),
            (-10879.0, -1685.0),
            (-10731.0, -760.0),
            (-12517.0, 5459.0),
            (-15510.0, 7154.0),
            (-18010.0, 7033.0),
            (-18717.0, 7537.0),
            (-19896.0, 8964.0),
            (-20100.0, 9025.0)
        ], 
    },
    {
        "map_id": explorable_name_to_id["The Black Curtain"],
        "path": [
            (17882.0, 15989.0),
            (16343.0, 15499.0),
            (15376.0, 15197.0),
            (13700.0, 12800.0),
            (14617.0, 16812.0),
            (13315.0, 17474.0),
            (10971.0, 18014.0),
            (8716.0, 18587.0),
            (5616.0, 17732.0),
            (3795.0, 17750.0),
            (1938.0, 16994.0),
            (592.0, 16243.0),
            (-686.0, 14967.0),
            (-1968.0, 14407.0),
            (-3398.0, 14730.0),
            (-4340.0, 14938.0),
            (-5004.0, 15424.0),
            (-5207.0, 15882.0),
            (-5180.0, 16000.0)
        ], 
    },
    {
        "map_id": outpost_name_to_id["Temple of the Ages"],
        "path": [],  # no further walking once you arrive
    },
]
